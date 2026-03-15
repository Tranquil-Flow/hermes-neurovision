"""Curses renderer for Hermes Vision."""

from __future__ import annotations

import curses
import math
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Iterable, Optional, Tuple

from hermes_neurovision.themes import ThemeConfig, STAR_CHARS, PULSE_CHARS

if TYPE_CHECKING:
    from hermes_neurovision.scene import ThemeState

# ---------------------------------------------------------------------------
# Buffer primitives
# ---------------------------------------------------------------------------

@dataclass
class Cell:
    char: str = " "
    color_pair: int = 0
    attr: int = 0
    age: int = 0  # for decay (future phases)


class FrameBuffer:
    """Off-screen cell buffer for compositing before blit."""

    def __init__(self, w: int, h: int) -> None:
        self.w = w
        self.h = h
        self.cells = [[Cell() for _ in range(w)] for _ in range(h)]

    def put(self, x: int, y: int, char: str, color_pair: int, attr: int = 0) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            cell = self.cells[y][x]
            cell.char = char
            cell.color_pair = color_pair
            cell.attr = attr
            cell.age = 0  # reset age on write

    def get(self, x: int, y: int) -> Cell:
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.cells[y][x]
        return Cell()

    def clear(self) -> None:
        for row in self.cells:
            for cell in row:
                cell.char = " "
                cell.color_pair = 0
                cell.attr = 0
                cell.age = 0

    def blit_to_screen(self, stdscr) -> None:
        for y in range(self.h):
            for x in range(self.w):
                cell = self.cells[y][x]
                if cell.char != " " or cell.attr != 0:
                    try:
                        stdscr.addstr(y, x, cell.char, cell.color_pair | cell.attr)
                    except curses.error:
                        pass


class _BufferShim:
    """Wraps FrameBuffer with curses-compatible addstr()/getmaxyx() for plugin hooks."""

    # curses.A_COLOR mask — use the constant if available, fallback to standard.
    _A_COLOR = getattr(curses, "A_COLOR", 0xFF00)

    def __init__(self, buf: FrameBuffer) -> None:
        self._buf = buf

    def addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        pair = attr & self._A_COLOR
        style = attr & ~self._A_COLOR
        for i, ch in enumerate(text):
            self._buf.put(x + i, y, ch, pair, style)

    def getmaxyx(self) -> Tuple[int, int]:
        return (self._buf.h, self._buf.w)


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

