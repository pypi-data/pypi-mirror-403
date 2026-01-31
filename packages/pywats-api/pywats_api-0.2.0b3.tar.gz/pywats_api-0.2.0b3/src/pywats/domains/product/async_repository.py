"""Async Product repository - data access layer.

Async version of the product repository for non-blocking API calls.
Includes both public and internal API methods.
Uses Routes class for centralized endpoint definitions.

⚠️ INTERNAL API methods are marked and may change without notice.
"""
from typing import Optional, List, Dict, Any, Union, Sequence, TYPE_CHECKING
from uuid import UUID
import logging
import xml.etree.ElementTree as ET

from ...core.routes import Routes

if TYPE_CHECKING:
    from ...core.async_client import AsyncHttpClient
    from ...core.exceptions import ErrorHandler

from .models import Product, ProductRevision, ProductGroup, BomItem, ProductRevisionRelation

logger = logging.getLogger(__name__)


class AsyncProductRepository:
    """
    Async Product data access layer.

    Handles all async WATS API interactions for products.
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
        """
        ⚠️ INTERNAL: Make an internal API GET request with Referer header.
        """
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
        operation: str = "internal_post"
    ) -> Any:
        """
        ⚠️ INTERNAL: Make an internal API POST request with Referer header.
        """
        response = await self._http_client.post(
            endpoint,
            data=data,
            params=params,
            headers={"Referer": self._base_url}
        )
        return self._error_handler.handle_response(
            response, operation=operation, allow_empty=True
        )

    async def _internal_put(
        self, 
        endpoint: str, 
        data: Any = None, 
        params: Optional[Dict[str, Any]] = None,
        operation: str = "internal_put"
    ) -> Any:
        """
        ⚠️ INTERNAL: Make an internal API PUT request with Referer header.
        """
        response = await self._http_client.put(
            endpoint,
            data=data,
            params=params,
            headers={"Referer": self._base_url}
        )
        return self._error_handler.handle_response(
            response, operation=operation, allow_empty=True
        )

    async def _internal_delete(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        operation: str = "internal_delete"
    ) -> bool:
        """
        ⚠️ INTERNAL: Make an internal API DELETE request with Referer header.
        """
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
    # Product CRUD
    # =========================================================================

    async def get_all(self) -> List[Product]:
        """
        Get all products.

        GET /api/Product/Query
        """
        logger.debug("Fetching all products")
        response = await self._http_client.get(Routes.Product.QUERY)
        data = self._error_handler.handle_response(
            response, operation="get_all", allow_empty=True
        )
        if data:
            products = [Product.model_validate(item) for item in data]
            logger.info(f"Retrieved {len(products)} products")
            return products
        return []

    async def get_by_part_number(self, part_number: str) -> Optional[Product]:
        """
        Get a product by part number.

        GET /api/Product/{partNumber}
        """
        logger.debug(f"Fetching product: {part_number}")
        response = await self._http_client.get(Routes.Product.product(part_number))
        data = self._error_handler.handle_response(
            response, 
            operation=f"get_by_part_number('{part_number}')"
        )
        if data is None:
            logger.info(f"Product not found: {part_number}")
            return None
        product = Product.model_validate(data)
        logger.info(f"Retrieved product: {part_number} ({product.name})")
        return product

    async def save(
        self, product: Union[Product, Dict[str, Any]]
    ) -> Optional[Product]:
        """
        Create or update a product.

        PUT /api/Product
        """
        if isinstance(product, Product):
            payload = product.model_dump(by_alias=True, exclude_none=True, mode='json')
        else:
            payload = product
        response = await self._http_client.put(Routes.Product.BASE, data=payload)
        data = self._error_handler.handle_response(
            response, operation="save", allow_empty=False
        )
        if data:
            return Product.model_validate(data)
        return None

    async def save_bulk(
        self, products: Sequence[Union[Product, Dict[str, Any]]]
    ) -> List[Product]:
        """
        Bulk create or update products.

        PUT /api/Product/Products
        """
        payload = [
            p.model_dump(by_alias=True, exclude_none=True, mode='json')
            if isinstance(p, Product) else p
            for p in products
        ]
        response = await self._http_client.put(Routes.Product.PRODUCTS, data=payload)
        data = self._error_handler.handle_response(
            response, operation="save_bulk", allow_empty=True
        )
        if data:
            return [Product.model_validate(item) for item in data]
        return []

    # =========================================================================
    # Revision Operations
    # =========================================================================

    async def get_revision(
        self, part_number: str, revision: str
    ) -> Optional[ProductRevision]:
        """
        Get a specific product revision.

        GET /api/Product?partNumber={partNumber}&revision={revision}
        """
        response = await self._http_client.get(
            Routes.Product.BASE, 
            params={"partNumber": part_number, "revision": revision}
        )
        data = self._error_handler.handle_response(
            response, operation="get_revision", allow_empty=True
        )
        if data:
            return ProductRevision.model_validate(data)
        return None

    async def save_revision(
        self, revision: Union[ProductRevision, Dict[str, Any]]
    ) -> Optional[ProductRevision]:
        """
        Create or update a product revision.

        PUT /api/Product/Revision
        """
        if isinstance(revision, ProductRevision):
            payload = revision.model_dump(mode="json", by_alias=True, exclude_none=True)
        else:
            payload = revision
        response = await self._http_client.put(Routes.Product.REVISION, data=payload)
        data = self._error_handler.handle_response(
            response, operation="save_revision", allow_empty=False
        )
        if data:
            return ProductRevision.model_validate(data)
        return None

    async def save_revisions_bulk(
        self, revisions: Sequence[Union[ProductRevision, Dict[str, Any]]]
    ) -> List[ProductRevision]:
        """
        Bulk create or update product revisions.

        PUT /api/Product/Revisions
        """
        payload = [
            r.model_dump(by_alias=True, exclude_none=True, mode='json')
            if isinstance(r, ProductRevision) else r
            for r in revisions
        ]
        response = await self._http_client.put(Routes.Product.REVISIONS, data=payload)
        data = self._error_handler.handle_response(
            response, operation="save_revisions_bulk", allow_empty=True
        )
        if data:
            return [ProductRevision.model_validate(item) for item in data]
        return []

    # =========================================================================
    # Product Groups
    # =========================================================================

    async def get_groups(self) -> List[ProductGroup]:
        """
        Get all product groups.

        GET /api/Product/Groups
        """
        response = await self._http_client.get(Routes.Product.GROUPS)
        data = self._error_handler.handle_response(
            response, operation="get_groups", allow_empty=True
        )
        if data:
            return [ProductGroup.model_validate(item) for item in data]
        return []

    async def save_group(
        self, group: Union[ProductGroup, Dict[str, Any]]
    ) -> Optional[ProductGroup]:
        """
        Create or update a product group.

        PUT /api/Product/Group
        """
        if isinstance(group, ProductGroup):
            payload = group.model_dump(by_alias=True, exclude_none=True, mode='json')
        else:
            payload = group
        response = await self._http_client.put(Routes.Product.GROUP, data=payload)
        data = self._error_handler.handle_response(
            response, operation="save_group", allow_empty=False
        )
        if data:
            return ProductGroup.model_validate(data)
        return None

    # =========================================================================
    # ⚠️ INTERNAL API - BOM Operations
    # =========================================================================

    async def get_bom(self, part_number: str, revision: str) -> List[BomItem]:
        """
        ⚠️ INTERNAL: Get BOM (Bill of Materials) for a product revision.
        
        GET /api/internal/Product/Bom
        """
        data = await self._internal_get(
            Routes.Product.Internal.BOM,
            params={"partNumber": part_number, "revision": revision},
            operation="get_bom"
        )
        if data and isinstance(data, list):
            return [BomItem.model_validate(item) for item in data]
        return []

    async def upload_bom(
        self,
        part_number: str,
        revision: str,
        bom_items: List[Dict[str, Any]],
        format: str = "json"
    ) -> bool:
        """
        ⚠️ INTERNAL: Upload/update BOM items.
        
        PUT /api/internal/Product/BOM
        """
        result = await self._internal_put(
            Routes.Product.Internal.BOM_UPLOAD,
            data=bom_items,
            params={
                "partNumber": part_number,
                "revision": revision,
                "format": format
            },
            operation="upload_bom"
        )
        return result is not None

    async def update_bom(
        self,
        part_number: str,
        revision: str,
        bom_items: List[BomItem],
        description: Optional[str] = None
    ) -> bool:
        """
        Update product BOM (Bill of Materials) using WSBF XML format.

        PUT /api/Product/BOM

        The public API uses WSBF (WATS Standard BOM Format) XML.
        Example:
            <BOM xmlns="http://wats.virinco.com/schemas/WATS/wsbf"
                 Partnumber="100100" Revision="1.0" Desc="Product Description">
                <Component Number="100200" Rev="1.0" Qty="2" Desc="Description" Ref="R1;R2"/>
            </BOM>

        Args:
            part_number: Product part number
            revision: Product revision
            bom_items: List of BomItem objects
            description: Optional product description

        Returns:
            True if successful
        """
        xml_content = self._generate_wsbf_xml(part_number, revision, bom_items, description)

        # Send as XML with proper content type
        response = await self._http_client.put(
            Routes.Product.BOM,
            data=xml_content,
            headers={"Content-Type": "application/xml"}
        )
        self._error_handler.handle_response(
            response, operation="update_bom", allow_empty=True
        )
        return response.is_success

    def _generate_wsbf_xml(
        self,
        part_number: str,
        revision: str,
        bom_items: List[BomItem],
        description: Optional[str] = None
    ) -> str:
        """
        Generate WSBF (WATS Standard BOM Format) XML.

        Args:
            part_number: Product part number
            revision: Product revision
            bom_items: List of BomItem objects
            description: Optional product description

        Returns:
            WSBF XML string
        """
        root = ET.Element("BOM", attrib={
            "xmlns": "http://wats.virinco.com/schemas/WATS/wsbf",
            "Partnumber": part_number,
            "Revision": revision
        })

        if description:
            root.set("Desc", description)

        # Add Component elements for each BOM item
        for item in bom_items:
            comp_attrib: Dict[str, str] = {}

            # Required: Number (part number)
            if item.part_number:
                comp_attrib["Number"] = item.part_number

            # Optional attributes
            if item.component_ref:
                comp_attrib["Ref"] = item.component_ref

            if item.quantity:
                comp_attrib["Qty"] = str(item.quantity)

            if item.description:
                comp_attrib["Desc"] = item.description

            # Add revision if we can get it (from manufacturer_pn as fallback)
            # The WSBF format uses "Rev" for component revision
            if item.manufacturer_pn:
                comp_attrib["Rev"] = item.manufacturer_pn

            ET.SubElement(root, "Component", attrib=comp_attrib)

        # Generate XML string
        return ET.tostring(root, encoding="unicode")

    # =========================================================================
    # ⚠️ INTERNAL API - Product Hierarchy
    # =========================================================================

    async def get_product_hierarchy(
        self,
        part_number: str,
        revision: str
    ) -> List[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get product hierarchy including all child revision relations.
        
        GET /api/internal/Product/GetProductInfo
        """
        data = await self._internal_get(
            Routes.Product.Internal.GET_PRODUCT_INFO,
            params={"partNumber": part_number, "revision": revision},
            operation="get_product_hierarchy"
        )
        return data if isinstance(data, list) else []

    async def get_product_with_relations(
        self, 
        part_number: str, 
        revision: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get product with revision relations (box build template).
        
        GET /api/internal/Product/GetProductByPN
        
        NOTE: This endpoint does NOT return ChildProductRevisionRelations.
        Use get_product_hierarchy() instead for box build relations.
        
        Args:
            part_number: Product part number
            revision: Optional specific revision to filter
            
        Returns:
            Product data with relations or None
        """
        return await self._internal_get(
            Routes.Product.Internal.GET_PRODUCT_BY_PN,
            params={"PN": part_number},
            operation="get_product_with_relations"
        )

    # =========================================================================
    # ⚠️ INTERNAL API - Product Revision Relations
    # =========================================================================

    async def create_revision_relation(
        self,
        parent_revision_id: UUID,
        child_revision_id: UUID,
        quantity: int = 1,
        revision_mask: Optional[str] = None
    ) -> Optional[ProductRevisionRelation]:
        """
        ⚠️ INTERNAL: Create a product revision relation (add subunit to box build).
        
        POST /api/internal/Product/PostProductRevisionRelation
        """
        data = {
            "ParentProductRevisionId": str(parent_revision_id),
            "ProductRevisionId": str(child_revision_id),
            "Quantity": quantity,
        }
        if revision_mask:
            data["RevisionMask"] = revision_mask
            
        result = await self._internal_post(
            Routes.Product.Internal.POST_REVISION_RELATION,
            data=data,
            operation="create_revision_relation"
        )
        
        if result and isinstance(result, list):
            for item in result:
                if (item.get("ProductRevisionId") == str(child_revision_id) and 
                    item.get("ParentProductRevisionId") == str(parent_revision_id) and
                    item.get("ProductRevisionRelationId")):
                    return ProductRevisionRelation.model_validate(item)
            return None
        elif result:
            return ProductRevisionRelation.model_validate(result)
        return None

    async def update_revision_relation(
        self,
        relation: ProductRevisionRelation
    ) -> Optional[ProductRevisionRelation]:
        """
        ⚠️ INTERNAL: Update a product revision relation.
        
        PUT /api/internal/Product/PutProductRevisionRelation
        """
        payload = relation.model_dump(by_alias=True, exclude_none=True, mode='json')
        result = await self._internal_put(
            Routes.Product.Internal.PUT_REVISION_RELATION,
            data=payload,
            operation="update_revision_relation"
        )
        if result:
            return ProductRevisionRelation.model_validate(result)
        return None

    async def delete_revision_relation(self, relation_id: UUID) -> bool:
        """
        ⚠️ INTERNAL: Delete a product revision relation.
        
        DELETE /api/internal/Product/DeleteProductRevisionRelation
        """
        return await self._internal_delete(
            Routes.Product.Internal.DELETE_REVISION_RELATION,
            params={"productRevisionRelationId": str(relation_id)},
            operation="delete_revision_relation"
        )

    # =========================================================================
    # ⚠️ INTERNAL API - Product Categories
    # =========================================================================

    async def get_categories(self) -> List[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get all product categories.
        
        GET /api/internal/Product/GetProductCategories
        """
        data = await self._internal_get(
            Routes.Product.Internal.GET_CATEGORIES,
            operation="get_categories"
        )
        if data and isinstance(data, list):
            return data
        return []

    async def save_categories(self, categories: List[Dict[str, Any]]) -> bool:
        """
        ⚠️ INTERNAL: Save product categories.
        
        PUT /api/internal/Product/PutProductCategories
        """
        result = await self._internal_put(
            Routes.Product.Internal.PUT_CATEGORIES,
            data=categories,
            operation="save_categories"
        )
        return result is not None

    # =========================================================================
    # ⚠️ INTERNAL API - Product Tags
    # =========================================================================

    async def get_product_tags(self, part_number: str) -> List[Dict[str, str]]:
        """
        ⚠️ INTERNAL: Get tags for a product.
        
        GET /api/internal/Product/GetProductTags
        """
        data = await self._internal_get(
            Routes.Product.Internal.GET_PRODUCT_TAGS,
            params={"partNumber": part_number},
            operation="get_product_tags"
        )
        if data and isinstance(data, list):
            return data
        return []

    async def set_product_tags(
        self,
        part_number: str,
        tags: List[Dict[str, str]]
    ) -> bool:
        """
        ⚠️ INTERNAL: Set tags for a product.
        
        PUT /api/internal/Product/PutProductTags
        """
        result = await self._internal_put(
            Routes.Product.Internal.PUT_PRODUCT_TAGS,
            data=tags,
            params={"partNumber": part_number},
            operation="set_product_tags"
        )
        return result is not None

    async def get_revision_tags(
        self,
        part_number: str,
        revision: str
    ) -> List[Dict[str, str]]:
        """
        ⚠️ INTERNAL: Get tags for a product revision.
        
        GET /api/internal/Product/GetRevisionTags
        """
        data = await self._internal_get(
            Routes.Product.Internal.GET_REVISION_TAGS,
            params={"partNumber": part_number, "revision": revision},
            operation="get_revision_tags"
        )
        if data and isinstance(data, list):
            return data
        return []

    async def set_revision_tags(
        self,
        part_number: str,
        revision: str,
        tags: List[Dict[str, str]]
    ) -> bool:
        """
        ⚠️ INTERNAL: Set tags for a product revision.
        
        PUT /api/internal/Product/PutRevisionTags
        """
        result = await self._internal_put(
            Routes.Product.Internal.PUT_REVISION_TAGS,
            data=tags,
            params={"partNumber": part_number, "revision": revision},
            operation="set_revision_tags"
        )
        return result is not None

    # =========================================================================
    # Vendors (Public API)
    # =========================================================================

    async def get_vendors(self) -> List[Dict[str, Any]]:
        """
        Get all vendors.
        
        GET /api/Product/Vendors
        """
        response = await self._http_client.get(Routes.Product.VENDORS)
        data = self._error_handler.handle_response(
            response, operation="get_vendors", allow_empty=True
        )
        if data and isinstance(data, list):
            return data
        return []

    async def save_vendor(
        self,
        name: str,
        vendor_id: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Create or update a vendor.
        
        PUT /api/Product/Vendors
        """
        payload = {"name": name, **kwargs}
        if vendor_id:
            payload["vendorId"] = vendor_id
        
        response = await self._http_client.put(Routes.Product.VENDORS, data=payload)
        data = self._error_handler.handle_response(
            response, operation="save_vendor", allow_empty=False
        )
        return data

    async def delete_vendor(self, vendor_id: str) -> bool:
        """
        Delete a vendor.
        
        DELETE /api/Product/Vendors/{vendorId}
        """
        response = await self._http_client.delete(Routes.Product.vendor(vendor_id))
        self._error_handler.handle_response(
            response, operation="delete_vendor", allow_empty=True
        )
        return response.is_success

    # =========================================================================
    # ⚠️ INTERNAL API - Product Hierarchy / Box Build Template
    # =========================================================================

    async def get_product_hierarchy(
        self,
        part_number: str,
        revision: str
    ) -> List[Dict[str, Any]]:
        """
        Get product hierarchy including all child revision relations.
        
        ⚠️ INTERNAL API - uses /api/internal/Product/GetProductInfo
        
        This returns the full product tree including:
        - The parent product at hlevel=0
        - All child relations at hlevel=1+ with ProductRevisionRelationId
        
        Args:
            part_number: Product part number
            revision: Product revision
            
        Returns:
            List of hierarchy items. Each item includes:
            - PartNumber, Revision, ProductRevisionId
            - ParentProductRevisionId, ProductRevisionRelationId (for children)
            - hlevel (0=parent, 1+=children)
            - Quantity, RevisionMask
        """
        data = await self._internal_get(
            Routes.Product.Internal.GET_PRODUCT_INFO,
            params={"partNumber": part_number, "revision": revision},
            operation="get_product_hierarchy"
        )
        return data if isinstance(data, list) else []

    async def get_product_with_relations(
        self, 
        part_number: str, 
        revision: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get product with revision relations (box build template).
        
        ⚠️ INTERNAL API - uses /api/internal/Product/GetProductByPN
        
        NOTE: This endpoint does NOT return ChildProductRevisionRelations.
        Use get_product_hierarchy() instead for box build relations.
        
        Args:
            part_number: Product part number
            revision: Optional specific revision to filter
            
        Returns:
            Product data with relations or None
        """
        data = await self._internal_get(
            Routes.Product.Internal.GET_PRODUCT_BY_PN,
            params={"PN": part_number},
            operation="get_product_with_relations"
        )
        return data

    async def create_revision_relation(
        self,
        parent_revision_id: UUID,
        child_revision_id: UUID,
        quantity: int = 1,
        item_number: Optional[str] = None,
        revision_mask: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a product revision relation (add subunit to box build).
        
        ⚠️ INTERNAL API - uses POST /api/internal/Product/PostProductRevisionRelation
        
        Args:
            parent_revision_id: Parent product revision ID
            child_revision_id: Child product revision ID
            quantity: Number of child units required
            item_number: Optional item/position number
            revision_mask: Optional revision mask pattern (comma-separated, % wildcard)
            
        Returns:
            Created relation data or None
        """
        data = {
            "ParentProductRevisionId": str(parent_revision_id),
            "ProductRevisionId": str(child_revision_id),
            "Quantity": quantity,
        }
        if revision_mask:
            data["RevisionMask"] = revision_mask
            
        result = await self._internal_post(
            Routes.Product.Internal.POST_REVISION_RELATION,
            data=data,
            operation="create_revision_relation"
        )
        
        # API returns the full hierarchy as a list, find the newly created relation
        if result and isinstance(result, list):
            for item in result:
                if (item.get("ProductRevisionId") == str(child_revision_id) and 
                    item.get("ParentProductRevisionId") == str(parent_revision_id) and
                    item.get("ProductRevisionRelationId")):
                    return item
            return None
        return result

    async def update_revision_relation(
        self,
        relation_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a product revision relation.
        
        ⚠️ INTERNAL API - uses PUT /api/internal/Product/PutProductRevisionRelation
        
        Args:
            relation_data: Relation data dict with updated values
            
        Returns:
            Updated relation data or None
        """
        result = await self._internal_put(
            Routes.Product.Internal.PUT_REVISION_RELATION,
            data=relation_data,
            operation="update_revision_relation"
        )
        return result

    async def delete_revision_relation(self, relation_id: UUID) -> bool:
        """
        Delete a product revision relation.
        
        ⚠️ INTERNAL API - uses DELETE /api/internal/Product/DeleteProductRevisionRelation
        
        Args:
            relation_id: The relation ID to delete
            
        Returns:
            True if successful
        """
        return await self._internal_delete(
            Routes.Product.Internal.DELETE_REVISION_RELATION,
            params={"productRevisionRelationId": str(relation_id)},
            operation="delete_revision_relation"
        )

    async def get_groups_for_product(
        self,
        part_number: str
    ) -> List[ProductGroup]:
        """
        ⚠️ INTERNAL: Get groups that contain a specific product.
        
        GET /api/internal/Product/GetGroupsForProduct
        """
        data = await self._internal_get(
            Routes.Product.Internal.GET_GROUPS_FOR_PRODUCT,
            params={"partNumber": part_number},
            operation="get_groups_for_product"
        )
        if data and isinstance(data, list):
            return [ProductGroup.model_validate(item) for item in data]
        return []
