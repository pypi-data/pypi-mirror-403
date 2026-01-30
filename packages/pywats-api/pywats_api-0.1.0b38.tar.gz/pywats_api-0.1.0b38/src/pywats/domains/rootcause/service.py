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
        """Get a ticket by ID.

        Args:
            ticket_id: Ticket UUID or string ID.

        Returns:
            Ticket if found, None otherwise.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If ticket_id format is invalid.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_ticket(ticket_id))

    def get_tickets(
        self,
        status: TicketStatus = TicketStatus.OPEN,
        view: TicketView = TicketView.ASSIGNED,
        search_string: Optional[str] = None,
    ) -> List[Ticket]:
        """Get tickets with given status.

        Args:
            status: Filter by ticket status (default: OPEN).
            view: Filter by view type (default: ASSIGNED).
            search_string: Optional text search filter.

        Returns:
            List of matching Ticket objects.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_tickets(status, view, search_string))

    def get_open_tickets(
        self, view: TicketView = TicketView.ASSIGNED
    ) -> List[Ticket]:
        """Get all open tickets.

        Args:
            view: Filter by view type (default: ASSIGNED).

        Returns:
            List of open Ticket objects.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_open_tickets(view))

    def get_active_tickets(
        self, view: TicketView = TicketView.ASSIGNED
    ) -> List[Ticket]:
        """Get all active tickets (Open or In Progress).

        Args:
            view: Filter by view type (default: ASSIGNED).

        Returns:
            List of active Ticket objects.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
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
        """Create a new ticket.

        Args:
            subject: Ticket subject/title.
            priority: Ticket priority (default: MEDIUM).
            assignee: Optional user to assign ticket to.
            team: Optional team to assign ticket to.
            report_uuid: Optional linked report UUID.
            initial_comment: Optional initial comment text.

        Returns:
            Created Ticket or None if failed.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If subject is empty or data is invalid.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(
            self._async_service.create_ticket(
                subject, priority, assignee, team, report_uuid, initial_comment
            )
        )

    def update_ticket(self, ticket: Ticket) -> Optional[Ticket]:
        """Update an existing ticket.

        Args:
            ticket: Ticket object with updated fields.

        Returns:
            Updated Ticket or None if failed.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If ticket data is invalid.
            NotFoundError: If ticket not found.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.update_ticket(ticket))

    def add_comment(
        self, ticket_id: Union[str, UUID], comment: str,
        assignee: Optional[str] = None
    ) -> Optional[Ticket]:
        """Add a comment to a ticket.

        Args:
            ticket_id: Ticket UUID or string ID.
            comment: Comment text to add.
            assignee: Optional new assignee.

        Returns:
            Updated Ticket or None if failed.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If ticket_id or comment is invalid.
            NotFoundError: If ticket not found.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.add_comment(ticket_id, comment, assignee))

    def change_status(
        self, ticket_id: Union[str, UUID], status: TicketStatus,
        assignee: Optional[str] = None
    ) -> Optional[Ticket]:
        """Change the status of a ticket.

        Args:
            ticket_id: Ticket UUID or string ID.
            status: New ticket status.
            assignee: Optional new assignee.

        Returns:
            Updated Ticket or None if failed.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If ticket_id or status is invalid.
            NotFoundError: If ticket not found.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.change_status(ticket_id, status, assignee))

    def assign_ticket(
        self, ticket_id: Union[str, UUID], assignee: str
    ) -> Optional[Ticket]:
        """Assign a ticket to a user.

        Args:
            ticket_id: Ticket UUID or string ID.
            assignee: User to assign the ticket to.

        Returns:
            Updated Ticket or None if failed.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If ticket_id or assignee is invalid.
            NotFoundError: If ticket not found.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.assign_ticket(ticket_id, assignee))

    def archive_tickets(
        self, ticket_ids: List[Union[str, UUID]]
    ) -> Optional[Ticket]:
        """Archive solved tickets.

        Args:
            ticket_ids: List of ticket UUIDs or string IDs to archive.

        Returns:
            Last archived Ticket or None if failed.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If ticket_ids is empty or contains invalid IDs.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.archive_tickets(ticket_ids))

    # =========================================================================
    # Attachment Operations
    # =========================================================================

    def get_attachment(
        self, attachment_id: Union[str, UUID], filename: Optional[str] = None
    ) -> Optional[bytes]:
        """Get attachment content.

        Args:
            attachment_id: Attachment UUID or string ID.
            filename: Optional filename hint.

        Returns:
            Attachment content as bytes, or None if not found.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If attachment_id format is invalid.
            NotFoundError: If attachment not found.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_attachment(attachment_id, filename))

    def upload_attachment(
        self, file_content: bytes, filename: str
    ) -> Optional[UUID]:
        """Upload an attachment.

        Args:
            file_content: File content as bytes.
            filename: Name for the uploaded file.

        Returns:
            UUID of the uploaded attachment, or None if failed.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If file_content is empty or filename is invalid.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.upload_attachment(file_content, filename))
