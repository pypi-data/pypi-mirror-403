"""
Epochly Plugin Compatibility Layer

This module provides compatibility shims for importlib.metadata across Python versions.
Handles the API changes between Python 3.8-3.9 and 3.10+ for entry points.

Author: Epochly Development Team
"""

import sys
from typing import Iterator, Optional, Any

try:
    from importlib import metadata as _im
except ImportError:
    # Fallback for Python < 3.8
    import importlib_metadata as _im  # type: ignore


def iter_entry_points(group: str, *, name: Optional[str] = None) -> Iterator[Any]:
    """
    Yields entry points for both old (<3.10) and new (>=3.10) metadata API.
    
    Args:
        group: Entry point group name
        name: Optional entry point name filter
        
    Yields:
        Entry point objects compatible across Python versions
    """
    try:
        eps = _im.entry_points()
        
        # Python 3.10+ has .select() method
        if hasattr(eps, "select"):
            if name is not None:
                yield from eps.select(group=group, name=name)  # type: ignore
            else:
                yield from eps.select(group=group)  # type: ignore
        else:
            # Python 3.8-3.9 style - use runtime checks to avoid type issues
            all_eps = []
            
            # Try different access patterns with type: ignore to suppress warnings
            try:
                # Method 1: Try get() method
                if hasattr(eps, 'get'):
                    group_result = eps.get(group, [])  # type: ignore
                    if group_result:
                        # Runtime check for iterability
                        try:
                            # Test if it's iterable
                            test_iter = iter(group_result)  # type: ignore
                            next(test_iter, None)  # Test if iterator works
                            # If we get here, it's iterable
                            if not isinstance(group_result, (str, bytes)):
                                all_eps.extend(list(group_result))  # type: ignore
                            else:
                                all_eps.append(group_result)
                        except (TypeError, StopIteration):
                            # Not iterable or empty, treat as single item
                            all_eps.append(group_result)
            except Exception:
                pass
            
            if not all_eps:
                try:
                    # Method 2: Try subscript access
                    if hasattr(eps, '__contains__') and group in eps:  # type: ignore
                        group_result = eps[group]  # type: ignore
                        if group_result:
                            try:
                                # Test if it's iterable
                                test_iter = iter(group_result)  # type: ignore
                                next(test_iter, None)
                                # If we get here, it's iterable
                                if not isinstance(group_result, (str, bytes)):
                                    all_eps.extend(list(group_result))  # type: ignore
                                else:
                                    all_eps.append(group_result)
                            except (TypeError, StopIteration):
                                # Not iterable or empty, treat as single item
                                all_eps.append(group_result)
                except Exception:
                    pass
            
            if not all_eps:
                try:
                    # Method 3: Try iteration and filtering
                    for ep in eps:  # type: ignore
                        if hasattr(ep, 'group') and ep.group == group:
                            all_eps.append(ep)
                except Exception:
                    pass
            
            # Apply name filter and yield results
            for ep in all_eps:
                try:
                    if name is None or (hasattr(ep, 'name') and ep.name == name):
                        yield ep
                except Exception:
                    continue
                    
    except Exception:
        # If all else fails, return empty iterator
        return


def get_python_version_info() -> tuple:
    """Get Python version info for compatibility checks."""
    return sys.version_info[:3]


def is_python_310_plus() -> bool:
    """Check if running on Python 3.10 or later."""
    return sys.version_info >= (3, 10)