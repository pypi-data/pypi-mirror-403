"""
Subprocess Safety Detection for Epochly

Detects when Epochly is running inside a subprocess and prevents nested process
spawning deadlocks that occur with:
- pytest test execution
- CI/CD pipeline jobs
- Task queue workers (Celery, RQ)
- Containerized environments

When nested subprocess is detected, Epochly automatically downgrades from Level 3
(sub-interpreters + multiprocessing) to Level 2 (JIT only) to avoid deadlocks.

This implements the "it just works or gets out of the way" philosophy.

Author: Epochly Development Team
Date: November 19, 2025
"""

import os
import sys
import subprocess
import multiprocessing
from dataclasses import dataclass
from typing import Optional

# Try to import psutil for parent process detection
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from ..core.epochly_core import EnhancementLevel
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SubprocessContext:
    """
    Context information about subprocess environment.

    Attributes:
        is_nested: Whether running inside a subprocess
        can_spawn: Whether process spawning is safe
        parent_name: Name of parent process
        is_pytest: Whether running under pytest
        is_ci: Whether running in CI/CD
        is_worker: Whether running as task queue worker
    """
    is_nested: bool
    can_spawn: bool
    parent_name: str
    is_pytest: bool = False
    is_ci: bool = False
    is_worker: bool = False

    @property
    def is_safe_for_level3(self) -> bool:
        """
        Check if environment is safe for Level 3 (sub-interpreters + multiprocessing).

        Returns:
            True if Level 3 is safe, False if should downgrade
        """
        # Level 3 requires both:
        # 1. Not nested in subprocess (no existing multiprocessing context)
        # 2. Able to spawn new processes successfully
        return not self.is_nested and self.can_spawn


def is_nested_subprocess() -> bool:
    """
    Detect if running inside a subprocess.

    Checks multiple heuristics:
    1. multiprocessing.current_process() name (not 'MainProcess')
    2. PYTEST_CURRENT_TEST environment variable
    3. Parent process name (pytest, celery, worker)
    4. CI/CD environment variables

    Returns:
        True if running in subprocess, False if main process
    """
    # Check 1: multiprocessing context
    try:
        current_proc = multiprocessing.current_process()
        if current_proc.name != 'MainProcess':
            logger.debug(f"Detected subprocess: process name = {current_proc.name}")
            return True
    except Exception:
        pass

    # Check 2: Pytest environment
    if 'PYTEST_CURRENT_TEST' in os.environ:
        logger.debug("Detected pytest subprocess: PYTEST_CURRENT_TEST present")
        return True

    # Check 3: Parent process name (requires psutil)
    if PSUTIL_AVAILABLE:
        try:
            parent = psutil.Process(os.getppid())
            parent_name = parent.name().lower()

            # Check for common subprocess parents
            subprocess_indicators = ['pytest', 'celery', 'worker', 'gunicorn', 'uwsgi']
            for indicator in subprocess_indicators:
                if indicator in parent_name:
                    logger.debug(f"Detected subprocess: parent name contains '{indicator}'")
                    return True
        except Exception:
            pass

    # Check 4: CI environment (heuristic - may run in main process)
    ci_vars = ['CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'JENKINS_HOME', 'TRAVIS']
    if any(var in os.environ for var in ci_vars):
        # CI environments often have process spawning restrictions
        # Be conservative: treat as subprocess
        logger.debug("Detected CI environment: treating as subprocess for safety")
        return True

    # Appears to be main process
    return False


def can_spawn_processes_safely() -> bool:
    """
    Test if process spawning is safe and functional.

    Attempts to spawn a simple subprocess and checks if it completes successfully.
    This catches environments where multiprocessing doesn't work (containers,
    restrictive security policies, etc.)

    Returns:
        True if spawning works, False if spawning fails/hangs
    """
    try:
        # Quick spawn test with timeout
        result = subprocess.run(
            [sys.executable, '-c', 'print("ok")'],
            capture_output=True,
            timeout=1.0
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.warning("Process spawning timeout detected - multiprocessing may deadlock")
        return False
    except Exception as e:
        logger.warning(f"Process spawning failed: {e}")
        return False


def detect_subprocess_context() -> SubprocessContext:
    """
    Detect complete subprocess context.

    Returns:
        SubprocessContext with all detection results
    """
    is_nested = is_nested_subprocess()
    can_spawn = can_spawn_processes_safely()

    # Determine parent process name
    parent_name = 'unknown'
    if PSUTIL_AVAILABLE:
        try:
            parent = psutil.Process(os.getppid())
            parent_name = parent.name()
        except:
            pass

    # Specific environment flags
    is_pytest = 'PYTEST_CURRENT_TEST' in os.environ
    is_ci = any(var in os.environ for var in ['CI', 'GITHUB_ACTIONS', 'GITLAB_CI'])
    is_worker = multiprocessing.current_process().name != 'MainProcess'

    return SubprocessContext(
        is_nested=is_nested,
        can_spawn=can_spawn,
        parent_name=parent_name,
        is_pytest=is_pytest,
        is_ci=is_ci,
        is_worker=is_worker
    )


def get_max_safe_level(context: SubprocessContext) -> EnhancementLevel:
    """
    Get maximum safe enhancement level for current subprocess context.

    Args:
        context: Subprocess context information

    Returns:
        Maximum safe EnhancementLevel

    Environment Variables:
        EPOCHLY_FORCE_LEVEL3: Set to '1' to override safety check (may cause deadlocks)
    """
    # Check for explicit override
    if os.environ.get('EPOCHLY_FORCE_LEVEL3') == '1':
        logger.warning(
            "EPOCHLY_FORCE_LEVEL3=1: Overriding subprocess safety check. "
            "This may cause deadlocks if multiprocessing is used. "
            "Remove this variable if you experience hangs."
        )
        return EnhancementLevel.LEVEL_3_FULL

    # Determine safe level based on context
    if context.is_safe_for_level3:
        # Safe environment: All levels available
        return EnhancementLevel.LEVEL_3_FULL
    else:
        # Unsafe environment: Limit to Level 2 (JIT only, no multiprocessing)
        if context.is_nested:
            logger.info(
                "Subprocess detected: Limiting to Level 2 (JIT only). "
                "Level 3 (sub-interpreters) skipped to avoid multiprocessing deadlocks. "
                "Set EPOCHLY_FORCE_LEVEL3=1 to override."
            )
        elif not context.can_spawn:
            logger.info(
                "Process spawning unavailable: Limiting to Level 2 (JIT only). "
                "Environment may have restrictions on multiprocessing."
            )

        return EnhancementLevel.LEVEL_2_JIT
