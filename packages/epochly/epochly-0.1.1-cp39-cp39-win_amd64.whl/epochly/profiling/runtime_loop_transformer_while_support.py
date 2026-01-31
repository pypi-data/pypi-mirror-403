"""
Runtime Loop Transformer - While Loop Support Extension

Adds while loop transformation support to RuntimeLoopTransformer.

Author: Epochly Development Team
Date: November 18, 2025
"""

import functools
from typing import Callable, Optional, Dict, Any

from ..utils.logger import get_logger
from .while_loop_analyzer import analyze_while_loop
from .while_loop_transformer import WhileLoopTransformer

logger = get_logger(__name__)


def add_while_loop_support_to_transformer():
    """
    Monkey-patch RuntimeLoopTransformer to add while loop support.
    """
    from .runtime_loop_transformer import RuntimeLoopTransformer

    # Store original methods
    original_analyze = RuntimeLoopTransformer.analyze_function
    original_create = RuntimeLoopTransformer._create_transformed_function

    def analyze_function_with_while(self, func: Callable) -> Optional[Dict[str, Any]]:
        """
        Extended analyze_function that detects while loops.
        """
        # First try original analysis
        analysis = original_analyze(self, func)

        if analysis:
            # Check if contains while loop
            if 'While' in analysis.get('pattern', ''):
                # Analyze while loop specifically
                while_analysis = analyze_while_loop(func)
                if while_analysis.has_while_loop:
                    analysis['has_while_loop'] = True
                    analysis['while_loop_type'] = while_analysis.condition_type
                    analysis['while_loop_variable'] = while_analysis.loop_variable
                    analysis['while_parallelizable'] = while_analysis.is_parallelizable

        return analysis

    def create_transformed_with_while(self, func: Callable, analysis: Dict[str, Any]) -> Optional[Callable]:
        """
        Extended _create_transformed_function that handles while loops.
        """
        # Check if has while loop
        if analysis.get('has_while_loop', False):
            # Try while loop transformation
            while_transformer = WhileLoopTransformer(
                batch_dispatcher=self._batch_dispatcher,
                max_iterations=1000000
            )

            while_analysis = analyze_while_loop(func)
            if while_analysis.is_parallelizable:
                transformed = while_transformer.transform_function(func, while_analysis)
                if transformed:
                    logger.info(f"Transformed while loop in {func.__name__}")
                    return transformed

        # Fall back to original transformation
        return original_create(self, func, analysis)

    # Monkey-patch the methods
    RuntimeLoopTransformer.analyze_function = analyze_function_with_while
    RuntimeLoopTransformer._create_transformed_function = create_transformed_with_while

    logger.debug("Added while loop support to RuntimeLoopTransformer")


# Auto-apply when imported
add_while_loop_support_to_transformer()