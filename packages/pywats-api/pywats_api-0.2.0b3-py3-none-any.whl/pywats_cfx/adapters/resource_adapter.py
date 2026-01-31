"""
CFX Resource Adapter.

Converts CFX resource/endpoint messages (FaultOccurred, StationStateChanged) to normalized events.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from pywats_events.models import Event, EventMetadata, EventType
from pywats_events.models.domain_events import (
    AssetFaultEvent,
    AssetState,
    AssetStateChangedEvent,
    SeverityLevel,
)

from ..models.cfx_messages import (
    Fault,
    FaultOccurred,
    FaultCleared,
    FaultSeverity,
    StationStateChanged,
    ResourceState,
)


class CFXResourceAdapter:
    """
    Adapts CFX resource/endpoint messages to normalized domain events.
    
    Handles conversion of IPC-CFX resource performance messages to the
    protocol-agnostic domain events used by pyWATS handlers.
    
    Supported messages:
        - FaultOccurred → AssetFaultEvent
        - FaultCleared → AssetFaultEvent (with cleared=True)
        - StationStateChanged → AssetStateChangedEvent
    """
    
    def __init__(self, source_endpoint: Optional[str] = None) -> None:
        """
        Initialize adapter.
        
        Args:
            source_endpoint: CFX endpoint identifier for event source.
        """
        self.source_endpoint = source_endpoint or "cfx"
    
    def from_fault_occurred(
        self,
        message: FaultOccurred,
        correlation_id: Optional[str] = None,
    ) -> Event:
        """
        Convert CFX FaultOccurred message to AssetFaultEvent.
        
        Args:
            message: CFX FaultOccurred message.
            correlation_id: Optional correlation ID for tracing.
            
        Returns:
            AssetFaultEvent for the fault.
        """
        fault_data = message.Fault
        
        # Map severity to SeverityLevel enum
        severity_map = {
            "Error": SeverityLevel.ERROR,
            "Warning": SeverityLevel.WARNING, 
            "Information": SeverityLevel.INFO,
        }
        severity = severity_map.get(fault_data.get("Severity", "Error"), SeverityLevel.ERROR)
        
        domain_event = AssetFaultEvent(
            asset_id=self.source_endpoint,
            fault_code=fault_data.get("FaultCode") or fault_data.get("Cause", "UNKNOWN"),
            fault_message=fault_data.get("Description") or fault_data.get("Cause", ""),
            severity=severity,
            cleared=False,
            custom_data={
                "fault_occurrence_id": fault_data.get("FaultOccurrenceId"),
                "occurrence_type": fault_data.get("OccurrenceType"),
                "component_of_interest": fault_data.get("ComponentOfInterest"),
                "related_units": fault_data.get("RelatedUnits", []),
                "lane": message.Lane,
                "stage": message.Stage,
            },
        )
        
        return Event(
            event_type=EventType.ASSET_FAULT,
            payload=domain_event.to_dict(),
            metadata=EventMetadata(
                correlation_id=correlation_id or fault_data.get("FaultOccurrenceId") or str(uuid4()),
                source=f"cfx:{self.source_endpoint}",
                trace_id=str(uuid4()),
            ),
        )
    
    def from_fault_cleared(
        self,
        message: FaultCleared,
        correlation_id: Optional[str] = None,
    ) -> Event:
        """
        Convert CFX FaultCleared message to AssetFaultEvent.
        
        Args:
            message: CFX FaultCleared message.
            correlation_id: Optional correlation ID for tracing.
            
        Returns:
            AssetFaultEvent indicating fault was cleared.
        """
        domain_event = AssetFaultEvent(
            asset_id=self.source_endpoint,
            fault_code=message.FaultOccurrenceId,
            fault_message="Fault cleared",
            severity="info",
            cleared=True,
            attributes={
                "fault_occurrence_id": message.FaultOccurrenceId,
            },
        )
        
        return Event(
            event_type=EventType.ASSET_FAULT_CLEARED,
            payload=domain_event.to_dict(),
            metadata=EventMetadata(
                correlation_id=correlation_id or message.FaultOccurrenceId,
                source=f"cfx:{self.source_endpoint}",
                trace_id=str(uuid4()),
            ),
        )
    
    def from_station_state_changed(
        self,
        message: StationStateChanged,
        correlation_id: Optional[str] = None,
    ) -> Event:
        """
        Convert CFX StationStateChanged message to AssetStateChangedEvent.
        
        Args:
            message: CFX StationStateChanged message.
            correlation_id: Optional correlation ID for tracing.
            
        Returns:
            AssetStateChangedEvent for the state transition.
        """
        # Normalize state names
        # Map CFX states to AssetState enum
        state_map = {
            "On": AssetState.ONLINE,
            "Off": AssetState.OFFLINE,
            "Standby": AssetState.IDLE,
            "Engineering": AssetState.IDLE,
            "ReadyProcessing": AssetState.IDLE,
            "Processing": AssetState.BUSY,
            "ProcessingExecutingRecipe": AssetState.BUSY,
            "Blocked": AssetState.BUSY,
            "Starved": AssetState.IDLE,
            "Maintenance": AssetState.MAINTENANCE,
            "ScheduledMaintenance": AssetState.MAINTENANCE,
            "UnscheduledMaintenance": AssetState.MAINTENANCE,
            "MachineError": AssetState.ERROR,
            "Setup": AssetState.BUSY,
            "Teardown": AssetState.BUSY,
        }
        
        # Handle state being either an enum or a string
        old_state_val = message.OldState.value if hasattr(message.OldState, 'value') else str(message.OldState) if message.OldState else "unknown"
        new_state_val = message.NewState.value if hasattr(message.NewState, 'value') else str(message.NewState) if message.NewState else "unknown"
        
        domain_event = AssetStateChangedEvent(
            asset_id=self.source_endpoint,
            new_state=state_map.get(new_state_val, AssetState.OFFLINE),
            previous_state=state_map.get(old_state_val, None),
            custom_data={
                "cfx_old_state": old_state_val,
                "cfx_new_state": new_state_val,
                "old_state_duration_seconds": message.OldStateDuration,
            },
        )
        
        return Event(
            event_type=EventType.ASSET_STATE_CHANGED,
            payload=domain_event.to_dict(),
            metadata=EventMetadata(
                correlation_id=correlation_id or str(uuid4()),
                source=f"cfx:{self.source_endpoint}",
                trace_id=str(uuid4()),
            ),
        )


def adapt_resource_message(cfx_data: dict[str, Any], source: str = "cfx") -> Event:
    """
    Convenience function to adapt CFX resource data to events.
    
    Args:
        cfx_data: Raw CFX message dict.
        source: Source endpoint identifier.
        
    Returns:
        Resource domain event.
    """
    from ..models.cfx_messages import parse_cfx_message
    
    adapter = CFXResourceAdapter(source_endpoint=source)
    message = parse_cfx_message(cfx_data)
    
    if isinstance(message, FaultOccurred):
        return adapter.from_fault_occurred(message)
    elif isinstance(message, FaultCleared):
        return adapter.from_fault_cleared(message)
    elif isinstance(message, StationStateChanged):
        return adapter.from_station_state_changed(message)
    else:
        raise ValueError(f"Unsupported message type: {message.MessageName}")
