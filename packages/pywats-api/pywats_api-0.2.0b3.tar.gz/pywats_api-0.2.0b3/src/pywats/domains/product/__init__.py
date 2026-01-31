"""Product domain.

Provides models, services, and repository for product management.
"""
from .models import (
    Product, 
    ProductRevision, 
    ProductView, 
    ProductGroup,
    ProductCategory,
    ProductRevisionRelation,
    BomItem,
)
from .enums import ProductState
from .box_build import BoxBuildTemplate

# Async implementations (primary API)
from .async_repository import AsyncProductRepository
from .async_service import AsyncProductService

__all__ = [
    # Models
    "Product",
    "ProductRevision",
    "ProductView",
    "ProductGroup",
    "ProductCategory",
    "ProductRevisionRelation",
    "BomItem",
    # Box Build
    "BoxBuildTemplate",
    # Enums
    "ProductState",
    # Async implementations
    "AsyncProductRepository",
    "AsyncProductService",
]
