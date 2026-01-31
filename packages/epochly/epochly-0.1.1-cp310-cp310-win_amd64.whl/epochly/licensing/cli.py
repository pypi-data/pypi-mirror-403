"""
Epochly Licensing CLI

Command-line interface for Epochly licensing management.
Provides license activation, validation, status commands, and
developer token management for local development.

Author: Epochly Development Team
"""

import argparse
import asyncio
import base64
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from .license_manager import LicenseManager, LicenseError
from .license_validator import LicenseValidator, ValidationError
from .dev_token_validator import (
    DevTokenValidator,
    DevTokenValidationResult,
    ValidationReason,
    get_dev_token_validator,
)
from ..utils.logging_bootstrap import setup_logging

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


# Dev token constants
DEV_KEY_DIR = Path.home() / '.epochly' / 'keys'
DEV_PRIVATE_KEY_PATH = DEV_KEY_DIR / 'dev-signing-key.pem'
DEV_PUBLIC_KEY_PATH = DEV_KEY_DIR / 'dev-signing-key.pub'
DEFAULT_TOKEN_PATH = Path.home() / '.epochly' / 'dev-token.json'
VALID_TIERS = ['developer', 'enterprise-dev', 'ci-cd']
VALID_ENVIRONMENTS = ['development', 'testing', 'ci']
DEFAULT_FEATURES = ['level_0', 'level_1', 'level_2', 'level_3', 'level_4', 'gpu']
MAX_TOKEN_LIFETIME_DAYS = 90
REQUIRED_ISSUER = 'api.epochly.com'


