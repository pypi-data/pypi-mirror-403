"""Modbus TCP Server for exposing cached register values.

This module implements a Modbus TCP server that:
- Serves register values from the cache
- Maintains same register addresses as original meters
- Runs on port 4196 (same as Waveshare converters)
- Supports multiple unit IDs for different meters
- Supports virtual unit ID mapping for multi-connection setups
"""

import asyncio
import logging
from typing import Dict, Optional, Any, Set

from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore.store import BaseModbusDataBlock
from pymodbus.server import StartAsyncTcpServer

# ModbusSlaveContext import - try multiple locations for compatibility
try:
    from pymodbus.datastore import ModbusSlaveContext
except ImportError:
    try:
        from pymodbus.datastore.context import ModbusSlaveContext
    except ImportError:
        ModbusSlaveContext = None  # Will use custom context

# ModbusDeviceIdentification moved/removed in pymodbus 3.6+
try:
    from pymodbus.device import ModbusDeviceIdentification
except ImportError:
    ModbusDeviceIdentification = None

from src.services.register_cache import RegisterCache, get_cache

logger = logging.getLogger(__name__)


class CacheBackedDataBlock(BaseModbusDataBlock):
    """A Modbus data block backed by the register cache.

    This data block serves register values from the cache,
    making them available to external Modbus TCP clients.

    For multi-connection setups, unit_id is treated as a virtual unit ID
    and resolved to (connection_id, physical_unit_id) using the cache's
    virtual unit mapping.
    """

    def __init__(self, cache: RegisterCache, unit_id: int, address_offset: int = 0):
        """Initialize the cache-backed data block.

        Args:
            cache: The register cache to read from
            unit_id: The Modbus unit ID this block represents (virtual unit ID)
            address_offset: Optional offset for address translation
        """
        super().__init__()
        self.cache = cache
        self.unit_id = unit_id  # This is the virtual unit ID seen by TCP clients
        self.address_offset = address_offset
        self.default_value = 0

    def validate(self, address: int, count: int = 1) -> bool:
        """Check if the given address range is valid.

        We accept any address and return default values for uncached registers.
        """
        # Accept addresses 0-65535 (full Modbus address space)
        return 0 <= address <= 65535 and count > 0 and (address + count) <= 65536

    def getValues(self, address: int, count: int = 1):
        """Get values from the cache.

        Args:
            address: Starting register address (pymodbus adds +1 internally, so we subtract 1)
            count: Number of registers to read

        Returns:
            List of register values

        Note:
            Uses get_registers_by_virtual_unit to automatically resolve
            virtual unit IDs to (connection_id, physical_unit_id) for
            multi-connection setups.

            IMPORTANT: We use get_cache() directly here instead of self.cache because
            pymodbus async server can lose object references across async boundaries.
            This ensures we always access the global singleton cache that the polling
            service is writing to.
        """
        # PyModbus adds +1 to address internally before calling getValues
        # We need to subtract 1 to get the actual register address that matches our cache
        actual_address = address - 1 + self.address_offset

        # IMPORTANT: Always get the global cache instance to avoid pymodbus async issues
        # where object references can be lost across async boundaries
        cache = get_cache()

        # Log at DEBUG level to avoid I/O overhead on hot path
        logger.debug(f"TCP Gateway getValues: virtual_unit={self.unit_id}, addr={actual_address}, count={count}")

        # Try to get from cache using virtual unit ID resolution
        # This will automatically resolve virtual unit -> (connection, physical_unit)
        cached = cache.get_registers_by_virtual_unit(self.unit_id, actual_address, count)

        if cached is not None:
            return cached

        # If not in cache, return default values
        logger.debug(f"TCP Gateway MISS: virtual_unit {self.unit_id} @ {actual_address}, returning {count} defaults")
        return [self.default_value] * count

    def setValues(self, address: int, values: list):
        """Set values - not supported for cache-backed blocks.

        The cache is read-only from the TCP server perspective.
        Writes are ignored but logged.
        """
        logger.warning(f"Write attempt to cache-backed block ignored: unit {self.unit_id} @ {address}")

    def default(self, count: int, value: bool = False) -> list:
        """Return default values."""
        return [self.default_value] * count

    async def async_getValues(self, address: int, count: int = 1):
        """Async version of getValues - delegates to sync version.

        Note: We delegate to getValues which uses get_cache() directly
        to avoid pymodbus async reference issues.
        """
        return self.getValues(address, count)


