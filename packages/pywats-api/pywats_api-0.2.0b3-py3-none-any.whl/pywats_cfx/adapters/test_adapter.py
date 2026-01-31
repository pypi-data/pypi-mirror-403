"""
CFX Test Result Adapter.

Converts CFX UnitsTested and UnitsInspected messages to normalized TestResultEvent.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from pywats_events.models import Event, EventMetadata, EventType
from pywats_events.models.domain_events import (
    InstalledComponent,
    TestMeasurement,
    TestResultEvent,
    TestStep,
)

from ..models.cfx_messages import (
    Measurement,
    TestedUnit,
    Test,
    TestResult,
    UnitsTested,
    UnitsInspected,
    InspectedUnit,
)


class CFXTestResultAdapter:
    """
    Adapts CFX test/inspection messages to normalized TestResultEvent.
    
    This adapter handles the conversion of IPC-CFX messages to the
    protocol-agnostic domain events used by pyWATS handlers.
    
    Example:
        adapter = CFXTestResultAdapter()
        
        # From CFX message
        cfx_message = UnitsTested(...)
        events = adapter.from_units_tested(cfx_message)
        
        # Each unit gets its own TestResultEvent
        for event in events:
            event_bus.publish(event)
    """
    
    def __init__(self, source_endpoint: Optional[str] = None) -> None:
        """
        Initialize adapter.
        
        Args:
            source_endpoint: CFX endpoint identifier for event source.
        """
        self.source_endpoint = source_endpoint or "cfx"
    
    def from_units_tested(
        self,
        message: UnitsTested,
        correlation_id: Optional[str] = None,
    ) -> list[Event]:
        """
        Convert CFX UnitsTested message to TestResultEvents.
        
        Creates one TestResultEvent per tested unit in the message.
        
        Args:
            message: CFX UnitsTested message.
            correlation_id: Optional correlation ID for tracing.
            
        Returns:
            List of TestResultEvents, one per unit.
        """
        events = []
        correlation = correlation_id or str(message.TransactionId)
        
        for unit in message.TestedUnits:
            test_result = self._convert_tested_unit(unit, message)
            
            event = Event(
                event_type=EventType.TEST_RESULT,
                payload=test_result.to_dict(),
                metadata=EventMetadata(
                    correlation_id=correlation,
                    source=f"cfx:{self.source_endpoint}",
                    trace_id=str(uuid4()),
                ),
            )
            events.append(event)
        
        return events
    
    def from_units_inspected(
        self,
        message: UnitsInspected,
        correlation_id: Optional[str] = None,
    ) -> list[Event]:
        """
        Convert CFX UnitsInspected message to TestResultEvents.
        
        Creates one TestResultEvent per inspected unit.
        
        Args:
            message: CFX UnitsInspected message.
            correlation_id: Optional correlation ID for tracing.
            
        Returns:
            List of TestResultEvents, one per unit.
        """
        events = []
        correlation = correlation_id or str(message.TransactionId)
        
        for unit in message.InspectedUnits:
            test_result = self._convert_inspected_unit(unit, message)
            
            event = Event(
                event_type=EventType.INSPECTION_RESULT,
                payload=test_result.to_dict(),
                metadata=EventMetadata(
                    correlation_id=correlation,
                    source=f"cfx:{self.source_endpoint}",
                    trace_id=str(uuid4()),
                ),
            )
            events.append(event)
        
        return events
    
    def _convert_tested_unit(
        self,
        unit: TestedUnit,
        message: UnitsTested,
    ) -> TestResultEvent:
        """Convert a single TestedUnit to TestResultEvent."""
        from pywats_events.models.domain_events import TestResult as DomainTestResult
        from datetime import datetime
        
        # Convert test steps
        steps = []
        for test in unit.Tests:
            step = self._convert_test_step(test)
            steps.append(step)
        
        # Map overall result
        result = DomainTestResult.PASS if unit.OverallResult == TestResult.PASSED else DomainTestResult.FAIL
        
        # Parse datetime strings
        start_time = message.TestStartTime if isinstance(message.TestStartTime, datetime) else datetime.fromisoformat(str(message.TestStartTime).replace('Z', '+00:00'))
        end_time = message.TestEndTime if isinstance(message.TestEndTime, datetime) else datetime.fromisoformat(str(message.TestEndTime).replace('Z', '+00:00'))
        
        return TestResultEvent(
            unit_id=unit.UnitIdentifier,
            result=result,
            part_number=None,  # Not in CFX message - can be enriched later
            station_id=message.Tester,
            operator_id=message.TestedBy,
            start_time=start_time,
            end_time=end_time,
            steps=steps,
            custom_data={
                "cfx_transaction_id": str(message.TransactionId),
                "test_method": message.TestMethod or "CFX_TEST",
                "recipe_name": message.RecipeName,
                "recipe_revision": message.RecipeRevision or unit.RecipeRevision,
                "lane": message.Lane,
                "stage": message.Stage,
                "symptoms": unit.Symptoms,
                "defects": unit.Defects,
            },
        )
    
    def _convert_test_step(self, test: Test) -> TestStep:
        """Convert CFX Test to TestStep."""
        from pywats_events.models.domain_events import TestResult as DomainTestResult
        from datetime import datetime
        
        # Convert measurements
        measurements = []
        for m in test.Measurements:
            measurement = self._convert_measurement(m)
            measurements.append(measurement)
        
        # Map CFX result to domain result
        status = DomainTestResult.PASS
        if test.Result:
            if test.Result == TestResult.FAILED:
                status = DomainTestResult.FAIL
            elif test.Result == TestResult.ABORTED:
                status = DomainTestResult.ABORTED
            elif test.Result == TestResult.ERROR:
                status = DomainTestResult.ERROR
        
        return TestStep(
            name=test.TestName,
            status=status,
            start_time=test.TestStartTime if test.TestStartTime else None,
            end_time=test.TestEndTime if test.TestEndTime else None,
            measurements=measurements,
            message=", ".join(test.DefectsFound) if test.DefectsFound else None,
        )
    
    def _convert_measurement(self, m: Measurement) -> TestMeasurement:
        """Convert CFX Measurement to TestMeasurement."""
        from pywats_events.models.domain_events import TestResult as DomainTestResult
        
        # Map CFX result to domain result
        status = DomainTestResult.PASS
        if m.Result:
            if m.Result == TestResult.FAILED:
                status = DomainTestResult.FAIL
            elif m.Result == TestResult.ABORTED:
                status = DomainTestResult.ABORTED
                
        return TestMeasurement(
            name=m.MeasurementName,
            value=m.MeasuredValue,
            unit=m.MeasurementUnits or "?",
            status=status,
            low_limit=m.LowerLimit,
            high_limit=m.UpperLimit,
            nominal=m.ExpectedValue,
        )
    
    def _convert_inspected_unit(
        self,
        unit: InspectedUnit,
        message: UnitsInspected,
    ) -> TestResultEvent:
        """Convert InspectedUnit to TestResultEvent."""
        from pywats_events.models.domain_events import TestResult as DomainTestResult
        from ..models.cfx_messages import InspectionResult
        from datetime import datetime
        
        result = DomainTestResult.PASS if unit.OverallResult == InspectionResult.PASSED else DomainTestResult.FAIL
        
        # Convert inspections to steps
        steps = []
        for inspection in unit.Inspections:
            step_status = DomainTestResult.PASS if inspection.get("Result") == "Passed" else DomainTestResult.FAIL
            step = TestStep(
                name=inspection.get("InspectionName", "Inspection"),
                status=step_status,
                measurements=[],
            )
            steps.append(step)
        
        # Parse datetime
        start_time = message.InspectionStartTime if isinstance(message.InspectionStartTime, datetime) else datetime.fromisoformat(str(message.InspectionStartTime).replace('Z', '+00:00'))
        end_time = message.InspectionEndTime if isinstance(message.InspectionEndTime, datetime) else datetime.fromisoformat(str(message.InspectionEndTime).replace('Z', '+00:00'))
        
        return TestResultEvent(
            unit_id=unit.UnitIdentifier,
            result=result,
            part_number=None,
            station_id=message.Inspector,
            operator_id=message.InspectedBy,
            start_time=start_time,
            end_time=end_time,
            steps=steps,
            custom_data={
                "cfx_transaction_id": str(message.TransactionId),
                "inspection_method": message.InspectionMethod or "CFX_INSPECTION",
                "recipe_name": message.RecipeName,
                "recipe_revision": message.RecipeRevision,
                "defects": [d.get("DefectCode") for d in unit.Defects],
            },
        )


def adapt_test_result(cfx_data: dict[str, Any], source: str = "cfx") -> list[Event]:
    """
    Convenience function to adapt CFX test data to events.
    
    Args:
        cfx_data: Raw CFX message dict.
        source: Source endpoint identifier.
        
    Returns:
        List of TestResultEvents.
    """
    from ..models.cfx_messages import parse_cfx_message
    
    adapter = CFXTestResultAdapter(source_endpoint=source)
    message = parse_cfx_message(cfx_data)
    
    if isinstance(message, UnitsTested):
        return adapter.from_units_tested(message)
    elif isinstance(message, UnitsInspected):
        return adapter.from_units_inspected(message)
    else:
        raise ValueError(f"Unsupported message type: {message.MessageName}")
