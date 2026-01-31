"""
Trial system with email verification for Epochly.

Implements strict one-email-one-machine trial policy with AWS SES integration.
"""

import json
import secrets
import boto3
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from decimal import Decimal

# Custom JSON encoder for Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

# Initialize AWS services
if os.environ.get('EPOCHLY_TEST_MODE') != '1':
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    ses_client = boto3.client('ses', region_name='us-west-2')
    
    # DynamoDB tables
    licenses_table = dynamodb.Table('epochly-active-licenses')
    trials_table = dynamodb.Table('epochly-trial-registry')
    verifications_table = dynamodb.Table('epochly-email-verifications')
else:
    # For testing
    dynamodb = None
    ses_client = None
    licenses_table = None
    trials_table = None
    verifications_table = None

# Test mode for unit tests
TEST_MODE = os.environ.get('EPOCHLY_TEST_MODE') == '1'


class TrialPolicy:
    """Enforces the one-email-one-machine trial policy."""
    
    def __init__(self):
        self._email_registry = {}
        self._machine_registry = {}
    
    def can_use_email(self, email: str) -> bool:
        """Check if email has been used for a trial."""
        if TEST_MODE:
            return email not in self._email_registry
        
        # Check DynamoDB
        response = trials_table.get_item(Key={'email': email})
        return 'Item' not in response
    
    def can_use_machine(self, machine_fingerprint: str) -> bool:
        """Check if machine has already had a trial."""
        if TEST_MODE:
            return machine_fingerprint not in self._machine_registry
        
        # Check in licenses table
        response = licenses_table.get_item(
            Key={'machine_fingerprint': machine_fingerprint}
        )
        return not (response.get('Item', {}).get('had_trial', False))
    
    def mark_email_used(self, email: str, machine_fingerprint: str):
        """Mark email as used for a trial on specific machine."""
        if TEST_MODE:
            self._email_registry[email] = machine_fingerprint
        else:
            trials_table.put_item(
                Item={
                    'email': email,
                    'machine_fingerprint': machine_fingerprint,
                    'registered_at': datetime.now(timezone.utc).isoformat(),
                    'had_trial': True
                }
            )
    
    def mark_machine_used(self, machine_fingerprint: str, email: str):
        """Mark machine as having used its trial."""
        if TEST_MODE:
            self._machine_registry[machine_fingerprint] = email
        else:
            # Update licenses table to mark had_trial
            licenses_table.update_item(
                Key={'machine_fingerprint': machine_fingerprint},
                UpdateExpression='SET had_trial = :true',
                ExpressionAttributeValues={':true': True}
            )
    
    def check_eligibility(self, email: str, machine_fingerprint: str) -> Dict[str, Any]:
        """Check if email/machine combination is eligible for trial."""
        # Check machine first
        if not self.can_use_machine(machine_fingerprint):
            return {
                'eligible': False,
                'reason': 'machine_already_had_trial'
            }
        
        # Check if email was used
        if not self.can_use_email(email):
            # Get which machine used this email
            if TEST_MODE:
                used_machine = self._email_registry.get(email)
            else:
                response = trials_table.get_item(Key={'email': email})
                used_machine = response.get('Item', {}).get('machine_fingerprint')
            
            if used_machine != machine_fingerprint:
                return {
                    'eligible': False,
                    'reason': 'email_already_used_different_machine'
                }
            else:
                return {
                    'eligible': False,
                    'reason': 'trial_already_active'
                }
        
        return {'eligible': True}


def request_trial_handler(event, context):
    """
    AWS Lambda handler for trial activation requests.
    Enforces strict one-email-one-machine policy.
    """
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        machine_fingerprint = body.get('machine_fingerprint')
        
        if not email or not machine_fingerprint:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'missing_parameters',
                    'message': 'Email and machine fingerprint are required'
                }, cls=DecimalEncoder)
            }
        
        # Check eligibility
        policy = TrialPolicy()
        eligibility = policy.check_eligibility(email, machine_fingerprint)
        
        if not eligibility['eligible']:
            reason = eligibility['reason']
            
            if reason == 'machine_already_had_trial':
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'trial_already_used_machine',
                        'message': 'This machine has already used its one-time trial',
                        'suggestion': 'Purchase a license at https://epochly.com/pricing'
                    }, cls=DecimalEncoder)
                }
            
            elif reason == 'email_already_used_different_machine':
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'trial_email_already_used',
                        'message': f'The email \'{email}\' has already been used for a trial on another machine',
                        'details': 'Each email address can only be used for one trial, on one machine',
                        'suggestion': 'Use a different email or purchase a license at https://epochly.com/pricing'
                    }, cls=DecimalEncoder)
                }
            
            else:  # trial_already_active
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'trial_already_active',
                        'message': 'Trial already associated with this email and machine',
                        'suggestion': 'Check your license status with: epochly status'
                    }, cls=DecimalEncoder)
                }
        
        # Generate verification token
        token = secrets.token_urlsafe(32)
        
        # Store pending verification (24-hour expiry)
        if not TEST_MODE:
            verifications_table.put_item(
                Item={
                    'token': token,
                    'email': email,
                    'machine_fingerprint': machine_fingerprint,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'expires_at': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
                    'verified': False
                }
            )
        
        # Send verification email
        if not TEST_MODE:
            ses_client.send_email(
                Source='hello@epochly.com',
                Destination={'ToAddresses': [email]},
                Message={
                    'Subject': {'Data': 'Activate Your Epochly 30-Day Trial'},
                    'Body': {
                        'Html': {'Data': create_trial_activation_email(token, email)}
                    }
                }
            )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Verification email sent',
                'email': email,
                'expires_in': '24 hours',
                'note': 'This email can only be used for one trial on one machine'
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error in request_trial_handler: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'}, cls=DecimalEncoder)
        }


