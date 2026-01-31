"""
Epochly Deployment Infrastructure

This module provides controlled deployment capabilities for Epochly including:
- Transparent activation via sitecustomize.py
- Selective activation and deactivation controls
- Emergency controls for production safety
- Deployment monitoring and health checks

Author: Epochly Development Team
"""

from .deployment_controller import DeploymentController
from .activation_manager import ActivationManager, ActivationMode
from .sitecustomize_installer import SitecustomizeInstaller
from .emergency_controls import EmergencyControls

__all__ = [
    'DeploymentController',
    'ActivationManager', 
    'ActivationMode',
    'SitecustomizeInstaller',
    'EmergencyControls'
]