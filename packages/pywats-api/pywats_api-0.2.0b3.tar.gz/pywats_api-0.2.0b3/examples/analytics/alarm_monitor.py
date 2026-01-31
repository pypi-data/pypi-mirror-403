"""
Alarm Monitor Example - Production-ready alarm polling service.

This example demonstrates how to build an alarm monitoring service using
pyWATS's get_alarm_logs() endpoint. Use this as a starting point for
building custom notification integrations.

IMPORTANT: This is an EXAMPLE, not a built-in pyWATS feature. Customize
the handlers, polling logic, and persistence to match your requirements.

Features demonstrated:
- Polling loop with configurable interval
- State tracking to detect new alarms
- Multiple notification handlers (email, Slack, Teams examples)
- Filtering by alarm type
- Graceful shutdown
- Error handling and retries

Usage:
    # Set environment variables
    export WATS_BASE_URL="https://your-wats-server.com"
    export WATS_TOKEN="your-api-token"
    
    # Run the monitor
    python alarm_monitor.py
    
    # Or customize and import into your own application
"""
import os
import sys
import time
import signal
import logging
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Set, Dict, Any
from abc import ABC, abstractmethod

# Add parent directory to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from pywats import pyWATS, AlarmType, AlarmLog


# =============================================================================
# Logging Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("alarm_monitor")


# =============================================================================
# Notification Handlers (Abstract Base)
# =============================================================================

class AlarmHandler(ABC):
    """
    Base class for alarm notification handlers.
    
    Implement this class to create custom notification integrations.
    """
    
    @abstractmethod
    def handle(self, alarm: AlarmLog) -> bool:
        """
        Handle an alarm notification.
        
        Args:
            alarm: The triggered alarm log entry
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable handler name for logging."""
        pass


class ConsoleHandler(AlarmHandler):
    """Simple handler that prints alarms to console."""
    
    @property
    def name(self) -> str:
        return "Console"
    
    def handle(self, alarm: AlarmLog) -> bool:
        print(f"\n{'='*60}")
        print(f"🚨 ALARM: {alarm.name}")
        print(f"   Type: {alarm.alarm_type_name}")
        print(f"   Time: {alarm.log_date}")
        
        # Type-specific details
        if alarm.type == AlarmType.YIELD_VOLUME:
            print(f"   Product: {alarm.part_number}")
            print(f"   FPY: {alarm.fpy_percent:.1f}%" if alarm.fpy is not None else "")
            print(f"   Trend: {alarm.fpy_trend_percent:+.1f}%" if alarm.fpy_trend is not None else "")
        elif alarm.type == AlarmType.REPORT:
            print(f"   Serial: {alarm.serial_number}")
            print(f"   Station: {alarm.station_name}")
        elif alarm.type == AlarmType.ASSET:
            print(f"   Asset: {alarm.asset_name}")
            print(f"   Serial: {alarm.asset_serial_number}")
        elif alarm.type == AlarmType.MEASUREMENT:
            print(f"   Path: {alarm.measurement_path}")
            print(f"   Cpk: {alarm.cpk}" if alarm.cpk is not None else "")
        elif alarm.type == AlarmType.SERIAL_NUMBER:
            print(f"   Free: {alarm.free}")
            print(f"   Reserved: {alarm.reserved}")
        
        print(f"{'='*60}\n")
        return True


class LoggingHandler(AlarmHandler):
    """Handler that logs alarms using Python logging."""
    
    def __init__(self, logger_name: str = "alarm_notifications"):
        self._logger = logging.getLogger(logger_name)
    
    @property
    def name(self) -> str:
        return "Logging"
    
    def handle(self, alarm: AlarmLog) -> bool:
        self._logger.warning(
            "ALARM [%s] %s - Product: %s, Type: %s",
            alarm.log_id,
            alarm.name,
            alarm.part_number or "N/A",
            alarm.alarm_type_name
        )
        return True


# =============================================================================
# Example Handler Stubs (Implement these for your environment)
# =============================================================================

