"""
GUI Pages module

Contains all page widgets for the main window.

Active pages are used in the main navigation.
Unused pages are stored in the 'unused' subfolder for potential future use.
"""

from .base import BasePage
from .dashboard import DashboardPage
from .setup import SetupPage
from .connection import ConnectionPage
from .api_settings import APISettingsPage
from .converters import ConvertersPageV2 as ConvertersPage  # AI-enabled unified converters page
from .sn_handler import SNHandlerPage
from .software import SoftwarePage
from .log import LogPage

# Pages that exist but are not currently used in the main window
# Kept for potential future use or reference
from .proxy_settings import ProxySettingsPage  # Settings moved to SettingsDialog
from .location import LocationPage  # Settings moved to SettingsDialog
from .about import AboutPage  # Not currently integrated

__all__ = [
    # Active pages (used in main navigation)
    "BasePage",
    "DashboardPage",
    "SetupPage",
    "ConnectionPage",
    "APISettingsPage",
    "ConvertersPage",
    "SNHandlerPage",
    "SoftwarePage",
    "LogPage",
    # Available but not actively used
    "ProxySettingsPage",
    "LocationPage",
    "AboutPage",
]

