from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
import logging

from dataclasses_json import dataclass_json

from src.models.alert import AlertSeverity, Alert
from src.models.modbus_types import Endianness, RegisterType, ConnectionType, FramerType, DataType
from src.models.mqtt_trigger import (
    MQTTTrigger, WriteOperation, CompositeCondition
)

logger = logging.getLogger(__name__)


def parse_enum(enum_class, value):
    """Safely parse a string into an Enum value."""
    try:
        return enum_class(value)
    except ValueError:
        raise ValueError(f"Invalid value '{value}' for enum {enum_class.__name__}")

@dataclass_json
@dataclass(frozen=True)
class Threshold:
    value: Any
    message: str
    severity: AlertSeverity = AlertSeverity.INFO
    send_resolution_alert: bool = False

def create_thresholds(thresholds: List[dict]) -> List[Threshold]:
    """Create a list of Threshold objects from dictionaries."""
    return [Threshold(**t) for t in thresholds]

class AlertHistoryMetadata:
    def __init__(self):
        self.Triggered: bool = False
        self.Alert: Optional[Alert] = None


@dataclass_json
@dataclass
class Delta:
    value: float
    message: str
    severity: AlertSeverity = AlertSeverity.MEDIUM

def create_delta(delta: dict) -> List[Delta]:
    """Create a Delta object from a dictionary."""
    return [Delta(**t) for t in delta]


@dataclass_json
@dataclass
class Register:
    address: int
    count: int
    data_type: DataType
    field_name: str
    label: str
    unit: str
    register_type: RegisterType = RegisterType.HoldingRegister
    multiplication_factor: float = None
    upper_threshold: Optional[List[Threshold]] = None
    lower_threshold: Optional[List[Threshold]] = None
    delta: Optional[List[Delta]] = None
    AlertHistory: Optional[Dict[Threshold, AlertHistoryMetadata]] = None

def create_register(register_data: dict) -> Register:
    """Create a Register object, safely handling enum conversions."""
    register_data['data_type'] = parse_enum(DataType, register_data['data_type'])
    register_data['register_type'] = parse_enum(RegisterType, register_data.get('register_type', RegisterType.HoldingRegister.value))

    if 'upper_threshold' in register_data and register_data['upper_threshold'] is not None:
        register_data['upper_threshold'] = create_thresholds(register_data['upper_threshold'])
    if 'lower_threshold' in register_data and register_data['lower_threshold'] is not None:
        register_data['lower_threshold'] = create_thresholds(register_data['lower_threshold'])
    if 'delta' in register_data and register_data['delta'] is not None:
        register_data['delta'] = create_delta(register_data['delta'])

    reg = Register(**register_data)
    reg.AlertHistory = {}
    return reg

@dataclass_json
@dataclass
class ModbusClient:
    id: str
    type: str
    registers: List[Register]
    previous_values: Dict[str, Any] # {field_name: value}
    mqtt_triggers: Optional[List[MQTTTrigger]] = None
    active_monitors: Dict[str, Any] = field(default_factory=dict)  # Store running monitors

    # Optional label for display purposes
    label: Optional[str] = None

    # Polling configuration
    polling_interval: int = 60  # DEPRECATED: Use http_interval instead. Kept for backward compatibility.
    unit_id: int = 1
    endianness: Endianness = Endianness.BIG

    # MQTT configuration - unified with HTTP (no separate clients needed)
    mqtt_enabled: bool = True  # Whether to send data to MQTT
    mqtt_topic: Optional[str] = None  # Custom MQTT topic (uses default if not set)
    mqtt_interval: Optional[int] = None  # MQTT publish interval in seconds (uses polling_interval if not set)

    # HTTP configuration
    http_enabled: bool = True  # Whether to send data to HTTP API
    http_interval: Optional[int] = None  # HTTP publish interval in seconds (uses polling_interval if not set)

    # Calculated field - actual Modbus read interval (set by create_modbus_client)
    modbus_read_interval: Optional[int] = None  # min(mqtt_interval, http_interval) for enabled protocols

    # Legacy fields (for backward compatibility)
    mqtt_preferred: bool = False  # Deprecated: use mqtt_enabled + http_enabled
    mqtt_preferred_topic: Optional[str] = None  # Deprecated: use mqtt_topic

    # Gateway options
    expose_via_tcp: bool = False  # Whether to expose this client's registers via TCP gateway
    use_cache: bool = True  # Whether to use cached values (for MQTT/HTTP consolidation)

    # Meter registry options (for auto-generating registers)
    meter_model: Optional[str] = None  # Meter model ID from meter_registry.yaml
    profile: Optional[str] = None  # Client profile from meter_registry.yaml
    target_table: Optional[str] = None  # Target DB table (distribution, substation, water)


