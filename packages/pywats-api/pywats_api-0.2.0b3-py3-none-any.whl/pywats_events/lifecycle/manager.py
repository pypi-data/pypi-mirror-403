"""
Lifecycle management for event system components.
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Callable, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pywats_events.bus.event_bus import EventBus
    from pywats_events.bus.async_event_bus import AsyncEventBus
    from pywats_events.transports.base_transport import BaseTransport
    from pywats_events.handlers.base_handler import BaseHandler


logger = logging.getLogger(__name__)


class LifecycleState(Enum):
    """Lifecycle states."""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class LifecycleManager:
    """
    Manages the lifecycle of event system components.
    
    Coordinates startup and shutdown of event bus, transports, and handlers
    with proper ordering and error handling.
    
    Example:
        >>> manager = LifecycleManager()
        >>> manager.add_component(event_bus)
        >>> manager.add_component(cfx_transport)
        >>> manager.add_component(mqtt_transport)
        >>> 
        >>> # Start all components
        >>> await manager.start()
        >>> 
        >>> # Stop all components (reverse order)
        >>> await manager.stop()
    """
    
    def __init__(self):
        """Initialize lifecycle manager."""
        self._components: List[tuple[any, int]] = []  # (component, priority)
        self._state = LifecycleState.CREATED
        self._on_start_callbacks: List[Callable[[], None]] = []
        self._on_stop_callbacks: List[Callable[[], None]] = []
        self._on_error_callbacks: List[Callable[[Exception], None]] = []
        self._logger = logging.getLogger(__name__)
    
    @property
    def state(self) -> LifecycleState:
        """Current lifecycle state."""
        return self._state
    
    @property
    def is_running(self) -> bool:
        """Whether manager is in running state."""
        return self._state == LifecycleState.RUNNING
    
    def add_component(self, component: any, priority: int = 100) -> "LifecycleManager":
        """
        Add a component to manage.
        
        Components are started in priority order (lower = first)
        and stopped in reverse order.
        
        Args:
            component: Component with start/stop methods
            priority: Startup priority
            
        Returns:
            Self for chaining
        """
        self._components.append((component, priority))
        self._components.sort(key=lambda x: x[1])
        return self
    
    def add_event_bus(
        self,
        event_bus: "EventBus | AsyncEventBus",
        priority: int = 0
    ) -> "LifecycleManager":
        """
        Add event bus (starts first, stops last).
        
        Args:
            event_bus: Event bus to manage
            priority: Startup priority (default 0 = first)
            
        Returns:
            Self for chaining
        """
        return self.add_component(event_bus, priority)
    
    def add_transport(
        self,
        transport: "BaseTransport",
        priority: int = 50
    ) -> "LifecycleManager":
        """
        Add transport adapter.
        
        Args:
            transport: Transport to manage
            priority: Startup priority (default 50 = after bus)
            
        Returns:
            Self for chaining
        """
        return self.add_component(transport, priority)
    
    async def start(self) -> None:
        """
        Start all components in priority order.
        
        If any component fails to start, previously started components
        will be stopped.
        """
        if self._state == LifecycleState.RUNNING:
            self._logger.warning("Already running")
            return
        
        self._logger.info("Starting lifecycle manager")
        self._state = LifecycleState.STARTING
        
        started: List[any] = []
        
        try:
            for component, priority in self._components:
                self._logger.debug(f"Starting component: {component}")
                
                if hasattr(component, 'start_async'):
                    await component.start_async()
                elif hasattr(component, 'start'):
                    result = component.start()
                    if asyncio.iscoroutine(result):
                        await result
                
                started.append(component)
            
            self._state = LifecycleState.RUNNING
            self._logger.info("Lifecycle manager started")
            
            # Notify callbacks
            for callback in self._on_start_callbacks:
                try:
                    result = callback()
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    self._logger.error(f"Start callback error: {e}")
                    
        except Exception as e:
            self._logger.error(f"Startup failed: {e}")
            self._state = LifecycleState.ERROR
            
            # Rollback: stop started components
            for component in reversed(started):
                try:
                    if hasattr(component, 'stop_async'):
                        await component.stop_async()
                    elif hasattr(component, 'stop'):
                        result = component.stop()
                        if asyncio.iscoroutine(result):
                            await result
                except Exception as stop_error:
                    self._logger.error(f"Rollback stop error: {stop_error}")
            
            # Notify error callbacks
            for callback in self._on_error_callbacks:
                try:
                    result = callback(e)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as cb_error:
                    self._logger.error(f"Error callback error: {cb_error}")
            
            raise
    
    async def stop(self, timeout: float = 10.0) -> None:
        """
        Stop all components in reverse priority order.
        
        Args:
            timeout: Maximum time to wait for each component
        """
        if self._state == LifecycleState.STOPPED:
            return
        
        self._logger.info("Stopping lifecycle manager")
        self._state = LifecycleState.STOPPING
        
        # Stop in reverse order
        for component, priority in reversed(self._components):
            try:
                self._logger.debug(f"Stopping component: {component}")
                
                if hasattr(component, 'stop_async'):
                    await asyncio.wait_for(
                        component.stop_async(),
                        timeout=timeout
                    )
                elif hasattr(component, 'stop'):
                    result = component.stop()
                    if asyncio.iscoroutine(result):
                        await asyncio.wait_for(result, timeout=timeout)
                        
            except asyncio.TimeoutError:
                self._logger.warning(f"Timeout stopping component: {component}")
            except Exception as e:
                self._logger.error(f"Error stopping component: {e}")
        
        self._state = LifecycleState.STOPPED
        self._logger.info("Lifecycle manager stopped")
        
        # Notify callbacks
        for callback in self._on_stop_callbacks:
            try:
                result = callback()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                self._logger.error(f"Stop callback error: {e}")
    
    def on_start(self, callback: Callable[[], None]) -> "LifecycleManager":
        """Register callback for successful startup."""
        self._on_start_callbacks.append(callback)
        return self
    
    def on_stop(self, callback: Callable[[], None]) -> "LifecycleManager":
        """Register callback for shutdown."""
        self._on_stop_callbacks.append(callback)
        return self
    
    def on_error(self, callback: Callable[[Exception], None]) -> "LifecycleManager":
        """Register callback for errors."""
        self._on_error_callbacks.append(callback)
        return self
    
    async def __aenter__(self) -> "LifecycleManager":
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()
    
    def __repr__(self) -> str:
        return f"LifecycleManager(components={len(self._components)}, state={self._state.value})"
