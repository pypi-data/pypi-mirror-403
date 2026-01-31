"""
Retry policy for failed event handling.

Provides configurable retry behavior with exponential backoff,
maximum retry limits, and exception filtering.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Set, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from pywats_events.models.event import Event


logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """
    Configuration for retry behavior.
    
    Attributes:
        max_retries: Maximum number of retry attempts (0 = no retries)
        initial_delay: Initial delay before first retry (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Base for exponential backoff (delay = initial * base^attempt)
        jitter: Whether to add random jitter to delays
        jitter_factor: Jitter range as factor of delay (0.1 = ±10%)
    """
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1


class RetryPolicy:
    """
    Retry policy for handling event processing failures.
    
    Determines when and how to retry failed event handlers.
    
    Example:
        >>> policy = RetryPolicy(
        ...     max_retries=3,
        ...     initial_delay=1.0,
        ...     exponential_backoff=True
        ... )
        >>> policy.retry_on(ConnectionError, TimeoutError)
        >>> policy.no_retry_on(ValidationError)
        >>> 
        >>> if policy.should_retry(event, error):
        ...     delay = policy.get_delay(event)
        ...     await asyncio.sleep(delay)
        ...     await handler.handle(event.with_retry())
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        jitter_factor: float = 0.1,
    ):
        """
        Initialize retry policy.
        
        Args:
            max_retries: Maximum retry attempts
            initial_delay: Initial delay (seconds)
            max_delay: Maximum delay (seconds)
            exponential_base: Exponential backoff base
            jitter: Add random jitter
            jitter_factor: Jitter range factor
        """
        self._config = RetryConfig(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            jitter_factor=jitter_factor,
        )
        
        # Exception types to retry on (empty = retry all)
        self._retry_exceptions: Set[Type[Exception]] = set()
        
        # Exception types to never retry on
        self._no_retry_exceptions: Set[Type[Exception]] = set()
        
        # Custom retry predicates
        self._retry_predicates: List[Callable[["Event", Exception], bool]] = []
        
        self._logger = logging.getLogger(__name__)
    
    @property
    def max_retries(self) -> int:
        """Maximum retry attempts."""
        return self._config.max_retries
    
    @property
    def config(self) -> RetryConfig:
        """Retry configuration."""
        return self._config
    
    def retry_on(self, *exception_types: Type[Exception]) -> "RetryPolicy":
        """
        Add exception types to retry on.
        
        If any retry_on exceptions are specified, ONLY those exception
        types will be retried.
        
        Args:
            exception_types: Exception types to retry
            
        Returns:
            Self for chaining
        """
        self._retry_exceptions.update(exception_types)
        return self
    
    def no_retry_on(self, *exception_types: Type[Exception]) -> "RetryPolicy":
        """
        Add exception types to never retry on.
        
        These take precedence over retry_on exceptions.
        
        Args:
            exception_types: Exception types to not retry
            
        Returns:
            Self for chaining
        """
        self._no_retry_exceptions.update(exception_types)
        return self
    
    def add_predicate(
        self,
        predicate: Callable[["Event", Exception], bool]
    ) -> "RetryPolicy":
        """
        Add a custom retry predicate.
        
        Args:
            predicate: Function(event, error) -> bool, returns True to retry
            
        Returns:
            Self for chaining
        """
        self._retry_predicates.append(predicate)
        return self
    
    def should_retry(self, event: "Event", error: Exception) -> bool:
        """
        Determine if an event should be retried after a failure.
        
        Args:
            event: The failed event
            error: The exception that was raised
            
        Returns:
            True if the event should be retried
        """
        # Check retry count
        if event.metadata.retry_count >= self._config.max_retries:
            self._logger.debug(
                f"Max retries ({self._config.max_retries}) reached for event {event.id[:8]}"
            )
            return False
        
        # Check no-retry exceptions first (takes precedence)
        for exc_type in self._no_retry_exceptions:
            if isinstance(error, exc_type):
                self._logger.debug(
                    f"No-retry exception {type(error).__name__} for event {event.id[:8]}"
                )
                return False
        
        # Check retry exceptions (if any specified)
        if self._retry_exceptions:
            matched = any(
                isinstance(error, exc_type) 
                for exc_type in self._retry_exceptions
            )
            if not matched:
                self._logger.debug(
                    f"Exception {type(error).__name__} not in retry list for event {event.id[:8]}"
                )
                return False
        
        # Check custom predicates (all must pass)
        for predicate in self._retry_predicates:
            try:
                if not predicate(event, error):
                    self._logger.debug(
                        f"Predicate rejected retry for event {event.id[:8]}"
                    )
                    return False
            except Exception as pred_error:
                self._logger.warning(f"Predicate error: {pred_error}")
                return False
        
        return True
    
    def get_delay(self, event: "Event") -> float:
        """
        Calculate the delay before the next retry attempt.
        
        Uses exponential backoff with optional jitter.
        
        Args:
            event: The event being retried
            
        Returns:
            Delay in seconds
        """
        attempt = event.metadata.retry_count
        
        # Exponential backoff
        delay = self._config.initial_delay * (
            self._config.exponential_base ** attempt
        )
        
        # Cap at max delay
        delay = min(delay, self._config.max_delay)
        
        # Add jitter
        if self._config.jitter:
            jitter_range = delay * self._config.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    def wait_sync(self, event: "Event") -> None:
        """
        Wait for the retry delay (synchronous).
        
        Args:
            event: The event being retried
        """
        delay = self.get_delay(event)
        self._logger.debug(f"Waiting {delay:.2f}s before retry for event {event.id[:8]}")
        time.sleep(delay)
    
    async def wait_async(self, event: "Event") -> None:
        """
        Wait for the retry delay (asynchronous).
        
        Args:
            event: The event being retried
        """
        import asyncio
        delay = self.get_delay(event)
        self._logger.debug(f"Waiting {delay:.2f}s before retry for event {event.id[:8]}")
        await asyncio.sleep(delay)
    
    def __repr__(self) -> str:
        return (
            f"RetryPolicy(max_retries={self._config.max_retries}, "
            f"initial_delay={self._config.initial_delay}, "
            f"max_delay={self._config.max_delay})"
        )


class NoRetryPolicy(RetryPolicy):
    """Policy that never retries."""
    
    def __init__(self):
        super().__init__(max_retries=0)
    
    def should_retry(self, event: "Event", error: Exception) -> bool:
        return False


class ImmediateRetryPolicy(RetryPolicy):
    """Policy that retries immediately without delay."""
    
    def __init__(self, max_retries: int = 3):
        super().__init__(max_retries=max_retries, initial_delay=0, jitter=False)
    
    def get_delay(self, event: "Event") -> float:
        return 0.0
