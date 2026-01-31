"""
CLI commands for trial management in Epochly.

Provides commands for requesting and verifying trial licenses.
"""

import os
import sys
import click
import requests
import json
import logging
from typing import Optional, Tuple
import re

from epochly.config.api_endpoints import APIEndpoints

# Module logger for debugging
logger = logging.getLogger(__name__)


def get_api_timeout() -> int:
    """Get configurable API timeout from environment (default: 10 seconds)."""
    try:
        return int(os.environ.get('EPOCHLY_API_TIMEOUT', '10'))
    except ValueError:
        return 10


def safe_json_parse(response: requests.Response) -> Optional[dict]:
    """
    Safely parse JSON from response, returning None if parsing fails.

    Handles cases where server returns HTML (proxy, WAF, CDN error pages)
    instead of expected JSON. Also handles cases where JSON is valid but
    not a dict (e.g., list or string).
    """
    try:
        data = response.json()
    except (ValueError, json.JSONDecodeError):
        return None
    # Ensure we return a dict (response.json() can return list, str, etc.)
    return data if isinstance(data, dict) else None


def get_api_base_url() -> str:
    """
    Get API base URL with automatic fallback.

    Respects EPOCHLY_API_URL environment variable override.
    Tries the configured URL first, falls back to direct AWS endpoint if needed.
    Uses a short probe timeout (3s) to quickly detect unavailable servers.
    """
    # Use BASE_URL which respects EPOCHLY_API_URL env var override
    primary_url = APIEndpoints.BASE_URL

    # Use shorter timeout for probe (3s) - we want quick fallback
    probe_timeout = min(3, get_api_timeout())

    # Try primary URL
    try:
        response = requests.head(
            f"{primary_url}/trial/activate",
            timeout=probe_timeout
        )
        if response.status_code < 500:
            return primary_url
    except (requests.exceptions.RequestException, OSError) as e:
        logger.debug("Primary API probe failed: %s", e)

    # Use fallback
    logger.debug("Using fallback API URL: %s", APIEndpoints.FALLBACK_BASE_URL)
    return APIEndpoints.FALLBACK_BASE_URL


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@click.command()
@click.option('--email', required=True, help='Email for one-time trial activation')
def trial(email: str) -> int:
    """
    Request a 30-day trial with email verification.

    IMPORTANT: Each email address can only be used ONCE for a trial,
    and only on ONE machine. Choose your email carefully.

    Returns: 0 on success, 1 on error
    """

    # Show clear policy information
    click.echo("[Epochly] Trial Policy:")
    click.echo("[Epochly]   - One trial per email address (lifetime)")
    click.echo("[Epochly]   - One trial per machine (lifetime)")
    click.echo("[Epochly]   - This email cannot be used on other machines")
    click.echo("[Epochly]   - 30 days with ALL CPU cores enabled")
    click.echo("")

    # Confirm with user
    if not click.confirm("[Epochly] Do you want to use this email for your one-time trial?"):
        click.echo("[Epochly] Trial request cancelled")
        return 1  # User cancelled

    # Validate email format
    if not validate_email(email):
        click.echo("[Epochly] Error: Invalid email format")
        click.echo("[Epochly] Please provide a valid email address")
        return 1

    # Get machine fingerprint
    try:
        from epochly.compatibility.secure_node_auth import MachineFingerprint
        fingerprint = MachineFingerprint.generate()
    except Exception as e:
        logger.debug("Machine fingerprint generation failed", exc_info=True)
        click.echo(f"[Epochly] Error generating machine fingerprint: {e}")
        click.echo("[Epochly] Please ensure Epochly is properly installed")
        return 1

    # Show what we're doing
    click.echo(f"[Epochly] Requesting trial for: {email}")
    click.echo("[Epochly] Machine fingerprint generated")

    # Request trial via API
    try:
        api_base = get_api_base_url()
        response = requests.post(
            f'{api_base}/trial/activate',
            json={
                'email': email,
                'machine_id': fingerprint
            },
            timeout=get_api_timeout()
        )

        if response.status_code == 200:
            click.echo("")
            click.echo(f"[Epochly] Verification email sent to {email}")
            click.echo("[Epochly] Check your email to activate your one-time trial")
            click.echo("[Epochly] ")
            click.echo("[Epochly] Next steps:")
            click.echo("[Epochly]   1. Open the activation email")
            click.echo("[Epochly]   2. Click the activation link OR")
            click.echo("[Epochly]   3. Run: epochly verify --token <token-from-email>")
            click.echo("")
            click.echo("[Epochly] Remember: This email cannot be used for trials on other machines")
            return 0  # Success

        elif response.status_code == 403:
            error_data = safe_json_parse(response)
            error_type = error_data.get('error') if error_data else None

            click.echo("")
            if error_type == 'trial_already_used_machine':
                click.echo("[Epochly] This machine has already used its one-time trial")
                click.echo("[Epochly] ")
                click.echo("[Epochly] To unlock all cores, purchase a license:")
                click.echo("[Epochly]   - Instance: $16/month per machine")
                click.echo("[Epochly]   - Site: Custom pricing for teams")
                click.echo("[Epochly] ")
                click.echo("[Epochly] Visit: https://epochly.com/pricing")

            elif error_type == 'trial_email_already_used':
                click.echo(f"[Epochly] The email '{email}' has already been used for a trial")
                click.echo("[Epochly] ")
                click.echo("[Epochly] Each email can only be used once, on one machine.")
                click.echo("[Epochly] Options:")
                click.echo("[Epochly]   - Use a different email address")
                click.echo("[Epochly]   - Purchase a license at https://epochly.com/pricing")
            else:
                click.echo("[Epochly] Trial request was denied.")

            return 1  # Forbidden error

        elif response.status_code == 400:
            error_data = safe_json_parse(response)
            click.echo("")
            if error_data:
                click.echo(f"[Epochly] Error: {error_data.get('message', 'Invalid request')}")
            else:
                click.echo("[Epochly] Error: Invalid request")
            return 1

        else:
            click.echo("")
            click.echo("[Epochly] Error requesting trial. Please try again later.")
            click.echo(f"[Epochly] Status: {response.status_code}")
            return 1

    except requests.exceptions.Timeout:
        logger.debug("Trial request timed out", exc_info=True)
        click.echo("")
        click.echo("[Epochly] Request timed out. Please check your internet connection.")
        return 1
    except requests.exceptions.ConnectionError:
        logger.debug("Trial request connection error", exc_info=True)
        click.echo("")
        click.echo("[Epochly] Cannot connect to Epochly servers.")
        click.echo("[Epochly] Please check your internet connection.")
        return 1
    except Exception as e:
        logger.debug("Trial request unexpected error", exc_info=True)
        click.echo("")
        click.echo(f"[Epochly] Unexpected error: {e}")
        click.echo("[Epochly] Please report this issue at https://github.com/epochly/epochly/issues")
        return 1


