"""Core infrastructure for pyWATS.

Contains HTTP client, authentication, error handling, and base exceptions.
"""
from .client import HttpClient, Response
from .async_client import AsyncHttpClient
from .config import (
    APISettings,
    DomainSettings,
    ProductDomainSettings,
    ReportDomainSettings,
    ProductionDomainSettings,
    ProcessDomainSettings,
    SoftwareDomainSettings,
    AssetDomainSettings,
    RootCauseDomainSettings,
    AppDomainSettings,
    get_default_settings,
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
from .retry_handler import (
    RetryHandler,
    RetryContext,
)
from .parallel import (
    parallel_execute,
    parallel_execute_with_retry,
    ParallelConfig,
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
from .validation import (
    allow_problematic_characters,
    validate_serial_number,
    validate_part_number,
    validate_batch_serial_number,
    validate_report_header_field,
    find_problematic_characters,
    is_problematic_chars_allowed,
    ReportHeaderValidationError,
    ReportHeaderValidationWarning,
    PROBLEMATIC_CHARS,
    SUPPRESS_PREFIX,
)

__all__ = [
    # Client
    "HttpClient",
    "Response",
    # Config (pure models, no file I/O)
    "APISettings",
    "DomainSettings",
    "ProductDomainSettings",
    "ReportDomainSettings",
    "ProductionDomainSettings",
    "ProcessDomainSettings",
    "SoftwareDomainSettings",
    "AssetDomainSettings",
    "RootCauseDomainSettings",
    "AppDomainSettings",
    "get_default_settings",
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
    "RetryHandler",
    "RetryContext",
    "RETRYABLE_STATUS_CODES",
    "IDEMPOTENT_METHODS",
    # Parallel execution (renamed from batch to avoid WATS production batch confusion)
    "parallel_execute",
    "parallel_execute_with_retry",
    "ParallelConfig",
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
    # Validation
    "allow_problematic_characters",
    "validate_serial_number",
    "validate_part_number",
    "validate_batch_serial_number",
    "validate_report_header_field",
    "find_problematic_characters",
    "is_problematic_chars_allowed",
    "ReportHeaderValidationError",
    "ReportHeaderValidationWarning",
    "PROBLEMATIC_CHARS",
    "SUPPRESS_PREFIX",
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
