"""Import themes from .hvtheme files."""

import base64
import curses
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


@dataclass
class Version:
    """Version number for compatibility checking."""
    major: int
    minor: int
    
    @classmethod
    def parse(cls, version_str: str) -> "Version":
        """Parse version string like '1.0' into Version object."""
        parts = version_str.split(".")
        return cls(
            major=int(parts[0]),
            minor=int(parts[1]) if len(parts) > 1 else 0
        )
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"
    
    def __ge__(self, other) -> bool:
        if self.major != other.major:
            return self.major > other.major
        return self.minor >= other.minor


class IncompatibleVersionError(Exception):
    """Raised when theme format version is incompatible."""
    pass


def import_theme(theme_path: str, preview_only: bool = False, trust: bool = False) -> Dict[str, Any]:
    """
    Import theme from .hvtheme file.
    
    Args:
        theme_path: Path to .hvtheme file
        preview_only: If True, only show info without installing
        trust: If True, skip confirmation for custom plugins
        
    Returns:
        Dict with import result and metadata
        
    Raises:
        IncompatibleVersionError: If format version is too new
        FileNotFoundError: If theme file doesn't exist
        ValueError: If theme file is invalid
    """
    theme_path = Path(theme_path).expanduser()
    
    if not theme_path.exists():
        raise FileNotFoundError(f"Theme file not found: {theme_path}")
    
    # Load theme file
    with open(theme_path) as f:
        try:
            theme_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in theme file: {e}")
    
    # Check version compatibility
    file_version = Version.parse(theme_data.get("format_version", "0.9"))
    current_version = Version.parse("1.0")
    
    # Check major version compatibility
    if file_version.major > current_version.major:
        raise IncompatibleVersionError(
            f"Theme requires format version {file_version.major}.x\n"
            f"Current version: {current_version.major}.x\n"
            f"Please upgrade Hermes Vision to import this theme."
        )
    
    # Migrate old versions
    if file_version.major == 0:
        print("⚠  Theme from pre-release version detected")
        print("   Attempting automatic migration...\n")
        theme_data = _migrate_v0_to_v1(theme_data)
        file_version = Version.parse("1.0")
    
    # Warn about newer minor versions
    if file_version.minor > current_version.minor:
        print(f"⚠  Theme created with newer format version ({file_version})")
        print(f"   Current version: {current_version}")
        print("   Some features may not be available.")
        print("   Consider upgrading Hermes Vision.\n")
    
    # Validate required fields
    if "metadata" not in theme_data:
        raise ValueError("Invalid theme file: missing 'metadata' field")
    if "config" not in theme_data:
        raise ValueError("Invalid theme file: missing 'config' field")
    if "plugin" not in theme_data:
        raise ValueError("Invalid theme file: missing 'plugin' field")
    
    metadata = theme_data["metadata"]
    config = theme_data["config"]
    plugin = theme_data["plugin"]
    
    # Preview mode - just return info
    if preview_only:
        return {
            "preview": True,
            "name": metadata.get("name", "unknown"),
            "title": metadata.get("title", "Untitled"),
            "author": metadata.get("author", "unknown"),
            "description": metadata.get("description", ""),
            "created": metadata.get("created", ""),
            "has_plugin": plugin.get("type") == "custom",
            "config": config
        }
    
    # Check for custom plugin
    has_custom_plugin = plugin.get("type") == "custom"
    
    if has_custom_plugin and not trust:
        # Show warning and require confirmation
        print("⚠  WARNING: This theme contains custom Python code\n")
        print("   Theme:", metadata.get("title", "Unknown"))
        print("   Author:", metadata.get("author", "Unknown"))
        print(f"   Created: {metadata.get('created', 'Unknown')}\n")
        
        response = input("   Review plugin code before installing? [Y/n] ").strip().lower()
        
        if response not in ("n", "no"):
            # Show plugin code
            plugin_code = base64.b64decode(plugin["code"]).decode('utf-8')
            print("\n" + "="*70)
            print("PLUGIN CODE:")
            print("="*70)
            print(plugin_code)
            print("="*70 + "\n")
        
        response = input("   Install this theme? [y/N] ").strip().lower()
        
        if response not in ("y", "yes"):
            print("\n✗  Import cancelled by user")
            return {"success": False, "cancelled": True}
    
    # Import theme
    theme_name = metadata["name"]
    
    # 1. Save .hvtheme file to ~/.hermes/vision/themes/imported/
    import_dir = Path.home() / ".hermes" / "vision" / "themes" / "imported"
    import_dir.mkdir(parents=True, exist_ok=True)
    
    dest_file = import_dir / f"{theme_name}.hvtheme"
    
    with open(dest_file, 'w') as f:
        json.dump(theme_data, f, indent=2)
    
    # 2. Register theme config at runtime
    _register_theme_config(theme_name, metadata.get("title", theme_name.title()), config)
    
    # 3. If custom plugin, register it
    if has_custom_plugin:
        plugin_code = base64.b64decode(plugin["code"]).decode('utf-8')
        class_name = plugin["class_name"]
        _register_plugin(theme_name, plugin_code, class_name)
    
    # 4. Update theme registry
    _update_registry(theme_name, metadata, has_custom_plugin, str(dest_file))
    
    return {
        "success": True,
        "name": theme_name,
        "title": metadata.get("title", theme_name.title()),
        "path": str(dest_file),
        "has_plugin": has_custom_plugin
    }


