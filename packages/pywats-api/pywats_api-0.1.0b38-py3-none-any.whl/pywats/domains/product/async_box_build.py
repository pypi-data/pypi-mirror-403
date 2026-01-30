"""Async Box Build Template management.

Async version of box_build.py for use with AsyncProductService.

See box_build.py for detailed documentation on the Box Build concept.
"""
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

from .models import ProductRevision, ProductRevisionRelation

if TYPE_CHECKING:
    from .async_service import AsyncProductService


class AsyncBoxBuildTemplate:
    """
    Async builder class for managing box build templates (product-level definitions).
    
    This is the async version of BoxBuildTemplate for use with the async API.
    
    A box build template defines the subunits required to build a parent product.
    For example, a controller module may require 2 PCBAs, 1 power supply, etc.
    
    This class provides a fluent interface for adding/removing subunits and
    commits all changes to the server when save() is called.
    
    Example:
        # Get or create a box build template
        template = await api.product.get_box_build_template("MAIN-BOARD", "A")
        
        # Add subunits (defines what's needed)
        await template.add_subunit("PCBA-001", "A", quantity=2)
        await template.add_subunit("PSU-100", "B", quantity=1)
        
        # Remove a subunit
        await template.remove_subunit("OLD-PART", "A")
        
        # Save all changes
        await template.save()
        
        # Or use async context manager for auto-save
        async with await api.product.get_box_build_template("MAIN-BOARD", "A") as template:
            await template.add_subunit("PCBA-001", "A", quantity=2)
        # Changes saved automatically
    """
    
    def __init__(
        self,
        parent_revision: ProductRevision,
        service: "AsyncProductService",
        existing_relations: Optional[List[ProductRevisionRelation]] = None
    ) -> None:
        """
        Initialize box build template.
        
        Args:
            parent_revision: The parent product revision
            service: AsyncProductService for API operations
            existing_relations: Existing relations loaded from server
        """
        self._parent = parent_revision
        self._service = service
        
        # Track current state
        self._relations: List[ProductRevisionRelation] = list(existing_relations or [])
        
        # Track pending changes
        self._to_add: List[ProductRevisionRelation] = []
        self._to_update: List[ProductRevisionRelation] = []
        self._to_delete: List[UUID] = []
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def parent_part_number(self) -> Optional[str]:
        """Get the parent product part number."""
        return self._parent.part_number
    
    @property
    def parent_revision(self) -> str:
        """Get the parent product revision."""
        return self._parent.revision
    
    @property
    def parent_revision_id(self) -> Optional[UUID]:
        """Get the parent product revision ID."""
        return self._parent.product_revision_id
    
    @property
    def subunits(self) -> List[ProductRevisionRelation]:
        """
        Get current subunits (including pending additions, excluding pending deletions).
        
        Returns:
            List of ProductRevisionRelation representing subunits
        """
        current = [r for r in self._relations if r.relation_id not in self._to_delete]
        return current + self._to_add
    
    @property
    def has_pending_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return bool(self._to_add or self._to_update or self._to_delete)
    
    # =========================================================================
    # Async Fluent Builder Methods
    # =========================================================================
    
    async def add_subunit(
        self,
        part_number: str,
        revision: str,
        quantity: int = 1,
        item_number: Optional[str] = None,
        revision_mask: Optional[str] = None
    ) -> "AsyncBoxBuildTemplate":
        """
        Add a subunit to the box build template.
        
        Args:
            part_number: Subunit part number
            revision: Subunit revision (default revision for the subunit)
            quantity: Number of subunits required (default: 1)
            item_number: Optional item/position number
            revision_mask: Optional revision mask pattern
            
        Returns:
            Self for method chaining
        """
        # Get the child revision ID
        child_revision = await self._service.get_revision(part_number, revision)
        if not child_revision or not child_revision.product_revision_id:
            raise ValueError(f"Product revision not found: {part_number}/{revision}")
        
        if not self._parent.product_revision_id:
            raise ValueError("Parent product revision ID is not set")
        
        # Check if already exists
        for rel in self.subunits:
            if rel.child_product_revision_id == child_revision.product_revision_id:
                # Update quantity instead of adding duplicate
                return await self.update_subunit(
                    part_number, revision, 
                    quantity=quantity, 
                    item_number=item_number,
                    revision_mask=revision_mask
                )
        
        # Create new relation with revision mask
        relation = ProductRevisionRelation(
            parent_product_revision_id=self._parent.product_revision_id,
            child_product_revision_id=child_revision.product_revision_id,
            quantity=quantity,
            item_number=item_number,
            child_part_number=part_number,
            child_revision=revision,
            revision_mask=revision_mask
        )
        self._to_add.append(relation)
        
        return self
    
    async def update_subunit(
        self,
        part_number: str,
        revision: str,
        quantity: Optional[int] = None,
        item_number: Optional[str] = None,
        revision_mask: Optional[str] = None
    ) -> "AsyncBoxBuildTemplate":
        """
        Update an existing subunit in the box build template.
        
        Args:
            part_number: Subunit part number
            revision: Subunit revision
            quantity: New quantity (if provided)
            item_number: New item number (if provided)
            revision_mask: New revision mask pattern (if provided)
            
        Returns:
            Self for method chaining
        """
        # Find existing relation
        for rel in self._relations:
            if rel.child_part_number == part_number and rel.child_revision == revision:
                if quantity is not None:
                    rel.quantity = quantity
                if item_number is not None:
                    rel.item_number = item_number
                if revision_mask is not None:
                    rel.revision_mask = revision_mask
                if rel not in self._to_update:
                    self._to_update.append(rel)
                return self
        
        # Check pending additions
        for rel in self._to_add:
            if rel.child_part_number == part_number and rel.child_revision == revision:
                if quantity is not None:
                    rel.quantity = quantity
                if item_number is not None:
                    rel.item_number = item_number
                if revision_mask is not None:
                    rel.revision_mask = revision_mask
                return self
        
        raise ValueError(f"Subunit not found: {part_number}/{revision}")
    
    async def remove_subunit(self, part_number: str, revision: str) -> "AsyncBoxBuildTemplate":
        """
        Remove a subunit from the box build template.
        
        Args:
            part_number: Subunit part number
            revision: Subunit revision
            
        Returns:
            Self for method chaining
        """
        # Check existing relations
        for rel in self._relations:
            if rel.child_part_number == part_number and rel.child_revision == revision:
                if rel.relation_id:
                    self._to_delete.append(rel.relation_id)
                # Remove from update list if present
                if rel in self._to_update:
                    self._to_update.remove(rel)
                return self
        
        # Check pending additions
        for rel in self._to_add:
            if rel.child_part_number == part_number and rel.child_revision == revision:
                self._to_add.remove(rel)
                return self
        
        raise ValueError(f"Subunit not found: {part_number}/{revision}")
    
    def clear_all(self) -> "AsyncBoxBuildTemplate":
        """
        Mark all subunits for removal.
        
        Returns:
            Self for method chaining
        """
        for rel in self._relations:
            if rel.relation_id:
                self._to_delete.append(rel.relation_id)
        self._to_add.clear()
        self._to_update.clear()
        return self
    
    async def set_quantity(self, part_number: str, revision: str, quantity: int) -> "AsyncBoxBuildTemplate":
        """
        Set the quantity for a subunit.
        
        Args:
            part_number: Subunit part number
            revision: Subunit revision
            quantity: New quantity
            
        Returns:
            Self for method chaining
        """
        return await self.update_subunit(part_number, revision, quantity=quantity)
    
    # =========================================================================
    # Save/Commit Operations
    # =========================================================================
    
    async def save(self) -> "AsyncBoxBuildTemplate":
        """
        Save all pending changes to the server.
        
        Performs all additions, updates, and deletions in order.
        
        Returns:
            Self for method chaining
        """
        # Process deletions first
        for relation_id in self._to_delete:
            await self._service._repository.delete_revision_relation(relation_id)
        
        # Remove deleted relations from our list
        self._relations = [r for r in self._relations if r.relation_id not in self._to_delete]
        self._to_delete.clear()
        
        # Process updates
        for relation in self._to_update:
            payload = relation.model_dump(by_alias=True, exclude_none=True, mode='json')
            updated_data = await self._service._repository.update_revision_relation(payload)
            if updated_data:
                updated = ProductRevisionRelation.model_validate(updated_data)
                idx = next((i for i, r in enumerate(self._relations) if r.relation_id == updated.relation_id), None)
                if idx is not None:
                    self._relations[idx] = updated
        self._to_update.clear()
        
        # Process additions
        for relation in self._to_add:
            created_data = await self._service._repository.create_revision_relation(
                parent_revision_id=relation.parent_product_revision_id,
                child_revision_id=relation.child_product_revision_id,
                quantity=relation.quantity,
                item_number=relation.item_number,
                revision_mask=relation.revision_mask
            )
            if created_data:
                created = ProductRevisionRelation.model_validate(created_data)
                self._relations.append(created)
        self._to_add.clear()
        
        return self
    
    def discard(self) -> "AsyncBoxBuildTemplate":
        """
        Discard all pending changes.
        
        Returns:
            Self for method chaining
        """
        self._to_add.clear()
        self._to_update.clear()
        self._to_delete.clear()
        return self
    
    async def reload(self) -> "AsyncBoxBuildTemplate":
        """
        Reload relations from server, discarding pending changes.
        
        Returns:
            Self for method chaining
        """
        self.discard()
        self._relations = await self._service._load_box_build_relations(
            self._parent.part_number or "",
            self._parent.revision
        )
        return self
    
    # =========================================================================
    # Validation Helpers
    # =========================================================================
    
    def validate_subunit(self, part_number: str, revision: str) -> bool:
        """
        Check if a specific subunit revision is valid for this box build.
        
        Args:
            part_number: The part number to validate
            revision: The revision to validate
            
        Returns:
            True if the subunit/revision combination is valid
        """
        for rel in self.subunits:
            if rel.child_part_number == part_number:
                return rel.matches_revision(revision)
        return False
    
    def get_matching_subunits(self, part_number: str) -> List[ProductRevisionRelation]:
        """
        Get all subunit definitions for a given part number.
        
        Args:
            part_number: The part number to search for
            
        Returns:
            List of matching ProductRevisionRelation objects
        """
        return [rel for rel in self.subunits if rel.child_part_number == part_number]
    
    def get_required_parts(self) -> List[dict]:
        """
        Get a summary of all required parts for this box build.
        
        Returns:
            List of dicts with part_number, default_revision, quantity, revision_mask
        """
        return [
            {
                "part_number": rel.child_part_number,
                "default_revision": rel.child_revision,
                "quantity": rel.quantity,
                "revision_mask": rel.revision_mask,
                "item_number": rel.item_number
            }
            for rel in self.subunits
        ]
    
    # =========================================================================
    # Async Context Manager Support
    # =========================================================================
    
    async def __aenter__(self) -> "AsyncBoxBuildTemplate":
        """Enter async context manager."""
        return self
    
    async def __aexit__(
        self, 
        exc_type: Optional[type], 
        exc_val: Optional[BaseException], 
        exc_tb: Optional[object]
    ) -> None:
        """Exit async context manager - auto-save if no exception."""
        if exc_type is None and self.has_pending_changes:
            await self.save()
    
    # =========================================================================
    # String Representation
    # =========================================================================
    
    def __repr__(self) -> str:
        return (
            f"AsyncBoxBuildTemplate(parent='{self.parent_part_number}/{self.parent_revision}', "
            f"subunits={len(self.subunits)}, pending_changes={self.has_pending_changes})"
        )
    
    def __str__(self) -> str:
        lines = [f"Box Build: {self.parent_part_number}/{self.parent_revision}"]
        lines.append(f"Subunits ({len(self.subunits)}):")
        for sub in self.subunits:
            mask_info = f" [mask: {sub.revision_mask}]" if sub.revision_mask else ""
            lines.append(f"  - {sub.child_part_number}/{sub.child_revision} x{sub.quantity}{mask_info}")
        if self.has_pending_changes:
            lines.append(f"Pending: +{len(self._to_add)} ~{len(self._to_update)} -{len(self._to_delete)}")
        return "\n".join(lines)


# Alias for compatibility with sync code
BoxBuildTemplate = AsyncBoxBuildTemplate
