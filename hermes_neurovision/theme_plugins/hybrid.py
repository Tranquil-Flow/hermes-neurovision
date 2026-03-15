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

from hermes_neurovision.plugin import ThemePlugin, Reaction, ReactiveElement, SpecialEffect
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


    # ── v0.2: Emergent system ─────────────────────────────────────────────────

    def wave_config(self):
        return {"speed": 0.4, "damping": 0.97}

    def emergent_layer(self):
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────

    def glow_radius(self):
        return 1

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────

    def intensity_curve(self, raw):
        return raw ** 0.8

    # ── v0.2: Reactive system ─────────────────────────────────────────────────

    def react(self, event_kind, data):
        cx, cy = 0.5, 0.5
        rng = __import__("random")
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.9,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "llm_start":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.8,
                            origin=(cx, cy), color_key="accent", duration=3.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.4,
                            origin=(rng.random(), rng.random()),
                            color_key="bright", duration=0.5)
        if event_kind == "tool_call":
            # At grid node position (random 0.25/0.5/0.75)
            pos = rng.choice([0.25, 0.5, 0.75])
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.65,
                            origin=(pos, pos), color_key="accent", duration=1.5)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.75,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "error":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                            origin=(rng.random(), rng.random()),
                            color_key="warning", duration=2.0)
        if event_kind == "context_pressure":
            return Reaction(element=ReactiveElement.GAUGE,
                            intensity=data.get("level", 0.5),
                            origin=(cx, cy), color_key="accent", duration=2.0)
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────

    def palette_shift(self, trigger_effect, intensity, base_palette):
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────

    def special_effects(self):
        return [SpecialEffect(name="grid-surge", trigger_kinds=["burst"],
                              min_intensity=0.3, cooldown=5.0, duration=2.5)]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        if special_name != "grid-surge":
            return
        w, h = state.width, state.height
        cp_bright = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        cp_accent = curses.color_pair(color_pairs.get("accent", 0))
        # Flash all grid nodes with bright surging signal
        cols = [int(w * 0.25), int(w * 0.50), int(w * 0.75)]
        rows = [int(h * 0.30), int(h * 0.50), int(h * 0.70)]
        surge_r = int(min(w, h) * 0.3 * math.sin(progress * math.pi))
        for row in rows:
            for col in cols:
                for r in range(1, max(2, surge_r), 2):
                    for a_deg in range(0, 360, 30):
                        a = math.radians(a_deg)
                        px = col + int(r * math.cos(a) * 2)
                        py = row + int(r * math.sin(a))
                        if 1 <= py < h - 1 and 0 <= px < w - 1:
                            try:
                                stdscr.addstr(py, px, "+",
                                              cp_bright if r < surge_r // 2 else cp_accent)
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


    # ── v0.2: Emergent system ─────────────────────────────────────────────────

    def neural_field_config(self):
        return {"threshold": 2, "fire_duration": 2, "refractory": 6}

    def emergent_layer(self):
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────

    def glow_radius(self):
        return 1

    def echo_decay(self):
        return 4

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────

    def intensity_curve(self, raw):
        return raw ** 0.4

    # ── v0.2: Reactive system ─────────────────────────────────────────────────

    def react(self, event_kind, data):
        cx, cy = 0.5, 0.5
        rng = __import__("random")
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.9,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "llm_start":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.8,
                            origin=(cx, cy), color_key="accent", duration=3.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.4,
                            origin=(rng.random(), rng.random()),
                            color_key="bright", duration=0.5)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.6,
                            origin=(rng.random(), rng.random()),
                            color_key="accent", duration=1.5)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.75,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "error":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                            origin=(rng.random(), rng.random()),
                            color_key="warning", duration=2.0)
        if event_kind == "mcp_connected":
            return Reaction(element=ReactiveElement.CONSTELLATION, intensity=0.8,
                            origin=(cx, cy), color_key="bright", duration=3.0)
        if event_kind == "provider_health":
            return Reaction(element=ReactiveElement.CONSTELLATION, intensity=0.6,
                            origin=(cx, cy), color_key="accent", duration=2.5)
        if event_kind == "cron_tick":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.5,
                            origin=(rng.random(), rng.random()),
                            color_key="soft", duration=2.0)
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────

    def palette_shift(self, trigger_effect, intensity, base_palette):
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────

    def special_effects(self):
        return [SpecialEffect(name="signal-contact", trigger_kinds=["burst"],
                              min_intensity=0.2, cooldown=5.0, duration=3.0)]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        if special_name != "signal-contact":
            return
        w, h = state.width, state.height
        cp_bright = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        cp_accent = curses.color_pair(color_pairs.get("accent", 0))
        # Constellation flash — connect all 6 nodes with bright lines
        cx2, cy2 = w / 2.0, h / 2.0
        r_x, r_y = w * 0.28, h * 0.28
        nodes = [(cx2 + math.cos(math.tau * k / 6) * r_x,
                  cy2 + math.sin(math.tau * k / 6) * r_y)
                 for k in range(6)]
        flash = math.sin(progress * math.pi)
        if flash > 0.3:
            for i, (nx, ny) in enumerate(nodes):
                try:
                    stdscr.addstr(int(ny), int(nx), "◈", cp_bright)
                except curses.error:
                    pass
                # Connect to next node
                nx2, ny2 = nodes[(i + 1) % 6]
                steps = max(abs(int(nx2) - int(nx)), abs(int(ny2) - int(ny)))
                for s in range(1, max(1, steps)):
                    t = s / max(steps, 1)
                    px = int(nx + (nx2 - nx) * t)
                    py = int(ny + (ny2 - ny) * t)
                    if 1 <= py < h - 1 and 0 <= px < w - 1:
                        try:
                            stdscr.addstr(py, px, "·", cp_accent)
                        except curses.error:
                            pass

    # ── v0.2: Ambient tick ────────────────────────────────────────────────────

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        pass  # slow scan signal pulses continuously via draw_background


register(PlasmaGridPlugin())
register(DeepSignalPlugin())
