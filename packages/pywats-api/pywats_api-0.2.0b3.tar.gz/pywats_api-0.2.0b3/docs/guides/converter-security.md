# Converter Security Guide

This guide documents the security features for converter execution in pyWATS Client, including the sandbox system for isolating third-party converters.

## Overview

Converters in pyWATS process external data files (test results, logs, etc.) and transform them into WATS reports. Since converters may come from various sources (built-in, user-created, third-party), the client provides a sandboxing system to execute converters securely.

### Security Model

pyWATS uses a **defense-in-depth** approach:

1. **Static Analysis** - Validates converter code before execution
2. **Process Isolation** - Runs converters in separate subprocess
3. **Capability-Based Permissions** - Fine-grained permission control
4. **Resource Limits** - Prevents resource exhaustion

## Sandbox Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    AsyncConverterPool                        │
│                                                              │
│  ┌─────────────────┐    ┌─────────────────────────────────┐│
│  │ Trusted Mode    │    │ Sandboxed Mode                  ││
│  │ (Direct exec)   │    │ ┌─────────────────────────────┐ ││
│  │                 │    │ │ ConverterSandbox            │ ││
│  │                 │    │ │  - ConverterValidator       │ ││
│  │                 │    │ │  - SandboxProcess           │ ││
│  │                 │    │ │  - SandboxConfig            │ ││
│  │                 │    │ └─────────────────────────────┘ ││
│  └─────────────────┘    │ ┌─────────────────────────────┐ ││
│                         │ │ sandbox_runner.py           │ ││
│                         │ │  (Isolated Subprocess)      │ ││
│                         │ │  - SafeFileHandler          │ ││
│                         │ │  - RestrictedImporter       │ ││
│                         │ └─────────────────────────────┘ ││
│                         └─────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Execution Flow

1. **Converter Registration** - Pool validates converter source
2. **File Detection** - Watchdog triggers file event
3. **Sandbox Decision** - Check if sandbox should be used
4. **Process Creation** - Spawn isolated subprocess
5. **Converter Loading** - Load converter in restricted environment
6. **Execution** - Run conversion with resource limits
7. **Result Collection** - Retrieve result via IPC
8. **Cleanup** - Terminate subprocess

## Using the Sandbox

### Default Behavior

By default, the `AsyncConverterPool` runs converters in the sandbox:

```python
from pywats_client.service import AsyncConverterPool

# Sandbox is enabled by default
pool = AsyncConverterPool(
    config=config,
    api=api,
    enable_sandbox=True,  # Default
)
```

### Disabling the Sandbox

For trusted converters or development, you can disable the sandbox:

```python
# Disable sandbox for all converters
pool = AsyncConverterPool(
    config=config,
    api=api,
    enable_sandbox=False,
)
```

### Per-Converter Trust Mode

Individual converters can be marked as trusted:

```python
from pywats_client.converters import FileConverter

class MyTrustedConverter(FileConverter):
    @property
    def trusted_mode(self) -> bool:
        # Skip sandbox for this converter
        return True
```

## Sandbox Configuration

### SandboxConfig

The `SandboxConfig` class controls sandbox behavior:

```python
from pywats_client.converters import (
    SandboxConfig,
    SandboxCapability,
    ResourceLimits,
)

config = SandboxConfig(
    # Capabilities granted to converters
    capabilities=frozenset([
        SandboxCapability.READ_INPUT,
        SandboxCapability.WRITE_OUTPUT,
        SandboxCapability.LOG_INFO,
    ]),
    
    # Resource limits
    resource_limits=ResourceLimits(
        timeout_seconds=300,      # 5 minutes max
        memory_mb=512,            # 512 MB memory
        cpu_time_seconds=120,     # 2 minutes CPU
    ),
    
    # Blocked imports (dangerous modules)
    blocked_imports=frozenset([
        "subprocess", "os.system", "socket",
        "ctypes", "multiprocessing",
    ]),
)
```

### Capabilities

The `SandboxCapability` enum defines what converters can do:

