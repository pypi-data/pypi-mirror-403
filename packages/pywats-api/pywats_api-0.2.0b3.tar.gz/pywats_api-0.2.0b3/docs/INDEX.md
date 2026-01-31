# PyWATS Documentation

Official documentation for pyWATS - Python API library for WATS.

## Getting Started

- **[Getting Started Guide](getting-started.md)** - Complete installation, configuration, and initialization guide
- **[Quick Reference](reference/quick-reference.md)** - Common patterns and code snippets
- **[README](../README.md)** - Package overview and quick start
- **[CHANGELOG](../CHANGELOG.md)** - Version history and release notes

## Installation

**Choose the right installation for your needs:**

- **[Installation Overview](installation/)** - Decision tree and comparison
- **[API Installation](installation/api.md)** - Python SDK only (~5 MB) - for scripts and direct integration
- **[Client Service](installation/client.md)** - Background service with queue and converters
- **[GUI Application](installation/gui.md)** - Desktop app for monitoring and configuration

## Architecture & Design

**System architecture, integration patterns, and extension points:**

- **[Architecture Overview](guides/architecture.md)** - Complete system design: API, Client, GUI layers; async/sync patterns; deployment modes
- **[Client Architecture](guides/client-architecture.md)** - Client service internals: IPC, queue system, converters, multi-instance
- **[Integration Patterns](guides/integration-patterns.md)** - Practical workflows: station setup, multi-process testing, error recovery, performance optimization
- **[Thread Safety Guide](guides/thread-safety.md)** - Threading and concurrency patterns: thread-safe components, best practices, cross-platform compatibility

**See these guides to understand:**
- How the three layers (API, Client, GUI) work together
- When to use async vs sync API
- Thread safety guarantees and concurrent usage patterns
- How to extend with custom converters or domains
- Common integration scenarios and best practices

## Domain Guides

Complete documentation for each WATS domain with examples and API reference:

### Core Domains

- **[Product Domain](domains/product.md)** - Products, revisions, BOMs, box build templates, vendors, categories
- **[Asset Domain](domains/asset.md)** - Equipment tracking, calibration, maintenance, hierarchy, logs
- **[Production Domain](domains/production.md)** - Unit lifecycle, serial numbers, assembly, verification, phases
- **[Report Domain](domains/report.md)** - Test reports (UUT/UUR), all step types, querying, attachments

### Analysis & Tracking

- **[Analytics Domain](domains/analytics.md)** - Yield analysis, measurements, Cpk statistics, Unit Flow visualization
- **[Software Domain](domains/software.md)** - Package management, versioning, distribution, tags, virtual folders
- **[RootCause Domain](domains/rootcause.md)** - Issue tracking, defect management, status workflows, priorities
- **[Process Domain](domains/process.md)** - Operation types, test/repair processes, caching

### Identity & Administration

- **[SCIM Domain](domains/scim.md)** - User provisioning from Azure AD, SCIM protocol support

### Detailed Domain Guides

Usage guides with comprehensive examples and patterns:

- **[Report Domain Guide](usage/report-domain.md)** - Detailed report creation and querying
- **[Report Builder](usage/report-builder.md)** - Simple, LLM-friendly report building for converters
- **[Product Domain Guide](usage/product-domain.md)** - Product and BOM management
- **[Production Domain Guide](usage/production-domain.md)** - Serial number and unit tracking
- **[Asset Domain Guide](usage/asset-domain.md)** - Equipment and calibration management
- **[Software Domain Guide](usage/software-domain.md)** - Package distribution
- **[RootCause Domain Guide](usage/rootcause-domain.md)** - Ticket and defect tracking
- **[Process Domain Guide](usage/process-domain.md)** - Process operations
- **[Box Build Guide](usage/box-build-guide.md)** - Assembly and box build workflows

## Deployment & Operations

**Service deployment and containerization:**

- **[Docker Deployment](installation/docker.md)** - Container deployment guide for production and development
- **[Windows Service Setup](installation/windows-service.md)** - Install client as Windows Service (auto-start on boot)
- **[Linux Service Setup](installation/linux-service.md)** - Install client as systemd service (Ubuntu, RHEL, Debian)
- **[macOS Service Setup](installation/macos-service.md)** - Install client as launchd daemon (auto-start on boot)

## For Developers

**Resources for developers extending or troubleshooting pyWATS:**

- **[WATS Domain Knowledge](guides/wats-domain-knowledge.md)** - Essential domain concepts for AI agents and developers (units, reports, processes, operations)
- **[LLM Converter Guide](guides/llm-converter-guide.md)** - Quick reference template for implementing converters
- **[Environment Variables](reference/env-variables.md)** - Using env vars for development and debugging
- **[Error Catalog](reference/error-catalog.md)** - Comprehensive error reference with causes, examples, and remediation

**Platform Compatibility:**
- **[Platform Compatibility Guide](platforms/platform-compatibility.md)** - Comprehensive multi-platform deployment matrix
- **[Windows IoT LTSC Guide](platforms/windows-iot-ltsc.md)** - Windows IoT Enterprise LTSC setup

**Client GUI Development:**
- **[GUI Configuration](../src/pywats_client/GUI_CONFIGURATION.md)** - Configure GUI tabs, logging, and settings
- **[Headless Operation Guide](../src/pywats_client/control/HEADLESS_GUIDE.md)** - Run on Raspberry Pi, servers, embedded systems

## Quick Reference by Task

### Async vs Sync Usage
See [Getting Started - Async Usage](getting-started.md#async-usage) - Use `AsyncWATS` for concurrent requests or `pyWATS` for simple blocking calls

### Creating Test Reports
Start with [Report Domain](domains/report.md) - Learn how to create UUT reports with all step types

### Managing Products & BOMs
See [Product Domain](domains/product.md) - Product creation, revisions, BOMs, box build workflows

### Tracking Units Through Production
See [Production Domain](domains/production.md) - Serial numbers, unit phases, assembly, verification

### Equipment & Calibration
See [Asset Domain](domains/asset.md) - Asset tracking, calibration schedules, maintenance

### Analyzing Yield & Quality
See [Analytics Domain](domains/analytics.md) - Yield calculations, measurement statistics, Cpk analysis

### Software Distribution
See [Software Domain](domains/software.md) - Package management, versioning, releases

### Issue Tracking
See [RootCause Domain](domains/rootcause.md) - Create tickets, track defects, manage workflows

### Operation Types
See [Process Domain](domains/process.md) - Define test/repair operations, process caching

## Tools & Utilities

- **[LLM Converter Guide](llm-converter-guide.md)** - Quick reference for LLMs implementing converters

## Links

- **GitHub Repository**: https://github.com/olreppe/pyWATS
- **WATS Website**: https://wats.com
- **Virinco**: https://virinco.com
- **PyPI Package**: https://pypi.org/project/pywats-api/

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/olreppe/pyWATS/issues
- Email: support@virinco.com
