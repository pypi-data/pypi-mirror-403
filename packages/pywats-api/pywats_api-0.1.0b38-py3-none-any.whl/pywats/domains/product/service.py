"""Product service - thin sync wrapper around AsyncProductService.

This module provides synchronous access to AsyncProductService methods.
All business logic is maintained in async_service.py (source of truth).

⚠️ INTERNAL API methods are marked and may change without notice.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID

from .async_service import AsyncProductService
from .async_repository import AsyncProductRepository
from .models import Product, ProductRevision, ProductGroup, ProductView, BomItem, ProductRevisionRelation
from .enums import ProductState
from ...core.sync_runner import run_sync


class ProductService:
    """
    Synchronous wrapper for AsyncProductService.

    Provides sync access to all async product service operations.
    All business logic is in AsyncProductService.

    ⚠️ INTERNAL API methods are marked and may change without notice.
    """

    def __init__(self, async_service: AsyncProductService = None, *, repository=None) -> None:
        """
        Initialize with AsyncProductService or repository.

        Args:
            async_service: AsyncProductService instance to wrap
            repository: (Deprecated) Repository instance for backward compatibility
        """
        if repository is not None:
            # Backward compatibility: create async service from repository
            self._async_service = AsyncProductService(repository)
            self._repository = repository  # Keep reference for tests
        elif async_service is not None:
            self._async_service = async_service
            self._repository = async_service._repository  # Expose underlying repo
        else:
            raise ValueError("Either async_service or repository must be provided")

    @classmethod
    def from_repository(cls, repository: AsyncProductRepository, base_url: str = "") -> "ProductService":
        """
        Create ProductService from an AsyncProductRepository.

        Args:
            repository: AsyncProductRepository instance
            base_url: Base URL for internal API calls

        Returns:
            ProductService wrapping an AsyncProductService
        """
        async_service = AsyncProductService(repository, base_url)
        return cls(async_service)

    # =========================================================================
    # Product Operations
    # =========================================================================

    def get_products(self) -> List[ProductView]:
        """Get all products as simplified views.
        
        Returns:
            List of ProductView objects with basic product info
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_products())

    def get_products_full(self) -> List[Product]:
        """Get all products with full details.
        
        Returns:
            List of full Product objects including revisions and metadata
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_products_full())

    def get_product(self, part_number: str) -> Optional[Product]:
        """Get a product by part number.
        
        Args:
            part_number: The unique product part number
            
        Returns:
            Product if found, None otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_product(part_number))

    def create_product(
        self,
        part_number: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        non_serial: bool = False,
        state: ProductState = ProductState.ACTIVE,
        *,
        xml_data: Optional[str] = None,
        product_category_id: Optional[str] = None,
    ) -> Optional[Product]:
        """Create a new product.
        
        Args:
            part_number: Unique product identifier
            name: Optional product display name
            description: Optional product description
            non_serial: Whether product uses non-serial tracking
            state: Initial product state (default: ACTIVE)
            xml_data: Optional XML configuration data
            product_category_id: Optional category UUID
            
        Returns:
            Created Product if successful, None otherwise
            
        Raises:
            ValidationError: If part_number is invalid or already exists
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(
            self._async_service.create_product(
                part_number, name, description, non_serial, state,
                xml_data=xml_data, product_category_id=product_category_id
            )
        )

    def update_product(self, product: Product) -> Optional[Product]:
        """Update an existing product.
        
        Args:
            product: Product object with updated fields
            
        Returns:
            Updated Product if successful, None otherwise
            
        Raises:
            NotFoundError: If product does not exist
            ValidationError: If product data is invalid
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.update_product(product))

    def bulk_save_products(self, products: List[Product]) -> List[Product]:
        """Bulk create or update products.
        
        Args:
            products: List of Product objects to save
            
        Returns:
            List of saved Product objects
            
        Raises:
            ValidationError: If any product data is invalid
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.bulk_save_products(products))

    def get_active_products(self) -> List[ProductView]:
        """Get all active products.
        
        Returns:
            List of ProductView objects where state is ACTIVE
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_active_products())

    def is_active(self, product: Product) -> bool:
        """Check if a product is in active state."""
        return self._async_service.is_active(product)

    # =========================================================================
    # Revision Operations
    # =========================================================================

    def get_revisions(self, part_number: str) -> List[ProductRevision]:
        """Get all revisions for a product.
        
        Args:
            part_number: The product part number
            
        Returns:
            List of ProductRevision objects for the product
            
        Raises:
            NotFoundError: If product does not exist
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_revisions(part_number))

    def get_revision(self, part_number: str, revision: str) -> Optional[ProductRevision]:
        """Get a specific product revision.
        
        Args:
            part_number: The product part number
            revision: The revision identifier
            
        Returns:
            ProductRevision if found, None otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_revision(part_number, revision))

    def create_revision(
        self,
        part_number: str,
        revision: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        state: ProductState = ProductState.ACTIVE
    ) -> Optional[ProductRevision]:
        """Create a new product revision.
        
        Args:
            part_number: The product part number
            revision: The revision identifier
            name: Optional revision display name
            description: Optional revision description
            state: Initial revision state (default: ACTIVE)
            
        Returns:
            Created ProductRevision if successful, None otherwise
            
        Raises:
            NotFoundError: If product does not exist
            ValidationError: If revision already exists or data is invalid
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(
            self._async_service.create_revision(
                part_number, revision, name, description, state
            )
        )

    def update_revision(self, revision: ProductRevision) -> Optional[ProductRevision]:
        """Update an existing product revision.
        
        Args:
            revision: ProductRevision object with updated fields
            
        Returns:
            Updated ProductRevision if successful, None otherwise
            
        Raises:
            NotFoundError: If revision does not exist
            ValidationError: If revision data is invalid
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.update_revision(revision))

    def bulk_save_revisions(self, revisions: List[ProductRevision]) -> List[ProductRevision]:
        """Bulk create or update product revisions.
        
        Args:
            revisions: List of ProductRevision objects to save
            
        Returns:
            List of saved ProductRevision objects
            
        Raises:
            ValidationError: If any revision data is invalid
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.bulk_save_revisions(revisions))

    # =========================================================================
    # Product Groups
    # =========================================================================

    def get_groups(self) -> List[ProductGroup]:
        """Get all product groups.
        
        Returns:
            List of all ProductGroup objects
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_groups())

    def create_group(
        self,
        name: str,
        description: Optional[str] = None
    ) -> Optional[ProductGroup]:
        """Create a new product group.
        
        Args:
            name: Group name (must be unique)
            description: Optional group description
            
        Returns:
            Created ProductGroup if successful, None otherwise
            
        Raises:
            ValidationError: If name already exists or is invalid
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.create_group(name, description))

    def get_groups_for_product(self, part_number: str) -> List[ProductGroup]:
        """Get product groups that contain a specific product.
        
        Args:
            part_number: The product part number
            
        Returns:
            List of ProductGroup objects containing the product
            
        Raises:
            NotFoundError: If product does not exist
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_groups_for_product(part_number))

    # =========================================================================
    # ⚠️ INTERNAL API - BOM Operations
    # =========================================================================

    def get_bom(self, part_number: str, revision: str) -> List[BomItem]:
        """⚠️ INTERNAL: Get BOM (Bill of Materials) for a product revision.
        
        Args:
            part_number: The product part number
            revision: The revision identifier
            
        Returns:
            List of BomItem objects
            
        Raises:
            NotFoundError: If product or revision does not exist
            AuthenticationError: If API authentication fails
            APIError: If the server request fails or endpoint changes
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_bom(part_number, revision))

    def upload_bom(
        self,
        part_number: str,
        revision: str,
        bom_items: List[Dict[str, Any]],
        format: str = "json"
    ) -> bool:
        """⚠️ INTERNAL: Upload/update BOM items.
        
        Args:
            part_number: The product part number
            revision: The revision identifier
            bom_items: List of BOM item dictionaries
            format: Import format (default: "json")
            
        Returns:
            True if upload successful
            
        Raises:
            NotFoundError: If product or revision does not exist
            ValidationError: If BOM data format is invalid
            AuthenticationError: If API authentication fails
            APIError: If the server request fails or endpoint changes
            PyWATSError: For other API-related errors
        """
        return run_sync(
            self._async_service.upload_bom(part_number, revision, bom_items, format)
        )

    def get_bom_items(self, part_number: str, revision: str) -> List[BomItem]:
        """⚠️ INTERNAL: Get BOM items (alias for get_bom)."""
        return run_sync(self._async_service.get_bom_items(part_number, revision))

    def update_bom(
        self,
        part_number: str,
        revision: str,
        bom_items: List[BomItem],
        description: Optional[str] = None
    ) -> bool:
        """Update product BOM (Bill of Materials)."""
        return run_sync(
            self._async_service.update_bom(part_number, revision, bom_items, description)
        )

    # =========================================================================
    # ⚠️ INTERNAL API - Box Build / Revision Relations
    # =========================================================================

    def get_product_hierarchy(
        self,
        part_number: str,
        revision: str
    ) -> List[Dict[str, Any]]:
        """⚠️ INTERNAL: Get product hierarchy including all child revision relations."""
        return run_sync(
            self._async_service.get_product_hierarchy(part_number, revision)
        )

    def add_subunit(
        self,
        parent_part_number: str,
        parent_revision: str,
        child_part_number: str,
        child_revision: str,
        quantity: int = 1,
        revision_mask: Optional[str] = None
    ) -> Optional[ProductRevisionRelation]:
        """⚠️ INTERNAL: Add a subunit to a product's box build template."""
        return run_sync(
            self._async_service.add_subunit(
                parent_part_number, parent_revision,
                child_part_number, child_revision,
                quantity, revision_mask
            )
        )

    def remove_subunit(self, relation_id: UUID) -> bool:
        """⚠️ INTERNAL: Remove a subunit from a product's box build template."""
        return run_sync(self._async_service.remove_subunit(relation_id))

    def get_box_build_template(self, part_number: str, revision: str):
        """⚠️ INTERNAL: Get or create a box build template for a product revision."""
        return run_sync(self._async_service.get_box_build_template(part_number, revision))

    def get_box_build_subunits(
        self,
        part_number: str,
        revision: str
    ) -> List[ProductRevisionRelation]:
        """⚠️ INTERNAL: Get subunits for a box build (read-only)."""
        return run_sync(
            self._async_service.get_box_build_subunits(part_number, revision)
        )

    # =========================================================================
    # ⚠️ INTERNAL API - Product Categories
    # =========================================================================

    def get_product_categories(self) -> List[Dict[str, Any]]:
        """⚠️ INTERNAL: Get all product categories."""
        return run_sync(self._async_service.get_product_categories())

    def save_product_categories(self, categories: List[Dict[str, Any]]) -> bool:
        """⚠️ INTERNAL: Save product categories."""
        return run_sync(self._async_service.save_product_categories(categories))

    # =========================================================================
    # Tags (using product/revision updates)
    # =========================================================================

    def get_product_tags(self, part_number: str) -> List[Dict[str, str]]:
        """Get tags for a product.
        
        Args:
            part_number: The product part number
            
        Returns:
            List of tag dictionaries with 'name' and 'value' keys
            
        Raises:
            NotFoundError: If product does not exist
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_product_tags(part_number))

    def set_product_tags(
        self,
        part_number: str,
        tags: List[Dict[str, str]]
    ) -> Optional[Product]:
        """Set tags for a product (replaces existing tags).
        
        Args:
            part_number: The product part number
            tags: List of tag dictionaries with 'name' and 'value' keys
            
        Returns:
            Updated Product if successful, None otherwise
            
        Raises:
            NotFoundError: If product does not exist
            ValidationError: If tag data is invalid
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.set_product_tags(part_number, tags))

    def add_product_tag(
        self,
        part_number: str,
        name: str,
        value: str
    ) -> Optional[Product]:
        """Add a single tag to a product.
        
        Args:
            part_number: The product part number
            name: Tag name
            value: Tag value
            
        Returns:
            Updated Product if successful, None otherwise
            
        Raises:
            NotFoundError: If product does not exist
            ValidationError: If tag name or value is invalid
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.add_product_tag(part_number, name, value))

    def get_revision_tags(
        self,
        part_number: str,
        revision: str
    ) -> List[Dict[str, str]]:
        """Get tags for a product revision.
        
        Args:
            part_number: The product part number
            revision: The revision identifier
            
        Returns:
            List of tag dictionaries with 'name' and 'value' keys
            
        Raises:
            NotFoundError: If product or revision does not exist
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_revision_tags(part_number, revision))

    def set_revision_tags(
        self,
        part_number: str,
        revision: str,
        tags: List[Dict[str, str]]
    ) -> Optional[ProductRevision]:
        """Set tags for a product revision.
        
        Args:
            part_number: The product part number
            revision: The revision identifier
            tags: List of tag dictionaries with 'name' and 'value' keys
            
        Returns:
            Updated ProductRevision if successful, None otherwise
            
        Raises:
            NotFoundError: If product or revision does not exist
            ValidationError: If tag data is invalid
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(
            self._async_service.set_revision_tags(part_number, revision, tags)
        )

    def add_revision_tag(
        self,
        part_number: str,
        revision: str,
        name: str,
        value: str
    ) -> Optional[ProductRevision]:
        """Add a single tag to a product revision.
        
        Args:
            part_number: The product part number
            revision: The revision identifier
            name: Tag name
            value: Tag value
            
        Returns:
            Updated ProductRevision if successful, None otherwise
            
        Raises:
            NotFoundError: If product or revision does not exist
            ValidationError: If tag name or value is invalid
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(
            self._async_service.add_revision_tag(part_number, revision, name, value)
        )

    # =========================================================================
    # ⚠️ INTERNAL API - Vendors
    # =========================================================================

    def get_vendors(self) -> List[Dict[str, Any]]:
        """⚠️ INTERNAL: Get all vendors."""
        return run_sync(self._async_service.get_vendors())

    def save_vendor(
        self,
        name: str,
        vendor_id: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Create or update a vendor."""
        return run_sync(self._async_service.save_vendor(name, vendor_id, **kwargs))

    def delete_vendor(self, vendor_id: str) -> bool:
        """⚠️ INTERNAL: Delete a vendor."""
        return run_sync(self._async_service.delete_vendor(vendor_id))
