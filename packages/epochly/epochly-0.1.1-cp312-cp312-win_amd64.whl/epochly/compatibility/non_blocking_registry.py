"""
Non-Blocking Module Compatibility Registry

Implements state-of-the-art patterns for zero-latency module compatibility checking:
- Optimistic fast path (assume safe by default)
- Background async analysis
- Lock-free data structures
- Bloom filter for O(1) lookups
- Memory-mapped cache for zero-copy access

Author: Epochly Development Team
"""

import asyncio
import threading
import mmap
import os
import json
import logging
import hashlib
import time
from typing import Set, Dict, Any, Optional, Callable
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from datetime import datetime, timedelta, timezone
import struct

logger = logging.getLogger(__name__)


class BloomFilter:
    """
    Fast probabilistic data structure for O(1) membership testing.
    Used for quick filtering of known safe/unsafe modules.
    """
    
    def __init__(self, size: int = 1024 * 1024, num_hashes: int = 3):
        """Initialize bloom filter with size in bits"""
        self.size = size
        self.num_hashes = num_hashes
        self.bit_array = bytearray(size // 8)
        self.count = 0
    
    def _hash(self, item: str, seed: int) -> int:
        """Generate hash for item with seed"""
        h = hashlib.md5(f"{item}{seed}".encode()).digest()
        return int.from_bytes(h[:4], 'big') % self.size
    
    def add(self, item: str) -> None:
        """Add item to bloom filter"""
        for i in range(self.num_hashes):
            pos = self._hash(item, i)
            byte_idx = pos // 8
            bit_idx = pos % 8
            self.bit_array[byte_idx] |= (1 << bit_idx)
        self.count += 1
    
    def contains(self, item: str) -> bool:
        """Check if item might be in set (no false negatives)"""
        for i in range(self.num_hashes):
            pos = self._hash(item, i)
            byte_idx = pos // 8
            bit_idx = pos % 8
            if not (self.bit_array[byte_idx] & (1 << bit_idx)):
                return False
        return True
    
    def clear(self):
        """Clear the bloom filter"""
        self.bit_array = bytearray(self.size // 8)
        self.count = 0


class NonBlockingCompatibilityRegistry:
    """
    Non-blocking registry that never stalls execution.
    
    Key features:
    - Optimistic defaults (assume safe until proven otherwise)
    - Background analysis with fire-and-forget
    - Lock-free reads with copy-on-write updates
    - Bloom filters for fast path checking
    - Memory-mapped cache for zero-copy access
    """
    
    # Known unsafe modules (minimal bootstrap set)
    BOOTSTRAP_UNSAFE = {
        'numpy', 'pandas', 'scipy', 'tensorflow', 'torch',
        'matplotlib', 'cv2', 'PIL', 'skimage', 'sklearn'
    }
    
    # Known safe modules (common stdlib)
    BOOTSTRAP_SAFE = {
        'json', 'csv', 'math', 'random', 'datetime', 'collections',
        'itertools', 'functools', 'os', 'sys', 're', 'string'
    }
    
    def __init__(self, 
                 cache_dir: Optional[Path] = None,
                 enable_background_analysis: bool = True,
                 max_background_workers: int = 2):
        """
        Initialize non-blocking registry.
        
        Args:
            cache_dir: Directory for memory-mapped cache
            enable_background_analysis: Enable async module analysis
            max_background_workers: Max threads for background work
        """
        # Fast-path data structures (lock-free via copy-on-write)
        self._unsafe_bloom = BloomFilter()
        self._safe_bloom = BloomFilter()
        
        # Definitive sets (updated atomically)
        self._unsafe_set = set(self.BOOTSTRAP_UNSAFE)
        self._safe_set = set(self.BOOTSTRAP_SAFE)
        
        # Initialize bloom filters with bootstrap data
        for module in self.BOOTSTRAP_UNSAFE:
            self._unsafe_bloom.add(module)
        for module in self.BOOTSTRAP_SAFE:
            self._safe_bloom.add(module)
        
        # Background analysis queue
        self._analysis_queue = deque(maxlen=1000)
        self._analyzed_cache = {}  # Results cache
        
        # Background executor
        self.enable_background = enable_background_analysis
        if enable_background_analysis:
            self._executor = ThreadPoolExecutor(
                max_workers=max_background_workers,
                thread_name_prefix="CompatAnalyzer"
            )
            self._start_background_worker()
        
        # Memory-mapped cache
        self.cache_dir = cache_dir or self._get_default_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.mmap_file = self.cache_dir / "compat_cache.mmap"
        self._init_mmap_cache()
        
        # Stats for monitoring
        self._stats = {
            'fast_path_hits': 0,
            'slow_path_triggers': 0,
            'background_analyses': 0,
            'false_positives': 0
        }
        
        logger.info("Non-blocking compatibility registry initialized")
    
    def is_safe_for_subinterpreter(self, module_name: str) -> bool:
        """
        Fast, non-blocking safety check.
        
        NEVER BLOCKS - returns immediately with best guess.
        Triggers background analysis if needed.
        
        Args:
            module_name: Module to check
            
        Returns:
            True if module is safe (or assumed safe)
            False only if definitely known unsafe
        """
        # Fast path 1: Check definitive unsafe set
        if module_name in self._unsafe_set:
            self._stats['fast_path_hits'] += 1
            return False
        
        # Fast path 2: Check bloom filter for unsafe
        if self._unsafe_bloom.contains(module_name):
            # Might be unsafe, verify (still fast)
            if module_name in self._unsafe_set:
                self._stats['fast_path_hits'] += 1
                return False
            else:
                self._stats['false_positives'] += 1
        
        # Fast path 3: Check definitive safe set
        if module_name in self._safe_set:
            self._stats['fast_path_hits'] += 1
            return True
        
        # Fast path 4: Check bloom filter for safe
        if self._safe_bloom.contains(module_name):
            self._stats['fast_path_hits'] += 1
            return True
        
        # Unknown module - trigger background analysis
        if self.enable_background:
            self._trigger_background_analysis(module_name)
            self._stats['slow_path_triggers'] += 1
        
        # OPTIMISTIC DEFAULT: Assume safe until proven otherwise
        # This ensures we NEVER block execution
        return True
    
    def _trigger_background_analysis(self, module_name: str) -> None:
        """
        Queue module for background analysis (fire-and-forget).
        
        Args:
            module_name: Module to analyze
        """
        if module_name not in self._analyzed_cache:
            try:
                self._analysis_queue.append(module_name)
            except:
                # Queue full, skip (not critical)
                pass
    
    def _start_background_worker(self) -> None:
        """Start background worker thread for module analysis"""
        def worker():
            while True:
                try:
                    if self._analysis_queue:
                        module = self._analysis_queue.popleft()
                        self._executor.submit(self._analyze_module, module)
                    else:
                        threading.Event().wait(0.1)  # Brief sleep
                except Exception as e:
                    logger.debug(f"Background worker error: {e}")
        
        thread = threading.Thread(target=worker, daemon=True, name="CompatWorker")
        thread.start()
    
    def _analyze_module(self, module_name: str) -> None:
        """
        Analyze module in background (slow path).
        
        This runs async and updates the registry when complete.
        
        Args:
            module_name: Module to analyze
        """
        try:
            self._stats['background_analyses'] += 1
            
            # Quick heuristics first
            is_unsafe = False
            
            # Check if it's a known C extension pattern
            c_extension_patterns = [
                'numpy', 'scipy', 'pandas', 'cv2', 'torch',
                'tensorflow', 'sklearn', 'matplotlib'
            ]
            
            for pattern in c_extension_patterns:
                if pattern in module_name.lower():
                    is_unsafe = True
                    break
            
            # Try lightweight import check (if not obviously unsafe)
            if not is_unsafe:
                try:
                    # Check if module is already loaded
                    import sys
                    if module_name in sys.modules:
                        module = sys.modules[module_name]
                        # Check for C extension indicators
                        if hasattr(module, '__file__'):
                            file_path = module.__file__
                            if file_path and (file_path.endswith('.so') or 
                                            file_path.endswith('.pyd') or
                                            file_path.endswith('.dll')):
                                is_unsafe = True
                except:
                    pass
            
            # Update registry atomically
            if is_unsafe:
                self._mark_unsafe(module_name)
            else:
                self._mark_safe(module_name)
            
            # Cache result
            self._analyzed_cache[module_name] = not is_unsafe
            
        except Exception as e:
            logger.debug(f"Module analysis failed for {module_name}: {e}")
            # On error, don't update (keep optimistic)
    
    def _mark_unsafe(self, module_name: str) -> None:
        """
        Mark module as unsafe (atomic update).
        
        Args:
            module_name: Module to mark unsafe
        """
        # Copy-on-write for lock-free update
        new_unsafe = self._unsafe_set.copy()
        new_unsafe.add(module_name)
        self._unsafe_set = new_unsafe
        self._unsafe_bloom.add(module_name)
        
        # Remove from safe if present
        if module_name in self._safe_set:
            new_safe = self._safe_set.copy()
            new_safe.discard(module_name)
            self._safe_set = new_safe
        
        logger.debug(f"Module {module_name} marked as unsafe")
    
    def _mark_safe(self, module_name: str) -> None:
        """
        Mark module as safe (atomic update).
        
        Args:
            module_name: Module to mark safe
        """
        # Copy-on-write for lock-free update
        new_safe = self._safe_set.copy()
        new_safe.add(module_name)
        self._safe_set = new_safe
        self._safe_bloom.add(module_name)
        
        logger.debug(f"Module {module_name} marked as safe")
    
    def report_failure(self, module_name: str, error_info: Dict[str, Any]) -> None:
        """
        Report module failure (immediate update).
        
        This is called when a module actually fails at runtime.
        Updates are immediate to prevent further issues.
        
        Args:
            module_name: Failed module
            error_info: Error details
        """
        self._mark_unsafe(module_name)
        logger.warning(f"Module {module_name} failed and marked unsafe: {error_info}")
    
    def _init_mmap_cache(self) -> None:
        """Initialize memory-mapped cache for zero-copy access"""
        try:
            # Create or load memory-mapped file
            cache_size = 10 * 1024 * 1024  # 10MB
            
            if self.mmap_file.exists():
                # Load existing
                with open(self.mmap_file, 'r+b') as f:
                    self.mmap = mmap.mmap(f.fileno(), cache_size)
                    self._load_from_mmap()
            else:
                # Create new
                with open(self.mmap_file, 'wb') as f:
                    f.write(b'\0' * cache_size)
                with open(self.mmap_file, 'r+b') as f:
                    self.mmap = mmap.mmap(f.fileno(), cache_size)
                    self._save_to_mmap()
        except Exception as e:
            logger.debug(f"Memory-mapped cache init failed: {e}")
            self.mmap = None
    
    def _load_from_mmap(self) -> None:
        """Load data from memory-mapped cache"""
        try:
            if not self.mmap:
                return
            
            # Read header (first 8 bytes)
            self.mmap.seek(0)
            header = self.mmap.read(8)
            if header[:4] != b'ECMM':  # Epochly Compat Memory Map
                return
            
            data_len = struct.unpack('>I', header[4:8])[0]
            if data_len == 0 or data_len > len(self.mmap) - 8:
                return
            
            # Read JSON data
            data = self.mmap.read(data_len)
            cache_data = json.loads(data.decode('utf-8'))
            
            # Update sets atomically
            if 'unsafe' in cache_data:
                self._unsafe_set = set(cache_data['unsafe'])
                for module in cache_data['unsafe']:
                    self._unsafe_bloom.add(module)
            
            if 'safe' in cache_data:
                self._safe_set = set(cache_data['safe'])
                for module in cache_data['safe']:
                    self._safe_bloom.add(module)
            
            logger.debug(f"Loaded {len(self._unsafe_set)} unsafe and {len(self._safe_set)} safe modules from cache")
            
        except Exception as e:
            logger.debug(f"Failed to load from mmap cache: {e}")
    
    def _save_to_mmap(self) -> None:
        """Save data to memory-mapped cache"""
        try:
            if not self.mmap:
                return
            
            # Prepare data
            cache_data = {
                'unsafe': list(self._unsafe_set),
                'safe': list(self._safe_set),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            data = json.dumps(cache_data).encode('utf-8')
            data_len = len(data)
            
            if data_len + 8 > len(self.mmap):
                logger.warning("Cache data too large for mmap")
                return
            
            # Write header and data
            self.mmap.seek(0)
            self.mmap.write(b'ECMM')  # Magic bytes
            self.mmap.write(struct.pack('>I', data_len))
            self.mmap.write(data)
            self.mmap.flush()
            
        except Exception as e:
            logger.debug(f"Failed to save to mmap cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            **self._stats,
            'unsafe_count': len(self._unsafe_set),
            'safe_count': len(self._safe_set),
            'analyzed_count': len(self._analyzed_cache),
            'queue_size': len(self._analysis_queue)
        }
    
    def _get_default_cache_dir(self) -> Path:
        """Get default cache directory"""
        if os.name == 'nt':
            base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            return Path(base) / 'Epochly' / 'cache' / 'compat'
        else:
            base = os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
            return Path(base) / 'epochly' / 'compat'
    
    def shutdown(self) -> None:
        """Shutdown background workers and save state"""
        if self.enable_background:
            self._executor.shutdown(wait=False)
        
        if self.mmap:
            self._save_to_mmap()
            self.mmap.close()
    
    def add_to_allowlist(self, module_name: str, reason: str = "") -> None:
        """
        Add a module to the safe/allowlist.
        
        Args:
            module_name: Module to mark as safe
            reason: Optional reason for the addition
        """
        self._mark_safe(module_name)
        logger.debug(f"Added {module_name} to allowlist: {reason}")
    
    def add_to_denylist(self, module_name: str, reason: str = "") -> None:
        """
        Add a module to the unsafe/denylist.
        
        Args:
            module_name: Module to mark as unsafe
            reason: Optional reason for the addition
        """
        self._mark_unsafe(module_name)
        logger.debug(f"Added {module_name} to denylist: {reason}")
    
    def get_safe_modules(self) -> Set[str]:
        """
        Get set of known safe modules.
        
        Returns:
            Set of safe module names
        """
        return self._safe_set.copy()
    
    def get_unsafe_modules(self) -> Set[str]:
        """
        Get set of known unsafe modules.

        Returns:
            Set of unsafe module names
        """
        return self._unsafe_set.copy()

    def check_module(self, module_name: str, force: bool = False, force_recheck: bool = False) -> 'CompatibilityResult':
        """
        Check module compatibility (API compatibility with CompatibilityRegistry).

        Args:
            module_name: Module to check
            force: Ignored (for API compatibility)
            force_recheck: Ignored (for API compatibility)

        Returns:
            CompatibilityResult indicating safety
        """
        from .registry import CompatibilityResult, CompatibilityLevel

        is_safe = self.is_safe_for_subinterpreter(module_name)

        if is_safe:
            return CompatibilityResult(
                module_name=module_name,
                level=CompatibilityLevel.FULL,
                score=1.0,
                details={"source": "non_blocking_registry", "safe": True}
            )
        else:
            return CompatibilityResult(
                module_name=module_name,
                level=CompatibilityLevel.NONE,
                score=0.0,
                details={"source": "non_blocking_registry", "safe": False}
            )

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate compatibility report (API compatibility with CompatibilityRegistry).

        Returns:
            Dictionary with registry statistics
        """
        return {
            'timestamp': time.time(),
            'allowlist_count': len(self._safe_set),
            'denylist_count': len(self._unsafe_set),
            'greylist_count': 0,  # NonBlockingRegistry doesn't have greylist
            'safe_modules': len(self._safe_set),
            'unsafe_modules': len(self._unsafe_set),
            'analyzed_cache_size': len(self._analyzed_cache),
            'stats': self.get_stats(),
            'registry_type': 'NonBlockingCompatibilityRegistry'
        }

    def update_from_cloud(self, data: Dict[str, Any]) -> None:
        """
        Update registry from cloud data.
        
        Args:
            data: Dictionary with 'allowlist' and 'denylist' keys
        """
        if 'allowlist' in data:
            for module_name in data['allowlist']:
                self._mark_safe(module_name)
        
        if 'denylist' in data:
            for module_name in data['denylist']:
                self._mark_unsafe(module_name)
        
        logger.debug(f"Updated from cloud: {len(data.get('allowlist', []))} safe, {len(data.get('denylist', []))} unsafe modules")


# Global non-blocking registry instance
_global_nb_registry = None
_registry_lock = threading.Lock()


def get_non_blocking_registry() -> NonBlockingCompatibilityRegistry:
    """
    Get global non-blocking registry instance (singleton).
    
    Returns:
        Global registry instance
    """
    global _global_nb_registry
    
    if _global_nb_registry is None:
        with _registry_lock:
            if _global_nb_registry is None:
                _global_nb_registry = NonBlockingCompatibilityRegistry()
    
    return _global_nb_registry