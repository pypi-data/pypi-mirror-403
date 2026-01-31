# Changelog

All notable changes to PyWATS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

For detailed migration instructions, see [MIGRATION.md](MIGRATION.md).
For beta version history (b1-b38), see [CHANGELOG-BETA.md](CHANGELOG-BETA.md).

<!-- 
AGENT INSTRUCTIONS: See CONTRIBUTING.md for changelog management rules.
- Keep entries concise (one-liners, no code blocks)
- Add migration examples to MIGRATION.md, not here
- Link breaking changes to MIGRATION.md sections
-->

---

## [0.2.0b3] - 2026-01-29

### Added
- **Documentation**: Comprehensive architecture review documents for code quality and maintenance
  - API Architecture Review (650+ lines) - 9.5/10 rating
  - Client Architecture Review (850+ lines) - 9.0/10 rating
  - Cross-Platform Support Review (1000+ lines) - 9.0/10 rating
  - GUI Architecture Review (600+ lines) - 8.0/10 rating

### Removed
- Obsolete internal documentation (NAMING_CONSISTENCY_REPORT.md)

---

## [0.2.0b2] - 2026-01-29

### Added
- Test coverage improvements for pywats_client: new tests for `io.py`, `config_manager.py`, `connection_config.py`, `exceptions.py`, `converters/models.py`, and `exit_codes.py` modules
- Coverage configuration: excluded GUI code from coverage metrics (gui/, service_tray.py, windows_service.py, diagnostics.py) to focus on testable modules
- **Documentation**: AI coding attribution and project credits (Integration Architect: Ola Lund Reppe)
- **Documentation**: Critical test suite warning - tests must NEVER be run on production servers
- **Threading**: Comprehensive thread safety documentation (`docs/guides/thread-safety.md`)
- **Threading**: Thread safety tests for TTLCache (`tests/cross_cutting/test_cache_threading.py` - 8 tests)
- **Threading**: Parallel execution stress tests (`tests/integration/test_parallel_stress.py` - 16 tests)
- **Threading**: Enhanced docstrings with thread safety guarantees for `MemoryQueue`, `TTLCache`, `parallel_execute`

### Changed
- **Company branding**: Updated from Virinco AS to The WATS Company AS across all documentation, deployment configs, and copyright notices
- **Performance**: `run_sync()` now uses pooled ThreadPoolExecutor (4 workers) instead of creating new executor per call
- **Performance**: `MemoryQueue.__iter__()` returns snapshot to avoid holding lock during iteration
- **Threading**: `AsyncTTLCache` refactored to remove inheritance and dual locking (asyncio.Lock only, no threading.RLock)

### Fixed
- Python 3.11 typing compatibility: `Result[T]` type alias cannot be subscripted on Union types. Changed `parallel_execute` return type to use `Union[Success[T], Failure]` directly.

---

## [Unreleased]

### Added
- **Async Client Architecture**: Complete async-first implementation for WATS Client
  - `AsyncClientService`: Main async service controller using asyncio event loop
  - `AsyncConverterPool`: Concurrent file conversion with asyncio.Semaphore (10 concurrent)
  - `AsyncPendingQueue`: Concurrent report uploads (5 concurrent vs sequential)
  - `AsyncAPIMixin`: GUI helper for async API calls with auto sync/async detection
- `qasync` integration for Qt + asyncio in GUI mode
- GUI auto-test: Connection page automatically tests server connectivity on startup
- `AttachmentIO` class in `pywats_client.io` for file-based attachment operations
- `Step.add_attachment()` method for memory-only attachment handling
- `AttachmentMetadata` class (renamed from `Attachment` in models.py for clarity)
- `QueueItemStatus` enum for unified queue states
- `RetryHandler` class for unified retry execution
- Platform native installers (Windows MSI, macOS PKG/DMG, standalone executables)
- Multi-platform deployment infrastructure (systemd, launchd, Windows Service)
- Enhanced error messages with troubleshooting hints
- Layered event architecture (`pywats_events`, `pywats_cfx`)
- WATS 25.3 Asset module enhancements (calibration/maintenance, count management)
- Alarm and notification logs API

### Fixed
- GUI responsiveness: qasync event loop integration enables async operations without blocking UI
- Connection test now follows HTTP redirects (301/302)
- Connection page status colors: "Connected"/"Online" now display in green
- "Offline"/"Disconnected" states now display in gray instead of red
- **GUI navigation**: Dashboard and API Settings pages now visible in sidebar menu
- **GUI signal connection**: Fixed "Setup" vs "General" page name mismatch

### Changed
- **File I/O architecture**: `pywats` is now memory-only; file operations in `pywats_client`
- **GUI pages reorganized**: Unused domain pages (Asset, Product, Production, RootCause) moved to `pages/unused/`
- Documentation reorganized into `docs/guides/`, `docs/reference/`, `docs/platforms/`, `docs/domains/`
- Core modules renamed: `batch` → `parallel`, `batching` → `coalesce`
- Terminology standardized: "Module" → "Domain"
- Test suite reorganized into domain-based structure
- Domain health grading upgraded to 60-point scale

### Removed (Breaking)
- `Attachment.from_file()` - Use `AttachmentIO.from_file()` ([migration](MIGRATION.md#v010b40---file-io-separation))
- `Step.attach_file()` - Use `AttachmentIO.from_file()` + `step.add_attachment()`
- `UURReport.attach_file()` - Use `attach_bytes()` instead
- `SimpleQueue` - Use `pywats_client.ClientService` for queuing
- `AsyncReportService` offline methods (`submit_offline`, `process_queue`, `offline_fallback`)
- Legacy UUR classes: `UURAttachment`, `Failure`, `UURPartInfo`, `FailCode`, `MiscUURInfo` ([migration](MIGRATION.md#v010b40---deprecated-uur-classes-removed))
- `gui/widgets/instance_selector.py` - Unused widget removed

### Deprecated
- UUR legacy classes marked for removal (now removed - see above)

---

## Beta Archive

All beta releases (0.1.0b1 through 0.1.0b38) have been archived to [CHANGELOG-BETA.md](CHANGELOG-BETA.md).

Key milestones from beta:
- **b38** - Report refactoring, type safety, queue architecture
- **b35** - Docker containerization, client test suite
- **b34** - Async-first architecture, batch operations, pagination
- **b32** - Unified API pattern (removed `*_internal` accessors)
- **b28** - Exception handling overhaul, ImportMode
- **b10** - Agent analysis tools
- **b1** - Initial release with all core domains
