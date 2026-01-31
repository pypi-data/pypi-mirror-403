# IPC Security Guide

This guide documents the security features for Inter-Process Communication (IPC) in pyWATS Client, which connects the GUI to the background service.

## Overview

pyWATS Client uses Unix domain sockets (or named pipes on Windows) for communication between the GUI and the service. This guide covers authentication and rate limiting features.

### Security Model

pyWATS uses a **pragmatic security approach**:

- **Target Environment:** Secure stations behind machine authentication
- **Threat Model:** Prevent accidents and basic abuse, not sophisticated attacks
- **Philosophy:** "Friendly" environment - trusted users on controlled machines

## IPC Architecture

```
┌──────────────┐          ┌──────────────────┐
│   GUI App    │◄────────►│  AsyncIPCServer  │
│              │  Socket  │                  │
│ AsyncIPCClient│          │  - Auth Handler  │
│              │          │  - Rate Limiter  │
└──────────────┘          └──────────────────┘
        │                         │
        │     Shared Secret       │
        └─────────────────────────┘
              (file-based)
```

## Authentication

### Shared Secret Authentication

The IPC server uses a shared secret for authentication:

1. **Secret Generation:** Service generates 256-bit random token on startup
2. **Secret Storage:** Stored in user-specific secure location
3. **Client Authentication:** Client reads secret and sends with connection
4. **Validation:** Server validates using timing-safe comparison

### Secret Storage Locations

| Platform | Location |
|----------|----------|
| Linux/macOS | `~/.config/pywats/secrets/<instance_id>.key` |
| Windows | `%LOCALAPPDATA%\pyWATS\secrets\<instance_id>.key` |

Files are created with restricted permissions:
- Unix: `0600` (owner read/write only)
- Windows: Current user only

### Authentication Flow

```
Client                              Server
   │                                   │
   │──────── Connect ─────────────────►│
   │                                   │
   │◄─────── Welcome ──────────────────│
   │                                   │
   │──────── auth <token> ────────────►│
   │                                   │
   │◄─────── OK | DENIED ──────────────│
   │                                   │
   │──────── (authenticated) ─────────►│
```

### Implementation

Server-side (AsyncIPCServer):

```python
async def _handle_auth(self, client_id: str, parts: List[str]):
    """Handle authentication request."""
    if len(parts) < 2:
        return "ERROR missing_token"
    
    token = parts[1]
    
    # Timing-safe comparison
    if secrets.compare_digest(token, self._auth_token):
        self._authenticated_clients.add(client_id)
        return "OK authenticated"
    else:
        return "DENIED invalid_token"
```

Client-side (AsyncIPCClient):

```python
async def _authenticate(self):
    """Authenticate with the server."""
    token = load_secret(self._instance_id)
    if not token:
        raise IPCAuthError("No secret available")
    
    response = await self._send_command(f"auth {token}")
    if not response.startswith("OK"):
        raise IPCAuthError(f"Authentication failed: {response}")
```

## Rate Limiting

### Token Bucket Algorithm

The server implements rate limiting using a token bucket:

- **Bucket Size (Burst):** 20 requests
- **Refill Rate:** 100 requests per minute
- **Per-Client:** Each connection has its own bucket

### Behavior

1. Each request consumes one token
2. Tokens refill over time
3. When bucket is empty, requests are rejected
4. `ping` command is always allowed (for health checks)

### Configuration

```python
from pywats_client.core.security import RateLimiter

# Create rate limiter with custom settings
limiter = RateLimiter(
    max_tokens=20,          # Burst size
    refill_rate=100,        # Tokens per minute
    cleanup_interval=300,   # Clean old buckets every 5 min
)
```

### Rate Limit Response

When rate limit is exceeded:

```
Client: some_command
Server: RATE_LIMIT rate_limit_exceeded
```

## Security API

### Core Security Module

Location: `src/pywats_client/core/security.py`

#### Secret Management

```python
from pywats_client.core.security import (
    generate_secret,
    save_secret,
    load_secret,
    delete_secret,
)

# Generate new secret
secret = generate_secret()  # 64-character hex string

# Save to secure location
save_secret("instance-1", secret)

# Load secret
loaded = load_secret("instance-1")

# Delete secret
delete_secret("instance-1")
```

#### Token Validation

```python
from pywats_client.core.security import validate_token

# Timing-safe comparison
is_valid = validate_token(provided_token, expected_token)
```

#### Rate Limiting

```python
from pywats_client.core.security import RateLimiter

limiter = RateLimiter()

# Check if request allowed
if limiter.check("client-1"):
    # Process request
    pass
else:
    # Rate limited
    pass

# Reset a client's bucket
limiter.reset("client-1")
```

## IPC Commands

### Authentication Commands

| Command | Description | Auth Required |
|---------|-------------|---------------|
| `ping` | Health check | No |
| `auth <token>` | Authenticate | No |
| `status` | Get service status | Yes |
| `start` | Start service | Yes |
| `stop` | Stop service | Yes |

### Example Session

```
# Connect to server
> ping
< PONG

# Authenticate
> auth abc123...
< OK authenticated

# Now can use protected commands
> status
< RUNNING processing_files=5

# Unauthenticated commands rejected
> status  # (without auth)
< ERROR authentication_required
```

## Troubleshooting

### Authentication Failures

**Symptom:** `DENIED invalid_token`

**Solutions:**
1. Check secret file exists in correct location
2. Verify file permissions allow reading
3. Ensure service and client use same instance ID
4. Restart service to regenerate secret

### Rate Limiting Issues

**Symptom:** `RATE_LIMIT rate_limit_exceeded`

**Solutions:**
1. Reduce request frequency
2. Use batch commands where possible
3. Check for runaway loops in client code
4. Increase rate limits if legitimate use case

### Permission Errors

**Symptom:** Cannot read/write secret file

**Solutions:**
1. Check directory permissions
2. Run as correct user
3. Ensure parent directories exist

## Security Notes

### What This Protects Against

- Accidental connections from other programs
- Basic unauthorized access
- Request flooding (accidental or intentional)

### What This Does NOT Protect Against

- Local privilege escalation
- Root/Admin access to machine
- Memory inspection attacks
- Hardware attacks

### Recommendations

1. **Secure Machine Access** - IPC security is a layer, not the only protection
2. **User Separation** - Each user should have their own service instance
3. **Secret Rotation** - Secrets are regenerated on service restart
4. **Monitor Logs** - Watch for authentication failures

## Implementation Details

### Files

- `src/pywats_client/core/security.py` - Security utilities
- `src/pywats_client/service/async_ipc_server.py` - Server with auth/rate limiting
- `src/pywats_client/service/async_ipc_client.py` - Client with authentication

### Tests

- `tests/client/test_security.py` - Security module tests
- `tests/client/test_ipc_auth.py` - IPC authentication tests

### Test Results

- Security tests: 16 passed
- IPC auth tests: 12 passed
