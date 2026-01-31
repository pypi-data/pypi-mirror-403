"""
Handler chain for middleware-style event processing.

Allows multiple handlers to process an event in sequence, with
the ability to modify, enrich, or short-circuit processing.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pywats_events.models.event import Event


logger = logging.getLogger(__name__)


class HandlerChain:
    """
    Middleware chain for event processing.
    
    Allows handlers to be chained together, where each handler can:
    - Process the event and pass to the next handler
    - Modify the event before passing to the next handler
    - Short-circuit processing by not calling next()
    
    Example:
        >>> chain = HandlerChain()
        >>> chain.add(LoggingMiddleware())
        >>> chain.add(ValidationMiddleware())
        >>> chain.add(EnrichmentMiddleware())
        >>> chain.add(FinalHandler())
        >>> 
        >>> await chain.execute(event)
    """
    
    def __init__(self):
        """Initialize an empty handler chain."""
        self._middlewares: List["ChainMiddleware"] = []
    
    def add(self, middleware: "ChainMiddleware") -> "HandlerChain":
        """
        Add middleware to the chain.
        
        Args:
            middleware: Middleware to add
            
        Returns:
            Self for chaining
        """
        self._middlewares.append(middleware)
        return self
    
    async def execute(self, event: "Event") -> Optional[Any]:
        """
        Execute the middleware chain for an event.
        
        Args:
            event: Event to process
            
        Returns:
            Result from the final handler (if any)
        """
        if not self._middlewares:
            return None
        
        # Build the chain from the end
        async def terminal(e: "Event") -> Optional[Any]:
            return None
        
        next_handler = terminal
        for middleware in reversed(self._middlewares):
            next_handler = self._wrap(middleware, next_handler)
        
        return await next_handler(event)
    
    def _wrap(
        self,
        middleware: "ChainMiddleware",
        next_handler: Callable
    ) -> Callable:
        """Wrap middleware to call next handler."""
        async def wrapped(event: "Event") -> Optional[Any]:
            return await middleware.process(event, next_handler)
        return wrapped
    
    def clear(self) -> None:
        """Remove all middleware from the chain."""
        self._middlewares.clear()
    
    def __len__(self) -> int:
        return len(self._middlewares)


class ChainMiddleware:
    """
    Base class for chain middleware.
    
    Middleware can process events and optionally pass them to the next
    handler in the chain.
    """
    
    async def process(
        self,
        event: "Event",
        next_handler: Callable[["Event"], Any]
    ) -> Optional[Any]:
        """
        Process an event in the chain.
        
        Args:
            event: The event to process
            next_handler: Function to call the next middleware
            
        Returns:
            Result from processing (passed through from next handlers)
        """
        # Default: pass through to next handler
        return await next_handler(event)


class LoggingMiddleware(ChainMiddleware):
    """Middleware that logs events passing through."""
    
    def __init__(self, log_level: int = logging.DEBUG):
        self.log_level = log_level
    
    async def process(
        self,
        event: "Event",
        next_handler: Callable[["Event"], Any]
    ) -> Optional[Any]:
        logger.log(
            self.log_level,
            f"Processing event: {event.event_type.value} ({event.id[:8]}...)"
        )
        try:
            result = await next_handler(event)
            logger.log(self.log_level, f"Event processed successfully: {event.id[:8]}...")
            return result
        except Exception as e:
            logger.error(f"Event processing failed: {event.id[:8]}... - {e}")
            raise


class ValidationMiddleware(ChainMiddleware):
    """Middleware that validates events before processing."""
    
    def __init__(self, validator: Callable[["Event"], bool]):
        """
        Initialize with a validator function.
        
        Args:
            validator: Function that returns True if event is valid
        """
        self.validator = validator
    
    async def process(
        self,
        event: "Event",
        next_handler: Callable[["Event"], Any]
    ) -> Optional[Any]:
        if not self.validator(event):
            logger.warning(f"Event validation failed: {event.id}")
            return None  # Short-circuit
        return await next_handler(event)


class EnrichmentMiddleware(ChainMiddleware):
    """Middleware that enriches events with additional data."""
    
    def __init__(self, enricher: Callable[["Event"], "Event"]):
        """
        Initialize with an enricher function.
        
        Args:
            enricher: Function that returns an enriched event
        """
        self.enricher = enricher
    
    async def process(
        self,
        event: "Event",
        next_handler: Callable[["Event"], Any]
    ) -> Optional[Any]:
        enriched_event = self.enricher(event)
        return await next_handler(enriched_event)
