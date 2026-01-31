"""
Telemetry aggregator for local metric aggregation before streaming.

Reduces bandwidth by calculating percentiles and patterns locally.
"""

import numpy as np
import time
import logging
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)


class TelemetryAggregator:
    """
    Local aggregation before streaming to reduce bandwidth.
    Calculates percentiles, rates, and patterns locally.
    """
    
    def __init__(self, streamer):
        self.streamer = streamer
        
        # Aggregation windows
        self.window_1m = deque(maxlen=60)   # 1 minute
        self.window_5m = deque(maxlen=300)  # 5 minutes
        self.window_1h = deque(maxlen=3600) # 1 hour
        
        # Pre-calculated stats
        self.p50_latency = 0.0
        self.p99_latency = 0.0
        self.error_rate = 0.0
        self.total_checks = 0
        
        # Module-specific stats
        self.module_stats = {}
    
    def aggregate_metrics(self):
        """Calculate aggregated metrics for streaming"""
        if self.streamer.metrics_index == 0:
            return
        
        # Extract latencies from buffer
        current_idx = min(self.streamer.metrics_index, 10000)
        latencies = self.streamer.metrics_buffer[:current_idx, 4]
        
        if len(latencies) > 0:
            # Calculate percentiles
            self.p50_latency = float(np.percentile(latencies, 50))
            self.p99_latency = float(np.percentile(latencies, 99))
            
            # Calculate error rate
            successes = self.streamer.metrics_buffer[:current_idx, 6]
            self.error_rate = 1.0 - (np.mean(successes) if len(successes) > 0 else 1.0)
            
            # Total checks
            self.total_checks = current_idx
        
        # Stream aggregated metrics
        self.streamer.record_event('aggregated_metrics', {
            'p50_latency_us': self.p50_latency,
            'p99_latency_us': self.p99_latency,
            'error_rate': self.error_rate,
            'total_checks': self.total_checks
        })
    
    def update_module_stats(self, module_name: str, latency_us: float, success: bool):
        """Update per-module statistics"""
        if module_name not in self.module_stats:
            self.module_stats[module_name] = {
                'count': 0,
                'successes': 0,
                'total_latency': 0.0,
                'max_latency': 0.0,
                'min_latency': float('inf')
            }
        
        stats = self.module_stats[module_name]
        stats['count'] += 1
        if success:
            stats['successes'] += 1
        stats['total_latency'] += latency_us
        stats['max_latency'] = max(stats['max_latency'], latency_us)
        stats['min_latency'] = min(stats['min_latency'], latency_us)
    
    def get_module_summary(self, module_name: str) -> Optional[dict]:
        """Get summary statistics for a module"""
        if module_name not in self.module_stats:
            return None
        
        stats = self.module_stats[module_name]
        if stats['count'] == 0:
            return None
        
        return {
            'module': module_name,
            'total_checks': stats['count'],
            'success_rate': stats['successes'] / stats['count'],
            'avg_latency_us': stats['total_latency'] / stats['count'],
            'max_latency_us': stats['max_latency'],
            'min_latency_us': stats['min_latency']
        }
    
    def get_system_summary(self) -> dict:
        """Get overall system summary"""
        return {
            'timestamp': time.time(),
            'p50_latency_us': self.p50_latency,
            'p99_latency_us': self.p99_latency,
            'error_rate': self.error_rate,
            'total_checks': self.total_checks,
            'unique_modules': len(self.module_stats)
        }
    
    def record_time_window(self, metrics: dict):
        """Record metrics in time windows for trend analysis"""
        current_time = time.time()
        
        # Add to all windows
        self.window_1m.append((current_time, metrics))
        self.window_5m.append((current_time, metrics))
        self.window_1h.append((current_time, metrics))
    
    def get_trend_analysis(self) -> dict:
        """Analyze trends over different time windows"""
        trends = {}
        
        # 1-minute trend
        if len(self.window_1m) > 10:
            recent = list(self.window_1m)[-10:]
            older = list(self.window_1m)[:10]
            
            recent_errors = sum(1 for _, m in recent if not m.get('success', True))
            older_errors = sum(1 for _, m in older if not m.get('success', True))
            
            trends['1m_error_trend'] = 'increasing' if recent_errors > older_errors else 'stable'
        
        # 5-minute trend
        if len(self.window_5m) > 50:
            recent = list(self.window_5m)[-50:]
            older = list(self.window_5m)[:50]
            
            recent_latencies = [m.get('latency_us', 0) for _, m in recent]
            older_latencies = [m.get('latency_us', 0) for _, m in older]
            
            if recent_latencies and older_latencies:
                recent_avg = np.mean(recent_latencies)
                older_avg = np.mean(older_latencies)
                
                trends['5m_latency_trend'] = 'increasing' if recent_avg > older_avg * 1.1 else 'stable'
        
        return trends
    
    def should_alert(self) -> bool:
        """Determine if current metrics warrant an alert"""
        # High error rate
        if self.error_rate > 0.1:  # > 10% errors
            return True
        
        # High latency
        if self.p99_latency > 5000:  # > 5ms
            return True
        
        # Trend-based alerts
        trends = self.get_trend_analysis()
        if trends.get('1m_error_trend') == 'increasing':
            return True
        
        return False
    
    def reset_stats(self):
        """Reset aggregated statistics"""
        self.p50_latency = 0.0
        self.p99_latency = 0.0
        self.error_rate = 0.0
        self.total_checks = 0
        self.module_stats.clear()