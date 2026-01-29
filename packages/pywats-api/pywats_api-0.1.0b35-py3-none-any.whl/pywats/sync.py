"""
Synchronous wrapper for async pyWATS API.

This module provides a synchronous interface to the async pyWATS API,
making it easy to use in scripts, test frameworks (like pytest without 
async fixtures), and other environments that don't have an event loop.

Usage:
    from pywats.sync import SyncWATS
    
    client = SyncWATS(base_url="https://wats.example.com", token="...")
    
    # Use just like the sync API
    unit = client.production.get_unit("SN-001", "PN-001")
    products = client.product.get_products()
    
    # Cleanup when done
    client.close()

Or with context manager:
    with SyncWATS(base_url="...", token="...") as client:
        unit = client.production.get_unit("SN-001", "PN-001")
"""
import asyncio
from typing import Optional, Any, TypeVar, Callable, Coroutine
from functools import wraps
import logging
import inspect

from .core.async_client import AsyncHttpClient
from .core.retry import RetryConfig
from .core.throttle import RateLimiter
from .core.exceptions import ErrorMode, ErrorHandler

logger = logging.getLogger(__name__)

T = TypeVar('T')


def _run_sync(coro: Coroutine[Any, Any, T]) -> T:
    """Run a coroutine synchronously, creating an event loop if needed."""
    try:
        loop = asyncio.get_running_loop()
        # If there's already a running loop, we can't use run_until_complete
        # This would happen in Jupyter notebooks or async contexts
        raise RuntimeError(
            "Cannot use SyncWATS from within an async context. "
            "Use the async API directly instead."
        )
    except RuntimeError:
        # No running loop - this is the normal case for sync usage
        pass
    
    # Create a new event loop for this call
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class SyncServiceWrapper:
    """
    Generic synchronous wrapper for async services.
    
    Automatically wraps all async methods of the underlying service
    to run synchronously using _run_sync.
    """
    
    def __init__(self, async_service: Any):
        """
        Initialize with an async service instance.
        
        Args:
            async_service: Any async service with async methods
        """
        self._async = async_service
    
    def __getattr__(self, name: str) -> Any:
        """
        Dynamically wrap async methods as sync methods.
        
        Args:
            name: Attribute name to access
            
        Returns:
            Wrapped sync method or original attribute
        """
        attr = getattr(self._async, name)
        
        # If it's a coroutine function (async method), wrap it
        if inspect.iscoroutinefunction(attr):
            @wraps(attr)
            def sync_wrapper(*args, **kwargs):
                return _run_sync(attr(*args, **kwargs))
            return sync_wrapper
        
        # Otherwise return as-is (properties, regular methods, etc.)
        return attr


