"""
Application Event Bus

Provides decoupled communication between GUI and application layers
using Qt Signals for thread-safe event delivery.

This enables:
- Pages to subscribe to events without knowing about MainWindow internals
- Application to broadcast state changes without knowing about pages
- Thread-safe event delivery (Qt Signals are thread-safe)
- Easy testing through mock event buses
"""
from enum import Enum, auto
from typing import Optional, Any, Dict, Callable, List
import logging

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class AppEvent(Enum):
    """
    Application event types.
    
    Events are grouped by category for clarity.
    """
    # Connection events
    CONNECTION_CHANGED = auto()      # data: {status: str}
    CONNECTION_ERROR = auto()        # data: {error: str}
    
    # Application lifecycle
    APP_STARTING = auto()            # data: {}
    APP_STARTED = auto()             # data: {}
    APP_STOPPING = auto()            # data: {}
    APP_STOPPED = auto()             # data: {}
    APP_ERROR = auto()               # data: {error: str}
    APP_STATUS_CHANGED = auto()      # data: {status: str}
    
    # API client events
    API_CLIENT_READY = auto()        # data: {client: pyWATS}
    API_CLIENT_DISCONNECTED = auto() # data: {}
    
    # Data events (for cache invalidation / refresh triggers)
    ASSETS_CHANGED = auto()          # data: {}
    PRODUCTS_CHANGED = auto()        # data: {}
    SOFTWARE_CHANGED = auto()        # data: {}
    PROCESSES_REFRESHED = auto()     # data: {}
    
    # Queue events
    QUEUE_ITEM_ADDED = auto()        # data: {item: Any}
    QUEUE_ITEM_PROCESSED = auto()    # data: {item: Any, success: bool}
    QUEUE_EMPTY = auto()             # data: {}
    QUEUE_STATUS_CHANGED = auto()    # data: {pending: int, failed: int}
    
    # Configuration events
    CONFIG_CHANGED = auto()          # data: {key: str, value: Any}
    CONFIG_SAVED = auto()            # data: {}


