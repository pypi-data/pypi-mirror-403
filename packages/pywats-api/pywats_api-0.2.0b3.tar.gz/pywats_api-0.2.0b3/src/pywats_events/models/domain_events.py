"""
Normalized domain event types for the pyWATS event system.

These are strongly-typed event payloads that represent domain-specific
events. They are protocol-agnostic and can be created from any transport
(CFX, MQTT, webhook, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from enum import Enum


class TestResult(Enum):
    """Test result status."""
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    SKIPPED = "skipped"
    ABORTED = "aborted"


class AssetState(Enum):
    """Equipment state."""
    ONLINE = "online"
    OFFLINE = "offline"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class SeverityLevel(Enum):
    """Fault severity level."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# =============================================================================
# Test & Inspection Events
# =============================================================================

@dataclass
class TestMeasurement:
    """
    A single measurement from a test.
    
    Attributes:
        name: Measurement name
        value: Measured value (numeric)
        unit: Unit of measurement
        status: Pass/fail status
        low_limit: Lower limit (if applicable)
        high_limit: Upper limit (if applicable)
        nominal: Nominal/expected value
        comp_op: Comparison operator (EQ, LT, GT, GELE, etc.)
    """
    name: str
    value: Optional[float] = None
    unit: str = "?"
    status: TestResult = TestResult.PASS
    low_limit: Optional[float] = None
    high_limit: Optional[float] = None
    nominal: Optional[float] = None
    comp_op: str = "GELE"
    
    def is_within_limits(self) -> bool:
        """Check if value is within limits."""
        if self.value is None:
            return True
        if self.low_limit is not None and self.value < self.low_limit:
            return False
        if self.high_limit is not None and self.value > self.high_limit:
            return False
        return True


@dataclass
class TestStep:
    """
    A test step with optional measurements.
    
    Attributes:
        name: Step name
        status: Step result
        start_time: Step start time
        end_time: Step end time
        measurements: Measurements taken in this step
        message: Status message or error
        step_type: Type of step (numeric, passfail, string, etc.)
    """
    name: str
    status: TestResult = TestResult.PASS
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    measurements: List[TestMeasurement] = field(default_factory=list)
    message: Optional[str] = None
    step_type: str = "passfail"
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Step duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None


@dataclass
class TestResultEvent:
    """
    Normalized test result event.
    
    This event represents a completed test on a unit. It can be created
    from CFX UnitsTested, MQTT messages, or any other test source.
    
    Attributes:
        unit_id: Unit serial number or identifier
        result: Overall test result
        part_number: Part number of the unit
        revision: Part revision
        station_id: Test station identifier
        operator_id: Operator identifier
        start_time: Test start time
        end_time: Test end time
        steps: Test steps with measurements
        test_socket: Test socket/position
        batch_sn: Batch serial number
        fixture_id: Test fixture identifier
        custom_data: Additional custom data
    """
    unit_id: str
    result: TestResult = TestResult.PASS
    part_number: Optional[str] = None
    revision: Optional[str] = None
    station_id: Optional[str] = None
    operator_id: Optional[str] = None
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    steps: List[TestStep] = field(default_factory=list)
    test_socket: Optional[int] = None
    batch_sn: Optional[str] = None
    fixture_id: Optional[str] = None
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Test duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None
    
    @property
    def passed(self) -> bool:
        """Whether the test passed."""
        return self.result == TestResult.PASS
    
    @property
    def measurement_count(self) -> int:
        """Total number of measurements across all steps."""
        return sum(len(step.measurements) for step in self.steps)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "unit_id": self.unit_id,
            "result": self.result.value,
            "part_number": self.part_number,
            "revision": self.revision,
            "station_id": self.station_id,
            "operator_id": self.operator_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "steps": [
                {
                    "name": s.name,
                    "status": s.status.value,
                    "measurements": [
                        {
                            "name": m.name,
                            "value": m.value,
                            "unit": m.unit,
                            "status": m.status.value,
                            "low_limit": m.low_limit,
                            "high_limit": m.high_limit,
                        }
                        for m in s.measurements
                    ]
                }
                for s in self.steps
            ],
            "custom_data": self.custom_data,
        }


@dataclass
class InspectionResultEvent:
    """
    Normalized inspection result event (AOI, visual, X-ray, etc.).
    
    Similar to TestResultEvent but focused on visual inspection data.
    """
    unit_id: str
    result: TestResult = TestResult.PASS
    part_number: Optional[str] = None
    station_id: Optional[str] = None
    inspection_type: str = "aoi"  # aoi, visual, xray, spi
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    defects: List[Dict[str, Any]] = field(default_factory=list)
    images: List[str] = field(default_factory=list)  # Image URLs/paths
    custom_data: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Asset & Resource Events
# =============================================================================