class SyncWATS:
    """
    Synchronous wrapper for async pyWATS API.
    
    Provides a blocking interface that internally uses the async API
    with automatic event loop management. All domain services are
    available with the same API as the async version.
    
    Example:
        client = SyncWATS(base_url="...", token="...")
        
        # All domains available
        unit = client.production.get_unit("SN-001", "PN-001")
        products = client.product.get_products()
        assets = client.asset.get_assets()
        yield_data = client.analytics.get_dynamic_yield(filter)
        tickets = client.rootcause.get_tickets()
        
        client.close()
    
    Or with context manager:
        with SyncWATS(base_url="...", token="...") as client:
            unit = client.production.get_unit("SN-001", "PN-001")
    """
    
    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        error_mode: ErrorMode = ErrorMode.STRICT,
        rate_limiter: Optional[RateLimiter] = None,
        enable_throttling: bool = True,
        retry_config: Optional[RetryConfig] = None,
        retry_enabled: bool = True,
    ):
        """
        Initialize the sync WATS client.
        
        Args:
            base_url: Base URL of the WATS server
            token: Base64 encoded authentication token
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            error_mode: Error handling mode (STRICT or LENIENT)
            rate_limiter: Custom rate limiter instance
            enable_throttling: Enable/disable rate limiting
            retry_config: Retry configuration
            retry_enabled: Enable/disable retry
        """
        self._base_url = base_url.rstrip("/")
        self._error_mode = error_mode
        self._error_handler = ErrorHandler(error_mode)
        
        # Retry configuration
        if retry_config is not None:
            self._retry_config = retry_config
        elif not retry_enabled:
            self._retry_config = RetryConfig(enabled=False)
        else:
            self._retry_config = RetryConfig()
        
        self._http_client = AsyncHttpClient(
            base_url=base_url,
            token=token,
            timeout=timeout,
            verify_ssl=verify_ssl,
            rate_limiter=rate_limiter,
            enable_throttling=enable_throttling,
            retry_config=self._retry_config,
        )
        
        # Lazy-initialized services
        self._product: Optional[SyncServiceWrapper] = None
        self._asset: Optional[SyncServiceWrapper] = None
        self._production: Optional[SyncServiceWrapper] = None
        self._report: Optional[SyncServiceWrapper] = None
        self._software: Optional[SyncServiceWrapper] = None
        self._analytics: Optional[SyncServiceWrapper] = None
        self._rootcause: Optional[SyncServiceWrapper] = None
        self._scim: Optional[SyncServiceWrapper] = None
        self._process: Optional[SyncServiceWrapper] = None
    
    @property
    def product(self) -> SyncServiceWrapper:
        """Access product service."""
        if self._product is None:
            from .domains.product import AsyncProductRepository, AsyncProductService
            repo = AsyncProductRepository(
                http_client=self._http_client, 
                base_url=self._base_url,
                error_handler=self._error_handler
            )
            async_service = AsyncProductService(repo, self._base_url)
            self._product = SyncServiceWrapper(async_service)
        return self._product
    
    @property
    def asset(self) -> SyncServiceWrapper:
        """Access asset service."""
        if self._asset is None:
            from .domains.asset import AsyncAssetRepository, AsyncAssetService
            repo = AsyncAssetRepository(
                http_client=self._http_client, 
                base_url=self._base_url,
                error_handler=self._error_handler
            )
            async_service = AsyncAssetService(repo, self._base_url)
            self._asset = SyncServiceWrapper(async_service)
        return self._asset
    
    @property
    def production(self) -> SyncServiceWrapper:
        """Access production service."""
        if self._production is None:
            from .domains.production import AsyncProductionRepository, AsyncProductionService
            repo = AsyncProductionRepository(
                http_client=self._http_client, 
                base_url=self._base_url,
                error_handler=self._error_handler
            )
            async_service = AsyncProductionService(repo, self._base_url)
            self._production = SyncServiceWrapper(async_service)
        return self._production
    
    @property
    def report(self) -> SyncServiceWrapper:
        """Access report service."""
        if self._report is None:
            from .domains.report import AsyncReportRepository, AsyncReportService
            repo = AsyncReportRepository(self._http_client, self._error_handler)
            async_service = AsyncReportService(repo)
            self._report = SyncServiceWrapper(async_service)
        return self._report
    
    @property
    def software(self):
        """Access software service."""
        if self._software is None:
            from .domains.software import AsyncSoftwareRepository, SoftwareService
            repo = AsyncSoftwareRepository(self._http_client, self._error_handler)
            self._software = SoftwareService.from_repository(repo)
        return self._software
    
    @property
    def analytics(self) -> SyncServiceWrapper:
        """Access analytics service."""
        if self._analytics is None:
            from .domains.analytics import AsyncAnalyticsRepository, AsyncAnalyticsService
            repo = AsyncAnalyticsRepository(
                http_client=self._http_client, 
                error_handler=self._error_handler,
                base_url=self._base_url
            )
            async_service = AsyncAnalyticsService(repo)
            self._analytics = SyncServiceWrapper(async_service)
        return self._analytics
    
    @property
    def rootcause(self):
        """Access rootcause (ticketing) service."""
        if self._rootcause is None:
            from .domains.rootcause import AsyncRootCauseRepository, RootCauseService
            repo = AsyncRootCauseRepository(self._http_client, self._error_handler)
            self._rootcause = RootCauseService.from_repository(repo)
        return self._rootcause
    
    @property
    def scim(self):
        """Access SCIM (user provisioning) service."""
        if self._scim is None:
            from .domains.scim import AsyncScimRepository, ScimService
            repo = AsyncScimRepository(self._http_client, self._error_handler)
            self._scim = ScimService.from_repository(repo)
        return self._scim
    
    @property
    def process(self) -> SyncServiceWrapper:
        """Access process service."""
        if self._process is None:
            from .domains.process import AsyncProcessRepository, AsyncProcessService
            repo = AsyncProcessRepository(
                http_client=self._http_client, 
                error_handler=self._error_handler,
                base_url=self._base_url
            )
            async_service = AsyncProcessService(repo)
            self._process = SyncServiceWrapper(async_service)
        return self._process
    
    def close(self) -> None:
        """Close the HTTP client."""
        _run_sync(self._http_client.close())
    
    def __enter__(self) -> "SyncWATS":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
