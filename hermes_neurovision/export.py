"""Export themes to .hvtheme format."""

import base64
import curses
import inspect
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from hermes_neurovision.themes import build_theme_config
from hermes_neurovision.theme_plugins import get_plugin
from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision import __version__


def export_theme(
    theme_name: str,
    output_path: Optional[str] = None,
    author: Optional[str] = None,
    description: Optional[str] = None
) -> Path:
    """
    Export a theme to .hvtheme file.
    
    Args:
        theme_name: Name of theme to export
        output_path: Optional custom output path
        author: Optional author name
        description: Optional description
        
    Returns:
        Path to created .hvtheme file
        
    Raises:
        ValueError: If theme doesn't exist
    """
    # Get theme config
    try:
        config = build_theme_config(theme_name)
    except KeyError:
        raise ValueError(f"Theme '{theme_name}' not found")
    
    # Get plugin
    plugin = get_plugin(theme_name)
    is_custom_plugin = type(plugin).__name__ != "ThemePlugin"
    
    # Build metadata
    metadata = {
        "name": theme_name,
        "title": config.title,
        "author": author or "anonymous",
        "description": description or f"{config.title} theme for Hermes Neurovision",
        "created": datetime.utcnow().isoformat() + "Z",
        "hermes_neurovision_version": __version__,
        "hermes_vision_version": "0.1.1",  # Backward compatibility
        "hermes_agent_version": "0.2.0",
        "min_api_version": "1.0"
    }
    
    # Build config dict
    config_dict = {
        "accent_char": config.accent_char,
        "background_density": config.background_density,
        "star_drift": config.star_drift,
        "node_jitter": config.node_jitter,
        "packet_rate": config.packet_rate,
        "packet_speed": list(config.packet_speed),
        "pulse_rate": config.pulse_rate,
        "edge_bias": config.edge_bias,
        "cluster_count": config.cluster_count,
        "palette": [_color_to_string(c) for c in config.palette]
    }
    
    # Build plugin block
    if is_custom_plugin:
        # Get plugin source code
        plugin_code = inspect.getsource(type(plugin))
        encoded_code = base64.b64encode(plugin_code.encode('utf-8')).decode('ascii')
        
        plugin_dict = {
            "type": "custom",
            "code": encoded_code,
            "class_name": type(plugin).__name__
        }
    else:
        plugin_dict = {
            "type": "base"
        }
    
    # Build complete export
    export_data = {
        "format_version": "1.1",
        "metadata": metadata,
        "config": config_dict,
        "plugin": plugin_dict
    }
    
    # Determine output path
    if output_path is None:
        output_path = f"{theme_name}.hvtheme"
    
    output_file = Path(output_path).expanduser()
    
    # Create parent directories if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to file
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    return output_file


def _color_to_string(color_code: int) -> str:
    """Convert curses color code to string."""
    color_map = {
        curses.COLOR_BLACK: "COLOR_BLACK",
        curses.COLOR_RED: "COLOR_RED",
        curses.COLOR_GREEN: "COLOR_GREEN",
        curses.COLOR_YELLOW: "COLOR_YELLOW",
        curses.COLOR_BLUE: "COLOR_BLUE",
        curses.COLOR_MAGENTA: "COLOR_MAGENTA",
        curses.COLOR_CYAN: "COLOR_CYAN",
        curses.COLOR_WHITE: "COLOR_WHITE",
    }
    return color_map.get(color_code, "COLOR_WHITE")
