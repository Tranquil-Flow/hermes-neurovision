"""Tuner — live parameter sliders and element toggles."""

from __future__ import annotations

import curses
from dataclasses import dataclass
from typing import List, Tuple


# ── Slider and toggle metadata ────────────────────────────────────────────────

# (label, attr_name, min, max, step)
_SLIDERS: List[Tuple[str, str, float, float, float]] = [
    ("Burst scale",       "burst_scale",       0.0, 3.0, 0.1),
    ("Packet rate",       "packet_rate_mult",  0.0, 3.0, 0.1),
    ("Pulse rate",        "pulse_rate_mult",   0.0, 3.0, 0.1),
    ("Particle density",  "particle_density",  0.0, 3.0, 0.1),
    ("Event sensitivity", "event_sensitivity", 0.0, 3.0, 0.1),
    ("Animation speed",   "animation_speed",   0.1, 5.0, 0.1),
]

# (label, attr_name)
_TOGGLES: List[Tuple[str, str]] = [
    ("packets",    "show_packets"),
    ("particles",  "show_particles"),
    ("pulses",     "show_pulses"),
    ("stars",      "show_stars"),
    ("background", "show_background"),
    ("nodes",      "show_nodes"),
    ("flash",      "show_flash"),
    ("spawn",      "show_spawn_node"),
]


# ── TuneSettings ──────────────────────────────────────────────────────────────

@dataclass
class TuneSettings:
    # Sliders
    burst_scale: float = 1.0
    packet_rate_mult: float = 1.0
    pulse_rate_mult: float = 1.0
    particle_density: float = 1.0
    event_sensitivity: float = 1.0
    animation_speed: float = 1.0

    # Element toggles — gate both passive ambient AND event-driven activity
    show_packets: bool = True
    show_particles: bool = True
    show_pulses: bool = True
    show_stars: bool = True
    show_background: bool = True
    show_nodes: bool = True
    show_flash: bool = True
    show_spawn_node: bool = True

    def is_default(self) -> bool:
        return (
            self.burst_scale == 1.0
            and self.packet_rate_mult == 1.0
            and self.pulse_rate_mult == 1.0
            and self.particle_density == 1.0
            and self.event_sensitivity == 1.0
            and self.animation_speed == 1.0
            and self.show_packets
            and self.show_particles
            and self.show_pulses
            and self.show_stars
            and self.show_background
            and self.show_nodes
            and self.show_flash
            and self.show_spawn_node
        )

    def reset(self) -> None:
        self.burst_scale = 1.0
        self.packet_rate_mult = 1.0
        self.pulse_rate_mult = 1.0
        self.particle_density = 1.0
        self.event_sensitivity = 1.0
        self.animation_speed = 1.0
        self.show_packets = True
        self.show_particles = True
        self.show_pulses = True
        self.show_stars = True
        self.show_background = True
        self.show_nodes = True
        self.show_flash = True
        self.show_spawn_node = True


# ── TuneOverlay ───────────────────────────────────────────────────────────────

