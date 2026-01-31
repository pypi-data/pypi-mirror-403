"""
Error Handling Mixin for GUI Pages.

Provides centralized error handling for GUI pages, showing appropriate
dialogs based on the type of error encountered.

Usage:
    class MyPage(BasePage, ErrorHandlingMixin):
        def _on_some_action(self):
            try:
                result = api.do_something()
            except Exception as e:
                self.handle_error(e, "doing something")
"""

import logging
from typing import Optional, Callable
from PySide6.QtWidgets import QMessageBox, QWidget

logger = logging.getLogger(__name__)


# Import exceptions conditionally to avoid circular imports
def _get_exception_types():
    """Lazily import exception types."""
    try:
        from pywats.core.exceptions import (
            AuthenticationError,
            AuthorizationError,
            ValidationError,
            NotFoundError,
            ServerError,
            ConnectionError,
            TimeoutError,
            PyWATSError,
        )
        return {
            'AuthenticationError': AuthenticationError,
            'AuthorizationError': AuthorizationError,
            'ValidationError': ValidationError,
            'NotFoundError': NotFoundError,
            'ServerError': ServerError,
            'ConnectionError': ConnectionError,
            'TimeoutError': TimeoutError,
            'PyWATSError': PyWATSError,
        }
    except ImportError:
        return {}


class ErrorHandlingMixin:
    """
    Mixin providing centralized error handling for GUI pages.
    
    Provides consistent error dialogs based on exception type:
    - Authentication errors: Suggest re-login
    - Validation errors: Show input issue
    - Server errors: Show server issue
    - Connection errors: Show connectivity issue
    - Other errors: Show generic error with logging
    """
    
    def handle_error(
        self,
        error: Exception,
        context: str = "",
        on_auth_error: Optional[Callable[[], None]] = None
    ) -> None:
        """
        Handle an error with appropriate user feedback.
        
        Args:
            error: The exception that occurred
            context: Description of what was being attempted (e.g., "loading assets")
            on_auth_error: Optional callback when authentication error occurs
        """
        # Get self as widget (mixin assumes we're mixed into a QWidget)
        widget: QWidget = self  # type: ignore
        
        # Get exception types
        exc_types = _get_exception_types()
        
        context_str = f" while {context}" if context else ""
        
        # Handle specific exception types
        if exc_types.get('AuthenticationError') and isinstance(error, exc_types['AuthenticationError']):
            QMessageBox.warning(
                widget,
                "Authentication Error",
                f"Your session has expired or credentials are invalid.\n\n"
                f"Please reconnect to the server."
            )
            if on_auth_error:
                on_auth_error()
            return
        
        if exc_types.get('AuthorizationError') and isinstance(error, exc_types['AuthorizationError']):
            QMessageBox.warning(
                widget,
                "Access Denied",
                f"You don't have permission to perform this action{context_str}.\n\n"
                f"Contact your administrator if you need access."
            )
            return
        
        if exc_types.get('ValidationError') and isinstance(error, exc_types['ValidationError']):
            QMessageBox.warning(
                widget,
                "Invalid Input",
                f"The server rejected the request{context_str}:\n\n{str(error)}"
            )
            return
        
        if exc_types.get('NotFoundError') and isinstance(error, exc_types['NotFoundError']):
            QMessageBox.information(
                widget,
                "Not Found",
                f"The requested item was not found{context_str}.\n\n"
                f"It may have been deleted or never existed."
            )
            return
        
        if exc_types.get('ServerError') and isinstance(error, exc_types['ServerError']):
            QMessageBox.critical(
                widget,
                "Server Error",
                f"The WATS server encountered an error{context_str}.\n\n"
                f"Please try again later or contact support if the issue persists.\n\n"
                f"Error: {str(error)}"
            )
            return
        
        if exc_types.get('ConnectionError') and isinstance(error, exc_types['ConnectionError']):
            QMessageBox.warning(
                widget,
                "Connection Error",
                f"Unable to connect to the WATS server{context_str}.\n\n"
                f"Please check your network connection and try again."
            )
            return
        
        if exc_types.get('TimeoutError') and isinstance(error, exc_types['TimeoutError']):
            QMessageBox.warning(
                widget,
                "Request Timeout",
                f"The request timed out{context_str}.\n\n"
                f"The server may be busy. Please try again."
            )
            return
        
        # Generic PyWATS error
        if exc_types.get('PyWATSError') and isinstance(error, exc_types['PyWATSError']):
            QMessageBox.critical(
                widget,
                "API Error",
                f"An error occurred{context_str}:\n\n{str(error)}"
            )
            return
        
        # Unknown error - log it and show generic message
        logger.exception(f"Unexpected error{context_str}: {error}")
        QMessageBox.critical(
            widget,
            "Unexpected Error",
            f"An unexpected error occurred{context_str}:\n\n{str(error)}\n\n"
            f"Please check the logs for more details."
        )
    
    def show_success(self, message: str, title: str = "Success") -> None:
        """Show a success message dialog."""
        widget: QWidget = self  # type: ignore
        QMessageBox.information(widget, title, message)
    
    def show_warning(self, message: str, title: str = "Warning") -> None:
        """Show a warning message dialog."""
        widget: QWidget = self  # type: ignore
        QMessageBox.warning(widget, title, message)
    
    def show_error(self, message: str, title: str = "Error") -> None:
        """Show an error message dialog."""
        widget: QWidget = self  # type: ignore
        QMessageBox.critical(widget, title, message)
    
    def confirm_action(self, message: str, title: str = "Confirm") -> bool:
        """
        Show a confirmation dialog.
        
        Returns:
            True if user clicked Yes, False otherwise
        """
        widget: QWidget = self  # type: ignore
        reply = QMessageBox.question(
            widget,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
