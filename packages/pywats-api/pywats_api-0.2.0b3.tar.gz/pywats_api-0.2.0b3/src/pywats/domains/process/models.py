"""Process domain models.

Models for test operations and repair operations.
"""
from typing import Optional, List, Any, NamedTuple
from uuid import UUID
from pydantic import Field

from ...shared.base_model import PyWATSModel


class FailureCodeInfo(NamedTuple):
    """Flattened failure code info for easy lookup."""
    category: str
    """Category name (e.g., "Component", "Assembly Process")"""
    code: str
    """Failure code description (e.g., "Defect Component")"""
    guid: UUID
    """Unique identifier for the fail code"""
    category_guid: UUID
    """GUID of the parent category"""


class ProcessInfo(PyWATSModel):
    """
    Process/operation information.

    Processes define the types of operations that can be performed:
    - Test operations (isTestOperation=true): End of line test, PCBA test, etc.
    - Repair operations (isRepairOperation=true): Repair, RMA repair, etc.
    - WIP operations (isWipOperation=true): Work-in-progress tracking

    Attributes:
        code: Process code (e.g., 100, 500)
        name: Process name (e.g., "End of line test", "Repair")
        description: Process description
        process_id: Process GUID (internal API only)
        is_test_operation: True if this is a test operation
        is_repair_operation: True if this is a repair operation
        is_wip_operation: True if this is a WIP operation
        process_index: Process order index
        state: Process state (1=active)
    """
    # Core fields (available from public API)
    code: Optional[int] = Field(default=None, validation_alias="code", serialization_alias="code")
    name: Optional[str] = Field(default=None, validation_alias="name", serialization_alias="name")
    description: Optional[str] = Field(default=None, validation_alias="description", serialization_alias="description")
    
    # Type flags (from public API with different casing)
    is_test_operation: bool = Field(default=False, validation_alias="isTestOperation", serialization_alias="isTestOperation")
    is_repair_operation: bool = Field(default=False, validation_alias="isRepairOperation", serialization_alias="isRepairOperation")
    is_wip_operation: bool = Field(default=False, validation_alias="isWipOperation", serialization_alias="isWipOperation")
    
    # Additional fields (internal API provides these with PascalCase)
    process_id: Optional[UUID] = Field(default=None, validation_alias="ProcessID", serialization_alias="ProcessID")
    process_index: Optional[int] = Field(default=None, validation_alias="processIndex", serialization_alias="processIndex")
    state: Optional[int] = Field(default=None, validation_alias="state", serialization_alias="state")
    properties: Optional[str] = Field(default=None, validation_alias="Properties", serialization_alias="Properties")

    # Allow both camelCase and PascalCase for internal API compatibility
    model_config = {"populate_by_name": True}


class RepairCategory(PyWATSModel):
    """
    Repair category (fail code category).
    
    Categories group related fail codes together (e.g., "Assembly Process", 
    "Component", "Solder Process").
    """
    guid: UUID = Field(validation_alias="GUID", serialization_alias="GUID")
    description: str = Field(validation_alias="Description", serialization_alias="Description")
    selectable: bool = Field(default=True, validation_alias="Selectable", serialization_alias="Selectable")
    sort_order: int = Field(default=0, validation_alias="SortOrder", serialization_alias="SortOrder")
    failure_type: int = Field(default=0, validation_alias="FailureType", serialization_alias="FailureType")
    image_constraint: Optional[str] = Field(default=None, validation_alias="ImageConstraint", serialization_alias="ImageConstraint")
    status: int = Field(default=1, validation_alias="Status", serialization_alias="Status")
    fail_codes: List["RepairCategory"] = Field(default_factory=list, validation_alias="Failcodes", serialization_alias="Failcodes")


class RepairOperationConfig(PyWATSModel):
    """
    Repair operation configuration.
    
    Contains the configuration for a repair operation including:
    - Required fields (UUT, BOM, vendor)
    - Component reference mask for validation
    - Categories with fail codes
    
    Structure:
        categories: List[RepairCategory]  # Top-level categories
            └── fail_codes: List[RepairCategory]  # Actual fail codes (one level)
    """
    description: str = Field(validation_alias="Description", serialization_alias="Description")
    uut_required: int = Field(default=1, validation_alias="UUTRequired", serialization_alias="UUTRequired")
    comp_ref_mask: Optional[str] = Field(default=None, validation_alias="CompRefMask", serialization_alias="CompRefMask")
    comp_ref_mask_description: Optional[str] = Field(default=None, validation_alias="CompRefMaskDescription", serialization_alias="CompRefMaskDescription")
    bom_constraint: Optional[str] = Field(default=None, validation_alias="BomConstraint", serialization_alias="BomConstraint")
    bom_required: int = Field(default=1, validation_alias="BOMRequired", serialization_alias="BOMRequired")
    vendor_required: int = Field(default=2, validation_alias="VendorRequired", serialization_alias="VendorRequired")
    categories: List[RepairCategory] = Field(default_factory=list, validation_alias="Categories", serialization_alias="Categories")
    misc_infos: List[Any] = Field(default_factory=list, validation_alias="MiscInfos", serialization_alias="MiscInfos")
    
    @property
    def failure_codes(self) -> List[FailureCodeInfo]:
        """
        Get flattened list of all failure codes across all categories.
        
        The hierarchy is: category (parent) → fail_codes (children, one level).
        
        Returns:
            List of FailureCodeInfo with category and code info
        """
        result = []
        for category in self.categories:
            # Each category contains fail_codes (which are also RepairCategory objects)
            for fail_code in category.fail_codes:
                if fail_code.selectable:  # Only selectable codes can be used
                    result.append(FailureCodeInfo(
                        category=category.description,
                        code=fail_code.description,
                        guid=fail_code.guid,
                        category_guid=category.guid
                    ))
        return result
    
    def get_fail_code_by_name(
        self, 
        category: str, 
        code: str
    ) -> Optional[FailureCodeInfo]:
        """
        Look up a fail code by category and code name.
        
        Args:
            category: Category description (e.g., "Component")
            code: Fail code description (e.g., "Defect Component")
            
        Returns:
            FailureCodeInfo if found, None otherwise
        """
        for fc in self.failure_codes:
            if fc.category == category and fc.code == code:
                return fc
        return None
    
    def validate_fail_code(self, category: str, code: str) -> tuple[bool, str]:
        """
        Validate that a category/code combination exists.
        
        Args:
            category: Category description
            code: Fail code description
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        fc = self.get_fail_code_by_name(category, code)
        if fc is None:
            return False, f"Invalid fail code: category='{category}', code='{code}'"
        return True, ""
