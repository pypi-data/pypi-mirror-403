"""
pyWATS Client Configuration Manager

File-based configuration persistence for pyWATS Client.
This provides the file I/O layer on top of pywats.core.config.APISettings.

Usage:
    from pywats_client.core import ConfigManager
    
    # Load from default location
    manager = ConfigManager()
    settings = manager.load()
    
    # Load from custom path
    manager = ConfigManager(config_path="/path/to/config.json")
    settings = manager.load()
    
    # Modify and save
    settings.timeout_seconds = 60
    manager.save(settings)
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from pywats.core.config import APISettings
from .file_utils import SafeFileWriter, SafeFileReader

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    File-based configuration manager for pyWATS Client.
    
    Handles loading, saving, and watching for changes to the API config file.
    Uses atomic file operations via SafeFileWriter for reliability.
    """
    
    DEFAULT_CONFIG_FILENAME = "pywats_api.json"
    
    def __init__(self, config_path: Optional[Path] = None, instance_id: str = "default") -> None:
        """
        Initialize the config manager.
        
        Args:
            config_path: Path to config file. If None, uses default location.
            instance_id: Instance ID for multi-instance support (affects default path)
        """
        self._instance_id = instance_id
        
        if config_path is None:
            config_path = self._get_default_config_path(instance_id)
        
        self.config_path = Path(config_path)
        self._settings: Optional[APISettings] = None
    
    @staticmethod
    def _get_default_config_path(instance_id: str = "default") -> Path:
        """
        Get the default config file path for an instance.
        
        Args:
            instance_id: Instance ID
            
        Returns:
            Path to config file
        """
        if os.name == 'nt':
            base = Path(os.environ.get('APPDATA', '')) / 'pyWATS'
        else:
            base = Path.home() / '.config' / 'pywats'
        
        if instance_id == "default":
            return base / ConfigManager.DEFAULT_CONFIG_FILENAME
        else:
            return base / "instances" / instance_id / ConfigManager.DEFAULT_CONFIG_FILENAME
    
    @staticmethod
    def get_config_directory(instance_id: str = "default") -> Path:
        """
        Get the config directory for an instance.
        
        Args:
            instance_id: Instance ID
            
        Returns:
            Path to config directory
        """
        return ConfigManager._get_default_config_path(instance_id).parent
    
    def load(self) -> APISettings:
        """
        Load settings from file, creating defaults if not found.
        
        Returns:
            APISettings instance
        """
        if self.config_path.exists():
            try:
                data = SafeFileReader.read_json_safe(self.config_path, try_backup=True)
                if data:
                    self._settings = APISettings.from_dict(data)
                    logger.debug(f"Loaded API settings from {self.config_path}")
                else:
                    logger.debug("Config file empty or corrupted, using defaults")
                    self._settings = APISettings()
            except Exception as e:
                logger.warning(f"Failed to load API config, using defaults: {e}")
                self._settings = APISettings()
        else:
            logger.debug("No API config file found, using defaults")
            self._settings = APISettings()
        
        return self._settings
    
    def save(self, settings: Optional[APISettings] = None) -> None:
        """
        Save settings to file (atomic write).
        
        Args:
            settings: Settings to save. If None, saves current settings.
        """
        if settings:
            self._settings = settings
        
        if self._settings is None:
            self._settings = APISettings()
        
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            result = SafeFileWriter.write_json_atomic(
                self.config_path,
                self._settings.to_dict(),
                backup=True
            )
            if result.success:
                logger.debug(f"Saved API settings to {self.config_path}")
            else:
                raise IOError(result.error)
        except Exception as e:
            logger.error(f"Failed to save API config: {e}")
            raise
    
    @property
    def settings(self) -> APISettings:
        """Get current settings, loading if needed."""
        if self._settings is None:
            self.load()
        return self._settings  # type: ignore
    
    @property
    def instance_id(self) -> str:
        """Get the instance ID."""
        return self._instance_id
    
    def reset_to_defaults(self) -> APISettings:
        """Reset all settings to defaults and save."""
        self._settings = APISettings()
        self.save()
        return self._settings
    
    def exists(self) -> bool:
        """Check if config file exists."""
        return self.config_path.exists()


# Convenience function for quick access
def load_client_settings(instance_id: str = "default") -> APISettings:
    """
    Load client settings from file.
    
    Args:
        instance_id: Instance ID (default: "default")
        
    Returns:
        APISettings loaded from file (or defaults if not found)
    """
    manager = ConfigManager(instance_id=instance_id)
    return manager.load()
