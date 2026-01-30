"""pyWATS - Main API Class

The main entry point for the pyWATS library.
Provides a synchronous interface by wrapping async services.
"""
import asyncio
import logging
import inspect
import threading
from typing import Optional, Any, TypeVar, Coroutine, TYPE_CHECKING
from functools import wraps

from .core.async_client import AsyncHttpClient
from .core.station import Station, StationRegistry
from .core.retry import RetryConfig
from .core.exceptions import ErrorMode, ErrorHandler

if TYPE_CHECKING:
    from .core.config import APISettings

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Thread-local storage for persistent event loops
_thread_local = threading.local()


def _get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """Get or create a persistent event loop for the current thread."""
    loop = getattr(_thread_local, 'loop', None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _thread_local.loop = loop
    return loop


def _run_sync(coro: Coroutine[Any, Any, T]) -> T:
    """Run a coroutine synchronously using a persistent event loop."""
    try:
        asyncio.get_running_loop()
        # If there's already a running loop, we can't use run_until_complete
        raise RuntimeError(
            "Cannot use pyWATS from within an async context. "
            "Use AsyncWATS instead."
        )
    except RuntimeError:
        # No running loop - this is the normal case for sync usage
        pass
    
    # Use a persistent event loop for this thread
    loop = _get_or_create_event_loop()
    return loop.run_until_complete(coro)


class SyncServiceWrapper:
    """
    Generic synchronous wrapper for async services.
    
    Automatically wraps all async methods of the underlying service
    to run synchronously.
    """
    
    def __init__(self, async_service: Any) -> None:
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


class SyncProductServiceWrapper(SyncServiceWrapper):
    """
    Specialized sync wrapper for AsyncProductService.
    
    Handles special cases like BoxBuildTemplate that need additional wrapping.
    """
    
    def __getattr__(self, name: str) -> Any:
        """Wrap async methods, with special handling for box build."""
        attr = getattr(self._async, name)
        
        # Special handling for box build methods
        if name in ('get_box_build_template', 'get_box_build'):
            @wraps(attr)
            def box_build_wrapper(*args, **kwargs):
                # Run async method
                async_template = _run_sync(attr(*args, **kwargs))
                # Wrap result in sync wrapper
                from .domains.product.sync_box_build import SyncBoxBuildTemplate
                return SyncBoxBuildTemplate(async_template)
            return box_build_wrapper
        
        # Default handling
        if inspect.iscoroutinefunction(attr):
            @wraps(attr)
            def sync_wrapper(*args, **kwargs):
                return _run_sync(attr(*args, **kwargs))
            return sync_wrapper
        
        return attr


class pyWATS:
    """
    Main pyWATS API class.
    
    Provides access to all WATS functionality through module properties:
    - product: Product management
    - asset: Asset management
    - production: Production/unit management
    - report: Report querying and submission
    - software: Software distribution
    - analytics: Yield statistics, KPIs, and failure analysis (also available as 'app')
    - rootcause: Ticketing system for issue collaboration
    - scim: SCIM user provisioning
    - process: Process/operation management
    
    Station Configuration:
        pyWATS supports a Station concept for managing test station identity.
        A Station encapsulates: name (machineName), location, and purpose.
        
        Single station mode (most common):
            api = pyWATS(
                base_url="https://your-wats-server.com",
                token="your-api-token",
                station=Station("TEST-STATION-01", "Lab A", "Production")
            )
        
        Multi-station mode (hub):
            api = pyWATS(base_url="...", token="...")
            api.stations.add("line-1", Station("PROD-LINE-1", "Building A", "Production"))
            api.stations.add("line-2", Station("PROD-LINE-2", "Building A", "Production"))
            api.stations.set_active("line-1")
    
    Usage:
        from pywats import pyWATS
        
        # Initialize the API
        api = pyWATS(
            base_url="https://your-wats-server.com",
            token="your-api-token"
        )
        
        # Access product operations
        products = api.product.get_products()
        product = api.product.get_product("PART-001")
        
        # Access report operations
        headers = api.report.query_uut_headers()
        report = api.report.get_report("report-uuid")
        
        # Access statistics
        yield_data = api.analytics.get_dynamic_yield(filter)
    
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
        timeout: Optional[int] = None,
        verify_ssl: Optional[bool] = None,
        error_mode: Optional[ErrorMode] = None,
        retry_config: Optional[RetryConfig] = None,
        retry_enabled: bool = True,
        instance_id: str = "default",
        settings: Optional['APISettings'] = None,
    ) -> None:
        """
        Initialize the pyWATS API.
        
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
            station: Default station configuration for reports. If provided,
                     this station's name, location, and purpose will be used
                     when creating reports (unless overridden).
            timeout: Request timeout in seconds. If None, uses settings or default (30).
            verify_ssl: Whether to verify SSL certificates. If None, uses settings or default (True).
            error_mode: Error handling mode (STRICT or LENIENT). If None, uses settings or default (STRICT).
                - STRICT: Raises exceptions for 404/empty responses
                - LENIENT: Returns None for 404/empty responses
            retry_config: Custom retry configuration. If None, uses defaults.
            retry_enabled: Enable/disable retry (default: True). 
                Shorthand for RetryConfig(enabled=False).
            instance_id: pyWATS Client instance ID for auto-discovery (default: "default")
            settings: APISettings object for injected configuration. Settings from this
                     object are used as defaults, but can be overridden by explicit parameters.
        
        Raises:
            ValueError: If credentials not provided and service discovery fails
        
        Examples:
            # Explicit credentials
            api = pyWATS(base_url="https://wats.com", token="abc123")
            
            # Auto-discover from running service
            api = pyWATS()  # Uses default instance
            api = pyWATS(instance_id="production")  # Specific instance
            
            # With injected settings
            from pywats.core.config import APISettings
            settings = APISettings(timeout_seconds=60, verify_ssl=False)
            api = pyWATS(base_url="...", token="...", settings=settings)
            
            # Client-loaded settings (file-based)
            from pywats_client.core import ConfigManager
            settings = ConfigManager().load()
            api = pyWATS(base_url="...", token="...", settings=settings)
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
        
        # Initialize async HTTP client (used by all services)
        self._http_client = AsyncHttpClient(
            base_url=self._base_url,
            token=self._token,
            timeout=self._timeout,
            verify_ssl=self._verify_ssl,
            retry_config=self._retry_config,
        )
        
        # Service instances (lazy initialization)
        self._product: Optional[SyncServiceWrapper] = None
        self._asset: Optional[SyncServiceWrapper] = None
        self._production: Optional[SyncServiceWrapper] = None
        self._report: Optional[SyncServiceWrapper] = None
        self._software: Optional[SyncServiceWrapper] = None
        self._analytics: Optional[SyncServiceWrapper] = None
        self._rootcause: Optional[SyncServiceWrapper] = None
        self._scim: Optional[SyncServiceWrapper] = None
        self._process: Optional[SyncServiceWrapper] = None
    
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
    # Module Properties
    # -------------------------------------------------------------------------
    
    @property
    def product(self) -> SyncProductServiceWrapper:
        """
        Access product management operations.
        
        Returns:
            SyncProductServiceWrapper around AsyncProductService
        """
        if self._product is None:
            from .domains.product import AsyncProductRepository, AsyncProductService
            repo = AsyncProductRepository(
                http_client=self._http_client, 
                base_url=self._base_url,
                error_handler=self._error_handler
            )
            async_service = AsyncProductService(repo, self._base_url)
            self._product = SyncProductServiceWrapper(async_service)
        return self._product
    
    @property
    def asset(self) -> SyncServiceWrapper:
        """
        Access asset management operations.
        
        Returns:
            SyncServiceWrapper around AsyncAssetService
        """
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
        """
        Access production/unit management operations.
        
        Includes operations for:
        - Unit management (get, create, update)
        - Serial number operations
        - Unit verification
        - Child unit management
        
        Returns:
            SyncServiceWrapper around AsyncProductionService
        """
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
        """
        Access report operations.
        
        Returns:
            SyncServiceWrapper around AsyncReportService
        """
        if self._report is None:
            from .domains.report import AsyncReportRepository, AsyncReportService
            repo = AsyncReportRepository(self._http_client, self._error_handler)
            async_service = AsyncReportService(repo)
            self._report = SyncServiceWrapper(async_service)
        return self._report
    
    @property
    def software(self) -> SyncServiceWrapper:
        """
        Access software distribution operations.
        
        Returns:
            SyncServiceWrapper around AsyncSoftwareService
        """
        if self._software is None:
            from .domains.software import AsyncSoftwareRepository, AsyncSoftwareService
            repo = AsyncSoftwareRepository(
                self._http_client, 
                base_url=self._base_url,
                error_handler=self._error_handler
            )
            async_service = AsyncSoftwareService(repo)
            self._software = SyncServiceWrapper(async_service)
        return self._software
    
    @property
    def analytics(self) -> SyncServiceWrapper:
        """
        Access yield statistics, KPIs, and failure analysis.
        
        Provides high-level operations for:
        - Yield statistics (dynamic yield, volume yield, worst yield)
        - Failure analysis (top failed steps, test step analysis)
        - Production metrics (OEE, measurements)
        - Report queries (serial number history, UUT/UUR reports)
        - Unit flow analysis (internal API)
        - Measurement/step drill-down (internal API)
        
        Example:
            >>> # Get yield for a product
            >>> yield_data = api.analytics.get_dynamic_yield(
            ...     WATSFilter(part_number="WIDGET-001", period_count=30)
            ... )
            >>> # Get top failures
            >>> failures = api.analytics.get_top_failed(part_number="WIDGET-001")
        
        Returns:
            SyncServiceWrapper around AsyncAnalyticsService
        """
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
    def rootcause(self) -> SyncServiceWrapper:
        """
        Access RootCause ticketing operations.
        
        The RootCause module provides a ticketing system for 
        collaboration on issue tracking and resolution.
        
        Returns:
            SyncServiceWrapper around AsyncRootCauseService
        """
        if self._rootcause is None:
            from .domains.rootcause import AsyncRootCauseRepository, AsyncRootCauseService
            repo = AsyncRootCauseRepository(self._http_client, self._error_handler)
            async_service = AsyncRootCauseService(repo)
            self._rootcause = SyncServiceWrapper(async_service)
        return self._rootcause
    
    @property
    def scim(self) -> SyncServiceWrapper:
        """
        Access SCIM user provisioning operations.
        
        SCIM (System for Cross-domain Identity Management) provides
        automatic user provisioning from Azure Active Directory to WATS.
        
        Use this for:
        - Generating provisioning tokens for Azure AD configuration
        - Managing SCIM users (create, read, update, delete)
        - Querying users by ID or username
        
        Returns:
            SyncServiceWrapper around AsyncScimService
        """
        if self._scim is None:
            from .domains.scim import AsyncScimRepository, AsyncScimService
            repo = AsyncScimRepository(self._http_client, self._error_handler)
            async_service = AsyncScimService(repo)
            self._scim = SyncServiceWrapper(async_service)
        return self._scim
    
    @property
    def process(self) -> SyncServiceWrapper:
        """
        Access process/operation management.
        
        Processes define the types of operations:
        - Test operations (e.g., End of line test, PCBA test)
        - Repair operations (e.g., Repair, RMA repair)
        - WIP operations (e.g., Assembly)
        
        Example:
            # Get all processes
            processes = api.process.get_processes()
            
            # Get detailed process info
            detailed = api.process.get_processes_detailed()
        
        Returns:
            SyncServiceWrapper around AsyncProcessService
        """
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
    
    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------
    
    @property
    def base_url(self) -> str:
        """Get the configured base URL."""
        return self._base_url
    
    @property
    def timeout(self) -> int:
        """Get the configured request timeout."""
        return self._timeout
    
    @timeout.setter
    def timeout(self, value: int):
        """Set the request timeout."""
        self._timeout = value
        self._http_client.timeout = value
    
    @property
    def error_mode(self) -> ErrorMode:
        """Get the configured error handling mode."""
        return self._error_mode
    
    @property
    def retry_config(self) -> RetryConfig:
        """Get the retry configuration."""
        return self._retry_config
    
    @retry_config.setter
    def retry_config(self, value: RetryConfig) -> None:
        """Set the retry configuration."""
        self._retry_config = value
        self._http_client.retry_config = value
    
    # -------------------------------------------------------------------------
    # Station Configuration
    # -------------------------------------------------------------------------
    
    @property
    def station(self) -> Optional[Station]:
        """
        Get the currently active station.
        
        Returns the active station from the registry, or the default station
        if no active station is set.
        
        Returns:
            Active Station or None
        """
        return self._station_registry.active or self._station
    
    @station.setter
    def station(self, station: Optional[Station]) -> None:
        """
        Set the default station.
        
        This station will be used for reports when no station is explicitly
        specified.
        
        Args:
            station: Station to set as default
        """
        self._station = station
        if station:
            self._station_registry.set_default(station)
    
    @property
    def stations(self) -> StationRegistry:
        """
        Access the station registry for multi-station support.
        
        Use this for scenarios where a single client handles reports
        from multiple stations (hub mode).
        
        Example:
            # Add stations
            api.stations.add("line-1", Station("PROD-LINE-1", "Building A", "Production"))
            api.stations.add("line-2", Station("PROD-LINE-2", "Building A", "Production"))
            
            # Set active station
            api.stations.set_active("line-1")
            
            # Get active station
            station = api.stations.active
        
        Returns:
            StationRegistry instance
        """
        return self._station_registry
    
    def _get_station(self) -> Optional[Station]:
        """
        Internal method to get the current station.
        
        Used by services that need station information.
        
        Returns:
            Current station or None
        """
        return self.station
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def test_connection(self) -> bool:
        """
        Test the connection to the WATS server.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            version = self.analytics.get_version()
            return version is not None
        except Exception as e:
            logger.debug(f"Connection test failed: {e}")
            return False
    
    def get_version(self) -> dict:
        """
        Get WATS server version information.
        
        Returns:
            Version information dictionary
        """
        return self.analytics.get_version()
    
    def close(self) -> None:
        """Close the HTTP client and release resources."""
        _run_sync(self._http_client.close())
    
    def __enter__(self) -> "pyWATS":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
    
    def __repr__(self) -> str:
        """String representation of the pyWATS instance."""
        return f"pyWATS(base_url='{self._base_url}')"
