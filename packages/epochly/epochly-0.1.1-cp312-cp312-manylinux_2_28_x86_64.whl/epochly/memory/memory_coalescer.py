"""
Epochly Memory Foundation - Memory Coalescer Implementation

This module implements advanced memory coalescing logic for fragmentation
reduction in the hybrid O(1)/O(log n) memory allocation architecture.

Author: Epochly Memory Foundation Team
"""

import threading
import time
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

from .atomic_primitives import AtomicCounter
from .circuit_breaker import MemoryCircuitBreakerManager


class CoalescingStrategy(Enum):
    """Memory coalescing strategies."""
    IMMEDIATE = "immediate"        # Coalesce immediately on free
    DEFERRED = "deferred"         # Coalesce during allocation pressure
    LAZY = "lazy"                 # Coalesce during idle periods
    ADAPTIVE = "adaptive"         # Adapt strategy based on workload


@dataclass
class MemoryBlock:
    """Represents a memory block for coalescing operations."""
    address: int
    size: int
    is_free: bool = True
    timestamp: float = 0.0
    
    @property
    def end_address(self) -> int:
        """Get the end address of the block."""
        return self.address + self.size
    
    def is_adjacent_to(self, other: 'MemoryBlock') -> bool:
        """Check if this block is adjacent to another block."""
        return (self.end_address == other.address or 
                other.end_address == self.address)
    
    def can_coalesce_with(self, other: 'MemoryBlock') -> bool:
        """Check if this block can be coalesced with another."""
        return (self.is_free and other.is_free and 
                self.is_adjacent_to(other))


@dataclass
class CoalescingStats:
    """Statistics for memory coalescing operations."""
    total_coalesces: int = 0
    bytes_coalesced: int = 0
    fragmentation_reduced: float = 0.0
    coalescing_time_ms: float = 0.0
    blocks_merged: int = 0
    largest_coalesced_block: int = 0


