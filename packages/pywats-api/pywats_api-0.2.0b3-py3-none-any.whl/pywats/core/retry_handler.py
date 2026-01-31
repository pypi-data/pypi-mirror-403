"""
Shared Retry Handler for HTTP Clients

Provides a unified retry execution strategy used by both sync and async HTTP clients.
This eliminates code duplication while keeping the execution model (sync/async) separate.

The handler encapsulates:
- Retry decision logic (status codes, exceptions, methods)
- Delay calculation (exponential backoff, jitter, Retry-After header)
- Statistics tracking
- Logging

Usage:
    # In sync client
    handler = RetryHandler(config, rate_limiter)
    result = handler.execute_sync(make_request_func, method, endpoint)
    
    # In async client  
    handler = RetryHandler(config, rate_limiter)
    result = await handler.execute_async(make_request_coro, method, endpoint)
"""
from __future__ import annotations

import time
import asyncio
import logging
from typing import TYPE_CHECKING, Callable, Awaitable, Optional, TypeVar, Any
from dataclasses import dataclass

from .retry import RetryConfig, should_retry
from .throttle import RateLimiter

if TYPE_CHECKING:
    from .client import Response

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class RetryContext:
    """Context passed to retry callbacks for logging and tracing."""
    method: str
    endpoint: str
    attempt: int
    max_attempts: int
    delay: float = 0.0
    error_type: Optional[str] = None
    status_code: Optional[int] = None