class TuneOverlay:
    """Centered modal overlay with slider + toggle rows.

    Navigation: ↑↓ move through rows (sliders first, then toggles).
    Sliders: ←→ decrease/increase value.
    Toggles: ← or → flips the boolean.
    't' closes. 'r' resets all.
    """

    slider_count: int = len(_SLIDERS)
    toggle_count: int = len(_TOGGLES)
    row_count: int = len(_SLIDERS) + len(_TOGGLES)

    def __init__(self, settings: TuneSettings) -> None:
        self._settings = settings
        self.active: bool = False
        self.selected_index: int = 0

    @property
    def current_settings(self) -> TuneSettings:
        return self._settings

    # ── key handling ──────────────────────────────────────────────────────────

    def handle_key(self, ch: int) -> bool:
        """Process a keypress. Returns True if consumed."""
        if ch == curses.KEY_DOWN:
            self.selected_index = (self.selected_index + 1) % self.row_count
            return True

        if ch == curses.KEY_UP:
            self.selected_index = (self.selected_index - 1) % self.row_count
            return True

        if ch in (curses.KEY_LEFT, curses.KEY_RIGHT):
            if self.selected_index < self.slider_count:
                self._adjust_slider(self.selected_index, ch == curses.KEY_RIGHT)
            else:
                self._flip_toggle(self.selected_index - self.slider_count)
            return True

        if ch == ord('r'):
            self._settings.reset()
            return True

        if ch == ord('t'):
            self.active = False
            return True

        return False

    def _adjust_slider(self, idx: int, increase: bool) -> None:
        label, attr, lo, hi, step = _SLIDERS[idx]
        val = getattr(self._settings, attr)
        val = val + step if increase else val - step
        val = round(max(lo, min(hi, val)), 10)
        setattr(self._settings, attr, val)

    def _flip_toggle(self, idx: int) -> None:
        _, attr = _TOGGLES[idx]
        setattr(self._settings, attr, not getattr(self._settings, attr))

    # ── drawing ───────────────────────────────────────────────────────────────

    def draw(self, stdscr, color_pairs: dict) -> None:
        """Draw the tuner modal centered on stdscr."""
        if not self.active:
            return

        h, w = stdscr.getmaxyx()
        modal_w = min(38, w - 4)
        # Height: 2 header + 1 slider-section + 6*2 slider rows + 1 toggle-section
        #         + 8 toggle rows + 1 footer + 2 border = ~32 max, clamp to screen
        modal_h = min(2 + 1 + self.slider_count * 2 + 1 + self.toggle_count + 3, h - 2)
        top = max(0, (h - modal_h) // 2)
        left = max(0, (w - modal_w) // 2)

        bright = color_pairs.get("bright", 0)
        accent = color_pairs.get("accent", 0)
        soft = color_pairs.get("soft", 0)

        def put(y, x, text, attr=0):
            try:
                stdscr.addstr(top + y, left + x, text[:modal_w - 2], attr)
            except curses.error:
                pass

        # Border
        for row in range(modal_h):
            try:
                stdscr.addstr(top + row, left, " " * modal_w, soft)
            except curses.error:
                pass

        put(0, 1, "─" * (modal_w - 2), soft)
        put(0, (modal_w - 8) // 2, " TUNER ", bright | curses.A_BOLD)
        put(modal_h - 1, 1, "─" * (modal_w - 2), soft)

        row = 1
        put(row, 1, "── SLIDERS " + "─" * (modal_w - 14), accent)
        row += 1

        for i, (label, attr, lo, hi, step) in enumerate(_SLIDERS):
            val = getattr(self._settings, attr)
            is_sel = (self.selected_index == i)
            prefix = "▶ " if is_sel else "  "
            label_attr = bright | curses.A_BOLD if is_sel else soft
            put(row, 1, f"{prefix}{label:<20} {val:.1f}", label_attr)
            row += 1
            # Slider bar
            bar_w = modal_w - 6
            filled = int((val - lo) / max(hi - lo, 0.001) * bar_w)
            bar = "═" * filled + "●" + "═" * (bar_w - filled)
            put(row, 3, f"[{bar[:bar_w]}]", accent if is_sel else soft)
            row += 1

        if row < modal_h - 2:
            put(row, 1, "── ELEMENTS " + "─" * (modal_w - 15), accent)
            row += 1

        for i, (label, attr) in enumerate(_TOGGLES):
            if row >= modal_h - 1:
                break
            is_sel = (self.selected_index == self.slider_count + i)
            val = getattr(self._settings, attr)
            prefix = "▶ " if is_sel else "  "
            tag = "[ON] " if val else "[  ] "
            tag_attr = bright | curses.A_BOLD if val else soft
            label_attr = bright | curses.A_BOLD if is_sel else soft
            put(row, 1, prefix, label_attr)
            put(row, 3, tag, tag_attr)
            put(row, 8, label, label_attr)
            row += 1

        if row < modal_h - 1:
            put(row, 1, "↑↓ select  ←→ adjust/toggle  t close  r reset", soft)
