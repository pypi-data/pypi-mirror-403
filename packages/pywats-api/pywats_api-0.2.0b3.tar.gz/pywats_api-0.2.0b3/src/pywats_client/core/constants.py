"""
Client Constants

Type-safe constants for the pyWATS client layer.
Eliminates magic strings throughout the codebase.
"""

from enum import Enum


class FolderName(str, Enum):
    """
    Standard folder names used by the client service.
    
    These folders are created in the drop folder location for
    organizing converted files.
    
    Example:
        >>> drop_folder = Path("/data/converters")
        >>> done_folder = drop_folder / FolderName.DONE
        >>> error_folder = drop_folder / FolderName.ERROR
    """
    DONE = "Done"
    ERROR = "Error"
    PENDING = "Pending"
    PROCESSING = "Processing"
    ARCHIVE = "Archive"
    

class LogLevel(str, Enum):
    """
    Log level names for configuration.
    
    Maps to Python logging levels.
    """
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ServiceMode(str, Enum):
    """
    Operating mode for the client service.
    """
    SERVICE = "service"  # Background service mode
    GUI = "gui"          # GUI mode with tray icon
    CLI = "cli"          # Command-line interface mode


class ConverterType(str, Enum):
    """
    Types of converters supported.
    """
    FILE = "file"           # Watches for individual files
    FOLDER = "folder"       # Watches for complete folders
    SCHEDULED = "scheduled"  # Runs on schedule (database, API)


class ErrorHandling(str, Enum):
    """
    Error handling strategies for converters.
    """
    MOVE = "move"      # Move failed files to Error folder
    RETRY = "retry"    # Retry with exponential backoff
    IGNORE = "ignore"  # Log and continue
    RAISE = "raise"    # Raise exception


# Default values
DEFAULT_DROP_FOLDER = "Drop"
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY_SECONDS = 60
DEFAULT_WATCH_INTERVAL_SECONDS = 5
DEFAULT_CACHE_TTL_SECONDS = 300
