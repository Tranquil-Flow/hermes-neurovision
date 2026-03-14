"""Theme plugin registry for Hermes Vision."""

from __future__ import annotations

from hermes_vision.plugin import ThemePlugin

# Plugin registry — populated by imports below
_PLUGINS: dict[str, ThemePlugin] = {}


def register(plugin: ThemePlugin) -> ThemePlugin:
    """Register a plugin instance by its name."""
    _PLUGINS[plugin.name] = plugin
    return plugin


def get_plugin(name: str) -> ThemePlugin:
    """Get plugin for a theme name, falling back to base plugin."""
    return _PLUGINS.get(name, ThemePlugin())


def registered_names() -> list[str]:
    """Return all registered plugin names."""
    return list(_PLUGINS.keys())


# Import plugin modules to trigger registration
# Each module registers its plugins at import time
def _load_all() -> None:
    from hermes_vision.theme_plugins import originals  # noqa: F401
    try:
        from hermes_vision.theme_plugins import nature  # noqa: F401
    except ImportError:
        pass
    try:
        from hermes_vision.theme_plugins import cosmic  # noqa: F401
    except ImportError:
        pass
    try:
        from hermes_vision.theme_plugins import industrial  # noqa: F401
    except ImportError:
        pass
    try:
        from hermes_vision.theme_plugins import whimsical  # noqa: F401
    except ImportError:
        pass
    try:
        from hermes_vision.theme_plugins import hostile  # noqa: F401
    except ImportError:
        pass
    try:
        from hermes_vision.theme_plugins import exotic  # noqa: F401
    except ImportError:
        pass
    try:
        from hermes_vision.theme_plugins import mechanical  # noqa: F401
    except ImportError:
        pass
    try:
        from hermes_vision.theme_plugins import cosmic_new  # noqa: F401
    except ImportError:
        pass


_load_all()
