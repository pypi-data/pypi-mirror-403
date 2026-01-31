"""
Kubernetes Integration Module

This module provides Kubernetes-specific integrations for Epochly including
health endpoints, graceful shutdown handling, and container optimization.
"""

from .health_server import HealthServer

__all__ = ['HealthServer']