"""
AWS API Gateway telemetry client with secure node authentication.

Routes all telemetry through AWS API Gateway using node-based authentication
instead of AWS SigV4, following the Epochly licensing architecture.
"""

import os
import json
import time
import logging
from collections import deque
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Import the secure node auth
try:
    from epochly.compatibility.secure_node_auth import get_secure_auth
    NODE_AUTH_AVAILABLE = True
except ImportError:
    NODE_AUTH_AVAILABLE = False
    logger.warning("SecureNodeAuth not available - telemetry disabled")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not available - telemetry disabled")


class AWSSecureTelemetryClient:
    """
    Routes ALL telemetry through our AWS API Gateway using node authentication.
    No direct connections - everything goes through our secured API.
    
    Features:
    - Secure node-based authentication
    - Machine fingerprinting
    - Anti-tampering protection
    - API Gateway rate limiting compliance
    - Batch telemetry support
    """
    
    def __init__(self):
        # AWS API Gateway endpoint (configured via environment)
        self.api_endpoint = os.environ.get('EPOCHLY_API_ENDPOINT')

        if not self.api_endpoint:
            logger.warning("EPOCHLY_API_ENDPOINT not set - telemetry disabled")
            self.enabled = False
            return

        # CRITICAL: Disable in test mode to prevent CI hangs
        test_mode = os.environ.get('EPOCHLY_TEST_MODE', '0') == '1'
        offline_mode = os.environ.get('EPOCHLY_OFFLINE_MODE', '0') == '1'
        disable_telemetry = os.environ.get('EPOCHLY_DISABLE_TELEMETRY', '0') == '1'

        self.enabled = NODE_AUTH_AVAILABLE and REQUESTS_AVAILABLE and not (test_mode or offline_mode or disable_telemetry)

        # Test mode: ultra-fast timeouts to prevent hangs
        if test_mode:
            self.request_timeout = 0.1  # 100ms max
        else:
            self.request_timeout = 10.0  # 10s for production

        if self.enabled:
            # Initialize secure node authentication
            self.node_auth = get_secure_auth()

            # Batch queue for telemetry
            self.batch_queue = deque(maxlen=1000)
            self.batch_size = 50
            self.last_flush = time.time()

            # Stats tracking
            self.stats = {
                'sent': 0,
                'errors': 0,
                'batches': 0
            }
        else:
            self.node_auth = None
            self.batch_queue = None
    
    def send_telemetry(self, metrics: dict):
        """
        Send telemetry through our API Gateway with node authentication.
        All data is validated and secured at the API layer.
        """
        if not self.enabled:
            return
        
        try:
            # Add to batch queue
            self.batch_queue.append(metrics)
            
            # Flush if batch is full
            if len(self.batch_queue) >= self.batch_size:
                self.flush_batch()
                
        except Exception as e:
            logger.error(f"Failed to queue telemetry: {e}")
            self.stats['errors'] += 1

    def send_critical_event(self, event_type: str, event_data: dict):
        """
        Send critical event immediately without batching.
        Critical events are sent synchronously for immediate processing.

        Args:
            event_type: Type of critical event (e.g., 'segfault', 'crash')
            event_data: Event details

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Prepare critical event payload
            payload = {
                'event_type': event_type,
                'event_data': event_data,
                'timestamp': time.time(),
                'node_fingerprint': self.node_auth.machine_fingerprint if self.node_auth else None,
                'priority': 'CRITICAL'
            }

            # Prepare endpoint for critical events
            endpoint = f"{self.api_endpoint}/telemetry/critical"

            # Generate authentication headers
            auth_headers = self.node_auth.generate_auth_headers(payload)

            # Merge headers
            headers = {
                'Content-Type': 'application/json',
                **auth_headers
            }

            # Send immediately without batching
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.request_timeout
            )

            if response.status_code in (200, 202):
                self.stats['sent'] += 1
                return True
            else:
                logger.warning(f"Critical event API error: {response.status_code}")
                self.stats['errors'] += 1
                return False

        except Exception as e:
            logger.error(f"Failed to send critical event: {e}")
            self.stats['errors'] += 1
            return False

    def flush_batch(self):
        """Flush the batch queue to API Gateway."""
        if not self.enabled or not self.batch_queue:
            return
        
        try:
            # Prepare batch
            batch = []
            while self.batch_queue and len(batch) < self.batch_size:
                batch.append(self.batch_queue.popleft())
            
            if not batch:
                return
            
            # Prepare request data
            endpoint = f"{self.api_endpoint}/telemetry/metrics"
            
            if len(batch) == 1:
                # Single record
                payload = batch[0]
            else:
                # Batch records
                payload = {'batch': batch}
            
            # Generate authentication headers
            auth_headers = self.node_auth.generate_auth_headers(payload)
            
            # Merge headers
            headers = {
                'Content-Type': 'application/json',
                **auth_headers
            }
            
            # Send request
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                self.stats['sent'] += len(batch)
                self.stats['batches'] += 1
                logger.debug(f"Sent {len(batch)} telemetry records")
            else:
                # Handle errors
                logger.warning(f"API error: {response.status_code}")
                self.stats['errors'] += 1
                
                # Put batch back in queue for retry
                for item in reversed(batch):
                    self.batch_queue.appendleft(item)
                    
        except Exception as e:
            logger.error(f"Failed to send telemetry batch: {e}")
            self.stats['errors'] += 1
    
    def report_compatibility(self, module_name: str, decision: dict):
        """
        Report module compatibility decision.
        
        Args:
            module_name: Name of the module
            decision: Compatibility decision with use_subinterpreter, confidence, etc.
        """
        if not self.enabled:
            return
        
        try:
            endpoint = f"{self.api_endpoint}/report"
            
            payload = {
                'module': module_name,
                'timestamp': time.time(),
                'decision': decision
            }
            
            # Generate authentication headers
            auth_headers = self.node_auth.generate_auth_headers(payload)
            
            # Merge headers
            headers = {
                'Content-Type': 'application/json',
                **auth_headers
            }
            
            # Send request
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.request_timeout
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to report compatibility: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to report compatibility: {e}")
    
    def sync_compatibility_data(self) -> Optional[Dict[str, Any]]:
        """
        Sync compatibility data from cloud.
        
        Returns:
            Dictionary of compatibility updates or None if failed
        """
        if not self.enabled:
            return None
        
        try:
            endpoint = f"{self.api_endpoint}/sync"
            
            # For GET requests, we still need to authenticate
            request_data = {'timestamp': time.time()}
            auth_headers = self.node_auth.generate_auth_headers(request_data)
            
            # Send request
            response = requests.get(
                endpoint,
                headers=auth_headers,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to sync data: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to sync compatibility data: {e}")
            return None
    
    def get_stats(self) -> Dict[str, int]:
        """Get telemetry statistics."""
        if not self.enabled:
            return {'sent': 0, 'errors': 0, 'batches': 0}
        return self.stats.copy()
    
    def shutdown(self):
        """Shutdown the client and flush any remaining data."""
        if self.enabled:
            self.flush_batch()
            logger.info(f"Telemetry client shutdown - sent: {self.stats['sent']}, errors: {self.stats['errors']}")


# Global instance for convenience
_global_client = None


def get_telemetry_client() -> AWSSecureTelemetryClient:
    """Get global telemetry client instance."""
    global _global_client
    if _global_client is None:
        _global_client = AWSSecureTelemetryClient()
    return _global_client