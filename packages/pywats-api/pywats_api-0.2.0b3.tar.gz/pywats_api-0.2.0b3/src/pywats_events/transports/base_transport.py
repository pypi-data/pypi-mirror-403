"""
Base transport adapter for connecting to external message sources.

Transports are protocol-specific adapters that connect to message brokers
(AMQP, MQTT, etc.) or other event sources (webhooks, file watchers) and
translate messages into normalized pyWATS events.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pywats_events.models.event import Event
    from pywats_events.models.event_types import EventType
    from pywats_events.bus.event_bus import EventBus
    from pywats_events.bus.async_event_bus import AsyncEventBus


logger = logging.getLogger(__name__)


class TransportState(Enum):
    """Transport connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class BaseTransport(ABC):
    """
    Abstract base class for transport adapters.
    
    Transport adapters connect to external message sources and convert
    incoming messages to normalized pyWATS events.
    
    Responsibilities:
    1. Connect/disconnect from message source
    2. Subscribe to topics/channels
    3. Receive messages and convert to Events
    4. Publish Events to the EventBus
    5. Handle reconnection on failures
    
    Example:
        >>> class MQTTTransport(BaseTransport):
        ...     def __init__(self, broker_url: str, topics: List[str]):
        ...         super().__init__(name="mqtt")
        ...         self.broker_url = broker_url
        ...         self.topics = topics
        ...     
        ...     def start(self) -> None:
        ...         # Connect to MQTT broker
        ...         self._client = mqtt.Client()
        ...         self._client.on_message = self._on_message
        ...         self._client.connect(self.broker_url)
        ...         for topic in self.topics:
        ...             self._client.subscribe(topic)
        ...         self._client.loop_start()
        ...     
        ...     def _on_message(self, client, userdata, msg):
        ...         event = self._convert_message(msg)
        ...         self.publish_event(event)
    """
    
    def __init__(self, name: str = "transport"):
        """
        Initialize the transport.
        
        Args:
            name: Transport name for logging
        """
        self._name = name
        self._event_bus: Optional["EventBus"] = None
        self._async_event_bus: Optional["AsyncEventBus"] = None
        self._state = TransportState.DISCONNECTED
        self._logger = logging.getLogger(f"{__name__}.{name}")
        
        # Callbacks
        self._on_connect_callbacks: List[Callable[[], None]] = []
        self._on_disconnect_callbacks: List[Callable[[], None]] = []
        self._on_error_callbacks: List[Callable[[Exception], None]] = []
    
    @property
    def name(self) -> str:
        """Transport name."""
        return self._name
    
    @property
    def state(self) -> TransportState:
        """Current connection state."""
        return self._state
    
    @property
    def is_connected(self) -> bool:
        """Whether transport is connected."""
        return self._state == TransportState.CONNECTED
    
    def set_event_bus(self, event_bus: "EventBus") -> None:
        """
        Set the event bus for publishing events.
        
        Called by EventBus.register_transport().
        
        Args:
            event_bus: The EventBus to publish to
        """
        self._event_bus = event_bus
    
    def set_async_event_bus(self, event_bus: "AsyncEventBus") -> None:
        """
        Set the async event bus for publishing events.
        
        Called by AsyncEventBus.register_transport().
        
        Args:
            event_bus: The AsyncEventBus to publish to
        """
        self._async_event_bus = event_bus
    
    # =========================================================================
    # Lifecycle Methods (must be implemented)
    # =========================================================================
    
    @abstractmethod
    def start(self) -> None:
        """
        Start the transport (synchronous).
        
        Connect to the message source, subscribe to topics, and begin
        receiving messages.
        """
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """
        Stop the transport (synchronous).
        
        Disconnect from the message source and clean up resources.
        """
        pass
    
    async def start_async(self) -> None:
        """
        Start the transport (asynchronous).
        
        Default implementation calls synchronous start().
        Override for async-native transports.
        """
        self.start()
    
    async def stop_async(self) -> None:
        """
        Stop the transport (asynchronous).
        
        Default implementation calls synchronous stop().
        Override for async-native transports.
        """
        self.stop()
    
    # =========================================================================
    # Event Publishing
    # =========================================================================
    
    def publish_event(self, event: "Event") -> None:
        """
        Publish an event to the event bus.
        
        Call this from your message handler after converting the
        protocol-specific message to a pyWATS Event.
        
        Args:
            event: The event to publish
        """
        if self._event_bus:
            self._event_bus.publish(event)
        elif self._async_event_bus:
            # Queue for async processing
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._async_event_bus.publish_queued(event))
            except RuntimeError:
                # No running loop, create one
                asyncio.run(self._async_event_bus.publish_queued(event))
        else:
            self._logger.warning(f"No event bus set, dropping event: {event}")
    
    async def publish_event_async(self, event: "Event") -> None:
        """
        Publish an event asynchronously.
        
        Args:
            event: The event to publish
        """
        if self._async_event_bus:
            await self._async_event_bus.publish(event)
        elif self._event_bus:
            self._event_bus.publish(event)
        else:
            self._logger.warning(f"No event bus set, dropping event: {event}")
    
    # =========================================================================
    # State Management
    # =========================================================================
    
    def _set_state(self, state: TransportState) -> None:
        """
        Update transport state and trigger callbacks.
        
        Args:
            state: New state
        """
        old_state = self._state
        self._state = state
        self._logger.debug(f"State changed: {old_state.value} -> {state.value}")
        
        if state == TransportState.CONNECTED and old_state != TransportState.CONNECTED:
            self._notify_connect()
        elif state == TransportState.DISCONNECTED and old_state == TransportState.CONNECTED:
            self._notify_disconnect()
    
    def _notify_connect(self) -> None:
        """Notify listeners of connection."""
        from pywats_events.models.event import Event
        from pywats_events.models.event_types import EventType
        
        self._logger.info(f"Transport {self._name} connected")
        
        # Publish system event
        event = Event.create(
            event_type=EventType.TRANSPORT_CONNECTED,
            payload={"transport": self._name},
            source=self._name,
        )
        self.publish_event(event)
        
        for callback in self._on_connect_callbacks:
            try:
                callback()
            except Exception as e:
                self._logger.error(f"Connect callback error: {e}")
    
    def _notify_disconnect(self) -> None:
        """Notify listeners of disconnection."""
        from pywats_events.models.event import Event
        from pywats_events.models.event_types import EventType
        
        self._logger.info(f"Transport {self._name} disconnected")
        
        # Publish system event
        event = Event.create(
            event_type=EventType.TRANSPORT_DISCONNECTED,
            payload={"transport": self._name},
            source=self._name,
        )
        self.publish_event(event)
        
        for callback in self._on_disconnect_callbacks:
            try:
                callback()
            except Exception as e:
                self._logger.error(f"Disconnect callback error: {e}")
    
    def _notify_error(self, error: Exception) -> None:
        """Notify listeners of an error."""
        from pywats_events.models.event import Event
        from pywats_events.models.event_types import EventType
        
        self._logger.error(f"Transport {self._name} error: {error}")
        
        # Publish system event
        event = Event.create(
            event_type=EventType.TRANSPORT_ERROR,
            payload={
                "transport": self._name,
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
            source=self._name,
        )
        self.publish_event(event)
        
        for callback in self._on_error_callbacks:
            try:
                callback(error)
            except Exception as e:
                self._logger.error(f"Error callback error: {e}")
    
    # =========================================================================
    # Callbacks
    # =========================================================================
    
    def on_connect(self, callback: Callable[[], None]) -> None:
        """Register callback for connection."""
        self._on_connect_callbacks.append(callback)
    
    def on_disconnect(self, callback: Callable[[], None]) -> None:
        """Register callback for disconnection."""
        self._on_disconnect_callbacks.append(callback)
    
    def on_error(self, callback: Callable[[Exception], None]) -> None:
        """Register callback for errors."""
        self._on_error_callbacks.append(callback)
    
    # =========================================================================
    # Abstract Methods (optional overrides)
    # =========================================================================
    
    def get_subscribed_topics(self) -> List[str]:
        """
        Get list of subscribed topics/channels.
        
        Override to return actual subscriptions.
        
        Returns:
            List of topic names
        """
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get transport statistics.
        
        Override to return actual metrics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            "name": self._name,
            "state": self._state.value,
            "is_connected": self.is_connected,
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self._name}, state={self._state.value})"
