"""
Epochly Jupyter Integration

This module provides Jupyter/IPython integration for Epochly, including:
- IPython magic commands for interactive control
- Jupyter kernel installation and management
- Notebook-specific optimizations and reporting

Author: Epochly Development Team
"""

# Always available - kernel installation doesn't require IPython
from .kernel_installer import install_epochly_kernel, uninstall_epochly_kernel, list_epochly_kernels

# Conditionally import magic commands - only available when IPython is installed
try:
    from .magic_commands import EpochlyMagics, load_ipython_extension, unload_ipython_extension
    _IPYTHON_AVAILABLE = True
    __all__ = [
        'EpochlyMagics',
        'load_ipython_extension', 
        'unload_ipython_extension',
        'install_epochly_kernel',
        'uninstall_epochly_kernel', 
        'list_epochly_kernels'
    ]
except ImportError:
    _IPYTHON_AVAILABLE = False
    __all__ = [
        'install_epochly_kernel',
        'uninstall_epochly_kernel', 
        'list_epochly_kernels'
    ]