# Documentation Folder Structure

This folder contains **official, user-facing documentation** that ships with `pip install pywats-api`.

## 📚 Published Documentation (in this folder)

### Getting Started
- **[getting-started.md](getting-started.md)** - Complete installation, configuration, logging, and error handling guide
- **[INDEX.md](INDEX.md)** - Documentation index and navigation

### Installation Guides

Choose by component and use case:

- **[installation/](installation/)** - Installation overview with decision tree
  - **[installation/api.md](installation/api.md)** - Python SDK only
  - **[installation/client.md](installation/client.md)** - Client service with queue
  - **[installation/gui.md](installation/gui.md)** - Desktop GUI application
  - **[installation/docker.md](installation/docker.md)** - Container deployment
  - **[installation/windows-service.md](installation/windows-service.md)** - Windows service
  - **[installation/linux-service.md](installation/linux-service.md)** - Linux systemd
  - **[installation/macos-service.md](installation/macos-service.md)** - macOS launchd

### Domain API Documentation
These files are included in the PyPI package:

- **[domains/product.md](domains/product.md)** - Product domain API reference
- **[domains/asset.md](domains/asset.md)** - Asset domain API reference
- **[domains/production.md](domains/production.md)** - Production domain API reference
- **[domains/report.md](domains/report.md)** - Report domain API reference
- **[domains/analytics.md](domains/analytics.md)** - Analytics domain API reference
- **[domains/software.md](domains/software.md)** - Software domain API reference
- **[domains/rootcause.md](domains/rootcause.md)** - RootCause domain API reference
- **[domains/process.md](domains/process.md)** - Process domain API reference

### Domain Usage Guides
Detailed guides with comprehensive examples:

- **[usage/](usage/)** - Detailed domain guides (report-domain.md, product-domain.md, etc.)
  - Detailed usage patterns
  - Advanced examples
  - Factory method documentation

### Documentation Examples
Code snippets and examples embedded in documentation:

- **[examples/](examples/)** - Example code referenced in documentation
  - `basic_usage.py` - Getting started example

## 🔒 Internal Documentation (NOT published)

The following folders are **excluded from the pip package** and only available in the GitHub repository:

- `internal_documentation/` - Architecture, design docs, AI agent knowledge, internal guides
- `domain_health/` - Domain health tracking and scoring (maintainer use only)

These folders are for internal development use only.

## 📁 Folder Structure

```
docs/
├── INDEX.md                    ✅ Published - Documentation index
├── README.md                   ✅ Published - This file
├── getting-started.md          ✅ Published - Getting started guide
├── pyWATS_Documentation.html   ✅ Published - HTML documentation
├── guides/                     ✅ Published - Comprehensive guides
│   ├── architecture.md
│   ├── client-architecture.md
│   ├── integration-patterns.md
│   ├── llm-converter-guide.md
│   └── wats-domain-knowledge.md
├── reference/                  ✅ Published - Quick references
│   ├── quick-reference.md
│   ├── env-variables.md
│   └── error-catalog.md
├── platforms/                  ✅ Published - Platform-specific docs
│   ├── platform-compatibility.md
│   └── windows-iot-ltsc.md
├── domains/                    ✅ Published - Domain API docs
│   ├── product.md
│   ├── asset.md
│   ├── report.md
│   └── ...
├── usage/                      ✅ Published - Detailed domain guides
│   ├── report-domain.md
│   ├── product-domain.md
│   └── ...
├── installation/               ✅ Published - Installation guides
│   ├── client.md
│   ├── docker.md
│   └── ...
├── internal_documentation/     ❌ NOT Published - Internal docs
│   ├── archived/
│   ├── WIP/
│   └── ...
└── domain_health/              ❌ NOT Published - Health tracking
```

## ✅ Rule of Thumb

- **Files/folders in `docs/` root** → Published with pip package
- **Folders: `guides/`, `reference/`, `platforms/`, `usage/`, `domains/`, `installation/`** → Published (user-facing)
- **Folders: `internal_documentation/`, `domain_health/`** → NOT Published (GitHub only)

## 🔄 Moving Documents

When creating new documentation:

- **User-facing API docs** → Put in `docs/domains/`
- **Detailed usage guides** → Put in `docs/usage/`
- **Installation guides** → Put in `docs/installation/`
- **Architecture/patterns** → Put in `docs/guides/`
- **Quick references** → Put in `docs/reference/`
- **Platform-specific docs** → Put in `docs/platforms/`
- **Internal architecture/design** → Put in `docs/internal_documentation/`

## 📦 Packaging

Controlled by `MANIFEST.in` in the project root:
- **Includes:** `docs/*.md`, `docs/guides/`, `docs/reference/`, `docs/platforms/`, `docs/usage/`, `docs/domains/`, `docs/installation/`
- **Excludes:** `docs/internal_documentation/`, `docs/domain_health/`
