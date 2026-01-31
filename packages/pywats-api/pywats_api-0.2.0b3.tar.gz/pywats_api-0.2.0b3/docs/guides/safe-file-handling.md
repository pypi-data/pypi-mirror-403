# Safe File Handling Guide

This guide covers the safe file handling utilities in pyWATS Client, designed to prevent data loss and corruption during file operations.

## Overview

The pyWATS Client uses robust file handling utilities to ensure:

- **Atomic writes**: Files are written completely or not at all
- **Backup recovery**: Automatic fallback to backup files if main file is corrupted
- **File locking**: Cross-platform file locking to prevent concurrent access issues
- **Validation and repair**: Configuration files are validated and can be automatically repaired

## Core Components

### SafeFileWriter

Provides atomic write operations that prevent partial writes and data corruption.

```python
from pywats_client.core.file_utils import SafeFileWriter

# Write JSON atomically with backup
SafeFileWriter.write_json_atomic(
    path="/path/to/config.json",
    data={"key": "value"},
    create_backup=True  # Creates .bak file before overwriting
)

# Write text atomically
SafeFileWriter.write_text_atomic(
    path="/path/to/file.txt",
    content="File contents",
    encoding="utf-8"
)

# Write binary data atomically
SafeFileWriter.write_bytes_atomic(
    path="/path/to/file.bin",
    data=b"\x00\x01\x02"
)
```

**How atomic writes work:**
1. Data is written to a temporary file (`.tmp` extension)
2. The temporary file is flushed and synced to disk
3. If a backup is requested and the original exists, it's copied to `.bak`
4. The temporary file is atomically renamed to the target path
5. If any step fails, the original file remains untouched

### SafeFileReader

Provides safe read operations with automatic backup recovery.

```python
from pywats_client.core.file_utils import SafeFileReader

# Read JSON with automatic backup recovery
data = SafeFileReader.read_json_safe("/path/to/config.json")
# If config.json is corrupted but config.json.bak exists and is valid,
# the backup is automatically restored and returned

# Read text with fallback
content = SafeFileReader.read_text_safe("/path/to/file.txt")
```

**Recovery behavior:**
1. Attempts to read the main file
2. If the main file is corrupted (JSON parse error, etc.), checks for `.bak` file
3. If backup is valid, restores it to the main file and returns its contents
4. If both are corrupted, returns `None`

### File Locking

Cross-platform file locking prevents race conditions when multiple processes access the same file.

```python
from pywats_client.core.file_utils import locked_file

# Use as context manager
with locked_file("/path/to/file.json", mode="w", timeout=5.0) as f:
    json.dump(data, f)

# Read with lock
with locked_file("/path/to/file.json", mode="r", timeout=10.0) as f:
    data = json.load(f)
```

**Platform support:**
- **Unix/Linux/macOS**: Uses `fcntl.flock()` for file locking
- **Windows**: Uses `msvcrt.locking()` for file locking

**Lock types:**
- Write mode (`w`, `a`): Exclusive lock (blocks other readers and writers)
- Read mode (`r`): Shared lock (allows other readers, blocks writers)

## Configuration Validation

### Validating Configuration

```python
from pywats_client.core.config import ClientConfig

# Load config
config = ClientConfig.load("/path/to/config.json")

# Validate
errors = config.validate()
if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Configuration is valid")

# Quick check
if config.is_valid():
    print("Config OK")
```

**Validated fields:**
- `instance_id`: Required, non-empty
- `sync_interval_seconds`: Must be non-negative
- `max_retry_attempts`: Must be non-negative
- `retry_interval_seconds`: Must be non-negative
- `proxy_port`: Must be 0-65535
- `yield_threshold`: Must be 0.0-100.0
- `log_level`: Must be DEBUG, INFO, WARNING, ERROR, or CRITICAL
- `station_name_source`: Must be hostname, config, or manual
- `proxy_mode`: Must be none, system, or manual
- `converters`: Each converter is validated individually

### Automatic Repair

```python
# Repair individual config
config = ClientConfig()
config.sync_interval_seconds = -100  # Invalid!

repairs = config.repair()
# repairs = ["Reset negative sync_interval_seconds to 300"]
# config.sync_interval_seconds is now 300

# Load and repair in one step
config, repairs = ClientConfig.load_and_repair("/path/to/config.json")
if repairs:
    print(f"Made {len(repairs)} repairs:")
    for repair in repairs:
        print(f"  - {repair}")
```

