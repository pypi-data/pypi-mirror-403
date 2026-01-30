"""Async Asset service - business logic layer.

Async version of the asset service for non-blocking operations.
Includes both public and internal API methods.

⚠️ INTERNAL API methods are marked and may change without notice.
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
import logging

from .models import Asset, AssetType, AssetLog
from .enums import AssetState
from .async_repository import AsyncAssetRepository

logger = logging.getLogger(__name__)


class AsyncAssetService:
    """
    Async Asset business logic.

    Provides high-level async operations for managing assets, types, and files.
    Includes both public and internal API methods (marked with ⚠️).
    """

    def __init__(
        self, 
        repository: AsyncAssetRepository,
        base_url: str = ""
    ) -> None:
        """
        Initialize with async repository.

        Args:
            repository: AsyncAssetRepository for data access
            base_url: Base URL for internal API calls
        """
        self._repository = repository
        self._base_url = base_url.rstrip("/") if base_url else ""

    # =========================================================================
    # Asset Operations
    # =========================================================================

    async def get_assets(
        self,
        filter_str: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List[Asset]:
        """
        Get all assets with optional filtering.

        Args:
            filter_str: OData filter string
            orderby: OData order by string
            top: Maximum number to return
            skip: Number to skip (pagination)

        Returns:
            List of Asset objects
        """
        return await self._repository.get_all(filter_str, orderby, top, skip)

    async def get_asset(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None
    ) -> Optional[Asset]:
        """
        Get an asset by ID or serial number.

        Args:
            asset_id: Asset ID (GUID)
            serial_number: Asset serial number

        Returns:
            Asset if found, None otherwise
        """
        if not asset_id and not serial_number:
            raise ValueError("Either asset_id or serial_number is required")
        
        if asset_id:
            return await self._repository.get_by_id(asset_id)
        return await self._repository.get_by_serial_number(serial_number)

    async def get_asset_by_serial(self, serial_number: str) -> Optional[Asset]:
        """
        Get an asset by its serial number.

        Args:
            serial_number: Asset serial number

        Returns:
            Asset if found, None otherwise
        """
        if not serial_number or not serial_number.strip():
            raise ValueError("serial_number is required")
        return await self._repository.get_by_serial_number(serial_number)

    async def create_asset(
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
        """
        Create a new asset.

        Args:
            serial_number: Unique serial number (required)
            type_id: Asset type UUID (required)
            asset_name: Optional display name
            description: Optional description text
            location: Optional physical location
            parent_asset_id: Parent asset ID for hierarchical assets
            parent_serial_number: Parent asset serial number for hierarchy
            part_number: Asset part number
            revision: Asset revision string
            state: Asset state (default: AssetState.OK)
            client_id: Client identifier
            first_seen_date: Date asset was first seen
            last_seen_date: Date asset was last seen
            last_maintenance_date: Date of last maintenance
            next_maintenance_date: Date of next scheduled maintenance
            last_calibration_date: Date of last calibration
            next_calibration_date: Date of next scheduled calibration
            total_count: Total usage count
            running_count: Running count since last calibration

        Returns:
            Created Asset object, or None on failure
        """
        if not serial_number or not serial_number.strip():
            raise ValueError("serial_number is required")
        if not type_id:
            raise ValueError("type_id is required")
        
        asset = Asset(
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
        )
        result = await self._repository.save(asset)
        if result:
            logger.info(f"ASSET_CREATED: {result.serial_number} (type_id={type_id}, name={asset_name})")
        return result

    async def update_asset(self, asset: Asset) -> Optional[Asset]:
        """
        Update an existing asset.

        Args:
            asset: Asset object with updated fields

        Returns:
            Updated Asset object
        """
        result = await self._repository.save(asset)
        if result:
            logger.info(f"ASSET_UPDATED: {result.serial_number}")
        return result

    async def delete_asset(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None
    ) -> bool:
        """
        Delete an asset.

        Args:
            asset_id: Asset ID
            serial_number: Asset serial number (alternative)

        Returns:
            True if deleted successfully
        """
        if not asset_id and not serial_number:
            raise ValueError("Either asset_id or serial_number is required")
        
        result = await self._repository.delete(asset_id, serial_number)
        if result:
            logger.info(f"ASSET_DELETED: {asset_id or serial_number}")
        return result

    # =========================================================================
    # Asset Status and State
    # =========================================================================

    async def get_status(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the current status of an asset.

        Args:
            asset_id: Asset ID
            serial_number: Asset serial number (alternative)

        Returns:
            Status dictionary or None
        """
        return await self._repository.get_status(asset_id, serial_number)

    async def get_asset_state(self, asset_id: str) -> Optional[AssetState]:
        """
        Get the current state of an asset.

        Args:
            asset_id: Asset ID

        Returns:
            Current AssetState or None if not found
        """
        asset = await self._repository.get_by_id(asset_id)
        return asset.state if asset else None

    async def set_asset_state(
        self,
        state: Union[AssetState, int],
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None
    ) -> bool:
        """
        Set the state of an asset.

        Args:
            state: New state (AssetState enum or int)
            asset_id: Asset ID
            serial_number: Asset serial number (alternative to asset_id)

        Returns:
            True if successful

        Example:
            >>> await api.asset.set_asset_state(
            ...     state=AssetState.IN_MAINTENANCE,
            ...     serial_number="ASSET-001"
            ... )
        """
        return await self._repository.set_state(state, asset_id, serial_number)

    def is_in_alarm(self, asset: Asset) -> bool:
        """
        Check if an asset is in alarm state.

        Args:
            asset: Asset object to check

        Returns:
            True if asset is in alarm state
        """
        return asset.state == AssetState.IN_ALARM

    def is_in_warning(self, asset: Asset) -> bool:
        """
        Check if an asset is in warning state.

        Args:
            asset: Asset object to check

        Returns:
            True if asset is in warning state
        """
        return asset.state == AssetState.IN_WARNING

    async def get_assets_in_alarm(
        self,
        top: Optional[int] = None
    ) -> List[Asset]:
        """
        Get all assets currently in alarm state.

        Args:
            top: Maximum number to return

        Returns:
            List of assets in alarm state
        """
        return await self.get_assets_by_alarm_state(AssetState.IN_ALARM, top)

    async def get_assets_in_warning(
        self,
        top: Optional[int] = None
    ) -> List[Asset]:
        """
        Get all assets currently in warning state.

        Args:
            top: Maximum number to return

        Returns:
            List of assets in warning state
        """
        return await self.get_assets_by_alarm_state(AssetState.IN_WARNING, top)

    async def get_assets_by_alarm_state(
        self,
        state: Union[AssetState, int],
        top: Optional[int] = None
    ) -> List[Asset]:
        """
        Get assets by their alarm state.

        Args:
            state: State to filter by
            top: Maximum number to return

        Returns:
            List of assets in the specified state
        """
        state_value = state.value if isinstance(state, AssetState) else state
        filter_str = f"state eq {state_value}"
        return await self.get_assets(filter_str=filter_str, top=top)

    # =========================================================================
    # Asset Count Operations
    # =========================================================================

    async def increment_count(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        amount: int = 1,
        increment_children: bool = False
    ) -> bool:
        """
        Increment the usage count of an asset.

        Args:
            asset_id: Asset ID
            serial_number: Asset serial number
            amount: Amount to increment by (default 1)
            increment_children: Also increment child asset counts

        Returns:
            True if successful
        """
        return await self._repository.update_count(
            asset_id=asset_id,
            serial_number=serial_number,
            increment_by=amount,
            increment_children=increment_children
        )

    async def reset_running_count(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Reset the running count to 0.

        Args:
            asset_id: Asset ID
            serial_number: Asset serial number (alternative)
            comment: Log message

        Returns:
            True if successful
        """
        return await self._repository.reset_running_count(asset_id, serial_number, comment)

    # =========================================================================
    # Calibration and Maintenance
    # =========================================================================

    async def record_calibration(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        date_time: Optional[datetime] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Record that an asset has been calibrated.

        Args:
            asset_id: Asset ID
            serial_number: Asset serial number (alternative)
            date_time: Calibration date (default: now)
            comment: Log message

        Returns:
            True if successful
        """
        return await self._repository.post_calibration(
            asset_id, serial_number, date_time, comment
        )

    async def record_maintenance(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        date_time: Optional[datetime] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Record that an asset has had maintenance.

        Args:
            asset_id: Asset ID
            serial_number: Asset serial number (alternative)
            date_time: Maintenance date (default: now)
            comment: Log message

        Returns:
            True if successful
        """
        return await self._repository.post_maintenance(
            asset_id, serial_number, date_time, comment
        )

    # =========================================================================
    # Asset Log
    # =========================================================================

    async def get_asset_log(
        self,
        filter_str: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None
    ) -> List[AssetLog]:
        """
        Get asset log records.

        Args:
            filter_str: OData filter string
            orderby: OData order by string
            top: Maximum number to return

        Returns:
            List of AssetLog objects
        """
        return await self._repository.get_log(filter_str, orderby, top)

    async def add_log_message(
        self,
        asset_id: str,
        message: str,
        user: Optional[str] = None
    ) -> bool:
        """
        Post a message to the asset log.

        Args:
            asset_id: Asset ID
            message: Log message
            user: User who posted the message

        Returns:
            True if successful
        """
        return await self._repository.post_message(asset_id, message, user)

    # =========================================================================
    # Asset Types
    # =========================================================================

    async def get_asset_types(self) -> List[AssetType]:
        """
        Get all asset types.

        Returns:
            List of AssetType objects
        """
        return await self._repository.get_types()

    async def create_asset_type(
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
        """
        Create a new asset type.

        Args:
            type_name: Name of the asset type (required)
            running_count_limit: Max running count before alarm triggers
            total_count_limit: Maximum total usage count
            calibration_interval: Days between calibrations (float)
            maintenance_interval: Days between maintenance (float)
            warning_threshold: Warning threshold percentage (0-100)
            alarm_threshold: Alarm threshold percentage (0-100)
            icon: Icon identifier string for UI display

        Returns:
            Created AssetType object, or None on failure

        Example:
            >>> asset_type = await service.create_asset_type(
            ...     type_name="Test Station",
            ...     calibration_interval=365.0,
            ...     warning_threshold=80.0,
            ...     alarm_threshold=90.0
            ... )
        """
        asset_type = AssetType(
            type_name=type_name,
            running_count_limit=running_count_limit,
            total_count_limit=total_count_limit,
            calibration_interval=calibration_interval,
            maintenance_interval=maintenance_interval,
            warning_threshold=warning_threshold,
            alarm_threshold=alarm_threshold,
            icon=icon,
        )
        result = await self._repository.save_type(asset_type)
        if result:
            logger.info(f"ASSET_TYPE_CREATED: {result.type_name} (id={result.type_id})")
        return result

    # =========================================================================
    # Sub-Assets
    # =========================================================================

    async def get_child_assets(
        self,
        parent_id: Optional[str] = None,
        parent_serial: Optional[str] = None,
        level: Optional[int] = None
    ) -> List[Asset]:
        """
        Get child assets of a parent asset.

        Args:
            parent_id: Parent asset ID
            parent_serial: Parent asset serial number (alternative)
            level: How many levels deep (0=all, 1=direct children)

        Returns:
            List of child Asset objects
        """
        return await self._repository.get_sub_assets(parent_id, parent_serial, level)

    async def add_child_asset(
        self,
        parent_id: str,
        child_id: str
    ) -> bool:
        """
        Add a child asset to a parent asset.

        Args:
            parent_id: Parent asset ID
            child_id: Child asset ID to add

        Returns:
            True if successful
        """
        # Get child asset and update its parent
        child = await self._repository.get_by_id(child_id)
        if not child:
            raise ValueError(f"Child asset not found: {child_id}")
        
        child.parent_asset_id = parent_id
        result = await self._repository.save(child)
        if result:
            logger.info(f"CHILD_ASSET_ADDED: {child_id} -> parent {parent_id}")
        return result is not None

    # =========================================================================
    # ⚠️ INTERNAL API - File Operations
    # =========================================================================

    async def upload_file(
        self,
        asset_id: str,
        filename: str,
        content: bytes
    ) -> bool:
        """
        ⚠️ INTERNAL: Upload a file to an asset.

        Args:
            asset_id: Asset ID (GUID)
            filename: Unique filename
            content: File content as bytes

        Returns:
            True if successful
        """
        result = await self._repository.upload_file(asset_id, filename, content)
        if result:
            logger.info(f"FILE_UPLOADED: {filename} -> asset {asset_id}")
        return result

    async def download_file(
        self,
        asset_id: str,
        filename: str
    ) -> Optional[bytes]:
        """
        ⚠️ INTERNAL: Download a file from an asset.

        Args:
            asset_id: Asset ID (GUID)
            filename: Filename to download

        Returns:
            File content as bytes, or None
        """
        return await self._repository.download_file(asset_id, filename)

    async def list_files(self, asset_id: str) -> List[str]:
        """
        ⚠️ INTERNAL: List all files attached to an asset.

        Args:
            asset_id: Asset ID (GUID)

        Returns:
            List of filenames
        """
        return await self._repository.list_files(asset_id)

    async def delete_files(
        self,
        asset_id: str,
        filenames: List[str]
    ) -> bool:
        """
        ⚠️ INTERNAL: Delete files from an asset.

        Args:
            asset_id: Asset ID (GUID)
            filenames: List of filenames to delete

        Returns:
            True if successful
        """
        result = await self._repository.delete_files(asset_id, filenames)
        if result:
            logger.info(f"FILES_DELETED: {len(filenames)} files from asset {asset_id}")
        return result
