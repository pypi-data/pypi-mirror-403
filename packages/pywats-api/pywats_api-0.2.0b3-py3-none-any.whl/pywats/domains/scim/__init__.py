"""SCIM domain package.

System for Cross-domain Identity Management (SCIM) domain for user provisioning.

This module provides access to SCIM user management functionality for
automatic user provisioning from Azure Active Directory to WATS.

EXPORTS
-------
Models:
    ScimToken           - JWT token response for Azure provisioning
    ScimUser            - SCIM user resource
    ScimUserName        - User name components (given/family name)
    ScimUserEmail       - User email entry
    ScimPatchRequest    - SCIM patch request body
    ScimPatchOperation  - Single patch operation
    ScimListResponse    - List response with user resources

USAGE
-----
>>> # Access via the main client
>>> from pywats import pyWATS
>>> api = pyWATS(base_url="https://myserver", token="...")

>>> # Get provisioning token for Azure AD
>>> token = api.scim.get_token(duration_days=90)

>>> # List all users
>>> users = api.scim.get_users()
>>> for user in users.resources:
...     print(f"{user.user_name}: {user.display_name}")

>>> # Create a new user
>>> from pywats.domains.scim import ScimUser, ScimUserName
>>> user = ScimUser(
...     user_name="john.doe@example.com",
...     display_name="John Doe",
...     active=True
... )
>>> created = api.scim.create_user(user)
"""
# Models
from .models import (
    ScimToken,
    ScimUser,
    ScimUserName,
    ScimUserEmail,
    ScimPatchRequest,
    ScimPatchOperation,
    ScimListResponse,
)

# Async implementations (primary API)
from .async_repository import AsyncScimRepository
from .async_service import AsyncScimService

__all__ = [
    # Models
    "ScimToken",
    "ScimUser",
    "ScimUserName",
    "ScimUserEmail",
    "ScimPatchRequest",
    "ScimPatchOperation",
    "ScimListResponse",
    # Async implementations
    "AsyncScimRepository",
    "AsyncScimService",
]
