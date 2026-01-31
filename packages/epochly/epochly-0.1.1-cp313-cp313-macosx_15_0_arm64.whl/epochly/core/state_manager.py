"""
State persistence system for crash recovery.

This module provides mechanisms to save and restore Epochly's runtime state
across process restarts, enabling warm startup and recovery from abnormal
shutdowns.
"""
import os
import sys
import time
import pickle
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List
from ..utils.logger import get_logger


class StateManager:
    """
    Manages persistence of Epochly runtime state for crash recovery.

    State includes:
    - Enhancement level
    - Hot functions identified by profiler
    - Performance history and metrics
    - Learned workload patterns
    - ML model states (LSTM weights, etc.)

    Thread-safe for concurrent save operations.
    """

    def __init__(self, state_dir: str = '~/.epochly/state'):
        """
        Initialize state manager.

        Args:
            state_dir: Directory to store state files (default: ~/.epochly/state)
        """
        self.state_dir = Path(state_dir).expanduser()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)
        self._lock = threading.RLock()

    def save_state(self, core) -> bool:
        """
        Save Epochly core state for crash recovery.

        Args:
            core: EpochlyCore instance to save state from

        Returns:
            bool: True if state was saved successfully, False otherwise
        """
        with self._lock:
            try:
                # Collect state from various components
                state = {
                    'version': '1.0.0',  # State format version
                    'timestamp': time.time(),
                    'python_version': sys.version_info[:2],
                    'pid': os.getpid(),
                }

                # Enhancement level
                if hasattr(core, 'current_level'):
                    state['enhancement_level'] = core.current_level.value
                else:
                    state['enhancement_level'] = 0

                # Hot functions from auto-profiler
                if hasattr(core, '_auto_profiler') and core._auto_profiler:
                    try:
                        hot_loops = core._auto_profiler.get_hot_loops()
                        state['hot_functions'] = hot_loops if hot_loops else []
                    except Exception as e:
                        self.logger.debug(f"Could not get hot loops: {e}")
                        state['hot_functions'] = []
                else:
                    state['hot_functions'] = []

                # Performance history
                if hasattr(core, 'performance_monitor') and core.performance_monitor:
                    try:
                        metrics = core.performance_monitor.get_metrics()
                        # Only persist serializable metrics
                        state['performance_history'] = self._sanitize_metrics(metrics)
                    except Exception as e:
                        self.logger.debug(f"Could not get performance metrics: {e}")
                        state['performance_history'] = {}
                else:
                    state['performance_history'] = {}

                # Workload patterns from adaptive orchestrator
                if hasattr(core, '_adaptive_orchestrator') and core._adaptive_orchestrator:
                    try:
                        patterns = core._adaptive_orchestrator.get_learned_patterns()
                        state['workload_patterns'] = patterns if patterns else {}
                    except Exception as e:
                        self.logger.debug(f"Could not get workload patterns: {e}")
                        state['workload_patterns'] = {}
                else:
                    state['workload_patterns'] = {}

                # ML model states (if any)
                state['ml_model_states'] = self._extract_ml_model_states(core)

                # Write state to file
                state_file = self.state_dir / f'epochly_state_{os.getpid()}.pkl'
                with open(state_file, 'wb') as f:
                    pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)

                self.logger.debug(f"State saved to {state_file}")
                return True

            except Exception as e:
                self.logger.error(f"Failed to save state: {e}")
                return False

    def load_state(self) -> Optional[Dict[str, Any]]:
        """
        Load most recent compatible state.

        Searches for state files, validates compatibility, and returns
        the most recent valid state.

        Returns:
            Dict with state data if found and compatible, None otherwise
        """
        with self._lock:
            try:
                # Find all state files, sorted by modification time (newest first)
                state_files = sorted(
                    self.state_dir.glob('epochly_state_*.pkl'),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )

                if not state_files:
                    self.logger.debug("No state files found")
                    return None

                # Try to load the most recent compatible state
                for state_file in state_files:
                    try:
                        with open(state_file, 'rb') as f:
                            state = pickle.load(f)

                        # Validate Python version compatibility
                        if 'python_version' not in state:
                            self.logger.debug(f"Skipping {state_file.name}: missing Python version")
                            continue

                        if state['python_version'] != sys.version_info[:2]:
                            self.logger.debug(
                                f"Skipping {state_file.name}: Python {state['python_version']} "
                                f"state incompatible with current {sys.version_info[:2]}"
                            )
                            continue

                        # Validate state format version
                        if 'version' not in state:
                            self.logger.debug(f"Skipping {state_file.name}: missing state version")
                            continue

                        # Check if state is too old (>7 days)
                        state_age = time.time() - state.get('timestamp', 0)
                        if state_age > 7 * 24 * 3600:  # 7 days
                            self.logger.debug(f"Skipping {state_file.name}: state too old ({state_age/3600:.1f}h)")
                            continue

                        self.logger.info(f"Loaded state from {state_file.name} (age: {state_age:.1f}s)")
                        return state

                    except (pickle.UnpicklingError, EOFError, AttributeError) as e:
                        self.logger.debug(f"Could not load {state_file.name}: {e}")
                        continue
                    except Exception as e:
                        self.logger.warning(f"Error loading {state_file.name}: {e}")
                        continue

                self.logger.debug("No compatible state files found")
                return None

            except Exception as e:
                self.logger.error(f"Failed to load state: {e}")
                return None

    def restore_state(self, core, state: Dict[str, Any]) -> bool:
        """
        Restore Epochly state to core instance.

        Args:
            core: EpochlyCore instance to restore state to
            state: State dictionary from load_state()

        Returns:
            bool: True if state was restored successfully, False otherwise
        """
        if not state:
            return False

        with self._lock:
            try:
                # Restore enhancement level (unless explicitly overridden by EPOCHLY_LEVEL env var)
                if 'enhancement_level' in state and not os.environ.get('EPOCHLY_LEVEL'):
                    try:
                        from ..core.epochly_core import EnhancementLevel
                        target_level = EnhancementLevel(state['enhancement_level'])
                        current_level = core.current_level if hasattr(core, 'current_level') else EnhancementLevel.LEVEL_0_MONITOR

                        # FIX (Dec 2025): Only call set_enhancement_level if we need to UPGRADE
                        # If already at or above the target level, don't re-initialize systems
                        # This prevents thread double-start issues when background detection
                        # has already upgraded the level before state restoration runs.
                        if current_level.value < target_level.value:
                            success = core.set_enhancement_level(target_level, force=True)
                            if success:
                                self.logger.debug(f"Restored enhancement level: {target_level.name}")
                            else:
                                self.logger.warning(f"Failed to restore enhancement level to {target_level.name}")
                        else:
                            self.logger.debug(f"Already at {current_level.name}, skipping level restoration (target: {target_level.name})")
                    except Exception as e:
                        self.logger.warning(f"Could not restore enhancement level: {e}")

                # Restore hot functions to auto-profiler
                if 'hot_functions' in state and state['hot_functions']:
                    if hasattr(core, '_auto_profiler') and core._auto_profiler:
                        try:
                            # Auto-profiler should have a method to restore hot loops
                            if hasattr(core._auto_profiler, 'restore_hot_loops'):
                                core._auto_profiler.restore_hot_loops(state['hot_functions'])
                                self.logger.debug(f"Restored {len(state['hot_functions'])} hot functions")
                        except Exception as e:
                            self.logger.debug(f"Could not restore hot functions: {e}")

                # Restore performance history
                if 'performance_history' in state and state['performance_history']:
                    if hasattr(core, 'performance_monitor') and core.performance_monitor:
                        try:
                            # Performance monitor should have a method to restore metrics
                            if hasattr(core.performance_monitor, 'restore_metrics'):
                                core.performance_monitor.restore_metrics(state['performance_history'])
                                self.logger.debug("Restored performance history")
                        except Exception as e:
                            self.logger.debug(f"Could not restore performance history: {e}")

                # Restore workload patterns to orchestrator
                if 'workload_patterns' in state and state['workload_patterns']:
                    if hasattr(core, '_adaptive_orchestrator') and core._adaptive_orchestrator:
                        try:
                            # Orchestrator should have a method to restore patterns
                            if hasattr(core._adaptive_orchestrator, 'restore_learned_patterns'):
                                core._adaptive_orchestrator.restore_learned_patterns(state['workload_patterns'])
                                self.logger.debug("Restored workload patterns")
                        except Exception as e:
                            self.logger.debug(f"Could not restore workload patterns: {e}")

                # Restore ML model states
                if 'ml_model_states' in state and state['ml_model_states']:
                    self._restore_ml_model_states(core, state['ml_model_states'])

                self.logger.info("State restoration completed")
                return True

            except Exception as e:
                self.logger.error(f"Failed to restore state: {e}")
                return False

    def cleanup_old_state(self, max_age_days: int = 7, max_files: int = 10):
        """
        Clean up old state files.

        Args:
            max_age_days: Remove files older than this many days
            max_files: Keep at most this many recent files
        """
        with self._lock:
            try:
                state_files = sorted(
                    self.state_dir.glob('epochly_state_*.pkl'),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )

                now = time.time()
                max_age_seconds = max_age_days * 24 * 3600
                removed_count = 0

                # Remove old files and keep only max_files recent ones
                for i, state_file in enumerate(state_files):
                    should_remove = False

                    # Remove if too old
                    age = now - state_file.stat().st_mtime
                    if age > max_age_seconds:
                        should_remove = True
                        reason = f"age {age/3600:.1f}h > {max_age_days}d"

                    # Remove if beyond max_files limit
                    elif i >= max_files:
                        should_remove = True
                        reason = f"beyond limit (#{i+1} > {max_files})"

                    if should_remove:
                        try:
                            state_file.unlink()
                            removed_count += 1
                            self.logger.debug(f"Removed {state_file.name}: {reason}")
                        except Exception as e:
                            self.logger.warning(f"Could not remove {state_file.name}: {e}")

                if removed_count > 0:
                    self.logger.info(f"Cleaned up {removed_count} old state files")

            except Exception as e:
                self.logger.error(f"Failed to cleanup old state: {e}")

    def _sanitize_metrics(self, metrics: Any) -> Dict[str, Any]:
        """
        Sanitize metrics to ensure they are pickleable.

        Removes thread objects, file handles, and other non-serializable items.

        Args:
            metrics: Metrics object to sanitize

        Returns:
            Sanitized dictionary safe for pickle
        """
        if not metrics:
            return {}

        try:
            # If it's already a dict, filter it
            if isinstance(metrics, dict):
                sanitized = {}
                for key, value in metrics.items():
                    # Skip non-serializable types
                    if isinstance(value, (str, int, float, bool, list, dict, tuple)):
                        sanitized[key] = value
                    elif hasattr(value, '__dict__'):
                        # Try to extract simple attributes
                        try:
                            sanitized[key] = {
                                k: v for k, v in value.__dict__.items()
                                if isinstance(v, (str, int, float, bool, list, dict, tuple))
                            }
                        except:
                            pass
                return sanitized
            else:
                # Try to convert to dict
                return {}
        except Exception as e:
            self.logger.debug(f"Could not sanitize metrics: {e}")
            return {}

    def _extract_ml_model_states(self, core) -> Dict[str, Any]:
        """
        Extract ML model states (e.g., LSTM weights) for persistence.

        Args:
            core: EpochlyCore instance

        Returns:
            Dictionary of model states
        """
        ml_states = {}

        try:
            # Check for LSTM models in adaptive orchestrator
            if hasattr(core, '_adaptive_orchestrator') and core._adaptive_orchestrator:
                orchestrator = core._adaptive_orchestrator

                # Check if orchestrator has ML models
                if hasattr(orchestrator, 'get_model_state'):
                    try:
                        model_state = orchestrator.get_model_state()
                        if model_state:
                            ml_states['adaptive_orchestrator'] = model_state
                    except Exception as e:
                        self.logger.debug(f"Could not get orchestrator model state: {e}")

        except Exception as e:
            self.logger.debug(f"Could not extract ML model states: {e}")

        return ml_states

    def _restore_ml_model_states(self, core, ml_states: Dict[str, Any]):
        """
        Restore ML model states.

        Args:
            core: EpochlyCore instance
            ml_states: Dictionary of model states to restore
        """
        try:
            # Restore adaptive orchestrator model
            if 'adaptive_orchestrator' in ml_states:
                if hasattr(core, '_adaptive_orchestrator') and core._adaptive_orchestrator:
                    orchestrator = core._adaptive_orchestrator

                    if hasattr(orchestrator, 'restore_model_state'):
                        try:
                            orchestrator.restore_model_state(ml_states['adaptive_orchestrator'])
                            self.logger.debug("Restored adaptive orchestrator model state")
                        except Exception as e:
                            self.logger.debug(f"Could not restore orchestrator model: {e}")

        except Exception as e:
            self.logger.debug(f"Could not restore ML model states: {e}")


# Global state manager instance
_state_manager: Optional[StateManager] = None
_state_manager_lock = threading.Lock()


def get_state_manager() -> StateManager:
    """
    Get the global state manager instance (singleton).

    Returns:
        StateManager instance
    """
    global _state_manager

    if _state_manager is None:
        with _state_manager_lock:
            if _state_manager is None:
                _state_manager = StateManager()

    return _state_manager


def _reset_state_manager() -> None:
    """
    Reset the global state manager singleton.

    This is primarily for testing to ensure test isolation.
    Each test gets a fresh state manager instance.
    """
    global _state_manager

    with _state_manager_lock:
        _state_manager = None
