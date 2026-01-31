"""
UURReport - Unit Under Repair Report.

Simplified Pydantic model following UUTReport design pattern.
Failures are stored on sub-units (UURSubUnit.failures), not on the report.

Based on C# UURReport specification.
"""

from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
from pydantic import Field, model_validator

from .uur_info import UURInfo
from .uur_sub_unit import UURSubUnit, UURFailure
from ..attachment import Attachment  # Shared attachment class
from ..report import Report

if TYPE_CHECKING:
    from .....domains.report.report_models.uut.uut_report import UUTReport


class UURReport(Report):
    """
    A unit under repair report (UUR).
    
    UUR reports document repair/rework activities on units that have failed
    testing. Key features:
    
    - Links to original UUT report via `uur_info.ref_uut`
    - Dual process codes: repair_process_code (what repair type) and 
      test_operation_code (original test that failed)
    - Failures are stored on sub_units (idx=0 is main unit)
    - Supports sub-unit replacement tracking
    
    Example:
        >>> # Create via service factory (recommended)
        >>> uur = service.create_uur_report(
        ...     uut_report,
        ...     repair_process_code=500,
        ...     operator="John"
        ... )
        >>> 
        >>> # Add failure to main unit
        >>> main = uur.get_main_unit()
        >>> main.add_failure(category="Component", code="CAPACITOR_FAIL")
        >>> 
        >>> # Add sub-unit and its failures
        >>> sub = uur.add_sub_unit("SUB-001", "SN-001")
        >>> sub.add_failure(category="Solder", code="COLD_JOINT")
    """
    
    # Report type = Repair
    type: str = Field(default="R", pattern='^[R]$')
    
    # UUR-specific info (dual process codes, operator, comment, etc.)
    uur_info: UURInfo = Field(
        default_factory=UURInfo, 
        validation_alias="uur", 
        serialization_alias="uur"
    )
    
    # Sub-units with failures (idx=0 is main unit)
    sub_units: List[UURSubUnit] = Field(
        default_factory=list, 
        validation_alias="subUnits", 
        serialization_alias="subUnits"
    )
    
    # Attachments (report-level) - uses shared Attachment class
    attachments: List[Attachment] = Field(
        default_factory=list,
        validation_alias="binaryData",
        serialization_alias="binaryData"
    )
    
    @model_validator(mode='after')
    def ensure_main_unit(self) -> 'UURReport':
        """Ensure main unit (idx=0) exists."""
        if not self.sub_units or not any(su.idx == 0 for su in self.sub_units):
            main = UURSubUnit.create_main_unit(
                pn=self.pn,
                sn=self.sn,
                rev=self.rev or ""
            )
            self.sub_units.insert(0, main)
        return self
    
    # =========================================================================
    # Sub-Unit Access
    # =========================================================================
    
    def get_main_unit(self) -> UURSubUnit:
        """
        Get the main unit (idx=0).
        
        Returns:
            UURSubUnit representing the main unit being repaired
        """
        for su in self.sub_units:
            if su.idx == 0:
                return su
        # Should never happen due to model validator
        raise ValueError("Main unit (idx=0) not found")
    
    def get_sub_unit(self, idx: int) -> Optional[UURSubUnit]:
        """
        Get sub-unit by index.
        
        Args:
            idx: Sub-unit index
            
        Returns:
            UURSubUnit if found, None otherwise
        """
        for su in self.sub_units:
            if su.idx == idx:
                return su
        return None
    
    def add_sub_unit(
        self,
        pn: str,
        sn: str,
        rev: str = "",
        part_type: str = "SubUnit",
        parent_idx: int = 0
    ) -> UURSubUnit:
        """
        Add a sub-unit to the repair.
        
        Args:
            pn: Part number
            sn: Serial number
            rev: Revision
            part_type: Type of sub-unit
            parent_idx: Index of parent unit (default=0, main unit)
            
        Returns:
            Created UURSubUnit
        """
        # Get next index
        max_idx = max((su.idx for su in self.sub_units), default=-1)
        new_idx = max_idx + 1
        
        sub_unit = UURSubUnit(
            pn=pn,
            sn=sn,
            rev=rev,
            part_type=part_type,
            idx=new_idx,
            parent_idx=parent_idx
        )
        self.sub_units.append(sub_unit)
        return sub_unit
    
    # =========================================================================
    # Failure Convenience Methods (delegate to main unit)
    # =========================================================================
    
    def add_failure(
        self,
        category: str,
        code: str,
        comment: Optional[str] = None,
        component_ref: Optional[str] = None,
        ref_step_id: Optional[int] = None
    ) -> UURFailure:
        """
        Add a failure to the main unit.
        
        Convenience method - equivalent to `get_main_unit().add_failure(...)`.
        
        Args:
            category: Failure category
            code: Failure code
            comment: Optional comment
            component_ref: Component reference (e.g., "C12")
            ref_step_id: UUT step ID that revealed the failure
            
        Returns:
            Created UURFailure
        """
        return self.get_main_unit().add_failure(
            category=category,
            code=code,
            comment=comment,
            component_ref=component_ref,
            ref_step_id=ref_step_id
        )
    
    def add_failure_to_main_unit(
        self,
        category: str,
        code: str,
        comment: Optional[str] = None,
        component_ref: Optional[str] = None,
        ref_step_id: Optional[int] = None
    ) -> UURFailure:
        """
        Add a failure to the main unit.
        
        Note:
            This is an alias for `add_failure()` for clarity when working with multi-unit repairs.
        
        Args:
            category: Failure category
            code: Failure code
            comment: Optional comment
            component_ref: Component reference (e.g., "C12")
            ref_step_id: UUT step ID that revealed the failure
            
        Returns:
            Created UURFailure
        """
        return self.add_failure(
            category=category,
            code=code,
            comment=comment,
            component_ref=component_ref,
            ref_step_id=ref_step_id
        )
    
    @property
    def failures(self) -> List[UURFailure]:
        """
        Get failures for the main unit.
        
        Returns:
            List of failures on main unit (idx=0)
        """
        main = self.get_main_unit()
        return main.failures or []
    
    @property
    def all_failures(self) -> List[UURFailure]:
        """
        Get all failures across all sub-units.
        
        Returns:
            List of all failures
        """
        result = []
        for su in self.sub_units:
            if su.failures:
                result.extend(su.failures)
        return result
    
    # =========================================================================
    # UUR Properties (delegated to uur_info)
    # =========================================================================
    
    @property
    def uut_guid(self) -> Optional[UUID]:
        """GUID of the referenced UUT report."""
        return self.uur_info.ref_uut
    
    @uut_guid.setter
    def uut_guid(self, value: UUID) -> None:
        self.uur_info.ref_uut = value
    
    @property
    def operator(self) -> Optional[str]:
        """Operator who performed the repair."""
        return self.uur_info.uur_operator
    
    @operator.setter
    def operator(self, value: str) -> None:
        self.uur_info.uur_operator = value
    
    @property
    def comment(self) -> Optional[str]:
        """Repair comment."""
        return self.uur_info.comment
    
    @comment.setter
    def comment(self, value: str) -> None:
        self.uur_info.comment = value
    
    @property
    def execution_time(self) -> float:
        """Time spent on repair (seconds)."""
        return self.uur_info.exec_time or 0.0
    
    @execution_time.setter
    def execution_time(self, value: float) -> None:
        self.uur_info.exec_time = value
    
    @property
    def repair_process_code(self) -> Optional[int]:
        """The repair process code (type of repair operation)."""
        return self.uur_info.repair_process_code
    
    @property
    def test_operation_code(self) -> Optional[int]:
        """The original test operation code."""
        return self.uur_info.test_operation_code
    
    # =========================================================================
    # Attachment Methods
    # =========================================================================
    
    def attach_bytes(
        self,
        name: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        failure_idx: Optional[int] = None
    ) -> Attachment:
        """
        Attach binary data to the repair report.
        
        Note:
            For file attachments, use pywats_client.io.AttachmentIO:
            
            >>> from pywats_client.io import AttachmentIO
            >>> content, name, mime_type = AttachmentIO.read_file("report.pdf")
            >>> report.attach_bytes(name, content, mime_type)
        
        Args:
            name: Display name
            content: Binary content
            content_type: MIME type (default: application/octet-stream)
            failure_idx: Attach to specific failure (None = report-level)
            
        Returns:
            Created Attachment
        """
        attachment = Attachment.from_bytes(
            name=name,
            content=content,
            content_type=content_type,
            failure_idx=failure_idx
        )
        self.attachments.append(attachment)
        return attachment
    
    # =========================================================================
    # Misc Info (inherited from Report, but with convenience methods)
    # =========================================================================
    
    def copy_misc_from_uut(self, uut_report: 'UUTReport') -> None:
        """
        Copy misc info from a UUT report.
        
        Args:
            uut_report: Source UUT report
        """
        if uut_report.misc_infos:
            for misc in uut_report.misc_infos:
                self.add_misc_info(misc.description, misc.string_value)
    
    # =========================================================================
    # Validation
    # =========================================================================
    
    def validate_report(self) -> tuple[bool, str]:
        """
        Validate this UUR report.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        errors = []
        
        # Main unit must exist
        try:
            _ = self.get_main_unit()  # Will raise if main unit missing
        except ValueError as e:
            errors.append(str(e))
            return False, "; ".join(errors)
        
        # Validate dual process codes
        if self.uur_info.repair_process_code and self.uur_info.test_operation_code:
            if self.uur_info.repair_process_code == self.uur_info.test_operation_code:
                errors.append("repair_process_code and test_operation_code should differ")
        
        # Check for failures (UUR should typically have at least one)
        if not self.all_failures:
            # Warning, not error - some repairs may not have documented failures
            pass
        
        if errors:
            return False, "; ".join(errors)
        return True, ""
    
    # =========================================================================
    # Summary / Debug
    # =========================================================================
    
    def get_summary(self) -> dict:
        """Get summary of this UUR report."""
        return {
            'type': 'UUR',
            'id': str(self.id),
            'pn': self.pn,
            'sn': self.sn,
            'rev': self.rev,
            'uut_guid': str(self.uut_guid) if self.uut_guid else None,
            'operator': self.operator,
            'comment': self.comment,
            'repair_process_code': self.repair_process_code,
            'test_operation_code': self.test_operation_code,
            'sub_unit_count': len(self.sub_units),
            'failure_count': len(self.all_failures),
            'attachment_count': len(self.attachments),
            'misc_info_count': len(self.misc_infos) if self.misc_infos else 0,
            'execution_time': self.execution_time
        }
