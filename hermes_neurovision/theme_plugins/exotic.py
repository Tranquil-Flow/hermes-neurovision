"""Exotic theme plugins for Hermes Vision."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


class NeonRainPlugin(ThemePlugin):
    """Cyberpunk city in the rain."""
    name = "neon-rain"

    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        # Scattered window lights at varied floor heights — 15-20 nodes max
        target = min(count, 18)
        # Building anchor x positions (spread across screen)
        building_xs = [
            w * 0.08, w * 0.18, w * 0.28, w * 0.40,
            w * 0.52, w * 0.63, w * 0.74, w * 0.85, w * 0.93,
        ]
        # Floor heights — varied to suggest different building heights
        floor_bands = [h * 0.15, h * 0.22, h * 0.28, h * 0.35, h * 0.42, h * 0.50]
        placed = 0
        for bx in building_xs:
            if placed >= target:
                break
            # 1-2 lit windows per building, at random floors
            lights = rng.randint(1, 2)
            for _ in range(lights):
                if placed >= target:
                    break
                floor_y = rng.choice(floor_bands) + rng.uniform(-1.5, 1.5)
                x = bx + rng.uniform(-1.5, 1.5)
                y = max(2.0, min(h * 0.58, floor_y))
                nodes.append((x, y))
                placed += 1
        # Pad if needed
        while len(nodes) < count:
            nodes.append((rng.uniform(4, w - 5), rng.uniform(2, h * 0.55)))
        return nodes[:count]

    def step_star(self, star, frame, w, h, rng):
        # Rain falling diagonally — move down and slightly left
        speed = star[2] * 0.4 + 0.3
        star[1] += speed
        star[0] -= speed * 0.25
        if star[1] >= h - 2:
            star[1] = rng.uniform(0, 3)
            star[0] = rng.uniform(2, w - 3)
        if star[0] < 1:
            star[0] = w - 3
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Puddle splashes at bottom or neon sign flicker sparks
        if rng.random() < 0.6:
            # Splash at bottom
            x = rng.uniform(2, w - 3)
            y = h - rng.uniform(1, 4)
            vx = rng.uniform(-0.15, 0.15)
            vy = rng.uniform(-0.08, 0.02)
            char = rng.choice("·.~")
        else:
            # Neon flicker spark
            x = rng.uniform(4, w - 5)
            y = rng.uniform(2, h * 0.5)
            vx = rng.uniform(-0.2, 0.2)
            vy = rng.uniform(-0.15, 0.05)
            char = "*"
        life = rng.randint(4, 9)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        # Building outlines — strictly vertical or horizontal
        return "│" if abs(dy) > abs(dx) else "─"

    def edge_color_key(self, step, idx_a, frame):
        return "base"

    def node_glyph(self, idx, intensity, total):
        # Most windows are subtle dots; only very bright ones get a filled square
        if intensity > 0.8:
            return "▪"
        return "·"

    def pulse_style(self):
        return "ripple"

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        w = state.width
        h = state.height
        frame = state.frame
        # City skyline silhouette — sparse, gapped buildings
        building_profiles = [
            (0, int(w * 0.14), int(h * 0.35)),
            (int(w * 0.20), int(w * 0.32), int(h * 0.25)),
            (int(w * 0.38), int(w * 0.52), int(h * 0.20)),
            (int(w * 0.58), int(w * 0.70), int(h * 0.28)),
            (int(w * 0.76), int(w * 0.90), int(h * 0.32)),
        ]
        base_pair = curses.color_pair(color_pairs.get("base", 1))
        for x_start, x_end, top_y in building_profiles:
            # Sparse: only draw every other column to create gaps
            for x in range(max(0, x_start), min(w - 1, x_end), 2):
                for y in range(max(0, top_y), min(h - 1, h)):
                    ch = "█" if y == top_y else "▒"
                    try:
                        stdscr.addch(y, x, ch, base_pair)
                    except curses.error:
                        pass
        # Neon signs — only 30% of frames, single character flicker
        sign_positions = [(int(w * 0.21), int(h * 0.54)), (int(w * 0.66), int(h * 0.51))]
        accent_pair = curses.color_pair(color_pairs.get("accent", 1))
        for i, (sx, sy) in enumerate(sign_positions):
            cycle = (frame + i * 13) % 30
            if cycle < 9 and 0 <= sy < h and 0 <= sx < w - 1:
                # Alternate between * and ◆ for flicker
                ch = "*" if cycle % 2 == 0 else "◆"
                try:
                    stdscr.addch(sy, sx, ch, accent_pair | curses.A_BOLD)
                except curses.error:
                    pass


class VolcanicPlugin(ThemePlugin):
    """Active volcano eruption."""
    name = "volcanic"

    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        crater_x = cx
        crater_y = h * 0.15
        # Inner nodes near crater
        inner = max(4, count // 3)
        for i in range(inner):
            a = (math.tau * i) / inner
            r = rng.uniform(1.5, 4.0)
            nodes.append((crater_x + math.cos(a) * r, crater_y + math.sin(a) * r * 0.5))
        # Outer nodes at base — lava channels radiating outward
        outer = count - inner
        for i in range(outer):
            a = math.pi * (i / max(1, outer - 1)) + math.pi * 0.1
            r = rng.uniform(h * 0.3, h * 0.7)
            nodes.append((crater_x + math.cos(a) * r * 0.7, crater_y + math.sin(a) * r))
        return nodes[:count]

    def step_star(self, star, frame, w, h, rng):
        # Ash particles drifting upward and outward from crater
        cx = w / 2.0
        star[1] -= star[2] * 0.15 + 0.05
        star[0] += (star[0] - cx) * 0.004 + rng.uniform(-0.05, 0.05)
        if star[1] < 0:
            star[1] = h * rng.uniform(0.05, 0.25)
            star[0] = cx + rng.uniform(-3, 3)
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Lava bombs ejecting upward from crater
        cx = w / 2.0
        crater_y = h * 0.15
        x = cx + rng.uniform(-3, 3)
        y = crater_y + rng.uniform(0, 2)
        a = rng.uniform(math.pi * 1.1, math.pi * 1.9)
        speed = rng.uniform(0.3, 0.7)
        vx = math.cos(a) * speed
        vy = math.sin(a) * speed - 0.2
        char = rng.choice("●◉*")
        life = rng.randint(4, 8)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        return "≈" if abs(dx) > abs(dy) else "~"

    def pulse_params(self):
        return (0.40, 0.22)

    def particle_base_chance(self):
        return 0.045

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        from hermes_neurovision.ascii_art import VOLCANO
        cx = max(2, state.width // 2)
        cy = max(2, state.height - VOLCANO.height - 1)
        VOLCANO.draw(stdscr, cx, cy, color_pairs.get("accent", 1), anchor="topleft")

    def node_glyph(self, idx, intensity, total):
        return "◉" if intensity > 0.7 else ("●" if intensity > 0.4 else "·")


class CrystalCavePlugin(ThemePlugin):
    """Underground crystal formations."""
    name = "crystal-cave"

    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        # Stalactites in upper 30%
        stalactite_count = count // 2
        for _ in range(stalactite_count):
            x = rng.uniform(4, w - 5)
            y = rng.uniform(1, h * 0.30)
            nodes.append((x, y))
        # Stalagmites in lower 30%
        stalagmite_count = count - stalactite_count
        for _ in range(stalagmite_count):
            x = rng.uniform(4, w - 5)
            y = rng.uniform(h * 0.70, h - 2)
            nodes.append((x, y))
        return nodes

    def step_star(self, star, frame, w, h, rng):
        # Ambient sparkle — very sparse, no drift, intermittent brightness
        return False

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        if rng.random() < 0.65 and nodes:
            # Dripping water from top nodes
            top_nodes = [(nx, ny) for nx, ny in nodes if ny < h * 0.4]
            if top_nodes:
                nx, ny = rng.choice(top_nodes)
                x = nx + rng.uniform(-0.5, 0.5)
                y = ny + 1.0
            else:
                x = rng.uniform(4, w - 5)
                y = rng.uniform(1, h * 0.35)
            vx = rng.uniform(-0.02, 0.02)
            vy = rng.uniform(0.08, 0.18)
            char = "·"
            life = rng.randint(6, 12)
        else:
            # Light refraction sparks
            x = rng.uniform(4, w - 5)
            y = rng.uniform(2, h - 3)
            vx = rng.uniform(-0.1, 0.1)
            vy = rng.uniform(-0.1, 0.1)
            char = "*"
            life = rng.randint(3, 6)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        if abs(dy) > abs(dx) * 1.5:
            return "│"
        elif dx * dy < 0:
            return "╱"
        else:
            return "╲"

    def node_glyph(self, idx, intensity, total):
        half = total // 2
        # Top nodes (stalactites) get ◇ or ◆, bottom get △
        if idx < half:
            return "◆" if intensity > 0.6 else "◇"
        else:
            return "△"

    def pulse_params(self):
        return (0.30, 0.16)


class SpiderWebPlugin(ThemePlugin):
    """Dew-covered web at dawn."""
    name = "spider-web"

    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        # Center hub
        nodes.append((cx, cy))
        # 7 radial spokes going to the edges of the screen
        num_spokes = 7
        # 6 concentric rings at increasing radii filling the screen
        # Use half-width * 2.0 to account for terminal char aspect ratio on x
        max_rx = (w / 2.0) * 0.97
        max_ry = (h / 2.0) * 0.95
        ring_fracs = [0.15, 0.30, 0.45, 0.60, 0.80, 0.95]
        # node layout: hub at index 0, then ring0_spoke0..ring0_spokeN, ring1_spoke0..etc.
        for ring_idx, frac in enumerate(ring_fracs):
            rx = max_rx * frac
            ry = max_ry * frac
            for spoke in range(num_spokes):
                a = (math.tau * spoke) / num_spokes
                nodes.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
        # Trim or pad to count
        while len(nodes) < count:
            a = rng.uniform(0, math.tau)
            r_frac = rng.uniform(0.5, 0.9)
            nodes.append((cx + math.cos(a) * max_rx * r_frac, cy + math.sin(a) * max_ry * r_frac))
        return nodes[:count]

    def build_edges_extra(self, nodes, edges_set):
        # Connect nodes along spokes (radially) and along rings (circumferentially)
        if not nodes:
            return
        hub = 0
        num_spokes = 7
        ring_fracs = [0.15, 0.30, 0.45, 0.60, 0.80, 0.95]
        num_rings = len(ring_fracs)
        # Index helper: node at ring r, spoke s = 1 + r * num_spokes + s
        def node_idx(ring, spoke):
            return 1 + ring * num_spokes + spoke
        # Hub connects to all first-ring nodes (spokes)
        for s in range(num_spokes):
            idx = node_idx(0, s)
            if idx < len(nodes):
                edges_set.add((hub, idx))
        # Radial connections: each spoke across all rings
        for s in range(num_spokes):
            for r in range(num_rings - 1):
                a = node_idx(r, s)
                b = node_idx(r + 1, s)
                if a < len(nodes) and b < len(nodes):
                    edges_set.add((a, b))
        # Circumferential connections: each ring connects adjacent spokes
        for r in range(num_rings):
            for s in range(num_spokes):
                a = node_idx(r, s)
                b = node_idx(r, (s + 1) % num_spokes)
                if a < len(nodes) and b < len(nodes):
                    edges_set.add((min(a, b), max(a, b)))

    def step_star_post(self, star, frame, w, h, rng):
        # Morning mist — very sparse, slow rightward drift
        if rng.random() < 0.03:
            star[0] += 0.04

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        x = rng.uniform(4, w - 5)
        y = rng.uniform(2, h - 3)
        vx = rng.uniform(-0.02, 0.02)
        vy = rng.uniform(0.01, 0.05)
        char = "·"
        life = rng.randint(8, 16)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        if abs(dy) < abs(dx) * 0.4:
            return "─"
        elif abs(dx) < abs(dy) * 0.4:
            return "│"
        elif dx * dy < 0:
            return "╱"
        else:
            return "╲"

    def edge_keep_count(self):
        return 4

    def edge_color_key(self, step, idx_a, frame):
        return "base"

    def node_glyph(self, idx, intensity, total):
        num_spokes = 7
        if idx == 0:
            return "●"
        # First ring: indices 1..num_spokes
        if idx <= num_spokes:
            return "○"
        # Middle rings: up to 4th ring
        ring = (idx - 1) // num_spokes
        if ring <= 3:
            return "◦"
        # Outer rings
        return "·"

    def packet_color_key(self):
        return "accent"

    def pulse_style(self):
        return "spoked"

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        from hermes_neurovision.ascii_art import SPIDER
        cx = max(2, state.width // 2)
        cy = max(2, state.height // 2)
        SPIDER.draw(stdscr, cx, cy, color_pairs.get("soft", 1), anchor="center")


class SnowGlobePlugin(ThemePlugin):
    """Freshly shaken snow globe."""
    name = "snow-globe"

    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        # Village at bottom — spread across most of the screen width
        base_y = int(h * 0.82)
        # Houses spread across the bottom
        house_xs = [cx - int(w * 0.28), cx - int(w * 0.12), cx + int(w * 0.05), cx + int(w * 0.20)]
        for hx in house_xs:
            nodes.append((max(2, min(w - 3, hx)), base_y))
        # Trees interspersed
        tree_xs = [cx - int(w * 0.35), cx - int(w * 0.20), cx, cx + int(w * 0.13), cx + int(w * 0.30)]
        for tx in tree_xs:
            nodes.append((max(2, min(w - 3, tx)), base_y - rng.randint(0, 2)))
        # Lampposts at base level
        for lx in [cx - int(w * 0.08), cx + int(w * 0.08)]:
            nodes.append((max(2, min(w - 3, lx)), base_y))
        # Fill remaining count with scattered snow-dome nodes (upper 80% area)
        while len(nodes) < count:
            x = rng.uniform(3, w - 4)
            y = rng.uniform(2, h * 0.78)
            nodes.append((x, y))
        return nodes[:count]

    def edge_keep_count(self):
        return 1

    def step_star(self, star, frame, w, h, rng):
        # Snowflakes falling with horizontal sway
        star_id = int(star[3] * 1000) % 100
        speed = 0.08 + (star_id % 7) * 0.02
        sway = math.sin(frame * 0.04 + star_id * 0.6) * 0.12
        star[1] += speed
        star[0] += sway
        # Swirl near edges
        if star[0] < w * 0.1 or star[0] > w * 0.9:
            star[0] += math.sin(frame * 0.08 + star_id) * 0.2
        if star[1] >= h - 2:
            star[1] = rng.uniform(0, 3)
            star[0] = rng.uniform(2, w - 3)
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Snow accumulation near bottom
        x = rng.uniform(4, w - 5)
        y = h - rng.uniform(1, 3)
        vx = rng.uniform(-0.03, 0.03)
        vy = 0.0
        char = "░"
        life = rng.randint(10, 20)
        return Particle(x, y, vx, vy, life, life, char)

    def node_glyph(self, idx, intensity, total):
        if idx < 2:
            return "▣"
        elif idx < 5:
            return "♠"
        return "│"

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        w = state.width
        h = state.height
        cx = w // 2
        cy = h // 2
        soft_pair = curses.color_pair(color_pairs.get("soft", 1))
        # Draw a dome border that traces the terminal edges — elliptical arc
        # covering top and sides of the screen (bottom left open for village)
        rx = (w // 2) - 1
        ry = (h // 2) - 1
        dome_bottom_y = int(h * 0.85)
        # Draw top arc: points where the ellipse is above dome_bottom_y
        steps = w * 2
        for i in range(steps + 1):
            a = math.pi * i / steps  # 0..pi covers top semicircle
            px = int(cx + rx * math.cos(a))
            py = int(cy - ry * math.sin(a))
            if 0 <= py < dome_bottom_y and 0 <= px < w - 1:
                ch = "·" if (i % 5 != 0) else "○"
                try:
                    stdscr.addch(py, px, ch, soft_pair)
                except curses.error:
                    pass
        # Draw vertical side lines from arc endpoints down to dome_bottom_y
        for side_x in [1, w - 2]:
            for sy in range(cy, dome_bottom_y):
                if 0 <= sy < h:
                    try:
                        stdscr.addch(sy, side_x, "│", soft_pair)
                    except curses.error:
                        pass

    def star_glyph(self, brightness, char_idx):
        chars = ["*", "✦", "·", "°"]
        return chars[char_idx % len(chars)]


# ── Register all exotic plugins ───────────────────────────────────

for _cls in [
    NeonRainPlugin, VolcanicPlugin, CrystalCavePlugin,
    SpiderWebPlugin, SnowGlobePlugin,
]:
    register(_cls())
