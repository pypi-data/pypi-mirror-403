"""
CGC Common - ComfyUI Integration Module.

Provides a clean, testable client for ComfyUI API communication.
"""

from .client import ComfyUIClient, ComfyUIError, ConnectionError, ExecutionError
from .models import (
    ComfyUIConfig,
    ExecutionResult,
    OutputFile,
    QueueResponse,
)
from .workflow import (
    inject_seed,
    inject_resolution,
    set_node_value,
    get_node_by_title,
    find_nodes_by_class,
)

__all__ = [
    # Client
    "ComfyUIClient",
    "ComfyUIError",
    "ConnectionError",
    "ExecutionError",
    # Models
    "ComfyUIConfig",
    "ExecutionResult",
    "OutputFile",
    "QueueResponse",
    # Workflow Utilities
    "inject_seed",
    "inject_resolution",
    "set_node_value",
    "get_node_by_title",
    "find_nodes_by_class",
]
