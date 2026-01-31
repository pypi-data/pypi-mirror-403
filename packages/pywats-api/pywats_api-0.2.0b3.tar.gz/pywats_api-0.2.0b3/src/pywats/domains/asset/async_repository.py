"""Async Asset repository - data access layer.

Async version of the asset repository for non-blocking API calls.
Includes both public and internal API methods.
Uses Routes class for centralized endpoint management.

⚠️ INTERNAL API methods are marked and may change without notice.
"""
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING, cast
from datetime import datetime
import base64
import logging

if TYPE_CHECKING:
    from ...core.async_client import AsyncHttpClient
    from ...core.exceptions import ErrorHandler

from ...core.routes import Routes
from .models import Asset, AssetType, AssetLog
from .enums import AssetState

logger = logging.getLogger(__name__)


class AsyncAssetRepository:
    """
    Async Asset data access layer.

    Handles all async WATS API interactions for asset management.
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
            error_handler: Optional ErrorHandler for error handling (default: STRICT mode)
        """
        self._http_client = http_client
        self._base_url = base_url.rstrip('/') if base_url else ""
        from ...core.exceptions import ErrorHandler, ErrorMode
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
        """⚠️ INTERNAL: Make an internal API GET request with Referer header."""
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
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        operation: str = "internal_post"
    ) -> Any:
        """⚠️ INTERNAL: Make an internal API POST request with Referer header."""
        all_headers = {"Referer": self._base_url}
        if headers:
            all_headers.update(headers)
        response = await self._http_client.post(
            endpoint,
            data=data,
            params=params,
            headers=all_headers
        )
        self._error_handler.handle_response(
            response, operation=operation, allow_empty=True
        )
        return response

    async def _internal_delete(
        self,
        endpoint: str,
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
        operation: str = "internal_delete"
    ) -> bool:
        """⚠️ INTERNAL: Make an internal API DELETE request with Referer header."""
        response = await self._http_client.delete(
            endpoint,
            params=params,
            headers={"Referer": self._base_url}
        )
        self._error_handler.handle_response(
            response, operation=operation, allow_empty=True
        )
        return response.is_success

    # =========================================================================
    # Asset CRUD
    # =========================================================================

    async def get_all(
        self,
        filter_str: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List[Asset]:
        """
        Get all assets with optional OData filtering.

        GET /api/Asset
        """
        logger.debug(f"Fetching assets (filter={filter_str}, top={top})")
        params: Dict[str, Any] = {}
        if filter_str:
            params["$filter"] = filter_str
        if orderby:
            params["$orderby"] = orderby
        if top:
            params["$top"] = top
        if skip:
            params["$skip"] = skip

        response = await self._http_client.get(
            Routes.Asset.BASE,
            params=params if params else None
        )
        data = self._error_handler.handle_response(
            response, operation="get_all", allow_empty=True
        )
        if data:
            assets = [Asset.model_validate(item) for item in data]
            logger.info(f"Retrieved {len(assets)} assets")
            return assets
        return []

    async def get_by_id(self, asset_id: str) -> Optional[Asset]:
        """
        Get an asset by its ID.

        GET /api/Asset/{assetId}
        """
        logger.debug(f"Fetching asset: {asset_id}")
        response = await self._http_client.get(Routes.Asset.asset(str(asset_id)))
        data = self._error_handler.handle_response(
            response, operation="get_by_id", allow_empty=True
        )
        if data:
            asset = Asset.model_validate(data)
            logger.info(f"Retrieved asset: {asset_id}")
            return asset
        return None

    async def get_by_serial_number(self, serial_number: str) -> Optional[Asset]:
        """
        Get an asset by its serial number.

        GET /api/Asset/{serialNumber}
        """
        response = await self._http_client.get(Routes.Asset.asset(serial_number))
        data = self._error_handler.handle_response(
            response, operation="get_by_serial_number", allow_empty=True
        )
        if data:
            return Asset.model_validate(data)
        return None

    async def save(self, asset: Union[Asset, Dict[str, Any]]) -> Optional[Asset]:
        """
        Create a new asset or update an existing one.

        PUT /api/Asset
        """
        if isinstance(asset, Asset):
            payload = asset.model_dump(mode="json", by_alias=True, exclude_none=True)
        else:
            payload = asset
        response = await self._http_client.put(Routes.Asset.BASE, data=payload)
        data = self._error_handler.handle_response(
            response, operation="save", allow_empty=False
        )
        if data:
            return Asset.model_validate(data)
        return None

    async def delete(self, asset_id: str, serial_number: Optional[str] = None) -> bool:
        """
        Delete an asset by ID or serial number.

        DELETE /api/Asset
        """
        params: Dict[str, Any] = {}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        response = await self._http_client.delete(Routes.Asset.BASE, params=params)
        self._error_handler.handle_response(
            response, operation="delete", allow_empty=True
        )
        return response.is_success

    # =========================================================================
    # Asset Status and State
    # =========================================================================

    async def get_status(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        translate: bool = True,
        culture_code: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the current status of an asset including alarm state.

        GET /api/Asset/Status
        """
        params: Dict[str, Any] = {}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        if not translate:
            params["translate"] = "false"
        if culture_code:
            params["cultureCode"] = culture_code
            
        response = await self._http_client.get(Routes.Asset.STATUS, params=params)
        data = self._error_handler.handle_response(
            response, operation="get_status", allow_empty=True
        )
        if data:
            return cast(Dict[str, Any], data)
        return None

    async def set_state(
        self,
        state: Union[AssetState, int],
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None
    ) -> bool:
        """
        Set the state of an asset.

        PUT /api/Asset/State
        """
        state_value = state.value if isinstance(state, AssetState) else state
        params: Dict[str, Any] = {"state": state_value}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        response = await self._http_client.put(Routes.Asset.STATE, params=params)
        self._error_handler.handle_response(
            response, operation="set_state", allow_empty=True
        )
        return response.is_success

    # =========================================================================
    # Asset Count
    # =========================================================================

    async def update_count(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        total_count: Optional[int] = None,
        increment_by: Optional[int] = None,
        increment_children: bool = False
    ) -> bool:
        """
        Increment the running and total count on an asset.

        PUT /api/Asset/Count
        """
        params: Dict[str, Any] = {}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        if total_count is not None:
            params["totalCount"] = total_count
        if increment_by is not None:
            params["incrementBy"] = increment_by
        if increment_children:
            params["incrementChildren"] = "true"
        response = await self._http_client.put(Routes.Asset.COUNT, params=params)
        self._error_handler.handle_response(
            response, operation="update_count", allow_empty=True
        )
        return response.is_success

    async def reset_running_count(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Reset the running count to 0.

        POST /api/Asset/ResetRunningCount
        """
        params: Dict[str, Any] = {}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        if comment:
            params["comment"] = comment
        response = await self._http_client.post(
            Routes.Asset.RESET_RUNNING_COUNT,
            params=params
        )
        self._error_handler.handle_response(
            response, operation="reset_running_count", allow_empty=True
        )
        return response.is_success

    async def set_running_count(
        self,
        value: int,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None
    ) -> bool:
        """
        Set the running count to a specific value.

        PUT /api/Asset/SetRunningCount

        New in WATS 25.3. Requires 'Edit Total count' permission.
        """
        params: Dict[str, Any] = {"runningCount": value}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        response = await self._http_client.put(
            Routes.Asset.SET_RUNNING_COUNT,
            params=params
        )
        self._error_handler.handle_response(
            response, operation="set_running_count", allow_empty=True
        )
        return response.is_success

    async def set_total_count(
        self,
        value: int,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None
    ) -> bool:
        """
        Set the total count to a specific value.

        PUT /api/Asset/SetTotalCount

        New in WATS 25.3. Requires 'Edit Total count' permission.
        """
        params: Dict[str, Any] = {"totalCount": value}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        response = await self._http_client.put(
            Routes.Asset.SET_TOTAL_COUNT,
            params=params
        )
        self._error_handler.handle_response(
            response, operation="set_total_count", allow_empty=True
        )
        return response.is_success

    # =========================================================================
    # Calibration and Maintenance
    # =========================================================================

    async def post_calibration(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        date_time: Optional[datetime] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Inform that an asset has been calibrated.

        POST /api/Asset/Calibration
        """
        params: Dict[str, Any] = {}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        if date_time:
            params["dateTime"] = date_time.isoformat()
        if comment:
            params["comment"] = comment
        response = await self._http_client.post(Routes.Asset.CALIBRATION, params=params)
        self._error_handler.handle_response(
            response, operation="post_calibration", allow_empty=True
        )
        return response.is_success

    async def post_maintenance(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        date_time: Optional[datetime] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Inform that an asset has had maintenance.

        POST /api/Asset/Maintenance
        """
        params: Dict[str, Any] = {}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        if date_time:
            params["dateTime"] = date_time.isoformat()
        if comment:
            params["comment"] = comment
        response = await self._http_client.post(Routes.Asset.MAINTENANCE, params=params)
        self._error_handler.handle_response(
            response, operation="post_maintenance", allow_empty=True
        )
        return response.is_success

    async def post_calibration_external(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Inform that an asset has been calibrated with external date range.

        POST /api/Asset/Calibration/External

        New in WATS 25.3. Use when calibration is managed by an external system.
        Allows setting both 'last calibration' and 'next calibration' dates.
        """
        params: Dict[str, Any] = {}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        if from_date:
            params["fromDate"] = from_date.isoformat()
        if to_date:
            params["toDate"] = to_date.isoformat()
        if comment:
            params["comment"] = comment
        response = await self._http_client.post(
            Routes.Asset.CALIBRATION_EXTERNAL,
            params=params
        )
        self._error_handler.handle_response(
            response, operation="post_calibration_external", allow_empty=True
        )
        return response.is_success

    async def post_maintenance_external(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Inform that an asset has had maintenance with external date range.

        POST /api/Asset/Maintenance/External

        New in WATS 25.3. Use when maintenance is managed by an external system.
        Allows setting both 'last maintenance' and 'next maintenance' dates.
        """
        params: Dict[str, Any] = {}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        if from_date:
            params["fromDate"] = from_date.isoformat()
        if to_date:
            params["toDate"] = to_date.isoformat()
        if comment:
            params["comment"] = comment
        response = await self._http_client.post(
            Routes.Asset.MAINTENANCE_EXTERNAL,
            params=params
        )
        self._error_handler.handle_response(
            response, operation="post_maintenance_external", allow_empty=True
        )
        return response.is_success

    # =========================================================================
    # Asset Log
    # =========================================================================

    async def get_log(
        self,
        filter_str: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List[AssetLog]:
        """
        Get asset log records.

        GET /api/Asset/Log
        """
        params: Dict[str, Any] = {}
        if filter_str:
            params["$filter"] = filter_str
        if orderby:
            params["$orderby"] = orderby
        if top:
            params["$top"] = top
        if skip:
            params["$skip"] = skip
        response = await self._http_client.get(
            Routes.Asset.LOG,
            params=params if params else None
        )
        data = self._error_handler.handle_response(
            response, operation="get_log", allow_empty=True
        )
        if data:
            return [AssetLog.model_validate(item) for item in data]
        return []

    async def post_message(
        self,
        asset_id: str,
        message: str,
        user: Optional[str] = None
    ) -> bool:
        """
        Post a message to the asset log.

        POST /api/Asset/Message
        """
        payload: Dict[str, Any] = {"assetId": asset_id, "comment": message}
        if user:
            payload["user"] = user
        response = await self._http_client.post(Routes.Asset.MESSAGE, data=payload)
        self._error_handler.handle_response(
            response, operation="post_message", allow_empty=True
        )
        return response.is_success

    # =========================================================================
    # Asset Types
    # =========================================================================

    async def get_types(
        self,
        filter_str: Optional[str] = None,
        top: Optional[int] = None
    ) -> List[AssetType]:
        """
        Get all asset types.

        GET /api/Asset/Types
        """
        params: Dict[str, Any] = {}
        if filter_str:
            params["$filter"] = filter_str
        if top:
            params["$top"] = top
        response = await self._http_client.get(
            Routes.Asset.TYPES,
            params=params if params else None
        )
        data = self._error_handler.handle_response(
            response, operation="get_types", allow_empty=True
        )
        if data:
            return [AssetType.model_validate(item) for item in data]
        return []

    async def save_type(
        self,
        asset_type: Union[AssetType, Dict[str, Any]]
    ) -> Optional[AssetType]:
        """
        Create or update an asset type.

        PUT /api/Asset/Types
        """
        if isinstance(asset_type, AssetType):
            payload = asset_type.model_dump(by_alias=True, exclude_none=True)
        else:
            payload = asset_type
        response = await self._http_client.put(Routes.Asset.TYPES, data=payload)
        data = self._error_handler.handle_response(
            response, operation="save_type", allow_empty=False
        )
        if data:
            return AssetType.model_validate(data)
        return None

    # =========================================================================
    # Sub-Assets
    # =========================================================================

    async def get_sub_assets(
        self,
        parent_id: Optional[str] = None,
        parent_serial: Optional[str] = None,
        level: Optional[int] = None
    ) -> List[Asset]:
        """
        Get child assets of a parent asset.

        GET /api/Asset/SubAssets
        """
        params: Dict[str, Any] = {}
        if parent_id:
            params["id"] = parent_id
        if parent_serial:
            params["serialNumber"] = parent_serial
        if level is not None:
            params["level"] = level
        response = await self._http_client.get(Routes.Asset.SUB_ASSETS, params=params)
        data = self._error_handler.handle_response(
            response, operation="get_sub_assets", allow_empty=True
        )
        if data:
            return [Asset.model_validate(item) for item in data]
        return []

    # =========================================================================
    # ⚠️ INTERNAL API - File Operations (Blob)
    # =========================================================================

    async def upload_file(
        self,
        asset_id: str,
        filename: str,
        content: bytes
    ) -> bool:
        """
        ⚠️ INTERNAL: Upload a file to an asset.

        POST /api/internal/Blob/Asset
        """
        params = {"assetId": asset_id, "filename": filename}
        response = await self._internal_post(
            Routes.Asset.Internal.BLOB_BASE,
            params=params,
            data=content,
            headers={"Content-Type": "application/octet-stream"},
            operation="upload_file"
        )
        return response.is_success if response else False

    async def download_file(
        self,
        asset_id: str,
        filename: str
    ) -> Optional[bytes]:
        """
        ⚠️ INTERNAL: Download a file from an asset.

        GET /api/internal/Blob/Asset
        """
        params = {"assetId": asset_id, "filename": filename}
        response = await self._http_client.get(
            Routes.Asset.Internal.BLOB_BASE,
            params=params,
            headers={"Referer": self._base_url}
        )
        data = self._error_handler.handle_response(
            response, operation="download_file", allow_empty=True
        )
        if data:
            if isinstance(data, bytes):
                return data
            if isinstance(data, dict):
                content = data.get("content") or data.get("Content")
                if content:
                    return base64.b64decode(content)
        return None

    async def list_files(self, asset_id: str) -> List[str]:
        """
        ⚠️ INTERNAL: List all files attached to an asset.

        GET /api/internal/Blob/Asset/List/{assetId}
        """
        data = await self._internal_get(
            Routes.Asset.Internal.list_files(str(asset_id)),
            operation="list_files"
        )
        if data:
            return list(data) if isinstance(data, list) else []
        return []

    async def delete_files(
        self,
        asset_id: str,
        filenames: List[str]
    ) -> bool:
        """
        ⚠️ INTERNAL: Delete files from an asset.

        DELETE /api/internal/Blob/Assets
        """
        return await self._internal_delete(
            Routes.Asset.Internal.DELETE_FILES,
            params={"assetId": asset_id},
            data=filenames,
            operation="delete_files"
        )
