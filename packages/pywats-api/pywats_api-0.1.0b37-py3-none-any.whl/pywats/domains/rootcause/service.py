"""Sync RootCause service - thin wrapper around async service.

Provides synchronous access to RootCause ticket operations.

IMPORTANT - Server Behavior Note:
------------------------------------
The WATS server does NOT return the `assignee` field in ticket API responses.
This means:
- When you GET a ticket, the `assignee` field will always be None
- When you create/update a ticket with an assignee, the response won't include it

Workarounds:
1. Track assignee yourself after setting it
2. Use the `assignee` parameter in `change_status()` and `add_comment()`
3. For bulk operations, maintain a local mapping
"""
from typing import Optional, List, Union
from uuid import UUID

from ...core.sync_runner import run_sync
from .async_service import AsyncRootCauseService
from .async_repository import AsyncRootCauseRepository
from .models import Ticket, TicketUpdate
from .enums import TicketStatus, TicketPriority, TicketView


class RootCauseService:
    """Sync RootCause (Ticketing) service - wraps AsyncRootCauseService."""

    def __init__(
        self,
        async_service: Optional[AsyncRootCauseService] = None,
        repository: Optional[AsyncRootCauseRepository] = None,
    ) -> None:
        """
        Initialize with async_service or repository (backward compat).

        Args:
            async_service: AsyncRootCauseService instance (preferred)
            repository: AsyncRootCauseRepository instance (legacy)
        """
        if async_service:
            self._async_service = async_service
        elif repository:
            self._async_service = AsyncRootCauseService(repository)
        else:
            raise ValueError("Either async_service or repository is required")

    @classmethod
    def from_repository(cls, repository: AsyncRootCauseRepository) -> "RootCauseService":
        """
        Create service from repository.

        Args:
            repository: AsyncRootCauseRepository instance

        Returns:
            RootCauseService instance
        """
        async_service = AsyncRootCauseService(repository)
        return cls(async_service=async_service)

    # =========================================================================
    # Ticket Operations
    # =========================================================================

    def get_ticket(self, ticket_id: Union[str, UUID]) -> Optional[Ticket]:
        """Get a ticket by ID."""
        return run_sync(self._async_service.get_ticket(ticket_id))

    def get_tickets(
        self,
        status: TicketStatus = TicketStatus.OPEN,
        view: TicketView = TicketView.ASSIGNED,
        search_string: Optional[str] = None,
    ) -> List[Ticket]:
        """Get tickets with given status."""
        return run_sync(self._async_service.get_tickets(status, view, search_string))

    def get_open_tickets(
        self, view: TicketView = TicketView.ASSIGNED
    ) -> List[Ticket]:
        """Get all open tickets."""
        return run_sync(self._async_service.get_open_tickets(view))

    def get_active_tickets(
        self, view: TicketView = TicketView.ASSIGNED
    ) -> List[Ticket]:
        """Get all active tickets (Open or In Progress)."""
        return run_sync(self._async_service.get_active_tickets(view))

    def create_ticket(
        self,
        subject: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
        assignee: Optional[str] = None,
        team: Optional[str] = None,
        report_uuid: Optional[Union[str, UUID]] = None,
        initial_comment: Optional[str] = None,
    ) -> Optional[Ticket]:
        """Create a new ticket."""
        return run_sync(
            self._async_service.create_ticket(
                subject, priority, assignee, team, report_uuid, initial_comment
            )
        )

    def update_ticket(self, ticket: Ticket) -> Optional[Ticket]:
        """Update an existing ticket."""
        return run_sync(self._async_service.update_ticket(ticket))

    def add_comment(
        self, ticket_id: Union[str, UUID], comment: str,
        assignee: Optional[str] = None
    ) -> Optional[Ticket]:
        """Add a comment to a ticket."""
        return run_sync(self._async_service.add_comment(ticket_id, comment, assignee))

    def change_status(
        self, ticket_id: Union[str, UUID], status: TicketStatus,
        assignee: Optional[str] = None
    ) -> Optional[Ticket]:
        """Change the status of a ticket."""
        return run_sync(self._async_service.change_status(ticket_id, status, assignee))

    def assign_ticket(
        self, ticket_id: Union[str, UUID], assignee: str
    ) -> Optional[Ticket]:
        """Assign a ticket to a user."""
        return run_sync(self._async_service.assign_ticket(ticket_id, assignee))

    def archive_tickets(
        self, ticket_ids: List[Union[str, UUID]]
    ) -> Optional[Ticket]:
        """Archive solved tickets."""
        return run_sync(self._async_service.archive_tickets(ticket_ids))

    # =========================================================================
    # Attachment Operations
    # =========================================================================

    def get_attachment(
        self, attachment_id: Union[str, UUID], filename: Optional[str] = None
    ) -> Optional[bytes]:
        """Get attachment content."""
        return run_sync(self._async_service.get_attachment(attachment_id, filename))

    def upload_attachment(
        self, file_content: bytes, filename: str
    ) -> Optional[UUID]:
        """Upload an attachment."""
        return run_sync(self._async_service.upload_attachment(file_content, filename))
