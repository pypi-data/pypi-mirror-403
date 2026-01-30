"""AsyncWATS - Async Main API Class

The main async entry point for the pyWATS library.
Use this for GUI applications (with qasync) or async code.

For synchronous scripts, use SyncWATS from pywats.sync instead.
"""
import logging
from typing import Optional

from .core.async_client import AsyncHttpClient
from .core.station import Station, StationRegistry
from .core.retry import RetryConfig
from .core.throttle import RateLimiter
from .core.exceptions import ErrorMode, ErrorHandler

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
        base_url: str,
        token: str,
        station: Optional[Station] = None,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        error_mode: ErrorMode = ErrorMode.STRICT,
        rate_limiter: Optional[RateLimiter] = None,
        enable_throttling: bool = True,
        retry_config: Optional[RetryConfig] = None,
        retry_enabled: bool = True,
    ):
        """
        Initialize the async pyWATS API.
        
        Args:
            base_url: Base URL of the WATS server (e.g., "https://your-wats.com")
            token: API token (Base64-encoded credentials)
            station: Default station configuration for reports
            timeout: Request timeout in seconds (default: 30)
            verify_ssl: Whether to verify SSL certificates (default: True)
            error_mode: Error handling mode (STRICT or LENIENT). Default is STRICT.
            rate_limiter: Custom RateLimiter instance (default: global limiter)
            enable_throttling: Enable/disable rate limiting (default: True)
            retry_config: Custom retry configuration. If None, uses defaults.
            retry_enabled: Enable/disable retry (default: True).
        """
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout
        self._verify_ssl = verify_ssl
        self._error_mode = error_mode
        self._error_handler = ErrorHandler(error_mode)
        
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
