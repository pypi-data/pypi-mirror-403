"""
TensorFlow Detector for Epochly.

Tier 1 detection-only for TensorFlow GPU usage.

CRITICAL: TensorFlow coordination is NOT SAFE for automatic handling because:
1. TF pre-allocates ALL GPU memory by default
2. set_memory_growth() must be called BEFORE any TF operations
3. Epochly cannot control user's TF initialization order
4. The experimental API designation indicates instability

This class DETECTS TensorFlow and WARNS users, but does NOT attempt
any automatic GPU memory coordination. Users must configure TensorFlow
themselves following the guidance provided.

Compatible with Python 3.9-3.13, Windows/Linux/Mac.

Author: Epochly Team
License: Apache 2.0
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any, Optional, Tuple

if TYPE_CHECKING:
    import tensorflow as tf


class TensorFlowDetector:
    """
    Tier 1 detection-only for TensorFlow.

    TensorFlow coordination is NOT SAFE for automatic handling because:
    1. TF pre-allocates ALL GPU memory by default
    2. set_memory_growth() must be called BEFORE any TF ops
    3. Epochly cannot control user's TF initialization order

    This class detects TF and warns users, but does NOT attempt coordination.

    Thread Safety:
        All methods are thread-safe.

    Example:
        >>> detector = TensorFlowDetector()
        >>> if detector.detect_tensorflow_active():
        ...     is_safe, warning = detector.check_memory_growth_enabled()
        ...     if not is_safe:
        ...         print(warning)
        ...         print(detector.get_user_guidance())
    """

    def __init__(self) -> None:
        """
        Initialize the TensorFlow detector.

        Does not import TensorFlow at initialization time to avoid
        triggering GPU memory allocation. Imports are deferred to method calls.
        """
        self._tf: Optional[Any] = None
        self._tf_available: Optional[bool] = None

    def _ensure_tensorflow(self) -> Optional[Any]:
        """
        Lazily import and return the tensorflow module.

        Returns:
            The tensorflow module, or None if not installed.
        """
        if self._tf is None:
            try:
                import tensorflow as tf

                self._tf = tf
            except ImportError:
                self._tf = None
        return self._tf

    def _check_tf_available(self) -> bool:
        """
        Check if TensorFlow is available with GPU support.

        Returns:
            True if TensorFlow is installed and has GPU devices, False otherwise.
        """
        if self._tf_available is None:
            try:
                tf = self._ensure_tensorflow()
                if tf is None:
                    self._tf_available = False
                else:
                    # Check for physical GPU devices
                    gpus = tf.config.list_physical_devices("GPU")
                    self._tf_available = len(gpus) > 0
            except (ImportError, RuntimeError, AttributeError):
                self._tf_available = False
        return self._tf_available

    def detect_tensorflow_active(self) -> bool:
        """
        Check if TensorFlow is imported and using GPU.

        This method checks:
        1. If TensorFlow is installed
        2. If TensorFlow can see any GPU devices

        Note: This method is designed to be safe - it should not
        trigger GPU memory allocation by itself.

        Returns:
            True if TensorFlow is available with GPU support, False otherwise.

        Example:
            >>> detector = TensorFlowDetector()
            >>> if detector.detect_tensorflow_active():
            ...     print("TensorFlow with GPU is active")
        """
        return self._check_tf_available()

    def check_memory_growth_enabled(self) -> Tuple[bool, str]:
        """
        Check if TensorFlow memory growth is enabled.

        Memory growth should be enabled to allow TensorFlow to share
        GPU memory with other frameworks like CuPy/Epochly.

        Returns:
            Tuple of (is_enabled, warning_message):
            - is_enabled: True if memory growth is enabled for all GPUs
            - warning_message: Guidance message (always contains useful info)

        When TensorFlow is not installed or has no GPUs, returns
        (True, "No TensorFlow GPU detected") as this is a safe state.

        Example:
            >>> detector = TensorFlowDetector()
            >>> is_safe, message = detector.check_memory_growth_enabled()
            >>> if not is_safe:
            ...     print(f"Warning: {message}")
        """
        tf = self._ensure_tensorflow()

        if tf is None:
            return (True, "TensorFlow is not installed - no configuration needed.")

        try:
            gpus = tf.config.list_physical_devices("GPU")
            if not gpus:
                return (True, "No TensorFlow GPU devices detected - no configuration needed.")

            # Check memory growth setting for each GPU
            all_enabled = True
            disabled_gpus = []

            for gpu in gpus:
                try:
                    growth_enabled = tf.config.experimental.get_memory_growth(gpu)
                    if not growth_enabled:
                        all_enabled = False
                        disabled_gpus.append(gpu.name)
                except (RuntimeError, AttributeError):
                    # May fail if already initialized
                    all_enabled = False
                    disabled_gpus.append(gpu.name)

            if all_enabled:
                return (
                    True,
                    "TensorFlow memory growth is enabled - GPU memory sharing is possible.",
                )
            else:
                return (
                    False,
                    f"TensorFlow memory growth is NOT enabled for: {', '.join(disabled_gpus)}. "
                    "TensorFlow may pre-allocate ALL GPU memory, preventing other "
                    "frameworks from using the GPU. Call tf.config.experimental."
                    "set_memory_growth(gpu, True) BEFORE any TensorFlow operations.",
                )

        except (RuntimeError, AttributeError) as e:
            return (
                False,
                f"Unable to check TensorFlow memory growth configuration: {e}. "
                "Ensure tf.config.experimental.set_memory_growth() is called "
                "before any TensorFlow operations.",
            )

    def get_user_guidance(self) -> str:
        """
        Return comprehensive documentation for TensorFlow + Epochly coexistence.

        This provides users with the necessary code to configure TensorFlow
        for shared GPU memory usage.

        Returns:
            Multi-line string with setup instructions and code example.

        Example:
            >>> detector = TensorFlowDetector()
            >>> print(detector.get_user_guidance())
        """
        return '''TensorFlow + Epochly GPU Memory Configuration
=============================================

CRITICAL: TensorFlow pre-allocates ALL GPU memory by default.
To allow Epochly (and other frameworks) to share GPU memory,
you MUST configure TensorFlow BEFORE any TensorFlow operations.

REQUIRED SETUP (add this at the START of your script):
------------------------------------------------------

import tensorflow as tf

# Configure memory growth BEFORE any TF operations
gpus = tf.config.list_physical_devices('GPU')
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu, True)

# NOW you can import and use Epochly
import epochly

# Your TensorFlow and Epochly code here...


ALTERNATIVE: Limit TensorFlow memory usage
------------------------------------------

import tensorflow as tf

# Limit TF to use only 4GB of GPU memory
gpus = tf.config.list_physical_devices('GPU')
for gpu in gpus:
    tf.config.set_logical_device_configuration(
        gpu,
        [tf.config.LogicalDeviceConfiguration(memory_limit=4096)]
    )


WHY THIS IS NECESSARY:
- TensorFlow's default behavior is to allocate ALL available GPU memory
- This prevents CuPy, PyTorch, and Epochly from using the GPU
- The set_memory_growth() call makes TF allocate memory on-demand
- This MUST be done BEFORE any TensorFlow operations (including imports
  that trigger TF initialization)

IMPORT ORDER MATTERS:
1. Import tensorflow
2. Configure memory growth
3. Import epochly (and other GPU frameworks)
4. Run your code

If you see "failed to allocate memory" errors, TensorFlow likely
grabbed all GPU memory before other frameworks could initialize.
'''


# Module-level singleton for convenience (thread-safe)
_detector: Optional[TensorFlowDetector] = None
_detector_lock = threading.Lock()


def get_tensorflow_detector() -> TensorFlowDetector:
    """
    Get or create the module-level TensorFlowDetector singleton.

    This function is thread-safe and uses double-checked locking to
    minimize lock contention after initialization.

    Returns:
        The shared TensorFlowDetector instance.

    Example:
        >>> detector = get_tensorflow_detector()
        >>> if detector.detect_tensorflow_active():
        ...     print(detector.get_user_guidance())
    """
    global _detector
    if _detector is None:
        with _detector_lock:
            # Double-check after acquiring lock
            if _detector is None:
                _detector = TensorFlowDetector()
    return _detector


def is_tensorflow_active() -> bool:
    """
    Convenience function to check if TensorFlow with GPU is available.

    Returns:
        True if TensorFlow is installed and has GPU access.

    Example:
        >>> if is_tensorflow_active():
        ...     print("TensorFlow GPU detected")
    """
    return get_tensorflow_detector().detect_tensorflow_active()
