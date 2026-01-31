"""
Block Coalescer for Memory Pool

This module provides block coalescing functionality to reduce fragmentation
in the WorkloadAwareMemoryPool by merging adjacent free blocks.

Author: Epochly Memory Foundation Team
"""

import time
import threading
from typing import List, Optional, Set, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import uuid

from .memory_block import MemoryBlock


class CoalescingEvent:
    """Event emitted when blocks are coalesced."""
    
    def __init__(self, timestamp: float, blocks_merged: int, size_recovered: int):
        self.timestamp = timestamp
        self.blocks_merged = blocks_merged
        self.size_recovered = size_recovered


class BlockCoalescer:
    """
    Handles coalescing of adjacent free blocks in memory pool.
    
    This class provides methods to find adjacent blocks, merge them,
    and perform coalescing operations on lists of free blocks.
    """
    
    def __init__(self):
        """Initialize the block coalescer."""
        self._lock = threading.RLock()
    
    def find_adjacent_blocks(self, block: MemoryBlock, blocks: List[MemoryBlock]) -> List[MemoryBlock]:
        """
        Find all blocks adjacent to the given block.
        
        Args:
            block: The block to find adjacent blocks for
            blocks: List of all blocks to search through
            
        Returns:
            List of blocks that are adjacent to the given block
        """
        adjacent = []
        
        for other in blocks:
            # Skip the same block (by reference)
            if other is block:
                continue
                
            # Use the built-in is_adjacent_to method
            if block.is_adjacent_to(other):
                adjacent.append(other)
        
        return adjacent
    
    def merge_blocks(self, block1: MemoryBlock, block2: MemoryBlock) -> MemoryBlock:
        """
        Merge two adjacent blocks into a single block.
        
        Args:
            block1: First block
            block2: Second block
            
        Returns:
            New merged block
        """
        # Determine which block comes first
        if block1.offset < block2.offset:
            first, second = block1, block2
        else:
            first, second = block2, block1
        
        # Create merged block
        merged = MemoryBlock(
            offset=first.offset,
            size=first.size + second.size,
            free=True
        )
        
        return merged
    
    def merge_blocks_list(self, blocks: List[MemoryBlock]) -> MemoryBlock:
        """
        Merge a list of adjacent blocks into a single block.
        
        Args:
            blocks: List of blocks to merge (assumed to be adjacent)
            
        Returns:
            Single merged block
        """
        if not blocks:
            raise ValueError("Cannot merge empty list of blocks")
        
        if len(blocks) == 1:
            return blocks[0]
        
        # Sort blocks by offset
        sorted_blocks = sorted(blocks, key=lambda b: b.offset)
        
        # Calculate total size and starting offset
        total_size = sum(b.size for b in sorted_blocks)
        start_offset = sorted_blocks[0].offset
        
        # Create merged block
        merged = MemoryBlock(
            offset=start_offset,
            size=total_size,
            free=True
        )
        
        return merged
    
    def coalesce(self, free_blocks: List[MemoryBlock]) -> List[MemoryBlock]:
        """
        Coalesce adjacent free blocks in the given list.
        
        Args:
            free_blocks: List of free blocks to coalesce
            
        Returns:
            List of coalesced blocks
        """
        if len(free_blocks) <= 1:
            return free_blocks
        
        with self._lock:
            # Sort blocks by offset for efficient adjacency checking
            sorted_blocks = sorted(free_blocks, key=lambda b: b.offset)
            coalesced = []
            
            i = 0
            while i < len(sorted_blocks):
                current = sorted_blocks[i]
                adjacent_group = [current]
                
                # Find all consecutive adjacent blocks
                j = i + 1
                while j < len(sorted_blocks):
                    if sorted_blocks[j].offset == current.offset + current.size:
                        adjacent_group.append(sorted_blocks[j])
                        current = sorted_blocks[j]
                        j += 1
                    else:
                        break
                
                # Merge adjacent blocks or keep single block
                if len(adjacent_group) > 1:
                    merged = self.merge_blocks_list(adjacent_group)
                    coalesced.append(merged)
                else:
                    coalesced.append(adjacent_group[0])
                
                i = j
            
            return coalesced


class CoalescingPolicy(ABC):
    """Abstract base class for coalescing policies."""
    
    @abstractmethod
    def should_coalesce(self, **kwargs) -> bool:
        """
        Determine whether coalescing should be performed.
        
        Args:
            **kwargs: Policy-specific parameters
            
        Returns:
            True if coalescing should occur, False otherwise
        """
        pass
    
    def reset(self):
        """Reset any internal state of the policy."""
        pass


