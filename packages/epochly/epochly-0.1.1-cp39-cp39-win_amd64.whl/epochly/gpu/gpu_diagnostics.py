"""
GPU Diagnostics and User Guidance for Level 4 Enhancement.

Provides comprehensive GPU status checking with actionable installation
guidance when GPU acceleration is unavailable.

This module is the primary resource for users to understand:
1. Why Level 4 GPU acceleration isn't working
2. What steps to take to enable it
3. Current GPU status and capabilities

Reference: Level 4 UX audit requirements
"""

import logging
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)


class GPUDiagnosticStatus(Enum):
    """Status codes for GPU diagnostic checks."""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    NOT_CHECKED = "not_checked"


@dataclass
class DiagnosticResult:
    """Result of a single diagnostic check."""
    name: str
    status: GPUDiagnosticStatus
    message: str
    details: Optional[str] = None
    recommendation: Optional[str] = None


@dataclass
class GPUDiagnosticReport:
    """Complete GPU diagnostic report with all checks."""
    checks: List[DiagnosticResult] = field(default_factory=list)
    overall_status: GPUDiagnosticStatus = GPUDiagnosticStatus.NOT_CHECKED
    gpu_available: bool = False
    cuda_version: Optional[str] = None
    cupy_version: Optional[str] = None
    device_name: Optional[str] = None
    device_memory_gb: Optional[float] = None
    recommendations: List[str] = field(default_factory=list)

    def add_check(self, result: DiagnosticResult) -> None:
        """Add a diagnostic check result."""
        self.checks.append(result)
        if result.recommendation:
            self.recommendations.append(result.recommendation)

    def compute_overall_status(self) -> None:
        """Compute overall status from individual checks."""
        if any(c.status == GPUDiagnosticStatus.ERROR for c in self.checks):
            self.overall_status = GPUDiagnosticStatus.ERROR
        elif any(c.status == GPUDiagnosticStatus.WARNING for c in self.checks):
            self.overall_status = GPUDiagnosticStatus.WARNING
        elif all(c.status == GPUDiagnosticStatus.OK for c in self.checks):
            self.overall_status = GPUDiagnosticStatus.OK
        else:
            self.overall_status = GPUDiagnosticStatus.NOT_CHECKED


def get_installation_guide() -> str:
    """
    Get comprehensive GPU installation guide for the current platform.

    Returns:
        Multi-line string with installation instructions.
    """
    system = platform.system()

    guide = """
================================================================================
                    EPOCHLY LEVEL 4 GPU ACCELERATION SETUP
================================================================================

Level 4 provides GPU acceleration using NVIDIA CUDA through CuPy.
This can provide 10-100x speedup for array operations.

REQUIREMENTS:
-------------
1. NVIDIA GPU with CUDA Compute Capability 3.0 or higher
2. NVIDIA Driver (version 450.80.02+ for CUDA 11, 525.60.13+ for CUDA 12)
3. Python package: CuPy with matching CUDA version

"""

    if system == "Linux":
        guide += """
LINUX INSTALLATION:
-------------------

Step 1: Verify NVIDIA Driver
   nvidia-smi
   # Should show your GPU and CUDA version (e.g., CUDA 12.7)

Step 2: Install CuPy (choose matching CUDA version)

   # For CUDA 12.x (recommended if nvidia-smi shows CUDA 12.x):
   pip install cupy-cuda12x

   # For CUDA 11.x:
   pip install cupy-cuda11x

   # For CUDA 12 with prebuilt NVIDIA libraries:
   pip install cupy-cuda12x nvidia-cuda-runtime-cu12 nvidia-cuda-nvrtc-cu12

Step 3: Set library path for pip-installed NVIDIA packages (if needed)
   # If CuPy fails to find CUDA libraries, use the wrapper script:
   ./scripts/run_gpu_tests.sh your_script.py

   # Or set LD_LIBRARY_PATH manually (adjust for your Python version):
   export LD_LIBRARY_PATH=$(python -c "import site; print(site.getsitepackages()[0])")/nvidia/cuda_runtime/lib:$LD_LIBRARY_PATH

Step 4: Verify installation
   python -c "import cupy; print(f'CuPy {cupy.__version__} using CUDA {cupy.cuda.runtime.runtimeGetVersion()}')"
"""

    elif system == "Windows":
        guide += """
WINDOWS INSTALLATION:
---------------------

Step 1: Install NVIDIA Driver
   Download from: https://www.nvidia.com/Download/index.aspx

Step 2: Verify NVIDIA Driver
   Open Command Prompt and run:
   nvidia-smi
   # Should show your GPU and CUDA version

Step 3: Install CUDA Toolkit (optional but recommended)
   Download from: https://developer.nvidia.com/cuda-downloads
   # Alternatively, CuPy can use bundled CUDA libraries

Step 4: Install CuPy (choose matching CUDA version)

   # For CUDA 12.x:
   pip install cupy-cuda12x

   # For CUDA 11.x:
   pip install cupy-cuda11x

Step 5: Verify installation
   python -c "import cupy; print(f'CuPy {cupy.__version__}')"
"""

    elif system == "Darwin":  # macOS
        guide += """
MACOS NOTES:
------------
Apple Silicon (M1/M2/M3) Macs do not support NVIDIA CUDA.
Level 4 GPU acceleration is not available on macOS.

For Apple Silicon, Epochly Levels 0-3 provide excellent performance
using the built-in Accelerate framework and Metal acceleration
through NumPy and SciPy.

For Intel Macs with NVIDIA GPUs (rare, older models):
- NVIDIA dropped macOS CUDA support after CUDA 10.2
- CuPy requires CUDA 11+ for modern features
- Level 4 is not recommended on macOS
"""

    guide += """
TROUBLESHOOTING:
----------------

Problem: "CuPy not available"
  - Verify NVIDIA driver: nvidia-smi
  - Install CuPy: pip install cupy-cuda12x

Problem: "No GPU detected"
  - Check nvidia-smi shows your GPU
  - Ensure GPU has Compute Capability >= 3.0
  - Check GPU isn't in use by another process

Problem: "Cannot find libnvrtc.so.12" (Linux)
  - Install NVIDIA NVRTC: pip install nvidia-cuda-nvrtc-cu12
  - Set LD_LIBRARY_PATH (see Step 3 above)

Problem: "CUDA out of memory"
  - Close other GPU applications
  - Reduce batch size in your workload
  - Epochly's intelligent memory handles this automatically

CHECKING YOUR SETUP:
--------------------
Run: epochly gpu check

This will diagnose any issues and provide specific recommendations.

================================================================================
"""
    return guide


