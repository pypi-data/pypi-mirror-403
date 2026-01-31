"""
DynamoDB Backend for Centralized Compatibility Storage

Provides centralized storage and synchronization of compatibility data
across all Epochly instances using AWS DynamoDB.

Author: Epochly Development Team
"""

import os
import json
import logging
import time
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import uuid

logger = logging.getLogger(__name__)

# Lazy import boto3 to avoid 12s initialization delay
# Import is deferred until actually needed for AWS operations
BOTO3_AVAILABLE = False
boto3 = None
Key = None
Attr = None
ClientError = None
BotoCoreError = None

def _ensure_boto3():
    """Lazy initialization of boto3 to avoid startup delay."""
    global BOTO3_AVAILABLE, boto3, Key, Attr, ClientError, BotoCoreError

    if boto3 is not None:
        return  # Already loaded

    # Check if we should skip AWS loading for performance
    try:
        # Import performance optimizer from benchmarks directory
        import sys
        import os
        benchmarks_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'benchmarks')
        if benchmarks_path not in sys.path:
            sys.path.insert(0, benchmarks_path)

        from performance_optimization import should_skip_aws

        if should_skip_aws():
            logger.debug("Skipping AWS/boto3 loading due to performance optimization")
            BOTO3_AVAILABLE = False
            return

    except ImportError:
        # Performance optimizer not available, proceed with normal loading
        pass

    # Load boto3 only when actually needed
    try:
        import boto3 as boto3_module
        from boto3.dynamodb.conditions import Key as KeyCondition, Attr as AttrCondition
        from botocore.exceptions import ClientError as BotoClientError, BotoCoreError as BotoCoreErr

        # Assign to module-level globals (must match global declaration above)
        globals()['boto3'] = boto3_module
        globals()['Key'] = KeyCondition
        globals()['Attr'] = AttrCondition
        globals()['ClientError'] = BotoClientError
        globals()['BotoCoreError'] = BotoCoreErr
        globals()['BOTO3_AVAILABLE'] = True

        logger.debug("boto3 loaded successfully (lazy initialization)")

    except ImportError:
        globals()['BOTO3_AVAILABLE'] = False
        logger.debug("boto3 not available - DynamoDB backend will be disabled")


