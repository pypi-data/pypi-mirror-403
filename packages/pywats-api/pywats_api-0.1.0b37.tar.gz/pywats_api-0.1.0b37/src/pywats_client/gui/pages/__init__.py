"""
GUI Pages module

Contains all page widgets for the main window.
"""

from .base import BasePage
from .dashboard import DashboardPage
from .setup import SetupPage
from .connection import ConnectionPage
from .api_settings import APISettingsPage
from .proxy_settings import ProxySettingsPage
from .converters import ConvertersPageV2 as ConvertersPage  # AI-enabled unified converters page
from .location import LocationPage
from .sn_handler import SNHandlerPage
from .software import SoftwarePage
from .about import AboutPage
from .log import LogPage

__all__ = [
    "BasePage",
    "DashboardPage",
    "SetupPage",
    "ConnectionPage",
    "APISettingsPage",
    "ProxySettingsPage",
    "ConvertersPage",
    "LocationPage",
    "SNHandlerPage",
    "SoftwarePage",
    "AboutPage",
    "LogPage",
]