def run_diagnostics() -> GPUDiagnosticReport:
    """
    Run comprehensive GPU diagnostics.

    Returns:
        GPUDiagnosticReport with all check results.
    """
    report = GPUDiagnosticReport()

    # Check 1: Platform support
    report.add_check(_check_platform_support())

    # Check 2: NVIDIA driver
    report.add_check(_check_nvidia_driver())

    # Check 3: CuPy installation
    cupy_result = _check_cupy_installation()
    report.add_check(cupy_result)
    if cupy_result.status == GPUDiagnosticStatus.OK:
        report.cupy_version = cupy_result.details

    # Check 4: CUDA availability via CuPy
    cuda_result = _check_cuda_via_cupy()
    report.add_check(cuda_result)
    if cuda_result.status == GPUDiagnosticStatus.OK:
        report.cuda_version = cuda_result.details

    # Check 5: GPU device detection
    device_result = _check_gpu_device()
    report.add_check(device_result)
    if device_result.status == GPUDiagnosticStatus.OK:
        report.gpu_available = True
        if device_result.details:
            parts = device_result.details.split("|")
            if len(parts) >= 1:
                report.device_name = parts[0].strip()
            if len(parts) >= 2:
                try:
                    report.device_memory_gb = float(parts[1].strip())
                except ValueError:
                    pass

    # Check 6: NVIDIA library paths (Linux and Windows only - macOS doesn't support CUDA)
    if platform.system() in ("Linux", "Windows"):
        report.add_check(_check_nvidia_library_paths())

    # Check 7: Epochly GPU module
    report.add_check(_check_epochly_gpu_module())

    # Check 8: Simple CuPy operation test
    if report.gpu_available:
        report.add_check(_check_cupy_operation())

    report.compute_overall_status()
    return report


