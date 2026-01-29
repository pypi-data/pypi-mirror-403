import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Deque
from dataclasses import dataclass, field
import statistics

logger = logging.getLogger(__name__)


@dataclass
class AggregatedData:
    """Aggregated measurement data."""
    device_id: str
    device_type: str
    field_name: str
    window_duration: str  # e.g., "1min", "5min", "15min"
    start_timestamp: int
    end_timestamp: int
    count: int
    min_value: float
    max_value: float
    avg_value: float
    sum_value: float
    std_dev: Optional[float] = None
    median: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'device_id': self.device_id,
            'device_type': self.device_type,
            'field_name': self.field_name,
            'window_duration': self.window_duration,
            'start_timestamp': self.start_timestamp,
            'end_timestamp': self.end_timestamp,
            'count': self.count,
            'min': self.min_value,
            'max': self.max_value,
            'avg': self.avg_value,
            'sum': self.sum_value,
            'std_dev': self.std_dev,
            'median': self.median
        }


@dataclass
class DataPoint:
    """Individual data point for aggregation."""
    timestamp: int
    value: float


class TimeWindowAggregator:
    """
    Aggregates measurement data over time windows.

    Supports multiple window sizes: 1min, 5min, 15min, 1hour
    Computes: min, max, avg, sum, std_dev, median
    """

    def __init__(
        self,
        windows: List[int] = None,  # Window sizes in seconds
        max_buffer_size: int = 3600  # Keep last hour of data
    ):
        """
        Initialize aggregator.

        Args:
            windows: List of window sizes in seconds (default: [60, 300, 900])
            max_buffer_size: Maximum number of data points to keep per device/field
        """
        self.windows = windows or [60, 300, 900, 3600]  # 1min, 5min, 15min, 1hour
        self.max_buffer_size = max_buffer_size

        # Store data points: {device_id: {field_name: deque[DataPoint]}}
        self.data_buffers: Dict[str, Dict[str, Deque[DataPoint]]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=max_buffer_size))
        )

        # Track last aggregation time for each window
        self.last_aggregation: Dict[int, int] = {window: 0 for window in self.windows}

    def add_measurement(
        self,
        device_id: str,
        device_type: str,
        timestamp: int,
        values: Dict[str, Any]
    ):
        """
        Add a measurement to the aggregation buffer.

        Args:
            device_id: Device identifier
            device_type: Device type
            timestamp: Measurement timestamp
            values: Dict of field_name: value pairs
        """
        for field_name, value in values.items():
            # Only aggregate numeric values
            if not isinstance(value, (int, float)):
                continue

            data_point = DataPoint(timestamp=timestamp, value=float(value))
            self.data_buffers[device_id][field_name].append(data_point)

        logger.debug(
            f"Added measurement for {device_id}: {len(values)} fields at {timestamp}"
        )

    def aggregate_window(
        self,
        device_id: str,
        device_type: str,
        field_name: str,
        window_seconds: int,
        end_time: Optional[int] = None
    ) -> Optional[AggregatedData]:
        """
        Aggregate data for a specific time window.

        Args:
            device_id: Device identifier
            device_type: Device type
            field_name: Field to aggregate
            window_seconds: Window size in seconds
            end_time: End of window (default: now)

        Returns:
            AggregatedData or None if insufficient data
        """
        if device_id not in self.data_buffers:
            return None
        if field_name not in self.data_buffers[device_id]:
            return None

        end_time = end_time or int(datetime.now().timestamp())
        start_time = end_time - window_seconds

        # Get data points within window
        data_points = self.data_buffers[device_id][field_name]
        window_data = [
            dp.value for dp in data_points
            if start_time <= dp.timestamp <= end_time
        ]

        if not window_data:
            return None

        # Compute statistics
        min_value = min(window_data)
        max_value = max(window_data)
        avg_value = statistics.mean(window_data)
        sum_value = sum(window_data)

        # Optional: std_dev and median (more expensive)
        std_dev = None
        median = None
        if len(window_data) >= 2:
            try:
                std_dev = statistics.stdev(window_data)
                median = statistics.median(window_data)
            except Exception as e:
                logger.debug(f"Could not compute std_dev/median: {e}")

        # Window label
        window_label = self._format_window_label(window_seconds)

        return AggregatedData(
            device_id=device_id,
            device_type=device_type,
            field_name=field_name,
            window_duration=window_label,
            start_timestamp=start_time,
            end_timestamp=end_time,
            count=len(window_data),
            min_value=min_value,
            max_value=max_value,
            avg_value=avg_value,
            sum_value=sum_value,
            std_dev=std_dev,
            median=median
        )

    def aggregate_all_windows(
        self,
        device_id: str,
        device_type: str,
        field_name: str
    ) -> List[AggregatedData]:
        """
        Aggregate data for all configured windows.

        Args:
            device_id: Device identifier
            device_type: Device type
            field_name: Field to aggregate

        Returns:
            List of AggregatedData for each window
        """
        results = []
        for window in self.windows:
            aggregated = self.aggregate_window(
                device_id, device_type, field_name, window
            )
            if aggregated:
                results.append(aggregated)

        return results

    def get_all_aggregations(self) -> List[AggregatedData]:
        """
        Get aggregations for all devices and fields across all windows.

        Returns:
            List of all aggregated data
        """
        results = []
        for device_id, fields in self.data_buffers.items():
            for field_name in fields.keys():
                # Try to infer device_type (you may want to store this separately)
                device_type = "unknown"  # Should be tracked separately
                aggregations = self.aggregate_all_windows(
                    device_id, device_type, field_name
                )
                results.extend(aggregations)

        return results

    def cleanup_old_data(self, max_age_seconds: int = 7200):
        """
        Remove data points older than max_age_seconds.

        Args:
            max_age_seconds: Maximum age to keep (default: 2 hours)
        """
        current_time = int(datetime.now().timestamp())
        cutoff_time = current_time - max_age_seconds
        removed_count = 0

        for device_id, fields in self.data_buffers.items():
            for field_name, data_points in fields.items():
                # Remove old points
                while data_points and data_points[0].timestamp < cutoff_time:
                    data_points.popleft()
                    removed_count += 1

        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} old data points")

    @staticmethod
    def _format_window_label(seconds: int) -> str:
        """Format window size as human-readable label."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}min"
        else:
            return f"{seconds // 3600}hour"


class AggregationService:
    """
    Service that manages data aggregation and periodic reporting.
    """

    def __init__(
        self,
        aggregator: TimeWindowAggregator,
        report_interval: int = 60,  # Report every minute
        api_service = None,
        mqtt_service = None
    ):
        """
        Initialize aggregation service.

        Args:
            aggregator: TimeWindowAggregator instance
            report_interval: How often to send aggregated data (seconds)
            api_service: Optional API service for sending aggregations
            mqtt_service: Optional MQTT service for publishing aggregations
        """
        self.aggregator = aggregator
        self.report_interval = report_interval
        self.api_service = api_service
        self.mqtt_service = mqtt_service
        self.stop_event = asyncio.Event()

        # Track device types separately
        self.device_types: Dict[str, str] = {}

    def register_device(self, device_id: str, device_type: str):
        """Register device type for aggregation."""
        self.device_types[device_id] = device_type

    def add_measurement(
        self,
        device_id: str,
        device_type: str,
        timestamp: int,
        values: Dict[str, Any]
    ):
        """
        Add measurement to aggregation buffer.

        Args:
            device_id: Device identifier
            device_type: Device type
            timestamp: Measurement timestamp
            values: Dict of field_name: value pairs
        """
        # Register device type
        self.device_types[device_id] = device_type

        # Add to aggregator
        self.aggregator.add_measurement(device_id, device_type, timestamp, values)

    async def start_reporting(self):
        """Start periodic aggregation reporting task."""
        logger.info(
            f"Starting aggregation reporting service (interval: {self.report_interval}s, "
            f"windows: {[self.aggregator._format_window_label(w) for w in self.aggregator.windows]})"
        )

        while not self.stop_event.is_set():
            try:
                await asyncio.sleep(self.report_interval)
                await self._generate_and_send_reports()

                # Cleanup old data every 10 reports
                if int(datetime.now().timestamp()) % (self.report_interval * 10) == 0:
                    self.aggregator.cleanup_old_data()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in aggregation reporting loop: {e}")
                await asyncio.sleep(60)

    async def _generate_and_send_reports(self):
        """Generate aggregation reports and send them."""
        reports_sent = 0

        for device_id, device_type in self.device_types.items():
            if device_id not in self.aggregator.data_buffers:
                continue

            for field_name in self.aggregator.data_buffers[device_id].keys():
                aggregations = self.aggregator.aggregate_all_windows(
                    device_id, device_type, field_name
                )

                for agg in aggregations:
                    # Send to API if configured
                    if self.api_service:
                        try:
                            # You'll need to add send_aggregation method to APIService
                            # await self.api_service.send_aggregation(agg.to_dict())
                            pass
                        except Exception as e:
                            logger.error(f"Failed to send aggregation to API: {e}")

                    # Publish to MQTT if configured
                    if self.mqtt_service:
                        try:
                            topic = f"sensors/{device_type}/aggregations/{agg.window_duration}"
                            self.mqtt_service.client.publish(
                                topic,
                                str(agg.to_dict()),
                                qos=1
                            )
                            reports_sent += 1
                        except Exception as e:
                            logger.error(f"Failed to publish aggregation to MQTT: {e}")

        if reports_sent > 0:
            logger.debug(f"Sent {reports_sent} aggregation reports")

    async def stop(self):
        """Stop aggregation reporting."""
        self.stop_event.set()
        logger.info("Aggregation reporting service stopped")

    def get_latest_aggregation(
        self,
        device_id: str,
        field_name: str,
        window_seconds: int
    ) -> Optional[AggregatedData]:
        """
        Get latest aggregation for specific device/field/window.

        Args:
            device_id: Device identifier
            field_name: Field name
            window_seconds: Window size in seconds

        Returns:
            AggregatedData or None
        """
        device_type = self.device_types.get(device_id, "unknown")
        return self.aggregator.aggregate_window(
            device_id, device_type, field_name, window_seconds
        )


# Example usage
"""
Usage in main.py:

```python
from src.services.aggregation_service import TimeWindowAggregator, AggregationService

# Initialize
aggregator = TimeWindowAggregator(
    windows=[60, 300, 900],  # 1min, 5min, 15min
    max_buffer_size=3600
)

aggregation_service = AggregationService(
    aggregator=aggregator,
    report_interval=60,
    mqtt_service=mqtt_service
)

# Start reporting
await aggregation_service.start_reporting()

# In your monitoring loop, add measurements:
aggregation_service.add_measurement(
    device_id=modbus_client.id,
    device_type=modbus_client.type,
    timestamp=int(time.time()),
    values=values  # Your measurement values dict
)

# Get specific aggregation
agg = aggregation_service.get_latest_aggregation(
    device_id="device_1",
    field_name="voltage_rms",
    window_seconds=300  # 5 minutes
)
if agg:
    print(f"5-min avg voltage: {agg.avg_value}V")
    print(f"5-min min: {agg.min_value}V, max: {agg.max_value}V")
```
"""
