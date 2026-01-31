"""
Container Integration Module

This module provides container-specific optimizations and adaptations
for Docker, Kubernetes, Lambda, and other containerized environments.
"""

from .adapter import ContainerAdapter

__all__ = ['ContainerAdapter']