"""
Epochly Plugins Package

This package provides the plugin management system for the Epochly (Epochly) framework.
It enables modular extension of Epochly functionality through a plugin architecture.

Author: Epochly Development Team
"""

from .plugin_manager import PluginManager, PluginInterface
from .base_plugins import (
    EpochlyPlugin, EpochlyAnalyzer, EpochlyExecutor, EpochlyOptimizer, EpochlyCommunicator, EpochlyMonitor,
    PluginType, PluginPriority, PluginMetadata,
    create_analyzer_metadata, create_executor_metadata, create_optimizer_metadata,
    create_communicator_metadata, create_monitor_metadata
)
from .communication import (
    MessageType, MessagePriority, PluginMessage, PluginMessageEvent,
    PluginCommunicationProtocol, EventBusPluginCommunication, PluginMessageHandler,
    send_plugin_notification, broadcast_plugin_message
)
from .performance import (
    MessageBatcher, EventBusConnectionPool, MessageCompressor, PerformanceConfig,
    get_message_batcher, get_connection_pool, shutdown_performance_utilities
)
from .metrics import (
    MetricType, CommunicationMetrics, CommunicationHealthCheck, MetricsCollector,
    get_metrics_collector, reset_global_metrics
)
from .security import (
    MessageValidator, RetryPolicy, CircuitBreaker, SecurityConfig,
    ValidationResult, ValidationError, CircuitBreakerOpenError, CircuitBreakerState,
    configure_security, get_message_validator, get_retry_policy, get_circuit_breaker,
    reset_security_utilities
)
from .advanced import (
    MessagePriority as AdvancedMessagePriority, PriorityMessage, PriorityMessageQueue,
    FailedMessage, DeadLetterQueue,
    get_priority_queue, get_dead_letter_queue, reset_global_queues
)

# Import analyzer components for Week 4 integration
from .analyzer import (
    WorkloadDetectionAnalyzer, MemoryProfiler, MemoryPoolSelector, AdaptiveOrchestrator,
    WorkloadPattern, AllocationPattern, SelectionCriteria, MemoryStats,
    WorkloadCharacteristics, AllocationEvent, AllocationInfo,
    PoolRecommendation, PoolScore, AdaptationTrigger, AdaptationEvent, OrchestrationConfig
)

__all__ = [
    'PluginManager', 'PluginInterface',
    'EpochlyPlugin', 'EpochlyAnalyzer', 'EpochlyExecutor', 'EpochlyOptimizer', 'EpochlyCommunicator', 'EpochlyMonitor',
    'PluginType', 'PluginPriority', 'PluginMetadata',
    'create_analyzer_metadata', 'create_executor_metadata', 'create_optimizer_metadata',
    'create_communicator_metadata', 'create_monitor_metadata',
    'MessageType', 'MessagePriority', 'PluginMessage', 'PluginMessageEvent',
    'PluginCommunicationProtocol', 'EventBusPluginCommunication', 'PluginMessageHandler',
    'send_plugin_notification', 'broadcast_plugin_message',
    'MessageBatcher', 'EventBusConnectionPool', 'MessageCompressor', 'PerformanceConfig',
    'get_message_batcher', 'get_connection_pool', 'shutdown_performance_utilities',
    'MetricType', 'CommunicationMetrics', 'CommunicationHealthCheck', 'MetricsCollector',
    'get_metrics_collector', 'reset_global_metrics',
    'MessageValidator', 'RetryPolicy', 'CircuitBreaker', 'SecurityConfig',
    'ValidationResult', 'ValidationError', 'CircuitBreakerOpenError', 'CircuitBreakerState',
    'configure_security', 'get_message_validator', 'get_retry_policy', 'get_circuit_breaker',
    'reset_security_utilities',
    'AdvancedMessagePriority', 'PriorityMessage', 'PriorityMessageQueue',
    'FailedMessage', 'DeadLetterQueue',
    'get_priority_queue', 'get_dead_letter_queue', 'reset_global_queues',
    # Week 4 Analyzer Components
    'WorkloadDetectionAnalyzer', 'MemoryProfiler', 'MemoryPoolSelector', 'AdaptiveOrchestrator',
    'WorkloadPattern', 'AllocationPattern', 'SelectionCriteria', 'MemoryStats',
    'WorkloadCharacteristics', 'AllocationEvent', 'AllocationInfo',
    'PoolRecommendation', 'PoolScore', 'AdaptationTrigger', 'AdaptationEvent', 'OrchestrationConfig'
]