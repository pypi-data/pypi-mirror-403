# PyWATS Error Catalog

**Last Updated:** January 23, 2026  
**Version:** 0.1.0b34

This document provides a comprehensive reference for all errors that can occur when using the pyWATS library. Each error includes its cause, examples, and remediation steps.

---

## Table of Contents

- [Error Handling Modes](#error-handling-modes)
- [Exception Hierarchy](#exception-hierarchy)
- [Connection Errors](#connection-errors)
- [Authentication & Authorization](#authentication--authorization)
- [Data Validation Errors](#data-validation-errors)
- [Resource Errors](#resource-errors)
- [Server Errors](#server-errors)
- [Result Pattern Error Codes](#result-pattern-error-codes)
- [Client Errors](#client-errors)
- [Retry Behavior](#retry-behavior)
- [Quick Reference](#quick-reference)

---

## Error Handling Modes

PyWATS supports two error handling modes that control how the library responds to ambiguous situations:

### STRICT Mode (Default)

```python
from pywats import pyWATS, ErrorMode

api = pyWATS(
    base_url="https://wats.example.com",
    token="your_token",
    error_mode=ErrorMode.STRICT  # Default
)
```

**Behavior:**
- ✅ Raises exceptions for all errors (404, validation, server errors)
- ✅ Raises `EmptyResponseError` when expecting data but receiving empty response
- ✅ Best for production code that needs certainty
- ✅ Fail-fast approach

### LENIENT Mode

```python
from pywats import pyWATS, ErrorMode

api = pyWATS(
    base_url="https://wats.example.com",
    token="your_token",
    error_mode=ErrorMode.LENIENT
)
```

**Behavior:**
- ✅ Returns `None` for 404 (resource not found)
- ✅ Returns `None` for empty responses
- ✅ Only raises exceptions for actual errors (validation, authentication, server errors)
- ✅ Best for exploratory code and scripts that handle missing data gracefully

---

## Exception Hierarchy

```
Exception
└── PyWATSError (base for all pyWATS errors)
    ├── WatsApiError (HTTP 4xx/5xx errors)
    │   ├── AuthenticationError (401)
    │   ├── AuthorizationError (403)
    │   ├── ValidationError (400)
    │   ├── ConflictError (409)
    │   └── ServerError (5xx)
    ├── NotFoundError (404)
    ├── EmptyResponseError (STRICT mode only)
    ├── ConnectionError (network failures)
    └── TimeoutError (request timeouts)
```

**All exceptions inherit from `PyWATSError`**, so you can catch all pyWATS-specific errors with:

```python
try:
    product = api.product.get_product("WIDGET-001")
except PyWATSError as e:
    print(f"PyWATS error: {e.message}")
    print(f"Operation: {e.operation}")
    print(f"Details: {e.details}")
```

---

## Connection Errors

### ConnectionError

**HTTP Status:** N/A (network level)  
**Error Code:** `CONNECTION_ERROR`  
**Retry:** ✅ Automatic (if retry enabled)

**Cause:**
- Cannot connect to WATS server
- DNS resolution failure
- Network unavailable
- Firewall blocking connection
- Server is down

**Example:**
```python
from pywats import pyWATS, ConnectionError

api = pyWATS(base_url="https://unreachable-server.com", token="...")

try:
    api.test_connection()
except ConnectionError as e:
    print(f"Cannot connect: {e.message}")
    # Details: {'cause': 'Name or service not known'}
```

**Remediation:**
1. Verify server URL is correct
2. Check network connectivity (`ping wats-server.com`)
3. Verify DNS resolution (`nslookup wats-server.com`)
4. Check firewall/proxy settings
5. Confirm WATS server is running
6. Try accessing server URL in browser

**Related Errors:**
- `TimeoutError` - Connection attempt times out

---

### TimeoutError

**HTTP Status:** N/A (network level)  
**Error Code:** `TIMEOUT`  
**Retry:** ✅ Automatic (if retry enabled)

**Cause:**
- Request takes longer than configured timeout
- Server is slow to respond
- Network latency issues
- Large data transfer

**Example:**
```python
from pywats import pyWATS, TimeoutError

# Set a short timeout
api = pyWATS(base_url="...", token="...", timeout=5)

try:
    # Large query that takes >5 seconds
    reports = api.report.query_uut_headers(filter)
except TimeoutError as e:
    print(f"Request timed out: {e.message}")
```

**Remediation:**
1. Increase timeout value:
   ```python
   api = pyWATS(base_url="...", token="...", timeout=60)
   ```
2. Narrow query scope (use filters, limit results)
3. Check network latency
4. Contact server administrator if persistent

**Related Errors:**
- `ConnectionError` - Cannot establish connection

---

## Authentication & Authorization

### AuthenticationError

**HTTP Status:** 401 Unauthorized  
**Error Code:** `UNAUTHORIZED`  
**Retry:** ❌ No (credentials need fixing)

**Cause:**
- Invalid credentials (username/password)
- Malformed authentication token
- Token not Base64 encoded properly
- Expired session

**Example:**
```python
from pywats import pyWATS, AuthenticationError

api = pyWATS(base_url="...", token="invalid_token")

try:
    api.test_connection()
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
    print(f"Status code: {e.status_code}")  # 401
```

**Remediation:**
1. Verify credentials are correct
2. Ensure token is Base64 encoded:
   ```python
   import base64
   credentials = "username:password"
   token = base64.b64encode(credentials.encode()).decode()
   ```
3. Check for special characters in password
4. Try authenticating through WATS web interface
5. Contact administrator to verify account status

**Related Errors:**
- `AuthorizationError` - Valid credentials but insufficient permissions

---

### AuthorizationError

**HTTP Status:** 403 Forbidden  
**Error Code:** `FORBIDDEN`  
**Retry:** ❌ No (permissions issue)

**Cause:**
- User lacks required permissions for operation
- API endpoint requires elevated privileges
- Resource access restricted

**Example:**
```python
from pywats import pyWATS, AuthorizationError

api = pyWATS(base_url="...", token="...")

try:
    # User doesn't have permission to create products
    product = api.product.create_product(...)
except AuthorizationError as e:
    print(f"Permission denied: {e.message}")
```

**Remediation:**
1. Verify user has required permissions in WATS
2. Contact administrator to grant necessary roles
3. Use account with appropriate access level
4. Check WATS user permissions in admin panel

**Related Errors:**
- `AuthenticationError` - Invalid credentials

---

## Data Validation Errors

### ReportHeaderValidationError

**HTTP Status:** N/A (client-side validation)  
**Error Code:** `PROBLEMATIC_CHARACTERS`  
**Retry:** ❌ No (fix input data or bypass intentionally)

**Cause:**
- Serial number or part number contains characters that cause issues with WATS searches/filters
- Problematic characters: `*`, `%`, `?`, `[`, `]`, `^`, `!`, `/`, `\`

**Example:**
```python
from pywats.models import UUTReport
from pywats import ReportHeaderValidationError

try:
    report = UUTReport(
        pn="PART/001",  # Contains '/' - problematic!
        sn="SN*001",    # Contains '*' - problematic!
        rev="A",
        process_code=10,
        station_name="TestStation",
        location="Lab",
        purpose="Development"
    )
except Exception as e:  # Wrapped in pydantic ValidationError
    print(f"Problematic characters in report header")
```

**Bypass Options:**

When you intentionally need to use problematic characters:

#### Option 1: Context Manager
```python
from pywats import allow_problematic_characters
from pywats.models import UUTReport

with allow_problematic_characters():
    report = UUTReport(
        pn="PART/001",  # Now allowed (warning issued)
        sn="SN*001",    # Now allowed (warning issued)
        ...
    )
```

#### Option 2: SUPPRESS: Prefix
```python
from pywats.models import UUTReport

report = UUTReport(
    pn="SUPPRESS:PART/001",  # Prefix stripped, value = "PART/001"
    sn="SUPPRESS:SN*001",    # Prefix stripped, value = "SN*001"
    ...
)
```

**Remediation:**
1. Use only recommended characters: `A-Z`, `a-z`, `0-9`, `-`, `_`, `.`
2. If problematic characters are required, use bypass options above
3. Be aware that bypassed values may cause issues with WATS searches/filters

**Related Errors:**
- `ValidationError` - General validation failures

---

### ValidationError

**HTTP Status:** 400 Bad Request  
**Error Code:** `INVALID_INPUT`, `MISSING_REQUIRED_FIELD`, `INVALID_FORMAT`, `VALUE_OUT_OF_RANGE`  
**Retry:** ❌ No (fix input data)

**Cause:**
- Missing required fields
- Invalid data format
- Value out of acceptable range
- Failed Pydantic model validation
- Constraint violation

**Example:**
```python
from pywats import pyWATS, ValidationError

api = pyWATS(base_url="...", token="...")

try:
    # Missing required field
    product = api.product.create_product(
        part_number="",  # Empty part number
        state="ACTIVE"
    )
except ValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Field: {e.field}")  # 'part_number'
    print(f"Value: {e.value}")  # ''
```

**Common Scenarios:**

#### Missing Required Field
```python
# Error: part_number is required
api.product.create_product(description="Widget")

# Fix:
api.product.create_product(
    part_number="WIDGET-001",
    description="Widget"
)
```

#### Invalid Format
```python
# Error: Invalid date format
filter = WATSFilter(start_date="2024-13-40")  # Invalid date

# Fix:
from datetime import datetime
filter = WATSFilter(start_date=datetime(2024, 1, 15))
```

#### Pydantic Validation
```python
from pywats.models import Product
from pydantic import ValidationError as PydanticValidationError

try:
    product = Product(
        part_number="WIDGET",
        state="INVALID_STATE"  # Not a valid ProductState
    )
except PydanticValidationError as e:
    print(e.errors())
```

**Remediation:**
1. Check error message for specific field and issue
2. Verify all required fields are provided
3. Validate data types match expected types
4. Check value constraints (min/max, length, pattern)
5. Review model documentation for field requirements
6. Use Pydantic models for automatic validation

**Related Errors:**
- Pydantic `ValidationError` - Model validation failures

---

## Resource Errors

### NotFoundError

**HTTP Status:** 404 Not Found  
**Error Code:** `NOT_FOUND`  
**Retry:** ❌ No (resource doesn't exist)

**Behavior:**
- **STRICT mode:** Raises `NotFoundError`
- **LENIENT mode:** Returns `None`

**Cause:**
- Resource with given identifier doesn't exist
- Wrong part number, serial number, or ID
- Resource was deleted
- Typo in identifier

**Example:**
```python
from pywats import pyWATS, NotFoundError

api = pyWATS(base_url="...", token="...", error_mode=ErrorMode.STRICT)

try:
    product = api.product.get_product("NONEXISTENT-PART")
except NotFoundError as e:
    print(f"Not found: {e.message}")
    print(f"Resource type: {e.resource_type}")  # 'Product'
    print(f"Identifier: {e.identifier}")  # 'NONEXISTENT-PART'
```

**LENIENT mode example:**
```python
api = pyWATS(base_url="...", token="...", error_mode=ErrorMode.LENIENT)

product = api.product.get_product("MAYBE-EXISTS")
if product is None:
    print("Product not found, creating new one...")
else:
    print(f"Found: {product.part_number}")
```

**Remediation:**
1. Verify identifier is correct (check for typos)
2. List available resources to confirm existence:
   ```python
   products = api.product.get_products()
   print([p.part_number for p in products])
   ```
3. Use search/query methods to find resource
4. Check if resource was deleted
5. Use LENIENT mode if `None` is acceptable

**Related Errors:**
- `EmptyResponseError` - Empty result set in STRICT mode

---

### ConflictError

**HTTP Status:** 409 Conflict  
**Error Code:** `CONFLICT`, `ALREADY_EXISTS`  
**Retry:** ❌ No (conflict must be resolved)

**Cause:**
- Resource already exists (duplicate)
- Concurrent modification conflict
- Constraint violation (unique key)
- Version mismatch (optimistic locking)

**Example:**
```python
from pywats import pyWATS, ConflictError

api = pyWATS(base_url="...", token="...")

try:
    # Part number already exists
    product = api.product.create_product(
        part_number="WIDGET-001",  # Already exists
        description="Duplicate"
    )
except ConflictError as e:
    print(f"Conflict: {e.message}")
```

**Remediation:**
1. Check if resource already exists before creating
2. Use update instead of create for existing resources
3. Handle concurrent modifications with retry logic
4. Use unique identifiers
5. Implement optimistic locking if needed

**Related Errors:**
- `ValidationError` - Data validation failures

---

### EmptyResponseError

**HTTP Status:** 200 OK (but body is empty)  
**Error Code:** N/A  
**Retry:** ❌ No  
**Mode:** STRICT only

**Cause:**
- Server returned 200 OK but response body is empty/null
- Query returned no results
- Resource exists but has no data
- Server bug (should return 404)

**Example:**
```python
from pywats import pyWATS, EmptyResponseError, ErrorMode

api = pyWATS(base_url="...", token="...", error_mode=ErrorMode.STRICT)

try:
    # Query returns empty result set
    reports = api.report.query_uut_headers(
        WATSFilter(part_number="NEVER-TESTED")
    )
except EmptyResponseError as e:
    print(f"Empty response: {e.message}")
    print(f"Operation: {e.operation}")  # 'query_uut_headers'
```

**Remediation:**
1. Switch to LENIENT mode if empty results are acceptable:
   ```python
   api = pyWATS(error_mode=ErrorMode.LENIENT)
   reports = api.report.query_uut_headers(filter)
   if reports is None or len(reports) == 0:
       print("No reports found")
   ```
2. Broaden query filters
3. Verify resource should have data
4. Check if operation allows empty responses

**Related Errors:**
- `NotFoundError` - Resource doesn't exist (404)

---

## Server Errors

### ServerError

**HTTP Status:** 500-599 (Server errors)  
**Error Code:** `API_ERROR`, `OPERATION_FAILED`  
**Retry:** ✅ Automatic (if retry enabled)

**Cause:**
- Internal server error
- Database error
- Server bug
- Resource exhaustion
- Unhandled exception on server

**Example:**
```python
from pywats import pyWATS, ServerError

api = pyWATS(base_url="...", token="...")

try:
    result = api.report.submit_report(report)
except ServerError as e:
    print(f"Server error: {e.message}")
    print(f"Status code: {e.status_code}")  # 500, 502, 503, etc.
    print(f"Response body: {e.response_body}")
```

**Common Status Codes:**
- **500** - Internal Server Error
- **502** - Bad Gateway (proxy error)
- **503** - Service Unavailable (server overloaded)
- **504** - Gateway Timeout

**Remediation:**
1. Wait and retry (automatic retry is enabled by default)
2. Check WATS server logs for details
3. Contact server administrator
4. Reduce request frequency (see [Retry Behavior](#retry-behavior))
5. Report bug to WATS support if persistent

**Related Errors:**
- `TimeoutError` - Request times out before server responds

---

## Result Pattern Error Codes

When using the `Result[T]` pattern, methods return `Success[T]` or `Failure` instead of raising exceptions:

```python
from pywats import pyWATS
from pywats.shared import Result, Success, Failure, ErrorCode

result: Result[Product] = api.product.some_result_based_method(...)

if result.is_success:
    product = result.value
    print(f"Success: {product.part_number}")
else:
    # result is Failure
    print(f"Error [{result.error_code}]: {result.message}")
    print(f"Details: {result.details}")
    print(f"Suggestions: {result.suggestions}")
```

### Standard Error Codes

| Error Code | Description | HTTP Equivalent |
|-----------|-------------|-----------------|
| `INVALID_INPUT` | Input validation failed | 400 |
| `MISSING_REQUIRED_FIELD` | Required field not provided | 400 |
| `INVALID_FORMAT` | Data format is incorrect | 400 |
| `VALUE_OUT_OF_RANGE` | Value exceeds constraints | 400 |
| `NOT_FOUND` | Resource doesn't exist | 404 |
| `ALREADY_EXISTS` | Resource already exists | 409 |
| `CONFLICT` | Resource conflict | 409 |
| `OPERATION_FAILED` | Operation failed | 500 |
| `SAVE_FAILED` | Save operation failed | 500 |
| `DELETE_FAILED` | Delete operation failed | 500 |
| `UNAUTHORIZED` | Authentication required | 401 |
| `FORBIDDEN` | Insufficient permissions | 403 |
| `CONNECTION_ERROR` | Network failure | N/A |
| `TIMEOUT` | Request timeout | N/A |
| `API_ERROR` | Generic API error | 500 |
| `UNKNOWN_ERROR` | Unclassified error | N/A |

### Example Usage

```python
from pywats.shared import Failure, ErrorCode

# Creating a failure
failure = Failure(
    error_code=ErrorCode.MISSING_REQUIRED_FIELD,
    message="part_number is required to create a product",
    details={"field": "part_number", "received": None},
    suggestions=["Provide a unique part_number string"]
)

# Handling failures
if result.is_failure:
    if result.error_code == ErrorCode.NOT_FOUND:
        print("Resource not found, creating new one...")
    elif result.error_code == ErrorCode.UNAUTHORIZED:
        print("Authentication required")
    else:
        print(f"Unexpected error: {result.message}")
```

---

## Client Errors

These errors occur in the pyWATS Client application (`pywats_client`):

### Configuration Errors

**Cause:**
- Invalid configuration file
- Missing required configuration
- Failed to load/save config

**Example:**
```python
from pywats_client.core.config import ClientConfig

try:
    config = ClientConfig.load("invalid_config.json")
except Exception as e:
    print(f"Config error: {e}")
```

**Remediation:**
1. Verify config file exists and is valid JSON
2. Use `ClientConfig.load_or_create()` to create default if missing
3. Check file permissions
4. Validate required fields are present

### Converter Errors

**Cause:**
- File format not recognized
- Invalid converter configuration
- Converter execution failure

**Example:**
```python
from pywats_client.converters.models import ValidationResult

# Low confidence - file not recognized
result = converter.validate_file("unknown.dat")
if not result.can_convert:
    print(f"Cannot convert: {result.message}")
    print(f"Confidence: {result.confidence}")  # < 0.5
```

**Remediation:**
1. Check file format matches converter expectations
2. Verify converter is enabled
3. Review converter configuration
4. Check converter logs for details
5. Ensure dependencies are met (ready=True)

### Queue Errors

**Cause:**
- Failed to persist queue
- Queue corruption
- Disk space exhausted

**Remediation:**
1. Check disk space
2. Verify queue directory is writable
3. Clear corrupted queue files
4. Restart client

---

## Retry Behavior

PyWATS automatically retries failed requests for transient errors:

### Retryable Errors

The following errors trigger automatic retry:
- `ConnectionError` - Network failures
- `TimeoutError` - Request timeouts
- `ServerError` with status 429, 500, 502, 503, 504

### Retry Configuration

```python
from pywats import pyWATS, RetryConfig

# Default retry (3 attempts, exponential backoff)
api = pyWATS(base_url="...", token="...")

# Custom retry
config = RetryConfig(
    max_attempts=5,          # Try up to 5 times
    base_delay=2.0,          # Start with 2 second delay
    max_delay=60.0,          # Cap at 60 seconds
    exponential_base=2.0,    # Double delay each retry
    jitter=True,             # Add randomness to prevent thundering herd
)
api = pyWATS(base_url="...", token="...", retry_config=config)

# Disable retry
api = pyWATS(base_url="...", token="...", retry_enabled=False)
```

### Retry Delay Calculation

```
delay = min(base_delay * (exponential_base ** attempt), max_delay)
if jitter:
    delay = delay * (0.5 + random.random() * 0.5)
```

**Example delays (base_delay=1.0, exponential_base=2.0):**
- Attempt 1: 1 second
- Attempt 2: 2 seconds
- Attempt 3: 4 seconds
- Attempt 4: 8 seconds
- Attempt 5: 16 seconds

### Non-Retryable Errors

These errors are NOT retried (fix required):
- `AuthenticationError` (401)
- `AuthorizationError` (403)
- `ValidationError` (400)
- `NotFoundError` (404)
- `ConflictError` (409)

---

## Quick Reference

### Common Error Patterns

```python
from pywats import pyWATS, PyWATSError, NotFoundError, ValidationError, ConnectionError

api = pyWATS(base_url="...", token="...")

# Handle specific errors
try:
    product = api.product.get_product("WIDGET-001")
except NotFoundError:
    print("Product not found")
except ValidationError as e:
    print(f"Invalid input: {e.field} = {e.value}")
except ConnectionError:
    print("Cannot connect to server")
except PyWATSError as e:
    print(f"PyWATS error: {e.message}")

# Use LENIENT mode for optional resources
api = pyWATS(base_url="...", token="...", error_mode=ErrorMode.LENIENT)
product = api.product.get_product("MAYBE-EXISTS")
if product is None:
    print("Not found")
else:
    print(f"Found: {product.part_number}")

# Use Result pattern for structured errors
result = api.product.some_result_method(...)
if result.is_failure:
    print(f"[{result.error_code}] {result.message}")
    for suggestion in result.suggestions:
        print(f"  - {suggestion}")
```

### Debugging Tips

1. **Enable debug logging:**
   ```python
   from pywats.core.logging import enable_debug_logging
   enable_debug_logging()
   ```

2. **Inspect exception details:**
   ```python
   try:
       api.product.get_product("X")
   except PyWATSError as e:
       print(f"Message: {e.message}")
       print(f"Operation: {e.operation}")
       print(f"Details: {e.details}")
       if hasattr(e, 'cause') and e.cause:
           print(f"Cause: {e.cause}")
   ```

3. **Check HTTP status codes:**
   ```python
   try:
       api.product.create_product(...)
   except WatsApiError as e:
       print(f"HTTP Status: {e.status_code}")
   ```

4. **Use test_connection():**
   ```python
   if api.test_connection():
       print("Connected successfully")
   else:
       print("Connection failed")
   ```

### Getting Help

- **Documentation:** https://github.com/olreppe/pyWATS/tree/main/docs
- **GitHub Issues:** https://github.com/olreppe/pyWATS/issues
- **Email:** support@virinco.com
- **WATS Community:** https://wats.com/community

---

**Error catalog version:** 0.1.0b34  
**Last updated:** January 23, 2026
