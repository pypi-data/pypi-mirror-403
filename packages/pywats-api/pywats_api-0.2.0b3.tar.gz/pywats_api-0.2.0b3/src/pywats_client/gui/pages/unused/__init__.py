"""
Unused Pages Module

These pages are scaffolded for potential future use but are not currently
integrated into the main application. They provide UI for WATS API domains
that may be enabled in future versions.

Pages in this folder:
- AssetPage: Asset management (equipment, instruments, fixtures)
- ProductPage: Product management (part numbers, revisions, BOMs)
- ProductionPage: Production units (serial numbers, assemblies)
- RootCausePage: Issue tracking and resolution (tickets)
- GeneralPage: General settings (superseded by SetupPage)

To enable a page:
1. Move it back to the parent pages/ folder
2. Import and export it in pages/__init__.py
3. Add it to _build_nav_items() in main_window.py
4. Add it to _pages dict in _create_content_area() in main_window.py
"""

from .asset import AssetPage
from .product import ProductPage
from .production import ProductionPage
from .rootcause import RootCausePage
from .general import GeneralPage

__all__ = [
    "AssetPage",
    "ProductPage",
    "ProductionPage",
    "RootCausePage",
    "GeneralPage",
]
