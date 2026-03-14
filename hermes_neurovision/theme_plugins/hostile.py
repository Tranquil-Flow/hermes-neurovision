"""Hostile theme plugins for Hermes Vision."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


class NoxiousFumesPlugin(ThemePlugin):
    """Poisonous gas clouds — dense fog with toxic bubbles."""

    name = "noxious-fumes"

    def build_nodes(self, w, h, cx, cy, count, rng):
        # Nodes hidden in fog — scattered randomly
        nodes = []
        for _ in range(count):
            x = rng.uniform(4, max(5, w - 5))
            y = rng.uniform(2, max(3, h - 3))
            nodes.append((x, y))
        return nodes

    def step_star(self, star, frame, w, h, rng):
        # Dense fog drifting horizontally
        star[0] += 0.04 * star[2]  # drift right
        star[1] += math.sin(frame * 0.02 + star[3]) * 0.015  # slight vertical wobble
        if star[0] >= w - 1:
            # Wrap to left side
            star[0] = 1.0
            star[1] = rng.uniform(1, max(2, h - 2))
        return True

    def star_glyph(self, brightness, char_idx):
        # Dense fog characters
        if brightness > 0.65:
            return "▒"
        return "░"

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Toxic bubbles rising and popping
        x = rng.uniform(3, max(4, w - 4))
        y = rng.uniform(max(2, h * 0.4), max(h * 0.4 + 1, h - 2))
        vx = rng.uniform(-0.04, 0.04)
        vy = rng.uniform(-0.12, -0.04)  # rising
        char = rng.choice("°○")
        life = rng.randint(6, 14)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        # Barely visible wisps
        return "·" if abs(dx) > abs(dy) else "."

    def pulse_params(self):
        return (0.14, 0.24)

    def node_glyph(self, idx, intensity, total):
        return "○" if intensity > 0.65 else "◌"

    def node_color_key(self, idx, intensity, total):
        return "soft"

    def particle_color_key(self, age_ratio):
        return "soft"  # always dim toxic

    def edge_color_key(self, step, idx_a, frame):
        return "soft"

    def pulse_color_key(self):
        return "base"

    def packet_color_key(self):
        return "soft"


class MazeRunnerPlugin(ThemePlugin):
    """Shifting dimensional maze — walls phase in/out, reality tears, recursive portals."""

    name = "maze-runner"

    def build_nodes(self, w, h, cx, cy, count, rng):
        # Three layers of reality at different depths
        nodes = []
        for layer in range(3):
            layer_count = count // 3
            for _ in range(layer_count):
                # Each layer has different clustering
                if layer == 0:
                    # Front layer: scattered wide
                    x = rng.uniform(4, max(5, w - 5))
                    y = rng.uniform(2, max(3, h - 3))
                elif layer == 1:
                    # Middle layer: ring formation
                    angle = rng.uniform(0, math.tau)
                    radius = min(w, h) * 0.25
                    x = cx + math.cos(angle) * radius * 1.2
                    y = cy + math.sin(angle) * radius * 0.6
                else:
                    # Deep layer: central vortex
                    angle = rng.uniform(0, math.tau)
                    radius = rng.uniform(0, min(w, h) * 0.15)
                    x = cx + math.cos(angle) * radius * 1.0
                    y = cy + math.sin(angle) * radius * 0.5
                nodes.append((x, y))
        return nodes

    def step_nodes(self, nodes, frame, w, h):
        # Nodes phase between dimensions with sine-wave oscillation
        cx = w / 2.0
        cy = h / 2.0
        for i in range(len(nodes)):
            x, y = nodes[i]
            # Oscillate radius from center
            dx = x - cx
            dy = y - cy
            dist = max(0.5, math.hypot(dx, dy))
            angle = math.atan2(dy, dx)
            
            # Each layer phases differently
            layer = i % 3
            if layer == 0:
                # Front: slow expansion/contraction
                pulse = math.sin(frame * 0.03 + i * 0.5) * 2.0
            elif layer == 1:
                # Middle: rotation and pulse
                angle += 0.015
                pulse = math.cos(frame * 0.04 + i * 0.7) * 1.5
            else:
                # Deep: intense pulsing
                pulse = math.sin(frame * 0.06 + i * 1.2) * 3.0
            
            new_dist = dist + pulse
            new_x = cx + math.cos(angle) * new_dist * 1.2
            new_y = cy + math.sin(angle) * new_dist * 0.6
            
            nodes[i] = (
                max(3.0, min(w - 4.0, new_x)),
                max(2.0, min(h - 3.0, new_y))
            )

    def step_star(self, star, frame, w, h, rng):
        # Reality tears drifting through dimensions
        star[0] += math.sin(frame * 0.02 + star[3]) * 0.3
        star[1] += math.cos(frame * 0.025 + star[3] * 0.7) * 0.2
        # Wrap around
        if star[0] < 2:
            star[0] = w - 3
        elif star[0] > w - 3:
            star[0] = 2
        if star[1] < 1:
            star[1] = h - 2
        elif star[1] > h - 2:
            star[1] = 1
        return True

    def star_glyph(self, brightness, char_idx):
        # Dimensional rifts and tears
        if brightness > 0.8:
            return "※"
        elif brightness > 0.5:
            return "◊"
        return "·"

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Dimensional sparks ejected from portals
        if nodes:
            node = rng.choice(nodes)
            angle = rng.uniform(0, math.tau)
            speed = rng.uniform(0.08, 0.25)
            x = node[0]
            y = node[1]
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed * 0.6
        else:
            x = rng.uniform(3, max(4, w - 4))
            y = rng.uniform(2, max(3, h - 3))
            vx = rng.uniform(-0.15, 0.15)
            vy = rng.uniform(-0.10, 0.10)
        char = rng.choice("※◊*·")
        life = rng.randint(8, 18)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        # Reality bridges between dimensions
        return "╌" if abs(dx) > abs(dy) else "┆"

    def node_glyph(self, idx, intensity, total):
        layer = idx % 3
        if intensity > 0.75:
            return "⊗"  # Active portal
        elif layer == 0:
            return "◎"  # Front layer
        elif layer == 1:
            return "◉"  # Middle layer
        else:
            return "●"  # Deep layer

    def packet_budget(self):
        return 6

    def node_color_key(self, idx, intensity, total):
        layer = idx % 3
        if intensity > 0.75:
            return "warning"
        elif layer == 2:
            return "accent"
        elif layer == 1:
            return "bright"
        return "soft"

    def edge_color_key(self, step, idx_a, frame):
        # Edges phase in and out of visibility
        phase = (step + frame * 0.5) % 40
        if phase < 10:
            return "bright"
        elif phase < 20:
            return "accent"
        return "soft"

    def particle_color_key(self, age_ratio):
        return "bright" if age_ratio > 0.6 else "accent" if age_ratio > 0.3 else "soft"

    def packet_color_key(self):
        return "warning"

    def pulse_style(self):
        return "ripple"

    def pulse_style(self):
        return "diamond"

    def pulse_color_key(self):
        return "soft"

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        w = state.width
        h = state.height
        pair = curses.color_pair(color_pairs.get("soft", 0))
        # Top border: ╔══...══╗
        try:
            top_mid = "═" * max(0, w - 4)
            stdscr.addstr(0, 2, "╔" + top_mid + "╗", pair)
        except curses.error:
            pass
        # Side borders
        for row in range(1, h - 2):
            try:
                stdscr.addstr(row, 2, "║", pair)
            except curses.error:
                pass
            try:
                stdscr.addstr(row, w - 2, "║", pair)
            except curses.error:
                pass
        # Bottom border: ╚══...══╝
        try:
            bot_mid = "═" * max(0, w - 4)
            stdscr.addstr(h - 2, 2, "╚" + bot_mid + "╝", pair)
        except curses.error:
            pass


# ── Register all hostile plugins ─────────────────────────────────

for _cls in [
    NoxiousFumesPlugin, MazeRunnerPlugin,
]:
    register(_cls())
