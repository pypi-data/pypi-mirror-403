"""AsyncWATS - Async Main API Class

The main async entry point for the pyWATS library.
Use this for GUI applications (with qasync) or async code.

For synchronous scripts, use the pyWATS class instead.
"""
import logging
from typing import Optional, TYPE_CHECKING

from .core.async_client import AsyncHttpClient
from .core.station import Station, StationRegistry
from .core.retry import RetryConfig
from .core.throttle import RateLimiter
from .core.exceptions import ErrorMode, ErrorHandler

if TYPE_CHECKING:
    from .core.config import APISettings

# Import async services
from .domains.product import AsyncProductService, AsyncProductRepository
from .domains.asset import AsyncAssetService, AsyncAssetRepository
from .domains.production import AsyncProductionService, AsyncProductionRepository
from .domains.report import AsyncReportService, AsyncReportRepository
from .domains.software import AsyncSoftwareService, AsyncSoftwareRepository
from .domains.analytics import AsyncAnalyticsService, AsyncAnalyticsRepository
from .domains.rootcause import AsyncRootCauseService, AsyncRootCauseRepository
from .domains.scim import AsyncScimService, AsyncScimRepository
from .domains.process import AsyncProcessService, AsyncProcessRepository

logger = logging.getLogger(__name__)


