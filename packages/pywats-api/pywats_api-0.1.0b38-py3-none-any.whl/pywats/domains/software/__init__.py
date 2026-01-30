"""Software domain module.

Provides software distribution package services and models.
"""
from .enums import PackageStatus
from .models import Package, PackageFile, PackageTag, VirtualFolder

# Async implementations (primary API)
from .async_repository import AsyncSoftwareRepository
from .async_service import AsyncSoftwareService

# Backward-compatible aliases
SoftwareRepository = AsyncSoftwareRepository
SoftwareService = AsyncSoftwareService

__all__ = [
    # Enums
    "PackageStatus",
    # Models
    "Package",
    "PackageFile",
    "PackageTag",
    "VirtualFolder",
    # Async implementations (primary API)
    "AsyncSoftwareRepository",
    "AsyncSoftwareService",
    # Backward-compatible aliases
    "SoftwareRepository",
    "SoftwareService",
]
