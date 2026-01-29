"""Gateway configuration models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModbusTCPGatewayConfig:
    """Configuration for the Modbus TCP Gateway."""
    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 4196
    cache_ttl: int = 180  # seconds (3 minutes)
    max_batch_size: int = 125  # Maximum registers per read
    max_gap_size: int = 10  # Maximum gap in batch


def create_gateway_config(config_dict: Optional[dict]) -> Optional[ModbusTCPGatewayConfig]:
    """Create a gateway configuration from dictionary.

    Args:
        config_dict: Configuration dictionary from communication.yaml

    Returns:
        ModbusTCPGatewayConfig or None if not provided
    """
    if not config_dict:
        return None

    return ModbusTCPGatewayConfig(
        enabled=config_dict.get('enabled', False),
        host=config_dict.get('host', '0.0.0.0'),
        port=config_dict.get('port', 4196),
        cache_ttl=config_dict.get('cache_ttl', 180),
        max_batch_size=config_dict.get('max_batch_size', 125),
        max_gap_size=config_dict.get('max_gap_size', 10)
    )
