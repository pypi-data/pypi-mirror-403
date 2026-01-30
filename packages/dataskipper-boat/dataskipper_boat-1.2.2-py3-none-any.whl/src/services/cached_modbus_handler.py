"""Cached Modbus Handler with smart batch reading.

This module provides an enhanced Modbus handler that:
- Uses smart register planning for efficient batch reads
- Caches values for MQTT/HTTP consolidation
- Stores raw registers for TCP gateway exposure
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List

from src.models.device import ModbusClient, Register
from src.models.modbus_types import RegisterType, Endianness
from src.services.register_planner import RegisterPlanner, ReadPlan, RegisterBatch, get_planner
from src.services.register_cache import RegisterCache, get_cache
from src.utils.modbus_utils import get_unit_id_kwargs

logger = logging.getLogger(__name__)


class CachedModbusHandler:
    """Enhanced Modbus handler with caching and batch reading."""

    def __init__(
        self,
        base_client,  # The underlying async Modbus client (TCP or Serial)
        planner: Optional[RegisterPlanner] = None,
        cache: Optional[RegisterCache] = None
    ):
        """Initialize the cached handler.

        Args:
            base_client: The underlying pymodbus async client
            planner: Register planner (uses global if not provided)
            cache: Register cache (uses global if not provided)
        """
        self.base_client = base_client
        self.planner = planner or get_planner()
        self.cache = cache or get_cache()
        self._plans_cache: Dict[str, ReadPlan] = {}

    async def read_registers_batched(self, client: ModbusClient) -> Dict[str, Any]:
        """Read all registers for a client using batched reads.

        Args:
            client: The ModbusClient to read from

        Returns:
            Dictionary of field_name -> converted value
        """
        result = {}

        if not client.registers:
            return result

        # Check cache first if enabled
        if client.use_cache:
            cached = self.cache.get_client_values(client.id)
            if cached is not None:
                logger.debug(f"Using cached values for {client.id}")
                return cached

        # Create read plan
        plan = self.planner.create_read_plan(client)

        if not plan.batches:
            logger.warning(f"No batches in read plan for {client.id}")
            return result

        # Track raw register values for cache storage
        raw_registers: Dict[int, int] = {}

        # Execute batched reads
        try:
            for batch in plan.batches:
                batch_values = await self._read_batch(batch, client)

                if batch_values is None:
                    logger.warning(f"Failed to read batch starting at {batch.start_address}")
                    continue

                # Store raw values
                for i, val in enumerate(batch_values):
                    raw_registers[batch.start_address + i] = val

                # Extract individual register values from batch
                for register in batch.registers:
                    try:
                        value = self._extract_value(batch_values, batch.start_address, register, client)
                        if value is not None:
                            result[register.field_name] = value
                    except Exception as e:
                        logger.error(f"Error extracting value for {register.field_name}: {e}")

            # Store in cache
            if result:
                self.cache.store_client_values(
                    client_id=client.id,
                    unit_id=client.unit_id,
                    values=result,
                    raw_registers=raw_registers
                )

        except Exception as e:
            logger.error(f"Error during batched read for {client.id}: {e}")

        return result

    async def _read_batch(self, batch: RegisterBatch, client: ModbusClient) -> Optional[List[int]]:
        """Read a batch of registers.

        Args:
            batch: The batch specification
            client: The ModbusClient for connection info

        Returns:
            List of raw 16-bit register values, or None on error
        """
        try:
            if batch.register_type == RegisterType.HoldingRegister:
                response = await self.base_client.read_holding_registers(
                    address=batch.start_address,
                    count=batch.count,
                    **get_unit_id_kwargs(batch.unit_id)
                )
            elif batch.register_type == RegisterType.InputRegister:
                response = await self.base_client.read_input_registers(
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

            return response.registers

        except Exception as e:
            logger.error(f"Exception reading batch at {batch.start_address}: {e}")
            return None

    def _extract_value(
        self,
        batch_values: List[int],
        batch_start: int,
        register: Register,
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
        count = register.count if register.count > 0 else self.planner.get_register_size(register.data_type)

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
            from pymodbus.client.mixin import ModbusClientMixin
            from src.models.modbus_types import DATA_TYPE_MAPPING

            # Get pymodbus data type
            pymodbus_type = DATA_TYPE_MAPPING.get(register.data_type.name, ModbusClientMixin.DATATYPE.FLOAT32)

            # Create a temporary client mixin for conversion
            value = ModbusClientMixin.convert_from_registers(raw_values, data_type=pymodbus_type)

            # Apply multiplication factor
            if register.multiplication_factor:
                value = value * register.multiplication_factor

            return value

        except Exception as e:
            logger.error(f"Error converting register {register.field_name}: {e}")
            return None

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()

    def get_plan_efficiency(self, client: ModbusClient) -> Dict:
        """Get read plan efficiency metrics for a client."""
        plan = self.planner.create_read_plan(client)
        return self.planner.analyze_efficiency(plan)
