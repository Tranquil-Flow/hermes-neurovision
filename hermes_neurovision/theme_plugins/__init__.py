"""Theme plugin registry for Hermes Vision."""

from __future__ import annotations

from hermes_neurovision.plugin import ThemePlugin

# Plugin registry — populated by imports below
_PLUGINS: dict[str, ThemePlugin] = {}

# Runtime registry for imported theme plugins
_runtime_plugins: dict[str, ThemePlugin] = {}


def register(plugin: ThemePlugin) -> ThemePlugin:
    """Register a plugin instance by its name."""
    _PLUGINS[plugin.name] = plugin
    return plugin


def get_plugin(name: str) -> ThemePlugin:
    """Get plugin for a theme name, falling back to base plugin."""
    if name in _runtime_plugins:
        return _runtime_plugins[name]
    return _PLUGINS.get(name, ThemePlugin())


def registered_names() -> list[str]:
    """Return all registered plugin names."""
    return list(_PLUGINS.keys())


# Import plugin modules to trigger registration.
# Each module registers its plugins at import time.
# Add new plugin files here — order doesn't matter (last write wins on name collision).
def _load_all() -> None:
    _mods = [
        "originals",
        "nature",
        "cosmic",
        "industrial",
        "whimsical",
        "hostile",
        "exotic",
        "mechanical",
        "cosmic_new",
        "originals_v2",
        "nature_v2",
        "ascii_fields",
        "redesigned",
        "experimental",
        "hybrid",
        "emergent_showcase",
        "emergent_v2",
        "advanced_screens",
        "generators",
        "attractors",
        "spectacular",
        "new_screens",
        "legacy_v1_screens",
        "cosmic_v2",
        "mechanical_v2",
    ]
    for mod in _mods:
        try:
            __import__(f"hermes_neurovision.theme_plugins.{mod}")
        except ImportError:
            pass


_load_all()
