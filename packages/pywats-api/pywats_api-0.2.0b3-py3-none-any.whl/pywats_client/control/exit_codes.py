"""
Exit Codes for pyWATS Client CLI

These exit codes enable scripted deployment and CI/CD integration.
IT departments can check these codes to determine success/failure
of installation and other operations.

Usage:
    import sys
    from .exit_codes import EXIT_SUCCESS, EXIT_MISSING_REQUIREMENTS
    
    if not check_requirements():
        sys.exit(EXIT_MISSING_REQUIREMENTS)
    
    # ... do work ...
    sys.exit(EXIT_SUCCESS)

Exit Code Ranges:
    0      - Success
    1-9    - General errors
    10-19  - Installation errors
    20-29  - Configuration errors  
    30-39  - Service operation errors
    40-49  - Network/connectivity errors
"""

# Success
EXIT_SUCCESS = 0

# General errors (1-9)
EXIT_ERROR = 1                      # Generic error
EXIT_MISSING_REQUIREMENTS = 2       # Python version, pywin32, privileges, etc.
EXIT_INTERRUPTED = 3                # Ctrl+C or signal interrupt

# Installation errors (10-19)
EXIT_ALREADY_INSTALLED = 10         # Service already exists
EXIT_NOT_INSTALLED = 11             # Service doesn't exist (for uninstall/status)
EXIT_INSTALL_FAILED = 12            # Installation failed
EXIT_UNINSTALL_FAILED = 13          # Uninstall failed
EXIT_PERMISSION_DENIED = 14         # Insufficient privileges (need admin/root)

# Configuration errors (20-29)
EXIT_CONFIG_ERROR = 20              # Configuration file invalid or missing
EXIT_CONFIG_NOT_FOUND = 21          # Config file specified but doesn't exist
EXIT_CONFIG_INVALID = 22            # Config file exists but has invalid content

# Service operation errors (30-39)
EXIT_SERVICE_START_FAILED = 30      # Service failed to start
EXIT_SERVICE_STOP_FAILED = 31       # Service failed to stop
EXIT_SERVICE_NOT_RUNNING = 32       # Service not running (for stop/status)
EXIT_SERVICE_TIMEOUT = 33           # Operation timed out

# Network/connectivity errors (40-49)
EXIT_NETWORK_ERROR = 40             # General network error
EXIT_SERVER_UNREACHABLE = 41        # WATS server not reachable
EXIT_AUTH_FAILED = 42               # API token invalid


def get_exit_code_description(code: int) -> str:
    """
    Get human-readable description for an exit code.
    
    Args:
        code: Exit code number
        
    Returns:
        Description string
    """
    descriptions = {
        EXIT_SUCCESS: "Success",
        EXIT_ERROR: "General error",
        EXIT_MISSING_REQUIREMENTS: "Missing requirements (Python version, pywin32, or privileges)",
        EXIT_INTERRUPTED: "Operation interrupted",
        EXIT_ALREADY_INSTALLED: "Service already installed",
        EXIT_NOT_INSTALLED: "Service not installed",
        EXIT_INSTALL_FAILED: "Installation failed",
        EXIT_UNINSTALL_FAILED: "Uninstall failed",
        EXIT_PERMISSION_DENIED: "Permission denied (run as administrator)",
        EXIT_CONFIG_ERROR: "Configuration error",
        EXIT_CONFIG_NOT_FOUND: "Configuration file not found",
        EXIT_CONFIG_INVALID: "Configuration file invalid",
        EXIT_SERVICE_START_FAILED: "Service failed to start",
        EXIT_SERVICE_STOP_FAILED: "Service failed to stop",
        EXIT_SERVICE_NOT_RUNNING: "Service not running",
        EXIT_SERVICE_TIMEOUT: "Operation timed out",
        EXIT_NETWORK_ERROR: "Network error",
        EXIT_SERVER_UNREACHABLE: "WATS server unreachable",
        EXIT_AUTH_FAILED: "Authentication failed",
    }
    return descriptions.get(code, f"Unknown error (code {code})")
