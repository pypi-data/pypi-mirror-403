import asyncio
import logging
import os
import time
import psutil
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """System performance metrics."""
    timestamp: int
    cpu_percent: float
    cpu_count: int
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_used_gb: float
    disk_free_gb: float
    process_cpu_percent: float
    process_memory_mb: float
    process_threads: int
    network_sent_mb: float
    network_recv_mb: float
    uptime_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'cpu': {
                'percent': self.cpu_percent,
                'count': self.cpu_count
            },
            'memory': {
                'percent': self.memory_percent,
                'used_mb': self.memory_used_mb,
                'available_mb': self.memory_available_mb
            },
            'disk': {
                'percent': self.disk_usage_percent,
                'used_gb': self.disk_used_gb,
                'free_gb': self.disk_free_gb
            },
            'process': {
                'cpu_percent': self.process_cpu_percent,
                'memory_mb': self.process_memory_mb,
                'threads': self.process_threads
            },
            'network': {
                'sent_mb': self.network_sent_mb,
                'recv_mb': self.network_recv_mb
            },
            'uptime_seconds': self.uptime_seconds
        }


class PerformanceMonitor:
    """
    System and process performance monitoring service.

    Tracks CPU, memory, disk, network usage and provides alerts
    when thresholds are exceeded. Optimized for Raspberry Pi with
    limited resources (typically 4GB RAM).

    Features:
    - System-wide resource monitoring
    - Process memory growth detection
    - Raspberry Pi specific thresholds
    - Alert callbacks for external notification
    """

    # Raspberry Pi 4 typical available memory thresholds
    PI_LOW_MEMORY_MB = 200  # Critical: less than 200MB available
    PI_PROCESS_MEMORY_LIMIT_MB = 500  # Process using > 500MB is concerning

    def __init__(
        self,
        monitor_interval: int = 60,  # Check every minute
        cpu_threshold: float = 80.0,  # Alert if >80% CPU
        memory_threshold: float = 80.0,  # Alert if >80% memory
        disk_threshold: float = 90.0,  # Alert if >90% disk
        process_memory_threshold_mb: float = 500.0,  # Alert if process > 500MB
        low_memory_threshold_mb: float = 200.0,  # Alert if < 200MB available
        alert_callback=None  # Optional callback for alerts
    ):
        """
        Initialize performance monitor.

        Args:
            monitor_interval: How often to collect metrics (seconds)
            cpu_threshold: CPU usage alert threshold (percent)
            memory_threshold: Memory usage alert threshold (percent)
            disk_threshold: Disk usage alert threshold (percent)
            process_memory_threshold_mb: Process memory threshold in MB
            low_memory_threshold_mb: Low available memory threshold in MB
            alert_callback: Optional async callback for alerts (receives alert dict)
        """
        self.monitor_interval = monitor_interval
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
        self.process_memory_threshold_mb = process_memory_threshold_mb
        self.low_memory_threshold_mb = low_memory_threshold_mb
        self.alert_callback = alert_callback

        self.process = psutil.Process(os.getpid())
        self.start_time = time.time()
        self.last_metrics: Optional[PerformanceMetrics] = None
        self.stop_event = asyncio.Event()

        # Memory growth tracking
        self._initial_process_memory_mb: Optional[float] = None
        self._memory_samples: list = []  # Track memory over time
        self._max_memory_samples = 60  # Keep 1 hour of data at 1min interval

        # Network counters for delta calculation
        self.last_net_io = psutil.net_io_counters()

        # Alert cooldowns to prevent spam (alert_type -> last_alert_time)
        self._alert_cooldowns: Dict[str, float] = {}
        self._alert_cooldown_seconds = 300  # 5 minutes between same alerts

    def collect_metrics(self) -> PerformanceMetrics:
        """
        Collect current performance metrics.

        Returns:
            PerformanceMetrics object
        """
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()

        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_available_mb = memory.available / (1024 * 1024)

        disk = psutil.disk_usage('/')
        disk_usage_percent = disk.percent
        disk_used_gb = disk.used / (1024 * 1024 * 1024)
        disk_free_gb = disk.free / (1024 * 1024 * 1024)

        # Process metrics
        try:
            process_cpu_percent = self.process.cpu_percent(interval=0.1)
            process_memory = self.process.memory_info()
            process_memory_mb = process_memory.rss / (1024 * 1024)
            process_threads = self.process.num_threads()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            process_cpu_percent = 0.0
            process_memory_mb = 0.0
            process_threads = 0

        # Network metrics
        net_io = psutil.net_io_counters()
        network_sent_mb = net_io.bytes_sent / (1024 * 1024)
        network_recv_mb = net_io.bytes_recv / (1024 * 1024)

        # Uptime
        uptime_seconds = time.time() - self.start_time

        metrics = PerformanceMetrics(
            timestamp=int(time.time()),
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_usage_percent=disk_usage_percent,
            disk_used_gb=disk_used_gb,
            disk_free_gb=disk_free_gb,
            process_cpu_percent=process_cpu_percent,
            process_memory_mb=process_memory_mb,
            process_threads=process_threads,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            uptime_seconds=uptime_seconds
        )

        self.last_metrics = metrics
        return metrics

    def _should_alert(self, alert_type: str) -> bool:
        """Check if we should send an alert (respecting cooldown)."""
        now = time.time()
        last_alert = self._alert_cooldowns.get(alert_type, 0)
        if now - last_alert >= self._alert_cooldown_seconds:
            self._alert_cooldowns[alert_type] = now
            return True
        return False

    def _track_memory_growth(self, metrics: PerformanceMetrics) -> Optional[Dict[str, Any]]:
        """Track memory growth over time and detect leaks.

        Returns alert dict if memory leak suspected, else None.
        """
        # Record initial memory on first call
        if self._initial_process_memory_mb is None:
            self._initial_process_memory_mb = metrics.process_memory_mb
            logger.info(f"Initial process memory: {self._initial_process_memory_mb:.1f}MB")

        # Add sample
        self._memory_samples.append({
            'timestamp': metrics.timestamp,
            'process_mb': metrics.process_memory_mb,
            'system_percent': metrics.memory_percent
        })

        # Keep only recent samples
        while len(self._memory_samples) > self._max_memory_samples:
            self._memory_samples.pop(0)

        # Need at least 10 samples to detect trend
        if len(self._memory_samples) < 10:
            return None

        # Calculate memory growth rate
        first_sample = self._memory_samples[0]
        last_sample = self._memory_samples[-1]
        time_delta_hours = (last_sample['timestamp'] - first_sample['timestamp']) / 3600

        if time_delta_hours < 0.1:  # Need at least 6 minutes of data
            return None

        memory_growth_mb = last_sample['process_mb'] - first_sample['process_mb']
        growth_rate_mb_per_hour = memory_growth_mb / time_delta_hours

        # Alert if growing > 50MB/hour consistently
        if growth_rate_mb_per_hour > 50:
            return {
                'type': 'memory_leak_suspected',
                'severity': 'warning',
                'message': f"Memory leak suspected: growing at {growth_rate_mb_per_hour:.1f}MB/hour",
                'details': {
                    'initial_mb': self._initial_process_memory_mb,
                    'current_mb': metrics.process_memory_mb,
                    'growth_mb': memory_growth_mb,
                    'growth_rate_mb_per_hour': growth_rate_mb_per_hour,
                    'tracking_hours': time_delta_hours
                }
            }

        return None

    def check_thresholds(self, metrics: PerformanceMetrics) -> list:
        """
        Check if any metrics exceed thresholds.

        Args:
            metrics: PerformanceMetrics to check

        Returns:
            List of alert dicts with type, severity, message, and details
        """
        alerts = []

        # High CPU usage
        if metrics.cpu_percent > self.cpu_threshold:
            if self._should_alert('high_cpu'):
                alerts.append({
                    'type': 'high_cpu',
                    'severity': 'warning',
                    'message': f"High CPU usage: {metrics.cpu_percent:.1f}% (threshold: {self.cpu_threshold}%)",
                    'details': {'cpu_percent': metrics.cpu_percent, 'threshold': self.cpu_threshold}
                })

        # High system memory usage
        if metrics.memory_percent > self.memory_threshold:
            if self._should_alert('high_memory'):
                alerts.append({
                    'type': 'high_memory',
                    'severity': 'warning',
                    'message': f"High memory usage: {metrics.memory_percent:.1f}% ({metrics.memory_used_mb:.0f}MB used)",
                    'details': {'memory_percent': metrics.memory_percent, 'memory_used_mb': metrics.memory_used_mb}
                })

        # Critical: Low available memory (Raspberry Pi specific)
        if metrics.memory_available_mb < self.low_memory_threshold_mb:
            if self._should_alert('low_memory_critical'):
                alerts.append({
                    'type': 'low_memory_critical',
                    'severity': 'critical',
                    'message': f"CRITICAL: Only {metrics.memory_available_mb:.0f}MB available (threshold: {self.low_memory_threshold_mb}MB)",
                    'details': {'memory_available_mb': metrics.memory_available_mb, 'threshold': self.low_memory_threshold_mb}
                })

        # Process memory exceeds limit
        if metrics.process_memory_mb > self.process_memory_threshold_mb:
            if self._should_alert('process_memory_high'):
                alerts.append({
                    'type': 'process_memory_high',
                    'severity': 'warning',
                    'message': f"Process memory high: {metrics.process_memory_mb:.1f}MB (threshold: {self.process_memory_threshold_mb}MB)",
                    'details': {'process_memory_mb': metrics.process_memory_mb, 'threshold': self.process_memory_threshold_mb}
                })

        # High disk usage
        if metrics.disk_usage_percent > self.disk_threshold:
            if self._should_alert('high_disk'):
                alerts.append({
                    'type': 'high_disk',
                    'severity': 'warning',
                    'message': f"High disk usage: {metrics.disk_usage_percent:.1f}% ({metrics.disk_free_gb:.1f}GB free)",
                    'details': {'disk_percent': metrics.disk_usage_percent, 'disk_free_gb': metrics.disk_free_gb}
                })

        # Check for memory growth/leak
        leak_alert = self._track_memory_growth(metrics)
        if leak_alert and self._should_alert('memory_leak'):
            alerts.append(leak_alert)

        return alerts

    def get_summary(self) -> str:
        """
        Get human-readable summary of current metrics.

        Returns:
            Formatted summary string
        """
        if not self.last_metrics:
            return "No metrics available"

        m = self.last_metrics
        uptime_hours = m.uptime_seconds / 3600

        summary = (
            f"System Performance Summary:\n"
            f"  CPU: {m.cpu_percent:.1f}% ({m.cpu_count} cores)\n"
            f"  Memory: {m.memory_percent:.1f}% ({m.memory_used_mb:.0f}MB / "
            f"{m.memory_used_mb + m.memory_available_mb:.0f}MB)\n"
            f"  Disk: {m.disk_usage_percent:.1f}% ({m.disk_free_gb:.1f}GB free)\n"
            f"  Process CPU: {m.process_cpu_percent:.1f}%\n"
            f"  Process Memory: {m.process_memory_mb:.1f}MB\n"
            f"  Process Threads: {m.process_threads}\n"
            f"  Network Sent: {m.network_sent_mb:.1f}MB\n"
            f"  Network Recv: {m.network_recv_mb:.1f}MB\n"
            f"  Uptime: {uptime_hours:.1f} hours"
        )

        return summary

    async def start_monitoring(self, mqtt_service=None):
        """
        Start continuous performance monitoring.

        Args:
            mqtt_service: Optional MQTT service to publish metrics
        """
        logger.info(
            f"Starting performance monitoring "
            f"(interval: {self.monitor_interval}s, "
            f"thresholds: CPU={self.cpu_threshold}%, "
            f"MEM={self.memory_threshold}%, "
            f"DISK={self.disk_threshold}%)"
        )

        # Initial collection
        metrics = self.collect_metrics()
        logger.info(f"Initial metrics:\n{self.get_summary()}")

        while not self.stop_event.is_set():
            try:
                await asyncio.sleep(self.monitor_interval)

                # Collect metrics
                metrics = self.collect_metrics()

                # Check thresholds
                alerts = self.check_thresholds(metrics)
                for alert in alerts:
                    severity = alert.get('severity', 'warning')
                    message = alert.get('message', str(alert))

                    if severity == 'critical':
                        logger.error(f"🔴 CRITICAL: {message}")
                    else:
                        logger.warning(f"⚠️  {message}")

                    # Call alert callback if provided
                    if self.alert_callback:
                        try:
                            if asyncio.iscoroutinefunction(self.alert_callback):
                                await self.alert_callback(alert)
                            else:
                                self.alert_callback(alert)
                        except Exception as e:
                            logger.error(f"Error in alert callback: {e}")

                # Log summary
                logger.info(
                    f"Performance: CPU {metrics.cpu_percent:.1f}%, "
                    f"MEM {metrics.memory_percent:.1f}%, "
                    f"Process {metrics.process_cpu_percent:.1f}% CPU / "
                    f"{metrics.process_memory_mb:.1f}MB"
                )

                # Publish to MQTT if available
                if mqtt_service and mqtt_service.is_connected():
                    try:
                        mqtt_service.client.publish(
                            "sensors/system/performance",
                            str(metrics.to_dict()),
                            qos=0
                        )
                    except Exception as e:
                        logger.debug(f"Failed to publish performance metrics: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {e}")
                await asyncio.sleep(60)

    async def stop(self):
        """Stop performance monitoring."""
        self.stop_event.set()
        logger.info("Performance monitoring stopped")

    def get_current_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Get current cached metrics.

        Returns:
            Dict with metrics or None if not available
        """
        if not self.last_metrics:
            return None

        return self.last_metrics.to_dict()

    def get_memory_health(self) -> Dict[str, Any]:
        """
        Get detailed memory health status for monitoring.

        Returns:
            Dict with memory health information
        """
        if not self.last_metrics:
            metrics = self.collect_metrics()
        else:
            metrics = self.last_metrics

        # Calculate memory growth if we have samples
        growth_info = {}
        if self._memory_samples and len(self._memory_samples) >= 2:
            first = self._memory_samples[0]
            last = self._memory_samples[-1]
            time_delta_hours = (last['timestamp'] - first['timestamp']) / 3600

            if time_delta_hours > 0:
                growth_mb = last['process_mb'] - first['process_mb']
                growth_info = {
                    'growth_mb': growth_mb,
                    'growth_rate_mb_per_hour': growth_mb / time_delta_hours,
                    'tracking_hours': time_delta_hours,
                    'sample_count': len(self._memory_samples)
                }

        return {
            'status': 'healthy' if metrics.memory_available_mb > self.low_memory_threshold_mb else 'critical',
            'system': {
                'percent': metrics.memory_percent,
                'used_mb': metrics.memory_used_mb,
                'available_mb': metrics.memory_available_mb
            },
            'process': {
                'memory_mb': metrics.process_memory_mb,
                'initial_memory_mb': self._initial_process_memory_mb,
                'threads': metrics.process_threads
            },
            'thresholds': {
                'memory_percent': self.memory_threshold,
                'low_memory_mb': self.low_memory_threshold_mb,
                'process_limit_mb': self.process_memory_threshold_mb
            },
            'growth': growth_info,
            'uptime_hours': metrics.uptime_seconds / 3600
        }


class PollingRateMonitor:
    """
    Monitors actual polling rate vs configured rate.

    Tracks timing of polling loops and warns if falling behind.
    """

    def __init__(self):
        """Initialize polling rate monitor."""
        self.device_timings: Dict[str, list] = {}
        self.max_history = 100  # Keep last 100 timings per device

    def record_poll(self, device_id: str, duration_seconds: float, expected_interval: float):
        """
        Record a polling cycle.

        Args:
            device_id: Device identifier
            duration_seconds: Time taken for poll cycle
            expected_interval: Expected polling interval
        """
        if device_id not in self.device_timings:
            self.device_timings[device_id] = []

        self.device_timings[device_id].append({
            'timestamp': time.time(),
            'duration': duration_seconds,
            'expected': expected_interval
        })

        # Keep only recent history
        if len(self.device_timings[device_id]) > self.max_history:
            self.device_timings[device_id].pop(0)

        # Warn if polling is taking too long
        if duration_seconds > expected_interval:
            logger.warning(
                f"⚠️  Polling {device_id} took {duration_seconds:.2f}s "
                f"but interval is {expected_interval}s "
                f"(behind by {duration_seconds - expected_interval:.2f}s)"
            )

    def get_statistics(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get polling statistics for a device.

        Args:
            device_id: Device identifier

        Returns:
            Dict with statistics or None
        """
        if device_id not in self.device_timings:
            return None

        timings = self.device_timings[device_id]
        if not timings:
            return None

        durations = [t['duration'] for t in timings]
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)

        return {
            'device_id': device_id,
            'sample_count': len(durations),
            'avg_duration_seconds': avg_duration,
            'min_duration_seconds': min_duration,
            'max_duration_seconds': max_duration,
            'expected_interval': timings[-1]['expected'] if timings else None
        }

    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all devices."""
        return {
            device_id: self.get_statistics(device_id)
            for device_id in self.device_timings.keys()
        }


# Example usage
"""
Usage in main.py:

```python
from src.services.performance_monitor import PerformanceMonitor, PollingRateMonitor

# Initialize monitors
perf_monitor = PerformanceMonitor(
    monitor_interval=60,
    cpu_threshold=80.0,
    memory_threshold=80.0,
    disk_threshold=90.0
)

polling_monitor = PollingRateMonitor()

# Start performance monitoring
perf_task = asyncio.create_task(perf_monitor.start_monitoring(mqtt_service))

# In your polling loop:
async def monitor_client(self, ...):
    while True:
        start = datetime.now()

        # ... do polling ...

        end = datetime.now()
        duration = (end - start).total_seconds()

        # Record polling timing
        polling_monitor.record_poll(
            modbus_client.id,
            duration,
            modbus_client.polling_interval
        )

# Get statistics
stats = polling_monitor.get_statistics('device_1')
print(f"Average poll time: {stats['avg_duration_seconds']:.2f}s")
```
"""
