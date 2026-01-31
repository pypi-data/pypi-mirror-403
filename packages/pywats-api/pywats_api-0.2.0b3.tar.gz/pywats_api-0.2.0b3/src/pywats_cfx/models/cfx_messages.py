"""
IPC-CFX Message Models.

Pydantic models representing IPC-CFX message types based on the CFX standard.
These models handle serialization/deserialization of CFX JSON messages.

Reference: https://www.ipc-cfx.org/
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# CFX Enums
# =============================================================================

class TestResult(str, Enum):
    """Test result status per IPC-CFX."""
    PASSED = "Passed"
    FAILED = "Failed"
    ERROR = "Error"
    ABORTED = "Aborted"
    TERMINATED = "Terminated"
    INDETERMINATE = "Indeterminate"


class InspectionResult(str, Enum):
    """Inspection result status per IPC-CFX."""
    PASSED = "Passed"
    FAILED = "Failed"
    DEFECTIVE = "Defective"


class FaultSeverity(str, Enum):
    """Fault severity level per IPC-CFX."""
    ERROR = "Error"
    WARNING = "Warning"
    INFORMATION = "Information"


class FaultOccurrenceType(str, Enum):
    """Type of fault occurrence."""
    MOMENTARY = "Momentary"
    CONTINUOUS = "Continuous"


class ResourceState(str, Enum):
    """Resource/machine state per IPC-CFX."""
    ONLINE = "On"
    OFFLINE = "Off"
    STANDBY = "Standby"
    ENGINEERING = "Engineering"
    READY_PROCESSING = "ReadyProcessing"
    PROCESSING = "Processing"
    PROCESSING_EXECUTING_RECIPE = "ProcessingExecutingRecipe"
    BLOCKED = "Blocked"
    STARVED = "Starved"
    MAINTENANCE = "Maintenance"
    MAINTENANCE_SCHEDULED = "ScheduledMaintenance"
    MAINTENANCE_UNSCHEDULED = "UnscheduledMaintenance"
    ERROR = "MachineError"
    SETUP = "Setup"
    TEARDOWN = "Teardown"


class WorkResultState(str, Enum):
    """Work completion result state."""
    COMPLETED = "Completed"
    ABORTED = "Aborted"


# =============================================================================
# CFX Base Message
# =============================================================================

class CFXMessage(BaseModel):
    """
    Base class for all CFX messages.
    
    Every CFX message has a header with topic, sender, timestamp, and unique ID.
    """
    
    # Standard CFX header fields
    MessageName: str = Field(..., description="CFX message type name")
    CFX_MessageHandle: Optional[str] = Field(None, description="Unique message identifier")
    RequestID: Optional[str] = Field(None, description="Request correlation ID")
    
    class Config:
        """Pydantic config."""
        extra = "allow"  # Allow extra fields for extensibility
        use_enum_values = True


# =============================================================================
# Test & Inspection Messages
# =============================================================================

class UnitPosition(BaseModel):
    """Position of a unit on a carrier/panel."""
    PositionNumber: int = Field(..., description="Position on carrier")
    PositionName: Optional[str] = Field(None, description="Position name/label")
    UnitIdentifier: Optional[str] = Field(None, description="Unique unit identifier")
    X: Optional[float] = Field(None, description="X position in mm")
    Y: Optional[float] = Field(None, description="Y position in mm")
    Rotation: Optional[float] = Field(None, description="Rotation in degrees")


class Measurement(BaseModel):
    """A single measurement value with limits and result."""
    MeasurementName: str = Field(..., description="Name of measurement")
    MeasuredValue: Optional[Any] = Field(None, description="Measured value")
    ExpectedValue: Optional[Any] = Field(None, description="Expected value")
    MeasurementUnits: Optional[str] = Field(None, description="Unit of measurement")
    LowerLimit: Optional[float] = Field(None, description="Lower specification limit")
    UpperLimit: Optional[float] = Field(None, description="Upper specification limit")
    Result: Optional[TestResult] = Field(None, description="Measurement result")
    TimeStamp: Optional[datetime] = Field(None, description="When measurement was taken")
    Characteristics: Optional[dict[str, Any]] = Field(default_factory=dict)


class Test(BaseModel):
    """A test step with multiple measurements."""
    TestName: str = Field(..., description="Name of test")
    Result: TestResult = Field(..., description="Test result")
    TestStartTime: Optional[datetime] = Field(None, description="Test start time")
    TestEndTime: Optional[datetime] = Field(None, description="Test end time")
    Measurements: list[Measurement] = Field(default_factory=list)
    SymptomsFound: list[str] = Field(default_factory=list)
    DefectsFound: list[str] = Field(default_factory=list)


class TestedUnit(BaseModel):
    """Test results for a single unit."""
    UnitIdentifier: str = Field(..., description="Unique unit identifier")
    UnitPositionNumber: Optional[int] = Field(None, description="Position on carrier")
    OverallResult: TestResult = Field(..., description="Overall test result")
    Tests: list[Test] = Field(default_factory=list)
    Symptoms: list[str] = Field(default_factory=list)
    Defects: list[str] = Field(default_factory=list)
    RecipeRevision: Optional[str] = Field(None, description="Test recipe version")


class UnitsTested(CFXMessage):
    """
    CFX.Production.Testing.UnitsTested message.
    
    Published when one or more units have completed testing at a test station.
    """
    MessageName: str = "CFX.Production.Testing.UnitsTested"
    
    TransactionId: UUID = Field(..., description="Transaction identifier")
    TestMethod: Optional[str] = Field(None, description="Test method used (ICT, FCT, etc.)")
    TestedBy: Optional[str] = Field(None, description="Operator identifier")
    Tester: Optional[str] = Field(None, description="Test equipment identifier")
    TestStartTime: datetime = Field(..., description="When testing started")
    TestEndTime: datetime = Field(..., description="When testing completed")
    TestedUnits: list[TestedUnit] = Field(default_factory=list)
    RecipeName: Optional[str] = Field(None, description="Test recipe name")
    RecipeRevision: Optional[str] = Field(None, description="Test recipe version")
    Lane: Optional[int] = Field(None, description="Lane number")
    Stage: Optional[str] = Field(None, description="Stage identifier")


class InspectedUnit(BaseModel):
    """Inspection results for a single unit."""
    UnitIdentifier: str = Field(..., description="Unique unit identifier")
    UnitPositionNumber: Optional[int] = Field(None, description="Position on carrier")
    OverallResult: InspectionResult = Field(..., description="Overall inspection result")
    Inspections: list[dict[str, Any]] = Field(default_factory=list)
    Defects: list[dict[str, Any]] = Field(default_factory=list)


class UnitsInspected(CFXMessage):
    """
    CFX.Production.Assembly.UnitsInspected message.
    
    Published when units have been inspected (AOI, SPI, X-ray, etc.).
    """
    MessageName: str = "CFX.Production.Assembly.UnitsInspected"
    
    TransactionId: UUID = Field(..., description="Transaction identifier")
    InspectionMethod: Optional[str] = Field(None, description="Inspection method")
    InspectedBy: Optional[str] = Field(None, description="Operator identifier")
    Inspector: Optional[str] = Field(None, description="Inspection equipment ID")
    InspectionStartTime: datetime = Field(..., description="Inspection start")
    InspectionEndTime: datetime = Field(..., description="Inspection end")
    InspectedUnits: list[InspectedUnit] = Field(default_factory=list)
    RecipeName: Optional[str] = Field(None, description="Inspection recipe")
    RecipeRevision: Optional[str] = Field(None, description="Recipe version")


# =============================================================================
# Material Messages  
# =============================================================================

class InstalledMaterial(BaseModel):
    """Information about installed material/component."""
    UnitIdentifier: str = Field(..., description="Unit receiving material")
    UnitPositionNumber: Optional[int] = Field(None, description="Position on carrier")
    InstalledComponents: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Components installed on this unit"
    )


class MaterialPackage(BaseModel):
    """Information about a material package (reel, tray, etc.)."""
    UniqueIdentifier: str = Field(..., description="Package unique ID")
    InternalPartNumber: Optional[str] = Field(None, description="Internal part number")
    ManufacturerPartNumber: Optional[str] = Field(None, description="Manufacturer PN")
    Vendor: Optional[str] = Field(None, description="Vendor name")
    ManufacturerLotCode: Optional[str] = Field(None, description="Lot code")
    DateCode: Optional[str] = Field(None, description="Date code")
    Quantity: Optional[float] = Field(None, description="Quantity in package")
    Status: Optional[str] = Field(None, description="Package status")


class MaterialsInstalled(CFXMessage):
    """
    CFX.Production.Assembly.MaterialsInstalled message.
    
    Published when materials are installed on units during assembly.
    """
    MessageName: str = "CFX.Production.Assembly.MaterialsInstalled"
    
    TransactionId: UUID = Field(..., description="Transaction identifier")
    InstalledMaterials: list[InstalledMaterial] = Field(default_factory=list)


class MaterialsLoaded(CFXMessage):
    """
    CFX.ResourcePerformance.MaterialsLoaded message.
    
    Published when materials are loaded into a machine/feeder.
    """
    MessageName: str = "CFX.ResourcePerformance.MaterialsLoaded"
    
    Materials: list[dict[str, Any]] = Field(default_factory=list)


class MaterialsUnloaded(CFXMessage):
    """
    CFX.ResourcePerformance.MaterialsUnloaded message.
    
    Published when materials are unloaded from a machine.
    """
    MessageName: str = "CFX.ResourcePerformance.MaterialsUnloaded"
    
    Materials: list[dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Production Messages
# =============================================================================

class WorkStarted(CFXMessage):
    """
    CFX.Production.WorkStarted message.
    
    Published when work begins on units at a station.
    """
    MessageName: str = "CFX.Production.WorkStarted"
    
    TransactionId: UUID = Field(..., description="Transaction identifier")
    Lane: Optional[int] = Field(None, description="Lane number")
    Stage: Optional[str] = Field(None, description="Stage identifier")
    Units: list[UnitPosition] = Field(default_factory=list)


class WorkCompleted(CFXMessage):
    """
    CFX.Production.WorkCompleted message.
    
    Published when work is completed on units at a station.
    """
    MessageName: str = "CFX.Production.WorkCompleted"
    
    TransactionId: UUID = Field(..., description="Transaction identifier")
    Result: WorkResultState = Field(..., description="Work result")
    Lane: Optional[int] = Field(None, description="Lane number")
    Stage: Optional[str] = Field(None, description="Stage identifier")
    Units: list[UnitPosition] = Field(default_factory=list)


class UnitsArrived(CFXMessage):
    """
    CFX.Production.UnitsArrived message.
    
    Published when units arrive at a station.
    """
    MessageName: str = "CFX.Production.UnitsArrived"
    
    TransactionId: Optional[UUID] = Field(None, description="Transaction identifier")
    Lane: Optional[int] = Field(None, description="Lane number")
    Stage: Optional[str] = Field(None, description="Stage identifier")
    Units: list[UnitPosition] = Field(default_factory=list)


class UnitsDeparted(CFXMessage):
    """
    CFX.Production.UnitsDeparted message.
    
    Published when units depart from a station.
    """
    MessageName: str = "CFX.Production.UnitsDeparted"
    
    TransactionId: Optional[UUID] = Field(None, description="Transaction identifier")
    Lane: Optional[int] = Field(None, description="Lane number")
    Stage: Optional[str] = Field(None, description="Stage identifier")
    Units: list[UnitPosition] = Field(default_factory=list)


class UnitsDisqualified(CFXMessage):
    """
    CFX.Production.UnitsDisqualified message.
    
    Published when units are disqualified/rejected.
    """
    MessageName: str = "CFX.Production.UnitsDisqualified"
    
    TransactionId: Optional[UUID] = Field(None, description="Transaction identifier")
    Lane: Optional[int] = Field(None, description="Lane number")
    Stage: Optional[str] = Field(None, description="Stage identifier")
    DisqualifiedUnits: list[dict[str, Any]] = Field(default_factory=list)
    Reason: Optional[str] = Field(None, description="Disqualification reason")


# =============================================================================
# Resource/Endpoint Messages
# =============================================================================

class FaultOccurred(CFXMessage):
    """
    CFX.ResourcePerformance.FaultOccurred message.
    
    Published when a fault/error occurs at an endpoint.
    """
    MessageName: str = "CFX.ResourcePerformance.FaultOccurred"
    
    Fault: dict[str, Any] = Field(default_factory=dict)
    Lane: Optional[int] = Field(None, description="Lane number")
    Stage: Optional[str] = Field(None, description="Stage identifier")


class Fault(BaseModel):
    """Fault/error information."""
    Cause: str = Field(..., description="Fault cause code/description")
    Severity: FaultSeverity = Field(..., description="Fault severity")
    FaultCode: Optional[str] = Field(None, description="Fault code")
    FaultOccurrenceId: Optional[str] = Field(None, description="Unique fault ID")
    OccurrenceType: Optional[FaultOccurrenceType] = Field(None)
    OccurredAt: Optional[datetime] = Field(None, description="When fault occurred")
    Description: Optional[str] = Field(None, description="Fault description")
    DescriptionTranslations: Optional[dict[str, str]] = Field(default_factory=dict)
    ComponentOfInterest: Optional[str] = Field(None, description="Affected component")
    RelatedUnits: list[str] = Field(default_factory=list)


class FaultCleared(CFXMessage):
    """
    CFX.ResourcePerformance.FaultCleared message.
    
    Published when a fault is cleared/resolved.
    """
    MessageName: str = "CFX.ResourcePerformance.FaultCleared"
    
    FaultOccurrenceId: str = Field(..., description="ID of cleared fault")


class StationStateChanged(CFXMessage):
    """
    CFX.ResourcePerformance.StationStateChanged message.
    
    Published when a station's operational state changes.
    """
    MessageName: str = "CFX.ResourcePerformance.StationStateChanged"
    
    OldState: ResourceState = Field(..., description="Previous state")
    NewState: ResourceState = Field(..., description="New state")
    OldStateDuration: Optional[float] = Field(None, description="Duration in old state (seconds)")


class EndpointConnected(CFXMessage):
    """
    CFX.Transport.EndpointConnected message.
    
    Published when an endpoint connects to the CFX network.
    """
    MessageName: str = "CFX.Transport.EndpointConnected"
    
    CFXHandle: str = Field(..., description="Endpoint CFX handle")


class EndpointDisconnected(CFXMessage):
    """
    CFX.Transport.EndpointDisconnected message.
    
    Published when an endpoint disconnects from the CFX network.
    """
    MessageName: str = "CFX.Transport.EndpointDisconnected"
    
    CFXHandle: str = Field(..., description="Endpoint CFX handle")


# =============================================================================
# Request/Response Messages
# =============================================================================

class GetEndpointInformationRequest(CFXMessage):
    """Request endpoint information."""
    MessageName: str = "CFX.GetEndpointInformationRequest"


class GetEndpointInformationResponse(CFXMessage):
    """Response with endpoint information."""
    MessageName: str = "CFX.GetEndpointInformationResponse"
    
    CFXHandle: str = Field(..., description="Endpoint CFX handle")
    RequestNetworkUri: Optional[str] = Field(None, description="Request URI")
    RequestEncodingType: Optional[str] = Field(None, description="Encoding type")
    Vendor: Optional[str] = Field(None, description="Endpoint vendor")
    ModelNumber: Optional[str] = Field(None, description="Model number")
    SerialNumber: Optional[str] = Field(None, description="Serial number")
    SoftwareVersion: Optional[str] = Field(None, description="Software version")
    OperatorId: Optional[str] = Field(None, description="Current operator")
    NumberOfLanes: Optional[int] = Field(None, description="Number of lanes")
    NumberOfStages: Optional[int] = Field(None, description="Number of stages")


# =============================================================================
# Message Type Registry
# =============================================================================

CFX_MESSAGE_TYPES: dict[str, type[CFXMessage]] = {
    # Testing
    "CFX.Production.Testing.UnitsTested": UnitsTested,
    "CFX.Production.Assembly.UnitsInspected": UnitsInspected,
    
    # Materials
    "CFX.Production.Assembly.MaterialsInstalled": MaterialsInstalled,
    "CFX.ResourcePerformance.MaterialsLoaded": MaterialsLoaded,
    "CFX.ResourcePerformance.MaterialsUnloaded": MaterialsUnloaded,
    
    # Production
    "CFX.Production.WorkStarted": WorkStarted,
    "CFX.Production.WorkCompleted": WorkCompleted,
    "CFX.Production.UnitsArrived": UnitsArrived,
    "CFX.Production.UnitsDeparted": UnitsDeparted,
    "CFX.Production.UnitsDisqualified": UnitsDisqualified,
    
    # Resource
    "CFX.ResourcePerformance.FaultOccurred": FaultOccurred,
    "CFX.ResourcePerformance.FaultCleared": FaultCleared,
    "CFX.ResourcePerformance.StationStateChanged": StationStateChanged,
    
    # Transport
    "CFX.Transport.EndpointConnected": EndpointConnected,
    "CFX.Transport.EndpointDisconnected": EndpointDisconnected,
    
    # Info
    "CFX.GetEndpointInformationRequest": GetEndpointInformationRequest,
    "CFX.GetEndpointInformationResponse": GetEndpointInformationResponse,
}


def parse_cfx_message(data: dict[str, Any]) -> CFXMessage:
    """
    Parse a CFX message from JSON data.
    
    Args:
        data: Parsed JSON data with MessageName field.
        
    Returns:
        Typed CFX message instance.
        
    Raises:
        ValueError: If MessageName is missing or unknown.
    """
    message_name = data.get("MessageName")
    if not message_name:
        raise ValueError("CFX message must have MessageName field")
    
    message_class = CFX_MESSAGE_TYPES.get(message_name, CFXMessage)
    return message_class.model_validate(data)


def serialize_cfx_message(message: CFXMessage) -> dict[str, Any]:
    """
    Serialize a CFX message to JSON-compatible dict.
    
    Args:
        message: CFX message instance.
        
    Returns:
        Dict ready for JSON serialization.
    """
    return message.model_dump(mode="json", exclude_none=True)
