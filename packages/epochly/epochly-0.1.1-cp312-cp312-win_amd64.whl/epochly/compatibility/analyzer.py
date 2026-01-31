"""
Module Analysis for Compatibility Detection

Analyzes Python modules to determine compatibility with Epochly features,
particularly sub-interpreters and other optimization techniques.

Author: Epochly Development Team
"""

import ast
import sys
import os
import importlib
import importlib.util
import importlib.machinery
import inspect
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
import sysconfig

logger = logging.getLogger(__name__)


class _Constants:
    """Namespace for analyzer-level constants."""

    PROBLEMATIC_MODULES: Set[str] = {
        'multiprocessing', 'concurrent.futures', 'threading',
        'ctypes', 'cffi', 'cython',
        'tensorflow', 'torch', 'numpy', 'scipy',
        'tkinter', 'PyQt5', 'PyQt6', 'pygame'
    }


class ModuleAnalyzer:
    """
    Analyzes Python modules for compatibility features.
    
    Checks for:
    - C extensions
    - Global state usage
    - Thread safety
    - Sub-interpreter compatibility
    """
    
    def __init__(self):
        """Initialize the module analyzer"""
        self.extension_detector = ExtensionDetector()
        self._analysis_cache = {}
        # Cache of parsed import graphs keyed by file path. Each entry stores a
        # tuple of (mtime, size, problematic_imports) so we can avoid re-parsing
        # large modules when they have not changed.
        # Thread-safe with RLock, LRU eviction at 1000 entries
        from collections import OrderedDict
        import threading
        self._import_cache: OrderedDict[str, Tuple[float, int, Tuple[str, ...]]] = OrderedDict()
        self._cache_lock = threading.RLock()
        self._max_cache_size = 1000
    
    def analyze(self, module_name: str, force: bool = False) -> Dict[str, Any]:
        """
        Analyze a module for compatibility features.
        
        Args:
            module_name: Name of module to analyze
            force: Force re-analysis even if cached
            
        Returns:
            Dictionary with analysis results
        """
        if not force and module_name in self._analysis_cache:
            return self._analysis_cache[module_name]
        
        analysis = {
            'module_name': module_name,
            'has_c_extension': False,
            'uses_global_state': False,
            'is_thread_safe': True,
            'is_builtin': False,
            'is_package': False,
            'problematic_imports': [],
            'warnings': [],
            'c_modules': [],
            'pure_python': True,
            'analysis': {}
        }
        
        try:
            # Try to import module first (works with mocked modules)
            module = None
            try:
                module = importlib.import_module(module_name)
                
                # Check if module file indicates C extension
                if hasattr(module, '__file__') and module.__file__:
                    ext = os.path.splitext(module.__file__)[1]
                    if ext in ['.so', '.pyd', '.dll']:
                        analysis['has_c_extension'] = True
                        analysis['pure_python'] = False
                        analysis['c_modules'] = [module_name]
            except ImportError as e:
                # Module couldn't be imported - mark as error
                analysis['error'] = True
                analysis['error_message'] = f'Import failed: {str(e)}'
            
            # Check if it's a builtin module
            if module_name in sys.builtin_module_names:
                analysis['is_builtin'] = True
            
            # Check if module can be found via spec (for non-mocked modules)
            if module is None:
                spec = importlib.util.find_spec(module_name)
                if spec is None:
                    analysis['error'] = True
                    analysis['error_message'] = f'Import failed: Module {module_name} not found'
                    # Cache error results too to avoid repeated lookups
                    self._analysis_cache[module_name] = analysis
                    return analysis
            
            # Check for C extensions using detector if not already found
            if not analysis['has_c_extension']:
                c_ext_info = self.extension_detector.analyze_module(module_name)
                analysis['has_c_extension'] = c_ext_info['has_c_extension']
                if 'c_modules' not in analysis or not analysis['c_modules']:
                    analysis['c_modules'] = c_ext_info['c_modules']
                analysis['pure_python'] = c_ext_info['pure_python']
            
            # Continue inspection if module was imported
            if module:
                
                # Check if it's a package
                if hasattr(module, '__path__'):
                    analysis['is_package'] = True
                
                # Check for problematic patterns
                problems = self._check_problematic_patterns(module)
                analysis.update(problems)
                
                # Check dependencies
                deps = self._analyze_dependencies(module)
                analysis['dependencies'] = deps
            
            # Cache the analysis
            self._analysis_cache[module_name] = analysis
            
        except Exception as e:
            logger.debug(f"Error analyzing module {module_name}: {e}")
            analysis['error'] = str(e)
        
        return analysis

    def quick_check(self, module_name: str) -> bool:
        """
        Quick safety check for module (uses cached analysis).

        Args:
            module_name: Name of module to check

        Returns:
            bool: True if module is likely safe for sub-interpreters

        Note: This is a fast check using cached data. For detailed analysis,
        use analyze() method.
        """
        # Use full analyze() which leverages cache
        result = self.analyze(module_name)

        # Simple heuristic: safe if no C extensions and no errors
        has_c_ext = result.get('has_c_extension', False)
        has_error = result.get('error', False)
        uses_global_state = result.get('uses_global_state', False)

        # Safe if: no C extension, no errors, no problematic global state
        is_safe = not has_c_ext and not has_error and not uses_global_state

        return is_safe

    def _check_problematic_patterns(self, module) -> Dict[str, Any]:
        """Check for problematic patterns in module"""
        results = {
            'uses_global_state': False,
            'problematic_imports': [],
            'warnings': [],
            'analysis': {
                'has_mutable_globals': False,
                'uses_threading': False
            }
        }
        
        # Check for global variables (mutable module-level state)
        for name, obj in inspect.getmembers(module):
            if not name.startswith('_'):
                # Check if it's a mutable global
                if not callable(obj) and not inspect.ismodule(obj):
                    if not isinstance(obj, (str, int, float, bool, type(None))):
                        results['uses_global_state'] = True
                        results['analysis']['has_mutable_globals'] = True
                        results['warnings'].append(f"Module has mutable global: {name}")
                
                # Check for threading-related attributes
                if 'lock' in name.lower() or 'thread' in name.lower():
                    results['analysis']['uses_threading'] = True
        
        # Check imports
        if hasattr(module, '__file__') and module.__file__:
            problematic = self._check_imports(module.__file__)
            results['problematic_imports'] = problematic
            # Check if threading is imported
            if 'threading' in problematic or 'thread' in problematic:
                results['analysis']['uses_threading'] = True
        
        return results
    
    def _check_imports(self, file_path: str) -> List[str]:
        """
        Check imports in a Python file with thread-safe caching.

        Uses mtime/size-based cache with LRU eviction to avoid re-parsing
        unchanged files. Cache entries invalidated automatically when
        file is modified.

        Thread safety: Protected by RLock for concurrent access.

        Args:
            file_path: Path to Python file

        Returns:
            List of problematic import names
        """
        problematic = []

        # Resolve path to prevent cache key confusion
        path = Path(file_path).resolve()
        file_path_str = str(path)

        # Check cache first (thread-safe)
        with self._cache_lock:
            cache_entry = self._import_cache.get(file_path_str)

        try:
            stat = path.stat()
        except OSError as exc:
            logger.debug(f"Failed to stat {file_path_str}: {exc}")
            return []

        # Cache hit?
        if cache_entry and cache_entry[0] == stat.st_mtime and cache_entry[1] == stat.st_size:
            return list(cache_entry[2])

        # Cache miss - parse file
        try:
            source = path.read_text(encoding='utf-8')
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if self._is_problematic_import(alias.name):
                            problematic.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and self._is_problematic_import(node.module):
                        problematic.append(node.module)

        except Exception as e:
            logger.debug(f"Failed to parse imports from {file_path_str}: {e}")
            return []

        # Verify file unchanged during parsing (prevent race condition)
        try:
            verify_stat = path.stat()
            if verify_stat.st_mtime == stat.st_mtime and verify_stat.st_size == stat.st_size:
                # Cache result with LRU eviction
                with self._cache_lock:
                    # Evict oldest if at limit
                    if len(self._import_cache) >= self._max_cache_size:
                        self._import_cache.popitem(last=False)

                    self._import_cache[file_path_str] = (
                        stat.st_mtime,
                        stat.st_size,
                        tuple(problematic)
                    )
        except OSError:
            # File may have been removed/modified - skip caching
            pass

        return problematic
    
    def _is_problematic_import(self, module_name: str) -> bool:
        """Check if an import is problematic for sub-interpreters"""
        # Check if module or its parent is problematic
        parts = module_name.split('.')
        for i in range(len(parts)):
            partial = '.'.join(parts[:i+1])
            if partial in _Constants.PROBLEMATIC_MODULES:
                return True

        return False
    
    def _analyze_dependencies(self, module) -> List[str]:
        """Analyze module dependencies"""
        deps = []

        try:
            # Get module dependencies from __requires__ if available
            if hasattr(module, '__requires__'):
                deps.extend(module.__requires__)

            module_dict = getattr(module, '__dict__', {})
            for name, obj in module_dict.items():
                if name.startswith('_'):
                    continue
                if inspect.ismodule(obj):
                    mod_name = getattr(obj, '__name__', '')
                    if mod_name and not mod_name.startswith('_'):
                        deps.append(mod_name)

        except Exception as e:
            logger.debug(f"Failed to analyze dependencies: {e}")

        return list(set(deps))


