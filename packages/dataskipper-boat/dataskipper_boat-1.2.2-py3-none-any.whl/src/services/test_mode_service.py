"""
Test Mode Service for RTU Web Portal.

Provides a safe way for operators to test configurations without affecting
production data streams. Key features:

1. Test Mode Toggle - Switches to test_config directory, disables HTTP/MQTT publish
2. Auto-expiration - Test mode automatically ends after a configurable timeout
3. Live Register Inspector - Read specific registers on demand
4. Device Probe - Single-shot read from any device
5. Config Validation - Validate YAML configs before applying

Safety Guarantees:
- All operations are wrapped in try/except to prevent crashes
- Test mode state is stored in memory, not affecting main loop directly
- Main loop checks test_mode flag and adjusts behavior accordingly
- Auto-expiration ensures forgotten test sessions don't persist
"""

import asyncio
import logging
import os
import struct
import time
import yaml
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.utils.modbus_utils import get_unit_id_kwargs

logger = logging.getLogger(__name__)


# ==================== Data Type Conversion ====================

class DataType(Enum):
    """Supported data types for register interpretation."""
    UINT16 = "uint16"           # Unsigned 16-bit (raw register)
    INT16 = "int16"             # Signed 16-bit
    UINT32 = "uint32"           # Unsigned 32-bit (2 registers)
    INT32 = "int32"             # Signed 32-bit (2 registers)
    FLOAT32 = "float32"         # IEEE 754 float (2 registers)
    UINT64 = "uint64"           # Unsigned 64-bit (4 registers)
    INT64 = "int64"             # Signed 64-bit (4 registers)
    FLOAT64 = "float64"         # IEEE 754 double (4 registers)


class ByteOrder(Enum):
    """Byte ordering for multi-register values."""
    BIG_ENDIAN = "big"                    # AB CD (most common)
    LITTLE_ENDIAN = "little"              # CD AB
    BIG_ENDIAN_SWAP = "big_swap"          # BA DC (word swap)
    LITTLE_ENDIAN_SWAP = "little_swap"    # DC BA


def convert_registers(
    registers: List[int],
    data_type: DataType,
    byte_order: ByteOrder = ByteOrder.BIG_ENDIAN,
    scale: float = 1.0,
    offset: float = 0.0
) -> Union[int, float, List[Union[int, float]]]:
    """
    Convert raw 16-bit register values to a specific data type.

    Args:
        registers: List of raw 16-bit register values
        data_type: Target data type for interpretation
        byte_order: Byte ordering for multi-register values
        scale: Multiply result by this factor
        offset: Add this value after scaling

    Returns:
        Converted value(s) based on data type
    """
    if not registers:
        return []

    try:
        # Single register types
        if data_type == DataType.UINT16:
            return [(r & 0xFFFF) * scale + offset for r in registers]

        elif data_type == DataType.INT16:
            results = []
            for r in registers:
                val = r & 0xFFFF
                if val >= 0x8000:
                    val -= 0x10000
                results.append(val * scale + offset)
            return results

        # Two-register types (32-bit)
        elif data_type in (DataType.UINT32, DataType.INT32, DataType.FLOAT32):
            results = []
            for i in range(0, len(registers) - 1, 2):
                r1, r2 = registers[i], registers[i + 1]

                # Apply byte ordering
                if byte_order == ByteOrder.BIG_ENDIAN:
                    combined = (r1 << 16) | r2
                elif byte_order == ByteOrder.LITTLE_ENDIAN:
                    combined = (r2 << 16) | r1
                elif byte_order == ByteOrder.BIG_ENDIAN_SWAP:
                    # Swap bytes within each word
                    r1_swap = ((r1 & 0xFF) << 8) | ((r1 >> 8) & 0xFF)
                    r2_swap = ((r2 & 0xFF) << 8) | ((r2 >> 8) & 0xFF)
                    combined = (r1_swap << 16) | r2_swap
                else:  # LITTLE_ENDIAN_SWAP
                    r1_swap = ((r1 & 0xFF) << 8) | ((r1 >> 8) & 0xFF)
                    r2_swap = ((r2 & 0xFF) << 8) | ((r2 >> 8) & 0xFF)
                    combined = (r2_swap << 16) | r1_swap

                if data_type == DataType.UINT32:
                    results.append(combined * scale + offset)
                elif data_type == DataType.INT32:
                    if combined >= 0x80000000:
                        combined -= 0x100000000
                    results.append(combined * scale + offset)
                else:  # FLOAT32
                    packed = struct.pack('>I', combined)
                    val = struct.unpack('>f', packed)[0]
                    results.append(val * scale + offset)

            return results if len(results) > 1 else (results[0] if results else 0)

        # Four-register types (64-bit)
        elif data_type in (DataType.UINT64, DataType.INT64, DataType.FLOAT64):
            results = []
            for i in range(0, len(registers) - 3, 4):
                r1, r2, r3, r4 = registers[i:i+4]

                # Apply byte ordering (for 64-bit, treat as two 32-bit values)
                if byte_order == ByteOrder.BIG_ENDIAN:
                    combined = (r1 << 48) | (r2 << 32) | (r3 << 16) | r4
                elif byte_order == ByteOrder.LITTLE_ENDIAN:
                    combined = (r4 << 48) | (r3 << 32) | (r2 << 16) | r1
                elif byte_order == ByteOrder.BIG_ENDIAN_SWAP:
                    r1_s = ((r1 & 0xFF) << 8) | ((r1 >> 8) & 0xFF)
                    r2_s = ((r2 & 0xFF) << 8) | ((r2 >> 8) & 0xFF)
                    r3_s = ((r3 & 0xFF) << 8) | ((r3 >> 8) & 0xFF)
                    r4_s = ((r4 & 0xFF) << 8) | ((r4 >> 8) & 0xFF)
                    combined = (r1_s << 48) | (r2_s << 32) | (r3_s << 16) | r4_s
                else:  # LITTLE_ENDIAN_SWAP
                    r1_s = ((r1 & 0xFF) << 8) | ((r1 >> 8) & 0xFF)
                    r2_s = ((r2 & 0xFF) << 8) | ((r2 >> 8) & 0xFF)
                    r3_s = ((r3 & 0xFF) << 8) | ((r3 >> 8) & 0xFF)
                    r4_s = ((r4 & 0xFF) << 8) | ((r4 >> 8) & 0xFF)
                    combined = (r4_s << 48) | (r3_s << 32) | (r2_s << 16) | r1_s

                if data_type == DataType.UINT64:
                    results.append(combined * scale + offset)
                elif data_type == DataType.INT64:
                    if combined >= 0x8000000000000000:
                        combined -= 0x10000000000000000
                    results.append(combined * scale + offset)
                else:  # FLOAT64
                    packed = struct.pack('>Q', combined)
                    val = struct.unpack('>d', packed)[0]
                    results.append(val * scale + offset)

            return results if len(results) > 1 else (results[0] if results else 0)

        return registers  # Fallback - return raw values

    except Exception as e:
        logger.error(f"Error converting registers: {e}")
        return registers


