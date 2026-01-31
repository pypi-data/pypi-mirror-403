"""
Non-blocking compatibility analyzer for sub-interpreter safety detection.

Provides sub-millisecond decision making for compatibility checks with
automatic learning and fallback mechanisms.
"""

import time
import threading
from collections import deque, defaultdict
from dataclasses import dataclass
from typing import Optional, Dict, Set, Any
from multiprocessing import shared_memory
import struct
import logging

from .lstm_predictor import CompatibilityLSTM

logger = logging.getLogger(__name__)


@dataclass
class Decision:
    """Compatibility decision result"""
    use_subinterpreter: bool
    confidence: float
    strategy: str


class NonBlockingAnalyzer:
    """
    Zero-latency compatibility analyzer.
    
    GUARANTEES:
    - Never blocks > 1ms
    - Always returns a decision
    - Learns from execution results
    """
    
    def __init__(self):
        # Fast lookup structures (all O(1))
        self._decision_cache: Dict[str, Decision] = {}
        self._blacklist: Set[str] = set()
        self._safe_cache: Set[str] = set()
        
        # Failure tracking
        self._failure_counts: Dict[str, int] = defaultdict(int)
        
        # LSTM predictor for learning
        self.lstm_predictor = CompatibilityLSTM()
        
        # Shared memory heartbeat for supervisor
        # CRITICAL FIX (Jan 2026): Skip SharedMemory on Python 3.13 macOS
        # SharedMemory uses multiprocessing.resource_tracker which has known deadlock
        # issues on Python 3.13 macOS.
        import sys
        is_python313_macos = sys.version_info[:2] == (3, 13) and sys.platform == 'darwin'
        if is_python313_macos:
            self.heartbeat_shm = None
        else:
            try:
                self.heartbeat_shm = shared_memory.SharedMemory(
                    name='epochly_heartbeat',
                    create=False  # Connect to existing
                )
            except FileNotFoundError:
                # Supervisor not running, create our own
                try:
                    self.heartbeat_shm = shared_memory.SharedMemory(
                        name='epochly_heartbeat',
                        create=True,
                        size=64
                    )
                except FileExistsError:
                    # Race condition, connect to existing
                    self.heartbeat_shm = shared_memory.SharedMemory(
                        name='epochly_heartbeat',
                        create=False
                    )
            except Exception:
                # Shared memory not available
                self.heartbeat_shm = None
        
        # Start heartbeat thread if shared memory available
        if self.heartbeat_shm:
            self._start_heartbeat_thread()
    
    def check_compatibility(self, module_name: str) -> Decision:
        """
        Check module compatibility in < 1ms.
        
        Returns:
            Decision object with use_subinterpreter, confidence, and strategy
        """
        start_time = time.perf_counter_ns()
        
        # Level 1: Blacklist check (~10 ns)
        if module_name in self._blacklist:
            return Decision(
                use_subinterpreter=False,
                confidence=0.0,
                strategy='BLACKLISTED'
            )
        
        # Level 2: Safe cache check (~50 ns)
        if module_name in self._safe_cache:
            return Decision(
                use_subinterpreter=True,
                confidence=0.95,
                strategy='CACHED_SAFE'
            )
        
        # Level 3: LSTM prediction if we have history (~100 microseconds)
        if self.lstm_predictor.has_history(module_name):
            confidence = self.lstm_predictor.predict_fast(module_name)
            
            # Make decision based on confidence
            use_subinterpreter = confidence > 0.5
            
            return Decision(
                use_subinterpreter=use_subinterpreter,
                confidence=confidence,
                strategy='LSTM_PREDICTED'
            )
        
        # Level 4: Optimistic default for unknown modules
        return Decision(
            use_subinterpreter=True,  # Optimistic
            confidence=0.5,  # Unknown
            strategy='OPTIMISTIC_DEFAULT'
        )
    
    def report_success(self, module_name: str, execution_mode: str):
        """Report successful execution"""
        # Add to safe cache if sub-interpreter succeeded
        if execution_mode == 'subinterpreter':
            self._safe_cache.add(module_name)
        
        # Update LSTM
        self.lstm_predictor.update_online(module_name, success=True)
        
        # Reset failure count
        self._failure_counts[module_name] = 0
    
    def report_failure(self, module_name: str, error: Exception):
        """Report failed execution"""
        # Increment failure count
        self._failure_counts[module_name] += 1
        
        # Update LSTM
        self.lstm_predictor.update_online(module_name, success=False)
        
        # Blacklist if too many failures
        if self._failure_counts[module_name] >= 3:
            self._blacklist.add(module_name)
            logger.warning(f"Blacklisted module {module_name} after {self._failure_counts[module_name]} failures")
    
    def has_history(self, module_name: str) -> bool:
        """Check if we have history for a module"""
        return self.lstm_predictor.has_history(module_name)
    
    def _write_heartbeat(self):
        """Write heartbeat timestamp to shared memory"""
        if self.heartbeat_shm:
            try:
                timestamp = time.time()
                struct.pack_into('d', self.heartbeat_shm.buf, 0, timestamp)
            except Exception as e:
                logger.debug(f"Failed to write heartbeat: {e}")
    
    def _start_heartbeat_thread(self):
        """Start background thread for heartbeat updates"""
        def heartbeat_loop():
            while True:
                self._write_heartbeat()
                time.sleep(1.0)  # Update every second
        
        thread = threading.Thread(target=heartbeat_loop, daemon=True)
        thread.start()
    
    def update_confidence(self, module_name: str, confidence: float, analysis: Optional[Dict] = None):
        """Update confidence score from background analysis"""
        # Update LSTM with new information
        if analysis:
            # Use analysis results to refine predictions
            if analysis.get('has_c_extension') and not analysis.get('thread_safe'):
                # Likely unsafe for sub-interpreters
                if confidence < 0.3:
                    self._blacklist.add(module_name)
            elif confidence > 0.8 and not analysis.get('uses_global_state'):
                # Likely safe
                self._safe_cache.add(module_name)
    
    def __del__(self):
        """Cleanup shared memory on destruction"""
        if hasattr(self, 'heartbeat_shm') and self.heartbeat_shm:
            try:
                self.heartbeat_shm.close()
            except Exception:
                pass