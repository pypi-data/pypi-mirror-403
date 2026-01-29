"""Sync Box Build Template wrapper.

Provides a synchronous wrapper around AsyncBoxBuildTemplate for use with pyWATS (sync API).
"""
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

from .models import ProductRevision, ProductRevisionRelation

# Import the shared _run_sync from pywats to use the same event loop
from ...pywats import _run_sync

if TYPE_CHECKING:
    from .async_box_build import AsyncBoxBuildTemplate


class SyncBoxBuildTemplate:
    """
    Synchronous wrapper for AsyncBoxBuildTemplate.
    
    Provides the same interface as AsyncBoxBuildTemplate but runs all
    async operations synchronously. Used by pyWATS (sync API).
    
    Example:
        # Via pyWATS (sync)
        template = api.product.get_box_build_template("MAIN-BOARD", "A")
        template.add_subunit("PCBA-001", "A", quantity=2)
        template.save()
        
        # Or with context manager
        with api.product.get_box_build_template("MAIN-BOARD", "A") as template:
            template.add_subunit("PCBA-001", "A", quantity=2)
    """
    
    def __init__(self, async_template: "AsyncBoxBuildTemplate"):
        """
        Initialize with an async template.
        
        Args:
            async_template: The underlying AsyncBoxBuildTemplate
        """
        self._async = async_template
    
    # =========================================================================
    # Properties (passthrough)
    # =========================================================================
    
    @property
    def parent_part_number(self) -> Optional[str]:
        """Get the parent product part number."""
        return self._async.parent_part_number
    
    @property
    def parent_revision(self) -> str:
        """Get the parent product revision."""
        return self._async.parent_revision
    
    @property
    def parent_revision_id(self) -> Optional[UUID]:
        """Get the parent product revision ID."""
        return self._async.parent_revision_id
    
    @property
    def subunits(self) -> List[ProductRevisionRelation]:
        """Get current subunits."""
        return self._async.subunits
    
    @property
    def has_pending_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self._async.has_pending_changes
    
    # =========================================================================
    # Sync Builder Methods (wrap async)
    # =========================================================================
    
    def add_subunit(
        self,
        part_number: str,
        revision: str,
        quantity: int = 1,
        item_number: Optional[str] = None,
        revision_mask: Optional[str] = None
    ) -> "SyncBoxBuildTemplate":
        """Add a subunit to the box build template."""
        _run_sync(self._async.add_subunit(
            part_number, revision, quantity, item_number, revision_mask
        ))
        return self
    
    def update_subunit(
        self,
        part_number: str,
        revision: str,
        quantity: Optional[int] = None,
        item_number: Optional[str] = None,
        revision_mask: Optional[str] = None
    ) -> "SyncBoxBuildTemplate":
        """Update an existing subunit."""
        _run_sync(self._async.update_subunit(
            part_number, revision, quantity, item_number, revision_mask
        ))
        return self
    
    def remove_subunit(self, part_number: str, revision: str) -> "SyncBoxBuildTemplate":
        """Remove a subunit from the template."""
        _run_sync(self._async.remove_subunit(part_number, revision))
        return self
    
    def clear_all(self) -> "SyncBoxBuildTemplate":
        """Mark all subunits for removal."""
        self._async.clear_all()
        return self
    
    def set_quantity(self, part_number: str, revision: str, quantity: int) -> "SyncBoxBuildTemplate":
        """Set the quantity for a subunit."""
        _run_sync(self._async.set_quantity(part_number, revision, quantity))
        return self
    
    # =========================================================================
    # Save/Commit Operations
    # =========================================================================
    
    def save(self) -> "SyncBoxBuildTemplate":
        """Save all pending changes to the server."""
        _run_sync(self._async.save())
        return self
    
    def discard(self) -> "SyncBoxBuildTemplate":
        """Discard all pending changes."""
        self._async.discard()
        return self
    
    def reload(self) -> "SyncBoxBuildTemplate":
        """Reload relations from server."""
        _run_sync(self._async.reload())
        return self
    
    # =========================================================================
    # Validation Helpers
    # =========================================================================
    
    def validate_subunit(self, part_number: str, revision: str) -> bool:
        """Check if a specific subunit revision is valid."""
        return self._async.validate_subunit(part_number, revision)
    
    def get_matching_subunits(self, part_number: str) -> List[ProductRevisionRelation]:
        """Get all subunit definitions for a given part number."""
        return self._async.get_matching_subunits(part_number)
    
    def get_required_parts(self) -> List[dict]:
        """Get a summary of all required parts."""
        return self._async.get_required_parts()
    
    # =========================================================================
    # Context Manager Support (sync version)
    # =========================================================================
    
    def __enter__(self) -> "SyncBoxBuildTemplate":
        """Enter context manager."""
        return self
    
    def __exit__(
        self, 
        exc_type: Optional[type], 
        exc_val: Optional[BaseException], 
        exc_tb: Optional[object]
    ) -> None:
        """Exit context manager - auto-save if no exception."""
        if exc_type is None and self.has_pending_changes:
            self.save()
    
    # =========================================================================
    # String Representation
    # =========================================================================
    
    def __repr__(self) -> str:
        return (
            f"SyncBoxBuildTemplate(parent='{self.parent_part_number}/{self.parent_revision}', "
            f"subunits={len(self.subunits)}, pending_changes={self.has_pending_changes})"
        )
    
    def __str__(self) -> str:
        return str(self._async)


# Alias for backward compatibility
BoxBuildTemplate = SyncBoxBuildTemplate
