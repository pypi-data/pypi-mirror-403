"""
CFX Production Adapter.

Converts CFX production messages (WorkStarted, WorkCompleted, etc.) to normalized events.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from pywats_events.models import Event, EventMetadata, EventType
from pywats_events.models.domain_events import (
    WorkCompletedEvent,
    WorkStartedEvent,
    UnitDisqualifiedEvent,
)

from ..models.cfx_messages import (
    WorkStarted,
    WorkCompleted,
    UnitsArrived,
    UnitsDeparted,
    UnitsDisqualified,
    WorkResultState,
)


class CFXProductionAdapter:
    """
    Adapts CFX production messages to normalized domain events.
    
    Handles conversion of IPC-CFX production flow messages to the
    protocol-agnostic domain events used by pyWATS handlers.
    
    Supported messages:
        - WorkStarted → WorkStartedEvent
        - WorkCompleted → WorkCompletedEvent  
        - UnitsDisqualified → UnitDisqualifiedEvent
    """
    
    def __init__(self, source_endpoint: Optional[str] = None) -> None:
        """
        Initialize adapter.
        
        Args:
            source_endpoint: CFX endpoint identifier for event source.
        """
        self.source_endpoint = source_endpoint or "cfx"
    
    def from_work_started(
        self,
        message: WorkStarted,
        correlation_id: Optional[str] = None,
    ) -> list[Event]:
        """
        Convert CFX WorkStarted message to WorkStartedEvents.
        
        Args:
            message: CFX WorkStarted message.
            correlation_id: Optional correlation ID for tracing.
            
        Returns:
            List of WorkStartedEvents, one per unit.
        """
        events = []
        correlation = correlation_id or str(message.TransactionId)
        
        for unit in message.Units:
            domain_event = WorkStartedEvent(
                unit_id=unit.UnitIdentifier or f"Position-{unit.PositionNumber}",
                station_id="",  # Will be set by handler if available
                work_order_id=None,  # Not in CFX message
                operator_id=None,
                lane=message.Lane,
                custom_data={
                    "cfx_transaction_id": str(message.TransactionId),
                    "position_number": unit.PositionNumber,
                    "position_name": unit.PositionName,
                    "serial_number": unit.UnitIdentifier,
                    "stage": message.Stage,
                },
            )
            
            event = Event(
                event_type=EventType.WORK_STARTED,
                payload=domain_event.to_dict(),
                metadata=EventMetadata(
                    correlation_id=correlation,
                    source=f"cfx:{self.source_endpoint}",
                    trace_id=str(uuid4()),
                ),
            )
            events.append(event)
        
        return events
    
    def from_work_completed(
        self,
        message: WorkCompleted,
        correlation_id: Optional[str] = None,
    ) -> list[Event]:
        """
        Convert CFX WorkCompleted message to WorkCompletedEvents.
        
        Args:
            message: CFX WorkCompleted message.
            correlation_id: Optional correlation ID for tracing.
            
        Returns:
            List of WorkCompletedEvents, one per unit.
        """
        events = []
        correlation = correlation_id or str(message.TransactionId)
        
        for unit in message.Units:
            # Handle Result being either an enum or a string
            result_value = message.Result.value if hasattr(message.Result, 'value') else str(message.Result) if message.Result else None
            
            domain_event = WorkCompletedEvent(
                unit_id=unit.UnitIdentifier or f"Position-{unit.PositionNumber}",
                station_id="",  # Will be set by handler if available
                work_order_id=None,
                operator_id=None,
                result="completed" if result_value == "Completed" else "failed",
                custom_data={
                    "cfx_transaction_id": str(message.TransactionId),
                    "cfx_result": result_value,
                    "position_number": unit.PositionNumber,
                    "serial_number": unit.UnitIdentifier,
                    "lane": message.Lane,
                    "stage": message.Stage,
                },
            )
            
            event = Event(
                event_type=EventType.WORK_COMPLETED,
                payload=domain_event.to_dict(),
                metadata=EventMetadata(
                    correlation_id=correlation,
                    source=f"cfx:{self.source_endpoint}",
                    trace_id=str(uuid4()),
                ),
            )
            events.append(event)
        
        return events
    
    def from_units_disqualified(
        self,
        message: UnitsDisqualified,
        correlation_id: Optional[str] = None,
    ) -> list[Event]:
        """
        Convert CFX UnitsDisqualified message to UnitDisqualifiedEvents.
        
        Args:
            message: CFX UnitsDisqualified message.
            correlation_id: Optional correlation ID for tracing.
            
        Returns:
            List of UnitDisqualifiedEvents, one per unit.
        """
        events = []
        correlation = correlation_id or str(message.TransactionId) if message.TransactionId else str(uuid4())
        
        for unit_data in message.DisqualifiedUnits:
            domain_event = UnitDisqualifiedEvent(
                unit_id=unit_data.get("UnitIdentifier", ""),
                serial_number=unit_data.get("UnitIdentifier"),
                reason=message.Reason or unit_data.get("Reason", "Unknown"),
                station_id=None,
                operator_id=None,
                lane=message.Lane,
                stage=message.Stage,
                attributes={
                    "cfx_transaction_id": str(message.TransactionId) if message.TransactionId else None,
                },
            )
            
            event = Event(
                event_type=EventType.UNIT_DISQUALIFIED,
                payload=domain_event.to_dict(),
                metadata=EventMetadata(
                    correlation_id=correlation,
                    source=f"cfx:{self.source_endpoint}",
                    trace_id=str(uuid4()),
                ),
            )
            events.append(event)
        
        return events


def adapt_production_message(cfx_data: dict[str, Any], source: str = "cfx") -> list[Event]:
    """
    Convenience function to adapt CFX production data to events.
    
    Args:
        cfx_data: Raw CFX message dict.
        source: Source endpoint identifier.
        
    Returns:
        List of production events.
    """
    from ..models.cfx_messages import parse_cfx_message
    
    adapter = CFXProductionAdapter(source_endpoint=source)
    message = parse_cfx_message(cfx_data)
    
    if isinstance(message, WorkStarted):
        return adapter.from_work_started(message)
    elif isinstance(message, WorkCompleted):
        return adapter.from_work_completed(message)
    elif isinstance(message, UnitsDisqualified):
        return adapter.from_units_disqualified(message)
    else:
        raise ValueError(f"Unsupported message type: {message.MessageName}")
