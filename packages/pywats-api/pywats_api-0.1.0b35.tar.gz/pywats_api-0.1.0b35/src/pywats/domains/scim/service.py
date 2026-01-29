"""SCIM service - thin sync wrapper around AsyncScimService.

This module provides synchronous access to AsyncScimService methods.
All business logic is maintained in async_service.py (source of truth).
"""
from typing import Optional, List, Callable, Iterator

from .async_service import AsyncScimService
from .async_repository import AsyncScimRepository
from .models import (
    ScimToken,
    ScimUser,
    ScimPatchRequest,
    ScimListResponse,
)
from ...core.sync_runner import run_sync


class ScimService:
    """
    Synchronous wrapper for AsyncScimService.

    Provides sync access to all async SCIM service operations.
    All business logic is in AsyncScimService.
    """

    def __init__(self, async_service: AsyncScimService = None, *, repository=None):
        """
        Initialize with AsyncScimService or repository.

        Args:
            async_service: AsyncScimService instance to wrap
            repository: (Deprecated) Repository instance for backward compatibility
        """
        if repository is not None:
            # Backward compatibility: create async service from repository
            self._async_service = AsyncScimService(repository)
            self._repository = repository
        elif async_service is not None:
            self._async_service = async_service
            self._repository = async_service._repository
        else:
            raise ValueError("Either async_service or repository must be provided")

    @classmethod
    def from_repository(cls, repository: AsyncScimRepository) -> "ScimService":
        """Create ScimService from an AsyncScimRepository."""
        async_service = AsyncScimService(repository)
        return cls(async_service)

    # =========================================================================
    # Token
    # =========================================================================

    def get_token(self, duration_days: int = 90) -> Optional[ScimToken]:
        """Get a JWT token for SCIM provisioning from Azure AD."""
        return run_sync(self._async_service.get_token(duration_days=duration_days))

    # =========================================================================
    # Users - Query
    # =========================================================================

    def get_users(
        self,
        start_index: Optional[int] = None,
        count: Optional[int] = None,
    ) -> ScimListResponse:
        """Get SCIM users with optional pagination."""
        return run_sync(self._async_service.get_users(start_index=start_index, count=count))

    def iter_users(
        self,
        page_size: int = 100,
        max_users: Optional[int] = None,
        on_page: Optional[Callable[[int, int, Optional[int]], None]] = None,
    ) -> Iterator[ScimUser]:
        """Iterate over all SCIM users with automatic pagination."""
        async def collect_users():
            users = []
            async for user in self._async_service.iter_users(
                page_size=page_size,
                max_users=max_users,
                on_page=on_page,
            ):
                users.append(user)
            return users
        
        return iter(run_sync(collect_users()))

    def get_user(self, user_id: str) -> Optional[ScimUser]:
        """Get a SCIM user by ID."""
        return run_sync(self._async_service.get_user(user_id))

    def get_user_by_username(self, username: str) -> Optional[ScimUser]:
        """Get a SCIM user by username."""
        return run_sync(self._async_service.get_user_by_username(username))

    # =========================================================================
    # Users - Create, Update, Delete
    # =========================================================================

    def create_user(self, user: ScimUser) -> Optional[ScimUser]:
        """Create a new SCIM user."""
        return run_sync(self._async_service.create_user(user))

    def update_user(self, user_id: str, patch_request: ScimPatchRequest) -> Optional[ScimUser]:
        """Update a SCIM user using SCIM patch operations."""
        return run_sync(self._async_service.update_user(user_id, patch_request))

    def delete_user(self, user_id: str) -> None:
        """Delete a SCIM user by ID."""
        return run_sync(self._async_service.delete_user(user_id))

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def deactivate_user(self, user_id: str) -> Optional[ScimUser]:
        """Deactivate a SCIM user."""
        return run_sync(self._async_service.deactivate_user(user_id))

    def set_user_active(self, user_id: str, active: bool) -> Optional[ScimUser]:
        """Set a SCIM user's active status."""
        return run_sync(self._async_service.set_user_active(user_id, active))

    def update_display_name(self, user_id: str, display_name: str) -> Optional[ScimUser]:
        """Update a SCIM user's display name."""
        return run_sync(self._async_service.update_display_name(user_id, display_name))
