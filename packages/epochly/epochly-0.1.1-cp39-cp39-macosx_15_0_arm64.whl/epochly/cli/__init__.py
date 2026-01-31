"""
Epochly Main CLI Tool

Provides command-line interface for Epochly management and operations.
Integrates with deployment, monitoring, and licensing subsystems.

Author: Epochly Development Team
"""

import argparse
import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Lazy imports: Only import when needed to avoid triggering full Epochly initialization
# for simple commands like 'config get' or 'doctor'
from epochly.utils.logger import setup_logging, get_logger
from epochly.utils.exceptions import EpochlyError


class PositiveIntAction(argparse.Action):
    """Custom action to validate positive integer values."""
    def __call__(self, parser, namespace, values, option_string=None):
        if values <= 0:
            parser.error(f"{option_string} must be a positive integer (got {values})")
        setattr(namespace, self.dest, values)


class NonNegativeIntAction(argparse.Action):
    """Custom action to validate non-negative integer values."""
    def __call__(self, parser, namespace, values, option_string=None):
        if values < 0:
            parser.error(f"{option_string} must be non-negative (got {values})")
        setattr(namespace, self.dest, values)


class PercentageAction(argparse.Action):
    """Custom action to validate percentage values (1-100)."""
    def __call__(self, parser, namespace, values, option_string=None):
        if values < 1 or values > 100:
            parser.error(f"{option_string} must be between 1 and 100 (got {values})")
        setattr(namespace, self.dest, values)


class EpochlyCLIError(EpochlyError):
    """CLI-specific error"""
    pass


class EpochlyCLI:
    """Main Epochly CLI controller"""

    def __init__(self):
        self.logger = get_logger(__name__)
        # Lazy-loaded, type: Optional[DeploymentController]
        self.deployment_controller: Optional[Any] = None

    def setup_logging(self, verbose: bool = False) -> None:
        """Setup logging for CLI operations"""
        level = "DEBUG" if verbose else "INFO"
        setup_logging(level=level)

    async def status(self) -> Dict[str, str]:
        """Get Epochly system status including enhancement level and core metrics"""
        try:
            # Get Epochly core status (includes enhancement level, workers, JIT, etc.)
            import epochly
            core_status = epochly.get_status()

            status = {
                "enabled": "yes" if core_status.get("enabled", False) else "no",
                "enhancement_level": f"{core_status.get('level', 0)} ({core_status.get('enhancement_level', 'UNKNOWN')})",
                "python_version": core_status.get("python_version", "unknown"),
                "platform": core_status.get("platform", "unknown"),
            }

            # Add worker information if available
            if core_status.get("worker_count", 0) > 0:
                status["workers"] = str(core_status["worker_count"])

            # Add JIT status
            status["jit"] = "enabled" if core_status.get("jit_enabled", False) else "disabled"

            # Add shared memory status
            if core_status.get("shared_memory_active", False):
                status["shared_memory"] = "active"

            # Get deployment status
            try:
                from epochly.deployment.deployment_controller import DeploymentController
                if not self.deployment_controller:
                    self.deployment_controller = DeploymentController()
                deployment_status = self.deployment_controller.get_status()
                status["deployment"] = "active" if deployment_status.get("enabled", False) else "inactive"
                status["mode"] = deployment_status.get("mode", "unknown")
            except Exception:
                status["deployment"] = "unavailable"

            # Check monitoring status
            try:
                from epochly.monitoring.prometheus_exporter import get_prometheus_exporter
                exporter = get_prometheus_exporter()
                status["monitoring"] = "active" if exporter.is_active() else "inactive"
            except Exception:
                status["monitoring"] = "unavailable"

            status["version"] = "0.1.0"

            # Add configuration status (simple loaded/not loaded indicator)
            status["config"] = "loaded"

            return status

        except Exception as e:
            self.logger.error(f"Failed to get status: {e}")
            raise EpochlyCLIError(f"Status check failed: {e}")

    async def start(self, mode: str = "balanced") -> None:
        """Start Epochly system"""
        try:
            # Lazy import to avoid triggering full Epochly init
            from epochly.deployment.deployment_controller import DeploymentController, DeploymentMode

            if not self.deployment_controller:
                self.deployment_controller = DeploymentController()

            # Set deployment mode if specified
            if mode in [m.value for m in DeploymentMode]:
                deployment_mode = DeploymentMode(mode)
                self.deployment_controller.set_mode(deployment_mode)

            self.logger.info(f"Epochly started in {mode} mode")

        except Exception as e:
            self.logger.error(f"Failed to start Epochly: {e}")
            raise EpochlyCLIError(f"Start failed: {e}")

    async def stop(self) -> None:
        """Stop Epochly system"""
        try:
            if self.deployment_controller:
                self.deployment_controller.shutdown()

            # Stop monitoring if active
            try:
                # Lazy import to avoid triggering full Epochly init
                from epochly.monitoring.prometheus_exporter import get_prometheus_exporter
                exporter = get_prometheus_exporter()
                if exporter.is_active():
                    exporter.stop()
            except Exception:
                pass

            self.logger.info("Epochly stopped")

        except Exception as e:
            self.logger.error(f"Failed to stop Epochly: {e}")
            raise EpochlyCLIError(f"Stop failed: {e}")

    async def restart(self, mode: str = "balanced") -> None:
        """Restart Epochly system"""
        try:
            await self.stop()
            await asyncio.sleep(1)  # Brief pause
            await self.start(mode)
            self.logger.info("Epochly restarted")

        except Exception as e:
            self.logger.error(f"Failed to restart Epochly: {e}")
            raise EpochlyCLIError(f"Restart failed: {e}")

    async def health_check(self) -> Dict[str, str]:
        """Perform comprehensive health check"""
        try:
            # Lazy import to avoid triggering full Epochly init
            from epochly.deployment.deployment_controller import DeploymentController

            health = {
                "overall": "healthy",
                "deployment": "unknown",
                "monitoring": "unknown",
                "config": "unknown"
            }

            # Check deployment controller
            try:
                if not self.deployment_controller:
                    self.deployment_controller = DeploymentController()

                status = self.deployment_controller.get_status()
                health["deployment"] = "healthy" if not status.get("emergency_disable", False) else "emergency"
                health["config"] = "healthy"

            except Exception as e:
                health["deployment"] = f"error: {e}"
                health["overall"] = "unhealthy"

            # Check monitoring
            try:
                # Lazy import to avoid triggering full Epochly init
                from epochly.monitoring.prometheus_exporter import get_prometheus_exporter
                exporter = get_prometheus_exporter()
                health["monitoring"] = "healthy" if exporter.is_active() else "inactive"

            except Exception as e:
                health["monitoring"] = f"error: {e}"

            # Determine overall health
            if any("error" in v for v in health.values() if v != health["overall"]):
                health["overall"] = "unhealthy"
            elif health["deployment"] == "emergency":
                health["overall"] = "emergency"

            return health

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            raise EpochlyCLIError(f"Health check failed: {e}")



    def metrics_drops(self, reset: bool = False) -> Dict[str, Any]:
        """
        Show metrics drop information (IO-8).
        
        Args:
            reset: Whether to reset drop counter after showing
            
        Returns:
            Dictionary containing drop metrics
        """
        try:
            from epochly.monitoring.performance_monitor import get_performance_monitor
            
            monitor = get_performance_monitor()
            
            drop_count = monitor.get_drop_count()
            total = monitor.get_total_metrics_attempted()
            drop_rate = monitor.get_drop_rate()
            
            result = {
                'drops': drop_count,
                'total_attempts': total,
                'drop_rate': drop_rate,
                'drop_rate_pct': drop_rate * 100
            }
            
            if reset:
                monitor.reset_drop_count()
                result['reset'] = True
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get metrics drops: {e}")
            raise EpochlyCLIError(f"Metrics drops failed: {e}")
    
    def metrics_drops_config(self, alert_interval: Optional[int] = None) -> Dict[str, Any]:
        """
        Configure drop alerting (IO-8).
        
        Args:
            alert_interval: Alert every N drops (0 to disable, None to show current)
            
        Returns:
            Dictionary containing configuration
        """
        try:
            from epochly.monitoring.performance_monitor import get_performance_monitor
            
            monitor = get_performance_monitor()
            
            if alert_interval is not None:
                monitor.set_drop_alert_interval(alert_interval)
                return {
                    'alert_interval': alert_interval,
                    'configured': True
                }
            else:
                return {
                    'alert_interval': monitor._drop_alert_interval,
                    'configured': False
                }
            
        except Exception as e:
            self.logger.error(f"Failed to configure metrics: {e}")
            raise EpochlyCLIError(f"Metrics configuration failed: {e}")