class EmailHandler(AlarmHandler):
    """
    Example email notification handler.
    
    CUSTOMIZE THIS: Replace with your SMTP server configuration.
    """
    
    def __init__(
        self,
        smtp_server: str = "smtp.company.com",
        smtp_port: int = 587,
        sender: str = "wats-alerts@company.com",
        recipients: List[str] = None,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender = sender
        self.recipients = recipients or []
    
    @property
    def name(self) -> str:
        return "Email"
    
    def handle(self, alarm: AlarmLog) -> bool:
        """
        Send email notification.
        
        IMPLEMENT THIS: Add actual SMTP sending logic.
        """
        # Example implementation (uncomment and customize):
        #
        # import smtplib
        # from email.mime.text import MIMEText
        # from email.mime.multipart import MIMEMultipart
        #
        # msg = MIMEMultipart()
        # msg['From'] = self.sender
        # msg['To'] = ', '.join(self.recipients)
        # msg['Subject'] = f"WATS Alert: {alarm.name}"
        #
        # body = f"""
        # WATS Alarm Triggered
        # 
        # Name: {alarm.name}
        # Type: {alarm.alarm_type_name}
        # Time: {alarm.log_date}
        # Product: {alarm.part_number}
        # """
        # msg.attach(MIMEText(body, 'plain'))
        #
        # with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
        #     server.starttls()
        #     server.sendmail(self.sender, self.recipients, msg.as_string())
        
        logger.info(f"[EMAIL] Would send to {self.recipients}: {alarm.name}")
        return True


class SlackHandler(AlarmHandler):
    """
    Example Slack webhook notification handler.
    
    CUSTOMIZE THIS: Set your Slack webhook URL.
    """
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    
    @property
    def name(self) -> str:
        return "Slack"
    
    def handle(self, alarm: AlarmLog) -> bool:
        """
        Send Slack notification via webhook.
        
        IMPLEMENT THIS: Add actual HTTP POST to webhook.
        """
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
        
        # Example implementation (uncomment and customize):
        #
        # import requests
        #
        # message = {
        #     "text": f"🚨 *WATS Alarm*: {alarm.name}",
        #     "blocks": [
        #         {
        #             "type": "section",
        #             "text": {
        #                 "type": "mrkdwn",
        #                 "text": f"*{alarm.name}*\nType: {alarm.alarm_type_name}\nProduct: {alarm.part_number or 'N/A'}"
        #             }
        #         }
        #     ]
        # }
        # response = requests.post(self.webhook_url, json=message)
        # return response.status_code == 200
        
        logger.info(f"[SLACK] Would post to webhook: {alarm.name}")
        return True


class TeamsHandler(AlarmHandler):
    """
    Example Microsoft Teams webhook notification handler.
    
    CUSTOMIZE THIS: Set your Teams webhook URL.
    """
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.environ.get("TEAMS_WEBHOOK_URL")
    
    @property
    def name(self) -> str:
        return "Teams"
    
    def handle(self, alarm: AlarmLog) -> bool:
        """
        Send Teams notification via webhook.
        
        IMPLEMENT THIS: Add actual HTTP POST to webhook.
        """
        if not self.webhook_url:
            logger.warning("Teams webhook URL not configured")
            return False
        
        # Example implementation (uncomment and customize):
        #
        # import requests
        #
        # card = {
        #     "@type": "MessageCard",
        #     "themeColor": "FF0000",
        #     "title": f"WATS Alarm: {alarm.name}",
        #     "text": f"Type: {alarm.alarm_type_name}\nProduct: {alarm.part_number or 'N/A'}"
        # }
        # response = requests.post(self.webhook_url, json=card)
        # return response.status_code == 200
        
        logger.info(f"[TEAMS] Would post to webhook: {alarm.name}")
        return True


# =============================================================================
# Alarm Monitor Service
# =============================================================================

@dataclass
class AlarmMonitorConfig:
    """Configuration for the alarm monitor."""
    
    poll_interval_seconds: int = 60
    """How often to poll for new alarms (seconds)."""
    
    lookback_minutes: int = 5
    """How far back to look on first poll (minutes)."""
    
    alarm_types: Optional[List[AlarmType]] = None
    """Filter to specific alarm types (None = all types)."""
    
    product_groups: Optional[List[str]] = None
    """Filter to specific product groups (None = all groups)."""
    
    max_alarms_per_poll: int = 100
    """Maximum alarms to fetch per poll."""
    
    retry_on_error: bool = True
    """Retry on transient errors."""
    
    max_retries: int = 3
    """Maximum retry attempts on error."""
    
    retry_delay_seconds: int = 10
    """Delay between retries (seconds)."""


class AlarmMonitor:
    """
    Production-ready alarm monitoring service.
    
    Polls WATS for new alarms and dispatches to registered handlers.
    
    Example:
        >>> monitor = AlarmMonitor(api)
        >>> monitor.add_handler(ConsoleHandler())
        >>> monitor.add_handler(SlackHandler(webhook_url="..."))
        >>> monitor.run()  # Runs until interrupted
    """
    
    def __init__(
        self,
        api: pyWATS,
        config: AlarmMonitorConfig = None,
    ):
        """
        Initialize alarm monitor.
        
        Args:
            api: Configured pyWATS client instance
            config: Optional configuration (uses defaults if not provided)
        """
        self.api = api
        self.config = config or AlarmMonitorConfig()
        self._handlers: List[AlarmHandler] = []
        self._seen_alarm_ids: Set[int] = set()
        self._last_poll_time: Optional[datetime] = None
        self._running = False
        self._stats = {
            "polls": 0,
            "alarms_processed": 0,
            "notifications_sent": 0,
            "errors": 0,
        }
    
    def add_handler(self, handler: AlarmHandler) -> "AlarmMonitor":
        """
        Add a notification handler.
        
        Args:
            handler: AlarmHandler implementation
            
        Returns:
            self for method chaining
        """
        self._handlers.append(handler)
        logger.info(f"Added handler: {handler.name}")
        return self
    
    def remove_handler(self, handler: AlarmHandler) -> "AlarmMonitor":
        """Remove a notification handler."""
        self._handlers.remove(handler)
        return self
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get monitoring statistics."""
        return self._stats.copy()
    
    def _fetch_alarms(self) -> List[AlarmLog]:
        """Fetch new alarms from WATS."""
        # Determine date range
        if self._last_poll_time:
            date_from = self._last_poll_time
        else:
            date_from = datetime.now(timezone.utc) - timedelta(
                minutes=self.config.lookback_minutes
            )
        
        date_to = datetime.now(timezone.utc)
        
        # Fetch alarms for each configured type (or all if not filtered)
        all_alarms: List[AlarmLog] = []
        
        if self.config.alarm_types:
            for alarm_type in self.config.alarm_types:
                try:
                    alarms = self.api.analytics.get_alarm_logs(
                        alarm_type=alarm_type,
                        date_from=date_from,
                        date_to=date_to,
                        top_count=self.config.max_alarms_per_poll,
                    )
                    all_alarms.extend(alarms)
                except Exception as e:
                    logger.error(f"Error fetching {alarm_type.name} alarms: {e}")
                    self._stats["errors"] += 1
        else:
            try:
                all_alarms = self.api.analytics.get_alarm_logs(
                    date_from=date_from,
                    date_to=date_to,
                    top_count=self.config.max_alarms_per_poll,
                )
            except Exception as e:
                logger.error(f"Error fetching alarms: {e}")
                self._stats["errors"] += 1
        
        self._last_poll_time = date_to
        return all_alarms
    
    def _filter_new_alarms(self, alarms: List[AlarmLog]) -> List[AlarmLog]:
        """Filter out already-seen alarms."""
        new_alarms = []
        for alarm in alarms:
            if alarm.log_id and alarm.log_id not in self._seen_alarm_ids:
                new_alarms.append(alarm)
                self._seen_alarm_ids.add(alarm.log_id)
        
        # Prevent memory leak - keep only recent IDs
        if len(self._seen_alarm_ids) > 10000:
            # Keep the most recent half
            recent_ids = sorted(self._seen_alarm_ids)[-5000:]
            self._seen_alarm_ids = set(recent_ids)
        
        return new_alarms
    
    def _dispatch_alarm(self, alarm: AlarmLog) -> int:
        """
        Dispatch alarm to all handlers.
        
        Returns:
            Number of successful notifications
        """
        success_count = 0
        for handler in self._handlers:
            try:
                if handler.handle(alarm):
                    success_count += 1
            except Exception as e:
                logger.error(f"Handler {handler.name} failed: {e}")
        return success_count
    
    def poll_once(self) -> int:
        """
        Poll for alarms once and dispatch notifications.
        
        Returns:
            Number of new alarms processed
        """
        self._stats["polls"] += 1
        
        # Fetch alarms
        alarms = self._fetch_alarms()
        logger.debug(f"Fetched {len(alarms)} alarms")
        
        # Filter to new ones
        new_alarms = self._filter_new_alarms(alarms)
        
        if new_alarms:
            logger.info(f"Processing {len(new_alarms)} new alarm(s)")
        
        # Dispatch
        for alarm in new_alarms:
            self._stats["alarms_processed"] += 1
            notifications = self._dispatch_alarm(alarm)
            self._stats["notifications_sent"] += notifications
        
        return len(new_alarms)
    
    def run(self) -> None:
        """
        Start the polling loop (runs until interrupted).
        
        Press Ctrl+C to stop gracefully.
        """
        self._running = True
        
        # Setup graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Shutdown signal received")
            self._running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info(
            f"Starting alarm monitor (poll interval: {self.config.poll_interval_seconds}s)"
        )
        logger.info(f"Handlers: {[h.name for h in self._handlers]}")
        
        retry_count = 0
        
        while self._running:
            try:
                new_count = self.poll_once()
                retry_count = 0  # Reset on success
                
                if new_count > 0:
                    logger.info(f"Processed {new_count} new alarm(s)")
                
            except Exception as e:
                logger.error(f"Poll error: {e}")
                self._stats["errors"] += 1
                
                if self.config.retry_on_error:
                    retry_count += 1
                    if retry_count >= self.config.max_retries:
                        logger.error("Max retries exceeded, stopping")
                        break
                    time.sleep(self.config.retry_delay_seconds)
                    continue
            
            # Wait for next poll
            if self._running:
                time.sleep(self.config.poll_interval_seconds)
        
        logger.info(f"Alarm monitor stopped. Stats: {self._stats}")
    
    def stop(self) -> None:
        """Request graceful shutdown."""
        self._running = False


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Example usage of AlarmMonitor."""
    
    # Configure from environment
    base_url = os.environ.get("WATS_BASE_URL", "https://demo.wats.com")
    token = os.environ.get("WATS_TOKEN", "")
    
    if not token:
        print("ERROR: Set WATS_TOKEN environment variable")
        print("Usage:")
        print("  export WATS_BASE_URL='https://your-wats-server.com'")
        print("  export WATS_TOKEN='your-api-token'")
        print("  python alarm_monitor.py")
        sys.exit(1)
    
    # Create API client
    api = pyWATS(base_url=base_url, token=token)
    
    # Configure monitor
    config = AlarmMonitorConfig(
        poll_interval_seconds=30,      # Poll every 30 seconds
        lookback_minutes=10,            # Look back 10 minutes on start
        alarm_types=[                   # Only monitor yield and asset alarms
            AlarmType.YIELD_VOLUME,
            AlarmType.ASSET,
        ],
        max_alarms_per_poll=50,
    )
    
    # Create monitor with handlers
    monitor = AlarmMonitor(api, config)
    monitor.add_handler(ConsoleHandler())
    monitor.add_handler(LoggingHandler())
    
    # Uncomment to add real notification handlers:
    # monitor.add_handler(EmailHandler(
    #     recipients=["alerts@company.com"]
    # ))
    # monitor.add_handler(SlackHandler(
    #     webhook_url=os.environ.get("SLACK_WEBHOOK_URL")
    # ))
    
    print("\n🔔 Starting WATS Alarm Monitor")
    print(f"   Server: {base_url}")
    print(f"   Poll interval: {config.poll_interval_seconds}s")
    print(f"   Alarm types: {[t.name for t in config.alarm_types]}")
    print("\nPress Ctrl+C to stop\n")
    
    # Run the monitor
    monitor.run()


if __name__ == "__main__":
    main()
