"""
pywats_cfx - IPC-CFX Integration for pyWATS

This package provides the CFX-specific transport adapter for the pyWATS
event system. It handles AMQP communication with CFX message brokers
and translates CFX messages to normalized pyWATS events.

IPC-CFX (IPC-2591) is an industry standard for factory floor connectivity.
This package implements:
- AMQP 1.0 client for CFX message brokers
- CFX message models (UnitsTested, MaterialsInstalled, etc.)
- Adapters to convert CFX messages to pyWATS domain events

Example:
    >>> from pywats_cfx import CFXTransport, CFXConfig
    >>> from pywats_cfx.config import AMQPConfig, EndpointConfig
    >>> from pywats_events import AsyncEventBus
    >>>
    >>> config = CFXConfig(
    ...     amqp=AMQPConfig(host="cfx-broker.factory.local"),
    ...     endpoint=EndpointConfig(cfx_handle="//MyCompany/WATS/Station1"),
    ... )
    >>> transport = CFXTransport(config)
    >>> await transport.connect()
"""

# Transport
from pywats_cfx.transport import CFXTransport

# Configuration
from pywats_cfx.config import (
    CFXConfig,
    AMQPConfig,
    EndpointConfig,
    ExchangeConfig,
    RetryConfig,
    DEFAULT_CFX_CONFIG,
)

# Message models
from pywats_cfx.models import (
    CFXMessage,
    UnitsTested,
    UnitsInspected,
    MaterialsInstalled,
    MaterialsLoaded,
    MaterialsUnloaded,
    WorkStarted,
    WorkCompleted,
    UnitsArrived,
    UnitsDeparted,
    UnitsDisqualified,
    FaultOccurred,
    FaultCleared,
    StationStateChanged,
    TestResult,
    InspectionResult,
    FaultSeverity,
    ResourceState,
    parse_cfx_message,
    serialize_cfx_message,
)

# Adapters
from pywats_cfx.adapters import (
    CFXTestResultAdapter,
    CFXMaterialAdapter,
    CFXProductionAdapter,
    CFXResourceAdapter,
    adapt_test_result,
    adapt_materials_installed,
    adapt_production_message,
    adapt_resource_message,
)

__version__ = "0.2.0b1"

__all__ = [
    # Transport
    "CFXTransport",
    # Configuration
    "CFXConfig",
    "AMQPConfig",
    "EndpointConfig",
    "ExchangeConfig",
    "RetryConfig",
    "DEFAULT_CFX_CONFIG",
    # Messages
    "CFXMessage",
    "UnitsTested",
    "UnitsInspected",
    "MaterialsInstalled",
    "MaterialsLoaded",
    "MaterialsUnloaded",
    "WorkStarted",
    "WorkCompleted",
    "UnitsArrived",
    "UnitsDeparted",
    "UnitsDisqualified",
    "FaultOccurred",
    "FaultCleared",
    "StationStateChanged",
    # Enums
    "TestResult",
    "InspectionResult",
    "FaultSeverity",
    "ResourceState",
    # Helpers
    "parse_cfx_message",
    "serialize_cfx_message",
    # Adapters
    "CFXTestResultAdapter",
    "CFXMaterialAdapter",
    "CFXProductionAdapter",
    "CFXResourceAdapter",
    "adapt_test_result",
    "adapt_materials_installed",
    "adapt_production_message",
    "adapt_resource_message",
]