def format_register_display(
    registers: List[int],
    start_address: int,
    data_type: str = "uint16",
    byte_order: str = "big",
    scale: float = 1.0,
    offset: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Format registers for display with multiple representations.

    Returns a list of dicts with address, raw value, hex, and converted value.
    """
    results = []

    # Handle RAW mode - just return raw register data
    if data_type == "raw":
        for i, raw in enumerate(registers):
            results.append({
                "address": start_address + i,
                "raw": raw,
                "hex": f"0x{raw:04X}",
                "binary": f"{raw:016b}",
                "is_group_start": True,
                "group_size": 1
            })
        return results

    try:
        dt = DataType(data_type)
        bo = ByteOrder(byte_order)
    except ValueError:
        dt = DataType.UINT16
        bo = ByteOrder.BIG_ENDIAN

    # Get converted values
    converted = convert_registers(registers, dt, bo, scale, offset)
    if not isinstance(converted, list):
        converted = [converted]

    # Determine register grouping
    regs_per_value = 1
    if dt in (DataType.UINT32, DataType.INT32, DataType.FLOAT32):
        regs_per_value = 2
    elif dt in (DataType.UINT64, DataType.INT64, DataType.FLOAT64):
        regs_per_value = 4

    conv_idx = 0
    for i, raw in enumerate(registers):
        result = {
            "address": start_address + i,
            "raw": raw,
            "hex": f"0x{raw:04X}",
            "binary": f"{raw:016b}"
        }

        # Add converted value at the start of each group
        if i % regs_per_value == 0 and conv_idx < len(converted):
            cv = converted[conv_idx]
            if isinstance(cv, float):
                result["converted"] = round(cv, 6)
            else:
                result["converted"] = cv
            result["is_group_start"] = True
            result["group_size"] = regs_per_value
            conv_idx += 1
        else:
            result["is_group_start"] = False

        results.append(result)

    return results


class TestModeStatus(Enum):
    """Test mode status."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    EXPIRING = "expiring"  # Last minute warning


@dataclass
class TestModeState:
    """Current state of test mode."""
    status: TestModeStatus = TestModeStatus.INACTIVE
    started_at: Optional[float] = None
    expires_at: Optional[float] = None
    timeout_minutes: int = 10
    original_config_dir: Optional[str] = None
    test_config_dir: Optional[str] = None

    # What's disabled in test mode
    http_disabled: bool = True
    mqtt_disabled: bool = True
    alerts_disabled: bool = True
    polling_paused: bool = True  # Pause polling to free serial port for testing

    # Statistics
    reads_performed: int = 0
    last_read_time: Optional[float] = None
    devices_tested: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        remaining = 0
        if self.expires_at:
            remaining = max(0, self.expires_at - time.time())

        return {
            "status": self.status.value,
            "started_at": datetime.fromtimestamp(self.started_at).isoformat() if self.started_at else None,
            "expires_at": datetime.fromtimestamp(self.expires_at).isoformat() if self.expires_at else None,
            "remaining_seconds": int(remaining),
            "remaining_minutes": round(remaining / 60, 1),
            "timeout_minutes": self.timeout_minutes,
            "http_disabled": self.http_disabled,
            "mqtt_disabled": self.mqtt_disabled,
            "alerts_disabled": self.alerts_disabled,
            "reads_performed": self.reads_performed,
            "last_read_time": datetime.fromtimestamp(self.last_read_time).isoformat() if self.last_read_time else None,
            "devices_tested": self.devices_tested
        }


@dataclass
class RegisterReadResult:
    """Result of a register read operation."""
    success: bool
    device_id: str
    unit_id: int
    register_address: int
    register_count: int
    values: Optional[List[int]] = None
    converted_values: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    duration_ms: float = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    data_type: str = "uint16"
    byte_order: str = "big"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "device_id": self.device_id,
            "unit_id": self.unit_id,
            "register_address": self.register_address,
            "register_count": self.register_count,
            "values": self.values,
            "converted_values": self.converted_values,
            "data_type": self.data_type,
            "byte_order": self.byte_order,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp
        }


