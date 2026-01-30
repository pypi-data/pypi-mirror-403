"""
Headless Service Runner for pyWATS Client

Provides daemon/service mode for running pyWATS Client without GUI.
This is a thin wrapper around ClientService for CLI usage.

Usage:
    # Run in foreground
    python -m pywats_client service
    
    # With specific instance
    python -m pywats_client service --instance-id station1
"""

import logging
import sys
import signal
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..core.config import ClientConfig

logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Configuration for headless service wrapper"""
    # Logging
    log_to_file: bool = True
    log_file: str = "pywats_service.log"
    log_level: str = "INFO"


class HeadlessService:
    """
    Headless service runner for pyWATS Client.
    
    Thin wrapper around ClientService for CLI usage.
    
    Usage:
        from pywats_client.core.config import ClientConfig
        from pywats_client.control.service import HeadlessService, ServiceConfig
        
        service = HeadlessService(instance_id="default")
        service.run()
    """
    
    def __init__(
        self,
        instance_id: str = "default",
        client_config: Optional["ClientConfig"] = None,
        service_config: Optional[ServiceConfig] = None
    ) -> None:
        """
        Initialize headless service.
        
        Args:
            instance_id: Instance identifier
            client_config: Client configuration (optional, will load from instance)
            service_config: Service runtime configuration
        """
        self.instance_id = instance_id
        self.client_config = client_config
        self.service_config = service_config or ServiceConfig()
        
        self._client_service = None
        self._running = False
        
        # Setup signal handlers
        self._setup_signals()
    
    def _setup_signals(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGHUP, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals"""
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, initiating shutdown...")
        self.stop()
    
    def _setup_logging(self) -> None:
        """Configure logging for headless operation"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))
        
        handlers = [console_handler]
        
        # File handler if enabled
        if self.service_config.log_to_file:
            from ..core.config import ClientConfig
            config = self.client_config or ClientConfig.load_for_instance(self.instance_id)
            log_path = config.get_reports_path().parent / self.service_config.log_file
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(file_handler)
        
        # Configure root logger
        log_level = getattr(logging, self.service_config.log_level.upper(), logging.INFO)
        logging.basicConfig(level=log_level, handlers=handlers, force=True)
    
    def run(self) -> int:
        """
        Run the headless service (blocking).
        
        Returns:
            Exit code (0 = success)
        """
        self._setup_logging()
        
        logger.info(f"Starting pyWATS Client Service [instance: {self.instance_id}]")
        
        try:
            from ..service.client_service import ClientService
            
            self._client_service = ClientService(instance_id=self.instance_id)
            self._running = True
            
            # ClientService.start() is blocking
            self._client_service.start()
            
            return 0
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            return 0
        except Exception as e:
            logger.exception(f"Service error: {e}")
            return 1
        finally:
            self._running = False
            logger.info("Service stopped")
    
    def stop(self) -> None:
        """Stop the service gracefully"""
        if self._client_service:
            self._client_service.stop()
        self._running = False
