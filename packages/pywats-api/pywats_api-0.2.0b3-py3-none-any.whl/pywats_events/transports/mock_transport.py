"""
Mock transport for testing.

Provides a controllable transport for unit and integration testing
without requiring actual network connections.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pywats_events.transports.base_transport import BaseTransport, TransportState

if TYPE_CHECKING:
    from pywats_events.models.event import Event


logger = logging.getLogger(__name__)


class MockTransport(BaseTransport):
    """
    Mock transport for testing.
    
    Allows injecting events for testing handlers and event bus behavior
    without external dependencies.
    
    Example:
        >>> # In tests
        >>> transport = MockTransport()
        >>> bus.register_transport(transport)
        >>> bus.start()
        >>> 
        >>> # Inject test events
        >>> transport.inject_event(Event.create(
        ...     EventType.TEST_RESULT,
        ...     payload={"unit_id": "TEST123", "result": "pass"}
        ... ))
        >>> 
        >>> # Verify handlers received the event
        >>> assert handler.calls == 1
    """
    
    def __init__(
        self,
        name: str = "mock",
        auto_connect: bool = True,
    ):
        """
        Initialize mock transport.
        
        Args:
            name: Transport name
            auto_connect: Automatically connect on start
        """
        super().__init__(name=name)
        self._auto_connect = auto_connect
        
        # Track injected and published events
        self._injected_events: List["Event"] = []
        self._published_events: List["Event"] = []
        
        # Control behavior
        self._should_fail_on_start = False
        self._should_fail_on_inject = False
        self._inject_delay: float = 0.0
    
    @property
    def injected_events(self) -> List["Event"]:
        """List of events injected via inject_event()."""
        return self._injected_events.copy()
    
    @property
    def published_events(self) -> List["Event"]:
        """List of events published to the event bus."""
        return self._published_events.copy()
    
    @property
    def event_count(self) -> int:
        """Number of events published."""
        return len(self._published_events)
    
    def start(self) -> None:
        """Start the mock transport."""
        self._logger.info(f"Starting mock transport: {self._name}")
        
        if self._should_fail_on_start:
            self._set_state(TransportState.ERROR)
            raise ConnectionError("Mock transport configured to fail")
        
        self._set_state(TransportState.CONNECTING)
        
        if self._auto_connect:
            self._set_state(TransportState.CONNECTED)
    
    def stop(self) -> None:
        """Stop the mock transport."""
        self._logger.info(f"Stopping mock transport: {self._name}")
        self._set_state(TransportState.DISCONNECTED)
    
    async def start_async(self) -> None:
        """Start the mock transport asynchronously."""
        self.start()
    
    async def stop_async(self) -> None:
        """Stop the mock transport asynchronously."""
        self.stop()
    
    # =========================================================================
    # Event Injection (for testing)
    # =========================================================================
    
    def inject_event(self, event: "Event") -> None:
        """
        Inject an event as if it came from an external source.
        
        The event will be published to the event bus.
        
        Args:
            event: Event to inject
        """
        if self._should_fail_on_inject:
            raise RuntimeError("Mock transport configured to fail on inject")
        
        if not self.is_connected:
            raise RuntimeError("Transport not connected")
        
        self._injected_events.append(event)
        self._published_events.append(event)
        
        self._logger.debug(f"Injecting event: {event}")
        self.publish_event(event)
    
    async def inject_event_async(self, event: "Event") -> None:
        """
        Inject an event asynchronously.
        
        Args:
            event: Event to inject
        """
        import asyncio
        
        if self._inject_delay > 0:
            await asyncio.sleep(self._inject_delay)
        
        if self._should_fail_on_inject:
            raise RuntimeError("Mock transport configured to fail on inject")
        
        if not self.is_connected:
            raise RuntimeError("Transport not connected")
        
        self._injected_events.append(event)
        self._published_events.append(event)
        
        self._logger.debug(f"Injecting event async: {event}")
        await self.publish_event_async(event)
    
    def inject_events(self, events: List["Event"]) -> None:
        """
        Inject multiple events.
        
        Args:
            events: Events to inject
        """
        for event in events:
            self.inject_event(event)
    
    # =========================================================================
    # Test Control
    # =========================================================================
    
    def configure_failure(
        self,
        fail_on_start: bool = False,
        fail_on_inject: bool = False,
    ) -> None:
        """
        Configure transport to fail for testing error handling.
        
        Args:
            fail_on_start: Fail when start() is called
            fail_on_inject: Fail when inject_event() is called
        """
        self._should_fail_on_start = fail_on_start
        self._should_fail_on_inject = fail_on_inject
    
    def set_inject_delay(self, delay: float) -> None:
        """
        Set delay before injecting events (async only).
        
        Args:
            delay: Delay in seconds
        """
        self._inject_delay = delay
    
    def simulate_disconnect(self) -> None:
        """Simulate a disconnection."""
        if self.is_connected:
            self._set_state(TransportState.DISCONNECTED)
    
    def simulate_reconnect(self) -> None:
        """Simulate a reconnection."""
        if not self.is_connected:
            self._set_state(TransportState.RECONNECTING)
            self._set_state(TransportState.CONNECTED)
    
    def simulate_error(self, error: Exception) -> None:
        """
        Simulate a transport error.
        
        Args:
            error: Error to simulate
        """
        self._set_state(TransportState.ERROR)
        self._notify_error(error)
    
    def clear(self) -> None:
        """Clear all tracked events."""
        self._injected_events.clear()
        self._published_events.clear()
    
    def reset(self) -> None:
        """Reset transport to initial state."""
        self.clear()
        self._should_fail_on_start = False
        self._should_fail_on_inject = False
        self._inject_delay = 0.0
        self._set_state(TransportState.DISCONNECTED)
    
    # =========================================================================
    # Stats and Info
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get transport statistics."""
        return {
            **super().get_stats(),
            "injected_count": len(self._injected_events),
            "published_count": len(self._published_events),
        }
    
    def __repr__(self) -> str:
        return (
            f"MockTransport(name={self._name}, "
            f"state={self._state.value}, "
            f"events={len(self._published_events)})"
        )
