"""RootCause domain module.

Provides ticketing system services and models.
"""
from .enums import (
    TicketStatus,
    TicketPriority,
    TicketView,
    TicketUpdateType,
)
from .models import Ticket, TicketUpdate, TicketAttachment

# Async implementations (primary API)
from .async_repository import AsyncRootCauseRepository
from .async_service import AsyncRootCauseService

# Backward-compatible aliases
RootCauseRepository = AsyncRootCauseRepository
RootCauseService = AsyncRootCauseService

__all__ = [
    # Enums
    "TicketStatus",
    "TicketPriority",
    "TicketView",
    "TicketUpdateType",
    # Models
    "Ticket",
    "TicketUpdate",
    "TicketAttachment",
    # Async implementations (primary API)
    "AsyncRootCauseRepository",
    "AsyncRootCauseService",
    # Backward-compatible aliases
    "RootCauseRepository",
    "RootCauseService",
]
