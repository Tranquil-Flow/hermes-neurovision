"""Theme configurations for Hermes Vision."""

from __future__ import annotations

import curses
from dataclasses import dataclass
from typing import Tuple

THEMES: Tuple[str, ...] = (
    "neural-sky",
    "electric-mycelium",
    "cathedral-circuit",
    "storm-core",
    "hybrid",
    "moonwire",
    "rootsong",
    "stormglass",
    "spiral-galaxy",
    "black-hole",
)

FRAME_DELAY = 0.05
DEFAULT_THEME_SECONDS = 8.0
STAR_CHARS = ".·*+"
PACKET_CHARS = "o*+x"
PULSE_CHARS = ".:oO@"


@dataclass
class ThemeConfig:
    name: str
    title: str
    accent_char: str
    background_density: float
    star_drift: float
    node_jitter: float
    packet_rate: float
    packet_speed: Tuple[float, float]
    pulse_rate: float
    edge_bias: float
    cluster_count: int
    ring_mode: bool = False
    storm_mode: bool = False
    root_mode: bool = False
    cathedral_mode: bool = False
    glass_mode: bool = False
    moon_mode: bool = False
    hybrid_mode: bool = False
    galaxy_mode: bool = False
    black_hole_mode: bool = False
    palette: Tuple[int, int, int, int] = (curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_MAGENTA)


def build_theme_config(name: str) -> ThemeConfig:
    configs = {
        "neural-sky": ThemeConfig(name, "Neural Sky", "*", 0.030, 0.10, 0.40, 0.32, (0.04, 0.08), 0.10, 0.4, 3, palette=(curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_MAGENTA)),
        "electric-mycelium": ThemeConfig(name, "Electric Mycelium", "o", 0.020, 0.05, 0.18, 0.40, (0.05, 0.10), 0.12, 0.55, 4, palette=(curses.COLOR_GREEN, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "cathedral-circuit": ThemeConfig(name, "Cathedral Circuit", "#", 0.015, 0.03, 0.08, 0.24, (0.03, 0.06), 0.07, 0.70, 2, cathedral_mode=True, palette=(curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_MAGENTA)),
        "storm-core": ThemeConfig(name, "Storm Core", "x", 0.024, 0.18, 0.52, 0.42, (0.06, 0.10), 0.12, 0.35, 3, storm_mode=True, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "hybrid": ThemeConfig(name, "Hybrid", "@", 0.028, 0.11, 0.28, 0.38, (0.05, 0.09), 0.12, 0.50, 4, hybrid_mode=True, palette=(curses.COLOR_CYAN, curses.COLOR_MAGENTA, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "moonwire": ThemeConfig(name, "Moonwire", "•", 0.026, 0.04, 0.16, 0.20, (0.02, 0.05), 0.07, 0.48, 2, ring_mode=True, moon_mode=True, palette=(curses.COLOR_WHITE, curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_MAGENTA)),
        "rootsong": ThemeConfig(name, "Rootsong", ":", 0.014, 0.02, 0.14, 0.28, (0.03, 0.06), 0.10, 0.66, 2, root_mode=True, palette=(curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_CYAN)),
        "stormglass": ThemeConfig(name, "Stormglass", "+", 0.032, 0.08, 0.30, 0.34, (0.04, 0.08), 0.12, 0.58, 3, glass_mode=True, palette=(curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_BLUE, curses.COLOR_MAGENTA)),
        "spiral-galaxy": ThemeConfig(name, "Spiral Galaxy", "✦", 0.040, 0.00, 0.10, 0.26, (0.02, 0.05), 0.07, 0.62, 3, galaxy_mode=True, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_MAGENTA)),
        "black-hole": ThemeConfig(name, "Black Hole", "·", 0.036, 0.00, 0.06, 0.18, (0.02, 0.04), 0.05, 0.74, 2, black_hole_mode=True, palette=(curses.COLOR_BLUE, curses.COLOR_MAGENTA, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
    }
    return configs[name]