class ImmediateCoalescingPolicy(CoalescingPolicy):
    """Policy that triggers coalescing immediately on every deallocation."""
    
    def should_coalesce(self, **kwargs) -> bool:
        """Always coalesce immediately."""
        return True


class DeferredCoalescingPolicy(CoalescingPolicy):
    """Policy that defers coalescing until a time threshold is reached."""
    
    def __init__(self, time_threshold: float = 5.0):
        """
        Initialize deferred policy.
        
        Args:
            time_threshold: Time in seconds between coalescing operations
        """
        self.time_threshold = time_threshold
        self.last_coalesce_time = time.time()
        self._lock = threading.Lock()
    
    def should_coalesce(self, **kwargs) -> bool:
        """Check if enough time has passed since last coalescing."""
        with self._lock:
            current_time = time.time()
            if current_time - self.last_coalesce_time >= self.time_threshold:
                return True
            return False
    
    def reset(self):
        """Reset the timer."""
        with self._lock:
            self.last_coalesce_time = time.time()


class ThresholdCoalescingPolicy(CoalescingPolicy):
    """Policy that triggers based on fragmentation or free block count thresholds."""
    
    def __init__(self, fragmentation_threshold: float = 0.3, 
                 free_blocks_threshold: int = 10):
        """
        Initialize threshold policy.
        
        Args:
            fragmentation_threshold: Fragmentation ratio threshold (0-1)
            free_blocks_threshold: Number of free blocks threshold
        """
        self.fragmentation_threshold = fragmentation_threshold
        self.free_blocks_threshold = free_blocks_threshold
    
    def should_coalesce(self, fragmentation_ratio: float = 0.0, 
                       free_blocks_count: int = 0, **kwargs) -> bool:
        """
        Check if thresholds are exceeded.
        
        Args:
            fragmentation_ratio: Current fragmentation ratio
            free_blocks_count: Current number of free blocks
            
        Returns:
            True if any threshold is exceeded
        """
        return (fragmentation_ratio > self.fragmentation_threshold or
                free_blocks_count > self.free_blocks_threshold)


class AdaptiveCoalescingPolicy(CoalescingPolicy):
    """
    Adaptive policy that learns from workload patterns.
    
    This policy adjusts its behavior based on allocation/deallocation rates
    and feedback from coalescing operations.
    """
    
    def __init__(self):
        """Initialize adaptive policy."""
        self.base_threshold = 0.3
        self.adjustment_factor = 1.0
        self.history = []
        self.max_history = 100
        self._lock = threading.Lock()
    
    def should_coalesce(self, fragmentation_ratio: float = 0.0,
                       allocation_rate: float = 0.0,
                       deallocation_rate: float = 0.0, **kwargs) -> bool:
        """
        Determine if coalescing should occur based on adaptive logic.
        
        Args:
            fragmentation_ratio: Current fragmentation ratio
            allocation_rate: Recent allocation rate (allocs/sec)
            deallocation_rate: Recent deallocation rate (deallocs/sec)
            
        Returns:
            True if coalescing should occur
        """
        with self._lock:
            # High allocation rate suggests deferring coalescing
            if allocation_rate > 50.0:  # More than 50 allocs/sec
                return False
            
            # High deallocation rate with high fragmentation suggests coalescing
            if deallocation_rate > 30.0 and fragmentation_ratio > 0.4:
                return True
            
            # Use adjusted threshold
            effective_threshold = self.base_threshold * self.adjustment_factor
            return fragmentation_ratio > effective_threshold
    
    def update_feedback(self, coalescing_benefit: float, coalescing_cost: float):
        """
        Update policy based on feedback from coalescing operations.
        
        Args:
            coalescing_benefit: Benefit metric (0-1, e.g., fragmentation reduction)
            coalescing_cost: Cost metric (0-1, e.g., time spent)
        """
        with self._lock:
            # Calculate net benefit
            net_benefit = coalescing_benefit - coalescing_cost
            
            # Add to history
            self.history.append(net_benefit)
            if len(self.history) > self.max_history:
                self.history.pop(0)
            
            # Adjust threshold based on average net benefit
            if len(self.history) >= 10:
                avg_benefit = sum(self.history) / len(self.history)
                
                if avg_benefit > 0.5:
                    # Very beneficial - be more aggressive
                    self.adjustment_factor = max(0.5, self.adjustment_factor * 0.9)
                elif avg_benefit < 0.1:
                    # Not beneficial - be more conservative
                    self.adjustment_factor = min(2.0, self.adjustment_factor * 1.1)
    
    def reset(self):
        """Reset adaptive state."""
        with self._lock:
            self.adjustment_factor = 1.0
            self.history.clear()