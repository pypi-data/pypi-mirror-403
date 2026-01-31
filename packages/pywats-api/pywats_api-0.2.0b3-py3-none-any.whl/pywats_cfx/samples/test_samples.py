"""
CFX Test & Inspection Sample Messages.

Based on IPC-CFX SDK examples for UnitsTested and UnitsInspected.
"""

# =============================================================================
# UnitsTested - ICT (In-Circuit Test)
# =============================================================================

UNITS_TESTED_ICT = {
    "MessageName": "CFX.Production.Testing.UnitsTested",
    "TransactionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "TestMethod": "ICT",
    "TestedBy": "OPERATOR001",
    "Tester": "ICT-STATION-01",
    "TestStartTime": "2026-01-26T08:30:00.000",
    "TestEndTime": "2026-01-26T08:30:45.500",
    "RecipeName": "PCB_MAIN_ICT_V2",
    "RecipeRevision": "2.1.0",
    "Lane": 1,
    "Stage": "ICT",
    "TestedUnits": [
        {
            "UnitIdentifier": "SN-2026012600001",
            "UnitPositionNumber": 1,
            "OverallResult": "Passed",
            "RecipeRevision": "2.1.0",
            "Tests": [
                {
                    "TestName": "Power_Supply_Check",
                    "Result": "Passed",
                    "TestStartTime": "2026-01-26T08:30:00.500",
                    "TestEndTime": "2026-01-26T08:30:05.200",
                    "Measurements": [
                        {
                            "MeasurementName": "VCC_3V3",
                            "MeasuredValue": 3.298,
                            "ExpectedValue": 3.3,
                            "MeasurementUnits": "V",
                            "LowerLimit": 3.135,
                            "UpperLimit": 3.465,
                            "Result": "Passed",
                            "TimeStamp": "2026-01-26T08:30:01.000"
                        },
                        {
                            "MeasurementName": "VCC_5V",
                            "MeasuredValue": 5.021,
                            "ExpectedValue": 5.0,
                            "MeasurementUnits": "V",
                            "LowerLimit": 4.75,
                            "UpperLimit": 5.25,
                            "Result": "Passed",
                            "TimeStamp": "2026-01-26T08:30:02.000"
                        },
                        {
                            "MeasurementName": "VCC_12V",
                            "MeasuredValue": 11.95,
                            "ExpectedValue": 12.0,
                            "MeasurementUnits": "V",
                            "LowerLimit": 11.4,
                            "UpperLimit": 12.6,
                            "Result": "Passed",
                            "TimeStamp": "2026-01-26T08:30:03.000"
                        }
                    ],
                    "SymptomsFound": [],
                    "DefectsFound": []
                },
                {
                    "TestName": "Resistor_Network_R1_R10",
                    "Result": "Passed",
                    "TestStartTime": "2026-01-26T08:30:05.500",
                    "TestEndTime": "2026-01-26T08:30:15.000",
                    "Measurements": [
                        {
                            "MeasurementName": "R1",
                            "MeasuredValue": 9980,
                            "ExpectedValue": 10000,
                            "MeasurementUnits": "Ohm",
                            "LowerLimit": 9500,
                            "UpperLimit": 10500,
                            "Result": "Passed"
                        },
                        {
                            "MeasurementName": "R2",
                            "MeasuredValue": 4720,
                            "ExpectedValue": 4700,
                            "MeasurementUnits": "Ohm",
                            "LowerLimit": 4465,
                            "UpperLimit": 4935,
                            "Result": "Passed"
                        },
                        {
                            "MeasurementName": "R3",
                            "MeasuredValue": 1002,
                            "ExpectedValue": 1000,
                            "MeasurementUnits": "Ohm",
                            "LowerLimit": 950,
                            "UpperLimit": 1050,
                            "Result": "Passed"
                        }
                    ],
                    "SymptomsFound": [],
                    "DefectsFound": []
                },
                {
                    "TestName": "Capacitor_Check_C1_C5",
                    "Result": "Passed",
                    "TestStartTime": "2026-01-26T08:30:15.500",
                    "TestEndTime": "2026-01-26T08:30:25.000",
                    "Measurements": [
                        {
                            "MeasurementName": "C1",
                            "MeasuredValue": 98.5,
                            "ExpectedValue": 100,
                            "MeasurementUnits": "uF",
                            "LowerLimit": 80,
                            "UpperLimit": 120,
                            "Result": "Passed"
                        },
                        {
                            "MeasurementName": "C2",
                            "MeasuredValue": 10.2,
                            "ExpectedValue": 10,
                            "MeasurementUnits": "uF",
                            "LowerLimit": 8,
                            "UpperLimit": 12,
                            "Result": "Passed"
                        }
                    ],
                    "SymptomsFound": [],
                    "DefectsFound": []
                }
            ],
            "Symptoms": [],
            "Defects": []
        }
    ]
}

# =============================================================================
# UnitsTested - FCT (Functional Test) with FAILURE
# =============================================================================

