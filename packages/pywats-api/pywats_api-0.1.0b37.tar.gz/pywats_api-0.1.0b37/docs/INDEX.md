# PyWATS Documentation

Official documentation for pyWATS - Python API library for WATS.

## Getting Started

- **[Getting Started Guide](GETTING_STARTED.md)** - Complete installation, configuration, and initialization guide
- **[Client Installation](installation/client.md)** - End-user client installation for test stations
- **[Quick Reference](QUICK_REFERENCE.md)** - Common patterns and code snippets
- **[README](../README.md)** - Package overview and quick start
- **[CHANGELOG](../CHANGELOG.md)** - Version history and release notes

## Architecture & Design

**System architecture, integration patterns, and extension points:**

- **[Architecture Overview](ARCHITECTURE.md)** - Complete system design: API, Client, GUI layers; async/sync patterns; deployment modes
- **[Client Architecture](CLIENT_ARCHITECTURE.md)** - Client service internals: IPC, queue system, converters, multi-instance
- **[Integration Patterns](INTEGRATION_PATTERNS.md)** - Practical workflows: station setup, multi-process testing, error recovery, performance optimization

**See these guides to understand:**
- How the three layers (API, Client, GUI) work together
- When to use async vs sync API
- How to extend with custom converters or domains
- Common integration scenarios and best practices

## Domain Guides

Complete documentation for each WATS domain with examples and API reference:

### Core Domains

- **[Product Domain](modules/product.md)** - Products, revisions, BOMs, box build templates, vendors, categories
- **[Asset Domain](modules/asset.md)** - Equipment tracking, calibration, maintenance, hierarchy, logs
- **[Production Domain](modules/production.md)** - Unit lifecycle, serial numbers, assembly, verification, phases
- **[Report Domain](modules/report.md)** - Test reports (UUT/UUR), all step types, querying, attachments

### Analysis & Tracking

- **[Analytics Domain](modules/analytics.md)** - Yield analysis, measurements, Cpk statistics, Unit Flow visualization
- **[Software Domain](modules/software.md)** - Package management, versioning, distribution, tags, virtual folders
- **[RootCause Domain](modules/rootcause.md)** - Issue tracking, defect management, status workflows, priorities
- **[Process Domain](modules/process.md)** - Operation types, test/repair processes, caching

### Identity & Administration

- **[SCIM Domain](modules/scim.md)** - User provisioning from Azure AD, SCIM protocol support

### Detailed Module Guides

Legacy usage guides with comprehensive examples and patterns:

- **[Report Module Guide](usage/REPORT_MODULE.md)** - Detailed report creation and querying
- **[Report Builder](usage/REPORT_BUILDER.md)** - Simple, LLM-friendly report building for converters
- **[Product Module Guide](usage/PRODUCT_MODULE.md)** - Product and BOM management
- **[Production Module Guide](usage/PRODUCTION_MODULE.md)** - Serial number and unit tracking
- **[Asset Module Guide](usage/ASSET_MODULE.md)** - Equipment and calibration management
- **[Software Module Guide](usage/SOFTWARE_MODULE.md)** - Package distribution
- **[RootCause Module Guide](usage/ROOTCAUSE_MODULE.md)** - Ticket and defect tracking
- **[Process Module Guide](usage/PROCESS_MODULE.md)** - Process operations
- **[Box Build Guide](usage/BOX_BUILD_GUIDE.md)** - Assembly and box build workflows

## Deployment & Operations

**Service deployment and containerization:**

- **[Docker Deployment](installation/docker.md)** - Container deployment guide for production and development
- **[Windows Service Setup](installation/windows-service.md)** - Install client as Windows Service (auto-start on boot)
- **[Linux Service Setup](installation/linux-service.md)** - Install client as systemd service (Ubuntu, RHEL, Debian)
- **[macOS Service Setup](installation/macos-service.md)** - Install client as launchd daemon (auto-start on boot)

## For Developers

**Resources for developers extending or troubleshooting pyWATS:**

- **[WATS Domain Knowledge](WATS_DOMAIN_KNOWLEDGE.md)** - Essential domain concepts for AI agents and developers (units, reports, processes, operations)
- **[LLM Converter Guide](LLM_CONVERTER_GUIDE.md)** - Quick reference template for implementing converters
- **[Environment Variables](ENV_VARIABLES.md)** - Using env vars for development and debugging
- **[Error Catalog](ERROR_CATALOG.md)** - Comprehensive error reference with causes, examples, and remediation

**Client GUI Development:**
- **[GUI Configuration](../src/pywats_client/GUI_CONFIGURATION.md)** - Configure GUI tabs, logging, and settings
- **[Headless Operation Guide](../src/pywats_client/control/HEADLESS_GUIDE.md)** - Run on Raspberry Pi, servers, embedded systems

## Quick Reference by Task

### Async vs Sync Usage
See [Getting Started - Async Usage](GETTING_STARTED.md#async-usage) - Use `AsyncWATS` for concurrent requests or `pyWATS` for simple blocking calls

### Creating Test Reports
Start with [Report Domain](modules/report.md) - Learn how to create UUT reports with all step types

### Managing Products & BOMs
See [Product Domain](modules/product.md) - Product creation, revisions, BOMs, box build workflows

### Tracking Units Through Production
See [Production Domain](modules/production.md) - Serial numbers, unit phases, assembly, verification

### Equipment & Calibration
See [Asset Domain](modules/asset.md) - Asset tracking, calibration schedules, maintenance

### Analyzing Yield & Quality
See [Analytics Domain](modules/analytics.md) - Yield calculations, measurement statistics, Cpk analysis

### Software Distribution
See [Software Domain](modules/software.md) - Package management, versioning, releases

### Issue Tracking
See [RootCause Domain](modules/rootcause.md) - Create tickets, track defects, manage workflows

### Operation Types
See [Process Domain](modules/process.md) - Define test/repair operations, process caching

## Tools & Utilities

- **[LLM Converter Guide](LLM_CONVERTER_GUIDE.md)** - Quick reference for LLMs implementing converters
- **[MCP Recommendations](MCP_RECOMMENDATIONS.md)** - Guide for building MCP servers (if needed in future)

## Links

- **GitHub Repository**: https://github.com/olreppe/pyWATS
- **WATS Website**: https://wats.com
- **Virinco**: https://virinco.com
- **PyPI Package**: https://pypi.org/project/pywats-api/

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/olreppe/pyWATS/issues
- Email: support@virinco.com
