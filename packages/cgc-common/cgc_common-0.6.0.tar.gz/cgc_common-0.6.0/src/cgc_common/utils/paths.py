"""Path sanitization and security utilities.

Provides protection against path traversal attacks and ensures
file operations stay within allowed directories.
"""

import os
from pathlib import Path


class PathTraversalError(ValueError):
    """Raised when a path traversal attempt is detected."""
    pass


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing dangerous characters.

    Removes or replaces characters that could be used for
    path traversal or command injection.

    Args:
        filename: The filename to sanitize

    Returns:
        Sanitized filename safe for filesystem use

    Raises:
        ValueError: If filename is empty after sanitization

    Usage:
        safe_name = sanitize_filename("../../../etc/passwd")
        # Returns: "etc_passwd"

        safe_name = sanitize_filename("file<with>bad:chars?.txt")
        # Returns: "file_with_bad_chars_.txt"
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    # Remove null bytes
    filename = filename.replace("\x00", "")

    # Get just the basename (remove any directory components)
    filename = os.path.basename(filename)

    # Replace dangerous characters
    dangerous_chars = '<>:"/\\|?*\x00'
    for char in dangerous_chars:
        filename = filename.replace(char, "_")

    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")

    # Handle reserved names on Windows
    reserved_names = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    }
    name_without_ext = filename.split(".")[0].upper()
    if name_without_ext in reserved_names:
        filename = f"_{filename}"

    if not filename:
        raise ValueError("Filename is empty after sanitization")

    return filename


def is_safe_path(path: str | Path, base_dir: str | Path) -> bool:
    """Check if a path is safely contained within a base directory.

    Resolves both paths to absolute form and checks that the target
    path starts with the base directory path.

    Args:
        path: The path to check
        base_dir: The allowed base directory

    Returns:
        True if path is within base_dir, False otherwise

    Usage:
        is_safe_path("/app/data/../data/file.txt", "/app/data")  # True
        is_safe_path("/app/data/../config/secrets", "/app/data")  # False
    """
    try:
        base_resolved = Path(base_dir).resolve()
        path_resolved = Path(path).resolve()

        # Check if the resolved path starts with the base directory
        return str(path_resolved).startswith(str(base_resolved) + os.sep) or \
               path_resolved == base_resolved
    except (OSError, ValueError):
        return False


def resolve_safe_path(
    path: str | Path,
    base_dir: str | Path,
    must_exist: bool = False,
) -> Path:
    """Resolve a path and ensure it's within the allowed base directory.

    Combines path resolution with security validation in one step.

    Args:
        path: The path to resolve (can be relative or absolute)
        base_dir: The allowed base directory
        must_exist: If True, raise error if resolved path doesn't exist

    Returns:
        Resolved, validated Path object

    Raises:
        PathTraversalError: If path escapes base_dir
        FileNotFoundError: If must_exist=True and path doesn't exist

    Usage:
        # Safe usage
        safe_path = resolve_safe_path("subdir/file.txt", "/app/data")

        # Catches traversal attempt
        resolve_safe_path("../../../etc/passwd", "/app/data")
        # Raises PathTraversalError
    """
    base_resolved = Path(base_dir).resolve()

    # If path is relative, join with base_dir
    path_obj = Path(path)
    if not path_obj.is_absolute():
        full_path = base_resolved / path_obj
    else:
        full_path = path_obj

    path_resolved = full_path.resolve()

    # Validate containment
    if not is_safe_path(path_resolved, base_resolved):
        raise PathTraversalError(
            f"Path '{path}' escapes allowed directory '{base_dir}'"
        )

    if must_exist and not path_resolved.exists():
        raise FileNotFoundError(f"Path does not exist: {path_resolved}")

    return path_resolved


def safe_join(base_dir: str | Path, *parts: str) -> Path:
    """Safely join path components, preventing traversal.

    Like os.path.join but with security validation.

    Args:
        base_dir: The base directory
        *parts: Path components to join

    Returns:
        Resolved, validated Path object

    Raises:
        PathTraversalError: If resulting path escapes base_dir

    Usage:
        # Safe
        path = safe_join("/app/data", "subdir", "file.txt")

        # Raises error
        path = safe_join("/app/data", "..", "secrets")
    """
    combined = Path(base_dir)
    for part in parts:
        # Reject absolute paths in parts
        if Path(part).is_absolute():
            raise PathTraversalError(f"Absolute path not allowed: {part}")
        combined = combined / part

    return resolve_safe_path(combined, base_dir)


def normalize_path(path: str | Path) -> Path:
    """Normalize a path by expanding user directory and resolving.

    Does NOT perform security validation - use resolve_safe_path for that.

    Args:
        path: Path to normalize

    Returns:
        Normalized Path object

    Usage:
        normalize_path("~/documents")  # /home/user/documents
        normalize_path("./relative/../path")  # /current/path
    """
    return Path(path).expanduser().resolve()
