"""
CGC Common - ComfyUI Workflow Utilities.

Provides helper functions for manipulating ComfyUI workflows.
"""

import random
from typing import Any


def inject_seed(workflow: dict[str, Any], seed: int | None = None) -> dict[str, Any]:
    """
    Inject a seed value into all sampler nodes marked with '(seed)' in their title.

    Nodes must have '(seed)' in their _meta.title to be affected.
    Supports both 'seed' parameter (KSampler) and 'noise_seed' parameter (KSamplerAdvanced).

    Args:
        workflow: ComfyUI workflow dict (API format)
        seed: Seed value to inject. If None, generates a random seed.

    Returns:
        Modified workflow dict (same reference, modified in place)

    Example:
        >>> workflow = load_workflow("my_workflow.json")
        >>> inject_seed(workflow, seed=12345)
        >>> # Or with random seed:
        >>> inject_seed(workflow)
    """
    if seed is None:
        # JavaScript-safe max integer (2^53 - 1)
        seed = random.randint(0, 9007199254740991)

    for node_id, node in workflow.items():
        if not isinstance(node, dict):
            continue

        title = node.get("_meta", {}).get("title", "")
        if "(seed)" not in title.lower():
            continue

        inputs = node.get("inputs", {})

        # KSampler uses "seed"
        if "seed" in inputs:
            inputs["seed"] = seed
        # KSamplerAdvanced / RandomNoise use "noise_seed"
        elif "noise_seed" in inputs:
            inputs["noise_seed"] = seed

    return workflow


def inject_resolution(
    workflow: dict[str, Any],
    resolution: str,
) -> dict[str, Any]:
    """
    Inject resolution (width/height) into all nodes with 'Resolution' in their title.

    Args:
        workflow: ComfyUI workflow dict (API format)
        resolution: Resolution string like "1920x1080" or "1024x1024"

    Returns:
        Modified workflow dict (same reference, modified in place)

    Example:
        >>> workflow = load_workflow("my_workflow.json")
        >>> inject_resolution(workflow, "1920x1080")
    """
    try:
        width, height = map(int, resolution.lower().split("x"))
    except (ValueError, AttributeError):
        # Invalid format, return unchanged
        return workflow

    for node_id, node in workflow.items():
        if not isinstance(node, dict):
            continue

        title = node.get("_meta", {}).get("title", "")
        if "resolution" not in title.lower():
            continue

        inputs = node.get("inputs", {})

        # Set width and height if they exist
        if "width" in inputs:
            inputs["width"] = width
        if "height" in inputs:
            inputs["height"] = height

    return workflow


def set_node_value(
    workflow: dict[str, Any],
    node_title: str,
    param_name: str,
    value: Any,
) -> bool:
    """
    Set a parameter value on a node identified by its title.

    Args:
        workflow: ComfyUI workflow dict (API format)
        node_title: The _meta.title of the node to modify
        param_name: The parameter name in inputs to set
        value: The value to set

    Returns:
        True if node was found and modified, False otherwise

    Example:
        >>> set_node_value(workflow, "Positive Prompt", "value", "a beautiful sunset")
        >>> set_node_value(workflow, "Resolution", "width", 1920)
    """
    for node_id, node in workflow.items():
        if not isinstance(node, dict):
            continue

        title = node.get("_meta", {}).get("title", "")
        if title == node_title:
            if "inputs" not in node:
                node["inputs"] = {}
            node["inputs"][param_name] = value
            return True

    return False


def get_node_by_title(
    workflow: dict[str, Any],
    node_title: str,
) -> tuple[str | None, dict[str, Any] | None]:
    """
    Find a node by its title.

    Args:
        workflow: ComfyUI workflow dict (API format)
        node_title: The _meta.title of the node to find

    Returns:
        Tuple of (node_id, node_dict) or (None, None) if not found

    Example:
        >>> node_id, node = get_node_by_title(workflow, "KSampler (seed)")
        >>> if node:
        ...     print(f"Found at {node_id}: {node['inputs']}")
    """
    for node_id, node in workflow.items():
        if not isinstance(node, dict):
            continue

        title = node.get("_meta", {}).get("title", "")
        if title == node_title:
            return node_id, node

    return None, None


def find_nodes_by_class(
    workflow: dict[str, Any],
    class_type: str,
) -> list[tuple[str, dict[str, Any]]]:
    """
    Find all nodes of a specific class type.

    Args:
        workflow: ComfyUI workflow dict (API format)
        class_type: The class_type to search for (e.g., "KSampler", "CLIPTextEncode")

    Returns:
        List of (node_id, node_dict) tuples

    Example:
        >>> samplers = find_nodes_by_class(workflow, "KSampler")
        >>> for node_id, node in samplers:
        ...     print(f"Sampler at {node_id}: steps={node['inputs'].get('steps')}")
    """
    results = []
    for node_id, node in workflow.items():
        if not isinstance(node, dict):
            continue

        if node.get("class_type") == class_type:
            results.append((node_id, node))

    return results
