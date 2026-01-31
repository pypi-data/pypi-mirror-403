"""
CFX Resource/Endpoint Sample Messages.

Based on IPC-CFX SDK examples for faults and state changes.
"""

# =============================================================================
# FaultOccurred - Temperature
# =============================================================================

FAULT_OCCURRED_TEMPERATURE = {
    "MessageName": "CFX.ResourcePerformance.FaultOccurred",
    "Lane": 1,
    "Stage": "Reflow_Zone_3",
    "Fault": {
        "Cause": "Zone temperature exceeded upper threshold",
        "Severity": "Error",
        "FaultCode": "TEMP_HIGH_Z3",
        "FaultOccurrenceId": "FAULT-2026012600001",
        "OccurrenceType": "Continuous",
        "OccurredAt": "2026-01-26T14:30:00.000",
        "Description": "Reflow oven zone 3 temperature exceeded 265°C threshold. Current reading: 272°C",
        "DescriptionTranslations": {
            "de": "Reflow-Ofen Zone 3 Temperatur überschreitet 265°C Schwellenwert. Aktueller Wert: 272°C",
            "zh": "回流炉3区温度超过265°C阈值。当前读数：272°C"
        },
        "ComponentOfInterest": "Zone3_Heater",
        "RelatedUnits": ["PCB-2026012600100", "PCB-2026012600101"]
    }
}

# =============================================================================
# FaultOccurred - Feeder Error
# =============================================================================

FAULT_OCCURRED_FEEDER = {
    "MessageName": "CFX.ResourcePerformance.FaultOccurred",
    "Lane": 1,
    "Stage": "SMT_Placement",
    "Fault": {
        "Cause": "Feeder component pickup failure",
        "Severity": "Warning",
        "FaultCode": "FEEDER_PICKUP_FAIL",
        "FaultOccurrenceId": "FAULT-2026012600002",
        "OccurrenceType": "Momentary",
        "OccurredAt": "2026-01-26T09:15:30.500",
        "Description": "Component pickup failed on Feeder F01 after 3 retry attempts. Possible causes: empty reel, tape jam, or nozzle issue.",
        "ComponentOfInterest": "Feeder_F01",
        "RelatedUnits": ["PCB-2026012600042"]
    }
}

# =============================================================================
# FaultCleared
# =============================================================================

FAULT_CLEARED_SAMPLE = {
    "MessageName": "CFX.ResourcePerformance.FaultCleared",
    "FaultOccurrenceId": "FAULT-2026012600001"
}

# =============================================================================
# StationStateChanged - Various Examples
# =============================================================================

STATION_STATE_CHANGED_SAMPLES = [
    # Startup sequence
    {
        "MessageName": "CFX.ResourcePerformance.StationStateChanged",
        "OldState": "Off",
        "NewState": "Standby",
        "OldStateDuration": None
    },
    # Ready to process
    {
        "MessageName": "CFX.ResourcePerformance.StationStateChanged",
        "OldState": "Standby",
        "NewState": "ReadyProcessing",
        "OldStateDuration": 120.5  # seconds in standby
    },
    # Starting work
    {
        "MessageName": "CFX.ResourcePerformance.StationStateChanged",
        "OldState": "ReadyProcessing",
        "NewState": "Processing",
        "OldStateDuration": 5.2
    },
    # Work complete, back to ready
    {
        "MessageName": "CFX.ResourcePerformance.StationStateChanged",
        "OldState": "Processing",
        "NewState": "ReadyProcessing",
        "OldStateDuration": 45.8  # Processing time
    },
    # Blocked due to downstream
    {
        "MessageName": "CFX.ResourcePerformance.StationStateChanged",
        "OldState": "Processing",
        "NewState": "Blocked",
        "OldStateDuration": 12.3
    },
    # Starved - waiting for input
    {
        "MessageName": "CFX.ResourcePerformance.StationStateChanged",
        "OldState": "ReadyProcessing",
        "NewState": "Starved",
        "OldStateDuration": 30.0
    },
    # Going into maintenance
    {
        "MessageName": "CFX.ResourcePerformance.StationStateChanged",
        "OldState": "ReadyProcessing",
        "NewState": "ScheduledMaintenance",
        "OldStateDuration": 3600.0  # 1 hour of operation
    },
    # Error state
    {
        "MessageName": "CFX.ResourcePerformance.StationStateChanged",
        "OldState": "Processing",
        "NewState": "MachineError",
        "OldStateDuration": 8.5
    },
    # Recovery from error
    {
        "MessageName": "CFX.ResourcePerformance.StationStateChanged",
        "OldState": "MachineError",
        "NewState": "Standby",
        "OldStateDuration": 180.0  # 3 minutes in error
    },
    # Shutdown
    {
        "MessageName": "CFX.ResourcePerformance.StationStateChanged",
        "OldState": "Standby",
        "NewState": "Off",
        "OldStateDuration": 60.0
    }
]

# =============================================================================
# EndpointConnected / Disconnected
# =============================================================================

ENDPOINT_CONNECTED_SAMPLE = {
    "MessageName": "CFX.Transport.EndpointConnected",
    "CFXHandle": "//Virinco/WATS/TestStation001"
}

ENDPOINT_DISCONNECTED_SAMPLE = {
    "MessageName": "CFX.Transport.EndpointDisconnected",
    "CFXHandle": "//Virinco/WATS/TestStation001"
}

# =============================================================================
# GetEndpointInformation Response
# =============================================================================

ENDPOINT_INFO_RESPONSE = {
    "MessageName": "CFX.GetEndpointInformationResponse",
    "CFXHandle": "//Virinco/WATS/TestStation001",
    "RequestNetworkUri": "amqp://cfx-broker.factory.local:5672",
    "RequestEncodingType": "JSON",
    "Vendor": "Virinco",
    "ModelNumber": "pyWATS-Client",
    "SerialNumber": "PYWATS-001",
    "SoftwareVersion": "1.0.0",
    "OperatorId": "OPERATOR001",
    "NumberOfLanes": 1,
    "NumberOfStages": 3
}
