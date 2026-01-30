"""
Retry configuration and utilities for transient failure handling.

This module provides automatic retry logic for HTTP requests that fail
due to transient issues like network errors, timeouts, or server overloads.

Example:
    >>> from pywats import pyWATS, RetryConfig
    >>> 
    >>> # Default retry (3 attempts, exponential backoff)
    >>> api = pyWATS(base_url="...", token="...")
    >>> 
    >>> # Custom retry configuration
    >>> config = RetryConfig(max_attempts=5, base_delay=2.0)
    >>> api = pyWATS(base_url="...", token="...", retry_config=config)
    >>> 
    >>> # Disable retry
    >>> api = pyWATS(base_url="...", token="...", retry_enabled=False)
"""
import builtins
import time
import random
import logging
from dataclasses import dataclass, field
from typing import Optional, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Response

logger = logging.getLogger(__name__)


# Status codes that indicate transient failures worth retrying
RETRYABLE_STATUS_CODES: Set[int] = {429, 500, 502, 503, 504}

# HTTP methods that are safe to retry (idempotent)
IDEMPOTENT_METHODS: Set[str] = {"GET", "PUT", "DELETE", "HEAD", "OPTIONS"}


@dataclass
class RetryConfig:
    """
    Configuration for automatic retry behavior.
    
    The retry system uses exponential backoff with optional jitter to handle
    transient failures gracefully without overwhelming the server.
    
    Attributes:
        enabled: Whether retry is enabled (default: True)
        max_attempts: Maximum number of attempts including initial (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay cap in seconds (default: 30.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        jitter: Whether to add random jitter (default: True)
        retry_methods: HTTP methods to retry (default: idempotent only)
        retry_status_codes: HTTP status codes to retry (default: 429, 5xx)
        retry_on_timeout: Retry on timeout errors (default: True)
        retry_on_connection_error: Retry on connection errors (default: True)
        
    Example:
        >>> # Default configuration
        >>> config = RetryConfig()
        >>> 
        >>> # More aggressive retry
        >>> config = RetryConfig(max_attempts=5, base_delay=0.5)
        >>> 
        >>> # Disable jitter for predictable behavior in tests
        >>> config = RetryConfig(jitter=False)
        >>> 
        >>> # Only retry GET requests
        >>> config = RetryConfig(retry_methods={"GET"})
    """
    enabled: bool = True
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_methods: Set[str] = field(default_factory=lambda: IDEMPOTENT_METHODS.copy())
    retry_status_codes: Set[int] = field(default_factory=lambda: RETRYABLE_STATUS_CODES.copy())
    retry_on_timeout: bool = True
    retry_on_connection_error: bool = True
    
    # Statistics (updated during operation)
    _total_retries: int = field(default=0, repr=False)
    _total_retry_time: float = field(default=0.0, repr=False)
    
    def should_retry_method(self, method: str) -> bool:
        """Check if the HTTP method is safe to retry."""
        return method.upper() in self.retry_methods
    
    def should_retry_status(self, status_code: int) -> bool:
        """Check if the status code indicates a retryable error."""
        return status_code in self.retry_status_codes
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry attempt.
        
        Uses exponential backoff with optional jitter.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = self.base_delay * (self.exponential_base ** attempt)
        
        if self.jitter:
            # Full jitter: random value between 0 and calculated delay
            delay = random.uniform(0, delay)
        
        return min(delay, self.max_delay)
    
    def get_retry_after(self, response: "Response") -> Optional[float]:
        """
        Extract Retry-After header value if present.
        
        Args:
            response: HTTP response object
            
        Returns:
            Delay in seconds, or None if header not present
        """
        retry_after = response.headers.get("Retry-After")
        if retry_after is None:
            return None
        
        try:
            # Try parsing as integer (seconds)
            return float(retry_after)
        except ValueError:
            # Could be HTTP date format - ignore for simplicity
            logger.debug(f"Could not parse Retry-After header: {retry_after}")
            return None
    
    @property
    def stats(self) -> dict:
        """Get retry statistics."""
        return {
            "total_retries": self._total_retries,
            "total_retry_time": round(self._total_retry_time, 2),
        }
    
    def record_retry(self, delay: float) -> None:
        """Record a retry attempt for statistics."""
        self._total_retries += 1
        self._total_retry_time += delay
    
    def reset_stats(self) -> None:
        """Reset retry statistics."""
        self._total_retries = 0
        self._total_retry_time = 0.0


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted."""
    
    def __init__(
        self, 
        message: str, 
        attempts: int, 
        last_error: Optional[Exception] = None,
        last_exception: Optional[Exception] = None  # Alias for backwards compat
    ):
        super().__init__(message)
        self.attempts = attempts
        # Accept either name for the last error
        self.last_error = last_error or last_exception
        self.last_exception = self.last_error  # Alias


def should_retry(
    config: RetryConfig,
    method: str,
    attempt: int,
    response: Optional["Response"] = None,
    exception: Optional[Exception] = None
) -> Tuple[bool, float]:
    """
    Determine if a request should be retried.
    
    Args:
        config: Retry configuration
        method: HTTP method
        attempt: Current attempt number (0-indexed)
        response: HTTP response (if request completed)
        exception: Exception raised (if request failed)
        
    Returns:
        Tuple of (should_retry, delay_seconds)
    """
    if not config.enabled:
        return False, 0.0
    
    # Check if we've exhausted attempts
    if attempt >= config.max_attempts - 1:
        return False, 0.0
    
    # Check if method is retryable
    if not config.should_retry_method(method):
        logger.debug(f"Method {method} is not configured for retry")
        return False, 0.0
    
    # Determine if this failure is retryable
    should_retry_this = False
    
    if exception is not None:
        # Import here to avoid circular imports
        from .exceptions import ConnectionError as PyWATSConnectionError
        from .exceptions import TimeoutError as PyWATSTimeoutError
        
        # Check for both our custom exceptions and Python's built-in ones
        is_connection_error = isinstance(exception, (PyWATSConnectionError, builtins.ConnectionError))
        is_timeout_error = isinstance(exception, (PyWATSTimeoutError, builtins.TimeoutError))
        
        if is_connection_error and config.retry_on_connection_error:
            should_retry_this = True
        elif is_timeout_error and config.retry_on_timeout:
            should_retry_this = True
    
    elif response is not None:
        if config.should_retry_status(response.status_code):
            should_retry_this = True
    
    if not should_retry_this:
        return False, 0.0
    
    # Calculate delay
    delay = config.calculate_delay(attempt)
    
    # Check for Retry-After header (takes precedence)
    if response is not None:
        retry_after = config.get_retry_after(response)
        if retry_after is not None:
            delay = min(retry_after, config.max_delay)
            logger.debug(f"Using Retry-After header: {delay}s")
    
    return True, delay