UNITS_TESTED_FCT = {
    "MessageName": "CFX.Production.Testing.UnitsTested",
    "TransactionId": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
    "TestMethod": "FCT",
    "TestedBy": "OPERATOR002",
    "Tester": "FCT-STATION-03",
    "TestStartTime": "2026-01-26T09:15:00.000",
    "TestEndTime": "2026-01-26T09:17:30.250",
    "RecipeName": "SENSOR_BOARD_FCT",
    "RecipeRevision": "1.5.2",
    "Lane": 1,
    "Stage": "FCT",
    "TestedUnits": [
        {
            "UnitIdentifier": "SN-2026012600042",
            "UnitPositionNumber": 1,
            "OverallResult": "Failed",
            "Tests": [
                {
                    "TestName": "Boot_Sequence",
                    "Result": "Passed",
                    "TestStartTime": "2026-01-26T09:15:00.500",
                    "TestEndTime": "2026-01-26T09:15:10.000",
                    "Measurements": [
                        {
                            "MeasurementName": "BootTime",
                            "MeasuredValue": 2.35,
                            "ExpectedValue": 3.0,
                            "MeasurementUnits": "s",
                            "LowerLimit": 0,
                            "UpperLimit": 5.0,
                            "Result": "Passed"
                        }
                    ],
                    "SymptomsFound": [],
                    "DefectsFound": []
                },
                {
                    "TestName": "Sensor_Calibration",
                    "Result": "Failed",
                    "TestStartTime": "2026-01-26T09:15:10.500",
                    "TestEndTime": "2026-01-26T09:16:00.000",
                    "Measurements": [
                        {
                            "MeasurementName": "Temperature_Sensor_Offset",
                            "MeasuredValue": 5.8,
                            "ExpectedValue": 0,
                            "MeasurementUnits": "°C",
                            "LowerLimit": -2.0,
                            "UpperLimit": 2.0,
                            "Result": "Failed"
                        },
                        {
                            "MeasurementName": "Humidity_Sensor_Offset",
                            "MeasuredValue": 1.2,
                            "ExpectedValue": 0,
                            "MeasurementUnits": "%RH",
                            "LowerLimit": -3.0,
                            "UpperLimit": 3.0,
                            "Result": "Passed"
                        }
                    ],
                    "SymptomsFound": ["Temperature reading drift"],
                    "DefectsFound": ["TEMP_SENSOR_OOT"]
                },
                {
                    "TestName": "Communication_Test",
                    "Result": "Passed",
                    "TestStartTime": "2026-01-26T09:16:00.500",
                    "TestEndTime": "2026-01-26T09:17:00.000",
                    "Measurements": [
                        {
                            "MeasurementName": "I2C_Response_Time",
                            "MeasuredValue": 0.5,
                            "MeasurementUnits": "ms",
                            "LowerLimit": 0,
                            "UpperLimit": 2.0,
                            "Result": "Passed"
                        },
                        {
                            "MeasurementName": "SPI_Throughput",
                            "MeasuredValue": 8.5,
                            "MeasurementUnits": "Mbps",
                            "LowerLimit": 5.0,
                            "UpperLimit": None,
                            "Result": "Passed"
                        }
                    ],
                    "SymptomsFound": [],
                    "DefectsFound": []
                }
            ],
            "Symptoms": ["Temperature reading drift"],
            "Defects": ["TEMP_SENSOR_OOT"]
        }
    ]
}

# =============================================================================
# UnitsTested - Multiple Measurements (like NI TestStand)
# =============================================================================

UNITS_TESTED_MULTI_MEASUREMENT = {
    "MessageName": "CFX.Production.Testing.UnitsTested",
    "TransactionId": "c3d4e5f6-a7b8-9012-cdef-345678901234",
    "TestMethod": "MultiMeasurement",
    "TestedBy": "OPERATOR003",
    "Tester": "TEST-STATION-07",
    "TestStartTime": "2026-01-26T10:00:00.000",
    "TestEndTime": "2026-01-26T10:05:30.000",
    "RecipeName": "MOTOR_DRIVER_TEST",
    "Lane": 1,
    "TestedUnits": [
        {
            "UnitIdentifier": "MD-2026-00123",
            "OverallResult": "Passed",
            "Tests": [
                {
                    "TestName": "Motor_Current_Profile",
                    "Result": "Passed",
                    "Measurements": [
                        {
                            "MeasurementName": "Startup_Current",
                            "MeasuredValue": 2.5,
                            "MeasurementUnits": "A",
                            "LowerLimit": 2.0,
                            "UpperLimit": 3.5,
                            "Result": "Passed",
                            "Characteristics": {
                                "Phase": "A",
                                "LoadCondition": "No Load"
                            }
                        },
                        {
                            "MeasurementName": "Steady_State_Current",
                            "MeasuredValue": 0.85,
                            "MeasurementUnits": "A",
                            "LowerLimit": 0.5,
                            "UpperLimit": 1.2,
                            "Result": "Passed",
                            "Characteristics": {
                                "Phase": "A",
                                "LoadCondition": "No Load"
                            }
                        },
                        {
                            "MeasurementName": "Peak_Current",
                            "MeasuredValue": 4.2,
                            "MeasurementUnits": "A",
                            "LowerLimit": None,
                            "UpperLimit": 5.0,
                            "Result": "Passed",
                            "Characteristics": {
                                "Phase": "A",
                                "LoadCondition": "Full Load"
                            }
                        }
                    ],
                    "SymptomsFound": [],
                    "DefectsFound": []
                },
                {
                    "TestName": "PWM_Frequency_Check",
                    "Result": "Passed",
                    "Measurements": [
                        {
                            "MeasurementName": "PWM_Frequency",
                            "MeasuredValue": 20050,
                            "ExpectedValue": 20000,
                            "MeasurementUnits": "Hz",
                            "LowerLimit": 19000,
                            "UpperLimit": 21000,
                            "Result": "Passed"
                        },
                        {
                            "MeasurementName": "Duty_Cycle_Accuracy",
                            "MeasuredValue": 50.2,
                            "ExpectedValue": 50.0,
                            "MeasurementUnits": "%",
                            "LowerLimit": 49.0,
                            "UpperLimit": 51.0,
                            "Result": "Passed"
                        }
                    ],
                    "SymptomsFound": [],
                    "DefectsFound": []
                }
            ],
            "Symptoms": [],
            "Defects": []
        }
    ]
}

