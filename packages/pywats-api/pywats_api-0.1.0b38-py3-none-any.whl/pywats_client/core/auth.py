"""
Authentication utilities for pyWATS Client GUI

Provides simple authentication helpers that use pyWATS API directly.
"""

import logging
from typing import Optional, Tuple
from dataclasses import dataclass

from pywats import pyWATS

logger = logging.getLogger(__name__)


@dataclass
class AuthResult:
    """Result of authentication attempt"""
    success: bool
    token: Optional[str] = None
    error: Optional[str] = None
    base_url: Optional[str] = None


def authenticate_with_password(
    server_url: str,
    password: str,
    username: str = ""
) -> AuthResult:
    """
    Authenticate with WATS server using password.
    
    Args:
        server_url: WATS server URL (e.g., https://company.wats.com)
        password: User password or API token
        username: Optional username (not typically needed)
        
    Returns:
        AuthResult with success status and token/error
    """
    server_url = server_url.rstrip('/')
    
    if not server_url or not password:
        return AuthResult(
            success=False,
            error="Server URL and password are required"
        )
    
    try:
        # Try to connect with pyWATS using password as token
        # The password might actually be a pre-generated token
        api = pyWATS(base_url=server_url, token=password)
        
        # Test connection by fetching client info
        info = api.get_client_info()
        
        if info:
            logger.info(f"Successfully authenticated to {server_url}")
            return AuthResult(
                success=True,
                token=password,
                base_url=server_url
            )
        else:
            return AuthResult(
                success=False,
                error="Failed to retrieve client info"
            )
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Authentication failed: {error_msg}")
        return AuthResult(
            success=False,
            error=error_msg
        )


def test_connection(server_url: str, token: str) -> bool:
    """
    Test if connection to WATS server works.
    
    Args:
        server_url: WATS server URL
        token: API token
        
    Returns:
        True if connection successful
    """
    try:
        api = pyWATS(base_url=server_url, token=token)
        info = api.get_client_info()
        return info is not None
    except Exception:
        return False