def create_modbus_client(client_data: dict, meter_registry=None) -> ModbusClient:
    """Create a ModbusClient object, safely handling enum conversions.

    Args:
        client_data: Client configuration dictionary
        meter_registry: Optional MeterRegistry instance for auto-generating registers

    Returns:
        ModbusClient instance
    """
    # Check if we need to auto-generate registers from meter registry
    meter_model = client_data.get('meter_model')
    profile = client_data.get('profile')

    if meter_model and not client_data.get('registers'):
        # Auto-generate registers from meter registry
        if meter_registry is None:
            try:
                from src.services.meter_registry import get_meter_registry
                meter_registry = get_meter_registry()
            except Exception as e:
                logger.warning(f"Could not load meter registry: {e}")
                meter_registry = None

        if meter_registry:
            meter = meter_registry.get_meter(meter_model)
            if meter:
                # Use meter's default endianness if not specified
                if 'endianness' not in client_data:
                    client_data['endianness'] = meter.defaults.get('endianness', 'big')

                # Get target table for DB field mapping
                target_table = client_data.get('target_table')
                if not target_table and profile:
                    profile_obj = meter_registry.get_profile(profile)
                    if profile_obj:
                        target_table = profile_obj.target_table

                # Generate registers
                registers = meter_registry.generate_client_registers(
                    meter_id=meter_model,
                    profile_name=profile,
                    register_names=client_data.get('register_names'),
                    target_table=target_table,
                    custom_registers=client_data.get('custom_registers'),
                )
                client_data['registers'] = registers
                logger.info(f"Auto-generated {len(registers)} registers for client '{client_data.get('id')}' using meter '{meter_model}'")
            else:
                logger.warning(f"Unknown meter model '{meter_model}' for client '{client_data.get('id')}'")

    # Parse endianness
    client_data['endianness'] = parse_enum(Endianness, client_data.get('endianness', Endianness.BIG.value))

    # Parse registers
    registers_def = client_data.get('registers')
    if registers_def:
        client_data['registers'] = [create_register(reg) if isinstance(reg, dict) else reg for reg in registers_def]
    else:
        client_data['registers'] = []

    # Initialize previous values
    client_data['previous_values'] = {}

    # Handle legacy mqtt_preferred field
    if client_data.get('mqtt_preferred'):
        # Legacy mode: mqtt_preferred=true means MQTT only, no HTTP
        client_data['mqtt_enabled'] = True
        client_data['http_enabled'] = False
        if client_data.get('mqtt_preferred_topic'):
            client_data['mqtt_topic'] = client_data['mqtt_preferred_topic']

    # Convert MQTT triggers from dict to objects if present
    if 'mqtt_triggers' in client_data:
        triggers = []
        for trigger_data in client_data['mqtt_triggers']:
            # Convert write operations
            if 'on_true_actions' in trigger_data:
                write_ops = []
                for op in trigger_data['on_true_actions'].get('write_operations', []):
                    write_ops.append(WriteOperation.from_dict(op))
                trigger_data['on_true_actions']['write_operations'] = write_ops

            if 'on_false_actions' in trigger_data:
                write_ops = []
                for op in trigger_data['on_false_actions'].get('write_operations', []):
                    write_ops.append(WriteOperation.from_dict(op))
                trigger_data['on_false_actions']['write_operations'] = write_ops

            # Convert conditions
            if 'initial_condition' in trigger_data:
                trigger_data['initial_condition'] = CompositeCondition.from_dict(trigger_data['initial_condition'])
            if 'monitoring_condition' in trigger_data:
                trigger_data['monitoring_condition'] = CompositeCondition.from_dict(trigger_data['monitoring_condition'])

            # Convert the full trigger
            triggers.append(MQTTTrigger.from_dict(trigger_data))
        client_data['mqtt_triggers'] = triggers

    # Remove fields that aren't part of ModbusClient dataclass
    fields_to_remove = ['register_names', 'custom_registers']
    for field_name in fields_to_remove:
        client_data.pop(field_name, None)

    # Calculate effective intervals with backward compatibility
    polling_interval = client_data.get('polling_interval', 60)

    # http_interval defaults to polling_interval if not specified
    if client_data.get('http_interval') is None:
        client_data['http_interval'] = polling_interval

    # mqtt_interval defaults to polling_interval if not specified
    if client_data.get('mqtt_interval') is None:
        client_data['mqtt_interval'] = polling_interval

    # Calculate modbus_read_interval = min of enabled protocols
    http_enabled = client_data.get('http_enabled', True)
    mqtt_enabled = client_data.get('mqtt_enabled', True)
    http_interval = client_data['http_interval']
    mqtt_interval = client_data['mqtt_interval']

    if http_enabled and mqtt_enabled:
        modbus_read_interval = min(http_interval, mqtt_interval)
    elif http_enabled:
        modbus_read_interval = http_interval
    elif mqtt_enabled:
        modbus_read_interval = mqtt_interval
    else:
        # Neither enabled - use polling_interval as fallback
        modbus_read_interval = polling_interval

    client_data['modbus_read_interval'] = modbus_read_interval

    logger.debug(f"Client '{client_data.get('id')}': modbus_read_interval={modbus_read_interval}s "
                 f"(http={http_interval}s/{http_enabled}, mqtt={mqtt_interval}s/{mqtt_enabled})")

    return ModbusClient(**client_data)


