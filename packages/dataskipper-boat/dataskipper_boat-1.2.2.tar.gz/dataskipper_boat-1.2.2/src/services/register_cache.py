"""Register Cache for Modbus data.

This module provides an in-memory cache for register values with:
- Configurable TTL (default 60 seconds / 1 minute)
- Thread-safe operations for concurrent TCP requests
- Support for both gateway and internal MQTT/HTTP consolidation
- Storage by (connection_id, unit_id, register_address) for multi-connection support
- Virtual unit ID mapping for TCP gateway (resolves virtual → physical unit)
"""

import logging
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

# Default connection ID for backward compatibility with single-connection setups
DEFAULT_CONNECTION_ID = "default"


@dataclass
class CachedValue:
    """A cached register value with metadata."""
    value: int  # Raw 16-bit register value
    timestamp: float  # Unix timestamp when cached
    field_name: Optional[str] = None  # Original field name from config
    data_type: Optional[str] = None  # Original data type

    def is_expired(self, ttl: float) -> bool:
        """Check if this cached value has expired."""
        return (time.time() - self.timestamp) > ttl

    def age(self) -> float:
        """Get age of this cached value in seconds."""
        return time.time() - self.timestamp


@dataclass
class ClientCacheEntry:
    """Cache entry for a complete client read."""
    client_id: str
    values: Dict[str, Any]  # field_name -> converted value
    raw_registers: Dict[int, int]  # address -> raw 16-bit value
    timestamp: float
    unit_id: int
    connection_id: str = DEFAULT_CONNECTION_ID  # Connection this client belongs to

    def is_expired(self, ttl: float) -> bool:
        """Check if this entry has expired."""
        return (time.time() - self.timestamp) > ttl

    def age(self) -> float:
        """Get age of this entry in seconds."""
        return time.time() - self.timestamp


@dataclass
class VirtualUnitMapping:
    """Mapping from virtual unit ID to physical unit ID and connection."""
    virtual_unit_id: int
    physical_unit_id: int
    connection_id: str
    offset: int  # The offset used (virtual = physical + offset)