class ExtensionDetector:
    """
    Detects C extensions and native code in Python modules.
    """

    # Class attribute: Known C extension modules (for fast lookup)
    KNOWN_C_EXTENSIONS = {
        # NumPy ecosystem
        'numpy', 'numpy.core', 'numpy.linalg', 'numpy.fft', 'numpy.random',
        'scipy', 'scipy.linalg', 'scipy.sparse', 'scipy.special',
        'pandas', 'pandas._libs', 'pandas.core',

        # ML/AI frameworks
        'tensorflow', 'torch', 'jax', 'mxnet', 'theano', 'keras',
        'sklearn', 'scikit-learn', 'xgboost', 'lightgbm',

        # Image processing
        'cv2', 'PIL', 'Pillow', 'skimage', 'imageio',

        # Data formats
        'h5py', 'netCDF4', 'zarr', 'pyarrow', 'fastparquet',

        # Database drivers
        'psycopg2', 'mysqlclient', 'cx_Oracle', 'pymssql', 'ibm_db',

        # Crypto
        'cryptography', 'pycrypto', 'bcrypt', 'nacl',

        # System/hardware
        'pyserial', 'pyusb', 'pybluez', 'RPi', 'pigpio', 'psutil',

        # GUI
        'tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx', 'pygame',

        # Other
        'lxml', 'yaml', 'msgpack', 'ujson', 'orjson', 'regex'
    }

    def __init__(self):
        """Initialize the extension detector"""
        self.stdlib_path = sysconfig.get_path('stdlib')
        self.platstdlib_path = sysconfig.get_path('platstdlib')
        # Use class attribute as basis
        self._known_c_extensions = self.KNOWN_C_EXTENSIONS.copy()
        self._cache = {}
    
    def _build_known_extensions(self) -> Set[str]:
        """Build set of known C extension modules"""
        known = {
            # NumPy ecosystem
            'numpy', 'numpy.core', 'numpy.linalg', 'numpy.fft', 'numpy.random',
            'scipy', 'scipy.linalg', 'scipy.sparse', 'scipy.special',
            'pandas', 'pandas._libs', 'pandas.core',
            
            # ML/AI frameworks
            'tensorflow', 'torch', 'jax', 'mxnet', 'theano', 'keras',
            'sklearn', 'scikit-learn', 'xgboost', 'lightgbm',
            
            # Image processing
            'cv2', 'PIL', 'Pillow', 'skimage', 'imageio',
            
            # Data formats
            'h5py', 'netCDF4', 'zarr', 'pyarrow', 'fastparquet',
            
            # Database drivers
            'psycopg2', 'mysqlclient', 'cx_Oracle', 'pymssql', 'ibm_db',
            
            # Crypto
            'cryptography', 'pycrypto', 'bcrypt', 'nacl', 'hashlib',
            
            # System/hardware
            'pyserial', 'pyusb', 'pybluez', 'RPi', 'pigpio', 'psutil',
            
            # GUI
            'tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx', 'pygame',
            
            # Other
            'lxml', 'yaml', 'msgpack', 'ujson', 'orjson', 'regex'
        }
        
        return known
    
    def has_c_extension(self, module_name: str) -> bool:
        """
        Quick check if module has C extensions.
        
        Args:
            module_name: Module to check
            
        Returns:
            True if module has C extensions
        """
        # Check known extensions first
        if module_name in self._known_c_extensions:
            return True
        
        # Check parent modules
        parts = module_name.split('.')
        for i in range(len(parts)):
            partial = '.'.join(parts[:i+1])
            if partial in self._known_c_extensions:
                return True
        
        # Try to detect through analysis
        info = self.analyze_module(module_name)
        return info['has_c_extension']
    
    def analyze_module(self, module_name: str) -> Dict[str, Any]:
        """
        Analyze module for C extensions.
        
        Args:
            module_name: Module to analyze
            
        Returns:
            Dictionary with extension information
        """
        # Check cache first
        if module_name in self._cache:
            return self._cache[module_name]
        
        result = {
            'module': module_name,
            'has_c_extension': False,
            'c_modules': [],
            'pure_python': True,
            'extension_suffixes': []
        }
        
        try:
            # Find module spec
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                result['error'] = 'Module not found'
                return result

            # Check if it's a built-in module
            # Builtin modules have origin == 'built-in' or origin is None and in sys.builtin_module_names
            if spec.origin == 'built-in' or (spec.origin is None and module_name in sys.builtin_module_names):
                result['has_c_extension'] = True
                result['pure_python'] = False
                result['c_modules'].append(module_name)
                return result

            # Check file extension (even if file doesn't exist - for mocking)
            if spec.origin:
                ext = os.path.splitext(spec.origin)[1]

                # Get valid extension suffixes for this platform
                ext_suffixes = importlib.machinery.EXTENSION_SUFFIXES

                # Check for C extension suffixes
                if ext in ext_suffixes or ext in ['.so', '.pyd', '.dll']:
                    result['has_c_extension'] = True
                    result['pure_python'] = False
                    result['c_modules'].append(module_name)
                    result['extension_suffixes'].append(ext)
            
            # Check if it's a package and look for extensions
            if spec.submodule_search_locations:
                for search_path in spec.submodule_search_locations:
                    if os.path.exists(search_path):
                        self._scan_directory_for_extensions(
                            Path(search_path), 
                            result
                        )
            
        except Exception as e:
            logger.debug(f"Error analyzing module {module_name}: {e}")
            result['error'] = str(e)
        
        # Cache the result
        self._cache[module_name] = result
        
        return result

    def check_module_imports(self, module_name: str) -> List[str]:
        """
        Check which C extension modules are imported by this module.

        Args:
            module_name: Module to analyze

        Returns:
            List of C extension module names that this module imports

        Useful for understanding indirect C extension dependencies.
        """
        c_imports = []

        try:
            # Import the module
            module = importlib.import_module(module_name)

            # Check module's imports/attributes
            for name, obj in vars(module).items():
                # Check if it's a module
                if hasattr(obj, '__name__') and hasattr(obj, '__file__'):
                    obj_name = obj.__name__

                    # Check if this imported module is a known C extension
                    if obj_name in self._known_c_extensions:
                        c_imports.append(obj_name)

                    # Also check via has_c_extension for unlisted modules
                    elif self.has_c_extension(obj_name):
                        c_imports.append(obj_name)

            # Remove duplicates and sort
            c_imports = sorted(set(c_imports))

            logger.debug(f"{module_name} imports C extensions: {c_imports}")

        except ImportError as e:
            logger.debug(f"Could not import {module_name} to check imports: {e}")
        except Exception as e:
            logger.debug(f"Error checking imports for {module_name}: {e}")

        return c_imports

    def _scan_directory_for_extensions(self, directory: Path, result: Dict[str, Any]) -> None:
        """Scan directory for C extension files"""
        ext_suffixes = importlib.machinery.EXTENSION_SUFFIXES
        
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    for suffix in ext_suffixes:
                        if str(file_path).endswith(suffix):
                            result['has_c_extension'] = True
                            result['pure_python'] = False
                            
                            # Extract module name from file
                            rel_path = file_path.relative_to(directory)
                            module_parts = list(rel_path.parts[:-1])
                            module_parts.append(rel_path.stem)
                            c_module = '.'.join(module_parts)
                            
                            result['c_modules'].append(c_module)
                            if suffix not in result['extension_suffixes']:
                                result['extension_suffixes'].append(suffix)
                            
        except Exception as e:
            logger.debug(f"Error scanning directory {directory}: {e}")

    def scan_directory(self, directory: str, recursive: bool = True) -> List[str]:
        """
        Scan directory for C extension files.

        Args:
            directory: Path to directory to scan
            recursive: If True, scan subdirectories recursively

        Returns:
            List of C extension file paths found
        """
        c_extension_files = []

        try:
            dir_path = Path(directory)
            if not dir_path.exists() or not dir_path.is_dir():
                return []

            # Get valid extension suffixes for this platform
            ext_suffixes = importlib.machinery.EXTENSION_SUFFIXES
            # Also check for common C extension suffixes
            all_suffixes = set(ext_suffixes) | {'.so', '.pyd', '.dll'}

            # Choose iterator based on recursive flag
            file_iterator = dir_path.rglob('*') if recursive else dir_path.glob('*')

            for file_path in file_iterator:
                if file_path.is_file():
                    ext = file_path.suffix
                    if ext in all_suffixes:
                        c_extension_files.append(str(file_path))

        except Exception as e:
            logger.debug(f"Error scanning directory {directory}: {e}")

        return c_extension_files

    def is_unsafe_for_subinterpreters(self, module_name: str) -> bool:
        """
        Check if module is known to be unsafe for sub-interpreters.
        
        Args:
            module_name: Module to check
            
        Returns:
            True if module is unsafe for sub-interpreters
        """
        # Modules with known global state issues
        unsafe_modules = {
            'numpy', 'scipy', 'pandas', 'matplotlib',
            'tensorflow', 'torch', 'jax',
            'multiprocessing', 'concurrent.futures',
            'tkinter', 'pygame', 'PyQt5', 'PyQt6',
            'cv2', 'PIL', 'Pillow'
        }
        
        # Check exact match
        if module_name in unsafe_modules:
            return True
        
        # Check if it's a submodule of unsafe module
        for unsafe in unsafe_modules:
            if module_name.startswith(unsafe + '.'):
                return True
        
        return False