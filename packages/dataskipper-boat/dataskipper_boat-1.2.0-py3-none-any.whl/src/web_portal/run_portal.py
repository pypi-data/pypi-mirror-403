#!/usr/bin/env python3
"""
RTU Web Portal - Standalone Runner

Run this script to start the web portal independently from the main application.
This is useful for monitoring and configuration without affecting the main service.

Usage:
    python3 -m src.web_portal.run_portal [--host HOST] [--port PORT]

Or directly:
    python3 src/web_portal/run_portal.py [--host HOST] [--port PORT]
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.web_portal.app import run_portal, PORTAL_PORT


def main():
    parser = argparse.ArgumentParser(
        description="RTU Web Portal - Monitoring and Configuration Interface"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=PORTAL_PORT,
        help=f"Port to listen on (default: {PORTAL_PORT})"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print(f"""
╔═══════════════════════════════════════════════════╗
║           RTU Control Portal v1.0                 ║
╠═══════════════════════════════════════════════════╣
║  Dashboard:  http://{args.host}:{args.port}/
║  Config:     http://{args.host}:{args.port}/config
║  Logs:       http://{args.host}:{args.port}/logs
║  Alerts:     http://{args.host}:{args.port}/alerts
╚═══════════════════════════════════════════════════╝
    """)

    run_portal(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