class MemoryCoalescer:
    """
    Advanced memory coalescing implementation for fragmentation reduction.
    
    Provides multiple coalescing strategies and adaptive behavior based on
    memory pressure and allocation patterns.
    """
    
    def __init__(self, strategy: CoalescingStrategy = CoalescingStrategy.ADAPTIVE):
        """
        Initialize memory coalescer.
        
        Args:
            strategy: Coalescing strategy to use
        """
        self.strategy = strategy
        
        # Memory block tracking
        self.free_blocks: Dict[int, MemoryBlock] = {}  # address -> block
        self.size_index: Dict[int, Set[int]] = defaultdict(set)  # size -> addresses
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Statistics and monitoring
        self.stats = CoalescingStats()
        self.total_operations = AtomicCounter()
        self.successful_coalesces = AtomicCounter()
        self.failed_coalesces = AtomicCounter()
        
        # Circuit breaker for preventing infinite coalescing loops
        self.circuit_breaker = MemoryCircuitBreakerManager()
        
        # Adaptive strategy parameters
        self.fragmentation_threshold = 0.3  # 30% fragmentation triggers aggressive coalescing
        self.pressure_threshold = 0.8       # 80% memory usage triggers deferred coalescing
        self.idle_time_threshold = 0.1      # 100ms idle time triggers lazy coalescing
        
        # Performance tracking
        self.last_coalesce_time = 0.0
        self.coalescing_frequency = AtomicCounter()
        
        # Background coalescing for lazy strategy
        self.background_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        
        if strategy == CoalescingStrategy.LAZY:
            self._start_background_coalescing()
    
    def add_free_block(self, block: MemoryBlock) -> None:
        """
        Add a free block and potentially coalesce with adjacent blocks.
        
        Args:
            block: Memory block to add
        """
        self.total_operations.increment()
        
        with self.lock:
            # Add block to tracking structures
            self.free_blocks[block.address] = block
            self.size_index[block.size].add(block.address)
            
            # Apply coalescing strategy
            if self.strategy == CoalescingStrategy.IMMEDIATE:
                self._immediate_coalesce(block)
            elif self.strategy == CoalescingStrategy.DEFERRED:
                self._check_deferred_coalesce()
            elif self.strategy == CoalescingStrategy.ADAPTIVE:
                self._adaptive_coalesce(block)
            # LAZY strategy handled by background thread
    
    def remove_block(self, address: int) -> Optional[MemoryBlock]:
        """
        Remove a block from coalescing tracking.
        
        Args:
            address: Address of block to remove
            
        Returns:
            Removed block or None if not found
        """
        with self.lock:
            block = self.free_blocks.pop(address, None)
            if block:
                self.size_index[block.size].discard(address)
                if not self.size_index[block.size]:
                    del self.size_index[block.size]
            return block
    
    def find_best_fit(self, size: int) -> Optional[MemoryBlock]:
        """
        Find the best-fit block for the requested size.
        
        Args:
            size: Requested size
            
        Returns:
            Best-fit block or None if not found
        """
        with self.lock:
            best_block = None
            best_size = float('inf')
            
            # Look for exact size match first
            if size in self.size_index and self.size_index[size]:
                address = next(iter(self.size_index[size]))
                return self.free_blocks[address]
            
            # Find smallest block that fits
            for block_size, addresses in self.size_index.items():
                if block_size >= size and block_size < best_size and addresses:
                    address = next(iter(addresses))
                    best_block = self.free_blocks[address]
                    best_size = block_size
            
            return best_block
    
    def _immediate_coalesce(self, block: MemoryBlock) -> None:
        """
        Immediately coalesce the block with adjacent free blocks.
        
        Args:
            block: Block to coalesce
        """
        try:
            self.circuit_breaker.get_breaker("coalescing").call(
                self._perform_coalescing, block
            )
        except Exception:
            self.failed_coalesces.increment()
    
    def _perform_coalescing(self, block: MemoryBlock) -> None:
        """
        Perform the actual coalescing operation.
        
        Args:
            block: Block to coalesce
        """
        start_time = time.perf_counter()
        
        # Find adjacent blocks
        adjacent_blocks = self._find_adjacent_blocks(block)
        
        if not adjacent_blocks:
            return
        
        # Merge blocks
        merged_block = self._merge_blocks([block] + adjacent_blocks)
        
        # Update tracking structures
        for adj_block in adjacent_blocks:
            self._remove_block_from_tracking(adj_block)
        
        self._remove_block_from_tracking(block)
        self._add_block_to_tracking(merged_block)
        
        # Update statistics
        elapsed = (time.perf_counter() - start_time) * 1000
        self.stats.total_coalesces += 1
        self.stats.bytes_coalesced += sum(b.size for b in adjacent_blocks)
        self.stats.coalescing_time_ms += elapsed
        self.stats.blocks_merged += len(adjacent_blocks) + 1
        self.stats.largest_coalesced_block = max(
            self.stats.largest_coalesced_block, merged_block.size
        )
        
        self.successful_coalesces.increment()
        self.last_coalesce_time = time.perf_counter()
    
    def _find_adjacent_blocks(self, block: MemoryBlock) -> List[MemoryBlock]:
        """
        Find all adjacent free blocks.
        
        Args:
            block: Block to find adjacent blocks for
            
        Returns:
            List of adjacent free blocks
        """
        adjacent = []
        
        # Check all free blocks for adjacency
        for addr, free_block in self.free_blocks.items():
            if addr != block.address and block.can_coalesce_with(free_block):
                adjacent.append(free_block)
        
        return adjacent
    
    def _merge_blocks(self, blocks: List[MemoryBlock]) -> MemoryBlock:
        """
        Merge multiple blocks into a single block.
        
        Args:
            blocks: Blocks to merge
            
        Returns:
            Merged block
        """
        if not blocks:
            raise ValueError("Cannot merge empty block list")
        
        # Sort blocks by address
        sorted_blocks = sorted(blocks, key=lambda b: b.address)
        
        # Calculate merged block properties
        start_address = sorted_blocks[0].address
        total_size = sum(block.size for block in sorted_blocks)
        
        return MemoryBlock(
            address=start_address,
            size=total_size,
            is_free=True,
            timestamp=time.perf_counter()
        )
    
    def _remove_block_from_tracking(self, block: MemoryBlock) -> None:
        """Remove block from tracking structures."""
        self.free_blocks.pop(block.address, None)
        self.size_index[block.size].discard(block.address)
        if not self.size_index[block.size]:
            del self.size_index[block.size]
    
    def _add_block_to_tracking(self, block: MemoryBlock) -> None:
        """Add block to tracking structures."""
        self.free_blocks[block.address] = block
        self.size_index[block.size].add(block.address)
    
    def _check_deferred_coalesce(self) -> None:
        """Check if deferred coalescing should be triggered."""
        memory_pressure = self._calculate_memory_pressure()
        fragmentation = self._calculate_fragmentation()
        
        if (memory_pressure > self.pressure_threshold or 
            fragmentation > self.fragmentation_threshold):
            self._perform_bulk_coalescing()
    
    def _adaptive_coalesce(self, block: MemoryBlock) -> None:
        """
        Adaptive coalescing based on current conditions.
        
        Args:
            block: Block to potentially coalesce
        """
        fragmentation = self._calculate_fragmentation()
        memory_pressure = self._calculate_memory_pressure()
        
        # High fragmentation or pressure triggers immediate coalescing
        if fragmentation > self.fragmentation_threshold:
            self._immediate_coalesce(block)
        elif memory_pressure > self.pressure_threshold:
            self._immediate_coalesce(block)
        else:
            # Low pressure - defer coalescing
            pass
    
    def _calculate_fragmentation(self) -> float:
        """Calculate current memory fragmentation ratio."""
        if not self.free_blocks:
            return 0.0
        
        total_free_memory = sum(block.size for block in self.free_blocks.values())
        num_free_blocks = len(self.free_blocks)
        
        if num_free_blocks <= 1:
            return 0.0
        
        # Simple fragmentation metric: more blocks = more fragmentation
        return min(1.0, (num_free_blocks - 1) / max(1, total_free_memory // 4096))
    
    def _calculate_memory_pressure(self) -> float:
        """Calculate current memory pressure (0.0 to 1.0)."""
        # Simplified pressure calculation based on free block count
        # In real implementation, this would consider total memory usage
        if len(self.free_blocks) < 10:
            return 0.9  # High pressure when few free blocks
        elif len(self.free_blocks) < 50:
            return 0.5  # Medium pressure
        else:
            return 0.1  # Low pressure
    
    def _perform_bulk_coalescing(self) -> None:
        """Perform bulk coalescing of all possible adjacent blocks."""
        with self.lock:
            blocks_to_process = list(self.free_blocks.values())
            
            for block in blocks_to_process:
                if block.address in self.free_blocks:  # Still exists
                    self._immediate_coalesce(block)
    
    def _start_background_coalescing(self) -> None:
        """Start background thread for lazy coalescing."""
        def background_worker():
            while not self.shutdown_event.wait(self.idle_time_threshold):
                current_time = time.perf_counter()
                if (current_time - self.last_coalesce_time) > self.idle_time_threshold:
                    self._perform_bulk_coalescing()
        
        self.background_thread = threading.Thread(target=background_worker, daemon=True)
        self.background_thread.start()
    
    def shutdown(self) -> None:
        """Shutdown the coalescer and cleanup resources."""
        self.shutdown_event.set()
        if self.background_thread:
            self.background_thread.join(timeout=1.0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get coalescing statistics."""
        with self.lock:
            return {
                'strategy': self.strategy.value,
                'total_operations': self.total_operations.load(),
                'successful_coalesces': self.successful_coalesces.load(),
                'failed_coalesces': self.failed_coalesces.load(),
                'total_coalesces': self.stats.total_coalesces,
                'bytes_coalesced': self.stats.bytes_coalesced,
                'fragmentation_reduced': self.stats.fragmentation_reduced,
                'coalescing_time_ms': self.stats.coalescing_time_ms,
                'blocks_merged': self.stats.blocks_merged,
                'largest_coalesced_block': self.stats.largest_coalesced_block,
                'current_fragmentation': self._calculate_fragmentation(),
                'current_memory_pressure': self._calculate_memory_pressure(),
                'free_blocks_count': len(self.free_blocks),
                'unique_sizes_count': len(self.size_index)
            }
    
    def reset_statistics(self) -> None:
        """Reset all statistics."""
        with self.lock:
            self.stats = CoalescingStats()
            self.total_operations.store(0)
            self.successful_coalesces.store(0)
            self.failed_coalesces.store(0)
            self.coalescing_frequency.store(0)