@click.command()
@click.option('--token', required=True, help='Activation token from email')
def activate(token: str) -> int:
    """
    Activate your 30-day trial using the token from your email.

    Returns: 0 on success, 1 on error
    """

    click.echo("[Epochly] Activating trial with token...")

    try:
        # Use the magic link confirmation endpoint with token
        # Use params= for proper URL encoding of token
        api_base = get_api_base_url()
        response = requests.get(
            f'{api_base}/trial/confirm',
            params={'token': token},
            headers={'Accept': 'application/json'},
            timeout=get_api_timeout()
        )

        if response.status_code == 200:
            data = response.json()
            cpu_count = os.cpu_count() or 8

            click.echo("")
            click.echo("[Epochly] Trial activated successfully!")
            click.echo("[Epochly] ")
            click.echo(f"[Epochly] Duration: {data.get('days_remaining', 30)} days")
            click.echo(f"[Epochly] CPU Cores: ALL {cpu_count} cores enabled")
            click.echo("[Epochly] ")
            click.echo("[Epochly] Your trial benefits:")
            click.echo("[Epochly]   - Unlimited CPU cores")
            click.echo("[Epochly]   - Advanced JIT compilation")
            click.echo("[Epochly]   - Maximum parallel execution")
            click.echo("[Epochly] ")
            click.echo("[Epochly] Trial reminders will be sent at 15, 7, and 1 day remaining")
            click.echo("[Epochly] ")
            click.echo("[Epochly] To check your trial status anytime:")
            click.echo("[Epochly]   epochly status")
            return 0  # Success

        elif response.status_code == 400:
            error_data = safe_json_parse(response)
            error = error_data.get('error') if error_data else None

            click.echo("")
            if error == 'token_expired':
                click.echo("[Epochly] Verification token has expired (24 hour limit)")
                click.echo("[Epochly] Please request a new trial: epochly trial --email")
            elif error == 'already_activated':
                click.echo("[Epochly] Trial already activated")
                days = error_data.get('days_remaining', 0) if error_data else 0
                click.echo(f"[Epochly] You have {days} days remaining")
                click.echo("[Epochly] Check your trial status: epochly status")
                return 0  # Already activated is not an error for the user
            else:
                msg = error_data.get('message', 'Invalid token') if error_data else 'Invalid token'
                click.echo(f"[Epochly] Error: {msg}")
            return 1

        elif response.status_code == 404:
            click.echo("")
            click.echo("[Epochly] Invalid verification token")
            click.echo("[Epochly] Please check the token from your email and try again")
            return 1

        else:
            click.echo("")
            click.echo("[Epochly] Error verifying trial. Please try again later.")
            return 1

    except requests.exceptions.Timeout:
        logger.debug("Verify request timed out", exc_info=True)
        click.echo("")
        click.echo("[Epochly] Request timed out. Please check your internet connection.")
        return 1
    except requests.exceptions.ConnectionError:
        logger.debug("Verify request connection error", exc_info=True)
        click.echo("")
        click.echo("[Epochly] Cannot connect to Epochly servers.")
        click.echo("[Epochly] Please check your internet connection.")
        return 1
    except Exception as e:
        logger.debug("Verify request unexpected error", exc_info=True)
        click.echo("")
        click.echo(f"[Epochly] Unexpected error: {e}")
        return 1


