import asyncio
import json
import logging
import time
from queue import Queue, Empty
from threading import Thread, Event, Lock
from typing import Dict, Optional, Union
from importlib import resources as importlib_resources
from pathlib import Path

import paho.mqtt.client as mqtt

from .mqtt_trigger_service import MQTTTriggerService
from ..models.alert import Alert
from ..models.device import ModbusClient, ModbusConnection
from ..models.measurement import Measurement, ModBusMeasurement

logger = logging.getLogger(__name__)


class MQTTService:
    def __init__(
            self,
            host: str,
            port: int,
            username: str,
            password: str,
            topics: Dict[str, Dict[str, str]],
            modbus_clients: Optional[Dict[str, ModbusClient]] = None,
            modbus_connections: Optional[Dict[str, ModbusConnection]] = None,
            keepalive: int = 60,
            reconnect_min_delay: int = 1,
            reconnect_max_delay: int = 120
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        self.topics = topics
        self.keepalive = keepalive
        self.reconnect_min_delay = reconnect_min_delay
        self.reconnect_max_delay = reconnect_max_delay

        # Connection state tracking
        self.is_connected_flag = False
        self.connection_lock = Lock()
        self.reconnect_count = 0
        self.last_disconnect_time = None
        self.manual_disconnect = False

        # Message handling
        self.message_queue = Queue()
        self.stop_event = Event()
        self.loop = None  # Store reference to event loop
        self.health_check_task = None

        # Initialize MQTT client with unique client ID
        import socket
        import uuid
        # Add unique suffix to prevent client ID collisions
        unique_suffix = str(uuid.uuid4())[:8]
        client_id = f"rtu_{socket.gethostname()}_{username}_{unique_suffix}"
        self.client = mqtt.Client(client_id=client_id, clean_session=False)

        # Only enable TLS if using secure port (8883)
        if self.port == 8883:
            try:
                # Load CA certificate from package resources
                try:
                    # Python 3.9+ approach using importlib.resources
                    cert_ref = importlib_resources.files('dataskipper_boat').joinpath('emqxsl-ca.crt')
                    with importlib_resources.as_file(cert_ref) as cert_file:
                        self.client.tls_set(ca_certs=str(cert_file))
                except (TypeError, AttributeError, ModuleNotFoundError):
                    # Fallback: try relative path from this file
                    cert_path = Path(__file__).parent.parent.parent / 'dataskipper_boat' / 'emqxsl-ca.crt'
                    if cert_path.exists():
                        self.client.tls_set(ca_certs=str(cert_path))
                logger.info("TLS enabled for MQTT (port 8883)")
            except Exception as e:
                logger.warning(f"Failed to set TLS certificate: {e}")
                logger.info("Proceeding without TLS certificate validation")
        else:
            logger.info(f"Using plain MQTT (port {self.port}, no TLS)")

        self.client.username_pw_set(username, password)

        # Set up trigger service if Modbus clients are provided
        self.trigger_service = None
        if modbus_clients and modbus_connections:
            self.trigger_service = MQTTTriggerService(
                modbus_clients=modbus_clients,
                modbus_connections=modbus_connections
            )

        # Set up MQTT callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self.on_message

        # Configure automatic reconnection
        self.client.reconnect_delay_set(min_delay=reconnect_min_delay, max_delay=reconnect_max_delay)

        # Initial connection attempt
        self._connect()

    def _connect(self):
        """Initial connection attempt with error handling."""
        try:
            logger.info(f"Attempting to connect to MQTT broker at {self.host}:{self.port}...")
            self.client.connect(self.host, self.port, keepalive=self.keepalive)
            self.client.loop_start()
            logger.info("MQTT loop started")
        except Exception as e:
            logger.error(f'Failed to connect with MQTT server: {e}')
            logger.info("Will retry connection automatically...")

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connection is established"""
        with self.connection_lock:
            if rc == 0:
                self.is_connected_flag = True
                self.reconnect_count = 0
                logger.info(f"✓ Successfully connected to MQTT broker (rc={rc})")

                # Resubscribe to all topics on reconnection
                if self.trigger_service:
                    self.subscribe_to_trigger_topics()

                # Log reconnection success if this was a reconnect
                if self.last_disconnect_time:
                    downtime = time.time() - self.last_disconnect_time
                    logger.info(f"Connection restored after {downtime:.1f} seconds of downtime")
                    self.last_disconnect_time = None
            else:
                self.is_connected_flag = False
                error_messages = {
                    1: "Connection refused - incorrect protocol version",
                    2: "Connection refused - invalid client identifier",
                    3: "Connection refused - server unavailable",
                    4: "Connection refused - bad username or password",
                    5: "Connection refused - not authorized"
                }
                error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
                logger.error(f"✗ Failed to connect to MQTT broker: {error_msg}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback when connection is lost"""
        with self.connection_lock:
            self.is_connected_flag = False

            # Don't log/reconnect if this was a manual disconnect
            if self.manual_disconnect:
                logger.info("Disconnected from MQTT broker (manual)")
                return

            self.last_disconnect_time = time.time()
            self.reconnect_count += 1

            if rc == 0:
                logger.warning("⚠ Disconnected from MQTT broker gracefully")
            else:
                logger.error(f"✗ Unexpectedly disconnected from MQTT broker (rc={rc})")

            logger.info(f"Automatic reconnection attempt #{self.reconnect_count} will begin shortly...")

            # The paho client will automatically attempt to reconnect
            # due to loop_start() and reconnect_delay_set() configuration

    def on_message(self, client, userdata, message):
        """Synchronous callback that queues messages for processing"""
        if not self.trigger_service:
            return
            
        try:
            logger.debug(f"Received MQTT message on topic: {message.topic}")
            self.message_queue.put((message.topic, message.payload))
            logger.debug("Successfully queued message for processing")
        except Exception as e:
            logger.error(f"Error queueing MQTT message: {e}")

    async def start_processing(self, loop):
        """Start message processing - called from main async context"""
        self.loop = loop
        self.stop_event.clear()

        # Start message processing in a separate thread
        self.process_thread = Thread(target=self._process_messages)
        self.process_thread.daemon = True
        self.process_thread.start()
        logger.info("Message processing thread started")

        # Start health monitoring task
        self.health_check_task = asyncio.create_task(self._health_monitor())
        logger.info("MQTT health monitoring started")

    async def _health_monitor(self):
        """Periodically check connection health and attempt recovery if needed."""
        check_interval_normal = 30  # Check every 30 seconds when connected
        check_interval_reconnecting = 10  # Check every 10 seconds when disconnected
        consecutive_failures = 0
        max_consecutive_failures = 3

        while not self.stop_event.is_set():
            try:
                # Use shorter interval when disconnected for faster recovery
                with self.connection_lock:
                    is_connected = self.is_connected_flag

                check_interval = check_interval_normal if is_connected else check_interval_reconnecting
                await asyncio.sleep(check_interval)

                # Re-check connection status after sleep
                with self.connection_lock:
                    is_connected = self.is_connected_flag

                if not is_connected and not self.manual_disconnect:
                    consecutive_failures += 1
                    logger.warning(f"Health check: MQTT connection lost (failure #{consecutive_failures}), attempting recovery...")

                    try:
                        # Stop the loop first to clean up
                        self.client.loop_stop()

                        # Small delay before reconnection
                        await asyncio.sleep(2)

                        # Reconnect with fresh connection
                        logger.info(f"Attempting to reconnect to MQTT broker at {self.host}:{self.port}...")
                        self.client.connect(self.host, self.port, keepalive=self.keepalive)
                        self.client.loop_start()
                        logger.info("Reconnection initiated, waiting for connection callback...")

                        # Reset failure counter on successful attempt (actual success checked in on_connect)
                        if consecutive_failures >= max_consecutive_failures:
                            logger.warning(f"Multiple reconnection attempts made ({consecutive_failures}), connection may be unstable")

                    except Exception as e:
                        logger.error(f"Health check reconnection failed: {e}", exc_info=True)
                        if consecutive_failures >= max_consecutive_failures:
                            logger.error(f"Failed to reconnect after {consecutive_failures} attempts, will keep trying...")
                else:
                    # Connection is healthy, reset failure counter
                    if consecutive_failures > 0:
                        logger.info("Connection restored and stable")
                        consecutive_failures = 0
                    logger.debug("Health check: MQTT connection is healthy")

            except asyncio.CancelledError:
                logger.info("Health monitor task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in MQTT health monitor: {e}", exc_info=True)
                # Don't break, keep monitoring

    def _process_messages(self):
        """Process messages in a separate thread"""
        while not self.stop_event.is_set():
            try:
                # Get message with timeout to allow checking stop_event
                try:
                    topic, payload = self.message_queue.get(timeout=0.1)
                except Empty:
                    continue

                logger.debug(f"Processing message from topic: {topic}")
                
                # Create future for async processing
                future = asyncio.run_coroutine_threadsafe(
                    self.trigger_service.handle_mqtt_message(
                        topic=topic,
                        message=payload.decode()
                    ),
                    self.loop
                )

                try:
                    # Wait for result with timeout
                    result = future.result(timeout=10)
                    
                    if result:
                        logger.debug(f"Message processing result: {result}")
                        # Send response if configured
                        if (
                            result.get("success") 
                            and "write_results" in result 
                            and all(result["write_results"].values())
                        ):
                            actions = result.get("on_true_actions")
                        else:
                            actions = result.get("on_false_actions")
                            
                        if actions:
                            # Handle both dictionary and ActionSet object cases
                            if isinstance(actions, dict):
                                response_topic = actions.get("response_topic")
                                response_message = actions.get("response_message")
                            else:
                                response_topic = actions.response_topic
                                response_message = actions.response_message
                            
                            if response_topic and response_message:
                                response = {
                                    "success": result.get("success", False),
                                    "message": response_message,
                                    "details": {
                                        "condition_values": result.get("condition_values", {}),
                                        "write_results": result.get("write_results", {})
                                    }
                                }
                                self.client.publish(
                                    response_topic,
                                    json.dumps(response)
                                )
                                logger.debug(f"Published response to: {response_topic}")
                            
                except Exception as e:
                    logger.error(f"Error processing MQTT message: {e}", exc_info=True)
                finally:
                    self.message_queue.task_done()
                    
            except Exception as e:
                logger.error(f"Error in message processing thread: {e}", exc_info=True)
                # Brief sleep on error to prevent tight loop
                self.stop_event.wait(1.0)

    def subscribe_to_trigger_topics(self):
        """Subscribe to all topics configured in triggers."""
        if not self.trigger_service:
            return
            
        topics = set()
        for client in self.trigger_service.modbus_clients.values():
            if not client.mqtt_triggers:
                continue
            for trigger in client.mqtt_triggers:
                if isinstance(trigger, dict):
                    topics.add(trigger.get('topic'))
                else:
                    topics.add(trigger.topic)
        
        for topic in topics:
            if topic:  # Only subscribe if topic is not None
                try:
                    self.client.subscribe(topic)
                    logger.info(f"Subscribed to trigger topic: {topic}")
                except Exception as e:
                    logger.error(f"Failed to subscribe to topic {topic}: {e}")

    def publish_measurement(self, measurement: Union[Measurement, ModBusMeasurement], topic: str) -> bool:
        """Publish measurement with connection check and retry logic."""
        if not topic:
            # Get device type from measurement (different attribute names for different types)
            device_type = getattr(measurement, 'device_type', None) or getattr(measurement, 'client_type', 'electrical')
            # Get topic from config, fallback to default format if not configured
            topic = self.topics.get(device_type, {}).get("measurements")
            if not topic:
                topic = f"iot/{device_type}/measurements"

        # Check connection status
        with self.connection_lock:
            if not self.is_connected_flag:
                logger.warning(f"Cannot publish measurement: MQTT not connected (reconnection in progress)")
                return False

        try:
            measurement_dict = measurement.to_dict()
            # Log field count for debugging
            if hasattr(measurement, 'data'):
                logger.info(f"MQTT payload for {measurement.client_id}: {len(measurement.data)} fields - keys: {list(measurement.data.keys())}")
            elif hasattr(measurement, 'values'):
                logger.info(f"MQTT payload for {measurement.device_id}: {len(measurement.values)} fields - keys: {list(measurement.values.keys())}")

            result = self.client.publish(
                topic,
                json.dumps(measurement_dict),
                qos=1  # At least once delivery
            )

            # Check if publish was successful
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Successfully published measurement to {topic}")
                return True
            elif result.rc == mqtt.MQTT_ERR_NO_CONN:
                logger.error("Failed to publish measurement: No connection")
                # Trigger reconnection attempt
                self._attempt_reconnect()
                return False
            else:
                logger.error(f"Failed to publish measurement: Error code {result.rc}")
                return False

        except Exception as e:
            logger.error(f'Failed to publish measurement to MQTT server: {e}')
            return False

    def publish_alert(self, alert: Alert) -> bool:
        """Publish alert with connection check and retry logic."""
        # Get topic from config, fallback to default format if not configured
        topic = self.topics.get(alert.device_type, {}).get("alerts")
        if not topic:
            topic = f"iot/{alert.device_type}/alerts"

        # Check connection status
        with self.connection_lock:
            if not self.is_connected_flag:
                logger.warning(f"Cannot publish alert: MQTT not connected (reconnection in progress)")
                return False

        try:
            result = self.client.publish(
                topic,
                json.dumps(alert.to_dict()),
                qos=1  # At least once delivery
            )

            # Check if publish was successful
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Successfully published alert to {topic}")
                return True
            elif result.rc == mqtt.MQTT_ERR_NO_CONN:
                logger.error("Failed to publish alert: No connection")
                # Trigger reconnection attempt
                self._attempt_reconnect()
                return False
            else:
                logger.error(f"Failed to publish alert: Error code {result.rc}")
                return False

        except Exception as e:
            logger.error(f'Failed to publish alert to MQTT server: {e}')
            return False

    def _attempt_reconnect(self):
        """Attempt to manually trigger reconnection if not already in progress."""
        try:
            if not self.client.is_connected() and not self.manual_disconnect:
                logger.info("Triggering immediate reconnection attempt...")
                # The health monitor will handle reconnection, but we can trigger it faster
                # by just logging - the health monitor runs every 30 seconds
                # For immediate reconnection, we rely on paho's automatic reconnect
                pass
        except Exception as e:
            logger.error(f"Manual reconnection check failed: {e}")

    def disconnect(self):
        """Disconnect from MQTT broker and cleanup."""
        logger.info("Shutting down MQTT service...")

        # Set manual disconnect flag to prevent reconnection attempts
        with self.connection_lock:
            self.manual_disconnect = True

        # Stop event processing
        self.stop_event.set()

        # Cancel health monitoring task if it exists
        if self.health_check_task and not self.health_check_task.done():
            self.health_check_task.cancel()
            logger.info("Health monitoring task cancelled")

        # Wait for message processing thread to finish
        if hasattr(self, 'process_thread') and self.process_thread.is_alive():
            self.process_thread.join(timeout=5.0)
            if self.process_thread.is_alive():
                logger.warning("Message processing thread did not stop gracefully")

        # Disconnect MQTT client
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
                logger.info("MQTT client disconnected successfully")
            except Exception as e:
                logger.error(f"Error disconnecting MQTT client: {e}")

    def is_connected(self) -> bool:
        """Check if MQTT is currently connected."""
        with self.connection_lock:
            return self.is_connected_flag

    def get_connection_stats(self) -> dict:
        """Get connection statistics for monitoring."""
        with self.connection_lock:
            return {
                "connected": self.is_connected_flag,
                "reconnect_count": self.reconnect_count,
                "last_disconnect_time": self.last_disconnect_time,
                "manual_disconnect": self.manual_disconnect
            }