# =============================================================================
# UnitsInspected - AOI (Automated Optical Inspection)
# =============================================================================

UNITS_INSPECTED_AOI = {
    "MessageName": "CFX.Production.Assembly.UnitsInspected",
    "TransactionId": "d4e5f6a7-b8c9-0123-def0-456789012345",
    "InspectionMethod": "AOI",
    "InspectedBy": None,  # Automated
    "Inspector": "AOI-MACHINE-02",
    "InspectionStartTime": "2026-01-26T11:00:00.000",
    "InspectionEndTime": "2026-01-26T11:00:15.500",
    "RecipeName": "PCB_AOI_POSTPLACE",
    "RecipeRevision": "3.0.1",
    "InspectedUnits": [
        {
            "UnitIdentifier": "PCB-2026012600055",
            "UnitPositionNumber": 1,
            "OverallResult": "Failed",
            "Inspections": [
                {
                    "InspectionName": "Component_Presence",
                    "Result": "Passed",
                    "InspectedComponents": ["U1", "U2", "U3", "R1-R20", "C1-C15"]
                },
                {
                    "InspectionName": "Solder_Joint_Quality",
                    "Result": "Failed",
                    "InspectedComponents": ["U1", "U2"]
                },
                {
                    "InspectionName": "Component_Orientation",
                    "Result": "Passed",
                    "InspectedComponents": ["U1", "U2", "U3"]
                }
            ],
            "Defects": [
                {
                    "DefectCode": "SOLDER_BRIDGE",
                    "ComponentDesignator": "U1",
                    "Pin": "12-13",
                    "Severity": "Critical",
                    "X": 25.5,
                    "Y": 18.2,
                    "ImageFile": "defect_001.jpg"
                },
                {
                    "DefectCode": "INSUFFICIENT_SOLDER",
                    "ComponentDesignator": "U2",
                    "Pin": "5",
                    "Severity": "Major",
                    "X": 42.1,
                    "Y": 22.8,
                    "ImageFile": "defect_002.jpg"
                }
            ]
        },
        {
            "UnitIdentifier": "PCB-2026012600056",
            "UnitPositionNumber": 2,
            "OverallResult": "Passed",
            "Inspections": [
                {
                    "InspectionName": "Component_Presence",
                    "Result": "Passed"
                },
                {
                    "InspectionName": "Solder_Joint_Quality",
                    "Result": "Passed"
                },
                {
                    "InspectionName": "Component_Orientation",
                    "Result": "Passed"
                }
            ],
            "Defects": []
        }
    ]
}

# =============================================================================
# UnitsInspected - SPI (Solder Paste Inspection)
# =============================================================================

UNITS_INSPECTED_SPI = {
    "MessageName": "CFX.Production.Assembly.UnitsInspected",
    "TransactionId": "e5f6a7b8-c9d0-1234-ef01-567890123456",
    "InspectionMethod": "SPI",
    "Inspector": "SPI-KYHECK-01",
    "InspectionStartTime": "2026-01-26T07:45:00.000",
    "InspectionEndTime": "2026-01-26T07:45:08.200",
    "RecipeName": "SOLDER_PASTE_INSPECTION",
    "InspectedUnits": [
        {
            "UnitIdentifier": "PCB-2026012600033",
            "OverallResult": "Passed",
            "Inspections": [
                {
                    "InspectionName": "Paste_Volume",
                    "Result": "Passed",
                    "AverageVolume": 95.2,
                    "VolumeUnit": "%",
                    "MinVolume": 78.5,
                    "MaxVolume": 115.3
                },
                {
                    "InspectionName": "Paste_Height",
                    "Result": "Passed",
                    "AverageHeight": 125.5,
                    "HeightUnit": "um",
                    "MinHeight": 110,
                    "MaxHeight": 142
                },
                {
                    "InspectionName": "Paste_Area",
                    "Result": "Passed"
                }
            ],
            "Defects": []
        }
    ]
}
