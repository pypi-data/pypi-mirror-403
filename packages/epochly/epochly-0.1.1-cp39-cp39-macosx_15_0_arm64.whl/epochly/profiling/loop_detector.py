"""
Loop Detector - Identifies loops in Python code for optimization

Uses bytecode analysis and runtime tracking to detect loops that would
benefit from JIT compilation and parallel execution.

Author: Epochly Development Team
Date: November 17, 2025
"""

import dis
import sys
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LoopStatistics:
    """
    Statistics for a detected loop.

    Attributes:
        code_object: Code object containing the loop
        loop_start_offset: Bytecode offset where loop starts
        loop_end_offset: Bytecode offset where loop ends
        iteration_count: Number of times loop executed
        total_cpu_time: Total CPU time spent in loop (seconds)
        avg_iteration_time: Average time per iteration (seconds)
        is_hot: Whether loop exceeds threshold
    """
    code_object: object  # Code object
    loop_start_offset: int
    loop_end_offset: int
    iteration_count: int = 0
    total_cpu_time: float = 0.0
    avg_iteration_time: float = 0.0
    is_hot: bool = False
    optimization_applied: bool = False  # Whether optimization has been applied


class LoopDetector:
    """
    Detects loops in Python code using bytecode analysis.

    Identifies loop constructs (for/while) and tracks their execution
    characteristics for optimization decisions.
    """

    def __init__(self, cpu_threshold_ms: float = 10.0):
        """
        Initialize loop detector.

        Args:
            cpu_threshold_ms: CPU time threshold for hot loop classification
        """
        self.cpu_threshold_ms = cpu_threshold_ms
        self._loop_cache: Dict[int, List[LoopStatistics]] = {}  # code_id -> [loops]
        self._analyzed_code: Set[int] = set()

        logger.debug(f"LoopDetector initialized (threshold: {cpu_threshold_ms}ms)")

    def find_loops_in_code(self, code_object) -> List[LoopStatistics]:
        """
        Find all loops in a code object using bytecode analysis.

        Args:
            code_object: Code object to analyze

        Returns:
            List of LoopStatistics for detected loops
        """
        code_id = id(code_object)

        # Check cache
        if code_id in self._loop_cache:
            return self._loop_cache[code_id]

        # Analyze bytecode to find loop constructs
        loops = []

        try:
            instructions = list(dis.get_instructions(code_object))

            # Look for loop patterns in bytecode
            # Python loops typically use FOR_ITER (for loops) or JUMP_BACKWARD (while loops)
            for i, instr in enumerate(instructions):
                if instr.opname in ('FOR_ITER', 'JUMP_BACKWARD', 'JUMP_IF_FALSE_OR_POP'):
                    # This might be a loop
                    loop_stat = self._analyze_loop_pattern(instructions, i)
                    if loop_stat:
                        loops.append(loop_stat)

            # Cache results
            self._loop_cache[code_id] = loops
            self._analyzed_code.add(code_id)

            if loops:
                logger.debug(f"Found {len(loops)} loops in {code_object.co_name}")

        except Exception as e:
            logger.debug(f"Failed to analyze code for loops: {e}")

        return loops

    def _analyze_loop_pattern(self, instructions: List, index: int) -> Optional[LoopStatistics]:
        """
        Analyze bytecode pattern to identify loop bounds.

        Args:
            instructions: List of bytecode instructions
            index: Index of potential loop instruction

        Returns:
            LoopStatistics if valid loop detected, None otherwise
        """
        instr = instructions[index]

        if instr.opname == 'FOR_ITER':
            # For loop pattern
            loop_start = instr.offset
            # FOR_ITER jumps to end of loop on exhaustion
            loop_end = instr.argval if instr.argval else loop_start + 100

            return LoopStatistics(
                code_object=None,  # Will be set by caller
                loop_start_offset=loop_start,
                loop_end_offset=loop_end
            )

        elif instr.opname == 'JUMP_BACKWARD':
            # While loop or for loop (Python 3.11+ uses JUMP_BACKWARD)
            loop_end = instr.offset
            # Jump target is the loop start
            loop_start = instr.argval if instr.argval else loop_end - 100

            return LoopStatistics(
                code_object=None,
                loop_start_offset=loop_start,
                loop_end_offset=loop_end
            )

        return None

    def update_loop_timing(self, loop_stat: LoopStatistics, cpu_time: float, iterations: int = 1):
        """
        Update loop timing statistics.

        Args:
            loop_stat: Loop statistics object to update
            cpu_time: CPU time for this execution (seconds)
            iterations: Number of iterations in this execution
        """
        loop_stat.iteration_count += iterations
        loop_stat.total_cpu_time += cpu_time
        loop_stat.avg_iteration_time = loop_stat.total_cpu_time / max(1, loop_stat.iteration_count)

        # Check if loop is hot
        cpu_time_ms = cpu_time * 1000
        if cpu_time_ms >= self.cpu_threshold_ms:
            loop_stat.is_hot = True

    def should_optimize_loop(self, loop_stat: LoopStatistics) -> bool:
        """
        Determine if loop should be optimized.

        Args:
            loop_stat: Loop statistics

        Returns:
            True if loop should be optimized
        """
        # Must be hot
        if not loop_stat.is_hot:
            return False

        # Must not already be optimized
        if loop_stat.optimization_applied:
            return False

        # Must have enough iterations to benefit from parallelization
        if loop_stat.iteration_count < 100:
            return False  # Too few iterations

        return True