class MultiUnitSlaveContext:
    """A slave context that supports multiple unit IDs with cache-backed storage."""

    def __init__(self, cache: RegisterCache, unit_ids: Set[int]):
        """Initialize multi-unit context.

        Args:
            cache: The register cache
            unit_ids: Set of unit IDs to support
        """
        self.cache = cache
        self.unit_ids = unit_ids
        self._contexts: Dict[int, ModbusSlaveContext] = {}

        # Create a context for each unit ID
        for unit_id in unit_ids:
            # Create cache-backed data blocks
            hr_block = CacheBackedDataBlock(cache, unit_id)
            ir_block = CacheBackedDataBlock(cache, unit_id)

            # Create slave context with these blocks
            # di=discrete inputs, co=coils, hr=holding registers, ir=input registers
            # Note: pymodbus 3.x has a bug where all stores check 'if di is not None' instead
            # of checking their own parameter. We must provide di to avoid this bug.
            from pymodbus.datastore import ModbusSequentialDataBlock
            context = ModbusSlaveContext(
                di=ModbusSequentialDataBlock.create(),  # Must provide di due to pymodbus bug
                co=ModbusSequentialDataBlock.create(),
                hr=hr_block,
                ir=ir_block
            )
            self._contexts[unit_id] = context

    def __getitem__(self, unit_id: int) -> Optional[ModbusSlaveContext]:
        """Get context for a specific unit ID."""
        return self._contexts.get(unit_id)

    def __contains__(self, unit_id: int) -> bool:
        """Check if unit ID is supported."""
        return unit_id in self._contexts

    def __iter__(self):
        """Iterate over unit IDs."""
        return iter(self._contexts.items())

    def keys(self):
        """Return unit IDs (required by pymodbus)."""
        return self._contexts.keys()

    def add_unit(self, unit_id: int):
        """Add a new unit ID dynamically."""
        if unit_id not in self._contexts:
            hr_block = CacheBackedDataBlock(self.cache, unit_id)
            ir_block = CacheBackedDataBlock(self.cache, unit_id)
            # Note: pymodbus 3.x has a bug where all stores check 'if di is not None' instead
            # of checking their own parameter. We must provide di to avoid this bug.
            from pymodbus.datastore import ModbusSequentialDataBlock
            context = ModbusSlaveContext(
                di=ModbusSequentialDataBlock.create(),  # Must provide di due to pymodbus bug
                co=ModbusSequentialDataBlock.create(),
                hr=hr_block,
                ir=ir_block
            )
            self._contexts[unit_id] = context
            self.unit_ids.add(unit_id)
            logger.info(f"Added unit ID {unit_id} to TCP server")


class DynamicServerContext(ModbusServerContext):
    """Server context that dynamically handles any unit ID request."""

    def __init__(self, cache: RegisterCache, known_unit_ids: Optional[Set[int]] = None):
        """Initialize with cache and optional known unit IDs.

        Args:
            cache: The register cache
            known_unit_ids: Set of initially known unit IDs
        """
        self.cache = cache
        self.multi_unit = MultiUnitSlaveContext(cache, known_unit_ids or set())
        super().__init__(slaves=self.multi_unit, single=False)

    def __getitem__(self, slave_id: int):
        """Get or create context for any slave ID."""
        if slave_id not in self.multi_unit:
            # Dynamically add new unit IDs
            self.multi_unit.add_unit(slave_id)
        return self.multi_unit[slave_id]

    def __contains__(self, slave_id: int) -> bool:
        """Always return True - we support any slave ID."""
        return True


