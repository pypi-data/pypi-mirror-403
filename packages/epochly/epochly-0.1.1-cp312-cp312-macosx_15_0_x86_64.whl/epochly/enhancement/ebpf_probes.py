"""
eBPF Performance Probes (Phase 4.3)

BCC-based eBPF probes for auto-selecting execution strategies based on
real-time performance counters.

Architecture:
- Linux-only (kernel ≥4.18)
- Uses BCC (BPF Compiler Collection) for Python integration
- Graceful fallback on non-Linux platforms
- Minimal overhead with sampling

Performance Counters:
- CPU cycles
- Cache misses
- Instructions (for IPC calculation)
- Context switches

Auto-Selection Logic:
- High IPC + low cache misses → JIT (CPU-bound)
- Low IPC + high cache misses → GPU/sub-interpreter (memory-bound)
- High context switches → Sub-interpreter (parallelism)

Author: Epochly Development Team
Date: November 13, 2025
"""

import sys
import platform
import threading
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ============================================================================
# Platform Detection
# ============================================================================

def is_linux() -> bool:
    """Check if running on Linux."""
    return sys.platform.startswith('linux')

def get_kernel_version() -> tuple:
    """
    Get Linux kernel version.

    Returns:
        Tuple (major, minor, patch) or (0, 0, 0) if not Linux
    """
    if not is_linux():
        return (0, 0, 0)

    try:
        version_str = platform.release()
        # Parse "5.15.0-91-generic" -> (5, 15, 0)
        parts = version_str.split('-')[0].split('.')
        return tuple(int(p) for p in parts[:3])
    except Exception:
        return (0, 0, 0)

from functools import lru_cache

@lru_cache(maxsize=1)
def is_ebpf_available() -> bool:
    """
    Check if eBPF is available on this system (cached).

    Requires:
    - Linux kernel ≥4.18
    - BCC (BPF Compiler Collection) installed

    Returns:
        True if eBPF probes can be used
    """
    # Check Linux
    if not is_linux():
        return False

    # Check kernel version
    kernel = get_kernel_version()
    if kernel < (4, 18, 0):
        logger.debug(f"Kernel {kernel} < 4.18.0 - eBPF unavailable")
        return False

    # Check BCC availability
    try:
        from bcc import BPF  # noqa: F401
        return True
    except ImportError:
        logger.debug("BCC not installed - eBPF unavailable")
        return False

# ============================================================================
# Performance Counters
# ============================================================================

@dataclass
class PerformanceCounters:
    """
    Performance counter snapshot from eBPF probes.

    Counters:
    - cpu_cycles: Total CPU cycles
    - cache_misses: LLC (Last Level Cache) misses
    - instructions: Total instructions executed
    - context_switches: Number of context switches

    Derived Metrics:
    - IPC (Instructions Per Cycle): instructions / cycles
    """

    cpu_cycles: int = 0
    cache_misses: int = 0
    instructions: int = 0
    context_switches: int = 0
    timestamp_ns: int = field(default_factory=lambda: time.perf_counter_ns())

    def get_ipc(self) -> float:
        """
        Calculate Instructions Per Cycle.

        Returns:
            IPC value (higher is better for CPU-bound workloads)
        """
        if self.cpu_cycles == 0:
            return 0.0
        return self.instructions / self.cpu_cycles

    def get_cache_miss_rate(self) -> float:
        """
        Calculate cache miss rate.

        Returns:
            Cache misses per instruction
        """
        if self.instructions == 0:
            return 0.0
        return self.cache_misses / self.instructions

    def recommend_strategy(self) -> str:
        """
        Recommend execution strategy based on counters.

        Returns:
            Strategy name: 'jit', 'gpu', 'sub_interpreter', or 'cpu'
        """
        ipc = self.get_ipc()
        cache_miss_rate = self.get_cache_miss_rate()

        # High IPC + low cache misses → CPU-bound → JIT
        if ipc >= 1.5 and cache_miss_rate < 0.01:
            return 'jit'

        # Low IPC + high cache misses → Memory-bound → GPU/sub-interpreter
        elif ipc < 0.8 and cache_miss_rate > 0.05:
            if self.cache_misses > 100000:
                return 'gpu'  # Very high cache misses
            else:
                return 'sub_interpreter'

        # High context switches → Parallelism → sub-interpreter
        elif self.context_switches > 100:
            return 'sub_interpreter'

        # Default: CPU
        else:
            return 'cpu'

# ============================================================================
# eBPF Probe Manager
# ============================================================================