@dataclass
class ConfigValidationResult:
    """Result of config validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    device_count: int = 0
    connection_count: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "device_count": self.device_count,
            "connection_count": self.connection_count,
            "details": self.details
        }


class TestModeService:
    """
    Service for managing test mode operations.

    Test mode allows operators to:
    1. Test new device configurations without affecting production
    2. Read specific registers on demand
    3. Validate configurations before applying

    Safety: All operations are designed to fail gracefully without
    crashing the main application.
    """

    # Singleton instance
    _instance: Optional['TestModeService'] = None

    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.state = TestModeState()
        self._expiration_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        # References to main app components (set by portal)
        self._modbus_clients: Dict[str, Any] = {}
        self._connections: Dict[str, Any] = {}
        self._cache: Optional[Any] = None

        logger.info(f"TestModeService initialized with config_dir: {config_dir}")

    @classmethod
    def get_instance(cls, config_dir: str) -> 'TestModeService':
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls(config_dir)
        return cls._instance

    def set_modbus_references(self, clients: Dict, connections: Dict, cache: Any = None):
        """Set references to Modbus clients for live reads."""
        self._modbus_clients = clients
        self._connections = connections
        self._cache = cache
        logger.debug(f"TestModeService: registered {len(clients)} clients, {len(connections)} connections")

    # ==================== Test Mode Toggle ====================

    async def enter_test_mode(
        self,
        timeout_minutes: int = 10,
        disable_http: bool = True,
        disable_mqtt: bool = True,
        disable_alerts: bool = True
    ) -> Tuple[bool, str]:
        """
        Enter test mode.

        Args:
            timeout_minutes: Auto-exit after this many minutes (max 30)
            disable_http: Disable HTTP API publishing
            disable_mqtt: Disable MQTT publishing
            disable_alerts: Disable alert processing

        Returns:
            Tuple of (success, message)
        """
        async with self._lock:
            try:
                if self.state.status == TestModeStatus.ACTIVE:
                    return False, "Test mode is already active"

                # Validate timeout (max 30 minutes for safety)
                timeout_minutes = min(max(1, timeout_minutes), 30)

                # Set up test config directory
                test_config_dir = os.path.join(os.path.dirname(self.config_dir), "test_config")

                # Create test_config directory if it doesn't exist
                if not os.path.exists(test_config_dir):
                    os.makedirs(test_config_dir, exist_ok=True)
                    # Copy current config as starting point
                    for filename in ['slave_config.yaml', 'communication.yaml']:
                        src = os.path.join(self.config_dir, filename)
                        dst = os.path.join(test_config_dir, filename)
                        if os.path.exists(src) and not os.path.exists(dst):
                            shutil.copy2(src, dst)
                    logger.info(f"Created test_config directory with copies of current config")

                # Update state
                now = time.time()
                self.state = TestModeState(
                    status=TestModeStatus.ACTIVE,
                    started_at=now,
                    expires_at=now + (timeout_minutes * 60),
                    timeout_minutes=timeout_minutes,
                    original_config_dir=self.config_dir,
                    test_config_dir=test_config_dir,
                    http_disabled=disable_http,
                    mqtt_disabled=disable_mqtt,
                    alerts_disabled=disable_alerts,
                    reads_performed=0,
                    devices_tested=[]
                )

                # Start expiration timer
                if self._expiration_task:
                    self._expiration_task.cancel()
                self._expiration_task = asyncio.create_task(self._expiration_monitor())

                logger.info(f"Entered test mode: timeout={timeout_minutes}min, "
                           f"http_disabled={disable_http}, mqtt_disabled={disable_mqtt}")

                return True, f"Test mode activated. Will auto-exit in {timeout_minutes} minutes."

            except Exception as e:
                logger.error(f"Error entering test mode: {e}", exc_info=True)
                return False, f"Failed to enter test mode: {str(e)}"

    async def exit_test_mode(self, reason: str = "manual") -> Tuple[bool, str]:
        """
        Exit test mode and return to normal operation.

        Args:
            reason: Reason for exiting (manual, timeout, error)

        Returns:
            Tuple of (success, message)
        """
        async with self._lock:
            try:
                if self.state.status == TestModeStatus.INACTIVE:
                    return False, "Test mode is not active"

                # Cancel expiration task
                if self._expiration_task:
                    self._expiration_task.cancel()
                    self._expiration_task = None

                # Log statistics
                duration = time.time() - (self.state.started_at or time.time())
                logger.info(f"Exiting test mode: reason={reason}, duration={duration:.1f}s, "
                           f"reads={self.state.reads_performed}, devices={len(self.state.devices_tested)}")

                # Reset state
                old_state = self.state
                self.state = TestModeState()

                return True, (f"Test mode deactivated after {int(duration)}s. "
                             f"Performed {old_state.reads_performed} reads on "
                             f"{len(old_state.devices_tested)} devices.")

            except Exception as e:
                logger.error(f"Error exiting test mode: {e}", exc_info=True)
                # Force reset state even on error
                self.state = TestModeState()
                return False, f"Error exiting test mode: {str(e)}"

    async def _expiration_monitor(self):
        """Background task to monitor test mode expiration."""
        try:
            while self.state.status == TestModeStatus.ACTIVE:
                remaining = (self.state.expires_at or 0) - time.time()

                if remaining <= 0:
                    # Time's up
                    await self.exit_test_mode(reason="timeout")
                    break
                elif remaining <= 60 and self.state.status != TestModeStatus.EXPIRING:
                    # Last minute warning
                    self.state.status = TestModeStatus.EXPIRING
                    logger.warning("Test mode expiring in less than 1 minute")

                # Check every 5 seconds
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in expiration monitor: {e}")
            # Safety: exit test mode on any error
            await self.exit_test_mode(reason="error")

    def is_test_mode_active(self) -> bool:
        """Check if test mode is currently active."""
        return self.state.status in (TestModeStatus.ACTIVE, TestModeStatus.EXPIRING)

    def should_publish_http(self) -> bool:
        """Check if HTTP publishing should occur (respects test mode)."""
        if self.is_test_mode_active() and self.state.http_disabled:
            return False
        return True

    def should_publish_mqtt(self) -> bool:
        """Check if MQTT publishing should occur (respects test mode)."""
        if self.is_test_mode_active() and self.state.mqtt_disabled:
            return False
        return True

    def should_process_alerts(self) -> bool:
        """Check if alerts should be processed (respects test mode)."""
        if self.is_test_mode_active() and self.state.alerts_disabled:
            return False
        return True

    def should_pause_polling(self) -> bool:
        """Check if polling should be paused (to free serial port for testing)."""
        if self.is_test_mode_active() and self.state.polling_paused:
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """Get current test mode status."""
        return self.state.to_dict()

    # ==================== Live Register Inspector ====================

    async def read_registers(
        self,
        connection_id: str,
        unit_id: int,
        start_address: int,
        count: int = 1,
        function_code: int = 3,  # 3=holding, 4=input
        data_type: str = "uint16",
        byte_order: str = "big",
        scale: float = 1.0,
        offset: float = 0.0
    ) -> RegisterReadResult:
        """
        Read specific registers from a device.

        This is a direct Modbus read, bypassing the normal polling loop.
        Useful for troubleshooting and testing new register configurations.

        Args:
            connection_id: The connection ID to use
            unit_id: Modbus unit/slave ID
            start_address: Starting register address
            count: Number of registers to read
            function_code: Modbus function code (3=holding, 4=input)

        Returns:
            RegisterReadResult with values or error
        """
        start_time = time.time()

        try:
            # Get the client for this connection
            client = self._modbus_clients.get(connection_id)
            if not client:
                available = list(self._modbus_clients.keys())
                return RegisterReadResult(
                    success=False,
                    device_id=f"unit_{unit_id}",
                    unit_id=unit_id,
                    register_address=start_address,
                    register_count=count,
                    error=f"Connection '{connection_id}' not found. Available: {available}",
                    duration_ms=(time.time() - start_time) * 1000
                )

            # Perform the read using the client's internal methods
            if not hasattr(client, 'client') or client.client is None:
                return RegisterReadResult(
                    success=False,
                    device_id=f"unit_{unit_id}",
                    unit_id=unit_id,
                    register_address=start_address,
                    register_count=count,
                    error="Modbus client not initialized",
                    duration_ms=(time.time() - start_time) * 1000
                )

            # Ensure connection is established (client has _ensure_connection method)
            if hasattr(client, '_ensure_connection'):
                try:
                    await asyncio.wait_for(client._ensure_connection(), timeout=5.0)
                except Exception as conn_err:
                    return RegisterReadResult(
                        success=False,
                        device_id=f"unit_{unit_id}",
                        unit_id=unit_id,
                        register_address=start_address,
                        register_count=count,
                        error=f"Connection failed: {str(conn_err)}",
                        duration_ms=(time.time() - start_time) * 1000
                    )

            if function_code == 3:
                # Holding registers - use keyword arguments for pymodbus 3.x
                result = await asyncio.wait_for(
                    client.client.read_holding_registers(
                        address=start_address,
                        count=count,
                        **get_unit_id_kwargs(unit_id)
                    ),
                    timeout=5.0
                )
            elif function_code == 4:
                # Input registers - use keyword arguments for pymodbus 3.x
                result = await asyncio.wait_for(
                    client.client.read_input_registers(
                        address=start_address,
                        count=count,
                        **get_unit_id_kwargs(unit_id)
                    ),
                    timeout=5.0
                )
            else:
                return RegisterReadResult(
                    success=False,
                    device_id=f"unit_{unit_id}",
                    unit_id=unit_id,
                    register_address=start_address,
                    register_count=count,
                    error=f"Unsupported function code: {function_code}. Use 3 (holding) or 4 (input).",
                    duration_ms=(time.time() - start_time) * 1000
                )

            # Check for errors
            if result.isError():
                return RegisterReadResult(
                    success=False,
                    device_id=f"unit_{unit_id}",
                    unit_id=unit_id,
                    register_address=start_address,
                    register_count=count,
                    error=f"Modbus error: {result}",
                    duration_ms=(time.time() - start_time) * 1000
                )

            # Update statistics
            self.state.reads_performed += 1
            self.state.last_read_time = time.time()
            device_key = f"{connection_id}:unit_{unit_id}"
            if device_key not in self.state.devices_tested:
                self.state.devices_tested.append(device_key)

            # Convert values with formatting
            raw_values = list(result.registers)
            converted = format_register_display(
                raw_values, start_address, data_type, byte_order, scale, offset
            )

            return RegisterReadResult(
                success=True,
                device_id=f"unit_{unit_id}",
                unit_id=unit_id,
                register_address=start_address,
                register_count=count,
                values=raw_values,
                converted_values=converted,
                data_type=data_type,
                byte_order=byte_order,
                duration_ms=(time.time() - start_time) * 1000
            )

        except asyncio.TimeoutError:
            return RegisterReadResult(
                success=False,
                device_id=f"unit_{unit_id}",
                unit_id=unit_id,
                register_address=start_address,
                register_count=count,
                error="Read timeout (5s)",
                duration_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            logger.error(f"Error reading registers: {e}", exc_info=True)
            return RegisterReadResult(
                success=False,
                device_id=f"unit_{unit_id}",
                unit_id=unit_id,
                register_address=start_address,
                register_count=count,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )

    # ==================== Device Probe ====================

    async def probe_device(
        self,
        connection_id: str,
        unit_id: int,
        test_address: int = 0,
        test_count: int = 1
    ) -> Dict[str, Any]:
        """
        Probe a device to check if it responds.

        Performs a minimal read to verify device communication.

        Args:
            connection_id: Connection to use
            unit_id: Device unit ID
            test_address: Register to read (default 0)
            test_count: Number of registers (default 1)

        Returns:
            Dict with probe results
        """
        start_time = time.time()

        # Try holding registers first, then input registers
        holding_result = await self.read_registers(
            connection_id, unit_id, test_address, test_count, function_code=3
        )

        if holding_result.success:
            return {
                "success": True,
                "device_id": f"unit_{unit_id}",
                "connection_id": connection_id,
                "unit_id": unit_id,
                "message": f"Device responded on holding register {test_address}",
                "register_type": "holding",
                "values": holding_result.values,
                "duration_ms": (time.time() - start_time) * 1000
            }

        # Try input registers
        input_result = await self.read_registers(
            connection_id, unit_id, test_address, test_count, function_code=4
        )

        if input_result.success:
            return {
                "success": True,
                "device_id": f"unit_{unit_id}",
                "connection_id": connection_id,
                "unit_id": unit_id,
                "message": f"Device responded on input register {test_address}",
                "register_type": "input",
                "values": input_result.values,
                "duration_ms": (time.time() - start_time) * 1000
            }

        return {
            "success": False,
            "device_id": f"unit_{unit_id}",
            "connection_id": connection_id,
            "unit_id": unit_id,
            "message": "Device did not respond",
            "holding_error": holding_result.error,
            "input_error": input_result.error,
            "duration_ms": (time.time() - start_time) * 1000,
            "troubleshooting": [
                f"Check device is powered on",
                f"Verify unit ID is {unit_id}",
                f"Check RS485 wiring (A+/B- polarity)",
                f"Verify baud rate matches device settings",
                f"Try different register address"
            ]
        }

    # ==================== Config Validation ====================

    def validate_config(self, config_path: Optional[str] = None) -> ConfigValidationResult:
        """
        Validate a slave_config.yaml file.

        Checks:
        - YAML syntax
        - Required fields present
        - Register addresses valid
        - Unit IDs unique per connection
        - Known device types

        Args:
            config_path: Path to config file (default: test_config/slave_config.yaml)

        Returns:
            ConfigValidationResult
        """
        errors = []
        warnings = []
        details = {}

        # Default to test_config
        if not config_path:
            config_path = os.path.join(
                os.path.dirname(self.config_dir),
                "test_config",
                "slave_config.yaml"
            )

        try:
            # Check file exists
            if not os.path.exists(config_path):
                return ConfigValidationResult(
                    valid=False,
                    errors=[f"Config file not found: {config_path}"]
                )

            # Parse YAML
            with open(config_path) as f:
                config = yaml.safe_load(f)

            if not config:
                return ConfigValidationResult(
                    valid=False,
                    errors=["Config file is empty"]
                )

            # Check structure
            connections = config.get('connections', [])
            if not connections:
                errors.append("No 'connections' defined in config")
                return ConfigValidationResult(valid=False, errors=errors)

            connection_count = len(connections)
            device_count = 0
            unit_ids_per_connection = {}

            for i, conn in enumerate(connections):
                conn_id = conn.get('id', f'connection_{i}')
                conn_type = conn.get('connection_type')

                # Check connection type
                if conn_type not in ['tcp', 'serial']:
                    errors.append(f"Connection '{conn_id}': invalid connection_type '{conn_type}'")

                # TCP-specific checks
                if conn_type == 'tcp':
                    if not conn.get('host'):
                        errors.append(f"Connection '{conn_id}': missing 'host' for TCP connection")
                    if not conn.get('port'):
                        warnings.append(f"Connection '{conn_id}': no 'port' specified, using default 502")

                # Serial-specific checks
                if conn_type == 'serial':
                    if not conn.get('port'):
                        errors.append(f"Connection '{conn_id}': missing 'port' for serial connection")

                # Check clients/devices
                clients = conn.get('clients', [])
                if not clients:
                    warnings.append(f"Connection '{conn_id}': no clients/devices defined")

                unit_ids_per_connection[conn_id] = []

                for j, client in enumerate(clients):
                    client_id = client.get('id', f'device_{j}')
                    unit_id = client.get('unit_id')
                    device_type = client.get('type', '')
                    is_disabled = client.get('disabled', False)

                    # Skip disabled devices from validation
                    if is_disabled:
                        continue

                    device_count += 1

                    # Check required fields
                    if not client_id:
                        errors.append(f"Connection '{conn_id}', device {j}: missing 'id'")
                    if unit_id is None:
                        errors.append(f"Connection '{conn_id}', device '{client_id}': missing 'unit_id'")
                    else:
                        # Check for duplicate unit IDs (warning only for relay devices, they often share unit_id)
                        if unit_id in unit_ids_per_connection[conn_id]:
                            if device_type == 'relay':
                                # Relay devices commonly share unit_id with different coil addresses - just warn
                                pass  # Don't flag as error for relay devices
                            else:
                                warnings.append(f"Connection '{conn_id}': duplicate unit_id {unit_id} (device '{client_id}')")
                        unit_ids_per_connection[conn_id].append(unit_id)

                        # Validate unit ID range
                        if not (1 <= unit_id <= 247):
                            errors.append(f"Device '{client_id}': unit_id {unit_id} out of range (1-247)")

                    # Check device type
                    known_types = ['electrical', 'water', 'relay', 'environment', 'gas', 'custom']
                    if device_type and device_type not in known_types:
                        warnings.append(f"Device '{client_id}': unknown type '{device_type}'")

                    # Check registers
                    registers = client.get('registers', [])
                    if not registers:
                        warnings.append(f"Device '{client_id}': no registers defined")

                    for k, reg in enumerate(registers):
                        reg_addr = reg.get('address')
                        if reg_addr is None:
                            errors.append(f"Device '{client_id}', register {k}: missing 'address'")
                        elif not (0 <= reg_addr <= 65535):
                            errors.append(f"Device '{client_id}', register {k}: address {reg_addr} out of range")

                        if not reg.get('field_name'):
                            errors.append(f"Device '{client_id}', register {k}: missing 'field_name'")

                    # Check intervals
                    polling = client.get('polling_interval')
                    if polling and polling < 1:
                        warnings.append(f"Device '{client_id}': polling_interval {polling}s is very fast")

            details = {
                "file": config_path,
                "connections": connection_count,
                "devices": device_count,
                "unit_ids_by_connection": unit_ids_per_connection
            }

            return ConfigValidationResult(
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                device_count=device_count,
                connection_count=connection_count,
                details=details
            )

        except yaml.YAMLError as e:
            return ConfigValidationResult(
                valid=False,
                errors=[f"YAML syntax error: {str(e)}"]
            )
        except Exception as e:
            logger.error(f"Error validating config: {e}", exc_info=True)
            return ConfigValidationResult(
                valid=False,
                errors=[f"Validation error: {str(e)}"]
            )

    def get_test_config(self) -> Optional[Dict[str, Any]]:
        """Get the current test configuration."""
        test_config_path = os.path.join(
            os.path.dirname(self.config_dir),
            "test_config",
            "slave_config.yaml"
        )

        try:
            if os.path.exists(test_config_path):
                with open(test_config_path) as f:
                    return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error reading test config: {e}")

        return None

    def save_test_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Save a test configuration.

        Args:
            config: The configuration dictionary to save

        Returns:
            Tuple of (success, message)
        """
        test_config_dir = os.path.join(os.path.dirname(self.config_dir), "test_config")
        test_config_path = os.path.join(test_config_dir, "slave_config.yaml")

        try:
            # Create directory if needed
            os.makedirs(test_config_dir, exist_ok=True)

            # Validate before saving
            # Write to temp file first
            temp_path = test_config_path + ".tmp"
            with open(temp_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            # Validate the temp file
            validation = self.validate_config(temp_path)
            if not validation.valid:
                os.remove(temp_path)
                return False, f"Config validation failed: {'; '.join(validation.errors)}"

            # Move temp to final
            shutil.move(temp_path, test_config_path)

            return True, f"Test config saved with {validation.device_count} devices"

        except Exception as e:
            logger.error(f"Error saving test config: {e}", exc_info=True)
            return False, f"Failed to save config: {str(e)}"

    def save_test_config_content(self, filename: str, content: str, subdirectory: str = None) -> Tuple[bool, str]:
        """
        Save raw config content to test_config directory.

        Args:
            filename: Name of the config file
            content: Raw YAML content as string
            subdirectory: Optional subdirectory within test_config (e.g., 'slave_configs')

        Returns:
            Tuple of (success, message)
        """
        # Get the base directory (parent of config_dir)
        # config_dir is typically /home/dcu/config/ess-3a or similar
        # We want test_config to be at /home/dcu/test_config (sibling of config)
        base_dir = os.path.dirname(self.config_dir)
        test_config_dir = os.path.join(base_dir, "test_config")

        # If subdirectory specified, add it (subdirectory should be relative like "slave_configs")
        if subdirectory:
            # Clean up subdirectory - remove any absolute path components
            subdirectory = subdirectory.lstrip('/')
            # Only use the last component if it looks like it has nested paths
            # This handles cases like "/home/dcu/slave_configs" -> "slave_configs"
            if '/' in subdirectory:
                subdirectory = os.path.basename(subdirectory.rstrip('/'))
            test_config_dir = os.path.join(test_config_dir, subdirectory)

        test_config_path = os.path.join(test_config_dir, filename)
        logger.info(f"Saving test config to: {test_config_path}")

        try:
            # Create directory if needed
            os.makedirs(test_config_dir, exist_ok=True)

            # Validate YAML syntax first
            try:
                yaml.safe_load(content)
            except yaml.YAMLError as e:
                return False, f"Invalid YAML syntax: {str(e)}"

            # Write to temp file first
            temp_path = test_config_path + ".tmp"
            with open(temp_path, 'w') as f:
                f.write(content)

            # If it's slave_config, validate it
            if 'slave' in filename.lower():
                validation = self.validate_config(temp_path)
                if not validation.valid:
                    os.remove(temp_path)
                    return False, f"Config validation failed: {'; '.join(validation.errors)}"

            # Move temp to final
            shutil.move(temp_path, test_config_path)

            relative_path = f"{subdirectory}/{filename}" if subdirectory else filename
            return True, f"Config saved to test_config/{relative_path}"

        except Exception as e:
            logger.error(f"Error saving test config content: {e}", exc_info=True)
            return False, f"Failed to save config: {str(e)}"

    # ==================== Test Config Management ====================

    def get_test_config_dir(self) -> str:
        """Get the test_config directory path."""
        base_dir = os.path.dirname(self.config_dir)
        return os.path.join(base_dir, "test_config")

    def list_test_configs(self) -> List[Dict[str, Any]]:
        """List all files in test_config directory."""
        test_config_dir = self.get_test_config_dir()
        files = []

        if not os.path.exists(test_config_dir):
            return files

        def scan_dir(directory, prefix=""):
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                rel_path = os.path.join(prefix, item) if prefix else item

                if os.path.isfile(item_path):
                    stat = os.stat(item_path)
                    files.append({
                        "name": item,
                        "path": rel_path,
                        "full_path": item_path,
                        "size_kb": round(stat.st_size / 1024, 2),
                        "modified": stat.st_mtime
                    })
                elif os.path.isdir(item_path):
                    scan_dir(item_path, rel_path)

        scan_dir(test_config_dir)
        return files

    def apply_test_config_to_production(self, filename: str, subdirectory: str = None) -> Tuple[bool, str]:
        """
        Copy a test config file to production config directory.

        Args:
            filename: Name of the config file
            subdirectory: Optional subdirectory (e.g., 'slave_configs')

        Returns:
            Tuple of (success, message)
        """
        try:
            test_config_dir = self.get_test_config_dir()
            if subdirectory:
                subdirectory = subdirectory.lstrip('/')
                test_config_dir = os.path.join(test_config_dir, subdirectory)

            test_file = os.path.join(test_config_dir, filename)

            if not os.path.exists(test_file):
                return False, f"Test config not found: {filename}"

            # Determine production path
            prod_dir = self.config_dir
            if subdirectory:
                prod_dir = os.path.join(os.path.dirname(self.config_dir), subdirectory)

            prod_file = os.path.join(prod_dir, filename)

            # Create backup of production file if it exists
            if os.path.exists(prod_file):
                import time as time_module
                backup_file = f"{prod_file}.bak.{int(time_module.time())}"
                shutil.copy2(prod_file, backup_file)
                logger.info(f"Created backup: {backup_file}")

            # Copy test config to production
            os.makedirs(os.path.dirname(prod_file), exist_ok=True)
            shutil.copy2(test_file, prod_file)

            logger.info(f"Applied test config to production: {test_file} -> {prod_file}")
            return True, f"Config applied to production. Restart service to load changes."

        except Exception as e:
            logger.error(f"Error applying test config: {e}", exc_info=True)
            return False, f"Failed to apply config: {str(e)}"

    def get_test_config_content(self, filename: str, subdirectory: str = None) -> Tuple[bool, str, str]:
        """
        Read content of a test config file.

        Returns:
            Tuple of (success, content_or_error, full_path)
        """
        test_config_dir = self.get_test_config_dir()
        if subdirectory:
            subdirectory = subdirectory.lstrip('/')
            test_config_dir = os.path.join(test_config_dir, subdirectory)

        test_file = os.path.join(test_config_dir, filename)

        if not os.path.exists(test_file):
            return False, f"Test config not found: {filename}", ""

        try:
            with open(test_file, 'r') as f:
                content = f.read()
            return True, content, test_file
        except Exception as e:
            return False, str(e), test_file

    # ==================== Config Verification ====================

    async def verify_config(self, config_content: str) -> Dict[str, Any]:
        """
        Verify a configuration by testing all connections and reading from all devices.

        This creates temporary connections and attempts to read registers from each device
        to verify the configuration is correct.

        Timeout: 30 seconds max for entire verification

        Args:
            config_content: YAML config content as string

        Returns:
            Dict with verification results for each connection and device
        """
        VERIFICATION_TIMEOUT = 30.0  # Max total time for verification

        results = {
            "success": True,
            "connections": [],
            "summary": {
                "total_connections": 0,
                "successful_connections": 0,
                "failed_connections": 0,
                "total_devices": 0,
                "successful_devices": 0,
                "failed_devices": 0,
                "skipped_devices": 0
            },
            "duration_seconds": 0
        }

        start_time = time.time()

        # Log test mode status at start of verification
        logger.info(f"Starting config verification - test_mode_active: {self.is_test_mode_active()}, polling_paused: {self.state.polling_paused}")

        try:
            # Parse YAML
            config = yaml.safe_load(config_content)
            if not config or 'connections' not in config:
                return {
                    "success": False,
                    "error": "Invalid config: no 'connections' section found",
                    "connections": []
                }

            connections = config.get('connections', [])
            results["summary"]["total_connections"] = len(connections)

            for conn_config in connections:
                # Check overall timeout
                elapsed = time.time() - start_time
                if elapsed > VERIFICATION_TIMEOUT:
                    results["timeout"] = True
                    results["error"] = f"Verification timed out after {VERIFICATION_TIMEOUT}s"
                    logger.warning(f"Verification timeout after {elapsed:.1f}s")
                    break

                conn_result = await self._verify_connection(conn_config)
                results["connections"].append(conn_result)

                if conn_result["connection_ok"]:
                    results["summary"]["successful_connections"] += 1
                else:
                    results["summary"]["failed_connections"] += 1
                    results["success"] = False

                results["summary"]["total_devices"] += len(conn_result.get("devices", []))
                for dev in conn_result.get("devices", []):
                    if dev.get("skipped"):
                        results["summary"]["skipped_devices"] += 1
                    elif dev.get("success"):
                        results["summary"]["successful_devices"] += 1
                    else:
                        results["summary"]["failed_devices"] += 1
                        results["success"] = False

            results["duration_seconds"] = round(time.time() - start_time, 2)

        except yaml.YAMLError as e:
            return {
                "success": False,
                "error": f"Invalid YAML: {str(e)}",
                "connections": [],
                "duration_seconds": round(time.time() - start_time, 2)
            }
        except Exception as e:
            logger.error(f"Error verifying config: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "connections": [],
                "duration_seconds": round(time.time() - start_time, 2)
            }

        return results

    async def _verify_connection(self, conn_config: Dict) -> Dict[str, Any]:
        """
        Verify a single connection by connecting and reading from all its devices.

        For serial connections: CLOSES existing connection and creates NEW one with test settings.
        This properly tests baud rate, parity, and other serial settings.
        For TCP connections: creates a temporary connection.

        After verification completes, the serial port is freed and main polling
        will reconnect with its original settings when test mode ends.
        """
        conn_id = conn_config.get('id', 'unknown')
        conn_type = conn_config.get('connection_type', 'serial')

        result = {
            "id": conn_id,
            "type": conn_type,
            "connection_ok": False,
            "error": None,
            "devices": [],
            "using_existing": False,
            "warnings": [],
            "settings_tested": {}
        }

        temp_client = None
        closed_existing = False

        try:
            # For serial connections: CLOSE existing and create NEW with test settings
            if conn_type == 'serial':
                serial_port = conn_config.get('port', conn_config.get('serial_port', '/dev/ttyS0'))
                baud_rate = conn_config.get('baud_rate', 9600)
                parity = conn_config.get('parity', 'N')
                stop_bits = conn_config.get('stop_bits', 1)
                bytesize = conn_config.get('bytesize', 8)
                timeout = min(conn_config.get('timeout', 3), 3)

                # Map parity
                parity_map = {"N": "N", "E": "E", "O": "O", "none": "N", "even": "E", "odd": "O"}
                parity_char = parity_map.get(str(parity).upper(), "N")

                # Store settings being tested for display
                result["settings_tested"] = {
                    "port": serial_port,
                    "baud_rate": baud_rate,
                    "parity": parity_char,
                    "stop_bits": stop_bits,
                    "bytesize": bytesize
                }

                logger.info(f"Testing serial connection with: port={serial_port}, baud={baud_rate}, parity={parity_char}")

                # CRITICAL: Close existing serial connections to free the port
                for existing_conn_id, existing_handler in self._modbus_clients.items():
                    if existing_handler and hasattr(existing_handler, 'client') and existing_handler.client:
                        existing_client = existing_handler.client
                        # Check if this is an async serial client
                        if 'Async' in type(existing_client).__name__ and 'Serial' in type(existing_client).__name__:
                            logger.info(f"Closing existing serial connection '{existing_conn_id}' to free port for testing")
                            try:
                                existing_client.close()
                                closed_existing = True
                                # Give OS time to release the port
                                await asyncio.sleep(0.5)
                            except Exception as close_err:
                                logger.warning(f"Error closing existing connection: {close_err}")

                # Now create a NEW connection with the TEST settings
                from pymodbus.client import AsyncModbusSerialClient

                temp_client = AsyncModbusSerialClient(
                    port=serial_port,
                    baudrate=baud_rate,
                    parity=parity_char,
                    stopbits=stop_bits,
                    bytesize=bytesize,
                    timeout=timeout
                )

                # Connect with the new settings
                try:
                    await temp_client.connect()
                    if hasattr(temp_client, 'connected') and not temp_client.connected:
                        result["error"] = f"Failed to connect to {serial_port} at {baud_rate} baud"
                        return result
                    result["connection_ok"] = True
                    logger.info(f"Test connection established: {serial_port} @ {baud_rate} baud")
                except Exception as conn_err:
                    logger.error(f"Error creating test connection: {conn_err}")
                    result["error"] = f"Connection failed with test settings: {conn_err}"
                    return result

            else:
                # TCP connection - create temporary connection
                host = conn_config.get('host', '')
                port = conn_config.get('port', 502)
                verify_timeout = min(conn_config.get('timeout', 3), 1.5)

                if not host:
                    result["error"] = "Missing host for TCP connection"
                    return result

                from pymodbus.client import ModbusTcpClient
                temp_client = ModbusTcpClient(
                    host=host,
                    port=port,
                    timeout=verify_timeout
                )

                connected = temp_client.connect()
                if not connected:
                    result["error"] = f"Failed to connect to {host}:{port}"
                    return result

                result["connection_ok"] = True

            # Test each device (skip disabled devices)
            clients = conn_config.get('clients', [])
            for client_config in clients:
                # Skip disabled devices
                if client_config.get('disabled', False):
                    device_id = client_config.get('id', 'unknown')
                    result["devices"].append({
                        "id": device_id,
                        "unit_id": client_config.get('unit_id', 1),
                        "success": True,
                        "skipped": True,
                        "message": "Device is disabled - skipped validation"
                    })
                    continue
                device_result = await self._verify_device(temp_client, client_config)
                result["devices"].append(device_result)

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error verifying connection {conn_id}: {e}")
        finally:
            # Always close the test connection to free the port
            # Main polling will reconnect when test mode ends
            if temp_client:
                try:
                    temp_client.close()
                    logger.info(f"Closed test connection for {conn_id}")
                except Exception as close_err:
                    logger.warning(f"Error closing test connection: {close_err}")

        return result

    async def _verify_device(self, client, device_config: Dict) -> Dict[str, Any]:
        """
        Verify a single device with ONE quick connectivity test.

        Reads a meaningful register (voltage/frequency for electrical, flow for water)
        to confirm device responds at the configured unit ID.
        Uses the device's configured endianness for proper value conversion.
        """
        device_id = device_config.get('id', 'unknown')
        unit_id = device_config.get('unit_id', 1)
        meter_model = device_config.get('meter_model', '')
        profile_name = device_config.get('profile', '')
        device_type = device_config.get('type', 'electrical')

        # Get endianness from device config, default to 'big'
        endianness = device_config.get('endianness', 'big')

        # Map endianness string to ByteOrder enum
        byte_order_map = {
            'big': ByteOrder.BIG_ENDIAN,
            'little': ByteOrder.LITTLE_ENDIAN,
            'big_swap': ByteOrder.BIG_ENDIAN_SWAP,
            'little_swap': ByteOrder.LITTLE_ENDIAN_SWAP,
        }
        byte_order = byte_order_map.get(endianness.lower(), ByteOrder.BIG_ENDIAN)

        result = {
            "id": device_id,
            "unit_id": unit_id,
            "meter_model": meter_model,
            "profile": profile_name,
            "success": False,
            "error": None,
            "sample_values": {},
            "endianness": endianness
        }

        try:
            # Choose a meaningful register based on device type
            # Priority: voltage > frequency > first register in profile
            test_address = 0
            test_count = 2
            register_type = 'holding'
            field_name = 'test_value'
            unit = ''

            if meter_model and profile_name:
                try:
                    from src.services.meter_registry import get_meter_registry
                    registry = get_meter_registry()

                    # Try to get endianness from meter registry if not in device config
                    if endianness == 'big':  # default, might need to check registry
                        meter_info = registry.get_meter_info(meter_model)
                        if meter_info and meter_info.get('endianness'):
                            endianness = meter_info.get('endianness')
                            byte_order = byte_order_map.get(endianness.lower(), ByteOrder.BIG_ENDIAN)
                            result["endianness"] = endianness

                    registers = registry.generate_client_registers(
                        meter_id=meter_model,
                        profile_name=profile_name
                    )
                    if registers:
                        # Find a meaningful register to read
                        # For electrical: prefer voltage_ry, voltage, frequency
                        # For water: prefer flow_rate, total_flow
                        preferred_fields = []
                        if device_type == 'water':
                            preferred_fields = ['flow_rate', 'total_flow', 'volume', 'flow']
                        else:  # electrical
                            preferred_fields = ['voltage_ry', 'voltage', 'avg_voltage_ll', 'frequency', 'power']

                        selected_reg = None
                        for pref in preferred_fields:
                            for reg in registers:
                                if pref in reg.get('field_name', '').lower():
                                    selected_reg = reg
                                    break
                            if selected_reg:
                                break

                        # Fallback to first register
                        if not selected_reg:
                            selected_reg = registers[0]

                        test_address = selected_reg.get('address', 0)
                        test_count = selected_reg.get('count', 2)
                        register_type = selected_reg.get('register_type', 'holding')
                        field_name = selected_reg.get('field_name', f'addr_{test_address}')
                        unit = selected_reg.get('unit', '')
                        result["test_register"] = field_name

                except Exception as e:
                    logger.debug(f"Could not load meter profile for {device_id}: {e}")

            # Check if client is async
            is_async = 'Async' in type(client).__name__

            # Single read to verify connectivity
            if register_type == 'input':
                if is_async:
                    response = await client.read_input_registers(address=test_address, count=test_count, **get_unit_id_kwargs(unit_id))
                else:
                    response = client.read_input_registers(address=test_address, count=test_count, **get_unit_id_kwargs(unit_id))
            else:
                if is_async:
                    response = await client.read_holding_registers(address=test_address, count=test_count, **get_unit_id_kwargs(unit_id))
                else:
                    response = client.read_holding_registers(address=test_address, count=test_count, **get_unit_id_kwargs(unit_id))

            if response.isError():
                result["error"] = f"Device not responding: {response}"
            else:
                result["success"] = True
                # Show sample value with proper field name, unit, and correct byte order
                if response.registers:
                    raw_regs = list(response.registers)
                    if len(raw_regs) >= 2:
                        # Convert as float32 using device's byte order
                        try:
                            converted = convert_registers(raw_regs[:2], DataType.FLOAT32, byte_order)
                            value = round(converted, 2) if isinstance(converted, float) else converted
                            display_value = f"{value} {unit}".strip() if unit else value
                            result["sample_values"] = {field_name: display_value}
                        except Exception as conv_err:
                            logger.debug(f"Conversion error for {device_id}: {conv_err}")
                            result["sample_values"] = {field_name: raw_regs[0]}
                    else:
                        result["sample_values"] = {field_name: raw_regs[0]}

        except Exception as e:
            result["error"] = str(e)

        return result

    # ==================== Connection Info ====================

    def get_available_connections(self) -> List[Dict[str, Any]]:
        """Get list of available connections for register reads."""
        connections = []

        for conn_id, client in self._modbus_clients.items():
            conn_info = self._connections.get(conn_id)

            connections.append({
                "id": conn_id,
                "type": getattr(conn_info, 'connection_type', 'unknown') if conn_info else 'unknown',
                "host": getattr(conn_info, 'host', None) if conn_info else None,
                "port": getattr(conn_info, 'port', None) if conn_info else None,
                "connected": hasattr(client, 'client') and client.client is not None,
                "clients": [
                    {
                        "id": c.id,
                        "unit_id": c.unit_id,
                        "type": c.type
                    }
                    for c in getattr(conn_info, 'clients', [])
                ] if conn_info else []
            })

        return connections


    # ==================== Temporary Connection Testing ====================

    async def test_temporary_connection(
        self,
        connection_type: str,  # "tcp" or "serial"
        # TCP params
        host: Optional[str] = None,
        port: int = 502,
        # Serial params
        serial_port: Optional[str] = None,
        baudrate: int = 9600,
        parity: str = "N",
        stopbits: int = 1,
        bytesize: int = 8,
        # Test params
        unit_id: int = 1,
        test_address: int = 0,
        timeout: float = 3.0
    ) -> Dict[str, Any]:
        """
        Test a temporary Modbus connection without affecting the main config.

        This creates a transient connection, tests communication, and closes it.
        Useful for testing new devices before adding them to config.

        Args:
            connection_type: "tcp" or "serial"
            host: TCP host address
            port: TCP port (default 502)
            serial_port: Serial port path (e.g., /dev/ttyUSB0)
            baudrate: Serial baud rate
            parity: Serial parity (N, E, O)
            stopbits: Serial stop bits (1 or 2)
            bytesize: Serial data bits (7 or 8)
            unit_id: Modbus unit ID to test
            test_address: Register address to read
            timeout: Connection timeout in seconds

        Returns:
            Dict with connection test results
        """
        start_time = time.time()
        temp_client = None

        try:
            from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient

            if connection_type == "tcp":
                if not host:
                    return {
                        "success": False,
                        "error": "Host address is required for TCP connection",
                        "connection_type": "tcp",
                        "duration_ms": (time.time() - start_time) * 1000
                    }

                temp_client = AsyncModbusTcpClient(
                    host=host,
                    port=port,
                    timeout=timeout
                )

                # Connect
                connected = await asyncio.wait_for(
                    temp_client.connect(),
                    timeout=timeout
                )

                if not connected:
                    return {
                        "success": False,
                        "error": f"Failed to connect to {host}:{port}",
                        "connection_type": "tcp",
                        "host": host,
                        "port": port,
                        "duration_ms": (time.time() - start_time) * 1000
                    }

            elif connection_type == "serial":
                if not serial_port:
                    return {
                        "success": False,
                        "error": "Serial port is required for serial connection",
                        "connection_type": "serial",
                        "duration_ms": (time.time() - start_time) * 1000
                    }

                # Map parity
                parity_map = {"N": "N", "E": "E", "O": "O", "none": "N", "even": "E", "odd": "O"}
                parity_char = parity_map.get(parity.upper(), "N")

                temp_client = AsyncModbusSerialClient(
                    port=serial_port,
                    baudrate=baudrate,
                    parity=parity_char,
                    stopbits=stopbits,
                    bytesize=bytesize,
                    timeout=timeout
                )

                connected = await asyncio.wait_for(
                    temp_client.connect(),
                    timeout=timeout
                )

                if not connected:
                    return {
                        "success": False,
                        "error": f"Failed to open serial port {serial_port}",
                        "connection_type": "serial",
                        "serial_port": serial_port,
                        "baudrate": baudrate,
                        "duration_ms": (time.time() - start_time) * 1000
                    }
            else:
                return {
                    "success": False,
                    "error": f"Unsupported connection type: {connection_type}",
                    "duration_ms": (time.time() - start_time) * 1000
                }

            # Try to read a register
            connect_time = time.time()

            result = await asyncio.wait_for(
                temp_client.read_holding_registers(
                    address=test_address,
                    count=1,
                    **get_unit_id_kwargs(unit_id)
                ),
                timeout=timeout
            )

            read_time = time.time()

            if result.isError():
                return {
                    "success": False,
                    "connected": True,
                    "error": f"Device at unit {unit_id} did not respond: {result}",
                    "connection_type": connection_type,
                    "host": host if connection_type == "tcp" else None,
                    "port": port if connection_type == "tcp" else None,
                    "serial_port": serial_port if connection_type == "serial" else None,
                    "baudrate": baudrate if connection_type == "serial" else None,
                    "unit_id": unit_id,
                    "connect_ms": (connect_time - start_time) * 1000,
                    "duration_ms": (time.time() - start_time) * 1000,
                    "troubleshooting": [
                        f"Connection was established successfully",
                        f"Device at unit ID {unit_id} did not respond",
                        "Try different unit ID (1-247)",
                        "Check if device is powered and online"
                    ]
                }

            # Success!
            return {
                "success": True,
                "message": f"Connection successful! Device responded at unit {unit_id}",
                "connection_type": connection_type,
                "host": host if connection_type == "tcp" else None,
                "port": port if connection_type == "tcp" else None,
                "serial_port": serial_port if connection_type == "serial" else None,
                "baudrate": baudrate if connection_type == "serial" else None,
                "parity": parity if connection_type == "serial" else None,
                "unit_id": unit_id,
                "test_address": test_address,
                "test_value": result.registers[0] if result.registers else None,
                "connect_ms": (connect_time - start_time) * 1000,
                "read_ms": (read_time - connect_time) * 1000,
                "duration_ms": (time.time() - start_time) * 1000
            }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Connection timeout after {timeout}s",
                "connection_type": connection_type,
                "host": host if connection_type == "tcp" else None,
                "serial_port": serial_port if connection_type == "serial" else None,
                "duration_ms": (time.time() - start_time) * 1000,
                "troubleshooting": [
                    "Check network connectivity (TCP) or cable connection (Serial)",
                    "Verify host/port or serial port settings",
                    "Ensure device is powered on",
                    "Check firewall settings (TCP)"
                ]
            }
        except Exception as e:
            logger.error(f"Error testing temporary connection: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "connection_type": connection_type,
                "duration_ms": (time.time() - start_time) * 1000
            }
        finally:
            # Always close the temporary connection
            if temp_client:
                try:
                    temp_client.close()
                except Exception:
                    pass

    async def scan_serial_ports(self) -> List[Dict[str, Any]]:
        """
        Scan for available serial ports on the system.

        Returns:
            List of available serial port info
        """
        ports = []
        try:
            import serial.tools.list_ports
            for port in serial.tools.list_ports.comports():
                ports.append({
                    "device": port.device,
                    "name": port.name,
                    "description": port.description,
                    "hwid": port.hwid,
                    "manufacturer": port.manufacturer
                })
        except ImportError:
            logger.warning("pyserial not installed, cannot list serial ports")
        except Exception as e:
            logger.error(f"Error scanning serial ports: {e}")

        return ports


# Singleton accessor
_test_mode_service: Optional[TestModeService] = None


def get_test_mode_service(config_dir: str) -> TestModeService:
    """Get or create the test mode service singleton."""
    global _test_mode_service
    if _test_mode_service is None:
        _test_mode_service = TestModeService(config_dir)
    return _test_mode_service
