"""Whimsical theme plugins for Hermes Vision."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


class CampfirePlugin(ThemePlugin):
    """Campfire at night — embers rising, stars in upper sky."""

    name = "campfire"

    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        # Large flame cluster at bottom-center for bonfire effect
        flame_count = max(8, count // 2)  # More flame nodes
        for i in range(flame_count):
            x = cx + rng.uniform(-w * 0.10, w * 0.10)  # Wider flames
            y = h - rng.uniform(3, 12)  # Taller flames
            nodes.append((x, y))

        # Scattered tree/rock nodes in upper area
        remaining = count - flame_count
        for _ in range(remaining):
            x = rng.uniform(4, max(5, w - 5))
            y = rng.uniform(2, max(3, h * 0.5))
            nodes.append((x, y))
        return nodes

    def step_star(self, star, frame, w, h, rng):
        threshold = h * 0.40
        if star[1] > threshold:
            # Embers rising from lower portion
            star[1] -= 0.08 * star[2]
            star[0] += math.sin(frame * 0.1 + star[3]) * 0.06
            if star[1] < 1:
                # Reset as new ember near fire
                star[0] = w / 2 + rng.uniform(-w * 0.08, w * 0.08)
                star[1] = h - rng.uniform(2, 5)
        else:
            # Normal star twinkle in upper sky
            star[0] += math.sin(frame * 0.02 + star[3]) * 0.01 * star[2]
            star[1] += math.cos(frame * 0.015 + star[3]) * 0.008 * star[2]
        return True

    def star_glyph(self, brightness, char_idx):
        return "·" if brightness < 0.5 else "*"

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Embers rising with sway from bottom center
        x = w / 2 + rng.uniform(-w * 0.07, w * 0.07)
        y = h - rng.uniform(2, 6)
        vx = rng.uniform(-0.10, 0.10)
        vy = rng.uniform(-0.22, -0.06)
        char = rng.choice("·*'")
        life = rng.randint(7, 14)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        # Flame flickers cycling
        return "╱"

    def node_glyph(self, idx, intensity, total):
        return "▲" if intensity > 0.65 else "△"

    def node_color_key(self, idx, intensity, total):
        flame_count = max(8, total // 2)
        if idx < flame_count:
            return "warning" if intensity > 0.5 else "accent"
        return "soft"

    def particle_color_key(self, age_ratio):
        return "accent" if age_ratio > 0.5 else "warning"

    def pulse_color_key(self):
        return "warning"

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        from hermes_neurovision.ascii_art import BONFIRE
        cx = max(7, state.width // 2 - 6)
        bottom = max(10, state.height - 2)
        BONFIRE.draw(stdscr, cx, bottom, color_pairs["warning"], anchor="bottomleft")


class AquariumPlugin(ThemePlugin):
    """Tropical fish tank — fish, bubbles, seaweed."""

    name = "aquarium"

    def build_nodes(self, w, h, cx, cy, count, rng):
        # Fish scattered across middle band
        nodes = []
        for i in range(count):
            x = rng.uniform(4, max(5, w - 5))
            y = rng.uniform(h * 0.25, max(h * 0.25 + 1, h * 0.75))
            nodes.append((x, y))
        return nodes

    def edge_keep_count(self):
        return 1

    def step_star(self, star, frame, w, h, rng):
        # Bubbles rising slowly
        star[1] -= 0.06 * star[2]
        star[0] += math.sin(frame * 0.04 + star[3]) * 0.02
        if star[1] < 1:
            # New bubble from bottom
            star[0] = rng.uniform(2, max(3, w - 3))
            star[1] = h - rng.uniform(1, 3)
        return True

    def star_glyph(self, brightness, char_idx):
        return "°" if brightness > 0.6 else "○"

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        if rng.random() < 0.6:
            # Food flakes descending from top
            x = rng.uniform(3, max(4, w - 4))
            y = rng.uniform(1, max(2, h * 0.15))
            vx = rng.uniform(-0.03, 0.03)
            vy = rng.uniform(0.04, 0.10)
            char = rng.choice(".,")
        else:
            # Tiny dots sinking
            x = rng.uniform(3, max(4, w - 4))
            y = rng.uniform(h * 0.1, max(h * 0.1 + 1, h * 0.5))
            vx = rng.uniform(-0.02, 0.02)
            vy = rng.uniform(0.03, 0.07)
            char = "·"
        life = rng.randint(8, 16)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        return "~"

    def node_glyph(self, idx, intensity, total):
        return "►" if idx % 2 == 0 else "◄"

    def node_color_key(self, idx, intensity, total):
        colors = ["accent", "bright", "soft", "base"]
        return colors[idx % len(colors)]

    def particle_color_key(self, age_ratio):
        return "soft"

    def packet_color_key(self):
        return "bright"

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        w = state.width
        h = state.height
        frame = state.frame if hasattr(state, "frame") else 0

        # Gravel floor
        floor_y = h - 2
        try:
            stdscr.addstr(floor_y, 2, "·" * max(0, w - 4),
                          curses.color_pair(color_pairs["soft"]))
        except curses.error:
            pass

        # Seaweed at bottom swaying with sin(frame)
        seaweed_positions = [4, w // 4, w // 2, 3 * w // 4, w - 5]
        for sx in seaweed_positions:
            for row in range(3):
                sy = h - 3 - row
                sway = int(math.sin(frame * 0.08 + sx * 0.3) * 1)
                draw_x = sx + sway
                if 0 <= draw_x < w - 1 and 0 <= sy < h - 1:
                    try:
                        stdscr.addstr(sy, draw_x, "¦",
                                      curses.color_pair(color_pairs["base"]))
                    except curses.error:
                        pass


class CircuitBoardPlugin(ThemePlugin):
    """PCB close-up — strict grid, copper traces, signal packets."""

    name = "circuit-board"

    def build_nodes(self, w, h, cx, cy, count, rng):
        # Spread components all over the screen with slight randomization
        usable_w = max(12.0, w - 6.0)
        usable_h = max(6.0, h - 4.0)
        # Dense grid covering entire screen
        cols = max(5, w // 5)
        rows = max(4, h // 3)
        nodes = []
        for row in range(rows):
            for col in range(cols):
                x = 3 + col * (usable_w / max(1, cols - 1))
                y = 2 + row * (usable_h / max(1, rows - 1))
                # Small jitter so they're not perfectly aligned
                x += rng.uniform(-0.5, 0.5)
                y += rng.uniform(-0.3, 0.3)
                x = max(3.0, min(w - 4.0, x))
                y = max(2.0, min(h - 2.0, y))
                nodes.append((x, y))
        return nodes

    def edge_keep_count(self):
        return 4

    def build_edges_extra(self, nodes, edges_set):
        # Add orthogonal PCB traces — connect to nearest in each cardinal direction
        for i, (x, y) in enumerate(nodes):
            best = {"left": None, "right": None, "up": None, "down": None}
            best_d = {"left": float("inf"), "right": float("inf"),
                      "up": float("inf"), "down": float("inf")}
            for j, (nx, ny) in enumerate(nodes):
                if i == j:
                    continue
                dx = nx - x
                dy = ny - y
                dist = abs(dx) + abs(dy)
                if abs(dx) > abs(dy) * 1.5:
                    if dx < 0 and dist < best_d["left"]:
                        best["left"] = j
                        best_d["left"] = dist
                    elif dx > 0 and dist < best_d["right"]:
                        best["right"] = j
                        best_d["right"] = dist
                elif abs(dy) > abs(dx) * 1.5:
                    if dy < 0 and dist < best_d["up"]:
                        best["up"] = j
                        best_d["up"] = dist
                    elif dy > 0 and dist < best_d["down"]:
                        best["down"] = j
                        best_d["down"] = dist
            for direction, j in best.items():
                if j is not None:
                    edge = (min(i, j), max(i, j))
                    edges_set.add(edge)

    def step_star(self, star, frame, w, h, rng):
        # Electrical signals flickering across the PCB
        star[0] += rng.uniform(-0.05, 0.05)
        star[1] += rng.uniform(-0.04, 0.04)
        # Wrap around to keep signals everywhere on the board
        if star[0] < 2:
            star[0] = w - 3
        elif star[0] > w - 3:
            star[0] = 2
        if star[1] < 1:
            star[1] = h - 2
        elif star[1] > h - 2:
            star[1] = rng.uniform(1, h - 2)  # respawn anywhere
        return True

    def spawn_particle(self, w, h, nodes, rng):
        return None  # Clean environment — no particles

    def particle_base_chance(self):
        return 0.001

    def edge_glyph(self, dx, dy):
        return "═" if abs(dx) > abs(dy) else "║"

    def node_glyph(self, idx, intensity, total):
        mod = idx % 8
        if mod == 0:
            return "▣"   # IC chip
        elif mod == 4:
            return "◉"   # capacitor
        elif mod == 2:
            return "┤"   # connector
        else:
            return "•"   # via hole

    def edge_color_key(self, step, idx_a, frame):
        return "soft"

    def packet_budget(self):
        return 12

    def node_color_key(self, idx, intensity, total):
        return "accent" if idx % 4 == 0 else "bright"

    def packet_color_key(self):
        return "accent"

    def pulse_color_key(self):
        return "bright"


class LavaLampPlugin(ThemePlugin):
    """Hypnotic blobs rising and sinking."""

    name = "lava-lamp"

    def build_nodes(self, w, h, cx, cy, count, rng):
        # 6-8 blob centers, heavy jitter
        blob_count = min(count, rng.randint(6, 8))
        nodes = []
        for i in range(blob_count):
            # Spread vertically across the screen
            base_y = 2 + (i / max(1, blob_count - 1)) * (h - 5)
            x = cx + rng.uniform(-w * 0.22, w * 0.22)
            y = base_y + rng.uniform(-h * 0.08, h * 0.08)
            x = max(4.0, min(w - 5.0, x))
            y = max(2.0, min(h - 3.0, y))
            nodes.append((x, y))
        return nodes

    def step_nodes(self, nodes, frame, w, h):
        # More dramatic vertical oscillation — larger amplitude, different speeds
        for i in range(len(nodes)):
            x, y = nodes[i]
            # Unique phase and speed per blob
            phase = i * (math.tau / max(1, len(nodes)))
            # Alternate direction: even-indexed blobs go one way, odd the other
            direction = 1.0 if i % 2 == 0 else -1.0
            speed = 0.018 + (i % 3) * 0.008
            amplitude = h * 0.3
            dy = math.sin(frame * speed * direction + phase) * amplitude * 0.05
            new_y = y + dy
            new_y = max(2.0, min(h - 3.0, new_y))
            nodes[i] = (x, new_y)

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        if not nodes:
            return None
        node = rng.choice(nodes)
        x = node[0] + rng.uniform(-2, 2)
        y = node[1] + rng.uniform(-1, 1)
        # Some rising, some sinking
        if rng.random() < 0.5:
            vy = rng.uniform(-0.08, -0.02)
        else:
            vy = rng.uniform(0.02, 0.08)
        vx = rng.uniform(-0.03, 0.03)
        char = rng.choice("●◉○")
        life = rng.randint(14, 24)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        return "○" if abs(dx) > abs(dy) else "◌"

    def pulse_params(self):
        return (0.18, 0.22)

    def particle_life_range(self):
        return (14, 24)

    def node_glyph(self, idx, intensity, total):
        # Size based on vertical position: bigger near middle
        # We don't have y here directly, so use intensity as a proxy
        if intensity > 0.65:
            return "●"   # large blob
        elif intensity > 0.35:
            return "◉"   # medium blob
        else:
            return "○"   # small blob

    def pulse_style(self):
        return "cloud"

    def node_color_key(self, idx, intensity, total):
        colors = ["accent", "warning", "bright", "soft"]
        return colors[idx % len(colors)]

    def particle_color_key(self, age_ratio):
        return "accent" if age_ratio > 0.6 else "warning"

    def pulse_color_key(self):
        return "warning"

    def packet_color_key(self):
        return "accent"


class FireflyFieldPlugin(ThemePlugin):
    """Open meadow at dusk — blinking fireflies."""

    name = "firefly-field"

    def build_nodes(self, w, h, cx, cy, count, rng):
        # Very few nodes — trees at edges
        node_count = min(count, rng.randint(4, 6))
        nodes = []
        # Trees at left and right edges
        for i in range(node_count):
            if i < node_count // 2:
                x = rng.uniform(3, max(4, w * 0.18))
            else:
                x = rng.uniform(max(w * 0.82, w - 10.0), max(w * 0.82 + 1, w - 3.0))
            y = rng.uniform(h * 0.3, max(h * 0.3 + 1, h * 0.85))
            nodes.append((x, y))
        return nodes

    def edge_keep_count(self):
        return 2

    def step_star(self, star, frame, w, h, rng):
        # Fireflies blink via sin cycle
        rate = 0.04 + (star[3] % 0.06)  # unique blink rate per star
        brightness_val = math.sin(frame * rate + star[3])
        # Store blink state in star[2] — abuse speed field slightly
        # Actually just drift slowly and let star_glyph handle visibility
        star[0] += math.sin(frame * 0.015 + star[3]) * 0.04
        star[1] += math.cos(frame * 0.012 + star[3] * 0.7) * 0.03
        # Wrap
        if star[0] < 1:
            star[0] = w - 2
        elif star[0] >= w - 1:
            star[0] = 1
        if star[1] < 1:
            star[1] = h - 2
        elif star[1] >= h - 1:
            star[1] = 1
        return True

    def star_glyph(self, brightness, char_idx):
        # Only visible when sin > 0.3 (simulated via brightness)
        if brightness > 0.7:
            return "✧"
        if brightness > 0.3:
            return "·"
        return " "  # dark — firefly off

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # More fireflies spawning near ground, drifting up
        x = rng.uniform(3, max(4, w - 4))
        y = rng.uniform(max(2, h * 0.5), max(h * 0.5 + 1, h - 3))
        vx = rng.uniform(-0.06, 0.06)
        vy = rng.uniform(-0.08, -0.02)
        char = rng.choice("·✧*")
        life = rng.randint(8, 16)
        return Particle(x, y, vx, vy, life, life, char)

    def particle_base_chance(self):
        return 0.035

    def node_glyph(self, idx, intensity, total):
        return "↟" if intensity > 0.6 else "¦"

    def node_color_key(self, idx, intensity, total):
        return "soft"

    def particle_color_key(self, age_ratio):
        return "accent" if age_ratio > 0.5 else "soft"

    def pulse_color_key(self):
        return "soft"

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        w = state.width
        h = state.height
        # Grass line at bottom
        grass_y = h - 2
        grass = "∿" * max(0, (w - 4) // 1)
        try:
            stdscr.addstr(grass_y, 2, grass[:max(0, w - 4)],
                          curses.color_pair(color_pairs["base"]))
        except curses.error:
            pass


# ── Register all whimsical plugins ───────────────────────────────

for _cls in [
    CampfirePlugin, AquariumPlugin, CircuitBoardPlugin,
    LavaLampPlugin, FireflyFieldPlugin,
]:
    register(_cls())
