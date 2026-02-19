"""Serve generated dashboard HTML files over HTTP."""

from __future__ import annotations

import argparse
import logging
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from qa_chatbot.config import LoggingSettings, configure_logging


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the server."""
    parser = argparse.ArgumentParser(description="Serve the dashboard HTML output directory.")
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path("./dashboard_html"),
        help="Path to the generated dashboard HTML directory (default: ./dashboard_html).",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000).")
    return parser.parse_args()


LOGGER = logging.getLogger(__name__)


def run_server(directory: Path, host: str, port: int) -> None:
    """Run the static file server for the given directory."""
    if not directory.exists():
        message = f"Dashboard output directory not found: {directory}"
        raise FileNotFoundError(message)
    handler = partial(SimpleHTTPRequestHandler, directory=str(directory.resolve()))
    server = ThreadingHTTPServer((host, port), handler)
    LOGGER.info(
        "Serving dashboard HTML",
        extra={
            "directory": str(directory),
            "url": f"http://{host}:{port}",
        },
    )
    server.serve_forever()


def main() -> None:
    """Entry point for the dashboard server."""
    args = parse_args()
    configure_logging(LoggingSettings(level="INFO"))
    run_server(args.directory, args.host, args.port)


if __name__ == "__main__":
    main()