class ModbusTCPServer:
    """Modbus TCP Server that serves cached register values."""

    DEFAULT_PORT = 4196  # Same as Waveshare

    def __init__(
        self,
        cache: Optional[RegisterCache] = None,
        host: str = "0.0.0.0",
        port: int = DEFAULT_PORT,
        unit_ids: Optional[Set[int]] = None
    ):
        """Initialize the Modbus TCP server.

        Args:
            cache: Register cache to serve from (uses global if not provided)
            host: Host address to bind to
            port: Port to listen on (default 4196)
            unit_ids: Initial set of unit IDs to support
        """
        self.cache = cache or get_cache()
        self.host = host
        self.port = port
        self.unit_ids = unit_ids or set()

        self._server = None
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Device identification (optional, not available in all pymodbus versions)
        self.identity = None
        if ModbusDeviceIdentification is not None:
            self.identity = ModbusDeviceIdentification()
            self.identity.VendorName = "DataSkipper"
            self.identity.ProductCode = "DSB-Gateway"
            self.identity.VendorUrl = "https://dataskipper.io"
            self.identity.ProductName = "Modbus Gateway"
            self.identity.ModelName = "RTU-Gateway"
            self.identity.MajorMinorRevision = "1.0.0"

    def add_unit_id(self, unit_id: int):
        """Add a unit ID to the server."""
        self.unit_ids.add(unit_id)
        logger.info(f"Registered unit ID {unit_id} with TCP server")

    async def start(self):
        """Start the Modbus TCP server."""
        if self._running:
            logger.warning("Modbus TCP server already running")
            return

        try:
            # Create server context with cache-backed storage
            context = DynamicServerContext(self.cache, self.unit_ids)

            logger.info(f"Starting Modbus TCP server on {self.host}:{self.port}")
            logger.info(f"Serving unit IDs: {self.unit_ids if self.unit_ids else 'dynamic'}")

            self._running = True

            # Start the async TCP server
            # Note: pymodbus 3.x doesn't use allow_reuse_address parameter
            server_kwargs = {
                "context": context,
                "address": (self.host, self.port),
            }
            if self.identity is not None:
                server_kwargs["identity"] = self.identity
            await StartAsyncTcpServer(**server_kwargs)

        except Exception as e:
            logger.error(f"Failed to start Modbus TCP server: {e}")
            self._running = False
            raise

    async def start_background(self):
        """Start the server as a background task."""
        if self._task is not None and not self._task.done():
            logger.warning("Modbus TCP server task already running")
            return

        self._task = asyncio.create_task(self._run_server())
        logger.info("Modbus TCP server started in background")

    async def _run_server(self):
        """Run the server (for background task)."""
        try:
            await self.start()
        except asyncio.CancelledError:
            logger.info("Modbus TCP server cancelled")
        except Exception as e:
            logger.error(f"Modbus TCP server error: {e}")
        finally:
            self._running = False

    async def stop(self):
        """Stop the Modbus TCP server."""
        if not self._running:
            return

        logger.info("Stopping Modbus TCP server...")
        self._running = False

        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("Modbus TCP server stopped")

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running

    def get_status(self) -> Dict[str, Any]:
        """Get server status information."""
        virtual_mappings = self.cache.get_virtual_unit_mappings()
        return {
            "running": self._running,
            "host": self.host,
            "port": self.port,
            "unit_ids": list(self.unit_ids),
            "virtual_unit_mappings": {
                vid: {
                    "physical_unit_id": m.physical_unit_id,
                    "connection_id": m.connection_id,
                    "offset": m.offset
                }
                for vid, m in virtual_mappings.items()
            },
            "cache_stats": self.cache.get_stats()
        }


# Global server instance
_server: Optional[ModbusTCPServer] = None


def get_tcp_server(
    cache: Optional[RegisterCache] = None,
    port: int = ModbusTCPServer.DEFAULT_PORT
) -> ModbusTCPServer:
    """Get or create the global Modbus TCP server instance."""
    global _server
    if _server is None:
        _server = ModbusTCPServer(cache=cache, port=port)
    return _server
