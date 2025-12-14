#!/usr/bin/env python
# Main Entry Point for PeerAgent
"""
Start the PeerAgent API server.

Usage:
    python main.py                  # Development server
    python main.py --production     # Production server with gunicorn
"""

import sys
import argparse


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PeerAgent API Server")
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run in production mode with gunicorn"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of workers for production (default: 4)"
    )
    
    args = parser.parse_args()
    
    if args.production:
        import subprocess
        cmd = [
            "gunicorn", "src.api.main:app",
            "--workers", str(args.workers),
            "--worker-class", "uvicorn.workers.UvicornWorker",
            "--bind", f"{args.host}:{args.port}",
            "--timeout", "120",
            "--keep-alive", "5",
            "--access-logfile", "-",
            "--error-logfile", "-"
        ]
        subprocess.run(cmd)
    else:
        import uvicorn
        uvicorn.run(
            "src.api.main:app",
            host=args.host,
            port=args.port,
            reload=True,
            log_level="debug"
        )


if __name__ == "__main__":
    main()
