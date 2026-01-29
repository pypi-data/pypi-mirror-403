"""Utility classes for Modbus communication"""
import inspect
import logging
import time
from abc import ABC
from typing import Dict, Any, List, Optional
import asyncio

import pymodbus
from pymodbus.client import ModbusTcpClient, ModbusSerialClient, AsyncModbusTcpClient, AsyncModbusSerialClient
from pymodbus.client.mixin import ModbusClientMixin

from src.interfaces.modbus_client import IModbusClient


# Detect pymodbus API version for unit ID parameter
# - pymodbus 2.x: uses 'unit'
# - pymodbus 3.0-3.10: uses 'slave'
# - pymodbus 3.11+: uses 'device_id'
def _get_unit_id_param_name():
    """Detect whether pymodbus uses 'slave', 'unit', or 'device_id' parameter."""
    # First, try to detect from the method signature (most reliable)
    try:
        sig = inspect.signature(ModbusClientMixin.read_holding_registers)
        params = list(sig.parameters.keys())
        # Check in order of preference for newer versions
        if 'device_id' in params:
            return 'device_id'
        elif 'slave' in params:
            return 'slave'
        elif 'unit' in params:
            return 'unit'
    except (ValueError, TypeError):
        pass

    # Fallback: try to determine from pymodbus version
    try:
        version = pymodbus.__version__
        parts = version.split('.')
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0

        if major >= 3 and minor >= 11:
            return 'device_id'  # pymodbus 3.11+ uses device_id
        elif major >= 3:
            return 'slave'  # pymodbus 3.0-3.10 uses slave
        else:
            return 'unit'  # pymodbus 2.x uses unit
    except Exception:
        pass

    # Final fallback - try 'device_id' (newest API)
    return 'device_id'

_UNIT_ID_PARAM = _get_unit_id_param_name()


def get_unit_id_kwargs(unit_id: int) -> Dict[str, int]:
    """Get the correct keyword argument for unit ID based on pymodbus version."""
    return {_UNIT_ID_PARAM: unit_id}
from src.models.device import ModbusClient
from src.models.modbus_types import DataType, DATA_TYPE_MAPPING, RegisterType
from src.models.modbus_types import Endianness
from src.models.mqtt_trigger import WriteOperation
from src.services.register_planner import get_planner, ReadPlan, RegisterBatch
from src.services.register_cache import get_cache, DEFAULT_CONNECTION_ID

logger = logging.getLogger(__name__)


