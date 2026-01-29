"""Async Product service - business logic layer.

Async version of the product service for non-blocking operations.
Includes both public and internal API methods.

⚠️ INTERNAL API methods are marked and may change without notice.
"""
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from uuid import UUID
import logging

from .models import Product, ProductRevision, ProductGroup, ProductView, BomItem, ProductRevisionRelation
from .enums import ProductState
from .async_repository import AsyncProductRepository

logger = logging.getLogger(__name__)


class AsyncProductService:
    """
    Async Product business logic.

    Provides high-level async operations for managing products, revisions,
    groups, and vendors.
    Includes both public and internal API methods (marked with ⚠️).
    """

    def __init__(
        self, 
        repository: AsyncProductRepository,
        base_url: str = ""
    ):
        """
        Initialize with async repository.

        Args:
            repository: AsyncProductRepository for data access
            base_url: Base URL for internal API calls
        """
        self._repository = repository
        self._base_url = base_url.rstrip("/") if base_url else ""

    # =========================================================================
    # Product Operations
    # =========================================================================

    async def get_products(self) -> List[ProductView]:
        """
        Get all products as simplified views.

        Returns:
            List of ProductView objects
        """
        products = await self._repository.get_all()
        return [
            ProductView(
                part_number=p.part_number,
                name=p.name,
                non_serial=p.non_serial,
                state=p.state
            )
            for p in products
        ]

    async def get_products_full(self) -> List[Product]:
        """
        Get all products with full details.

        Returns:
            List of Product objects
        """
        return await self._repository.get_all()

    async def get_product(self, part_number: str) -> Optional[Product]:
        """
        Get a product by part number.

        Args:
            part_number: The product part number

        Returns:
            Product if found, None otherwise
        """
        if not part_number or not part_number.strip():
            raise ValueError("part_number is required")
        return await self._repository.get_by_part_number(part_number)

    async def create_product(
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
        """
        Create a new product.

        Args:
            part_number: Unique part number (required)
            name: Product display name
            description: Product description text
            non_serial: If True, product cannot have serialized units
            state: Product state (default: ACTIVE)
            xml_data: Custom XML data for key-value storage
            product_category_id: UUID of product category to assign

        Returns:
            Created Product object, or None on failure
        """
        if not part_number or not part_number.strip():
            raise ValueError("part_number is required")
        product = Product(
            part_number=part_number,
            name=name,
            description=description,
            non_serial=non_serial,
            state=state,
            xml_data=xml_data,
            product_category_id=product_category_id,
        )
        result = await self._repository.save(product)
        if result:
            logger.info(f"PRODUCT_CREATED: {result.part_number} (name={name}, state={state.name})")
        return result

    async def update_product(self, product: Product) -> Optional[Product]:
        """
        Update an existing product.

        Args:
            product: Product object with updated fields

        Returns:
            Updated Product object
        """
        result = await self._repository.save(product)
        if result:
            logger.info(f"PRODUCT_UPDATED: {result.part_number}")
        return result

    async def bulk_save_products(
        self, products: List[Product]
    ) -> List[Product]:
        """
        Bulk create or update products.

        Args:
            products: List of Product objects

        Returns:
            List of saved Product objects
        """
        results = await self._repository.save_bulk(products)
        if results:
            logger.info(f"PRODUCTS_BULK_SAVED: count={len(results)}")
        return results

    async def get_active_products(self) -> List[ProductView]:
        """
        Get all active products.

        Returns:
            List of active ProductView objects
        """
        products = await self.get_products()
        return [p for p in products if p.state == ProductState.ACTIVE]

    def is_active(self, product: Product) -> bool:
        """
        Check if a product is in active state.
        
        Args:
            product: Product to check
            
        Returns:
            True if product state is ACTIVE
        """
        return product.state == ProductState.ACTIVE

    # =========================================================================
    # Revision Operations
    # =========================================================================

    async def get_revisions(self, part_number: str) -> List[ProductRevision]:
        """
        Get all revisions for a product.
        
        Args:
            part_number: Product part number
            
        Returns:
            List of ProductRevision objects
        """
        product = await self.get_product(part_number)
        if not product:
            return []
        return product.revisions

    async def get_revision(
        self, part_number: str, revision: str
    ) -> Optional[ProductRevision]:
        """
        Get a specific product revision.

        Args:
            part_number: The product part number
            revision: The revision identifier

        Returns:
            ProductRevision or None if not found
        """
        if not part_number or not part_number.strip():
            raise ValueError("part_number is required")
        if not revision or not revision.strip():
            raise ValueError("revision is required")
        
        product = await self._repository.get_by_part_number(part_number)
        if not product:
            return None
        
        for rev in product.revisions:
            if rev.revision == revision:
                rev.part_number = part_number
                return rev
        return None

    async def create_revision(
        self,
        part_number: str,
        revision: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        state: ProductState = ProductState.ACTIVE
    ) -> Optional[ProductRevision]:
        """
        Create a new product revision.

        Args:
            part_number: Product part number
            revision: Revision identifier
            name: Revision name/title
            description: Revision description
            state: Revision state

        Returns:
            Created ProductRevision object
        """
        if not part_number or not part_number.strip():
            raise ValueError("part_number is required")
        if not revision or not revision.strip():
            raise ValueError("revision is required")
        
        # Get or create the product to obtain product_id
        product = await self._repository.get_by_part_number(part_number)
        
        rev = ProductRevision(
            part_number=part_number,
            revision=revision,
            name=name,
            description=description,
            state=state,
            product_id=product.product_id if product else None
        )
        result = await self._repository.save_revision(rev)
        if result:
            logger.info(f"REVISION_CREATED: {part_number}/{revision}")
        return result

    async def update_revision(
        self, revision: ProductRevision
    ) -> Optional[ProductRevision]:
        """
        Update an existing product revision.

        Args:
            revision: ProductRevision object with updated fields

        Returns:
            Updated ProductRevision object
        """
        result = await self._repository.save_revision(revision)
        if result:
            logger.info(f"REVISION_UPDATED: {revision.part_number}/{revision.revision}")
        return result

    async def bulk_save_revisions(
        self, revisions: List[ProductRevision]
    ) -> List[ProductRevision]:
        """
        Bulk create or update product revisions.
        
        Args:
            revisions: List of ProductRevision objects
            
        Returns:
            List of saved ProductRevision objects
        """
        results = []
        for rev in revisions:
            result = await self._repository.save_revision(rev)
            if result:
                results.append(result)
        if results:
            logger.info(f"REVISIONS_BULK_SAVED: count={len(results)}")
        return results

    # =========================================================================
    # Product Groups
    # =========================================================================

    async def get_groups(self) -> List[ProductGroup]:
        """
        Get all product groups.

        Returns:
            List of ProductGroup objects
        """
        return await self._repository.get_groups()

    async def create_group(
        self,
        name: str,
        description: Optional[str] = None
    ) -> Optional[ProductGroup]:
        """
        Create a new product group.

        Args:
            name: Group name
            description: Group description

        Returns:
            Created ProductGroup object
        """
        group = ProductGroup(name=name, description=description)
        result = await self._repository.save_group(group)
        if result:
            logger.info(f"GROUP_CREATED: {name}")
        return result

    # =========================================================================
    # ⚠️ INTERNAL API - BOM Operations
    # =========================================================================

    async def get_bom(self, part_number: str, revision: str) -> List[BomItem]:
        """
        ⚠️ INTERNAL: Get BOM (Bill of Materials) for a product revision.

        Args:
            part_number: Product part number
            revision: Product revision

        Returns:
            List of BomItem objects
        """
        return await self._repository.get_bom(part_number, revision)

    async def upload_bom(
        self,
        part_number: str,
        revision: str,
        bom_items: List[Dict[str, Any]],
        format: str = "json"
    ) -> bool:
        """
        ⚠️ INTERNAL: Upload/update BOM items.

        Args:
            part_number: Product part number
            revision: Product revision
            bom_items: List of BOM item dictionaries
            format: BOM format (default: "json")

        Returns:
            True if successful
        """
        return await self._repository.upload_bom(part_number, revision, bom_items, format)

    # =========================================================================
    # ⚠️ INTERNAL API - Box Build / Revision Relations
    # =========================================================================

    async def get_product_hierarchy(
        self,
        part_number: str,
        revision: str
    ) -> List[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get product hierarchy including all child revision relations.

        Args:
            part_number: Product part number
            revision: Product revision

        Returns:
            List of hierarchy items
        """
        return await self._repository.get_product_hierarchy(part_number, revision)

    async def add_subunit(
        self,
        parent_part_number: str,
        parent_revision: str,
        child_part_number: str,
        child_revision: str,
        quantity: int = 1,
        revision_mask: Optional[str] = None
    ) -> Optional[ProductRevisionRelation]:
        """
        ⚠️ INTERNAL: Add a subunit to a product's box build template.

        Args:
            parent_part_number: Parent product part number
            parent_revision: Parent product revision
            child_part_number: Child product part number
            child_revision: Child product revision
            quantity: Number of child units required
            revision_mask: Optional revision mask pattern

        Returns:
            Created ProductRevisionRelation or None
        """
        parent = await self.get_revision(parent_part_number, parent_revision)
        if not parent or not parent.product_revision_id:
            raise ValueError(f"Parent revision not found: {parent_part_number}/{parent_revision}")
        
        child = await self.get_revision(child_part_number, child_revision)
        if not child or not child.product_revision_id:
            raise ValueError(f"Child revision not found: {child_part_number}/{child_revision}")
        
        result = await self._repository.create_revision_relation(
            parent_revision_id=parent.product_revision_id,
            child_revision_id=child.product_revision_id,
            quantity=quantity,
            revision_mask=revision_mask
        )
        if result:
            logger.info(f"SUBUNIT_ADDED: {child_part_number}/{child_revision} -> {parent_part_number}/{parent_revision}")
        return result

    async def remove_subunit(self, relation_id: UUID) -> bool:
        """
        ⚠️ INTERNAL: Remove a subunit from a product's box build template.

        Args:
            relation_id: The relation ID to remove

        Returns:
            True if successful
        """
        result = await self._repository.delete_revision_relation(relation_id)
        if result:
            logger.info(f"SUBUNIT_REMOVED: relation_id={relation_id}")
        return result

    # =========================================================================
    # ⚠️ INTERNAL API - Product Categories
    # =========================================================================

    async def get_product_categories(self) -> List[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get all product categories.

        Returns:
            List of category dictionaries
        """
        return await self._repository.get_categories()

    async def save_product_categories(self, categories: List[Dict[str, Any]]) -> bool:
        """
        ⚠️ INTERNAL: Save product categories.

        Args:
            categories: List of category dictionaries

        Returns:
            True if successful
        """
        return await self._repository.save_categories(categories)

    # =========================================================================
    # Tags (using product/revision updates)
    # =========================================================================

    async def get_product_tags(self, part_number: str) -> List[Dict[str, str]]:
        """
        Get tags for a product.
        
        Args:
            part_number: Product part number
            
        Returns:
            List of tag dictionaries with 'key' and 'value'
        """
        product = await self.get_product(part_number)
        if product and product.tags:
            return [{"key": t.key, "value": t.value or ""} for t in product.tags]
        return []

    async def set_product_tags(
        self,
        part_number: str,
        tags: List[Dict[str, str]]
    ) -> Optional[Product]:
        """
        Set tags for a product (replaces existing tags).
        
        Args:
            part_number: Product part number
            tags: List of tag dictionaries with 'key' and 'value'
            
        Returns:
            Updated Product or None if not found
        """
        from ...shared import Setting, ChangeType
        product = await self.get_product(part_number)
        if not product:
            return None
        
        product.tags = [
            Setting(key=t["key"], value=t["value"], change=ChangeType.ADD)
            for t in tags
        ]
        return await self.update_product(product)

    async def add_product_tag(
        self,
        part_number: str,
        name: str,
        value: str
    ) -> Optional[Product]:
        """
        Add a single tag to a product.
        
        Args:
            part_number: Product part number
            name: Tag key/name
            value: Tag value
            
        Returns:
            Updated Product or None if not found
        """
        from ...shared import Setting, ChangeType
        product = await self.get_product(part_number)
        if not product:
            return None
        
        if not product.tags:
            product.tags = []
        
        # Check if tag already exists
        for tag in product.tags:
            if tag.key == name:
                tag.value = value
                tag.change = ChangeType.UPDATE
                return await self.update_product(product)
        
        # Add new tag
        product.tags.append(Setting(key=name, value=value, change=ChangeType.ADD))
        return await self.update_product(product)

    async def get_revision_tags(
        self,
        part_number: str,
        revision: str
    ) -> List[Dict[str, str]]:
        """
        Get tags for a product revision.
        
        Args:
            part_number: Product part number
            revision: Revision identifier
            
        Returns:
            List of tag dictionaries
        """
        rev = await self.get_revision(part_number, revision)
        if rev and rev.tags:
            return [{"key": t.key, "value": t.value or ""} for t in rev.tags]
        return []

    async def set_revision_tags(
        self,
        part_number: str,
        revision: str,
        tags: List[Dict[str, str]]
    ) -> Optional[ProductRevision]:
        """
        Set tags for a product revision.
        
        Args:
            part_number: Product part number
            revision: Revision identifier
            tags: List of tag dictionaries
            
        Returns:
            Updated ProductRevision or None if not found
        """
        from ...shared import Setting, ChangeType
        rev = await self.get_revision(part_number, revision)
        if not rev:
            return None
        
        rev.tags = [
            Setting(key=t["key"], value=t["value"], change=ChangeType.ADD)
            for t in tags
        ]
        return await self.update_revision(rev)

    async def add_revision_tag(
        self,
        part_number: str,
        revision: str,
        name: str,
        value: str
    ) -> Optional[ProductRevision]:
        """
        Add a single tag to a product revision.
        
        Args:
            part_number: Product part number
            revision: Revision identifier
            name: Tag key/name
            value: Tag value
            
        Returns:
            Updated ProductRevision or None if not found
        """
        from ...shared import Setting, ChangeType
        rev = await self.get_revision(part_number, revision)
        if not rev:
            return None
        
        if not rev.tags:
            rev.tags = []
        
        # Check if tag already exists
        for tag in rev.tags:
            if tag.key == name:
                tag.value = value
                tag.change = ChangeType.UPDATE
                return await self.update_revision(rev)
        
        # Add new tag
        rev.tags.append(Setting(key=name, value=value, change=ChangeType.ADD))
        return await self.update_revision(rev)

    # =========================================================================
    # ⚠️ INTERNAL API - Vendors
    # =========================================================================

    async def get_vendors(self) -> List[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get all vendors.
        
        Returns:
            List of vendor dictionaries
        """
        return await self._repository.get_vendors()

    async def save_vendor(
        self,
        name: str,
        vendor_id: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Create or update a vendor.
        
        Args:
            name: Vendor name
            vendor_id: Vendor ID for updates
            **kwargs: Additional vendor fields
            
        Returns:
            Saved vendor dictionary or None
        """
        return await self._repository.save_vendor(name, vendor_id, **kwargs)

    async def delete_vendor(self, vendor_id: str) -> bool:
        """
        ⚠️ INTERNAL: Delete a vendor.
        
        Args:
            vendor_id: Vendor ID to delete
            
        Returns:
            True if successful
        """
        return await self._repository.delete_vendor(vendor_id)

    # =========================================================================
    # ⚠️ INTERNAL API - Box Build Template
    # =========================================================================

    async def _load_box_build_relations(
        self, 
        part_number: str, 
        revision: str
    ) -> List[ProductRevisionRelation]:
        """
        Load existing box build relations from server.
        
        ⚠️ INTERNAL API
        
        Uses GetProductInfo which returns the full hierarchy including
        all child relations with their ProductRevisionRelationId.
        
        Args:
            part_number: Product part number
            revision: Product revision
            
        Returns:
            List of ProductRevisionRelation
        """
        hierarchy = await self._repository.get_product_hierarchy(part_number, revision)
        if not hierarchy:
            return []
        
        # Extract child relations (hlevel > 0 with ProductRevisionRelationId)
        relations = []
        for item in hierarchy:
            if item.get("hlevel", 0) > 0 and item.get("ProductRevisionRelationId"):
                try:
                    # Map hierarchy fields to ProductRevisionRelation fields
                    rel_data = {
                        "ProductRevisionRelationId": item.get("ProductRevisionRelationId"),
                        "ParentProductRevisionId": item.get("ParentProductRevisionId"),
                        "ProductRevisionId": item.get("ProductRevisionId"),
                        "Quantity": item.get("Quantity", 1),
                        "RevisionMask": item.get("RevisionMask"),
                        "ChildPartNumber": item.get("PartNumber"),
                        "ChildRevision": item.get("Revision"),
                    }
                    relations.append(ProductRevisionRelation.model_validate(rel_data))
                except Exception as e:
                    logger.debug(f"Skipping invalid product revision relation: {e}")
        
        return relations

    async def get_box_build_template(
        self,
        part_number: str,
        revision: str
    ) -> "AsyncBoxBuildTemplate":
        """
        Get or create a box build template for a product revision.
        
        ⚠️ INTERNAL API
        
        A box build template defines WHAT subunits are required to build a product.
        This is a PRODUCT-LEVEL definition - it does not create production units.
        
        Use the returned AsyncBoxBuildTemplate to add/remove subunits, then call
        save() to persist changes to the server.
        
        Args:
            part_number: Parent product part number
            revision: Parent product revision
            
        Returns:
            AsyncBoxBuildTemplate for managing subunits
            
        Raises:
            ValueError: If product revision not found
        """
        from .async_box_build import AsyncBoxBuildTemplate
        
        # Get the parent revision
        parent_revision = await self.get_revision(part_number, revision)
        if not parent_revision:
            raise ValueError(f"Product revision not found: {part_number}/{revision}")
        
        # Load existing relations
        relations = await self._load_box_build_relations(part_number, revision)
        
        return AsyncBoxBuildTemplate(
            parent_revision=parent_revision,
            service=self,
            existing_relations=relations
        )

    async def get_box_build_subunits(
        self,
        part_number: str,
        revision: str
    ) -> List[ProductRevisionRelation]:
        """
        Get subunits for a box build (read-only).
        
        ⚠️ INTERNAL API
        
        Args:
            part_number: Parent product part number
            revision: Parent product revision
            
        Returns:
            List of ProductRevisionRelation representing subunits
        """
        return await self._load_box_build_relations(part_number, revision)

    async def get_groups_for_product(
        self,
        part_number: str
    ) -> List[ProductGroup]:
        """
        Get product groups that contain a specific product.
        
        Args:
            part_number: Product part number
            
        Returns:
            List of ProductGroup objects containing this product
        """
        product = await self.get_product(part_number)
        if not product:
            return []
        return await self._repository.get_groups_for_product(part_number)

    async def get_bom_items(
        self,
        part_number: str,
        revision: str
    ) -> List[BomItem]:
        """
        ⚠️ INTERNAL: Get BOM items (alias for get_bom).
        
        Args:
            part_number: Product part number
            revision: Revision identifier
            
        Returns:
            List of BomItem objects
        """
        return await self.get_bom(part_number, revision)

    async def update_bom(
        self,
        part_number: str,
        revision: str,
        bom_items: List[BomItem],
        description: Optional[str] = None
    ) -> bool:
        """
        Update product BOM (Bill of Materials).
        
        Uses the public API which accepts WSBF (WATS Standard BOM Format) XML.
        
        Args:
            part_number: Product part number
            revision: Revision identifier
            bom_items: List of BomItem objects
            description: Optional product description
            
        Returns:
            True if successful
        """
        result = await self._repository.update_bom(part_number, revision, bom_items, description)
        if result:
            logger.info(f"BOM_UPDATED: {part_number}/{revision} (items={len(bom_items)})")
        return result