def _check_platform_support() -> DiagnosticResult:
    """Check if platform supports NVIDIA CUDA."""
    system = platform.system()

    if system == "Darwin":
        machine = platform.machine()
        if machine == "arm64":
            return DiagnosticResult(
                name="Platform Support",
                status=GPUDiagnosticStatus.ERROR,
                message="Apple Silicon does not support NVIDIA CUDA",
                details="M1/M2/M3 Macs cannot use GPU acceleration",
                recommendation="Use Levels 0-3 for optimal performance on Apple Silicon"
            )
        else:
            return DiagnosticResult(
                name="Platform Support",
                status=GPUDiagnosticStatus.WARNING,
                message="Intel Mac detected - CUDA support limited",
                details="NVIDIA dropped macOS CUDA support after 10.2",
                recommendation="Consider using Levels 0-3 instead"
            )
    elif system in ("Linux", "Windows"):
        return DiagnosticResult(
            name="Platform Support",
            status=GPUDiagnosticStatus.OK,
            message=f"{system} supports NVIDIA CUDA",
            details=f"{system} {platform.release()}"
        )
    else:
        return DiagnosticResult(
            name="Platform Support",
            status=GPUDiagnosticStatus.WARNING,
            message=f"Unknown platform: {system}",
            recommendation="Verify NVIDIA CUDA toolkit is available"
        )