class Renderer:
    def __init__(self, stdscr: "curses._CursesWindow") -> None:
        self.stdscr = stdscr
        self.color_pairs = self._init_colors()
        self._current_palette: Optional[Tuple[int, int, int, int]] = None
        self._buffer: Optional[FrameBuffer] = None

    def _init_colors(self) -> Dict[str, int]:
        pairs = {
            "base": 0,
            "soft": 0,
            "bright": 0,
            "accent": 0,
            "warning": 0,
        }
        if not curses.has_colors():
            return pairs

        curses.start_color()
        curses.use_default_colors()
        palette = [
            (1, curses.COLOR_BLUE, -1),
            (2, curses.COLOR_CYAN, -1),
            (3, curses.COLOR_WHITE, -1),
            (4, curses.COLOR_MAGENTA, -1),
            (5, curses.COLOR_YELLOW, -1),
        ]
        for pair_id, fg, bg in palette:
            try:
                curses.init_pair(pair_id, fg, bg)
            except curses.error:
                pass
        pairs.update({"base": 1, "soft": 2, "bright": 3, "accent": 4, "warning": 5})
        return pairs

    def _apply_palette(self, palette: Tuple[int, int, int, int]) -> None:
        """Re-initialize color pairs 1-4 from theme palette. Pair 5 (warning) stays fixed."""
        if palette == self._current_palette:
            return
        self._current_palette = palette
        if not curses.has_colors():
            return
        for idx, color in enumerate(palette):
            try:
                curses.init_pair(idx + 1, color, -1)
            except curses.error:
                pass

    def draw(self, state: "ThemeState", gallery_index: int, gallery_total: int,
             end_time: Optional[float], hide_hud: bool = False) -> None:
        stdscr = self.stdscr
        h, w = stdscr.getmaxyx()
        state.resize(w, h)
        self._apply_palette(state.config.palette)

        # Create / resize buffer
        if self._buffer is None or self._buffer.w != w or self._buffer.h != h:
            self._buffer = FrameBuffer(w, h)
        else:
            self._buffer.clear()

        # Build buffer --------------------------------------------------
        tune = getattr(state, "tune", None)
        if not tune or tune.show_stars:
            self._draw_stars(state)
        shim = _BufferShim(self._buffer)
        if not tune or tune.show_background:
            state.plugin.draw_background(shim, state, self.color_pairs)
        if not tune or tune.show_nodes:
            self._draw_edges(state)
        self._draw_pulses(state)
        if not tune or tune.show_nodes:
            self._draw_nodes(state)
        self._draw_packets(state)
        self._draw_particles(state)
        if not tune or tune.show_background:
            state.plugin.draw_extras(shim, state, self.color_pairs)

        # Blit buffer → screen -----------------------------------------
        stdscr.erase()
        self._buffer.blit_to_screen(stdscr)

        # HUD overlays (directly on stdscr, NOT buffered) ---------------
        if hide_hud:
            self._draw_hide_hint(h, w)
        else:
            self._draw_overlay(state, gallery_index, gallery_total, end_time)
        stdscr.refresh()

    # ── HUD (direct to stdscr) ────────────────────────────────────────

    def _draw_hide_hint(self, h: int, w: int) -> None:
        """Draw minimal unhide reminder in bottom-right corner."""
        hint = " [h] show HUD "
        try:
            self.stdscr.addstr(
                h - 1, max(0, w - len(hint) - 1), hint,
                curses.color_pair(self.color_pairs["soft"]) | curses.A_DIM
            )
        except curses.error:
            pass

    def _draw_overlay(self, state: "ThemeState", gallery_index: int, gallery_total: int, end_time: Optional[float]) -> None:
        title = f" Hermes Neurovisualizer // {state.config.name} "
        from hermes_neurovision import __version__
        version = f"v{__version__}"
        footer = " q quit  n next  p prev  space pause "
        if gallery_total > 1:
            footer = f" theme {gallery_index + 1}/{gallery_total} |" + footer
        if end_time is not None:
            remaining = max(0.0, end_time - time.time())
            footer += f" | auto-exit {remaining:0.1f}s "

        # Add version to footer
        footer += f" | {version} "

        try:
            self.stdscr.addstr(0, 1, title[: max(0, state.width - 2)], curses.color_pair(self.color_pairs["bright"]) | curses.A_BOLD)
        except curses.error:
            pass
        try:
            self.stdscr.addstr(state.height - 1, 1, footer[: max(0, state.width - 2)], curses.color_pair(self.color_pairs["soft"]))
        except curses.error:
            pass

    # ── Buffered draw methods ─────────────────────────────────────────

    def _draw_stars(self, state: "ThemeState") -> None:
        plugin = state.plugin
        buf = self._buffer
        for x, y, brightness, char_idx in state.stars:
            custom_glyph = plugin.star_glyph(brightness, int(char_idx))
            glyph = custom_glyph if custom_glyph is not None else STAR_CHARS[min(len(STAR_CHARS) - 1, int(char_idx))]
            cp = curses.color_pair(self.color_pairs["base"])
            attr = curses.A_DIM
            if brightness >= 0.8:
                cp = curses.color_pair(self.color_pairs["soft"])
                attr = 0
            buf.put(int(x), int(y), glyph, cp, attr)

    def _draw_edges(self, state: "ThemeState") -> None:
        plugin = state.plugin
        buf = self._buffer
        for idx_a, idx_b in state.edges:
            # Bounds check to prevent IndexError
            if idx_a >= len(state.nodes) or idx_b >= len(state.nodes):
                continue
            ax, ay = self._node_position(state, idx_a)
            bx, by = self._node_position(state, idx_b)
            dx = bx - ax
            dy = by - ay
            steps = max(abs(int(dx)), abs(int(dy)), 1)
            for step in range(1, steps):
                t = step / steps
                x = int(round(ax + dx * t))
                y = int(round(ay + dy * t))
                custom_glyph = plugin.edge_glyph(dx, dy)
                glyph = custom_glyph if custom_glyph is not None else self._default_edge_glyph(dx, dy)
                color_key = plugin.edge_color_key(step, idx_a, state.frame)
                cp = curses.color_pair(self.color_pairs[color_key])
                style = curses.A_DIM if color_key == "base" else 0
                buf.put(x, y, glyph, cp, style)

    def _draw_nodes(self, state: "ThemeState") -> None:
        plugin = state.plugin
        buf = self._buffer
        total = len(state.nodes)
        for idx, _ in enumerate(state.nodes):
            x, y = self._node_position(state, idx)
            intensity = 0.5 + 0.5 * math.sin(state.frame * 0.12 + idx * 0.6)
            glyph = plugin.node_glyph(idx, intensity, total)
            color_key = plugin.node_color_key(idx, intensity, total)
            cp = curses.color_pair(self.color_pairs[color_key])
            buf.put(x, y, glyph, cp)

    def _draw_packets(self, state: "ThemeState") -> None:
        plugin = state.plugin
        buf = self._buffer
        color_key = plugin.packet_color_key()
        for packet in state.packets:
            # Bounds check to prevent IndexError
            if packet.edge[0] >= len(state.nodes) or packet.edge[1] >= len(state.nodes):
                continue
            ax, ay = self._node_position(state, packet.edge[0])
            bx, by = self._node_position(state, packet.edge[1])
            x = int(round(ax + (bx - ax) * packet.progress))
            y = int(round(ay + (by - ay) * packet.progress))
            cp = curses.color_pair(self.color_pairs[color_key])
            buf.put(x, y, packet.glyph, cp, curses.A_BOLD)

    def _draw_particles(self, state: "ThemeState") -> None:
        plugin = state.plugin
        buf = self._buffer
        for particle in state.particles:
            x = int(round(particle.x))
            y = int(round(particle.y))
            if not (0 <= x < state.width and 0 <= y < state.height):
                continue
            color_key = plugin.particle_color_key(particle.age_ratio)
            cp = curses.color_pair(self.color_pairs[color_key])
            style = curses.A_DIM if color_key in ("soft", "base") else 0
            buf.put(x, y, particle.char, cp, style)

    def _draw_pulses(self, state: "ThemeState") -> None:
        plugin = state.plugin
        buf = self._buffer
        color_key = plugin.pulse_color_key()
        style_name = plugin.pulse_style()
        for x, y, radius in state.pulses:
            if style_name == "rays":
                points = self._ray_points(x, y, radius, state.frame)
            elif style_name == "spoked":
                points = self._spoked_points(x, y, radius, state.frame)
            elif style_name == "ripple":
                points = self._ripple_points(x, y, radius, state.frame)
            elif style_name == "cloud":
                points = self._cloud_points(x, y, radius, state.frame)
            elif style_name == "diamond":
                points = self._diamond_points(x, y, radius)
            else:
                points = self._ring_points(x, y, radius)
            cp = curses.color_pair(self.color_pairs[color_key])
            style = curses.A_DIM if color_key in ("soft", "base") else 0
            for px, py, glyph in points:
                buf.put(px, py, glyph, cp, style)

    # ── Helpers (unchanged) ───────────────────────────────────────────

    def _node_position(self, state: "ThemeState", idx: int) -> Tuple[int, int]:
        x, y = state.nodes[idx]
        jitter = state.config.node_jitter

        # Check plugin for custom position adjustment
        custom = state.plugin.node_position_adjust(x, y, idx, state.frame, state.width, state.height)
        if custom is not None:
            xf, yf = custom
        else:
            xf = x + math.sin(state.frame * 0.05 + idx * 0.9) * jitter
            yf = y + math.cos(state.frame * 0.04 + idx * 1.1) * jitter * 0.6

        return int(max(1, min(state.width - 2, round(xf)))), int(max(1, min(state.height - 2, round(yf))))

    @staticmethod
    def _default_edge_glyph(dx: float, dy: float) -> str:
        if abs(dy) < abs(dx) * 0.35:
            return "\u2500"
        if abs(dx) < abs(dy) * 0.45:
            return "\u2502"
        return "\u2571" if dx * dy < 0 else "\u2572"

    @staticmethod
    def _ring_points(cx: float, cy: float, radius: float) -> Iterable[Tuple[int, int, str]]:
        if radius < 1.2:
            yield int(round(cx)), int(round(cy)), PULSE_CHARS[2]
            return
        steps = max(8, int(radius * 8))
        glyph = PULSE_CHARS[min(len(PULSE_CHARS) - 1, int(radius) % len(PULSE_CHARS))]
        for step in range(steps):
            angle = math.tau * step / steps
            x = int(round(cx + math.cos(angle) * radius * 2.0))
            y = int(round(cy + math.sin(angle) * radius))
            yield x, y, glyph

    @staticmethod
    def _ray_points(cx: float, cy: float, radius: float, frame: int) -> Iterable[Tuple[int, int, str]]:
        """Rays of light radiating outward — lines from center."""
        ray_count = 8
        ray_chars = "\u2500\u2502\u2571\u2572\u2500\u2502\u2571\u2572"
        for i in range(ray_count):
            angle = math.tau * i / ray_count + frame * 0.02
            for d in range(1, int(radius) + 1):
                x = int(round(cx + math.cos(angle) * d * 2.0))
                y = int(round(cy + math.sin(angle) * d))
                glyph = ray_chars[i % len(ray_chars)]
                yield x, y, glyph

    @staticmethod
    def _spoked_points(cx: float, cy: float, radius: float, frame: int) -> Iterable[Tuple[int, int, str]]:
        """Spoked burst — only some directions emit, rotating over time."""
        spoke_count = 5
        gap = math.tau / spoke_count
        base_angle = frame * 0.04
        for i in range(spoke_count):
            angle = base_angle + i * gap
            for d in range(1, int(radius) + 1):
                x = int(round(cx + math.cos(angle) * d * 2.0))
                y = int(round(cy + math.sin(angle) * d))
                glyph = "*" if d < radius * 0.5 else "\u00b7"
                yield x, y, glyph

    @staticmethod
    def _ripple_points(cx: float, cy: float, radius: float, frame: int) -> Iterable[Tuple[int, int, str]]:
        """Gentle concentric ripples — multiple fading rings."""
        for ring in range(3):
            r = radius - ring * 1.5
            if r < 0.5:
                continue
            steps = max(6, int(r * 6))
            glyph = "\u00b7" if ring > 0 else "."
            if ring == 0:
                glyph = PULSE_CHARS[min(len(PULSE_CHARS) - 1, int(r) % len(PULSE_CHARS))]
            for step in range(steps):
                angle = math.tau * step / steps
                x = int(round(cx + math.cos(angle) * r * 2.0))
                y = int(round(cy + math.sin(angle) * r))
                yield x, y, glyph

    @staticmethod
    def _cloud_points(cx: float, cy: float, radius: float, frame: int) -> Iterable[Tuple[int, int, str]]:
        """Staggered cloudy effect — wobbly, organic expansion."""
        steps = max(10, int(radius * 10))
        cloud_chars = "\u2591\u2592\u2593\u2591\u00b7."
        for step in range(steps):
            angle = math.tau * step / steps
            wobble = 1.0 + 0.3 * math.sin(angle * 3 + frame * 0.1)
            r = radius * wobble
            x = int(round(cx + math.cos(angle) * r * 2.0))
            y = int(round(cy + math.sin(angle) * r))
            glyph = cloud_chars[step % len(cloud_chars)]
            yield x, y, glyph

    @staticmethod
    def _diamond_points(cx: float, cy: float, radius: float) -> Iterable[Tuple[int, int, str]]:
        """Diamond/geometric burst — expanding diamond shape."""
        r = int(radius)
        for d in range(r + 1):
            inv = r - d
            points = [
                (int(round(cx + d * 2)), int(round(cy - inv))),
                (int(round(cx - d * 2)), int(round(cy - inv))),
                (int(round(cx + d * 2)), int(round(cy + inv))),
                (int(round(cx - d * 2)), int(round(cy + inv))),
            ]
            glyph = "\u25c7" if d == r else "\u00b7"
            for x, y in points:
                yield x, y, glyph
