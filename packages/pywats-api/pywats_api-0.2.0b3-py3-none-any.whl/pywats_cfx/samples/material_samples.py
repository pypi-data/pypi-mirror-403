"""
CFX Material Sample Messages.

Based on IPC-CFX SDK examples for material/component tracking.
"""

# =============================================================================
# MaterialsInstalled - SMT Components
# =============================================================================

MATERIALS_INSTALLED_SMT = {
    "MessageName": "CFX.Production.Assembly.MaterialsInstalled",
    "TransactionId": "d0e1f2a3-b4c5-6789-3456-012345678901",
    "InstalledMaterials": [
        {
            "UnitIdentifier": "PCB-2026012600100",
            "UnitPositionNumber": 1,
            "InstalledComponents": [
                {
                    "ReferenceDesignator": "U1",
                    "InternalPartNumber": "MCU-STM32F401",
                    "ManufacturerPartNumber": "STM32F401RET6",
                    "Manufacturer": "STMicroelectronics",
                    "LotCode": "LOT-2025-Q4-001",
                    "DateCode": "2548",
                    "ComponentSerialNumber": None,
                    "Quantity": 1,
                    "FeederLocation": "F01",
                    "HeadAndNozzle": "Head1-Nozzle2"
                },
                {
                    "ReferenceDesignator": "U2",
                    "InternalPartNumber": "FLASH-W25Q128",
                    "ManufacturerPartNumber": "W25Q128JVSIQ",
                    "Manufacturer": "Winbond",
                    "LotCode": "LOT-2025-Q3-042",
                    "DateCode": "2542",
                    "Quantity": 1,
                    "FeederLocation": "F02"
                },
                {
                    "ReferenceDesignator": "R1",
                    "InternalPartNumber": "RES-0603-10K",
                    "ManufacturerPartNumber": "RC0603FR-0710KL",
                    "Manufacturer": "Yageo",
                    "LotCode": "LOT-2025-Q4-100",
                    "Quantity": 1,
                    "FeederLocation": "F10"
                },
                {
                    "ReferenceDesignator": "R2",
                    "InternalPartNumber": "RES-0603-10K",
                    "ManufacturerPartNumber": "RC0603FR-0710KL",
                    "Manufacturer": "Yageo",
                    "LotCode": "LOT-2025-Q4-100",
                    "Quantity": 1,
                    "FeederLocation": "F10"
                },
                {
                    "ReferenceDesignator": "C1",
                    "InternalPartNumber": "CAP-0603-100N",
                    "ManufacturerPartNumber": "GRM188R71H104KA93D",
                    "Manufacturer": "Murata",
                    "LotCode": "LOT-2025-Q4-050",
                    "Quantity": 1,
                    "FeederLocation": "F20"
                },
                {
                    "ReferenceDesignator": "C2",
                    "InternalPartNumber": "CAP-0805-10U",
                    "ManufacturerPartNumber": "GRM21BR61A106KE19L",
                    "Manufacturer": "Murata",
                    "LotCode": "LOT-2025-Q4-051",
                    "Quantity": 1,
                    "FeederLocation": "F21"
                }
            ]
        },
        {
            "UnitIdentifier": "PCB-2026012600101",
            "UnitPositionNumber": 2,
            "InstalledComponents": [
                {
                    "ReferenceDesignator": "U1",
                    "InternalPartNumber": "MCU-STM32F401",
                    "ManufacturerPartNumber": "STM32F401RET6",
                    "Manufacturer": "STMicroelectronics",
                    "LotCode": "LOT-2025-Q4-001",
                    "DateCode": "2548",
                    "Quantity": 1,
                    "FeederLocation": "F01"
                }
                # ... more components same as first unit
            ]
        }
    ]
}

# =============================================================================
# MaterialsInstalled - Through-Hole Components
# =============================================================================

MATERIALS_INSTALLED_THROUGH_HOLE = {
    "MessageName": "CFX.Production.Assembly.MaterialsInstalled",
    "TransactionId": "e1f2a3b4-c5d6-7890-4567-123456789012",
    "InstalledMaterials": [
        {
            "UnitIdentifier": "PCB-2026012600100",
            "InstalledComponents": [
                {
                    "ReferenceDesignator": "J1",
                    "InternalPartNumber": "CONN-USB-C",
                    "ManufacturerPartNumber": "USB4110-GF-A",
                    "Manufacturer": "GCT",
                    "LotCode": "LOT-2025-Q4-200",
                    "Quantity": 1
                },
                {
                    "ReferenceDesignator": "J2",
                    "InternalPartNumber": "CONN-HDR-2X10",
                    "ManufacturerPartNumber": "TSW-110-07-G-D",
                    "Manufacturer": "Samtec",
                    "LotCode": "LOT-2025-Q3-150",
                    "Quantity": 1
                },
                {
                    "ReferenceDesignator": "SW1",
                    "InternalPartNumber": "SWITCH-TACT-6MM",
                    "ManufacturerPartNumber": "EVQP0N02B",
                    "Manufacturer": "Panasonic",
                    "LotCode": "LOT-2025-Q4-080",
                    "Quantity": 1
                }
            ]
        }
    ]
}

# =============================================================================
# MaterialsLoaded - Feeder Setup
# =============================================================================

MATERIALS_LOADED_FEEDER = {
    "MessageName": "CFX.ResourcePerformance.MaterialsLoaded",
    "Materials": [
        {
            "LocationIdentifier": "F01",
            "LocationName": "Feeder Bank A - Slot 1",
            "Material": {
                "UniqueIdentifier": "REEL-2026012600001",
                "InternalPartNumber": "MCU-STM32F401",
                "ManufacturerPartNumber": "STM32F401RET6",
                "Manufacturer": "STMicroelectronics",
                "ManufacturerLotCode": "LOT-2025-Q4-001",
                "DateCode": "2548",
                "Quantity": 500,
                "InitialQuantity": 1000,
                "Status": "Active"
            },
            "QuantityLoaded": 500
        },
        {
            "LocationIdentifier": "F10",
            "LocationName": "Feeder Bank B - Slot 1",
            "Material": {
                "UniqueIdentifier": "REEL-2026012600010",
                "InternalPartNumber": "RES-0603-10K",
                "ManufacturerPartNumber": "RC0603FR-0710KL",
                "Manufacturer": "Yageo",
                "ManufacturerLotCode": "LOT-2025-Q4-100",
                "Quantity": 4500,
                "InitialQuantity": 5000,
                "Status": "Active"
            },
            "QuantityLoaded": 4500
        },
        {
            "LocationIdentifier": "F20",
            "LocationName": "Feeder Bank C - Slot 1",
            "Material": {
                "UniqueIdentifier": "REEL-2026012600020",
                "InternalPartNumber": "CAP-0603-100N",
                "ManufacturerPartNumber": "GRM188R71H104KA93D",
                "Manufacturer": "Murata",
                "ManufacturerLotCode": "LOT-2025-Q4-050",
                "Quantity": 3800,
                "InitialQuantity": 4000,
                "Status": "Active"
            },
            "QuantityLoaded": 3800
        }
    ]
}
