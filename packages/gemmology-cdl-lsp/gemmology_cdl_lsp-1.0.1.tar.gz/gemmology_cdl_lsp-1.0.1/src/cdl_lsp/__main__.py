"""
CDL Language Server entry point.

Allows running the server with: python -m cdl_lsp
"""

import argparse
import logging
import sys


def main():
    """Main entry point for the CDL Language Server."""
    parser = argparse.ArgumentParser(description="CDL Language Server")
    parser.add_argument(
        "--stdio", action="store_true", default=True, help="Use stdio for communication (default)"
    )
    parser.add_argument("--tcp", action="store_true", help="Use TCP for communication")
    parser.add_argument("--host", default="127.0.0.1", help="TCP host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=2087, help="TCP port (default: 2087)")
    parser.add_argument("--log-file", default="/tmp/cdl-lsp.log", help="Log file path")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        filename=args.log_file,
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        from .server import create_server
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Install pygls with: pip install pygls lsprotocol", file=sys.stderr)
        sys.exit(1)

    server = create_server()

    if args.tcp:
        server.start_tcp(args.host, args.port)
    else:
        server.start_io()


if __name__ == "__main__":
    main()
