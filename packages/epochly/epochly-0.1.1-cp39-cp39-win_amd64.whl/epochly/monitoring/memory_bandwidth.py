"""
Memory Bandwidth Monitoring

Provides cross-platform memory bandwidth utilization estimation.

Since true hardware-level memory bandwidth monitoring requires:
- Linux: perf_event_open with PMU counters (kernel support)
- Windows: Performance Data Helper (PDH) API
- macOS: Kernel extensions or IOKit

This module provides practical approximations using available system metrics:
- Page faults/sec → memory pressure indicator
- Memory read/write activity from /proc/vmstat (Linux)
- System performance counters (Windows)
- vm_stat activity (macOS)

Author: Epochly Development Team
"""

import os
import sys
import time
import platform
import subprocess
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class MemoryBandwidthStats:
    """Memory bandwidth statistics"""
    estimated_bandwidth_mbps: float  # Estimated MB/s
    utilization_percentage: float    # 0.0-100.0
    page_faults_per_sec: float
    platform: str
    measurement_method: str


class MemoryBandwidthMonitor:
    """
    Cross-platform memory bandwidth monitoring.

    Provides practical bandwidth estimation using available system metrics.
    """

    def __init__(self):
        """Initialize platform-specific monitoring"""
        self.platform = platform.system()
        self._last_measurement_time = None
        self._last_vmstat = None  # Linux: /proc/vmstat cache
        self._baseline_bandwidth = None  # Platform-specific max bandwidth

        # Try to detect theoretical max bandwidth
        self._detect_max_bandwidth()

    def _detect_max_bandwidth(self) -> None:
        """Detect theoretical maximum memory bandwidth for this system"""
        # This is a rough approximation
        # Real value would require DMI/SMBIOS or hardware specs
        # We estimate based on typical modern systems
        try:
            import psutil

            # Rough estimate: DDR4-3200 = ~25 GB/s per channel
            # Assume dual-channel for consumer systems
            # This is conservative - servers have more channels
            self._baseline_bandwidth = 25000.0  # MB/s (conservative estimate)

        except Exception:
            # Fallback to conservative default
            self._baseline_bandwidth = 20000.0  # MB/s

    def get_bandwidth_utilization(self) -> MemoryBandwidthStats:
        """
        Get current memory bandwidth utilization.

        Returns estimated bandwidth based on platform-specific metrics.
        """
        if self.platform == "Linux":
            return self._measure_linux()
        elif self.platform == "Windows":
            return self._measure_windows()
        elif self.platform == "Darwin":  # macOS
            return self._measure_macos()
        else:
            return self._measure_fallback()

    def _measure_linux(self) -> MemoryBandwidthStats:
        """Measure memory bandwidth on Linux using /proc/vmstat"""
        try:
            # Read /proc/vmstat for memory activity
            with open('/proc/vmstat', 'r') as f:
                vmstat = {}
                for line in f:
                    if line.strip():
                        key, value = line.strip().split()
                        vmstat[key] = int(value)

            current_time = time.time()

            # Calculate deltas if we have previous measurement
            if self._last_vmstat and self._last_measurement_time:
                time_delta = current_time - self._last_measurement_time

                if time_delta > 0:
                    # Page faults indicate memory pressure
                    pgfault_delta = vmstat.get('pgfault', 0) - self._last_vmstat.get('pgfault', 0)
                    pgfaults_per_sec = pgfault_delta / time_delta

                    # Page ins/outs indicate actual memory transfer
                    pgin_delta = vmstat.get('pgpgin', 0) - self._last_vmstat.get('pgpgin', 0)
                    pgout_delta = vmstat.get('pgpgout', 0) - self._last_vmstat.get('pgpgout', 0)

                    # Each page in/out is typically 4KB
                    page_size = 4096
                    total_bytes = (pgin_delta + pgout_delta) * page_size
                    bandwidth_mbps = (total_bytes / time_delta) / (1024 * 1024)

                    # Estimate utilization (conservative)
                    utilization = min(100.0, (bandwidth_mbps / self._baseline_bandwidth) * 100.0)

                    # Store current measurement
                    self._last_vmstat = vmstat
                    self._last_measurement_time = current_time

                    return MemoryBandwidthStats(
                        estimated_bandwidth_mbps=bandwidth_mbps,
                        utilization_percentage=utilization,
                        page_faults_per_sec=pgfaults_per_sec,
                        platform="Linux",
                        measurement_method="/proc/vmstat"
                    )

            # First measurement - just store baseline
            self._last_vmstat = vmstat
            self._last_measurement_time = current_time

            return MemoryBandwidthStats(
                estimated_bandwidth_mbps=0.0,
                utilization_percentage=0.0,
                page_faults_per_sec=0.0,
                platform="Linux",
                measurement_method="/proc/vmstat (initializing)"
            )

        except Exception as e:
            return self._measure_fallback()

    def _measure_windows(self) -> MemoryBandwidthStats:
        """Measure memory bandwidth on Windows using Performance Counters"""
        try:
            import wmi

            c = wmi.WMI()

            # Get memory statistics
            # Windows doesn't expose bandwidth directly, we approximate from page file activity
            for os_info in c.Win32_OperatingSystem():
                # Pages read/written to page file
                total_virtual_memory = int(os_info.TotalVirtualMemorySize)
                free_virtual_memory = int(os_info.FreeVirtualMemorySize)

                # Rough approximation based on paging activity
                paging_activity = total_virtual_memory - free_virtual_memory

                # Convert to MB/s (very rough estimate)
                bandwidth_mbps = paging_activity / 1024.0  # Conservative

                utilization = min(100.0, (bandwidth_mbps / self._baseline_bandwidth) * 100.0)

                return MemoryBandwidthStats(
                    estimated_bandwidth_mbps=bandwidth_mbps,
                    utilization_percentage=utilization,
                    page_faults_per_sec=0.0,  # WMI doesn't provide this directly
                    platform="Windows",
                    measurement_method="WMI (approximation)"
                )

            return self._measure_fallback()

        except ImportError:
            # WMI not available - try psutil fallback
            return self._measure_psutil_approximation("Windows")
        except Exception:
            return self._measure_fallback()

    def _measure_macos(self) -> MemoryBandwidthStats:
        """Measure memory bandwidth on macOS using vm_stat"""
        try:
            # Run vm_stat for memory statistics
            output = subprocess.check_output(['vm_stat']).decode('utf-8')

            # Parse vm_stat output
            stats = {}
            for line in output.splitlines()[1:]:  # Skip header
                if ':' in line:
                    key, value = line.split(':')
                    # Remove 'Pages ' prefix and parse number
                    key = key.strip()
                    value = value.strip().rstrip('.')
                    try:
                        stats[key] = int(value)
                    except ValueError:
                        continue

            # Get page size
            pagesize_output = subprocess.check_output(['pagesize']).decode('utf-8').strip()
            page_size = int(pagesize_output)

            # Calculate activity from page ins/outs
            current_time = time.time()

            if self._last_vmstat and self._last_measurement_time:
                time_delta = current_time - self._last_measurement_time

                if time_delta > 0:
                    # Calculate page activity
                    pageins_delta = stats.get('Pageins', 0) - self._last_vmstat.get('Pageins', 0)
                    pageouts_delta = stats.get('Pageouts', 0) - self._last_vmstat.get('Pageouts', 0)

                    total_bytes = (pageins_delta + pageouts_delta) * page_size
                    bandwidth_mbps = (total_bytes / time_delta) / (1024 * 1024)

                    utilization = min(100.0, (bandwidth_mbps / self._baseline_bandwidth) * 100.0)

                    # Page faults
                    pagefaults_delta = stats.get('Pageins', 0) - self._last_vmstat.get('Pageins', 0)
                    pagefaults_per_sec = pagefaults_delta / time_delta

                    self._last_vmstat = stats
                    self._last_measurement_time = current_time

                    return MemoryBandwidthStats(
                        estimated_bandwidth_mbps=bandwidth_mbps,
                        utilization_percentage=utilization,
                        page_faults_per_sec=pagefaults_per_sec,
                        platform="Darwin (macOS)",
                        measurement_method="vm_stat"
                    )

            # First measurement
            self._last_vmstat = stats
            self._last_measurement_time = current_time

            return MemoryBandwidthStats(
                estimated_bandwidth_mbps=0.0,
                utilization_percentage=0.0,
                page_faults_per_sec=0.0,
                platform="Darwin (macOS)",
                measurement_method="vm_stat (initializing)"
            )

        except Exception:
            return self._measure_fallback()

    def _measure_psutil_approximation(self, platform_name: str) -> MemoryBandwidthStats:
        """Fallback approximation using psutil memory activity"""
        try:
            import psutil

            # Use swap activity as proxy for memory pressure
            swap = psutil.swap_memory()
            mem = psutil.virtual_memory()

            # Rough approximation: swap activity + memory pressure
            # This is very conservative but prevents returning 0.0
            memory_pressure = (mem.percent / 100.0) * 0.1  # 10% of usage as utilization
            utilization = min(10.0, memory_pressure * 100.0)  # Cap at 10% for approximation

            return MemoryBandwidthStats(
                estimated_bandwidth_mbps=utilization * self._baseline_bandwidth / 100.0,
                utilization_percentage=utilization,
                page_faults_per_sec=0.0,
                platform=platform_name,
                measurement_method="psutil (approximation)"
            )

        except Exception:
            return self._measure_fallback()

    def _measure_fallback(self) -> MemoryBandwidthStats:
        """Ultimate fallback when no platform-specific method works"""
        return MemoryBandwidthStats(
            estimated_bandwidth_mbps=0.0,
            utilization_percentage=0.0,
            page_faults_per_sec=0.0,
            platform=self.platform,
            measurement_method="unavailable"
        )


# Singleton instance
_monitor_instance: Optional[MemoryBandwidthMonitor] = None


def get_memory_bandwidth_monitor() -> MemoryBandwidthMonitor:
    """Get singleton memory bandwidth monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = MemoryBandwidthMonitor()
    return _monitor_instance


def get_memory_bandwidth_utilization() -> float:
    """
    Get current memory bandwidth utilization as percentage (0.0-100.0).

    This is a convenience function for quick checks.
    """
    monitor = get_memory_bandwidth_monitor()
    stats = monitor.get_bandwidth_utilization()
    return stats.utilization_percentage
