"""
Security utilities for pyWATS Client.

Simple, pragmatic security for trusted environments:
- Shared secret authentication (prevent accidents)
- Token validation
- Secret storage and management

Context: pyWATS typically runs on secure stations behind machine authentication.
This is not military-grade security - it prevents accidents and basic abuse.
"""

import hashlib
import secrets
import sys
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_secret_directory() -> Path:
    """
    Get platform-specific directory for storing secrets.
    
    Returns:
        Path to secrets directory (created if not exists)
    """
    if sys.platform == 'win32':
        # Windows: Use AppData\Local
        base = Path.home() / "AppData" / "Local" / "pyWATS" / "secrets"
    else:
        # Linux/macOS: Use ~/.config
        base = Path.home() / ".config" / "pywats" / "secrets"
    
    # Create directory if it doesn't exist
    base.mkdir(parents=True, exist_ok=True)
    
    # Set restrictive permissions on Unix
    if sys.platform != 'win32':
        try:
            base.chmod(0o700)  # rwx------ (owner only)
        except Exception as e:
            logger.warning(f"Failed to set restrictive permissions on secrets directory: {e}")
    
    return base


def generate_secret() -> str:
    """
    Generate a cryptographically secure random secret.
    
    Returns:
        Secret token (64 hex characters, 256 bits)
    """
    return secrets.token_hex(32)  # 32 bytes = 256 bits


def save_secret(instance_id: str, secret: str) -> Path:
    """
    Save secret to secure location.
    
    Args:
        instance_id: Instance identifier
        secret: Secret token to save
        
    Returns:
        Path to saved secret file
        
    Raises:
        OSError: If file cannot be created/written
    """
    secret_dir = get_secret_directory()
    secret_file = secret_dir / f"{instance_id}.key"
    
    # Write secret
    secret_file.write_text(secret, encoding='utf-8')
    
    # Set restrictive permissions on Unix
    if sys.platform != 'win32':
        try:
            secret_file.chmod(0o600)  # rw------- (owner read/write only)
        except Exception as e:
            logger.warning(f"Failed to set restrictive permissions on secret file: {e}")
    
    logger.info(f"Secret saved for instance '{instance_id}': {secret_file}")
    return secret_file


def load_secret(instance_id: str) -> Optional[str]:
    """
    Load secret from secure location.
    
    Args:
        instance_id: Instance identifier
        
    Returns:
        Secret token if found, None otherwise
    """
    secret_dir = get_secret_directory()
    secret_file = secret_dir / f"{instance_id}.key"
    
    if not secret_file.exists():
        return None
    
    try:
        secret = secret_file.read_text(encoding='utf-8').strip()
        return secret
    except Exception as e:
        logger.error(f"Failed to load secret for instance '{instance_id}': {e}")
        return None


def delete_secret(instance_id: str) -> bool:
    """
    Delete secret file.
    
    Args:
        instance_id: Instance identifier
        
    Returns:
        True if deleted, False if not found
    """
    secret_dir = get_secret_directory()
    secret_file = secret_dir / f"{instance_id}.key"
    
    if not secret_file.exists():
        return False
    
    try:
        secret_file.unlink()
        logger.info(f"Secret deleted for instance '{instance_id}'")
        return True
    except Exception as e:
        logger.error(f"Failed to delete secret for instance '{instance_id}': {e}")
        return False


def validate_token(token: str, secret: str) -> bool:
    """
    Validate authentication token.
    
    Simple comparison - no complex challenge/response needed for trusted environment.
    
    Args:
        token: Token provided by client
        secret: Expected secret
        
    Returns:
        True if token matches secret
    """
    return secrets.compare_digest(token, secret)


def hash_secret(secret: str) -> str:
    """
    Hash secret for logging/debugging (never log raw secret).
    
    Args:
        secret: Secret to hash
        
    Returns:
        SHA256 hash (first 16 hex characters for brevity)
    """
    hash_obj = hashlib.sha256(secret.encode('utf-8'))
    return hash_obj.hexdigest()[:16]


class RateLimiter:
    """
    Simple token bucket rate limiter.
    
    Prevents accidental DoS from misbehaving clients.
    Not cryptographically secure - trusted environment.
    """
    
    def __init__(self, requests_per_minute: int = 100, burst_size: int = 20):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Sustained request rate limit
            burst_size: Maximum burst size above sustained rate
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        
        # Token bucket state per client
        self._buckets: dict[str, dict] = {}
    
    def check_rate_limit(self, client_id: str) -> bool:
        """
        Check if client is within rate limit.
        
        Args:
            client_id: Client identifier (e.g., peer address)
            
        Returns:
            True if allowed, False if rate limited
        """
        import time
        
        now = time.time()
        
        # Get or create bucket for client
        if client_id not in self._buckets:
            self._buckets[client_id] = {
                'tokens': self.burst_size,
                'last_update': now
            }
        
        bucket = self._buckets[client_id]
        
        # Refill tokens based on time elapsed
        time_elapsed = now - bucket['last_update']
        tokens_to_add = time_elapsed * (self.requests_per_minute / 60.0)
        bucket['tokens'] = min(bucket['tokens'] + tokens_to_add, self.burst_size)
        bucket['last_update'] = now
        
        # Check if token available
        if bucket['tokens'] >= 1.0:
            bucket['tokens'] -= 1.0
            return True
        else:
            return False
    
    def reset(self, client_id: str) -> None:
        """
        Reset rate limit for client.
        
        Args:
            client_id: Client identifier
        """
        if client_id in self._buckets:
            del self._buckets[client_id]
    
    def cleanup_old_clients(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up buckets for clients that haven't been seen recently.
        
        Args:
            max_age_seconds: Maximum age to keep inactive clients
            
        Returns:
            Number of clients removed
        """
        import time
        
        now = time.time()
        old_clients = [
            client_id for client_id, bucket in self._buckets.items()
            if now - bucket['last_update'] > max_age_seconds
        ]
        
        for client_id in old_clients:
            del self._buckets[client_id]
        
        return len(old_clients)