class AsyncWATS:
    """
    Async pyWATS API class.
    
    Provides async access to all WATS functionality through module properties:
    - product: Product management
    - asset: Asset management
    - production: Production/unit management
    - report: Report querying and submission
    - software: Software distribution
    - analytics: Yield statistics, KPIs, and failure analysis
    - rootcause: Ticketing system for issue collaboration
    - scim: SCIM user provisioning
    - process: Process/operation management
    
    For GUI applications using Qt/PySide6, use with qasync:
    
        import asyncio
        from qasync import QEventLoop
        from PySide6.QtWidgets import QApplication
        from pywats import AsyncWATS
        
        app = QApplication(sys.argv)
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        async with AsyncWATS(base_url="...", token="...") as api:
            products = await api.product.get_products()
        
        with loop:
            loop.run_forever()
    
    For async scripts:
    
        import asyncio
        from pywats import AsyncWATS
        
        async def main():
            async with AsyncWATS(base_url="...", token="...") as api:
                products = await api.product.get_products()
                print(products)
        
        asyncio.run(main())
    
    Authentication:
        The API uses Basic authentication. The token should be a Base64-encoded
        string in the format "username:password". The Authorization header will
        be sent as: "Basic <token>"
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        station: Optional[Station] = None,
        timeout: Optional[float] = None,
        verify_ssl: Optional[bool] = None,
        error_mode: Optional[ErrorMode] = None,
        rate_limiter: Optional[RateLimiter] = None,
        enable_throttling: bool = True,
        retry_config: Optional[RetryConfig] = None,
        retry_enabled: bool = True,
        instance_id: str = "default",
        settings: Optional['APISettings'] = None,
    ):
        """
        Initialize the async pyWATS API.
        
        Credentials can be provided explicitly, via settings injection, or 
        auto-discovered from a running pyWATS Client service.
        
        Configuration priority (highest to lowest):
        1. Explicit parameters (base_url, token, timeout, etc.)
        2. Injected settings object
        3. Auto-discovered from running service
        4. Built-in constant defaults
        
        Args:
            base_url: Base URL of the WATS server (e.g., "https://your-wats.com")
                     If None, attempts to discover from running service.
            token: API token (Base64-encoded credentials)
                   If None, attempts to discover from running service.
            station: Default station configuration for reports
            timeout: Request timeout in seconds. If None, uses settings or default (30).
            verify_ssl: Whether to verify SSL certificates. If None, uses settings or default (True).
            error_mode: Error handling mode (STRICT or LENIENT). Default is STRICT.
            rate_limiter: Custom RateLimiter instance (default: global limiter)
            enable_throttling: Enable/disable rate limiting (default: True)
            retry_config: Custom retry configuration. If None, uses defaults.
            retry_enabled: Enable/disable retry (default: True).
            instance_id: pyWATS Client instance ID for auto-discovery (default: "default")
            settings: APISettings object for injected configuration. Settings from this
                     object are used as defaults, but can be overridden by explicit parameters.
        
        Raises:
            ValueError: If credentials not provided and service discovery fails
            
        Examples:
            # Explicit credentials
            async with AsyncWATS(base_url="https://wats.com", token="abc123") as api:
                products = await api.product.get_products()
            
            # Auto-discover from running service
            async with AsyncWATS() as api:  # Uses default instance
                products = await api.product.get_products()
        """
        # Import APISettings for type checking and defaults
        from .core.config import APISettings, get_default_settings
        
        # Use injected settings or get defaults (no file I/O)
        if settings is None:
            settings = get_default_settings()
        
        # Auto-discover credentials from running service if not provided
        if not base_url or not token:
            discovered = self._discover_credentials(instance_id)
            if discovered:
                base_url = base_url or discovered["base_url"]
                token = token or discovered["token"]
                logger.info(f"Auto-discovered credentials from service instance '{instance_id}'")
            elif not base_url or not token:
                raise ValueError(
                    "Credentials required. Either provide base_url and token, "
                    f"or ensure pyWATS Client service is running (instance: {instance_id})"
                )
        
        # Apply configuration: explicit params > settings > defaults
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout if timeout is not None else settings.timeout_seconds
        self._verify_ssl = verify_ssl if verify_ssl is not None else settings.verify_ssl
        
        # Error mode: explicit > settings > default
        if error_mode is not None:
            self._error_mode = error_mode
        elif settings.error_mode:
            self._error_mode = ErrorMode(settings.error_mode)
        else:
            self._error_mode = ErrorMode.STRICT
        self._error_handler = ErrorHandler(self._error_mode)
        
        # Store settings for domain-specific config access
        self._settings = settings
        
        # Retry configuration
        if retry_config is not None:
            self._retry_config = retry_config
        elif not retry_enabled:
            self._retry_config = RetryConfig(enabled=False)
        else:
            self._retry_config = RetryConfig()
        
        # Station configuration
        self._station: Optional[Station] = station
        self._station_registry = StationRegistry()
        if station:
            self._station_registry.set_default(station)
        
        # Initialize async HTTP client
        self._http_client = AsyncHttpClient(
            base_url=self._base_url,
            token=self._token,
            timeout=self._timeout,
            verify_ssl=self._verify_ssl,
            rate_limiter=rate_limiter,
            enable_throttling=enable_throttling,
            retry_config=self._retry_config,
        )
        
        # Service instances (lazy initialization)
        self._product: Optional[AsyncProductService] = None
        self._asset: Optional[AsyncAssetService] = None
        self._production: Optional[AsyncProductionService] = None
        self._report: Optional[AsyncReportService] = None
        self._software: Optional[AsyncSoftwareService] = None
        self._analytics: Optional[AsyncAnalyticsService] = None
        self._rootcause: Optional[AsyncRootCauseService] = None
        self._scim: Optional[AsyncScimService] = None
        self._process: Optional[AsyncProcessService] = None
    
    @staticmethod
    def _discover_credentials(instance_id: str = "default") -> Optional[dict]:
        """
        Attempt to discover credentials from running pyWATS Client service.
        
        Args:
            instance_id: Instance ID to connect to (defaults to "default")
            
        Returns:
            Dictionary with 'base_url' and 'token' or None if not found
        """
        try:
            # Import here to avoid circular dependency
            from pywats_client.service.ipc_client import ServiceIPCClient
            
            client = ServiceIPCClient(instance_id)
            if client.connect(timeout_ms=500):
                credentials = client.get_credentials()
                client.disconnect()
                
                if credentials and credentials.get("base_url") and credentials.get("token"):
                    return credentials
        except ImportError:
            # pywats_client not installed - that's ok
            pass
        except Exception as e:
            logger.debug(f"Service discovery failed: {e}")
        
        return None
    
    # -------------------------------------------------------------------------
    # Configuration Access
    # -------------------------------------------------------------------------
    
    @property
    def settings(self) -> 'APISettings':
        """
        Get the API settings being used.
        
        Returns:
            APISettings instance (pure model, no file I/O)
        """
        return self._settings
    
    # -------------------------------------------------------------------------
    # Connection Testing
    # -------------------------------------------------------------------------
    
    async def test_connection(self) -> bool:
        """
        Test if the connection to the WATS server is working.
        
        Makes a simple API call to verify connectivity.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            version = await self.analytics.get_version()
            return version is not None
        except Exception as e:
            logger.debug(f"Connection test failed: {e}")
            return False
    
    async def get_version(self) -> Optional[str]:
        """
        Get WATS server version information.
        
        Returns:
            Version string (e.g., "24.1.0") or None if not available
        """
        return await self.analytics.get_version()
    
    # -------------------------------------------------------------------------
    # Context Manager Support
    # -------------------------------------------------------------------------
    
    async def __aenter__(self) -> "AsyncWATS":
        """Enter async context manager."""
        await self._http_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self.close()
    
    async def close(self) -> None:
        """Close the async HTTP client."""
        await self._http_client.close()
    
    # -------------------------------------------------------------------------
    # Station Configuration
    # -------------------------------------------------------------------------
    
    @property
    def stations(self) -> StationRegistry:
        """Access the station registry for multi-station configurations."""
        return self._station_registry
    
    def _get_station(self) -> Optional[Station]:
        """Get the current active station."""
        return self._station_registry.active or self._station
    
    # -------------------------------------------------------------------------
    # Module Properties
    # -------------------------------------------------------------------------
    
    @property
    def product(self) -> AsyncProductService:
        """
        Access product management operations.
        
        Returns:
            AsyncProductService instance
        """
        if self._product is None:
            repo = AsyncProductRepository(
                http_client=self._http_client, 
                base_url=self._base_url,
                error_handler=self._error_handler
            )
            self._product = AsyncProductService(repo, self._base_url)
        return self._product
    
    @property
    def asset(self) -> AsyncAssetService:
        """
        Access asset management operations.
        
        Returns:
            AsyncAssetService instance
        """
        if self._asset is None:
            repo = AsyncAssetRepository(
                http_client=self._http_client, 
                base_url=self._base_url,
                error_handler=self._error_handler
            )
            self._asset = AsyncAssetService(repo, self._base_url)
        return self._asset
    
    @property
    def production(self) -> AsyncProductionService:
        """
        Access production/unit management operations.
        
        Includes operations for:
        - Units: create, get, update, verify
        - Batches: create, get, update
        - Phases: get_phases, get_phase
        - Serial numbers: get_serial_number_types
        
        Returns:
            AsyncProductionService instance
        """
        if self._production is None:
            repo = AsyncProductionRepository(
                http_client=self._http_client, 
                base_url=self._base_url,
                error_handler=self._error_handler
            )
            self._production = AsyncProductionService(repo, self._base_url)
        return self._production
    
    @property
    def report(self) -> AsyncReportService:
        """
        Access report operations.
        
        Returns:
            AsyncReportService instance
        """
        if self._report is None:
            repo = AsyncReportRepository(
                self._http_client, 
                self._error_handler
            )
            self._report = AsyncReportService(repo)
        return self._report
    
    @property
    def software(self) -> AsyncSoftwareService:
        """
        Access software distribution operations.
        
        Returns:
            AsyncSoftwareService instance
        """
        if self._software is None:
            repo = AsyncSoftwareRepository(
                self._http_client, 
                self._error_handler
            )
            self._software = AsyncSoftwareService(repo)
        return self._software
    
    @property
    def analytics(self) -> AsyncAnalyticsService:
        """
        Access yield statistics, KPIs, and failure analysis.
        
        Provides high-level async operations for:
        - Yield statistics (dynamic yield, volume yield, worst yield)
        - Failure analysis (top failed steps, test step analysis)
        - Production metrics (OEE, measurements)
        - Report queries (serial number history, UUT/UUR reports)
        
        Returns:
            AsyncAnalyticsService instance
        """
        if self._analytics is None:
            repo = AsyncAnalyticsRepository(
                http_client=self._http_client, 
                error_handler=self._error_handler,
                base_url=self._base_url
            )
            self._analytics = AsyncAnalyticsService(repo)
        return self._analytics
    
    @property
    def rootcause(self) -> AsyncRootCauseService:
        """
        Access RootCause ticketing operations.
        
        The RootCause module provides a ticketing system for 
        collaboration on issue tracking and resolution.
        
        Returns:
            AsyncRootCauseService instance
        """
        if self._rootcause is None:
            repo = AsyncRootCauseRepository(
                self._http_client, 
                self._error_handler
            )
            self._rootcause = AsyncRootCauseService(repo)
        return self._rootcause
    
    @property
    def scim(self) -> AsyncScimService:
        """
        Access SCIM user provisioning operations.
        
        SCIM (System for Cross-domain Identity Management) provides
        automatic user provisioning from Azure Active Directory to WATS.
        
        Returns:
            AsyncScimService instance
        """
        if self._scim is None:
            repo = AsyncScimRepository(
                self._http_client, 
                self._error_handler
            )
            self._scim = AsyncScimService(repo)
        return self._scim
    
    @property
    def process(self) -> AsyncProcessService:
        """
        Access process/operation management.
        
        Returns:
            AsyncProcessService instance
        """
        if self._process is None:
            repo = AsyncProcessRepository(
                http_client=self._http_client, 
                error_handler=self._error_handler,
                base_url=self._base_url
            )
            self._process = AsyncProcessService(repo)
        return self._process
    
    # -------------------------------------------------------------------------
    # HTTP Client Access (advanced usage)
    # -------------------------------------------------------------------------
    
    @property
    def http_client(self) -> AsyncHttpClient:
        """
        Access the underlying async HTTP client.
        
        This is for advanced usage when you need to make custom API calls
        not covered by the service modules.
        
        Returns:
            AsyncHttpClient instance
        """
        return self._http_client