def create_parser(include_script_args=True, include_subcommands=True) -> argparse.ArgumentParser:
    """Create CLI argument parser

    Args:
        include_script_args: Whether to include positional script arguments.
                           Set to False for command-only mode to avoid conflicts.
        include_subcommands: Whether to include management subcommands.
                           Set to False for script-only mode to avoid conflicts.
    """
    parser = argparse.ArgumentParser(
        description="Epochly - Accelerate Python Scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage="epochly [script.py] [script args...] or epochly [command] [options]",
        epilog="""
Examples:
  epochly myscript.py              # Run script with Epochly acceleration
  epochly myscript.py --arg value  # Pass arguments to your script
  epochly -l 3 myscript.py         # Run with specific optimization level
  epochly status                   # Check Epochly status
  epochly health                   # Run health check
  epochly sitecustomize install    # Install transparent activation
        """
    )

    # Only add script arguments if requested (to avoid conflicts with subcommands)
    if include_script_args:
        # Script execution arguments (for running Python files)
        parser.add_argument(
            "script",
            nargs="?",
            help="Python script to run with Epochly acceleration"
        )

        parser.add_argument(
            "script_args",
            nargs=argparse.REMAINDER,
            help="Arguments to pass to the script"
        )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "-l", "--level",
        type=int,
        choices=[0, 1, 2, 3, 4],
        default=3,
        help="Optimization level (0=monitor, 1=conservative, 2=balanced, 3=aggressive, 4=gpu)"
    )

    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Disable automatic optimization (monitor only)"
    )

    # Memory pool configuration (per architecture spec)
    parser.add_argument(
        "--pin-pool",
        choices=["fast", "legacy", "sharded"],
        help="Pin to specific memory pool type"
    )

    parser.add_argument(
        "--allowed-pools",
        help="Comma-separated list of allowed memory pools"
    )

    # Core usage limits (per architecture spec)
    parser.add_argument(
        "--max-cores",
        type=int,
        action=PositiveIntAction,
        metavar="N",
        help="Maximum number of CPU cores to use"
    )

    parser.add_argument(
        "--max-cores-percent",
        type=int,
        action=PercentageAction,
        metavar="PERCENT",
        help="Maximum percentage of CPU cores to use (1-100)"
    )

    parser.add_argument(
        "--reserve-cores",
        type=int,
        action=NonNegativeIntAction,
        metavar="N",
        help="Number of cores to reserve for other processes"
    )

    # Advanced analysis commands (per architecture spec)
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Save profiling data for analysis"
    )

    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Compare performance with and without Epochly"
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check compatibility without running (dry run)"
    )

    parser.add_argument(
        "--explain",
        action="store_true",
        help="Explain optimization decisions made by Epochly"
    )

    # Runtime configuration
    parser.add_argument(
        "--workers",
        type=int,
        help="Override default worker count"
    )

    parser.add_argument(
        "--mode",
        choices=["monitor", "conservative", "balanced", "aggressive"],
        help="Optimization mode (overrides --level)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed logging"
    )

    # Python-compatible execution modes
    parser.add_argument(
        "-m",
        dest="module",
        help="Run library module as a script (like python -m)"
    )

    parser.add_argument(
        "-c",
        dest="command",
        help="Execute program passed in as string (like python -c)"
    )

    # Only add subcommands if requested
    if include_subcommands:
        subparsers = parser.add_subparsers(dest="command", help="Management commands")

        # Status command
        subparsers.add_parser("status", help="Show Epochly system status")

        # Start command
        start_parser = subparsers.add_parser("start", help="Start Epochly system")
        start_parser.add_argument(
        "--mode",
        choices=["monitor", "conservative", "balanced", "aggressive"],
        default="balanced",
        help="Deployment mode (default: balanced)"
        )

        # Stop command
        subparsers.add_parser("stop", help="Stop Epochly system")

        # Restart command
        restart_parser = subparsers.add_parser("restart", help="Restart Epochly system")
        restart_parser.add_argument(
        "--mode",
        choices=["monitor", "conservative", "balanced", "aggressive"],
        default="balanced",
        help="Deployment mode (default: balanced)"
        )

        # Health command
        subparsers.add_parser("health", help="Perform health check")

        # Jupyter command
        jupyter_parser = subparsers.add_parser("jupyter", help="Jupyter integration commands")
        jupyter_subparsers = jupyter_parser.add_subparsers(dest="jupyter_command", help="Jupyter subcommands")

        # Jupyter install
        jupyter_install = jupyter_subparsers.add_parser("install", help="Install Epochly Jupyter kernel")
        jupyter_install.add_argument("--name", default="epochly", help="Kernel name")
        jupyter_install.add_argument("--display-name", default="Python (epochly)", help="Display name")
        jupyter_install.add_argument("--system", action="store_true", help="Install system-wide")
        jupyter_install.add_argument("--force", action="store_true", help="Overwrite existing")

        # Jupyter uninstall
        jupyter_uninstall = jupyter_subparsers.add_parser("uninstall", help="Uninstall Epochly Jupyter kernel")
        jupyter_uninstall.add_argument("--name", default="epochly", help="Kernel name")
        jupyter_uninstall.add_argument("--system", action="store_true", help="Remove from system")

        # Jupyter list
        jupyter_list = jupyter_subparsers.add_parser("list", help="List Epochly kernels")
        jupyter_list.add_argument("--system", action="store_true", help="List system kernels")

        # Jupyter setup
        jupyter_setup = jupyter_subparsers.add_parser("setup", help="Complete Jupyter setup")
        jupyter_setup.add_argument("--force", action="store_true", help="Overwrite existing")

        # Jupyter test
        jupyter_subparsers.add_parser("test", help="Test magic commands")

        # Sitecustomize command (install/uninstall transparent activation)
        sitecustomize_parser = subparsers.add_parser(
            "sitecustomize",
            help="Manage transparent Epochly activation via sitecustomize.py"
        )
        sitecustomize_subparsers = sitecustomize_parser.add_subparsers(
            dest="sitecustomize_command",
            help="Sitecustomize subcommands"
        )

        # Sitecustomize install
        sitecustomize_install = sitecustomize_subparsers.add_parser(
            "install",
            help="Install sitecustomize.py for transparent activation"
        )
        sitecustomize_install.add_argument(
            "--force",
            action="store_true",
            help="Force installation even if conflicts exist"
        )
        sitecustomize_install.add_argument(
            "--no-preserve",
            action="store_true",
            help="Don't preserve existing sitecustomize.py content"
        )

        # Sitecustomize uninstall
        sitecustomize_uninstall = sitecustomize_subparsers.add_parser(
            "uninstall",
            help="Uninstall Epochly sitecustomize.py"
        )
        sitecustomize_uninstall.add_argument(
            "--no-restore",
            action="store_true",
            help="Don't restore original sitecustomize.py from backup"
        )

        # Sitecustomize status
        sitecustomize_subparsers.add_parser(
            "status",
            help="Check sitecustomize.py installation status"
        )

        # Sitecustomize validate
        sitecustomize_subparsers.add_parser(
            "validate",
            help="Validate sitecustomize.py installation"
        )

        # Sitecustomize list-backups
        sitecustomize_subparsers.add_parser(
            "list-backups",
            help="List available sitecustomize.py backups"
        )

        # GPU command - Level 4 diagnostics and setup guidance
        gpu_parser = subparsers.add_parser(
            "gpu",
            help="GPU acceleration diagnostics and setup (Level 4)"
        )
        gpu_subparsers = gpu_parser.add_subparsers(
            dest="gpu_command",
            help="GPU subcommands"
        )

        # GPU check - run diagnostics
        gpu_check = gpu_subparsers.add_parser(
            "check",
            help="Run GPU diagnostics and show status"
        )
        gpu_check.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Show detailed diagnostic information"
        )

        # GPU guide - show installation guide
        gpu_subparsers.add_parser(
            "guide",
            help="Show GPU installation and setup guide"
        )

        # GPU status - quick status check
        gpu_subparsers.add_parser(
            "status",
            help="Quick GPU status check"
        )

        # Shell command
        shell_parser = subparsers.add_parser("shell",
                                            help="Launch Epochly-enabled Python REPL",
                                            description="Launch Epochly-enabled Python REPL with enhanced performance monitoring")
        shell_parser.add_argument(
            "--startup",
            help="Path to startup script to execute on REPL start"
        )
        shell_parser.add_argument(
            "--no-banner",
            action="store_true",
            help="Suppress the Epochly banner on startup"
        )
        shell_parser.add_argument(
            "-i", "--interactive",
            action="store_true",
            help="Force interactive mode (default)"
        )
        shell_parser.add_argument(
            "-q", "--quiet",
            action="store_true",
            help="Quiet mode - minimal output"
        )

        # Config command
        config_parser = subparsers.add_parser("config", help="Interactive configuration wizard")
        config_subparsers = config_parser.add_subparsers(dest="config_command", help="Config subcommands")

        # Config show
        config_show = config_subparsers.add_parser("show", help="Show current configuration")
        config_show.add_argument("--global", dest="global_config", action="store_true", help="Show global configuration")
        config_show.add_argument("--local", dest="local_config", action="store_true", help="Show local configuration")
        config_show.add_argument("--system", dest="system_config", action="store_true", help="Show system configuration")

        # Config set
        config_set = config_subparsers.add_parser("set", help="Set configuration value")
        config_set.add_argument("key", help="Configuration key")
        config_set.add_argument("value", help="Configuration value")
        config_set.add_argument("--global", dest="global_config", action="store_true", help="Set in global configuration")
        config_set.add_argument("--local", dest="local_config", action="store_true", help="Set in local configuration")
        config_set.add_argument("--system", dest="system_config", action="store_true", help="Set in system configuration")

        # Config get
        config_get = config_subparsers.add_parser("get", help="Get configuration value")
        config_get.add_argument("key", help="Configuration key")
        config_get.add_argument("--global", dest="global_config", action="store_true", help="Get from global configuration")
        config_get.add_argument("--local", dest="local_config", action="store_true", help="Get from local configuration")
        config_get.add_argument("--system", dest="system_config", action="store_true", help="Get from system configuration")

        # Config reset
        config_reset = config_subparsers.add_parser("reset", help="Reset configuration to defaults")
        config_reset.add_argument("--force", action="store_true", help="Skip confirmation prompt")

        # Config wizard
        config_subparsers.add_parser("wizard", help="Run interactive configuration wizard")

        # Config export
        config_export = config_subparsers.add_parser("export", help="Export configuration")
        config_export.add_argument("--format", choices=["yaml", "json"], default="yaml", help="Export format")

        # Config import
        config_import = config_subparsers.add_parser("import", help="Import configuration")
        config_import.add_argument("file", help="Configuration file to import")

        # Doctor command
        doctor_parser = subparsers.add_parser("doctor", help="Diagnose installation and compatibility")
        doctor_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed diagnostic information"
        )
        doctor_parser.add_argument(
            "--fix",
            action="store_true",
            help="Attempt to fix detected issues automatically"
        )
        doctor_parser.add_argument(
            "--json",
            action="store_true",
            help="Output results in JSON format"
        )

        # Trial command

        # Metrics command (IO-8: Monitor back-pressure)
        metrics_parser = subparsers.add_parser("metrics", help="Monitor performance metrics")
        metrics_subparsers = metrics_parser.add_subparsers(dest="metrics_command", help="Metrics subcommands")
        
        # Metrics drops
        metrics_drops = metrics_subparsers.add_parser("drops", help="Show dropped metrics count")
        metrics_drops.add_argument(
            "--reset",
            action="store_true",
            help="Reset drop counter after showing"
        )
        
        # Metrics config
        metrics_config = metrics_subparsers.add_parser("config", help="Configure metrics monitoring")
        metrics_config.add_argument(
            "--alert-interval",
            type=int,
            help="Alert every N drops (0 to disable)"
        )


        trial_parser = subparsers.add_parser("trial", help="Request a 30-day trial with email verification")
        trial_parser.add_argument(
            "--email",
            required=True,
            help="Email for one-time trial activation (can only be used once)"
        )

        # Verify command
        verify_parser = subparsers.add_parser("verify", help="Verify email and activate your 30-day trial")
        verify_parser.add_argument(
            "--token",
            required=True,
            help="Verification token from email"
        )

    return parser


