"""Async Software service - business logic layer.

All async business operations for software distribution packages.
Includes both public and internal API methods.

⚠️ INTERNAL API methods are marked and may change without notice.
"""
from typing import Optional, List, Union, Dict, Any
from uuid import UUID
import logging

from .async_repository import AsyncSoftwareRepository
from .models import Package, PackageFile, PackageTag, VirtualFolder
from .enums import PackageStatus

logger = logging.getLogger(__name__)


class AsyncSoftwareService:
    """
    Async Software distribution business logic layer.

    Provides high-level async operations for managing software packages.
    """

    def __init__(self, repository: AsyncSoftwareRepository):
        """
        Initialize with AsyncSoftwareRepository.

        Args:
            repository: AsyncSoftwareRepository instance for data access
        """
        self._repository = repository

    # =========================================================================
    # Query Packages
    # =========================================================================

    async def get_packages(self) -> List[Package]:
        """
        Get all available software packages.

        Returns:
            List of Package objects
        """
        return await self._repository.get_packages()

    async def get_package(self, package_id: Union[str, UUID]) -> Optional[Package]:
        """
        Get a specific software package by ID.

        Args:
            package_id: Package UUID

        Returns:
            Package object or None if not found
        """
        if not package_id:
            raise ValueError("package_id is required")
        return await self._repository.get_package(package_id)

    async def get_package_by_name(
        self,
        name: str,
        status: Optional[PackageStatus] = None,
        version: Optional[int] = None,
    ) -> Optional[Package]:
        """
        Get a software package by name.

        Args:
            name: Package name
            status: Optional status filter
            version: Optional specific version number

        Returns:
            Package object or None if not found
        """
        if not name or not name.strip():
            raise ValueError("name is required")
        return await self._repository.get_package_by_name(name, status, version)

    async def get_released_package(self, name: str) -> Optional[Package]:
        """
        Get the released version of a package.

        Args:
            name: Package name

        Returns:
            Released Package object or None
        """
        if not name or not name.strip():
            raise ValueError("name is required")
        return await self._repository.get_package_by_name(
            name, status=PackageStatus.RELEASED
        )

    async def get_packages_by_tag(
        self,
        tag: str,
        value: str,
        status: Optional[PackageStatus] = None,
    ) -> List[Package]:
        """
        Get packages filtered by tag.

        Args:
            tag: Tag name to filter by
            value: Tag value to match
            status: Optional status filter

        Returns:
            List of matching Package objects
        """
        if not tag or not tag.strip():
            raise ValueError("tag is required")
        if not value or not value.strip():
            raise ValueError("value is required")
        return await self._repository.get_packages_by_tag(tag, value, status)

    # =========================================================================
    # Create, Update, Delete Packages
    # =========================================================================

    async def create_package(
        self,
        name: str,
        description: Optional[str] = None,
        install_on_root: bool = False,
        root_directory: Optional[str] = None,
        priority: Optional[int] = None,
        tags: Optional[List[PackageTag]] = None,
    ) -> Optional[Package]:
        """
        Create a new package in Draft status.

        Args:
            name: Package name (required)
            description: Package description
            install_on_root: Whether to install on root
            root_directory: Root directory path
            priority: Installation priority
            tags: List of PackageTag objects

        Returns:
            Created Package object or None
        """
        if not name or not name.strip():
            raise ValueError("name is required")
        package = Package(
            name=name,
            description=description,
            install_on_root=install_on_root,
            root_directory=root_directory,
            priority=priority,
            tags=tags,
        )
        result = await self._repository.create_package(package)
        if result:
            logger.info(f"PACKAGE_CREATED: {result.name} (id={result.package_id}, version={result.version})")
        return result

    async def update_package(self, package: Package) -> Optional[Package]:
        """
        Update a software package.

        Args:
            package: Package object with updated data

        Returns:
            Updated Package object or None
        """
        if not package.package_id:
            return None
        result = await self._repository.update_package(package.package_id, package)
        if result:
            logger.info(f"PACKAGE_UPDATED: {result.name} (id={result.package_id})")
        return result

    async def delete_package(self, package_id: Union[str, UUID]) -> bool:
        """
        Delete a software package by ID.

        Args:
            package_id: Package UUID to delete

        Returns:
            True if deleted successfully
        """
        if not package_id:
            raise ValueError("package_id is required")
        result = await self._repository.delete_package(package_id)
        if result:
            logger.info(f"PACKAGE_DELETED: id={package_id}")
        return result

    async def delete_package_by_name(
        self, name: str, version: Optional[int] = None
    ) -> bool:
        """
        Delete a software package by name.

        Args:
            name: Package name
            version: Optional version number

        Returns:
            True if deleted successfully
        """
        if not name or not name.strip():
            raise ValueError("name is required")
        result = await self._repository.delete_package_by_name(name, version)
        if result:
            logger.info(f"PACKAGE_DELETED: {name} (version={version})")
        return result

    # =========================================================================
    # Package Status Workflow
    # =========================================================================

    async def submit_for_review(self, package_id: Union[str, UUID]) -> bool:
        """
        Submit a draft package for review (Draft -> Pending).

        Args:
            package_id: Package UUID

        Returns:
            True if successful
        """
        if not package_id:
            raise ValueError("package_id is required")
        result = await self._repository.update_package_status(
            package_id, PackageStatus.PENDING
        )
        if result:
            logger.info(f"PACKAGE_SUBMITTED_FOR_REVIEW: id={package_id} (status=PENDING)")
        return result

    async def return_to_draft(self, package_id: Union[str, UUID]) -> bool:
        """
        Return a pending package to draft (Pending -> Draft).

        Args:
            package_id: Package UUID

        Returns:
            True if successful
        """
        if not package_id:
            raise ValueError("package_id is required")
        result = await self._repository.update_package_status(
            package_id, PackageStatus.DRAFT
        )
        if result:
            logger.info(f"PACKAGE_RETURNED_TO_DRAFT: id={package_id} (status=DRAFT)")
        return result

    async def release_package(self, package_id: Union[str, UUID]) -> bool:
        """
        Release a pending package (Pending -> Released).

        Args:
            package_id: Package UUID

        Returns:
            True if successful
        """
        if not package_id:
            raise ValueError("package_id is required")
        result = await self._repository.update_package_status(
            package_id, PackageStatus.RELEASED
        )
        if result:
            logger.info(f"PACKAGE_RELEASED: id={package_id} (status=RELEASED)")
        return result

    async def revoke_package(self, package_id: Union[str, UUID]) -> bool:
        """
        Revoke a released package (Released -> Revoked).

        Args:
            package_id: Package UUID

        Returns:
            True if successful
        """
        if not package_id:
            raise ValueError("package_id is required")
        result = await self._repository.update_package_status(
            package_id, PackageStatus.REVOKED
        )
        if result:
            logger.info(f"PACKAGE_REVOKED: id={package_id} (status=REVOKED)")
        return result

    # =========================================================================
    # Package Files
    # =========================================================================

    async def get_package_files(
        self, package_id: Union[str, UUID]
    ) -> List[PackageFile]:
        """
        Get files associated with a package.

        Args:
            package_id: Package UUID

        Returns:
            List of PackageFile objects
        """
        if not package_id:
            raise ValueError("package_id is required")
        return await self._repository.get_package_files(package_id)

    async def upload_zip(
        self,
        package_id: Union[str, UUID],
        zip_content: bytes,
        clean_install: bool = False,
    ) -> bool:
        """
        Upload a zip file to a software package.

        Args:
            package_id: Package UUID
            zip_content: Zip file content as bytes
            clean_install: If True, delete existing files first

        Returns:
            True if upload successful
        """
        if not package_id:
            raise ValueError("package_id is required")
        if not zip_content:
            raise ValueError("zip_content is required")
        result = await self._repository.upload_package_zip(
            package_id, zip_content, clean_install
        )
        if result:
            logger.info(f"PACKAGE_ZIP_UPLOADED: id={package_id} (size={len(zip_content)}, clean_install={clean_install})")
        return result

    async def update_file_attribute(
        self, file_id: Union[str, UUID], attributes: str
    ) -> bool:
        """
        Update file attributes for a specific file.

        Args:
            file_id: The file ID (from get_package_files)
            attributes: Attribute data to update

        Returns:
            True if update successful
        """
        if not file_id:
            raise ValueError("file_id is required")
        if not attributes or not attributes.strip():
            raise ValueError("attributes is required")
        return await self._repository.update_file_attribute(file_id, attributes)

    # =========================================================================
    # Virtual Folders
    # =========================================================================

    async def get_virtual_folders(self) -> List[VirtualFolder]:
        """
        Get all virtual folders registered in Production Manager.

        Returns:
            List of VirtualFolder objects
        """
        return await self._repository.get_virtual_folders()

    # =========================================================================
    # ⚠️ INTERNAL API - Connection Check
    # =========================================================================

    async def is_connected(self) -> bool:
        """
        ⚠️ INTERNAL: Check if Software module is connected.
        
        Returns:
            True if connected
        """
        return await self._repository.is_connected()

    # =========================================================================
    # ⚠️ INTERNAL API - File Operations
    # =========================================================================

    async def get_file(self, file_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get file metadata by ID.
        
        Args:
            file_id: File UUID
            
        Returns:
            File metadata dictionary or None
        """
        return await self._repository.get_file(file_id)

    async def check_file(
        self,
        package_id: Union[str, UUID],
        parent_folder_id: Union[str, UUID],
        file_path: str,
        checksum: str,
        file_date_epoch: int
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Check if a file already exists on the server.
        
        Used before uploading to avoid duplicate uploads.
        
        Args:
            package_id: Package UUID
            parent_folder_id: Parent folder UUID
            file_path: File path within package
            checksum: MD5 or SHA1 checksum
            file_date_epoch: File date as Unix epoch
            
        Returns:
            Check result dictionary or None
        """
        return await self._repository.check_file(
            package_id, parent_folder_id, file_path, checksum, file_date_epoch
        )

    # =========================================================================
    # ⚠️ INTERNAL API - Folder Operations
    # =========================================================================

    async def create_package_folder(
        self,
        package_id: Union[str, UUID],
        folder_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Create a new folder in a package.
        
        Args:
            package_id: Package UUID
            folder_data: Folder definition (SoftwareEntity)
            
        Returns:
            Created folder data or None
        """
        return await self._repository.create_package_folder(package_id, folder_data)

    async def update_package_folder(
        self,
        folder_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Update an existing package folder.
        
        Args:
            folder_data: Updated folder definition (SoftwareEntity)
            
        Returns:
            Updated folder data or None
        """
        return await self._repository.update_package_folder(folder_data)

    async def delete_package_folder(
        self,
        package_folder_id: Union[str, UUID]
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Delete a package folder.
        
        Args:
            package_folder_id: Folder UUID to delete
            
        Returns:
            Result or None
        """
        return await self._repository.delete_package_folder(package_folder_id)

    async def delete_package_folder_files(
        self,
        file_ids: List[Union[str, UUID]]
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Delete multiple files from a package folder.
        
        Args:
            file_ids: List of file UUIDs to delete
            
        Returns:
            Result or None
        """
        return await self._repository.delete_package_folder_files(file_ids)

    # =========================================================================
    # ⚠️ INTERNAL API - Package History & Validation
    # =========================================================================

    async def get_package_history(
        self,
        tags: str,
        status: Optional[int] = None,
        all_versions: Optional[bool] = None
    ) -> List[Package]:
        """
        ⚠️ INTERNAL: Get package history by tags.
        
        Args:
            tags: Tags to filter by (comma-separated)
            status: Optional status filter (0=Draft, 1=Pending, 2=Released, 3=Revoked)
            all_versions: Whether to include all versions
            
        Returns:
            List of Package objects
        """
        return await self._repository.get_package_history(tags, status, all_versions)

    async def get_package_download_history(
        self,
        client_id: int
    ) -> List[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get package download history for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            List of download records
        """
        return await self._repository.get_package_download_history(client_id)

    async def get_revoked_packages(
        self,
        installed_packages: List[Union[str, UUID]],
        include_revoked_only: Optional[bool] = None
    ) -> List[str]:
        """
        ⚠️ INTERNAL: Get list of revoked package IDs from installed packages.
        
        Args:
            installed_packages: List of installed package UUIDs
            include_revoked_only: Only return revoked without newer released version
            
        Returns:
            List of revoked package UUIDs (as strings)
        """
        return await self._repository.get_revoked_packages(
            installed_packages, include_revoked_only
        )

    async def get_available_packages(
        self,
        installed_packages: List[Union[str, UUID]]
    ) -> List[Package]:
        """
        ⚠️ INTERNAL: Check server for new versions of installed packages.
        
        Args:
            installed_packages: List of installed package UUIDs
            
        Returns:
            List of Package objects with newer versions available
        """
        return await self._repository.get_available_packages(installed_packages)

    async def get_software_entity_details(
        self,
        package_id: Union[str, UUID]
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get detailed information about a software package.
        
        Args:
            package_id: Package UUID
            
        Returns:
            Detailed entity data or None
        """
        return await self._repository.get_software_entity_details(package_id)

    # =========================================================================
    # ⚠️ INTERNAL API - Logging
    # =========================================================================

    async def log_download(
        self,
        package_id: Union[str, UUID],
        download_size: int
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Log a package download.
        
        Args:
            package_id: Package UUID that was downloaded
            download_size: Size of downloaded data in bytes
            
        Returns:
            Log result or None
        """
        return await self._repository.log_download(package_id, download_size)
