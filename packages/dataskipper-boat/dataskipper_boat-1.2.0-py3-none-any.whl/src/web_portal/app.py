"""
RTU Web Portal - Lightweight FastAPI application for monitoring and configuration.

Performance considerations:
- All endpoints are async to not block the main application
- Metrics are cached to reduce system calls
- Log streaming is rate-limited
- Maximum 3 concurrent WebSocket connections
"""

import asyncio
import logging
import os
import platform
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import subprocess
import math
import psutil
import yaml

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from src.web_portal.auth import (
    authenticate, validate_session, logout, get_session_cookie_name,
    get_credentials_store, SESSION_COOKIE_NAME
)

logger = logging.getLogger(__name__)


def sanitize_for_json(obj):
    """Sanitize values for JSON serialization (handles inf, nan, etc.)."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    return obj

# Configuration
PORTAL_PORT = 8080
MAX_WEBSOCKET_CONNECTIONS = 3
METRICS_CACHE_SECONDS = 5
LOG_STREAM_INTERVAL = 1.0  # seconds between log updates
MAX_LOG_LINES = 500
SUPERVISOR_CONF_DIR = Path("/etc/supervisor/conf.d")
SUPERVISOR_CONF_PATH = SUPERVISOR_CONF_DIR / "dcu.conf"  # Legacy default
SUPERVISOR_LOG_DIR = Path("/var/log/supervisor")

# Current service's config directory (from environment)
CURRENT_CONFIG_DIR = os.getenv('CONFIG_DIR', '')


def get_current_config_dir() -> str:
    """Get the config directory for the currently running service."""
    return CURRENT_CONFIG_DIR


def get_device_id() -> str:
    """
    Get the device ID for this RTU.

    Priority:
    1. device_id from communication.yaml (if exists)
    2. First supervisor service name
    3. Fallback to "unknown-device"
    """
    # Try to read device_id from communication.yaml
    config_dir = get_current_config_dir()
    if config_dir:
        comm_config_path = Path(config_dir) / "communication.yaml"
        if comm_config_path.exists():
            try:
                with open(comm_config_path, 'r') as f:
                    data = yaml.safe_load(f)
                    # Check for device_id at top level or under communication
                    device_id = data.get('device_id') or data.get('communication', {}).get('device_id')
                    if device_id:
                        return device_id
            except Exception as e:
                logger.warning(f"Error reading device_id from communication.yaml: {e}")

    # Fallback to supervisor service name
    supervisor_config = parse_supervisor_config()
    services = supervisor_config.get("services", [])
    if services:
        return services[0].get("name", "unknown-device")

    return "unknown-device"


def get_service_status_from_process(service_name: str, config_dir: str = None) -> Dict[str, Any]:
    """
    Get service status by checking if the process is running.
    This avoids supervisor socket permission issues.

    We match processes by checking:
    1. If config_dir is provided, check for CONFIG_DIR in process environment
    2. Otherwise fall back to checking if 'dataskipper-boat' is in cmdline
    """
    try:
        # Look for running processes that match dataskipper-boat
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status', 'create_time']):
            try:
                cmdline = proc.info.get('cmdline', [])
                cmdline_str = ' '.join(cmdline) if cmdline else ''

                # Check if this is a dataskipper-boat process
                if 'dataskipper-boat' not in cmdline_str:
                    continue

                # If we have a config_dir, try to match by environment variable
                if config_dir:
                    try:
                        proc_obj = psutil.Process(proc.pid)
                        environ = proc_obj.environ()
                        proc_config_dir = environ.get('CONFIG_DIR', '')

                        # Check if this process's CONFIG_DIR matches our service's config_dir
                        if proc_config_dir and Path(proc_config_dir).resolve() == Path(config_dir).resolve():
                            uptime_secs = time.time() - proc.info.get('create_time', time.time())
                            uptime_str = format_process_uptime(uptime_secs)
                            return {
                                "state": "RUNNING",
                                "statename": "RUNNING",
                                "pid": proc.pid,
                                "description": f"pid {proc.pid}, uptime {uptime_str}"
                            }
                    except (psutil.AccessDenied, psutil.NoSuchProcess, KeyError):
                        # Can't read environ, fall back to cmdline matching
                        pass

                # Fallback: if service_name is exactly in the cmdline
                if service_name in cmdline_str:
                    uptime_secs = time.time() - proc.info.get('create_time', time.time())
                    uptime_str = format_process_uptime(uptime_secs)
                    return {
                        "state": "RUNNING",
                        "statename": "RUNNING",
                        "pid": proc.pid,
                        "description": f"pid {proc.pid}, uptime {uptime_str}"
                    }

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # No matching process found - assume stopped
        return {
            "state": "STOPPED",
            "statename": "STOPPED",
            "description": "Not running"
        }

    except Exception as e:
        return {
            "state": "UNKNOWN",
            "statename": "ERROR",
            "description": str(e)
        }


def format_process_uptime(seconds: float) -> str:
    """Format process uptime."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def get_service_logs(service_name: str, lines: int = 100) -> List[str]:
    """
    Get service logs from supervisor log files or journald.
    Supervisor log files are typically named: {program_name}_stdout.log or {program_name}_stderr.log
    Prefer stderr logs as they contain the actual application logs with timestamps.
    """
    logs = []
    import glob as glob_module

    # Try supervisor log files - STDERR FIRST (contains actual app logs with timestamps)
    log_patterns = [
        # Primary: supervisor stderr logs (actual application logs)
        str(SUPERVISOR_LOG_DIR / f"{service_name}_stderr.log"),
        # Numbered variants for stderr (supervisor rotates logs)
        str(SUPERVISOR_LOG_DIR / f"{service_name}_stderr.log.*"),
        # Then stdout as fallback
        str(SUPERVISOR_LOG_DIR / f"{service_name}_stdout.log"),
        str(SUPERVISOR_LOG_DIR / f"{service_name}_stdout.log.*"),
        # Alternative formats
        str(SUPERVISOR_LOG_DIR / f"{service_name}-stderr---supervisor-*.log"),
        str(SUPERVISOR_LOG_DIR / f"{service_name}-stdout---supervisor-*.log"),
        str(SUPERVISOR_LOG_DIR / f"{service_name}_00-stderr.log"),
        str(SUPERVISOR_LOG_DIR / f"{service_name}_00-stdout.log"),
        # Generic log file
        str(SUPERVISOR_LOG_DIR / f"{service_name}.log"),
        f"/var/log/{service_name}.log",
        str(Path.home() / "dataskipper-boat" / "logs" / f"{service_name}.log"),
    ]

    for pattern in log_patterns:
        try:
            if '*' in pattern:
                # Glob pattern - find most recent matching file
                matching_files = glob_module.glob(pattern)
                if matching_files:
                    # Get most recent file
                    log_file = max(matching_files, key=os.path.getmtime)
                    with open(log_file, 'r') as f:
                        logs = f.readlines()[-lines:]
                        logs = [l.strip() for l in logs if l.strip()]
                        if logs:
                            return logs
            else:
                # Direct file path
                if os.path.exists(pattern):
                    with open(pattern, 'r') as f:
                        logs = f.readlines()[-lines:]
                        logs = [l.strip() for l in logs if l.strip()]
                        if logs:
                            return logs
        except PermissionError:
            # Try reading with tail command as fallback for permission issues
            try:
                result = subprocess.run(
                    ['tail', '-n', str(lines), pattern.replace('*', '')],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    return [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]
            except Exception:
                pass
            continue
        except Exception:
            continue

    # Try journalctl as fallback
    try:
        result = subprocess.run(
            ['journalctl', '-u', service_name, '-n', str(lines), '--no-pager', '-o', 'short'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]
    except Exception:
        pass

    return logs

# Paths
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
LOG_FILE = Path("/var/log/dataskipper-boat.log")

# Initialize FastAPI
app = FastAPI(
    title="RTU Control Portal",
    description="Lightweight monitoring and configuration interface",
    version="1.0.0",
    docs_url=None,  # Disable Swagger UI to save resources
    redoc_url=None  # Disable ReDoc to save resources
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure all errors return JSON."""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "error": "Internal Server Error"}
    )


# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ============== Authentication ==============

# Public paths that don't require authentication
PUBLIC_PATHS = {
    "/login",
    "/api/auth/login",
    "/api/auth/device-info",
    "/static",
}


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to require authentication for all routes except public ones."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Allow public paths
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)

        # Check for valid session
        session_token = request.cookies.get(SESSION_COOKIE_NAME)

        if not session_token:
            # No session, redirect to login
            if request.url.path.startswith("/api/"):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required"}
                )
            return RedirectResponse(url="/login", status_code=302)

        session = validate_session(session_token)
        if not session:
            # Invalid or expired session
            if request.url.path.startswith("/api/"):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Session expired. Please login again."}
                )
            response = RedirectResponse(url="/login", status_code=302)
            response.delete_cookie(SESSION_COOKIE_NAME)
            return response

        # Valid session, continue
        request.state.user = session.get("username")
        return await call_next(request)


# Add authentication middleware
app.add_middleware(AuthenticationMiddleware)


# Cache for metrics and supervisor config
_metrics_cache: Dict[str, Any] = {}
_metrics_cache_time: float = 0
_supervisor_config_cache: Optional[Dict[str, Any]] = None

# Active WebSocket connections
active_connections: List[WebSocket] = []

# Shared register cache (injected from main process)
_shared_register_cache = None


def set_register_cache(cache):
    """Set the shared register cache from the main process.

    This allows the web portal to access the same cache instance
    that the main Modbus monitor is using, enabling real-time
    device status display.
    """
    global _shared_register_cache
    _shared_register_cache = cache
    logger.info(f"Web portal: register cache injected (id={id(cache)})")


class ConfigUpdate(BaseModel):
    """Model for configuration updates."""
    filename: str
    content: str


class ConnectionUpdate(BaseModel):
    """Model for connection configuration updates."""
    id: str
    label: str
    connection_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    timeout: int = 2
    retries: int = 1
    reconnect_delay: int = 1
    # Serial specific
    serial_port: Optional[str] = None
    baud_rate: Optional[int] = None
    parity: Optional[str] = None
    stop_bits: Optional[int] = None
    bytesize: Optional[int] = None


class ClientUpdate(BaseModel):
    """Model for client/device configuration updates."""
    id: str
    type: str
    polling_interval: int
    unit_id: int
    endianness: str = "little"
    mqtt_preferred: bool = False
    mqtt_preferred_topic: str = ""


class RegisterUpdate(BaseModel):
    """Model for register configuration updates."""
    address: int
    count: int = 2
    data_type: str = "float"
    field_name: str
    label: str
    unit: str
    register_type: str = "holding"


class AlertConfig(BaseModel):
    """Model for alert configuration."""
    device_id: str
    metric: str
    threshold: float
    condition: str  # 'above', 'below', 'equals'
    enabled: bool = True


def parse_supervisor_config() -> Dict[str, Any]:
    """Parse all supervisor .conf files to discover all services and their config paths.

    Scans all .conf files in /etc/supervisor/conf.d/ to find dataskipper services.
    """
    global _supervisor_config_cache

    if _supervisor_config_cache is not None:
        return _supervisor_config_cache

    services = []

    # Check if the supervisor conf directory exists
    if not SUPERVISOR_CONF_DIR.exists():
        # Fallback to default config directory
        return {
            "services": [{
                "name": "dataskipper-boat",
                "program_name": "dataskipper-boat",
                "config_dir": str(Path.home() / "config"),
                "data_dir": str(Path.home() / "data"),
                "directory": str(Path.home() / "dataskipper-boat"),
                "command": ""
            }],
            "default_config_dir": str(Path.home() / "config")
        }

    try:
        # Scan all .conf files in the supervisor conf directory
        conf_files = list(SUPERVISOR_CONF_DIR.glob("*.conf"))
        logger.info(f"Found {len(conf_files)} supervisor config files: {[f.name for f in conf_files]}")

        for conf_file in conf_files:
            try:
                content = conf_file.read_text()
                current_service = None

                for line in content.split('\n'):
                    line = line.strip()

                    # Skip comments and empty lines
                    if line.startswith('#') or not line:
                        continue

                    # New program section
                    if line.startswith('[program:'):
                        if current_service:
                            services.append(current_service)
                        program_name = line[9:-1]  # Extract name from [program:name]
                        current_service = {
                            "name": program_name,
                            "program_name": program_name,
                            "config_dir": str(Path.home() / "config"),
                            "data_dir": str(Path.home() / "data"),
                            "directory": "",
                            "command": "",
                            "conf_file": str(conf_file)
                        }

                    elif current_service and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        if key == 'command':
                            current_service['command'] = value
                        elif key == 'directory':
                            current_service['directory'] = value
                        elif key == 'environment':
                            # Parse environment variables
                            env_parts = re.findall(r'(\w+)="([^"]*)"', value)
                            for env_key, env_value in env_parts:
                                if env_key == 'CONFIG_DIR':
                                    current_service['config_dir'] = env_value
                                elif env_key == 'DATA_DIR':
                                    current_service['data_dir'] = env_value

                if current_service:
                    services.append(current_service)

            except Exception as e:
                logger.error(f"Error parsing {conf_file}: {e}")

    except Exception as e:
        logger.error(f"Error scanning supervisor config directory: {e}")
        services = [{
            "name": "dataskipper-boat",
            "program_name": "dataskipper-boat",
            "config_dir": str(Path.home() / "config"),
            "data_dir": str(Path.home() / "data"),
            "directory": str(Path.home() / "dataskipper-boat"),
            "command": ""
        }]

    # Sort services by name for consistent ordering
    services.sort(key=lambda s: s['name'])

    _supervisor_config_cache = {
        "services": services,
        "default_config_dir": services[0]['config_dir'] if services else str(Path.home() / "config")
    }

    logger.info(f"Discovered {len(services)} services: {[s['name'] for s in services]}")
    return _supervisor_config_cache


def get_all_config_dirs() -> List[Dict[str, Any]]:
    """Get all config directories from all services."""
    supervisor_config = parse_supervisor_config()
    config_dirs = []
    seen_dirs = set()

    for service in supervisor_config['services']:
        config_dir = service['config_dir']
        if config_dir not in seen_dirs:
            seen_dirs.add(config_dir)
            config_dirs.append({
                "path": config_dir,
                "service": service['name'],
                "exists": Path(config_dir).exists()
            })

    return config_dirs


def get_cached_metrics() -> Dict[str, Any]:
    """Get system metrics with caching to reduce overhead."""
    global _metrics_cache, _metrics_cache_time

    current_time = time.time()
    if current_time - _metrics_cache_time < METRICS_CACHE_SECONDS:
        return _metrics_cache

    supervisor_config = parse_supervisor_config()

    try:
        # Get process info for dataskipper-boat processes
        boat_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_percent', 'cpu_percent']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'dataskipper-boat' in ' '.join(cmdline):
                    boat_processes.append({
                        "pid": proc.pid,
                        "memory_percent": round(proc.info['memory_percent'], 2),
                        "cpu_percent": proc.info['cpu_percent'],
                        "cmdline": ' '.join(cmdline)[:100]
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # System metrics
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Get service status by checking running processes
        services_status = []
        for service in supervisor_config['services']:
            # Use process-based detection instead of supervisorctl
            # Pass config_dir to match processes by their CONFIG_DIR environment variable
            proc_info = get_service_status_from_process(service['program_name'], service.get('config_dir'))

            # Map state to simple status
            state = proc_info.get('state', 'UNKNOWN')
            if state == 'RUNNING':
                status = 'running'
            elif state == 'STOPPED':
                status = 'stopped'
            elif state == 'FATAL':
                status = 'fatal'
            elif state in ['STARTING', 'STOPPING', 'BACKOFF']:
                status = 'pending'
            else:
                status = 'unknown'

            services_status.append({
                "name": service['name'],
                "status": status,
                "state": state,
                "description": proc_info.get('description', ''),
                "config_dir": service['config_dir'],
                "pid": proc_info.get('pid')
            })

        # Boot time and uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_str = format_uptime(uptime_seconds)

        # Get network interface IPs
        network_interfaces = []
        try:
            addrs = psutil.net_if_addrs()
            for iface_name, iface_addrs in addrs.items():
                # Skip loopback and docker interfaces
                if iface_name.startswith(('lo', 'docker', 'br-', 'veth')):
                    continue
                for addr in iface_addrs:
                    # Only include IPv4 addresses (family 2 is AF_INET)
                    if addr.family == 2:  # AF_INET
                        network_interfaces.append({
                            "interface": iface_name,
                            "ip": addr.address,
                            "netmask": addr.netmask
                        })
        except Exception as net_err:
            logger.warning(f"Error getting network interfaces: {net_err}")

        _metrics_cache = {
            "hostname": platform.node(),
            "platform": platform.system(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "boot_time": boot_time.isoformat(),
            "uptime": uptime_str,
            "uptime_seconds": uptime_seconds,
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "cpu_count": psutil.cpu_count(),
            "memory_total_mb": round(memory.total / 1024 / 1024),
            "memory_used_mb": round(memory.used / 1024 / 1024),
            "memory_percent": memory.percent,
            "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
            "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 1),
            "disk_percent": disk.percent,
            "services": services_status,
            "boat_processes": boat_processes,
            "network_interfaces": network_interfaces,
            "timestamp": datetime.now().isoformat()
        }
        _metrics_cache_time = current_time

    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        _metrics_cache = {"error": str(e), "timestamp": datetime.now().isoformat()}

    return _metrics_cache


def format_uptime(seconds: float) -> str:
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


def get_config_files_for_service(config_dir: str) -> List[Dict[str, Any]]:
    """List all configuration files for a specific service."""
    config_files = []
    config_path = Path(config_dir)

    # Files to exclude from config editor (internal codebase files)
    EXCLUDED_FILES = {'meter_registry.yaml'}

    if config_path.exists():
        for f in config_path.glob("*.yaml"):
            # Skip excluded files
            if f.name in EXCLUDED_FILES:
                continue

            stat = f.stat()
            # Determine config type
            config_type = "unknown"
            if "communication" in f.name.lower():
                config_type = "communication"
            elif "slave" in f.name.lower() or "config" in f.name.lower():
                config_type = "slave"

            config_files.append({
                "name": f.name,
                "path": str(f),
                "config_dir": config_dir,
                "size_kb": round(stat.st_size / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "type": config_type
            })

    return sorted(config_files, key=lambda x: x['name'])


def get_all_config_files() -> List[Dict[str, Any]]:
    """List all configuration files from all config directories."""
    all_files = []
    for config_dir_info in get_all_config_dirs():
        if config_dir_info['exists']:
            files = get_config_files_for_service(config_dir_info['path'])
            for f in files:
                f['service'] = config_dir_info['service']
            all_files.extend(files)
    return all_files


def read_config_file(config_dir: str, filename: str) -> str:
    """Read a configuration file safely."""
    config_path = Path(config_dir)
    file_path = config_path / filename

    # Security check - prevent path traversal
    if not file_path.resolve().is_relative_to(config_path.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return file_path.read_text()


def parse_slave_config(content: str) -> Dict[str, Any]:
    """Parse slave configuration and return structured data for UI."""
    try:
        data = yaml.safe_load(content)
        connections = data.get('connections', [])

        parsed = {
            "connections": []
        }

        for conn in connections:
            conn_type = conn.get('connection_type', 'tcp')
            # Default framer based on connection type
            default_framer = 'socket' if conn_type == 'tcp' else 'rtu'

            connection = {
                "id": conn.get('id', ''),
                "label": conn.get('label', ''),
                "connection_type": conn_type,
                "framer": conn.get('framer', default_framer),
                "timeout": conn.get('timeout', 2),
                "retries": conn.get('retries', 1),
                "reconnect_delay": conn.get('reconnect_delay', 1),
                "clients": []
            }

            # TCP specific
            if conn_type == 'tcp':
                connection['host'] = conn.get('host', '')
                connection['port'] = conn.get('port', 502)
            # Serial specific
            elif conn_type == 'serial':
                connection['serial_port'] = conn.get('port', '')
                connection['baud_rate'] = conn.get('baud_rate', 9600)
                connection['parity'] = conn.get('parity', 'N')
                connection['stop_bits'] = conn.get('stop_bits', 1)
                connection['bytesize'] = conn.get('bytesize', 8)

            # Parse clients
            for client in conn.get('clients', []):
                client_data = {
                    "id": client.get('id', ''),
                    "type": client.get('type', 'electrical'),
                    "polling_interval": client.get('polling_interval', 60),
                    "unit_id": client.get('unit_id', 1),
                    "endianness": client.get('endianness', 'little'),
                    # New unified MQTT/HTTP configuration
                    "mqtt_enabled": client.get('mqtt_enabled', True),
                    "http_enabled": client.get('http_enabled', True),
                    "mqtt_topic": client.get('mqtt_topic', ''),
                    "mqtt_interval": client.get('mqtt_interval', None),
                    "http_interval": client.get('http_interval', None),
                    # Meter registry fields
                    "meter_model": client.get('meter_model', ''),
                    "profile": client.get('profile', ''),
                    "target_table": client.get('target_table', ''),
                    # Legacy fields (for backward compatibility)
                    "mqtt_preferred": client.get('mqtt_preferred', False),
                    "mqtt_preferred_topic": client.get('mqtt_preferred_topic', ''),
                    "registers": []
                }

                # Parse registers
                for reg in client.get('registers', []):
                    client_data['registers'].append({
                        "address": reg.get('address', 0),
                        "count": reg.get('count', 2),
                        "data_type": reg.get('data_type', 'float'),
                        "field_name": reg.get('field_name', ''),
                        "label": reg.get('label', ''),
                        "unit": reg.get('unit', ''),
                        "register_type": reg.get('register_type', 'holding'),
                        "multiplication_factor": reg.get('multiplication_factor', None)
                    })

                connection['clients'].append(client_data)

            parsed['connections'].append(connection)

        return parsed

    except Exception as e:
        logger.error(f"Error parsing slave config: {e}")
        return {"error": str(e), "connections": []}


def parse_communication_config(content: str) -> Dict[str, Any]:
    """Parse communication configuration and return structured data for UI."""
    try:
        data = yaml.safe_load(content)
        comm = data.get('communication', {})

        # device_id can be at top level or under communication
        device_id = data.get('device_id') or comm.get('device_id', '')

        parsed = {
            "device_id": device_id,
            "api_endpoints": comm.get('api_endpoints', {}),
            "mqtt_config": comm.get('mqtt_config', {}),
            "retry_config": comm.get('retry_config', {}),
            "discord_webhook_url": data.get('discord_webhook_url', ''),
            "ntp_config": comm.get('ntp_config', {}),
            "weather_config": comm.get('weather_config', {}),
            "aggregation_config": comm.get('aggregation_config', {}),
            "performance_config": comm.get('performance_config', {}),
            "watchdog_config": comm.get('watchdog_config', {}),
            "modbus_tcp_gateway": comm.get('modbus_tcp_gateway', {}),
            "cache_ttl": comm.get('cache_ttl', 120)
        }

        return parsed

    except Exception as e:
        logger.error(f"Error parsing communication config: {e}")
        return {"error": str(e)}


def validate_yaml(content: str) -> bool:
    """Validate YAML syntax."""
    try:
        yaml.safe_load(content)
        return True
    except yaml.YAMLError:
        return False


def get_recent_logs(service_name: str = None, lines: int = 100, level_filter: Optional[str] = None) -> List[str]:
    """Get recent log lines with optional filtering."""
    logs = []
    supervisor_config = parse_supervisor_config()

    # Determine which service to get logs for
    if service_name is None and supervisor_config['services']:
        service_name = supervisor_config['services'][0]['program_name']

    # Use our log retrieval function that doesn't require supervisor permissions
    if service_name:
        logs = get_service_logs(service_name, lines=500)

    # If no logs found, try the default log file
    if not logs and LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r') as f:
                logs = f.readlines()[-500:]
                logs = [l.strip() for l in logs]
        except Exception:
            pass

    # Also try reading from data directory logs
    if not logs:
        for service in supervisor_config['services']:
            data_dir = service.get('data_dir', '')
            if data_dir:
                log_path = Path(data_dir) / 'logs'
                if log_path.exists():
                    try:
                        import glob
                        log_files = glob.glob(str(log_path / '*.log'))
                        if log_files:
                            latest_log = max(log_files, key=os.path.getmtime)
                            with open(latest_log, 'r') as f:
                                logs = f.readlines()[-500:]
                                logs = [l.strip() for l in logs]
                                if logs:
                                    break
                    except Exception:
                        continue

    # Filter by level if specified
    if level_filter and level_filter.upper() in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        level = level_filter.upper()
        logs = [l for l in logs if level in l]

    return logs[-lines:]


# ============== Authentication Routes ==============

class LoginRequest(BaseModel):
    """Model for login request."""
    username: str
    password: str


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    # If already logged in, redirect to dashboard
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token and validate_session(session_token):
        return RedirectResponse(url="/", status_code=302)

    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/api/auth/login")
async def api_login(request: Request, login_data: LoginRequest):
    """Handle login request."""
    # Get client IP for rate limiting
    client_ip = request.client.host if request.client else "unknown"

    # Authenticate
    result = authenticate(login_data.username, login_data.password, client_ip)

    if result["success"]:
        # Create response with session cookie
        response = JSONResponse({
            "success": True,
            "message": "Login successful",
            "redirect": "/"
        })

        # Set secure session cookie
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=result["token"],
            httponly=True,  # Prevent JavaScript access
            secure=False,  # Set to True if using HTTPS
            samesite="lax",
            max_age=24 * 60 * 60  # 24 hours
        )

        return response
    else:
        # Return error with rate limiting info
        return JSONResponse({
            "success": False,
            "message": result.get("message", "Login failed"),
            "attempts_remaining": result.get("attempts_remaining"),
            "locked_until": result.get("locked_until")
        }, status_code=401)


@app.post("/api/auth/logout")
async def api_logout(request: Request):
    """Handle logout request."""
    session_token = request.cookies.get(SESSION_COOKIE_NAME)

    if session_token:
        logout(session_token)

    response = JSONResponse({"success": True, "message": "Logged out"})
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@app.get("/api/auth/device-info")
async def api_device_info():
    """Get device info for login page (public endpoint)."""
    device_id = get_device_id()

    return JSONResponse({"device_id": device_id})


@app.get("/api/auth/status")
async def api_auth_status(request: Request):
    """Check authentication status."""
    return JSONResponse({
        "authenticated": True,
        "username": getattr(request.state, "user", None)
    })


# ============== Routes ==============

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    metrics = get_cached_metrics()
    config_files = get_all_config_files()
    supervisor_config = parse_supervisor_config()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "metrics": metrics,
        "config_files": config_files,
        "services": supervisor_config['services']
    })


@app.get("/api/metrics")
async def api_metrics():
    """API endpoint for metrics (used by JavaScript polling)."""
    return JSONResponse(get_cached_metrics())


@app.get("/api/cache/debug")
async def api_cache_debug():
    """Debug endpoint to check shared cache status."""
    if _shared_register_cache:
        try:
            stats = _shared_register_cache.get_stats()
            info = _shared_register_cache.get_cache_info()
            return JSONResponse({
                "cache_injected": True,
                "cache_id": id(_shared_register_cache),
                "stats": stats,
                "client_count": len(info.get("clients", {})),
                "client_ids": list(info.get("clients", {}).keys())[:10]
            })
        except Exception as e:
            return JSONResponse({
                "cache_injected": True,
                "error": str(e)
            })
    else:
        return JSONResponse({
            "cache_injected": False,
            "message": "No shared cache - running standalone or cache not yet injected"
        })


@app.get("/api/supervisor")
async def api_supervisor():
    """API endpoint for supervisor configuration."""
    return JSONResponse(parse_supervisor_config())


@app.get("/api/logs")
async def api_logs(service: Optional[str] = None, lines: int = 100, level: Optional[str] = None):
    """API endpoint for log retrieval."""
    logs = get_recent_logs(service_name=service, lines=min(lines, MAX_LOG_LINES), level_filter=level)
    return JSONResponse({"logs": logs, "count": len(logs)})


@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Configuration management page."""
    config_files = get_all_config_files()
    supervisor_config = parse_supervisor_config()

    return templates.TemplateResponse("config.html", {
        "request": request,
        "config_files": config_files,
        "services": supervisor_config['services'],
        "config_dirs": get_all_config_dirs()
    })


@app.get("/config/editor", response_class=HTMLResponse)
async def config_editor_page(request: Request):
    """Intuitive configuration editor page."""
    config_files = get_all_config_files()
    supervisor_config = parse_supervisor_config()

    return templates.TemplateResponse("config_editor.html", {
        "request": request,
        "config_files": config_files,
        "services": supervisor_config['services'],
        "config_dirs": get_all_config_dirs()
    })


@app.get("/api/config/list")
async def list_configs():
    """List all config files across all services."""
    return JSONResponse({
        "config_files": get_all_config_files(),
        "config_dirs": get_all_config_dirs()
    })


@app.get("/api/config/backup")
async def backup_all_configs():
    """Create a ZIP backup of all config files."""
    import zipfile
    import io
    from fastapi.responses import StreamingResponse

    # Create ZIP in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        config_files = get_all_config_files()
        for file_info in config_files:
            config_dir = file_info.get('config_dir', '')
            filename = file_info.get('name', '')
            try:
                content = read_config_file(config_dir, filename)
                # Use relative path in ZIP
                zip_path = f"{Path(config_dir).name}/{filename}" if config_dir else filename
                zip_file.writestr(zip_path, content)
            except Exception as e:
                logger.warning(f"Could not backup {filename}: {e}")

    zip_buffer.seek(0)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"config_backup_{timestamp}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
    )


@app.get("/api/config/validate")
async def validate_all_configs():
    """Validate all YAML config files."""
    config_files = get_all_config_files()
    errors = []
    valid_count = 0

    for file_info in config_files:
        config_dir = file_info.get('config_dir', '')
        filename = file_info.get('name', '')
        try:
            content = read_config_file(config_dir, filename)
            if validate_yaml(content):
                valid_count += 1
            else:
                errors.append({
                    "file": filename,
                    "config_dir": config_dir,
                    "error": "Invalid YAML syntax"
                })
        except Exception as e:
            errors.append({
                "file": filename,
                "config_dir": config_dir,
                "error": str(e)
            })

    return JSONResponse({
        "valid": len(errors) == 0,
        "total_files": len(config_files),
        "valid_count": valid_count,
        "errors": errors
    })


@app.get("/config/edit/slave", response_class=HTMLResponse)
async def config_slave_editor_page(request: Request, file: str, dir: str):
    """Visual editor for slave config files."""
    return templates.TemplateResponse("config_slave_editor.html", {
        "request": request,
        "config_file": file,
        "config_dir": dir
    })


@app.get("/config/edit/comm", response_class=HTMLResponse)
async def config_comm_editor_page(request: Request, file: str, dir: str):
    """Form-based editor for communication config files."""
    return templates.TemplateResponse("config_comm_editor.html", {
        "request": request,
        "config_file": file,
        "config_dir": dir
    })


@app.get("/api/config/{config_dir:path}/{filename}")
async def get_config(config_dir: str, filename: str, parsed: bool = False):
    """Get configuration file content."""
    # Handle URL encoded path
    config_dir = "/" + config_dir if not config_dir.startswith("/") else config_dir
    content = read_config_file(config_dir, filename)

    if parsed:
        if "communication" in filename.lower():
            return JSONResponse({
                "filename": filename,
                "config_dir": config_dir,
                "type": "communication",
                "parsed": parse_communication_config(content),
                "raw": content
            })
        else:
            return JSONResponse({
                "filename": filename,
                "config_dir": config_dir,
                "type": "slave",
                "parsed": parse_slave_config(content),
                "raw": content
            })

    return JSONResponse({"filename": filename, "config_dir": config_dir, "content": content})


@app.post("/api/config/{config_dir:path}/{filename}")
async def update_config(config_dir: str, filename: str, update: ConfigUpdate):
    """Update configuration file with validation and backup."""
    config_dir = "/" + config_dir if not config_dir.startswith("/") else config_dir
    config_path = Path(config_dir)
    file_path = config_path / filename

    # Security check
    if not file_path.resolve().is_relative_to(config_path.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")

    # Validate YAML
    if not validate_yaml(update.content):
        raise HTTPException(status_code=400, detail="Invalid YAML syntax")

    # Create backup
    if file_path.exists():
        backup_path = file_path.with_suffix(f".yaml.bak.{int(time.time())}")
        backup_path.write_text(file_path.read_text())

    # Write new content
    file_path.write_text(update.content)

    return JSONResponse({
        "success": True,
        "message": f"Configuration {filename} updated successfully",
        "backup_created": True
    })


@app.post("/api/service/{service_name}/{action}")
async def service_control(service_name: str, action: str):
    """Control supervisor service (restart/stop/start)."""
    if action not in ['restart', 'stop', 'start']:
        raise HTTPException(status_code=400, detail="Invalid action")

    process_name = f'{service_name}:{service_name}_00'

    # Try multiple approaches to control the service
    commands_to_try = [
        # Try with sudo first (most RTUs have sudo configured for dcu user)
        ['sudo', 'supervisorctl', action, process_name],
        # Try without sudo
        ['supervisorctl', action, process_name],
        # Try with the service name only (some configs)
        ['sudo', 'supervisorctl', action, service_name],
    ]

    result = None
    output = ""

    for cmd in commands_to_try:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=30
            )
            output = result.stdout.strip() or result.stderr.strip()

            # Check if successful
            if result.returncode == 0 or any(s in output.lower() for s in ['started', 'stopped', 'restarted']):
                return JSONResponse({
                    "success": True,
                    "output": output,
                    "error": None
                })

            # If permission denied, try next command
            if 'permission denied' in output.lower():
                continue

        except subprocess.TimeoutExpired:
            output = "Command timed out"
            continue
        except FileNotFoundError:
            continue
        except Exception as e:
            output = str(e)
            continue

    # All commands failed
    return JSONResponse({
        "success": False,
        "output": output,
        "error": output or "Failed to control service. You may need to configure sudo permissions for supervisorctl."
    })


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Logs viewer page."""
    supervisor_config = parse_supervisor_config()
    return templates.TemplateResponse("logs.html", {
        "request": request,
        "services": supervisor_config['services']
    })


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket, service: Optional[str] = None):
    """WebSocket endpoint for real-time log streaming."""
    # Check connection limit
    if len(active_connections) >= MAX_WEBSOCKET_CONNECTIONS:
        await websocket.close(code=1008, reason="Maximum connections reached")
        return

    try:
        await websocket.accept()
    except Exception as e:
        logger.error(f"WebSocket accept failed: {e}")
        return

    active_connections.append(websocket)
    last_log_hash = ""

    try:
        while True:
            try:
                logs = get_recent_logs(service_name=service, lines=50)
                # Use hash to detect changes more reliably
                current_hash = hash(tuple(logs)) if logs else ""

                # Only send if there are new logs
                if current_hash != last_log_hash:
                    await websocket.send_json({
                        "type": "logs",
                        "logs": logs,
                        "timestamp": datetime.now().isoformat()
                    })
                    last_log_hash = current_hash

            except WebSocketDisconnect:
                # Client disconnected, break out of loop
                break
            except Exception as e:
                # Log error but don't try to send to potentially closed connection
                logger.debug(f"WebSocket log fetch error: {e}")
                break

            await asyncio.sleep(LOG_STREAM_INTERVAL)

    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected")
    except Exception as e:
        # Only log unexpected errors at debug level to reduce noise
        logger.debug(f"WebSocket closed: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)


@app.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request):
    """Alerts configuration page."""
    return templates.TemplateResponse("alerts.html", {"request": request})


@app.get("/devices", response_class=HTMLResponse)
async def devices_page(request: Request):
    """Device Health Dashboard - shows real-time status of all configured meters."""
    return templates.TemplateResponse("devices.html", {"request": request})


@app.get("/api/devices")
async def get_devices():
    """Get list of configured devices from all config files."""
    devices = []

    for config_file in get_all_config_files():
        if config_file['type'] == 'slave':
            try:
                content = read_config_file(config_file['config_dir'], config_file['name'])
                parsed = parse_slave_config(content)

                for conn in parsed.get('connections', []):
                    for client in conn.get('clients', []):
                        # Calculate effective intervals
                        polling_interval = client.get('polling_interval', 60)
                        http_interval = client.get('http_interval') or polling_interval
                        mqtt_interval = client.get('mqtt_interval') or polling_interval

                        devices.append({
                            "config_file": config_file['name'],
                            "config_dir": config_file['config_dir'],
                            "service": config_file.get('service', 'unknown'),
                            "connection_id": conn.get('id', ''),
                            "connection_label": conn.get('label', ''),
                            "device_id": client.get('id', 'unknown'),
                            "unit_id": client.get('unit_id'),
                            "device_type": client.get('type', 'unknown'),
                            "polling_interval": polling_interval,
                            "http_interval": http_interval,
                            "mqtt_interval": mqtt_interval,
                            "http_enabled": client.get('http_enabled', True),
                            "mqtt_enabled": client.get('mqtt_enabled', True),
                            "register_count": len(client.get('registers', []))
                        })
            except Exception as e:
                logger.error(f"Error parsing {config_file['name']}: {e}")

    return JSONResponse({"devices": devices, "count": len(devices)})


@app.get("/api/devices/status")
async def get_devices_status():
    """Get real-time status of all configured devices with latest readings.

    This endpoint combines device configuration with cache data to show:
    - Device status (online/stale/offline)
    - Latest readings from cache
    - Time since last reading

    Only shows devices from the current service (based on CONFIG_DIR environment variable).
    """
    devices = []
    summary = {"total": 0, "online": 0, "stale": 0, "offline": 0}

    # Use the shared register cache (injected from main process)
    cache = _shared_register_cache
    if cache:
        try:
            cache_info = cache.get_cache_info()
            client_cache = cache_info.get('clients', {})
            logger.debug(f"Web portal: using shared cache with {len(client_cache)} clients")
        except Exception as e:
            logger.warning(f"Error accessing shared cache: {e}")
            client_cache = {}
    else:
        # Fallback: try to import (works when running standalone)
        try:
            from src.services.register_cache import get_cache
            cache = get_cache()
            cache_info = cache.get_cache_info()
            client_cache = cache_info.get('clients', {})
        except (ImportError, Exception) as e:
            logger.warning(f"No register cache available: {e}")
            cache = None
            client_cache = {}

    # Only show devices from the current service if CONFIG_DIR is set
    # This avoids showing devices from other services that aren't running
    current_config_dir = get_current_config_dir()

    for config_file in get_all_config_files():
        # Skip configs from other services when CONFIG_DIR is set
        if current_config_dir and config_file['config_dir'] != current_config_dir:
            continue

        if config_file['type'] == 'slave':
            try:
                content = read_config_file(config_file['config_dir'], config_file['name'])
                parsed = parse_slave_config(content)

                for conn in parsed.get('connections', []):
                    conn_type = conn.get('connection_type', 'tcp')
                    conn_info = {"type": conn_type}

                    if conn_type == 'tcp':
                        conn_info['host'] = conn.get('host', '')
                        conn_info['port'] = conn.get('port', 502)
                    elif conn_type == 'serial':
                        conn_info['port'] = conn.get('serial_port', '')
                        conn_info['baud_rate'] = conn.get('baud_rate', 9600)

                    for client in conn.get('clients', []):
                        device_id = client.get('id', 'unknown')
                        polling_interval = client.get('polling_interval', 60)

                        # Calculate effective modbus read interval (min of enabled protocols)
                        http_enabled = client.get('http_enabled', True)
                        mqtt_enabled = client.get('mqtt_enabled', True)
                        http_interval = client.get('http_interval') or polling_interval
                        mqtt_interval = client.get('mqtt_interval') or polling_interval

                        # modbus_read_interval = min of enabled protocols
                        if http_enabled and mqtt_enabled:
                            modbus_read_interval = min(http_interval, mqtt_interval)
                        elif http_enabled:
                            modbus_read_interval = http_interval
                        elif mqtt_enabled:
                            modbus_read_interval = mqtt_interval
                        else:
                            modbus_read_interval = polling_interval

                        # Get cache info for this device
                        cache_entry = client_cache.get(device_id, {})
                        age = cache_entry.get('age')
                        is_expired = cache_entry.get('expired', True)

                        # Determine status based on age
                        # With staggered polling (25 devices × 0.5s = 12.5s spread) + read interval,
                        # a device can legitimately have an age of up to (stagger_spread + read_interval)
                        # before its next read. Use generous multipliers to avoid false "stale" status.
                        cache_ttl = 60  # Should match communication.yaml cache_ttl
                        stagger_spread = 12.5  # 25 devices × 0.5s stagger
                        status_base_interval = max(cache_ttl, modbus_read_interval) + stagger_spread

                        if age is None:
                            status = 'offline'
                            seconds_since_last = None
                            latest_values = {}
                        elif age > status_base_interval * 2:
                            status = 'offline'
                            seconds_since_last = age
                            latest_values = {}
                        elif age > status_base_interval * 1.2:
                            status = 'stale'
                            seconds_since_last = age
                            # Try to get cached values
                            if cache:
                                latest_values = cache.get_client_values(device_id) or {}
                            else:
                                latest_values = {}
                        else:
                            status = 'online'
                            seconds_since_last = age
                            # Get cached values
                            if cache:
                                latest_values = cache.get_client_values(device_id) or {}
                            else:
                                latest_values = {}

                        # Build device info
                        device_info = {
                            "id": device_id,
                            "label": client.get('id', '').replace('-', ' ').replace('_', ' ').title(),
                            "type": client.get('type', 'electrical'),
                            "status": status,
                            "last_reading": datetime.fromtimestamp(time.time() - age).isoformat() if age else None,
                            "seconds_since_last": round(seconds_since_last, 1) if seconds_since_last else None,
                            "polling_interval": polling_interval,
                            "http_interval": http_interval,
                            "mqtt_interval": mqtt_interval,
                            "modbus_read_interval": modbus_read_interval,
                            "http_enabled": http_enabled,
                            "mqtt_enabled": mqtt_enabled,
                            "unit_id": client.get('unit_id'),
                            "connection": conn_info,
                            "connection_label": conn.get('label', ''),
                            "latest_values": latest_values,
                            "config_file": config_file['name']
                        }

                        devices.append(device_info)
                        summary["total"] += 1
                        summary[status] += 1

            except Exception as e:
                logger.error(f"Error parsing {config_file['name']}: {e}")

    # Add cache debug info for troubleshooting
    cache_debug = {
        "cache_injected": _shared_register_cache is not None,
        "cache_id": id(_shared_register_cache) if _shared_register_cache else None,
        "client_cache_count": len(client_cache)
    }

    # Sanitize data for JSON (handles inf/nan values)
    return JSONResponse(sanitize_for_json({
        "devices": devices,
        "summary": summary,
        "timestamp": datetime.now().isoformat(),
        "cache_debug": cache_debug
    }))


# ============== Config Wizard ==============

def load_meter_registry() -> Dict[str, Any]:
    """Load meter registry YAML for the wizard."""
    # Try multiple paths for meter registry - check src/config first (where it actually lives)
    paths_to_try = [
        Path(__file__).parent.parent / "config" / "meter_registry.yaml",  # src/config/
        Path(__file__).parent.parent.parent / "config" / "meter_registry.yaml",  # project root config/
        Path("/home/dcu/dataskipper-boat/src/config/meter_registry.yaml"),
        Path("/home/dcu/dataskipper-boat/config/meter_registry.yaml"),
        Path.home() / "dataskipper-boat" / "src" / "config" / "meter_registry.yaml",
        Path.home() / "dataskipper-boat" / "config" / "meter_registry.yaml",
    ]

    for path in paths_to_try:
        if path.exists():
            try:
                logger.info(f"Loading meter registry from: {path}")
                with open(path) as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Error loading meter registry from {path}: {e}")

    logger.warning("Meter registry not found in any location")
    return {}


@app.get("/config/wizard", response_class=HTMLResponse)
async def config_wizard_page(request: Request):
    """Configuration Wizard - guided meter setup."""
    supervisor_config = parse_supervisor_config()
    return templates.TemplateResponse("config_wizard.html", {
        "request": request,
        "services": supervisor_config['services'],
        "config_dirs": get_all_config_dirs()
    })


@app.get("/api/wizard/meters")
async def get_available_meters():
    """Get available meter models from registry."""
    registry = load_meter_registry()

    meters = []

    # Parse electrical distribution meters
    for meter_id, meter_data in registry.get('electrical_distribution', {}).items():
        meters.append({
            "id": meter_id,
            "category": "electrical_distribution",
            "manufacturer": meter_data.get('manufacturer', ''),
            "model": meter_data.get('model', ''),
            "description": meter_data.get('description', ''),
            "defaults": meter_data.get('defaults', {})
        })

    # Parse electrical substation meters
    for meter_id, meter_data in registry.get('electrical_substation', {}).items():
        if meter_data.get('extends'):
            continue  # Skip meters that extend others (they inherit)
        meters.append({
            "id": meter_id,
            "category": "electrical_substation",
            "manufacturer": meter_data.get('manufacturer', ''),
            "model": meter_data.get('model', ''),
            "description": meter_data.get('description', ''),
            "defaults": meter_data.get('defaults', {})
        })

    # Parse water meters
    for meter_id, meter_data in registry.get('water', {}).items():
        meters.append({
            "id": meter_id,
            "category": "water",
            "manufacturer": meter_data.get('manufacturer', ''),
            "model": meter_data.get('model', ''),
            "description": meter_data.get('description', ''),
            "defaults": meter_data.get('defaults', {})
        })

    return JSONResponse({"meters": meters})


@app.get("/api/wizard/profiles")
async def get_available_profiles(meter_id: Optional[str] = None):
    """Get available client profiles from registry.

    If meter_id is provided, returns profiles with compatibility info.
    Compatibility is based on whether the meter has all registers required by the profile.

    Note: Meters like Schneider and Secure can be used for BOTH distribution and substation,
    so we check register availability rather than rigid category matching.
    """
    registry = load_meter_registry()

    # Get meter info if specified
    meter_registers = set()
    meter_type = None  # 'electrical' or 'water'
    if meter_id:
        # Find meter in registry - check all categories
        for category in ['electrical_distribution', 'electrical_substation', 'water']:
            if meter_id in registry.get(category, {}):
                meter_data = registry[category][meter_id]
                meter_registers = set(meter_data.get('registers', {}).keys())
                meter_type = 'water' if category == 'water' else 'electrical'
                break

    profiles = []
    for profile_id, profile_data in registry.get('client_profiles', {}).items():
        profile_registers = set(profile_data.get('registers', []))
        target_table = profile_data.get('target_table', '')

        # Determine compatibility based on register availability
        is_compatible = True
        compatibility_reason = ""

        if meter_id:
            # First check: is this a water profile for a water meter or electrical for electrical?
            profile_is_water = target_table == 'water'
            meter_is_water = meter_type == 'water'

            if profile_is_water != meter_is_water:
                # Water/electrical mismatch
                is_compatible = False
                compatibility_reason = "Water/electrical mismatch"
            elif meter_id in profile_id:
                # Profile is specifically designed for this meter
                is_compatible = True
                compatibility_reason = "Designed for this meter"
            elif any(m in profile_id for m in ['lt_wl4400', 'secure_elite', 'schneider', 'krohne']):
                # Profile is specifically for a different meter model
                # Extract which meter the profile is for
                other_meter = None
                for m in ['lt_wl4400', 'secure_elite', 'schneider', 'krohne']:
                    if m in profile_id and m != meter_id:
                        other_meter = m
                        break
                if other_meter:
                    is_compatible = False
                    compatibility_reason = f"Designed for {other_meter.replace('_', ' ').title()}"
                else:
                    # Meter name is in profile but matches our meter
                    is_compatible = True
                    compatibility_reason = "Designed for this meter"
            else:
                # Generic profile - check if meter has all required registers
                # This allows Schneider/Secure to work with both distribution AND substation profiles
                missing = profile_registers - meter_registers
                if missing:
                    is_compatible = False
                    missing_list = list(missing)[:3]
                    compatibility_reason = f"Missing: {', '.join(missing_list)}"
                    if len(missing) > 3:
                        compatibility_reason += f" (+{len(missing)-3} more)"
                else:
                    is_compatible = True
                    compatibility_reason = "All registers available"

        profiles.append({
            "id": profile_id,
            "description": profile_data.get('description', ''),
            "target_table": target_table,
            "register_count": len(profile_registers),
            "compatible": is_compatible,
            "compatibility_reason": compatibility_reason
        })

    # Sort: compatible first, then by ID
    profiles.sort(key=lambda x: (not x['compatible'], x['id']))

    return JSONResponse({"profiles": profiles, "meter_id": meter_id})


@app.get("/api/wizard/connections")
async def get_existing_connections():
    """Get existing connections from all config files for reuse."""
    connections = []

    for config_file in get_all_config_files():
        if config_file['type'] == 'slave':
            try:
                content = read_config_file(config_file['config_dir'], config_file['name'])
                parsed = parse_slave_config(content)

                for conn in parsed.get('connections', []):
                    conn['config_file'] = config_file['name']
                    conn['config_dir'] = config_file['config_dir']
                    conn['client_count'] = len(conn.get('clients', []))
                    connections.append(conn)
            except Exception as e:
                logger.error(f"Error parsing {config_file['name']}: {e}")

    return JSONResponse({"connections": connections})


class WizardDeviceConfig(BaseModel):
    """Model for wizard-generated device configuration."""
    # Connection settings (can be existing or new)
    use_existing_connection: bool = False
    existing_connection_id: Optional[str] = None
    connection_type: str = "serial"  # serial or tcp
    # Serial settings
    serial_port: Optional[str] = "/dev/ttyS0"
    baud_rate: int = 9600
    parity: str = "N"
    # TCP settings
    host: Optional[str] = None
    port: Optional[int] = 502
    # Device settings
    device_id: str
    device_label: str
    unit_id: int
    meter_model: str
    profile: str
    # Protocol settings
    mqtt_enabled: bool = True
    mqtt_interval: int = 10
    mqtt_topic: Optional[str] = None
    http_enabled: bool = True
    http_interval: int = 60
    # Config file
    config_file: str = "slave_config.yaml"
    config_dir: str


@app.post("/api/wizard/generate")
async def generate_device_config(config: WizardDeviceConfig):
    """Generate YAML configuration for a new device."""

    # Build client configuration
    client_config = {
        "id": config.device_id,
        "type": "electrical" if "water" not in config.profile else "water",
        "unit_id": config.unit_id,
        "meter_model": config.meter_model,
        "profile": config.profile,
        "target_table": config.profile.split('_')[0] if '_' in config.profile else "distribution",
        "polling_interval": max(config.http_interval, config.mqtt_interval),
        "mqtt_enabled": config.mqtt_enabled,
        "mqtt_interval": config.mqtt_interval,
        "http_enabled": config.http_enabled,
    }

    if config.mqtt_topic:
        client_config["mqtt_topic"] = config.mqtt_topic

    # Generate YAML snippet
    yaml_snippet = yaml.dump({"client": client_config}, default_flow_style=False, sort_keys=False)

    return JSONResponse({
        "success": True,
        "client_config": client_config,
        "yaml_snippet": yaml_snippet,
        "instructions": f"Add this client to the '{config.config_file}' file under the appropriate connection."
    })


@app.post("/api/wizard/add-device")
async def add_device_to_config(config: WizardDeviceConfig):
    """Add a new device to an existing configuration file."""
    config_path = Path(config.config_dir) / config.config_file

    if not config_path.exists():
        raise HTTPException(status_code=404, detail=f"Config file not found: {config.config_file}")

    try:
        # Read existing config
        with open(config_path) as f:
            existing_config = yaml.safe_load(f)

        if not existing_config or 'connections' not in existing_config:
            raise HTTPException(status_code=400, detail="Invalid config file format")

        # Build client configuration
        new_client = {
            "id": config.device_id,
            "type": "electrical" if "water" not in config.profile else "water",
            "unit_id": config.unit_id,
            "meter_model": config.meter_model,
            "profile": config.profile,
            "target_table": config.profile.split('_')[0] if '_' in config.profile else "distribution",
            "polling_interval": max(config.http_interval, config.mqtt_interval),
            "mqtt_enabled": config.mqtt_enabled,
            "mqtt_interval": config.mqtt_interval,
            "http_enabled": config.http_enabled,
        }

        if config.mqtt_topic:
            new_client["mqtt_topic"] = config.mqtt_topic

        # Find target connection
        target_conn = None
        if config.use_existing_connection and config.existing_connection_id:
            for conn in existing_config['connections']:
                if conn.get('id') == config.existing_connection_id:
                    target_conn = conn
                    break

            if not target_conn:
                raise HTTPException(status_code=404, detail=f"Connection not found: {config.existing_connection_id}")

            # Check for duplicate device ID
            for client in target_conn.get('clients', []):
                if client.get('id') == config.device_id:
                    raise HTTPException(status_code=400, detail=f"Device ID already exists: {config.device_id}")

            # Check for duplicate unit ID in same connection
            for client in target_conn.get('clients', []):
                if client.get('unit_id') == config.unit_id:
                    raise HTTPException(status_code=400,
                        detail=f"Unit ID {config.unit_id} already in use by {client.get('id')}")

            # Add client to connection
            if 'clients' not in target_conn:
                target_conn['clients'] = []
            target_conn['clients'].append(new_client)

        else:
            # Create new connection
            new_conn = {
                "id": f"conn_{config.device_id}",
                "label": f"Connection for {config.device_label}",
                "connection_type": config.connection_type,
                "timeout": 3,
                "retries": 3,
                "reconnect_delay": 1,
                "clients": [new_client]
            }

            if config.connection_type == "serial":
                new_conn["port"] = config.serial_port
                new_conn["baud_rate"] = config.baud_rate
                new_conn["parity"] = config.parity
                new_conn["stop_bits"] = 1
                new_conn["bytesize"] = 8
                new_conn["framer"] = "rtu"
            else:
                new_conn["host"] = config.host
                new_conn["port"] = config.port
                new_conn["framer"] = "socket"

            existing_config['connections'].append(new_conn)

        # Create backup
        backup_path = config_path.with_suffix(f".yaml.bak.{int(time.time())}")
        backup_path.write_text(config_path.read_text())

        # Write updated config
        with open(config_path, 'w') as f:
            yaml.dump(existing_config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        return JSONResponse({
            "success": True,
            "message": f"Device '{config.device_id}' added successfully",
            "backup_created": str(backup_path),
            "restart_required": True
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding device: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============== Diagnostics ==============

# Import diagnostic service
try:
    from src.services.diagnostic_service import (
        get_diagnostic_service, DiagnosticResult, DiagnosticReport, CheckStatus,
        TROUBLESHOOTING_TREES
    )
    DIAGNOSTICS_AVAILABLE = True
except ImportError:
    DIAGNOSTICS_AVAILABLE = False
    logger.warning("Diagnostic service not available")


@app.get("/diagnostics", response_class=HTMLResponse)
async def diagnostics_page(request: Request):
    """System Diagnostics page - automated checks and troubleshooting wizard."""
    return templates.TemplateResponse("diagnostics.html", {"request": request})


@app.get("/api/diagnostics/run")
async def run_diagnostics(category: Optional[str] = None):
    """Run diagnostic checks.

    Args:
        category: Optional category to run (connectivity, system, devices).
                  If not specified, runs all checks.
    """
    if not DIAGNOSTICS_AVAILABLE:
        return JSONResponse({
            "error": "Diagnostic service not available",
            "results": [],
            "summary": {}
        }, status_code=503)

    try:
        diagnostic_service = get_diagnostic_service(CURRENT_CONFIG_DIR)

        if category:
            # Run specific category
            results = await diagnostic_service.run_category_checks(
                category,
                cache=_shared_register_cache
            )
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

            return JSONResponse(sanitize_for_json({
                "category": category,
                "results": [_result_to_dict(r) for r in results],
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            }))
        else:
            # Run all checks
            report = await diagnostic_service.run_all_checks(cache=_shared_register_cache)
            return JSONResponse(sanitize_for_json({
                "results": [_result_to_dict(r) for r in report.results],
                "summary": report.summary,
                "timestamp": report.timestamp,
                "duration_ms": report.duration_ms
            }))

    except Exception as e:
        logger.error(f"Error running diagnostics: {e}", exc_info=True)
        return JSONResponse({
            "error": str(e),
            "results": [],
            "summary": {}
        }, status_code=500)


@app.post("/api/diagnostics/check/{check_id}")
async def run_single_check(check_id: str):
    """Run a single diagnostic check by ID."""
    if not DIAGNOSTICS_AVAILABLE:
        return JSONResponse({"error": "Diagnostic service not available"}, status_code=503)

    try:
        diagnostic_service = get_diagnostic_service(CURRENT_CONFIG_DIR)

        # Map check IDs to methods
        check_methods = {
            "internet": diagnostic_service.check_internet,
            "dns": diagnostic_service.check_dns,
            "mqtt": diagnostic_service.check_mqtt,
            "api": diagnostic_service.check_api,
            "cpu": diagnostic_service.check_cpu,
            "memory": diagnostic_service.check_memory,
            "disk": diagnostic_service.check_disk,
            "service": diagnostic_service.check_service,
        }

        if check_id in check_methods:
            result = await check_methods[check_id]()
            return JSONResponse(sanitize_for_json(_result_to_dict(result)))
        elif check_id == "modbus_gateways":
            results = await diagnostic_service.check_modbus_gateways()
            return JSONResponse(sanitize_for_json({
                "results": [_result_to_dict(r) for r in results]
            }))
        elif check_id == "devices":
            results = await diagnostic_service.check_devices(cache=_shared_register_cache)
            return JSONResponse(sanitize_for_json({
                "results": [_result_to_dict(r) for r in results]
            }))
        else:
            return JSONResponse({"error": f"Unknown check: {check_id}"}, status_code=404)

    except Exception as e:
        logger.error(f"Error running check {check_id}: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/diagnostics/troubleshoot/{tree_id}")
async def get_troubleshooting_tree(tree_id: str):
    """Get a troubleshooting decision tree by ID."""
    if not DIAGNOSTICS_AVAILABLE:
        return JSONResponse({"error": "Diagnostic service not available"}, status_code=503)

    diagnostic_service = get_diagnostic_service(CURRENT_CONFIG_DIR)
    tree = diagnostic_service.get_troubleshooting_tree(tree_id)

    if tree:
        return JSONResponse({"tree_id": tree_id, "tree": tree})
    else:
        return JSONResponse({"error": f"Troubleshooting tree not found: {tree_id}"}, status_code=404)


@app.get("/api/diagnostics/troubleshoot")
async def list_troubleshooting_trees():
    """List all available troubleshooting trees."""
    if not DIAGNOSTICS_AVAILABLE:
        return JSONResponse({"error": "Diagnostic service not available"}, status_code=503)

    diagnostic_service = get_diagnostic_service(CURRENT_CONFIG_DIR)
    trees = diagnostic_service.get_all_troubleshooting_trees()

    # Return summary of each tree
    summaries = []
    for tree_id, tree in trees.items():
        summaries.append({
            "id": tree_id,
            "title": tree.get("title", ""),
            "description": tree.get("description", ""),
            "steps_count": len(tree.get("steps", []))
        })

    return JSONResponse({"trees": summaries})


@app.post("/api/diagnostics/test-modbus")
async def test_modbus_connection(host: str, port: int = 502, unit_id: int = 1):
    """Test Modbus connection by attempting to read from a device.

    This is useful for troubleshooting to verify direct communication.
    """
    start = time.time()
    try:
        # Simple TCP connection test first
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=5
        )
        writer.close()
        await writer.wait_closed()

        return JSONResponse({
            "success": True,
            "message": f"TCP connection successful to {host}:{port}",
            "duration_ms": (time.time() - start) * 1000,
            "note": "TCP port is open. For full Modbus test, use a Modbus scanner tool."
        })
    except asyncio.TimeoutError:
        return JSONResponse({
            "success": False,
            "message": f"Connection timeout to {host}:{port}",
            "duration_ms": (time.time() - start) * 1000,
            "actions": [
                "Check gateway power and network connection",
                f"Try: ping {host}",
                "Verify port number is correct"
            ]
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "duration_ms": (time.time() - start) * 1000,
            "actions": [
                "Check network connectivity",
                "Verify host and port are correct"
            ]
        })


def _result_to_dict(result: 'DiagnosticResult') -> Dict[str, Any]:
    """Convert DiagnosticResult to dictionary for JSON response."""
    return {
        "check_id": result.check_id,
        "name": result.name,
        "category": result.category,
        "status": result.status.value,
        "message": result.message,
        "duration_ms": result.duration_ms,
        "details": result.details,
        "actions": result.actions,
        "troubleshooting_tree": result.troubleshooting_tree,
        "timestamp": result.timestamp
    }


# ============== Test Mode & Troubleshooting Tools ==============

# Import test mode service
try:
    from src.services.test_mode_service import get_test_mode_service, TestModeService
    TEST_MODE_AVAILABLE = True
except ImportError:
    TEST_MODE_AVAILABLE = False
    logger.warning("Test mode service not available")

# Global reference for test mode service (set when modbus references available)
_test_mode_service: Optional['TestModeService'] = None


def init_test_mode_service(clients: Dict, connections: Dict, cache=None):
    """Initialize test mode service with Modbus references.

    Called from main.py after Modbus clients are set up.
    """
    global _test_mode_service
    if TEST_MODE_AVAILABLE:
        _test_mode_service = get_test_mode_service(CURRENT_CONFIG_DIR)
        _test_mode_service.set_modbus_references(clients, connections, cache)
        logger.info("Test mode service initialized with Modbus references")


@app.get("/testing", response_class=HTMLResponse)
async def testing_page(request: Request):
    """Testing & Troubleshooting Tools page."""
    return templates.TemplateResponse("testing.html", {"request": request})


@app.get("/api/test-mode/status")
async def get_test_mode_status():
    """Get current test mode status."""
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available",
            "status": "unavailable"
        }, status_code=503)

    return JSONResponse(_test_mode_service.get_status())


@app.post("/api/test-mode/enter")
async def enter_test_mode(
    timeout_minutes: int = 10,
    disable_http: bool = True,
    disable_mqtt: bool = True,
    disable_alerts: bool = True
):
    """Enter test mode.

    Args:
        timeout_minutes: Auto-exit timeout (1-30 minutes, default 10)
        disable_http: Disable HTTP API publishing (default true)
        disable_mqtt: Disable MQTT publishing (default true)
        disable_alerts: Disable alert processing (default true)
    """
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    success, message = await _test_mode_service.enter_test_mode(
        timeout_minutes=timeout_minutes,
        disable_http=disable_http,
        disable_mqtt=disable_mqtt,
        disable_alerts=disable_alerts
    )

    if success:
        return JSONResponse({
            "success": True,
            "message": message,
            "status": _test_mode_service.get_status()
        })
    else:
        return JSONResponse({
            "success": False,
            "error": message
        }, status_code=400)


@app.post("/api/test-mode/exit")
async def exit_test_mode():
    """Exit test mode and return to normal operation."""
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    success, message = await _test_mode_service.exit_test_mode(reason="manual")

    return JSONResponse({
        "success": success,
        "message": message,
        "status": _test_mode_service.get_status()
    })


@app.post("/api/test-mode/extend")
async def extend_test_mode():
    """Extend test mode by 5 minutes."""
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    if not _test_mode_service.is_test_mode_active():
        return JSONResponse({
            "success": False,
            "message": "Test mode is not active"
        })

    # Extend by 5 minutes
    import time
    _test_mode_service.state.expires_at = time.time() + 300 + _test_mode_service.state.expires_at - time.time()
    # Actually just add 5 minutes to current expiration
    _test_mode_service.state.expires_at += 300

    # Reset expiring status if we extended
    from src.services.test_mode_service import TestModeStatus
    if _test_mode_service.state.status == TestModeStatus.EXPIRING:
        _test_mode_service.state.status = TestModeStatus.ACTIVE

    return JSONResponse({
        "success": True,
        "message": "Test mode extended by 5 minutes",
        "status": _test_mode_service.get_status()
    })


@app.get("/api/test-mode/connections")
async def get_available_connections():
    """Get list of available Modbus connections for testing."""
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    connections = _test_mode_service.get_available_connections()
    return JSONResponse({"connections": connections})


@app.post("/api/test-mode/read-registers")
async def read_registers(
    connection_id: str,
    unit_id: int,
    start_address: int,
    count: int = 1,
    function_code: int = 3,
    data_type: str = "uint16",
    byte_order: str = "big",
    scale: float = 1.0,
    offset: float = 0.0
):
    """Read specific registers from a device with data type conversion.

    Args:
        connection_id: Connection ID to use
        unit_id: Modbus unit/slave ID
        start_address: Starting register address
        count: Number of registers to read (1-125)
        function_code: 3 for holding registers, 4 for input registers
        data_type: Data type for interpretation (uint16, int16, uint32, int32, float32, uint64, int64, float64)
        byte_order: Byte ordering (big, little, big_swap, little_swap)
        scale: Scale factor to apply to converted values
        offset: Offset to add after scaling
    """
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    # Validate count
    count = min(max(1, count), 125)

    result = await _test_mode_service.read_registers(
        connection_id=connection_id,
        unit_id=unit_id,
        start_address=start_address,
        count=count,
        function_code=function_code,
        data_type=data_type,
        byte_order=byte_order,
        scale=scale,
        offset=offset
    )

    return JSONResponse(result.to_dict())


@app.post("/api/test-mode/probe-device")
async def probe_device(
    connection_id: str,
    unit_id: int,
    test_address: int = 0
):
    """Probe a device to check if it responds.

    Args:
        connection_id: Connection ID to use
        unit_id: Modbus unit/slave ID to probe
        test_address: Register address to test (default 0)
    """
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    result = await _test_mode_service.probe_device(
        connection_id=connection_id,
        unit_id=unit_id,
        test_address=test_address
    )

    return JSONResponse(result)


@app.get("/api/test-mode/config")
async def get_test_config():
    """Get the current test configuration."""
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    config = _test_mode_service.get_test_config()
    if config:
        return JSONResponse({"config": config})
    else:
        return JSONResponse({
            "error": "No test configuration found",
            "hint": "Test config is created when entering test mode"
        }, status_code=404)


@app.post("/api/test-mode/config")
async def save_test_config(request: Request):
    """Save a test configuration.

    Body can be either:
    - YAML config as JSON dict (legacy)
    - Object with 'filename' and 'content' keys for raw content
    """
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    # Check if test mode is active
    if not _test_mode_service.is_test_mode_active():
        return JSONResponse({
            "success": False,
            "error": "Test mode is not active. Enter test mode first to edit configurations."
        }, status_code=403)

    try:
        data = await request.json()

        # Check if this is raw content or a config dict
        if 'content' in data and 'filename' in data:
            # Raw content mode - support optional directory parameter
            directory = data.get('directory', '')
            # Clean up directory path (remove leading/trailing slashes)
            if directory:
                directory = directory.strip('/')
            success, message = _test_mode_service.save_test_config_content(
                filename=data['filename'],
                content=data['content'],
                subdirectory=directory if directory else None
            )
        else:
            # Legacy dict mode
            success, message = _test_mode_service.save_test_config(data)

        if success:
            return JSONResponse({
                "success": True,
                "message": message
            })
        else:
            return JSONResponse({
                "success": False,
                "error": message
            }, status_code=400)

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=400)


@app.post("/api/test-mode/validate-config")
async def validate_config(config_path: Optional[str] = None):
    """Validate a configuration file.

    Args:
        config_path: Path to config file (default: test_config/slave_config.yaml)
    """
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    result = _test_mode_service.validate_config(config_path)
    return JSONResponse(result.to_dict())


@app.get("/api/test-mode/configs")
async def list_test_configs():
    """List all test configuration files."""
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    files = _test_mode_service.list_test_configs()
    return JSONResponse({
        "test_config_dir": _test_mode_service.get_test_config_dir(),
        "files": files
    })


@app.get("/api/test-mode/config/{filepath:path}")
async def get_test_config_file(filepath: str):
    """Get content of a specific test config file."""
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    # Split filepath into directory and filename
    parts = filepath.rsplit('/', 1)
    if len(parts) == 2:
        subdirectory, filename = parts
    else:
        subdirectory, filename = None, filepath

    success, content, full_path = _test_mode_service.get_test_config_content(filename, subdirectory)

    if success:
        return JSONResponse({
            "success": True,
            "filename": filename,
            "subdirectory": subdirectory,
            "full_path": full_path,
            "content": content
        })
    else:
        return JSONResponse({
            "success": False,
            "error": content
        }, status_code=404)


@app.post("/api/test-mode/apply-to-production")
async def apply_test_config_to_production(request: Request):
    """Apply a test config file to production.

    Body: { "filename": "slave_config.yaml", "subdirectory": "slave_configs" }
    """
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    try:
        data = await request.json()
        filename = data.get('filename')
        subdirectory = data.get('subdirectory')

        if not filename:
            return JSONResponse({
                "success": False,
                "error": "Filename is required"
            }, status_code=400)

        success, message = _test_mode_service.apply_test_config_to_production(filename, subdirectory)

        if success:
            return JSONResponse({
                "success": True,
                "message": message
            })
        else:
            return JSONResponse({
                "success": False,
                "error": message
            }, status_code=400)

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=400)


@app.post("/api/test-mode/verify-config")
async def verify_config_connections(request: Request):
    """Verify a config by testing all connections and reading from all devices.

    Body: { "content": "YAML config content" }

    Returns verification results for each connection and device.
    """
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    # Check if test mode is active
    if not _test_mode_service.is_test_mode_active():
        return JSONResponse({
            "success": False,
            "error": "Test mode is not active. Enter test mode first to verify configurations."
        }, status_code=403)

    try:
        data = await request.json()
        content = data.get('content')

        if not content:
            return JSONResponse({
                "success": False,
                "error": "Config content is required"
            }, status_code=400)

        results = await _test_mode_service.verify_config(content)
        return JSONResponse(results)

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=400)


@app.post("/api/test-mode/publish-config")
async def publish_config_to_backend(request: Request):
    """Publish a verified config to the backend server.

    This endpoint:
    1. Saves config to test directory
    2. POSTs the YAML to the backend API for version control

    Body: {
        "content": "YAML config content",
        "filename": "slave_config.yaml",
        "directory": "/home/dcu/config",
        "config_type": "slave",
        "backend_url": "https://your-backend.com/iot-backend/api/v1/config/submit/"
    }

    Backend API:
    - POST to backend_url
    - Headers: Content-Type: text/plain, X-Device-ID, X-Config-Type, X-Submitted-By
    - Body: raw YAML content

    Returns:
    - Success: {status, message, commit_sha, device_id, config_type}
    - Error: {valid: false, errors: [], warnings: []}
    """
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    # Check if test mode is active
    if not _test_mode_service.is_test_mode_active():
        return JSONResponse({
            "success": False,
            "error": "Test mode is not active. Enter test mode first to publish configurations."
        }, status_code=403)

    try:
        import aiohttp
    except ImportError:
        return JSONResponse({
            "success": False,
            "error": "aiohttp package not installed. Required for backend API calls."
        }, status_code=500)

    try:
        data = await request.json()
        content = data.get('content')
        filename = data.get('filename', 'slave_config.yaml')
        directory = data.get('directory', '')
        config_type = data.get('config_type', 'slave')
        backend_url = data.get('backend_url')

        if not content:
            return JSONResponse({
                "success": False,
                "error": "Config content is required"
            }, status_code=400)

        if not backend_url:
            return JSONResponse({
                "success": False,
                "error": "Backend URL is required"
            }, status_code=400)

        # Step 1: Save to test directory
        if directory:
            directory = directory.strip('/')
        success, message = _test_mode_service.save_test_config_content(
            filename=filename,
            content=content,
            subdirectory=directory if directory else None
        )

        if not success:
            return JSONResponse({
                "success": False,
                "error": f"Failed to save test config: {message}"
            }, status_code=400)

        # Step 2: Get device ID from communication config (or fallback to supervisor config)
        device_id = get_device_id()

        # Get username from session
        submitted_by = getattr(request.state, "user", "system")

        # Step 3: POST to backend API
        headers = {
            "Content-Type": "text/plain",
            "X-Device-ID": device_id,
            "X-Config-Type": config_type,
            "X-Submitted-By": submitted_by
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    backend_url,
                    data=content,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_text = await response.text()

                    try:
                        backend_response = await response.json()
                    except:
                        backend_response = {"raw_response": response_text}

                    if response.status == 200:
                        return JSONResponse({
                            "success": True,
                            "message": "Config saved and published successfully",
                            "test_config_saved": True,
                            "backend_response": backend_response
                        })
                    else:
                        return JSONResponse({
                            "success": False,
                            "test_config_saved": True,
                            "error": f"Backend API returned status {response.status}",
                            "backend_response": backend_response
                        }, status_code=response.status)

        except aiohttp.ClientError as e:
            return JSONResponse({
                "success": False,
                "test_config_saved": True,
                "error": f"Failed to connect to backend: {str(e)}",
                "hint": "Config was saved to test directory but backend submission failed"
            }, status_code=502)

    except Exception as e:
        logger.error(f"Error publishing config: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=400)


@app.post("/api/test-mode/scan-unit-ids")
async def scan_unit_ids(
    connection_id: str,
    start_id: int = 1,
    end_id: int = 10,
    test_address: int = 0
):
    """Scan a range of unit IDs to find responding devices.

    Args:
        connection_id: Connection ID to use
        start_id: Starting unit ID (1-247)
        end_id: Ending unit ID (1-247)
        test_address: Register address to test
    """
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    # Validate range
    start_id = max(1, min(start_id, 247))
    end_id = max(start_id, min(end_id, 247))

    # Limit scan range for safety
    if end_id - start_id > 20:
        return JSONResponse({
            "error": "Scan range too large. Maximum 20 unit IDs at a time."
        }, status_code=400)

    results = []
    responding = []

    for unit_id in range(start_id, end_id + 1):
        probe_result = await _test_mode_service.probe_device(
            connection_id=connection_id,
            unit_id=unit_id,
            test_address=test_address
        )
        results.append({
            "unit_id": unit_id,
            "success": probe_result["success"],
            "message": probe_result.get("message", "")
        })
        if probe_result["success"]:
            responding.append(unit_id)

    return JSONResponse({
        "connection_id": connection_id,
        "scan_range": f"{start_id}-{end_id}",
        "responding_units": responding,
        "total_found": len(responding),
        "results": results
    })


@app.post("/api/test-mode/test-connection")
async def test_temporary_connection(
    connection_type: str,
    host: Optional[str] = None,
    port: int = 502,
    serial_port: Optional[str] = None,
    baudrate: int = 9600,
    parity: str = "N",
    stopbits: int = 1,
    bytesize: int = 8,
    unit_id: int = 1,
    test_address: int = 0,
    timeout: float = 3.0
):
    """Test a temporary Modbus connection without affecting main config.

    Useful for testing new devices before adding to configuration.

    Args:
        connection_type: "tcp" or "serial"
        host: TCP host address (for TCP)
        port: TCP port (default 502)
        serial_port: Serial port path e.g. /dev/ttyUSB0 (for serial)
        baudrate: Serial baud rate
        parity: Serial parity (N, E, O)
        stopbits: Serial stop bits (1 or 2)
        bytesize: Serial data bits (7 or 8)
        unit_id: Modbus unit ID to test
        test_address: Register address to read
        timeout: Connection timeout in seconds
    """
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    result = await _test_mode_service.test_temporary_connection(
        connection_type=connection_type,
        host=host,
        port=port,
        serial_port=serial_port,
        baudrate=baudrate,
        parity=parity,
        stopbits=stopbits,
        bytesize=bytesize,
        unit_id=unit_id,
        test_address=test_address,
        timeout=timeout
    )

    status_code = 200 if result.get("success") else 400
    return JSONResponse(result, status_code=status_code)


@app.get("/api/test-mode/serial-ports")
async def list_serial_ports():
    """List available serial ports on the system."""
    if not TEST_MODE_AVAILABLE or not _test_mode_service:
        return JSONResponse({
            "error": "Test mode service not available"
        }, status_code=503)

    ports = await _test_mode_service.scan_serial_ports()
    return JSONResponse({"ports": ports})


def run_portal(host: str = "0.0.0.0", port: int = PORTAL_PORT):
    """Run the web portal server."""
    import uvicorn

    logger.info(f"Starting RTU Web Portal on http://{host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="warning",  # Reduce uvicorn logging
        access_log=False  # Disable access logs to reduce overhead
    )


if __name__ == "__main__":
    run_portal()
