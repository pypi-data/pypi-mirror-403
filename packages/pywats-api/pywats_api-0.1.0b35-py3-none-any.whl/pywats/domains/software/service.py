"""Software service - thin sync wrapper around AsyncSoftwareService.

This module provides synchronous access to AsyncSoftwareService methods.
All business logic is maintained in async_service.py (source of truth).

⚠️ INTERNAL API methods are marked and may change without notice.
"""
from typing import Optional, List, Union, Dict, Any
from uuid import UUID

from .async_service import AsyncSoftwareService
from .async_repository import AsyncSoftwareRepository
from .models import Package, PackageFile, PackageTag, VirtualFolder
from .enums import PackageStatus
from ...core.sync_runner import run_sync


class SoftwareService:
    """
    Synchronous wrapper for AsyncSoftwareService.

    Provides sync access to all async software service operations.
    All business logic is in AsyncSoftwareService.
    """

    def __init__(self, async_service: AsyncSoftwareService = None, *, repository=None):
        """
        Initialize with AsyncSoftwareService or repository.

        Args:
            async_service: AsyncSoftwareService instance to wrap
            repository: (Deprecated) Repository instance for backward compatibility
        """
        if repository is not None:
            # Backward compatibility: create async service from repository
            self._async_service = AsyncSoftwareService(repository)
            self._repository = repository
        elif async_service is not None:
            self._async_service = async_service
            self._repository = async_service._repository
        else:
            raise ValueError("Either async_service or repository must be provided")

    @classmethod
    def from_repository(cls, repository: AsyncSoftwareRepository) -> "SoftwareService":
        """Create SoftwareService from an AsyncSoftwareRepository."""
        async_service = AsyncSoftwareService(repository)
        return cls(async_service)

    # =========================================================================
    # Query Packages
    # =========================================================================

    def get_packages(self) -> List[Package]:
        """Get all available software packages."""
        return run_sync(self._async_service.get_packages())

    def get_package(self, package_id: Union[str, UUID]) -> Optional[Package]:
        """Get a specific software package by ID."""
        return run_sync(self._async_service.get_package(package_id))

    def get_package_by_name(
        self,
        name: str,
        status: Optional[PackageStatus] = None,
        version: Optional[int] = None,
    ) -> Optional[Package]:
        """Get a software package by name."""
        return run_sync(self._async_service.get_package_by_name(name, status, version))

    def get_released_package(self, name: str) -> Optional[Package]:
        """Get the released version of a package."""
        return run_sync(self._async_service.get_released_package(name))

    def get_packages_by_tag(
        self,
        tag: str,
        value: str,
        status: Optional[PackageStatus] = None,
    ) -> List[Package]:
        """Get packages filtered by tag."""
        return run_sync(self._async_service.get_packages_by_tag(tag, value, status))

    # =========================================================================
    # Create, Update, Delete Packages
    # =========================================================================

    def create_package(
        self,
        name: str,
        description: Optional[str] = None,
        install_on_root: bool = False,
        root_directory: Optional[str] = None,
        priority: Optional[int] = None,
        tags: Optional[List[PackageTag]] = None,
    ) -> Optional[Package]:
        """Create a new package in Draft status."""
        return run_sync(self._async_service.create_package(
            name=name,
            description=description,
            install_on_root=install_on_root,
            root_directory=root_directory,
            priority=priority,
            tags=tags,
        ))

    def update_package(self, package: Package) -> Optional[Package]:
        """Update a software package."""
        return run_sync(self._async_service.update_package(package))

    def delete_package(self, package_id: Union[str, UUID]) -> bool:
        """Delete a software package by ID."""
        return run_sync(self._async_service.delete_package(package_id))

    def delete_package_by_name(
        self, name: str, version: Optional[int] = None
    ) -> bool:
        """Delete a software package by name."""
        return run_sync(self._async_service.delete_package_by_name(name, version))

    # =========================================================================
    # Package Status Workflow
    # =========================================================================

    def submit_for_review(self, package_id: Union[str, UUID]) -> bool:
        """Submit a draft package for review (Draft -> Pending)."""
        return run_sync(self._async_service.submit_for_review(package_id))

    def return_to_draft(self, package_id: Union[str, UUID]) -> bool:
        """Return a pending package to draft (Pending -> Draft)."""
        return run_sync(self._async_service.return_to_draft(package_id))

    def release_package(self, package_id: Union[str, UUID]) -> bool:
        """Release a pending package (Pending -> Released)."""
        return run_sync(self._async_service.release_package(package_id))

    def revoke_package(self, package_id: Union[str, UUID]) -> bool:
        """Revoke a released package (Released -> Revoked)."""
        return run_sync(self._async_service.revoke_package(package_id))

    # =========================================================================
    # Package Files
    # =========================================================================

    def get_package_files(
        self, package_id: Union[str, UUID]
    ) -> List[PackageFile]:
        """Get files associated with a package."""
        return run_sync(self._async_service.get_package_files(package_id))

    def upload_zip(
        self,
        package_id: Union[str, UUID],
        zip_content: bytes,
        clean_install: bool = False,
    ) -> bool:
        """Upload a zip file to a software package."""
        return run_sync(self._async_service.upload_zip(package_id, zip_content, clean_install))

    def update_file_attribute(
        self, file_id: Union[str, UUID], attributes: str
    ) -> bool:
        """Update file attributes for a specific file."""
        return run_sync(self._async_service.update_file_attribute(file_id, attributes))

    # =========================================================================
    # Virtual Folders
    # =========================================================================

    def get_virtual_folders(self) -> List[VirtualFolder]:
        """Get all virtual folders registered in Production Manager."""
        return run_sync(self._async_service.get_virtual_folders())

    # =========================================================================
    # ⚠️ INTERNAL API - Connection Check
    # =========================================================================

    def is_connected(self) -> bool:
        """⚠️ INTERNAL: Check if Software module is connected."""
        return run_sync(self._async_service.is_connected())

    # =========================================================================
    # ⚠️ INTERNAL API - File Operations
    # =========================================================================

    def get_file(self, file_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Get file metadata by ID."""
        return run_sync(self._async_service.get_file(file_id))

    def check_file(
        self,
        package_id: Union[str, UUID],
        parent_folder_id: Union[str, UUID],
        file_path: str,
        checksum: str,
        file_date_epoch: int
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Check if a file already exists on the server."""
        return run_sync(self._async_service.check_file(
            package_id, parent_folder_id, file_path, checksum, file_date_epoch
        ))

    # =========================================================================
    # ⚠️ INTERNAL API - Folder Operations
    # =========================================================================

    def create_package_folder(
        self,
        package_id: Union[str, UUID],
        folder_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Create a new folder in a package."""
        return run_sync(self._async_service.create_package_folder(package_id, folder_data))

    def update_package_folder(
        self,
        folder_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Update an existing package folder."""
        return run_sync(self._async_service.update_package_folder(folder_data))

    def delete_package_folder(
        self,
        package_folder_id: Union[str, UUID]
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Delete a package folder."""
        return run_sync(self._async_service.delete_package_folder(package_folder_id))

    def delete_package_folder_files(
        self,
        file_ids: List[Union[str, UUID]]
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Delete multiple files from a package folder."""
        return run_sync(self._async_service.delete_package_folder_files(file_ids))

    # =========================================================================
    # ⚠️ INTERNAL API - Package History & Validation
    # =========================================================================

    def get_package_history(
        self,
        tags: str,
        status: Optional[int] = None,
        all_versions: Optional[bool] = None
    ) -> List[Package]:
        """⚠️ INTERNAL: Get package history by tags."""
        return run_sync(self._async_service.get_package_history(tags, status, all_versions))

    def get_package_download_history(
        self,
        client_id: int
    ) -> List[Dict[str, Any]]:
        """⚠️ INTERNAL: Get package download history for a client."""
        return run_sync(self._async_service.get_package_download_history(client_id))

    def get_revoked_packages(
        self,
        installed_packages: List[Union[str, UUID]],
        include_revoked_only: Optional[bool] = None
    ) -> List[str]:
        """⚠️ INTERNAL: Get list of revoked package IDs from installed packages."""
        return run_sync(self._async_service.get_revoked_packages(
            installed_packages, include_revoked_only
        ))

    def get_available_packages(
        self,
        installed_packages: List[Union[str, UUID]]
    ) -> List[Package]:
        """⚠️ INTERNAL: Check server for new versions of installed packages."""
        return run_sync(self._async_service.get_available_packages(installed_packages))

    def get_software_entity_details(
        self,
        package_id: Union[str, UUID]
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Get detailed information about a software package."""
        return run_sync(self._async_service.get_software_entity_details(package_id))

    # =========================================================================
    # ⚠️ INTERNAL API - Logging
    # =========================================================================

    def log_download(
        self,
        package_id: Union[str, UUID],
        download_size: int
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Log a package download."""
        return run_sync(self._async_service.log_download(package_id, download_size))
