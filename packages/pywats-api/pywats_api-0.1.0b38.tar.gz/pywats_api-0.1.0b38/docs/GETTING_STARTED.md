# Getting Started Guide

Complete guide to installing, configuring, and initializing pyWATS.

## Table of Contents

- [Installation](#installation)
- [API Initialization](#api-initialization)
- [Async Usage](#async-usage)
- [Authentication](#authentication)
- [Logging Configuration](#logging-configuration)
- [Exception Handling](#exception-handling)
- [Performance Optimization](#performance-optimization)
- [Internal API Usage](#internal-api-usage)
- [Client Installation](#client-installation)
- [Batch Operations & Pagination](#batch-operations--pagination)

---

## Installation

### Library Only (API Access)

For Python scripts and applications using the WATS API:

```bash
pip install pywats-api
```

### With GUI Client

For desktop applications with Qt-based GUI (Windows, macOS, Linux):

```bash
pip install pywats-api[client]
```

### Headless Client

For servers, Raspberry Pi, and embedded systems (no Qt/GUI):

```bash
pip install pywats-api[client-headless]
```

### Development Installation

From source for development:

```bash
git clone https://github.com/olreppe/pyWATS.git
cd pyWATS
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install -e ".[dev]"
```

---

## API Initialization

### Basic Initialization

```python
from pywats import pyWATS

# Initialize with credentials
api = pyWATS(
    base_url="https://your-wats-server.com",
    token="your_base64_token"  # Base64 of "username:password"
)

# Test connection
if api.test_connection():
    print(f"Connected! Server version: {api.get_version()}")
```

### Using Environment Variables

```python
import os
from pywats import pyWATS

# Set environment variables
os.environ['WATS_BASE_URL'] = 'https://your-wats-server.com'
os.environ['WATS_AUTH_TOKEN'] = 'your_base64_token'

# Initialize from environment
api = pyWATS()  # Automatically reads from environment
```

Or create a `.env` file:

```env
WATS_BASE_URL=https://your-wats-server.com
WATS_AUTH_TOKEN=your_base64_token
```

```python
from dotenv import load_dotenv
from pywats import pyWATS

load_dotenv()  # Load from .env file
api = pyWATS()
```

### Configuration Options

```python
from pywats import pyWATS, RetryConfig
from pywats.core.exceptions import ErrorMode

api = pyWATS(
    base_url="https://your-wats-server.com",
    token="your_token",
    
    # Optional: Custom timeout (default: 30 seconds)
    timeout=60,
    
    # Optional: Process cache refresh interval (default: 300 seconds)
    process_refresh_interval=600,
    
    # Optional: Error handling mode (default: STRICT)
    error_mode=ErrorMode.STRICT,  # or ErrorMode.LENIENT
    
    # Optional: Retry configuration (default: enabled with 3 attempts)
    retry_enabled=True,  # Set to False to disable
    # Or for advanced configuration:
    # retry_config=RetryConfig(max_attempts=5, base_delay=2.0)
)
```

### Automatic Retry

The library automatically retries requests that fail due to transient errors:

- **Connection errors** - Network unavailable, DNS failures
- **Timeout errors** - Server took too long to respond
- **HTTP 429** - Too Many Requests (respects `Retry-After` header)
- **HTTP 500/502/503/504** - Server errors, often transient during deployments

Retry uses **exponential backoff with jitter** to avoid thundering herd:

| Attempt | Delay (approx) |
|---------|----------------|
| 1 | 0-1 second |
| 2 | 0-2 seconds |
| 3 | 0-4 seconds |
| (fail) | Exception raised |

**Important:** Only idempotent methods (GET, PUT, DELETE) are retried. POST is never retried automatically to prevent duplicate creates.

```python
from pywats import pyWATS, RetryConfig

# Disable retry entirely
api = pyWATS(
    base_url="https://...",
    token="...",
    retry_enabled=False
)

# Custom retry configuration
config = RetryConfig(
    max_attempts=5,      # Try up to 5 times
    base_delay=2.0,      # Start with 2 second delay
    max_delay=60.0,      # Cap delay at 60 seconds
    jitter=True,         # Add randomness to avoid thundering herd
)
api = pyWATS(
    base_url="https://...",
    token="...",
    retry_config=config
)

# Check retry statistics
print(api.retry_config.stats)
# {'total_retries': 3, 'total_retry_time': 4.5}
```

### Error Handling Modes

The library supports two error handling modes that control how missing data and 404 responses are handled:

#### STRICT Mode (Default - Recommended for Production)

```python
from pywats import pyWATS
from pywats.core.exceptions import ErrorMode

api = pyWATS(
    base_url="https://your-wats-server.com",
    token="your_token",
    error_mode=ErrorMode.STRICT  # Default, can be omitted
)
```

**Behavior:**
- **404 errors** → Raises `NotFoundError`
- **Empty responses** (200 with no data) → Raises `EmptyResponseError`
- **All 4xx/5xx errors** → Raises appropriate exception
- **If no exception** → You have valid data (guaranteed)

**Use STRICT when:**
- Writing production code that needs certainty
- Validating data existence
- Critical operations where failures must be explicit
- You want type safety (no None checks needed)

**Example:**
```python
from pywats import NotFoundError

try:
    product = api.product.get_product("WIDGET-001")
    # If we reach here, product is DEFINITELY valid
    print(f"Found: {product.part_number}")
except NotFoundError:
    print("Product doesn't exist - handle explicitly")
```

#### LENIENT Mode (Recommended for Scripts/Exploration)

```python
from pywats import pyWATS
from pywats.core.exceptions import ErrorMode

api = pyWATS(
    base_url="https://your-wats-server.com",
    token="your_token",
    error_mode=ErrorMode.LENIENT
)
```

**Behavior:**
- **404 errors** → Returns `None` (no exception)
- **Empty responses** → Returns `None` (no exception)
- **Actual errors** (5xx, 400, 401, 403, 409) → Still raises exceptions
- **Must check for None** before using returned data

**Use LENIENT when:**
- Writing exploratory scripts
- Querying optional data
- Batch processing where some items may not exist
- You want simpler code with less try/except boilerplate

**Example:**
```python
# Simpler code - no try/except needed for missing data
product = api.product.get_product("WIDGET-001")

if product is None:
    print("Product doesn't exist")
else:
    print(f"Found: {product.part_number}")
```

#### Mode Comparison

| Aspect | STRICT Mode | LENIENT Mode |
|--------|-------------|--------------|
| **404 Response** | Raises `NotFoundError` | Returns `None` |
| **Empty Response** | Raises `EmptyResponseError` | Returns `None` |
| **Server Error (5xx)** | Raises `ServerError` | Raises `ServerError` |
| **Validation Error (400)** | Raises `ValidationError` | Raises `ValidationError` |
| **Auth Error (401)** | Raises `AuthenticationError` | Raises `AuthenticationError` |
| **Permission Error (403)** | Raises `AuthorizationError` | Raises `AuthorizationError` |
| **Conflict (409)** | Raises `ConflictError` | Raises `ConflictError` |
| **Return Type** | `Model` or raises | `Model | None` |
| **None Checks** | Not needed | Required |
| **Best For** | Production code | Scripts/exploration |

#### Choosing the Right Mode

```python
# Production code - use STRICT for explicit error handling
from pywats.core.exceptions import ErrorMode

api_prod = pyWATS(..., error_mode=ErrorMode.STRICT)

try:
    product = api_prod.product.get_product(part_number)
    # Guaranteed to have valid product here
    process_product(product)
except NotFoundError as e:
    log_error(f"Product not found: {e}")
    send_alert(...)
except ValidationError as e:
    log_error(f"Invalid data: {e}")

# Exploratory script - use LENIENT for simpler code
api_explore = pyWATS(..., error_mode=ErrorMode.LENIENT)

for part_number in candidate_parts:
    product = api_explore.product.get_product(part_number)
    if product:  # Simple None check
        print(f"Found: {product.part_number}")
    # Missing products are silently skipped
```

### Station Configuration

Configure test station identity:

```python
from pywats import pyWATS, Station, StationConfig, Purpose

# Configure station
station = Station(
    config=StationConfig(
        station_name="ICT-01",
        location="Production Line A"
    )
)

# Initialize with station
api = pyWATS(
    base_url="https://your-wats-server.com",
    token="your_token",
    station=station
)

# Station is automatically used in reports
from pywats.tools.test_uut import TestUUT

uut = TestUUT(
    part_number="WIDGET-001",
    serial_number="SN-12345",
    revision="A",
    operator="John Doe",
    purpose=Purpose.TEST  # or 10
)
# Station info automatically filled from api.station
```

---

## Async Usage

pyWATS supports both synchronous and asynchronous usage patterns. The library is designed 
with an **async-first architecture** where all business logic lives in async services, 
and sync services are thin wrappers.

### Synchronous Usage (Default)

The standard synchronous API is the easiest way to use pyWATS:

```python
from pywats import pyWATS

api = pyWATS(base_url="https://...", token="...")

# Synchronous calls - simple and blocking
products = api.product.get_products()
unit = api.production.get_unit("SN-12345", "WIDGET-001")
```

### Asynchronous Usage

For high-performance applications, use the async API directly:

```python
import asyncio
from pywats import AsyncWATS

async def main():
    # Create async client
    async with AsyncWATS(base_url="https://...", token="...") as api:
        # Async calls - non-blocking
        products = await api.product.get_products()
        unit = await api.production.get_unit("SN-12345", "WIDGET-001")
        
        # Concurrent requests
        product, unit, assets = await asyncio.gather(
            api.product.get_product("WIDGET-001"),
            api.production.get_unit("SN-12345", "WIDGET-001"),
            api.asset.get_assets(top=10)
        )

asyncio.run(main())
```

### Using run_sync() for Mixed Code

When you have async code but need to call it from sync context:

```python
from pywats.core.sync_runner import run_sync
from pywats import AsyncWATS

async def fetch_data():
    async with AsyncWATS(base_url="https://...", token="...") as api:
        return await api.product.get_products()

# Call async code from sync context
products = run_sync(fetch_data())
```

### Service Architecture

All domains follow the same pattern:

| Component | Description |
|-----------|-------------|
| `AsyncXxxService` | Source of truth - all business logic |
| `XxxService` | Thin sync wrapper using `run_sync()` |
| `AsyncXxxRepository` | Async data access layer |

```python
# Both use the same underlying logic
from pywats.domains.product.service import ProductService           # Sync
from pywats.domains.product.async_service import AsyncProductService  # Async
```

---

## Authentication

### Token Generation

pyWATS uses Base64-encoded credentials:

```python
import base64

username = "your_username"
password = "your_password"

# Create token
credentials = f"{username}:{password}"
token = base64.b64encode(credentials.encode()).decode()

print(f"Token: {token}")
```

### Using in API

```python
from pywats import pyWATS

api = pyWATS(
    base_url="https://your-wats-server.com",
    token=token  # Use generated token
)
```

### Token Security

**Best Practices:**

1. **Never hardcode credentials** in source code
2. **Use environment variables** for production
3. **Use .env files** for development (add to .gitignore)
4. **Rotate tokens** regularly
5. **Use separate tokens** for different environments

```python
# ❌ DON'T DO THIS
api = pyWATS(base_url="https://...", token="dXNlcjpwYXNz")

# ✅ DO THIS
import os
api = pyWATS(
    base_url=os.getenv('WATS_BASE_URL'),
    token=os.getenv('WATS_AUTH_TOKEN')
)
```

---

## Logging Configuration

### Quick Debug Mode

Enable detailed logging for troubleshooting:

```python
from pywats import pyWATS, enable_debug_logging

# Enable debug logging before creating API instance
enable_debug_logging()

api = pyWATS(base_url="...", token="...")
```

This shows:
- HTTP requests and responses
- API calls to WATS server
- Data serialization/deserialization
- Repository and service operations

### Custom Logging Configuration

```python
import logging
from pywats import pyWATS

# Configure logging your way
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pywats.log'),
        logging.StreamHandler()
    ]
)

# Set pyWATS logger to DEBUG
logging.getLogger('pywats').setLevel(logging.DEBUG)

# Or be more specific
logging.getLogger('pywats.http_client').setLevel(logging.DEBUG)
logging.getLogger('pywats.domains.product').setLevel(logging.INFO)

api = pyWATS(base_url="...", token="...")
```

### Log Levels

| Level | Use Case | Output |
|-------|----------|--------|
| DEBUG | Development, troubleshooting | All details including HTTP requests |
| INFO | Normal operation | Important operations and status |
| WARNING | Production monitoring | Warnings and potential issues |
| ERROR | Minimal logging | Errors only |

### Example Log Output

```
2026-01-08 14:30:15 - pywats.http_client - INFO - GET https://wats.example.com/api/Product/1234
2026-01-08 14:30:15 - pywats.http_client - DEBUG - Response: 200 OK (1234 bytes)
2026-01-08 14:30:15 - pywats.domains.product - DEBUG - Retrieved product: WIDGET-001
```

### Disable Logging

```python
import logging

# Disable all pyWATS logging
logging.getLogger('pywats').setLevel(logging.CRITICAL)
```

---

## Exception Handling

### Exception Hierarchy

pyWATS provides a comprehensive exception hierarchy for precise error handling:

```
PyWATSError                      # Base exception for all pyWATS errors
├── AuthenticationError          # Authentication failed (401)
├── AuthorizationError           # Permission denied (403)
├── NotFoundError                # Resource not found (404)
├── ValidationError              # Invalid request data (400)
├── ConflictError                # Resource conflict (409)
├── EmptyResponseError           # Empty response in STRICT mode (200 with no data)
├── ServerError                  # Server-side error (5xx)
├── ConnectionError              # Network/connection failure
└── TimeoutError                 # Request timeout
```

All exceptions include:
- **message**: Human-readable error description
- **operation**: Name of the operation that failed (e.g., "get_product")
- **details**: Additional context without HTTP internals
- **cause**: Original exception if wrapping another error

### Basic Error Handling

```python
from pywats import pyWATS, PyWATSError, AuthenticationError

try:
    api = pyWATS(base_url="https://...", token="...")
    product = api.product.get_product("WIDGET-001")
    
except AuthenticationError:
    print("Invalid credentials - check your token")
    
except PyWATSError as e:
    print(f"WATS API error: {e}")
    print(f"Operation: {e.operation}")
    print(f"Details: {e.details}")
    
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Comprehensive Exception Handling

```python
from pywats import (
    pyWATS, 
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    ConflictError,
    EmptyResponseError,
    ServerError,
    ConnectionError,
    TimeoutError,
    PyWATSError
)

try:
    api = pyWATS(base_url="https://...", token="...")
    product = api.product.get_product("WIDGET-001")
    
except AuthenticationError as e:
    # 401 - Invalid credentials
    print(f"Authentication failed: {e.message}")
    # Action: Verify token, re-authenticate
    
except AuthorizationError as e:
    # 403 - No permission
    print(f"Permission denied: {e.message}")
    # Action: Check user permissions, request access
    
except NotFoundError as e:
    # 404 - Resource doesn't exist (STRICT mode only)
    print(f"Not found: {e.resource_type} '{e.identifier}'")
    # Action: Verify identifier, create resource
    
except ValidationError as e:
    # 400 - Invalid request data
    print(f"Validation error: {e.message}")
    if e.field:
        print(f"  Field: {e.field}")
    if e.value:
        print(f"  Value: {e.value}")
    # Action: Fix input data, check API documentation
    
except ConflictError as e:
    # 409 - Resource conflict
    print(f"Conflict: {e.message}")
    # Action: Resolve conflict, retry with updated data
    
except EmptyResponseError as e:
    # 200 with empty body (STRICT mode only)
    print(f"Empty response: {e.message}")
    # Action: Verify query parameters, switch to LENIENT mode
    
except ServerError as e:
    # 5xx - Server-side error
    print(f"Server error: {e.message}")
    if e.status_code:
        print(f"  Status: {e.status_code}")
    # Action: Retry, contact support if persistent
    
except ConnectionError as e:
    # Network failure
    print(f"Connection failed: {e.message}")
    # Action: Check network, verify URL
    
except TimeoutError as e:
    # Request timeout
    print(f"Request timed out: {e.message}")
    # Action: Increase timeout, check network
    
except PyWATSError as e:
    # Catch-all for other errors
    print(f"WATS error: {e.message}")
    print(f"Operation: {e.operation}")
    print(f"Details: {e.details}")
```

### Error Mode Impact on Exceptions

The `error_mode` parameter affects which exceptions are raised:

```python
from pywats import pyWATS, NotFoundError, EmptyResponseError
from pywats.core.exceptions import ErrorMode

# STRICT mode - raises exceptions for missing data
api_strict = pyWATS(..., error_mode=ErrorMode.STRICT)

try:
    product = api_strict.product.get_product("UNKNOWN")
except NotFoundError:
    # This WILL be raised in STRICT mode
    print("Product not found")

try:
    product = api_strict.product.get_product("EMPTY-RESULT")
except EmptyResponseError:
    # This WILL be raised in STRICT mode
    print("Query returned no data")

# LENIENT mode - returns None for missing data
api_lenient = pyWATS(..., error_mode=ErrorMode.LENIENT)

product = api_lenient.product.get_product("UNKNOWN")
# Returns None - no NotFoundError raised

if product is None:
    print("Product not found or empty")
```

**Exception Matrix by Mode:**

| Error Type | STRICT Mode | LENIENT Mode |
|------------|-------------|--------------|
| 404 Not Found | Raises `NotFoundError` | Returns `None` |
| Empty Response | Raises `EmptyResponseError` | Returns `None` |
| 400 Validation | Raises `ValidationError` | Raises `ValidationError` |
| 401 Auth | Raises `AuthenticationError` | Raises `AuthenticationError` |
| 403 Permission | Raises `AuthorizationError` | Raises `AuthorizationError` |
| 409 Conflict | Raises `ConflictError` | Raises `ConflictError` |
| 5xx Server Error | Raises `ServerError` | Raises `ServerError` |
| Network Failure | Raises `ConnectionError` | Raises `ConnectionError` |
| Timeout | Raises `TimeoutError` | Raises `TimeoutError` |
```

### Retry Logic

```python
import time
from pywats import pyWATS, ConnectionError, ServerError

def get_product_with_retry(api, part_number, max_retries=3):
    """Get product with automatic retry on network errors"""
    
    for attempt in range(max_retries):
        try:
            return api.product.get_product(part_number)
            
        except (ConnectionError, ServerError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise  # Re-raise on final attempt
    
    return None

# Use it
try:
    product = get_product_with_retry(api, "WIDGET-001")
except PyWATSError as e:
    print(f"Failed after retries: {e}")
```

### Validation Errors

```python
from pywats import ValidationError
from pywats.tools.test_uut import TestUUT

try:
    # Invalid data
    uut = TestUUT(
        part_number="",  # Empty part number - will raise ValidationError
        serial_number="SN-12345",
        revision="A"
    )
    
except ValidationError as e:
    print(f"Validation failed: {e}")
    # Handle gracefully - prompt user, use defaults, etc.
```

---

## Client Installation

### GUI Client (Desktop)

#### Prerequisites

- Python 3.10 or later
- Qt6 support (Windows, macOS, Linux with display)

#### Installation

```bash
# Install with client support
pip install pywats-api[client]

# Launch GUI
python -m pywats_client
```

Or from command line:

```bash
pywats-client
```

#### First-Time Setup

1. Launch the client
2. Go to **Setup** tab
3. Configure:
   - Server URL: `https://your-wats-server.com`
   - API Token: Your Base64 token
   - Station Name: `YOUR-STATION-01`
4. Click **Save**
5. Click **Test Connection**

See **[GUI Configuration Guide](../src/pywats_client/GUI_CONFIGURATION.md)** for detailed setup.

#### Using the File Menu

The GUI includes helpful controls in the **File** menu:

**Restart GUI** (Ctrl+R)
- Restarts only the GUI application
- Service continues running in the background
- Configuration is reloaded automatically
- Useful after GUI code changes during development

**Stop Service** (Ctrl+Shift+S)
- Sends stop command to the service process
- Stops all file watching and converter workers
- GUI remains open but shows [Disconnected] status
- Useful before making service code changes

**Exit** (Alt+F4)
- Closes the GUI application
- Service continues running if started separately

**Window Title Status:**
- Shows `[Connected]` when service is running
- Shows `[Disconnected]` when service is not reachable

---

### Headless Client (No GUI)

For servers, Raspberry Pi, and embedded systems.

#### Installation

```bash
# Install headless client (no Qt)
pip install pywats-api[client-headless]
```

#### Initialize Configuration

```bash
# Interactive setup
pywats-client config init

# Or non-interactive
pywats-client config init \
    --server-url https://wats.example.com \
    --api-token YOUR_TOKEN \
    --station-name RASPBERRY-PI-01 \
    --non-interactive
```

#### Test Connection

```bash
pywats-client test-connection
```

#### Start Service

```bash
# Foreground (for testing)
pywats-client start

# With HTTP API for remote management
pywats-client start --api --api-port 8765

# As daemon (Linux/Unix)
pywats-client start --daemon
```

#### Configuration File

Location:
- **Windows:** `%APPDATA%\pyWATS_Client\config.json`
- **Linux/Mac:** `~/.config/pywats_client/config.json`

Example:

```json
{
  "service_address": "https://wats.example.com",
  "api_token": "your_token",
  "station_name": "RASPBERRY-PI-01",
  "log_level": "INFO"
}
```

#### CLI Commands

```bash
# Configuration
pywats-client config show
pywats-client config get station_name
pywats-client config set log_level DEBUG

# Service control
pywats-client status
pywats-client start
pywats-client stop

# Converters
pywats-client converters list
pywats-client converters enable my_converter
```

See **[Headless Operation Guide](../src/pywats_client/control/HEADLESS_GUIDE.md)** for complete documentation.

---

## Complete Example

Putting it all together:

```python
"""
Complete example of pyWATS initialization with logging and error handling
"""

import os
import logging
from dotenv import load_dotenv
from pywats import (
    pyWATS,
    enable_debug_logging,
    PyWATSError,
    AuthenticationError,
    Station,
    StationConfig,
    Purpose
)

def initialize_api():
    """Initialize pyWATS API with proper configuration"""
    
    # Load environment variables
    load_dotenv()
    
    # Enable debug logging if in debug mode
    if os.getenv('DEBUG', 'false').lower() == 'true':
        enable_debug_logging()
    else:
        # Configure INFO level logging
        logging.basicConfig(level=logging.INFO)
    
    # Get credentials from environment
    base_url = os.getenv('WATS_BASE_URL')
    token = os.getenv('WATS_AUTH_TOKEN')
    
    if not base_url or not token:
        raise ValueError("WATS_BASE_URL and WATS_AUTH_TOKEN must be set")
    
    # Configure station
    station = Station(
        config=StationConfig(
            station_name=os.getenv('WATS_STATION_NAME', 'DEFAULT-STATION'),
            location=os.getenv('WATS_LOCATION', 'Default Location')
        )
    )
    
    # Initialize API
    try:
        api = pyWATS(
            base_url=base_url,
            token=token,
            station=station,
            timeout=int(os.getenv('WATS_TIMEOUT', '30'))
        )
        
        # Test connection
        if api.test_connection():
            version = api.get_version()
            logging.info(f"Connected to WATS server version: {version}")
            return api
        else:
            raise ConnectionError("Connection test failed")
            
    except AuthenticationError:
        logging.error("Authentication failed - check credentials")
        raise
        
    except PyWATSError as e:
        logging.error(f"Failed to initialize WATS API: {e}")
        raise

# Use it
if __name__ == "__main__":
    try:
        api = initialize_api()
        
        # Now use the API
        products = api.product.get_products()
        print(f"Found {len(products)} products")
        
    except Exception as e:
        logging.exception("Application error")
        exit(1)
```

---

## Performance Optimization

pyWATS includes several performance optimizations to make your applications faster and more efficient:

### Enhanced TTL Caching

Cache static data automatically with TTL (Time To Live) expiration:

```python
from pywats import AsyncWATS
from pywats.core.cache import AsyncTTLCache

async def main():
    async with AsyncWATS(base_url="https://...", token="...") as api:
        # Process service has built-in caching
        # First call - fetches from server
        processes = await api.process.get_processes()
        
        # Second call - returns cached data (100x faster!)
        processes = await api.process.get_processes()
        
        # Check cache statistics
        stats = api.process.cache_stats
        print(f"Cache hit rate: {stats['hit_rate']:.1%}")  # e.g., 95.0%
        
        # Clear cache when needed
        await api.process.clear_cache()

# Create your own caches for any data
cache = AsyncTTLCache[str](
    max_size=1000,
    default_ttl=300.0  # 5 minutes
)

async with cache:
    # Cache a value
    await cache.set("key", "value", ttl=60.0)  # Custom TTL
    
    # Get a value
    value = await cache.get("key")
    
    # Check statistics
    print(f"Hit rate: {cache.stats.hit_rate:.1%}")
    print(f"Hits: {cache.stats.hits}, Misses: {cache.stats.misses}")
```

**Performance Impact:** 95% reduction in server calls for static data, 100x faster cache hits vs server calls.

### Connection Pooling

HTTP/2 connection pooling is automatically enabled for all API calls:

```python
from pywats import AsyncWATS

async with AsyncWATS(base_url="https://...", token="...") as api:
    # All requests automatically use connection pooling
    # - Reuses connections (faster, less overhead)
    # - HTTP/2 multiplexing (multiple requests on one connection)
    # - Up to 100 max connections
    # - 20 keepalive connections
    
    # Concurrent requests are much faster
    import asyncio
    products, assets, units = await asyncio.gather(
        api.product.get_products(),
        api.asset.get_assets(top=100),
        api.production.get_units(top=100)
    )
```

**Performance Impact:** 3-5x faster for bulk operations, automatic connection reuse.

### Request Batching

Process multiple items efficiently with built-in batching utilities:

```python
from pywats import AsyncWATS
from pywats.core.batching import ChunkedBatcher, batch_map

async def main():
    async with AsyncWATS(base_url="https://...", token="...") as api:
        serial_numbers = [f"SN-{i:05d}" for i in range(1000)]
        
        # Method 1: ChunkedBatcher for size-based batching
        async with ChunkedBatcher(
            processor=lambda sns: api.production.get_units_batch(sns),
            chunk_size=50,  # Process 50 at a time
            max_concurrent=5  # Up to 5 concurrent batches
        ) as batcher:
            units = await batcher.process(serial_numbers)
        
        # Method 2: batch_map for simple concurrent mapping
        async def fetch_unit(sn: str):
            return await api.production.get_unit(sn, "WIDGET-001")
        
        units = await batch_map(
            items=serial_numbers,
            func=fetch_unit,
            batch_size=50,
            max_concurrent=10
        )
        
        print(f"Fetched {len(units)} units")

import asyncio
asyncio.run(main())
```

**Performance Impact:** 5-10x faster for bulk operations, automatic concurrency control.

### MessagePack Serialization

Use MessagePack for faster, smaller payloads (optional):

```python
# First, install MessagePack support
# pip install msgpack

from pywats.core.performance import Serializer

# Create serializer with MessagePack
serializer = Serializer(format='msgpack')

# Serialize data
data = {"part_number": "WIDGET-001", "values": [1, 2, 3]}
payload = serializer.serialize(data)

# Deserialize
result = serializer.deserialize(payload)

# Compare formats
json_serializer = Serializer(format='json')
msgpack_serializer = Serializer(format='msgpack')

json_size = len(json_serializer.serialize(data))
msgpack_size = len(msgpack_serializer.serialize(data))

print(f"JSON: {json_size} bytes")
print(f"MessagePack: {msgpack_size} bytes ({msgpack_size/json_size:.1%} size)")
# Output: MessagePack: 50% size of JSON

# Benchmark serialization speed
from pywats.core.performance import benchmark_serialization

results = benchmark_serialization(data, iterations=10000)
for fmt, metrics in results.items():
    print(f"{fmt}: {metrics['ops_per_sec']:.0f} ops/sec")
# MessagePack is typically 3x faster than JSON
```

**Performance Impact:** 50% smaller payloads, 3x faster serialization, graceful fallback to JSON if not installed.

### Combined Performance Pattern

Use all optimizations together for maximum performance:

```python
from pywats import AsyncWATS
from pywats.core.cache import AsyncTTLCache
from pywats.core.batching import batch_map

async def process_production_data():
    async with AsyncWATS(base_url="https://...", token="...") as api:
        # 1. Use built-in caching for static data
        processes = await api.process.get_processes()  # Cached automatically
        
        # 2. Create custom cache for frequently accessed data
        product_cache = AsyncTTLCache[dict](max_size=1000, default_ttl=600.0)
        
        async with product_cache:
            # 3. Batch process units with connection pooling
            serial_numbers = [f"SN-{i:05d}" for i in range(1000)]
            
            async def fetch_with_cache(sn: str):
                # Check cache first
                cached = await product_cache.get(sn)
                if cached:
                    return cached
                
                # Fetch from API (uses connection pooling automatically)
                unit = await api.production.get_unit(sn, "WIDGET-001")
                
                # Cache result
                await product_cache.set(sn, unit)
                return unit
            
            # Process in batches with concurrency control
            units = await batch_map(
                items=serial_numbers,
                func=fetch_with_cache,
                batch_size=100,
                max_concurrent=10
            )
            
            print(f"Processed {len(units)} units")
            print(f"Cache hit rate: {product_cache.stats.hit_rate:.1%}")
            # Expect 95%+ hit rate on subsequent runs

import asyncio
asyncio.run(process_production_data())
```

For complete documentation, see [PERFORMANCE_OPTIMIZATIONS.md](PERFORMANCE_OPTIMIZATIONS.md).

---

## Internal API Usage

### Understanding Internal vs Public APIs

pyWATS provides access to both **public** and **internal** WATS API endpoints:

**Public APIs** (Stable):
- Documented and stable endpoints (e.g., `/api/Product`, `/api/Report`)
- Accessed through standard modules: `api.product`, `api.report`, `api.asset`, etc.
- **Guaranteed stability** - Will not change without notice
- **Recommended** for production code

**Internal APIs** (Unstable):
- Undocumented endpoints used by WATS frontend (e.g., `/api/internal/UnitFlow`)
- Accessed through the same domain accessor: `api.product`, `api.analytics`, etc.
- Methods are marked with `⚠️ INTERNAL API` in docstrings
- **⚠️ MAY CHANGE WITHOUT NOTICE** - Subject to breaking changes
- **Use with caution** - Only when public APIs don't provide needed functionality

### When to Use Internal APIs

Internal APIs fill gaps where public endpoints don't yet exist:

| Feature | Method | Why Internal? |
|---------|--------|---------------|
| Unit Flow Analysis | `api.analytics.get_unit_flow()` | No public Unit Flow endpoints yet |
| Box Build Templates | `api.product.get_box_build_template()` | No public box build management |
| Asset File Operations | `api.asset.upload_blob()` | No public file upload/download |
| Unit Phases (MES) | `api.production.get_all_unit_phases()` | MES integration not in public API |
| Process Details | `api.process.get_all_processes()` | Full process info not in public API |

### Using Internal APIs Safely

```python
from pywats import pyWATS

api = pyWATS(base_url="...", token="...")

# ✅ Public API - Use this when available
products = api.product.get_products()

# ⚠️ Internal API - Use only when necessary
# This uses internal endpoints that may change (see docstring for warning)
box_build = api.product.get_box_build_template("WIDGET-001", "A")
```

**Best Practices:**

1. **Prefer Public APIs**: Always use public APIs when available
2. **Isolate Internal Calls**: Wrap internal API calls in your own functions
3. **Add Error Handling**: Internal APIs may fail differently than public ones
4. **Document Usage**: Note which parts of your code use internal APIs
5. **Monitor for Changes**: Subscribe to pyWATS updates for breaking changes

**Example - Isolated Internal API Usage:**

```python
def get_unit_flow_safely(api, part_number, date_from, date_to):
    """
    Get unit flow data using internal API.
    
    ⚠️ INTERNAL API: This function uses internal WATS endpoints
    that may change without notice.
    """
    try:
        from pywats import UnitFlowFilter
        
        filter_data = UnitFlowFilter(
            part_number=part_number,
            date_from=date_from,
            date_to=date_to
        )
        
        # Internal API call - wrapped for safety
        result = api.analytics.get_unit_flow(filter_data)
        return result
        
    except AttributeError:
        # API may have changed
        raise RuntimeError(
            "Unit Flow API has changed. "
            "Please update pyWATS to the latest version."
        )

# Use the wrapped function
try:
    flow = get_unit_flow_safely(api, "WIDGET-001", date_from, date_to)
except RuntimeError as e:
    # Handle API change gracefully
    logging.error(f"Unit Flow not available: {e}")
    # Fall back to alternative approach
```

### Deprecation Warnings

Some internal API methods will emit deprecation warnings:

```python
# This method is deprecated and will show a warning
bom_xml = api.product.repository.get_bom("WIDGET-001", "A")
# DeprecationWarning: ProductRepository.get_bom() uses an internal API endpoint...

# Use the unified API method instead
bom_items = api.product.get_bom_items("WIDGET-001", "A")
```

To suppress these warnings during testing (not recommended for production):

```python
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    bom = api.product.repository.get_bom("WIDGET-001", "A")
```

### Future-Proofing Your Code

As public APIs become available, migrate away from internal APIs:

```python
# Current unified API - Internal methods are marked in docstrings
def get_box_build_template(api, part_number, revision):
    # ⚠️ INTERNAL API (see docstring) - may change
    return api.product.get_box_build_template(part_number, revision)

# When endpoint becomes public, docstring warning will be removed
# Your code continues to work with no changes required
```

**Migration Checklist:**

- ✅ Monitor pyWATS release notes for new public endpoints
- ✅ Test your code with each new pyWATS version
- ✅ Keep internal API usage isolated and documented
- ✅ Have fallback strategies for critical workflows

---

## Batch Operations & Pagination

### Batch Operations

Execute multiple API calls concurrently for better performance:

```python
from pywats.core import batch_execute, collect_successes, collect_failures

# Fetch multiple products in parallel
part_numbers = ["PN-001", "PN-002", "PN-003", "PN-004", "PN-005"]

results = batch_execute(
    keys=part_numbers,
    operation=lambda pn: api.product.get_product(pn),
    max_workers=5  # Concurrent threads (default: 10)
)

# Extract successful results
products = collect_successes(results)
print(f"Fetched {len(products)} products successfully")

# Check for failures
failures = collect_failures(results)
for key, error in failures:
    print(f"Failed to fetch {key}: {error}")
```

Domain-specific batch methods are also available:

```python
# Product domain batch methods
product_results = api.product.get_products_batch(["PN-001", "PN-002", "PN-003"])

# Fetch multiple revisions
revision_pairs = [("PN-001", "A"), ("PN-001", "B"), ("PN-002", "A")]
revision_results = api.product.get_revisions_batch(revision_pairs)
```

### Pagination

Iterate over large datasets efficiently without loading everything into memory:

```python
# SCIM: Iterate over all users
for user in api.scim.iter_users(page_size=100):
    print(f"{user.user_name}: {user.display_name}")

# With a limit
for user in api.scim.iter_users(page_size=50, max_users=200):
    process_user(user)

# With progress tracking
def on_page(page_num, items_so_far, total):
    print(f"Page {page_num}: {items_so_far}/{total} users")

for user in api.scim.iter_users(on_page=on_page):
    sync_to_external_system(user)
```

For custom pagination needs, use the core utilities directly:

```python
from pywats.core import paginate, Paginator

# Custom pagination with any API
def fetch_page(start_index, count):
    return api.some_api.get_items(start=start_index, count=count)

for item in paginate(
    fetch_page=fetch_page,
    get_items=lambda r: r.items,
    get_total=lambda r: r.total_count,
    page_size=50
):
    process(item)
```

---

## See Also

- [Domain Guides](INDEX.md) - API documentation for each domain
- [GUI Configuration](../src/pywats_client/GUI_CONFIGURATION.md) - GUI client setup
- [Headless Operation](../src/pywats_client/control/HEADLESS_GUIDE.md) - Headless client setup
- [Examples](../examples/) - Working code examples
