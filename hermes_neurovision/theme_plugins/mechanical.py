"""Mechanical and retro theme plugins for Hermes Vision."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


class ClockworkPlugin(ThemePlugin):
    """Victorian steampunk mechanism."""
    name = "clockwork"

    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        # Gear centers arranged in meshing pairs
        gear_centers = [
            (cx, cy),
            (cx + w * 0.18, cy),
            (cx - w * 0.18, cy),
            (cx + w * 0.09, cy + h * 0.18),
            (cx - w * 0.09, cy - h * 0.18),
        ]
        sizes = [6, 4, 4, 3, 3]  # nodes per gear
        for (gx, gy), gsize in zip(gear_centers, sizes):
            r = gsize * 0.9
            for i in range(gsize):
                a = (math.tau * i) / gsize
                nodes.append((gx + math.cos(a) * r, gy + math.sin(a) * r * 0.6))
        # Fill remainder
        while len(nodes) < count:
            gx, gy = rng.choice(gear_centers)
            a = rng.uniform(0, math.tau)
            r = rng.uniform(1.5, 4.0)
            nodes.append((gx + math.cos(a) * r, gy + math.sin(a) * r * 0.5))
        return nodes[:count]

    def step_nodes(self, nodes, frame, w, h):
        # Nodes rotate around gear centers — counter-rotating adjacent gears
        gear_centers = [
            (w / 2.0, h / 2.0),
            (w / 2.0 + w * 0.18, h / 2.0),
            (w / 2.0 - w * 0.18, h / 2.0),
            (w / 2.0 + w * 0.09, h / 2.0 + h * 0.18),
            (w / 2.0 - w * 0.09, h / 2.0 - h * 0.18),
        ]
        gear_sizes = [6, 4, 4, 3, 3]
        gear_speeds = [0.02, -0.032, -0.032, 0.04, 0.04]  # counter-rotate adjacent
        node_idx = 0
        for (gx, gy), gsize, speed in zip(gear_centers, gear_sizes, gear_speeds):
            for _ in range(gsize):
                if node_idx >= len(nodes):
                    break
                dx = nodes[node_idx][0] - gx
                dy = nodes[node_idx][1] - gy
                radius = max(0.5, math.hypot(dx, dy))
                angle = math.atan2(dy, dx) + speed
                nodes[node_idx] = (gx + math.cos(angle) * radius, gy + math.sin(angle) * radius)
                node_idx += 1

    def step_star(self, star, frame, w, h, rng):
        # Clockwork sparks and steam particles drifting everywhere
        star[0] += rng.uniform(-0.08, 0.08)
        star[1] += rng.uniform(-0.10, 0.05)  # gentle upward bias
        # Wrap around edges - keep sparks everywhere
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
        from hermes_neurovision.scene import Particle
        # Steam puffs rising from pressure valves
        valve_x = rng.choice([w * 0.3, w * 0.5, w * 0.7])
        x = valve_x + rng.uniform(-1, 1)
        y = h * 0.5 + rng.uniform(-2, 2)
        vx = rng.uniform(-0.04, 0.04)
        vy = rng.uniform(-0.12, -0.05)
        char = rng.choice("~°")
        life = rng.randint(8, 16)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        return "═" if abs(dx) > abs(dy) * 0.5 else "─"

    def node_glyph(self, idx, intensity, total):
        if idx % 3 == 0:
            return "⚙"
        elif idx % 3 == 1:
            return "◎"
        return "○"

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        from hermes_neurovision.ascii_art import CLOCK_FACE
        
        frame = getattr(state, "frame", 0)
        w = state.width
        h = state.height
        
        # Large clock face in the center-top
        cx = max(7, w // 2 - 6)
        cy = 2
        CLOCK_FACE.draw(stdscr, cx, cy, color_pairs.get("bright", 1), anchor="topleft")
        
        # Giant pendulum swinging across entire screen
        # Swing angle: -45 to +45 degrees
        swing_angle = math.sin(frame * 0.04) * (math.pi / 4)  # -pi/4 to +pi/4
        
        # Pendulum anchor at top center
        anchor_x = w // 2
        anchor_y = 0
        
        # Pendulum length (goes almost to bottom)
        pendulum_length = h - 3
        
        # Calculate bob position
        bob_x = int(anchor_x + math.sin(swing_angle) * pendulum_length * 0.4)
        bob_y = int(anchor_y + math.cos(swing_angle) * pendulum_length)
        
        # Clamp to screen bounds
        bob_x = max(1, min(w - 2, bob_x))
        bob_y = max(1, min(h - 2, bob_y))
        
        # Draw the pendulum rod (line from anchor to bob)
        color = curses.color_pair(color_pairs.get("accent", 1))
        
        # Draw line segments
        steps = max(abs(bob_x - anchor_x), abs(bob_y - anchor_y))
        if steps > 0:
            for step in range(steps + 1):
                t = step / max(1, steps)
                x = int(anchor_x + (bob_x - anchor_x) * t)
                y = int(anchor_y + (bob_y - anchor_y) * t)
                if 0 <= x < w and 0 <= y < h:
                    try:
                        if step == 0:
                            stdscr.addstr(y, x, "┬", color)  # Anchor point
                        elif step < steps:
                            stdscr.addstr(y, x, "│", color)  # Rod
                        else:
                            # Pendulum bob (large)
                            stdscr.addstr(y, x, "●", color | curses.A_BOLD)
                    except curses.error:
                        pass


class CoralReefPlugin(ThemePlugin):
    """Vibrant underwater reef."""
    name = "coral-reef"

    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        # Coral formations in bottom 50%
        coral_count = count * 2 // 3
        for _ in range(coral_count):
            x = rng.uniform(4, w - 5)
            y = rng.uniform(h * 0.50, h - 2)
            nodes.append((x, y))
        # Sea creatures above
        creature_count = count - coral_count
        for _ in range(creature_count):
            x = rng.uniform(4, w - 5)
            y = rng.uniform(2, h * 0.50)
            nodes.append((x, y))
        return nodes

    def step_star(self, star, frame, w, h, rng):
        # Light rays from surface — shift slightly downward
        star[1] += 0.04
        if star[1] >= h - 1:
            star[1] = rng.uniform(0, 3)
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        if rng.random() < 0.7:
            # Tiny fish/plankton drifting in sinusoidal currents
            x = rng.uniform(2, w - 3)
            y = rng.uniform(3, h - 3)
            vx = rng.uniform(-0.12, 0.12)
            vy = math.sin(x * 0.3) * 0.05
            char = rng.choice("·°")
            life = rng.randint(8, 18)
        else:
            # Bubble rising
            x = rng.uniform(4, w - 5)
            y = h - rng.uniform(2, 6)
            vx = rng.uniform(-0.03, 0.03)
            vy = rng.uniform(-0.12, -0.06)
            char = "○"
            life = rng.randint(6, 14)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        if abs(dy) > abs(dx) * 1.2:
            return "│"
        elif dx * dy < 0:
            return "╱"
        return "╲"

    def node_glyph(self, idx, intensity, total):
        coral_count = total * 2 // 3
        if idx < coral_count:
            return "❋" if intensity > 0.5 else "✿"
        return "►"

    def edge_color_key(self, step, idx_a, frame):
        return "accent" if (step + frame) % 2 == 0 else "bright"


class AntColonyPlugin(ThemePlugin):
    """Underground tunnel network."""
    name = "ant-colony"

    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        # Chambers at different depths (underground — skip top 20% for surface)
        depths = [0.3, 0.45, 0.60, 0.75, 0.88]
        chambers_per_depth = max(2, count // len(depths))
        for depth in depths:
            y_base = h * depth
            for i in range(chambers_per_depth):
                x = rng.uniform(w * 0.1, w * 0.9)
                y = y_base + rng.uniform(-h * 0.04, h * 0.04)
                nodes.append((x, y))
        # Center queen chamber
        nodes.insert(0, (cx, h * 0.55))
        while len(nodes) < count:
            nodes.append((rng.uniform(4, w - 5), rng.uniform(h * 0.3, h - 2)))
        return nodes[:count]

    def step_star(self, star, frame, w, h, rng):
        # Underground dirt texture — sparse, no drift
        return False

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        if rng.random() < 0.5 and nodes:
            # Dirt being excavated, moving outward from a node
            nx, ny = rng.choice(nodes)
            x = nx + rng.uniform(-1, 1)
            y = ny + rng.uniform(-0.5, 0.5)
            vx = rng.uniform(-0.15, 0.15)
            vy = rng.uniform(-0.05, 0.05)
            char = rng.choice("·.")
        else:
            # Tiny ant
            x = rng.uniform(4, w - 5)
            y = rng.uniform(h * 0.25, h - 2)
            vx = rng.uniform(-0.2, 0.2)
            vy = rng.uniform(-0.05, 0.05)
            char = "·"
        life = rng.randint(5, 12)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        return "║" if abs(dy) > abs(dx) else "═"

    def node_glyph(self, idx, intensity, total):
        if idx == 0:
            return "◉"  # Queen chamber
        elif idx % 4 == 1:
            return "●"  # Food storage
        elif idx % 4 == 2:
            return "○"  # Nursery
        return "◌"

    def packet_budget(self):
        return 8

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        w = state.width
        h = state.height
        # Surface with grass at top
        ground_y = int(h * 0.22)
        soft_pair = curses.color_pair(color_pairs.get("soft", 1))
        accent_pair = curses.color_pair(color_pairs.get("accent", 1))
        # Ground line
        for x in range(min(w - 1, w)):
            try:
                stdscr.addch(ground_y, x, "─", soft_pair)
            except curses.error:
                pass
        # Grass tufts
        for x in range(1, w - 1, 3):
            try:
                stdscr.addch(ground_y - 1, x, "∿", accent_pair)
            except curses.error:
                pass


class SatelliteOrbitPlugin(ThemePlugin):
    """Earth from space with orbiting satellites."""
    name = "satellite-orbit"

    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        # Orbital rings (3-4), each with satellites
        orbits = [
            (h * 0.20, 6, 0.012),
            (h * 0.30, 8, 0.008),
            (h * 0.40, 10, 0.005),
        ]
        for orbit_r, sat_count, _speed in orbits:
            for i in range(sat_count):
                a = (math.tau * i) / sat_count
                x = cx + math.cos(a) * orbit_r * (w / h) * 0.9
                y = cy * 0.5 + math.sin(a) * orbit_r * 0.45
                nodes.append((x, y))
        # Ground stations
        ground_y = h * 0.72
        for i in range(3):
            nodes.append((cx + (i - 1) * w * 0.15, ground_y))
        while len(nodes) < count:
            a = rng.uniform(0, math.tau)
            r = rng.uniform(h * 0.15, h * 0.45)
            nodes.append((cx + math.cos(a) * r, cy * 0.5 + math.sin(a) * r * 0.4))
        return nodes[:count]

    def step_nodes(self, nodes, frame, w, h):
        cx = w / 2.0
        cy = h * 0.35
        orbit_speeds = [0.012, 0.008, 0.005]
        orbit_counts = [6, 8, 10]
        node_idx = 0
        for speed, orbit_count in zip(orbit_speeds, orbit_counts):
            for _ in range(orbit_count):
                if node_idx >= len(nodes):
                    break
                dx = nodes[node_idx][0] - cx
                dy = (nodes[node_idx][1] - cy) / 0.45
                radius = max(0.5, math.hypot(dx, dy * (h / w) * 0.9))
                angle = math.atan2(dy, dx) + speed
                nodes[node_idx] = (
                    cx + math.cos(angle) * radius,
                    cy + math.sin(angle) * radius * 0.45,
                )
                node_idx += 1

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Communication beams between satellites
        if nodes:
            nx, ny = rng.choice(nodes)
            x = nx + rng.uniform(-1, 1)
            y = ny + rng.uniform(-0.5, 0.5)
        else:
            x = rng.uniform(4, w - 5)
            y = rng.uniform(2, h * 0.7)
        vx = rng.uniform(-0.15, 0.15)
        vy = rng.uniform(-0.08, 0.08)
        char = rng.choice("·*")
        life = rng.randint(4, 10)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        if abs(dy) < abs(dx) * 0.2:
            return "─"
        elif abs(dx) < abs(dy) * 0.2:
            return "·"
        elif dx * dy < 0:
            return "╱"
        return "╲"

    def star_glyph(self, brightness, char_idx):
        # Starfield only in upper 50% — can't filter by position here, use sparse chars
        return "·" if brightness < 0.4 else None

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        w = state.width
        h = state.height
        earth_top = int(h * 0.65)
        base_pair = curses.color_pair(color_pairs.get("base", 1))
        soft_pair = curses.color_pair(color_pairs.get("soft", 1))
        accent_pair = curses.color_pair(color_pairs.get("accent", 1))
        # Curved Earth edge
        for x in range(w - 1):
            ratio = (x - w / 2.0) / (w / 2.0)
            curve = int(ratio * ratio * h * 0.08)
            y = earth_top + curve
            if 0 <= y < h - 1:
                ch = "═" if abs(ratio) < 0.3 else ("╱" if x < w // 2 else "╲")
                try:
                    stdscr.addch(y, x, ch, accent_pair)
                except curses.error:
                    pass
            # Fill below with land/ocean blocks
            for fill_y in range(y + 1, min(h - 1, y + 4)):
                density = (fill_y - y)
                ch2 = "░" if density == 1 else ("▒" if density == 2 else "▓")
                try:
                    stdscr.addch(fill_y, x, ch2, base_pair)
                except curses.error:
                    pass

    def node_glyph(self, idx, intensity, total):
        ground_start = total - 3
        if idx >= ground_start:
            return "╋"
        return "◇" if intensity > 0.6 else "▫"


class StarfallPlugin(ThemePlugin):
    """Meteor shower (legacy implementation)."""
    name = "legacy-starfall"

    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        # Constellation anchor points — sparse, fixed, in upper 70%
        for _ in range(count):
            x = rng.uniform(4, w - 5)
            y = rng.uniform(2, h * 0.70)
            nodes.append((x, y))
        return nodes

    def step_star(self, star, frame, w, h, rng):
        # Stars twinkle — briefly brighten based on sin(frame * unique_rate)
        unique_rate = 0.03 + (star[3] % 0.05)
        # Shift brightness phase — handled via char_idx in star_glyph
        # Just nudge brightness: star[2] is brightness-like
        star[2] = max(0.1, min(1.0, star[2] + math.sin(frame * unique_rate) * 0.02))
        return False  # Use default position drift

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Meteors — fast diagonal streaks
        x = rng.uniform(0, w - 1)
        y = rng.uniform(0, h * 0.5)
        angle = rng.uniform(math.pi * 0.55, math.pi * 0.75)
        speed = rng.uniform(1.2, 2.4)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed * 0.5
        char = rng.choice("━╲╱─")
        life = rng.randint(3, 6)
        return Particle(x, y, vx, vy, life, life, char)

    def particle_base_chance(self):
        return 0.04

    def particle_life_range(self):
        return (3, 6)

    def edge_glyph(self, dx, dy):
        return "·"

    def edge_color_key(self, step, idx_a, frame):
        return "base"

    def pulse_params(self):
        return (0.34, 0.14)

    def node_glyph(self, idx, intensity, total):
        return "✦" if intensity > 0.7 else ("*" if intensity > 0.4 else "·")

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        w = state.width
        h = state.height
        # Horizon treeline at bottom
        soft_pair = curses.color_pair(color_pairs.get("soft", 1))
        tree_y = h - 3
        for x in range(1, w - 1, 2):
            try:
                stdscr.addch(tree_y, x, "♠", soft_pair)
            except curses.error:
                pass
            try:
                stdscr.addch(tree_y + 1, x, "│", soft_pair)
            except curses.error:
                pass


# ── Register all mechanical plugins ──────────────────────────────

for _cls in [
    ClockworkPlugin, CoralReefPlugin, AntColonyPlugin,
    SatelliteOrbitPlugin, StarfallPlugin,
]:
    register(_cls())