def _check_nvidia_driver() -> DiagnosticResult:
    """Check NVIDIA driver installation."""
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return DiagnosticResult(
            name="NVIDIA Driver",
            status=GPUDiagnosticStatus.ERROR,
            message="nvidia-smi not found - NVIDIA driver not installed",
            recommendation="Install NVIDIA driver from https://www.nvidia.com/Download/index.aspx"
        )

    try:
        result = subprocess.run(
            [nvidia_smi, "--query-gpu=driver_version,name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            # Handle multi-GPU systems - take first GPU's info
            first_line = output.split("\n")[0]
            parts = first_line.split(",")
            driver_version = parts[0].strip() if len(parts) > 0 else "Unknown"
            gpu_name = parts[1].strip() if len(parts) > 1 else "Unknown"
            memory_mb = parts[2].strip() if len(parts) > 2 else "Unknown"

            return DiagnosticResult(
                name="NVIDIA Driver",
                status=GPUDiagnosticStatus.OK,
                message=f"Driver {driver_version} detected",
                details=f"{gpu_name}, {memory_mb}MB VRAM"
            )
        else:
            return DiagnosticResult(
                name="NVIDIA Driver",
                status=GPUDiagnosticStatus.ERROR,
                message="nvidia-smi failed",
                details=result.stderr.strip() if result.stderr else "Unknown error",
                recommendation="Verify NVIDIA driver installation"
            )
    except subprocess.TimeoutExpired:
        return DiagnosticResult(
            name="NVIDIA Driver",
            status=GPUDiagnosticStatus.WARNING,
            message="nvidia-smi timed out",
            recommendation="GPU may be busy or driver may have issues"
        )
    except Exception as e:
        return DiagnosticResult(
            name="NVIDIA Driver",
            status=GPUDiagnosticStatus.ERROR,
            message=f"Error checking NVIDIA driver: {e}",
            recommendation="Verify NVIDIA driver installation"
        )


def _check_cupy_installation() -> DiagnosticResult:
    """Check if CuPy is installed."""
    try:
        import cupy
        version = cupy.__version__
        return DiagnosticResult(
            name="CuPy Installation",
            status=GPUDiagnosticStatus.OK,
            message=f"CuPy {version} installed",
            details=version
        )
    except ImportError as e:
        error_msg = str(e)
        if "nvidia" in error_msg.lower() or "cuda" in error_msg.lower():
            return DiagnosticResult(
                name="CuPy Installation",
                status=GPUDiagnosticStatus.ERROR,
                message="CuPy installed but CUDA libraries missing",
                details=error_msg,
                recommendation="Run: pip install nvidia-cuda-runtime-cu12 nvidia-cuda-nvrtc-cu12"
            )
        else:
            return DiagnosticResult(
                name="CuPy Installation",
                status=GPUDiagnosticStatus.ERROR,
                message="CuPy not installed",
                recommendation="Run: pip install cupy-cuda12x (or cupy-cuda11x for CUDA 11)"
            )


def _check_cuda_via_cupy() -> DiagnosticResult:
    """Check CUDA runtime availability through CuPy."""
    try:
        import cupy
        cuda_version = cupy.cuda.runtime.runtimeGetVersion()
        major = cuda_version // 1000
        minor = (cuda_version % 1000) // 10
        version_str = f"{major}.{minor}"
        return DiagnosticResult(
            name="CUDA Runtime",
            status=GPUDiagnosticStatus.OK,
            message=f"CUDA {version_str} available",
            details=version_str
        )
    except ImportError:
        return DiagnosticResult(
            name="CUDA Runtime",
            status=GPUDiagnosticStatus.NOT_CHECKED,
            message="Cannot check - CuPy not available"
        )
    except Exception as e:
        error_msg = str(e)
        if "nvrtc" in error_msg.lower():
            return DiagnosticResult(
                name="CUDA Runtime",
                status=GPUDiagnosticStatus.ERROR,
                message="CUDA NVRTC library missing",
                details=error_msg,
                recommendation="Run: pip install nvidia-cuda-nvrtc-cu12"
            )
        elif "cudart" in error_msg.lower() or "runtime" in error_msg.lower():
            return DiagnosticResult(
                name="CUDA Runtime",
                status=GPUDiagnosticStatus.ERROR,
                message="CUDA runtime library missing",
                details=error_msg,
                recommendation="Run: pip install nvidia-cuda-runtime-cu12"
            )
        else:
            return DiagnosticResult(
                name="CUDA Runtime",
                status=GPUDiagnosticStatus.ERROR,
                message=f"CUDA runtime error: {e}",
                recommendation="Check CUDA installation and library paths"
            )


def _check_gpu_device() -> DiagnosticResult:
    """Check GPU device availability through CuPy."""
    try:
        import cupy
        device_count = cupy.cuda.runtime.getDeviceCount()
        if device_count == 0:
            # Check if CUDA_VISIBLE_DEVICES might be hiding GPUs
            cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
            if cuda_visible == "-1" or cuda_visible == "":
                return DiagnosticResult(
                    name="GPU Device",
                    status=GPUDiagnosticStatus.ERROR,
                    message="No CUDA-capable GPU detected",
                    recommendation="Check CUDA_VISIBLE_DEVICES env var (currently: "
                                  f"'{cuda_visible or 'not set'}') and verify nvidia-smi sees GPU"
                )
            return DiagnosticResult(
                name="GPU Device",
                status=GPUDiagnosticStatus.ERROR,
                message="No CUDA-capable GPU detected",
                recommendation="Verify GPU is visible to nvidia-smi"
            )

        # Get first device info
        device = cupy.cuda.Device(0)
        name = device.name if hasattr(device, 'name') else "Unknown GPU"
        mem_info = device.mem_info
        total_gb = mem_info[1] / (1024**3) if mem_info else 0

        return DiagnosticResult(
            name="GPU Device",
            status=GPUDiagnosticStatus.OK,
            message=f"{device_count} GPU(s) detected",
            details=f"{name}|{total_gb:.1f}"
        )
    except ImportError:
        return DiagnosticResult(
            name="GPU Device",
            status=GPUDiagnosticStatus.NOT_CHECKED,
            message="Cannot check - CuPy not available"
        )
    except Exception as e:
        return DiagnosticResult(
            name="GPU Device",
            status=GPUDiagnosticStatus.ERROR,
            message=f"GPU detection failed: {e}",
            recommendation="Check nvidia-smi and CUDA installation"
        )


def _check_nvidia_library_paths() -> DiagnosticResult:
    """Check if NVIDIA pip package libraries are accessible."""
    import site

    system = platform.system()

    # Check multiple site-packages locations (system, user, venv)
    locations_to_check = []

    # System site-packages
    try:
        locations_to_check.extend(site.getsitepackages())
    except (AttributeError, TypeError):
        pass

    # User site-packages
    try:
        user_site = site.getusersitepackages()
        if user_site:
            locations_to_check.append(user_site)
    except (AttributeError, TypeError):
        pass

    # Fallback for venv - platform-specific paths
    if system == "Windows":
        locations_to_check.append(os.path.join(sys.prefix, "Lib", "site-packages"))
    else:
        locations_to_check.append(
            f"{sys.prefix}/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
        )

    # Find nvidia directory
    nvidia_base = None
    checked_paths = []
    for loc in locations_to_check:
        check_path = os.path.join(loc, "nvidia")
        checked_paths.append(check_path)
        if os.path.isdir(check_path):
            nvidia_base = check_path
            break

    if nvidia_base is None:
        return DiagnosticResult(
            name="NVIDIA Library Paths",
            status=GPUDiagnosticStatus.WARNING,
            message="No nvidia-* pip packages found",
            details=f"Checked {len(checked_paths)} locations",
            recommendation="If using pip-installed CUDA: pip install nvidia-cuda-runtime-cu12 nvidia-cuda-nvrtc-cu12"
        )

    # Check for key libraries
    libs_found = []
    libs_missing = []
    required = ["cuda_runtime", "cuda_nvrtc"]
    optional = ["cublas", "nvjitlink", "cudnn"]

    for pkg in required + optional:
        lib_dir = os.path.join(nvidia_base, pkg, "lib")
        if os.path.isdir(lib_dir):
            libs_found.append(pkg)
        elif pkg in required:
            libs_missing.append(pkg)

    if libs_missing:
        # Build package names separately for Python 3.11 f-string compatibility
        pkg_names = ' '.join("nvidia-" + lib.replace('_', '-') + "-cu12" for lib in libs_missing)
        return DiagnosticResult(
            name="NVIDIA Library Paths",
            status=GPUDiagnosticStatus.WARNING,
            message=f"Missing libraries: {', '.join(libs_missing)}",
            details=f"Found: {', '.join(libs_found)}",
            recommendation=f"Run: pip install {pkg_names}"
        )

    # Check if library path includes nvidia libs (platform-specific)
    if system == "Windows":
        lib_path = os.environ.get("PATH", "")
        path_sep = ";"
        path_var_name = "PATH"
    elif system == "Darwin":
        lib_path = os.environ.get("DYLD_LIBRARY_PATH", "")
        path_sep = ":"
        path_var_name = "DYLD_LIBRARY_PATH"
    else:  # Linux
        lib_path = os.environ.get("LD_LIBRARY_PATH", "")
        path_sep = ":"
        path_var_name = "LD_LIBRARY_PATH"

    nvidia_in_path = any("nvidia" in p.lower() for p in lib_path.split(path_sep))

    if not nvidia_in_path and libs_found:
        if system == "Windows":
            recommendation = "Add NVIDIA library paths to PATH environment variable"
        else:
            recommendation = f"Use scripts/run_gpu_tests.sh or set {path_var_name} manually"

        return DiagnosticResult(
            name="NVIDIA Library Paths",
            status=GPUDiagnosticStatus.WARNING,
            message=f"NVIDIA libraries installed but not in {path_var_name}",
            details=f"Found packages: {', '.join(libs_found)}",
            recommendation=recommendation
        )

    return DiagnosticResult(
        name="NVIDIA Library Paths",
        status=GPUDiagnosticStatus.OK,
        message=f"NVIDIA libraries configured ({len(libs_found)} packages)",
        details=", ".join(libs_found)
    )


def _check_epochly_gpu_module() -> DiagnosticResult:
    """Check Epochly GPU module availability."""
    try:
        from epochly.gpu import GPUDetector, CuPyManager
        from epochly.gpu.gpu_detector import GPUBackend

        detector = GPUDetector()
        gpu_info = detector.get_gpu_info()

        if gpu_info.backend == GPUBackend.NONE:
            return DiagnosticResult(
                name="Epochly GPU Module",
                status=GPUDiagnosticStatus.WARNING,
                message="GPU module loaded but no backend available",
                recommendation="Install CuPy for GPU support"
            )

        return DiagnosticResult(
            name="Epochly GPU Module",
            status=GPUDiagnosticStatus.OK,
            message=f"GPU module ready (backend: {gpu_info.backend.name})",
            details=f"{gpu_info.device_name or 'Unknown GPU'}"
        )
    except ImportError as e:
        return DiagnosticResult(
            name="Epochly GPU Module",
            status=GPUDiagnosticStatus.ERROR,
            message=f"Cannot import Epochly GPU module: {e}",
            recommendation="Verify Epochly installation: pip install epochly[gpu]"
        )
    except Exception as e:
        return DiagnosticResult(
            name="Epochly GPU Module",
            status=GPUDiagnosticStatus.WARNING,
            message=f"GPU module error: {e}",
            details=str(e)
        )


def _check_cupy_operation() -> DiagnosticResult:
    """Run a simple CuPy operation to verify GPU is fully functional."""
    try:
        import cupy as cp

        # Simple array operation
        x = cp.array([1, 2, 3, 4, 5], dtype=cp.float32)
        y = cp.sum(x)
        result = float(y.get())

        if result == 15.0:
            return DiagnosticResult(
                name="GPU Operation Test",
                status=GPUDiagnosticStatus.OK,
                message="GPU computation verified",
                details="Basic array operations working"
            )
        else:
            return DiagnosticResult(
                name="GPU Operation Test",
                status=GPUDiagnosticStatus.WARNING,
                message="GPU computation returned unexpected result",
                details=f"Expected 15.0, got {result}"
            )
    except ImportError:
        return DiagnosticResult(
            name="GPU Operation Test",
            status=GPUDiagnosticStatus.NOT_CHECKED,
            message="Cannot test - CuPy not available"
        )
    except Exception as e:
        return DiagnosticResult(
            name="GPU Operation Test",
            status=GPUDiagnosticStatus.ERROR,
            message=f"GPU operation failed: {e}",
            recommendation="Check GPU memory and CUDA installation"
        )


def format_report(report: GPUDiagnosticReport, verbose: bool = False) -> str:
    """
    Format diagnostic report for display.

    Args:
        report: The diagnostic report to format.
        verbose: Include detailed information.

    Returns:
        Formatted string for display.
    """
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("              EPOCHLY GPU DIAGNOSTICS REPORT")
    lines.append("=" * 70)
    lines.append("")

    # Overall status
    status_icon = {
        GPUDiagnosticStatus.OK: "[PASS]",
        GPUDiagnosticStatus.WARNING: "[WARN]",
        GPUDiagnosticStatus.ERROR: "[FAIL]",
        GPUDiagnosticStatus.NOT_CHECKED: "[SKIP]"
    }

    lines.append(f"Overall Status: {status_icon[report.overall_status]} {report.overall_status.value.upper()}")
    lines.append(f"GPU Available: {'Yes' if report.gpu_available else 'No'}")

    if report.device_name:
        lines.append(f"GPU Device: {report.device_name}")
    if report.device_memory_gb:
        lines.append(f"GPU Memory: {report.device_memory_gb:.1f} GB")
    if report.cupy_version:
        lines.append(f"CuPy Version: {report.cupy_version}")
    if report.cuda_version:
        lines.append(f"CUDA Version: {report.cuda_version}")

    lines.append("")
    lines.append("-" * 70)
    lines.append("DIAGNOSTIC CHECKS:")
    lines.append("-" * 70)

    for check in report.checks:
        icon = status_icon[check.status]
        lines.append(f"  {icon} {check.name}: {check.message}")
        if verbose and check.details:
            lines.append(f"       Details: {check.details}")

    if report.recommendations:
        lines.append("")
        lines.append("-" * 70)
        lines.append("RECOMMENDATIONS:")
        lines.append("-" * 70)
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"  {i}. {rec}")

    if not report.gpu_available:
        lines.append("")
        lines.append("-" * 70)
        lines.append("NEXT STEPS:")
        lines.append("-" * 70)
        lines.append("  Run 'epochly gpu guide' for detailed installation instructions")

    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)