class BaseModbusHandler(IModbusClient, ABC):
    """Base implementation of ModbusConnectionHandler with common functionality.

    Features:
    - Connection health tracking with failure counting
    - Exponential backoff on repeated connection failures
    - Connection statistics for monitoring
    """

    def __init__(self):
        super().__init__()
        self.last_used = None
        self.connection_timeout = 300  # 5 minutes idle timeout
        self.is_connected = False

        # Connection health tracking
        self._connection_failures = 0
        self._max_consecutive_failures = 5
        self._last_failure_time: Optional[float] = None
        self._backoff_until: Optional[float] = None
        self._total_connects = 0
        self._total_disconnects = 0
        self._total_reads = 0
        self._total_errors = 0

    async def read_registers(self, client: ModbusClient) -> Dict[str, Any]:
        async with self.lock:
            result = {}
            if not client.registers:
                return result
            
            # Validate and ensure connection
            await self._ensure_connection()
            for register in client.registers:
                if register.count == 0:
                    count = self._get_register_count(register.data_type)
                else:
                    count = register.count
                logger.debug(f"Reading register {register.address} for client {client.id}")
                try:
                    if RegisterType(register.register_type) == RegisterType.InputRegister:
                        response = await self.client.read_input_registers(
                            address=register.address,
                            count=count,
                            **get_unit_id_kwargs(client.unit_id)
                        )
                    elif RegisterType(register.register_type) == RegisterType.HoldingRegister:
                        response = await self.client.read_holding_registers(
                            address=register.address,
                            count=count,
                            **get_unit_id_kwargs(client.unit_id)
                        )
                    else:
                        logger.error(f"Invalid register type: {register.register_type}, for register: {register.address}, of client id: {client.id}")
                    logger.debug(f"Read register {register.address} for client {client.id}")

                    if not response:
                        # await self.disconnect()
                        logger.warning(f"Got no response while reading data for client: {client.id}, register: {register.address}, returning.")
                        # return result
                        continue
                    if not response.isError():
                        register_values = response.registers if client.endianness == Endianness.BIG else response.registers[
                                                                                                         ::-1]
                        value = self.client.convert_from_registers(register_values, data_type=self._get_pymodbus_datatype_mapping(
                            data_type=register.data_type))
                        result[register.field_name] = value * register.multiplication_factor if register.multiplication_factor else value
                    else:
                        logger.error(f"Modbus error reading address {register.address}: {response}")
                except Exception as e:
                    # On error, disconnect to clean state
                    await self.disconnect()
                    self.is_connected = False
                    logger.error(f"Modbus error reading address {register.address} for client {client.id}: {e}", exc_info=True)
                    return result
                # Remove unnecessary delay between reads
                # await asyncio.sleep(0.05)

            # Check if connection should stay open (for direct RS485 without gateway)
            # Waveshare TCP gateways need disconnect to avoid unit ID mismatch due to response buffering
            keep_open = getattr(getattr(self, 'connection', None), 'keep_connection_open', False)
            if not keep_open:
                await self.disconnect()
                self.is_connected = False
                self._total_disconnects += 1
            self._total_reads += 1
        return result

    async def read_registers_batched(self, client: ModbusClient, use_cache: bool = True, connection_id: str = DEFAULT_CONNECTION_ID) -> Dict[str, Any]:
        """Read all registers using smart batching for efficiency.

        This method uses the register planner to batch contiguous registers
        and the cache to avoid redundant reads for MQTT/HTTP consolidation.

        When another client (e.g., MQTT) has already read the same physical meter
        (same unit_id, same registers), this method will reconstruct values from
        the raw register cache instead of re-reading from the device.

        Args:
            client: The ModbusClient to read from
            use_cache: Whether to check/use cached values
            connection_id: The connection ID for cache scoping (multi-connection support)

        Returns:
            Dictionary of field_name -> converted value
        """
        import time as _time
        _t_start = _time.perf_counter()
        async with self.lock:
            _t_lock_acquired = _time.perf_counter()
            _lock_wait = (_t_lock_acquired - _t_start) * 1000
            if _lock_wait > 50:  # Only log if > 50ms
                logger.debug(f"[TIMING] {client.id} lock wait: {_lock_wait:.1f}ms")

            result = {}
            if not client.registers:
                return result

            planner = get_planner()
            cache = get_cache()

            # Check client-level cache first (same client, same field names)
            if use_cache and client.use_cache:
                cached = cache.get_client_values(client.id)
                if cached is not None:
                    return cached

                # Client cache miss - check if raw registers are cached (from another client)
                # This handles the MQTT/HTTP consolidation with different field names
                reconstructed = self._try_reconstruct_from_raw_cache(client, cache, planner, connection_id)
                if reconstructed:
                    logger.info(f"Reconstructed values for {client.id} from raw register cache (another client's read)")
                    # Store in client cache for faster subsequent lookups
                    cache.store_client_values(
                        client_id=client.id,
                        unit_id=client.unit_id,
                        values=reconstructed,
                        raw_registers=None,  # Don't overwrite raw registers
                        connection_id=connection_id
                    )
                    return reconstructed

            # No cache hit - need to actually read from device
            # Reset result dict (it was set to {} at start, ensure it's still {})
            result = {}
            # Create read plan
            plan = planner.create_read_plan(client)

            if not plan.batches:
                logger.warning(f"No batches in read plan for {client.id}")
                return result

            # Track raw register values for cache storage
            raw_registers: Dict[int, int] = {}

            # Validate and ensure connection
            _t_conn_start = _time.perf_counter()
            await self._ensure_connection()
            _t_conn_done = _time.perf_counter()
            _conn_time = (_t_conn_done - _t_conn_start) * 1000
            if _conn_time > 50:  # Only log if > 50ms
                logger.debug(f"[TIMING] {client.id} connection: {_conn_time:.1f}ms")

            _t_batch_start = _time.perf_counter()
            try:
                for batch in plan.batches:
                    batch_values = await self._read_batch(batch)

                    if batch_values is None:
                        logger.warning(f"Failed to read batch starting at {batch.start_address}")
                        continue

                    # Store raw values
                    for i, val in enumerate(batch_values):
                        raw_registers[batch.start_address + i] = val

                    # Extract individual register values from batch
                    for register in batch.registers:
                        try:
                            value = self._extract_value_from_batch(batch_values, batch.start_address, register, client)
                            if value is not None:
                                result[register.field_name] = value
                        except Exception as e:
                            logger.error(f"Error extracting value for {register.field_name}: {e}", exc_info=True)

                _t_batch_done = _time.perf_counter()
                _batch_time = (_t_batch_done - _t_batch_start) * 1000

                # Store in cache if we got results
                if result:
                    logger.debug(f"Storing {len(result)} values and {len(raw_registers)} raw registers for {client.id} ({connection_id}:{client.unit_id})")
                    cache.store_client_values(
                        client_id=client.id,
                        unit_id=client.unit_id,
                        values=result,
                        raw_registers=raw_registers,
                        connection_id=connection_id
                    )

                # Log timing summary for this device (INFO only if slow, DEBUG otherwise)
                _t_total = (_time.perf_counter() - _t_start) * 1000
                _timing_msg = f"[TIMING] {client.id} unit={client.unit_id}: total={_t_total:.0f}ms batch={_batch_time:.0f}ms batches={len(plan.batches)}"
                if _t_total > 1000:  # Log as INFO if read took > 1 second
                    logger.info(_timing_msg)
                else:
                    logger.debug(_timing_msg)

            except Exception as e:
                logger.error(f"Error during batched read for {client.id}: {e}", exc_info=True)
                self._total_errors += 1
            finally:
                # Check if connection should stay open (for direct RS485 without gateway)
                # Waveshare TCP gateways need disconnect to avoid unit ID mismatch due to response buffering
                keep_open = getattr(getattr(self, 'connection', None), 'keep_connection_open', False)
                if not keep_open:
                    await self.disconnect()
                    self.is_connected = False
                    self._total_disconnects += 1
                self._total_reads += 1

            return result

    def _try_reconstruct_from_raw_cache(self, client: ModbusClient, cache, planner, connection_id: str = DEFAULT_CONNECTION_ID) -> Optional[Dict[str, Any]]:
        """Try to reconstruct client values from raw register cache.

        This is used when a different client (e.g., MQTT client) has already
        read the same physical meter (same unit_id), caching raw register values.
        We can reconstruct this client's values (possibly with different field names)
        from those cached raw registers.

        Args:
            client: The ModbusClient to reconstruct values for
            cache: The register cache
            planner: The register planner
            connection_id: The connection ID for cache scoping (multi-connection support)

        Returns:
            Dictionary of field_name -> value if all registers found in cache, else None
        """
        # Check if we have any cached registers for this unit (scoped by connection)
        if not cache.has_registers_for_unit(client.unit_id, connection_id):
            return None

        result = {}
        all_found = True

        for register in client.registers:
            # Get register count
            count = register.count if register.count > 0 else planner.get_register_size(register.data_type)

            # Try to get raw values from cache (scoped by connection)
            raw_values = cache.get_registers(client.unit_id, register.address, count, connection_id)

            if raw_values is None:
                # This register is not in cache
                all_found = False
                break

            # Apply endianness
            if client.endianness == Endianness.LITTLE:
                raw_values = raw_values[::-1]

            # Convert to final value
            try:
                pymodbus_type = self._get_pymodbus_datatype_mapping(register.data_type)
                value = self.client.convert_from_registers(raw_values, data_type=pymodbus_type)

                # Apply multiplication factor
                if register.multiplication_factor:
                    value = value * register.multiplication_factor

                result[register.field_name] = value

            except Exception as e:
                logger.warning(f"Error reconstructing {register.field_name} from cache: {e}")
                all_found = False
                break

        if all_found and result:
            return result
        return None

    async def _read_batch(self, batch: RegisterBatch) -> Optional[List[int]]:
        """Read a batch of registers.

        Args:
            batch: The batch specification

        Returns:
            List of raw 16-bit register values, or None on error
        """
        try:
            logger.debug(f"Reading batch: start={batch.start_address}, count={batch.count}, unit={batch.unit_id}")

            if batch.register_type == RegisterType.HoldingRegister:
                response = await self.client.read_holding_registers(
                    address=batch.start_address,
                    count=batch.count,
                    **get_unit_id_kwargs(batch.unit_id)
                )
            elif batch.register_type == RegisterType.InputRegister:
                response = await self.client.read_input_registers(
                    address=batch.start_address,
                    count=batch.count,
                    **get_unit_id_kwargs(batch.unit_id)
                )
            else:
                logger.error(f"Unsupported register type: {batch.register_type}")
                return None

            if response is None:
                logger.warning(f"No response for batch read at {batch.start_address}")
                return None

            if response.isError():
                logger.error(f"Modbus error reading batch at {batch.start_address}: {response}")
                return None

            logger.debug(f"Successfully read batch: {len(response.registers)} registers")
            return response.registers

        except Exception as e:
            logger.error(f"Exception reading batch at {batch.start_address}: {e}", exc_info=True)
            return None

    def _extract_value_from_batch(
        self,
        batch_values: List[int],
        batch_start: int,
        register,  # Register type
        client: ModbusClient
    ) -> Optional[Any]:
        """Extract a register value from batch data.

        Args:
            batch_values: Raw 16-bit values from batch read
            batch_start: Starting address of the batch
            register: The register to extract
            client: The ModbusClient for endianness info

        Returns:
            Converted value, or None on error
        """
        # Calculate offset within batch
        offset = register.address - batch_start

        if offset < 0 or offset >= len(batch_values):
            logger.error(f"Register {register.address} outside batch range")
            return None

        # Get register count
        count = register.count if register.count > 0 else self._get_register_count(register.data_type)

        if offset + count > len(batch_values):
            logger.error(f"Register {register.address} extends beyond batch")
            return None

        # Extract raw values
        raw_values = batch_values[offset:offset + count]

        # Apply endianness
        if client.endianness == Endianness.LITTLE:
            raw_values = raw_values[::-1]

        # Convert to final value using pymodbus
        try:
            pymodbus_type = self._get_pymodbus_datatype_mapping(register.data_type)
            value = self.client.convert_from_registers(raw_values, data_type=pymodbus_type)

            # Apply multiplication factor
            if register.multiplication_factor:
                value = value * register.multiplication_factor

            return value

        except Exception as e:
            logger.error(f"Error converting register {register.field_name}: {e}", exc_info=True)
            return None

    async def write_registers(self, client: ModbusClient, operations: List[WriteOperation]) -> Dict[int, bool]:
        async with self.lock:
            results = {}
            
            # Validate and ensure connection
            await self._ensure_connection()
            
            for i, operation in enumerate(operations):
                try:
                    if operation.register_type == RegisterType.Coil:
                        response = await self.client.write_coil(
                            address=operation.address,
                            value=bool(operation.value),
                            **get_unit_id_kwargs(client.unit_id)
                        )
                    elif operation.register_type == RegisterType.HoldingRegister:
                        # Convert value based on data type
                        data_type = DataType[operation.data_type]
                        pymodbus_type = self._get_pymodbus_datatype_mapping(data_type)
                        
                        # Apply multiplication factor if specified
                        value = operation.value
                        if operation.multiplication_factor:
                            value = value / operation.multiplication_factor
                            
                        registers = self.client.convert_to_registers(
                            value,
                            data_type=pymodbus_type,
                            number_of_registers=operation.count
                        )
                        
                        if client.endianness == Endianness.LITTLE:
                            registers = registers[::-1]
                            
                        if len(registers) == 1:
                            response = await self.client.write_register(
                                address=operation.address,
                                value=registers[0],
                                **get_unit_id_kwargs(client.unit_id)
                            )
                        else:
                            response = await self.client.write_registers(
                                address=operation.address,
                                values=registers,
                                **get_unit_id_kwargs(client.unit_id)
                            )
                    else:
                        logger.error(f"Unsupported register type for writing: {operation.register_type}")
                        results[i] = False
                        continue

                    results[i] = not response.isError() if response else False
                    
                    if not results[i]:
                        logger.error(f"Error writing to address {operation.address}: {response}")
                except Exception as e:
                    logger.error(f"Exception writing to address {operation.address}: {e}")
                    results[i] = False

            # Disconnect after each write to avoid unit ID mismatch with Waveshare gateway
            await self.disconnect()
            self.is_connected = False
            return results

    async def send_modbus_command(self, client: ModbusClient, command: bytes) -> bool:
        async with self.lock:
            if self.client.connected:
                await self.disconnect()
            try:
                # Create a new connection based on the client type
                if isinstance(self.client, AsyncModbusTcpClient):
                    new_client = ModbusTcpClient(
                        host=self.client.comm_params.host,
                        port=self.client.comm_params.port,
                        timeout=self.client.comm_params.timeout_connect,
                        retries=self.client.ctx.retries,
                    )
                elif isinstance(self.client, AsyncModbusSerialClient):  # Serial connection
                    new_client = ModbusSerialClient(
                        port=self.client.comm_params.host,
                        baudrate=self.client.comm_params.baudrate,
                        bytesize=self.client.comm_params.bytesize,
                        parity=self.client.comm_params.parity,
                        stopbits=self.client.comm_params.stopbits,
                        timeout=self.client.comm_params.timeout_connect,
                        retries=self.client.ctx.retries,
                    )
                else:
                    logger.error("Unrecognised client type")
                    return False
                if not new_client.connect():
                    logger.error("Failed to connect to Modbus device")
                    return False

                try:
                    logger.info(f"Sending command: {command.hex()}")
                    new_client.send(command)
                    return True
                except Exception as e:
                    logger.error(f"Exception sending command {command.hex()}: {e}")
                    return False
                finally:
                    new_client.close()

            except Exception as e:
                logger.error(f"Exception sending command {command.hex()}: {e}")
                return False
            finally:
                await self.disconnect()

    def _get_register_count(self, data_type: DataType) -> int:
        """Get the number of registers to read based on data type"""
        register_counts = {
            DataType.INT16.name: 1,
            DataType.INT32.name: 2,
            DataType.INT64.name: 4,
            DataType.UINT16.name: 1,
            DataType.UINT32.name: 2,
            DataType.UINT64.name: 4,
            DataType.FLOAT32.name: 2,
            DataType.FLOAT64.name: 4,
            DataType.STRING.name: 2,
        }
        return register_counts.get(data_type.name, 0)

    def _get_pymodbus_datatype_mapping(self, data_type: DataType) -> DataType:
        return DATA_TYPE_MAPPING.get(data_type.name, ModbusClientMixin.DATATYPE.FLOAT32)
    
    async def _ensure_connection(self, max_retries: int = 3) -> None:
        """Ensure the client is connected with retry logic and backoff protection.

        Features:
        - Exponential backoff after repeated failures
        - Connection health tracking
        - Prevents rapid reconnection attempts that can overwhelm devices
        """
        current_time = time.time()

        # Check if we should back off from connection attempts
        if self._should_backoff():
            remaining = self._backoff_until - current_time if self._backoff_until else 0
            raise ConnectionError(
                f"Backing off from connection attempts ({remaining:.1f}s remaining)"
            )

        # Check if connection is stale (idle > 5 minutes)
        if self.is_connected and self.last_used:
            idle_time = current_time - self.last_used
            if idle_time > self.connection_timeout:
                logger.info(f"Connection idle for {idle_time:.1f}s, reconnecting...")
                await self.disconnect()
                self.is_connected = False
                self._total_disconnects += 1

        # Connect if not connected
        if not self.is_connected or not self.client.connected:
            for attempt in range(max_retries):
                try:
                    logger.debug(f"Attempting to connect (attempt {attempt + 1}/{max_retries})")
                    await self.client.connect()

                    if self.client.connected:
                        self.is_connected = True
                        self.last_used = current_time
                        self._record_connection_success()
                        logger.debug(f"Connected successfully")
                        return

                except Exception as e:
                    logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1.0 * (attempt + 1))  # Exponential backoff

            # All attempts failed
            self._record_connection_failure()
            raise ConnectionError(f"Failed to establish connection after {max_retries} attempts")

        # Update last used time for existing connection
        self.last_used = current_time
    
    async def _validate_connection(self) -> bool:
        """Validate if the current connection is healthy."""
        if not self.client or not self.client.connected:
            return False

        try:
            # Try a simple read to validate connection health
            # This is a lightweight way to check if the connection is still alive
            if hasattr(self.client, 'transport') and self.client.transport:
                return not self.client.transport.is_closing()
            return True
        except Exception:
            return False

    def _should_backoff(self) -> bool:
        """Check if we should back off from connection attempts."""
        if self._backoff_until is None:
            return False
        if time.time() >= self._backoff_until:
            self._backoff_until = None
            return False
        return True

    def _calculate_backoff(self) -> float:
        """Calculate backoff duration based on failure count."""
        # Exponential backoff: 2^failures seconds, max 60 seconds
        backoff = min(60.0, 2.0 ** self._connection_failures)
        return backoff

    def _record_connection_success(self):
        """Record a successful connection/operation."""
        self._connection_failures = 0
        self._backoff_until = None
        self._total_connects += 1

    def _record_connection_failure(self):
        """Record a connection failure and set backoff if needed."""
        self._connection_failures += 1
        self._last_failure_time = time.time()
        self._total_errors += 1

        if self._connection_failures >= self._max_consecutive_failures:
            backoff_time = self._calculate_backoff()
            self._backoff_until = time.time() + backoff_time
            logger.warning(
                f"Modbus connection failed {self._connection_failures} times, "
                f"backing off for {backoff_time:.1f}s"
            )

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics for monitoring."""
        return {
            "total_connects": self._total_connects,
            "total_disconnects": self._total_disconnects,
            "total_reads": self._total_reads,
            "total_errors": self._total_errors,
            "consecutive_failures": self._connection_failures,
            "is_connected": self.is_connected,
            "backing_off": self._should_backoff(),
            "backoff_remaining": (
                max(0, self._backoff_until - time.time())
                if self._backoff_until else 0
            )
        }

def _compute_crc(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc

def build_flash_on_command(slave_id: int, flash_width_ms: int, channel: int) -> bytes:
    """Constructs the exact byte sequence for the flash command."""
    # Command structure: [SlaveID, 0x05, 0x02, RelayAddr, DelayHigh, DelayLow]
    func_code = 0x05  # Write Single Coil
    command = 0x02  # 0x02 = Flash ON
    
    logger.debug(f"Building flash command with: slave_id={slave_id}, flash_width_ms={flash_width_ms}, channel={channel}")
    
    flash_width_ms = int(flash_width_ms * 10)
    logger.debug(f"Adjusted flash_width_ms (multiply by 10): {flash_width_ms}")

    # Log individual byte values before construction
    logger.debug(f"Byte values to be used:")
    logger.debug(f"  slave_id: {slave_id} (0x{slave_id:02x})")
    logger.debug(f"  func_code: {func_code} (0x{func_code:02x})")
    logger.debug(f"  command: {command} (0x{command:02x})")
    logger.debug(f"  channel: {channel} (0x{channel:02x})")
    logger.debug(f"  flash_width_high: {(flash_width_ms >> 8) & 0xFF} (0x{((flash_width_ms >> 8) & 0xFF):02x})")
    logger.debug(f"  flash_width_low: {flash_width_ms & 0xFF} (0x{(flash_width_ms & 0xFF):02x})")

    # Construct the message (excluding CRC)
    try:
        msg = bytes([
            slave_id,
            func_code,
            command,
            channel,
            (flash_width_ms >> 8) & 0xFF,  # High byte of delay
            flash_width_ms & 0xFF  # Low byte of delay
        ])
        logger.debug(f"Successfully constructed message bytes: {msg.hex()}")
    except ValueError as e:
        logger.error(f"Failed to construct message bytes: {str(e)}")
        raise

    # Compute CRC16
    crc = _compute_crc(msg)
    crc_bytes = bytes([crc & 0xFF, (crc >> 8) & 0xFF])
    logger.debug(f"CRC bytes: {crc_bytes.hex()}")

    # Full command
    full_command = msg + crc_bytes
    logger.debug(f"Final command bytes: {full_command.hex()}")
    return full_command