class DynamoDBCompatibilityBackend:
    """
    DynamoDB backend for centralized compatibility storage.
    
    Features:
    - Centralized storage across all Epochly instances
    - Real-time synchronization
    - Community-driven compatibility data
    - License validation integration
    - Automatic table creation and management
    """
    
    TABLE_NAME = "epochly-compatibility"
    GSI_MODULE_TYPE = "ModuleTypeIndex"
    GSI_TIMESTAMP = "TimestampIndex"
    GSI_USER_ID = "UserIdIndex"
    
    def __init__(self, 
                 table_name: Optional[str] = None,
                 region: str = "us-east-1",
                 endpoint_url: Optional[str] = None,
                 create_table: bool = True,
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None):
        """
        Initialize DynamoDB backend.
        
        Args:
            table_name: DynamoDB table name (uses default if None)
            region: AWS region
            endpoint_url: Custom endpoint (for local DynamoDB)
            create_table: Auto-create table if it doesn't exist
            aws_access_key_id: AWS access key (for local testing)
            aws_secret_access_key: AWS secret key (for local testing)
        """
        # Ensure boto3 is loaded before proceeding
        _ensure_boto3()

        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for DynamoDB backend. Install with: pip install boto3")
        
        self.table_name = table_name or os.environ.get('EPOCHLY_DYNAMO_TABLE', self.TABLE_NAME)
        self.region = region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        self.endpoint_url = endpoint_url or os.environ.get('DYNAMODB_ENDPOINT_URL')
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        
        # Store references to boto3 exceptions and conditions for easy access
        # Use the module-level globals that were set by _ensure_boto3()
        global ClientError, BotoCoreError, Key, Attr
        if ClientError and BotoCoreError and Key and Attr:
            self.ClientError = ClientError
            self.BotoCoreError = BotoCoreError
            self.Key = Key
            self.Attr = Attr
        else:
            raise RuntimeError("boto3 conditions/exceptions not loaded properly")

        # Initialize DynamoDB client and resource
        self._init_aws_clients()

        # Get or create table
        if create_table:
            self._ensure_table_exists()

        # Cache for batch operations
        self._batch_cache = []
        self._last_batch_write = time.time()
    
    def _init_aws_clients(self) -> None:
        """Initialize AWS clients with proper credentials"""
        # Use the module-level boto3 that was loaded by _ensure_boto3()
        global boto3
        if boto3 is None:
            raise RuntimeError("boto3 not loaded - this should not happen after _ensure_boto3()")

        session_kwargs = {}

        # Support for explicit credentials (for testing)
        if self.aws_access_key_id and self.aws_secret_access_key:
            session_kwargs['aws_access_key_id'] = self.aws_access_key_id
            session_kwargs['aws_secret_access_key'] = self.aws_secret_access_key
        # Support for AWS profiles
        elif os.environ.get('AWS_PROFILE'):
            session_kwargs['profile_name'] = os.environ['AWS_PROFILE']

        session = boto3.Session(**session_kwargs)
        
        # Create clients
        client_kwargs = {'region_name': self.region}
        if self.endpoint_url:
            client_kwargs['endpoint_url'] = self.endpoint_url
        
        self.dynamodb = session.resource('dynamodb', **client_kwargs)
        self.dynamodb_client = session.client('dynamodb', **client_kwargs)
        
        # Get table reference
        self.table = self.dynamodb.Table(self.table_name)
    
    def _ensure_table_exists(self) -> None:
        """Ensure DynamoDB table exists with proper schema"""
        try:
            # Check if table exists
            self.table.load()
            logger.debug(f"DynamoDB table {self.table_name} exists")

        except self.ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Create table
                logger.info(f"Creating DynamoDB table {self.table_name}")
                self._create_table()
            else:
                raise
    
    def _create_table(self) -> None:
        """Create DynamoDB table with proper schema"""
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'pk', 'KeyType': 'HASH'},  # Partition key
                    {'AttributeName': 'sk', 'KeyType': 'RANGE'}   # Sort key
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'pk', 'AttributeType': 'S'},
                    {'AttributeName': 'sk', 'AttributeType': 'S'},
                    {'AttributeName': 'module_name', 'AttributeType': 'S'},
                    {'AttributeName': 'record_type', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'N'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': self.GSI_MODULE_TYPE,
                        'Keys': [
                            {'AttributeName': 'module_name', 'KeyType': 'HASH'},
                            {'AttributeName': 'record_type', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    },
                    {
                        'IndexName': self.GSI_TIMESTAMP,
                        'Keys': [
                            {'AttributeName': 'record_type', 'KeyType': 'HASH'},
                            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    },
                    {
                        'IndexName': self.GSI_USER_ID,
                        'Keys': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {'Key': 'Application', 'Value': 'Epochly'},
                    {'Key': 'Component', 'Value': 'Compatibility'}
                ]
            )
            
            # Wait for table to be active
            table.wait_until_exists()
            logger.info(f"Created DynamoDB table {self.table_name}")
            
        except self.ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.debug(f"Table {self.table_name} already exists")
            else:
                raise
    
    def put_compatibility_record(self, module_name: str, compatibility_info: Dict[str, Any], 
                                condition: Optional[str] = None) -> bool:
        """
        Store compatibility information for a module.
        
        Args:
            module_name: Name of the module
            compatibility_info: Compatibility information
            condition: Optional condition expression
            
        Returns:
            True if successful
        """
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                # Prepare item
                item = {
                    'pk': f"MODULE#{module_name}",
                    'sk': f"COMPAT#{datetime.now(timezone.utc).isoformat()}",
                    'module_name': module_name,
                    'record_type': 'compatibility',
                    'timestamp': Decimal(str(time.time())),
                    'data': json.dumps(compatibility_info),
                    'ttl': int(time.time() + 30 * 24 * 3600)  # 30 days TTL
                }
                
                # Add user context if available
                user_id = self._get_user_id()
                if user_id:
                    item['user_id'] = user_id
                
                # Prepare put parameters
                put_params = {'Item': item}
                if condition:
                    put_params['ConditionExpression'] = condition
                
                # Put item
                self.table.put_item(**put_params)
                logger.debug(f"Stored compatibility record for {module_name}")
                return True
                
            except self.ClientError as e:
                if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                        continue
                logger.error(f"Failed to store compatibility record: {e}")
                return False
            except Exception as e:
                logger.error(f"Failed to store compatibility record: {e}")
                return False
        
        return False
    
    def get_module_compatibility(self, module_name: str) -> Optional[Dict[str, Any]]:
        """
        Get latest compatibility information for a module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            Compatibility information or None
        """
        try:
            # Query for latest compatibility record
            response = self.table.query(
                KeyConditionExpression=self.Key('pk').eq(f"MODULE#{module_name}"),
                ScanIndexForward=False,  # Sort descending by timestamp
                Limit=1
            )
            
            if response['Items']:
                item = response['Items'][0]
                return json.loads(item['data'])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get compatibility record: {e}")
            return None
    
    def get_community_compatibility(self, module_name: str) -> Dict[str, Any]:
        """
        Get aggregated community compatibility data for a module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            Aggregated compatibility data
        """
        try:
            # Query all compatibility records for module
            response = self.table.query(
                IndexName=self.GSI_MODULE_TYPE,
                KeyConditionExpression=(
                    self.Key('module_name').eq(module_name) &
                    self.Key('record_type').eq('compatibility')
                )
            )
            
            # Aggregate results
            total_reports = len(response['Items'])
            compatible_count = 0
            incompatible_count = 0
            issues = []
            
            for item in response['Items']:
                data = json.loads(item['data'])
                if data.get('compatible', False):
                    compatible_count += 1
                else:
                    incompatible_count += 1
                    if 'error' in data:
                        issues.append(data['error'])
            
            return {
                'module': module_name,
                'total_reports': total_reports,
                'compatible_count': compatible_count,
                'incompatible_count': incompatible_count,
                'compatibility_score': compatible_count / total_reports if total_reports > 0 else 0,
                'common_issues': issues[:5]  # Top 5 issues
            }
            
        except Exception as e:
            logger.error(f"Failed to get community compatibility: {e}")
            return {}
    
    def report_failure(self, module_name: str, error_info: Dict[str, Any]) -> bool:
        """
        Report a module failure.
        
        Args:
            module_name: Name of the module
            error_info: Error information
            
        Returns:
            True if successful
        """
        try:
            # Prepare failure record
            item = {
                'pk': f"MODULE#{module_name}",
                'sk': f"FAILURE#{datetime.now(timezone.utc).isoformat()}",
                'module_name': module_name,
                'record_type': 'failure',
                'timestamp': Decimal(str(time.time())),
                'error_info': json.dumps(error_info),
                'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
                'platform': os.sys.platform,
                'ttl': int(time.time() + 90 * 24 * 3600)  # 90 days TTL
            }
            
            # Add user context
            user_id = self._get_user_id()
            if user_id:
                item['user_id'] = user_id
            
            # Put item
            self.table.put_item(Item=item)
            logger.debug(f"Reported failure for {module_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to report failure: {e}")
            return False
    
    def get_global_compatibility_list(self) -> Dict[str, Set[str]]:
        """
        Get global compatibility lists (allowlist/denylist).
        
        Returns:
            Dictionary with 'allowlist' and 'denylist' sets
        """
        try:
            # Get global configuration
            response = self.table.get_item(
                Key={
                    'pk': 'GLOBAL#CONFIG',
                    'sk': 'COMPATIBILITY#LISTS'
                }
            )
            
            if 'Item' in response:
                data = json.loads(response['Item']['data'])
                return {
                    'allowlist': set(data.get('allowlist', [])),
                    'denylist': set(data.get('denylist', []))
                }
            
            return {'allowlist': set(), 'denylist': set()}
            
        except Exception as e:
            logger.error(f"Failed to get global compatibility list: {e}")
            return {'allowlist': set(), 'denylist': set()}
    
    def update_global_lists(self, allowlist: Set[str], denylist: Set[str]) -> bool:
        """
        Update global compatibility lists (admin only).
        
        Args:
            allowlist: Set of allowed modules
            denylist: Set of denied modules
            
        Returns:
            True if successful
        """
        try:
            # Prepare item
            item = {
                'pk': 'GLOBAL#CONFIG',
                'sk': 'COMPATIBILITY#LISTS',
                'record_type': 'config',
                'timestamp': Decimal(str(time.time())),
                'data': json.dumps({
                    'allowlist': list(allowlist),
                    'denylist': list(denylist),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                })
            }
            
            # Put item
            self.table.put_item(Item=item)
            logger.info("Updated global compatibility lists")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update global lists: {e}")
            return False
    
    def batch_write_records(self, records: List[Dict[str, Any]]) -> bool:
        """
        Batch write multiple records.
        
        Args:
            records: List of records to write
            
        Returns:
            True if successful
        """
        try:
            with self.table.batch_writer() as batch:
                for record in records:
                    batch.put_item(Item=record)
            
            logger.debug(f"Batch wrote {len(records)} records")
            return True
            
        except Exception as e:
            logger.error(f"Failed to batch write records: {e}")
            return False
    
    def get_recent_updates(self, since_timestamp: float) -> List[Dict[str, Any]]:
        """
        Get recent compatibility updates.
        
        Args:
            since_timestamp: Unix timestamp to get updates since
            
        Returns:
            List of recent updates
        """
        try:
            # Query recent updates using GSI
            response = self.table.query(
                IndexName=self.GSI_TIMESTAMP,
                KeyConditionExpression=(
                    self.Key('record_type').eq('compatibility') &
                    self.Key('timestamp').gt(Decimal(str(since_timestamp)))
                ),
                Limit=100
            )
            
            updates = []
            for item in response['Items']:
                updates.append({
                    'module': item.get('module_name'),
                    'timestamp': float(item.get('timestamp', 0)),
                    'data': json.loads(item.get('data', '{}'))
                })
            
            return updates
            
        except Exception as e:
            logger.error(f"Failed to get recent updates: {e}")
            return []
    
    def validate_license(self, license_key: str) -> Dict[str, Any]:
        """
        Validate Epochly license (future implementation).
        
        Args:
            license_key: License key to validate
            
        Returns:
            License validation result
        """
        try:
            # Query license record
            response = self.table.get_item(
                Key={
                    'pk': f"LICENSE#{license_key}",
                    'sk': 'DETAILS'
                }
            )
            
            if 'Item' in response:
                data = json.loads(response['Item']['data'])
                
                # Check expiration
                if 'expires_at' in data:
                    expires = datetime.fromisoformat(data['expires_at'])
                    if expires < datetime.now(timezone.utc):
                        return {'valid': False, 'reason': 'expired'}
                
                return {
                    'valid': True,
                    'tier': data.get('tier', 'basic'),
                    'features': data.get('features', []),
                    'expires_at': data.get('expires_at')
                }
            
            return {'valid': False, 'reason': 'not_found'}
            
        except Exception as e:
            logger.error(f"Failed to validate license: {e}")
            return {'valid': False, 'reason': 'error'}
    
    def _get_user_id(self) -> Optional[str]:
        """Get user identifier for tracking"""
        # Try to get from environment
        user_id = os.environ.get('EPOCHLY_USER_ID')
        if user_id:
            return user_id
        
        # Try to get from license
        license_key = os.environ.get('EPOCHLY_LICENSE')
        if license_key:
            return hashlib.sha256(license_key.encode()).hexdigest()[:16]
        
        # Generate anonymous ID
        machine_id = f"{os.sys.platform}:{os.uname().nodename if hasattr(os, 'uname') else 'unknown'}"
        return hashlib.sha256(machine_id.encode()).hexdigest()[:16]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            # Get table item count (approximate)
            response = self.dynamodb_client.describe_table(TableName=self.table_name)
            
            return {
                'table_name': self.table_name,
                'item_count': response['Table']['ItemCount'],
                'table_size_bytes': response['Table']['TableSizeBytes'],
                'status': response['Table']['TableStatus']
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def table_exists(self) -> bool:
        """
        Check if the DynamoDB table exists.
        
        Returns:
            True if table exists, False otherwise
        """
        try:
            self.dynamodb_client.describe_table(TableName=self.table_name)
            return True
        except self.ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            raise
    
    def create_table(self) -> bool:
        """
        Create the DynamoDB table (wrapper method for compatibility).
        
        Returns:
            True if table created successfully, False if already exists or on error
        """
        try:
            # First check if table exists
            if self.table_exists():
                logger.debug(f"Table {self.table_name} already exists")
                return False
            
            self._create_table()
            return True
        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            return False
    
    def get_compatibility_records(self, module_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get compatibility records for a module.
        
        Args:
            module_name: Name of the module
            limit: Maximum number of records to return
            
        Returns:
            List of compatibility records
        """
        try:
            response = self.table.query(
                KeyConditionExpression=self.Key('pk').eq(f"MODULE#{module_name}"),
                ScanIndexForward=False,  # Sort descending by timestamp
                Limit=limit
            )
            
            records = []
            for item in response['Items']:
                data = json.loads(item['data'])
                data['module_name'] = module_name
                records.append(data)
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to get compatibility records: {e}")
            return []
    
    def put_community_data(self, community_data: Dict[str, Any]) -> bool:
        """
        Store community-wide compatibility data.
        
        Args:
            community_data: Community data dictionary
            
        Returns:
            True if successful
        """
        try:
            item = {
                'pk': 'COMMUNITY',
                'sk': f"DATA#{datetime.now(timezone.utc).isoformat()}",
                'record_type': 'community_data',
                'timestamp': Decimal(str(time.time())),
                'data': json.dumps(community_data),
                'ttl': int(time.time() + 30 * 24 * 3600)  # 30 days TTL
            }
            
            self.table.put_item(Item=item)
            logger.debug("Stored community data")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store community data: {e}")
            return False
    
    def get_community_data(self) -> Optional[Dict[str, Any]]:
        """
        Get latest community-wide compatibility data.
        
        Returns:
            Community data dictionary or None
        """
        try:
            response = self.table.query(
                KeyConditionExpression=self.Key('pk').eq('COMMUNITY'),
                ScanIndexForward=False,  # Sort descending by timestamp
                Limit=1
            )
            
            if response['Items']:
                item = response['Items'][0]
                return json.loads(item['data'])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get community data: {e}")
            return None
    
    def batch_get_modules(self, module_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Batch retrieve compatibility data for multiple modules.
        
        Args:
            module_names: List of module names
            
        Returns:
            Dictionary mapping module names to their compatibility data
        """
        try:
            # Build batch get requests
            keys = []
            for module_name in module_names:
                # Query for latest record of each module
                response = self.table.query(
                    KeyConditionExpression=self.Key('pk').eq(f"MODULE#{module_name}"),
                    ScanIndexForward=False,
                    Limit=1
                )
                
                if response['Items']:
                    keys.append({
                        'pk': f"MODULE#{module_name}",
                        'sk': response['Items'][0]['sk']
                    })
            
            if not keys:
                return {}
            
            # Batch get items
            response = self.dynamodb_client.batch_get_item(
                RequestItems={
                    self.table_name: {
                        'Keys': keys
                    }
                }
            )
            
            # Process results
            results = {}
            for item in response.get('Responses', {}).get(self.table_name, []):
                module_name = item['module_name']
                data = json.loads(item['data'])
                results[module_name] = data
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to batch get modules: {e}")
            return {}
    
    def scan_all_modules(self) -> List[Dict[str, Any]]:
        """
        Scan all modules in the table.
        
        Returns:
            List of all module records
        """
        try:
            modules = []
            last_evaluated_key = None
            
            while True:
                # Build scan parameters
                scan_params = {
                    'FilterExpression': self.Attr('record_type').eq('compatibility')
                }
                
                if last_evaluated_key:
                    scan_params['ExclusiveStartKey'] = last_evaluated_key
                
                response = self.table.scan(**scan_params)
                
                # Process items
                for item in response.get('Items', []):
                    data = json.loads(item['data'])
                    data['module_name'] = item.get('module_name')
                    modules.append(data)
                
                # Check if there are more items
                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break
            
            return modules
            
        except Exception as e:
            logger.error(f"Failed to scan modules: {e}")
            return []
    
    def delete_old_records(self, cutoff_date: datetime) -> int:
        """
        Delete records older than the specified cutoff date.
        
        Args:
            cutoff_date: Delete records older than this date
            
        Returns:
            Number of records deleted
        """
        try:
            cutoff_timestamp = cutoff_date.timestamp()
            
            # Query for old records
            response = self.table.query(
                IndexName=self.GSI_TIMESTAMP,
                KeyConditionExpression=(
                    self.Key('record_type').eq('compatibility') &
                    self.Key('timestamp').lt(Decimal(str(cutoff_timestamp)))
                )
            )
            
            if not response['Items']:
                return 0
            
            # Batch delete items
            with self.table.batch_writer() as batch:
                for item in response['Items']:
                    batch.delete_item(
                        Key={
                            'pk': item['pk'],
                            'sk': item['sk']
                        }
                    )
            
            deleted_count = len(response['Items'])
            logger.info(f"Deleted {deleted_count} old records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete old records: {e}")
            return 0
    
    def update_module_stats(self, module_name: str, 
                           increment_checks: bool = False,
                           increment_failures: bool = False) -> Dict[str, Any]:
        """
        Update statistics for a module.
        
        Args:
            module_name: Name of the module
            increment_checks: Increment check count
            increment_failures: Increment failure count
            
        Returns:
            Updated statistics
        """
        try:
            # Build update expression
            update_expression_parts = []
            expression_attribute_values = {}
            
            if increment_checks:
                update_expression_parts.append("check_count = check_count + :inc")
                expression_attribute_values[':inc'] = Decimal('1')
            
            if increment_failures:
                update_expression_parts.append("failure_count = failure_count + :inc")
                if ':inc' not in expression_attribute_values:
                    expression_attribute_values[':inc'] = Decimal('1')
            
            if not update_expression_parts:
                return {}
            
            update_expression = "ADD " + ", ".join(update_expression_parts)
            
            response = self.table.update_item(
                Key={
                    'pk': f"MODULE#{module_name}",
                    'sk': f"STATS#CURRENT"
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues='ALL_NEW'
            )
            
            return response.get('Attributes', {})
            
        except Exception as e:
            logger.error(f"Failed to update module stats: {e}")
            return {}
    
    def get_module_history(self, module_name: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get history of compatibility records for a module.
        
        Args:
            module_name: Name of the module
            days: Number of days of history to retrieve
            
        Returns:
            List of historical records sorted by timestamp (newest first)
        """
        try:
            # Calculate cutoff timestamp
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            cutoff_timestamp = cutoff_date.timestamp()
            
            # Query for records within time range
            response = self.table.query(
                KeyConditionExpression=self.Key('pk').eq(f"MODULE#{module_name}"),
                FilterExpression=self.Attr('timestamp').gte(Decimal(str(cutoff_timestamp))),
                ScanIndexForward=False  # Sort descending
            )
            
            history = []
            for item in response['Items']:
                data = json.loads(item['data'])
                # Add timestamp if available
                if 'timestamp' in item:
                    data['timestamp'] = float(item['timestamp'])
                history.append(data)
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get module history: {e}")
            return []