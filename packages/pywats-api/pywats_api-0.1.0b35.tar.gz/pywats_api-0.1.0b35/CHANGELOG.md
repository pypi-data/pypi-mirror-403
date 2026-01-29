# Changelog

All notable changes to PyWATS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0b35] - 2026-01-23

### Added

- **Comprehensive Client Test Suite** - 71 passing tests for pyWATS Client:
  - Configuration tests (18) - ClientConfig, ConverterConfig validation
  - Queue manager tests (26) - Offline queue, persistence, retry logic
  - Connection tests (7) - Service lifecycle, authentication, monitoring
  - Converter tests (10) - Base classes, validation, results
  - Integration tests (10) - End-to-end workflows, error recovery
  - Full documentation in `docs/project/TEST_SUITE_SUMMARY.md` and `api-tests/client/README.md`
  - Shared fixtures in `conftest.py` for temp dirs, mocks, sample data

- **Docker Containerization** - Official container support for headless deployment:
  - Multi-stage Dockerfile with 5 build targets (api, client-headless, mcp, dev, default)
  - Docker Compose with 3 service profiles for different deployment scenarios
  - Multi-architecture support (AMD64, ARM64) for Raspberry Pi/embedded systems
  - Health checks, volume mounts for persistence, security best practices
  - Comprehensive deployment guide in `docs/DOCKER.md` with Kubernetes/Swarm examples

- **Enhanced Error Catalog** - Complete error reference documentation:
  - 814-line `docs/ERROR_CATALOG.md` covering all error types and codes
  - Detailed remediation steps for every error scenario
  - Code examples for STRICT/LENIENT error modes
  - HTTP status code mappings and retry behavior
  - Quick reference tables organized by module and category

### Changed

- **Documentation Organization** - Reorganized project management documents:
  - Created `docs/project/` for internal tracking and review documents
  - Moved PROJECT_REVIEW.md, IMPROVEMENTS_PLAN.md, TEST_SUITE_SUMMARY.md to docs/project/
  - Added docs/project/README.md with overview and links
  - Updated docs/INDEX.md with Project Management & Development section
  - Cleaner root directory structure

## [0.1.0b34] - 2025-01-XX

### Added
  - `Routes` class in `pywats.core.routes` with 170 endpoints
  - Domain-specific nested classes: `Routes.Production`, `Routes.Product`, etc.
  - Internal API routes via `Routes.Domain.Internal` nested classes
  - Static methods for dynamic route generation (e.g., `Routes.Production.unit("SN", "PN")`)
  - Eliminates hardcoded endpoint strings throughout codebase

- **Complete Sync Service Layer** - All 9 domains now have sync services:
  - `AnalyticsService` - 42 methods wrapping async operations
  - `AssetService` - 26 methods for asset management
  - `ProcessService` - ~30 methods for process/operation lookup
  - `ProductService` - ~40 methods for product management
  - `ProductionService` - ~55 methods for unit tracking
  - `ReportService` - ~35 methods for test reports
  - `SoftwareService` - ~27 methods for package distribution
  - `RootCauseService` - ~12 methods for ticketing
  - `ScimService` - ~11 methods for user provisioning
  - All use `run_sync()` to delegate to async counterparts

- **Async-First Architecture** - Business logic centralized in async services:
  - `AsyncAnalyticsService`, `AsyncAssetService`, etc. are source of truth
  - Sync services are thin wrappers using `run_sync()` utility
  - Single point of maintenance for business logic
  - `run_sync()` utility in `pywats.core.sync_runner` for sync/async bridging