@dataclass_json
@dataclass
class ModbusConnection:
    id: str
    label: str
    connection_type: ConnectionType
    framer: FramerType
    clients: List[ModbusClient]

    timeout: int = 3
    retries: int = 3
    reconnect_delay: float = 0.1
    # TCP specific fields
    host: Optional[str] = None
    port: Any = None
    # Serial specific fields
    baud_rate: Optional[int] = None
    parity: Optional[str] = None
    stop_bits: Optional[int] = None
    bytesize: Optional[int] = None
    # Multi-connection support: virtual unit ID offset for TCP gateway
    # This allows multiple connections with overlapping unit IDs
    # virtual_unit_id = physical_unit_id + virtual_unit_id_offset
    virtual_unit_id_offset: int = 0

    # Connection behavior options
    # keep_connection_open: If True, don't disconnect after each device read.
    # For direct RS485/serial connections, this eliminates connect/disconnect overhead.
    # For TCP gateways (e.g., Waveshare), set to False to avoid response buffering issues.
    keep_connection_open: bool = False


def create_modbus_connection(connection_data: dict, meter_registry=None) -> ModbusConnection:
    """Create a ModbusConnection object, safely handling enum conversions and nested structures.

    Args:
        connection_data: Connection configuration dictionary
        meter_registry: Optional MeterRegistry instance for auto-generating registers

    Returns:
        ModbusConnection instance
    """
    # Safely parse enum values
    _validate_modbbus_connection_config(connection_data)
    connection_data['connection_type'] = parse_enum(ConnectionType, connection_data['connection_type'])

    # Set default framer if not specified (socket for TCP, rtu for serial)
    if 'framer' not in connection_data or not connection_data['framer']:
        if connection_data['connection_type'] == ConnectionType.TCP:
            connection_data['framer'] = FramerType.SOCKET
        else:
            connection_data['framer'] = FramerType.RTU
    else:
        connection_data['framer'] = parse_enum(FramerType, connection_data['framer'])

    # Load meter registry if needed and not provided
    if meter_registry is None:
        # Check if any client uses meter_model
        needs_registry = any(
            client.get('meter_model') for client in connection_data.get('clients', [])
        )
        if needs_registry:
            try:
                from src.services.meter_registry import get_meter_registry
                meter_registry = get_meter_registry()
            except Exception as e:
                logger.warning(f"Could not load meter registry: {e}")

    # Parse the clients list into ModbusClient objects
    connection_data['clients'] = [
        create_modbus_client(client, meter_registry) for client in connection_data['clients']
    ]

    # Return a ModbusConnection object
    return ModbusConnection(**connection_data)

def _validate_modbbus_connection_config(config: dict) -> None:
    connection_type = config.get('connection_type')
    if not connection_type:
        raise ValueError(f"No connection type specified in config for label: {config.get('label')}")
    if ConnectionType(connection_type) != ConnectionType.TCP and ConnectionType(connection_type) != ConnectionType.SERIAL:
        raise ValueError(f"Invalid connection type specified in config for label: {config.get('label')}")
    if ConnectionType(connection_type) == ConnectionType.TCP:
        if not config.get('host') or not config.get('port'):
            raise ValueError(f"No host or port specified in config for label: {config.get('label')}")
    if ConnectionType(connection_type) == ConnectionType.SERIAL:
        if not config.get('baud_rate') or not config.get('port'):
            raise ValueError(f"No baud_rate or port specified in config for label: {config.get('label')}")