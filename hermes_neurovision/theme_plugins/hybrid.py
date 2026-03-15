"""Hybrid themes — combine ASCII field background with node-based event storytelling.

These themes use both engines simultaneously:
  draw_background()  renders an ASCII field BEFORE nodes (backdrop layer)
  build_nodes()      returns real nodes that receive packets/pulses on agent events
  draw_extras()      optional foreground effects AFTER particles

The result: a rich generative field that pulses with agent intensity, with
traveling packets and expanding pulses making individual tool calls legible.
"""

from __future__ import annotations

import curses
import math
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


# ── Plasma Grid ───────────────────────────────────────────────────────────────

class PlasmaGridPlugin(ThemePlugin):
    """Sine-wave interference plasma backdrop + a node grid wired for event packets.

    Background: two-frequency sine interference pattern creates a plasma moiré
    that brightens and accelerates with agent intensity. At idle the field is a
    dim, slow ripple. Under load it flares to bright cyan/white.

    Nodes: 3×3 grid — packets travel grid edges when tool calls fire, pulses
    expand from nodes on message events. The grid stays visible because the
    background renders at moderate density rather than full coverage.
    """

    name = "plasma-grid"

    _CHARS = " ·.:+*#@"

    def build_nodes(self, w: int, h: int, cx: float, cy: float,
                    count: int, rng) -> List[Tuple[float, float]]:
        """3×3 evenly spaced grid."""
        cols = [w * 0.25, w * 0.50, w * 0.75]
        rows = [h * 0.30, h * 0.50, h * 0.70]
        return [(x, y) for y in rows for x in cols]

    def edge_keep_count(self) -> int:
        return 2

    def node_glyph(self, idx: int, intensity: float, total: int) -> str:
        return "+" if intensity > 0.72 else "·"

    def node_color_key(self, idx: int, intensity: float, total: int) -> str:
        return "bright" if intensity > 0.65 else "accent"

    def packet_color_key(self) -> str:
        return "bright"

    def pulse_color_key(self) -> str:
        return "accent"

    def draw_background(self, stdscr, state, color_pairs: dict) -> None:
        """Interference plasma field — drawn before nodes so grid floats on top."""
        h, w = stdscr.getmaxyx()
        f = state.frame
        intensity = state.intensity_multiplier
        chars = self._CHARS
        nchars = len(chars)
        cp_base = curses.color_pair(color_pairs.get("base", 0))
        cp_soft = curses.color_pair(color_pairs.get("soft", 0))
        cp_accent = curses.color_pair(color_pairs.get("accent", 0))

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                # Two-frequency interference + radial wave from center
                v = (math.sin(x / 8.0 + f * 0.04) * math.sin(y / 5.0 + f * 0.03)
                     + math.sin(math.sqrt((x - w * 0.5) ** 2 + (y - h * 0.5) ** 2) / 7.0 - f * 0.05))
                # Normalize -2..2 → 0..1, then scale by intensity
                v_norm = (v + 2.0) / 4.0 * intensity
                ci = min(nchars - 1, int(v_norm * nchars))
                char = chars[ci]
                if char == " ":
                    continue
                attr = cp_base if v_norm < 0.3 else (cp_soft if v_norm < 0.6 else cp_accent)
                try:
                    stdscr.addstr(y, x, char, attr)
                except curses.error:
                    pass


# ── Deep Signal ───────────────────────────────────────────────────────────────

class DeepSignalPlugin(ThemePlugin):
    """Slow drifting space-noise backdrop + a hexagonal signal constellation.

    Background: low-frequency sine drift gives a dark, atmospheric field that
    evokes deep space or a quiet radio telescope scan. At low agent activity it
    is nearly invisible — a faint texture. Under load it blooms to fill the
    terminal, making the constellation of nodes feel like it's being lit up.

    Nodes: 6 nodes in a ring — a hexagonal signal array. When the agent fires
    tool calls, packets radiate along the constellation edges. The simplicity of
    the layout makes each packet visually distinctive against the dim field.
    """

    name = "deep-signal"

    _CHARS = " ·:+"

    def build_nodes(self, w: int, h: int, cx: float, cy: float,
                    count: int, rng) -> List[Tuple[float, float]]:
        """Hexagonal ring of 6 signal nodes."""
        r_x = w * 0.28
        r_y = h * 0.28
        return [
            (cx + math.cos(math.tau * k / 6) * r_x,
             cy + math.sin(math.tau * k / 6) * r_y)
            for k in range(6)
        ]

    def edge_keep_count(self) -> int:
        return 2

    def node_glyph(self, idx: int, intensity: float, total: int) -> str:
        return "◈" if intensity > 0.72 else "◇"

    def node_color_key(self, idx: int, intensity: float, total: int) -> str:
        return "accent" if intensity > 0.65 else "soft"

    def packet_color_key(self) -> str:
        return "accent"

    def pulse_color_key(self) -> str:
        return "soft"

    def pulse_style(self) -> str:
        return "ripple"

    def draw_background(self, stdscr, state, color_pairs: dict) -> None:
        """Slow drifting noise field — atmospheric backdrop for the signal array."""
        h, w = stdscr.getmaxyx()
        f = state.frame
        intensity = state.intensity_multiplier
        chars = self._CHARS
        nchars = len(chars)
        cp_base = curses.color_pair(color_pairs.get("base", 0)) | curses.A_DIM

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                # Slow overlapping sine drift — very low frequency, soft movement
                v = (math.sin((x + f * 0.3) / 16.0) * math.cos((y + f * 0.2) / 13.0)
                     + math.sin((x * 0.6 - y * 0.4) / 20.0 + f * 0.015))
                v_norm = (v + 2.0) / 4.0 * intensity
                ci = min(nchars - 1, int(v_norm * nchars))
                char = chars[ci]
                if char == " ":
                    continue
                try:
                    stdscr.addstr(y, x, char, cp_base)
                except curses.error:
                    pass


register(PlasmaGridPlugin())
register(DeepSignalPlugin())
