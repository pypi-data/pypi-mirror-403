# SCIM - User Provisioning

The SCIM (System for Cross-domain Identity Management) domain provides API access for automatic user provisioning from Azure Active Directory to WATS.

## Overview

SCIM is an industry standard protocol (RFC 7644) for managing user identities across cloud services. The WATS SCIM endpoint enables automatic user provisioning from Azure AD, supporting:

- User creation and deletion
- User activation/deactivation
- User attribute updates (display name, etc.)
- Token generation for Azure AD configuration

## Quick Start

### Synchronous Usage

```python
from pywats import pyWATS

api = pyWATS(
    base_url="https://your-wats-server.com",
    token="your-api-token"
)

# Get provisioning token for Azure AD configuration
token = api.scim.get_token(duration_days=90)
if token:
    print(f"Configure Azure with: {token.token[:50]}...")

# List all SCIM users
users = api.scim.get_users()
for user in users.resources or []:
    status = "active" if user.active else "inactive"
    print(f"{user.user_name}: {user.display_name} ({status})")
```

### Asynchronous Usage

For concurrent requests and better performance:

```python
import asyncio
from pywats import AsyncWATS

async def provision_users():
    async with AsyncWATS(
        base_url="https://your-wats-server.com",
        token="your-api-token"
    ) as api:
        # Get token and users concurrently
        token, users = await asyncio.gather(
            api.scim.get_token(duration_days=90),
            api.scim.get_users()
        )
        
        print(f"Token valid until: {token.expires_utc if token else 'N/A'}")
        print(f"Total users: {users.total_results}")

asyncio.run(provision_users())
```

## Service Methods

### Token Generation

```python
# Get JWT token for Azure AD provisioning configuration
token = api.scim.get_token(duration_days=90)
if token:
    print(f"Token expires: {token.expires_utc}")
    print(f"Token: {token.token}")
```

### User Listing

```python
# Get all SCIM users (single page)
response = api.scim.get_users()
print(f"Total users: {response.total_results}")

for user in response.resources or []:
    print(f"  {user.id}: {user.user_name}")
```

### Paginated User Iteration

```python
# Iterate over ALL users efficiently (automatic pagination)
for user in api.scim.iter_users(page_size=100):
    print(f"{user.user_name}: {user.display_name}")

# With max limit
for user in api.scim.iter_users(page_size=50, max_users=200):
    process_user(user)

# With progress callback
def on_page(page_num, items_so_far, total):
    print(f"Fetched page {page_num}, {items_so_far}/{total} users")

for user in api.scim.iter_users(on_page=on_page):
    sync_user(user)
```

### User Creation

```python
from pywats import ScimUser, ScimUserName, ScimUserEmail

# Create a new user
user = ScimUser(
    user_name="john.doe@example.com",
    display_name="John Doe",
    active=True,
    name=ScimUserName(given_name="John", family_name="Doe"),
    emails=[ScimUserEmail(value="john.doe@example.com", type="work", primary=True)]
)

created = api.scim.create_user(user)
if created:
    print(f"Created user ID: {created.id}")
```

### User Retrieval

```python
# Get user by ID
user = api.scim.get_user("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
if user:
    print(f"User: {user.display_name}")

# Get user by username
user = api.scim.get_user_by_username("john.doe@example.com")
if user:
    print(f"User ID: {user.id}")
```

### User Updates

```python
from pywats import ScimPatchRequest, ScimPatchOperation

# Update display name (convenience method)
updated = api.scim.update_display_name("user-id", "John Smith")

# Deactivate a user (convenience method)
deactivated = api.scim.deactivate_user("user-id")

# Set active status (convenience method)
activated = api.scim.set_user_active("user-id", active=True)

# Manual patch operation
patch = ScimPatchRequest(
    operations=[
        ScimPatchOperation(op="replace", path="displayName", value="Jane Doe"),
        ScimPatchOperation(op="replace", path="active", value=False)
    ]
)
updated = api.scim.update_user("user-id", patch)
```

