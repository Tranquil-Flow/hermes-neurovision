"""Theme configurations for Hermes Vision."""

from __future__ import annotations

import curses
from dataclasses import dataclass
from typing import Tuple

LEGACY_THEMES: Tuple[str, ...] = (
    "legacy-starfall", "legacy-quasar", "legacy-supernova", "legacy-sol",
    "legacy-terra", "legacy-binary-star",
    "legacy-neural-sky", "legacy-storm-core", "legacy-moonwire",
    "legacy-rootsong", "legacy-stormglass", "legacy-spiral-galaxy", "legacy-black-hole",
    "legacy-deep-abyss", "legacy-storm-sea", "legacy-dark-forest",
    "legacy-mountain-stars", "legacy-beach-lighthouse",
)

THEMES: Tuple[str, ...] = (
    # ── Originals (7) ───────────────────────────────────────────
    "black-hole",
    "neural-sky",
    "storm-core",
    "moonwire",
    "rootsong",
    "stormglass",
    "spiral-galaxy",
    # ── Nature (5) ───────────────────────────────────────────────
    "deep-abyss",
    "storm-sea",
    "dark-forest",
    "mountain-stars",
    "beach-lighthouse",
    # ── Cosmic (4) ───────────────────────────────────────────────
    "aurora-borealis",
    "nebula-nursery",
    "binary-rain",
    "wormhole",
    # ── Industrial (4) ───────────────────────────────────────────
    "liquid-metal",
    "factory-floor",
    "pipe-hell",
    "oil-slick",
    # ── Whimsical (5) ────────────────────────────────────────────
    "campfire",
    "aquarium",
    "circuit-board",
    "lava-lamp",
    "firefly-field",
    # ── Hostile (2) ──────────────────────────────────────────────
    "noxious-fumes",
    "maze-runner",
    # ── Exotic (5) ───────────────────────────────────────────────
    "neon-rain",
    "volcanic",
    "crystal-cave",
    "spider-web",
    "snow-globe",
    # ── Mechanical/Retro (5) ─────────────────────────────────────
    "clockwork",
    "coral-reef",
    "ant-colony",
    "satellite-orbit",
    "starfall",
    # ── Cosmic New (5) ───────────────────────────────────────────
    "quasar",
    "supernova",
    "sol",
    "terra",
    "binary-star",
    # ── ASCII Fields (10) ─────────────────────────────────────────────
    "synaptic-plasma",
    "oracle",
    "cellular-cortex",
    "reaction-field",
    "stellar-weave",
    "life-colony",
    "aurora-bands",
    "waveform-scope",
    "lissajous-mind",
    "pulse-matrix",
    # ── Extreme Fields (3) ───────────────────────────────────────────
    "fractal-engine",
    "n-body",
    "standing-waves",
    # ── Experimental (3) ─────────────────────────────────────────────
    "clifford-attractor",
    "barnsley-fern",
    "flow-field",
    # ── Hybrid (2) ───────────────────────────────────────────────────
    "plasma-grid",
    "deep-signal",
)

FRAME_DELAY = 0.05
DEFAULT_THEME_SECONDS = 8.0
STAR_CHARS = ".\u00b7*+"
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
    palette: Tuple[int, int, int, int] = (curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_MAGENTA)


# Runtime registry for imported themes
_runtime_configs = {}


