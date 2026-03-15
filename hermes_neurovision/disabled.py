"""Theme disable/enable system for Hermes Vision.

Persists a list of disabled theme names to ~/.hermes/neurovision/disabled.json.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

DISABLED_CONFIG = os.path.expanduser("~/.hermes/neurovision/disabled.json")


def load_disabled() -> set[str]:
    """Return the set of currently disabled theme names."""
    try:
        with open(DISABLED_CONFIG) as f:
            data = json.load(f)
        return set(data.get("disabled", []))
    except (OSError, json.JSONDecodeError):
        return set()


def save_disabled(names: set[str]) -> None:
    """Persist the full set of disabled theme names."""
    path = Path(DISABLED_CONFIG)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({"disabled": sorted(names)}, f, indent=2)


def add_disabled(name: str) -> None:
    """Add a theme to the disabled list."""
    names = load_disabled()
    names.add(name)
    save_disabled(names)


def remove_disabled(name: str) -> None:
    """Remove a theme from the disabled list (enable it)."""
    names = load_disabled()
    names.discard(name)
    save_disabled(names)
