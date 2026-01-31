"""
Epochly Deployment CLI

Command-line interface for Epochly deployment management.
Provides deployment control, monitoring, and configuration commands.

Author: Epochly Development Team
"""

import argparse
import asyncio
import logging
import sys
from typing import Optional

from .deployment_controller import DeploymentController, DeploymentMode
from ..utils.logging_bootstrap import setup_logging
from ..monitoring.prometheus_exporter import get_prometheus_exporter
from ..utils.exceptions import EpochlyError


class DeploymentError(EpochlyError):
    """Deployment-related error."""
    pass


class DeploymentCLI:
    """
    Command-line interface for Epochly deployment operations.
    
    Provides commands for deployment management including status checking,
    mode configuration, monitoring, and emergency controls.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the deployment CLI.
        
        Args:
            config_path: Optional path to deployment configuration
        """
        self.deployment_controller = DeploymentController(config_path)
        self.prometheus_exporter = get_prometheus_exporter()
        self.logger = logging.getLogger(__name__)
    
    async def status(self) -> int:
        """
        Show deployment status.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            print("Epochly Deployment Status")
            print("=" * 25)
            
            status = self.deployment_controller.get_status()
            
            print(f"Status: {status.get('status', 'Unknown')}")
            print(f"Mode: {status.get('mode', 'Unknown')}")
            print(f"Uptime: {status.get('uptime', 'Unknown')}")
            print(f"Active Components: {status.get('active_components', 0)}")
            
            # Show component details
            components = status.get('components', {})
            if components:
                print("\nComponent Status:")
                for name, component_status in components.items():
                    status_icon = "✅" if component_status.get('healthy', False) else "❌"
                    print(f"  {status_icon} {name}: {component_status.get('status', 'Unknown')}")
            
            # Show performance metrics if available
            metrics = status.get('metrics', {})
            if metrics:
                print("\nPerformance Metrics:")
                print(f"  CPU Usage: {metrics.get('cpu_usage', 'N/A')}")
                print(f"  Memory Usage: {metrics.get('memory_usage', 'N/A')}")
                print(f"  Active Connections: {metrics.get('connections', 'N/A')}")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error getting deployment status: {e}")
            print(f"Error: {e}")
            return 1
    
    async def enable(self) -> int:
        """
        Enable the deployment.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            print("Enabling Epochly deployment...")
            
            # Enable deployment by setting enabled flag
            with self.deployment_controller._lock:
                self.deployment_controller._config.enabled = True
                self.deployment_controller._save_config()
            
            print("✅ Deployment enabled successfully!")
            
            # Show current status
            status = self.deployment_controller.get_status()
            print(f"Enabled: {status.get('enabled', False)}")
            print(f"Mode: {status.get('mode', 'Unknown')}")
            
            return 0
                
        except Exception as e:
            self.logger.error(f"Error enabling deployment: {e}")
            print(f"Error: {e}")
            return 1
    
    async def disable(self) -> int:
        """
        Disable the deployment.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            print("Disabling Epochly deployment...")
            
            # Disable deployment by setting enabled flag
            with self.deployment_controller._lock:
                self.deployment_controller._config.enabled = False
                self.deployment_controller._save_config()
            
            print("✅ Deployment disabled successfully!")
            return 0
                
        except Exception as e:
            self.logger.error(f"Error disabling deployment: {e}")
            print(f"Error: {e}")
            return 1
    
    async def toggle(self) -> int:
        """
        Toggle the deployment state.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            status = self.deployment_controller.get_status()
            current_enabled = status.get('enabled', False)
            
            if current_enabled:
                print("Disabling Epochly deployment...")
                result = await self.disable()
            else:
                print("Enabling Epochly deployment...")
                result = await self.enable()
            
            return result
                
        except Exception as e:
            self.logger.error(f"Error toggling deployment: {e}")
            print(f"Error: {e}")
            return 1
    
    async def set_mode(self, mode: str) -> int:
        """
        Set deployment mode.
        
        Args:
            mode: The deployment mode to set
            
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            valid_modes = ['monitor', 'conservative', 'balanced', 'aggressive']
            if mode not in valid_modes:
                print(f"Error: Invalid mode '{mode}'. Valid modes: {', '.join(valid_modes)}")
                return 1
            
            print(f"Setting deployment mode to '{mode}'...")
            
            # Convert string to enum
            mode_enum = DeploymentMode(mode)
            
            self.deployment_controller.set_mode(mode_enum)
            print(f"✅ Deployment mode set to '{mode}' successfully!")
            return 0
                
        except Exception as e:
            self.logger.error(f"Error setting deployment mode: {e}")
            print(f"Error: {e}")
            return 1
    
    async def monitor(self, duration: int = 30) -> int:
        """
        Monitor deployment in real-time.
        
        Args:
            duration: Monitoring duration in seconds
            
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            print(f"Monitoring Epochly deployment for {duration} seconds...")
            print("Press Ctrl+C to stop monitoring early")
            print("=" * 50)
            
            start_time = asyncio.get_event_loop().time()
            
            while True:
                current_time = asyncio.get_event_loop().time()
                elapsed = current_time - start_time
                
                if elapsed >= duration:
                    break
                
                # Get current status
                status = self.deployment_controller.get_status()
                
                # Clear screen and show status
                print(f"\r[{elapsed:.1f}s] Status: {status.get('status', 'Unknown')} | "
                      f"Components: {status.get('active_components', 0)} | "
                      f"Mode: {status.get('mode', 'Unknown')}", end="", flush=True)
                
                await asyncio.sleep(1)
            
            print("\n✅ Monitoring completed")
            return 0
            
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped by user")
            return 0
        except Exception as e:
            self.logger.error(f"Error during monitoring: {e}")
            print(f"\nError: {e}")
            return 1
    
    async def health_check(self) -> int:
        """
        Perform comprehensive health check.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            print("Performing Epochly deployment health check...")
            print("=" * 40)
            
            # Get deployment status
            status = self.deployment_controller.get_status()
            
            overall_healthy = True
            
            # Check deployment status
            deployment_enabled = status.get('enabled', False)
            emergency_disabled = status.get('emergency_disable', False)
            killswitch_active = status.get('killswitch_active', False)
            
            if deployment_enabled and not emergency_disabled and not killswitch_active:
                print("✅ Deployment Status: Enabled")
            else:
                print("❌ Deployment Status: Disabled")
                if emergency_disabled:
                    print("  - Emergency disable active")
                if killswitch_active:
                    print("  - Killswitch active")
                overall_healthy = False
            
            # Check configuration
            print("\n⚙️ Configuration:")
            print(f"  Mode: {status.get('mode', 'Unknown')}")
            print(f"  Strategy: {status.get('strategy', 'Unknown')}")
            print(f"  Percentage: {status.get('percentage', 0)}%")
            print(f"  Allowlist entries: {status.get('allowlist_count', 0)}")
            print(f"  Denylist entries: {status.get('denylist_count', 0)}")
            
            # Check monitoring
            if self.prometheus_exporter and self.prometheus_exporter.is_active():
                print("✅ Monitoring: Active")
            else:
                print("⚠️ Monitoring: Inactive")
            
            # Overall result
            print("\n" + "=" * 40)
            if overall_healthy:
                print("✅ Overall Health: HEALTHY")
                return 0
            else:
                print("❌ Overall Health: UNHEALTHY")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error during health check: {e}")
            print(f"Error: {e}")
            return 1
    
    async def emergency_stop(self) -> int:
        """
        Perform emergency stop of deployment.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            print("🚨 EMERGENCY STOP - Shutting down Epochly deployment immediately...")
            
            # Force shutdown
            self.deployment_controller.emergency_disable()
            print("✅ Emergency stop completed successfully!")
            return 0
                
        except Exception as e:
            self.logger.error(f"Error during emergency stop: {e}")
            print(f"Error: {e}")
            return 1