def print_quick_status() -> None:
    """Print quick GPU status (used when Level 4 is unavailable)."""
    try:
        import cupy
        print("[Epochly] GPU: CuPy available")
    except ImportError:
        print("[Epochly] GPU: CuPy not installed")
        print("[Epochly]   To enable Level 4 GPU acceleration:")
        print("[Epochly]     pip install cupy-cuda12x")
        print("[Epochly]   For detailed setup: epochly gpu guide")


def get_user_friendly_gpu_error(error: Exception) -> Tuple[str, str]:
    """
    Convert GPU error to user-friendly message and recommendation.

    Args:
        error: The exception that occurred.

    Returns:
        Tuple of (message, recommendation).
    """
    error_str = str(error).lower()
    error_type = type(error).__name__

    # Check for CuPy import errors
    if "cupy" in error_str or (error_type == "ImportError" and "cupy" in error_str):
        return (
            "CuPy is not installed",
            "Install with: pip install cupy-cuda12x"
        )

    # Also catch generic "no module named" for cupy
    if "no module named" in error_str and "cupy" in error_str:
        return (
            "CuPy is not installed",
            "Install with: pip install cupy-cuda12x"
        )

    if "nvrtc" in error_str:
        return (
            "CUDA NVRTC library not found",
            "Install with: pip install nvidia-cuda-nvrtc-cu12"
        )

    if "cudart" in error_str or "cuda runtime" in error_str:
        return (
            "CUDA runtime library not found",
            "Install with: pip install nvidia-cuda-runtime-cu12"
        )

    if "out of memory" in error_str or "oom" in error_str:
        return (
            "GPU out of memory",
            "Close other GPU applications or reduce batch size"
        )

    if "no cuda" in error_str or "cuda not available" in error_str:
        return (
            "CUDA not available on this system",
            "Install NVIDIA driver and CUDA toolkit"
        )

    if "device" in error_str and ("not found" in error_str or "no device" in error_str):
        return (
            "No GPU device found",
            "Check nvidia-smi to verify GPU is detected"
        )

    # Generic fallback
    return (
        f"GPU error: {error}",
        "Run 'epochly gpu check' for detailed diagnostics"
    )