### User Deletion

```python
# Delete user by ID
api.scim.delete_user("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
```

## Models

### ScimUser

Main user resource model.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique user identifier (GUID) |
| `user_name` | `str` | Username (typically email address) |
| `display_name` | `str` | Display name |
| `active` | `bool` | Whether user is active |
| `external_id` | `str` | External ID from Azure AD |
| `name` | `ScimUserName` | Structured name components |
| `emails` | `List[ScimUserEmail]` | Email addresses |
| `schemas` | `List[str]` | SCIM schemas |
| `meta` | `Dict` | SCIM metadata |

### ScimUserName

User name components.

| Field | Type | Description |
|-------|------|-------------|
| `formatted` | `str` | Full formatted name |
| `given_name` | `str` | First name |
| `family_name` | `str` | Last name (surname) |

### ScimUserEmail

User email entry.

| Field | Type | Description |
|-------|------|-------------|
| `value` | `str` | Email address |
| `type` | `str` | Email type (work, home, etc.) |
| `primary` | `bool` | Whether primary email |

### ScimToken

JWT token response.

| Field | Type | Description |
|-------|------|-------------|
| `token` | `str` | JWT token string |
| `expires_utc` | `datetime` | Token expiration (UTC) |
| `duration_days` | `int` | Token validity in days |

### ScimPatchRequest

SCIM patch request body.

| Field | Type | Description |
|-------|------|-------------|
| `schemas` | `List[str]` | Must include patch schema |
| `operations` | `List[ScimPatchOperation]` | Patch operations |

### ScimPatchOperation

Single patch operation.

| Field | Type | Description |
|-------|------|-------------|
| `op` | `str` | Operation type (only "replace" supported) |
| `path` | `str` | Attribute path |
| `value` | `Any` | New value |

### ScimListResponse

Paginated list response.

| Field | Type | Description |
|-------|------|-------------|
| `total_results` | `int` | Total result count |
| `items_per_page` | `int` | Items per page |
| `start_index` | `int` | Start index |
| `resources` | `List[ScimUser]` | User resources |
| `schemas` | `List[str]` | Response schemas |

## API Endpoints

| Method | Endpoint | Service Method |
|--------|----------|----------------|
| GET | `/api/SCIM/v2/Token` | `get_token()` |
| GET | `/api/SCIM/v2/Users` | `get_users()`, `iter_users()` |
| POST | `/api/SCIM/v2/Users` | `create_user()` |
| GET | `/api/SCIM/v2/Users/{id}` | `get_user()` |
| DELETE | `/api/SCIM/v2/Users/{id}` | `delete_user()` |
| PATCH | `/api/SCIM/v2/Users/{id}` | `update_user()` |
| GET | `/api/SCIM/v2/Users/userName={userName}` | `get_user_by_username()` |

## Azure AD Configuration

To configure Azure AD for automatic provisioning:

1. Generate a provisioning token:
   ```python
   token = api.scim.get_token(duration_days=90)
   ```

2. In Azure AD Enterprise Applications:
   - Select your WATS application
   - Go to Provisioning
   - Set Provisioning Mode to "Automatic"
   - Enter your WATS SCIM endpoint URL: `https://your-wats-server.com/api/SCIM/v2`
   - Use the generated token as the "Secret Token"

3. Configure attribute mappings as needed

4. Enable provisioning

## Error Handling

```python
from pywats import PyWATSError, NotFoundError

try:
    user = api.scim.get_user("non-existent-id")
except NotFoundError:
    print("User not found")
except PyWATSError as e:
    print(f"SCIM error: {e}")
```

## Notes

- SCIM PATCH operations only support "replace" operation type
- Users provisioned via SCIM should be managed through Azure AD
- Token duration default is 90 days if not specified
- All models use snake_case field names (camelCase aliases handled automatically)