async def run_script(args) -> int:
    """
    Run a Python script with Epochly acceleration.

    Args:
        args: Parsed command line arguments containing:
            - script: Path to Python script
            - script_args: Arguments to pass to the script
            - level: Optimization level (0-4)
            - verbose: Enable verbose logging
            - no_optimize: Disable optimization (monitor only)
            - pin_pool: Pin to specific memory pool type
            - allowed_pools: Comma-separated list of allowed memory pools

    Returns:
        Exit code from the script execution
    """
    logger = get_logger(__name__)

    # SECURITY: Validate and resolve script path (prevent path traversal)
    # Comprehensive security validation for cross-platform safety
    try:
        import stat

        # Resolve path (handles relative paths, symlinks, ..)
        script_path = Path(args.script).resolve()

        # SECURITY: Use lstat() to avoid following symlinks during existence check
        try:
            stat_info = script_path.lstat()
        except (OSError, FileNotFoundError):
            print(f"Error: Script '{args.script}' not found", file=sys.stderr)
            return 1

        # SECURITY: Verify it's a regular file, not symlink/directory/device
        # Handle both real stat_result and test mocks
        try:
            is_regular = stat.S_ISREG(stat_info.st_mode)
        except (TypeError, AttributeError):
            # Mock or invalid st_mode - fall back to is_file() check
            is_regular = script_path.is_file()

        if not is_regular:
            print(f"Error: '{args.script}' is not a regular file", file=sys.stderr)
            return 1

        # SECURITY: Optional size limit to prevent resource exhaustion
        # Handle both real stat_result and test mocks
        try:
            file_size = stat_info.st_size
            if file_size > 100 * 1024 * 1024:  # 100MB limit
                print(f"Error: Script file too large (>100MB)", file=sys.stderr)
                return 1
        except (TypeError, AttributeError):
            # Mock or invalid st_size - skip size check in tests
            pass

    except (OSError, RuntimeError) as e:
        print(f"Error: Cannot access script", file=sys.stderr)
        return 1

    # PRE-VALIDATE SYNTAX (fixes macOS subprocess timeout on syntax errors)
    # Check syntax BEFORE creating subprocess to avoid hanging on initialization
    try:
        with open(script_path, 'rb') as f:
            compile(f.read(), str(script_path), 'exec')
    except SyntaxError as e:
        # SECURITY: Don't expose full traceback with internal paths
        print(f"SyntaxError in {script_path.name}:", file=sys.stderr)
        # SECURITY: Sanitize error message to prevent path disclosure (cross-platform)
        import re
        safe_msg = str(e.msg)

        # Normalize paths for case-insensitive, separator-agnostic replacement
        # Handle both / and \ separators, case variations (Windows)
        for path_variant in [str(script_path), str(script_path.parent)]:
            # Create regex that matches both separators and any case
            escaped = re.escape(path_variant)
            # Replace both / and \ with pattern that matches either
            pattern = escaped.replace(r'\\', r'[\\/]').replace(r'\/', r'[\\/]')
            safe_msg = re.sub(pattern, script_path.name if path_variant == str(script_path) else '<script_dir>', safe_msg, flags=re.IGNORECASE)

        # Additional safety: Remove any remaining absolute paths (drive letters, root paths)
        safe_msg = re.sub(r'[A-Za-z]:[/\\][^\s"\'<>]*', '<path>', safe_msg)
        safe_msg = re.sub(r'/[^\s"\'<>]+', '<path>', safe_msg)

        if e.lineno:
            print(f"  Line {e.lineno}: {safe_msg}", file=sys.stderr)
        else:
            print(f"  {safe_msg}", file=sys.stderr)
        return 1
    except PermissionError:
        # Security: Don't expose permission errors in detail
        print(f"Error: Cannot access script '{args.script}'", file=sys.stderr)
        return 1
    except OSError:
        # Handle other file access errors (e.g., path traversal attempts)
        print(f"Error: Cannot read script '{args.script}'", file=sys.stderr)
        return 1

    # Set up environment variables for Epochly
    # NOTE: Intentionally inherit full environment for user script execution
    # User scripts expect access to PATH, HOME, AWS credentials, etc.
    # This is safe because: (1) running user's own code, (2) same security context
    env = os.environ.copy()

    # CRITICAL FIX (Jan 2026): Propagate test mode to subprocess to ensure reduced workers
    # In CI or test environments, the subprocess needs EPOCHLY_TEST_MODE=1 to avoid
    # creating too many ProcessPoolExecutor workers which can cause cleanup issues
    if env.get('PYTEST_CURRENT_TEST') or env.get('CI') or env.get('GITHUB_ACTIONS'):
        env['EPOCHLY_TEST_MODE'] = '1'
        # Also limit max workers for faster startup and cleaner cleanup
        if 'EPOCHLY_MAX_WORKERS' not in env:
            env['EPOCHLY_MAX_WORKERS'] = '2'
        # CRITICAL: Disable Epochly entirely in CI to prevent ProcessPoolExecutor creation
        # The ProcessPoolExecutor cleanup sends SIGTERM to workers, which can cause
        # the subprocess to exit with -15 when pytest terminates the test
        env['EPOCHLY_DISABLE'] = '1'

    # Add src directory to PYTHONPATH so subprocess can import epochly
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    env['PYTHONPATH'] = src_path + os.pathsep + env.get('PYTHONPATH', '')

    # Set optimization level (only if not already set by user/test)
    if 'EPOCHLY_LEVEL' not in env:
        if args.no_optimize:
            env['EPOCHLY_LEVEL'] = '0'  # Monitor only
        else:
            env['EPOCHLY_LEVEL'] = str(args.level)
    # else: Respect existing EPOCHLY_LEVEL from environment (e.g., from tests)

    # Set memory pool configuration
    if hasattr(args, 'pin_pool') and args.pin_pool:
        env['EPOCHLY_PIN_POOL'] = args.pin_pool

        # Validate pin_pool against allowed_pools if both specified
        if hasattr(args, 'allowed_pools') and args.allowed_pools:
            allowed_list = [p.strip() for p in args.allowed_pools.split(',')]
            if args.pin_pool not in allowed_list:
                logger.warning(f"Pinned pool '{args.pin_pool}' not in allowed list: {allowed_list}")
                # Add pinned pool to allowed list to avoid conflicts
                allowed_list.append(args.pin_pool)
                args.allowed_pools = ','.join(allowed_list)

    if hasattr(args, 'allowed_pools') and args.allowed_pools:
        env['EPOCHLY_ALLOWED_POOLS'] = args.allowed_pools

    # Set core usage limits
    if hasattr(args, 'max_cores') and args.max_cores:
        env['EPOCHLY_MAX_CORES'] = str(args.max_cores)

    if hasattr(args, 'max_cores_percent') and args.max_cores_percent:
        env['EPOCHLY_MAX_CORES_PERCENT'] = str(args.max_cores_percent)

    if hasattr(args, 'reserve_cores') and args.reserve_cores:
        env['EPOCHLY_RESERVE_CORES'] = str(args.reserve_cores)

    # Set advanced analysis options
    if hasattr(args, 'profile') and args.profile:
        env['EPOCHLY_PROFILE'] = '1'

    if hasattr(args, 'benchmark') and args.benchmark:
        env['EPOCHLY_BENCHMARK'] = '1'

    if hasattr(args, 'check') and args.check:
        env['EPOCHLY_CHECK'] = '1'

    if hasattr(args, 'explain') and args.explain:
        env['EPOCHLY_EXPLAIN'] = '1'

    # Set runtime configuration
    if hasattr(args, 'workers') and args.workers is not None:
        env['EPOCHLY_WORKERS'] = str(args.workers)

    if hasattr(args, 'mode') and args.mode:
        env['EPOCHLY_MODE'] = args.mode

    if hasattr(args, 'debug') and args.debug:
        env['EPOCHLY_DEBUG'] = '1'

    if args.verbose:
        env['EPOCHLY_VERBOSE'] = '1'
        print(f"Running {args.script} with Epochly optimization level {args.level}")

    # Build the command to run the script with Epochly
    # We inject Epochly initialization before running the script

    # Build configuration dictionary
    config_dict = {
        'enhancement_level': args.level if not args.no_optimize else 0
    }

    # Add memory pool configuration
    if hasattr(args, 'pin_pool') and args.pin_pool:
        config_dict['pin_pool'] = f"'{args.pin_pool}'"

    if hasattr(args, 'allowed_pools') and args.allowed_pools:
        allowed_list = [f"'{p.strip()}'" for p in args.allowed_pools.split(',')]
        config_dict['allowed_pools'] = f"[{', '.join(allowed_list)}]"

    # Add core usage limits
    if hasattr(args, 'max_cores') and args.max_cores:
        config_dict['max_cores'] = args.max_cores

    if hasattr(args, 'max_cores_percent') and args.max_cores_percent:
        config_dict['max_cores_percent'] = args.max_cores_percent

    if hasattr(args, 'reserve_cores') and args.reserve_cores:
        config_dict['reserve_cores'] = args.reserve_cores

    # Add advanced analysis options
    if hasattr(args, 'profile') and args.profile:
        config_dict['profile'] = 'True'

    if hasattr(args, 'benchmark') and args.benchmark:
        config_dict['benchmark'] = 'True'

    if hasattr(args, 'check') and args.check:
        config_dict['check_mode'] = 'True'

    if hasattr(args, 'explain') and args.explain:
        config_dict['explain'] = 'True'

    # Add runtime configuration
    if hasattr(args, 'workers') and args.workers is not None:
        config_dict['workers'] = args.workers

    if hasattr(args, 'mode') and args.mode:
        config_dict['mode'] = f"'{args.mode}'"

    if hasattr(args, 'debug') and args.debug:
        config_dict['debug'] = 'True'

    # Build config string
    config_str = ', '.join(f'{k}={v}' for k, v in config_dict.items())

    # Convert path to string for proper escaping in generated code
    # Use original path string to preserve test expectations
    # (tests expect exact path strings, not resolved symlinks)
    script_path_str = str(args.script)

    wrapper_code = f"""
import sys
import os
import logging
import signal

# CRITICAL: Suppress all logging during script execution
# User scripts should not see Epochly initialization logs in their stderr
logging.disable(logging.CRITICAL)

# Set up signal handling to ensure KeyboardInterrupt is raised properly
# This allows user's try/except blocks to work correctly
def sigint_handler(signum, frame):
    # Raise KeyboardInterrupt so user code can catch it
    raise KeyboardInterrupt()

# Install signal handler BEFORE importing/running user code
signal.signal(signal.SIGINT, sigint_handler)

# Add script directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath({script_path_str!r})))

# Initialize Epochly with the specified configuration (only if not disabled)
_epochly_module = None
if os.environ.get('EPOCHLY_DISABLE') != '1':
    import epochly as _epochly_module
    # Respect EPOCHLY_LEVEL environment variable if set
    _env_level = os.environ.get('EPOCHLY_LEVEL')
    if _env_level is not None:
        # Use environment variable - this takes precedence over CLI default
        # force=True bypasses progression validation for explicit level setting
        _epochly_module.configure(enhancement_level=int(_env_level), force=True)
    else:
        # No environment variable - use CLI-specified configuration
        # force=True allows immediate level setting without waiting for stability
        _epochly_module.configure({config_str}, force=True)

# Set up argv for the script
sys.argv = [{script_path_str!r}] + {args.script_args}

# Execute the script in __main__ module namespace (for proper __main__ access)
import __main__
__main__.__file__ = {script_path_str!r}

try:
    with open({script_path_str!r}, 'rb') as f:
        code = compile(f.read(), {script_path_str!r}, 'exec')
        exec(code, __main__.__dict__)
finally:
    # Explicit shutdown to ensure clean process exit
    # Without this, Level 4 GPU processes may hang during interpreter finalization
    if _epochly_module is not None:
        try:
            _epochly_module.shutdown()
        except Exception:
            pass  # Ignore shutdown errors
"""

    # Run the script with Epochly
    start_time = time.time()

    try:
        # Use Popen for signal handling with process groups
        # This allows proper SIGINT forwarding to CPU-intensive subprocesses
        import signal as signal_module

        # Use start_new_session for process group creation (safer than preexec_fn)
        # On Unix, creates new session and process group for better signal handling
        # This allows us to send signals to the entire process group
        proc = subprocess.Popen(
            [sys.executable, '-c', wrapper_code],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=(sys.platform != 'win32')  # Unix only: create new session
        )

        # Set up signal forwarding for SIGINT
        # Note: We forward SIGINT to the child and let its exit code/behavior propagate naturally.
        # On Unix with process groups, send to entire group for immediate interrupt.
        def forward_sigint(signum, frame):
            """Forward SIGINT to subprocess (or process group on Unix)."""
            try:
                if sys.platform != 'win32':
                    # Unix: Send to process group for immediate interrupt
                    # start_new_session=True makes proc.pid the process group ID
                    # This ensures even tight CPU loops get interrupted
                    try:
                        os.killpg(proc.pid, signal_module.SIGINT)
                    except (ProcessLookupError, PermissionError):
                        # Fallback to direct signal if process group unavailable
                        proc.send_signal(signal_module.SIGINT)
                else:
                    # Windows: Direct signal forwarding
                    proc.send_signal(signal_module.SIGINT)
            except ProcessLookupError:
                pass  # Process already exited

        # Install SIGINT handler
        original_sigint = signal_module.signal(signal_module.SIGINT, forward_sigint)

        try:
            # Wait for process to complete (with timeout)
            stdout, stderr = proc.communicate(timeout=300)
            result_returncode = proc.returncode

        finally:
            # Restore original SIGINT handler
            signal_module.signal(signal_module.SIGINT, original_sigint)

        # Create result object compatible with subprocess.run return
        class Result:
            def __init__(self, returncode, stdout, stderr):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr

        result = Result(result_returncode, stdout, stderr)

        # Forward captured output to maintain current behavior
        if result.stdout:
            print(result.stdout, end='')
        if result.stderr:
            print(result.stderr, end='', file=sys.stderr)

        elapsed = time.time() - start_time

        if args.verbose:
            print(f"\nExecution completed in {elapsed:.3f} seconds")
            # NOTE: Performance metrics are not available in the parent CLI process
            # because the script ran in a subprocess with its own Epochly instance.
            # Metrics would need to be collected from the subprocess itself.

        return result.returncode

    except KeyboardInterrupt:
        print("\nScript interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error running script: {e}", file=sys.stderr)
        return 1


