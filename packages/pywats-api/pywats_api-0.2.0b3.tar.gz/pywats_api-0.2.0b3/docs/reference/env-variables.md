# Environment Variables for pyWATS Client Debugging

## Overview

For development and debugging, you can use environment variables to provide credentials without committing them to the repository.

## Setup

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your credentials:**
   ```bash
   PYWATS_SERVER_URL=https://python.wats.com
   PYWATS_API_TOKEN=your_actual_token_here
   ```

3. **Load environment variables:**
   
   **PowerShell:**
   ```powershell
   # Load from .env file (requires dotenv package or manual loading)
   Get-Content .env | ForEach-Object {
       if ($_ -match '^([^=]+)=(.*)$') {
           [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
       }
   }
   ```
   
   **Bash/Linux:**
   ```bash
   export $(grep -v '^#' .env | xargs)
   ```
   
   **Or set directly:**
   ```powershell
   $env:PYWATS_SERVER_URL = "https://python.wats.com"
   $env:PYWATS_API_TOKEN = "cHlXQVRTX0FQ..."
   ```

4. **Run the client:**
   ```bash
   python -m pywats_client service --instance-id default
   ```

## How It Works

The `ClientConfig` class checks for environment variables at runtime via the `get_runtime_credentials()` method:

- `PYWATS_SERVER_URL` - Server URL (e.g., `https://python.wats.com`)
- `PYWATS_API_TOKEN` - API authentication token

**Important Behavior:**

1. **Environment variables are runtime-only** - They are NEVER saved to the config file
2. **Fallback mechanism** - Environment variables are only used if the config file has empty values
3. **Persistence** - Credentials entered through the GUI or saved to config.json are always persisted
4. **Development workflow** - Use env vars for debugging without modifying config files

This means:
- ✅ You can use env vars for debugging without them being saved to git
- ✅ Config file credentials (entered via GUI) persist between sessions
- ✅ Env vars only apply when config values are empty
- ✅ Changing credentials in GUI saves them properly to config.json

## VS Code Integration

For VS Code debugging, add to `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "pyWATS Client Service",
            "type": "python",
            "request": "launch",
            "module": "pywats_client",
            "args": ["service", "--instance-id", "default"],
            "env": {
                "PYWATS_SERVER_URL": "https://python.wats.com",
                "PYWATS_API_TOKEN": "your_token_here"
            }
        },
        {
            "name": "pyWATS Client GUI",
            "type": "python",
            "request": "launch",
            "module": "pywats_client",
            "args": ["gui", "--instance-id", "default"],
            "env": {
                "PYWATS_SERVER_URL": "https://python.wats.com",
                "PYWATS_API_TOKEN": "your_token_here"
            }
        }
    ]
}
```

## Security Notes

- ✅ `.env` is in `.gitignore` - safe for local credentials
- ✅ Environment variables are runtime-only and NEVER saved to config files
- ✅ Config file credentials (from GUI) are properly persisted
- ✅ Env vars don't override saved config values
- ⚠️ **Never commit `.env` or tokens to git**
- ⚠️ **Use test tokens for development, not production tokens**

## Getting Test Token

From test config:
```python
# api-tests/instances/client_a_config.json
{
    "service_address": "https://python.wats.com",
    "api_token": "cHlXQVRTX0FQSV9BVVRPVEVTVDo2cGhUUjg0ZTVIMHA1R3JUWGtQZlY0UTNvbmk2MiM="
}
```

Set in your local `.env`:
```bash
PYWATS_SERVER_URL=https://python.wats.com
PYWATS_API_TOKEN=cHlXQVRTX0FQSV9BVVRPVEVTVDo2cGhUUjg0ZTVIMHA1R3JUWGtQZlY0UTNvbmk2MiM=
```

## Priority Order

1. **Config file values** (if not empty)
2. **Environment variables** (if config empty)
3. **User prompt** (if both empty)

This means you can have different configs per instance but use env vars as a fallback for debugging.
