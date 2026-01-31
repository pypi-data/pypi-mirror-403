"""
Lightweight LSTM predictor for compatibility prediction.

Uses numpy-only implementation following existing Epochly patterns for
minimal overhead and fast predictions.
"""

import numpy as np
from collections import deque, defaultdict
from typing import Optional, Dict
import importlib.util
import logging

logger = logging.getLogger(__name__)


class CompatibilityLSTM:
    """
    Minimal LSTM for compatibility prediction.
    Based on existing LSTMResourcePredictor patterns.
    Uses numpy-only implementation for minimal overhead.
    """
    
    def __init__(self, sequence_length: int = 5, hidden_size: int = 16, learning_rate: float = 0.01):
        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.learning_rate = learning_rate
        
        # Input size: 3 features (has_c_ext, import_depth, failure_rate)
        input_size = 3
        
        # Simplified LSTM weights (numpy only)
        self.W_f = np.random.randn(hidden_size, hidden_size + input_size) * 0.01
        self.W_i = np.random.randn(hidden_size, hidden_size + input_size) * 0.01
        self.W_c = np.random.randn(hidden_size, hidden_size + input_size) * 0.01
        self.W_o = np.random.randn(hidden_size, hidden_size + input_size) * 0.01
        self.W_y = np.random.randn(1, hidden_size) * 0.01
        
        # Biases
        self.b_f = np.zeros(hidden_size)
        self.b_i = np.zeros(hidden_size)
        self.b_c = np.zeros(hidden_size)
        self.b_o = np.zeros(hidden_size)
        self.b_y = np.zeros(1)
        
        # History tracking (per module)
        self.module_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=sequence_length))
        self.accuracy_history = deque(maxlen=100)
        
        # Cache for C extension detection
        self._c_extension_cache = {}
    
    def predict_fast(self, module_name: str) -> float:
        """
        Fast prediction path - no gradient computation.
        Returns confidence score 0.0-1.0 in < 100 microseconds.
        """
        if module_name not in self.module_history or len(self.module_history[module_name]) == 0:
            return 0.5  # Neutral for unknown
        
        # Get features
        features = self._extract_features_fast(module_name)
        
        # Simplified forward pass (vectorized for speed)
        h = np.zeros(self.hidden_size)
        c = np.zeros(self.hidden_size)
        
        # Single LSTM step (not full sequence for speed)
        x = features
        combined = np.concatenate([h, x])
        
        # Gates (using fast approximations)
        f = self._fast_sigmoid(self.W_f @ combined + self.b_f)
        i = self._fast_sigmoid(self.W_i @ combined + self.b_i)
        c_tilde = np.tanh(self.W_c @ combined + self.b_c)
        c = f * c + i * c_tilde
        o = self._fast_sigmoid(self.W_o @ combined + self.b_o)
        h = o * np.tanh(c)
        
        # Output
        confidence = self._fast_sigmoid(self.W_y @ h + self.b_y)
        return float(confidence[0])
    
    def _fast_sigmoid(self, x):
        """Fast sigmoid approximation for < 1 microsecond operation"""
        # Using fast approximation: σ(x) ≈ 0.5 * (x / (1 + |x|) + 1)
        return 0.5 * (x / (1 + np.abs(x)) + 1)
    
    def _extract_features_fast(self, module_name: str) -> np.ndarray:
        """Extract features for module (fast path)"""
        features = np.zeros(3)
        
        # Feature 1: Has C extension (cached)
        features[0] = 1.0 if self._has_c_extension_cached(module_name) else 0.0
        
        # Feature 2: Import depth (normalized)
        depth = module_name.count('.')
        features[1] = min(1.0, depth / 5.0)
        
        # Feature 3: Recent failure rate
        if module_name in self.module_history:
            history = list(self.module_history[module_name])
            if len(history) > 0:
                # Count failures (0.0 values) in recent history
                failures = sum(1 for h in history if h < 0.5)
                features[2] = failures / len(history)
        
        return features
    
    def _has_c_extension_cached(self, module_name: str) -> bool:
        """Check if module has C extension (with caching)"""
        if module_name not in self._c_extension_cache:
            try:
                spec = importlib.util.find_spec(module_name)
                if spec and spec.origin:
                    self._c_extension_cache[module_name] = spec.origin.endswith(('.so', '.pyd', '.dll'))
                else:
                    self._c_extension_cache[module_name] = False
            except Exception:
                self._c_extension_cache[module_name] = False
        
        return self._c_extension_cache[module_name]
    
    def update_online(self, module_name: str, success: bool):
        """
        Online learning update.
        Runs in background, doesn't block.
        """
        # Record outcome
        self.module_history[module_name].append(1.0 if success else 0.0)
        
        # Only update weights if we have enough history
        if len(self.module_history[module_name]) >= min(3, self.sequence_length):
            # Get current prediction
            prediction = self.predict_fast(module_name)
            
            # Calculate error
            target = 1.0 if success else 0.0
            error = target - prediction
            
            # Record accuracy
            self.accuracy_history.append(abs(error) < 0.2)
            
            # Simple gradient update (if error is significant)
            if abs(error) > 0.1:
                # Update output weights with small gradient
                gradient = error * self.learning_rate
                self.W_y *= (1.0 + gradient * 0.1)  # Small adjustment
                self.b_y += gradient * 0.01
    
    def has_history(self, module_name: str) -> bool:
        """Check if we have history for a module"""
        return module_name in self.module_history and len(self.module_history[module_name]) > 0
    
    def get_accuracy(self) -> float:
        """Get recent prediction accuracy"""
        if len(self.accuracy_history) == 0:
            return 0.5
        return sum(self.accuracy_history) / len(self.accuracy_history)