"""State persistence utilities for Cindergrace applications.

Provides JSON-based state storage with XDG compliance.

Usage:
    from cgc_common.state import XDGStateStore

    store = XDGStateStore(
        app_name="cindergrace_netman",
        defaults={"autostart": False, "language": "en"}
    )

    # Load state (creates file with defaults if missing)
    state = store.load()

    # Update specific values
    store.update({"autostart": True})

    # Save complete state
    store.save({"autostart": True, "language": "de"})
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


def merge_defaults(
    data: Mapping[str, Any],
    defaults: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge defaults into data, only adding missing keys.

    Args:
        data: Existing data
        defaults: Default values for missing keys

    Returns:
        New dict with defaults applied for missing keys
    """
    result = dict(defaults)
    result.update(data)
    return result


@dataclass
class JSONStore:
    """Simple JSON file storage with defaults support.

    Attributes:
        path: Path to JSON file
        defaults: Default values for missing keys
        indent: JSON indentation (default: 2)
        ensure_ascii: Escape non-ASCII characters (default: False)
    """

    path: Path
    defaults: Mapping[str, Any] = field(default_factory=dict)
    indent: int = 2
    ensure_ascii: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.path, str):
            self.path = Path(self.path)

    def load(self) -> dict[str, Any]:
        """Load JSON file, merge with defaults.

        Returns:
            Dict with loaded data merged with defaults.
            Returns defaults if file doesn't exist.
        """
        if not self.path.exists():
            return dict(self.defaults)

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return dict(self.defaults)

        return merge_defaults(data, self.defaults)

    def save(self, data: Mapping[str, Any]) -> None:
        """Save data to JSON file.

        Creates parent directories if needed.

        Args:
            data: Data to save
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(
                dict(data),
                f,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii,
            )

    def update(self, patch: Mapping[str, Any]) -> dict[str, Any]:
        """Load, merge patch, save, and return result.

        Args:
            patch: Values to update

        Returns:
            Updated state dict
        """
        state = self.load()
        state.update(patch)
        self.save(state)
        return state


def get_xdg_config_home() -> Path:
    """Get XDG config home directory.

    Returns:
        Path from XDG_CONFIG_HOME or ~/.config
    """
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config)
    return Path.home() / ".config"


@dataclass
class XDGStateStore:
    """XDG-compliant state storage.

    Stores state in ~/.config/{app_name}/{filename}

    Attributes:
        app_name: Application name (directory under .config)
        filename: State filename (default: state.json)
        defaults: Default values for missing keys
        indent: JSON indentation (default: 2)
        ensure_ascii: Escape non-ASCII characters (default: False)
    """

    app_name: str
    filename: str = "state.json"
    defaults: Mapping[str, Any] = field(default_factory=dict)
    indent: int = 2
    ensure_ascii: bool = False

    def get_path(self) -> Path:
        """Get full path to state file.

        Returns:
            Path to state file under XDG config
        """
        return get_xdg_config_home() / self.app_name / self.filename

    def _store(self) -> JSONStore:
        """Get internal JSONStore instance."""
        return JSONStore(
            path=self.get_path(),
            defaults=self.defaults,
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
        )

    def load(self) -> dict[str, Any]:
        """Load state from XDG config path.

        Returns:
            Dict with loaded data merged with defaults.
        """
        return self._store().load()

    def save(self, data: Mapping[str, Any]) -> None:
        """Save state to XDG config path.

        Args:
            data: Data to save
        """
        self._store().save(data)

    def update(self, patch: Mapping[str, Any]) -> dict[str, Any]:
        """Update specific values in state.

        Args:
            patch: Values to update

        Returns:
            Updated state dict
        """
        return self._store().update(patch)

    def exists(self) -> bool:
        """Check if state file exists.

        Returns:
            True if state file exists
        """
        return self.get_path().exists()

    def delete(self) -> bool:
        """Delete state file if it exists.

        Returns:
            True if file was deleted, False if it didn't exist
        """
        path = self.get_path()
        if path.exists():
            path.unlink()
            return True
        return False
