import asyncio
import logging
import os
import sys
import time
import argparse
import random
from datetime import datetime
from pathlib import Path
from typing import List

import yaml

# Configure logging with separate handlers for stdout and stderr
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Handler for INFO and below (stdout)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(formatter)
stdout_handler.addFilter(lambda record: record.levelno <= logging.INFO)

# Handler for WARNING and above (stderr)
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.WARNING)
stderr_handler.setFormatter(formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers = []
root_logger.addHandler(stdout_handler)
root_logger.addHandler(stderr_handler)

logger = logging.getLogger(__name__)

from dataskipper_boat import __version__
from src.interfaces.modbus_client import IModbusClient
from src.models.alert import Alert
from src.models.device import ModbusConnection, create_modbus_connection, ModbusClient
from src.models.measurement import Measurement, ModBusMeasurement
from src.models.modbus_types import ConnectionType
from src.services.api_service import APIService
from src.services.modbus.serial_client import SerialModbusClient
from src.services.modbus.tcp_client import TcpModbusClient
from src.services.mqtt_service import MQTTService
from src.services.mqtt_trigger_service import MQTTTriggerService
from src.services.notifiers.discord_notifier import DiscordNotifier
from src.services.storage.file_storage import FileStorage
from src.utils.alert_checker import check_thresholds
from src.utils.common import async_api_handler

# Enhanced services
from src.services.aggregation_service import TimeWindowAggregator, AggregationService
from src.services.watchdog_service import SystemdWatchdog, ApplicationHealthMonitor
from src.services.performance_monitor import PerformanceMonitor, PollingRateMonitor

# Gateway and caching services
from src.services.register_cache import get_cache, RegisterCache, DEFAULT_CONNECTION_ID
from src.services.register_planner import get_planner
from src.services.modbus_tcp_server import get_tcp_server, ModbusTCPServer
from src.models.gateway_config import create_gateway_config, ModbusTCPGatewayConfig

# Optional web portal configuration
WEB_PORTAL_ENABLED = os.getenv('WEB_PORTAL_ENABLED', 'false').lower() == 'true'
WEB_PORTAL_PORT = int(os.getenv('WEB_PORTAL_PORT', '8080'))

# Test mode service (initialized later when web portal is enabled)
_test_mode_service = None

def get_test_mode_service():
    """Get the test mode service instance."""
    global _test_mode_service
    return _test_mode_service


class ModbusMonitor:
    def __init__(self, config_dir: str):
        # Initialize alert queue for background processing
        self._alert_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._alert_worker_task: asyncio.Task = None

        # Load configurations
        with open(Path(config_dir) / "slave_config.yaml") as f:
            connections_config = yaml.safe_load(f)

        with open(Path(config_dir) / "communication.yaml") as f:
            comm_config = yaml.safe_load(f)

        data_dir = os.getenv('DATA_DIR', os.path.join(os.path.expanduser('~'), "data"))

        # Initialize services
        storage = os.getenv('DATA_DIR', data_dir)
        self.storage = FileStorage(storage)

        # Initialize API and MQTT services first
        if comm_config.get('communication'):
            self.api_service = APIService(
                comm_config.get('communication')["api_endpoints"],
                comm_config.get('communication')["retry_config"]["max_retries"],
                comm_config.get('communication')["retry_config"]["interval"]
            )
            if comm_config.get('communication').get("mqtt_config"):
                mqtt_cfg = comm_config.get('communication')["mqtt_config"]
                self.mqtt_service = MQTTService(
                    mqtt_cfg["host"],
                    mqtt_cfg["port"],
                    mqtt_cfg["username"],
                    mqtt_cfg["password"],
                    mqtt_cfg.get("topics", {})
                )

        # Initialize notifiers
        self.notifiers = [
            DiscordNotifier(comm_config["discord_webhook_url"]),
        ]

        # Initialize Modbus clients
        self.connections: List[ModbusConnection] = []
        self.clients = {}

        for conn in connections_config.get("connections"):
            connection = create_modbus_connection(conn)
            self.connections.append(connection)

            if ConnectionType(connection.connection_type) == ConnectionType.TCP:
                client = TcpModbusClient(connection)
            elif ConnectionType(connection.connection_type) == ConnectionType.SERIAL:
                client = SerialModbusClient(connection)
            else:
                logger.warning(f"Invalid connection_type: {connection.connection_type} for connection: {connection.label}")
                continue

            self.clients[connection.id] = client

        if len(self.clients) == 0:
            raise ConnectionError("No connections")

        # Update MQTT service with clients after they are initialized
        if hasattr(self, 'mqtt_service'):
            self.mqtt_service.trigger_service = MQTTTriggerService(
                modbus_clients={client.id: client for connection in self.connections for client in connection.clients},
                modbus_connections={connection.id: connection for connection in self.connections}
            )
            self.mqtt_service.client.on_message = self.mqtt_service.on_message
            self.mqtt_service.subscribe_to_trigger_topics()

        # Initialize gateway and caching services
        self._init_gateway_services(comm_config)

        # Initialize enhanced services
        self._init_enhanced_services(comm_config)

    def _init_gateway_services(self, comm_config):
        """Initialize Modbus TCP gateway and caching services."""
        gateway_config = create_gateway_config(
            comm_config.get('communication', {}).get('modbus_tcp_gateway')
        )

        if gateway_config and gateway_config.enabled:
            self.cache = get_cache(ttl=gateway_config.cache_ttl)
            logger.info(f"Register cache initialized with TTL={gateway_config.cache_ttl}s")

            self.planner = get_planner(
                max_batch_size=gateway_config.max_batch_size,
                max_gap_size=gateway_config.max_gap_size
            )
            logger.info(f"Register planner initialized (batch_size={gateway_config.max_batch_size}, gap_size={gateway_config.max_gap_size})")

            unit_ids = set()
            for connection in self.connections:
                connection_id = connection.id
                offset = getattr(connection, 'virtual_unit_id_offset', 0)

                for client in connection.clients:
                    if getattr(client, 'expose_via_tcp', False):
                        physical_unit_id = client.unit_id
                        virtual_unit_id = physical_unit_id + offset

                        self.cache.register_virtual_unit(
                            virtual_unit_id=virtual_unit_id,
                            physical_unit_id=physical_unit_id,
                            connection_id=connection_id,
                            offset=offset
                        )

                        unit_ids.add(virtual_unit_id)
                        logger.info(f"Client {client.id}: physical unit {physical_unit_id} -> virtual unit {virtual_unit_id} (connection={connection_id}, offset={offset})")

            logger.info(f"Initializing TCP server with cache id={id(self.cache)}")
            self.tcp_server = get_tcp_server(
                cache=self.cache,
                port=gateway_config.port
            )
            logger.info(f"TCP server initialized, server.cache id={id(self.tcp_server.cache)}")
            for unit_id in unit_ids:
                self.tcp_server.add_unit_id(unit_id)

            self.gateway_config = gateway_config
            logger.info(f"Modbus TCP gateway configured on port {gateway_config.port}")
        else:
            cache_ttl = comm_config.get('communication', {}).get('cache_ttl', 180)
            self.cache = get_cache(ttl=cache_ttl)
            self.planner = get_planner()
            self.tcp_server = None
            self.gateway_config = None
            logger.info(f"Register cache initialized with TTL={cache_ttl}s (gateway disabled)")

    def _init_enhanced_services(self, comm_config):
        """Initialize aggregation and monitoring services."""
        if comm_config.get('communication', {}).get('aggregation_config', {}).get('enabled', False):
            agg_cfg = comm_config['communication']['aggregation_config']
            aggregator = TimeWindowAggregator(
                windows=agg_cfg.get('windows', [60, 300, 900, 3600]),
                max_buffer_size=agg_cfg.get('max_buffer_size', 3600)
            )
            self.aggregation_service = AggregationService(
                aggregator=aggregator,
                report_interval=agg_cfg.get('report_interval', 60),
                mqtt_service=self.mqtt_service if hasattr(self, 'mqtt_service') else None
            )
            logger.info("Aggregation service initialized")
        else:
            self.aggregation_service = None

        if comm_config.get('communication', {}).get('performance_config', {}).get('enabled', False):
            perf_cfg = comm_config['communication']['performance_config']
            self.performance_monitor = PerformanceMonitor(
                monitor_interval=perf_cfg.get('monitor_interval', 60),
                cpu_threshold=perf_cfg.get('cpu_threshold', 80.0),
                memory_threshold=perf_cfg.get('memory_threshold', 80.0),
                disk_threshold=perf_cfg.get('disk_threshold', 90.0)
            )
            logger.info("Performance monitor initialized")
        else:
            self.performance_monitor = None

        self.polling_monitor = PollingRateMonitor()
        self.watchdog = SystemdWatchdog()

        if comm_config.get('communication', {}).get('watchdog_config', {}).get('enabled', True):
            watchdog_cfg = comm_config.get('communication', {}).get('watchdog_config', {})
            self.health_monitor = ApplicationHealthMonitor(
                check_interval=watchdog_cfg.get('health_check_interval', 30),
                unhealthy_threshold=watchdog_cfg.get('unhealthy_threshold', 3)
            )
            self._register_health_checks()
            logger.info("Application health monitor initialized")
        else:
            self.health_monitor = None

    def _register_health_checks(self):
        """Register application health checks."""
        if not self.health_monitor:
            return

        async def check_mqtt_health():
            return hasattr(self, 'mqtt_service') and self.mqtt_service.is_connected()

        async def check_modbus_health():
            for client in self.clients.values():
                if hasattr(client, 'client') and client.client is not None:
                    if hasattr(client.client, 'connected') and client.client.connected:
                        return True
            if hasattr(self, 'cache') and self.cache:
                for client_id, entry in self.cache._client_cache.items():
                    if entry and hasattr(entry, 'timestamp'):
                        age = time.time() - entry.timestamp
                        if age < 300:
                            return True
            return False

        self.health_monitor.register_health_check('mqtt', check_mqtt_health)
        self.health_monitor.register_health_check('modbus', check_modbus_health)

    def queue_alerts(self, alerts: List[Alert]) -> None:
        """Queue alerts for background processing (non-blocking)."""
        for alert in alerts:
            try:
                self._alert_queue.put_nowait(alert)
            except asyncio.QueueFull:
                logger.warning(f"Alert queue full, dropping alert for {alert.device_id}")

    async def _alert_worker(self) -> None:
        """Background worker that processes alerts from the queue."""
        logger.info("Alert background worker started")
        while True:
            try:
                alert = await self._alert_queue.get()
                await self._process_single_alert(alert)
                self._alert_queue.task_done()
            except asyncio.CancelledError:
                logger.info("Alert worker cancelled, processing remaining alerts...")
                while not self._alert_queue.empty():
                    try:
                        alert = self._alert_queue.get_nowait()
                        await self._process_single_alert(alert)
                        self._alert_queue.task_done()
                    except asyncio.QueueEmpty:
                        break
                logger.info("Alert worker shutdown complete")
                break
            except Exception as e:
                logger.error(f"Error in alert worker: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _process_single_alert(self, alert: Alert) -> None:
        """Process a single alert through all configured channels."""
        try:
            await async_api_handler(
                first_method=self.api_service.send_alert,
                first_method_data=alert,
                result_of_first_method=False,
                second_method=self.storage.save_pending_alert,
                second_method_data=alert
            )
        except Exception as e:
            logger.error(f"Failed to send alert to API: {e}")

        try:
            if hasattr(self, 'mqtt_service') and self.mqtt_service.is_connected():
                self.mqtt_service.publish_alert(alert)
        except Exception as e:
            logger.error(f"Failed to send alert to MQTT: {e}")

        for notifier in self.notifiers:
            try:
                await notifier.send_alert(alert)
            except Exception as e:
                logger.error(f"Failed to send alert through notifier: {e}")

    async def process_alerts(self, alerts: List[Alert]) -> None:
        """Process and send alerts through all configured channels."""
        self.queue_alerts(alerts)

    async def monitor_client(self, reconnect_delay: float, modbus_client: ModbusClient, client: IModbusClient, connection_id: str = DEFAULT_CONNECTION_ID, initial_delay: float = 0.0) -> None:
        """Monitor a single Modbus client and its devices."""
        stagger_offset = initial_delay

        if stagger_offset > 0:
            logger.debug(f"{modbus_client.id}: Stagger offset {stagger_offset:.1f}s")
            await asyncio.sleep(stagger_offset)

        modbus_interval = getattr(modbus_client, 'modbus_read_interval', None) or modbus_client.polling_interval
        http_interval = getattr(modbus_client, 'http_interval', None) or modbus_client.polling_interval
        mqtt_interval = getattr(modbus_client, 'mqtt_interval', None) or modbus_client.polling_interval

        use_http = getattr(modbus_client, 'http_enabled', True)
        use_mqtt = getattr(modbus_client, 'mqtt_enabled', True)

        mqtt_topic = getattr(modbus_client, 'mqtt_topic', None) or getattr(modbus_client, 'mqtt_preferred_topic', None)
        if not mqtt_topic:
            mqtt_topic = f"iot/{modbus_client.type}/{modbus_client.id}"

        if getattr(modbus_client, 'mqtt_preferred', False):
            use_mqtt = True
            use_http = False

        logger.info(f"Starting client {modbus_client.id} (unit_id={modbus_client.unit_id}): "
                   f"modbus_read={modbus_interval}s, http={http_interval}s/{use_http}, mqtt={mqtt_interval}s/{use_mqtt}, topic={mqtt_topic}")

        use_batched = getattr(modbus_client, 'use_cache', True)
        last_http_publish = 0.0
        last_mqtt_publish = 0.0
        next_read_time = time.time()

        while True:
            try:
                test_svc = get_test_mode_service()
                if test_svc and test_svc.should_pause_polling():
                    logger.info(f"{modbus_client.id}: Polling PAUSED (test mode active)")
                    await asyncio.sleep(1)
                    continue

                start = datetime.now()
                current_time = time.time()

                if use_batched and hasattr(client, 'read_registers_batched'):
                    values = await client.read_registers_batched(modbus_client, use_cache=True, connection_id=connection_id)
                else:
                    values = await client.read_registers(modbus_client)

                if values:
                    logger.debug(f"Modbus read for {modbus_client.id}: {len(values)} values")

                    measurement = Measurement(
                        device_id=modbus_client.id,
                        device_type=modbus_client.type,
                        timestamp=int(current_time),
                        values=values,
                        target_table=getattr(modbus_client, 'target_table', None)
                    )

                    if self.aggregation_service:
                        self.aggregation_service.add_measurement(
                            device_id=modbus_client.id,
                            device_type=modbus_client.type,
                            timestamp=measurement.timestamp,
                            values=values
                        )

                    test_svc = get_test_mode_service()
                    test_mode_active = test_svc and test_svc.is_test_mode_active()

                    should_http = use_http and (current_time - last_http_publish >= http_interval)
                    if should_http and (not test_mode_active or test_svc.should_publish_http()):
                        try:
                            await async_api_handler(
                                first_method=self.api_service.send_measurement,
                                first_method_data=measurement,
                                result_of_first_method=False,
                                second_method=self.storage.save_pending_measurement,
                                second_method_data=measurement
                            )
                            last_http_publish = current_time
                            logger.debug(f"{modbus_client.id}: HTTP publish (interval={http_interval}s)")
                        except Exception as e:
                            logger.error(f"Failed to send measurement to API: {e}")
                    elif should_http and test_mode_active:
                        logger.debug(f"{modbus_client.id}: HTTP publish skipped (test mode)")
                        last_http_publish = current_time

                    should_mqtt = use_mqtt and (current_time - last_mqtt_publish >= mqtt_interval)
                    if should_mqtt and (not test_mode_active or test_svc.should_publish_mqtt()):
                        try:
                            if hasattr(self, 'mqtt_service') and self.mqtt_service.is_connected():
                                modbus_measurement = ModBusMeasurement(measurement)
                                self.mqtt_service.publish_measurement(modbus_measurement, mqtt_topic)
                                last_mqtt_publish = current_time
                                logger.debug(f"{modbus_client.id}: MQTT publish to {mqtt_topic}")
                        except Exception as e:
                            logger.error(f"Failed to send measurement to MQTT: {e}")
                    elif should_mqtt and test_mode_active:
                        logger.debug(f"{modbus_client.id}: MQTT publish skipped (test mode)")
                        last_mqtt_publish = current_time

                    alerts = []
                    previous_values = modbus_client.previous_values

                    for register in modbus_client.registers:
                        current_value = values[register.field_name]
                        previous_value = previous_values.get(register.field_name)

                        register_alerts = check_thresholds(
                            modbus_client.id,
                            modbus_client.type,
                            register,
                            current_value,
                            previous_value
                        )
                        alerts.extend(register_alerts)
                        modbus_client.previous_values[register.field_name] = current_value

                    if alerts:
                        if not test_mode_active or test_svc.should_process_alerts():
                            await self.process_alerts(alerts)
                        else:
                            logger.debug(f"{modbus_client.id}: {len(alerts)} alerts skipped (test mode)")

                end_time = datetime.now()
                diff = end_time - start

                if self.polling_monitor:
                    self.polling_monitor.record_poll(
                        modbus_client.id,
                        diff.total_seconds(),
                        modbus_interval
                    )

                next_read_time += modbus_interval
                sleep_time = next_read_time - time.time()
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                elif sleep_time < -modbus_interval:
                    logger.warning(f"{modbus_client.id}: read took {diff.total_seconds():.1f}s, resetting schedule")
                    next_read_time = time.time()

            except Exception as e:
                logger.error(f"Error monitoring client {modbus_client.id}: {e}", exc_info=True)
                await asyncio.sleep(reconnect_delay)

    async def start(self) -> None:
        """Start monitoring all Modbus connections."""
        tasks = []
        try:
            self._alert_worker_task = asyncio.create_task(self._alert_worker())
            tasks.append(self._alert_worker_task)
            logger.info("Background alert worker started")

            if self.tcp_server:
                logger.info(f"Starting Modbus TCP gateway on port {self.gateway_config.port}")
                tasks.append(asyncio.create_task(self.tcp_server.start_background()))

            if self.watchdog:
                tasks.append(asyncio.create_task(self.watchdog.start_keepalive()))

            if self.aggregation_service:
                tasks.append(asyncio.create_task(self.aggregation_service.start_reporting()))

            if self.performance_monitor:
                mqtt = self.mqtt_service if hasattr(self, 'mqtt_service') else None
                tasks.append(asyncio.create_task(self.performance_monitor.start_monitoring(mqtt)))

            if self.health_monitor:
                tasks.append(asyncio.create_task(self.health_monitor.start_monitoring()))

            client_index = 0
            stagger_delay = 0.5
            for connection in self.connections:
                client = self.clients[connection.id]
                for modbus_client in connection.clients:
                    read_interval = getattr(modbus_client, 'modbus_read_interval', None) or modbus_client.polling_interval
                    if read_interval:
                        initial_delay = client_index * stagger_delay
                        task = asyncio.create_task(
                            self.monitor_client(
                                connection.reconnect_delay,
                                modbus_client,
                                client,
                                connection_id=connection.id,
                                initial_delay=initial_delay
                            )
                        )
                        tasks.append(task)
                        client_index += 1

            task = asyncio.create_task(self.process_pending_measurements())
            tasks.append(task)
            task = asyncio.create_task(self.process_pending_alerts())
            tasks.append(task)
            task = asyncio.create_task(self.cleanup_cache_periodically())
            tasks.append(task)

            await asyncio.gather(*tasks)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, canceling tasks...")
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("All tasks canceled")

        finally:
            logger.info("Cleaning up resources...")
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await self.stop()

    async def stop(self) -> None:
        """Stop all services and Modbus connections."""
        logger.info("Stopping all services...")

        if self._alert_worker_task and not self._alert_worker_task.done():
            logger.info("Stopping alert worker...")
            self._alert_worker_task.cancel()
            try:
                await self._alert_worker_task
            except asyncio.CancelledError:
                pass
            logger.info("Alert worker stopped")

        if self.tcp_server:
            try:
                await self.tcp_server.stop()
            except Exception as e:
                logger.error(f"Error stopping TCP gateway: {e}")

        if self.watchdog:
            await self.watchdog.stop()
        if self.aggregation_service:
            await self.aggregation_service.stop()
        if self.performance_monitor:
            await self.performance_monitor.stop()
        if self.health_monitor:
            await self.health_monitor.stop()

        if hasattr(self, 'api_service') and self.api_service:
            try:
                await self.api_service.close()
            except Exception as e:
                logger.error(f"Error closing API service: {e}")

        if hasattr(self, 'mqtt_service') and self.mqtt_service:
            try:
                self.mqtt_service.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting MQTT service: {e}")

        for connection in self.connections:
            client = self.clients[connection.id]
            try:
                await client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting Modbus client {connection.id}: {e}")

    async def process_pending_measurements(self) -> None:
        while True:
            measurements = {}
            try:
                measurements = await self.storage.get_pending_measurements()
            except Exception as e:
                logger.error(f"Failed to get pending measurements: {e}")

            for file_name, measurement in measurements.items():
                sent = await self.api_service.send_measurement(measurement)
                if sent:
                    await self.storage.remove_pending_data(file_name)
                await asyncio.sleep(3)

            await asyncio.sleep(60)

    async def process_pending_alerts(self) -> None:
        while True:
            alerts = {}
            try:
                alerts = await self.storage.get_pending_alerts()
            except Exception as e:
                logger.error(f"Failed to get pending alerts: {e}")

            for file_name, alert in alerts.items():
                sent = await self.api_service.send_alert(alert)
                if sent:
                    await self.storage.remove_pending_data(file_name)
                await asyncio.sleep(5)

            await asyncio.sleep(60)

    async def cleanup_cache_periodically(self) -> None:
        """Periodically clean up expired cache entries."""
        while True:
            try:
                await asyncio.sleep(60)
                if self.cache:
                    self.cache.cleanup_expired()
                    stats = self.cache.get_stats()
                    logger.debug(f"Cache stats: {stats['register_entries']} registers, {stats['client_entries']} clients, {stats['hit_rate']}% hit rate")
            except Exception as e:
                logger.error(f"Error cleaning up cache: {e}")


async def run_web_portal(register_cache=None, modbus_clients=None, connections=None):
    """Run the web portal as part of the main process."""
    global _test_mode_service
    import uvicorn
    from src.web_portal.app import app, set_register_cache

    if register_cache:
        set_register_cache(register_cache)
        logger.info(f"Web portal: shared cache injected (id={id(register_cache)})")
    else:
        logger.warning("Web portal: No cache provided - device status will not work")

    try:
        from src.web_portal.app import init_test_mode_service
        from src.services.test_mode_service import get_test_mode_service as get_tms

        config_dir = os.getenv('CONFIG_DIR', os.path.join(os.path.expanduser('~'), "config"))
        _test_mode_service = get_tms(config_dir)

        if modbus_clients and connections:
            init_test_mode_service(modbus_clients, connections, register_cache)
            logger.info(f"Test mode service initialized with {len(modbus_clients)} clients")
        else:
            logger.warning("Test mode service: No Modbus references - live reads won't work")
    except Exception as e:
        logger.warning(f"Test mode service initialization failed: {e}")

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=WEB_PORTAL_PORT,
        log_level="warning",
        access_log=False
    )
    server = uvicorn.Server(config)
    await server.serve()


async def async_main():
    config_dir = os.getenv('CONFIG_DIR', os.path.join(os.path.expanduser('~'), "config"))
    monitor = ModbusMonitor(config_dir)

    tasks = []

    try:
        loop = asyncio.get_running_loop()

        if hasattr(monitor, 'mqtt_service'):
            await monitor.mqtt_service.start_processing(loop)

        if WEB_PORTAL_ENABLED:
            logger.info(f"Starting RTU Web Portal on port {WEB_PORTAL_PORT}")
            connections_dict = {conn.id: conn for conn in monitor.connections}
            portal_task = asyncio.create_task(run_web_portal(
                register_cache=monitor.cache,
                modbus_clients=monitor.clients,
                connections=connections_dict
            ))
            tasks.append(portal_task)

        monitor_task = asyncio.create_task(monitor.start())
        tasks.append(monitor_task)

        await asyncio.gather(*tasks)

    except KeyboardInterrupt:
        await monitor.stop()
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        logger.info("Shutdown complete")


def main():
    """Entry point for the console script."""
    parser = argparse.ArgumentParser(description='DataSkipper Boat - IEC61850/Modbus monitoring, control and data collection system')
    parser.add_argument('--version', '-v', action='version', version=f'dataskipper-boat {__version__}')

    args = parser.parse_args()

    asyncio.run(async_main())


if __name__ == "__main__":
    main()