class RetryHandler:
    """
    Unified retry execution handler for HTTP requests.
    
    Encapsulates retry logic shared between sync and async HTTP clients.
    The actual HTTP execution is delegated to caller-provided functions.
    
    Example:
        >>> handler = RetryHandler(retry_config, rate_limiter)
        >>> 
        >>> # Sync usage
        >>> response = handler.execute_sync(
        ...     request_func=lambda: client.request("GET", "/api/test"),
        ...     method="GET",
        ...     endpoint="/api/test"
        ... )
        >>> 
        >>> # Async usage
        >>> response = await handler.execute_async(
        ...     request_coro=lambda: client.request("GET", "/api/test"),
        ...     method="GET", 
        ...     endpoint="/api/test"
        ... )
    """
    
    def __init__(
        self,
        config: RetryConfig,
        rate_limiter: RateLimiter,
        on_retry: Optional[Callable[[RetryContext], None]] = None,
    ):
        """
        Initialize retry handler.
        
        Args:
            config: Retry configuration
            rate_limiter: Rate limiter for throttling
            on_retry: Optional callback invoked before each retry
        """
        self._config = config
        self._rate_limiter = rate_limiter
        self._on_retry = on_retry
    
    @property
    def config(self) -> RetryConfig:
        """Get retry configuration."""
        return self._config
    
    def _should_retry_response(
        self,
        response: "Response",
        method: str,
        attempt: int,
    ) -> tuple[bool, float]:
        """Check if response warrants a retry."""
        return should_retry(
            self._config, method, attempt, response=response
        )
    
    def _should_retry_exception(
        self,
        exception: Exception,
        method: str,
        attempt: int,
    ) -> tuple[bool, float]:
        """Check if exception warrants a retry."""
        return should_retry(
            self._config, method, attempt, exception=exception
        )
    
    def _log_retry(
        self,
        context: RetryContext,
    ) -> None:
        """Log retry attempt and update stats."""
        self._config.record_retry(context.delay)
        
        error_info = ""
        if context.status_code:
            error_info = f"HTTP {context.status_code}"
        elif context.error_type:
            error_info = context.error_type
        
        logger.info(
            f"Retry {context.attempt + 1}/{context.max_attempts} for "
            f"{context.method} {context.endpoint} after {context.delay:.2f}s ({error_info})"
        )
        
        if self._on_retry:
            self._on_retry(context)
    
    def execute_sync(
        self,
        request_func: Callable[[], "Response"],
        method: str,
        endpoint: str,
        handle_response: Callable[[Any], "Response"],
        retry_enabled: Optional[bool] = None,
    ) -> "Response":
        """
        Execute request with sync retry logic.
        
        Args:
            request_func: Function that makes the HTTP request and returns raw response
            method: HTTP method
            endpoint: API endpoint
            handle_response: Function to convert raw response to Response object
            retry_enabled: Override retry behavior
            
        Returns:
            Response object
            
        Raises:
            Exception from request_func if all retries exhausted
        """
        from .exceptions import ConnectionError, TimeoutError, PyWATSError
        import httpx
        
        should_retry_flag = retry_enabled if retry_enabled is not None else self._config.enabled
        max_attempts = self._config.max_attempts if should_retry_flag else 1
        
        last_exception: Optional[Exception] = None
        last_response: Optional["Response"] = None
        
        for attempt in range(max_attempts):
            # Acquire rate limiter slot
            self._rate_limiter.acquire()
            
            try:
                raw_response = request_func()
                parsed_response = handle_response(raw_response)
                
                # Check if we should retry this status code
                if should_retry_flag and self._config.should_retry_status(raw_response.status_code):
                    should_retry_now, delay = self._should_retry_response(
                        parsed_response, method, attempt
                    )
                    if should_retry_now:
                        self._log_retry(RetryContext(
                            method=method,
                            endpoint=endpoint,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            delay=delay,
                            status_code=raw_response.status_code,
                        ))
                        time.sleep(delay)
                        last_response = parsed_response
                        continue
                
                return parsed_response
                
            except httpx.ConnectError as e:
                last_exception = ConnectionError(
                    f"Failed to connect: {e}",
                    url=endpoint
                )
                
                if should_retry_flag:
                    should_retry_now, delay = self._should_retry_exception(
                        last_exception, method, attempt
                    )
                    if should_retry_now:
                        self._log_retry(RetryContext(
                            method=method,
                            endpoint=endpoint,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            delay=delay,
                            error_type="ConnectionError",
                        ))
                        time.sleep(delay)
                        continue
                
                raise last_exception
                
            except httpx.TimeoutException as e:
                last_exception = TimeoutError(
                    f"Request timed out: {e}",
                    endpoint=endpoint
                )
                
                if should_retry_flag:
                    should_retry_now, delay = self._should_retry_exception(
                        last_exception, method, attempt
                    )
                    if should_retry_now:
                        self._log_retry(RetryContext(
                            method=method,
                            endpoint=endpoint,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            delay=delay,
                            error_type="TimeoutError",
                        ))
                        time.sleep(delay)
                        continue
                
                raise last_exception
                
            except Exception as e:
                raise PyWATSError(f"HTTP request failed: {e}", show_hints=False)
        
        # All retries exhausted
        if last_exception:
            raise last_exception
        if last_response:
            return last_response
        
        raise PyWATSError("Unexpected state: no response or exception after retries", show_hints=False)
    
    async def execute_async(
        self,
        request_coro: Callable[[], Awaitable[Any]],
        method: str,
        endpoint: str,
        handle_response: Callable[[Any], "Response"],
        retry_enabled: Optional[bool] = None,
    ) -> "Response":
        """
        Execute request with async retry logic.
        
        Args:
            request_coro: Async function that makes the HTTP request
            method: HTTP method
            endpoint: API endpoint
            handle_response: Function to convert raw response to Response object
            retry_enabled: Override retry behavior
            
        Returns:
            Response object
            
        Raises:
            Exception from request_coro if all retries exhausted
        """
        from .exceptions import ConnectionError, TimeoutError, PyWATSError
        import httpx
        
        should_retry_flag = retry_enabled if retry_enabled is not None else self._config.enabled
        max_attempts = self._config.max_attempts if should_retry_flag else 1
        
        last_exception: Optional[Exception] = None
        last_response: Optional["Response"] = None
        
        for attempt in range(max_attempts):
            # Acquire rate limiter slot (sync - rate limiter is not async)
            self._rate_limiter.acquire()
            
            try:
                raw_response = await request_coro()
                parsed_response = handle_response(raw_response)
                
                # Check if we should retry this status code
                if should_retry_flag and self._config.should_retry_status(raw_response.status_code):
                    should_retry_now, delay = self._should_retry_response(
                        parsed_response, method, attempt
                    )
                    if should_retry_now:
                        self._log_retry(RetryContext(
                            method=method,
                            endpoint=endpoint,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            delay=delay,
                            status_code=raw_response.status_code,
                        ))
                        await asyncio.sleep(delay)
                        last_response = parsed_response
                        continue
                
                return parsed_response
                
            except httpx.ConnectError as e:
                last_exception = ConnectionError(
                    f"Failed to connect: {e}",
                    url=endpoint
                )
                
                if should_retry_flag:
                    should_retry_now, delay = self._should_retry_exception(
                        last_exception, method, attempt
                    )
                    if should_retry_now:
                        self._log_retry(RetryContext(
                            method=method,
                            endpoint=endpoint,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            delay=delay,
                            error_type="ConnectionError",
                        ))
                        await asyncio.sleep(delay)
                        continue
                
                raise last_exception
                
            except httpx.TimeoutException as e:
                last_exception = TimeoutError(
                    f"Request timed out: {e}",
                    endpoint=endpoint
                )
                
                if should_retry_flag:
                    should_retry_now, delay = self._should_retry_exception(
                        last_exception, method, attempt
                    )
                    if should_retry_now:
                        self._log_retry(RetryContext(
                            method=method,
                            endpoint=endpoint,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            delay=delay,
                            error_type="TimeoutError",
                        ))
                        await asyncio.sleep(delay)
                        continue
                
                raise last_exception
                
            except Exception as e:
                raise PyWATSError(f"HTTP request failed: {e}", show_hints=False)
        
        # All retries exhausted
        if last_exception:
            raise last_exception
        if last_response:
            return last_response
        
        raise PyWATSError("Unexpected state: no response or exception after retries", show_hints=False)
