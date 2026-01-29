"""Process domain module.

Provides process/operation management for test operations and repair operations.

This module handles the process list which defines:
- Test operations (e.g., End of line test, PCBA test, etc.)
- Repair operations (e.g., Repair, RMA repair)
- WIP operations
"""
from .models import ProcessInfo, RepairOperationConfig, RepairCategory

# Async implementations (primary API)
from .async_repository import AsyncProcessRepository
from .async_service import AsyncProcessService

# Backward-compatible aliases
ProcessRepository = AsyncProcessRepository
ProcessService = AsyncProcessService

__all__ = [
    # Models
    "ProcessInfo",
    "RepairOperationConfig",
    "RepairCategory",
    # Async implementations (primary API)
    "AsyncProcessRepository",
    "AsyncProcessService",
    # Backward-compatible aliases
    "ProcessRepository",
    "ProcessService",
]
