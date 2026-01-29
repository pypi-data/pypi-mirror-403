import asyncio
import logging
import ntplib
import time
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class NTPService:
    """Service for NTP time synchronization verification and monitoring."""

    def __init__(
        self,
        ntp_servers: list = None,
        sync_interval: int = 3600,  # Check every hour
        max_drift_seconds: float = 5.0
    ):
        """
        Initialize NTP service.

        Args:
            ntp_servers: List of NTP servers to use (defaults to pool.ntp.org)
            sync_interval: How often to check time sync in seconds
            max_drift_seconds: Maximum acceptable time drift in seconds
        """
        self.ntp_servers = ntp_servers or [
            'pool.ntp.org',
            'time.google.com',
            'time.cloudflare.com'
        ]
        self.sync_interval = sync_interval
        self.max_drift_seconds = max_drift_seconds
        self.client = ntplib.NTPClient()
        self.last_sync_time = None
        self.last_drift = None
        self.sync_failures = 0
        self.stop_event = asyncio.Event()

    async def check_time_sync(self) -> Optional[Dict[str, Any]]:
        """
        Check time synchronization with NTP server.

        Returns:
            Dict with sync info or None if failed
        """
        for server in self.ntp_servers:
            try:
                # Run NTP request in executor to avoid blocking
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    self.client.request,
                    server,
                    version=3
                )

                # Calculate drift
                system_time = time.time()
                ntp_time = response.tx_time
                drift = abs(system_time - ntp_time)

                self.last_sync_time = datetime.now()
                self.last_drift = drift
                self.sync_failures = 0

                sync_info = {
                    'server': server,
                    'ntp_time': ntp_time,
                    'system_time': system_time,
                    'drift_seconds': drift,
                    'drift_ms': drift * 1000,
                    'offset': response.offset,
                    'delay': response.delay,
                    'synced': drift < self.max_drift_seconds,
                    'timestamp': datetime.now().isoformat()
                }

                if drift > self.max_drift_seconds:
                    logger.warning(
                        f"⚠️  Time drift detected: {drift:.3f}s (max: {self.max_drift_seconds}s) "
                        f"from {server}"
                    )
                else:
                    logger.info(
                        f"✓ Time synchronized with {server}: drift {drift:.3f}s, "
                        f"offset {response.offset:.3f}s"
                    )

                return sync_info

            except ntplib.NTPException as e:
                logger.error(f"NTP error with {server}: {e}")
                continue
            except Exception as e:
                logger.error(f"Failed to sync with {server}: {e}")
                continue

        # All servers failed
        self.sync_failures += 1
        logger.error(
            f"❌ Failed to sync with all NTP servers "
            f"(failure count: {self.sync_failures})"
        )
        return None

    async def start_monitoring(self):
        """Start continuous NTP monitoring task."""
        logger.info(
            f"Starting NTP monitoring service (interval: {self.sync_interval}s, "
            f"servers: {', '.join(self.ntp_servers)})"
        )

        # Initial sync check
        await self.check_time_sync()

        # Periodic monitoring
        while not self.stop_event.is_set():
            try:
                await asyncio.sleep(self.sync_interval)
                await self.check_time_sync()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in NTP monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def stop(self):
        """Stop NTP monitoring."""
        self.stop_event.set()
        logger.info("NTP monitoring service stopped")

    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current synchronization status.

        Returns:
            Dict with current sync status
        """
        return {
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'last_drift_seconds': self.last_drift,
            'last_drift_ms': self.last_drift * 1000 if self.last_drift else None,
            'sync_failures': self.sync_failures,
            'is_synced': self.last_drift is not None and self.last_drift < self.max_drift_seconds,
            'max_drift_threshold': self.max_drift_seconds
        }

    def add_timestamp_quality_indicator(self, timestamp: int) -> Dict[str, Any]:
        """
        Add time quality indicator to measurement timestamp.

        Args:
            timestamp: Unix timestamp

        Returns:
            Dict with timestamp and quality info
        """
        quality = "good"
        if self.last_drift is None:
            quality = "unknown"
        elif self.last_drift > self.max_drift_seconds:
            quality = "poor"
        elif self.last_drift > self.max_drift_seconds / 2:
            quality = "fair"

        return {
            'timestamp': timestamp,
            'time_quality': quality,
            'time_drift_ms': self.last_drift * 1000 if self.last_drift else None,
            'time_source': 'ntp' if self.last_sync_time else 'system'
        }
