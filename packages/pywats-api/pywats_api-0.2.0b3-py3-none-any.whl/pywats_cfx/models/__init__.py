"""
CFX Message Models.

Pydantic models for IPC-CFX message types.
"""

from pywats_cfx.models.cfx_messages import (
    # Base
    CFXMessage,
    # Enums
    TestResult,
    InspectionResult,
    FaultSeverity,
    FaultOccurrenceType,
    ResourceState,
    WorkResultState,
    # Test/Inspection
    UnitPosition,
    Measurement,
    Test,
    TestedUnit,
    UnitsTested,
    InspectedUnit,
    UnitsInspected,
    # Materials
    InstalledMaterial,
    MaterialPackage,
    MaterialsInstalled,
    MaterialsLoaded,
    MaterialsUnloaded,
    # Production
    WorkStarted,
    WorkCompleted,
    UnitsArrived,
    UnitsDeparted,
    UnitsDisqualified,
    # Resource
    Fault,
    FaultOccurred,
    FaultCleared,
    StationStateChanged,
    EndpointConnected,
    EndpointDisconnected,
    # Request/Response
    GetEndpointInformationRequest,
    GetEndpointInformationResponse,
    # Registry & helpers
    CFX_MESSAGE_TYPES,
    parse_cfx_message,
    serialize_cfx_message,
)

__all__ = [
    # Base
    "CFXMessage",
    # Enums
    "TestResult",
    "InspectionResult",
    "FaultSeverity",
    "FaultOccurrenceType",
    "ResourceState",
    "WorkResultState",
    # Test/Inspection
    "UnitPosition",
    "Measurement",
    "Test",
    "TestedUnit",
    "UnitsTested",
    "InspectedUnit",
    "UnitsInspected",
    # Materials
    "InstalledMaterial",
    "MaterialPackage",
    "MaterialsInstalled",
    "MaterialsLoaded",
    "MaterialsUnloaded",
    # Production
    "WorkStarted",
    "WorkCompleted",
    "UnitsArrived",
    "UnitsDeparted",
    "UnitsDisqualified",
    # Resource
    "Fault",
    "FaultOccurred",
    "FaultCleared",
    "StationStateChanged",
    "EndpointConnected",
    "EndpointDisconnected",
    # Request/Response
    "GetEndpointInformationRequest",
    "GetEndpointInformationResponse",
    # Registry & helpers
    "CFX_MESSAGE_TYPES",
    "parse_cfx_message",
    "serialize_cfx_message",
]
