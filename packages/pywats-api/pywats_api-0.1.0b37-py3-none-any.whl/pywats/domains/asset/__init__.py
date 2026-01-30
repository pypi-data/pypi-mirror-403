"""Asset domain.

Provides models, services, and repository for asset management.
"""
from .models import Asset, AssetType, AssetLog
from .enums import AssetState, AssetLogType, AssetAlarmState

# Async implementations (primary API)
from .async_repository import AsyncAssetRepository
from .async_service import AsyncAssetService

# Backward-compatible aliases
AssetRepository = AsyncAssetRepository
AssetService = AsyncAssetService

__all__ = [
    # Models
    "Asset",
    "AssetType",
    "AssetLog",
    # Enums
    "AssetState",
    "AssetLogType",
    "AssetAlarmState",
    # Async implementations (primary API)
    "AsyncAssetRepository",
    "AsyncAssetService",
    # Backward-compatible aliases
    "AssetRepository",
    "AssetService",
]
