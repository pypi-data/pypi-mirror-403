"""
Diagnostic Service for RTU Web Portal.

Provides automated diagnostic checks for:
- Connectivity (Internet, DNS, MQTT, API, Modbus gateways)
- System health (CPU, Memory, Disk, Service status)
- Device status (per-device data freshness)

Also provides troubleshooting decision trees for common problems.
"""

import asyncio
import logging
import os
import platform
import socket
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil
import yaml

logger = logging.getLogger(__name__)


class CheckStatus(Enum):
    """Status of a diagnostic check."""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    RUNNING = "running"
    SKIPPED = "skipped"


@dataclass
class DiagnosticResult:
    """Result of a single diagnostic check."""
    check_id: str
    name: str
    category: str
    status: CheckStatus
    message: str
    duration_ms: float = 0
    details: Dict[str, Any] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)
    troubleshooting_tree: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DiagnosticReport:
    """Complete diagnostic report."""
    results: List[DiagnosticResult]
    summary: Dict[str, int]
    timestamp: str
    duration_ms: float


# Troubleshooting decision trees for common problems
TROUBLESHOOTING_TREES = {
    "no_data_from_device": {
        "title": "No Data from Device",
        "description": "Device is not sending any data to the system",
        "steps": [
            {
                "id": 1,
                "question": "Is the meter display showing readings (voltage, current, power)?",
                "help": "Check the LCD display on the meter front panel. It should show live values.",
                "options": {
                    "yes": {"next": 2},
                    "no": {
                        "diagnosis": "Meter has no power or is malfunctioning",
                        "actions": [
                            "Check meter power supply - verify 230V AC input is present",
                            "Verify the supply MCB/fuse is switched ON",
                            "Inspect incoming power terminals for loose connections",
                            "Check meter internal fuse if applicable"
                        ]
                    }
                }
            },
            {
                "id": 2,
                "question": "Is the RS485 communication LED blinking on the meter?",
                "help": "Most meters have a COM or TX/RX LED that blinks during communication attempts.",
                "options": {
                    "yes": {"next": 3},
                    "no": {
                        "diagnosis": "RS485 wiring or configuration issue",
                        "actions": [
                            "Check RS485 wiring polarity: A+ connects to A+, B- connects to B-",
                            "Verify RS485 cable is properly connected at both ends",
                            "Check for termination resistor (120 ohm) at end of bus",
                            "Verify meter's RS485 is enabled in meter settings"
                        ]
                    }
                }
            },
            {
                "id": 3,
                "question": "Is the Waveshare/USR gateway power LED on?",
                "help": "The serial-to-ethernet converter should have a power indicator LED.",
                "options": {
                    "yes": {"next": 4},
                    "no": {
                        "diagnosis": "Gateway has no power",
                        "actions": [
                            "Check 12V/24V DC power supply to gateway",
                            "Verify power adapter is plugged in and working",
                            "Try a different power outlet or adapter"
                        ]
                    }
                }
            },
            {
                "id": 4,
                "question": "Is the gateway's network/link LED on?",
                "help": "The gateway should have an Ethernet link LED indicating network connection.",
                "options": {
                    "yes": {"next": 5},
                    "no": {
                        "diagnosis": "Network connectivity issue with gateway",
                        "actions": [
                            "Check Ethernet cable connection at gateway",
                            "Try a different Ethernet cable",
                            "Verify gateway and RTU are on same network/VLAN",
                            "Check switch/router port status"
                        ]
                    }
                }
            },
            {
                "id": 5,
                "question": "Can you access the gateway's web interface?",
                "help": "Try accessing http://<gateway-ip> in a browser from the RTU.",
                "options": {
                    "yes": {"next": 6},
                    "no": {
                        "diagnosis": "Gateway IP or network configuration issue",
                        "actions": [
                            "Verify gateway IP address is correct in config",
                            "Check if gateway IP is reachable: ping <gateway-ip>",
                            "Verify no IP conflict on the network",
                            "Reset gateway to factory defaults if needed"
                        ]
                    }
                }
            },
            {
                "id": 6,
                "question": "Is the meter Unit ID configured correctly?",
                "help": "The Unit ID in config must match the meter's Modbus address setting.",
                "options": {
                    "yes": {
                        "diagnosis": "Communication parameters mismatch",
                        "actions": [
                            "Verify baud rate matches meter setting (typically 9600)",
                            "Check parity setting (typically None/N)",
                            "Verify stop bits (typically 1)",
                            "Check framer setting: 'rtu' for serial, 'socket' for TCP"
                        ]
                    },
                    "no": {
                        "diagnosis": "Unit ID mismatch",
                        "actions": [
                            "Check meter's Modbus address in meter settings menu",
                            "Update config file with correct Unit ID",
                            "Restart the service after config change"
                        ]
                    }
                }
            }
        ]
    },
    "stale_data": {
        "title": "Data is Delayed/Stale",
        "description": "Device data is arriving but with delays beyond expected interval",
        "steps": [
            {
                "id": 1,
                "question": "Is data delayed for ALL devices or just SOME devices?",
                "help": "Check the Device Health page to see which devices are stale.",
                "options": {
                    "all": {
                        "diagnosis": "System-wide performance issue",
                        "actions": [
                            "Check CPU usage - high CPU can cause delays",
                            "Check memory usage - low memory affects performance",
                            "Review polling intervals - too many devices polling too fast",
                            "Consider restarting the service",
                            "Check for network congestion"
                        ]
                    },
                    "some": {"next": 2}
                }
            },
            {
                "id": 2,
                "question": "Are the affected devices on the same RS485 bus/gateway?",
                "help": "Check if all stale devices share the same connection in config.",
                "options": {
                    "yes": {
                        "diagnosis": "RS485 bus or gateway issue",
                        "actions": [
                            "Check RS485 termination resistors at bus ends",
                            "Verify cable shielding is properly grounded",
                            "Look for sources of electrical interference",
                            "Check gateway serial port settings",
                            "Try reducing number of devices on the bus"
                        ]
                    },
                    "no": {"next": 3}
                }
            },
            {
                "id": 3,
                "question": "Are the affected devices the same meter model?",
                "help": "Check if all stale devices are from the same manufacturer.",
                "options": {
                    "yes": {
                        "diagnosis": "Meter-specific timing issue",
                        "actions": [
                            "Increase timeout value for this meter type",
                            "Add delay between register reads",
                            "Check meter firmware version",
                            "Verify register addresses are correct"
                        ]
                    },
                    "no": {
                        "diagnosis": "Individual device issues",
                        "actions": [
                            "Check each device's wiring individually",
                            "Verify communication LED activity on each meter",
                            "Test each device with a Modbus scanner tool",
                            "Check for loose RS485 connections"
                        ]
                    }
                }
            }
        ]
    },
    "gateway_connection_failed": {
        "title": "Cannot Connect to Modbus Gateway",
        "description": "TCP connection to serial gateway fails",
        "steps": [
            {
                "id": 1,
                "question": "Can you ping the gateway IP address from the RTU?",
                "help": "Open terminal and run: ping <gateway-ip>",
                "options": {
                    "yes": {"next": 2},
                    "no": {
                        "diagnosis": "Network layer issue",
                        "actions": [
                            "Check Ethernet cable at gateway and switch",
                            "Verify gateway and RTU are on same subnet",
                            "Check for IP address conflicts",
                            "Verify switch/router port is active"
                        ]
                    }
                }
            },
            {
                "id": 2,
                "question": "Is the correct port configured (usually 502 or 4196)?",
                "help": "Check communication.yaml or slave_config.yaml for port setting.",
                "options": {
                    "yes": {"next": 3},
                    "no": {
                        "diagnosis": "Port configuration mismatch",
                        "actions": [
                            "Check gateway web interface for Modbus port setting",
                            "Update config file with correct port",
                            "Common ports: 502 (standard), 4196 (some gateways), 8899 (USR)"
                        ]
                    }
                }
            },
            {
                "id": 3,
                "question": "Is only ONE application connecting to this gateway?",
                "help": "Most gateways only support one TCP connection at a time.",
                "options": {
                    "yes": {
                        "diagnosis": "Gateway application layer issue",
                        "actions": [
                            "Power cycle the gateway (unplug for 10 seconds)",
                            "Check gateway configuration via web interface",
                            "Verify Modbus TCP mode is enabled on gateway",
                            "Reset gateway to factory defaults if needed"
                        ]
                    },
                    "no": {
                        "diagnosis": "Connection limit exceeded",
                        "actions": [
                            "Ensure only one service connects to each gateway",
                            "Close any Modbus scanner/test tools",
                            "Stop other services that may be using this gateway",
                            "Consider using the built-in TCP gateway for sharing"
                        ]
                    }
                }
            }
        ]
    },
    "mqtt_connection_failed": {
        "title": "MQTT Connection Failed",
        "description": "Cannot connect to MQTT broker",
        "steps": [
            {
                "id": 1,
                "question": "Is the RTU connected to the internet/VPN?",
                "help": "Check if you can access external services.",
                "options": {
                    "yes": {"next": 2},
                    "no": {
                        "diagnosis": "No network connectivity",
                        "actions": [
                            "Check Ethernet/WiFi connection",
                            "Verify Tailscale VPN is connected (if used)",
                            "Check router/firewall settings",
                            "Contact network administrator"
                        ]
                    }
                }
            },
            {
                "id": 2,
                "question": "Are MQTT credentials configured correctly?",
                "help": "Check communication.yaml for mqtt_config section.",
                "options": {
                    "yes": {"next": 3},
                    "no": {
                        "diagnosis": "MQTT credentials issue",
                        "actions": [
                            "Verify MQTT username and password",
                            "Check MQTT broker hostname/IP",
                            "Verify MQTT port (1883 or 8883 for TLS)",
                            "Ensure client_id is unique"
                        ]
                    }
                }
            },
            {
                "id": 3,
                "question": "Does the MQTT broker require TLS/SSL?",
                "help": "Check if broker uses port 8883 (TLS) vs 1883 (plain).",
                "options": {
                    "yes": {
                        "diagnosis": "TLS configuration issue",
                        "actions": [
                            "Verify TLS is enabled in mqtt_config",
                            "Check certificate file exists and is valid",
                            "Verify certificate is not expired",
                            "Ensure correct CA certificate is configured"
                        ]
                    },
                    "no": {
                        "diagnosis": "MQTT broker issue",
                        "actions": [
                            "Verify MQTT broker is running",
                            "Check broker allows connections from this IP",
                            "Verify topic permissions for this user",
                            "Contact MQTT broker administrator"
                        ]
                    }
                }
            }
        ]
    }
}


