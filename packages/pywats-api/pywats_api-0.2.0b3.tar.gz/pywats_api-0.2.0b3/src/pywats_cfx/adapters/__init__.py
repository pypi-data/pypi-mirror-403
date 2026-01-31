"""
CFX to pyWATS Event Adapters.

Adapters that convert IPC-CFX messages to normalized domain events.
"""

from pywats_cfx.adapters.test_adapter import (
    CFXTestResultAdapter,
    adapt_test_result,
)
from pywats_cfx.adapters.material_adapter import (
    CFXMaterialAdapter,
    adapt_materials_installed,
)
from pywats_cfx.adapters.production_adapter import (
    CFXProductionAdapter,
    adapt_production_message,
)
from pywats_cfx.adapters.resource_adapter import (
    CFXResourceAdapter,
    adapt_resource_message,
)

__all__ = [
    # Adapter classes
    "CFXTestResultAdapter",
    "CFXMaterialAdapter",
    "CFXProductionAdapter",
    "CFXResourceAdapter",
    # Convenience functions
    "adapt_test_result",
    "adapt_materials_installed",
    "adapt_production_message",
    "adapt_resource_message",
]
