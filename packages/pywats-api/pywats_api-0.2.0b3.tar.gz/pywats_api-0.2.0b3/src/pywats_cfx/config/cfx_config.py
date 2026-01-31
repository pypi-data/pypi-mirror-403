"""
CFX Configuration.

Configuration models for IPC-CFX transport and endpoint settings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AMQPConfig:
    """AMQP broker connection configuration."""
    
    host: str = "localhost"
    port: int = 5672
    virtual_host: str = "/"
    username: str = "guest"
    password: str = "guest"
    
    # TLS/SSL settings
    use_ssl: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    ssl_ca_path: Optional[str] = None
    ssl_verify: bool = True
    
    # Connection settings
    heartbeat: int = 60
    connection_timeout: float = 30.0
    channel_max: int = 2047
    frame_max: int = 131072
    
    @property
    def broker_url(self) -> str:
        """Build AMQP broker URL."""
        scheme = "amqps" if self.use_ssl else "amqp"
        return f"{scheme}://{self.username}:{self.password}@{self.host}:{self.port}/{self.virtual_host}"


@dataclass
class EndpointConfig:
    """CFX endpoint identity configuration."""
    
    # Required endpoint identity
    cfx_handle: str = ""  # e.g., "//Virinco/WATS/TestStation001"
    
    # Optional endpoint metadata
    vendor: str = "Virinco"
    model_number: str = "pyWATS"
    serial_number: str = ""
    software_version: str = ""
    
    # Lane/stage configuration
    number_of_lanes: int = 1
    number_of_stages: int = 1
    
    def validate(self) -> None:
        """Validate endpoint configuration."""
        if not self.cfx_handle:
            raise ValueError("cfx_handle is required")
        if not self.cfx_handle.startswith("//"):
            raise ValueError("cfx_handle must start with '//'")


@dataclass
class ExchangeConfig:
    """AMQP exchange configuration for CFX topics."""
    
    # Exchange settings
    exchange_name: str = "cfx.exchange"
    exchange_type: str = "topic"
    durable: bool = True
    auto_delete: bool = False
    
    # Queue settings
    queue_name_prefix: str = "pywats"
    queue_durable: bool = True
    queue_auto_delete: bool = False
    queue_exclusive: bool = False
    
    # Message settings
    message_ttl: Optional[int] = None  # milliseconds
    prefetch_count: int = 100
    
    # Topic routing
    binding_keys: list[str] = field(default_factory=lambda: [
        "CFX.Production.Testing.#",
        "CFX.Production.Assembly.#",
        "CFX.ResourcePerformance.#",
    ])


@dataclass 
class RetryConfig:
    """Retry configuration for CFX transport."""
    
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class CFXConfig:
    """
    Complete CFX configuration.
    
    Combines AMQP, endpoint, exchange, and retry settings.
    
    Example usage:
        config = CFXConfig(
            amqp=AMQPConfig(host="broker.example.com"),
            endpoint=EndpointConfig(cfx_handle="//MyCompany/WATS/TestStation1"),
        )
    
    Or from YAML:
        cfx:
          amqp:
            host: broker.example.com
            port: 5672
            use_ssl: true
          endpoint:
            cfx_handle: "//MyCompany/WATS/TestStation1"
            vendor: "MyCompany"
          exchange:
            binding_keys:
              - "CFX.Production.Testing.#"
          retry:
            max_retries: 5
    """
    
    amqp: AMQPConfig = field(default_factory=AMQPConfig)
    endpoint: EndpointConfig = field(default_factory=EndpointConfig)
    exchange: ExchangeConfig = field(default_factory=ExchangeConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    
    # Feature flags
    auto_reconnect: bool = True
    publish_endpoint_connected: bool = True
    publish_endpoint_disconnected: bool = True
    
    # Logging
    log_messages: bool = False
    log_level: str = "INFO"
    
    def validate(self) -> None:
        """Validate complete configuration."""
        self.endpoint.validate()
        
        if self.amqp.port < 1 or self.amqp.port > 65535:
            raise ValueError(f"Invalid AMQP port: {self.amqp.port}")
        
        if self.retry.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        
        if self.retry.initial_delay <= 0:
            raise ValueError("initial_delay must be > 0")
    
    @classmethod
    def from_dict(cls, data: dict) -> "CFXConfig":
        """
        Create configuration from dictionary.
        
        Args:
            data: Configuration dictionary (e.g., from YAML).
            
        Returns:
            CFXConfig instance.
        """
        return cls(
            amqp=AMQPConfig(**data.get("amqp", {})),
            endpoint=EndpointConfig(**data.get("endpoint", {})),
            exchange=ExchangeConfig(**data.get("exchange", {})),
            retry=RetryConfig(**data.get("retry", {})),
            auto_reconnect=data.get("auto_reconnect", True),
            publish_endpoint_connected=data.get("publish_endpoint_connected", True),
            publish_endpoint_disconnected=data.get("publish_endpoint_disconnected", True),
            log_messages=data.get("log_messages", False),
            log_level=data.get("log_level", "INFO"),
        )
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        import dataclasses
        
        def asdict_shallow(obj):
            if dataclasses.is_dataclass(obj):
                return {
                    f.name: asdict_shallow(getattr(obj, f.name))
                    for f in dataclasses.fields(obj)
                }
            elif isinstance(obj, list):
                return [asdict_shallow(item) for item in obj]
            else:
                return obj
        
        return asdict_shallow(self)


# Default configuration instance
DEFAULT_CFX_CONFIG = CFXConfig()