class LicensingCLI:
    """
    Command-line interface for Epochly licensing operations.
    
    Provides commands for license management including activation,
    validation, status checking, and deactivation.
    """
    
    def __init__(self):
        """Initialize the licensing CLI."""
        self.license_manager = LicenseManager()
        self.license_validator = LicenseValidator()
        self.logger = logging.getLogger(__name__)
    
    async def activate(self, license_key: str) -> int:
        """
        Activate a license with the given key.
        
        Args:
            license_key: The license key to activate
            
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            print(f"Activating license: {license_key[:8]}...")
            
            # Validate license format first
            if not self.license_validator.validate_format(license_key):
                print("Error: Invalid license key format")
                return 1
            
            # Validate license signature
            if not self.license_validator.validate_signature(license_key):
                print("Error: Invalid license signature")
                return 1
            
            # Validate expiry
            if not self.license_validator.validate_expiry(license_key):
                print("Error: License has expired")
                return 1
            
            # Activate the license
            if self.license_manager.activate_license(license_key):
                print("License activated successfully!")
                
                # Show license info
                info = self.license_validator.get_license_info(license_key)
                if info:
                    print(f"License Type: {info['license_type']}")
                    print(f"Features: {', '.join(info['features'])}")
                    if info['expiry_date']:
                        print(f"Expires: {info['expiry_date']}")
                    else:
                        print("Expires: Never")
                
                return 0
            else:
                print("Error: Failed to activate license")
                return 1
                
        except (LicenseError, ValidationError) as e:
            print(f"License error: {e}")
            return 1
        except Exception as e:
            self.logger.error(f"Unexpected error during activation: {e}")
            print(f"Error: {e}")
            return 1
    
    async def deactivate(self) -> int:
        """
        Deactivate the current license.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            print("Deactivating license...")
            
            if self.license_manager.deactivate_license():
                print("License deactivated successfully!")
                return 0
            else:
                print("Error: Failed to deactivate license")
                return 1
                
        except LicenseError as e:
            print(f"License error: {e}")
            return 1
        except Exception as e:
            self.logger.error(f"Unexpected error during deactivation: {e}")
            print(f"Error: {e}")
            return 1
    
    async def status(self) -> int:
        """
        Show current license status.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            print("Epochly License Status")
            print("=" * 20)
            
            status = self.license_manager.get_license_status()
            
            print(f"Activated: {'Yes' if status['activated'] else 'No'}")
            print(f"Valid: {'Yes' if status['valid'] else 'No'}")
            print(f"License Type: {status['license_type']}")
            
            if status['expiry_date']:
                print(f"Expires: {status['expiry_date']}")
            else:
                print("Expires: Never")
            
            if status['features']:
                print(f"Licensed Features: {', '.join(status['features'])}")
            else:
                print("Licensed Features: None")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Unexpected error getting status: {e}")
            print(f"Error: {e}")
            return 1
    
    async def validate(self, license_key: Optional[str] = None) -> int:
        """
        Validate a license key or current license.
        
        Args:
            license_key: Optional license key to validate
            
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            if license_key:
                print(f"Validating license: {license_key[:8]}...")
                
                # Validate format
                if not self.license_validator.validate_format(license_key):
                    print("ERROR: Format validation failed")
                    return 1
                else:
                    print("SUCCESS: Format validation passed")
                
                # Validate signature
                if not self.license_validator.validate_signature(license_key):
                    print("ERROR: Signature validation failed")
                    return 1
                else:
                    print("SUCCESS: Signature validation passed")
                
                # Validate expiry
                if not self.license_validator.validate_expiry(license_key):
                    print("ERROR: Expiry validation failed")
                    return 1
                else:
                    print("SUCCESS: Expiry validation passed")
                
                print("SUCCESS: License is valid!")
                
                # Show license info
                info = self.license_validator.get_license_info(license_key)
                if info:
                    print("\nLicense Information:")
                    print(f"Type: {info['license_type']}")
                    print(f"Features: {', '.join(info['features'])}")
                    if info['expiry_date']:
                        print(f"Expires: {info['expiry_date']}")
                
            else:
                print("Validating current license...")
                if self.license_manager.validate_license():
                    print("SUCCESS: Current license is valid!")
                else:
                    print("ERROR: Current license is invalid or not found")
                    return 1
            
            return 0
            
        except (LicenseError, ValidationError) as e:
            print(f"Validation error: {e}")
            return 1
        except Exception as e:
            self.logger.error(f"Unexpected error during validation: {e}")
            print(f"Error: {e}")
            return 1
    
    async def info(self, license_key: str) -> int:
        """
        Show information about a license key.
        
        Args:
            license_key: The license key to analyze
            
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            print(f"License Information for: {license_key[:8]}...")
            print("=" * 40)
            
            info = self.license_validator.get_license_info(license_key)
            if not info:
                print("Error: Unable to parse license key")
                return 1
            
            print(f"License Type: {info['license_type']}")
            print(f"Version: {info['version']}")
            print(f"User Limit: {info['user_limit']}")
            print(f"Issued Date: {info['issued_date']}")
            
            if info['expiry_date']:
                print(f"Expiry Date: {info['expiry_date']}")
            else:
                print("Expiry Date: Never")
            
            print("Licensed Features:")
            for feature in info['features']:
                print(f"  - {feature}")
            
            return 0

        except Exception as e:
            self.logger.error(f"Unexpected error getting info: {e}")
            print(f"Error: {e}")
            return 1

    async def dev_token_generate(
        self,
        email: str,
        tier: str,
        environment: str,
        features: List[str],
        days: int,
        output: Path,
        init_keys: bool
    ) -> int:
        """
        Generate a cryptographically signed developer token.

        Args:
            email: Developer email
            tier: Token tier (developer, enterprise-dev, ci-cd)
            environment: Environment (development, testing, ci)
            features: List of enabled features
            days: Token validity in days
            output: Output path for token file
            init_keys: Force generation of new key pair

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        if not HAS_CRYPTOGRAPHY:
            print("Error: cryptography library not installed.")
            print("Install with: pip install cryptography")
            return 1

        # Validate tier
        if tier not in VALID_TIERS:
            print(f"Error: Invalid tier '{tier}'. Must be one of: {', '.join(VALID_TIERS)}")
            return 1

        # Validate environment
        if environment not in VALID_ENVIRONMENTS:
            print(f"Error: Invalid environment '{environment}'. Must be one of: {', '.join(VALID_ENVIRONMENTS)}")
            return 1

        # Validate days
        if days < 1 or days > MAX_TOKEN_LIFETIME_DAYS:
            print(f"Error: Duration must be 1-{MAX_TOKEN_LIFETIME_DAYS} days")
            return 1

        try:
            # Handle key initialization
            if init_keys and DEV_PRIVATE_KEY_PATH.exists():
                print("Warning: Existing key pair will be overwritten!")
                response = input("Continue? [y/N] ")
                if response.lower() != 'y':
                    print("Aborted.")
                    return 0
                DEV_PRIVATE_KEY_PATH.unlink()
                if DEV_PUBLIC_KEY_PATH.exists():
                    DEV_PUBLIC_KEY_PATH.unlink()

            # Load or create signing key
            private_key = self._load_or_create_signing_key()

            # Generate token
            print(f"\nGenerating developer token...")
            print(f"  Email: {email}")
            print(f"  Tier: {tier}")
            print(f"  Environment: {environment}")
            print(f"  Features: {', '.join(features)}")
            print(f"  Duration: {days} days")

            token = self._generate_dev_token(
                email=email,
                tier=tier,
                environment=environment,
                features=features,
                duration_days=days,
                private_key=private_key
            )

            # Save token
            self._save_token(token, output)

            # Display result
            expiry_date = datetime.fromtimestamp(
                token['payload']['exp'],
                tz=timezone.utc
            ).strftime('%Y-%m-%d %H:%M:%S UTC')

            print(f"\nToken generated successfully!")
            print(f"  Output: {output}")
            print(f"  Token ID: {token['payload']['jti'][:8]}...")
            print(f"  Expires: {expiry_date}")
            print()
            print("=" * 60)
            print("TO ACTIVATE THE DEV BYPASS:")
            print("=" * 60)
            print()
            print("1. Ensure the public key in LicenseCrypto matches your signing key.")
            print(f"   Run: epochly-license dev-token show-key")
            print()
            print("2. Set the environment variable:")
            print("   export EPOCHLY_TEST_MODE=1")
            print()
            print("3. Run your notebooks or scripts as usual.")
            print()
            print("Or run both in one command:")
            print("   EPOCHLY_TEST_MODE=1 jupyter notebook")
            print()

            return 0

        except Exception as e:
            self.logger.error(f"Error generating dev token: {e}")
            print(f"Error: {e}")
            return 1

    async def dev_token_show_key(self) -> int:
        """
        Display the public key for embedding in LicenseCrypto.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        if not HAS_CRYPTOGRAPHY:
            print("Error: cryptography library not installed.")
            print("Install with: pip install cryptography")
            return 1

        if DEV_PUBLIC_KEY_PATH.exists():
            with open(DEV_PUBLIC_KEY_PATH, 'rb') as f:
                public_key_pem = f.read()
            print("\nPublic key for LicenseCrypto.EMBEDDED_PUBLIC_KEY_PEM:")
            print("-" * 60)
            print(public_key_pem.decode())
            print("-" * 60)
            print()
            print("Copy this key to src/epochly/licensing/license_crypto.py")
            print("in the EMBEDDED_PUBLIC_KEY_PEM constant.")
            return 0
        else:
            print("No public key found.")
            print("Run: epochly-license dev-token generate --init-keys")
            return 1

    async def dev_token_validate(self, token_path: Optional[Path] = None) -> int:
        """
        Validate an existing developer token.

        Args:
            token_path: Optional path to token file

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            validator = get_dev_token_validator()

            # Load token if path provided
            token_data = None
            if token_path:
                if not token_path.exists():
                    print(f"Error: Token file not found: {token_path}")
                    return 1
                token_data, reason = validator.load_token_from_file(token_path)
                if token_data is None:
                    print(f"Error: Failed to load token: {reason.value}")
                    return 1

            # Validate (note: this requires EPOCHLY_TEST_MODE=1 by default)
            # We'll use skip mode for validation display
            original_require = validator._require_test_mode
            validator._require_test_mode = False
            validator.clear_cache()

            result = validator.validate(token_data, skip_revocation=True)

            validator._require_test_mode = original_require

            print("\nDeveloper Token Validation")
            print("=" * 40)

            if result.valid:
                print("Status: VALID")
                if result.payload:
                    print(f"Subject: {result.payload.subject}")
                    print(f"Tier: {result.payload.tier}")
                    print(f"Environment: {result.payload.environment}")
                    print(f"Token ID: {result.payload.token_id[:8]}...")

                    issued_date = datetime.fromtimestamp(
                        result.payload.issued_at,
                        tz=timezone.utc
                    ).strftime('%Y-%m-%d %H:%M:%S UTC')

                    expiry_date = datetime.fromtimestamp(
                        result.payload.expires_at,
                        tz=timezone.utc
                    ).strftime('%Y-%m-%d %H:%M:%S UTC')

                    print(f"Issued: {issued_date}")
                    print(f"Expires: {expiry_date}")
                    print(f"Features: {', '.join(result.payload.features)}")

                    # Calculate remaining time
                    remaining_seconds = result.payload.expires_at - int(time.time())
                    remaining_days = remaining_seconds / (24 * 60 * 60)
                    print(f"Remaining: {remaining_days:.1f} days")

                print()
                print("Note: To use this token, set EPOCHLY_TEST_MODE=1")
                return 0
            else:
                print(f"Status: INVALID")
                print(f"Reason: {result.reason.value}")
                if result.error:
                    print(f"Error: {result.error}")
                if result.expired:
                    print("Token has expired. Generate a new one with:")
                    print("  epochly-license dev-token generate")
                return 1

        except Exception as e:
            self.logger.error(f"Error validating token: {e}")
            print(f"Error: {e}")
            return 1

    async def dev_token_info(self, token_path: Optional[Path] = None) -> int:
        """
        Show information about a developer token without full validation.

        Args:
            token_path: Optional path to token file

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            validator = get_dev_token_validator()

            # Find or use specified token path
            path = token_path or validator.find_token_file()
            if not path:
                print("Error: No dev token found.")
                print("Token locations checked:")
                for loc in validator.TOKEN_LOCATIONS:
                    print(f"  - {loc}")
                return 1

            print(f"\nDev Token Info: {path}")
            print("=" * 40)

            # Read token file directly
            with open(path, 'r', encoding='utf-8') as f:
                token_data = json.load(f)

            payload = token_data.get('payload', {})

            print(f"Subject: {payload.get('sub', 'N/A')}")
            print(f"Issuer: {payload.get('iss', 'N/A')}")
            print(f"Tier: {payload.get('tier', 'N/A')}")
            print(f"Environment: {payload.get('env', 'N/A')}")
            print(f"Token ID: {payload.get('jti', 'N/A')[:8]}...")

            iat = payload.get('iat', 0)
            exp = payload.get('exp', 0)

            if iat:
                issued_date = datetime.fromtimestamp(
                    iat, tz=timezone.utc
                ).strftime('%Y-%m-%d %H:%M:%S UTC')
                print(f"Issued: {issued_date}")

            if exp:
                expiry_date = datetime.fromtimestamp(
                    exp, tz=timezone.utc
                ).strftime('%Y-%m-%d %H:%M:%S UTC')
                print(f"Expires: {expiry_date}")

                remaining_seconds = exp - int(time.time())
                if remaining_seconds > 0:
                    remaining_days = remaining_seconds / (24 * 60 * 60)
                    print(f"Remaining: {remaining_days:.1f} days")
                else:
                    print("Status: EXPIRED")

            features = payload.get('features', [])
            if features:
                print(f"Features: {', '.join(features)}")

            # Check signature validity (without test mode requirement)
            sig_valid = validator.validate_signature(token_data)
            print(f"Signature: {'Valid' if sig_valid else 'INVALID'}")

            return 0

        except json.JSONDecodeError:
            print("Error: Token file is not valid JSON")
            return 1
        except Exception as e:
            self.logger.error(f"Error reading token: {e}")
            print(f"Error: {e}")
            return 1

    def _load_or_create_signing_key(self) -> 'ed25519.Ed25519PrivateKey':
        """Load existing signing key or create a new one."""
        if DEV_PRIVATE_KEY_PATH.exists():
            with open(DEV_PRIVATE_KEY_PATH, 'rb') as f:
                private_key_pem = f.read()
            return serialization.load_pem_private_key(private_key_pem, password=None)

        # Create new key pair
        print("No existing signing key found. Generating new key pair...")
        DEV_KEY_DIR.mkdir(parents=True, exist_ok=True)

        private_key = ed25519.Ed25519PrivateKey.generate()

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_key_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Save private key (owner read-only)
        with open(DEV_PRIVATE_KEY_PATH, 'wb') as f:
            f.write(private_key_pem)
        os.chmod(DEV_PRIVATE_KEY_PATH, 0o600)

        # Save public key
        with open(DEV_PUBLIC_KEY_PATH, 'wb') as f:
            f.write(public_key_pem)
        os.chmod(DEV_PUBLIC_KEY_PATH, 0o644)

        print(f"  Private key saved to: {DEV_PRIVATE_KEY_PATH}")
        print(f"  Public key saved to: {DEV_PUBLIC_KEY_PATH}")
        print()
        print("IMPORTANT: Update LicenseCrypto.EMBEDDED_PUBLIC_KEY_PEM with this public key:")
        print("-" * 60)
        print(public_key_pem.decode())
        print("-" * 60)
        print()

        return private_key

    def _generate_dev_token(
        self,
        email: str,
        tier: str,
        environment: str,
        features: List[str],
        duration_days: int,
        private_key: 'ed25519.Ed25519PrivateKey'
    ) -> dict:
        """Generate a signed developer token."""
        current_time = int(time.time())
        jti = str(uuid.uuid4())

        payload = {
            'sub': email.strip().lower(),
            'iss': REQUIRED_ISSUER,
            'iat': current_time,
            'exp': current_time + (duration_days * 24 * 60 * 60),
            'jti': jti,
            'tier': tier,
            'features': sorted(features),
            'env': environment
        }

        signature = self._sign_payload(payload, private_key)

        return {
            'payload': payload,
            'signature': signature
        }

    def _sign_payload(
        self,
        payload: dict,
        private_key: 'ed25519.Ed25519PrivateKey'
    ) -> str:
        """Sign a token payload with ED25519."""
        # Create canonical JSON representation (sorted keys, no spaces)
        payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        payload_bytes = payload_json.encode('utf-8')

        # Sign the payload
        signature = private_key.sign(payload_bytes)

        # Return URL-safe base64 without padding
        return base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')

    def _save_token(self, token: dict, output_path: Path) -> None:
        """Save token to file with secure permissions."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(token, f, indent=2)

        os.chmod(output_path, 0o600)


