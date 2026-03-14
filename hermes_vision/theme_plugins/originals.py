"""Original 10 themes extracted from scene.py/renderer.py elif branches."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from hermes_vision.plugin import ThemePlugin
from hermes_vision.theme_plugins import register


class NeuralSkyPlugin(ThemePlugin):
    """Default theme — all base behavior."""
    name = "neural-sky"


class ElectricMyceliumPlugin(ThemePlugin):
    """Mycelium network — mostly default with slight tweaks."""
    name = "electric-mycelium"


class MoonwirePlugin(ThemePlugin):
    """Ring layout with moon."""
    name = "moonwire"

    def build_nodes(self, w, h, cx, cy, count, rng):
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)
        radius_x = usable_w * 0.28
        radius_y = usable_h * 0.30
        nodes = []
        for i in range(count):
            a = (math.tau * i) / count
            nodes.append((cx + math.cos(a) * radius_x, cy + math.sin(a) * radius_y))
        nodes.append((cx, cy))
        return nodes

    def build_edges_extra(self, nodes, edges_set):
        for idx in range(len(nodes) - 1):
            edges_set.add(tuple(sorted((idx, (idx + 1) % (len(nodes) - 1)))))
            edges_set.add(tuple(sorted((idx, len(nodes) - 1))))

    def star_glyph(self, brightness, char_idx):
        return None

    def edge_color_key(self, step, idx_a, frame):
        return "base"

    def packet_color_key(self):
        return "bright"

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        from hermes_vision.ascii_art import MOON_ART
        moon_x = max(3, state.width - 10)
        MOON_ART.draw(stdscr, moon_x + 1, 2, color_pairs["bright"], anchor="topleft")


class RootsongPlugin(ThemePlugin):
    """Tree root structure."""
    name = "rootsong"

    def build_nodes(self, w, h, cx, cy, count, rng):
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)
        nodes = []
        # Index tracking for edge building (stored as instance attr)
        self._trunk_indices = []
        self._branch_map = {}  # trunk_idx -> list of branch node indices

        # Main trunk: top-center downward, occupying upper 30% to bottom
        trunk_top_y = h * 0.30
        trunk_bot_y = h - 3.0
        trunk_segments = 8
        for seg in range(trunk_segments):
            ratio = seg / max(1, trunk_segments - 1)
            y = trunk_top_y + ratio * (trunk_bot_y - trunk_top_y)
            sway = math.sin(seg * 0.5) * 1.5
            idx = len(nodes)
            nodes.append((cx + sway, y))
            self._trunk_indices.append(idx)

        # Primary branches: every 2nd trunk node spawns left+right branches
        branch_origins = self._trunk_indices[2:]  # skip top 2 nodes
        self._branch_indices = []  # flat list of (branch_node_idx, parent_trunk_idx)
        for i, trunk_idx in enumerate(branch_origins):
            if i % 2 != 0:
                continue
            tx, ty = nodes[trunk_idx]
            spread = usable_w * 0.18 + i * (usable_w * 0.035)
            down = usable_h * 0.07 + i * (usable_h * 0.02)
            for side in (-1, 1):
                bx = tx + side * spread + rng.uniform(-1.5, 1.5)
                by = ty + down + rng.uniform(-1.0, 1.0)
                bidx = len(nodes)
                nodes.append((bx, by))
                self._branch_indices.append((bidx, trunk_idx))

                # Sub-branches from each primary branch
                for sub in range(1, 3):
                    sx = bx + side * spread * 0.5 * sub + rng.uniform(-2, 2)
                    sy = by + down * 0.6 * sub + rng.uniform(-1.0, 1.5)
                    sidx = len(nodes)
                    nodes.append((sx, sy))
                    self._branch_indices.append((sidx, bidx))

        return nodes

    def build_edges_extra(self, nodes, edges_set):
        # Connect trunk sequentially
        trunk = getattr(self, '_trunk_indices', [])
        for i in range(len(trunk) - 1):
            edges_set.add(tuple(sorted((trunk[i], trunk[i + 1]))))

        # Connect each branch node to its parent
        branch_map = getattr(self, '_branch_indices', [])
        for child_idx, parent_idx in branch_map:
            if child_idx < len(nodes) and parent_idx < len(nodes):
                edges_set.add(tuple(sorted((child_idx, parent_idx))))

    def edge_glyph(self, dx, dy):
        return "\u2502" if abs(dy) > abs(dx) else "\u2571" if dx * dy < 0 else "\u2572"

    def node_glyph(self, idx, intensity, total):
        return "\u25c9" if idx % 3 == 0 else "\u2022"

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_vision.scene import Particle
        x = w / 2 + rng.uniform(-4, 4)
        y = h - 3
        vx = rng.uniform(-0.12, 0.12)
        vy = rng.uniform(-0.22, -0.08)
        char = rng.choice(",.;`")
        life = rng.randint(7, 14)
        return Particle(x, y, vx, vy, life, life, char)


class CathedralCircuitPlugin(ThemePlugin):
    """Grid layout with arches."""
    name = "cathedral-circuit"

    def build_nodes(self, w, h, cx, cy, count, rng):
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)
        cols = max(4, min(8, w // 14))
        rows = max(3, min(7, h // 6))
        nodes = []
        for row in range(rows):
            for col in range(cols):
                x = 6 + col * (usable_w / max(1, cols - 1))
                y = 3 + row * (usable_h / max(1, rows - 1))
                arch = math.sin((col / max(1, cols - 1)) * math.pi) * 2.5
                nodes.append((x, y + arch))
        return nodes

    def edge_keep_count(self):
        return 4

    def edge_glyph(self, dx, dy):
        return "\u2551" if abs(dy) > abs(dx) else "\u2550"

    def edge_color_key(self, step, idx_a, frame):
        return "soft"

    def node_glyph(self, idx, intensity, total):
        return "\u2726" if idx % 5 == 0 else "\u25c6"


class StormCorePlugin(ThemePlugin):
    """Storm bands with lightning."""
    name = "storm-core"

    def build_nodes(self, w, h, cx, cy, count, rng):
        usable_h = max(6.0, h - 6.0)
        bands = max(3, h // 7)
        nodes = []
        for band in range(bands):
            y = 2 + band * (usable_h / max(1, bands - 1))
            for _ in range(max(3, w // 18)):
                x = rng.uniform(4, w - 5)
                nodes.append((x, y + rng.uniform(-1.5, 1.5)))
        return nodes

    def edge_keep_count(self):
        return 2

    def particle_base_chance(self):
        return 0.05

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_vision.scene import Particle
        x = rng.uniform(2, max(3, w - 3))
        y = rng.uniform(1, max(2, h / 2))
        vx = rng.uniform(-0.10, 0.10)
        vy = rng.uniform(0.12, 0.26)
        char = rng.choice("'|/\\")
        life = rng.randint(7, 14)
        return Particle(x, y, vx, vy, life, life, char)

    def pulse_params(self):
        return (0.34, 0.18)

    def pulse_style(self):
        return "rays"

    def edge_color_key(self, step, idx_a, frame):
        return "accent" if (step + frame) % 9 == 0 else "base"

    def node_glyph(self, idx, intensity, total):
        return "\u25cc" if intensity < 0.5 else "\u25c9"

    def pulse_color_key(self):
        return "warning"

    def step_star_post(self, star, frame, w, h, rng):
        star[0] -= 0.08 * star[2]

    def node_position_adjust(self, x, y, idx, frame, w, h):
        import math as _m
        return (x, y + _m.sin(frame * 0.08 + idx * 0.5) * 0.8)


class StormglassPlugin(ThemePlugin):
    """Glass refraction effect."""
    name = "stormglass"

    def pulse_style(self):
        return "diamond"

    def step_star_post(self, star, frame, w, h, rng):
        star[1] += math.sin(frame * 0.03 + star[0] * 0.1) * 0.02

    def edge_color_key(self, step, idx_a, frame):
        # Use step as proxy for position — actual x,y not available in this API
        return "bright" if (step + idx_a + frame) % 13 == 0 else "soft"

    def pulse_color_key(self):
        return "bright"

    def node_position_adjust(self, x, y, idx, frame, w, h):
        return (x + math.sin(frame * 0.03 + y * 0.2) * 0.5, y)


class HybridPlugin(ThemePlugin):
    """Hybrid mode with extra packets."""
    name = "hybrid"

    def packet_budget(self):
        return 6

    def node_color_key(self, idx, intensity, total):
        if idx % 4 == 0:
            return "accent"
        return "bright" if intensity > 0.65 else "soft"


class SpiralGalaxyPlugin(ThemePlugin):
    """3-arm spiral galaxy."""
    name = "spiral-galaxy"

    def build_nodes(self, w, h, cx, cy, count, rng):
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)
        disc_radius = min(usable_w, usable_h) * 0.85
        arms = 3
        total_arm_nodes = int(count * 1.5)
        nodes_per_arm = total_arm_nodes // arms
        nodes = []

        for arm_idx in range(arms):
            for i in range(nodes_per_arm):
                ratio = i / max(1, nodes_per_arm - 1)
                base_angle = arm_idx * (math.tau / arms)
                twist = ratio * math.tau * 2.5
                angle = base_angle + twist
                radius = disc_radius * (0.10 + ratio * 0.90)
                # Add some radial scatter but preserve arm identity
                radius += rng.uniform(-disc_radius * 0.3, disc_radius * 0.3) * ratio * 0.6
                radius = max(disc_radius * 0.05, radius)
                # Narrow perpendicular offset keeps arms distinct
                perp_offset = rng.uniform(-1.2, 1.2)
                x = cx + math.cos(angle) * radius + math.cos(angle + math.pi / 2) * perp_offset
                y = cy + math.sin(angle) * radius + math.sin(angle + math.pi / 2) * perp_offset
                nodes.append((x, y))

        core_radius = disc_radius * rng.uniform(0.05, 0.08)
        core_nodes = max(6, count // 6)
        for i in range(core_nodes):
            angle = (math.tau * i) / core_nodes
            radius = core_radius * rng.uniform(0.5, 1.0)
            nodes.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))

        nodes.append((cx, cy))
        return nodes

    def build_edges_extra(self, nodes, edges_set):
        center_idx = len(nodes) - 1
        for idx in range(len(nodes) - 2):
            if idx + 3 < len(nodes) - 1:
                edges_set.add(tuple(sorted((idx, idx + 3))))
            if idx % 4 == 0:
                edges_set.add(tuple(sorted((idx, center_idx))))

    def step_star(self, star, frame, w, h, rng):
        cx = w / 2.0
        cy = h / 2.0
        dx = star[0] - cx
        dy = star[1] - cy
        radius = max(1.0, math.hypot(dx, dy))
        # Differential rotation: outer stars orbit slower; radius divisor kept small
        # so stars spread across the full screen rather than clustering at centre
        angle = math.atan2(dy, dx) + 0.006 * star[2] / max(1.0, radius * 0.04)
        radius = radius * (0.9997 + math.sin(frame * 0.01 + star[3]) * 0.0006)
        # Clamp to screen so stars don't drift off edge
        max_r = max(w, h) * 0.55
        if radius > max_r:
            radius = max_r
        star[0] = cx + math.cos(angle) * radius
        star[1] = cy + math.sin(angle) * radius
        return True

    def particle_base_chance(self):
        return 0.022

    def particle_life_range(self):
        return (8, 16)

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_vision.scene import Particle
        angle = rng.uniform(0, math.tau)
        radius = min(w, h) * rng.uniform(0.10, 0.26)
        x = w / 2 + math.cos(angle) * radius
        y = h / 2 + math.sin(angle) * radius
        speed = rng.uniform(0.025, 0.06)
        vx = -math.sin(angle) * speed
        vy = math.cos(angle) * speed
        char = rng.choice(".:*")
        life = rng.randint(8, 16)
        return Particle(x, y, vx, vy, life, life, char)

    def pulse_params(self):
        return (0.24, 0.14)

    def pulse_style(self):
        return "spoked"

    def packet_budget(self):
        return 5

    def star_glyph(self, brightness, char_idx):
        return "\u2726" if brightness > 0.75 else None

    def node_glyph(self, idx, intensity, total):
        return "\u2726" if idx % 6 == 0 else "\u2022"

    def node_color_key(self, idx, intensity, total):
        if idx % 5 == 0:
            return "accent"
        return "bright" if intensity > 0.65 else "soft"

    def edge_glyph(self, dx, dy):
        return "\u00b7" if abs(dy) < abs(dx) * 0.35 else "\u2571" if dx * dy < 0 else "\u2572"

    def edge_color_key(self, step, idx_a, frame):
        return "soft" if (step + idx_a) % 5 else "accent"

    def pulse_color_key(self):
        return "accent"

    def node_position_adjust(self, x, y, idx, frame, w, h):
        cx = w / 2.0
        cy = h / 2.0
        dx = x - cx
        dy = y - cy
        radius = max(0.8, math.hypot(dx, dy))
        # Slower rotation for outer nodes, faster for inner — realistic differential rotation
        # Use a larger divisor so the orbit covers the full screen
        angular_speed = 0.012 / max(1.0, radius * 0.03) + idx * 0.0003
        angle = math.atan2(dy, dx) + angular_speed
        return (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)


class BlackHolePlugin(ThemePlugin):
    """Black hole with accretion disk."""
    name = "black-hole"

    def build_nodes(self, w, h, cx, cy, count, rng):
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)
        nodes = []

        # Inner event horizon ring
        inner_count = 8
        radius_x = usable_w * 0.12
        radius_y = usable_h * 0.14
        for i in range(inner_count):
            a = (math.tau * i) / inner_count
            nodes.append((cx + math.cos(a) * radius_x, cy + math.sin(a) * radius_y))

        # Middle accretion disk
        mid_count = max(12, count // 2)
        radius_x = usable_w * 0.22
        radius_y = usable_h * 0.26
        for i in range(mid_count):
            a = (math.tau * i) / mid_count
            wobble = 1.0 + math.sin(i * 0.9) * 0.08
            nodes.append((cx + math.cos(a) * radius_x * wobble, cy + math.sin(a) * radius_y * wobble))

        # Outer ring
        outer_count = max(6, count // 3)
        for i in range(outer_count):
            a = (math.tau * i) / outer_count + 0.4
            nodes.append((cx + math.cos(a) * usable_w * 0.32, cy + math.sin(a) * usable_h * 0.38))

        # Singularity
        nodes.append((cx, cy))
        return nodes

    def build_edges_extra(self, nodes, edges_set):
        center_idx = len(nodes) - 1
        ring_nodes = max(1, len(nodes) - 1)
        for idx in range(ring_nodes):
            edges_set.add(tuple(sorted((idx, (idx + 1) % ring_nodes))))
            if idx % 2 == 0:
                edges_set.add(tuple(sorted((idx, center_idx))))

    def step_star(self, star, frame, w, h, rng):
        cx = w / 2.0
        cy = h / 2.0
        dx = star[0] - cx
        dy = star[1] - cy
        radius = math.hypot(dx, dy)
        angle = math.atan2(dy, dx) + 0.010 * star[2]
        radius = radius * (0.996 - 0.0015 * star[2])
        if radius < 3.0:
            reset_angle = rng.uniform(0, math.tau)
            reset_radius = min(w, h) * rng.uniform(0.34, 0.48)
            star[0] = cx + math.cos(reset_angle) * reset_radius * 1.8
            star[1] = cy + math.sin(reset_angle) * reset_radius * 0.6
            return True
        star[0] = cx + math.cos(angle) * radius * 1.15
        star[1] = cy + math.sin(angle) * radius * 0.42
        return True

    def step_nodes(self, nodes, frame, w, h):
        cx = w / 2.0
        cy = h / 2.0
        inner_count = 8
        for i in range(min(inner_count, len(nodes))):
            dx = nodes[i][0] - cx
            dy = nodes[i][1] - cy
            radius = math.hypot(dx, dy)
            angle = math.atan2(dy, dx) + 0.08
            nodes[i] = (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)

        mid_start = inner_count
        mid_count = max(12, (len(nodes) - inner_count - 1) // 2)
        for i in range(mid_start, min(mid_start + mid_count, len(nodes) - 1)):
            dx = nodes[i][0] - cx
            dy = nodes[i][1] - cy
            radius = math.hypot(dx, dy)
            angle = math.atan2(dy, dx) + 0.04
            nodes[i] = (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)

        outer_start = mid_start + mid_count
        for i in range(outer_start, len(nodes) - 1):
            dx = nodes[i][0] - cx
            dy = nodes[i][1] - cy
            radius = math.hypot(dx, dy)
            angle = math.atan2(dy, dx) + 0.02
            nodes[i] = (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)

    def particle_base_chance(self):
        return 0.018

    def particle_life_range(self):
        return (6, 12)

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_vision.scene import Particle
        angle = rng.uniform(0, math.tau)
        radius = min(w, h) * rng.uniform(0.18, 0.34)
        x = w / 2 + math.cos(angle) * radius * 1.6
        y = h / 2 + math.sin(angle) * radius * 0.48
        vx = -math.cos(angle) * rng.uniform(0.04, 0.08)
        vy = -math.sin(angle) * rng.uniform(0.02, 0.05)
        char = rng.choice(".:·")
        life = rng.randint(6, 12)
        return Particle(x, y, vx, vy, life, life, char)

    def pulse_params(self):
        return (0.18, 0.10)

    def pulse_style(self):
        return "ripple"

    def packet_budget(self):
        return 3

    def star_glyph(self, brightness, char_idx):
        return "\u00b7" if brightness > 0.7 else None

    def node_glyph(self, idx, intensity, total):
        return "\u25cd" if idx == total - 1 else "\u2022"

    def node_color_key(self, idx, intensity, total):
        return "warning" if idx == total - 1 else "soft"

    def edge_glyph(self, dx, dy):
        return "~" if abs(dy) < abs(dx) * 0.35 else "(" if dx * dy < 0 else ")"

    def edge_color_key(self, step, idx_a, frame):
        return "warning" if step % 6 == 0 else "base"

    def packet_color_key(self):
        return "warning"

    def particle_color_key(self, age_ratio):
        return "warning" if age_ratio > 0.55 else "base"

    def pulse_color_key(self):
        return "base"

    def node_position_adjust(self, x, y, idx, frame, w, h):
        cx = w / 2.0
        cy = h / 2.0
        dx = x - cx
        dy = y - cy
        angle = math.atan2(dy, dx) + 0.015
        radius = max(1.5, math.hypot(dx, dy) * (0.9985 - idx * 0.00002))
        return (cx + math.cos(angle) * radius * 1.1, cy + math.sin(angle) * radius * 0.45)

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        cx = max(2, state.width // 2)
        cy = max(2, state.height // 2)
        disk = ((cx - 2, cy, "(( "), (cx + 1, cy, "))"), (cx - 1, cy, "\u2588\u2588"))
        for x, y, text in disk:
            try:
                stdscr.addstr(y, x, text, curses.color_pair(color_pairs["warning"]))
            except curses.error:
                pass


# ── Register all original plugins ────────────────────────────────

for _cls in [
    NeuralSkyPlugin, ElectricMyceliumPlugin, MoonwirePlugin,
    RootsongPlugin, CathedralCircuitPlugin, StormCorePlugin,
    StormglassPlugin, HybridPlugin, SpiralGalaxyPlugin, BlackHolePlugin,
]:
    register(_cls())
