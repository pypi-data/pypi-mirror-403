"""
JIT Manager Extensions for SPEC2 Task 12 (sys.monitoring integration).

Provides record_execution method for sys.monitoring callbacks.
"""


def add_sys_monitoring_support(jit_manager):
    """
    Add sys.monitoring support methods to JITManager.

    Args:
        jit_manager: JITManager instance to extend
    """
    def record_execution(func_name: str, code_object=None):
        """
        Record function execution from sys.monitoring.

        Called by sys.monitoring callbacks to track hot paths.

        Args:
            func_name: Function name
            code_object: Optional code object
        """
        if not hasattr(jit_manager, '_execution_counts'):
            jit_manager._execution_counts = {}

        jit_manager._execution_counts[func_name] = jit_manager._execution_counts.get(func_name, 0) + 1

        # Feed to adaptive policy if available
        if jit_manager._telemetry_store:
            jit_manager._telemetry_store.record_call(func_name)

        # Check if function is hot enough for compilation
        count = jit_manager._execution_counts[func_name]
        if count >= jit_manager.config.min_function_calls:
            # Mark as hot path candidate (P0.14: Also skip failed compilations)
            if func_name not in jit_manager.compilation_queue and func_name not in jit_manager.compiled_functions and func_name not in jit_manager._failed_compilations:
                jit_manager.compilation_queue.add(func_name)
                jit_manager.logger.debug(f"Function {func_name} marked as hot (count={count})")

    # Attach method to JITManager instance
    jit_manager.record_execution = record_execution