def verify_trial_handler(event, context):
    """
    AWS Lambda handler for email verification and trial activation.
    """
    try:
        body = json.loads(event.get('body', '{}'))
        token = body.get('token')
        
        if not token:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'missing_token',
                    'message': 'Verification token is required'
                }, cls=DecimalEncoder)
            }
        
        # Get verification record
        response = verifications_table.get_item(Key={'token': token})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'invalid_token',
                    'message': 'Invalid verification token'
                }, cls=DecimalEncoder)
            }
        
        verification = response['Item']
        
        # Check if already verified
        if verification.get('verified'):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'already_verified',
                    'message': 'This token has already been used'
                }, cls=DecimalEncoder)
            }
        
        # Check expiration
        expires_at = datetime.fromisoformat(verification['expires_at'])
        if expires_at < datetime.now(timezone.utc):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'token_expired',
                    'message': 'Verification token has expired. Please request a new trial.'
                }, cls=DecimalEncoder)
            }
        
        email = verification['email']
        machine_fingerprint = verification['machine_fingerprint']
        
        # Activate trial
        trial_start = datetime.now(timezone.utc)
        trial_end = trial_start + timedelta(days=30)
        
        # Register trial in registry (permanent record)
        trials_table.put_item(
            Item={
                'email': email,
                'machine_fingerprint': machine_fingerprint,
                'activated_at': trial_start.isoformat(),
                'expires_at': trial_end.isoformat(),
                'had_trial': True,
                'status': 'active'
            }
        )
        
        # Activate license
        licenses_table.put_item(
            Item={
                'machine_fingerprint': machine_fingerprint,
                'email': email,
                'tier_name': 'trial',
                'status': 'active',
                'activated_at': trial_start.isoformat(),
                'expires_at': trial_end.isoformat(),
                'had_trial': True
            }
        )
        
        # Mark verification as used
        verifications_table.update_item(
            Key={'token': token},
            UpdateExpression='SET verified = :true',
            ExpressionAttributeValues={':true': True}
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'trial_activated',
                'tier': 'trial',
                'email': email,
                'duration_days': 30,
                'expires_at': trial_end.isoformat(),
                'message': 'Your 30-day trial is now active with all CPU cores enabled!'
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error in verify_trial_handler: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'}, cls=DecimalEncoder)
        }


def check_trial_reminders_handler(event, context):
    """
    AWS Lambda handler for sending trial reminder emails.
    Runs daily via CloudWatch Events.
    """
    try:
        # Get all active trials
        if TEST_MODE:
            # In test mode, return a minimal response
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'reminders_sent': 1,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }, cls=DecimalEncoder)
            }
        
        response = licenses_table.scan(
            FilterExpression='tier_name = :trial AND #s = :active',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':trial': 'trial',
                ':active': 'active'
            }
        )
        
        reminders_sent = 0
        
        for trial in response.get('Items', []):
            email = trial.get('email')
            expires_at = trial.get('expires_at')
            
            if not email or not expires_at:
                continue
            
            # Calculate days remaining
            expiry_date = datetime.fromisoformat(expires_at)
            now = datetime.now(timezone.utc)
            days_remaining = (expiry_date - now).days
            
            # Send reminders at specific intervals
            if days_remaining in [15, 7, 1, 0]:
                send_trial_reminder(email, days_remaining)
                reminders_sent += 1
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'reminders_sent': reminders_sent,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error in check_trial_reminders_handler: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'}, cls=DecimalEncoder)
        }


def send_trial_reminder(email: str, days_remaining: int):
    """Send trial reminder email based on days remaining."""
    if TEST_MODE:
        # In test mode, just track the call
        return
    
    subject = get_reminder_subject(days_remaining)
    html_body = create_reminder_email(days_remaining)
    
    ses_client.send_email(
        Source='hello@epochly.com',
        Destination={'ToAddresses': [email]},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Html': {'Data': html_body}}
        }
    )


def get_reminder_subject(days_remaining: int) -> str:
    """Get email subject based on days remaining."""
    if days_remaining == 15:
        return "Your Epochly trial: 15 days remaining"
    elif days_remaining == 7:
        return "One week left in your Epochly trial"
    elif days_remaining == 1:
        return "Last day of your Epochly trial"
    elif days_remaining == 0:
        return "Your Epochly trial has ended"
    else:
        return f"Your Epochly trial: {days_remaining} days remaining"


