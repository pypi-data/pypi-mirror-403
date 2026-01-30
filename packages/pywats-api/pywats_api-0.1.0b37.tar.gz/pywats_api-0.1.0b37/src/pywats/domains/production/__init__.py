"""Production domain.

Provides models, services, and repository for production unit management.
"""
from .models import (
    Unit, UnitChange, ProductionBatch, SerialNumberType,
    UnitVerification, UnitVerificationGrade, UnitPhase
)
from .enums import SerialNumberIdentifier, UnitPhaseFlag

# Async implementations (primary API)
from .async_repository import AsyncProductionRepository
from .async_service import AsyncProductionService

# Backward-compatible aliases
ProductionRepository = AsyncProductionRepository
ProductionService = AsyncProductionService

# Rebuild Unit model to resolve forward references to Product/ProductRevision
from ..product.models import Product, ProductRevision
Unit.model_rebuild()

__all__ = [
    # Models
    "Unit",
    "UnitChange",
    "UnitPhase",
    "ProductionBatch",
    "SerialNumberType",
    "UnitVerification",
    "UnitVerificationGrade",
    # Enums
    "SerialNumberIdentifier",
    "UnitPhaseFlag",
    # Async implementations (primary API)
    "AsyncProductionService",
    "AsyncProductionRepository",
    # Backward-compatible aliases
    "ProductionRepository",
    "ProductionService",
]
