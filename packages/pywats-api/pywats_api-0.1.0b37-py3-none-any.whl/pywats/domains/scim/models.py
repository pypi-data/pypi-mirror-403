"""SCIM domain models.

System for Cross-domain Identity Management (SCIM) models for user provisioning.

SCIM is an industry standard protocol for managing user identities across
cloud services. This module provides models for the WATS SCIM API endpoints.

BACKEND API MAPPING
-------------------
These models are used with the WATS /api/SCIM/v2/* endpoints.

FIELD NAMING CONVENTION:
------------------------
All fields use Python snake_case naming (e.g., user_name, display_name).
Backend API aliases (camelCase) are handled automatically.
Always use the Python field names when creating or accessing these models.
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from uuid import UUID
from pydantic import Field, AliasChoices, ConfigDict

from ...shared.base_model import PyWATSModel


class ScimToken(PyWATSModel):
    """
    Represents a SCIM JWT token response.
    
    Returned from GET /api/SCIM/v2/Token.
    
    The token is used for automatic user provisioning from Azure AD.
    
    Attributes:
        token: The JWT token string
        expires_utc: Token expiration timestamp (UTC)
        duration_days: Token validity duration in days
        
    Example:
        >>> token_response = api.scim.get_token(duration_days=90)
        >>> print(f"Token expires: {token_response.expires_utc}")
        >>> # Use token_response.token for Azure provisioning configuration
    """
    
    token: Optional[str] = Field(
        default=None,
        description="The JWT token string for Azure provisioning"
    )
    expires_utc: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("expiresUtc", "expires_utc", "expires"),
        serialization_alias="expiresUtc",
        description="Token expiration timestamp (UTC)"
    )
    duration_days: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("durationDays", "duration_days", "duration"),
        serialization_alias="durationDays",
        description="Token validity duration in days"
    )
    # Forward-compatible: allow extra fields from backend
    model_config = ConfigDict(**PyWATSModel.model_config, extra="allow")


class ScimUserName(PyWATSModel):
    """
    SCIM user name components.
    
    Represents the structured name of a user.
    
    Attributes:
        formatted: Full formatted name
        given_name: First name
        family_name: Last name (surname)
    """
    
    formatted: Optional[str] = Field(
        default=None,
        description="Full formatted name"
    )
    given_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("givenName", "given_name"),
        serialization_alias="givenName",
        description="First name"
    )
    family_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("familyName", "family_name"),
        serialization_alias="familyName",
        description="Last name (surname)"
    )


class ScimUserEmail(PyWATSModel):
    """
    SCIM user email entry.
    
    Represents an email address for a user.
    
    Attributes:
        value: Email address
        type: Email type (e.g., "work", "home")
        primary: Whether this is the primary email
    """
    
    value: Optional[str] = Field(
        default=None,
        description="Email address"
    )
    type: Optional[str] = Field(
        default=None,
        description="Email type (e.g., 'work', 'home')"
    )
    primary: Optional[bool] = Field(
        default=None,
        description="Whether this is the primary email"
    )


class ScimUser(PyWATSModel):
    """
    Represents a SCIM user resource.
    
    Used with GET/POST/PATCH /api/SCIM/v2/Users endpoints.
    
    SCIM users are provisioned from Azure AD for single sign-on and
    automatic user management.
    
    Attributes:
        id: Unique user identifier (GUID)
        user_name: Username (typically email address)
        display_name: Display name
        active: Whether the user is active
        external_id: External ID from Azure AD
        name: Structured name components
        emails: List of email addresses
        schemas: SCIM schemas for this resource
        meta: SCIM metadata
        
    Example:
        >>> # Create a new user
        >>> user = ScimUser(
        ...     user_name="john.doe@example.com",
        ...     display_name="John Doe",
        ...     active=True,
        ...     name=ScimUserName(given_name="John", family_name="Doe")
        ... )
        >>> created_user = api.scim.create_user(user)
        >>> print(f"Created user ID: {created_user.id}")
    """
    
    id: Optional[str] = Field(
        default=None,
        description="Unique user identifier (GUID)"
    )
    user_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("userName", "user_name"),
        serialization_alias="userName",
        description="Username (typically email address)"
    )
    display_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("displayName", "display_name"),
        serialization_alias="displayName",
        description="Display name"
    )
    active: Optional[bool] = Field(
        default=None,
        description="Whether the user is active"
    )
    external_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("externalId", "external_id"),
        serialization_alias="externalId",
        description="External ID from Azure AD"
    )
    name: Optional[ScimUserName] = Field(
        default=None,
        description="Structured name components"
    )
    emails: Optional[List[ScimUserEmail]] = Field(
        default=None,
        description="List of email addresses"
    )
    schemas: Optional[List[str]] = Field(
        default=None,
        description="SCIM schemas for this resource"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="SCIM metadata (resourceType, created, lastModified, etc.)"
    )
    # Forward-compatible: allow extra fields from backend
    model_config = ConfigDict(**PyWATSModel.model_config, extra="allow")


class ScimPatchOperation(PyWATSModel):
    """
    Represents a single SCIM patch operation.
    
    Used within ScimPatchRequest for PATCH /api/SCIM/v2/Users/{id}.
    
    Attributes:
        op: Operation type (only "replace" is supported)
        path: Path to the attribute to update (e.g., "displayName", "active")
        value: New value (string or boolean depending on attribute type)
        
    Example:
        >>> op = ScimPatchOperation(op="replace", path="active", value=False)
    """
    
    op: Optional[str] = Field(
        default="replace",
        description="Operation type (only 'replace' is supported)"
    )
    path: Optional[str] = Field(
        default=None,
        description="Path to the attribute to update"
    )
    value: Optional[Any] = Field(
        default=None,
        description="New value (string or boolean)"
    )


class ScimPatchRequest(PyWATSModel):
    """
    Represents a SCIM patch request body.
    
    Used with PATCH /api/SCIM/v2/Users/{id}.
    
    SCIM patch requests must include the schema and follow the RFC 7644 format.
    Only "replace" operations are supported by the WATS server.
    
    Attributes:
        schemas: Must include "urn:ietf:params:scim:api:messages:2.0:PatchOp"
        operations: List of patch operations
        
    Example:
        >>> # Deactivate a user
        >>> patch = ScimPatchRequest(
        ...     schemas=["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        ...     operations=[
        ...         ScimPatchOperation(op="replace", path="active", value=False)
        ...     ]
        ... )
        >>> api.scim.update_user("user-id", patch)
    """
    
    schemas: Optional[List[str]] = Field(
        default_factory=lambda: ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        description="SCIM patch schema"
    )
    operations: Optional[List[ScimPatchOperation]] = Field(
        default=None,
        validation_alias=AliasChoices("Operations", "operations"),
        serialization_alias="Operations",
        description="List of patch operations"
    )


class ScimListResponse(PyWATSModel):
    """
    Represents a SCIM list response.
    
    Returned from GET /api/SCIM/v2/Users.
    
    Attributes:
        total_results: Total number of results
        items_per_page: Number of items per page
        start_index: Starting index of results
        resources: List of user resources
        schemas: SCIM schemas for this response
        
    Example:
        >>> response = api.scim.get_users()
        >>> print(f"Total users: {response.total_results}")
        >>> for user in response.resources:
        ...     print(f"  {user.user_name}: {user.display_name}")
    """
    
    total_results: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("totalResults", "total_results"),
        serialization_alias="totalResults",
        description="Total number of results"
    )
    items_per_page: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("itemsPerPage", "items_per_page"),
        serialization_alias="itemsPerPage",
        description="Number of items per page"
    )
    start_index: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("startIndex", "start_index"),
        serialization_alias="startIndex",
        description="Starting index of results"
    )
    resources: Optional[List[ScimUser]] = Field(
        default=None,
        validation_alias=AliasChoices("Resources", "resources"),
        serialization_alias="Resources",
        description="List of user resources"
    )
    schemas: Optional[List[str]] = Field(
        default=None,
        description="SCIM schemas for this response"
    )
    # Forward-compatible: allow extra fields from backend
    model_config = ConfigDict(**PyWATSModel.model_config, extra="allow")
