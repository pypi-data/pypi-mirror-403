"""Async RootCause service - business logic layer.

All async business operations for the RootCause ticketing system.

IMPORTANT - Server Behavior Note:
------------------------------------
The WATS server does NOT return the `assignee` field in ticket API responses.
See the sync service module docstring for full details and workarounds.
"""
from typing import Optional, List, Union
from uuid import UUID
import logging

from .async_repository import AsyncRootCauseRepository
from .models import Ticket, TicketUpdate
from .enums import TicketStatus, TicketPriority, TicketView

logger = logging.getLogger(__name__)


class AsyncRootCauseService:
    """
    Async RootCause (Ticketing) business logic layer.

    Provides high-level async operations for issue tracking and resolution.
    """

    def __init__(self, repository: AsyncRootCauseRepository) -> None:
        """
        Initialize with AsyncRootCauseRepository.

        Args:
            repository: AsyncRootCauseRepository instance for data access
        """
        self._repository = repository

    # =========================================================================
    # Ticket Operations
    # =========================================================================

    async def get_ticket(self, ticket_id: Union[str, UUID]) -> Optional[Ticket]:
        """
        Get a ticket by ID.
        
        WARNING: The returned ticket will have `assignee=None` even if the
        ticket is assigned. This is a server limitation.

        Args:
            ticket_id: The ticket ID (GUID)

        Returns:
            Ticket object or None if not found
        """
        if not ticket_id:
            raise ValueError("ticket_id is required")
        return await self._repository.get_ticket(ticket_id)

    async def get_tickets(
        self,
        status: TicketStatus = TicketStatus.OPEN,
        view: TicketView = TicketView.ASSIGNED,
        search_string: Optional[str] = None,
    ) -> List[Ticket]:
        """
        Get tickets with given status.

        Args:
            status: Ticket status flags (can be combined with |)
            view: View filter (ASSIGNED, FOLLOWING, ALL)
            search_string: Optional search for subject, tags, or tag value

        Returns:
            List of Ticket objects
        """
        return await self._repository.get_tickets(status, view, search_string)

    async def get_open_tickets(
        self, view: TicketView = TicketView.ASSIGNED
    ) -> List[Ticket]:
        """
        Get all open tickets.

        Args:
            view: View filter

        Returns:
            List of open Ticket objects
        """
        return await self._repository.get_tickets(TicketStatus.OPEN, view)

    async def get_active_tickets(
        self, view: TicketView = TicketView.ASSIGNED
    ) -> List[Ticket]:
        """
        Get all active tickets (Open or In Progress).

        Args:
            view: View filter

        Returns:
            List of active Ticket objects
        """
        status = TicketStatus.OPEN | TicketStatus.IN_PROGRESS
        return await self._repository.get_tickets(status, view)

    async def create_ticket(
        self,
        subject: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
        assignee: Optional[str] = None,
        team: Optional[str] = None,
        report_uuid: Optional[Union[str, UUID]] = None,
        initial_comment: Optional[str] = None,
    ) -> Optional[Ticket]:
        """
        Create a new ticket.

        Args:
            subject: Ticket subject/title
            priority: Priority level (default: MEDIUM)
            assignee: Username to assign ticket to
            team: Team to assign ticket to
            report_uuid: UUID of associated report
            initial_comment: Initial comment/description

        Returns:
            Created Ticket object or None
        """
        if not subject or not subject.strip():
            raise ValueError("subject is required")
        ticket = Ticket(
            subject=subject,
            priority=priority,
            assignee=assignee,
            team=team,
        )
        if report_uuid:
            ticket.report_uuid = (
                UUID(report_uuid)
                if isinstance(report_uuid, str)
                else report_uuid
            )
        if initial_comment:
            ticket.update = TicketUpdate(content=initial_comment)

        result = await self._repository.create_ticket(ticket)
        if result:
            # Preserve assignee in result since server doesn't return it
            if assignee and not result.assignee:
                result.assignee = assignee
            logger.info(f"TICKET_CREATED: {result.ticket_id} (subject={subject}, priority={priority.name})")
        return result

    async def update_ticket(self, ticket: Ticket) -> Optional[Ticket]:
        """
        Update an existing ticket.
        
        WARNING: If you fetch a ticket via `get_ticket()` and then update it,
        the assignee field will be None. Use `change_status()` or `add_comment()`
        with the `assignee` parameter instead.

        Args:
            ticket: Ticket object with updated data

        Returns:
            Updated Ticket object or None
        """
        result = await self._repository.update_ticket(ticket)
        if result:
            logger.info(f"TICKET_UPDATED: {result.ticket_id}")
        return result

    async def add_comment(
        self, ticket_id: Union[str, UUID], comment: str,
        assignee: Optional[str] = None
    ) -> Optional[Ticket]:
        """
        Add a comment to a ticket.

        Args:
            ticket_id: Ticket ID
            comment: Comment text
            assignee: Current assignee username (important - see docstring)

        Returns:
            Updated Ticket object or None
        """
        if not ticket_id:
            raise ValueError("ticket_id is required")
        if not comment or not comment.strip():
            raise ValueError("comment is required")
        
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            return None
        
        if assignee:
            ticket.assignee = assignee
        
        ticket.update = TicketUpdate(content=comment)
        result = await self._repository.update_ticket(ticket)
        if result:
            if assignee and not result.assignee:
                result.assignee = assignee
            logger.info(f"TICKET_COMMENT_ADDED: {ticket_id}")
        return result

    async def change_status(
        self, ticket_id: Union[str, UUID], status: TicketStatus,
        assignee: Optional[str] = None
    ) -> Optional[Ticket]:
        """
        Change the status of a ticket.

        Args:
            ticket_id: Ticket ID
            status: New status
            assignee: Current assignee username (important - see docstring)

        Returns:
            Updated Ticket object or None
        """
        if not ticket_id:
            raise ValueError("ticket_id is required")
        
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            return None
        
        if assignee:
            ticket.assignee = assignee
        
        ticket.status = status
        result = await self._repository.update_ticket(ticket)
        if result:
            if assignee and not result.assignee:
                result.assignee = assignee
            logger.info(f"TICKET_STATUS_CHANGED: {ticket_id} (status={status.name})")
        return result

    async def assign_ticket(
        self, ticket_id: Union[str, UUID], assignee: str
    ) -> Optional[Ticket]:
        """
        Assign a ticket to a user.

        Args:
            ticket_id: Ticket ID
            assignee: Username to assign to

        Returns:
            Updated Ticket object or None
        """
        if not ticket_id:
            raise ValueError("ticket_id is required")
        if not assignee or not assignee.strip():
            raise ValueError("assignee is required")
        
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            return None
        
        ticket.assignee = assignee
        result = await self._repository.update_ticket(ticket)
        if result:
            if not result.assignee:
                result.assignee = assignee
            logger.info(f"TICKET_ASSIGNED: {ticket_id} (assignee={assignee})")
        return result

    async def archive_tickets(
        self, ticket_ids: List[Union[str, UUID]]
    ) -> Optional[Ticket]:
        """
        Archive solved tickets.

        Args:
            ticket_ids: List of ticket IDs to archive

        Returns:
            Ticket object or None
        """
        result = await self._repository.archive_tickets(ticket_ids)
        if result:
            logger.info(f"TICKETS_ARCHIVED: count={len(ticket_ids)}")
        return result

    # =========================================================================
    # Attachment Operations
    # =========================================================================

    async def get_attachment(
        self, attachment_id: Union[str, UUID], filename: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Get attachment content.

        Args:
            attachment_id: The attachment ID (GUID)
            filename: Optional filename for download

        Returns:
            Attachment content as bytes, or None
        """
        if not attachment_id:
            raise ValueError("attachment_id is required")
        return await self._repository.get_attachment(attachment_id, filename)

    async def upload_attachment(
        self, file_content: bytes, filename: str
    ) -> Optional[UUID]:
        """
        Upload an attachment.

        Args:
            file_content: The file content as bytes
            filename: The filename for the attachment

        Returns:
            UUID of the created attachment, or None
        """
        if not file_content:
            raise ValueError("file_content is required")
        if not filename or not filename.strip():
            raise ValueError("filename is required")
        return await self._repository.upload_attachment(file_content, filename)
