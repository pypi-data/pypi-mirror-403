
"""
Attachment model for report attachments.

Shared base for both UUT and UUR reports. Memory-only operations -
for file I/O use pywats_client.io.AttachmentIO.
"""

from __future__ import annotations

import base64
import mimetypes
from typing import Optional, ClassVar
from uuid import UUID, uuid4

from pydantic import Field
from .wats_base import WATSBase


class Attachment(WATSBase):
    """
    A document or file in binary format.
    
    Used by both UUT (step-level) and UUR (report/failure-level) reports.
    
    Note:
        This class is memory-only. For file operations, use:
        - pywats_client.io.AttachmentIO.from_file() to load from file
        - pywats_client.io.AttachmentIO.save() to save to file
    
    Example:
        >>> # From bytes (memory-only)
        >>> attachment = Attachment.from_bytes("data.bin", b"\\x00\\x01\\x02")
        >>> 
        >>> # Manual construction
        >>> attachment = Attachment(name="test.txt", data="SGVsbG8=", content_type="text/plain")
        >>>
        >>> # With pywats_client for file operations
        >>> from pywats_client.io import AttachmentIO
        >>> attachment = AttachmentIO.from_file("report.pdf")
    """
    
    # Default max size (10 MB)
    DEFAULT_MAX_SIZE: ClassVar[int] = 10 * 1024 * 1024
    
    name: str = Field(..., min_length=1)
    """The name of the attached document or file."""
    
    content_type: Optional[str] = Field(
        default=None, 
        examples=[['image/png', 'text/plain']], 
        min_length=1, 
        validation_alias="contentType", 
        serialization_alias="contentType"
    )
    """The document or file MIME type."""
    
    data: Optional[str] = Field(default=None, min_length=1)
    """The data of the document or file in base64 format."""
    
    # Optional: failure index for UUR attachments (None = report level)
    failure_idx: Optional[int] = Field(
        default=None, 
        validation_alias="failIdx", 
        serialization_alias="failIdx",
        exclude=True  # Excluded from default serialization, added separately for UUR
    )
    """Index of failure this attachment belongs to (None for report-level, UUR only)."""
    
    # Internal tracking
    binary_data_guid: Optional[UUID] = Field(default_factory=uuid4, exclude=True)
    """Unique identifier for this binary data."""
    
    @classmethod
    def from_bytes(
        cls,
        name: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        failure_idx: Optional[int] = None,
        max_size: Optional[int] = None
    ) -> "Attachment":
        """
        Create an attachment from bytes.
        
        Args:
            name: Display name for the attachment
            content: Binary content
            content_type: MIME type
            failure_idx: Failure index (UUR only)
            max_size: Maximum size in bytes (default: 10 MB)
            
        Returns:
            Attachment instance
            
        Raises:
            ValueError: If content exceeds max size
        """
        max_allowed = max_size or cls.DEFAULT_MAX_SIZE
        if len(content) > max_allowed:
            raise ValueError(
                f"Content size ({len(content)} bytes) exceeds maximum ({max_allowed} bytes)"
            )
        
        data_b64 = base64.b64encode(content).decode('utf-8')
        
        return cls(
            name=name,
            data=data_b64,
            content_type=content_type,
            failure_idx=failure_idx
        )
    
    def get_bytes(self) -> bytes:
        """
        Get the attachment data as bytes.
        
        Returns:
            Decoded binary data
        """
        if not self.data:
            return b""
        return base64.b64decode(self.data)
    
    @property
    def size(self) -> int:
        """Size of the attachment in bytes (decoded)."""
        if not self.data:
            return 0
        # Base64 is ~4/3 of original size
        return len(base64.b64decode(self.data))
    
    @property
    def is_failure_attachment(self) -> bool:
        """True if attached to a specific failure (UUR), False if report/step level."""
        return self.failure_idx is not None
    
    # Convenience alias
    @property
    def mime_type(self) -> str:
        """MIME type of the attachment (alias for content_type)."""
        return self.content_type or "application/octet-stream"
    
    @mime_type.setter
    def mime_type(self, value: str) -> None:
        self.content_type = value
    
    @property
    def file_name(self) -> str:
        """Filename (alias for name)."""
        return self.name
    