class DiagnosticService:
    """Service for running diagnostic checks."""

    def __init__(self, config_dir: str = None):
        """Initialize diagnostic service.

        Args:
            config_dir: Path to configuration directory
        """
        self.config_dir = config_dir or os.getenv('CONFIG_DIR', '')
        self._comm_config = None
        self._slave_config = None

    def _load_communication_config(self) -> Dict[str, Any]:
        """Load communication configuration."""
        if self._comm_config is not None:
            return self._comm_config

        config_path = Path(self.config_dir)
        for filename in ['communication.yaml', 'comm_config.yaml']:
            file_path = config_path / filename
            if file_path.exists():
                try:
                    with open(file_path) as f:
                        self._comm_config = yaml.safe_load(f) or {}
                        return self._comm_config
                except Exception as e:
                    logger.error(f"Error loading {filename}: {e}")

        self._comm_config = {}
        return self._comm_config

    def _load_slave_config(self) -> Dict[str, Any]:
        """Load slave configuration."""
        if self._slave_config is not None:
            return self._slave_config

        config_path = Path(self.config_dir)
        for filename in ['slave_config.yaml', 'devices.yaml']:
            file_path = config_path / filename
            if file_path.exists():
                try:
                    with open(file_path) as f:
                        self._slave_config = yaml.safe_load(f) or {}
                        return self._slave_config
                except Exception as e:
                    logger.error(f"Error loading {filename}: {e}")

        self._slave_config = {}
        return self._slave_config

    async def check_internet(self) -> DiagnosticResult:
        """Check internet connectivity by pinging 8.8.8.8."""
        start = time.time()
        try:
            # Use ping command
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', '1', '-w', '2000', '8.8.8.8']
            else:
                cmd = ['ping', '-c', '1', '-W', '2', '8.8.8.8']

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            duration = (time.time() - start) * 1000

            if result.returncode == 0:
                return DiagnosticResult(
                    check_id="internet",
                    name="Internet Connection",
                    category="connectivity",
                    status=CheckStatus.PASS,
                    message="Internet connection active",
                    duration_ms=duration,
                    details={"target": "8.8.8.8"}
                )
            else:
                return DiagnosticResult(
                    check_id="internet",
                    name="Internet Connection",
                    category="connectivity",
                    status=CheckStatus.FAIL,
                    message="Cannot reach internet (8.8.8.8)",
                    duration_ms=duration,
                    actions=[
                        "Check network cable connection",
                        "Verify router/gateway is working",
                        "Check firewall settings"
                    ]
                )
        except subprocess.TimeoutExpired:
            return DiagnosticResult(
                check_id="internet",
                name="Internet Connection",
                category="connectivity",
                status=CheckStatus.FAIL,
                message="Ping timeout - no response from 8.8.8.8",
                duration_ms=(time.time() - start) * 1000,
                actions=["Check network connectivity", "Verify DNS settings"]
            )
        except Exception as e:
            return DiagnosticResult(
                check_id="internet",
                name="Internet Connection",
                category="connectivity",
                status=CheckStatus.FAIL,
                message=f"Error: {str(e)}",
                duration_ms=(time.time() - start) * 1000,
                actions=["Check system network configuration"]
            )

    async def check_dns(self) -> DiagnosticResult:
        """Check DNS resolution."""
        start = time.time()
        test_domain = "datasailors.io"
        try:
            ip = socket.gethostbyname(test_domain)
            duration = (time.time() - start) * 1000

            return DiagnosticResult(
                check_id="dns",
                name="DNS Resolution",
                category="connectivity",
                status=CheckStatus.PASS,
                message=f"DNS working ({test_domain} -> {ip})",
                duration_ms=duration,
                details={"domain": test_domain, "resolved_ip": ip}
            )
        except socket.gaierror as e:
            return DiagnosticResult(
                check_id="dns",
                name="DNS Resolution",
                category="connectivity",
                status=CheckStatus.FAIL,
                message=f"DNS resolution failed for {test_domain}",
                duration_ms=(time.time() - start) * 1000,
                actions=[
                    "Check DNS server configuration",
                    "Try: echo 'nameserver 8.8.8.8' | sudo tee /etc/resolv.conf",
                    "Verify network gateway is correct"
                ],
                details={"error": str(e)}
            )
        except Exception as e:
            return DiagnosticResult(
                check_id="dns",
                name="DNS Resolution",
                category="connectivity",
                status=CheckStatus.FAIL,
                message=f"Error: {str(e)}",
                duration_ms=(time.time() - start) * 1000,
                actions=["Check network configuration"]
            )

    async def check_mqtt(self) -> DiagnosticResult:
        """Check MQTT broker connectivity."""
        start = time.time()
        comm_config = self._load_communication_config()
        mqtt_config = comm_config.get('communication', {}).get('mqtt_config', {})

        if not mqtt_config:
            return DiagnosticResult(
                check_id="mqtt",
                name="MQTT Broker",
                category="connectivity",
                status=CheckStatus.SKIPPED,
                message="MQTT not configured",
                duration_ms=(time.time() - start) * 1000
            )

        host = mqtt_config.get('broker', mqtt_config.get('host', ''))
        port = mqtt_config.get('port', 1883)

        if not host:
            return DiagnosticResult(
                check_id="mqtt",
                name="MQTT Broker",
                category="connectivity",
                status=CheckStatus.SKIPPED,
                message="MQTT broker not configured",
                duration_ms=(time.time() - start) * 1000
            )

        try:
            # Test TCP connection to MQTT broker
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=5
            )
            writer.close()
            await writer.wait_closed()
            duration = (time.time() - start) * 1000

            return DiagnosticResult(
                check_id="mqtt",
                name="MQTT Broker",
                category="connectivity",
                status=CheckStatus.PASS,
                message=f"MQTT broker reachable at {host}:{port}",
                duration_ms=duration,
                details={"host": host, "port": port}
            )
        except asyncio.TimeoutError:
            return DiagnosticResult(
                check_id="mqtt",
                name="MQTT Broker",
                category="connectivity",
                status=CheckStatus.FAIL,
                message=f"Connection timeout to {host}:{port}",
                duration_ms=(time.time() - start) * 1000,
                actions=[
                    "Check MQTT broker is running",
                    "Verify broker hostname/IP is correct",
                    "Check firewall allows outbound connection"
                ],
                troubleshooting_tree="mqtt_connection_failed",
                details={"host": host, "port": port}
            )
        except Exception as e:
            return DiagnosticResult(
                check_id="mqtt",
                name="MQTT Broker",
                category="connectivity",
                status=CheckStatus.FAIL,
                message=f"Cannot connect to MQTT at {host}:{port}",
                duration_ms=(time.time() - start) * 1000,
                actions=[
                    "Verify MQTT broker is running",
                    "Check network/VPN connectivity",
                    "Verify firewall settings"
                ],
                troubleshooting_tree="mqtt_connection_failed",
                details={"host": host, "port": port, "error": str(e)}
            )

    async def check_api(self) -> DiagnosticResult:
        """Check backend API connectivity."""
        start = time.time()
        comm_config = self._load_communication_config()
        api_config = comm_config.get('communication', {}).get('api_endpoints', {})

        if not api_config:
            return DiagnosticResult(
                check_id="api",
                name="Backend API",
                category="connectivity",
                status=CheckStatus.SKIPPED,
                message="API endpoints not configured",
                duration_ms=(time.time() - start) * 1000
            )

        # Get the base URL from any endpoint
        base_url = api_config.get('base_url', '')
        if not base_url:
            # Recursively search for URL in nested config structure
            # Config structure: api_endpoints.electrical.measurements.url
            def find_url_in_dict(d):
                """Recursively find first URL in nested dictionary."""
                if isinstance(d, str) and d.startswith('http'):
                    return d
                if isinstance(d, dict):
                    # Check for 'url' key first
                    if 'url' in d and isinstance(d['url'], str) and d['url'].startswith('http'):
                        return d['url']
                    # Otherwise recurse into nested dicts
                    for key, value in d.items():
                        result = find_url_in_dict(value)
                        if result:
                            return result
                return None

            found_url = find_url_in_dict(api_config)
            if found_url:
                from urllib.parse import urlparse
                parsed = urlparse(found_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"

        if not base_url:
            return DiagnosticResult(
                check_id="api",
                name="Backend API",
                category="connectivity",
                status=CheckStatus.SKIPPED,
                message="No API base URL found in config",
                duration_ms=(time.time() - start) * 1000
            )

        try:
            # Parse host and port from URL
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)

            # Test TCP connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=5
            )
            writer.close()
            await writer.wait_closed()
            duration = (time.time() - start) * 1000

            return DiagnosticResult(
                check_id="api",
                name="Backend API",
                category="connectivity",
                status=CheckStatus.PASS,
                message=f"API server reachable at {host}:{port}",
                duration_ms=duration,
                details={"url": base_url, "host": host, "port": port}
            )
        except Exception as e:
            return DiagnosticResult(
                check_id="api",
                name="Backend API",
                category="connectivity",
                status=CheckStatus.FAIL,
                message=f"Cannot reach API server: {base_url}",
                duration_ms=(time.time() - start) * 1000,
                actions=[
                    "Check internet/VPN connectivity",
                    "Verify API URL is correct",
                    "Contact backend administrator"
                ],
                details={"url": base_url, "error": str(e)}
            )

    async def check_modbus_gateways(self) -> List[DiagnosticResult]:
        """Check connectivity to all configured Modbus TCP gateways."""
        results = []
        slave_config = self._load_slave_config()
        connections = slave_config.get('connections', [])

        tcp_connections = [c for c in connections if c.get('connection_type') == 'tcp']

        if not tcp_connections:
            results.append(DiagnosticResult(
                check_id="modbus_gateway",
                name="Modbus Gateways",
                category="connectivity",
                status=CheckStatus.SKIPPED,
                message="No TCP Modbus connections configured",
                duration_ms=0
            ))
            return results

        for conn in tcp_connections:
            conn_id = conn.get('id', 'unknown')
            label = conn.get('label', conn_id)
            host = conn.get('host', '')
            port = conn.get('port', 502)

            if not host:
                results.append(DiagnosticResult(
                    check_id=f"modbus_gateway_{conn_id}",
                    name=f"Gateway: {label}",
                    category="connectivity",
                    status=CheckStatus.SKIPPED,
                    message="No host configured",
                    duration_ms=0,
                    details={"connection_id": conn_id}
                ))
                continue

            start = time.time()
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=3
                )
                writer.close()
                await writer.wait_closed()
                duration = (time.time() - start) * 1000

                results.append(DiagnosticResult(
                    check_id=f"modbus_gateway_{conn_id}",
                    name=f"Gateway: {label}",
                    category="connectivity",
                    status=CheckStatus.PASS,
                    message=f"Reachable at {host}:{port}",
                    duration_ms=duration,
                    details={"connection_id": conn_id, "host": host, "port": port}
                ))
            except asyncio.TimeoutError:
                results.append(DiagnosticResult(
                    check_id=f"modbus_gateway_{conn_id}",
                    name=f"Gateway: {label}",
                    category="connectivity",
                    status=CheckStatus.FAIL,
                    message=f"Connection timeout to {host}:{port}",
                    duration_ms=(time.time() - start) * 1000,
                    actions=[
                        "Check gateway power LED is on",
                        "Verify Ethernet cable connection",
                        f"Try: ping {host}"
                    ],
                    troubleshooting_tree="gateway_connection_failed",
                    details={"connection_id": conn_id, "host": host, "port": port}
                ))
            except Exception as e:
                results.append(DiagnosticResult(
                    check_id=f"modbus_gateway_{conn_id}",
                    name=f"Gateway: {label}",
                    category="connectivity",
                    status=CheckStatus.FAIL,
                    message=f"Cannot connect: {str(e)}",
                    duration_ms=(time.time() - start) * 1000,
                    actions=[
                        "Check gateway is powered on",
                        "Verify network connectivity",
                        f"Confirm IP {host} is correct"
                    ],
                    troubleshooting_tree="gateway_connection_failed",
                    details={"connection_id": conn_id, "host": host, "port": port, "error": str(e)}
                ))

        return results

    async def check_cpu(self) -> DiagnosticResult:
        """Check CPU usage."""
        start = time.time()
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            duration = (time.time() - start) * 1000

            if cpu_percent >= 90:
                status = CheckStatus.FAIL
                message = f"CPU usage critical: {cpu_percent}%"
                actions = [
                    "Check for runaway processes",
                    "Consider reducing polling frequency",
                    "Restart the service if needed"
                ]
            elif cpu_percent >= 70:
                status = CheckStatus.WARN
                message = f"CPU usage elevated: {cpu_percent}%"
                actions = ["Monitor CPU usage", "Consider optimizing polling intervals"]
            else:
                status = CheckStatus.PASS
                message = f"CPU usage normal: {cpu_percent}%"
                actions = []

            return DiagnosticResult(
                check_id="cpu",
                name="CPU Usage",
                category="system",
                status=status,
                message=message,
                duration_ms=duration,
                actions=actions,
                details={"percent": cpu_percent, "count": psutil.cpu_count()}
            )
        except Exception as e:
            return DiagnosticResult(
                check_id="cpu",
                name="CPU Usage",
                category="system",
                status=CheckStatus.FAIL,
                message=f"Error checking CPU: {str(e)}",
                duration_ms=(time.time() - start) * 1000
            )

    async def check_memory(self) -> DiagnosticResult:
        """Check memory usage."""
        start = time.time()
        try:
            memory = psutil.virtual_memory()
            duration = (time.time() - start) * 1000

            if memory.percent >= 90:
                status = CheckStatus.FAIL
                message = f"Memory critical: {memory.percent}% used"
                actions = [
                    "Check for memory leaks",
                    "Restart the service to free memory",
                    "Consider adding more RAM"
                ]
            elif memory.percent >= 80:
                status = CheckStatus.WARN
                message = f"Memory elevated: {memory.percent}% used"
                actions = ["Monitor memory usage", "Plan for service restart if needed"]
            else:
                status = CheckStatus.PASS
                message = f"Memory normal: {memory.percent}% used"
                actions = []

            return DiagnosticResult(
                check_id="memory",
                name="Memory Usage",
                category="system",
                status=status,
                message=message,
                duration_ms=duration,
                actions=actions,
                details={
                    "percent": memory.percent,
                    "total_mb": round(memory.total / 1024 / 1024),
                    "used_mb": round(memory.used / 1024 / 1024),
                    "available_mb": round(memory.available / 1024 / 1024)
                }
            )
        except Exception as e:
            return DiagnosticResult(
                check_id="memory",
                name="Memory Usage",
                category="system",
                status=CheckStatus.FAIL,
                message=f"Error checking memory: {str(e)}",
                duration_ms=(time.time() - start) * 1000
            )

    async def check_disk(self) -> DiagnosticResult:
        """Check disk space."""
        start = time.time()
        try:
            disk = psutil.disk_usage('/')
            duration = (time.time() - start) * 1000

            if disk.percent >= 90:
                status = CheckStatus.FAIL
                message = f"Disk space critical: {disk.percent}% used"
                actions = [
                    "Clear old log files",
                    "Remove unnecessary data files",
                    "Check for large files: du -sh /*"
                ]
            elif disk.percent >= 80:
                status = CheckStatus.WARN
                message = f"Disk space low: {disk.percent}% used"
                actions = ["Plan disk cleanup", "Monitor disk usage"]
            else:
                status = CheckStatus.PASS
                message = f"Disk space OK: {disk.percent}% used"
                actions = []

            return DiagnosticResult(
                check_id="disk",
                name="Disk Space",
                category="system",
                status=status,
                message=message,
                duration_ms=duration,
                actions=actions,
                details={
                    "percent": disk.percent,
                    "total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
                    "used_gb": round(disk.used / 1024 / 1024 / 1024, 1),
                    "free_gb": round(disk.free / 1024 / 1024 / 1024, 1)
                }
            )
        except Exception as e:
            return DiagnosticResult(
                check_id="disk",
                name="Disk Space",
                category="system",
                status=CheckStatus.FAIL,
                message=f"Error checking disk: {str(e)}",
                duration_ms=(time.time() - start) * 1000
            )

    async def check_service(self) -> DiagnosticResult:
        """Check if dataskipper-boat service is running."""
        start = time.time()
        try:
            # Look for running dataskipper-boat process
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    cmdline_str = ' '.join(cmdline) if cmdline else ''

                    if 'dataskipper-boat' in cmdline_str or 'main.py' in cmdline_str:
                        uptime_secs = time.time() - proc.info.get('create_time', time.time())
                        uptime_str = self._format_uptime(uptime_secs)

                        return DiagnosticResult(
                            check_id="service",
                            name="Service Status",
                            category="system",
                            status=CheckStatus.PASS,
                            message=f"Running (uptime: {uptime_str})",
                            duration_ms=(time.time() - start) * 1000,
                            details={
                                "pid": proc.pid,
                                "uptime_seconds": uptime_secs,
                                "uptime_formatted": uptime_str
                            }
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # No process found
            return DiagnosticResult(
                check_id="service",
                name="Service Status",
                category="system",
                status=CheckStatus.FAIL,
                message="Service not running",
                duration_ms=(time.time() - start) * 1000,
                actions=[
                    "Start the service: sudo supervisorctl start <service-name>",
                    "Check supervisor logs for errors",
                    "Verify configuration files are valid"
                ]
            )
        except Exception as e:
            return DiagnosticResult(
                check_id="service",
                name="Service Status",
                category="system",
                status=CheckStatus.FAIL,
                message=f"Error checking service: {str(e)}",
                duration_ms=(time.time() - start) * 1000
            )

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")

        return " ".join(parts)

    async def check_devices(self, cache=None) -> List[DiagnosticResult]:
        """Check status of all configured devices.

        Args:
            cache: RegisterCache instance for checking device data freshness
        """
        results = []
        slave_config = self._load_slave_config()
        connections = slave_config.get('connections', [])

        # Get cache info if available
        client_cache = {}
        if cache:
            try:
                cache_info = cache.get_cache_info()
                client_cache = cache_info.get('clients', {})
            except Exception as e:
                logger.warning(f"Error getting cache info: {e}")

        for conn in connections:
            conn_id = conn.get('id', 'unknown')
            conn_label = conn.get('label', conn_id)

            for client in conn.get('clients', []):
                device_id = client.get('id', 'unknown')
                polling_interval = client.get('polling_interval', 60)

                # Calculate expected read interval
                http_interval = client.get('http_interval') or polling_interval
                mqtt_interval = client.get('mqtt_interval') or polling_interval
                http_enabled = client.get('http_enabled', True)
                mqtt_enabled = client.get('mqtt_enabled', True)

                if http_enabled and mqtt_enabled:
                    expected_interval = min(http_interval, mqtt_interval)
                elif http_enabled:
                    expected_interval = http_interval
                elif mqtt_enabled:
                    expected_interval = mqtt_interval
                else:
                    expected_interval = polling_interval

                # Check cache for this device
                cache_entry = client_cache.get(device_id, {})
                age = cache_entry.get('age')

                start = time.time()

                if age is None:
                    # No data ever received
                    results.append(DiagnosticResult(
                        check_id=f"device_{device_id}",
                        name=f"Device: {device_id}",
                        category="devices",
                        status=CheckStatus.FAIL,
                        message="No data received",
                        duration_ms=(time.time() - start) * 1000,
                        actions=[
                            "Check meter power and display",
                            "Verify RS485 wiring",
                            f"Confirm Unit ID is {client.get('unit_id')}"
                        ],
                        troubleshooting_tree="no_data_from_device",
                        details={
                            "connection": conn_label,
                            "unit_id": client.get('unit_id'),
                            "expected_interval": expected_interval
                        }
                    ))
                elif age > expected_interval * 3:
                    # Data very stale - effectively offline
                    results.append(DiagnosticResult(
                        check_id=f"device_{device_id}",
                        name=f"Device: {device_id}",
                        category="devices",
                        status=CheckStatus.FAIL,
                        message=f"Offline - last data {self._format_age(age)} ago",
                        duration_ms=(time.time() - start) * 1000,
                        actions=[
                            "Check device is powered on",
                            "Verify communication wiring",
                            "Check gateway connectivity"
                        ],
                        troubleshooting_tree="no_data_from_device",
                        details={
                            "connection": conn_label,
                            "age_seconds": age,
                            "expected_interval": expected_interval
                        }
                    ))
                elif age > expected_interval * 1.5:
                    # Data delayed
                    results.append(DiagnosticResult(
                        check_id=f"device_{device_id}",
                        name=f"Device: {device_id}",
                        category="devices",
                        status=CheckStatus.WARN,
                        message=f"Stale - last data {self._format_age(age)} ago (expected every {expected_interval}s)",
                        duration_ms=(time.time() - start) * 1000,
                        actions=[
                            "Check RS485 cable connections",
                            "Verify no communication interference"
                        ],
                        troubleshooting_tree="stale_data",
                        details={
                            "connection": conn_label,
                            "age_seconds": age,
                            "expected_interval": expected_interval
                        }
                    ))
                else:
                    # Data fresh
                    results.append(DiagnosticResult(
                        check_id=f"device_{device_id}",
                        name=f"Device: {device_id}",
                        category="devices",
                        status=CheckStatus.PASS,
                        message=f"Online - last data {self._format_age(age)} ago",
                        duration_ms=(time.time() - start) * 1000,
                        details={
                            "connection": conn_label,
                            "age_seconds": age,
                            "expected_interval": expected_interval
                        }
                    ))

        if not results:
            results.append(DiagnosticResult(
                check_id="devices",
                name="Devices",
                category="devices",
                status=CheckStatus.SKIPPED,
                message="No devices configured",
                duration_ms=0
            ))

        return results

    def _format_age(self, seconds: float) -> str:
        """Format age in human-readable format."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}h"
        else:
            return f"{int(seconds / 86400)}d"

    async def run_all_checks(self, cache=None) -> DiagnosticReport:
        """Run all diagnostic checks.

        Args:
            cache: RegisterCache instance for device checks

        Returns:
            Complete diagnostic report
        """
        start = time.time()
        results = []

        # Run connectivity checks concurrently
        connectivity_tasks = [
            self.check_internet(),
            self.check_dns(),
            self.check_mqtt(),
            self.check_api(),
        ]
        connectivity_results = await asyncio.gather(*connectivity_tasks, return_exceptions=True)

        for result in connectivity_results:
            if isinstance(result, Exception):
                logger.error(f"Connectivity check error: {result}")
            elif result:
                results.append(result)

        # Run gateway checks (returns list)
        gateway_results = await self.check_modbus_gateways()
        results.extend(gateway_results)

        # Run system checks concurrently
        system_tasks = [
            self.check_cpu(),
            self.check_memory(),
            self.check_disk(),
            self.check_service(),
        ]
        system_results = await asyncio.gather(*system_tasks, return_exceptions=True)

        for result in system_results:
            if isinstance(result, Exception):
                logger.error(f"System check error: {result}")
            elif result:
                results.append(result)

        # Run device checks (returns list)
        device_results = await self.check_devices(cache=cache)
        results.extend(device_results)

        # Calculate summary
        summary = {"pass": 0, "warn": 0, "fail": 0, "skipped": 0}
        for result in results:
            if result.status == CheckStatus.PASS:
                summary["pass"] += 1
            elif result.status == CheckStatus.WARN:
                summary["warn"] += 1
            elif result.status == CheckStatus.FAIL:
                summary["fail"] += 1
            elif result.status == CheckStatus.SKIPPED:
                summary["skipped"] += 1

        return DiagnosticReport(
            results=results,
            summary=summary,
            timestamp=datetime.now().isoformat(),
            duration_ms=(time.time() - start) * 1000
        )

    async def run_category_checks(self, category: str, cache=None) -> List[DiagnosticResult]:
        """Run checks for a specific category.

        Args:
            category: One of 'connectivity', 'system', 'devices'
            cache: RegisterCache instance for device checks
        """
        if category == "connectivity":
            results = []
            tasks = [
                self.check_internet(),
                self.check_dns(),
                self.check_mqtt(),
                self.check_api(),
            ]
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in task_results:
                if isinstance(result, DiagnosticResult):
                    results.append(result)

            gateway_results = await self.check_modbus_gateways()
            results.extend(gateway_results)
            return results

        elif category == "system":
            tasks = [
                self.check_cpu(),
                self.check_memory(),
                self.check_disk(),
                self.check_service(),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if isinstance(r, DiagnosticResult)]

        elif category == "devices":
            return await self.check_devices(cache=cache)

        else:
            return []

    def get_troubleshooting_tree(self, tree_id: str) -> Optional[Dict[str, Any]]:
        """Get a troubleshooting decision tree by ID."""
        return TROUBLESHOOTING_TREES.get(tree_id)

    def get_all_troubleshooting_trees(self) -> Dict[str, Dict[str, Any]]:
        """Get all available troubleshooting trees."""
        return TROUBLESHOOTING_TREES


# Global diagnostic service instance
_diagnostic_service: Optional[DiagnosticService] = None


def get_diagnostic_service(config_dir: str = None) -> DiagnosticService:
    """Get or create the global diagnostic service instance."""
    global _diagnostic_service
    if _diagnostic_service is None:
        _diagnostic_service = DiagnosticService(config_dir)
    return _diagnostic_service
