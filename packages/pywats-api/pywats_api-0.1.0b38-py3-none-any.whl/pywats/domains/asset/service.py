"""Asset service - thin sync wrapper around AsyncAssetService.

This module provides synchronous access to AsyncAssetService methods.
All business logic is maintained in async_service.py (source of truth).
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID

from .async_service import AsyncAssetService
from .async_repository import AsyncAssetRepository
from .models import Asset, AssetType, AssetLog
from .enums import AssetState
from ...core.sync_runner import run_sync


class AssetService:
    """
    Synchronous wrapper for AsyncAssetService.

    Provides sync access to all async asset service operations.
    All business logic is in AsyncAssetService.
    """

    def __init__(self, async_service: AsyncAssetService = None, *, repository=None) -> None:
        """
        Initialize with AsyncAssetService or repository.

        Args:
            async_service: AsyncAssetService instance to wrap
            repository: (Deprecated) Repository instance for backward compatibility
        """
        if repository is not None:
            # Backward compatibility: create async service from repository
            self._async_service = AsyncAssetService(repository)
            self._repository = repository
        elif async_service is not None:
            self._async_service = async_service
            self._repository = async_service._repository
        else:
            raise ValueError("Either async_service or repository must be provided")

    @classmethod
    def from_repository(cls, repository: AsyncAssetRepository) -> "AssetService":
        """Create AssetService from an AsyncAssetRepository."""
        async_service = AsyncAssetService(repository)
        return cls(async_service)

    # =========================================================================
    # Asset Operations
    # =========================================================================

    def get_assets(
        self,
        filter_str: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List[Asset]:
        """Get all assets with optional filtering.
        
        Args:
            filter_str: OData filter string
            orderby: OData orderby string
            top: Maximum number of results to return
            skip: Number of results to skip
            
        Returns:
            List of Asset objects matching the filter
            
        Raises:
            AuthenticationError: If API authentication fails
            ValidationError: If filter or orderby syntax is invalid
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_assets(filter_str, orderby, top, skip))

    def get_asset(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None
    ) -> Optional[Asset]:
        """Get an asset by ID or serial number.
        
        Args:
            asset_id: The unique asset identifier
            serial_number: The asset serial number
            
        Returns:
            Asset if found, None otherwise
            
        Raises:
            ValidationError: If neither asset_id nor serial_number is provided
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_asset(asset_id, serial_number))

    def get_asset_by_serial(self, serial_number: str) -> Optional[Asset]:
        """Get an asset by its serial number.
        
        Args:
            serial_number: The asset serial number
            
        Returns:
            Asset if found, None otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_asset_by_serial(serial_number))

    def create_asset(
        self,
        serial_number: str,
        type_id: UUID,
        asset_name: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        parent_asset_id: Optional[str] = None,
        parent_serial_number: Optional[str] = None,
        *,
        part_number: Optional[str] = None,
        revision: Optional[str] = None,
        state: AssetState = AssetState.OK,
        client_id: Optional[int] = None,
        first_seen_date: Optional[datetime] = None,
        last_seen_date: Optional[datetime] = None,
        last_maintenance_date: Optional[datetime] = None,
        next_maintenance_date: Optional[datetime] = None,
        last_calibration_date: Optional[datetime] = None,
        next_calibration_date: Optional[datetime] = None,
        total_count: Optional[int] = None,
        running_count: Optional[int] = None,
    ) -> Optional[Asset]:
        """Create a new asset."""
        return run_sync(self._async_service.create_asset(
            serial_number=serial_number,
            type_id=type_id,
            asset_name=asset_name,
            description=description,
            location=location,
            parent_asset_id=parent_asset_id,
            parent_serial_number=parent_serial_number,
            part_number=part_number,
            revision=revision,
            state=state,
            client_id=client_id,
            first_seen_date=first_seen_date,
            last_seen_date=last_seen_date,
            last_maintenance_date=last_maintenance_date,
            next_maintenance_date=next_maintenance_date,
            last_calibration_date=last_calibration_date,
            next_calibration_date=next_calibration_date,
            total_count=total_count,
            running_count=running_count,
        ))

    def update_asset(self, asset: Asset) -> Optional[Asset]:
        """Update an existing asset."""
        return run_sync(self._async_service.update_asset(asset))

    def delete_asset(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None
    ) -> bool:
        """Delete an asset."""
        return run_sync(self._async_service.delete_asset(asset_id, serial_number))

    # =========================================================================
    # Asset Status and State
    # =========================================================================

    def get_status(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get the current status of an asset."""
        return run_sync(self._async_service.get_status(asset_id, serial_number))

    def get_asset_state(self, asset_id: str) -> Optional[AssetState]:
        """Get the current state of an asset."""
        return run_sync(self._async_service.get_asset_state(asset_id))

    def set_asset_state(
        self,
        state: Union[AssetState, int],
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None
    ) -> bool:
        """Set the state of an asset."""
        return run_sync(self._async_service.set_asset_state(state, asset_id, serial_number))

    def is_in_alarm(self, asset: Asset) -> bool:
        """Check if an asset is in alarm state."""
        return self._async_service.is_in_alarm(asset)  # Sync method, no await

    def is_in_warning(self, asset: Asset) -> bool:
        """Check if an asset is in warning state."""
        return self._async_service.is_in_warning(asset)  # Sync method, no await

    def get_assets_in_alarm(self, top: Optional[int] = None) -> List[Asset]:
        """Get all assets currently in alarm state."""
        return run_sync(self._async_service.get_assets_in_alarm(top))

    def get_assets_in_warning(self, top: Optional[int] = None) -> List[Asset]:
        """Get all assets currently in warning state."""
        return run_sync(self._async_service.get_assets_in_warning(top))

    def get_assets_by_alarm_state(
        self,
        state: Union[AssetState, int],
        top: Optional[int] = None
    ) -> List[Asset]:
        """Get assets by their alarm state."""
        return run_sync(self._async_service.get_assets_by_alarm_state(state, top))

    # =========================================================================
    # Asset Count Operations
    # =========================================================================

    def increment_count(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        amount: int = 1,
        increment_children: bool = False
    ) -> bool:
        """Increment the usage count of an asset."""
        return run_sync(self._async_service.increment_count(
            asset_id, serial_number, amount, increment_children
        ))

    def reset_running_count(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        comment: Optional[str] = None
    ) -> bool:
        """Reset the running count to 0."""
        return run_sync(self._async_service.reset_running_count(asset_id, serial_number, comment))

    # =========================================================================
    # Calibration and Maintenance
    # =========================================================================

    def record_calibration(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        date_time: Optional[datetime] = None,
        comment: Optional[str] = None
    ) -> bool:
        """Record that an asset has been calibrated."""
        return run_sync(self._async_service.record_calibration(
            asset_id, serial_number, date_time, comment
        ))

    def record_maintenance(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        date_time: Optional[datetime] = None,
        comment: Optional[str] = None
    ) -> bool:
        """Record that an asset has had maintenance."""
        return run_sync(self._async_service.record_maintenance(
            asset_id, serial_number, date_time, comment
        ))

    # =========================================================================
    # Asset Log
    # =========================================================================

    def get_asset_log(
        self,
        filter_str: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None
    ) -> List[AssetLog]:
        """Get asset log records."""
        return run_sync(self._async_service.get_asset_log(filter_str, orderby, top))

    def add_log_message(
        self,
        asset_id: str,
        message: str,
        user: Optional[str] = None
    ) -> bool:
        """Post a message to the asset log."""
        return run_sync(self._async_service.add_log_message(asset_id, message, user))

    # =========================================================================
    # Asset Types
    # =========================================================================

    def get_asset_types(self) -> List[AssetType]:
        """Get all asset types."""
        return run_sync(self._async_service.get_asset_types())

    def create_asset_type(
        self,
        type_name: str,
        running_count_limit: Optional[int] = None,
        total_count_limit: Optional[int] = None,
        calibration_interval: Optional[float] = None,
        maintenance_interval: Optional[float] = None,
        warning_threshold: Optional[float] = None,
        alarm_threshold: Optional[float] = None,
        *,
        icon: Optional[str] = None,
    ) -> Optional[AssetType]:
        """Create a new asset type."""
        return run_sync(self._async_service.create_asset_type(
            type_name=type_name,
            running_count_limit=running_count_limit,
            total_count_limit=total_count_limit,
            calibration_interval=calibration_interval,
            maintenance_interval=maintenance_interval,
            warning_threshold=warning_threshold,
            alarm_threshold=alarm_threshold,
            icon=icon,
        ))

    # =========================================================================
    # Sub-Assets
    # =========================================================================

    def get_child_assets(
        self,
        parent_id: Optional[str] = None,
        parent_serial: Optional[str] = None,
        level: Optional[int] = None
    ) -> List[Asset]:
        """Get child assets of a parent asset."""
        return run_sync(self._async_service.get_child_assets(parent_id, parent_serial, level))

    def add_child_asset(self, parent_id: str, child_id: str) -> bool:
        """Add a child asset to a parent asset."""
        return run_sync(self._async_service.add_child_asset(parent_id, child_id))

    # =========================================================================
    # ⚠️ INTERNAL API - File Operations
    # =========================================================================

    def upload_file(self, asset_id: str, filename: str, content: bytes) -> bool:
        """⚠️ INTERNAL: Upload a file to an asset."""
        return run_sync(self._async_service.upload_file(asset_id, filename, content))

    def download_file(self, asset_id: str, filename: str) -> Optional[bytes]:
        """⚠️ INTERNAL: Download a file from an asset."""
        return run_sync(self._async_service.download_file(asset_id, filename))

    def list_files(self, asset_id: str) -> List[str]:
        """⚠️ INTERNAL: List all files attached to an asset."""
        return run_sync(self._async_service.list_files(asset_id))

    def delete_files(self, asset_id: str, filenames: List[str]) -> bool:
        """⚠️ INTERNAL: Delete files from an asset."""
        return run_sync(self._async_service.delete_files(asset_id, filenames))
