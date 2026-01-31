"""
pyWATS API Configuration Models

Pure configuration models for the pyWATS API library (no file I/O).
For file-based config persistence, see pywats_client.core.config_manager.

Configuration Hierarchy:
- API Settings: Core API behavior (timeouts, error modes, caching)
- Domain Settings: Per-domain configuration (product, report, etc.)

Usage:
    # Pure API - use constant defaults (no file I/O)
    settings = APISettings()
    
    # Or explicitly configure
    settings = APISettings(timeout_seconds=60, verify_ssl=False)
    
    # Client layer handles file persistence
    from pywats_client.core import ConfigManager
    manager = ConfigManager()
    settings = manager.load()
"""

import logging
from typing import Optional, Dict, Any, TypeVar, Type
from pydantic import BaseModel, Field, ConfigDict

# Import ErrorMode from exceptions to avoid duplication
from .exceptions import ErrorMode

logger = logging.getLogger(__name__)

# Type variable for domain settings subclasses
T = TypeVar('T', bound='DomainSettings')


class DomainSettings(BaseModel):
    """Settings for a specific API domain.
    
    Attributes:
        enabled: Whether the domain is enabled
        cache_enabled: Whether caching is enabled for this domain
        cache_ttl_seconds: Cache time-to-live in seconds
    """
    model_config = ConfigDict(extra='ignore')
    
    enabled: bool = Field(default=True, description="Whether the domain is enabled")
    cache_enabled: bool = Field(default=True, description="Whether caching is enabled")
    cache_ttl_seconds: int = Field(default=300, description="Cache TTL in seconds (default 5 minutes)")
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        return cls.model_validate(data)


class ProductDomainSettings(DomainSettings):
    """Product domain specific settings.
    
    Attributes:
        auto_create_products: Automatically create products if not found
        default_revision: Default revision for new products
    """
    auto_create_products: bool = Field(default=False, description="Auto-create products if not found")
    default_revision: str = Field(default="A", description="Default revision for new products")


class ReportDomainSettings(DomainSettings):
    """Report domain specific settings.
    
    Attributes:
        auto_submit: Automatically submit reports after creation
        validate_before_submit: Validate reports before submission
        include_attachments: Include attachments in reports
        max_attachment_size_mb: Maximum attachment size in MB
    """
    auto_submit: bool = Field(default=True, description="Auto-submit reports after creation")
    validate_before_submit: bool = Field(default=True, description="Validate before submission")
    include_attachments: bool = Field(default=True, description="Include attachments in reports")
    max_attachment_size_mb: int = Field(default=10, description="Max attachment size in MB")


class ProductionDomainSettings(DomainSettings):
    """Production domain specific settings.
    
    Attributes:
        auto_reserve_serials: Automatically reserve serial numbers
        serial_reserve_count: Number of serials to reserve at once
        validate_serial_format: Validate serial number format
    """
    auto_reserve_serials: bool = Field(default=True, description="Auto-reserve serial numbers")
    serial_reserve_count: int = Field(default=10, description="Number of serials to reserve")
    validate_serial_format: bool = Field(default=False, description="Validate serial format")


class ProcessDomainSettings(DomainSettings):
    """Process domain specific settings.
    
    Attributes:
        refresh_interval_seconds: Interval for refreshing process data
        auto_refresh: Enable automatic refresh
    """
    refresh_interval_seconds: int = Field(default=300, description="Refresh interval in seconds")
    auto_refresh: bool = Field(default=True, description="Enable automatic refresh")


class SoftwareDomainSettings(DomainSettings):
    """Software domain specific settings.
    
    Attributes:
        auto_download: Automatically download software updates
        download_path: Path for downloaded files
    """
    auto_download: bool = Field(default=False, description="Auto-download software updates")
    download_path: str = Field(default="./downloads", description="Download path")


class AssetDomainSettings(DomainSettings):
    """Asset domain specific settings."""
    pass  # Uses base settings only


class RootCauseDomainSettings(DomainSettings):
    """RootCause domain specific settings."""
    pass  # Uses base settings only


class AppDomainSettings(DomainSettings):
    """App/Statistics domain specific settings."""
    pass  # Uses base settings only


