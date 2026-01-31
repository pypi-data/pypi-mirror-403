"""
Sitecustomize CLI module - provides command-line interface for sitecustomize management.

Supports subcommands:
- install: Install Epochly sitecustomize.py for transparent activation
- uninstall: Remove Epochly sitecustomize.py
- status: Check sitecustomize.py installation status
- validate: Validate sitecustomize.py installation

Author: Epochly Development Team
"""

import sys
import argparse
from epochly.deployment.sitecustomize_installer import SitecustomizeInstaller


def main(args=None):
    """Main CLI entry point for sitecustomize management."""
    parser = argparse.ArgumentParser(
        description="Epochly Sitecustomize Management",
        prog="python -m epochly.cli.sitecustomize"
    )

    subparsers = parser.add_subparsers(dest="command", help="Sitecustomize subcommands")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install Epochly sitecustomize.py")
    install_parser.add_argument("--force", action="store_true", help="Force installation")
    install_parser.add_argument("--no-preserve", action="store_true", help="Don't preserve existing sitecustomize.py")

    # Uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall Epochly sitecustomize.py")
    uninstall_parser.add_argument("--no-restore", action="store_true", help="Don't restore backup")

    # Status command
    subparsers.add_parser("status", help="Check sitecustomize.py installation status")

    # Validate command
    subparsers.add_parser("validate", help="Validate sitecustomize.py installation")

    # List backups command
    subparsers.add_parser("list-backups", help="List available backups")

    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 1

    installer = SitecustomizeInstaller()

    try:
        if parsed_args.command == "install":
            preserve_existing = not parsed_args.no_preserve
            success = installer.install(force=parsed_args.force, preserve_existing=preserve_existing)
            if success:
                print("Epochly sitecustomize.py installed successfully")
                return 0
            else:
                print("Failed to install sitecustomize.py", file=sys.stderr)
                return 1

        elif parsed_args.command == "uninstall":
            restore_backup = not parsed_args.no_restore
            success = installer.uninstall(restore_backup=restore_backup)
            if success:
                print("Epochly sitecustomize.py uninstalled successfully")
                return 0
            else:
                print("Failed to uninstall sitecustomize.py", file=sys.stderr)
                return 1

        elif parsed_args.command == "status":
            status = installer.get_installation_status()
            print("Sitecustomize Installation Status:")
            print(f"  Installed: {status['installed']}")
            print(f"  Epochly Managed: {status['epochly_managed']}")
            print(f"  Valid: {status['valid']}")
            if status['path']:
                print(f"  Path: {status['path']}")
            print(f"  Backup Directory: {status['backup_directory']}")
            return 0

        elif parsed_args.command == "validate":
            is_valid = installer.validate_installation()
            if is_valid:
                print("Sitecustomize.py installation is valid")
                return 0
            else:
                print("Sitecustomize.py installation is invalid or not found", file=sys.stderr)
                return 1

        elif parsed_args.command == "list-backups":
            backups = installer.list_backups()
            if backups:
                print("Available Sitecustomize Backups:")
                for backup in backups:
                    from datetime import datetime
                    created = datetime.fromtimestamp(backup['created']).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"  {backup['filename']} - Created: {created}, Size: {backup['size']} bytes")
            else:
                print("No sitecustomize.py backups found")
            return 0

        else:
            print(f"Unknown command: {parsed_args.command}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())


__all__ = ['main']