async def main():
    """Main entry point for the licensing CLI."""
    parser = argparse.ArgumentParser(
        description="Epochly Licensing Management CLI",
        prog="epochly-license"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Activate command
    activate_parser = subparsers.add_parser("activate", help="Activate a license")
    activate_parser.add_argument("license_key", help="License key to activate")
    
    # Deactivate command
    subparsers.add_parser("deactivate", help="Deactivate current license")
    
    # Status command
    subparsers.add_parser("status", help="Show license status")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a license")
    validate_parser.add_argument(
        "license_key", 
        nargs="?", 
        help="License key to validate (optional, validates current if not provided)"
    )
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show license information")
    info_parser.add_argument("license_key", help="License key to analyze")

    # Dev-token command group
    dev_token_parser = subparsers.add_parser(
        "dev-token",
        help="Developer token management for local development"
    )
    dev_token_subparsers = dev_token_parser.add_subparsers(
        dest="dev_token_command",
        help="Dev token commands"
    )

    # dev-token generate
    dev_generate_parser = dev_token_subparsers.add_parser(
        "generate",
        help="Generate a new developer token"
    )
    dev_generate_parser.add_argument(
        "--email", "-e",
        default="dev@epochly.local",
        help="Developer email (default: dev@epochly.local)"
    )
    dev_generate_parser.add_argument(
        "--tier", "-t",
        default="developer",
        choices=VALID_TIERS,
        help="Token tier (default: developer)"
    )
    dev_generate_parser.add_argument(
        "--env",
        default="development",
        choices=VALID_ENVIRONMENTS,
        help="Environment (default: development)"
    )
    dev_generate_parser.add_argument(
        "--features", "-f",
        default=",".join(DEFAULT_FEATURES),
        help=f"Comma-separated features (default: {','.join(DEFAULT_FEATURES)})"
    )
    dev_generate_parser.add_argument(
        "--days", "-d",
        type=int,
        default=30,
        help="Token validity in days (default: 30, max: 90)"
    )
    dev_generate_parser.add_argument(
        "--output", "-o",
        type=Path,
        default=DEFAULT_TOKEN_PATH,
        help=f"Output path (default: {DEFAULT_TOKEN_PATH})"
    )
    dev_generate_parser.add_argument(
        "--init-keys",
        action="store_true",
        help="Force generation of new key pair"
    )

    # dev-token show-key
    dev_token_subparsers.add_parser(
        "show-key",
        help="Display the public key for embedding in LicenseCrypto"
    )

    # dev-token validate
    dev_validate_parser = dev_token_subparsers.add_parser(
        "validate",
        help="Validate an existing developer token"
    )
    dev_validate_parser.add_argument(
        "token_path",
        type=Path,
        nargs="?",
        help="Path to token file (uses default locations if not specified)"
    )

    # dev-token info
    dev_info_parser = dev_token_subparsers.add_parser(
        "info",
        help="Show developer token information"
    )
    dev_info_parser.add_argument(
        "token_path",
        type=Path,
        nargs="?",
        help="Path to token file (uses default locations if not specified)"
    )

    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Create CLI instance and execute command
    cli = LicensingCLI()
    
    try:
        if args.command == "activate":
            return await cli.activate(args.license_key)
        elif args.command == "deactivate":
            return await cli.deactivate()
        elif args.command == "status":
            return await cli.status()
        elif args.command == "validate":
            return await cli.validate(getattr(args, 'license_key', None))
        elif args.command == "info":
            return await cli.info(args.license_key)
        elif args.command == "dev-token":
            # Handle dev-token subcommands
            if not hasattr(args, 'dev_token_command') or not args.dev_token_command:
                dev_token_parser.print_help()
                return 1

            if args.dev_token_command == "generate":
                features = [f.strip() for f in args.features.split(',') if f.strip()]
                return await cli.dev_token_generate(
                    email=args.email,
                    tier=args.tier,
                    environment=args.env,
                    features=features,
                    days=args.days,
                    output=args.output,
                    init_keys=args.init_keys
                )
            elif args.dev_token_command == "show-key":
                return await cli.dev_token_show_key()
            elif args.dev_token_command == "validate":
                return await cli.dev_token_validate(
                    token_path=getattr(args, 'token_path', None)
                )
            elif args.dev_token_command == "info":
                return await cli.dev_token_info(
                    token_path=getattr(args, 'token_path', None)
                )
            else:
                print(f"Unknown dev-token command: {args.dev_token_command}")
                return 1
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))