- **Async GUI Infrastructure** - Non-blocking UI for all API operations in pyWATS Client:
  - `AsyncTaskRunner` - Bridge between async operations and Qt GUI thread
  - `TaskResult` - Container for async task results with success/error state
  - `TaskState` - Enum for task lifecycle states (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
  - `BasePage.run_async()` - Easy async execution with automatic loading indicators
  - Automatic loading state management with visual feedback

- **ErrorHandlingMixin** - Standardized error handling for GUI pages:
  - `handle_error(exception, context)` - Intelligent error dialog routing
  - `show_error(message)`, `show_warning(message)`, `show_info(message)`
  - Automatic handling of `AuthenticationError`, `ValidationError`, `ServerError`
  - Integrated into `BasePage` - all pages inherit error handling

- **Async Page Operations** - All GUI pages now use async patterns for API calls:
  - **AssetPage** - Async load, create, edit, and status check operations
  - **ProductPage** - Async load products, create, edit, and add revisions
  - **SoftwarePage** - Async load packages, create, release, revoke, delete
  - **RootCausePage** - Async load tickets, create, edit, add comments, status changes

- **ReportType Enum** - New enum for unified UUT/UUR report queries:
  - `ReportType.UUT` ("U") - Unit Under Test reports
  - `ReportType.UUR` ("R") - Unit Under Repair reports
  - Available at top level: `from pywats.domains.report import ReportType`

- **Unified Report Query Endpoint** - Query both UUT and UUR headers with a single method:
  - `query_headers(report_type, odata_filter, top, skip, orderby, expand)` - Unified query
  - Supports OData filter syntax for flexible querying
  - Example: `api.report.query_headers(report_type=ReportType.UUT, odata_filter="serialNumber eq 'W12345'")`

- **Report Query Helper Methods** - Convenient methods for common query patterns:
  - `get_headers_by_serial(serial_number)` - Get headers by serial number
  - `get_headers_by_part_number(part_number)` - Get headers by part number
  - `get_headers_by_date_range(start_date, end_date)` - Get headers by date range
  - `get_recent_headers(count)` - Get most recent headers (default: 100)
  - `get_todays_headers()` - Get today's headers

### Changed
- **All Repositories Use Routes Class** - No more hardcoded endpoint strings:
  - 9/9 async_repository.py files migrated to use `Routes`
  - Improves maintainability and reduces typo errors
  - Example: `Routes.Production.UNIT` instead of `"/api/Production/Unit"`

- **GUI Pages Use Async Execution** - API operations no longer block the UI:
  - Loading indicators display during data fetch operations
  - Error handling with user-friendly dialogs
  - Task cancellation support for long-running operations

- **Report Query API now uses OData** - The report query endpoints now use OData filter syntax instead of WATSFilter:
  - `query_uut_headers(odata_filter, top, skip, orderby, expand)` - Updated signature
  - `query_uur_headers(odata_filter, top, skip, orderby, expand)` - Updated signature
  - OData filter examples:
    - `"serialNumber eq 'W12345'"` - Filter by serial number
    - `"partNumber eq 'WIDGET-001'"` - Filter by part number
    - `"result eq 'Failed'"` - Filter by result
    - `"partNumber eq 'WIDGET-001' and result eq 'Failed'"` - Combined filters
  - **Note**: WATSFilter is still used for Analytics API endpoints

### Deprecated
- **repository_internal.py files** - Internal APIs now in main async_repository.py:
  - `production/repository_internal.py` - Use `AsyncProductionRepository` instead
  - `process/repository_internal.py` - Use `AsyncProcessRepository` instead
  - Deprecation warnings added; will be removed in future version

### Breaking Changes
- `query_uut_headers()` and `query_uur_headers()` no longer accept `WATSFilter` parameter
- Use OData filter syntax or helper methods instead
- Migration example:
  ```python
  # Before (WATSFilter - no longer works for report queries)
  from pywats.domains.report import WATSFilter
  filter_data = WATSFilter(serialNumber="W12345")
  headers = api.report.query_uut_headers(filter_data)
  
  # After (OData filter)
  headers = api.report.query_uut_headers(odata_filter="serialNumber eq 'W12345'")
  
  # Or using helper method
  headers = api.report.get_headers_by_serial("W12345")
  ```

## [0.1.0b34] - 2026-01-15

### Added
- **Batch Operations** - Execute multiple API calls concurrently with `batch_execute`:
  - `batch_execute(keys, operation)` - Run operations in parallel using ThreadPoolExecutor
  - `batch_execute_with_retry(keys, operation, max_retries)` - Batch with automatic retry on failures
  - Configurable concurrency via `max_workers` (default: 10)
  - Order-preserving results with `Result[T]` return type per item
  - Progress callbacks for tracking completion
  - Helper functions: `collect_successes()`, `collect_failures()`, `partition_results()`
  - New `BatchConfig` class for advanced configuration:
    ```python
    from pywats.core import batch_execute, collect_successes
    
    # Fetch multiple products concurrently
    results = batch_execute(
        keys=["PN-001", "PN-002", "PN-003"],
        operation=lambda pn: api.product.get_product(pn),
        max_workers=5
    )
    products = collect_successes(results)  # Get successful results only
    ```
  - Domain-specific batch methods:
    - `ProductService.get_products_batch(part_numbers)` - Fetch multiple products
    - `ProductService.get_revisions_batch(pairs)` - Fetch multiple revisions

- **Pagination Utilities** - Memory-efficient iteration over large datasets:
  - `paginate(fetch_page, get_items, ...)` - Generator-based pagination
  - `paginate_all(...)` - Fetch all pages into a list
  - `Paginator` class - Reusable paginator with `iterate()`, `all()`, `count()` methods
  - `PaginationConfig` for default settings
  - Early termination support (break from iteration)
  - Progress callbacks for page fetching
  - SCIM domain integration:
    ```python
    # Iterate over all SCIM users efficiently
    for user in api.scim.iter_users(page_size=100):
        print(user.userName)
    
    # With progress tracking
    for user in api.scim.iter_users(on_page=lambda p, n, t: print(f"Page {p}")):
        process(user)
    ```

- **Automatic Retry for Transient Failures** - HTTP requests now automatically retry on transient errors:
  - Retries on `ConnectionError`, `TimeoutError`, and HTTP 429/500/502/503/504
  - Exponential backoff with jitter (default: 3 attempts, 1s base delay)
  - Only idempotent methods (GET, PUT, DELETE) are retried (POST is not retried)
  - Respects `Retry-After` header from server for rate limiting (429)
  - New `RetryConfig` class for customization:
    ```python
    from pywats import pyWATS, RetryConfig
    
    # Custom retry configuration
    config = RetryConfig(max_attempts=5, base_delay=2.0)
    api = pyWATS(base_url="...", token="...", retry_config=config)
    
    # Disable retry entirely
    api = pyWATS(base_url="...", token="...", retry_enabled=False)
    ```
  - Retry statistics available via `api.retry_config.stats`
  - `RetryExhaustedError` exception when all attempts fail
  - Top-level exports: `from pywats import RetryConfig, RetryExhaustedError`

## [0.1.0b33] - 2025-01-15

### Added
- **Type-Safe Query Enums** - New enums for query parameter type safety:
  - `StatusFilter`: Filter by test status (`PASSED`, `FAILED`, `ERROR`, `TERMINATED`, `ALL`)
  - `RunFilter`: Filter by test run (`FIRST`, `LAST`, `ALL`, `ALL_EXCEPT_FIRST`)
  - `StepType`: Step types (`NUMERIC_LIMIT`, `STRING_VALUE`, `PASS_FAIL`, `SEQUENCECALL`, etc.)
  - `CompOperator`: Comparison operators (`GELE`, `GT`, `LT`, `EQ`, `NE`, `LOG`, etc.)
  - `SortDirection`: Sort direction (`ASC`, `DESC`)
  - All enums available at top level: `from pywats import StatusFilter, RunFilter`

- **Analytics Dimension/KPI Enums** - Type-safe dimension query building:
  - `Dimension`: 23+ grouping dimensions (`PART_NUMBER`, `STATION_NAME`, `PERIOD`, etc.)
  - `RepairDimension`: 15 repair-specific dimensions (`REPAIR_CODE`, `COMPONENT_REF`, etc.)
  - `KPI`: 21+ KPIs (`FPY`, `RTY`, `PPM_FPY`, `UNIT_COUNT`, `AVG_TEST_TIME`, etc.)
  - `RepairKPI`: Repair KPIs (`REPAIR_COUNT`, `REPAIR_REPORT_COUNT`)
  - `DimensionBuilder`: Fluent API for building dimension queries with presets

- **Path Utilities** - Seamless measurement path handling:
  - `StepPath` / `MeasurementPath`: Classes for working with step/measurement paths
  - Automatic conversion between user-friendly format (`/`) and API format (`¶`)
  - Path concatenation with `/` operator: `parent / "child" / "measurement"`
  - Properties: `.display` (user-friendly), `.api_format` (API), `.parts` (list)
  - All available at top level: `from pywats import MeasurementPath, StepPath`

- **DimensionBuilder Presets** - Common dimension query patterns:
  - `DimensionBuilder.yield_by_product()` - Yield analysis by product
  - `DimensionBuilder.yield_by_station()` - Yield analysis by station
  - `DimensionBuilder.repair_analysis()` - Repair statistics
  - `DimensionBuilder.oee_analysis()` - OEE metrics
  - Fluent API: `.add(Dimension.PART_NUMBER)`, `.add(KPI.FPY, desc=True)`

### Changed
- **WATSFilter Enum Support** - `status` and `run` parameters now accept enums:
  - `status=StatusFilter.FAILED` (or string `"F"` for backward compatibility)
  - `run=RunFilter.FIRST` (or integer `1` for backward compatibility)
  - Added `measurement_paths` field with automatic path normalization

- **Analytics Models Enhanced** - Type-safe fields and display properties:
  - `TopFailedStep.step_type` → `Union[StepType, str]`
  - `StepAnalysisRow.step_type` → `Union[StepType, str]`
  - `StepAnalysisRow.comp_operator` → `Union[CompOperator, str]`
  - Added `step_path_display` property on measurement/step models (returns `/`-separated paths)

- **Analytics Service Path Handling** - Automatic path normalization:
  - `get_aggregated_measurements(measurement_paths=...)` accepts `StepPath` or list
  - `get_measurements(measurement_paths=...)` accepts `StepPath` or list
  - Paths automatically converted to API format before server calls

### Fixed
- Restored the public analytics `get_aggregated_measurements()` helper and removed the internal XML-only variant to keep the simple measurement path workflow intact.
- **MCP Server Critical Bug** - Fixed invalid `WATSFilter` field names in AI tooling:
  - Changed `start=` to `date_from=` in 5 MCP tools (was causing Pydantic validation errors)
  - Fixed `status="F"` to use `StatusFilter.FAILED` enum for type safety
  - Affected tools: `query_reports`, `get_failures`, `get_yield`, `get_yield_by_station`, `get_yield_trend`
  - This resolves "'WATSFilter' object is not a mapping" errors reported by AI tool users

## [0.1.0b32] - 2025-01-14

### Changed
- **BREAKING: Unified API pattern** - Removed `api.*_internal` accessors:
  - All internal methods now accessed via main domain accessor
  - `api.product.get_box_build_template()` (was `api.product_internal.get_box_build()`)
  - `api.asset.upload_blob()` (was `api.asset_internal.upload_file()`)
  - `api.analytics.get_unit_flow()` (was `api.analytics_internal.get_unit_flow()`)
  - `api.production.get_all_unit_phases()` (was `api.production_internal.get_unit_phases()`)
  - `api.process.get_fail_codes()` (was `api.process_internal.get_fail_codes()`)
  - Internal methods marked with `⚠️ INTERNAL API` warnings in docstrings
  - See `docs/internal/API_DESIGN_CONVENTIONS.md` for migration guide

### Added
- **API Design Conventions** - New documentation for unified API pattern (`docs/internal/API_DESIGN_CONVENTIONS.md`)
- **Internal Analytics Tests** - Test suite for internal analytics endpoints

## [0.1.0b31] - 2025-01-14

_Note: Version b31 was released manually, b32 is the GitHub Actions release._

## [0.1.0b30] - 2025-01-13

### Fixed
- **MeasurementData API response parsing** - Fixed `analytics.get_measurements()` returning all `None` values:
  - The API returns a nested structure: `[{measurementPath, measurements: [...]}]`
  - Added `id` → `report_id` alias mapping
  - Added `startUtc` → `timestamp` alias mapping  
  - Already had `limit1` → `limit_low` and `limit2` → `limit_high` aliases
  - Updated docstring with field mapping documentation

- **StepStatusItem and MeasurementListItem aliases** - Added consistent field aliases for API compatibility:
  - Added `id` → `report_id` alias mapping
  - Added `startUtc` → `timestamp` alias mapping

## [0.1.0b29] - 2025-01-22

### Added
- **SCIM Domain** - New domain for System for Cross-domain Identity Management (user provisioning):
  - `ScimToken` model - JWT token response for Azure AD provisioning
  - `ScimUser` model - SCIM user resource with name, emails, active status
  - `ScimUserName`, `ScimUserEmail` - User name/email components
  - `ScimPatchRequest`, `ScimPatchOperation` - SCIM RFC 7644 patch format
  - `ScimListResponse` - Paginated user list response
  - Service methods via `api.scim`:
    - `get_token(duration_days)` - Generate provisioning token for Azure AD
    - `get_users()` - List all SCIM users
    - `create_user(user)` - Create a new user
    - `get_user(id)` - Get user by ID
    - `delete_user(id)` - Delete user by ID
    - `update_user(id, patch)` - Update user with SCIM patch operations
    - `get_user_by_username(username)` - Get user by username
    - `deactivate_user(id)` - Convenience method to deactivate user
    - `set_user_active(id, active)` - Set user active/inactive
    - `update_display_name(id, name)` - Update user display name
  - Complete documentation in `docs/SCIM.md`
  - Example scripts in `examples/scim/`

- **Internal Analytics Endpoints** - New step/measurement filter endpoints (⚠️ internal API):
  - All internal methods now accessible via `api.analytics` (unified API surface)
  - `StepStatusItem` model for step status data
  - `MeasurementListItem` model for measurement list data
  - `get_aggregated_measurements()` - Aggregated stats with step/sequence filters
  - `get_measurement_list()` - Measurement values with step/sequence filters
  - `get_step_status_list()` - Step statuses with step/sequence filters
  - `get_top_failed_advanced()` - Top failed steps with advanced filters (internal API)
  - `get_top_failed_by_product()` - Top failed steps with simple parameters
  - Simple variants: `get_measurement_list_by_product()`, `get_step_status_list_by_product()`
  - All methods accept XML step/sequence filters (obtained from TopFailed endpoint)
  - Unit Flow methods (`get_unit_flow()`, `get_bottlenecks()`, etc.) now on `api.analytics`
  - Unified API: All internal methods now accessed via main domain accessor (e.g., `api.product.get_box_build_template()` instead of `api.product_internal.get_box_build()`)
  - Removed separate `api.analytics_internal`, `api.product_internal`, `api.asset_internal`, `api.production_internal`, `api.process_internal` accessors
  - Internal API methods marked with "Note: Uses internal API endpoint" in docstrings

### Changed
- **Window size** - Increased default startup window size from 900x650 to 1000x750
- **Default tab visibility** - Asset, RootCause, Production, and Product tabs now hidden by default

### Fixed
- **System tray icon** - Fixed missing tray icon on Windows
  - Added icon validation and logging for troubleshooting
  - Added package-data config in pyproject.toml for resource files
- **Application exit** - Fixed app sometimes getting stuck on exit
  - Added status timer stop in quit handler
- **Settings dialog layout** - Fixed buttons taking up half the screen
  - Buttons now stay at bottom with fixed height

## [0.1.0b28] - 2025-01-12

### Changed
- **Test suite restructured** - Reorganized 30+ flat test files into module-based folders:
  - Each domain now has its own folder: `analytics/`, `asset/`, `process/`, `product/`, `production/`, `report/`, `rootcause/`, `software/`
  - Consistent naming: `test_service.py` (unit), `test_integration.py` (server), `test_workflow.py` (E2E)
  - Cross-cutting tests in `cross_cutting/` folder
  - Debug scripts moved to `scripts/` folder (not run by pytest)
  - Updated README with new structure and commands

### Fixed
- **RootCause assignee preservation** - Fixed ticket operations losing assignee information:
  - WATS server does not return `assignee` field in API responses
  - Service methods (`create_ticket`, `assign_ticket`, `add_comment`, `change_status`) now preserve assignee by returning it from input parameters
  - Added comprehensive documentation in service.py, models.py, and ROOTCAUSE.md

- **Pydantic ClassVar annotation** - Fixed `Step.MAX_NAME_LENGTH` causing Pydantic validation errors:
  - Changed from `MAX_NAME_LENGTH: int = 100` to `MAX_NAME_LENGTH: ClassVar[int] = 100`
  - Prevents Pydantic 2.x from treating class constants as model fields

- **Architecture cleanup** - Removed backward compatibility code that violated service layer pattern:
  - Removed `HttpClient` imports from `rootcause/service.py` and `software/service.py`
  - Service constructors now only accept repository instances (not HttpClient)
  - Enforces proper Service → Repository → HttpClient architecture

- **Test fixes** - Fixed 29 failing tests across multiple domains:
  - Product: `get_product_groups()` now uses correct HTTP GET method
  - Software: `delete_package_by_name()` test expects `None` return value
  - Report: Failing report fixture now sets `result="F"` for proper UUT status
  - RootCause: Tests now assign tickets before changing status (server requirement)

### Added
- **ImportMode for UUT reports** - New mode setting to control automatic status calculation and failure propagation:
  - `ImportMode.Import` (default): Passive mode - data stored exactly as provided
  - `ImportMode.Active`: Enables automatic behaviors for test report creation
  - Access via `api.report.import_mode = ImportMode.Active`
  
- **Automatic status calculation** - In Active mode, numeric measurements auto-calculate status:
  - Based on `comp_op` (comparison operator) and limits (`low_limit`, `high_limit`)
  - Supports all 15 CompOp types: EQ, NE, GT, LT, GE, LE, GTLT, GELE, GELT, GTLE, LTGT, LEGE, LEGT, LTGE, LOG
  - LOG comparison always passes (no limit check)
  - Status only auto-calculated when not explicitly provided
  
- **Failure propagation** - In Active mode, step failures propagate up hierarchy:
  - New `fail_parent_on_failure` property on Step class (default: `True`)
  - When step status is Failed and flag is True, parent SequenceCall also fails
  - Propagation continues recursively until flag is False or root is reached
  - `propagate_failure()` method on Step for manual propagation

### Fixed
- **Comprehensive exception handling overhaul** - Fixed ErrorHandler usage across ALL 7 domains (~139 methods):
  - **Asset domain** (20 methods): `get_asset()`, `get_assets()`, `get_asset_hierarchy()`, `create_asset()`, `update_asset()`, etc.
  - **Process domain** (5 methods): `get_processes()`, internal CRUD operations
  - **Product domain** (27 methods): `get_all()`, `save()`, `get_revision()`, `save_revision()`, batch operations, etc.
  - **Production domain** (39 methods): `get_unit()`, `save_units()`, serial number management, batch operations, etc.
  - **Report domain** (1 method): `post_wsxf()` - other methods already used ErrorHandler correctly
  - **RootCause domain** (7 methods): `get_ticket()`, `get_tickets()`, `create_ticket()`, `update_ticket()`, etc.
  - **Software domain** (28 methods): `get_packages()`, `create_package()`, folder management, history operations, etc.
  
  **Breaking behavior change**: Methods that previously returned empty lists/None on HTTP errors will now raise appropriate exceptions in STRICT mode (default):
  - HTTP 400 → `ValidationError`
  - HTTP 401 → `AuthenticationError`
  - HTTP 403 → `AuthorizationError`
  - HTTP 404 → `NotFoundError`
  - HTTP 409 → `ConflictError`
  - HTTP 5xx → `ServerError`
  
  For backwards compatibility with silent error handling, use LENIENT mode:
  ```python
  from pywats.core.exceptions import ErrorHandler, ErrorMode
  api = pyWATS(base_url, token, error_mode=ErrorMode.LENIENT)
  ```

### Changed
- **Magic numbers extracted to named constants**:
  - `ProcessService.DEFAULT_TEST_PROCESS_CODE` (100) and `DEFAULT_REPAIR_PROCESS_CODE` (500)
  - `ReportService.DEFAULT_REPAIR_PROCESS_CODE` (500) and `DEFAULT_RECENT_DAYS` (7)
  - `Step.MAX_NAME_LENGTH` (100) for step name validation

- **Input validation with ValueError** - Added required parameter validation across Service layers:
  - **Asset** (5 methods): `get_asset()`, `get_asset_by_serial()`, `create_asset()`, `delete_asset()`, `get_status()`
  - **Product** (5 methods): `get_product()`, `create_product()`, `get_revision()`, `get_revisions()`, `create_revision()`
  - **Production** (4 methods): `get_unit()`, `verify_unit()`, `get_unit_grade()`, `is_unit_passing()`
  - **RootCause** (7 methods): `get_ticket()`, `create_ticket()`, `add_comment()`, `change_status()`, `assign_ticket()`, `get_attachment()`, `upload_attachment()`
  - **Software** (14 methods): `get_package()`, `get_package_by_name()`, `get_released_package()`, `get_packages_by_tag()`, `create_package()`, `delete_package()`, `delete_package_by_name()`, all status workflow methods, `get_package_files()`, `upload_zip()`, `update_file_attribute()`
  
  All validated methods now raise `ValueError` with descriptive messages for empty/None required parameters.

## [0.1.0b27] - 2026-01-08

### Added
- **End-user installation guide** - Comprehensive documentation for pyWATS Client installation and setup:
  - Platform-specific file locations (Windows, Linux, Mac)
  - GUI vs headless installation modes
  - First-time setup instructions
  - Configuration management
  - Running as Windows service or Linux systemd service
  - Troubleshooting guide

### Fixed
- **Linting warnings** - Cleaned up development tooling:
  - Suppressed markdown line length warnings in VS Code
  - Fixed PowerShell linting issues in bump script

### Added

- **Analytics GET parameters** - Additional filtering options for analytics endpoints:
  - `get_processes()`: `include_test_operations`, `include_repair_operations`, `include_wip_operations`, `include_inactive_processes`
  - `get_product_groups()`: `include_filters` parameter to include filter configuration

- **Report bandwidth optimization** - New parameters to reduce payload sizes:
  - `get_report()`: `detail_level` (0-7), `include_chartdata`, `include_attachments`
  - `get_report_xml()`: `include_attachments`, `include_chartdata`, `include_indexes`

- **Software internal API** - New `SoftwareRepositoryInternal` class for internal operations:
  - File management: `get_file()`, `check_file()`
  - Folder management: `create_package_folder()`, `update_package_folder()`, `delete_package_folder()`, `delete_package_folder_files()`
  - Package history: `get_package_history()`, `get_package_download_history()`, `get_revoked_packages()`, `get_available_packages()`
  - Entity details: `get_software_entity_details()`, `log_download()`
  - Connection: `is_connected()`

- **Production internal API** - Extended `ProductionRepositoryInternal` with full coverage:
  - Unit operations: `get_unit()`, `get_unit_info()`, `get_unit_hierarchy()`, `get_unit_state_history()`, `get_unit_phase()`, `get_unit_process()`, `get_unit_contents()`, `create_unit()`
  - Child unit operations: `add_child_unit()`, `remove_child_unit()`, `remove_all_child_units()`, `check_child_units()`
  - Serial number management: `find_serial_numbers()`, `get_serial_number_count()`, `free_serial_numbers()`, `delete_free_serial_numbers()`, `get_serial_number_ranges()`, `get_serial_number_statistics()`
  - Sites: `get_sites()`, `is_connected()`

- **Asset alarm state filtering** - New method `get_assets_by_alarm_state()` for multi-state filtering

### Changed

- **Asset performance documentation** - `get_assets_in_alarm()` and `get_assets_in_warning()` now include:
  - Clear performance warning about N+1 API calls
  - New `top` parameter to limit assets checked
  - Documentation pointing to internal API alternatives

### Fixed
- **Analytics error handling** - `AnalyticsRepository` now properly raises exceptions on HTTP errors in STRICT mode (default):
  - Added default `ErrorHandler(ErrorMode.STRICT)` initialization, matching all other repositories
  - HTTP 403 now raises `AuthorizationError` instead of silently returning `[]`
  - HTTP 404 now raises `NotFoundError` instead of silently returning `[]`
  - HTTP 400 now raises `ValidationError` instead of silently returning `[]`
  - HTTP 5xx now raises `ServerError` instead of silently returning `[]`
  - Fixes silent error swallowing that made debugging permission/config issues difficult
  
- **DynamicYield/DynamicRepair period filtering** - `get_dynamic_yield()` and `get_dynamic_repair()` now default `includeCurrentPeriod=True` when using period-based filtering (`period_count`/`date_grouping`). Previously, omitting this parameter would return empty results due to WATS server behavior.

### Documentation
- **DynamicYield/DynamicRepair** - Enhanced documentation with:
  - Complete list of supported dimensions for both endpoints
  - Complete list of supported KPIs that can be ordered
  - Clear explanation that ordering is done via `dimensions` parameter with asc/desc hints (e.g., `"unitCount desc;partNumber"`)
  - Practical examples showing multi-level sorting and filtering patterns

## [0.1.0b20] - 2025-12-22

### Changed
- Beta version bump for ongoing development

## [0.1.0b19] - 2025-12-21

### Changed
- **Agent tool surface unified** - single canonical executor/tool interface (removed internal v1/v2 naming)
- **Wrapped tool module renamed** - internal wrapper module renamed to non-versioned name
- **Experimental TSA module renamed** - experimental TSA implementation renamed to non-versioned module

### Fixed
- **Tool result robustness** - tool execution guardrails to avoid blank/no-response outcomes (summary always present; empty data treated as explicit no-data)
- **Mypy configuration** - corrected `tool.mypy.python_version` to a real Python version

## [0.1.0b17] - 2025-12-21

### Added
- **Agent execution core** - LLM-safe tool results via bounded envelopes + out-of-band data handles
- **DynamicYield filter support** - Added misc-info and asset filter fields to `WATSFilter`

### Changed
- **Agent public API (BETA)** - canonical exports (breaking changes by design)

## [0.1.0b15] - 2025-12-21

### Fixed
- **Agent package bundling** - `pywats_agent` is now properly included in `pywats-api` package
  - Agent tools available via `from pywats_agent.tools import ...`
  - No separate package installation required

## [0.1.0b14] - 2025-12-21

### Fixed
- **Missing type imports** - Added missing `Any` imports to asset and product service modules
  - Fixed F821 linting errors that were blocking CI

### Added
- **Pre-release validation script** - New `scripts/pre_release_check.ps1` to catch errors before releasing
  - Runs flake8 linting checks (same as CI)
  - Optionally runs full test suite
  - Use `.\scripts\pre_release_check.ps1` before every release

## [0.1.0b12] - 2025-12-21

### Fixed
- **Import path issues** - Resolved package shadowing and import errors
  - Removed stale `src/pywats_agent/` directory that shadowed the correct package location
  - Fixed test imports to use public API (`pywats_agent.tools`) instead of internal paths (`pywats_agent.tools.shared.*`)
  - Added missing exports to `pywats_agent.tools.__init__.py` (TemporalMatrix, DeviationMatrix, DeviationCell, session creators)
  - All 877 tests now pass (589 agent tests + 288 API tests)

## [0.1.0b11] - Previous Release

### Added

- **Agent Autonomy System** - Configurable rigor and write safety controls
  - `AnalyticalRigor` enum: QUICK, BALANCED, THOROUGH, EXHAUSTIVE
    - Controls how thorough analytics operations are (data gathering, cross-validation)
    - Affects system prompt instructions and default parameters
  - `WriteMode` enum: BLOCKED, CONFIRM_ALL, CONFIRM_DESTRUCTIVE
    - Controls whether write operations (POST/PUT/DELETE) are allowed
    - Enforces confirmation requirements for mutations
  - `AgentConfig` class for unified configuration
    - `get_system_prompt()` - Generates rigor/write mode instructions
    - `get_default_parameters(rigor)` - Returns sample sizes scaled by rigor
    - `allows_write(operation)` - Checks if write operation is permitted
    - `requires_confirmation(operation)` - Checks if confirmation needed
  - 6 presets for common scenarios:
    - `viewer` - Read-only analytics, writes blocked
    - `quick_check` - Fast spot-checks, writes blocked  
    - `investigation` - Balanced analysis (default)
    - `audit` - Maximum thoroughness, all writes confirmed
    - `admin` - Balanced analysis with full write access
    - `power_user` - Quick analysis with full write access
  - `AgentContext` integration - Config flows through context to agent
  - 33 unit tests

- **Visualization Sidecar System** - Optional rich visualization for UI
  - `VisualizationPayload` - Bypasses LLM context, goes directly to UI
  - `VizBuilder` - Fluent builder for common chart types:
    - `line_chart()`, `area_chart()`, `bar_chart()` - Trends and comparisons
    - `pie_chart()`, `pareto_chart()` - Distribution analysis
    - `control_chart()` - SPC with UCL/LCL/target lines
    - `heatmap()`, `histogram()`, `scatter()` - Advanced analysis
    - `table()`, `kpi()`, `kpi_row()`, `dashboard()` - Data display
  - Reference lines, annotations, and drill-down support
  - `AgentResult.viz_payload` - Optional field (UI infers from data when absent)
  - `to_openai_response()` excludes viz (saves tokens)
  - `to_ui_response()` includes viz (for frontend rendering)
  - 37 unit tests

## [0.1.0b10] - 2025-12-20

### Added

- **UnitAnalysisTool** - Comprehensive individual unit analysis
  - Complete test history and status determination for any serial number
  - Production/MES tracking information (phase, batch, location)
  - Unit verification and grading (when rules configured)
  - Sub-unit (component) tracking from production and test reports
  - Multiple analysis scopes: quick, standard, full, history, verify
  - Status classification: passing, failing, in_progress, repaired, scrapped
  - 40+ unit tests

- **ControlPanelTool** - Unified administrative tool for managing WATS configuration
  - Single tool handles 5 domains: Asset, Product, Production, Software, Process
  - 12 operation types: list, get, search, create, update, delete, domain-specific
  - Entity support: assets, types, products, revisions, units, phases, packages, folders
  - Comprehensive input validation and confirmation for destructive operations
  - 50+ unit tests covering all domains and operations

- **SubUnitAnalysisTool** - Deep analysis of sub-unit (component) relationships
  - Uses query_header endpoint with OData expansion for efficient bulk queries
  - 4 query types:
    - `filter_by_subunit`: Find parent units containing a specific component
    - `get_subunits`: Get all sub-units for filtered parent reports
    - `statistics`: Aggregate sub-unit counts by type/part number/revision
    - `deviation`: Detect parents with missing, extra, or unexpected sub-units
  - Supports both UUT and UUR report types
  - Automatic baseline inference for deviation detection
  - 25 unit tests

- **Report Service Enhancements** - Extended query_header capabilities
  - OData $expand support for sub-units, misc info, assets, attachments
  - New service methods: `query_headers_with_subunits()`, `query_headers_by_subunit_part_number()`, `query_headers_by_subunit_serial()`
  - Support for OData $filter, $top, $orderby, $skip parameters

- **Report Models** - New models for expanded header data
  - `HeaderSubUnit`: serial_number, part_number, revision, part_type
  - `HeaderMiscInfo`: description, value
  - `HeaderAsset`: serial_number, running_count, total_count, calibration info

## [0.1.0b8] - 2025-12-19

### Added

- **Agent Tools in Main Package** - `pywats_agent` is now included in `pywats-api`
  - Install with `pip install pywats-api[agent]` for explicit dependency
  - Or just `pip install pywats-api` - agent tools are always included, no extra deps needed
  - LangChain integration available with `pip install pywats-api[langchain]`

### Fixed

- **Tool Selection Patterns** - Fixed regex patterns in `AgentTestHarness`
  - Added `\bwhat.?step\b` pattern for "What step is causing..." queries
  - Added `\bstep.*caus` pattern for step causation queries
  - Fixed plural forms `measurements?` for individual/raw measurements

## [0.1.0b7] - 2025-12-19

### Added

- **Agent Analysis Tools** (`pywats_agent.tools`) - Comprehensive root cause analysis workflow
  - **ProcessCapabilityTool** - Advanced SPC with:
    - Dual Cpk analysis (Cpk vs Cpk_wof - with/without failures)
    - Stability assessment before trusting Cpk values
    - Hidden mode detection (outliers, trends, drift, bimodal, centering, approaching limits)
    - Improvement priority matrix (critical → high → medium → low)
  - **StepAnalysisTool** - Test Step Analysis (TSA) for:
    - Root cause identification (steps causing unit failures)
    - Process capability (Cpk) analysis per measurement
    - Data integrity checks for SW versions and revisions
  - **DimensionalAnalysisTool** - Failure mode detection across dimensions:
    - Station, operator, fixture, batch, SW version analysis
    - Statistical significance assessment
    - Prioritized recommendations
  - **AdaptiveTimeFilter** - Dynamic time windows for varying production volumes:
    - Automatically adjusts query window based on volume
    - Prevents query overload for high-volume customers
  - **ProcessResolver** - Fuzzy matching for process/test operation names:
    - Handles imprecise user input ("PCBA" → "PCBA test")
    - Common alias expansion
    - Diagnoses mixed-test process issues

- **Documentation** - Enhanced domain knowledge documentation:
  - Process Capability Analysis section in WATS_DOMAIN_KNOWLEDGE.md
  - Workflow examples in YIELD_METRICS_GUIDE.md
  - Dual Cpk interpretation guide

## [0.1.0b6] - 2025-12-18

### Added

- **Request Throttling** - Built-in rate limiting to comply with WATS API limits (500 requests/minute)
  - New `RateLimiter` class with sliding window algorithm
  - Thread-safe implementation for concurrent usage
  - Configurable via `configure_throttling()` function
  - Can be disabled for testing with `configure_throttling(enabled=False)`
  - Statistics tracking (total requests, wait time, throttle count)

- **Analytics Typed Models** - New Pydantic models for analytics responses
  - `TopFailedStep` - Failed step statistics
  - `RepairStatistics` - Repair loop metrics
  - `RepairHistoryRecord` - Individual repair records
  - `MeasurementData` - Measurement values with statistics
  - `AggregatedMeasurement` - Time-series measurement aggregations
  - `OeeAnalysisResult` - OEE (Overall Equipment Effectiveness) analysis

- **Analytics Documentation** - Added docstrings with examples to all 23 analytics service methods

### Fixed

- **RootCause Acceptance Tests** - Fixed `DummyRootCauseRepository` to properly inherit from `RootCauseRepository`

## [0.1.0b5] - 2025-12-17

### Fixed

- **CI/CD** - Added `contents: read` permission to publish workflow for private repo checkout.

## [0.1.0b4] - 2025-12-17

### Fixed

- **Release pipeline** - Fixed flake8 `F821` (missing `Path` import) blocking the PyPI publish workflow.

## [0.1.0b3] - 2025-12-17

### Fixed

- **Cross-platform packaging** - Corrected package directory casing to `src/pywats` to avoid Linux/macOS import/install issues.
- **Release hygiene** - Ensured `tests/`, `docs/`, and other dev-only folders are excluded from PyPI artifacts and added publish-time guards.
- **UUT report parsing robustness** - Added a safe fallback for unknown step types and improved tolerance for null numeric values.
- **Query filtering** - Normalized `status=all` to omit the status filter (treat as “no status filter”).

## [0.1.0b2] - 2025-12-15

### Changed

- **Architecture Refactoring** - Internal API separation
  - All internal endpoint implementations now in separate `_internal` files
  - New `AssetRepositoryInternal` and `AssetServiceInternal` for file operations
  - New `ProductionRepositoryInternal` and `ProductionServiceInternal` for MES operations
  - Public repositories delegate to internal repositories for internal endpoints
  - Internal methods accessible via main domain accessor (e.g., `api.asset.upload_blob()`)
  - Note: Later unified so all domains use `api.{domain}.{method}()` pattern

### Fixed

- CompOp export path handling for None values
- TestInstanceConfig field mapping for process_code/test_operation

## [0.1.0b1] - 2025-12-14

### Added

- **PyWATS API Library** (`pywats`)
  - Product management (get, create, update products and revisions)
  - Asset management (equipment tracking, calibration, maintenance)
  - Report submission and querying (UUT/UUR reports in WSJF format)
  - Production/serial number management (units, batches, assemblies)
  - RootCause ticket system (issue tracking and resolution)
  - Software distribution (package management, releases)
  - Statistics and analytics endpoints
  - Station concept for multi-station deployments

- **PyWATS Client Application** (`pywats_client`)
  - Desktop GUI mode (PySide6/Qt)
  - Headless mode for servers and embedded systems (Raspberry Pi)
  - Connection management with encrypted token storage
  - Converter framework for custom file format processing
  - Report queue with offline support
  - HTTP control API for remote management

- **Developer Features**
  - Comprehensive type hints throughout
  - Pydantic models for data validation
  - Structured logging with debug mode
  - Async-ready architecture

### Requirements

- Python 3.10 or later
- **WATS Server 2025.3.9.824 or later**

### Notes

This is a **beta release**. The API is stabilizing but may have breaking changes
before the 1.0 release. Please report issues on GitHub.

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 0.1.0b2 | 2025-12-15 | Beta - Architecture refactoring |
| 0.1.0b1 | 2025-12-14 | Beta - Initial public release |