def build_theme_config(name: str) -> ThemeConfig:
    # Check runtime configs first (for imported themes)
    if name in _runtime_configs:
        return _runtime_configs[name]
    
    configs = {
        # ── Originals ────────────────────────────────────────────
        "neural-sky": ThemeConfig(name, "Neural Sky", "*", 0.030, 0.10, 0.40, 0.32, (0.04, 0.08), 0.10, 0.4, 3, palette=(curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_MAGENTA)),
        "electric-mycelium": ThemeConfig(name, "Electric Mycelium", "o", 0.020, 0.05, 0.18, 0.40, (0.05, 0.10), 0.12, 0.55, 4, palette=(curses.COLOR_GREEN, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "cathedral-circuit": ThemeConfig(name, "Cathedral Circuit", "#", 0.015, 0.03, 0.08, 0.24, (0.03, 0.06), 0.07, 0.70, 2, palette=(curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_MAGENTA)),
        "storm-core": ThemeConfig(name, "Storm Core", "x", 0.024, 0.18, 0.52, 0.42, (0.06, 0.10), 0.12, 0.35, 3, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "hybrid": ThemeConfig(name, "Hybrid", "@", 0.028, 0.11, 0.28, 0.38, (0.05, 0.09), 0.12, 0.50, 4, palette=(curses.COLOR_CYAN, curses.COLOR_MAGENTA, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "moonwire": ThemeConfig(name, "Moonwire", "\u2022", 0.026, 0.04, 0.16, 0.20, (0.02, 0.05), 0.07, 0.48, 2, palette=(curses.COLOR_WHITE, curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_MAGENTA)),
        "rootsong": ThemeConfig(name, "Rootsong", ":", 0.014, 0.02, 0.14, 0.28, (0.03, 0.06), 0.10, 0.66, 2, palette=(curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_CYAN)),
        "stormglass": ThemeConfig(name, "Stormglass", "+", 0.032, 0.08, 0.30, 0.34, (0.04, 0.08), 0.12, 0.58, 3, palette=(curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_BLUE, curses.COLOR_MAGENTA)),
        "spiral-galaxy": ThemeConfig(name, "Spiral Galaxy", "\u2726", 0.040, 0.00, 0.10, 0.26, (0.02, 0.05), 0.07, 0.62, 3, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_MAGENTA)),
        "black-hole": ThemeConfig(name, "Black Hole", "\u00b7", 0.036, 0.00, 0.06, 0.18, (0.02, 0.04), 0.05, 0.74, 2, palette=(curses.COLOR_BLUE, curses.COLOR_MAGENTA, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        # ── Nature ───────────────────────────────────────────────
        "deep-abyss": ThemeConfig(name, "Deep Abyss", "\u2727", 0.018, 0.02, 0.20, 0.22, (0.03, 0.06), 0.08, 0.50, 3, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_GREEN)),
        "storm-sea": ThemeConfig(name, "Storm Sea", "~", 0.028, 0.15, 0.48, 0.36, (0.05, 0.09), 0.10, 0.40, 3, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "dark-forest": ThemeConfig(name, "Dark Forest", "\u25c9", 0.022, 0.04, 0.14, 0.26, (0.03, 0.06), 0.08, 0.55, 3, palette=(curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_CYAN)),
        "mountain-stars": ThemeConfig(name, "Mountain Stars", "\u2726", 0.045, 0.00, 0.06, 0.20, (0.02, 0.04), 0.06, 0.60, 3, palette=(curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_MAGENTA)),
        "beach-lighthouse": ThemeConfig(name, "Beach Lighthouse", "\u00b7", 0.020, 0.03, 0.12, 0.18, (0.02, 0.04), 0.06, 0.45, 2, palette=(curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW, curses.COLOR_BLUE)),
        # ── Cosmic ───────────────────────────────────────────────
        "aurora-borealis": ThemeConfig(name, "Aurora Borealis", "~", 0.024, 0.02, 0.30, 0.24, (0.03, 0.06), 0.08, 0.50, 3, palette=(curses.COLOR_GREEN, curses.COLOR_CYAN, curses.COLOR_MAGENTA, curses.COLOR_WHITE)),
        "nebula-nursery": ThemeConfig(name, "Nebula Nursery", "*", 0.050, 0.04, 0.22, 0.30, (0.04, 0.08), 0.10, 0.45, 4, palette=(curses.COLOR_MAGENTA, curses.COLOR_CYAN, curses.COLOR_YELLOW, curses.COLOR_WHITE)),
        "binary-rain": ThemeConfig(name, "Binary Rain", "1", 0.038, 0.00, 0.06, 0.32, (0.04, 0.08), 0.08, 0.50, 3, palette=(curses.COLOR_GREEN, curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_YELLOW)),
        "wormhole": ThemeConfig(name, "Wormhole", "\u25cb", 0.032, 0.00, 0.14, 0.26, (0.03, 0.06), 0.08, 0.55, 3, palette=(curses.COLOR_MAGENTA, curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE)),
        # ── Industrial ───────────────────────────────────────────
        "liquid-metal": ThemeConfig(name, "Liquid Metal", "\u2022", 0.016, 0.06, 0.52, 0.30, (0.04, 0.08), 0.12, 0.45, 3, palette=(curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_MAGENTA)),
        "factory-floor": ThemeConfig(name, "Factory Floor", "\u25a0", 0.020, 0.08, 0.10, 0.34, (0.04, 0.08), 0.10, 0.50, 3, palette=(curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_MAGENTA)),
        "pipe-hell": ThemeConfig(name, "Pipe Hell", "\u256c", 0.018, 0.03, 0.12, 0.28, (0.03, 0.06), 0.08, 0.60, 3, palette=(curses.COLOR_GREEN, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "oil-slick": ThemeConfig(name, "Oil Slick", "\u25cf", 0.014, 0.04, 0.44, 0.22, (0.03, 0.06), 0.06, 0.48, 3, palette=(curses.COLOR_MAGENTA, curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_YELLOW)),
        # ── Whimsical ────────────────────────────────────────────
        "campfire": ThemeConfig(name, "Campfire", "*", 0.026, 0.06, 0.24, 0.28, (0.03, 0.07), 0.10, 0.45, 3, palette=(curses.COLOR_YELLOW, curses.COLOR_MAGENTA, curses.COLOR_WHITE, curses.COLOR_CYAN)),
        "aquarium": ThemeConfig(name, "Aquarium", "\u25ba", 0.020, 0.03, 0.18, 0.24, (0.03, 0.06), 0.08, 0.40, 2, palette=(curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_GREEN, curses.COLOR_WHITE)),
        "circuit-board": ThemeConfig(name, "Circuit Board", "\u25a3", 0.008, 0.00, 0.04, 0.38, (0.04, 0.08), 0.04, 0.65, 3, palette=(curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_CYAN)),
        "lava-lamp": ThemeConfig(name, "Lava Lamp", "\u25cf", 0.012, 0.02, 0.50, 0.20, (0.02, 0.05), 0.06, 0.40, 2, palette=(curses.COLOR_MAGENTA, curses.COLOR_YELLOW, curses.COLOR_CYAN, curses.COLOR_WHITE)),
        "firefly-field": ThemeConfig(name, "Firefly Field", "\u2727", 0.035, 0.03, 0.10, 0.18, (0.02, 0.04), 0.06, 0.35, 2, palette=(curses.COLOR_YELLOW, curses.COLOR_GREEN, curses.COLOR_WHITE, curses.COLOR_CYAN)),
        # ── Hostile ──────────────────────────────────────────────
        "noxious-fumes": ThemeConfig(name, "Noxious Fumes", "\u25cc", 0.042, 0.06, 0.20, 0.22, (0.03, 0.06), 0.08, 0.40, 3, palette=(curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_CYAN)),
        "maze-runner": ThemeConfig(name, "Maze Runner", "@", 0.004, 0.00, 0.04, 0.30, (0.03, 0.06), 0.04, 0.55, 3, palette=(curses.COLOR_WHITE, curses.COLOR_GREEN, curses.COLOR_CYAN, curses.COLOR_YELLOW)),
        # ── Exotic ───────────────────────────────────────────────
        "neon-rain": ThemeConfig(name, "Neon Rain", "\u25aa", 0.036, 0.12, 0.16, 0.28, (0.04, 0.08), 0.08, 0.50, 3, palette=(curses.COLOR_MAGENTA, curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_WHITE)),
        "volcanic": ThemeConfig(name, "Volcanic", "\u25c9", 0.030, 0.08, 0.28, 0.32, (0.04, 0.08), 0.12, 0.45, 3, palette=(curses.COLOR_YELLOW, curses.COLOR_MAGENTA, curses.COLOR_WHITE, curses.COLOR_CYAN)),
        "crystal-cave": ThemeConfig(name, "Crystal Cave", "\u25c7", 0.012, 0.00, 0.10, 0.24, (0.03, 0.06), 0.08, 0.50, 3, palette=(curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_MAGENTA, curses.COLOR_BLUE)),
        "spider-web": ThemeConfig(name, "Spider Web", "\u25cb", 0.010, 0.01, 0.06, 0.22, (0.02, 0.05), 0.06, 0.55, 2, palette=(curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_YELLOW)),
        "snow-globe": ThemeConfig(name, "Snow Globe", "*", 0.048, 0.08, 0.08, 0.16, (0.02, 0.04), 0.04, 0.35, 2, palette=(curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_YELLOW)),
        # ── Mechanical/Retro ─────────────────────────────────────
        "clockwork": ThemeConfig(name, "Clockwork", "\u2699", 0.014, 0.02, 0.16, 0.28, (0.03, 0.07), 0.08, 0.50, 3, palette=(curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_MAGENTA)),
        "coral-reef": ThemeConfig(name, "Coral Reef", "\u274b", 0.022, 0.04, 0.18, 0.26, (0.03, 0.06), 0.08, 0.50, 3, palette=(curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_MAGENTA, curses.COLOR_WHITE)),
        "ant-colony": ThemeConfig(name, "Ant Colony", "\u2022", 0.016, 0.00, 0.10, 0.36, (0.04, 0.08), 0.08, 0.55, 3, palette=(curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_GREEN)),
        "satellite-orbit": ThemeConfig(name, "Satellite Orbit", "\u25c7", 0.028, 0.00, 0.08, 0.24, (0.03, 0.06), 0.06, 0.50, 3, palette=(curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        # ── Redesigned: Starfall (v2 replaces legacy-starfall) ────────────────
        "starfall":      ThemeConfig(name, "Starfall",     "\u2726", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_MAGENTA)),
        # ── Cosmic New (redesigned v2 — replace old entries) ──────────────────
        "quasar":        ThemeConfig(name, "Quasar",       "\u25c8", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "supernova":     ThemeConfig(name, "Supernova",    "*",      0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_YELLOW, curses.COLOR_MAGENTA, curses.COLOR_WHITE, curses.COLOR_CYAN)),
        "sol":           ThemeConfig(name, "Sol",          "\u25c9", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_MAGENTA)),
        "terra":         ThemeConfig(name, "Terra",        "\u00b7", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_WHITE, curses.COLOR_BLUE)),
        "binary-star":   ThemeConfig(name, "Binary Star",  "\u2605", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        # ── Legacy variants (original implementations, hidden from gallery) ────
        "legacy-starfall":    ThemeConfig(name, "Starfall (Legacy)",    "\u2726", 0.040, 0.00, 0.06, 0.22, (0.03, 0.06), 0.08, 0.55, 3, palette=(curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_YELLOW, curses.COLOR_MAGENTA)),
        "legacy-quasar":      ThemeConfig(name, "Quasar (Legacy)",      "\u25c9", 0.034, 0.00, 0.08, 0.28, (0.03, 0.07), 0.10, 0.50, 3, palette=(curses.COLOR_MAGENTA, curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_CYAN)),
        "legacy-supernova":   ThemeConfig(name, "Supernova (Legacy)",   "*",      0.030, 0.00, 0.14, 0.34, (0.04, 0.08), 0.14, 0.45, 3, palette=(curses.COLOR_YELLOW, curses.COLOR_MAGENTA, curses.COLOR_WHITE, curses.COLOR_CYAN)),
        "legacy-sol":         ThemeConfig(name, "Sol (Legacy)",         "\u25c9", 0.026, 0.02, 0.20, 0.26, (0.03, 0.06), 0.10, 0.50, 3, palette=(curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_MAGENTA, curses.COLOR_CYAN)),
        "legacy-terra":       ThemeConfig(name, "Terra (Legacy)",       "\u00b7", 0.028, 0.02, 0.08, 0.22, (0.02, 0.05), 0.06, 0.50, 3, palette=(curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_GREEN)),
        "legacy-binary-star": ThemeConfig(name, "Binary Star (Legacy)", "\u25c9", 0.032, 0.00, 0.10, 0.24, (0.03, 0.06), 0.08, 0.50, 3, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        # ── ASCII Fields ──────────────────────────────────────────────
        "synaptic-plasma": ThemeConfig(name, "Synaptic Plasma", "\u00b7", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_MAGENTA)),
        "oracle":          ThemeConfig(name, "Oracle", "\u25ce", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_MAGENTA, curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE)),
        "cellular-cortex": ThemeConfig(name, "Cellular Cortex", "\u25c8", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_WHITE, curses.COLOR_MAGENTA)),
        "reaction-field":  ThemeConfig(name, "Reaction Field", "\u00b7", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_CYAN, curses.COLOR_MAGENTA, curses.COLOR_WHITE, curses.COLOR_GREEN)),
        "stellar-weave":   ThemeConfig(name, "Stellar Weave", "\u2726", 0.012, 0.01, 0.05, 0.05, (0.02, 0.05), 0.04, 0.5, 2, palette=(curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_MAGENTA, curses.COLOR_YELLOW)),
        "life-colony":     ThemeConfig(name, "Life Colony", "\u00b7", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_GREEN, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "aurora-bands":    ThemeConfig(name, "Aurora Bands", "~", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_GREEN, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_MAGENTA)),
        "waveform-scope":  ThemeConfig(name, "Waveform Scope", "\u2500", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "lissajous-mind":  ThemeConfig(name, "Lissajous Mind", "\u25c8", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_MAGENTA, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_BLUE)),
        "pulse-matrix":    ThemeConfig(name, "Pulse Matrix", "\u00b7", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_MAGENTA)),
        # ── Extreme Fields ────────────────────────────────────────────
        "fractal-engine":  ThemeConfig(name, "Fractal Engine",   "\u2588", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_MAGENTA)),
        "n-body":          ThemeConfig(name, "N-Body",           "\u25c9", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "standing-waves":  ThemeConfig(name, "Standing Waves",   "\u2592", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_MAGENTA, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_BLUE)),
        # ── Experimental ─────────────────────────────────────────────
        "clifford-attractor": ThemeConfig(name, "Clifford Attractor", "\u00b7", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_MAGENTA, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_BLUE)),
        "barnsley-fern":      ThemeConfig(name, "Barnsley Fern",      ":",     0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_GREEN, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "flow-field":         ThemeConfig(name, "Flow Field",         "\u25cf", 0.0, 0.0, 0.0, 0.0, (0.02, 0.05), 0.0, 0.5, 2, palette=(curses.COLOR_CYAN, curses.COLOR_MAGENTA, curses.COLOR_WHITE, curses.COLOR_BLUE)),
        # ── Hybrid (ASCII field + node graph) ────────────────────────
        "plasma-grid":  ThemeConfig(name, "Plasma Grid",  "+", 0.0, 0.0, 0.10, 0.34, (0.04, 0.08), 0.10, 0.5, 3, palette=(curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_BLUE, curses.COLOR_MAGENTA)),
        "deep-signal":  ThemeConfig(name, "Deep Signal",  "\u25c7", 0.0, 0.0, 0.08, 0.26, (0.03, 0.06), 0.08, 0.5, 2, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_MAGENTA)),
        # ── Legacy: Originals (original node-based implementations) ──
        "legacy-neural-sky":    ThemeConfig(name, "Neural Sky (Legacy)",    "*",      0.030, 0.10, 0.40, 0.32, (0.04, 0.08), 0.10, 0.4, 3, palette=(curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_MAGENTA)),
        "legacy-storm-core":    ThemeConfig(name, "Storm Core (Legacy)",    "x",      0.024, 0.18, 0.52, 0.42, (0.06, 0.10), 0.12, 0.35, 3, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "legacy-moonwire":      ThemeConfig(name, "Moonwire (Legacy)",      "\u2022", 0.026, 0.04, 0.16, 0.20, (0.02, 0.05), 0.07, 0.48, 2, palette=(curses.COLOR_WHITE, curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_MAGENTA)),
        "legacy-rootsong":      ThemeConfig(name, "Rootsong (Legacy)",      ":",      0.014, 0.02, 0.14, 0.28, (0.03, 0.06), 0.10, 0.66, 2, palette=(curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_CYAN)),
        "legacy-stormglass":    ThemeConfig(name, "Stormglass (Legacy)",    "+",      0.032, 0.08, 0.30, 0.34, (0.04, 0.08), 0.12, 0.58, 3, palette=(curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_BLUE, curses.COLOR_MAGENTA)),
        "legacy-spiral-galaxy": ThemeConfig(name, "Spiral Galaxy (Legacy)", "\u2726", 0.040, 0.00, 0.10, 0.26, (0.02, 0.05), 0.07, 0.62, 3, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_MAGENTA)),
        "legacy-black-hole":    ThemeConfig(name, "Black Hole (Legacy)",    "\u00b7", 0.036, 0.00, 0.06, 0.18, (0.02, 0.04), 0.05, 0.74, 2, palette=(curses.COLOR_BLUE, curses.COLOR_MAGENTA, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        # ── Legacy: Nature ────────────────────────────────────────────
        "legacy-deep-abyss":       ThemeConfig(name, "Deep Abyss (Legacy)",       "\u2727", 0.018, 0.02, 0.20, 0.22, (0.03, 0.06), 0.08, 0.50, 3, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_GREEN)),
        "legacy-storm-sea":        ThemeConfig(name, "Storm Sea (Legacy)",        "~",      0.028, 0.15, 0.48, 0.36, (0.05, 0.09), 0.10, 0.40, 3, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "legacy-dark-forest":      ThemeConfig(name, "Dark Forest (Legacy)",      "\u25c9", 0.022, 0.04, 0.14, 0.26, (0.03, 0.06), 0.08, 0.55, 3, palette=(curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_CYAN)),
        "legacy-mountain-stars":   ThemeConfig(name, "Mountain Stars (Legacy)",   "\u2726", 0.045, 0.00, 0.06, 0.20, (0.02, 0.04), 0.06, 0.60, 3, palette=(curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_MAGENTA)),
        "legacy-beach-lighthouse": ThemeConfig(name, "Beach Lighthouse (Legacy)", "\u00b7", 0.020, 0.03, 0.12, 0.18, (0.02, 0.04), 0.06, 0.45, 2, palette=(curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW, curses.COLOR_BLUE)),
    }
    return configs[name]
