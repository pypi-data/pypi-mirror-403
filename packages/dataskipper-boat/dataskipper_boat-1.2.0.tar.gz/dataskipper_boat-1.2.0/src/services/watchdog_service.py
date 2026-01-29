import asyncio
import logging
import os
import socket
import time
from typing import Optional

logger = logging.getLogger(__name__)


class SystemdWatchdog:
    """
    Systemd watchdog integration service.

    Sends periodic "I'm alive" notifications to systemd to prevent
    service restart due to watchdog timeout.
    """

    def __init__(self, notify_interval: Optional[int] = None):
        """
        Initialize watchdog service.

        Args:
            notify_interval: How often to notify systemd (seconds).
                           If None, will use WatchdogSec/2 from systemd.
        """
        self.enabled = False
        self.watchdog_usec = 0
        self.notify_interval = notify_interval
        self.socket_path = os.getenv('NOTIFY_SOCKET')
        self.last_notify_time = 0
        self.stop_event = asyncio.Event()

        # Check if running under systemd with watchdog enabled
        watchdog_usec_str = os.getenv('WATCHDOG_USEC')
        if watchdog_usec_str and self.socket_path:
            try:
                self.watchdog_usec = int(watchdog_usec_str)
                self.enabled = True

                # Set notify interval to half of watchdog timeout if not specified
                if self.notify_interval is None:
                    self.notify_interval = (self.watchdog_usec // 2) // 1000000  # Convert to seconds
                    # Ensure minimum interval of 5 seconds
                    self.notify_interval = max(5, self.notify_interval)

                logger.info(
                    f"✓ Systemd watchdog enabled: "
                    f"timeout={self.watchdog_usec/1000000:.1f}s, "
                    f"notify_interval={self.notify_interval}s"
                )
            except ValueError as e:
                logger.error(f"Invalid WATCHDOG_USEC value: {e}")
                self.enabled = False
        else:
            logger.info(
                "Systemd watchdog not enabled (WATCHDOG_USEC or NOTIFY_SOCKET not set). "
                "Running without watchdog."
            )

    def notify(self, status: str = "WATCHDOG=1"):
        """
        Send notification to systemd.

        Args:
            status: Status string to send (default: WATCHDOG=1 for keepalive)
        """
        if not self.enabled or not self.socket_path:
            return

        try:
            # Create a Unix domain socket
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            sock.sendto(status.encode(), self.socket_path)
            sock.close()
            self.last_notify_time = time.time()
            logger.debug(f"Sent watchdog notification: {status}")
        except Exception as e:
            logger.error(f"Failed to send watchdog notification: {e}")

    def notify_ready(self):
        """Notify systemd that service is ready."""
        self.notify("READY=1")
        logger.info("✓ Notified systemd: service ready")

    def notify_stopping(self):
        """Notify systemd that service is stopping."""
        self.notify("STOPPING=1")
        logger.info("Notified systemd: service stopping")

    def notify_watchdog(self):
        """Send watchdog keepalive notification."""
        self.notify("WATCHDOG=1")

    def notify_status(self, status: str):
        """
        Send status message to systemd.

        Args:
            status: Status message
        """
        self.notify(f"STATUS={status}")

    async def start_keepalive(self):
        """Start watchdog keepalive loop."""
        if not self.enabled:
            logger.info("Watchdog keepalive loop not started (watchdog disabled)")
            return

        logger.info(
            f"Starting watchdog keepalive loop (interval: {self.notify_interval}s)"
        )

        # Send initial ready notification
        self.notify_ready()

        while not self.stop_event.is_set():
            try:
                await asyncio.sleep(self.notify_interval)
                self.notify_watchdog()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in watchdog keepalive loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying

    async def stop(self):
        """Stop watchdog keepalive loop."""
        self.stop_event.set()
        if self.enabled:
            self.notify_stopping()
        logger.info("Watchdog keepalive service stopped")

    def get_status(self) -> dict:
        """
        Get watchdog status information.

        Returns:
            Dict with watchdog status
        """
        return {
            'enabled': self.enabled,
            'watchdog_timeout_seconds': self.watchdog_usec / 1000000 if self.watchdog_usec else None,
            'notify_interval_seconds': self.notify_interval,
            'last_notify_time': self.last_notify_time,
            'seconds_since_last_notify': time.time() - self.last_notify_time if self.last_notify_time else None
        }


class ApplicationHealthMonitor:
    """
    Application-level health monitor.

    Tracks health of critical components and can trigger
    application restart if issues detected.
    """

    def __init__(
        self,
        check_interval: int = 30,
        unhealthy_threshold: int = 3
    ):
        """
        Initialize health monitor.

        Args:
            check_interval: How often to check health (seconds)
            unhealthy_threshold: Number of consecutive failures before action
        """
        self.check_interval = check_interval
        self.unhealthy_threshold = unhealthy_threshold
        self.health_checks = {}
        self.failure_counts = {}
        self.stop_event = asyncio.Event()

    def register_health_check(self, name: str, check_func):
        """
        Register a health check function.

        Args:
            name: Name of the health check
            check_func: Async function that returns True if healthy, False otherwise
        """
        self.health_checks[name] = check_func
        self.failure_counts[name] = 0
        logger.info(f"Registered health check: {name}")

    async def start_monitoring(self):
        """Start health monitoring loop."""
        logger.info(
            f"Starting application health monitoring "
            f"(interval: {self.check_interval}s, threshold: {self.unhealthy_threshold})"
        )

        while not self.stop_event.is_set():
            try:
                await asyncio.sleep(self.check_interval)
                await self._run_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _run_health_checks(self):
        """Run all registered health checks."""
        for name, check_func in self.health_checks.items():
            try:
                is_healthy = await check_func()

                if is_healthy:
                    # Reset failure count on success
                    if self.failure_counts[name] > 0:
                        logger.info(f"✓ Health check '{name}' recovered")
                    self.failure_counts[name] = 0
                else:
                    # Increment failure count
                    self.failure_counts[name] += 1
                    logger.warning(
                        f"⚠️  Health check '{name}' failed "
                        f"({self.failure_counts[name]}/{self.unhealthy_threshold})"
                    )

                    # Take action if threshold exceeded
                    if self.failure_counts[name] >= self.unhealthy_threshold:
                        logger.critical(
                            f"❌ Health check '{name}' exceeded failure threshold! "
                            f"Application may need restart."
                        )
                        # You could trigger restart here or just log
                        # For now, just log - systemd watchdog will handle restart

            except Exception as e:
                logger.error(f"Error running health check '{name}': {e}")
                self.failure_counts[name] += 1

    async def stop(self):
        """Stop health monitoring."""
        self.stop_event.set()
        logger.info("Application health monitoring stopped")

    def get_health_status(self) -> dict:
        """
        Get current health status.

        Returns:
            Dict with health status of all checks
        """
        return {
            'checks': {
                name: {
                    'failure_count': self.failure_counts.get(name, 0),
                    'is_healthy': self.failure_counts.get(name, 0) == 0
                }
                for name in self.health_checks.keys()
            },
            'overall_healthy': all(count == 0 for count in self.failure_counts.values())
        }


# Example usage
"""
Usage in main.py:

```python
from src.services.watchdog_service import SystemdWatchdog, ApplicationHealthMonitor

# Initialize watchdog
watchdog = SystemdWatchdog()

# Initialize health monitor
health_monitor = ApplicationHealthMonitor(check_interval=30)

# Register health checks
async def check_mqtt_health():
    return hasattr(monitor, 'mqtt_service') and monitor.mqtt_service.is_connected()

async def check_modbus_health():
    # Check if at least one Modbus client is connected
    for client in monitor.clients.values():
        if client.client and hasattr(client.client, 'connected'):
            if client.client.connected:
                return True
    return False

health_monitor.register_health_check('mqtt', check_mqtt_health)
health_monitor.register_health_check('modbus', check_modbus_health)

# Start services
async def main():
    # Start watchdog keepalive
    watchdog_task = asyncio.create_task(watchdog.start_keepalive())

    # Start health monitoring
    health_task = asyncio.create_task(health_monitor.start_monitoring())

    # Start your main application
    await monitor.start()

    # Cleanup
    await watchdog.stop()
    await health_monitor.stop()
```
"""