**Automatic repairs:**
| Field | Invalid Value | Repaired To |
|-------|--------------|-------------|
| `instance_id` | Empty | "default" |
| `sync_interval_seconds` | Negative | 300 |
| `max_retry_attempts` | Negative | 5 |
| `retry_interval_seconds` | Negative | 60 |
| `proxy_port` | < 0 or > 65535 | 8080 |
| `yield_threshold` | < 0 | 0.0 |
| `yield_threshold` | > 100 | 100.0 |
| `log_level` | Invalid | "INFO" |
| `station_name_source` | Invalid | "hostname" |
| `proxy_mode` | Invalid | "system" |

## Best Practices

### 1. Always Use Atomic Writes for Critical Data

```python
# Good: Atomic write protects against power failure/crashes
SafeFileWriter.write_json_atomic(path, data, create_backup=True)

# Bad: Partial write can corrupt file
with open(path, 'w') as f:
    json.dump(data, f)  # If crash occurs here, file is corrupted
```

### 2. Enable Backups for Important Files

```python
# Enable backup creation
SafeFileWriter.write_json_atomic(path, data, create_backup=True)

# Backups are automatically used for recovery
data = SafeFileReader.read_json_safe(path)  # Falls back to .bak if needed
```

### 3. Use Locking for Shared Files

```python
# When multiple processes might access the same file:
with locked_file(path, mode='r+', timeout=10.0) as f:
    data = json.load(f)
    data['counter'] += 1
    f.seek(0)
    f.truncate()
    json.dump(data, f)
```

### 4. Validate After Loading

```python
config = ClientConfig.load(path)
if not config.is_valid():
    errors = config.validate()
    logger.warning(f"Config validation errors: {errors}")
    repairs = config.repair()
    config.save()
```

### 5. Use load_and_repair for Robustness

```python
# For production use, prefer load_and_repair
config, repairs = ClientConfig.load_and_repair(path)
# Handles corrupted files gracefully and fixes common issues
```

## Error Handling

### File Locking Timeouts

```python
from pywats_client.core.file_utils import locked_file

try:
    with locked_file(path, mode='w', timeout=5.0) as f:
        # ... write operations
        pass
except TimeoutError:
    logger.error("Could not acquire file lock within timeout")
```

### Corrupted Files

```python
# SafeFileReader returns None for unrecoverable corruption
data = SafeFileReader.read_json_safe(path)
if data is None:
    logger.error("Config corrupted and no valid backup")
    # Create fresh config
    data = create_default_config()
```

### Validation Errors

```python
config = ClientConfig.load(path)
errors = config.validate()

# Decide how to handle errors
if errors:
    # Option 1: Auto-repair
    repairs = config.repair()
    
    # Option 2: Report to user
    for error in errors:
        show_error_to_user(error)
    
    # Option 3: Use defaults for invalid fields only
    # (Custom logic based on error types)
```

## Converter Configuration Validation

Converter configurations have their own validation:

```python
from pywats_client.core.config import ConverterConfig

converter = ConverterConfig(
    name="My Converter",
    module_path="my_module.MyConverter",
    converter_type="file",
    watch_folder="/path/to/watch"
)

errors = converter.validate()
# Validates:
# - name is required
# - module_path is required
# - converter_type is valid
# - watch_folder required for file/folder converters
# - schedule required for scheduled converters
# - threshold values in valid ranges
```

## Migration Notes

If upgrading from older versions that used raw file I/O:

1. **ConfigManager** now uses `SafeFileWriter.write_json_atomic()` and `SafeFileReader.read_json_safe()`
2. **ClientConfig.save()** now creates backups automatically
3. **ClientConfig.load()** now recovers from backups when possible
4. **PersistentQueue** already used safe file utilities (no changes needed)

Existing configuration files remain compatible - the safe file utilities work transparently with existing JSON files.

## See Also

- [IPC Security Guide](./ipc-security.md) - IPC authentication and security
- [Converter Security Guide](./converter-security.md) - Converter sandboxing
- [Troubleshooting Guide](../TROUBLESHOOTING.md) - Common issues and solutions
