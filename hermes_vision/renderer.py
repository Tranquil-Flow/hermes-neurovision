"""Curses renderer for Hermes Vision."""

from __future__ import annotations

import curses
import math
import time
from typing import TYPE_CHECKING, Dict, Iterable, Optional, Tuple

from hermes_vision.themes import ThemeConfig, STAR_CHARS, PULSE_CHARS

if TYPE_CHECKING:
    from hermes_vision.scene import ThemeState


class Renderer:
    def __init__(self, stdscr: "curses._CursesWindow") -> None:
        self.stdscr = stdscr
        self.color_pairs = self._init_colors()

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

    def draw(self, state: "ThemeState", gallery_index: int, gallery_total: int, end_time: Optional[float]) -> None:
        stdscr = self.stdscr
        h, w = stdscr.getmaxyx()
        state.resize(w, h)
        stdscr.erase()

        self._draw_stars(state)
        self._draw_edges(state)
        self._draw_pulses(state)
        self._draw_nodes(state)
        self._draw_packets(state)
        self._draw_particles(state)
        self._draw_overlay(state, gallery_index, gallery_total, end_time)
        stdscr.refresh()

    def _draw_stars(self, state: "ThemeState") -> None:
        attr = curses.color_pair(self.color_pairs["base"]) | curses.A_DIM
        if state.config.moon_mode or state.config.glass_mode:
            attr = curses.color_pair(self.color_pairs["soft"]) | curses.A_DIM
        for x, y, brightness, char_idx in state.stars:
            glyph = STAR_CHARS[min(len(STAR_CHARS) - 1, char_idx)]
            if state.config.galaxy_mode and brightness > 0.75:
                glyph = "✦"
            elif state.config.black_hole_mode and brightness > 0.7:
                glyph = "·"
            try:
                self.stdscr.addstr(int(y), int(x), glyph, attr if brightness < 0.8 else curses.color_pair(self.color_pairs["soft"]))
            except curses.error:
                pass

        if state.config.black_hole_mode:
            cx = max(2, state.width // 2)
            cy = max(2, state.height // 2)
            disk = ((cx - 2, cy, "(( "), (cx + 1, cy, "))"), (cx - 1, cy, "██"))
            for x, y, text in disk:
                try:
                    self.stdscr.addstr(y, x, text, curses.color_pair(self.color_pairs["warning"]))
                except curses.error:
                    pass

        if state.config.moon_mode:
            moon_x = max(3, state.width - 10)
            moon_y = 2
            moon = ((moon_x, moon_y, "◜◝"), (moon_x, moon_y + 1, "◟◞"))
            for x, y, text in moon:
                try:
                    self.stdscr.addstr(y, x, text, curses.color_pair(self.color_pairs["bright"]))
                except curses.error:
                    pass

    def _draw_edges(self, state: "ThemeState") -> None:
        for idx_a, idx_b in state.edges:
            ax, ay = self._node_position(state, idx_a)
            bx, by = self._node_position(state, idx_b)
            dx = bx - ax
            dy = by - ay
            steps = max(abs(int(dx)), abs(int(dy)), 1)
            for step in range(1, steps):
                t = step / steps
                x = int(round(ax + dx * t))
                y = int(round(ay + dy * t))
                glyph = self._edge_glyph(dx, dy, state.config)
                attr = curses.color_pair(self.color_pairs["base"]) | curses.A_DIM
                if state.config.cathedral_mode:
                    attr = curses.color_pair(self.color_pairs["soft"])
                elif state.config.storm_mode:
                    attr = curses.color_pair(self.color_pairs["accent"]) if (step + state.frame) % 9 == 0 else attr
                elif state.config.glass_mode:
                    attr = curses.color_pair(self.color_pairs["bright"]) if (x + y + state.frame) % 13 == 0 else curses.color_pair(self.color_pairs["soft"])
                elif state.config.galaxy_mode:
                    attr = curses.color_pair(self.color_pairs["soft"]) if (step + idx_a) % 5 else curses.color_pair(self.color_pairs["accent"])
                elif state.config.black_hole_mode:
                    attr = curses.color_pair(self.color_pairs["warning"]) if step % 6 == 0 else curses.color_pair(self.color_pairs["base"])
                try:
                    self.stdscr.addstr(y, x, glyph, attr)
                except curses.error:
                    pass

    def _draw_nodes(self, state: "ThemeState") -> None:
        for idx, _ in enumerate(state.nodes):
            x, y = self._node_position(state, idx)
            intensity = 0.5 + 0.5 * math.sin(state.frame * 0.12 + idx * 0.6)
            glyph = "●" if intensity > 0.72 else "•"
            if state.config.cathedral_mode:
                glyph = "✦" if idx % 5 == 0 else "◆"
            elif state.config.root_mode:
                glyph = "◉" if idx % 3 == 0 else "•"
            elif state.config.storm_mode:
                glyph = "◌" if intensity < 0.5 else "◉"
            elif state.config.galaxy_mode:
                glyph = "✦" if idx % 6 == 0 else "•"
            elif state.config.black_hole_mode:
                glyph = "◍" if idx == len(state.nodes) - 1 else "•"
            attr = curses.color_pair(self.color_pairs["bright"] if intensity > 0.65 else self.color_pairs["soft"])
            if state.config.hybrid_mode and idx % 4 == 0:
                attr = curses.color_pair(self.color_pairs["accent"])
            elif state.config.galaxy_mode and idx % 5 == 0:
                attr = curses.color_pair(self.color_pairs["accent"])
            elif state.config.black_hole_mode:
                attr = curses.color_pair(self.color_pairs["warning"] if idx == len(state.nodes) - 1 else self.color_pairs["soft"])
            try:
                self.stdscr.addstr(y, x, glyph, attr)
            except curses.error:
                pass

    def _draw_packets(self, state: "ThemeState") -> None:
        for packet in state.packets:
            ax, ay = self._node_position(state, packet.edge[0])
            bx, by = self._node_position(state, packet.edge[1])
            x = int(round(ax + (bx - ax) * packet.progress))
            y = int(round(ay + (by - ay) * packet.progress))
            attr = curses.color_pair(self.color_pairs["accent"]) | curses.A_BOLD
            if state.config.moon_mode:
                attr = curses.color_pair(self.color_pairs["bright"])
            elif state.config.black_hole_mode:
                attr = curses.color_pair(self.color_pairs["warning"])
            try:
                self.stdscr.addstr(y, x, packet.glyph, attr)
            except curses.error:
                pass

    def _draw_particles(self, state: "ThemeState") -> None:
        for particle in state.particles:
            x = int(round(particle.x))
            y = int(round(particle.y))
            if not (0 <= x < state.width and 0 <= y < state.height):
                continue
            attr = curses.color_pair(self.color_pairs["soft"]) | curses.A_DIM
            if particle.age_ratio > 0.6:
                attr = curses.color_pair(self.color_pairs["accent"])
            if state.config.black_hole_mode:
                attr = curses.color_pair(self.color_pairs["warning"] if particle.age_ratio > 0.55 else self.color_pairs["base"])
            try:
                self.stdscr.addstr(y, x, particle.char, attr)
            except curses.error:
                pass

    def _draw_pulses(self, state: "ThemeState") -> None:
        for x, y, radius in state.pulses:
            points = self._ring_points(x, y, radius)
            for px, py, glyph in points:
                attr = curses.color_pair(self.color_pairs["soft"]) | curses.A_DIM
                if state.config.storm_mode:
                    attr = curses.color_pair(self.color_pairs["warning"])
                elif state.config.glass_mode:
                    attr = curses.color_pair(self.color_pairs["bright"])
                elif state.config.galaxy_mode:
                    attr = curses.color_pair(self.color_pairs["accent"])
                elif state.config.black_hole_mode:
                    attr = curses.color_pair(self.color_pairs["base"])
                try:
                    self.stdscr.addstr(py, px, glyph, attr)
                except curses.error:
                    pass

    def _draw_overlay(self, state: "ThemeState", gallery_index: int, gallery_total: int, end_time: Optional[float]) -> None:
        title = f" Hermes visualizer // {state.config.name} "
        footer = " q quit  n next  p prev  space pause "
        if gallery_total > 1:
            footer = f" theme {gallery_index + 1}/{gallery_total} |" + footer
        if end_time is not None:
            remaining = max(0.0, end_time - time.time())
            footer += f" | auto-exit {remaining:0.1f}s "

        try:
            self.stdscr.addstr(0, 1, title[: max(0, state.width - 2)], curses.color_pair(self.color_pairs["bright"]) | curses.A_BOLD)
        except curses.error:
            pass
        try:
            self.stdscr.addstr(state.height - 1, 1, footer[: max(0, state.width - 2)], curses.color_pair(self.color_pairs["soft"]))
        except curses.error:
            pass

    def _node_position(self, state: "ThemeState", idx: int) -> Tuple[int, int]:
        x, y = state.nodes[idx]
        jitter = state.config.node_jitter
        xf = x + math.sin(state.frame * 0.05 + idx * 0.9) * jitter
        yf = y + math.cos(state.frame * 0.04 + idx * 1.1) * jitter * 0.6
        if state.config.storm_mode:
            yf += math.sin(state.frame * 0.08 + idx * 0.5) * 0.8
        if state.config.glass_mode:
            xf += math.sin(state.frame * 0.03 + y * 0.2) * 0.5
        if state.config.galaxy_mode:
            cx = state.width / 2.0
            cy = state.height / 2.0
            dx = x - cx
            dy = y - cy
            radius = max(0.8, math.hypot(dx, dy))
            angle = math.atan2(dy, dx) + 0.008 / max(0.6, radius * 0.06) + idx * 0.0005
            xf = cx + math.cos(angle) * radius
            yf = cy + math.sin(angle) * radius
        elif state.config.black_hole_mode:
            cx = state.width / 2.0
            cy = state.height / 2.0
            dx = x - cx
            dy = y - cy
            angle = math.atan2(dy, dx) + 0.015
            radius = max(1.5, math.hypot(dx, dy) * (0.9985 - idx * 0.00002))
            xf = cx + math.cos(angle) * radius * 1.1
            yf = cy + math.sin(angle) * radius * 0.45
        return int(max(1, min(state.width - 2, round(xf)))), int(max(1, min(state.height - 2, round(yf))))

    @staticmethod
    def _edge_glyph(dx: float, dy: float, config: ThemeConfig) -> str:
        if config.root_mode:
            return "│" if abs(dy) > abs(dx) else "╱" if dx * dy < 0 else "╲"
        if config.cathedral_mode:
            return "║" if abs(dy) > abs(dx) else "═"
        if config.galaxy_mode:
            return "·" if abs(dy) < abs(dx) * 0.35 else "╱" if dx * dy < 0 else "╲"
        if config.black_hole_mode:
            return "~" if abs(dy) < abs(dx) * 0.35 else "(" if dx * dy < 0 else ")"
        if abs(dy) < abs(dx) * 0.35:
            return "─"
        if abs(dx) < abs(dy) * 0.45:
            return "│"
        return "╱" if dx * dy < 0 else "╲"

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
