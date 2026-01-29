"""Async RootCause repository - data access layer.

All async API interactions for the RootCause ticketing system.
All endpoints are defined in pywats.core.routes.Routes.
"""
from typing import Optional, List, Union, Dict, Any, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from ...core.async_client import AsyncHttpClient
    from ...core.exceptions import ErrorHandler

from ...core.routes import Routes
from .models import Ticket, TicketAttachment
from .enums import TicketStatus, TicketView


class AsyncRootCauseRepository:
    """
    Async RootCause (Ticketing) data access layer.

    Handles all async WATS API interactions for the ticketing system.
    """

    def __init__(
        self, 
        http_client: "AsyncHttpClient",
        error_handler: Optional["ErrorHandler"] = None
    ):
        """
        Initialize with async HTTP client.

        Args:
            http_client: AsyncHttpClient for making async HTTP requests
            error_handler: ErrorHandler for response handling
        """
        from ...core.exceptions import ErrorHandler, ErrorMode
        self._http_client = http_client
        self._error_handler = error_handler or ErrorHandler(ErrorMode.STRICT)

    # =========================================================================
    # Ticket Operations
    # =========================================================================

    async def get_ticket(self, ticket_id: Union[str, UUID]) -> Optional[Ticket]:
        """
        Get a root cause ticket by ID.

        GET /api/RootCause/Ticket

        Args:
            ticket_id: The ticket ID (GUID)

        Returns:
            Ticket object or None if not found
        """
        response = await self._http_client.get(
            Routes.RootCause.TICKET, params={"ticketId": str(ticket_id)}
        )
        data = self._error_handler.handle_response(
            response, operation="get_ticket", allow_empty=True
        )
        if data:
            return Ticket.model_validate(data)
        return None

    async def get_tickets(
        self,
        status: TicketStatus,
        view: TicketView,
        search_string: Optional[str] = None,
    ) -> List[Ticket]:
        """
        Get root cause tickets with a given status.

        GET /api/RootCause/Tickets

        Args:
            status: Ticket status flags (can be combined with |)
            view: View filter (ASSIGNED, FOLLOWING, ALL)
            search_string: Optional search for subject, tags, or tag value

        Returns:
            List of Ticket objects matching the criteria
        """
        params: Dict[str, Any] = {"status": int(status), "view": int(view)}
        if search_string:
            params["searchString"] = search_string

        response = await self._http_client.get(Routes.RootCause.TICKETS, params=params)
        data = self._error_handler.handle_response(
            response, operation="get_tickets", allow_empty=True
        )
        if data:
            return [Ticket.model_validate(item) for item in data]
        return []

    async def create_ticket(self, ticket: Ticket) -> Optional[Ticket]:
        """
        Create a new root cause ticket.

        POST /api/RootCause/Ticket

        Args:
            ticket: Ticket object with the new ticket data

        Returns:
            Created Ticket object with assigned ID and ticket number
        """
        response = await self._http_client.post(
            Routes.RootCause.TICKET,
            data=ticket.model_dump(mode="json", by_alias=True, exclude_none=True),
        )
        data = self._error_handler.handle_response(
            response, operation="create_ticket", allow_empty=False
        )
        if data:
            return Ticket.model_validate(data)
        return None

    async def update_ticket(self, ticket: Ticket) -> Optional[Ticket]:
        """
        Update a root cause ticket.

        PUT /api/RootCause/Ticket

        Args:
            ticket: Ticket object with updated data

        Returns:
            Updated Ticket object
        """
        response = await self._http_client.put(
            Routes.RootCause.TICKET,
            data=ticket.model_dump(mode="json", by_alias=True, exclude_none=True),
        )
        data = self._error_handler.handle_response(
            response, operation="update_ticket", allow_empty=False
        )
        if data:
            return Ticket.model_validate(data)
        return None

    async def archive_tickets(
        self, ticket_ids: List[Union[str, UUID]]
    ) -> Optional[Ticket]:
        """
        Archive tickets.

        POST /api/RootCause/ArchiveTickets

        Args:
            ticket_ids: List of ticket IDs to archive

        Returns:
            Ticket object or None
        """
        ids = [str(tid) for tid in ticket_ids]
        response = await self._http_client.post(Routes.RootCause.ARCHIVE_TICKETS, data=ids)
        data = self._error_handler.handle_response(
            response, operation="archive_tickets", allow_empty=True
        )
        if data:
            return Ticket.model_validate(data)
        return None

    # =========================================================================
    # Attachment Operations
    # =========================================================================

    async def get_attachment(
        self,
        attachment_id: Union[str, UUID],
        filename: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Get root cause attachment content.

        GET /api/RootCause/Attachment

        Args:
            attachment_id: The attachment ID (GUID)
            filename: Optional filename for download

        Returns:
            Attachment content as bytes, or None if not found
        """
        params: Dict[str, str] = {"attachmentId": str(attachment_id)}
        if filename:
            params["fileName"] = filename

        response = await self._http_client.get(Routes.RootCause.ATTACHMENT, params=params)
        if not response.is_success:
            self._error_handler.handle_response(
                response, operation="get_attachment"
            )
            return None
        return response.raw

    async def upload_attachment(
        self, file_content: bytes, filename: str
    ) -> Optional[UUID]:
        """
        Upload root cause attachment and return attachment ID.

        POST /api/RootCause/Attachment

        Args:
            file_content: The file content as bytes
            filename: The filename for the attachment

        Returns:
            UUID of the created attachment, or None if failed
        """
        files = {"file": (filename, file_content)}
        response = await self._http_client.post(Routes.RootCause.ATTACHMENT, files=files)
        data = self._error_handler.handle_response(
            response, operation="upload_attachment", allow_empty=False
        )
        if data:
            return UUID(data) if isinstance(data, str) else None
        return None