@dataclass
class AssetFaultEvent:
    """
    Normalized asset fault event.
    
    Represents an equipment fault, alarm, or error condition.
    
    Attributes:
        asset_id: Equipment identifier
        fault_code: Fault/error code
        fault_message: Human-readable fault message
        severity: Fault severity level
        timestamp: When the fault occurred
        cleared: Whether the fault has been cleared
        cleared_time: When the fault was cleared
        custom_data: Additional fault data
    """
    asset_id: str
    fault_code: str
    fault_message: str = ""
    severity: SeverityLevel = SeverityLevel.ERROR
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    cleared: bool = False
    cleared_time: Optional[datetime] = None
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "asset_id": self.asset_id,
            "fault_code": self.fault_code,
            "fault_message": self.fault_message,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "cleared": self.cleared,
            "cleared_time": self.cleared_time.isoformat() if self.cleared_time else None,
            "custom_data": self.custom_data,
        }


@dataclass
class AssetStateChangedEvent:
    """
    Normalized asset state change event.
    
    Represents equipment state transitions (online, offline, busy, etc.).
    """
    asset_id: str
    new_state: AssetState
    previous_state: Optional[AssetState] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: Optional[str] = None
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "asset_id": self.asset_id,
            "new_state": self.new_state.value if self.new_state else None,
            "previous_state": self.previous_state.value if self.previous_state else None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "reason": self.reason,
            "custom_data": self.custom_data,
        }


@dataclass
class MaintenanceEvent:
    """
    Normalized maintenance event.
    
    Represents maintenance performed on equipment.
    """
    asset_id: str
    maintenance_type: str  # scheduled, preventive, corrective
    description: str = ""
    performed_by: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_minutes: Optional[float] = None
    parts_replaced: List[str] = field(default_factory=list)
    custom_data: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Material Events
# =============================================================================

@dataclass
class InstalledComponent:
    """
    A component installed on a unit.
    
    Attributes:
        reference_designator: Component reference (e.g., R1, C5, U3)
        part_number: Component part number
        serial_number: Component serial number (if tracked)
        lot_number: Lot/batch number
        installed_time: When the component was installed
    """
    reference_designator: str
    part_number: Optional[str] = None
    serial_number: Optional[str] = None
    lot_number: Optional[str] = None
    installed_time: Optional[datetime] = None


@dataclass
class MaterialInstalledEvent:
    """
    Normalized material installation event.
    
    Represents components installed on a unit (BOM tracking).
    
    Attributes:
        unit_id: Unit serial number
        components: List of installed components
        station_id: Station where installation occurred
        timestamp: When the installation occurred
    """
    unit_id: str
    components: List[InstalledComponent] = field(default_factory=list)
    station_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def component_count(self) -> int:
        """Number of installed components."""
        return len(self.components)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "unit_id": self.unit_id,
            "components": [
                {
                    "reference_designator": c.reference_designator,
                    "part_number": c.part_number,
                    "serial_number": c.serial_number,
                    "lot_number": c.lot_number,
                }
                for c in self.components
            ],
            "station_id": self.station_id,
            "timestamp": self.timestamp.isoformat(),
            "custom_data": self.custom_data,
        }


# =============================================================================
# Production Events
# =============================================================================

@dataclass
class WorkStartedEvent:
    """
    Normalized work started event.
    
    Represents the start of work on a unit at a station.
    """
    unit_id: str
    station_id: str
    work_order_id: Optional[str] = None
    operator_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    lane: Optional[int] = None
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "unit_id": self.unit_id,
            "station_id": self.station_id,
            "work_order_id": self.work_order_id,
            "operator_id": self.operator_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "lane": self.lane,
            "custom_data": self.custom_data,
        }


@dataclass
class WorkCompletedEvent:
    """
    Normalized work completed event.
    
    Represents the completion of work on a unit at a station.
    """
    unit_id: str
    station_id: str
    result: Literal["completed", "failed", "aborted"] = "completed"
    work_order_id: Optional[str] = None
    operator_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Work duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "unit_id": self.unit_id,
            "station_id": self.station_id,
            "result": self.result,
            "work_order_id": self.work_order_id,
            "operator_id": self.operator_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "custom_data": self.custom_data,
        }


@dataclass
class UnitDisqualifiedEvent:
    """
    Normalized unit disqualification event.
    
    Represents a unit being removed from production flow.
    """
    unit_id: str
    reason: str
    station_id: Optional[str] = None
    disqualification_type: str = "scrapped"  # scrapped, reworked, returned
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    custom_data: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class WorkOrderEvent:
    """
    Normalized work order event.
    
    Represents work order creation or status updates.
    """
    work_order_id: str
    action: Literal["created", "updated", "started", "completed", "cancelled"]
    part_number: Optional[str] = None
    quantity: Optional[int] = None
    status: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    custom_data: Dict[str, Any] = field(default_factory=dict)
