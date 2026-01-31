"""
CFX AMQP Transport.

Transport adapter for IPC-CFX communication over AMQP (RabbitMQ).
Extends the base transport from pywats_events.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Optional
from uuid import uuid4

from pywats_events.models import Event, EventMetadata, EventType
from pywats_events.transports import BaseTransport, TransportState

from ..config.cfx_config import CFXConfig
from ..models.cfx_messages import (
    CFXMessage,
    EndpointConnected,
    EndpointDisconnected,
    parse_cfx_message,
    serialize_cfx_message,
)


logger = logging.getLogger(__name__)


class CFXTransport(BaseTransport):
    """
    IPC-CFX transport adapter using AMQP.
    
    Connects to an AMQP broker (typically RabbitMQ) and subscribes to
    CFX topics. Incoming CFX messages are converted to normalized Events
    and published to the event bus.
    
    Example usage:
        from pywats_cfx import CFXTransport, CFXConfig
        from pywats_events import EventBus
        
        config = CFXConfig(
            amqp=AMQPConfig(host="broker.example.com"),
            endpoint=EndpointConfig(cfx_handle="//MyCompany/WATS/Station1"),
        )
        
        bus = EventBus()
        transport = CFXTransport(config, bus)
        
        await transport.connect()
        # ... transport receives CFX messages and publishes events
        await transport.disconnect()
    """
    
    def __init__(
        self,
        config: CFXConfig,
        on_event: Optional[Callable[[Event], None]] = None,
    ) -> None:
        """
        Initialize CFX transport.
        
        Args:
            config: CFX configuration with AMQP and endpoint settings.
            on_event: Callback for received events.
        """
        super().__init__(name="cfx-amqp")
        
        self.config = config
        self._on_event = on_event
        
        # AMQP connection state (set when connected)
        self._connection: Optional[Any] = None
        self._channel: Optional[Any] = None
        self._consumer_tag: Optional[str] = None
        
        # Background task for consuming messages
        self._consume_task: Optional[asyncio.Task] = None
        
        # Reconnection state
        self._reconnect_attempts: int = 0
        self._should_reconnect: bool = True
        
        # Statistics
        self._messages_received: int = 0
        self._messages_sent: int = 0
        self._last_message_time: Optional[datetime] = None
    
    @property
    def transport_type(self) -> str:
        """Return transport type identifier."""
        return "amqp"
    
    async def connect(self) -> None:
        """
        Connect to AMQP broker and start consuming CFX messages.
        
        Establishes connection, declares exchange/queue, binds routing keys,
        and starts async message consumer.
        """
        if self._state == TransportState.CONNECTED:
            logger.warning("CFX transport already connected")
            return
        
        self._state = TransportState.CONNECTING
        logger.info(f"Connecting to CFX broker at {self.config.amqp.host}:{self.config.amqp.port}")
        
        try:
            # Import aio_pika here to make it optional
            import aio_pika
            
            # Connect to broker
            self._connection = await aio_pika.connect_robust(
                self.config.amqp.broker_url,
                timeout=self.config.amqp.connection_timeout,
            )
            
            # Create channel
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=self.config.exchange.prefetch_count)
            
            # Declare exchange
            exchange = await self._channel.declare_exchange(
                self.config.exchange.exchange_name,
                self.config.exchange.exchange_type,
                durable=self.config.exchange.durable,
                auto_delete=self.config.exchange.auto_delete,
            )
            
            # Declare queue
            queue_name = f"{self.config.exchange.queue_name_prefix}.{self.config.endpoint.cfx_handle}"
            queue = await self._channel.declare_queue(
                queue_name,
                durable=self.config.exchange.queue_durable,
                auto_delete=self.config.exchange.queue_auto_delete,
                exclusive=self.config.exchange.queue_exclusive,
            )
            
            # Bind routing keys
            for binding_key in self.config.exchange.binding_keys:
                await queue.bind(exchange, routing_key=binding_key)
                logger.debug(f"Bound queue to routing key: {binding_key}")
            
            # Start consuming
            self._consumer_tag = await queue.consume(self._on_message)
            
            self._state = TransportState.CONNECTED
            self._reconnect_attempts = 0
            
            logger.info(f"CFX transport connected as {self.config.endpoint.cfx_handle}")
            
            # Publish endpoint connected event
            if self.config.publish_endpoint_connected:
                await self._publish_endpoint_connected()
            
        except ImportError:
            logger.error("aio_pika not installed. Run: pip install aio_pika")
            self._state = TransportState.ERROR
            raise
        except Exception as e:
            logger.error(f"Failed to connect to CFX broker: {e}")
            self._state = TransportState.ERROR
            
            if self.config.auto_reconnect:
                await self._schedule_reconnect()
            else:
                raise
    
    async def disconnect(self) -> None:
        """Disconnect from AMQP broker."""
        if self._state == TransportState.DISCONNECTED:
            return
        
        self._should_reconnect = False
        self._state = TransportState.DISCONNECTING
        
        logger.info("Disconnecting from CFX broker")
        
        try:
            # Publish endpoint disconnected event
            if self.config.publish_endpoint_disconnected and self._channel:
                await self._publish_endpoint_disconnected()
            
            # Cancel consumer
            if self._channel and self._consumer_tag:
                await self._channel.cancel(self._consumer_tag)
            
            # Close connection
            if self._connection:
                await self._connection.close()
            
        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")
        finally:
            self._connection = None
            self._channel = None
            self._consumer_tag = None
            self._state = TransportState.DISCONNECTED
            
            logger.info("CFX transport disconnected")
    
    async def send(self, event: Event) -> None:
        """
        Send an event as a CFX message.
        
        Converts the normalized event to a CFX message and publishes
        to the AMQP exchange.
        
        Args:
            event: Event to send.
        """
        if self._state != TransportState.CONNECTED:
            raise RuntimeError("CFX transport not connected")
        
        try:
            import aio_pika
            
            # Convert event to CFX message format
            cfx_message = self._event_to_cfx(event)
            message_body = json.dumps(cfx_message).encode()
            
            # Get exchange
            exchange = await self._channel.get_exchange(self.config.exchange.exchange_name)
            
            # Determine routing key from event type
            routing_key = self._get_routing_key(event)
            
            # Publish message
            await exchange.publish(
                aio_pika.Message(
                    body=message_body,
                    content_type="application/json",
                    message_id=str(event.event_id),
                    correlation_id=event.metadata.correlation_id,
                    timestamp=datetime.now(),
                ),
                routing_key=routing_key,
            )
            
            self._messages_sent += 1
            self._last_message_time = datetime.now()
            
            if self.config.log_messages:
                logger.debug(f"Sent CFX message: {routing_key}")
            
        except Exception as e:
            logger.error(f"Failed to send CFX message: {e}")
            raise
    
    async def _on_message(self, message: Any) -> None:
        """
        Handle incoming AMQP message.
        
        Parses CFX JSON, converts to normalized Event, and invokes callback.
        """
        async with message.process():
            try:
                # Parse JSON body
                body = json.loads(message.body.decode())
                
                # Parse as CFX message
                cfx_message = parse_cfx_message(body)
                
                # Convert to normalized event
                event = self._cfx_to_event(cfx_message, message.routing_key)
                
                self._messages_received += 1
                self._last_message_time = datetime.now()
                
                if self.config.log_messages:
                    logger.debug(f"Received CFX message: {cfx_message.MessageName}")
                
                # Invoke callback
                if self._on_event:
                    self._on_event(event)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in CFX message: {e}")
            except Exception as e:
                logger.error(f"Error processing CFX message: {e}")
    
    def _cfx_to_event(self, cfx_message: CFXMessage, routing_key: str) -> Event:
        """
        Convert CFX message to normalized Event.
        
        Maps CFX message types to EventType enum values.
        """
        # Map CFX message name to event type
        event_type = self._map_message_to_event_type(cfx_message.MessageName)
        
        # Build metadata
        metadata = EventMetadata(
            correlation_id=cfx_message.RequestID or str(uuid4()),
            source=f"cfx:{self.config.endpoint.cfx_handle}",
            trace_id=str(uuid4()),
        )
        
        # Create event with CFX message as payload
        return Event(
            event_type=event_type,
            payload=serialize_cfx_message(cfx_message),
            metadata=metadata,
        )
    
    def _event_to_cfx(self, event: Event) -> dict[str, Any]:
        """Convert normalized Event back to CFX message format."""
        # If payload is already CFX format, use it directly
        if isinstance(event.payload, dict) and "MessageName" in event.payload:
            return event.payload
        
        # Otherwise, wrap payload in a generic CFX message
        return {
            "MessageName": f"CFX.Custom.{event.event_type.value}",
            "CFX_MessageHandle": str(event.event_id),
            "RequestID": event.metadata.correlation_id,
            "Payload": event.payload,
        }
    
    def _get_routing_key(self, event: Event) -> str:
        """Determine AMQP routing key from event type."""
        # If payload has MessageName, use it as routing key
        if isinstance(event.payload, dict) and "MessageName" in event.payload:
            return event.payload["MessageName"]
        
        # Map event type to CFX topic
        type_mapping = {
            EventType.TEST_RESULT: "CFX.Production.Testing.UnitsTested",
            EventType.INSPECTION_RESULT: "CFX.Production.Assembly.UnitsInspected",
            EventType.ASSET_FAULT: "CFX.ResourcePerformance.FaultOccurred",
            EventType.MATERIAL_INSTALLED: "CFX.Production.Assembly.MaterialsInstalled",
            EventType.WORK_STARTED: "CFX.Production.WorkStarted",
            EventType.WORK_COMPLETED: "CFX.Production.WorkCompleted",
        }
        
        return type_mapping.get(event.event_type, f"CFX.Custom.{event.event_type.value}")
    
    def _map_message_to_event_type(self, message_name: str) -> EventType:
        """Map CFX message name to EventType."""
        mapping = {
            "CFX.Production.Testing.UnitsTested": EventType.TEST_RESULT,
            "CFX.Production.Assembly.UnitsInspected": EventType.INSPECTION_RESULT,
            "CFX.Production.Assembly.MaterialsInstalled": EventType.MATERIAL_INSTALLED,
            "CFX.ResourcePerformance.FaultOccurred": EventType.ASSET_FAULT,
            "CFX.ResourcePerformance.FaultCleared": EventType.ASSET_FAULT_CLEARED,
            "CFX.ResourcePerformance.StationStateChanged": EventType.ASSET_STATE_CHANGED,
            "CFX.Production.WorkStarted": EventType.WORK_STARTED,
            "CFX.Production.WorkCompleted": EventType.WORK_COMPLETED,
            "CFX.Production.UnitsArrived": EventType.UNIT_ARRIVED,
            "CFX.Production.UnitsDeparted": EventType.UNIT_DEPARTED,
            "CFX.Production.UnitsDisqualified": EventType.UNIT_DISQUALIFIED,
        }
        
        return mapping.get(message_name, EventType.CUSTOM)
    
    async def _publish_endpoint_connected(self) -> None:
        """Publish EndpointConnected CFX message."""
        message = EndpointConnected(CFXHandle=self.config.endpoint.cfx_handle)
        event = Event(
            event_type=EventType.TRANSPORT_CONNECTED,
            payload=serialize_cfx_message(message),
        )
        await self.send(event)
    
    async def _publish_endpoint_disconnected(self) -> None:
        """Publish EndpointDisconnected CFX message."""
        message = EndpointDisconnected(CFXHandle=self.config.endpoint.cfx_handle)
        event = Event(
            event_type=EventType.TRANSPORT_DISCONNECTED,
            payload=serialize_cfx_message(message),
        )
        await self.send(event)
    
    async def _schedule_reconnect(self) -> None:
        """Schedule automatic reconnection with exponential backoff."""
        if not self._should_reconnect:
            return
        
        self._reconnect_attempts += 1
        retry_config = self.config.retry
        
        if self._reconnect_attempts > retry_config.max_retries:
            logger.error(f"Max reconnection attempts ({retry_config.max_retries}) exceeded")
            self._state = TransportState.ERROR
            return
        
        # Calculate backoff delay
        delay = min(
            retry_config.initial_delay * (retry_config.exponential_base ** (self._reconnect_attempts - 1)),
            retry_config.max_delay,
        )
        
        logger.info(f"Scheduling reconnection attempt {self._reconnect_attempts} in {delay:.1f}s")
        
        await asyncio.sleep(delay)
        
        if self._should_reconnect:
            await self.connect()
    
    def get_statistics(self) -> dict[str, Any]:
        """Get transport statistics."""
        return {
            "state": self._state.value,
            "messages_received": self._messages_received,
            "messages_sent": self._messages_sent,
            "last_message_time": self._last_message_time.isoformat() if self._last_message_time else None,
            "reconnect_attempts": self._reconnect_attempts,
            "endpoint": self.config.endpoint.cfx_handle,
            "broker": f"{self.config.amqp.host}:{self.config.amqp.port}",
        }
