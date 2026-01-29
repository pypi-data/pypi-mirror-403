"""Async SCIM domain service.

Async business logic layer for SCIM (System for Cross-domain Identity Management) operations.
"""
from typing import Optional, AsyncIterator, Callable

from .async_repository import AsyncScimRepository
from .models import (
    ScimToken,
    ScimUser,
    ScimPatchRequest,
    ScimPatchOperation,
    ScimListResponse,
)


class AsyncScimService:
    """
    Async service for SCIM user provisioning operations.
    
    Provides high-level async methods for managing SCIM users in WATS.
    """

    def __init__(self, repository: AsyncScimRepository):
        """
        Initialize the async SCIM service.
        
        Args:
            repository: AsyncScimRepository instance for API access
        """
        self._repository = repository

    async def get_token(self, duration_days: int = 90) -> Optional[ScimToken]:
        """
        Get a JWT token for SCIM provisioning from Azure AD.
        
        Args:
            duration_days: Token validity duration in days (default: 90)
            
        Returns:
            ScimToken with JWT and expiration info, or None
        """
        return await self._repository.get_token(duration_days=duration_days)

    async def get_users(
        self,
        start_index: Optional[int] = None,
        count: Optional[int] = None,
    ) -> ScimListResponse:
        """
        Get SCIM users with optional pagination.
        
        Args:
            start_index: 1-based starting index for pagination (SCIM spec)
            count: Maximum number of users to return per page
            
        Returns:
            ScimListResponse containing user resources
        """
        return await self._repository.get_users(start_index=start_index, count=count)

    async def iter_users(
        self,
        page_size: int = 100,
        max_users: Optional[int] = None,
        on_page: Optional[Callable[[int, int, Optional[int]], None]] = None,
    ) -> AsyncIterator[ScimUser]:
        """
        Iterate over all SCIM users with automatic pagination.
        
        Memory-efficient async iterator that fetches users page by page.
        
        Args:
            page_size: Number of users per page (default: 100)
            max_users: Maximum users to retrieve (default: all)
            on_page: Optional callback (page_num, users_so_far, total)
            
        Yields:
            ScimUser objects one at a time
        """
        start_index = 1
        page_num = 0
        users_yielded = 0
        
        while True:
            response = await self._repository.get_users(
                start_index=start_index, 
                count=page_size
            )
            
            resources = response.resources or []
            total = response.total_results
            
            page_num += 1
            if on_page:
                on_page(page_num, users_yielded + len(resources), total)
            
            for user in resources:
                if max_users and users_yielded >= max_users:
                    return
                yield user
                users_yielded += 1
            
            if not resources or len(resources) < page_size:
                break
            if total and start_index + len(resources) > total:
                break
            
            start_index += len(resources)

    async def create_user(self, user: ScimUser) -> Optional[ScimUser]:
        """
        Create a new SCIM user.
        
        Args:
            user: User data to create
            
        Returns:
            The created ScimUser with assigned ID, or None
        """
        return await self._repository.create_user(user)

    async def get_user(self, user_id: str) -> Optional[ScimUser]:
        """
        Get a SCIM user by ID.
        
        Args:
            user_id: The unique user identifier (GUID)
            
        Returns:
            ScimUser details, or None if not found
        """
        return await self._repository.get_user(user_id)

    async def delete_user(self, user_id: str) -> None:
        """
        Delete a SCIM user by ID.
        
        Args:
            user_id: The unique user identifier (GUID)
        """
        return await self._repository.delete_user(user_id)

    async def update_user(self, user_id: str, patch_request: ScimPatchRequest) -> Optional[ScimUser]:
        """
        Update a SCIM user using SCIM patch operations.
        
        Args:
            user_id: The unique user identifier (GUID)
            patch_request: SCIM patch request with operations to apply
            
        Returns:
            Updated ScimUser details, or None
        """
        return await self._repository.update_user(user_id, patch_request)

    async def get_user_by_username(self, username: str) -> Optional[ScimUser]:
        """
        Get a SCIM user by username.
        
        Args:
            username: The username to search for
            
        Returns:
            ScimUser details, or None if not found
        """
        return await self._repository.get_user_by_username(username)

    # Convenience methods

    async def deactivate_user(self, user_id: str) -> Optional[ScimUser]:
        """
        Deactivate a SCIM user.
        
        Args:
            user_id: The unique user identifier (GUID)
            
        Returns:
            Updated ScimUser details, or None
        """
        return await self.set_user_active(user_id, active=False)

    async def set_user_active(self, user_id: str, active: bool) -> Optional[ScimUser]:
        """
        Set a SCIM user's active status.
        
        Args:
            user_id: The unique user identifier (GUID)
            active: True to activate, False to deactivate
            
        Returns:
            Updated ScimUser details, or None
        """
        patch = ScimPatchRequest(
            operations=[
                ScimPatchOperation(op="replace", path="active", value=active)
            ]
        )
        return await self._repository.update_user(user_id, patch)

    async def update_display_name(self, user_id: str, display_name: str) -> Optional[ScimUser]:
        """
        Update a SCIM user's display name.
        
        Args:
            user_id: The unique user identifier (GUID)
            display_name: New display name
            
        Returns:
            Updated ScimUser details, or None
        """
        patch = ScimPatchRequest(
            operations=[
                ScimPatchOperation(op="replace", path="displayName", value=display_name)
            ]
        )
        return await self._repository.update_user(user_id, patch)