async def main():
    """Main entry point for the deployment CLI."""
    parser = argparse.ArgumentParser(
        description="Epochly Deployment Management CLI",
        prog="epochly-deploy"
    )
    
    parser.add_argument(
        "--config", "-c",
        help="Path to deployment configuration file"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    subparsers.add_parser("status", help="Show deployment status")
    
    # Enable command
    subparsers.add_parser("enable", help="Enable deployment")
    
    # Disable command
    subparsers.add_parser("disable", help="Disable deployment")
    
    # Toggle command
    subparsers.add_parser("toggle", help="Toggle deployment state")
    
    # Set mode command
    mode_parser = subparsers.add_parser("set-mode", help="Set deployment mode")
    mode_parser.add_argument(
        "mode",
        choices=["monitor", "conservative", "balanced", "aggressive"],
        help="Deployment mode to set"
    )
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor deployment")
    monitor_parser.add_argument(
        "--duration", "-d",
        type=int,
        default=30,
        help="Monitoring duration in seconds (default: 30)"
    )
    
    # Health check command
    subparsers.add_parser("health", help="Perform health check")
    
    # Emergency stop command
    subparsers.add_parser("emergency-stop", help="Emergency stop deployment")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Create CLI instance and execute command
    cli = DeploymentCLI(config_path=args.config)
    
    try:
        if args.command == "status":
            return await cli.status()
        elif args.command == "enable":
            return await cli.enable()
        elif args.command == "disable":
            return await cli.disable()
        elif args.command == "toggle":
            return await cli.toggle()
        elif args.command == "set-mode":
            return await cli.set_mode(args.mode)
        elif args.command == "monitor":
            return await cli.monitor(args.duration)
        elif args.command == "health":
            return await cli.health_check()
        elif args.command == "emergency-stop":
            return await cli.emergency_stop()
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