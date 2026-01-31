"""
Epochly API endpoints configuration.

Centralizes all API endpoint definitions for the Epochly system.
"""

import os
from typing import Dict, Optional


class APIEndpoints:
    """Manages API endpoint configuration for Epochly."""
    
    # Default to custom domain, fallback to direct AWS endpoint
    DEFAULT_BASE_URL = "https://api.epochly.com"
    FALLBACK_BASE_URL = "https://6g2po3kxnd.execute-api.us-west-2.amazonaws.com/prod"
    
    # Allow override via environment variable
    BASE_URL = os.environ.get('EPOCHLY_API_URL', DEFAULT_BASE_URL)
    
    # API endpoints
    ENDPOINTS = {
        # Trial system
        'trial_activation': f"{BASE_URL}/trial/activate",
        'trial_validation': f"{BASE_URL}/trial/validate",
        
        # Compatibility system
        'compatibility_report': f"{BASE_URL}/compatibility/report",
        'compatibility_sync': f"{BASE_URL}/compatibility/sync",
        'compatibility_get': f"{BASE_URL}/compatibility/get",
        
        # Node management
        'node_register': f"{BASE_URL}/node/register",
        'node_cleanup': f"{BASE_URL}/node/cleanup",
        
        # Telemetry
        'telemetry': f"{BASE_URL}/telemetry",
        'critical_event': f"{BASE_URL}/critical-event"
    }
    
    @classmethod
    def get_endpoint(cls, name: str) -> str:
        """
        Get endpoint URL by name.
        
        Args:
            name: Endpoint name
            
        Returns:
            Full endpoint URL
            
        Raises:
            KeyError: If endpoint name not found
        """
        if name not in cls.ENDPOINTS:
            raise KeyError(f"Unknown endpoint: {name}")
        return cls.ENDPOINTS[name]
    
    @classmethod
    def get_headers(cls, include_auth: bool = False, api_key: Optional[str] = None) -> Dict[str, str]:
        """
        Get standard headers for API requests.
        
        Args:
            include_auth: Whether to include authentication headers
            api_key: Optional API key for protected endpoints
            
        Returns:
            Dictionary of headers
        """
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Epochly/1.0'
        }
        
        if include_auth and api_key:
            headers['X-Epochly-API-Key'] = api_key
            
        return headers
    
    @classmethod
    def use_fallback(cls):
        """Switch to fallback URL if custom domain fails."""
        cls.BASE_URL = cls.FALLBACK_BASE_URL
        # Update all endpoints
        for key in cls.ENDPOINTS:
            endpoint_path = cls.ENDPOINTS[key].split('.com')[-1]
            cls.ENDPOINTS[key] = f"{cls.BASE_URL}{endpoint_path}"
    
    @classmethod
    def test_connectivity(cls) -> bool:
        """
        Test connectivity to API endpoint.
        
        Returns:
            True if API is reachable
        """
        import requests
        
        try:
            # Test with a simple OPTIONS request
            response = requests.options(
                f"{cls.BASE_URL}/trial/activate",
                timeout=5
            )
            return response.status_code == 200
        except (requests.RequestException, OSError):
            # Try fallback
            try:
                cls.use_fallback()
                response = requests.options(
                    f"{cls.BASE_URL}/trial/activate",
                    timeout=5
                )
                return response.status_code == 200
            except (requests.RequestException, OSError):
                return False


# Convenience function for importing
def get_api_endpoint(name: str) -> str:
    """Get API endpoint URL by name."""
    return APIEndpoints.get_endpoint(name)