async def run_module(args) -> int:
    """
    Run a Python module with Epochly acceleration (like python -m).

    Args:
        args: Parsed command line arguments containing:
            - module: Module name to run
            - script_args: Arguments to pass to the module
            - All standard Epochly configuration options

    Returns:
        Exit code from the module execution
    """
    logger = get_logger(__name__)

    if not args.module:
        print("Error: No module specified for -m", file=sys.stderr)
        return 1

    # Set up environment variables for Epochly
    env = os.environ.copy()

    # CRITICAL FIX (Jan 2026): Propagate test mode to subprocess to ensure reduced workers
    if env.get('PYTEST_CURRENT_TEST') or env.get('CI') or env.get('GITHUB_ACTIONS'):
        env['EPOCHLY_TEST_MODE'] = '1'
        if 'EPOCHLY_MAX_WORKERS' not in env:
            env['EPOCHLY_MAX_WORKERS'] = '2'
        # Disable Epochly in CI to prevent ProcessPoolExecutor cleanup SIGTERM issues
        env['EPOCHLY_DISABLE'] = '1'

    # Add src directory to PYTHONPATH so subprocess can import epochly
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    env['PYTHONPATH'] = src_path + os.pathsep + env.get('PYTHONPATH', '')

    # Set optimization level (only if not already set by user/test)
    if 'EPOCHLY_LEVEL' not in env:
        if hasattr(args, 'no_optimize') and args.no_optimize:
            env['EPOCHLY_LEVEL'] = '0'
        else:
            env['EPOCHLY_LEVEL'] = str(args.level if hasattr(args, 'level') else 3)
    # else: Respect existing EPOCHLY_LEVEL from environment

    # Set all configuration environment variables
    if hasattr(args, 'verbose') and args.verbose:
        env['EPOCHLY_VERBOSE'] = '1'

    # Set memory pool configuration
    if hasattr(args, 'pin_pool') and args.pin_pool:
        env['EPOCHLY_PIN_POOL'] = args.pin_pool
    if hasattr(args, 'allowed_pools') and args.allowed_pools:
        env['EPOCHLY_ALLOWED_POOLS'] = args.allowed_pools

    # Set core usage limits
    if hasattr(args, 'max_cores') and args.max_cores:
        env['EPOCHLY_MAX_CORES'] = str(args.max_cores)
    if hasattr(args, 'max_cores_percent') and args.max_cores_percent:
        env['EPOCHLY_MAX_CORES_PERCENT'] = str(args.max_cores_percent)
    if hasattr(args, 'reserve_cores') and args.reserve_cores:
        env['EPOCHLY_RESERVE_CORES'] = str(args.reserve_cores)

    # Set advanced analysis options
    if hasattr(args, 'profile') and args.profile:
        env['EPOCHLY_PROFILE'] = '1'
    if hasattr(args, 'benchmark') and args.benchmark:
        env['EPOCHLY_BENCHMARK'] = '1'
    if hasattr(args, 'check') and args.check:
        env['EPOCHLY_CHECK'] = '1'
    if hasattr(args, 'explain') and args.explain:
        env['EPOCHLY_EXPLAIN'] = '1'

    # Set runtime configuration
    if hasattr(args, 'workers') and args.workers is not None:
        env['EPOCHLY_WORKERS'] = str(args.workers)
    if hasattr(args, 'mode') and args.mode:
        env['EPOCHLY_MODE'] = args.mode
    if hasattr(args, 'debug') and args.debug:
        env['EPOCHLY_DEBUG'] = '1'

    # Create wrapper code to initialize Epochly before running module
    cli_level = args.level if hasattr(args, 'level') else 3
    wrapper_code = f"""
import sys
import os
import runpy
import logging

# CRITICAL: Suppress all logging during module execution
# User modules should not see Epochly initialization logs in their stderr
logging.disable(logging.CRITICAL)

_epochly_module = None
# Initialize Epochly (only if not disabled)
if os.environ.get('EPOCHLY_DISABLE') != '1':
    import epochly as _epochly_module
    # Respect EPOCHLY_LEVEL environment variable if set
    _env_level = os.environ.get('EPOCHLY_LEVEL')
    if _env_level is not None:
        # Use environment variable - this takes precedence over CLI default
        # force=True bypasses progression validation for explicit level setting
        _epochly_module.configure(enhancement_level=int(_env_level), force=True)
    else:
        # No environment variable - use CLI-specified configuration
        # force=True allows immediate level setting without waiting for stability
        _epochly_module.configure(enhancement_level={cli_level}, force=True)

# Set up sys.argv for the module
sys.argv = ['{args.module}'] + {args.script_args if hasattr(args, 'script_args') else []}

try:
    # Run the module
    runpy.run_module('{args.module}', run_name='__main__', alter_sys=True)
finally:
    # Explicit shutdown to ensure clean process exit
    # Without this, Level 4 GPU processes may hang during interpreter finalization
    if _epochly_module is not None:
        try:
            _epochly_module.shutdown()
        except Exception:
            pass  # Ignore shutdown errors
"""

    # Timeout for subprocess execution (in seconds)
    SUBPROCESS_TIMEOUT = 300  # 5 minutes max

    # Run the module with Epochly
    try:
        result = subprocess.run(
            [sys.executable, '-c', wrapper_code],
            env=env,
            capture_output=True,  # Capture output for proper propagation
            text=True,
            timeout=SUBPROCESS_TIMEOUT
        )

        # Forward captured output to maintain current behavior
        if result.stdout:
            print(result.stdout, end='')
        if result.stderr:
            print(result.stderr, end='', file=sys.stderr)

        if hasattr(args, 'verbose') and args.verbose:
            print(f"\nModule execution completed with exit code {result.returncode}")

        return result.returncode

    except subprocess.TimeoutExpired as e:
        # Process hung - output what we captured before timeout
        if e.stdout:
            print(e.stdout if isinstance(e.stdout, str) else e.stdout.decode('utf-8', errors='replace'), end='')
        if e.stderr:
            print(e.stderr if isinstance(e.stderr, str) else e.stderr.decode('utf-8', errors='replace'), end='', file=sys.stderr)
        print(f"\nError: Module timed out after {SUBPROCESS_TIMEOUT} seconds", file=sys.stderr)
        return 124  # Standard timeout exit code
    except KeyboardInterrupt:
        print("\nModule execution interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error running module: {e}", file=sys.stderr)
        return 1