def create_trial_activation_email(token: str, email: str) -> str:
    """Create HTML email template for trial activation."""
    import os
    cpu_count = os.cpu_count() or 8
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .warning {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .button {{ 
            display: inline-block;
            background: #007bff; 
            color: white; 
            padding: 12px 24px; 
            text-decoration: none; 
            border-radius: 5px;
            margin: 20px 0;
        }}
        .code {{ 
            background: #f4f4f4; 
            padding: 10px; 
            border-radius: 3px; 
            font-family: monospace;
            margin: 10px 0;
        }}
        ul {{ margin: 10px 0; padding-left: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Activate Your Epochly 30-Day Trial</h2>
        
        <p>Hi there!</p>
        
        <p>You're one click away from unlocking all CPU cores on your machine for 30 days.</p>
        
        <div class="warning">
            <strong>⚠️ Important Trial Information:</strong>
            <ul>
                <li>This email ({email}) can only be used for ONE trial</li>
                <li>This trial is locked to your current machine</li>
                <li>You cannot use this email for trials on other machines</li>
                <li>After 30 days, you'll return to Community Edition (4 cores)</li>
            </ul>
        </div>
        
        <p><strong>Your Trial Benefits:</strong></p>
        <ul>
            <li>✅ All CPU cores enabled (your machine has {cpu_count} cores)</li>
            <li>✅ Advanced JIT compilation at full capacity</li>
            <li>✅ Maximum parallel execution</li>
            <li>✅ 30 days of unlimited performance</li>
        </ul>
        
        <p style="text-align: center;">
            <a href="https://epochly.com/verify?token={token}" class="button">
                Activate My One-Time Trial
            </a>
        </p>
        
        <p>Or activate via CLI:</p>
        <div class="code">epochly verify --token {token}</div>
        
        <p><small>This verification link expires in 24 hours.</small></p>
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
        
        <p style="font-size: 14px; color: #666;">
            Questions? Contact us at support@epochly.com<br>
            Ready to purchase? Visit <a href="https://epochly.com/pricing">epochly.com/pricing</a>
        </p>
    </div>
</body>
</html>
"""


def create_reminder_email(days_remaining: int) -> str:
    """Create HTML email template for trial reminders."""
    if days_remaining == 15:
        message = "You're halfway through your trial. Here's what you've achieved so far..."
        urgency = "info"
    elif days_remaining == 7:
        message = "Your trial ends in one week. Don't lose access to all your CPU cores..."
        urgency = "warning"
    elif days_remaining == 1:
        message = "Tomorrow you'll be limited to 4 cores. Upgrade now to keep full access..."
        urgency = "urgent"
    elif days_remaining == 0:
        message = "Your trial has ended. You're now on Community Edition (4 cores)."
        urgency = "expired"
    else:
        message = f"You have {days_remaining} days left in your trial."
        urgency = "info"
    
    urgency_color = {
        'info': '#17a2b8',
        'warning': '#ffc107', 
        'urgent': '#dc3545',
        'expired': '#6c757d'
    }.get(urgency, '#17a2b8')
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {urgency_color}; color: white; padding: 20px; border-radius: 5px; }}
        .button {{ 
            display: inline-block;
            background: #28a745; 
            color: white; 
            padding: 12px 24px; 
            text-decoration: none; 
            border-radius: 5px;
            margin: 20px 0;
        }}
        .metrics {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>{"Your Epochly trial: 15 days remaining" if days_remaining == 15 else 
                 "One week left in your Epochly trial" if days_remaining == 7 else
                 "Last day of your Epochly trial" if days_remaining == 1 else
                 "Your Epochly trial has ended"}</h2>
        </div>
        
        <p>{message}</p>
        
        {"<p>You're halfway through your trial and making great progress!</p>" if days_remaining == 15 else ""}
        
        <div class="metrics">
            <strong>Your Trial Status:</strong>
            <ul>
                <li>Days Remaining: {days_remaining if days_remaining > 0 else "Expired"}</li>
                <li>Current Tier: {"Trial (All Cores)" if days_remaining > 0 else "Community Edition (4 cores)"}</li>
                <li>Available Cores: {"All cores on your machine" if days_remaining > 0 else "4 cores maximum"}</li>
            </ul>
        </div>
        
        {f'''<p style="text-align: center;">
            <a href="https://epochly.com/pricing" class="button">
                {"Keep Your Performance" if days_remaining > 0 else "Upgrade Now"}
            </a>
        </p>''' if days_remaining <= 7 else ''}
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
        
        <p style="font-size: 14px; color: #666;">
            Visit <a href="https://epochly.com/pricing">epochly.com/pricing</a> for pricing options<br>
            Questions? Contact support@epochly.com
        </p>
    </div>
</body>
</html>
"""