class APISettings(BaseModel):
    """
    Main API configuration settings.
    
    Controls global API behavior and per-domain settings.
    
    Attributes:
        timeout_seconds: HTTP request timeout
        max_retries: Maximum number of retry attempts
        retry_delay_seconds: Delay between retries
        error_mode: Error handling mode ("strict" or "lenient")
        log_requests: Log HTTP requests
        log_responses: Log HTTP responses
        verify_ssl: Verify SSL certificates
        product: Product domain settings
        report: Report domain settings
        production: Production domain settings
        process: Process domain settings
        software: Software domain settings
        asset: Asset domain settings
        rootcause: RootCause domain settings
        app: App/Statistics domain settings
    """
    model_config = ConfigDict(extra='ignore')
    
    # Connection settings
    timeout_seconds: int = Field(default=30, description="HTTP request timeout")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(default=1, description="Delay between retries")
    
    # Error handling
    error_mode: ErrorMode = Field(default=ErrorMode.STRICT, description="Error mode: STRICT or LENIENT")
    
    # Logging
    log_requests: bool = Field(default=False, description="Log HTTP requests")
    log_responses: bool = Field(default=False, description="Log HTTP responses")
    
    # SSL/TLS
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    
    # Domain settings
    product: ProductDomainSettings = Field(default_factory=ProductDomainSettings)
    report: ReportDomainSettings = Field(default_factory=ReportDomainSettings)
    production: ProductionDomainSettings = Field(default_factory=ProductionDomainSettings)
    process: ProcessDomainSettings = Field(default_factory=ProcessDomainSettings)
    software: SoftwareDomainSettings = Field(default_factory=SoftwareDomainSettings)
    asset: AssetDomainSettings = Field(default_factory=AssetDomainSettings)
    rootcause: RootCauseDomainSettings = Field(default_factory=RootCauseDomainSettings)
    app: AppDomainSettings = Field(default_factory=AppDomainSettings)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "error_mode": self.error_mode.value if isinstance(self.error_mode, ErrorMode) else self.error_mode,
            "log_requests": self.log_requests,
            "log_responses": self.log_responses,
            "verify_ssl": self.verify_ssl,
            "domains": {
                "product": self.product.to_dict(),
                "report": self.report.to_dict(),
                "production": self.production.to_dict(),
                "process": self.process.to_dict(),
                "software": self.software.to_dict(),
                "asset": self.asset.to_dict(),
                "rootcause": self.rootcause.to_dict(),
                "app": self.app.to_dict(),
            }
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APISettings":
        """Create from dictionary."""
        domains = data.pop("domains", {})
        
        # Handle error_mode as string or enum
        error_mode_value = data.get("error_mode", "strict")
        if isinstance(error_mode_value, str):
            error_mode = ErrorMode(error_mode_value)
        else:
            error_mode = error_mode_value
        
        settings = cls(
            timeout_seconds=data.get("timeout_seconds", 30),
            max_retries=data.get("max_retries", 3),
            retry_delay_seconds=data.get("retry_delay_seconds", 1),
            error_mode=error_mode,
            log_requests=data.get("log_requests", False),
            log_responses=data.get("log_responses", False),
            verify_ssl=data.get("verify_ssl", True),
        )
        
        # Load domain settings
        if "product" in domains:
            settings.product = ProductDomainSettings.from_dict(domains["product"])
        if "report" in domains:
            settings.report = ReportDomainSettings.from_dict(domains["report"])
        if "production" in domains:
            settings.production = ProductionDomainSettings.from_dict(domains["production"])
        if "process" in domains:
            settings.process = ProcessDomainSettings.from_dict(domains["process"])
        if "software" in domains:
            settings.software = SoftwareDomainSettings.from_dict(domains["software"])
        if "asset" in domains:
            settings.asset = AssetDomainSettings.from_dict(domains["asset"])
        if "rootcause" in domains:
            settings.rootcause = RootCauseDomainSettings.from_dict(domains["rootcause"])
        if "app" in domains:
            settings.app = AppDomainSettings.from_dict(domains["app"])
        
        return settings


# Default settings instance (constant, no file I/O)
_default_settings: Optional[APISettings] = None


def get_default_settings() -> APISettings:
    """
    Get the default API settings (constant defaults, no file I/O).
    
    For file-based persistence, use pywats_client.core.ConfigManager.
    """
    global _default_settings
    if _default_settings is None:
        _default_settings = APISettings()
    return _default_settings