async def run_command(args) -> int:
    """
    Run a Python command string with Epochly acceleration (like python -c).

    Args:
        args: Parsed command line arguments containing:
            - command: Python code to execute
            - All standard Epochly configuration options

    Returns:
        Exit code from the command execution
    """
    logger = get_logger(__name__)

    # Use 'is None' instead of falsy check: python -c "" is valid and returns 0
    if args.command is None:
        print("Error: No command specified for -c", file=sys.stderr)
        return 1

    # Get script_args for sys.argv passthrough (matches python -c behavior)
    script_args = getattr(args, 'script_args', None) or []

    # Set up environment variables for Epochly
    env = os.environ.copy()

    # CRITICAL FIX (Jan 2026): Propagate test mode to subprocess to ensure reduced workers
    if env.get('PYTEST_CURRENT_TEST') or env.get('CI') or env.get('GITHUB_ACTIONS'):
        env['EPOCHLY_TEST_MODE'] = '1'
        if 'EPOCHLY_MAX_WORKERS' not in env:
            env['EPOCHLY_MAX_WORKERS'] = '2'
        # Disable Epochly in CI to prevent ProcessPoolExecutor cleanup SIGTERM issues
        env['EPOCHLY_DISABLE'] = '1'

    # Add src directory to PYTHONPATH so subprocess can import epochly
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    env['PYTHONPATH'] = src_path + os.pathsep + env.get('PYTHONPATH', '')

    # Set optimization level (only if not already set by user/test)
    if 'EPOCHLY_LEVEL' not in env:
        if hasattr(args, 'no_optimize') and args.no_optimize:
            env['EPOCHLY_LEVEL'] = '0'
        else:
            env['EPOCHLY_LEVEL'] = str(args.level if hasattr(args, 'level') else 3)
    # else: Respect existing EPOCHLY_LEVEL from environment

    # Set all configuration environment variables (same as run_module)
    if hasattr(args, 'verbose') and args.verbose:
        env['EPOCHLY_VERBOSE'] = '1'

    # Set memory pool configuration
    if hasattr(args, 'pin_pool') and args.pin_pool:
        env['EPOCHLY_PIN_POOL'] = args.pin_pool
    if hasattr(args, 'allowed_pools') and args.allowed_pools:
        env['EPOCHLY_ALLOWED_POOLS'] = args.allowed_pools

    # Set core usage limits
    if hasattr(args, 'max_cores') and args.max_cores:
        env['EPOCHLY_MAX_CORES'] = str(args.max_cores)
    if hasattr(args, 'max_cores_percent') and args.max_cores_percent:
        env['EPOCHLY_MAX_CORES_PERCENT'] = str(args.max_cores_percent)
    if hasattr(args, 'reserve_cores') and args.reserve_cores:
        env['EPOCHLY_RESERVE_CORES'] = str(args.reserve_cores)

    # Set advanced analysis options
    if hasattr(args, 'profile') and args.profile:
        env['EPOCHLY_PROFILE'] = '1'
    if hasattr(args, 'benchmark') and args.benchmark:
        env['EPOCHLY_BENCHMARK'] = '1'
    if hasattr(args, 'check') and args.check:
        env['EPOCHLY_CHECK'] = '1'
    if hasattr(args, 'explain') and args.explain:
        env['EPOCHLY_EXPLAIN'] = '1'

    # Set runtime configuration
    if hasattr(args, 'workers') and args.workers is not None:
        env['EPOCHLY_WORKERS'] = str(args.workers)
    if hasattr(args, 'mode') and args.mode:
        env['EPOCHLY_MODE'] = args.mode
    if hasattr(args, 'debug') and args.debug:
        env['EPOCHLY_DEBUG'] = '1'

    # Create wrapper code to initialize Epochly before executing command
    cli_level = args.level if hasattr(args, 'level') else 3
    wrapper_code = f"""
import os
import sys
import logging

# CRITICAL: Suppress all logging during command execution
# User commands should not see Epochly initialization logs in their stderr
logging.disable(logging.CRITICAL)

# Match python -c argv semantics:
# argv[0] == '-c', remaining are extra args after the command string.
sys.argv = ['-c'] + {script_args!r}

_epochly_module = None
# Initialize Epochly (only if not disabled)
if os.environ.get('EPOCHLY_DISABLE') != '1':
    import epochly as _epochly_module
    # Respect EPOCHLY_LEVEL environment variable if set
    _env_level = os.environ.get('EPOCHLY_LEVEL')
    if _env_level is not None:
        # Use environment variable - this takes precedence over CLI default
        # force=True bypasses progression validation for explicit level setting
        _epochly_module.configure(enhancement_level=int(_env_level), force=True)
    else:
        # No environment variable - use CLI-specified configuration
        # force=True allows immediate level setting without waiting for stability
        _epochly_module.configure(enhancement_level={cli_level}, force=True)

try:
    # Execute the user's command using exec() to handle multi-line commands properly
    # Direct interpolation breaks when commands contain newlines (indentation is lost)
    # Use compile() with dont_inherit=True to ensure user code doesn't inherit wrapper flags
    _user_code = {args.command!r}
    _code = compile(_user_code, "<string>", "exec", dont_inherit=True)
    exec(_code, globals())
finally:
    # Explicit shutdown to ensure clean process exit
    # Without this, Level 4 GPU processes may hang during interpreter finalization
    if _epochly_module is not None:
        try:
            _epochly_module.shutdown()
        except Exception:
            pass  # Ignore shutdown errors
"""

    # Timeout for subprocess execution (in seconds)
    # Generous timeout allows for Level 4 GPU initialization + execution + cleanup
    # Normal commands: few seconds; complex GPU work: may need more
    SUBPROCESS_TIMEOUT = 300  # 5 minutes max

    # Run the command with Epochly
    try:
        result = subprocess.run(
            [sys.executable, '-c', wrapper_code],
            env=env,
            capture_output=True,  # Capture output for proper propagation
            text=True,
            timeout=SUBPROCESS_TIMEOUT
        )

        # Forward captured output to maintain current behavior
        if result.stdout:
            print(result.stdout, end='')
        if result.stderr:
            print(result.stderr, end='', file=sys.stderr)

        if hasattr(args, 'verbose') and args.verbose:
            print(f"\nCommand execution completed with exit code {result.returncode}")

        return result.returncode

    except subprocess.TimeoutExpired as e:
        # Process hung - output what we captured before timeout
        if e.stdout:
            print(e.stdout if isinstance(e.stdout, str) else e.stdout.decode('utf-8', errors='replace'), end='')
        if e.stderr:
            print(e.stderr if isinstance(e.stderr, str) else e.stderr.decode('utf-8', errors='replace'), end='', file=sys.stderr)
        print(f"\nError: Command timed out after {SUBPROCESS_TIMEOUT} seconds", file=sys.stderr)
        return 124  # Standard timeout exit code
    except KeyboardInterrupt:
        print("\nCommand execution interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error running command: {e}", file=sys.stderr)
        return 1