class EventBus(QObject):
    """
    Central event bus for application-wide communication.
    
    Uses Qt Signals for thread-safe delivery to GUI components.
    Implements singleton pattern to ensure single instance.
    
    Usage:
        # Get the singleton instance
        from pywats_client.core.event_bus import event_bus
        
        # Subscribe to events (direct signal connection)
        event_bus.connection_changed.connect(self._on_connection)
        
        # Or subscribe with callback
        event_bus.subscribe(AppEvent.CONNECTION_CHANGED, self._on_connection)
        
        # Publish events
        event_bus.publish(AppEvent.CONNECTION_CHANGED, status="Online")
        
        # Or use typed signals directly
        event_bus.connection_changed.emit("Online")
    """
    
    # =========================================================================
    # Typed signals for common events (for direct, type-safe connections)
    # =========================================================================
    
    # Connection status as string (Online/Offline/Connecting/etc.)
    connection_changed = Signal(str)
    
    # pyWATS client instance when API becomes available
    api_client_ready = Signal(object)
    
    # Application status changes (Starting/Running/Stopping/Stopped)
    app_status_changed = Signal(str)
    
    # Queue status: (pending_count, failed_count)
    queue_status_changed = Signal(int, int)
    
    # Generic signal for all events: (event_type, data_dict)
    event_occurred = Signal(object, dict)
    
    # =========================================================================
    # Singleton implementation
    # =========================================================================
    
    _instance: Optional['EventBus'] = None
    
    def __new__(cls) -> 'EventBus':
        """Singleton pattern for global event bus."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the event bus (only once due to singleton)."""
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        self._initialized = True
        self._subscribers: Dict[AppEvent, List[Callable]] = {}
        logger.debug("EventBus initialized")
    
    # =========================================================================
    # Publishing events
    # =========================================================================
    
    def publish(self, event: AppEvent, **data) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event type to publish
            **data: Event data as keyword arguments
            
        Example:
            event_bus.publish(AppEvent.CONNECTION_CHANGED, status="Online")
            event_bus.publish(AppEvent.API_CLIENT_READY, client=api_instance)
        """
        logger.debug(f"Publishing event: {event.name} with data: {list(data.keys())}")
        
        # Emit generic signal for subscribers using subscribe()
        self.event_occurred.emit(event, data)
        
        # Also emit typed signals for direct connections
        self._emit_typed_signal(event, data)
    
    def _emit_typed_signal(self, event: AppEvent, data: Dict[str, Any]) -> None:
        """Emit the appropriate typed signal for an event."""
        if event == AppEvent.CONNECTION_CHANGED:
            self.connection_changed.emit(data.get('status', ''))
            
        elif event == AppEvent.API_CLIENT_READY:
            self.api_client_ready.emit(data.get('client'))
            
        elif event == AppEvent.API_CLIENT_DISCONNECTED:
            self.api_client_ready.emit(None)
            
        elif event == AppEvent.APP_STATUS_CHANGED:
            self.app_status_changed.emit(data.get('status', ''))
            
        elif event in (AppEvent.APP_STARTING, AppEvent.APP_STARTED, 
                       AppEvent.APP_STOPPING, AppEvent.APP_STOPPED):
            self.app_status_changed.emit(event.name)
            
        elif event == AppEvent.QUEUE_STATUS_CHANGED:
            self.queue_status_changed.emit(
                data.get('pending', 0), 
                data.get('failed', 0)
            )
    
    # =========================================================================
    # Subscribing to events
    # =========================================================================
    
    def subscribe(self, event: AppEvent, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to a specific event type with a callback.
        
        The callback receives a dictionary with event data.
        
        Args:
            event: Event type to subscribe to
            callback: Function to call when event occurs.
                      Signature: callback(data: dict) -> None
                      
        Example:
            def on_connection(data):
                status = data.get('status')
                print(f"Connection: {status}")
                
            event_bus.subscribe(AppEvent.CONNECTION_CHANGED, on_connection)
        """
        if event not in self._subscribers:
            self._subscribers[event] = []
        
        if callback not in self._subscribers[event]:
            self._subscribers[event].append(callback)
            logger.debug(f"Subscribed to {event.name}: {callback.__name__}")
        
        # Connect the callback through the generic signal with filtering
        def filtered_handler(evt: AppEvent, data: Dict[str, Any]) -> None:
            if evt == event:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event.name}: {e}")
        
        # Store reference to prevent garbage collection
        if not hasattr(self, '_handlers'):
            self._handlers: List[Callable] = []
        self._handlers.append(filtered_handler)
        
        self.event_occurred.connect(filtered_handler)
    
    def unsubscribe(self, event: AppEvent, callback: Callable) -> None:
        """
        Remove a subscription.
        
        Note: This removes from the subscriber list but the Qt signal
        connection remains (Qt doesn't support disconnecting lambdas easily).
        For full cleanup, destroy the EventBus instance.
        
        Args:
            event: Event type to unsubscribe from
            callback: The callback function to remove
        """
        if event in self._subscribers:
            self._subscribers[event] = [
                cb for cb in self._subscribers[event] if cb != callback
            ]
            logger.debug(f"Unsubscribed from {event.name}: {callback.__name__}")
    
    def clear_subscribers(self) -> None:
        """Clear all subscribers (useful for testing)."""
        self._subscribers.clear()
        if hasattr(self, '_handlers'):
            self._handlers.clear()
        logger.debug("All subscribers cleared")
    
    # =========================================================================
    # Convenience methods for common events
    # =========================================================================
    
    def emit_connection_changed(self, status: str) -> None:
        """Convenience method to emit connection changed event."""
        self.publish(AppEvent.CONNECTION_CHANGED, status=status)
    
    def emit_api_ready(self, client: Any) -> None:
        """Convenience method to emit API client ready event."""
        self.publish(AppEvent.API_CLIENT_READY, client=client)
    
    def emit_api_disconnected(self) -> None:
        """Convenience method to emit API client disconnected event."""
        self.publish(AppEvent.API_CLIENT_DISCONNECTED)
    
    def emit_app_status(self, status: str) -> None:
        """Convenience method to emit application status change."""
        self.publish(AppEvent.APP_STATUS_CHANGED, status=status)
    
    def emit_queue_status(self, pending: int, failed: int) -> None:
        """Convenience method to emit queue status change."""
        self.publish(AppEvent.QUEUE_STATUS_CHANGED, pending=pending, failed=failed)


# Global singleton instance
event_bus = EventBus()
