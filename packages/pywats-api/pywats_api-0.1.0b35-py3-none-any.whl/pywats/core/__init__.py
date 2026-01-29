"""Core infrastructure for pyWATS.

Contains HTTP client, authentication, error handling, and base exceptions.
"""
from .client import HttpClient, Response
from .async_client import AsyncHttpClient
from .config import (
    APISettings,
    APIConfigManager,
    DomainSettings,
    ProductDomainSettings,
    ReportDomainSettings,
    ProductionDomainSettings,
    ProcessDomainSettings,
    SoftwareDomainSettings,
    AssetDomainSettings,
    RootCauseDomainSettings,
    AppDomainSettings,
    get_api_settings,
    get_api_config_manager,
)
from .exceptions import (
    # Error handling
    ErrorMode,
    ErrorHandler,
    # Exceptions
    PyWATSError,
    WatsApiError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    ServerError,
    ConflictError,
    EmptyResponseError,
    ConnectionError,
    TimeoutError,
)
from .station import (
    Station,
    StationConfig,
    StationRegistry,
    Purpose,
    get_default_station,
)
from .throttle import (
    RateLimiter,
    configure_throttling,
    get_default_limiter,
)
from .retry import (
    RetryConfig,
    RetryExhaustedError,
    RETRYABLE_STATUS_CODES,
    IDEMPOTENT_METHODS,
)
from .batch import (
    batch_execute,
    batch_execute_with_retry,
    BatchConfig,
    collect_successes,
    collect_failures,
    partition_results,
)
from .pagination import (
    paginate,
    paginate_all,
    Paginator,
    PaginationConfig,
)
from .routes import Routes, API

__all__ = [
    # Client
    "HttpClient",
    "Response",
    # Config
    "APISettings",
    "APIConfigManager",
    "DomainSettings",
    "ProductDomainSettings",
    "ReportDomainSettings",
    "ProductionDomainSettings",
    "ProcessDomainSettings",
    "SoftwareDomainSettings",
    "AssetDomainSettings",
    "RootCauseDomainSettings",
    "AppDomainSettings",
    "get_api_settings",
    "get_api_config_manager",
    # Station
    "Station",
    "StationConfig",
    "StationRegistry",
    "Purpose",
    "get_default_station",
    # Rate limiting
    "RateLimiter",
    "configure_throttling",
    "get_default_limiter",
    # Retry
    "RetryConfig",
    "RetryExhaustedError",
    "RETRYABLE_STATUS_CODES",
    "IDEMPOTENT_METHODS",
    # Batch operations
    "batch_execute",
    "batch_execute_with_retry",
    "BatchConfig",
    "collect_successes",
    "collect_failures",
    "partition_results",
    # Pagination
    "paginate",
    "paginate_all",
    "Paginator",
    "PaginationConfig",
    # Routes
    "Routes",
    "API",
    # Error handling
    "ErrorMode",
    "ErrorHandler",
    # Exceptions
    "PyWATSError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
    "ConflictError",
    "EmptyResponseError",
    "ConnectionError",
    "TimeoutError",
]
