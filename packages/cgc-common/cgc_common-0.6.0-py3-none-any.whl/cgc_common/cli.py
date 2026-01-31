"""CLI utilities for Cindergrace applications.

Provides common argument parsing patterns for Gradio-based apps.

Usage:
    from cgc_common.cli import add_server_args, ServerArgs

    parser = argparse.ArgumentParser()
    add_server_args(parser, default_port=7865)
    args = parser.parse_args()

    server_args = ServerArgs.from_namespace(args)
    demo.launch(
        server_name=server_args.host,
        server_port=server_args.port,
        share=server_args.share,
    )
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cgc_common.config import BaseConfig


@dataclass
class ServerArgs:
    """Common server arguments for Gradio apps."""

    host: str
    port: int
    share: bool = False

    @classmethod
    def from_namespace(cls, args: argparse.Namespace) -> "ServerArgs":
        """Create ServerArgs from parsed argparse Namespace."""
        return cls(
            host=getattr(args, "host", "127.0.0.1"),
            port=getattr(args, "port", 7865),
            share=getattr(args, "share", False),
        )


def add_server_args(
    parser: argparse.ArgumentParser,
    default_port: int = 7865,
    default_host: str | None = None,
    port_env_var: str | None = None,
    config_class: type["BaseConfig"] | None = None,
) -> None:
    """Add common server arguments to an argparse parser.

    Args:
        parser: ArgumentParser to add arguments to
        default_port: Default port number
        default_host: Default host (None = use SecurityMixin if available)
        port_env_var: Environment variable name for port (for help text)
        config_class: Optional Config class with SecurityMixin for host detection

    Adds arguments:
        --host: Server host address
        --port: Server port number
        --share: Enable Gradio share link
    """
    # Determine default host
    if default_host is None:
        if config_class is not None and hasattr(config_class, "get_server_bind"):
            default_host = None  # Will be resolved at runtime
            host_help = "Server host (default: from config/env)"
        else:
            default_host = "127.0.0.1"
            host_help = f"Server host (default: {default_host})"
    else:
        host_help = f"Server host (default: {default_host})"

    # Build port help text
    if port_env_var:
        port_help = f"Server port (default: {default_port}, env: {port_env_var})"
    else:
        port_help = f"Server port (default: {default_port})"

    parser.add_argument(
        "--host",
        type=str,
        default=default_host,
        help=host_help,
    )
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=port_help,
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create public Gradio share link",
    )


def resolve_host(
    args: argparse.Namespace,
    config_class: type["BaseConfig"] | None = None,
    default: str = "127.0.0.1",
) -> str:
    """Resolve host from args, config, or default.

    Priority:
    1. Explicit --host argument (if not None)
    2. Config class get_server_bind() (if available)
    3. Default value

    Args:
        args: Parsed argparse Namespace
        config_class: Optional Config class with SecurityMixin
        default: Fallback default host

    Returns:
        Resolved host address
    """
    # Check explicit argument
    host = getattr(args, "host", None)
    if host is not None:
        return host

    # Check config class
    if config_class is not None and hasattr(config_class, "get_server_bind"):
        return config_class.get_server_bind()

    return default


def build_base_parser(
    prog: str | None = None,
    description: str | None = None,
) -> argparse.ArgumentParser:
    """Create a base argument parser with common settings.

    Args:
        prog: Program name (default: auto-detect)
        description: Program description

    Returns:
        Configured ArgumentParser
    """
    return argparse.ArgumentParser(
        prog=prog,
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
