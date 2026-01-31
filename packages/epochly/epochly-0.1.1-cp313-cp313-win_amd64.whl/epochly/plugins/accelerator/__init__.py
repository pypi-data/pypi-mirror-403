"""
Cross-language accelerator plugin system (SPEC2 Task 16).
"""

from .plugin_interface import AcceleratorPlugin, PluginCapabilities, PluginError
from .plugin_registry import AcceleratorRegistry
from .shared_memory_contract import SharedMemoryContract, BufferLayout


__all__ = [
    'AcceleratorPlugin',
    'PluginCapabilities',
    'PluginError',
    'AcceleratorRegistry',
    'SharedMemoryContract',
    'BufferLayout'
]
