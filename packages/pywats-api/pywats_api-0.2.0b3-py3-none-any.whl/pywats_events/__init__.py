"""
pywats_events - Protocol-Agnostic Event Infrastructure

This package provides the core event system for pyWATS, enabling integration
with various message sources (IPC-CFX, MQTT, webhooks, etc.) through a
unified, protocol-agnostic interface.

Architecture Layers:
    1. Core (this package) - EventBus, handlers, policies, routing
    2. Transports (pywats_cfx, pywats_mqtt, etc.) - Protocol-specific adapters
    3. Domain Handlers - Business logic that works with any transport

Example:
    >>> from pywats_events import EventBus, Event, EventType
    >>> from pywats_events.handlers import BaseHandler
    >>>
    >>> bus = EventBus()
    >>> bus.register_handler(MyReportHandler())
    >>> bus.start()
    >>>
    >>> # Events from any transport flow to registered handlers
    >>> bus.publish(Event(type=EventType.TEST_RESULT, payload={...}))
"""

from pywats_events.models.event import Event, EventMetadata
from pywats_events.models.event_types import EventType
from pywats_events.bus.event_bus import EventBus
from pywats_events.bus.async_event_bus import AsyncEventBus
from pywats_events.handlers.base_handler import BaseHandler
from pywats_events.handlers.handler_registry import HandlerRegistry

__version__ = "0.2.0b1"

__all__ = [
    # Core classes
    "Event",
    "EventMetadata",
    "EventType",
    "EventBus",
    "AsyncEventBus",
    # Handlers
    "BaseHandler",
    "HandlerRegistry",
]
