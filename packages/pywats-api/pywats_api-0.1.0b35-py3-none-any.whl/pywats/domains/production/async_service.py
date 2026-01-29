"""Async Production service - business logic layer.

Async version of the production service for non-blocking operations.
Includes both public and internal API methods.

⚠️ INTERNAL API methods are marked and may change without notice.
"""
from typing import Optional, List, Dict, Any, Sequence, Union, TYPE_CHECKING
from datetime import datetime
import logging

from .models import (
    Unit, UnitChange, ProductionBatch, SerialNumberType,
    UnitVerification, UnitVerificationGrade, UnitPhase
)
from .enums import UnitPhaseFlag
from .async_repository import AsyncProductionRepository

logger = logging.getLogger(__name__)


class AsyncProductionService:
    """
    Async Production business logic.

    Provides high-level async operations for managing production units,
    serial numbers, batches, and assembly relationships.
    Includes both public and internal API methods (marked with ⚠️).
    """

    def __init__(
        self, 
        repository: AsyncProductionRepository, 
        base_url: str = ""
    ):
        """
        Initialize with async repository.

        Args:
            repository: AsyncProductionRepository for data access
            base_url: Base URL for internal API calls
        """
        self._repository = repository
        self._base_url = base_url.rstrip("/") if base_url else ""
        
        # Phase cache (loaded on first access)
        self._phases: Optional[List[UnitPhase]] = None
        self._phase_by_id: Dict[int, UnitPhase] = {}
        self._phase_by_code: Dict[str, UnitPhase] = {}
        self._phase_by_name: Dict[str, UnitPhase] = {}

    # =========================================================================
    # Unit Operations
    # =========================================================================

    async def get_unit(
        self, serial_number: str, part_number: str
    ) -> Optional[Unit]:
        """
        Get a production unit.

        Args:
            serial_number: The unit serial number
            part_number: The product part number

        Returns:
            Unit if found, None otherwise
        """
        if not serial_number or not serial_number.strip():
            raise ValueError("serial_number is required")
        if not part_number or not part_number.strip():
            raise ValueError("part_number is required")
        return await self._repository.get_unit(serial_number, part_number)

    async def create_units(self, units: Sequence[Unit]) -> List[Unit]:
        """
        Create multiple production units.

        Args:
            units: List of Unit objects to create

        Returns:
            List of created Unit objects
        """
        results = await self._repository.save_units(units)
        for unit in results:
            logger.info(f"UNIT_CREATED: {unit.serial_number} (pn={unit.part_number})")
        return results

    async def update_unit(self, unit: Unit) -> Optional[Unit]:
        """
        Update a production unit.

        Args:
            unit: Unit object with updated fields

        Returns:
            Updated Unit object
        """
        result = await self._repository.save_units([unit])
        if result:
            logger.info(f"UNIT_UPDATED: {unit.serial_number} (pn={unit.part_number})")
        return result[0] if result else None

    # =========================================================================
    # Unit Verification
    # =========================================================================

    async def verify_unit(
        self,
        serial_number: str,
        part_number: str,
        revision: Optional[str] = None
    ) -> Optional[UnitVerification]:
        """
        Verify a unit and get its status.

        Args:
            serial_number: The unit serial number
            part_number: The product part number
            revision: Optional product revision

        Returns:
            UnitVerification result
        """
        if not serial_number or not serial_number.strip():
            raise ValueError("serial_number is required")
        if not part_number or not part_number.strip():
            raise ValueError("part_number is required")
        return await self._repository.get_unit_verification(
            serial_number, part_number, revision
        )

    async def get_unit_grade(
        self,
        serial_number: str,
        part_number: str,
        revision: Optional[str] = None
    ) -> Optional[UnitVerificationGrade]:
        """
        Get the verification grade for a unit.

        Args:
            serial_number: The unit serial number
            part_number: The product part number
            revision: Optional product revision

        Returns:
            UnitVerificationGrade or None
        """
        if not serial_number or not serial_number.strip():
            raise ValueError("serial_number is required")
        if not part_number or not part_number.strip():
            raise ValueError("part_number is required")
        return await self._repository.get_unit_verification_grade(
            serial_number, part_number, revision
        )

    async def is_unit_passing(
        self,
        serial_number: str,
        part_number: str
    ) -> bool:
        """
        Check if a unit is passing all tests.
        
        Args:
            serial_number: The unit serial number
            part_number: The product part number
            
        Returns:
            True if unit is passing
            
        Raises:
            ValueError: If serial_number or part_number is empty or None
        """
        if not serial_number or not serial_number.strip():
            raise ValueError("serial_number is required")
        if not part_number or not part_number.strip():
            raise ValueError("part_number is required")
        grade = await self._repository.get_unit_verification_grade(
            serial_number, part_number
        )
        if grade:
            return grade.all_processes_passed_last_run
        return False

    # =========================================================================
    # Serial Number Types
    # =========================================================================

    async def get_serial_number_types(self) -> List[SerialNumberType]:
        """
        Get all configured serial number types.

        Returns:
            List of SerialNumberType objects
        """
        return await self._repository.get_serial_number_types()

    # =========================================================================
    # Unit Phases
    # =========================================================================

    async def get_phases(self, force_refresh: bool = False) -> List[UnitPhase]:
        """
        Get all available unit phases.

        Args:
            force_refresh: Force reload from server (default: False)

        Returns:
            List of UnitPhase objects
        """
        if self._phases is None or force_refresh:
            self._phases = await self._repository.get_unit_phases()
            self._phase_by_id = {p.phase_id: p for p in self._phases}
            self._phase_by_code = {p.code.lower(): p for p in self._phases if p.code}
            self._phase_by_name = {p.name.lower(): p for p in self._phases if p.name}
        return self._phases

    async def get_phase(
        self,
        phase_id: Optional[int] = None,
        code: Optional[str] = None,
        name: Optional[str] = None
    ) -> Optional[UnitPhase]:
        """
        Get a specific unit phase by ID, code, or name.

        Args:
            phase_id: Phase ID to look up
            code: Phase code to look up
            name: Phase name to look up

        Returns:
            UnitPhase if found, None otherwise
        """
        # Ensure phases are loaded
        await self.get_phases()
        
        if phase_id is not None:
            return self._phase_by_id.get(phase_id)
        if code:
            return self._phase_by_code.get(code)
        if name:
            return self._phase_by_name.get(name)
        return None

    async def get_phase_id(
        self,
        phase: Union[int, str, UnitPhaseFlag]
    ) -> Optional[int]:
        """
        Resolve a phase identifier to its ID.
        
        Args:
            phase: Phase ID (int), code (str), name (str), or UnitPhaseFlag enum
            
        Returns:
            Phase ID if found, None otherwise
            
        Example:
            phase_id = await api.production.get_phase_id("Finalized")  # Returns 16
            phase_id = await api.production.get_phase_id(UnitPhaseFlag.FINALIZED)  # Returns 16
        """
        if isinstance(phase, UnitPhaseFlag):
            return int(phase)
        if isinstance(phase, int):
            return phase
        
        # Try by name first, then by code (case-insensitive)
        phase_str = phase.lower()
        await self.get_phases()  # Ensure cache is loaded
        
        if phase_str in self._phase_by_name:
            return self._phase_by_name[phase_str].phase_id
        if phase_str in self._phase_by_code:
            return self._phase_by_code[phase_str].phase_id
        return None

    async def get_all_unit_phases(self) -> List[UnitPhase]:
        """
        Get all available unit phases.
        
        Alias for get_phases() for compatibility.
        
        Returns:
            List of UnitPhase objects
        """
        return await self.get_phases()

    async def get_phase_by_name(self, name: str) -> Optional[UnitPhase]:
        """
        Get a unit phase by name.
        
        Args:
            name: Phase name to look up
            
        Returns:
            UnitPhase if found, None otherwise
        """
        return await self.get_phase(name=name)

    # =========================================================================
    # Unit History
    # =========================================================================

    async def get_unit_history(
        self,
        serial_number: str,
        part_number: str
    ) -> List[UnitChange]:
        """
        Get the change history for a unit.

        Args:
            serial_number: The unit serial number
            part_number: The product part number

        Returns:
            List of UnitChange objects
        """
        if not serial_number or not serial_number.strip():
            raise ValueError("serial_number is required")
        if not part_number or not part_number.strip():
            raise ValueError("part_number is required")
        return await self._repository.get_unit_changes(serial_number, part_number)

    # =========================================================================
    # Batches
    # =========================================================================

    async def get_batches(
        self,
        part_number: Optional[str] = None,
        batch_id: Optional[str] = None
    ) -> List[ProductionBatch]:
        """
        Get production batches.

        Args:
            part_number: Filter by part number
            batch_id: Filter by batch ID

        Returns:
            List of ProductionBatch objects
        """
        return await self._repository.get_batches(part_number, batch_id)

    async def create_batch(
        self, batch: Union[ProductionBatch, Dict[str, Any]]
    ) -> Optional[ProductionBatch]:
        """
        Create a new production batch.

        Args:
            batch: ProductionBatch object or dict with batch data

        Returns:
            Created ProductionBatch object
        """
        result = await self._repository.save_batch(batch)
        if result:
            logger.info(f"BATCH_CREATED: {result.batch_id}")
        return result

    async def update_batch(
        self, batch: ProductionBatch
    ) -> Optional[ProductionBatch]:
        """
        Update an existing production batch.

        Args:
            batch: ProductionBatch object with updated fields

        Returns:
            Updated ProductionBatch object
        """
        result = await self._repository.save_batch(batch)
        if result:
            logger.info(f"BATCH_UPDATED: {result.batch_id}")
        return result

    async def save_batches(
        self, batches: Sequence[Union[ProductionBatch, Dict[str, Any]]]
    ) -> List[ProductionBatch]:
        """
        Add or update batches (bulk).

        Args:
            batches: List of ProductionBatch objects or data dictionaries

        Returns:
            List of saved ProductionBatch objects
        """
        return await self._repository.save_batches(batches)

    # =========================================================================
    # Unit Phase and Process
    # =========================================================================

    async def set_unit_phase(
        self,
        serial_number: str,
        part_number: str,
        phase: Union[int, str, UnitPhaseFlag],
        comment: Optional[str] = None
    ) -> bool:
        """
        Set a unit's current phase.

        Args:
            serial_number: The unit serial number
            part_number: The product part number
            phase: Phase ID (int), code (str), name (str), or UnitPhaseFlag enum
            comment: Optional comment

        Returns:
            True if successful
            
        Example:
            # By phase ID
            await api.production.set_unit_phase("SN001", "PART001", 16)

            # By phase code
            await api.production.set_unit_phase("SN001", "PART001", "Finalized")

            # By phase name
            await api.production.set_unit_phase("SN001", "PART001", "Under production")

            # By enum (recommended)
            await api.production.set_unit_phase("SN001", "PART001", UnitPhaseFlag.FINALIZED)
        """
        if not serial_number or not serial_number.strip():
            raise ValueError("serial_number is required")
        if not part_number or not part_number.strip():
            raise ValueError("part_number is required")
        
        # Resolve phase to ID if string/enum
        phase_id = await self.get_phase_id(phase)
        if phase_id is None:
            raise ValueError(f"Unknown phase: {phase}")
        
        return await self._repository.set_unit_phase(
            serial_number, part_number, phase_id, comment
        )

    async def set_unit_process(
        self,
        serial_number: str,
        part_number: str,
        process_code: Optional[int] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Set a unit's process.

        Args:
            serial_number: The unit serial number
            part_number: The product part number
            process_code: The process code
            comment: Optional comment

        Returns:
            True if successful
        """
        if not serial_number or not serial_number.strip():
            raise ValueError("serial_number is required")
        if not part_number or not part_number.strip():
            raise ValueError("part_number is required")
        return await self._repository.set_unit_process(
            serial_number, part_number, process_code, comment
        )

    # =========================================================================
    # Unit Changes
    # =========================================================================

    async def get_unit_changes(
        self,
        serial_number: Optional[str] = None,
        part_number: Optional[str] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List[UnitChange]:
        """
        Get unit change records.

        Args:
            serial_number: Optional serial number filter
            part_number: Optional part number filter
            top: Number of records to return
            skip: Number of records to skip

        Returns:
            List of UnitChange objects
        """
        return await self._repository.get_unit_changes(
            serial_number, part_number, top, skip
        )

    async def delete_unit_change(self, change_id: str) -> bool:
        """
        Delete a unit change record.

        Args:
            change_id: The change record ID

        Returns:
            True if successful
        """
        return await self._repository.delete_unit_change(change_id)

    async def acknowledge_unit_change(self, change_id: str) -> bool:
        """
        Acknowledge and delete a unit change record.
        
        Alias for delete_unit_change for compatibility with sync API.
        
        Args:
            change_id: The change record ID
            
        Returns:
            True if successful
        """
        return await self.delete_unit_change(change_id)

    # =========================================================================
    # Child Units (Assembly) - Public API
    # =========================================================================

    async def add_child_to_assembly(
        self,
        parent_serial: str,
        parent_part: str,
        child_serial: str,
        child_part: str
    ) -> bool:
        """
        Attach a child unit to a parent assembly.

        This is the primary method for box build assembly operations.
        The assembly structure is validated against the BoxBuildTemplate
        defined in the Product domain. The child unit should typically be 
        in "Finalized" phase before attachment.

        Args:
            parent_serial: Parent unit serial number
            parent_part: Parent product part number
            child_serial: Child unit serial number
            child_part: Child product part number

        Returns:
            True if successful

        Example:
            >>> # Attach a PCBA to a module
            >>> await api.production.add_child_to_assembly(
            ...     parent_serial="MODULE-001",
            ...     parent_part="MAIN-MODULE",
            ...     child_serial="PCBA-001",
            ...     child_part="PCBA-BOARD"
            ... )
        """
        return await self._repository.add_child_unit(
            parent_serial, parent_part, child_serial, child_part
        )

    async def remove_child_from_assembly(
        self,
        parent_serial: str,
        parent_part: str,
        child_serial: str,
        child_part: str
    ) -> bool:
        """
        Remove the parent/child relation between two units.

        Args:
            parent_serial: Parent unit serial number
            parent_part: Parent product part number
            child_serial: Child unit serial number
            child_part: Child product part number

        Returns:
            True if successful
        """
        return await self._repository.remove_child_unit(
            parent_serial, parent_part, child_serial, child_part
        )

    async def verify_assembly(
        self,
        serial_number: str,
        part_number: str,
        revision: str
    ) -> Optional[Dict[str, Any]]:
        """
        Verify that assembly child units match the box build template.
        
        Checks whether all required subunits (as defined in the product's
        box build template) have been attached to this specific unit.
        
        This compares:
        - Box Build Template: "What subunits are REQUIRED" (Product domain)
        - Current Assembly: "What units are ATTACHED" (Production domain)
        
        Args:
            serial_number: Parent serial number
            part_number: Parent part number
            revision: Parent revision
            
        Returns:
            Verification results or None
        """
        return await self._repository.check_child_units(
            serial_number, part_number, revision
        )

    # =========================================================================
    # Serial Numbers - Public API
    # =========================================================================

    async def allocate_serial_numbers(
        self,
        type_name: str,
        count: int = 1,
        reference_sn: Optional[str] = None,
        reference_pn: Optional[str] = None,
        station_name: Optional[str] = None
    ) -> List[str]:
        """
        Allocate serial numbers from pool.

        Args:
            type_name: Serial number type name
            count: Number of serial numbers to take (quantity)
            reference_sn: Optional reference serial number
            reference_pn: Optional reference part number
            station_name: Optional station name

        Returns:
            List of allocated serial numbers
        """
        return await self._repository.take_serial_numbers(
            type_name, count, reference_sn, reference_pn, station_name
        )

    async def find_serial_numbers_in_range(
        self,
        type_name: str,
        from_serial: str,
        to_serial: str
    ) -> List[Dict[str, Any]]:
        """
        Find serial numbers in a range.

        Args:
            type_name: Serial number type name
            from_serial: Start of range
            to_serial: End of range

        Returns:
            List of serial number records
        """
        return await self._repository.get_serial_numbers_by_range(
            type_name, from_serial, to_serial
        )

    async def find_serial_numbers_by_reference(
        self,
        type_name: str,
        reference_serial: Optional[str] = None,
        reference_part: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find serial numbers by reference.

        Args:
            type_name: Serial number type name
            reference_serial: Reference serial number
            reference_part: Reference part number

        Returns:
            List of serial number records
        """
        return await self._repository.get_serial_numbers_by_reference(
            type_name, reference_serial, reference_part
        )

    async def import_serial_numbers(
        self,
        file_content: bytes,
        content_type: str = "text/csv"
    ) -> bool:
        """
        Import serial numbers from file (XML or CSV).

        Args:
            file_content: File content as bytes
            content_type: MIME type (text/csv or application/xml)

        Returns:
            True if successful
        """
        return await self._repository.upload_serial_numbers(file_content, content_type)

    async def export_serial_numbers(
        self,
        type_name: str,
        state: Optional[str] = None,
        format: str = "csv"
    ) -> Optional[bytes]:
        """
        Export serial numbers as file.

        Args:
            type_name: Serial number type name
            state: Optional state filter
            format: Output format (csv or xml)

        Returns:
            File content as bytes or None
        """
        return await self._repository.export_serial_numbers(type_name, state, format)

    # =========================================================================
    # ⚠️ INTERNAL API - Connection Check
    # =========================================================================

    async def is_connected(self) -> bool:
        """
        ⚠️ INTERNAL: Check if Production module is connected.
        """
        return await self._repository.is_connected()

    # =========================================================================
    # ⚠️ INTERNAL API - Sites
    # =========================================================================

    async def get_sites(self) -> List[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get all production sites.
        """
        return await self._repository.get_sites()

    # =========================================================================
    # ⚠️ INTERNAL API - Unit Operations
    # =========================================================================

    async def get_unit_info(
        self,
        serial_number: str,
        part_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get detailed unit information.

        Args:
            serial_number: Unit serial number
            part_number: Unit part number

        Returns:
            Unit info dictionary or None
        """
        if not serial_number or not serial_number.strip():
            raise ValueError("serial_number is required")
        if not part_number or not part_number.strip():
            raise ValueError("part_number is required")
        return await self._repository.get_unit_info(serial_number, part_number)

    async def get_unit_hierarchy(
        self,
        serial_number: str,
        part_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get the complete unit hierarchy.

        Args:
            serial_number: Unit serial number
            part_number: Unit part number

        Returns:
            Hierarchy data dictionary or None
        """
        if not serial_number or not serial_number.strip():
            raise ValueError("serial_number is required")
        if not part_number or not part_number.strip():
            raise ValueError("part_number is required")
        return await self._repository.get_unit_hierarchy(serial_number, part_number)

    async def get_unit_state_history(
        self,
        serial_number: str,
        part_number: str
    ) -> List[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get the unit state change history.

        Args:
            serial_number: Unit serial number
            part_number: Unit part number

        Returns:
            List of state change records
        """
        if not serial_number or not serial_number.strip():
            raise ValueError("serial_number is required")
        if not part_number or not part_number.strip():
            raise ValueError("part_number is required")
        return await self._repository.get_unit_state_history(serial_number, part_number)

    async def get_unit_contents(
        self,
        serial_number: str,
        part_number: str,
        revision: str
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get unit contents (BOM/components).

        Args:
            serial_number: Unit serial number
            part_number: Unit part number
            revision: Unit revision

        Returns:
            Contents data dictionary or None
        """
        if not serial_number or not serial_number.strip():
            raise ValueError("serial_number is required")
        if not part_number or not part_number.strip():
            raise ValueError("part_number is required")
        return await self._repository.get_unit_contents(serial_number, part_number, revision)

    async def create_unit(
        self,
        serial_number: str,
        part_number: str,
        revision: str,
        batch_number: Optional[str] = None,
        unit_phase: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new unit in the production system.
        
        Uses internal MES API to create a production unit.
        
        Note: Uses internal API endpoint which may change without notice.

        Args:
            serial_number: Unit serial number
            part_number: Unit part number
            revision: Unit revision
            batch_number: Optional batch number
            unit_phase: Optional initial unit phase ID

        Returns:
            Created unit data or None
        """
        return await self._repository.create_unit(
            serial_number, part_number, revision, batch_number, unit_phase
        )

    # =========================================================================
    # ⚠️ INTERNAL API - Child Unit Operations  
    # =========================================================================

    async def add_child_unit_validated(
        self,
        serial_number: str,
        part_number: str,
        child_serial_number: str,
        child_part_number: str,
        check_part_number: str,
        check_revision: str,
        culture_code: str = "en-US",
        check_phase: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Add a child unit to a parent unit with validation.
        
        Uses internal MES API which validates the child unit relationship
        and returns localized response messages.
        
        Note: Uses internal API endpoint which may change without notice.

        Args:
            serial_number: Parent unit serial number
            part_number: Parent unit part number
            child_serial_number: Child unit serial number
            child_part_number: Child unit part number
            check_part_number: Part number to check against
            check_revision: Revision to check against
            culture_code: Culture code for error messages
            check_phase: Whether to check phase compatibility

        Returns:
            Result data or None
        """
        return await self._repository.add_child_unit_validated(
            serial_number, part_number, child_serial_number, child_part_number,
            check_part_number, check_revision, culture_code, check_phase
        )

    async def remove_child_unit_localized(
        self,
        serial_number: str,
        part_number: str,
        child_serial_number: str,
        child_part_number: str,
        culture_code: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Remove a child unit from a parent unit.
        
        Uses internal MES API which returns localized response messages.
        
        Note: Uses internal API endpoint which may change without notice.

        Args:
            serial_number: Parent unit serial number
            part_number: Parent unit part number
            child_serial_number: Child unit serial number
            child_part_number: Child unit part number
            culture_code: Optional culture code

        Returns:
            Result data or None
        """
        return await self._repository.remove_child_unit_localized(
            serial_number, part_number, child_serial_number, child_part_number, culture_code
        )

    async def remove_all_child_units(
        self,
        serial_number: str,
        part_number: str,
        culture_code: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Remove all child units from a parent unit.

        Args:
            serial_number: Parent unit serial number
            part_number: Parent unit part number
            culture_code: Optional culture code

        Returns:
            Result data or None
        """
        return await self._repository.remove_all_child_units(
            serial_number, part_number, culture_code
        )

    async def validate_child_units(
        self,
        parent_serial_number: str,
        parent_part_number: str,
        culture_code: str = "en-US"
    ) -> Optional[Dict[str, Any]]:
        """
        Validate child units of a parent unit.
        
        Performs validation check using internal MES API.
        
        Note: Uses internal API endpoint which may change without notice.

        Args:
            parent_serial_number: Parent unit serial number
            parent_part_number: Parent unit part number
            culture_code: Culture code for error messages

        Returns:
            Check result data or None
        """
        return await self._repository.validate_child_units(
            parent_serial_number, parent_part_number, culture_code
        )

    # =========================================================================
    # ⚠️ INTERNAL API - Serial Number Management
    # =========================================================================

    async def find_serial_numbers(
        self,
        serial_number_type: str,
        start_address: str,
        end_address: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Find all serial numbers in a range.

        Args:
            serial_number_type: Type of serial numbers to find
            start_address: Start of range
            end_address: End of range
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of serial number records
        """
        return await self._repository.find_serial_numbers(
            serial_number_type, start_address, end_address, start_date, end_date
        )

    async def get_serial_number_count(
        self,
        serial_number_type: str,
        start_address: Optional[str] = None,
        end_address: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Optional[int]:
        """
        ⚠️ INTERNAL: Get count of serial numbers in a range.

        Args:
            serial_number_type: Type of serial numbers
            start_address: Optional start of range
            end_address: Optional end of range
            from_date: Optional start date filter
            to_date: Optional end date filter

        Returns:
            Count of serial numbers or None
        """
        return await self._repository.get_serial_number_count(
            serial_number_type, start_address, end_address, from_date, to_date
        )

    async def free_serial_numbers(
        self,
        ranges: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Free reserved serial numbers in specified ranges.

        Args:
            ranges: List of range definitions

        Returns:
            Result data or None
        """
        return await self._repository.free_serial_numbers(ranges)

    async def get_serial_number_ranges(
        self,
        serial_number_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get current serial number ranges.

        Args:
            serial_number_type: Optional filter by type

        Returns:
            List of range records
        """
        return await self._repository.get_serial_number_ranges(serial_number_type)

    async def get_serial_number_statistics(
        self,
        serial_number_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get statistics for serial numbers.

        Args:
            serial_number_type: Optional filter by type

        Returns:
            Statistics data or None
        """
        return await self._repository.get_serial_number_statistics(serial_number_type)