| Capability | Description |
|------------|-------------|
| `READ_INPUT` | Read input file(s) |
| `WRITE_OUTPUT` | Write output file(s) |
| `NETWORK_WATS` | Connect to WATS API |
| `NETWORK_LOCAL` | Connect to localhost |
| `NETWORK_FULL` | Full network access |
| `LOG_DEBUG` | Write debug logs |
| `LOG_INFO` | Write info logs |
| `LOG_WARNING` | Write warning logs |
| `LOG_ERROR` | Write error logs |
| `FILE_TEMP` | Create temp files |
| `SHELL_EXECUTE` | Execute shell commands (use with caution!) |

Default capabilities are minimal:
- `READ_INPUT`
- `WRITE_OUTPUT`
- `LOG_INFO`
- `LOG_WARNING`
- `LOG_ERROR`

### Resource Limits

```python
from pywats_client.converters import ResourceLimits

limits = ResourceLimits(
    # Time limits
    timeout_seconds=300.0,     # Wall-clock timeout (default: 5 min)
    cpu_time_seconds=120.0,    # CPU time limit (default: 2 min)
    
    # Memory limits
    memory_mb=512,             # Max memory (default: 512 MB)
    
    # File limits
    max_output_size_mb=100,    # Max output file size (default: 100 MB)
    max_open_files=50,         # Max open file descriptors
    
    # Process limits
    max_processes=1,           # Prevent fork bombs
)
```

## Static Analysis (Validation)

Before executing a converter, the `ConverterValidator` performs static analysis:

### Blocked Patterns

The validator detects dangerous code patterns:

- **Dangerous Imports:** `subprocess`, `socket`, `ctypes`, `multiprocessing`, etc.
- **Dangerous Calls:** `eval()`, `exec()`, `compile()`, `__import__()`, `os.system()`
- **Syntax Errors:** Invalid Python code

### Using the Validator

```python
from pywats_client.converters import ConverterValidator, SandboxConfig

config = SandboxConfig()
validator = ConverterValidator(config)

# Validate source code
source = open("my_converter.py").read()
is_valid, issues = validator.validate_source(source)

if not is_valid:
    print("Validation failed:")
    for issue in issues:
        print(f"  - {issue}")
```

### Example: Blocked Converter

```python
# This converter will be REJECTED by the validator
import subprocess  # BLOCKED!

class BadConverter:
    def convert_file(self, file_path, args):
        # This will never run - blocked at validation
        subprocess.run(["rm", "-rf", "/"])
```

## Writing Sandbox-Safe Converters

### Best Practices

1. **Use Standard Library Only** - Avoid external dependencies when possible
2. **No Network Access** - Don't make HTTP requests unless necessary
3. **No Shell Commands** - Never use `os.system()` or `subprocess`
4. **File I/O via Parameters** - Only read/write the provided paths
5. **Handle Errors Gracefully** - Return error results, don't crash

### Example: Safe Converter

```python
"""Example of a sandbox-safe converter."""

from pathlib import Path
import json


class SafeCSVConverter:
    """Converts CSV files to WATS reports."""
    
    @property
    def name(self) -> str:
        return "SafeCSVConverter"
    
    @property
    def file_patterns(self) -> list:
        return ["*.csv"]
    
    def convert_file(self, file_path: Path, args: dict):
        """
        Convert a CSV file to a report.
        
        Args:
            file_path: Path to input file (sandbox provides access)
            args: Converter arguments from config
        
        Returns:
            dict with status, report, and metadata
        """
        try:
            # Read input (allowed via READ_INPUT capability)
            content = file_path.read_text()
            lines = content.strip().split('\n')
            
            # Parse CSV (simple example)
            header = lines[0].split(',')
            data = [line.split(',') for line in lines[1:]]
            
            # Build report
            report = {
                "type": "UUT",
                "partNumber": args.get("part_number", "UNKNOWN"),
                "serialNumber": data[0][0] if data else "UNKNOWN",
                "result": "Passed",
            }
            
            return {
                "status": "Success",
                "report": report,
                "metadata": {
                    "rows_processed": len(data),
                }
            }
            
        except Exception as e:
            return {
                "status": "Failed",
                "error": str(e),
            }
```

