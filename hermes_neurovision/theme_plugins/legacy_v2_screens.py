"""Legacy v2 pre-v0.2-upgrade theme screens.

Verbatim copies of screens from cosmic.py, exotic.py, whimsical.py, and
originals.py (active screens only), preserved before they were upgraded to
the v0.2 API (react(), emergent layer methods, postfx methods).

Registered under "legacy-v2-*" names so they do not conflict with v0.2 versions.
These are NOT in the THEMES tuple — access via --include-legacy flag.
"""

from __future__ import annotations

import curses
import math
import random
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register




# ======================================================================
# From cosmic.py
# ======================================================================

class Legacy2AuroraBorealisPlugin(ThemePlugin):
    """Northern lights — constellation patterns glowing in aurora colors."""

    name = "legacy-v2-aurora-borealis"

    def build_nodes(self, w, h, cx, cy, count, rng):
        # Create 3-4 constellation patterns in the sky
        nodes = []
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h * 0.70)  # upper 70% (sky region)
        
        # Constellation patterns (various shapes)
        constellations = [
            # Big dipper shape
            [(0, 0), (2, 1), (4, 1), (5, 0), (6, -1), (7, -2), (9, -2)],
            # Orion belt + shoulders
            [(0, 2), (2, 1), (4, 1), (6, 2), (3, -1), (3, -2), (3, -3)],
            # W shape (Cassiopeia-like)
            [(0, 0), (2, 2), (4, 0), (6, 2), (8, 0)],
            # Triangle/pyramid
            [(0, 3), (4, 0), (8, 3), (4, 2)],
        ]
        
        num_constellations = min(4, max(2, count // 7))
        for c_idx in range(num_constellations):
            # Pick a constellation shape
            pattern = rng.choice(constellations)
            # Place it somewhere in the sky
            base_x = rng.uniform(5, max(6, w - 15))
            base_y = rng.uniform(3, max(4, h * 0.50))
            scale = rng.uniform(1.5, 3.0)
            
            for px, py in pattern:
                x = base_x + px * scale
                y = base_y + py * scale * 0.6
                x = max(3.0, min(w - 4.0, x))
                y = max(2.0, min(h * 0.75, y))
                nodes.append((x, y))
        
        # Fill to count with scattered stars
        while len(nodes) < count:
            x = rng.uniform(3, max(4, w - 4))
            y = rng.uniform(2, max(3, h * 0.70))
            nodes.append((x, y))
        return nodes[:count]

    def step_nodes(self, nodes, frame, w, h):
        # Constellation stars pulse and shimmer gently
        for i, (ox, oy) in enumerate(nodes):
            # Gentle breathing pulse
            pulse = math.sin(frame * 0.02 + i * 0.3) * 0.5
            wobble_x = math.cos(frame * 0.015 + i * 0.5) * 0.3
            wobble_y = math.sin(frame * 0.018 + i * 0.7) * 0.2
            nodes[i] = (ox + wobble_x + pulse * 0.2, oy + wobble_y + pulse * 0.1)

    def step_star(self, star, frame, w, h, rng):
        # Stars in upper 40%: static starfield above the aurora
        if star[1] < h * 0.40:
            return True
        # Stars below: slowly drift upward (rising glow)
        star[1] -= 0.02 * star[2]
        if star[1] < 1.0:
            star[1] = float(h - 2)
            star[0] = rng.uniform(2.0, max(3.0, w - 3.0))
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Light wisps drifting slowly upward
        x = rng.uniform(2, max(3, w - 3))
        y = rng.uniform(h * 0.20, max(h * 0.21, h * 0.75))
        vx = rng.uniform(-0.03, 0.03)
        vy = rng.uniform(-0.08, -0.02)
        char = rng.choice("~\u2248")
        life = rng.randint(10, 20)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        # Curtain fabric — vertical for mostly-vertical edges, angled for diagonal
        if abs(dy) > abs(dx) * 2:
            return "\u2502"  # │ mostly vertical
        elif dx * dy < 0:
            return "\u2571"  # ╱
        elif dx * dy > 0:
            return "\u2572"  # ╲
        return "\u2502"

    def edge_color_key(self, step, idx_a, frame):
        # Shimmer by cycling through color keys
        cycle = (step + frame) % 20
        if cycle < 5:
            return "base"
        elif cycle < 10:
            return "soft"
        elif cycle < 15:
            return "bright"
        return "accent"

    def node_glyph(self, idx, intensity, total):
        return "\u2550"  # ═ horizontal shimmer

    def node_color_key(self, idx, intensity, total):
        cycle = idx % 4
        if cycle == 0:
            return "bright"
        elif cycle == 1:
            return "accent"
        elif cycle == 2:
            return "soft"
        return "warning"

    def particle_color_key(self, age_ratio):
        return "accent" if age_ratio > 0.5 else "soft"

    def pulse_style(self):
        return "cloud"

    def pulse_color_key(self):
        return "accent"

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        # Flat terrain line at the very bottom row using ▁ chars
        terrain_y = state.height - 2
        col_pair = curses.color_pair(color_pairs["base"])
        terrain_line = "\u2581" * (state.width - 2)
        try:
            stdscr.addstr(terrain_y, 1, terrain_line, col_pair)
        except curses.error:
            pass


class Legacy2NebulaNurseryPlugin(ThemePlugin):
    """Stellar nursery — proto-star cloud clusters, stellar wind particles."""

    name = "legacy-v2-nebula-nursery"

    def build_nodes(self, w, h, cx, cy, count, rng):
        # Dense cloud clusters
        cluster_count = max(3, count // 8)
        cluster_centers = []
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)
        for _ in range(cluster_count):
            cluster_centers.append((
                4.0 + rng.uniform(0, usable_w),
                2.0 + rng.uniform(0, usable_h),
            ))

        nodes = []
        per_cluster = max(2, count // cluster_count)
        for cc in cluster_centers:
            for _ in range(per_cluster):
                spread = rng.uniform(1.5, 5.0)
                x = cc[0] + rng.gauss(0, spread)
                y = cc[1] + rng.gauss(0, spread * 0.6)
                nodes.append((x, y))

        # Fill remaining
        while len(nodes) < count:
            x = rng.uniform(4, max(5, w - 5))
            y = rng.uniform(2, max(3, h - 3))
            nodes.append((x, y))
        return nodes[:count]

    def star_glyph(self, brightness, char_idx):
        # Dense gas cloud texture
        if brightness > 0.75:
            return "\u2591"
        elif brightness > 0.45:
            return "\u00b7"
        return "."

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Stellar wind ejecting outward from a bright node (very slow drift)
        if nodes:
            origin = rng.choice(nodes[:max(1, len(nodes) // 4)])
            angle = rng.uniform(0, math.tau)
            speed = rng.uniform(0.015, 0.04)  # Much slower: was 0.08-0.20
            x = origin[0]
            y = origin[1]
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed * 0.55
        else:
            x = w / 2 + rng.uniform(-5, 5)
            y = h / 2 + rng.uniform(-3, 3)
            vx = rng.uniform(-0.02, 0.02)  # Much slower: was -0.12 to 0.12
            vy = rng.uniform(-0.015, 0.015)  # Much slower: was -0.08 to 0.08
        char = rng.choice(".·*")
        life = rng.randint(8, 16)
        return Particle(x, y, vx, vy, life, life, char)

    def pulse_params(self):
        return (0.32, 0.20)

    def particle_base_chance(self):
        return 0.04

    def node_glyph(self, idx, intensity, total):
        return "\u2605" if intensity > 0.80 else "\u2022" if intensity > 0.50 else "\u00b7"

    def node_color_key(self, idx, intensity, total):
        if intensity > 0.80:
            return "bright"
        elif idx % 3 == 0:
            return "accent"
        return "soft"

    def edge_glyph(self, dx, dy):
        return "\u00b7"

    def edge_color_key(self, step, idx_a, frame):
        return "soft" if (step + idx_a) % 4 == 0 else "base"

    def pulse_color_key(self):
        return "accent"

    def particle_color_key(self, age_ratio):
        return "bright" if age_ratio > 0.65 else "accent" if age_ratio > 0.35 else "soft"


class Legacy2BinaryRainPlugin(ThemePlugin):
    """Matrix digital rain — dense vertical columns of 0/1 falling at varied speeds."""

    name = "legacy-v2-binary-rain"

    def build_nodes(self, w, h, cx, cy, count, rng):
        # Dense columns spanning full width — use w // 3 columns
        col_count = max(4, w // 3)
        col_spacing = max(2.0, (w - 4.0) / max(1, col_count - 1))
        nodes = []
        for i in range(col_count):
            x = 2.0 + i * col_spacing + rng.uniform(-0.3, 0.3)
            y = rng.uniform(1.0, 4.0)  # top of screen
            nodes.append((x, y))
        # Fill remaining nodes across full width
        while len(nodes) < count:
            x = rng.uniform(2.0, max(3.0, w - 3.0))
            y = rng.uniform(1.0, 4.0)
            nodes.append((x, y))
        return nodes[:count]

    def step_star(self, star, frame, w, h, rng):
        # Rain columns falling downward at varied speeds
        star[1] += 0.20 * star[2]
        if star[1] > h - 1:
            star[0] = rng.uniform(2.0, max(3.0, w - 3.0))
            star[1] = 0.0
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Splash at bottom spreading horizontally
        x = rng.uniform(2, max(3, w - 3))
        y = float(h - 2) + rng.uniform(-1, 0)
        vx = rng.uniform(-0.18, 0.18)
        vy = rng.uniform(-0.04, 0.02)
        char = rng.choice(".\u00b7")
        life = rng.randint(3, 7)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        return "\u2502"

    def star_glyph(self, brightness, char_idx):
        # Return 0 or 1 chars
        return "1" if brightness > 0.5 else "0"

    def node_glyph(self, idx, intensity, total):
        # 0 or 1 based on idx (proxy for frame variation)
        return "1" if idx % 2 == 0 else "0"

    def node_color_key(self, idx, intensity, total):
        return "bright" if intensity > 0.75 else "soft"

    def particle_base_chance(self):
        return 0.04

    def edge_color_key(self, step, idx_a, frame):
        return "soft" if (step + frame) % 5 == 0 else "base"

    def particle_color_key(self, age_ratio):
        return "soft" if age_ratio > 0.5 else "base"

    def packet_color_key(self):
        return "accent"

    def pulse_style(self):
        return "ripple"

    def pulse_params(self):
        return (0.15, 0.20)

    def pulse_color_key(self):
        return "soft"

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        # Dense cloud layer at top spanning entire width, several lines thick
        w = state.width
        frame = state.frame
        cloud_height = 5  # Number of rows for clouds
        
        for row in range(cloud_height):
            cloud_str = ""
            for col in range(w - 2):
                # Animate clouds with shifting pattern
                phase = col * 0.3 + frame * 0.08 + row * 0.5
                density = (math.sin(phase) + 1.0) / 2.0  # 0 to 1
                
                if density > 0.7:
                    char = "▓"  # Dense
                elif density > 0.4:
                    char = "▒"  # Medium
                elif density > 0.2:
                    char = "░"  # Light
                else:
                    char = " "
                cloud_str += char
            
            # Fade colors top to bottom
            if row < 2:
                color_key = "soft"
            elif row < 4:
                color_key = "base"
            else:
                color_key = "base"
            
            try:
                stdscr.addstr(row, 1, cloud_str[:w - 2], 
                             curses.color_pair(color_pairs[color_key]) | curses.A_DIM)
            except curses.error:
                pass


class Legacy2WormholePlugin(ThemePlugin):
    """Tunnel transit — 5 large concentric rings filling screen, rotating, stars pull inward."""

    name = "legacy-v2-wormhole"

    # Ring node counts: outer to inner
    _RING_SIZES = [16, 14, 12, 10, 6]
    # Ring radius ratios: outer to inner (90%, 70%, 50%, 30%, 10% of usable space)
    _RING_RATIOS = [0.90, 0.70, 0.50, 0.30, 0.10]
    # Rotation speeds: inner rings rotate faster
    _RING_SPEEDS = [0.005, 0.009, 0.014, 0.020, 0.030]

    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        usable_w = max(12.0, w - 4.0)
        usable_h = max(6.0, h - 4.0)
        outer_r = min(usable_w * 0.9, usable_h * 0.9)

        ring_count = len(self._RING_SIZES)
        for ring_idx in range(ring_count):
            ratio = self._RING_RATIOS[ring_idx]
            rx = outer_r * ratio * 0.5  # half because it's a radius from center
            ry = rx * (usable_h / max(1.0, usable_w))  # ellipse to fit terminal aspect
            n = self._RING_SIZES[ring_idx]
            for i in range(n):
                angle = (math.tau * i) / n + ring_idx * 0.4
                x = cx + math.cos(angle) * rx
                y = cy + math.sin(angle) * ry
                nodes.append((x, y))

        # Center node
        nodes.append((cx, cy))
        return nodes

    def step_nodes(self, nodes, frame, w, h):
        cx = w / 2.0
        cy = h / 2.0
        usable_w = max(12.0, w - 4.0)
        usable_h = max(6.0, h - 4.0)
        outer_r = min(usable_w * 0.9, usable_h * 0.9)
        pos = 0
        ring_count = len(self._RING_SIZES)
        for ring_idx in range(ring_count):
            ratio = self._RING_RATIOS[ring_idx]
            rx = outer_r * ratio * 0.5
            ry = rx * (usable_h / max(1.0, usable_w))
            n = self._RING_SIZES[ring_idx]
            speed = self._RING_SPEEDS[ring_idx]
            rotation = frame * speed + ring_idx * 0.4
            for i in range(n):
                angle = (math.tau * i) / n + rotation
                x = cx + math.cos(angle) * rx
                y = cy + math.sin(angle) * ry
                if pos + i < len(nodes):
                    nodes[pos + i] = (x, y)
            pos += n
        # Center stays fixed
        if pos < len(nodes):
            nodes[pos] = (cx, cy)

    def build_edges_extra(self, nodes, edges_set):
        # Radial spokes toward center + ring connections
        center_idx = len(nodes) - 1
        node_idx = 0
        ring_count = len(self._RING_SIZES)
        for ring_idx in range(ring_count):
            n = self._RING_SIZES[ring_idx]
            # Ring connections (connect each node to next in ring)
            for i in range(n):
                a = node_idx + i
                b = node_idx + (i + 1) % n
                edges_set.add(tuple(sorted((a, b))))
            # Spokes to center (every 3rd node)
            for i in range(0, n, 3):
                edges_set.add(tuple(sorted((node_idx + i, center_idx))))
            node_idx += n

    def step_star(self, star, frame, w, h, rng):
        # Stars accelerate inward and respawn at EDGES of terminal
        cx = w / 2.0
        cy = h / 2.0
        dx = cx - star[0]
        dy = cy - star[1]
        dist = math.hypot(dx, dy)
        if dist < 1.5:
            # Respawn at full terminal edges
            side = rng.randint(0, 3)
            if side == 0:
                star[0] = rng.uniform(0.0, float(w))
                star[1] = 0.0
            elif side == 1:
                star[0] = rng.uniform(0.0, float(w))
                star[1] = float(h - 1)
            elif side == 2:
                star[0] = 0.0
                star[1] = rng.uniform(0.0, float(h))
            else:
                star[0] = float(w - 1)
                star[1] = rng.uniform(0.0, float(h))
        else:
            # Accelerate inward faster
            speed = 0.06 + 0.18 * star[2] * (1.0 - dist / max(1, max(w, h)))
            speed = max(0.03, speed)
            star[0] += (dx / dist) * speed
            star[1] += (dy / dist) * speed
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Stretched light moving inward
        cx = w / 2.0
        cy = h / 2.0
        angle = rng.uniform(0, math.tau)
        r = max(w, h) * rng.uniform(0.25, 0.48)
        x = cx + math.cos(angle) * r
        y = cy + math.sin(angle) * r * 0.5
        speed = rng.uniform(0.12, 0.25)
        dx = cx - x
        dy = cy - y
        dist = max(1.0, math.hypot(dx, dy))
        vx = (dx / dist) * speed
        vy = (dy / dist) * speed
        char = rng.choice("\u2500\u2550\u2501")
        life = rng.randint(5, 10)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        if abs(dy) < abs(dx) * 0.3:
            return "\u00b7"
        return "\u2572" if dx * dy >= 0 else "\u2571"

    def pulse_style(self):
        return "ripple"

    def pulse_params(self):
        return (0.30, 0.20)

    def node_glyph(self, idx, intensity, total):
        if idx == total - 1:
            return "\u25ef"  # ◯ center
        ring_sizes = self._RING_SIZES
        pos = 0
        for ri, rs in enumerate(ring_sizes):
            if idx < pos + rs:
                if ri == 0:
                    return "\u25cb"  # ○ outer
                elif ri == len(ring_sizes) - 1:
                    return "\u25c9"  # ◉ innermost
                return "\u25e6"
            pos += rs
        return "\u25e6"

    def node_color_key(self, idx, intensity, total):
        if idx == total - 1:
            return "bright"
        ring_sizes = self._RING_SIZES
        pos = 0
        for ri, rs in enumerate(ring_sizes):
            if idx < pos + rs:
                if ri == 0:
                    return "base"
                elif ri <= 2:
                    return "soft"
                return "accent"
            pos += rs
        return "soft"

    def pulse_color_key(self):
        return "accent"

    def particle_color_key(self, age_ratio):
        return "bright" if age_ratio > 0.6 else "soft"

    def packet_color_key(self):
        return "bright"

    def particle_base_chance(self):
        return 0.035

    def edge_color_key(self, step, idx_a, frame):
        return "soft" if (step + idx_a + frame) % 7 == 0 else "base"


# ── Register all cosmic plugins ───────────────────────────────────

for _cls in [
    AuroraBorealisPlugin,
    NebulaNurseryPlugin,
    BinaryRainPlugin,
    WormholePlugin,
]:
    register(_cls())


# ======================================================================
# From exotic.py
# ======================================================================

class Legacy2NeonRainPlugin(ThemePlugin):
    """Cyberpunk city in the rain."""
    name = "legacy-v2-neon-rain"

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


class Legacy2VolcanicPlugin(ThemePlugin):
    """Active volcano eruption."""
    name = "legacy-v2-volcanic"

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


class Legacy2CrystalCavePlugin(ThemePlugin):
    """Underground crystal formations."""
    name = "legacy-v2-crystal-cave"

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


class Legacy2SpiderWebPlugin(ThemePlugin):
    """Dew-covered web at dawn."""
    name = "legacy-v2-spider-web"

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


class Legacy2SnowGlobePlugin(ThemePlugin):
    """Freshly shaken snow globe."""
    name = "legacy-v2-snow-globe"

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


# ======================================================================
# From whimsical.py
# ======================================================================

class Legacy2CampfirePlugin(ThemePlugin):
    """Campfire at night — embers rising, stars in upper sky."""

    name = "legacy-v2-campfire"

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


class Legacy2AquariumPlugin(ThemePlugin):
    """Tropical fish tank — fish, bubbles, seaweed."""

    name = "legacy-v2-aquarium"

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


class Legacy2CircuitBoardPlugin(ThemePlugin):
    """PCB close-up — strict grid, copper traces, signal packets."""

    name = "legacy-v2-circuit-board"

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


class Legacy2LavaLampPlugin(ThemePlugin):
    """Hypnotic blobs rising and sinking."""

    name = "legacy-v2-lava-lamp"

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


class Legacy2FireflyFieldPlugin(ThemePlugin):
    """Open meadow at dusk — blinking fireflies."""

    name = "legacy-v2-firefly-field"

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


# ======================================================================
# From originals.py
# ======================================================================

class Legacy2NeuralSkyPlugin(ThemePlugin):
    """Default theme — all base behavior."""
    name = "legacy-neural-sky"


class Legacy2ElectricMyceliumPlugin(ThemePlugin):
    """Mycelium network — mostly default with slight tweaks."""
    name = "legacy-v2-electric-mycelium"


class Legacy2MoonwirePlugin(ThemePlugin):
    """Ring layout with moon."""
    name = "legacy-moonwire"

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
        from hermes_neurovision.ascii_art import MOON_ART
        moon_x = max(3, state.width - 10)
        MOON_ART.draw(stdscr, moon_x + 1, 2, color_pairs["bright"], anchor="topleft")


class Legacy2RootsongPlugin(ThemePlugin):
    """Tree root structure."""
    name = "legacy-rootsong"

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
        from hermes_neurovision.scene import Particle
        x = w / 2 + rng.uniform(-4, 4)
        y = h - 3
        vx = rng.uniform(-0.12, 0.12)
        vy = rng.uniform(-0.22, -0.08)
        char = rng.choice(",.;`")
        life = rng.randint(7, 14)
        return Particle(x, y, vx, vy, life, life, char)


class Legacy2CathedralCircuitPlugin(ThemePlugin):
    """Grid layout with arches."""
    name = "legacy-v2-cathedral-circuit"

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


class Legacy2StormCorePlugin(ThemePlugin):
    """Storm bands with lightning."""
    name = "legacy-storm-core"

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
        from hermes_neurovision.scene import Particle
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


class Legacy2StormglassPlugin(ThemePlugin):
    """Glass refraction effect."""
    name = "legacy-stormglass"

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


class Legacy2HybridPlugin(ThemePlugin):
    """Hybrid mode with extra packets."""
    name = "legacy-v2-hybrid"

    def packet_budget(self):
        return 6

    def node_color_key(self, idx, intensity, total):
        if idx % 4 == 0:
            return "accent"
        return "bright" if intensity > 0.65 else "soft"


class Legacy2SpiralGalaxyPlugin(ThemePlugin):
    """3-arm spiral galaxy."""
    name = "legacy-spiral-galaxy"

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
        from hermes_neurovision.scene import Particle
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


class Legacy2BlackHolePlugin(ThemePlugin):
    """Black hole with accretion disk."""
    name = "legacy-black-hole"

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
        from hermes_neurovision.scene import Particle
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