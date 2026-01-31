"""
Event type enumeration for the pyWATS event system.

These event types represent normalized domain events that can originate
from any transport (CFX, MQTT, webhook, file watcher, etc.).
"""

from enum import Enum, auto


class EventType(Enum):
    """
    Enumeration of all event types in the pyWATS event system.
    
    Event types are organized by domain:
    - TEST_*: Test and inspection results
    - ASSET_*: Equipment and resource events
    - MATERIAL_*: BOM and material events
    - PRODUCTION_*: Work order and unit flow events
    - SYSTEM_*: Internal system events
    """
    
    # ==========================================================================
    # Test & Inspection Events (Report domain)
    # ==========================================================================
    TEST_RESULT = "test.result"
    """Unit test completed with pass/fail result and measurements."""
    
    TEST_STARTED = "test.started"
    """Unit test execution has started."""
    
    INSPECTION_RESULT = "inspection.result"
    """Visual/AOI inspection completed."""
    
    INSPECTION_STARTED = "inspection.started"
    """Inspection process has started."""
    
    # ==========================================================================
    # Asset & Resource Events (Asset domain)
    # ==========================================================================
    ASSET_FAULT = "asset.fault"
    """Equipment fault or error occurred."""
    
    ASSET_MAINTENANCE = "asset.maintenance"
    """Maintenance performed on equipment."""
    
    ASSET_STATE_CHANGED = "asset.state_changed"
    """Equipment state changed (online/offline/idle/busy)."""
    
    ASSET_CALIBRATION = "asset.calibration"
    """Calibration performed or due."""
    
    # ==========================================================================
    # Material Events (Product domain)
    # ==========================================================================
    MATERIAL_INSTALLED = "material.installed"
    """Components installed on a unit (BOM tracking)."""
    
    MATERIAL_CONSUMED = "material.consumed"
    """Material consumed from inventory."""
    
    MATERIAL_REJECTED = "material.rejected"
    """Material rejected/scrapped."""
    
    # ==========================================================================
    # Production Events (Production domain)
    # ==========================================================================
    WORK_STARTED = "production.work_started"
    """Work started on a unit at a station."""
    
    WORK_COMPLETED = "production.work_completed"
    """Work completed on a unit at a station."""
    
    UNIT_ARRIVED = "production.unit_arrived"
    """Unit arrived at a station."""
    
    UNIT_DEPARTED = "production.unit_departed"
    """Unit departed from a station."""
    
    UNIT_DISQUALIFIED = "production.unit_disqualified"
    """Unit removed from production flow."""
    
    WORK_ORDER_CREATED = "production.work_order_created"
    """New work order created."""
    
    WORK_ORDER_UPDATED = "production.work_order_updated"
    """Work order status/details updated."""
    
    # ==========================================================================
    # System Events (Internal)
    # ==========================================================================
    TRANSPORT_CONNECTED = "system.transport_connected"
    """Transport adapter connected to message source."""
    
    TRANSPORT_DISCONNECTED = "system.transport_disconnected"
    """Transport adapter disconnected."""
    
    TRANSPORT_ERROR = "system.transport_error"
    """Transport adapter encountered an error."""
    
    HANDLER_ERROR = "system.handler_error"
    """Event handler raised an exception."""
    
    EVENT_DEAD_LETTER = "system.dead_letter"
    """Event moved to dead letter queue after max retries."""
    
    # ==========================================================================
    # Custom/Extension Events
    # ==========================================================================
    CUSTOM = "custom"
    """Custom event type for user-defined events."""
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def from_string(cls, value: str) -> "EventType":
        """
        Get EventType from string value.
        
        Args:
            value: String representation of event type (e.g., "test.result")
            
        Returns:
            Matching EventType enum member
            
        Raises:
            ValueError: If no matching event type found
        """
        for event_type in cls:
            if event_type.value == value:
                return event_type
        raise ValueError(f"Unknown event type: {value}")
    
    @classmethod
    def test_events(cls) -> list["EventType"]:
        """Get all test-related event types."""
        return [cls.TEST_RESULT, cls.TEST_STARTED, cls.INSPECTION_RESULT, cls.INSPECTION_STARTED]
    
    @classmethod
    def asset_events(cls) -> list["EventType"]:
        """Get all asset-related event types."""
        return [cls.ASSET_FAULT, cls.ASSET_MAINTENANCE, cls.ASSET_STATE_CHANGED, cls.ASSET_CALIBRATION]
    
    @classmethod
    def material_events(cls) -> list["EventType"]:
        """Get all material-related event types."""
        return [cls.MATERIAL_INSTALLED, cls.MATERIAL_CONSUMED, cls.MATERIAL_REJECTED]
    
    @classmethod
    def production_events(cls) -> list["EventType"]:
        """Get all production-related event types."""
        return [
            cls.WORK_STARTED, cls.WORK_COMPLETED, cls.UNIT_ARRIVED, 
            cls.UNIT_DEPARTED, cls.UNIT_DISQUALIFIED,
            cls.WORK_ORDER_CREATED, cls.WORK_ORDER_UPDATED
        ]
    
    @classmethod
    def system_events(cls) -> list["EventType"]:
        """Get all system-related event types."""
        return [
            cls.TRANSPORT_CONNECTED, cls.TRANSPORT_DISCONNECTED, 
            cls.TRANSPORT_ERROR, cls.HANDLER_ERROR, cls.EVENT_DEAD_LETTER
        ]