class EBPFProbeManager:
    """
    Manages eBPF performance probes.

    Platform: Linux only (kernel ≥4.18)
    Dependencies: BCC (BPF Compiler Collection)

    Graceful Fallback:
    - Returns False from start() on non-Linux
    - Returns None from get_counters() when unavailable
    - No exceptions on unsupported platforms
    """

    def __init__(self):
        """Initialize eBPF probe manager."""
        self._bpf = None
        self._running = False
        self._lock = threading.Lock()
        self._counters: Optional[PerformanceCounters] = None
        self._available = is_ebpf_available()

    def is_running(self) -> bool:
        """
        Check if probes are currently running.

        Returns:
            True if probes active
        """
        with self._lock:
            return self._running

    def start(self) -> bool:
        """
        Start eBPF probes.

        Returns:
            True if started successfully, False if unavailable
        """
        with self._lock:
            # Already running
            if self._running:
                return True

            # Not available
            if not self._available:
                logger.debug("eBPF not available on this platform")
                return False

            try:
                from bcc import BPF

                # eBPF program for performance counters
                # Accumulates actual event counts using sample_period
                bpf_text = """
                #include <uapi/linux/ptrace.h>
                #include <linux/sched.h>

                // Performance counter map
                BPF_HASH(counters, u32, u64, 8);

                // Perf event probes (accumulate ctx->sample_period for accurate counts)
                int on_cpu_cycles(struct bpf_perf_event_data *ctx) {
                    u32 key = 0;  // cpu_cycles key
                    u64 inc = ctx->sample_period;  // Actual events since last sample
                    u64 zero = 0;
                    u64 *val = counters.lookup_or_init(&key, &zero);
                    if (val) {
                        __sync_fetch_and_add(val, inc);
                    }
                    return 0;
                }

                int on_cache_miss(struct bpf_perf_event_data *ctx) {
                    u32 key = 1;  // cache_misses key
                    u64 inc = ctx->sample_period;
                    u64 zero = 0;
                    u64 *val = counters.lookup_or_init(&key, &zero);
                    if (val) {
                        __sync_fetch_and_add(val, inc);
                    }
                    return 0;
                }

                int on_instruction(struct bpf_perf_event_data *ctx) {
                    u32 key = 2;  // instructions key
                    u64 inc = ctx->sample_period;
                    u64 zero = 0;
                    u64 *val = counters.lookup_or_init(&key, &zero);
                    if (val) {
                        __sync_fetch_and_add(val, inc);
                    }
                    return 0;
                }

                int on_context_switch(struct tracepoint__sched__sched_switch *ctx) {
                    u32 key = 3;  // context_switches key
                    u64 *val = counters.lookup(&key);
                    if (val) {
                        __sync_fetch_and_add(val, 1);
                    } else {
                        u64 init = 1;
                        counters.update(&key, &init);
                    }
                    return 0;
                }
                """

                # Compile BPF program
                self._bpf = BPF(text=bpf_text)

                # Attach perf event probes with sample_freq for consistent low overhead
                # 99 Hz sampling = ~1% overhead, standard for production profiling
                sample_freq = 99  # Samples per second (99 Hz)

                self._bpf.attach_perf_event(
                    ev_type=BPF.PerfType.HARDWARE,
                    ev_config=BPF.PerfHWConfig.CPU_CYCLES,
                    fn_name="on_cpu_cycles",
                    sample_freq=sample_freq  # Use freq not period for low overhead
                )

                self._bpf.attach_perf_event(
                    ev_type=BPF.PerfType.HARDWARE,
                    ev_config=BPF.PerfHWConfig.CACHE_MISSES,
                    fn_name="on_cache_miss",
                    sample_freq=sample_freq
                )

                self._bpf.attach_perf_event(
                    ev_type=BPF.PerfType.HARDWARE,
                    ev_config=BPF.PerfHWConfig.INSTRUCTIONS,
                    fn_name="on_instruction",
                    sample_freq=sample_freq
                )

                # Attach context switch tracepoint
                self._bpf.attach_tracepoint(
                    tp="sched:sched_switch",
                    fn_name="on_context_switch"
                )

                self._running = True
                logger.info("eBPF probes started successfully")
                return True

            except ImportError as e:
                logger.debug(f"BCC not available: {e}")
                return False
            except PermissionError as e:
                logger.warning(f"Insufficient permissions for eBPF: {e}")
                return False
            except Exception as e:
                logger.warning(f"Failed to start eBPF probes: {e}")
                return False

    def stop(self) -> None:
        """Stop eBPF probes and cleanup."""
        with self._lock:
            if not self._running:
                return

            try:
                if self._bpf is not None:
                    # BCC cleanup is automatic on del
                    self._bpf = None

                self._running = False
                logger.info("eBPF probes stopped")

            except Exception as e:
                logger.warning(f"Error stopping eBPF probes: {e}")
                self._running = False

    def get_counters(self) -> Optional[PerformanceCounters]:
        """
        Get current performance counters.

        Returns:
            PerformanceCounters if available, None otherwise
        """
        with self._lock:
            if not self._running or self._bpf is None:
                return None

            try:
                counters_map = self._bpf["counters"]

                # Read counter values (safe map access for BCC ctypes)
                # Convert all key-value pairs to Python ints
                values = {}
                try:
                    for k, v in counters_map.items():
                        values[k.value] = v.value
                except AttributeError:
                    # Older BCC versions may return plain ints
                    for k, v in counters_map.items():
                        values[int(k)] = int(v)

                cpu_cycles = values.get(0, 0)
                cache_misses = values.get(1, 0)
                instructions = values.get(2, 0)
                context_switches = values.get(3, 0)

                return PerformanceCounters(
                    cpu_cycles=cpu_cycles,
                    cache_misses=cache_misses,
                    instructions=instructions,
                    context_switches=context_switches,
                    timestamp_ns=time.perf_counter_ns()
                )

            except Exception as e:
                logger.debug(f"Failed to read eBPF counters: {e}")
                return None

    def reset_counters(self) -> None:
        """Reset all performance counters to zero."""
        with self._lock:
            if not self._running or self._bpf is None:
                return

            try:
                counters_map = self._bpf["counters"]
                counters_map.clear()
            except Exception as e:
                logger.debug(f"Failed to reset counters: {e}")

# ============================================================================
# Global Singleton
# ============================================================================

_global_probe_manager: Optional[EBPFProbeManager] = None
_manager_lock = threading.Lock()

def get_ebpf_probe_manager() -> EBPFProbeManager:
    """
    Get global eBPF probe manager (singleton).

    Returns:
        EBPFProbeManager instance
    """
    global _global_probe_manager

    if _global_probe_manager is None:
        with _manager_lock:
            if _global_probe_manager is None:
                _global_probe_manager = EBPFProbeManager()

    return _global_probe_manager