## Error Handling

### Sandbox Exceptions

```python
from pywats_client.converters import (
    SandboxError,
    SandboxTimeoutError,
    SandboxSecurityError,
)

try:
    result = await sandbox.run_converter(...)
except SandboxTimeoutError:
    print("Converter exceeded time limit")
except SandboxSecurityError:
    print("Converter failed security validation")
except SandboxError:
    print("General sandbox error")
```

### Handling Converter Failures

Converter failures are captured and returned:

```python
result = await sandbox.run_converter(...)

if result.get("status") == "Failed":
    error = result.get("error", "Unknown error")
    print(f"Conversion failed: {error}")
```

## Performance Considerations

### Subprocess Overhead

The sandbox spawns a new Python process for each conversion, which has overhead:

- **Process creation:** ~100-200ms on Windows, ~50-100ms on Unix
- **IPC communication:** ~1-10ms per message

For high-throughput scenarios, consider:
- Using `trusted_mode` for verified converters
- Batch processing multiple files per subprocess (future feature)

### Memory Usage

Each sandboxed converter runs in a separate process with its own memory space. Default limit is 512 MB per converter.

## Troubleshooting

### Converter Rejected by Validator

**Symptom:** `SandboxSecurityError: Converter validation failed`

**Solutions:**
1. Check for blocked imports
2. Remove dangerous function calls
3. If the module is safe, add to `allowed_imports`

### Timeout Errors

**Symptom:** `SandboxTimeoutError: Converter timed out`

**Solutions:**
1. Increase `timeout_seconds` in `ResourceLimits`
2. Optimize converter code
3. Use `trusted_mode` for known-slow converters

### Memory Limit Exceeded

**Symptom:** Process killed by OS

**Solutions:**
1. Increase `memory_mb` in `ResourceLimits`
2. Process files in smaller chunks
3. Use streaming instead of loading entire files

## Security Notes

### Threat Model

The sandbox protects against:
- Accidental resource exhaustion
- Simple malicious code injection
- Unauthorized file system access
- Dangerous module imports

The sandbox does **NOT** protect against:
- Sophisticated attacks (side channels, timing attacks)
- Kernel-level exploits
- Physical access

### Production Recommendations

1. **Review All Converters** - Don't run untrusted code, even with sandbox
2. **Limit Permissions** - Only grant necessary capabilities
3. **Monitor Resources** - Watch for unusual CPU/memory usage
4. **Keep Updated** - Apply security patches promptly

## API Reference

### Classes

- `SandboxCapability` - Enum of permissions
- `ResourceLimits` - Resource limit configuration
- `SandboxConfig` - Full sandbox configuration
- `ConverterValidator` - Static code analysis
- `ConverterSandbox` - High-level sandbox interface
- `SandboxError` - Base sandbox exception
- `SandboxTimeoutError` - Timeout exception
- `SandboxSecurityError` - Security violation exception

### Example: Full Configuration

```python
from pywats_client.converters import (
    SandboxCapability,
    ResourceLimits,
    SandboxConfig,
    ConverterSandbox,
)

# Create custom configuration
config = SandboxConfig(
    capabilities=frozenset([
        SandboxCapability.READ_INPUT,
        SandboxCapability.WRITE_OUTPUT,
        SandboxCapability.LOG_INFO,
        SandboxCapability.NETWORK_WATS,  # Allow WATS API calls
    ]),
    resource_limits=ResourceLimits(
        timeout_seconds=600,  # 10 minutes for slow converters
        memory_mb=1024,       # 1 GB for large files
    ),
    blocked_imports=frozenset([
        "subprocess", "os.system", "socket",
        "ctypes", "multiprocessing",
        "requests",  # Block HTTP library too
    ]),
)

# Create sandbox with custom config
sandbox = ConverterSandbox(default_config=config)

# Run converter
result = await sandbox.run_converter(
    converter_path=Path("my_converter.py"),
    converter_class="MyConverter",
    input_path=Path("input.csv"),
    args={"part_number": "PN-001"},
)
```
