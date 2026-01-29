"""Meter Registry Service

This module loads and manages meter type definitions from meter_registry.yaml.
It provides functionality to:
- Look up register mappings for a given meter model
- Generate client configurations from meter model + profile
- Validate meter configurations
- Map register values to database field names
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

import yaml

logger = logging.getLogger(__name__)


@dataclass
class RegisterDefinition:
    """Definition of a single Modbus register."""
    name: str
    address: int
    unit: str
    label: str
    data_type: str = "float"
    register_type: str = "holding"
    register_count: int = 2
    multiplication_factor: Optional[float] = None

    def to_client_register(self, db_field_name: Optional[str] = None) -> Dict[str, Any]:
        """Convert to client register format for slave_config."""
        # Normalize special data types to standard types
        # 4q_fp_pf is Schneider's 4-quadrant power factor format, which is essentially float32
        normalized_data_type = self.data_type
        if normalized_data_type.lower() in ('4q_fp_pf', '4q-fp-pf'):
            normalized_data_type = 'float'  # Map to FLOAT32

        reg = {
            "address": self.address,
            "count": self.register_count,
            "data_type": normalized_data_type,
            "field_name": db_field_name or self.name,
            "label": self.label,
            "unit": self.unit,
            "register_type": self.register_type,
        }
        if self.multiplication_factor is not None:
            reg["multiplication_factor"] = self.multiplication_factor
        return reg


@dataclass
class MeterDefinition:
    """Definition of a meter type with all its registers."""
    meter_id: str
    manufacturer: str
    model: str
    description: str
    category: str  # electrical_distribution, electrical_substation, water
    defaults: Dict[str, Any]
    registers: Dict[str, RegisterDefinition]

    def get_register(self, name: str) -> Optional[RegisterDefinition]:
        """Get a register by name."""
        return self.registers.get(name)

    def get_registers_for_profile(self, register_names: List[str]) -> List[RegisterDefinition]:
        """Get registers matching the given names."""
        result = []
        for name in register_names:
            if name in self.registers:
                result.append(self.registers[name])
            else:
                logger.warning(f"Register '{name}' not found in meter '{self.meter_id}'")
        return result

    def has_register(self, name: str) -> bool:
        """Check if meter has a specific register."""
        return name in self.registers


@dataclass
class ClientProfile:
    """A predefined profile for common monitoring scenarios."""
    name: str
    description: str
    target_table: str
    registers: List[str]


class MeterRegistry:
    """Registry for meter type definitions."""

    def __init__(self, registry_path: Optional[str] = None):
        """Initialize the meter registry.

        Args:
            registry_path: Path to meter_registry.yaml. If not provided,
                          looks in CONFIG_DIR or defaults to config/meter_registry.yaml
        """
        self.registry_path = registry_path or self._find_registry_path()
        self.meters: Dict[str, MeterDefinition] = {}
        self.profiles: Dict[str, ClientProfile] = {}
        self.db_field_mappings: Dict[str, Dict[str, str]] = {}
        self._raw_config: Dict = {}

        self._load_registry()

    def _find_registry_path(self) -> str:
        """Find the meter registry file path.

        Priority order:
        1. src/config/meter_registry.yaml (inside codebase)
        2. CONFIG_DIR environment variable
        3. config/meter_registry.yaml (legacy)
        """
        # Check inside codebase first (src/config/)
        current_dir = Path(__file__).parent.parent  # This is src/
        path = current_dir / "config" / "meter_registry.yaml"
        if path.exists():
            return str(path)

        # Check CONFIG_DIR environment variable
        config_dir = os.getenv('CONFIG_DIR')
        if config_dir:
            path = Path(config_dir) / "meter_registry.yaml"
            if path.exists():
                return str(path)

        # Fallback to config directory at repo root
        repo_root = Path(__file__).parent.parent.parent
        path = repo_root / "config" / "meter_registry.yaml"
        if path.exists():
            return str(path)

        # Default path
        return "config/meter_registry.yaml"

    def _load_registry(self):
        """Load the meter registry from YAML file."""
        try:
            with open(self.registry_path, 'r') as f:
                self._raw_config = yaml.safe_load(f)

            self._load_meters()
            self._load_profiles()
            self._load_db_mappings()

            logger.info(f"Loaded meter registry: {len(self.meters)} meters, {len(self.profiles)} profiles")

        except FileNotFoundError:
            logger.warning(f"Meter registry not found at {self.registry_path}, using empty registry")
        except Exception as e:
            logger.error(f"Error loading meter registry: {e}")
            raise

    def _load_meters(self):
        """Load meter definitions from config."""
        categories = ['electrical_distribution', 'electrical_substation', 'water']

        for category in categories:
            if category not in self._raw_config:
                continue

            for meter_id, meter_config in self._raw_config[category].items():
                try:
                    # Handle 'extends' for inheritance
                    if 'extends' in meter_config:
                        base_meter = self._resolve_extends(meter_config['extends'])
                        if base_meter:
                            meter_config = self._merge_meter_configs(base_meter, meter_config)

                    meter = self._parse_meter(meter_id, category, meter_config)
                    self.meters[meter_id] = meter

                except Exception as e:
                    logger.error(f"Error parsing meter '{meter_id}': {e}")

    def _resolve_extends(self, extends_path: str) -> Optional[Dict]:
        """Resolve an 'extends' reference to get base meter config."""
        parts = extends_path.split('.')
        if len(parts) != 2:
            logger.warning(f"Invalid extends path: {extends_path}")
            return None

        category, meter_id = parts
        if category in self._raw_config and meter_id in self._raw_config[category]:
            return self._raw_config[category][meter_id]
        return None

    def _merge_meter_configs(self, base: Dict, derived: Dict) -> Dict:
        """Merge a derived meter config with its base."""
        result = base.copy()

        # Override simple fields
        for key in ['manufacturer', 'model', 'description', 'defaults']:
            if key in derived:
                result[key] = derived[key]

        # Merge registers
        if 'registers' not in result:
            result['registers'] = {}
        if 'registers' in derived:
            result['registers'].update(derived['registers'])
        if 'additional_registers' in derived:
            result['registers'].update(derived['additional_registers'])

        return result

    def _parse_meter(self, meter_id: str, category: str, config: Dict) -> MeterDefinition:
        """Parse a meter definition from config dict."""
        defaults = config.get('defaults', {})

        registers = {}
        for reg_name, reg_config in config.get('registers', {}).items():
            reg = RegisterDefinition(
                name=reg_name,
                address=reg_config['address'],
                unit=reg_config.get('unit', ''),
                label=reg_config.get('label', reg_name),
                data_type=reg_config.get('data_type', defaults.get('data_type', 'float')),
                register_type=reg_config.get('register_type', defaults.get('register_type', 'holding')),
                register_count=reg_config.get('register_count', defaults.get('register_count', 2)),
                multiplication_factor=reg_config.get('multiplication_factor'),
            )
            registers[reg_name] = reg

        return MeterDefinition(
            meter_id=meter_id,
            manufacturer=config.get('manufacturer', ''),
            model=config.get('model', ''),
            description=config.get('description', ''),
            category=category,
            defaults=defaults,
            registers=registers,
        )

    def _load_profiles(self):
        """Load client profiles from config."""
        profiles_config = self._raw_config.get('client_profiles', {})

        for profile_name, profile_config in profiles_config.items():
            self.profiles[profile_name] = ClientProfile(
                name=profile_name,
                description=profile_config.get('description', ''),
                target_table=profile_config.get('target_table', ''),
                registers=profile_config.get('registers', []),
            )

    def _load_db_mappings(self):
        """Load database field mappings from config."""
        self.db_field_mappings = self._raw_config.get('db_field_mappings', {})

    def get_meter(self, meter_id: str) -> Optional[MeterDefinition]:
        """Get a meter definition by ID."""
        return self.meters.get(meter_id)

    def get_profile(self, profile_name: str) -> Optional[ClientProfile]:
        """Get a client profile by name."""
        return self.profiles.get(profile_name)

    def get_db_field_name(self, table: str, register_name: str) -> str:
        """Get the database field name for a register.

        Args:
            table: Target table (distribution, substation, water)
            register_name: The register name from meter config

        Returns:
            Database field name, or the register name if no mapping exists
        """
        if table in self.db_field_mappings:
            return self.db_field_mappings[table].get(register_name, register_name)
        return register_name

    def generate_client_registers(
        self,
        meter_id: str,
        profile_name: Optional[str] = None,
        register_names: Optional[List[str]] = None,
        target_table: Optional[str] = None,
        custom_registers: Optional[List[Dict]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate client register configuration for a meter.

        Args:
            meter_id: The meter type ID (e.g., 'lt_wl4400')
            profile_name: Optional profile to use for register selection
            register_names: Optional explicit list of registers to include
            target_table: Target DB table for field name mapping
            custom_registers: Optional custom register overrides/additions

        Returns:
            List of register configurations suitable for slave_config.yaml
        """
        meter = self.get_meter(meter_id)
        if not meter:
            logger.error(f"Unknown meter type: {meter_id}")
            return []

        # Determine which registers to include
        selected_names = []

        if register_names:
            selected_names = register_names
        elif profile_name:
            profile = self.get_profile(profile_name)
            if profile:
                selected_names = profile.registers
                if not target_table:
                    target_table = profile.target_table
        else:
            # Include all available registers
            selected_names = list(meter.registers.keys())

        # Generate register configs
        result = []
        for name in selected_names:
            reg = meter.get_register(name)
            if reg:
                db_field = self.get_db_field_name(target_table or '', name)
                result.append(reg.to_client_register(db_field))
            else:
                logger.warning(f"Register '{name}' not found in meter '{meter_id}'")

        # Add custom registers
        if custom_registers:
            result.extend(custom_registers)

        return result

    def generate_client_config(
        self,
        client_id: str,
        meter_id: str,
        unit_id: int,
        profile_name: Optional[str] = None,
        polling_interval: int = 60,
        client_type: str = "electrical",
        register_names: Optional[List[str]] = None,
        custom_registers: Optional[List[Dict]] = None,
        thresholds: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a complete client configuration.

        Args:
            client_id: Unique client identifier
            meter_id: Meter type ID
            unit_id: Modbus unit/slave ID
            profile_name: Optional profile for register selection
            polling_interval: Polling interval in seconds
            client_type: Type of client (electrical, water)
            register_names: Optional explicit register list
            custom_registers: Optional custom register overrides
            thresholds: Optional threshold configurations by register name

        Returns:
            Complete client configuration dict
        """
        meter = self.get_meter(meter_id)
        if not meter:
            logger.error(f"Unknown meter type: {meter_id}")
            return {}

        # Determine target table from profile or meter category
        target_table = None
        if profile_name:
            profile = self.get_profile(profile_name)
            if profile:
                target_table = profile.target_table

        # Generate registers
        registers = self.generate_client_registers(
            meter_id=meter_id,
            profile_name=profile_name,
            register_names=register_names,
            target_table=target_table,
            custom_registers=custom_registers,
        )

        # Apply thresholds if provided
        if thresholds:
            for reg in registers:
                field_name = reg.get('field_name')
                if field_name in thresholds:
                    threshold_config = thresholds[field_name]
                    if 'upper_threshold' in threshold_config:
                        reg['upper_threshold'] = threshold_config['upper_threshold']
                    if 'lower_threshold' in threshold_config:
                        reg['lower_threshold'] = threshold_config['lower_threshold']
                    if 'delta' in threshold_config:
                        reg['delta'] = threshold_config['delta']

        # Build client config
        client_config = {
            "id": client_id,
            "type": client_type,
            "polling_interval": polling_interval,
            "unit_id": unit_id,
            "endianness": meter.defaults.get('endianness', 'big'),
            "registers": registers,
            # Store meter model for reference
            "_meter_model": meter_id,
        }

        return client_config

    def list_meters(self, category: Optional[str] = None) -> List[str]:
        """List available meter types.

        Args:
            category: Optional filter by category

        Returns:
            List of meter IDs
        """
        if category:
            return [m.meter_id for m in self.meters.values() if m.category == category]
        return list(self.meters.keys())

    def list_profiles(self) -> List[str]:
        """List available client profiles."""
        return list(self.profiles.keys())

    def get_meter_info(self, meter_id: str) -> Optional[Dict[str, Any]]:
        """Get summary information about a meter type."""
        meter = self.get_meter(meter_id)
        if not meter:
            return None

        return {
            "meter_id": meter.meter_id,
            "manufacturer": meter.manufacturer,
            "model": meter.model,
            "description": meter.description,
            "category": meter.category,
            "endianness": meter.defaults.get('endianness', 'big'),
            "register_count": len(meter.registers),
            "available_registers": list(meter.registers.keys()),
        }

    def validate_meter_for_profile(self, meter_id: str, profile_name: str) -> Tuple[bool, List[str]]:
        """Check if a meter supports all registers required by a profile.

        Args:
            meter_id: Meter type ID
            profile_name: Profile name

        Returns:
            Tuple of (is_valid, missing_registers)
        """
        meter = self.get_meter(meter_id)
        profile = self.get_profile(profile_name)

        if not meter:
            return False, [f"Unknown meter: {meter_id}"]
        if not profile:
            return False, [f"Unknown profile: {profile_name}"]

        missing = []
        for reg_name in profile.registers:
            if not meter.has_register(reg_name):
                missing.append(reg_name)

        return len(missing) == 0, missing


# Global registry instance
_registry: Optional[MeterRegistry] = None


def get_meter_registry(registry_path: Optional[str] = None) -> MeterRegistry:
    """Get or create the global meter registry instance."""
    global _registry
    if _registry is None:
        _registry = MeterRegistry(registry_path)
    return _registry


def reload_meter_registry(registry_path: Optional[str] = None) -> MeterRegistry:
    """Reload the meter registry from disk."""
    global _registry
    _registry = MeterRegistry(registry_path)
    return _registry
