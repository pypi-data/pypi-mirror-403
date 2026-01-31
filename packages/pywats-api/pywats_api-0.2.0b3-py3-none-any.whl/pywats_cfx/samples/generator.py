"""
CFX Sample Message Generator.

Generates realistic CFX messages with customizable parameters.
Useful for testing, simulation, and development.
"""

from __future__ import annotations

import random
import string
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4


class CFXSampleGenerator:
    """
    Generates realistic CFX sample messages.
    
    Example:
        gen = CFXSampleGenerator(station_id="TEST-STATION-01")
        
        # Generate a passing test
        msg = gen.units_tested(
            serial_number="SN-001",
            test_method="ICT",
            passed=True,
        )
        
        # Generate a failing test with specific measurements
        msg = gen.units_tested(
            serial_number="SN-002",
            test_method="FCT",
            passed=False,
            measurements=[
                {"name": "Voltage", "value": 5.5, "low": 4.5, "high": 5.0, "unit": "V"},
            ]
        )
    """
    
    def __init__(
        self,
        station_id: str = "TEST-STATION-01",
        operator: Optional[str] = None,
        lane: int = 1,
        stage: str = "Test",
    ):
        """
        Initialize generator with defaults.
        
        Args:
            station_id: Default station/tester identifier.
            operator: Default operator (None = auto-generate).
            lane: Default lane number.
            stage: Default stage name.
        """
        self.station_id = station_id
        self.operator = operator
        self.lane = lane
        self.stage = stage
    
    def _generate_serial(self, prefix: str = "SN") -> str:
        """Generate a serial number."""
        date_part = datetime.now().strftime("%Y%m%d")
        seq = random.randint(1, 99999)
        return f"{prefix}-{date_part}{seq:05d}"
    
    def _generate_transaction_id(self) -> str:
        """Generate a transaction ID."""
        return str(uuid4())
    
    def _now(self) -> str:
        """Get current timestamp as ISO string."""
        return datetime.now().isoformat(timespec='milliseconds')
    
    def _time_offset(self, seconds: float) -> str:
        """Get timestamp offset from now."""
        return (datetime.now() + timedelta(seconds=seconds)).isoformat(timespec='milliseconds')
    
    def units_tested(
        self,
        serial_number: Optional[str] = None,
        test_method: str = "FCT",
        passed: bool = True,
        recipe_name: Optional[str] = None,
        measurements: Optional[list[dict[str, Any]]] = None,
        duration_seconds: float = 30.0,
    ) -> dict[str, Any]:
        """
        Generate a UnitsTested message.
        
        Args:
            serial_number: Unit serial (auto-generated if None).
            test_method: Test method (ICT, FCT, etc.).
            passed: Whether the test passed.
            recipe_name: Test recipe name.
            measurements: List of measurement dicts with name, value, low, high, unit.
            duration_seconds: Test duration.
            
        Returns:
            CFX UnitsTested message dict.
        """
        serial = serial_number or self._generate_serial()
        start_time = datetime.now() - timedelta(seconds=duration_seconds)
        end_time = datetime.now()
        
        # Build measurements
        tests = []
        if measurements:
            for m in measurements:
                meas_passed = True
                if m.get("low") is not None and m["value"] < m["low"]:
                    meas_passed = False
                if m.get("high") is not None and m["value"] > m["high"]:
                    meas_passed = False
                
                tests.append({
                    "TestName": m.get("test_name", m["name"]),
                    "Result": "Passed" if meas_passed else "Failed",
                    "Measurements": [{
                        "MeasurementName": m["name"],
                        "MeasuredValue": m["value"],
                        "ExpectedValue": m.get("nominal"),
                        "MeasurementUnits": m.get("unit", ""),
                        "LowerLimit": m.get("low"),
                        "UpperLimit": m.get("high"),
                        "Result": "Passed" if meas_passed else "Failed",
                    }],
                    "SymptomsFound": [],
                    "DefectsFound": [] if meas_passed else [f"{m['name']}_OUT_OF_SPEC"],
                })
        else:
            # Generate some default measurements
            tests = [
                {
                    "TestName": "Default_Test",
                    "Result": "Passed" if passed else "Failed",
                    "Measurements": [
                        {
                            "MeasurementName": "Sample_Value",
                            "MeasuredValue": 5.0 if passed else 6.0,
                            "ExpectedValue": 5.0,
                            "MeasurementUnits": "V",
                            "LowerLimit": 4.5,
                            "UpperLimit": 5.5,
                            "Result": "Passed" if passed else "Failed",
                        }
                    ],
                    "SymptomsFound": [],
                    "DefectsFound": [] if passed else ["VALUE_OUT_OF_SPEC"],
                }
            ]
        
        return {
            "MessageName": "CFX.Production.Testing.UnitsTested",
            "TransactionId": self._generate_transaction_id(),
            "TestMethod": test_method,
            "TestedBy": self.operator or f"OP{random.randint(1, 999):03d}",
            "Tester": self.station_id,
            "TestStartTime": start_time.isoformat(timespec='milliseconds'),
            "TestEndTime": end_time.isoformat(timespec='milliseconds'),
            "RecipeName": recipe_name or f"{test_method}_RECIPE_V1",
            "Lane": self.lane,
            "Stage": self.stage,
            "TestedUnits": [
                {
                    "UnitIdentifier": serial,
                    "UnitPositionNumber": 1,
                    "OverallResult": "Passed" if passed else "Failed",
                    "Tests": tests,
                    "Symptoms": [],
                    "Defects": [] if passed else ["TEST_FAILURE"],
                }
            ]
        }
    
    def materials_installed(
        self,
        serial_number: Optional[str] = None,
        components: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """
        Generate a MaterialsInstalled message.
        
        Args:
            serial_number: Unit serial.
            components: List of component dicts with ref, part_number, manufacturer, lot.
            
        Returns:
            CFX MaterialsInstalled message dict.
        """
        serial = serial_number or self._generate_serial("PCB")
        
        installed_components = []
        if components:
            for c in components:
                installed_components.append({
                    "ReferenceDesignator": c["ref"],
                    "InternalPartNumber": c.get("part_number", f"PN-{c['ref']}"),
                    "Manufacturer": c.get("manufacturer"),
                    "LotCode": c.get("lot"),
                    "DateCode": c.get("date_code"),
                    "Quantity": c.get("quantity", 1),
                })
        else:
            # Default component
            installed_components = [
                {
                    "ReferenceDesignator": "U1",
                    "InternalPartNumber": "MCU-001",
                    "Manufacturer": "STMicroelectronics",
                    "LotCode": f"LOT-{datetime.now().strftime('%Y%m%d')}",
                    "Quantity": 1,
                }
            ]
        
        return {
            "MessageName": "CFX.Production.Assembly.MaterialsInstalled",
            "TransactionId": self._generate_transaction_id(),
            "InstalledMaterials": [
                {
                    "UnitIdentifier": serial,
                    "UnitPositionNumber": 1,
                    "InstalledComponents": installed_components,
                }
            ]
        }
    
    def fault_occurred(
        self,
        fault_code: str,
        description: str,
        severity: str = "Error",
        component: Optional[str] = None,
        related_units: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Generate a FaultOccurred message.
        
        Args:
            fault_code: Fault code identifier.
            description: Human-readable description.
            severity: Error, Warning, or Information.
            component: Affected component.
            related_units: List of affected unit serials.
            
        Returns:
            CFX FaultOccurred message dict.
        """
        fault_id = f"FAULT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1, 999):03d}"
        
        return {
            "MessageName": "CFX.ResourcePerformance.FaultOccurred",
            "Lane": self.lane,
            "Stage": self.stage,
            "Fault": {
                "Cause": description,
                "Severity": severity,
                "FaultCode": fault_code,
                "FaultOccurrenceId": fault_id,
                "OccurrenceType": "Momentary",
                "OccurredAt": self._now(),
                "Description": description,
                "ComponentOfInterest": component,
                "RelatedUnits": related_units or [],
            }
        }
    
    def station_state_changed(
        self,
        old_state: str,
        new_state: str,
        duration_seconds: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Generate a StationStateChanged message.
        
        Args:
            old_state: Previous state (Off, Standby, Processing, etc.).
            new_state: New state.
            duration_seconds: How long in old state.
            
        Returns:
            CFX StationStateChanged message dict.
        """
        return {
            "MessageName": "CFX.ResourcePerformance.StationStateChanged",
            "OldState": old_state,
            "NewState": new_state,
            "OldStateDuration": duration_seconds,
        }
    
    def work_started(
        self,
        serial_numbers: list[str],
    ) -> dict[str, Any]:
        """
        Generate a WorkStarted message.
        
        Args:
            serial_numbers: List of unit serials starting work.
            
        Returns:
            CFX WorkStarted message dict.
        """
        units = []
        for i, sn in enumerate(serial_numbers, 1):
            units.append({
                "PositionNumber": i,
                "UnitIdentifier": sn,
            })
        
        return {
            "MessageName": "CFX.Production.WorkStarted",
            "TransactionId": self._generate_transaction_id(),
            "Lane": self.lane,
            "Stage": self.stage,
            "Units": units,
        }
    
    def work_completed(
        self,
        serial_numbers: list[str],
        completed: bool = True,
    ) -> dict[str, Any]:
        """
        Generate a WorkCompleted message.
        
        Args:
            serial_numbers: List of unit serials.
            completed: True for Completed, False for Aborted.
            
        Returns:
            CFX WorkCompleted message dict.
        """
        units = []
        for i, sn in enumerate(serial_numbers, 1):
            units.append({
                "PositionNumber": i,
                "UnitIdentifier": sn,
            })
        
        return {
            "MessageName": "CFX.Production.WorkCompleted",
            "TransactionId": self._generate_transaction_id(),
            "Result": "Completed" if completed else "Aborted",
            "Lane": self.lane,
            "Stage": self.stage,
            "Units": units,
        }