def _migrate_v0_to_v1(data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate pre-release format to v1.0."""
    return {
        "format_version": "1.0",
        "metadata": {
            "name": data.get("name", "unknown"),
            "title": data.get("title", "Untitled"),
            "author": "unknown",
            "description": "Migrated from pre-release version",
            "created": datetime.utcnow().isoformat() + "Z",
            "hermes_vision_version": "0.1.1"
        },
        "config": data.get("config", {}),
        "plugin": {
            "type": "custom" if "plugin_code" in data else "base",
            "code": data.get("plugin_code"),
            "class_name": data.get("plugin_class")
        }
    }


def _register_theme_config(theme_name: str, title: str, config_dict: Dict[str, Any]) -> None:
    """Register theme config at runtime."""
    from hermes_vision.themes import ThemeConfig
    
    # Convert color strings back to curses constants
    color_map = {
        "COLOR_BLACK": curses.COLOR_BLACK,
        "COLOR_RED": curses.COLOR_RED,
        "COLOR_GREEN": curses.COLOR_GREEN,
        "COLOR_YELLOW": curses.COLOR_YELLOW,
        "COLOR_BLUE": curses.COLOR_BLUE,
        "COLOR_MAGENTA": curses.COLOR_MAGENTA,
        "COLOR_CYAN": curses.COLOR_CYAN,
        "COLOR_WHITE": curses.COLOR_WHITE,
    }
    
    palette = tuple(color_map.get(c, curses.COLOR_WHITE) for c in config_dict.get("palette", []))
    
    # Create ThemeConfig
    config = ThemeConfig(
        name=theme_name,
        title=title,
        accent_char=config_dict.get("accent_char", "*"),
        background_density=config_dict.get("background_density", 0.030),
        star_drift=config_dict.get("star_drift", 0.10),
        node_jitter=config_dict.get("node_jitter", 0.20),
        packet_rate=config_dict.get("packet_rate", 0.30),
        packet_speed=tuple(config_dict.get("packet_speed", [0.04, 0.08])),
        pulse_rate=config_dict.get("pulse_rate", 0.10),
        edge_bias=config_dict.get("edge_bias", 0.50),
        cluster_count=config_dict.get("cluster_count", 3),
        palette=palette
    )
    
    # Add to runtime config registry
    from hermes_vision import themes
    if not hasattr(themes, '_runtime_configs'):
        themes._runtime_configs = {}
    themes._runtime_configs[theme_name] = config


def _register_plugin(theme_name: str, plugin_code: str, class_name: str) -> None:
    """Register plugin at runtime."""
    # Import necessary items for plugin code
    from hermes_vision.plugin import ThemePlugin
    from hermes_vision.scene import Particle
    import math
    
    # Execute plugin code in namespace with required imports
    namespace = {
        'ThemePlugin': ThemePlugin,
        'Particle': Particle,
        'math': math,
    }
    exec(plugin_code, namespace)
    
    # Get plugin class
    if class_name not in namespace:
        raise ValueError(f"Plugin class '{class_name}' not found in code")
    
    plugin_class = namespace[class_name]
    plugin_instance = plugin_class()
    
    # Register with plugin system
    from hermes_vision import theme_plugins
    if not hasattr(theme_plugins, '_runtime_plugins'):
        theme_plugins._runtime_plugins = {}
    theme_plugins._runtime_plugins[theme_name] = plugin_instance


def _update_registry(theme_name: str, metadata: Dict[str, Any], has_plugin: bool, source_path: str) -> None:
    """Update theme registry."""
    registry_path = Path.home() / ".hermes" / "vision" / "theme_registry.json"
    
    # Load existing registry
    if registry_path.exists():
        with open(registry_path) as f:
            registry = json.load(f)
    else:
        registry = {"themes": {}}
    
    # Add/update entry
    registry["themes"][theme_name] = {
        "type": "imported",
        "source": source_path,
        "installed": datetime.utcnow().isoformat() + "Z",
        "author": metadata.get("author", "unknown"),
        "title": metadata.get("title", theme_name.title()),
        "description": metadata.get("description", ""),
        "has_plugin": has_plugin
    }
    
    # Save registry
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)


def list_themes(custom_only: bool = False) -> None:
    """List all themes with metadata."""
    registry_path = Path.home() / ".hermes" / "vision" / "theme_registry.json"
    
    if not registry_path.exists():
        print("No imported themes found")
        return
    
    with open(registry_path) as f:
        registry = json.load(f)
    
    themes = registry.get("themes", {})
    
    if not themes:
        print("No imported themes found")
        return
    
    print("\nImported Themes:")
    print("=" * 70)
    
    for name, info in themes.items():
        if custom_only and info.get("type") != "custom":
            continue
        
        print(f"\n  Name: {name}")
        print(f"  Title: {info.get('title', 'N/A')}")
        print(f"  Author: {info.get('author', 'unknown')}")
        print(f"  Installed: {info.get('installed', 'unknown')}")
        print(f"  Custom Plugin: {'Yes' if info.get('has_plugin') else 'No'}")
        if info.get("description"):
            print(f"  Description: {info.get('description')}")
    
    print("\n" + "=" * 70)
    print(f"Total: {len(themes)} theme(s)\n")
