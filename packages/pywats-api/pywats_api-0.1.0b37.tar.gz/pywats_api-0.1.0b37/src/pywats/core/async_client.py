"""
Async HTTP Client for WATS API.

This module provides an asynchronous HTTP client with Basic authentication
for communicating with the WATS server using httpx.AsyncClient.

Usage:
    async with AsyncHttpClient(base_url="...", token="...") as client:
        response = await client.get("/api/Product/ABC123")

For GUI applications using Qt/PySide6, use with qasync:
    from qasync import QEventLoop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
"""
from typing import Optional, Dict, Any, AsyncIterator
from contextlib import asynccontextmanager
import asyncio
import time
import httpx
import json
import logging

from .exceptions import (
    ConnectionError,
    TimeoutError,
    PyWATSError,
    WatsApiError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    ServerError,
)
from .throttle import RateLimiter, get_default_limiter
from .retry import RetryConfig, should_retry
from .client import Response  # Reuse the Response model

logger = logging.getLogger(__name__)


class AsyncHttpClient:
    """
    Async HTTP client with Basic authentication for WATS API.

    This client handles all async HTTP communication with the WATS server,
    including authentication, request/response handling, and error management.
    
    Example:
        >>> async with AsyncHttpClient(base_url="https://wats.example.com", token="...") as client:
        ...     response = await client.get("/api/Product/ABC123")
        ...     print(response.data)
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        rate_limiter: Optional[RateLimiter] = None,
        enable_throttling: bool = True,
        retry_config: Optional[RetryConfig] = None,
    ):
        """
        Initialize the async HTTP client.

        Args:
            base_url: Base URL of the WATS server
            token: Base64 encoded authentication token for Basic auth
            timeout: Request timeout in seconds (default: 30)
            verify_ssl: Whether to verify SSL certificates (default: True)
            rate_limiter: Custom RateLimiter instance (default: global limiter)
            enable_throttling: Enable/disable rate limiting (default: True)
            retry_config: Retry configuration (default: RetryConfig())
        """
        # Clean up base URL
        self.base_url = base_url.rstrip("/")
        if self.base_url.endswith("/api"):
            self.base_url = self.base_url[:-4]

        self.token = token
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # Rate limiter
        if rate_limiter is not None:
            self._rate_limiter = rate_limiter
        elif enable_throttling:
            self._rate_limiter = get_default_limiter()
        else:
            self._rate_limiter = RateLimiter(enabled=False)
        
        # Retry configuration
        self._retry_config = retry_config if retry_config is not None else RetryConfig()

        # Default headers
        self._headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Async httpx client (created on first use or via context manager)
        self._client: Optional[httpx.AsyncClient] = None

        # Trace capture stack
        self._trace_stack: list[list[dict[str, Any]]] = []

    @asynccontextmanager
    async def capture_traces(self) -> AsyncIterator[list[dict[str, Any]]]:
        """Capture HTTP request/response traces within this async context."""
        bucket: list[dict[str, Any]] = []
        self._trace_stack.append(bucket)
        try:
            yield bucket
        finally:
            if self._trace_stack and self._trace_stack[-1] is bucket:
                self._trace_stack.pop()

    def _emit_trace(self, trace: dict[str, Any]) -> None:
        """Append trace to all active capture buckets."""
        for bucket in self._trace_stack:
            bucket.append(trace)

    @staticmethod
    def _bounded_json(value: Any, *, max_chars: int = 10_000) -> Any:
        """Return a JSON-serializable structure, bounded for debug surfaces."""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            try:
                text = json.dumps(value, ensure_ascii=False, default=str)
            except Exception:
                return {"_unserializable": True, "type": type(value).__name__}
            if len(text) <= max_chars:
                return value
            return {"_truncated": True, "_original_chars": len(text), "_preview": text[:max_chars]}
        if isinstance(value, (bytes, bytearray)):
            size = len(value)
            if size <= max_chars:
                return value.decode("utf-8", errors="replace")
            return {"_truncated": True, "_original_bytes": size, "_preview": value[:max_chars].decode("utf-8", errors="replace")}
        if isinstance(value, str):
            if len(value) <= max_chars:
                return value
            return {"_truncated": True, "_original_chars": len(value), "_preview": value[:max_chars]}
        return value

    @property
    def rate_limiter(self) -> RateLimiter:
        """Get the rate limiter instance."""
        return self._rate_limiter

    @property
    def retry_config(self) -> RetryConfig:
        """Get the retry configuration instance."""
        return self._retry_config
    
    @retry_config.setter
    def retry_config(self, value: RetryConfig) -> None:
        """Set the retry configuration instance."""
        self._retry_config = value

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async httpx client with connection pooling."""
        if self._client is None:
            # Configure connection pooling for better performance
            limits = httpx.Limits(
                max_connections=100,  # Total connection pool size
                max_keepalive_connections=20,  # Keep connections alive
                keepalive_expiry=30.0  # Keep-alive timeout in seconds
            )
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
                follow_redirects=True,
                limits=limits,  # Enable connection pooling
                http2=True  # Enable HTTP/2 for multiplexing
            )
        return self._client

    async def close(self) -> None:
        """Close the async HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "AsyncHttpClient":
        await self._get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def _handle_response(self, response: httpx.Response) -> Response:
        """
        Handle HTTP response and convert to Response object.
        Does NOT raise exceptions - that's handled by the caller if needed.
        """
        data = None
        try:
            if response.content:
                data = response.json()
        except (json.JSONDecodeError, ValueError):
            data = response.text if response.text else None

        return Response(
            status_code=response.status_code,
            data=data,
            headers=dict(response.headers),
            raw=response.content
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Any = None,
        headers: Optional[Dict[str, str]] = None,
        retry: Optional[bool] = None
    ) -> Response:
        """
        Make an async HTTP request with automatic retry for transient failures.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/api/Product/ABC123")
            params: Query parameters
            data: Request body data (will be JSON encoded)
            headers: Additional headers to merge with defaults
            retry: Override retry behavior (True/False/None for default)

        Returns:
            Response object
        """
        retry_enabled = retry if retry is not None else self._retry_config.enabled
        max_attempts = self._retry_config.max_attempts if retry_enabled else 1
        
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"

        request_headers = self._headers.copy()
        if headers:
            request_headers.update(headers)

        kwargs: Dict[str, Any] = {
            "method": method,
            "url": endpoint,
            "headers": request_headers
        }

        if params:
            kwargs["params"] = {k: v for k, v in params.items() if v is not None}

        if data is not None:
            if isinstance(data, (dict, list)):
                kwargs["json"] = data
            else:
                kwargs["content"] = data

        full_url = f"{self.base_url}{endpoint}"
        
        last_exception: Optional[Exception] = None
        last_response: Optional[Response] = None
        
        client = await self._get_client()
        
        for attempt in range(max_attempts):
            # Rate limiting (sync for now - could be made async)
            self._rate_limiter.acquire()
            
            started = time.perf_counter()
            try:
                response = await client.request(**kwargs)
                duration_ms = (time.perf_counter() - started) * 1000.0
                
                self._emit_trace({
                    "method": method,
                    "url": full_url,
                    "params": self._bounded_json(kwargs.get("params")),
                    "json": self._bounded_json(kwargs.get("json")),
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "response_bytes": len(response.content or b""),
                    "attempt": attempt + 1,
                })
                
                parsed_response = self._handle_response(response)
                
                # Check if we should retry this status code
                if retry_enabled and self._retry_config.should_retry_status(response.status_code):
                    should_retry_flag, delay = should_retry(
                        self._retry_config, method, attempt, response=parsed_response
                    )
                    if should_retry_flag:
                        self._retry_config._total_retries += 1
                        self._retry_config._total_retry_time += delay
                        logger.info(
                            f"Retry {attempt + 1}/{max_attempts} for {method} {endpoint} "
                            f"after {delay:.2f}s (HTTP {response.status_code})"
                        )
                        await asyncio.sleep(delay)
                        last_response = parsed_response
                        continue
                
                return parsed_response
                
            except httpx.ConnectError as e:
                last_exception = ConnectionError(f"Failed to connect to {self.base_url}: {e}")
                
                if retry_enabled:
                    should_retry_flag, delay = should_retry(
                        self._retry_config, method, attempt, exception=last_exception
                    )
                    if should_retry_flag:
                        self._retry_config._total_retries += 1
                        self._retry_config._total_retry_time += delay
                        logger.info(
                            f"Retry {attempt + 1}/{max_attempts} for {method} {endpoint} "
                            f"after {delay:.2f}s (ConnectionError)"
                        )
                        await asyncio.sleep(delay)
                        continue
                
                raise last_exception
                
            except httpx.TimeoutException as e:
                last_exception = TimeoutError(f"Request timed out: {e}")
                
                if retry_enabled:
                    should_retry_flag, delay = should_retry(
                        self._retry_config, method, attempt, exception=last_exception
                    )
                    if should_retry_flag:
                        self._retry_config._total_retries += 1
                        self._retry_config._total_retry_time += delay
                        logger.info(
                            f"Retry {attempt + 1}/{max_attempts} for {method} {endpoint} "
                            f"after {delay:.2f}s (TimeoutError)"
                        )
                        await asyncio.sleep(delay)
                        continue
                
                raise last_exception
                
            except Exception as e:
                raise PyWATSError(f"HTTP request failed: {e}")
        
        if last_exception:
            raise last_exception
        if last_response:
            return last_response
        
        raise PyWATSError("Unexpected state: no response or exception after retries")

    # Convenience methods
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Response:
        """Make an async GET request."""
        return await self._make_request("GET", endpoint, params=params, **kwargs)

    async def post(
        self,
        endpoint: str,
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Response:
        """Make an async POST request."""
        return await self._make_request("POST", endpoint, data=data, params=params, **kwargs)

    async def put(
        self,
        endpoint: str,
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Response:
        """Make an async PUT request."""
        return await self._make_request("PUT", endpoint, data=data, params=params, **kwargs)

    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Response:
        """Make an async DELETE request."""
        return await self._make_request("DELETE", endpoint, params=params, **kwargs)

    async def patch(
        self,
        endpoint: str,
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Response:
        """Make an async PATCH request."""
        return await self._make_request("PATCH", endpoint, data=data, params=params, **kwargs)
