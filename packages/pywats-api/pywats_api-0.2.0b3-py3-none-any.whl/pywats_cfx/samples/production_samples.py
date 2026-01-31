"""
CFX Production Flow Sample Messages.

Based on IPC-CFX SDK examples for work tracking.
"""

# =============================================================================
# WorkStarted
# =============================================================================

WORK_STARTED_SAMPLE = {
    "MessageName": "CFX.Production.WorkStarted",
    "TransactionId": "f6a7b8c9-d0e1-2345-f012-678901234567",
    "Lane": 1,
    "Stage": "SMT_Placement",
    "Units": [
        {
            "PositionNumber": 1,
            "PositionName": "Panel_Position_1",
            "UnitIdentifier": "PCB-2026012600100",
            "X": 0.0,
            "Y": 0.0,
            "Rotation": 0.0
        },
        {
            "PositionNumber": 2,
            "PositionName": "Panel_Position_2", 
            "UnitIdentifier": "PCB-2026012600101",
            "X": 150.0,
            "Y": 0.0,
            "Rotation": 0.0
        },
        {
            "PositionNumber": 3,
            "PositionName": "Panel_Position_3",
            "UnitIdentifier": "PCB-2026012600102",
            "X": 300.0,
            "Y": 0.0,
            "Rotation": 0.0
        }
    ]
}

# =============================================================================
# WorkCompleted - Passed
# =============================================================================

WORK_COMPLETED_PASSED = {
    "MessageName": "CFX.Production.WorkCompleted",
    "TransactionId": "f6a7b8c9-d0e1-2345-f012-678901234567",  # Same as WorkStarted
    "Result": "Completed",
    "Lane": 1,
    "Stage": "SMT_Placement",
    "Units": [
        {
            "PositionNumber": 1,
            "UnitIdentifier": "PCB-2026012600100"
        },
        {
            "PositionNumber": 2,
            "UnitIdentifier": "PCB-2026012600101"
        },
        {
            "PositionNumber": 3,
            "UnitIdentifier": "PCB-2026012600102"
        }
    ]
}

# =============================================================================
# WorkCompleted - Failed/Aborted
# =============================================================================

WORK_COMPLETED_FAILED = {
    "MessageName": "CFX.Production.WorkCompleted",
    "TransactionId": "a7b8c9d0-e1f2-3456-0123-789012345678",
    "Result": "Aborted",
    "Lane": 2,
    "Stage": "Reflow",
    "Units": [
        {
            "PositionNumber": 1,
            "UnitIdentifier": "PCB-2026012600200"
        }
    ]
}

# =============================================================================
# UnitsArrived
# =============================================================================

UNITS_ARRIVED_SAMPLE = {
    "MessageName": "CFX.Production.UnitsArrived",
    "TransactionId": "b8c9d0e1-f2a3-4567-1234-890123456789",
    "Lane": 1,
    "Stage": "Reflow_Oven",
    "Units": [
        {
            "PositionNumber": 1,
            "UnitIdentifier": "PCB-2026012600100",
            "X": 0.0,
            "Y": 0.0
        },
        {
            "PositionNumber": 2,
            "UnitIdentifier": "PCB-2026012600101",
            "X": 150.0,
            "Y": 0.0
        }
    ]
}

# =============================================================================
# UnitsDeparted
# =============================================================================

UNITS_DEPARTED_SAMPLE = {
    "MessageName": "CFX.Production.UnitsDeparted",
    "TransactionId": "b8c9d0e1-f2a3-4567-1234-890123456789",
    "Lane": 1,
    "Stage": "Reflow_Oven",
    "Units": [
        {
            "PositionNumber": 1,
            "UnitIdentifier": "PCB-2026012600100"
        },
        {
            "PositionNumber": 2,
            "UnitIdentifier": "PCB-2026012600101"
        }
    ]
}

# =============================================================================
# UnitsDisqualified
# =============================================================================

UNITS_DISQUALIFIED_SAMPLE = {
    "MessageName": "CFX.Production.UnitsDisqualified",
    "TransactionId": "c9d0e1f2-a3b4-5678-2345-901234567890",
    "Lane": 1,
    "Stage": "AOI_Post_Reflow",
    "Reason": "Failed AOI inspection - multiple solder defects",
    "DisqualifiedUnits": [
        {
            "UnitIdentifier": "PCB-2026012600055",
            "PositionNumber": 1,
            "Reason": "Solder bridge on U1 pins 12-13",
            "DefectsFound": ["SOLDER_BRIDGE", "INSUFFICIENT_SOLDER"]
        }
    ]
}
