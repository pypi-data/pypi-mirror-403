"""
CFX Material Adapter.

Converts CFX MaterialsInstalled messages to normalized MaterialInstalledEvent.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from pywats_events.models import Event, EventMetadata, EventType
from pywats_events.models.domain_events import (
    InstalledComponent,
    MaterialInstalledEvent,
)

from ..models.cfx_messages import (
    InstalledMaterial,
    MaterialsInstalled,
)


class CFXMaterialAdapter:
    """
    Adapts CFX material messages to normalized MaterialInstalledEvent.
    
    Handles conversion of IPC-CFX MaterialsInstalled messages to the
    protocol-agnostic domain events used by pyWATS handlers.
    
    Example:
        adapter = CFXMaterialAdapter()
        
        cfx_message = MaterialsInstalled(...)
        events = adapter.from_materials_installed(cfx_message)
        
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
    
    def from_materials_installed(
        self,
        message: MaterialsInstalled,
        correlation_id: Optional[str] = None,
    ) -> list[Event]:
        """
        Convert CFX MaterialsInstalled message to MaterialInstalledEvents.
        
        Creates one MaterialInstalledEvent per unit that had materials installed.
        
        Args:
            message: CFX MaterialsInstalled message.
            correlation_id: Optional correlation ID for tracing.
            
        Returns:
            List of MaterialInstalledEvents, one per unit.
        """
        events = []
        correlation = correlation_id or str(message.TransactionId)
        
        for material in message.InstalledMaterials:
            domain_event = self._convert_installed_material(material, message)
            
            event = Event(
                event_type=EventType.MATERIAL_INSTALLED,
                payload=domain_event.to_dict(),
                metadata=EventMetadata(
                    correlation_id=correlation,
                    source=f"cfx:{self.source_endpoint}",
                    trace_id=str(uuid4()),
                ),
            )
            events.append(event)
        
        return events
    
    def _convert_installed_material(
        self,
        material: InstalledMaterial,
        message: MaterialsInstalled,
    ) -> MaterialInstalledEvent:
        """Convert a single InstalledMaterial to MaterialInstalledEvent."""
        
        # Convert installed components
        components = []
        for comp_data in material.InstalledComponents:
            component = self._convert_component(comp_data)
            components.append(component)
        
        return MaterialInstalledEvent(
            unit_id=material.UnitIdentifier,
            components=components,
            station_id=None,  # Not in CFX message
            custom_data={
                "cfx_transaction_id": str(message.TransactionId),
                "unit_position": material.UnitPositionNumber,
            },
        )
    
    def _convert_component(self, comp_data: dict[str, Any]) -> InstalledComponent:
        """Convert CFX component data to InstalledComponent."""
        return InstalledComponent(
            reference_designator=comp_data.get("ReferenceDesignator", ""),
            part_number=comp_data.get("InternalPartNumber") or comp_data.get("PartNumber", ""),
            serial_number=comp_data.get("ComponentSerialNumber"),
            lot_number=comp_data.get("LotCode") or comp_data.get("ManufacturerLotCode"),
        )


def adapt_materials_installed(cfx_data: dict[str, Any], source: str = "cfx") -> list[Event]:
    """
    Convenience function to adapt CFX materials data to events.
    
    Args:
        cfx_data: Raw CFX message dict.
        source: Source endpoint identifier.
        
    Returns:
        List of MaterialInstalledEvents.
    """
    from ..models.cfx_messages import parse_cfx_message, MaterialsInstalled
    
    adapter = CFXMaterialAdapter(source_endpoint=source)
    message = parse_cfx_message(cfx_data)
    
    if isinstance(message, MaterialsInstalled):
        return adapter.from_materials_installed(message)
    else:
        raise ValueError(f"Unsupported message type: {message.MessageName}")
