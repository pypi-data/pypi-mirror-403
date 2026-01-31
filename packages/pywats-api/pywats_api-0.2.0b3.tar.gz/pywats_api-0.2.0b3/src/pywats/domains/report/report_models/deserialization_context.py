from enum import Enum


class ContextType(Enum):
    """Context type for deserialization (server-defined values)."""
    Defaults = "Defaults"
    LegacyData = "LegacyData"  # Server term for older data format

class DeserializationContext:
    def __init__(self, type: ContextType, defaults: dict) -> None:
        self.type = type
        self.defaults = defaults
