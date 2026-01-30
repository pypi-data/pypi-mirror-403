import enum
import json
import logging
import os
from datetime import datetime
from typing import Dict

from tenacity import retry, stop_after_attempt, wait_exponential

from src.interfaces.storage import IStorage
from src.models.alert import Alert
from src.models.measurement import Measurement
from src.utils.common import human_readable_time

logger = logging.getLogger(__name__)


class Status(str, enum.Enum):
    PENDING = 'pending'
    PROCESSED = 'processed'


class FileStorage(IStorage):
    """File-based storage with limits to prevent disk exhaustion.

    Implements a maximum pending files limit to prevent unbounded growth
    when the backend API is unavailable for extended periods.
    """

    DEFAULT_MAX_PENDING_MEASUREMENTS = 100000
    DEFAULT_MAX_PENDING_ALERTS = 500

    def __init__(
        self,
        base_path: str,
        max_pending_measurements: int = DEFAULT_MAX_PENDING_MEASUREMENTS,
        max_pending_alerts: int = DEFAULT_MAX_PENDING_ALERTS
    ):
        self.measurements_path = os.path.join(base_path, "measurements")
        self.alerts_path = os.path.join(base_path, "alerts")
        self.pending_path = os.path.join(base_path, "pending")
        self.pending_alert_path = os.path.join(base_path, "pending", "alerts")
        self.pending_measurement_path = os.path.join(base_path, "pending", "measurements")

        # Limits to prevent disk exhaustion
        self.max_pending_measurements = max_pending_measurements
        self.max_pending_alerts = max_pending_alerts

        # Create all required directories
        for path in [base_path, self.measurements_path, self.alerts_path,
                    self.pending_path, self.pending_alert_path,
                    self.pending_measurement_path]:
            os.makedirs(path, exist_ok=True)

    def _count_files(self, directory: str) -> int:
        """Count files in a directory."""
        try:
            if not os.path.exists(directory):
                return 0
            return len([f for f in os.listdir(directory) if f.endswith('.json')])
        except Exception as e:
            logger.error(f"Error counting files in {directory}: {e}")
            return 0

    def _evict_oldest_files(self, directory: str, max_files: int) -> int:
        """Remove oldest files when directory exceeds limit.

        Args:
            directory: Path to the directory
            max_files: Maximum number of files to keep

        Returns:
            Number of files evicted
        """
        try:
            if not os.path.exists(directory):
                return 0

            files = []
            for filename in os.listdir(directory):
                if filename.endswith('.json'):
                    filepath = os.path.join(directory, filename)
                    try:
                        mtime = os.path.getmtime(filepath)
                        files.append((filepath, mtime))
                    except OSError:
                        continue

            if len(files) <= max_files:
                return 0

            # Sort by modification time (oldest first)
            files.sort(key=lambda x: x[1])

            # Remove oldest files to get under limit (keep 90% of max)
            target_count = int(max_files * 0.9)
            evict_count = len(files) - target_count
            evicted = 0

            for filepath, _ in files[:evict_count]:
                try:
                    os.remove(filepath)
                    evicted += 1
                except Exception as e:
                    logger.error(f"Failed to evict file {filepath}: {e}")

            if evicted > 0:
                logger.warning(
                    f"Evicted {evicted} oldest pending files from {directory} "
                    f"(limit: {max_files})"
                )
            return evicted
        except Exception as e:
            logger.error(f"Error evicting files from {directory}: {e}")
            return 0

    def get_pending_stats(self) -> dict:
        """Get statistics about pending files."""
        return {
            "pending_measurements": self._count_files(self.pending_measurement_path),
            "pending_alerts": self._count_files(self.pending_alert_path),
            "max_pending_measurements": self.max_pending_measurements,
            "max_pending_alerts": self.max_pending_alerts
        }

    async def save_measurement(self, measurement: Measurement) -> None:
        """Save measurement data to file system."""
        filename = f"{measurement.device_id}_{human_readable_time(measurement.timestamp)}.json"
        path = os.path.join(self.measurements_path, filename)
        if isinstance(measurement.timestamp, datetime):
            measurement.timestamp = measurement.timestamp.timestamp()

        with open(path, 'w') as f:
            json.dump(measurement.to_dict(), f)

    async def save_alert(self, alert: Alert) -> None:
        """Save alert with UUID as filename for easy lookup and tracking."""
        filename = f"{alert.id}.json"
        path = os.path.join(self.alerts_path, filename)
        
        # Convert UUIDs to strings for JSON serialization
        alert_dict = alert.to_dict()
        alert_dict['id'] = str(alert_dict['id'])
        if alert_dict.get('parent_alert_id'):
            alert_dict['parent_alert_id'] = str(alert_dict['parent_alert_id'])

        with open(path, 'w') as f:
            json.dump(alert_dict, f)

    async def save_pending_measurement(self, measurement: Measurement) -> None:
        """Save pending measurement with status tracking.

        Enforces maximum pending files limit by evicting oldest files if needed.
        """
        # Check and enforce limit before saving
        current_count = self._count_files(self.pending_measurement_path)
        if current_count >= self.max_pending_measurements:
            self._evict_oldest_files(
                self.pending_measurement_path,
                self.max_pending_measurements
            )

        filename = f"{measurement.device_id}_{human_readable_time(measurement.timestamp)}.json"
        path = os.path.join(self.pending_measurement_path, filename)
        if isinstance(measurement.timestamp, datetime):
            measurement.timestamp = measurement.timestamp.timestamp()

        data = measurement.to_dict()
        data["processing_status"] = Status.PENDING.value

        with open(path, 'w') as f:
            json.dump(data, f)

    async def save_pending_alert(self, alert: Alert) -> None:
        """Save pending alert with UUID and status tracking.

        Enforces maximum pending files limit by evicting oldest files if needed.
        """
        # Check and enforce limit before saving
        current_count = self._count_files(self.pending_alert_path)
        if current_count >= self.max_pending_alerts:
            self._evict_oldest_files(
                self.pending_alert_path,
                self.max_pending_alerts
            )

        filename = f"{alert.id}.json"
        path = os.path.join(self.pending_alert_path, filename)

        alert_dict = alert.to_dict()
        alert_dict['id'] = str(alert_dict['id'])
        if alert_dict.get('parent_alert_id'):
            alert_dict['parent_alert_id'] = str(alert_dict['parent_alert_id'])
        alert_dict["processing_status"] = Status.PENDING.value

        with open(path, 'w') as f:
            json.dump(alert_dict, f)

    async def get_pending_measurements(self) -> Dict[str, Measurement]:
        """Retrieve all pending measurements."""
        pending = {}
        pending_dir = os.path.join(self.pending_measurement_path)

        if not os.path.exists(pending_dir):
            return pending

        process_file_count = 0
        for filename in os.listdir(pending_dir):
            if process_file_count > 10:
                break
            path = os.path.join(pending_dir, filename)
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    pending[path] = Measurement.from_dict(data)
                    process_file_count += 1
            except Exception as e:
                logger.error(f"Error reading pending measurement {filename}: {e}")
                continue

        return pending

    async def get_pending_alerts(self) -> Dict[str, Alert]:
        """Retrieve all pending alerts with UUID handling."""
        pending = {}
        pending_dir = os.path.join(self.pending_alert_path)

        if not os.path.exists(pending_dir):
            return pending

        process_file_count = 0
        for filename in os.listdir(pending_dir):
            if process_file_count > 10:
                break
            path = os.path.join(pending_dir, filename)
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    data = preprocess_data(data=data)
                    pending[path] = Alert.from_dict(data)
                    process_file_count += 1
            except Exception as e:
                logger.error(f"Error reading pending alert {filename}: {e}")
                continue

        return pending

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def remove_pending_data(self, file_path: str) -> None:
        """Remove pending data file with retry mechanism."""
        try:
            os.remove(file_path)
            logger.info(f"Successfully removed pending file: {file_path}")
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except PermissionError:
            logger.error(f"Permission denied: Cannot delete {file_path}")
        except Exception as e:
            logger.error(f"Error removing pending file {file_path}: {e}")
            raise

def preprocess_data(data):
    # Traverse the dictionary and replace "None" with None
    for key, value in data.items():
        if value == "None":  # Replace string "None" with None
            data[key] = None
        elif isinstance(value, dict):  # Recurse into nested dictionaries
            preprocess_data(value)
        elif isinstance(value, list):  # Process lists of dictionaries
            for item in value:
                if isinstance(item, dict):
                    preprocess_data(item)
    return data