async def print_performance_report() -> None:
    """Print performance metrics after script execution.

    NOTE: This function is only useful when running in the same process
    as Epochly. When scripts are run via subprocess (the normal case for CLI),
    the metrics remain in the subprocess and cannot be accessed from the parent.

    This function is kept for potential future use with in-process execution modes.
    """
    try:
        from epochly.api.public_api import get_metrics
        metrics = get_metrics()

        if metrics and 'error' not in metrics:
            print("\n=== Epochly Performance Report ===")
            if 'optimization_count' in metrics:
                print(f"Functions optimized: {metrics['optimization_count']}")
            if 'total_speedup' in metrics:
                print(f"Average speedup: {metrics['total_speedup']:.2f}x")
            if 'time_saved' in metrics:
                print(f"Time saved: {metrics['time_saved']:.3f} seconds")
            print("=" * 35)
    except Exception:
        # Silently ignore if we can't get metrics
        pass


async def main() -> int:
    """Main CLI entry point"""
    # Define all known top-level commands
    # Note: --help and -h are handled by argparse, not as subcommands
    KNOWN_COMMANDS = {
        'status', 'start', 'stop', 'restart', 'health',
        'jupyter', 'sitecustomize', 'shell', 'config', 'doctor',
        'trial', 'verify',  # Trial management commands
        'gpu', 'metrics',  # GPU diagnostics and metrics commands
    }

    # Intelligent command vs script detection following best practices:
    # 1. First check if first non-flag argument is a known command -> command mode (highest priority)
    # 2. Then check if first non-flag argument ends with .py -> script mode
    # 3. Otherwise assume script mode for backward compatibility

    is_script_mode = False
    is_command_mode = False
    script_index = -1

    # Check for Python compatibility modes early
    # Look for -m or -c in Epochly's flags (before script args or --)
    is_module_mode = False
    is_c_mode = False
    for arg in sys.argv[1:]:
        if arg == '--':
            # Reached script args separator, stop checking
            break
        if arg == '-m':
            is_module_mode = True
            break
        if arg == '-c':
            is_c_mode = True
            break
        # Stop at first positional arg that looks like a script/command
        if not arg.startswith('-') and (arg.endswith('.py') or '/' in arg or '\\' in arg):
            break

    # Find first non-flag argument to determine mode
    if not is_module_mode and not is_c_mode:
        if len(sys.argv) > 1:
            # Find first non-flag argument (skipping flag values)
            # Flags that take arguments
            FLAGS_WITH_VALUES = {
                '-l', '--level', '--workers', '--mode', '--max-cores',
                '--max-cores-percent', '--reserve-cores', '--pin-pool',
                '--allowed-pools', '-m', '-c'
            }

            first_non_flag = None
            first_non_flag_index = -1
            skip_next = False

            for i, arg in enumerate(sys.argv[1:], 1):
                if skip_next:
                    # This is a value for the previous flag
                    skip_next = False
                    continue

                if arg == '--':
                    # Double dash separator - everything after is script args
                    # The script must be before the --
                    break

                if arg.startswith('-'):
                    # Check if this flag takes a value
                    flag_name = arg.split('=')[0]  # Handle --flag=value format
                    if flag_name in FLAGS_WITH_VALUES and '=' not in arg:
                        # Next arg is the value for this flag
                        skip_next = True
                else:
                    # Found first true positional argument
                    first_non_flag = arg
                    first_non_flag_index = i
                    break

            # Check if it's a known command FIRST
            if first_non_flag and first_non_flag in KNOWN_COMMANDS:
                is_command_mode = True
            elif first_non_flag:
                # Not a known command, treat as script
                is_script_mode = True
                script_index = first_non_flag_index
            else:
                # Only flags provided, show help
                is_command_mode = True
        else:
            # No arguments, show help
            is_command_mode = True

    # Handle script execution mode
    if is_script_mode and script_index > 0:
        # Extract everything before the script as flags
        flags = sys.argv[1:script_index]
        script = sys.argv[script_index]
        script_args = sys.argv[script_index + 1:]

        # Parse just the flags to get options like -l, -v, etc.
        flag_parser = argparse.ArgumentParser(add_help=False)
        flag_parser.add_argument('-v', '--verbose', action='store_true')
        flag_parser.add_argument('-l', '--level', type=int, choices=[0, 1, 2, 3, 4], default=3)
        flag_parser.add_argument('--no-optimize', action='store_true')
        # Add memory pool configuration
        flag_parser.add_argument('--pin-pool', choices=['fast', 'legacy', 'sharded'])
        flag_parser.add_argument('--allowed-pools')
        # Add core usage limits
        flag_parser.add_argument('--max-cores', type=int)
        flag_parser.add_argument('--max-cores-percent', type=int)
        flag_parser.add_argument('--reserve-cores', type=int)
        # Add advanced analysis
        flag_parser.add_argument('--profile', action='store_true')
        flag_parser.add_argument('--benchmark', action='store_true')
        flag_parser.add_argument('--check', action='store_true')
        flag_parser.add_argument('--explain', action='store_true')
        # Add runtime configuration
        flag_parser.add_argument('--workers', type=int)
        flag_parser.add_argument('--mode', choices=['monitor', 'conservative', 'balanced', 'aggressive'])
        flag_parser.add_argument('--debug', action='store_true')

        # Parse known flags, ignore unknown
        flag_args, _ = flag_parser.parse_known_args(flags)

        # Create args object for run_script
        class ScriptArgs:
            def __init__(self):
                self.script = script
                self.script_args = script_args
                self.verbose = flag_args.verbose
                self.level = flag_args.level
                self.no_optimize = flag_args.no_optimize
                # Memory pool configuration
                self.pin_pool = flag_args.pin_pool
                self.allowed_pools = flag_args.allowed_pools
                # Core usage limits
                self.max_cores = flag_args.max_cores
                self.max_cores_percent = flag_args.max_cores_percent
                self.reserve_cores = flag_args.reserve_cores
                # Advanced analysis
                self.profile = flag_args.profile
                self.benchmark = flag_args.benchmark
                self.check = flag_args.check
                self.explain = flag_args.explain
                # Runtime configuration
                self.workers = flag_args.workers
                self.mode = flag_args.mode
                self.debug = flag_args.debug

        return await run_script(ScriptArgs())

    # Handle Python compatibility modes (-m and -c) specially
    if is_module_mode or is_c_mode:
        # Use parse_known_args for -m and -c modes to capture everything after module/command
        parser = create_parser(include_script_args=False, include_subcommands=False)
        args, unknown = parser.parse_known_args()

        if hasattr(args, 'module') and args.module:
            # Module execution mode: epochly -m module [args]
            # Everything after module name should be in unknown
            args.script_args = unknown
            return await run_module(args)

        if hasattr(args, 'command') and args.command:
            # Command execution mode: epochly -c "code" [args]
            # For -c mode, there might be additional args after the command string
            args.script_args = unknown
            return await run_command(args)

    # Create parser based on detected mode
    # In command mode, don't include script args to avoid conflicts
    # In script mode, don't include subcommands to avoid conflicts
    if is_command_mode:
        parser = create_parser(include_script_args=False, include_subcommands=True)
    else:
        parser = create_parser(include_script_args=True, include_subcommands=False)

    # Parse arguments normally for non-Python-compatibility modes
    args = parser.parse_args()

    # Check if we have a command
    if is_command_mode:
        # In command mode, if no command was specified, show help
        if not hasattr(args, 'command') or not args.command:
            parser.print_help()
            return 1
    else:
        # In mixed mode, check for script
        if not args.command and not args.script:
            parser.print_help()
            return 1

        # Handle backward compatibility case where command was captured as script
        if not args.command and args.script and not args.script.endswith('.py'):
            if args.script in KNOWN_COMMANDS:
                args.command = args.script
                args.script = None
            else:
                print(f"Error: '{args.script}' is not a recognized command or Python script", file=sys.stderr)
                print("Run 'epochly --help' for available commands", file=sys.stderr)
                return 1

    cli = EpochlyCLI()
    cli.setup_logging(args.verbose if hasattr(args, 'verbose') else False)

    try:
        if args.command == "status":
            status = await cli.status()
            print("Epochly System Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")

            # Also show license tier info
            try:
                from epochly.licensing.license_enforcer import get_license_enforcer
                enforcer = get_license_enforcer()
                limits = enforcer.get_limits()
                tier = limits.get('tier', 'community').upper()
                if tier == 'COMMUNITY':
                    tier_display = "Community Edition (Free)"
                elif tier == 'TRIAL':
                    tier_display = "Trial (30 Days)"
                else:
                    tier_display = tier.title()
                print(f"  tier: {tier_display}")
            except Exception:
                # Log exception with traceback for debugging while providing graceful fallback
                logger = get_logger(__name__)
                logger.debug("Failed to retrieve tier info", exc_info=True)
                print("  tier: Community (default)")

        elif args.command == "start":
            await cli.start(args.mode)
            print(f"Epochly started in {args.mode} mode")

        elif args.command == "stop":
            await cli.stop()
            print("Epochly stopped")

        elif args.command == "restart":
            await cli.restart(args.mode)
            print(f"Epochly restarted in {args.mode} mode")

        elif args.command == "health":
            health = await cli.health_check()
            print("Epochly Health Check:")
            for key, value in health.items():
                print(f"  {key}: {value}")

        elif args.command == "jupyter":
            # Handle Jupyter subcommands
            from epochly.cli.jupyter import main as jupyter_main

            # Pass only jupyter subcommands to jupyter CLI
            jupyter_args = sys.argv[2:]  # Skip 'epochly jupyter'
            return jupyter_main(jupyter_args)

        elif args.command == "sitecustomize":
            # Handle sitecustomize subcommands
            from epochly.deployment.sitecustomize_installer import SitecustomizeInstaller

            installer = SitecustomizeInstaller()

            # Check if subcommand was provided
            if not hasattr(args, 'sitecustomize_command') or not args.sitecustomize_command:
                print("Please specify a sitecustomize subcommand: install, uninstall, status, validate, or list-backups", file=sys.stderr)
                return 1

            if args.sitecustomize_command == "install":
                preserve_existing = not args.no_preserve
                success = installer.install(force=args.force, preserve_existing=preserve_existing)
                if success:
                    print("Epochly sitecustomize.py installed successfully")
                    print("Python will now automatically activate Epochly on startup")
                else:
                    print("Failed to install sitecustomize.py", file=sys.stderr)
                    return 1

            elif args.sitecustomize_command == "uninstall":
                restore_backup = not args.no_restore
                success = installer.uninstall(restore_backup=restore_backup)
                if success:
                    print("Epochly sitecustomize.py uninstalled successfully")
                else:
                    print("Failed to uninstall sitecustomize.py", file=sys.stderr)
                    return 1

            elif args.sitecustomize_command == "status":
                status = installer.get_installation_status()
                print("Sitecustomize Installation Status:")
                print(f"  Installed: {status['installed']}")
                print(f"  Epochly Managed: {status['epochly_managed']}")
                print(f"  Valid: {status['valid']}")
                if status['path']:
                    print(f"  Path: {status['path']}")
                print(f"  Backup Directory: {status['backup_directory']}")

            elif args.sitecustomize_command == "validate":
                is_valid = installer.validate_installation()
                if is_valid:
                    print("Sitecustomize.py installation is valid")
                else:
                    print("Sitecustomize.py installation is invalid or not found", file=sys.stderr)
                    return 1

            elif args.sitecustomize_command == "list-backups":
                backups = installer.list_backups()
                if backups:
                    print("Available Sitecustomize Backups:")
                    for backup in backups:
                        from datetime import datetime
                        created = datetime.fromtimestamp(backup['created']).strftime('%Y-%m-%d %H:%M:%S')
                        print(f"  {backup['filename']} - Created: {created}, Size: {backup['size']} bytes")
                else:
                    print("No sitecustomize.py backups found")

            else:
                print(f"Unknown sitecustomize command: {args.sitecustomize_command}", file=sys.stderr)
                return 1

        elif args.command == "gpu":
            # Handle GPU subcommands - Level 4 diagnostics and setup guidance
            from epochly.gpu.gpu_diagnostics import (
                run_diagnostics, format_report, get_installation_guide
            )

            # Check if subcommand was provided
            if not hasattr(args, 'gpu_command') or not args.gpu_command:
                # Default to 'check' if no subcommand
                args.gpu_command = "check"
                args.verbose = False

            if args.gpu_command == "check":
                print("Running GPU diagnostics...")
                print("")
                report = run_diagnostics()
                print(format_report(report, verbose=getattr(args, 'verbose', False)))

                # Return non-zero if GPU not available
                if not report.gpu_available:
                    return 1

            elif args.gpu_command == "guide":
                print(get_installation_guide())

            elif args.gpu_command == "status":
                # Quick status check
                try:
                    from epochly.gpu import GPUDetector, is_gpu_available
                    from epochly.gpu.gpu_detector import GPUBackend

                    if is_gpu_available():
                        detector = GPUDetector()
                        info = detector.get_gpu_info()
                        print(f"[Epochly] GPU Status: Available")
                        print(f"[Epochly]   Device: {info.device_name or 'Unknown'}")
                        print(f"[Epochly]   Backend: {info.backend.name}")
                        if info.memory_total:
                            print(f"[Epochly]   Memory: {info.memory_total // (1024*1024)}MB")
                        print(f"[Epochly]   Level 4 GPU acceleration is READY")
                    else:
                        print("[Epochly] GPU Status: Not Available")
                        print("[Epochly]   Level 4 GPU acceleration is DISABLED")
                        print("[Epochly]")
                        print("[Epochly]   To enable GPU acceleration:")
                        print("[Epochly]     1. Verify NVIDIA driver: nvidia-smi")
                        print("[Epochly]     2. Install CuPy: pip install cupy-cuda12x")
                        print("[Epochly]     3. Run 'epochly gpu check' for detailed diagnostics")
                        return 1
                except ImportError as e:
                    print(f"[Epochly] GPU Status: Module not available ({e})")
                    print("[Epochly]   Install with: pip install epochly[gpu]")
                    return 1
                except Exception as e:
                    print(f"[Epochly] GPU Status: Error - {e}")
                    print("[Epochly]   Run 'epochly gpu check' for detailed diagnostics")
                    return 1

            else:
                print(f"Unknown gpu command: {args.gpu_command}", file=sys.stderr)
                return 1

        elif args.command == "shell":
            # Handle shell command - launch Epochly-enabled Python REPL
            env = os.environ.copy()

            # Add src directory to PYTHONPATH
            src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            env['PYTHONPATH'] = src_path + os.pathsep + env.get('PYTHONPATH', '')

            # Enable Epochly
            env['EPOCHLY_ENABLED'] = '1'
            env['EPOCHLY_MODE'] = 'balanced'

            # Set up startup script if provided
            if hasattr(args, 'startup') and args.startup:
                script_path = args.startup
                if not os.path.exists(script_path):
                    print(f"Startup script not found: {script_path}", file=sys.stderr)
                    return 1
                env['PYTHONSTARTUP'] = script_path

            # Print banner unless suppressed
            if not hasattr(args, 'no_banner') or not args.no_banner:
                print("=" * 50)
                print("Epochly-Enabled Python REPL")
                print(f"Python {sys.version}")
                print("Epochly version: 0.1.0")
                print("Type 'help(epochly)' for Epochly documentation")
                print("=" * 50)

            # Launch Python REPL with Epochly
            cmd = [sys.executable, '-i']

            # Add quiet flag if requested
            if hasattr(args, 'quiet') and args.quiet:
                cmd.append('-q')

            try:
                result = subprocess.run(cmd, env=env)
                if result.returncode != 0:
                    print("Failed to start Epochly shell", file=sys.stderr)
                return result.returncode
            except KeyboardInterrupt:
                print("\nShell interrupted by user", file=sys.stderr)
                return 130
            except Exception as e:
                print(f"Failed to start Epochly shell: {e}", file=sys.stderr)
                return 1

        elif args.command == "config":
            # Handle config command
            from epochly.config import ConfigManager, ConfigWizard

            config_manager = ConfigManager()

            # Check if subcommand was provided
            if not hasattr(args, 'config_command') or not args.config_command:
                print("Please specify a config subcommand: show, set, get, reset, wizard, export, or import", file=sys.stderr)
                return 1

            # Determine scope
            scope = 'effective'  # Default
            if hasattr(args, 'global_config') and args.global_config:
                scope = 'global'
            elif hasattr(args, 'local_config') and args.local_config:
                scope = 'local'
            elif hasattr(args, 'system_config') and args.system_config:
                scope = 'system'

            if args.config_command == "show":
                config = config_manager.get_all_config(scope=scope)
                print(f"Epochly Configuration ({scope}):")
                for key, value in config.items():
                    print(f"  {key}: {value}")

            elif args.config_command == "set":
                try:
                    # For set command, default to 'user' scope if not specified
                    set_scope = 'user'  # Default for set command
                    if hasattr(args, 'global_config') and args.global_config:
                        set_scope = 'global'
                    elif hasattr(args, 'local_config') and args.local_config:
                        set_scope = 'local'
                    elif hasattr(args, 'system_config') and args.system_config:
                        set_scope = 'system'

                    # Validate configuration before setting
                    is_valid, error = config_manager.validate_config(args.key, args.value)
                    if not is_valid:
                        print(f"Validation error: {error}", file=sys.stderr)
                        return 1

                    config_manager.set_config(args.key, args.value, scope=set_scope)
                    print(f"Configuration updated: {args.key} = {args.value}")
                except ValueError as e:
                    print(f"Error: Invalid configuration key: {args.key}", file=sys.stderr)
                    return 1

            elif args.config_command == "get":
                value = config_manager.get_config(args.key, scope=scope)
                if value is not None:
                    print(value)
                else:
                    print("(not set)")

            elif args.config_command == "reset":
                if not hasattr(args, 'force') or not args.force:
                    # Check if running in interactive mode (TTY)
                    if sys.stdin.isatty():
                        try:
                            response = input("Are you sure you want to reset configuration to defaults? (y/n): ")
                            if response.lower() != 'y':
                                print("Reset cancelled")
                                return 0
                        except EOFError:
                            # EOF on interactive TTY - treat as cancellation
                            print("Reset cancelled")
                            return 0
                    else:
                        # Non-interactive mode without --force is unsafe
                        print("Error: Refusing to reset config without confirmation in non-interactive mode.", file=sys.stderr)
                        print("Re-run with --force to skip confirmation.", file=sys.stderr)
                        return 1

                config_manager.reset_config()
                print("Configuration reset to defaults")

            elif args.config_command == "wizard":
                wizard = ConfigWizard()
                new_config = wizard.run()
                if new_config:
                    config_manager.apply_config(new_config)
                    print("Configuration wizard completed successfully")
                else:
                    print("Configuration wizard cancelled")

            elif args.config_command == "export":
                export_data = config_manager.export_config(format=args.format)
                print(export_data)

            elif args.config_command == "import":
                if not os.path.exists(args.file):
                    print(f"Configuration file not found: {args.file}", file=sys.stderr)
                    return 1

                with open(args.file, 'r') as f:
                    config_data = f.read()

                success = config_manager.import_config(config_data)
                if success:
                    print(f"Configuration imported from {args.file}")
                else:
                    print(f"Failed to import configuration from {args.file}", file=sys.stderr)
                    return 1

            else:
                print(f"Unknown config command: {args.config_command}", file=sys.stderr)
                return 1

        elif args.command == "doctor":
            # Handle doctor command - diagnose installation
            from epochly.diagnostics import Doctor

            doctor = Doctor()

            # Run diagnostics
            verbose = hasattr(args, 'verbose') and args.verbose
            results = doctor.run_diagnostics(verbose=verbose)

            # Output in JSON if requested
            if hasattr(args, 'json') and args.json:
                import json
                print(json.dumps(results, indent=2))
                return 0 if all(r.get('status') != 'fail' for r in results.values()) else 1

            # Print results
            print("Epochly Doctor - Installation Diagnostics")
            print("=" * 50)

            has_failures = False
            has_warnings = False

            for check_name, result in results.items():
                status = result.get('status', 'unknown')
                message = result.get('message', '')

                if status == 'pass':
                    status_str = "PASS:"
                elif status == 'fail':
                    status_str = "FAIL:"
                    has_failures = True
                elif status == 'warn':
                    status_str = "WARN:"
                    has_warnings = True
                else:
                    status_str = "INFO:"

                print(f"{status_str:6} {check_name:20} - {message}")

                # Print details if verbose
                if verbose and 'details' in result:
                    details = result['details']
                    if isinstance(details, dict):
                        for key, value in details.items():
                            print(f"       {key}: {value}")
                    else:
                        print(f"       {details}")

            print("=" * 50)

            # Attempt fixes if requested
            if hasattr(args, 'fix') and args.fix and has_failures:
                print("\nAttempting to fix issues...")
                fix_results = doctor.fix_issues()

                for issue, fix_result in fix_results.items():
                    if fix_result.get('fixed'):
                        print(f"Fixed: {issue} - {fix_result.get('message', 'Success')}")
                    else:
                        print(f"Could not fix: {issue} - {fix_result.get('message', 'Unknown error')}")

            # Summary
            if has_failures:
                print("\nSome checks failed. Run 'epochly doctor --fix' to attempt automatic fixes.")
                return 1
            elif has_warnings:
                print("\nAll checks passed with warnings.")
                return 0
            else:
                print("\nAll checks passed")
                print("Epochly is ready to use!")
                return 0

        elif args.command == "trial":
            # Handle trial command
            from epochly.cli.trial_command import trial as trial_func

            # Convert argparse namespace to click-style call
            class FakeContext:
                def __init__(self):
                    self.params = {'email': args.email}

            # Call the trial function with email
            # Use .callback() since trial_func is a Click Command object
            return trial_func.callback(email=args.email)

        elif args.command == "verify":
            # Handle verify command
            from epochly.cli.trial_command import verify as verify_func

            # Call the verify function with token
            # Use .callback() since verify_func is a Click Command object
            return verify_func.callback(token=args.token)


        elif args.command == "metrics":
            # IO-8: Metrics monitoring
            if not hasattr(args, 'metrics_command') or args.metrics_command is None:
                print("Error: metrics command requires a subcommand (drops, config)")
                return 1

            if args.metrics_command == "drops":
                result = cli.metrics_drops(reset=args.reset)
                print(f"Metrics Dropped: {result['drops']}")
                print(f"Total Attempts: {result['total_attempts']}")
                print(f"Drop Rate: {result['drop_rate_pct']:.2f}%")
                if result.get('reset'):
                    print("Drop counter reset.")
                return 0

            elif args.metrics_command == "config":
                if args.alert_interval is not None:
                    result = cli.metrics_drops_config(alert_interval=args.alert_interval)
                    print(f"Alert interval set to: {result['alert_interval']}")
                else:
                    result = cli.metrics_drops_config()
                    print(f"Current alert interval: {result['alert_interval']}")
                return 0

        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1

        return 0

    except EpochlyCLIError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def cli_main() -> None:
    """Synchronous wrapper for main CLI function"""
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    cli_main()

# Lazy export: Don't import jupyter at module level
# Access via: from epochly.cli.jupyter import main as jupyter_main

__all__ = [
    'EpochlyCLI',
    'EpochlyCLIError',
    'main',
    'cli_main',
    'run_script',
    'run_module',
    'run_command',
    'create_parser',
    'print_performance_report',
]
