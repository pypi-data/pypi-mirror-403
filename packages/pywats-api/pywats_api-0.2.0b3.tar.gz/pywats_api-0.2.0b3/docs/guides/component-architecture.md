# Component Architecture & Versioning Strategy

## Current Component Structure

```
pywats-api (single package)
├── pywats/              # Core API library (sync + async)
├── pywats_client/       # Client application
│   ├── core/            # Configuration, auth
│   ├── service/         # Background service (headless-capable)
│   ├── gui/             # Qt GUI (requires PySide6)
│   ├── converters/      # File converters
│   ├── queue/           # Persistent queue
│   ├── control/         # CLI interface
│   └── io.py            # File I/O utilities
├── pywats_cfx/          # CFX integration (optional)
└── pywats_events/       # Event system (optional)
```

## Dependency Analysis

### 1. `pywats` (Core API)
**Dependencies:** httpx, pydantic, python-dateutil, attrs
**Dependents:** pywats_client, pywats_cfx, pywats_events
**Coupling:** LOW - Pure API library, no dependencies on other internal packages

### 2. `pywats_client/service/` (Background Service)
**Dependencies:** pywats (AsyncWATS), watchdog, aiofiles
**Qt Dependencies:** NONE (after IPC refactoring)
**Coupling:** MEDIUM - Depends on pywats, but no GUI coupling

### 3. `pywats_client/gui/` (Qt GUI)
**Dependencies:** PySide6, qasync, pywats_client.service
**Coupling:** HIGH - Tightly coupled to service layer

### 4. `pywats_client/converters/` (File Converters)
**Dependencies:** pywats (report models)
**Coupling:** LOW - Can be used independently

## Current Coupling Issues

### GUI ↔ Service Coupling
```
gui/main_window.py → service/async_ipc_client.py
gui/async_api_mixin.py → pywats (pyWATS, AsyncWATS)
```

### Service ↔ Core Coupling
```
service/async_client_service.py → pywats (AsyncWATS)
service/async_pending_queue.py → pywats (AsyncWATS)
service/async_converter_pool.py → pywats (AsyncWATS)
```

## Recommended Package Split

To enable independent versioning and releases:

### Option A: Three Packages (Recommended)

```
1. pywats (v0.x.x) - Core API
   - pywats/
   - Dependencies: httpx, pydantic, attrs
   - Can release independently
   - Stable interface for external users

2. pywats-client-core (v0.x.x) - Headless Client
   - pywats_client/ (excluding gui/)
   - Dependencies: pywats, watchdog, aiofiles
   - Can run on Raspberry Pi, servers, embedded
   - No Qt dependency

3. pywats-client-gui (v0.x.x) - Desktop GUI
   - pywats_client/gui/
   - Dependencies: pywats-client-core, PySide6, qasync
   - Desktop-only (Windows, macOS, Linux desktop)
```

### Option B: Two Packages (Simpler)

```
1. pywats (v0.x.x) - Core API
   - Same as Option A

2. pywats-client (v0.x.x) - Full Client
   - pywats_client/ (all)
   - Optional dependencies:
     - [gui]: PySide6, qasync
     - [headless]: watchdog, aiofiles only
```

## Current Implementation (pyproject.toml)

```toml
[project.optional-dependencies]
# Full client with Qt GUI
client = [
    "PySide6>=6.4.0",
    "watchdog>=3.0.0",
    "aiofiles>=23.0.0",
    "qasync>=0.27.0",
]
# Headless client without Qt
client-headless = [
    "watchdog>=3.0.0",
    "aiofiles>=23.0.0",
]
```

This already supports headless mode! Install with:
- `pip install pywats-api[client]` - Full GUI
- `pip install pywats-api[client-headless]` - Headless only

## Recommended Versioning Strategy

### Single Version (Current)
All components share one version number.
- **Pro:** Simple, single release
- **Con:** Minor GUI fix requires full release

### Semantic Versioning with Tags (Recommended)
Keep single package but use more granular versioning:

```
Version: 0.1.0-beta.39

Breaking changes:
- pywats API: Major version bump (0.x → 1.0)
- pywats_client: Major version bump
- GUI only: Patch version bump (0.1.x → 0.1.y)
```

### Independent Packages (Future)
If decoupling is critical:

1. Split `pywats` into its own package
2. Split `pywats-client-core` (service + converters)
3. Keep GUI as optional dependency

## Recommended Actions

### Short-term (Current Sprint)
1. ✅ Remove Qt from service layer (DONE - async IPC)
2. ✅ Document headless installation option
3. Keep single package with optional dependencies

### Medium-term (Next Release)
1. Add lazy imports for GUI components
2. Ensure `pywats_client service` works without PySide6
3. Add runtime check: only import GUI when needed

### Long-term (If Needed)
1. Split into separate packages on PyPI
2. Independent version numbers
3. Cross-package compatibility matrix

## Code Changes for Better Decoupling

### 1. Lazy GUI Import (main.py)
```python
def _run_gui_mode(config):
    # Only import GUI when running in GUI mode
    try:
        from .gui.app import run_gui
    except ImportError as e:
        print("GUI not available. Install with: pip install pywats-api[client]")
        raise SystemExit(1)
    
    return run_gui(config)
```

### 2. Optional Qt Check (`__main__.py`)
```python
def check_gui_available() -> bool:
    """Check if GUI dependencies are installed."""
    try:
        import PySide6
        import qasync
        return True
    except ImportError:
        return False
```

### 3. Service Entry Point (`service/__main__.py`)
```python
# Service can run completely headless
# No GUI imports at module level
from .async_client_service import AsyncClientService
from .client_service import ClientService

# GUI-specific features only when needed
def with_tray():
    """Run service with system tray (requires Qt)."""
    from .service_tray import run_with_tray
    run_with_tray()
```

## Summary

**Current State:**
- Single package `pywats-api`
- Optional dependencies for GUI vs headless
- Service layer now Qt-free (after IPC refactoring)

**Recommendation:**
- Keep single package for simplicity
- Use optional dependencies for install variants
- Version with semantic versioning
- Only split packages if truly needed for deployment constraints

**Why Not Split Now:**
1. Maintenance overhead of multiple packages
2. Version compatibility matrix complexity
3. Current optional deps already work
4. Most users want full package anyway