@click.command()
def status() -> int:
    """
    Check your current Epochly license and trial status.

    Returns: 0 on success, 1 on error
    """

    try:
        from epochly.licensing.license_enforcer import get_license_enforcer

        enforcer = get_license_enforcer()
        limits = enforcer.get_limits()

        click.echo("[Epochly] License Status")
        click.echo("-" * 50)

        tier = limits['tier'].upper()
        if tier == 'COMMUNITY':
            tier_display = "Community Edition (Free Forever)"
        elif tier == 'TRIAL':
            tier_display = "Trial (30 Days)"
        else:
            tier_display = tier.title()

        click.echo(f"Tier: {tier_display}")

        # Core information
        max_cores = limits.get('max_cores')
        total_cores = os.cpu_count() or 8
        if max_cores:
            click.echo(f"CPU Cores: {max_cores} of {total_cores} available")
        else:
            click.echo(f"CPU Cores: All {total_cores} cores enabled")

        # GPU information
        gpu_enabled = limits.get('gpu_enabled', False)
        click.echo(f"GPU Acceleration: {'Enabled' if gpu_enabled else 'Not Available'}")

        # Features
        features = limits.get('features', [])
        if features:
            click.echo(f"Features: {', '.join(features[:3])}")

        # Trial-specific information
        if limits['tier'] == 'trial':
            try:
                # Get trial expiration info
                license_data = enforcer._license_data
                if license_data:
                    expires_at = license_data.get('expires_at')
                    if expires_at:
                        from datetime import datetime, timezone
                        expiry = datetime.fromisoformat(expires_at)
                        now = datetime.now(timezone.utc)
                        days_remaining = max(0, (expiry - now).days)

                        click.echo("")
                        click.echo(f"Trial Days Remaining: {days_remaining}")

                        if days_remaining <= 7:
                            click.echo("")
                            click.echo(f"WARNING: Trial expires in {days_remaining} days!")
                            click.echo("After expiration: Limited to 4 cores (Community Edition)")
                            click.echo("Maintain full access: https://epochly.com/pricing")
            except Exception as e:
                logger.debug("Failed to get trial expiration info", exc_info=True)

        # Community tier with trial eligibility
        elif limits['tier'] == 'community':
            had_trial = enforcer.had_trial()

            click.echo("")
            if had_trial:
                click.echo("Trial Status: Already used (one-time only)")
                click.echo("")
                click.echo("Unlock all cores with a paid license:")
                click.echo("  - Instance: $16/month per machine")
                click.echo("  - Site: Custom pricing for teams")
                click.echo("  - Visit: https://epochly.com/pricing")
            else:
                click.echo("Trial Status: Available")
                click.echo("")
                click.echo(f"You're using {max_cores} of {total_cores} available cores")
                click.echo("Get a 30-day trial with ALL cores enabled:")
                click.echo("  epochly trial --email your@email.com")
                click.echo("")
                click.echo("Note: Each email can only be used once, on one machine")

        return 0  # Success

    except Exception as e:
        logger.debug("Status check failed", exc_info=True)
        click.echo(f"[Epochly] Error checking status: {e}")
        click.echo("[Epochly] Please ensure Epochly is properly installed")
        return 1


# Alias for CLI compatibility - CLI imports 'verify' but function is 'activate'
verify = activate

# Export commands for CLI registration
__all__ = ['trial', 'activate', 'verify', 'status']