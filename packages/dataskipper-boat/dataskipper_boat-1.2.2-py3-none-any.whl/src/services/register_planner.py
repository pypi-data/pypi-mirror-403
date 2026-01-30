"""Smart Register Planner for efficient Modbus reads.

This module analyzes register lists and groups them into optimal read batches.
- Sequential registers are batched together for single read operations
- Scattered registers are read individually
- Supports different meter types (L&T WL4400, Schneider EM6400NG+, Secure)
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from src.models.device import Register, ModbusClient
from src.models.modbus_types import RegisterType, DataType

logger = logging.getLogger(__name__)


@dataclass
class RegisterBatch:
    """A batch of contiguous registers that can be read in a single operation."""
    start_address: int
    count: int  # Total number of 16-bit registers to read
    register_type: RegisterType
    unit_id: int
    registers: List[Register] = field(default_factory=list)

    def __repr__(self):
        return f"RegisterBatch(start={self.start_address}, count={self.count}, registers={len(self.registers)})"


@dataclass
class ReadPlan:
    """Complete read plan for a client."""
    client_id: str
    unit_id: int
    batches: List[RegisterBatch] = field(default_factory=list)
    total_reads: int = 0  # Number of Modbus read operations required
    total_registers: int = 0  # Total number of individual register values

    def __repr__(self):
        return f"ReadPlan(client={self.client_id}, batches={len(self.batches)}, reads={self.total_reads})"


class RegisterPlanner:
    """Plans efficient register read operations by batching contiguous registers."""

    # Maximum number of registers that can be read in a single Modbus operation
    # Standard Modbus limit is 125 for holding/input registers
    MAX_BATCH_SIZE = 125

    # Maximum gap between registers to still consider them part of the same batch
    # If registers are within this gap, we read the gap too (wasted bandwidth but fewer operations)
    MAX_GAP_SIZE = 10

    def __init__(self, max_batch_size: int = 125, max_gap_size: int = 10):
        """Initialize the register planner.

        Args:
            max_batch_size: Maximum registers per read operation (default 125)
            max_gap_size: Maximum gap to tolerate in a batch (default 10)
        """
        self.max_batch_size = max_batch_size
        self.max_gap_size = max_gap_size
        self._plans_cache: Dict[str, ReadPlan] = {}

    def get_register_size(self, data_type: DataType) -> int:
        """Get the number of 16-bit registers used by a data type."""
        sizes = {
            DataType.INT16: 1,
            DataType.UINT16: 1,
            DataType.INT32: 2,
            DataType.UINT32: 2,
            DataType.FLOAT32: 2,
            DataType.INT64: 4,
            DataType.UINT64: 4,
            DataType.FLOAT64: 4,
            DataType.STRING: 2,  # Default, actual size may vary
            DataType.BOOL: 1,
        }
        return sizes.get(data_type, 1)

    def create_read_plan(self, client: ModbusClient) -> ReadPlan:
        """Create an optimized read plan for a Modbus client.

        Args:
            client: The ModbusClient to create a plan for

        Returns:
            ReadPlan with batched register reads
        """
        if not client.registers:
            return ReadPlan(client_id=client.id, unit_id=client.unit_id)

        # Check cache
        cache_key = f"{client.id}_{hash(tuple(r.address for r in client.registers))}"
        if cache_key in self._plans_cache:
            return self._plans_cache[cache_key]

        # Group registers by type (holding vs input)
        holding_registers = []
        input_registers = []

        for reg in client.registers:
            if reg.register_type == RegisterType.HoldingRegister:
                holding_registers.append(reg)
            elif reg.register_type == RegisterType.InputRegister:
                input_registers.append(reg)

        plan = ReadPlan(client_id=client.id, unit_id=client.unit_id)

        # Create batches for each register type
        if holding_registers:
            batches = self._create_batches(holding_registers, RegisterType.HoldingRegister, client.unit_id)
            plan.batches.extend(batches)

        if input_registers:
            batches = self._create_batches(input_registers, RegisterType.InputRegister, client.unit_id)
            plan.batches.extend(batches)

        plan.total_reads = len(plan.batches)
        plan.total_registers = len(client.registers)

        # Cache the plan
        self._plans_cache[cache_key] = plan

        logger.debug(f"Created read plan for {client.id}: {plan.total_reads} reads for {plan.total_registers} registers")
        return plan

    def _create_batches(self, registers: List[Register], reg_type: RegisterType, unit_id: int) -> List[RegisterBatch]:
        """Create optimized batches from a list of registers.

        Args:
            registers: List of registers to batch
            reg_type: The register type (holding or input)
            unit_id: The Modbus unit ID

        Returns:
            List of RegisterBatch objects
        """
        if not registers:
            return []

        # Sort registers by address
        sorted_regs = sorted(registers, key=lambda r: r.address)

        batches = []
        current_batch_regs = [sorted_regs[0]]
        batch_start = sorted_regs[0].address
        batch_end = batch_start + self._get_register_span(sorted_regs[0])

        for reg in sorted_regs[1:]:
            reg_start = reg.address
            reg_span = self._get_register_span(reg)
            reg_end = reg_start + reg_span

            # Check if this register can be added to current batch
            gap = reg_start - batch_end
            new_batch_size = reg_end - batch_start

            if gap <= self.max_gap_size and new_batch_size <= self.max_batch_size:
                # Add to current batch
                current_batch_regs.append(reg)
                batch_end = max(batch_end, reg_end)
            else:
                # Finalize current batch and start new one
                batch = RegisterBatch(
                    start_address=batch_start,
                    count=batch_end - batch_start,
                    register_type=reg_type,
                    unit_id=unit_id,
                    registers=current_batch_regs.copy()
                )
                batches.append(batch)

                # Start new batch
                current_batch_regs = [reg]
                batch_start = reg_start
                batch_end = reg_end

        # Don't forget the last batch
        if current_batch_regs:
            batch = RegisterBatch(
                start_address=batch_start,
                count=batch_end - batch_start,
                register_type=reg_type,
                unit_id=unit_id,
                registers=current_batch_regs
            )
            batches.append(batch)

        return batches

    def _get_register_span(self, register: Register) -> int:
        """Get the number of 16-bit registers spanned by this register."""
        if register.count > 0:
            return register.count
        return self.get_register_size(register.data_type)

    def analyze_efficiency(self, plan: ReadPlan) -> Dict:
        """Analyze the efficiency of a read plan.

        Returns:
            Dictionary with efficiency metrics
        """
        if not plan.batches:
            return {"efficiency": 0, "reduction": 0}

        total_registers_read = sum(b.count for b in plan.batches)
        actual_registers = plan.total_registers

        # Calculate efficiency (useful registers / total registers read)
        efficiency = (actual_registers / total_registers_read * 100) if total_registers_read > 0 else 0

        # Calculate read reduction (individual reads vs batched reads)
        reduction = ((actual_registers - plan.total_reads) / actual_registers * 100) if actual_registers > 0 else 0

        return {
            "total_reads": plan.total_reads,
            "total_registers": actual_registers,
            "registers_read": total_registers_read,
            "efficiency": round(efficiency, 1),
            "read_reduction": round(reduction, 1),
            "batches": [
                {
                    "start": b.start_address,
                    "count": b.count,
                    "type": b.register_type.value,
                    "registers": len(b.registers)
                }
                for b in plan.batches
            ]
        }

    def clear_cache(self):
        """Clear the plans cache."""
        self._plans_cache.clear()


# Global planner instance
_planner: Optional[RegisterPlanner] = None


def get_planner(max_batch_size: int = 125, max_gap_size: int = 10) -> RegisterPlanner:
    """Get or create the global register planner instance."""
    global _planner
    if _planner is None:
        _planner = RegisterPlanner(max_batch_size, max_gap_size)
    return _planner
