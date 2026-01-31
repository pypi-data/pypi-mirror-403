"""Async Software repository - data access layer.

All async API interactions for software distribution packages.
Includes both public and internal API methods.
Uses Routes class for all endpoint definitions.

⚠️ INTERNAL API methods are marked and may change without notice.
"""
from typing import Optional, List, Union, Dict, Any, TYPE_CHECKING
from uuid import UUID
import logging

from ...core.routes import Routes

if TYPE_CHECKING:
    from ...core.async_client import AsyncHttpClient
    from ...core.exceptions import ErrorHandler

from .models import Package, PackageFile, VirtualFolder
from .enums import PackageStatus

logger = logging.getLogger(__name__)


class AsyncSoftwareRepository:
    """
    Async Software distribution data access layer.

    Handles all async WATS API interactions for software packages.
    Includes both public API methods and internal API methods (marked with ⚠️).
    """

    def __init__(
        self, 
        http_client: "AsyncHttpClient",
        base_url: str = "",
        error_handler: Optional["ErrorHandler"] = None
    ) -> None:
        """
        Initialize with async HTTP client.

        Args:
            http_client: AsyncHttpClient for making async HTTP requests
            base_url: Base URL (needed for internal API Referer header)
            error_handler: ErrorHandler for response handling
        """
        from ...core.exceptions import ErrorHandler, ErrorMode
        self._http_client = http_client
        self._base_url = base_url.rstrip('/') if base_url else ""
        self._error_handler = error_handler or ErrorHandler(ErrorMode.STRICT)

    # =========================================================================
    # Internal API Helpers
    # =========================================================================

    async def _internal_get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        operation: str = "internal_get"
    ) -> Any:
        """
        ⚠️ INTERNAL: Make an internal API GET request with Referer header.
        """
        response = await self._http_client.get(
            endpoint,
            params=params,
            headers={"Referer": self._base_url}
        )
        return self._error_handler.handle_response(
            response, operation=operation, allow_empty=True
        )

    async def _internal_post(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        operation: str = "internal_post"
    ) -> Any:
        """
        ⚠️ INTERNAL: Make an internal API POST request with Referer header.
        """
        response = await self._http_client.post(
            endpoint,
            params=params,
            data=data,
            headers={"Referer": self._base_url}
        )
        return self._error_handler.handle_response(
            response, operation=operation, allow_empty=True
        )

    # =========================================================================
    # Query Packages
    # =========================================================================

    async def get_packages(self) -> List[Package]:
        """
        Get all software packages.

        GET /api/Software/Packages

        Returns:
            List of Package objects
        """
        response = await self._http_client.get(Routes.Software.PACKAGES)
        data = self._error_handler.handle_response(
            response, operation="get_packages", allow_empty=True
        )
        if data and isinstance(data, list):
            return [Package.model_validate(item) for item in data]
        return []

    async def get_package(self, package_id: Union[str, UUID]) -> Optional[Package]:
        """
        Get a specific software package by ID.

        GET /api/Software/Package/{id}

        Args:
            package_id: The package UUID

        Returns:
            Package object or None if not found
        """
        response = await self._http_client.get(Routes.Software.package(str(package_id)))
        data = self._error_handler.handle_response(
            response, operation="get_package", allow_empty=True
        )
        if data:
            return Package.model_validate(data)
        return None

    async def get_package_by_name(
        self,
        name: str,
        status: Optional[Union[PackageStatus, str]] = None,
        version: Optional[int] = None,
    ) -> Optional[Package]:
        """
        Get a software package by name.

        GET /api/Software/PackageByName

        Args:
            name: Package name
            status: Optional status filter
            version: Optional specific version number

        Returns:
            Package object or None if not found
        """
        params: Dict[str, Any] = {"name": name}
        if status:
            params["status"] = status.value if hasattr(status, 'value') else status
        if version is not None:
            params["version"] = version
        response = await self._http_client.get(Routes.Software.PACKAGE_BY_NAME, params=params)
        data = self._error_handler.handle_response(
            response, operation="get_package_by_name", allow_empty=True
        )
        if data:
            return Package.model_validate(data)
        return None

    async def get_packages_by_tag(
        self,
        tag: str,
        value: str,
        status: Optional[Union[PackageStatus, str]] = None,
    ) -> List[Package]:
        """
        Get packages filtered by tag.

        GET /api/Software/PackagesByTag

        Args:
            tag: Tag name to filter by
            value: Tag value to match
            status: Optional status filter

        Returns:
            List of matching Package objects
        """
        params: Dict[str, Any] = {"tag": tag, "value": value}
        if status:
            params["status"] = status.value if hasattr(status, 'value') else status
        response = await self._http_client.get(Routes.Software.PACKAGES_BY_TAG, params=params)
        data = self._error_handler.handle_response(
            response, operation="get_packages_by_tag", allow_empty=True
        )
        if data and isinstance(data, list):
            return [Package.model_validate(item) for item in data]
        return []

    # =========================================================================
    # Create, Update, Delete Packages
    # =========================================================================

    async def create_package(self, package: Package) -> Optional[Package]:
        """
        Create a new package in Draft status.

        POST /api/Software/Package

        Args:
            package: Package object with metadata

        Returns:
            Created Package object or None
        """
        payload = package.model_dump(by_alias=True, exclude_none=True)
        response = await self._http_client.post(Routes.Software.PACKAGE, data=payload)
        data = self._error_handler.handle_response(
            response, operation="create_package", allow_empty=False
        )
        if data:
            return Package.model_validate(data)
        return None

    async def update_package(
        self, package_id: Union[str, UUID], package: Package
    ) -> Optional[Package]:
        """
        Update a software package.

        PUT /api/Software/Package/{id}

        Args:
            package_id: The package UUID
            package: Updated package data

        Returns:
            Updated Package object or None
        """
        payload = package.model_dump(mode="json", by_alias=True, exclude_none=True)
        response = await self._http_client.put(
            Routes.Software.package(str(package_id)), data=payload
        )
        data = self._error_handler.handle_response(
            response, operation="update_package", allow_empty=False
        )
        if data:
            return Package.model_validate(data)
        return None

    async def delete_package(self, package_id: Union[str, UUID]) -> bool:
        """
        Delete a software package by ID.

        DELETE /api/Software/Package/{id}

        Args:
            package_id: The package UUID to delete

        Returns:
            True if successful
        """
        response = await self._http_client.delete(Routes.Software.package(str(package_id)))
        self._error_handler.handle_response(
            response, operation="delete_package", allow_empty=True
        )
        return response.is_success

    async def delete_package_by_name(
        self, name: str, version: Optional[int] = None
    ) -> bool:
        """
        Delete a software package by name.

        DELETE /api/Software/PackageByName

        Args:
            name: Package name
            version: Optional version number

        Returns:
            True if successful
        """
        params: Dict[str, Any] = {"name": name}
        if version is not None:
            params["version"] = version
        response = await self._http_client.delete(
            Routes.Software.PACKAGE_BY_NAME, params=params
        )
        self._error_handler.handle_response(
            response, operation="delete_package_by_name", allow_empty=True
        )
        return response.is_success

    # =========================================================================
    # Package Status
    # =========================================================================

    async def update_package_status(
        self, package_id: Union[str, UUID], status: PackageStatus
    ) -> bool:
        """
        Update the status of a software package.

        POST /api/Software/PackageStatus/{id}

        Args:
            package_id: The package UUID
            status: New status

        Returns:
            True if successful
        """
        response = await self._http_client.post(
            Routes.Software.package_status(str(package_id)),
            params={"status": status.value},
        )
        self._error_handler.handle_response(
            response, operation="update_package_status", allow_empty=True
        )
        return response.is_success

    # =========================================================================
    # Package Files
    # =========================================================================

    async def get_package_files(
        self, package_id: Union[str, UUID]
    ) -> List[PackageFile]:
        """
        Get files associated with a package.

        GET /api/Software/PackageFiles/{id}

        Args:
            package_id: The package UUID

        Returns:
            List of PackageFile objects
        """
        response = await self._http_client.get(Routes.Software.package_files(str(package_id)))
        data = self._error_handler.handle_response(
            response, operation="get_package_files", allow_empty=True
        )
        if data and isinstance(data, list):
            return [PackageFile.model_validate(item) for item in data]
        return []

    async def upload_package_zip(
        self,
        package_id: Union[str, UUID],
        zip_content: bytes,
        clean_install: bool = False,
    ) -> bool:
        """
        Upload a zip file to a software package.

        POST /api/Software/Package/UploadZip/{id}

        Args:
            package_id: The package UUID
            zip_content: Zip file content as bytes
            clean_install: If True, delete existing files first

        Returns:
            True if successful
        """
        params = {"cleanInstall": "true"} if clean_install else {}
        headers = {"Content-Type": "application/zip"}
        response = await self._http_client.post(
            Routes.Software.upload_zip(str(package_id)),
            data=zip_content,
            params=params,
            headers=headers,
        )
        self._error_handler.handle_response(
            response, operation="upload_package_zip", allow_empty=True
        )
        return response.is_success

    async def update_file_attribute(
        self,
        file_id: Union[str, UUID],
        attributes: str,
    ) -> bool:
        """
        Update file attributes for a specific file.

        POST /api/Software/Package/FileAttribute/{id}

        Args:
            file_id: The file ID
            attributes: Attribute data to update

        Returns:
            True if successful
        """
        response = await self._http_client.post(
            Routes.Software.file_attribute(str(file_id)),
            data={"attributes": attributes},
        )
        self._error_handler.handle_response(
            response, operation="update_file_attribute", allow_empty=True
        )
        return response.is_success

    # =========================================================================
    # Virtual Folders
    # =========================================================================

    async def get_virtual_folders(self) -> List[VirtualFolder]:
        """
        Get all virtual folders registered in Production Manager.

        GET /api/Software/VirtualFolders

        Returns:
            List of VirtualFolder objects
        """
        response = await self._http_client.get(Routes.Software.VIRTUAL_FOLDERS)
        data = self._error_handler.handle_response(
            response, operation="get_virtual_folders", allow_empty=True
        )
        if data and isinstance(data, list):
            return [VirtualFolder.model_validate(item) for item in data]
        return []

    # =========================================================================
    # ⚠️ INTERNAL API - Connection Check
    # =========================================================================

    async def is_connected(self) -> bool:
        """
        ⚠️ INTERNAL: Check if Software module is connected.
        
        GET /api/internal/Software/isConnected
        
        Returns:
            True if connected
        """
        result = await self._internal_get(
            Routes.Software.Internal.IS_CONNECTED,
            operation="is_connected"
        )
        return result is not None

    # =========================================================================
    # ⚠️ INTERNAL API - File Operations
    # =========================================================================

    async def get_file(self, file_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get file metadata by ID.
        
        GET /api/internal/Software/File/{id}
        
        Args:
            file_id: File UUID
            
        Returns:
            File metadata dictionary or None
        """
        return await self._internal_get(
            Routes.Software.Internal.file(str(file_id)),
            operation="get_file"
        )

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
        
        GET /api/internal/Software/CheckFile
        
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
        params = {
            "packageId": str(package_id),
            "parentFolderId": str(parent_folder_id),
            "filePath": file_path,
            "checksum": checksum,
            "fileDateEpoch": file_date_epoch
        }
        return await self._internal_get(
            Routes.Software.Internal.CHECK_FILE, 
            params,
            operation="check_file"
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
        
        POST /api/internal/Software/PostPackageFolder
        
        Args:
            package_id: Package UUID
            folder_data: Folder definition (SoftwareEntity)
            
        Returns:
            Created folder data or None
        """
        return await self._internal_post(
            Routes.Software.Internal.POST_FOLDER,
            params={"packageId": str(package_id)},
            data=folder_data,
            operation="create_package_folder"
        )

    async def update_package_folder(
        self,
        folder_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Update an existing package folder.
        
        POST /api/internal/Software/UpdatePackageFolder
        
        Args:
            folder_data: Updated folder definition (SoftwareEntity)
            
        Returns:
            Updated folder data or None
        """
        return await self._internal_post(
            Routes.Software.Internal.UPDATE_FOLDER,
            data=folder_data,
            operation="update_package_folder"
        )

    async def delete_package_folder(
        self,
        package_folder_id: Union[str, UUID]
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Delete a package folder.
        
        POST /api/internal/Software/DeletePackageFolder
        
        Args:
            package_folder_id: Folder UUID to delete
            
        Returns:
            Result or None
        """
        return await self._internal_post(
            Routes.Software.Internal.DELETE_FOLDER,
            params={"packageFolderId": str(package_folder_id)},
            operation="delete_package_folder"
        )

    async def delete_package_folder_files(
        self,
        file_ids: List[Union[str, UUID]]
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Delete multiple files from a package folder.
        
        POST /api/internal/Software/DeletePackageFolderFiles
        
        Args:
            file_ids: List of file UUIDs to delete
            
        Returns:
            Result or None
        """
        ids_str = ",".join(str(fid) for fid in file_ids)
        return await self._internal_post(
            Routes.Software.Internal.DELETE_FOLDER_FILES,
            params={"packageFolderFileIds": ids_str},
            operation="delete_package_folder_files"
        )

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
        
        GET /api/internal/Software/GetPackageHistory
        
        Args:
            tags: Tags to filter by (comma-separated)
            status: Optional status filter (0=Draft, 1=Pending, 2=Released, 3=Revoked)
            all_versions: Whether to include all versions
            
        Returns:
            List of Package objects
        """
        params: Dict[str, Any] = {"tags": tags}
        if status is not None:
            params["status"] = status
        if all_versions is not None:
            params["allVersions"] = all_versions
        data = await self._internal_get(
            Routes.Software.Internal.GET_HISTORY, 
            params,
            operation="get_package_history"
        )
        if data and isinstance(data, list):
            return [Package.model_validate(item) for item in data]
        return []

    async def get_package_download_history(
        self,
        client_id: int
    ) -> List[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get package download history for a client.
        
        GET /api/internal/Software/GetPackageDownloadHistory
        
        Args:
            client_id: Client identifier
            
        Returns:
            List of download records
        """
        params = {"clientId": client_id}
        data = await self._internal_get(
            Routes.Software.Internal.GET_DOWNLOAD_HISTORY, 
            params,
            operation="get_package_download_history"
        )
        if data and isinstance(data, list):
            return data
        return []

    async def get_revoked_packages(
        self,
        installed_packages: List[Union[str, UUID]],
        include_revoked_only: Optional[bool] = None
    ) -> List[str]:
        """
        ⚠️ INTERNAL: Get list of revoked package IDs from installed packages.
        
        GET /api/internal/Software/GetRevokedPackages
        
        Args:
            installed_packages: List of installed package UUIDs
            include_revoked_only: Only return revoked without newer released version
            
        Returns:
            List of revoked package UUIDs (as strings)
        """
        params: Dict[str, Any] = {
            "installedPackages": ",".join(str(p) for p in installed_packages)
        }
        if include_revoked_only is not None:
            params["includeRevokedOnly"] = include_revoked_only
        data = await self._internal_get(
            Routes.Software.Internal.GET_REVOKED, 
            params,
            operation="get_revoked_packages"
        )
        if data and isinstance(data, list):
            return data
        return []

    async def get_available_packages(
        self,
        installed_packages: List[Union[str, UUID]]
    ) -> List[Package]:
        """
        ⚠️ INTERNAL: Check server for new versions of installed packages.
        
        GET /api/internal/Software/GetAvailablePackages
        
        Args:
            installed_packages: List of installed package UUIDs
            
        Returns:
            List of Package objects with newer versions available
        """
        params = {
            "installedPackages": ",".join(str(p) for p in installed_packages)
        }
        data = await self._internal_get(
            Routes.Software.Internal.GET_AVAILABLE, 
            params,
            operation="get_available_packages"
        )
        if data and isinstance(data, list):
            return [Package.model_validate(item) for item in data]
        return []

    async def get_software_entity_details(
        self,
        package_id: Union[str, UUID]
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get detailed information about a software package.
        
        GET /api/internal/Software/GetSoftwareEntityDetails
        
        Args:
            package_id: Package UUID
            
        Returns:
            Detailed entity data or None
        """
        params = {"packageId": str(package_id)}
        return await self._internal_get(
            Routes.Software.Internal.GET_DETAILS, 
            params,
            operation="get_software_entity_details"
        )

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
        
        GET /api/internal/Software/Log
        
        Args:
            package_id: Package UUID that was downloaded
            download_size: Size of downloaded data in bytes
            
        Returns:
            Log result or None
        """
        params = {
            "packageId": str(package_id),
            "downloadSize": download_size
        }
        return await self._internal_get(
            Routes.Software.Internal.LOG, 
            params,
            operation="log_download"
        )
