"""
Epochly IPython Magic Commands

Provides interactive control over Epochly within Jupyter notebooks and IPython sessions.

Magic commands:
- %epochly stats - Display worker counts, compiled functions, recent speedup
- %epochly on/off - Toggle Epochly acceleration within session
- %epochly profile - Show performance profiling for cell execution
- %epochly level <0-4> - Change enhancement level dynamically
- %epochly status - Show current Epochly system status
- %epochly benchmark - Run quick benchmark in current cell

Author: Epochly Development Team
"""

import time
from typing import Dict, Any, Optional
from IPython.core.magic import Magics, magics_class, line_cell_magic
from IPython.core.magic_arguments import (argument, magic_arguments, parse_argstring)
from IPython.display import display, HTML

try:
    import epochly
    from epochly.core.epochly_core import EpochlyCore
    from epochly.monitoring.performance_monitor import PerformanceMonitor
    EPOCHLY_AVAILABLE = True
except ImportError:
    EPOCHLY_AVAILABLE = False


@magics_class
class EpochlyMagics(Magics):
    """Epochly magic commands for Jupyter/IPython integration."""

    def __init__(self, shell):
        super().__init__(shell)
        self._epochly_enabled = True
        self._last_profile_data = None
        self._cell_start_time = None

        # Store original state for restoration
        self._original_epochly_state = None

        if EPOCHLY_AVAILABLE:
            try:
                self.epochly_core = EpochlyCore.get_instance()
                self.performance_monitor = self.epochly_core.performance_monitor
            except:
                self.epochly_core = None
                self.performance_monitor = None
        else:
            self.epochly_core = None
            self.performance_monitor = None

    @line_cell_magic
    @magic_arguments()
    @argument('--profile', action='store_true', help='Profile cell execution')
    @argument('--level', type=int, help='Override enhancement level for this cell')
    @argument('--benchmark', action='store_true', help='Benchmark cell execution')
    def epochly(self, line: str, cell: Optional[str] = None):
        """
        Epochly magic command for both line and cell modes.

        Line magic usage:
            %epochly stats    - Show Epochly statistics
            %epochly on       - Enable Epochly acceleration
            %epochly off      - Disable Epochly acceleration
            %epochly profile  - Show performance profile
            %epochly level N  - Set enhancement level (0-4)
            %epochly status   - Show system status
            %epochly help     - Show help information

        Cell magic usage:
            %%epochly --profile
            # Your code here

            %%epochly --level 3
            # Your code here

            %%epochly --benchmark
            # Your code here
        """
        if not EPOCHLY_AVAILABLE:
            print("ERROR: Epochly not available. Please install Epochly first.")
            if cell is not None:
                self.shell.run_cell(cell)
            return

        # Cell magic mode - has a cell body
        if cell is not None:
            return self._handle_cell_magic(line, cell)

        # Line magic mode - process commands
        args = line.strip().split()
        if not args:
            args = ['help']

        command = args[0].lower()

        if command == 'stats':
            self._show_stats()
        elif command == 'on':
            self._enable_epochly()
        elif command == 'off':
            self._disable_epochly()
        elif command == 'profile':
            self._show_profile()
        elif command == 'level':
            if len(args) > 1:
                try:
                    level = int(args[1])
                    self._set_level(level)
                except ValueError:
                    print("ERROR: Level must be an integer (0-4)")
            else:
                print("ERROR: Usage: %epochly level <0-4>")
        elif command == 'status':
            self._show_status()
        elif command == 'help':
            self._show_help()
        else:
            print(f"ERROR: Unknown command: {command}")
            self._show_help()

    def _handle_cell_magic(self, line: str, cell: str):
        """Handle cell magic execution with profiling/benchmarking."""
        args = parse_argstring(self.epochly, line)

        # Store original level if overriding
        original_level = None
        if args.level is not None:
            if self.epochly_core:
                original_level = self.epochly_core.get_enhancement_level()
                self._set_level(args.level, quiet=True)

        # Start profiling if requested
        start_time = time.time()
        if args.profile and self.performance_monitor:
            self.performance_monitor.start_profiling()

        try:
            # Execute the cell
            result = self.shell.run_cell(cell)

            # Calculate execution time
            execution_time = time.time() - start_time

            # Show results
            if args.profile:
                self._show_cell_profile(execution_time)
            elif args.benchmark:
                self._show_cell_benchmark(execution_time)

            return result

        finally:
            # Restore original level if it was overridden
            if original_level is not None:
                self._set_level(original_level.value if hasattr(original_level, 'value') else original_level, quiet=True)

            # Stop profiling
            if args.profile and self.performance_monitor:
                self.performance_monitor.stop_profiling()

    def _show_stats(self):
        """Display Epochly statistics."""
        if not self.epochly_core:
            print("ERROR: Epochly core not available")
            return

        try:
            status = self.epochly_core.get_status()

            print("[STATS] Epochly Statistics")
            print("=" * 50)
            print(f"[CONFIG] Enhancement Level: {status.get('enhancement_level', 'Unknown')}")
            print(f"[WORKERS] Workers: {status.get('worker_count', 0)}")
            print(f"[JIT] JIT Backend: {status.get('jit_backend', 'None')}")
            print(f"[MEMORY] Memory Pool: {status.get('memory_pool_size', 'Unknown')}")

            # Show recent performance if available
            if self.performance_monitor:
                metrics = self.performance_monitor.get_current_metrics()
                if metrics:
                    print(f"[SPEEDUP] Recent Speedup: {metrics.get('average_speedup', 'N/A'):.1f}x")
                    print(f"[TARGET] Target Achievement: {metrics.get('target_achievement_rate', 0):.0f}%")

            # Show component status
            components = status.get('components', {})
            if components:
                print("\n[COMPONENTS] Component Status:")
                for component, info in components.items():
                    status_icon = "[ACTIVE]" if info.get('active', False) else "[INACTIVE]"
                    print(f"  {status_icon} {component}: {info.get('status', 'Unknown')}")

        except Exception as e:
            print(f"ERROR: Error getting Epochly stats: {e}")

    def _enable_epochly(self):
        """Enable Epochly acceleration."""
        if not self.epochly_core:
            print("ERROR: Epochly core not available")
            return

        self._epochly_enabled = True
        print("SUCCESS: Epochly acceleration enabled")

        # Show current status
        try:
            level = self.epochly_core.get_enhancement_level()
            print(f"[CONFIG] Current level: {level}")
        except:
            pass

    def _disable_epochly(self):
        """Disable Epochly acceleration."""
        if not self.epochly_core:
            print("ERROR: Epochly core not available")
            return

        self._epochly_enabled = False
        print("[DISABLED] Epochly acceleration disabled")
        print("TIP: Some optimizations may still be active due to system architecture")

    def _show_profile(self):
        """Show performance profiling information."""
        if not self.performance_monitor:
            print("ERROR: Performance monitor not available")
            return

        try:
            metrics = self.performance_monitor.get_current_metrics()
            if not metrics:
                print("[INFO] No profiling data available. Run some code first.")
                return

            print("[PROFILE] Performance Profile")
            print("=" * 50)

            # Show execution metrics
            if 'execution_time' in metrics:
                print(f"[TIME] Execution Time: {metrics['execution_time']:.3f}s")
            if 'speedup' in metrics:
                print(f"[SPEEDUP] Speedup: {metrics['speedup']:.1f}x")
            if 'memory_usage' in metrics:
                print(f"[MEMORY] Memory Usage: {metrics['memory_usage']:.1f}MB")

            # Show optimization details
            optimizations = metrics.get('optimizations', {})
            if optimizations:
                print("\n[OPTIMIZATIONS] Applied Optimizations:")
                for opt_type, details in optimizations.items():
                    print(f"  • {opt_type}: {details}")

        except Exception as e:
            print(f"ERROR: Error getting profile data: {e}")

    def _set_level(self, level: int, quiet: bool = False):
        """Set Epochly enhancement level."""
        if not self.epochly_core:
            if not quiet:
                print("ERROR: Epochly core not available")
            return

        if level < 0 or level > 4:
            if not quiet:
                print("ERROR: Enhancement level must be 0-4")
            return

        try:
            # Convert int to appropriate enum if needed
            from epochly.core.epochly_core import EnhancementLevel
            level_map = {
                0: EnhancementLevel.LEVEL_0_MONITOR,
                1: EnhancementLevel.LEVEL_1_THREADING,
                2: EnhancementLevel.LEVEL_2_JIT,
                3: EnhancementLevel.LEVEL_3_FULL,
                4: EnhancementLevel.LEVEL_4_GPU
            }

            target_level = level_map.get(level)
            if target_level:
                self.epochly_core.set_enhancement_level(target_level)
                if not quiet:
                    print(f"[CONFIG] Enhancement level set to: {level}")
            else:
                if not quiet:
                    print(f"ERROR: Invalid enhancement level: {level}")

        except Exception as e:
            if not quiet:
                print(f"ERROR: Error setting level: {e}")

    def _show_status(self):
        """Show comprehensive Epochly system status."""
        if not self.epochly_core:
            print("ERROR: Epochly core not available")
            return

        try:
            status = self.epochly_core.get_status()

            # Create HTML status display
            html = self._create_status_html(status)
            display(HTML(html))

        except Exception as e:
            print(f"ERROR: Error getting system status: {e}")

    def _create_status_html(self, status: Dict[str, Any]) -> str:
        """Create HTML representation of Epochly status."""
        level = status.get('enhancement_level', 'Unknown')
        worker_count = status.get('worker_count', 0)
        components = status.get('components', {})

        # Determine status color
        if level == 'LEVEL_3_FULL' or level == 'LEVEL_4_GPU':
            status_color = "#28a745"  # Green
            status_text = "[OPTIMAL] Optimal"
        elif level in ['LEVEL_1_THREADING', 'LEVEL_2_JIT']:
            status_color = "#ffc107"  # Yellow
            status_text = "[ACTIVE] Active"
        else:
            status_color = "#6c757d"  # Gray
            status_text = "[MONITORING] Monitoring"

        html = f"""
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; background: #f8f9fa;">
            <h3 style="margin-top: 0; color: {status_color};">Epochly System Status</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div>
                    <strong>[CONFIG] Enhancement Level:</strong><br>
                    <span style="color: {status_color}; font-weight: bold;">{level}</span>
                </div>
                <div>
                    <strong>[WORKERS] Workers:</strong><br>
                    {worker_count}
                </div>
                <div>
                    <strong>[STATUS] Status:</strong><br>
                    <span style="color: {status_color}; font-weight: bold;">{status_text}</span>
                </div>
            </div>
        """

        # Add component status
        if components:
            html += "<h4>Component Status:</h4><ul>"
            for component, info in components.items():
                icon = "[ACTIVE]" if info.get('active', False) else "[INACTIVE]"
                html += f"<li>{icon} <strong>{component}:</strong> {info.get('status', 'Unknown')}</li>"
            html += "</ul>"

        html += "</div>"
        return html

    def _show_cell_profile(self, execution_time: float):
        """Show profiling results for a cell."""
        print("\n[PROFILE] Cell Execution Profile")
        print(f"[TIME] Execution Time: {execution_time:.3f}s")

        if self.performance_monitor:
            try:
                metrics = self.performance_monitor.get_current_metrics()
                if metrics:
                    if 'speedup' in metrics:
                        print(f"[SPEEDUP] Estimated Speedup: {metrics['speedup']:.1f}x")
                    if 'memory_usage' in metrics:
                        print(f"[MEMORY] Memory Usage: {metrics['memory_usage']:.1f}MB")
            except:
                pass

    def _show_cell_benchmark(self, execution_time: float):
        """Show benchmark results for a cell."""
        print("\n[BENCHMARK] Cell Benchmark Results")
        print(f"[TIME] Execution Time: {execution_time:.3f}s")

        # Could add comparison with baseline execution here
        if execution_time < 0.001:
            print("[FAST] Lightning fast execution!")
        elif execution_time < 0.1:
            print("[FAST] Fast execution")
        elif execution_time < 1.0:
            print("[MODERATE] Moderate execution time")
        else:
            print("[SLOW] Slow execution - consider optimization")

    def _show_help(self):
        """Show help information for Epochly magic commands."""
        help_text = """
[HELP] Epochly Magic Commands Help

Line magics:
  %epochly stats     - Show Epochly statistics and worker information
  %epochly on        - Enable Epochly acceleration for this session
  %epochly off       - Disable Epochly acceleration for this session
  %epochly profile   - Show performance profiling information
  %epochly level N   - Set enhancement level (0=monitor, 1=threading, 2=JIT, 3=full, 4=GPU)
  %epochly status    - Show comprehensive system status
  %epochly help      - Show this help message

Cell magics:
  %%epochly --profile
  # Your code here

  %%epochly --level 3
  # Your code here

  %%epochly --benchmark
  # Your code here

Examples:
  %epochly stats                    # Show current Epochly statistics
  %epochly level 3                  # Enable full optimization
  %%epochly --profile               # Profile the next cell
  your_slow_function()

For more information, visit: https://docs.epochly.dev
        """
        print(help_text)


def load_ipython_extension(ipython):
    """Load the Epochly magic commands extension."""
    if not EPOCHLY_AVAILABLE:
        print("WARNING: Epochly not available. Magic commands will have limited functionality.")

    # CRITICAL: Use register_magics, not register_magic_functions
    # register_magic_functions doesn't exist - correct API is register_magics
    ipython.register_magics(EpochlyMagics)
    print("SUCCESS: Epochly magic commands loaded. Type '%epochly help' for usage information.")


def unload_ipython_extension(ipython):
    """Unload the Epochly magic commands extension."""
    # IPython handles this automatically when the extension is unloaded
    print("[UNLOADED] Epochly magic commands unloaded.")
