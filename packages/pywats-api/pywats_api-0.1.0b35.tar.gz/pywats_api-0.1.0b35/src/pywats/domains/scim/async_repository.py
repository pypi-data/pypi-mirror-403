"""Async SCIM domain repository.

Async data access layer for SCIM (System for Cross-domain Identity Management) operations.
All endpoints are defined in pywats.core.routes.Routes.
"""
from typing import Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from ...core.async_client import AsyncHttpClient
    from ...core.exceptions import ErrorHandler

from ...core.routes import Routes
from .models import (
    ScimToken,
    ScimUser,
    ScimPatchRequest,
    ScimListResponse,
)

logger = logging.getLogger(__name__)


class AsyncScimRepository:
    """
    Async repository for SCIM API operations.
    
    Provides low-level async data access methods for SCIM user provisioning.
    """

    def __init__(
        self, 
        http_client: "AsyncHttpClient",
        error_handler: Optional["ErrorHandler"] = None
    ):
        """
        Initialize the async SCIM repository.
        
        Args:
            http_client: AsyncHttpClient for API calls
            error_handler: ErrorHandler for response processing
        """
        from ...core.exceptions import ErrorHandler, ErrorMode
        self._http_client = http_client
        self._error_handler = error_handler or ErrorHandler(ErrorMode.STRICT)

    async def get_token(self, duration_days: int = 90) -> Optional[ScimToken]:
        """
        Get a JWT token for SCIM provisioning from Azure AD.
        
        GET /api/SCIM/v2/Token
        
        Args:
            duration_days: Token validity duration in days (default: 90)
            
        Returns:
            ScimToken with JWT and expiration info, or None
        """
        response = await self._http_client.get(
            Routes.SCIM.TOKEN,
            params={"duration": duration_days}
        )
        data = self._error_handler.handle_response(
            response, operation="get_token", allow_empty=False
        )
        if data:
            return ScimToken.model_validate(data)
        return None

    async def get_users(
        self,
        start_index: Optional[int] = None,
        count: Optional[int] = None,
    ) -> ScimListResponse:
        """
        Get SCIM users with optional pagination.
        
        GET /api/SCIM/v2/Users
        
        Args:
            start_index: 1-based starting index for pagination (SCIM spec)
            count: Maximum number of users to return
            
        Returns:
            ScimListResponse containing user resources
        """
        params = {}
        if start_index is not None:
            params["startIndex"] = start_index
        if count is not None:
            params["count"] = count
            
        response = await self._http_client.get(Routes.SCIM.USERS, params=params or None)
        data = self._error_handler.handle_response(
            response, operation="get_users", allow_empty=True
        )
        if data:
            return ScimListResponse.model_validate(data)
        return ScimListResponse(resources=[], total_results=0)

    async def create_user(self, user: ScimUser) -> Optional[ScimUser]:
        """
        Create a new SCIM user.
        
        POST /api/SCIM/v2/Users
        
        Args:
            user: User data to create
            
        Returns:
            The created ScimUser with assigned ID, or None
        """
        response = await self._http_client.post(
            Routes.SCIM.USERS,
            json=user.model_dump(by_alias=True, exclude_none=True)
        )
        data = self._error_handler.handle_response(
            response, operation="create_user", allow_empty=False
        )
        if data:
            logger.info(f"Created SCIM user: {user.user_name}")
            return ScimUser.model_validate(data)
        return None

    async def get_user(self, user_id: str) -> Optional[ScimUser]:
        """
        Get a SCIM user by ID.
        
        GET /api/SCIM/v2/Users/{id}
        
        Args:
            user_id: The unique user identifier (GUID)
            
        Returns:
            ScimUser details, or None if not found
        """
        response = await self._http_client.get(Routes.SCIM.user(user_id))
        data = self._error_handler.handle_response(
            response, operation="get_user", allow_empty=True
        )
        if data:
            return ScimUser.model_validate(data)
        return None

    async def delete_user(self, user_id: str) -> None:
        """
        Delete a SCIM user by ID.
        
        DELETE /api/SCIM/v2/Users/{id}
        
        Args:
            user_id: The unique user identifier (GUID)
        """
        response = await self._http_client.delete(Routes.SCIM.user(user_id))
        self._error_handler.handle_response(
            response, operation="delete_user", allow_empty=True
        )
        logger.info(f"Deleted SCIM user: {user_id}")

    async def update_user(self, user_id: str, patch_request: ScimPatchRequest) -> Optional[ScimUser]:
        """
        Update a SCIM user using SCIM patch operations.
        
        PATCH /api/SCIM/v2/Users/{id}
        
        Args:
            user_id: The unique user identifier (GUID)
            patch_request: SCIM patch request with operations to apply
            
        Returns:
            Updated ScimUser details, or None
        """
        response = await self._http_client.patch(
            Routes.SCIM.user(user_id),
            json=patch_request.model_dump(by_alias=True, exclude_none=True)
        )
        data = self._error_handler.handle_response(
            response, operation="update_user", allow_empty=False
        )
        if data:
            logger.info(f"Updated SCIM user: {user_id}")
            return ScimUser.model_validate(data)
        return None

    async def get_user_by_username(self, username: str) -> Optional[ScimUser]:
        """
        Get a SCIM user by username.
        
        GET /api/SCIM/v2/Users/userName={userName}
        
        Args:
            username: The username to search for
            
        Returns:
            ScimUser details, or None if not found
        """
        response = await self._http_client.get(Routes.SCIM.user_by_name(username))
        data = self._error_handler.handle_response(
            response, operation="get_user_by_username", allow_empty=True
        )
        if data:
            return ScimUser.model_validate(data)
        return None