class RegisterCache:
    """Thread-safe cache for Modbus register values.

    Supports two access patterns:
    1. By (connection_id, unit_id, address) - for Modbus TCP gateway with multi-connection
    2. By client_id - for internal MQTT/HTTP consolidation

    Features:
    - LRU eviction when cache size exceeds max_entries
    - Virtual unit ID mapping for TCP gateway (resolves virtual → physical unit)
    - Backward compatible with single-connection setups (uses DEFAULT_CONNECTION_ID)
    """

    DEFAULT_TTL = 60  # 1 minute
    DEFAULT_MAX_REGISTER_ENTRIES = 10000  # Max register cache entries
    DEFAULT_MAX_CLIENT_ENTRIES = 500  # Max client cache entries

    def __init__(
        self,
        ttl: float = DEFAULT_TTL,
        max_register_entries: int = DEFAULT_MAX_REGISTER_ENTRIES,
        max_client_entries: int = DEFAULT_MAX_CLIENT_ENTRIES
    ):
        """Initialize the register cache.

        Args:
            ttl: Time-to-live in seconds for cached values (default 60s)
            max_register_entries: Maximum number of register cache entries (default 10000)
            max_client_entries: Maximum number of client cache entries (default 500)
        """
        self.ttl = ttl
        self.max_register_entries = max_register_entries
        self.max_client_entries = max_client_entries
        self._lock = threading.RLock()

        # Register-level cache: (connection_id, unit_id, address) -> CachedValue
        # For backward compatibility, connection_id defaults to DEFAULT_CONNECTION_ID
        self._register_cache: Dict[Tuple[str, int, int], CachedValue] = {}

        # Client-level cache: client_id -> ClientCacheEntry
        self._client_cache: Dict[str, ClientCacheEntry] = {}

        # Mapping: client_id -> (connection_id, unit_id) (for lookups)
        self._client_unit_map: Dict[str, Tuple[str, int]] = {}

        # Virtual unit ID mapping: virtual_unit_id -> VirtualUnitMapping
        # This allows TCP gateway to resolve virtual unit → (connection, physical unit)
        self._virtual_unit_map: Dict[int, VirtualUnitMapping] = {}

        # Stats
        self._hits = 0
        self._misses = 0
        self._updates = 0
        self._evictions = 0

    def set_ttl(self, ttl: float):
        """Update the cache TTL."""
        with self._lock:
            self.ttl = ttl

    def _evict_oldest_registers(self):
        """Evict oldest 10% of register entries when cache is full (LRU eviction).

        Must be called while holding the lock.
        """
        if len(self._register_cache) <= self.max_register_entries:
            return

        # Sort by timestamp (oldest first)
        sorted_entries = sorted(
            self._register_cache.items(),
            key=lambda x: x[1].timestamp
        )

        # Evict oldest 10%
        evict_count = max(1, self.max_register_entries // 10)
        for key, _ in sorted_entries[:evict_count]:
            del self._register_cache[key]

        self._evictions += evict_count
        logger.debug(f"Evicted {evict_count} oldest register entries (LRU)")

    def _evict_oldest_clients(self):
        """Evict oldest 10% of client entries when cache is full (LRU eviction).

        Must be called while holding the lock.
        """
        if len(self._client_cache) <= self.max_client_entries:
            return

        # Sort by timestamp (oldest first)
        sorted_entries = sorted(
            self._client_cache.items(),
            key=lambda x: x[1].timestamp
        )

        # Evict oldest 10%
        evict_count = max(1, self.max_client_entries // 10)
        for cid, _ in sorted_entries[:evict_count]:
            del self._client_cache[cid]
            if cid in self._client_unit_map:
                del self._client_unit_map[cid]

        self._evictions += evict_count
        logger.debug(f"Evicted {evict_count} oldest client entries (LRU)")

    def store_client_values(
        self,
        client_id: str,
        unit_id: int,
        values: Dict[str, Any],
        raw_registers: Optional[Dict[int, int]] = None,
        connection_id: str = DEFAULT_CONNECTION_ID
    ):
        """Store values for a client after a read operation.

        Args:
            client_id: The Modbus client ID
            unit_id: The Modbus unit/slave ID
            values: Dictionary of field_name -> converted value
            raw_registers: Optional dictionary of address -> raw 16-bit value
            connection_id: The connection ID (for multi-connection support)
        """
        with self._lock:
            timestamp = time.time()

            # Store client-level entry
            entry = ClientCacheEntry(
                client_id=client_id,
                values=values.copy(),
                raw_registers=raw_registers.copy() if raw_registers else {},
                timestamp=timestamp,
                unit_id=unit_id,
                connection_id=connection_id
            )
            self._client_cache[client_id] = entry
            self._client_unit_map[client_id] = (connection_id, unit_id)

            # Also store at register level for TCP gateway
            if raw_registers:
                for address, raw_value in raw_registers.items():
                    key = (connection_id, unit_id, address)
                    self._register_cache[key] = CachedValue(
                        value=raw_value,
                        timestamp=timestamp
                    )
                logger.debug(f"Stored {len(raw_registers)} raw registers for {connection_id}:{unit_id}")

            self._updates += 1
            logger.debug(f"Cached {len(values)} values for client {client_id} ({connection_id}:{unit_id})")

            # Evict oldest entries if cache is full
            self._evict_oldest_registers()
            self._evict_oldest_clients()

    def store_raw_registers(
        self,
        unit_id: int,
        start_address: int,
        values: List[int],
        timestamp: Optional[float] = None,
        connection_id: str = DEFAULT_CONNECTION_ID
    ):
        """Store raw register values from a batch read.

        Args:
            unit_id: The Modbus unit/slave ID
            start_address: Starting register address
            values: List of 16-bit register values
            timestamp: Optional timestamp (defaults to now)
            connection_id: The connection ID (for multi-connection support)
        """
        with self._lock:
            ts = timestamp or time.time()
            for i, value in enumerate(values):
                address = start_address + i
                key = (connection_id, unit_id, address)
                self._register_cache[key] = CachedValue(value=value, timestamp=ts)
            self._updates += 1

            # Evict oldest entries if cache is full
            self._evict_oldest_registers()

    def get_client_values(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get cached values for a client.

        Args:
            client_id: The Modbus client ID

        Returns:
            Dictionary of field_name -> value if found and not expired, else None
        """
        with self._lock:
            entry = self._client_cache.get(client_id)
            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired(self.ttl):
                self._misses += 1
                logger.debug(f"Cache expired for client {client_id} (age: {entry.age():.1f}s)")
                return None

            self._hits += 1
            logger.debug(f"Cache hit for client {client_id} (age: {entry.age():.1f}s)")
            return entry.values.copy()

    def has_registers_for_unit(self, unit_id: int, connection_id: str = DEFAULT_CONNECTION_ID) -> bool:
        """Check if we have any cached registers for a unit ID.

        This is useful for checking if another client (with different field names)
        has already read the same physical meter.

        Args:
            unit_id: The Modbus unit/slave ID
            connection_id: The connection ID (for multi-connection support)
        """
        with self._lock:
            for (conn_id, uid, _), cached in self._register_cache.items():
                if conn_id == connection_id and uid == unit_id and not cached.is_expired(self.ttl):
                    return True
            return False

    def get_raw_register_timestamp(self, unit_id: int, address: int, connection_id: str = DEFAULT_CONNECTION_ID) -> Optional[float]:
        """Get the timestamp of a cached raw register.

        Args:
            unit_id: The Modbus unit/slave ID
            address: The register address
            connection_id: The connection ID (for multi-connection support)

        Returns:
            Timestamp when cached, or None if not found/expired
        """
        with self._lock:
            key = (connection_id, unit_id, address)
            cached = self._register_cache.get(key)
            if cached is None or cached.is_expired(self.ttl):
                return None
            return cached.timestamp

    def get_register(self, unit_id: int, address: int, connection_id: str = DEFAULT_CONNECTION_ID) -> Optional[int]:
        """Get a single cached register value.

        Args:
            unit_id: The Modbus unit/slave ID
            address: The register address
            connection_id: The connection ID (for multi-connection support)

        Returns:
            The raw 16-bit register value if found and not expired, else None
        """
        with self._lock:
            key = (connection_id, unit_id, address)
            cached = self._register_cache.get(key)
            if cached is None:
                self._misses += 1
                return None

            if cached.is_expired(self.ttl):
                self._misses += 1
                return None

            self._hits += 1
            return cached.value

    def get_registers(self, unit_id: int, start_address: int, count: int, connection_id: str = DEFAULT_CONNECTION_ID) -> Optional[List[int]]:
        """Get a range of cached register values.

        Args:
            unit_id: The Modbus unit/slave ID
            start_address: Starting register address
            count: Number of registers to get
            connection_id: The connection ID (for multi-connection support)

        Returns:
            List of register values if ALL are found and not expired, else None
        """
        with self._lock:
            values = []
            for i in range(count):
                address = start_address + i
                key = (connection_id, unit_id, address)
                cached = self._register_cache.get(key)

                if cached is None or cached.is_expired(self.ttl):
                    self._misses += 1
                    return None

                values.append(cached.value)

            self._hits += 1
            return values

    def get_registers_by_virtual_unit(self, virtual_unit_id: int, start_address: int, count: int) -> Optional[List[int]]:
        """Get a range of cached register values using virtual unit ID.

        This method resolves the virtual unit ID to (connection_id, physical_unit_id)
        using the virtual unit mapping, then retrieves registers.

        Note: This method intentionally does NOT acquire the lock for performance.
        Python dicts are thread-safe for single read operations, and we accept
        occasional inconsistency in exchange for not blocking polling tasks.

        Args:
            virtual_unit_id: The virtual Modbus unit ID (as seen by TCP gateway clients)
            start_address: Starting register address
            count: Number of registers to get

        Returns:
            List of register values if ALL are found and not expired, else None
        """
        # Resolve virtual unit ID without lock (dict.get is atomic)
        mapping = self._virtual_unit_map.get(virtual_unit_id)
        if mapping:
            connection_id = mapping.connection_id
            physical_unit_id = mapping.physical_unit_id
        else:
            # No mapping - assume it's a direct unit ID with default connection
            connection_id = DEFAULT_CONNECTION_ID
            physical_unit_id = virtual_unit_id

        # Get registers without lock (dict.get is atomic)
        values = []
        for i in range(count):
            address = start_address + i
            key = (connection_id, physical_unit_id, address)
            cached = self._register_cache.get(key)

            if cached is None:
                return None

            if cached.is_expired(self.ttl):
                return None

            values.append(cached.value)

        return values

    def get_all_registers_for_unit(self, unit_id: int, connection_id: str = DEFAULT_CONNECTION_ID) -> Dict[int, int]:
        """Get all cached registers for a unit.

        Args:
            unit_id: The Modbus unit/slave ID
            connection_id: The connection ID (for multi-connection support)

        Returns:
            Dictionary of address -> value for all non-expired registers
        """
        with self._lock:
            result = {}
            for (conn_id, uid, address), cached in self._register_cache.items():
                if conn_id == connection_id and uid == unit_id and not cached.is_expired(self.ttl):
                    result[address] = cached.value
            return result

    # =========================================================================
    # Virtual Unit ID Mapping Methods
    # =========================================================================

    def register_virtual_unit(self, virtual_unit_id: int, physical_unit_id: int, connection_id: str, offset: int = 0):
        """Register a virtual unit ID mapping.

        Args:
            virtual_unit_id: The virtual unit ID (as seen by TCP gateway clients)
            physical_unit_id: The actual physical unit ID of the device
            connection_id: The connection this device belongs to
            offset: The offset used (virtual = physical + offset)
        """
        with self._lock:
            self._virtual_unit_map[virtual_unit_id] = VirtualUnitMapping(
                virtual_unit_id=virtual_unit_id,
                physical_unit_id=physical_unit_id,
                connection_id=connection_id,
                offset=offset
            )
            logger.info(f"Registered virtual unit mapping: {virtual_unit_id} -> {connection_id}:{physical_unit_id} (offset={offset})")

    def resolve_virtual_unit(self, virtual_unit_id: int) -> Tuple[str, int]:
        """Resolve a virtual unit ID to connection_id and physical unit ID.

        Args:
            virtual_unit_id: The virtual unit ID

        Returns:
            Tuple of (connection_id, physical_unit_id). If no mapping exists,
            returns (DEFAULT_CONNECTION_ID, virtual_unit_id).
        """
        with self._lock:
            mapping = self._virtual_unit_map.get(virtual_unit_id)
            if mapping:
                return (mapping.connection_id, mapping.physical_unit_id)
            return (DEFAULT_CONNECTION_ID, virtual_unit_id)

    def get_virtual_unit_mappings(self) -> Dict[int, VirtualUnitMapping]:
        """Get all virtual unit mappings.

        Returns:
            Dictionary of virtual_unit_id -> VirtualUnitMapping
        """
        with self._lock:
            return self._virtual_unit_map.copy()

    def invalidate_client(self, client_id: str):
        """Invalidate cache for a specific client."""
        with self._lock:
            if client_id in self._client_cache:
                del self._client_cache[client_id]
            if client_id in self._client_unit_map:
                del self._client_unit_map[client_id]

    def invalidate_unit(self, unit_id: int, connection_id: str = DEFAULT_CONNECTION_ID):
        """Invalidate all cache entries for a unit ID.

        Args:
            unit_id: The Modbus unit/slave ID
            connection_id: The connection ID (for multi-connection support)
        """
        with self._lock:
            # Remove register cache entries for this (connection_id, unit_id)
            keys_to_remove = [
                key for key in self._register_cache.keys()
                if key[0] == connection_id and key[1] == unit_id
            ]
            for key in keys_to_remove:
                del self._register_cache[key]

            # Remove client cache entries for this (connection_id, unit_id)
            clients_to_remove = [
                cid for cid, (conn_id, uid) in self._client_unit_map.items()
                if conn_id == connection_id and uid == unit_id
            ]
            for cid in clients_to_remove:
                if cid in self._client_cache:
                    del self._client_cache[cid]
                del self._client_unit_map[cid]

    def cleanup_expired(self):
        """Remove all expired entries from the cache."""
        with self._lock:
            # Cleanup register cache
            expired_regs = [
                key for key, cached in self._register_cache.items()
                if cached.is_expired(self.ttl)
            ]
            for key in expired_regs:
                del self._register_cache[key]

            # Cleanup client cache
            expired_clients = [
                cid for cid, entry in self._client_cache.items()
                if entry.is_expired(self.ttl)
            ]
            for cid in expired_clients:
                del self._client_cache[cid]
                if cid in self._client_unit_map:
                    del self._client_unit_map[cid]

            if expired_regs or expired_clients:
                logger.debug(f"Cleaned up {len(expired_regs)} registers, {len(expired_clients)} clients")

    def clear(self):
        """Clear all cached values."""
        with self._lock:
            self._register_cache.clear()
            self._client_cache.clear()
            self._client_unit_map.clear()
            self._hits = 0
            self._misses = 0
            self._updates = 0
            self._evictions = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "hits": self._hits,
                "misses": self._misses,
                "updates": self._updates,
                "evictions": self._evictions,
                "hit_rate": round(hit_rate, 1),
                "register_entries": len(self._register_cache),
                "client_entries": len(self._client_cache),
                "max_register_entries": self.max_register_entries,
                "max_client_entries": self.max_client_entries,
                "ttl": self.ttl
            }

    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information for debugging."""
        with self._lock:
            now = time.time()
            register_info = {}
            for (connection_id, unit_id, address), cached in self._register_cache.items():
                key = f"{connection_id}:unit_{unit_id}"
                if key not in register_info:
                    register_info[key] = {}
                register_info[key][address] = {
                    "value": cached.value,
                    "age": round(now - cached.timestamp, 1),
                    "expired": cached.is_expired(self.ttl)
                }

            client_info = {}
            for cid, entry in self._client_cache.items():
                client_info[cid] = {
                    "connection_id": entry.connection_id,
                    "unit_id": entry.unit_id,
                    "fields": len(entry.values),
                    "age": round(now - entry.timestamp, 1),
                    "expired": entry.is_expired(self.ttl)
                }

            virtual_mappings = {}
            for vid, mapping in self._virtual_unit_map.items():
                virtual_mappings[vid] = {
                    "physical_unit_id": mapping.physical_unit_id,
                    "connection_id": mapping.connection_id,
                    "offset": mapping.offset
                }

            return {
                "stats": self.get_stats(),
                "registers": register_info,
                "clients": client_info,
                "virtual_mappings": virtual_mappings
            }


# Global cache instance
_cache: Optional[RegisterCache] = None


def get_cache(
    ttl: float = RegisterCache.DEFAULT_TTL,
    max_register_entries: int = RegisterCache.DEFAULT_MAX_REGISTER_ENTRIES,
    max_client_entries: int = RegisterCache.DEFAULT_MAX_CLIENT_ENTRIES
) -> RegisterCache:
    """Get or create the global register cache instance.

    Args:
        ttl: Time-to-live in seconds for cached values
        max_register_entries: Maximum number of register cache entries
        max_client_entries: Maximum number of client cache entries

    Returns:
        The global RegisterCache instance
    """
    global _cache
    if _cache is None:
        _cache = RegisterCache(
            ttl=ttl,
            max_register_entries=max_register_entries,
            max_client_entries=max_client_entries
        )
    return _cache
