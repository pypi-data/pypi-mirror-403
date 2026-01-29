"""Production service - thin sync wrapper around AsyncProductionService.

This module provides synchronous access to AsyncProductionService methods.
All business logic is maintained in async_service.py (source of truth).

⚠️ INTERNAL API methods are marked and may change without notice.
"""
from typing import Optional, List, Dict, Any, Sequence, Union
from datetime import datetime

from .async_service import AsyncProductionService
from .async_repository import AsyncProductionRepository
from .models import (
    Unit, UnitChange, ProductionBatch, SerialNumberType,
    UnitVerification, UnitVerificationGrade, UnitPhase
)
from .enums import UnitPhaseFlag
from ...core.sync_runner import run_sync


class ProductionService:
    """
    Synchronous wrapper for AsyncProductionService.

    Provides sync access to all async production service operations.
    All business logic is in AsyncProductionService.
    """

    def __init__(self, async_service: AsyncProductionService = None, *, repository=None):
        """
        Initialize with AsyncProductionService or repository.

        Args:
            async_service: AsyncProductionService instance to wrap
            repository: (Deprecated) Repository instance for backward compatibility
        """
        if repository is not None:
            # Backward compatibility: create async service from repository
            self._async_service = AsyncProductionService(repository)
            self._repository = repository  # Keep reference for tests
        elif async_service is not None:
            self._async_service = async_service
            self._repository = async_service._repository  # Expose underlying repo
        else:
            raise ValueError("Either async_service or repository must be provided")

    @classmethod
    def from_repository(cls, repository: AsyncProductionRepository) -> "ProductionService":
        """
        Create ProductionService from an AsyncProductionRepository.

        Args:
            repository: AsyncProductionRepository instance

        Returns:
            ProductionService wrapping an AsyncProductionService
        """
        async_service = AsyncProductionService(repository)
        return cls(async_service)

    # =========================================================================
    # Unit Operations
    # =========================================================================

    def get_unit(self, serial_number: str, part_number: str) -> Optional[Unit]:
        """Get a production unit."""
        return run_sync(self._async_service.get_unit(serial_number, part_number))

    def create_units(self, units: Sequence[Unit]) -> List[Unit]:
        """Create multiple production units."""
        return run_sync(self._async_service.create_units(units))

    def update_unit(self, unit: Unit) -> Optional[Unit]:
        """Update a production unit."""
        return run_sync(self._async_service.update_unit(unit))

    # =========================================================================
    # Unit Verification
    # =========================================================================

    def verify_unit(
        self,
        serial_number: str,
        part_number: str,
        revision: Optional[str] = None
    ) -> Optional[UnitVerification]:
        """Verify a unit and get its status."""
        return run_sync(self._async_service.verify_unit(serial_number, part_number, revision))

    def get_unit_grade(
        self,
        serial_number: str,
        part_number: str,
        revision: Optional[str] = None
    ) -> Optional[UnitVerificationGrade]:
        """Get the verification grade for a unit."""
        return run_sync(self._async_service.get_unit_grade(serial_number, part_number, revision))

    def is_unit_passing(self, serial_number: str, part_number: str) -> bool:
        """Check if a unit is passing all tests."""
        return run_sync(self._async_service.is_unit_passing(serial_number, part_number))

    # =========================================================================
    # Serial Number Types
    # =========================================================================

    def get_serial_number_types(self) -> List[SerialNumberType]:
        """Get all configured serial number types."""
        return run_sync(self._async_service.get_serial_number_types())

    # =========================================================================
    # Unit Phases
    # =========================================================================

    def get_phases(self, force_refresh: bool = False) -> List[UnitPhase]:
        """Get all available unit phases."""
        return run_sync(self._async_service.get_phases(force_refresh))

    def get_phase(
        self,
        phase_id: Optional[int] = None,
        code: Optional[str] = None,
        name: Optional[str] = None
    ) -> Optional[UnitPhase]:
        """Get a specific unit phase by ID, code, or name."""
        return run_sync(self._async_service.get_phase(phase_id, code, name))

    def get_phase_id(self, phase: Union[int, str, UnitPhaseFlag]) -> Optional[int]:
        """Resolve a phase identifier to its ID."""
        return run_sync(self._async_service.get_phase_id(phase))

    def get_all_unit_phases(self) -> List[UnitPhase]:
        """Get all available unit phases (alias for get_phases)."""
        return run_sync(self._async_service.get_all_unit_phases())

    def get_phase_by_name(self, name: str) -> Optional[UnitPhase]:
        """Get a unit phase by name."""
        return run_sync(self._async_service.get_phase_by_name(name))

    # =========================================================================
    # Unit History
    # =========================================================================

    def get_unit_history(
        self,
        serial_number: str,
        part_number: str
    ) -> List[UnitChange]:
        """Get the change history for a unit."""
        return run_sync(self._async_service.get_unit_history(serial_number, part_number))

    # =========================================================================
    # Batches
    # =========================================================================

    def get_batches(
        self,
        part_number: Optional[str] = None,
        batch_id: Optional[str] = None
    ) -> List[ProductionBatch]:
        """Get production batches."""
        return run_sync(self._async_service.get_batches(part_number, batch_id))

    def create_batch(
        self, batch: Union[ProductionBatch, Dict[str, Any]]
    ) -> Optional[ProductionBatch]:
        """Create a new production batch."""
        return run_sync(self._async_service.create_batch(batch))

    def update_batch(self, batch: ProductionBatch) -> Optional[ProductionBatch]:
        """Update an existing production batch."""
        return run_sync(self._async_service.update_batch(batch))

    def save_batches(
        self, batches: Sequence[Union[ProductionBatch, Dict[str, Any]]]
    ) -> List[ProductionBatch]:
        """Add or update batches (bulk)."""
        return run_sync(self._async_service.save_batches(batches))

    # =========================================================================
    # Unit Phase and Process
    # =========================================================================

    def set_unit_phase(
        self,
        serial_number: str,
        part_number: str,
        phase: Union[int, str, UnitPhaseFlag],
        comment: Optional[str] = None
    ) -> bool:
        """Set a unit's current phase."""
        return run_sync(self._async_service.set_unit_phase(
            serial_number, part_number, phase, comment
        ))

    def set_unit_process(
        self,
        serial_number: str,
        part_number: str,
        process_code: Optional[int] = None,
        comment: Optional[str] = None
    ) -> bool:
        """Set a unit's process."""
        return run_sync(self._async_service.set_unit_process(
            serial_number, part_number, process_code, comment
        ))

    # =========================================================================
    # Unit Changes
    # =========================================================================

    def get_unit_changes(
        self,
        serial_number: Optional[str] = None,
        part_number: Optional[str] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List[UnitChange]:
        """Get unit change records."""
        return run_sync(self._async_service.get_unit_changes(
            serial_number, part_number, top, skip
        ))

    def delete_unit_change(self, change_id: str) -> bool:
        """Delete a unit change record."""
        return run_sync(self._async_service.delete_unit_change(change_id))

    def acknowledge_unit_change(self, change_id: str) -> bool:
        """Acknowledge and delete a unit change record."""
        return run_sync(self._async_service.acknowledge_unit_change(change_id))

    # =========================================================================
    # Child Units (Assembly) - Public API
    # =========================================================================

    def add_child_to_assembly(
        self,
        parent_serial: str,
        parent_part: str,
        child_serial: str,
        child_part: str
    ) -> bool:
        """Attach a child unit to a parent assembly."""
        return run_sync(self._async_service.add_child_to_assembly(
            parent_serial, parent_part, child_serial, child_part
        ))

    def remove_child_from_assembly(
        self,
        parent_serial: str,
        parent_part: str,
        child_serial: str,
        child_part: str
    ) -> bool:
        """Remove the parent/child relation between two units."""
        return run_sync(self._async_service.remove_child_from_assembly(
            parent_serial, parent_part, child_serial, child_part
        ))

    def verify_assembly(
        self,
        serial_number: str,
        part_number: str,
        revision: str
    ) -> Optional[Dict[str, Any]]:
        """Verify that assembly child units match the box build template."""
        return run_sync(self._async_service.verify_assembly(
            serial_number, part_number, revision
        ))

    # =========================================================================
    # Serial Numbers - Public API
    # =========================================================================

    def allocate_serial_numbers(
        self,
        type_name: str,
        count: int = 1,
        reference_sn: Optional[str] = None,
        reference_pn: Optional[str] = None,
        station_name: Optional[str] = None
    ) -> List[str]:
        """Allocate serial numbers from pool."""
        return run_sync(self._async_service.allocate_serial_numbers(
            type_name, count, reference_sn, reference_pn, station_name
        ))

    def find_serial_numbers_in_range(
        self,
        type_name: str,
        from_serial: str,
        to_serial: str
    ) -> List[Dict[str, Any]]:
        """Find serial numbers in a range."""
        return run_sync(self._async_service.find_serial_numbers_in_range(
            type_name, from_serial, to_serial
        ))

    def find_serial_numbers_by_reference(
        self,
        type_name: str,
        reference_serial: Optional[str] = None,
        reference_part: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find serial numbers by reference."""
        return run_sync(self._async_service.find_serial_numbers_by_reference(
            type_name, reference_serial, reference_part
        ))

    def import_serial_numbers(
        self,
        file_content: bytes,
        content_type: str = "text/csv"
    ) -> bool:
        """Import serial numbers from file (XML or CSV)."""
        return run_sync(self._async_service.import_serial_numbers(file_content, content_type))

    def export_serial_numbers(
        self,
        type_name: str,
        state: Optional[str] = None,
        format: str = "csv"
    ) -> Optional[bytes]:
        """Export serial numbers as file."""
        return run_sync(self._async_service.export_serial_numbers(type_name, state, format))

    # =========================================================================
    # ⚠️ INTERNAL API - Connection Check
    # =========================================================================

    def is_connected(self) -> bool:
        """⚠️ INTERNAL: Check if Production module is connected."""
        return run_sync(self._async_service.is_connected())

    # =========================================================================
    # ⚠️ INTERNAL API - Sites
    # =========================================================================

    def get_sites(self) -> List[Dict[str, Any]]:
        """⚠️ INTERNAL: Get all production sites."""
        return run_sync(self._async_service.get_sites())

    # =========================================================================
    # ⚠️ INTERNAL API - Unit Operations
    # =========================================================================

    def get_unit_info(
        self,
        serial_number: str,
        part_number: str
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Get detailed unit information."""
        return run_sync(self._async_service.get_unit_info(serial_number, part_number))

    def get_unit_hierarchy(
        self,
        serial_number: str,
        part_number: str
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Get the complete unit hierarchy."""
        return run_sync(self._async_service.get_unit_hierarchy(serial_number, part_number))

    def get_unit_state_history(
        self,
        serial_number: str,
        part_number: str
    ) -> List[Dict[str, Any]]:
        """⚠️ INTERNAL: Get the unit state change history."""
        return run_sync(self._async_service.get_unit_state_history(serial_number, part_number))

    def get_unit_contents(
        self,
        serial_number: str,
        part_number: str,
        revision: str
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Get unit contents (BOM/components)."""
        return run_sync(self._async_service.get_unit_contents(
            serial_number, part_number, revision
        ))

    def create_unit(
        self,
        serial_number: str,
        part_number: str,
        revision: str,
        batch_number: Optional[str] = None,
        unit_phase: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Create a new unit in the production system."""
        return run_sync(self._async_service.create_unit(
            serial_number, part_number, revision, batch_number, unit_phase
        ))

    # =========================================================================
    # ⚠️ INTERNAL API - Child Unit Operations
    # =========================================================================

    def add_child_unit_validated(
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
        """⚠️ INTERNAL: Add a child unit to a parent unit with validation."""
        return run_sync(self._async_service.add_child_unit_validated(
            serial_number, part_number, child_serial_number, child_part_number,
            check_part_number, check_revision, culture_code, check_phase
        ))

    def remove_child_unit_localized(
        self,
        serial_number: str,
        part_number: str,
        child_serial_number: str,
        child_part_number: str,
        culture_code: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Remove a child unit from a parent unit."""
        return run_sync(self._async_service.remove_child_unit_localized(
            serial_number, part_number, child_serial_number, child_part_number, culture_code
        ))

    def remove_all_child_units(
        self,
        serial_number: str,
        part_number: str,
        culture_code: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Remove all child units from a parent unit."""
        return run_sync(self._async_service.remove_all_child_units(
            serial_number, part_number, culture_code
        ))

    def validate_child_units(
        self,
        parent_serial_number: str,
        parent_part_number: str,
        culture_code: str = "en-US"
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Validate child units of a parent unit."""
        return run_sync(self._async_service.validate_child_units(
            parent_serial_number, parent_part_number, culture_code
        ))

    # =========================================================================
    # ⚠️ INTERNAL API - Serial Number Management
    # =========================================================================

    def find_serial_numbers(
        self,
        serial_number_type: str,
        start_address: str,
        end_address: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """⚠️ INTERNAL: Find all serial numbers in a range."""
        return run_sync(self._async_service.find_serial_numbers(
            serial_number_type, start_address, end_address, start_date, end_date
        ))

    def get_serial_number_count(
        self,
        serial_number_type: str,
        start_address: Optional[str] = None,
        end_address: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Optional[int]:
        """⚠️ INTERNAL: Get count of serial numbers in a range."""
        return run_sync(self._async_service.get_serial_number_count(
            serial_number_type, start_address, end_address, from_date, to_date
        ))

    def free_serial_numbers(
        self,
        ranges: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Free reserved serial numbers in specified ranges."""
        return run_sync(self._async_service.free_serial_numbers(ranges))

    def get_serial_number_ranges(
        self,
        serial_number_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """⚠️ INTERNAL: Get current serial number ranges."""
        return run_sync(self._async_service.get_serial_number_ranges(serial_number_type))

    def get_serial_number_statistics(
        self,
        serial_number_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """⚠️ INTERNAL: Get statistics for serial numbers."""
        return run_sync(self._async_service.get_serial_number_statistics(serial_number_type))
