"""5 new cosmic themes for Hermes Vision."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


# ── Quasar ───────────────────────────────────────────────────────────────────

class QuasarPlugin(ThemePlugin):
    """Relativistic jet from an active galactic nucleus (legacy implementation)."""

    name = "legacy-quasar"

    # Internal layout metadata
    _disk_count: int = 0
    _jet_count: int = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)
        nodes = []

        # Accretion disk: wide horizontal ellipse at center
        disk_count = max(14, count // 2)
        self._disk_count = disk_count
        rx = usable_w * 0.38
        ry = usable_h * 0.14
        for i in range(disk_count):
            a = (math.tau * i) / disk_count
            wobble = 1.0 + math.sin(i * 1.1) * 0.06
            nodes.append((cx + math.cos(a) * rx * wobble, cy + math.sin(a) * ry * wobble))

        # Jets: two narrow columns extending from center toward top and bottom
        jet_per_side = max(6, count // 4)
        self._jet_count = jet_per_side * 2
        jet_reach_top = usable_h * 0.46
        jet_reach_bot = usable_h * 0.46
        jet_width = usable_w * 0.04

        for i in range(jet_per_side):
            ratio = (i + 1) / jet_per_side
            # Top jet
            jy = cy - ratio * jet_reach_top
            jx = cx + rng.uniform(-jet_width, jet_width)
            nodes.append((jx, jy))
            # Bottom jet
            jy2 = cy + ratio * jet_reach_bot
            jx2 = cx + rng.uniform(-jet_width, jet_width)
            nodes.append((jx2, jy2))

        # Central nucleus
        nodes.append((cx, cy))
        return nodes

    def build_edges_extra(self, nodes, edges_set):
        dc = self._disk_count
        # Ring around disk
        for i in range(dc):
            edges_set.add(tuple(sorted((i, (i + 1) % dc))))
        # Connect nucleus to disk
        nucleus = len(nodes) - 1
        for i in range(0, dc, 3):
            edges_set.add(tuple(sorted((i, nucleus))))

    def step_nodes(self, nodes, frame, w, h):
        cx = w / 2.0
        cy = h / 2.0
        dc = self._disk_count

        # Disk: fast orbital rotation (like black-hole)
        for i in range(min(dc, len(nodes))):
            dx = nodes[i][0] - cx
            dy = nodes[i][1] - cy
            radius = math.hypot(dx, dy)
            angle = math.atan2(dy, dx) + 0.055
            nodes[i] = (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)

        # Jet nodes: pulse outward from center along jet axis, wrap at edge
        jet_start = dc
        jet_end = dc + self._jet_count
        total = len(nodes)
        for i in range(jet_start, min(jet_end, total - 1)):
            nx, ny = nodes[i]
            dy = ny - cy
            # Push away from center vertically
            if dy >= 0:
                ny += 0.18
                if ny > cy + h * 0.48:
                    ny = cy + 1.0
            else:
                ny -= 0.18
                if ny < cy - h * 0.48:
                    ny = cy - 1.0
            nodes[i] = (nx, ny)

    def step_star(self, star, frame, w, h, rng):
        cx = w / 2.0
        cy = h / 2.0
        dx = star[0] - cx
        dy = star[1] - cy
        dist_y = abs(dy)
        dist_x = abs(dx)

        if dist_y > dist_x * 1.8:
            # Near jet axis — drag along jet direction
            sign = 1 if dy > 0 else -1
            star[1] += sign * 0.12 * star[2]
            # Wrap
            if star[1] > h - 1:
                star[1] = 1.0
                star[0] = cx + rng.uniform(-w * 0.05, w * 0.05)
            elif star[1] < 1:
                star[1] = h - 2.0
                star[0] = cx + rng.uniform(-w * 0.05, w * 0.05)
        else:
            # Near disk plane — orbit like black-hole
            radius = math.hypot(dx * 0.6, dy)
            angle = math.atan2(dy, dx) + 0.008 * star[2]
            radius = radius * (0.997 - 0.001 * star[2])
            if radius < 2.0:
                reset_a = rng.uniform(0, math.tau)
                reset_r = min(w, h) * rng.uniform(0.30, 0.48)
                star[0] = cx + math.cos(reset_a) * reset_r * 1.6
                star[1] = cy + math.sin(reset_a) * reset_r * 0.3
                return True
            star[0] = cx + math.cos(angle) * radius * 1.6
            star[1] = cy + math.sin(angle) * radius * 0.3
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        cx = w / 2.0
        cy = h / 2.0
        # Jet ejecta — fast along vertical axis
        sign = rng.choice([-1, 1])
        x = cx + rng.uniform(-2, 2)
        y = cy + sign * rng.uniform(0, h * 0.05)
        vx = rng.uniform(-0.04, 0.04)
        vy = sign * rng.uniform(0.25, 0.55)
        char = rng.choice("·:.")
        life = rng.randint(6, 14)
        return Particle(x, y, vx, vy, life, life, char)

    def particle_base_chance(self):
        return 0.04

    def particle_life_range(self):
        return (6, 14)

    def pulse_style(self):
        return "rays"

    def pulse_params(self):
        return (0.32, 0.20)

    def node_glyph(self, idx, intensity, total):
        if idx == total - 1:
            return "◉"
        if idx < self._disk_count:
            return "●"
        return "·"

    def node_color_key(self, idx, intensity, total):
        if idx == total - 1:
            return "warning"
        if idx < self._disk_count:
            return "bright" if intensity > 0.6 else "accent"
        return "soft"

    def edge_color_key(self, step, idx_a, frame):
        return "accent" if step % 4 == 0 else "soft"

    def pulse_color_key(self):
        return "accent"

    def particle_color_key(self, age_ratio):
        return "bright" if age_ratio > 0.6 else "soft"

    def star_glyph(self, brightness, char_idx):
        return "·" if brightness > 0.6 else None


# ── Supernova ─────────────────────────────────────────────────────────────────

class SupernovaPlugin(ThemePlugin):
    """Expanding shockwave explosion that loops (legacy implementation)."""

    name = "legacy-supernova"

    _rings: list = []
    _ring_radii_base: list = []
    _cycle_length: int = 180

    def build_nodes(self, w, h, cx, cy, count, rng):
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)
        nodes = []

        # Concentric rings starting tight at center
        num_rings = 5
        nodes_per_ring = max(8, count // num_rings)
        self._rings = []
        self._ring_radii_base = []
        max_r = min(usable_w * 0.45, usable_h * 0.45)

        for ring_idx in range(num_rings):
            ring_start = len(nodes)
            # Start radius — very tight
            base_r = max_r * (ring_idx + 1) / num_rings * 0.08
            self._ring_radii_base.append(base_r)
            for i in range(nodes_per_ring):
                a = (math.tau * i) / nodes_per_ring
                rx = cx + math.cos(a) * base_r * 1.6
                ry = cy + math.sin(a) * base_r * 0.6
                nodes.append((rx, ry))
            ring_end = len(nodes)
            self._rings.append((ring_start, ring_end, nodes_per_ring))

        nodes.append((cx, cy))
        return nodes

    def build_edges_extra(self, nodes, edges_set):
        for ring_start, ring_end, npr in self._rings:
            for i in range(ring_start, ring_end):
                next_i = ring_start + (i - ring_start + 1) % npr
                edges_set.add(tuple(sorted((i, next_i))))

    def step_nodes(self, nodes, frame, w, h):
        cx = w / 2.0
        cy = h / 2.0
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)
        max_r = min(usable_w * 0.45, usable_h * 0.45)
        cycle = self._cycle_length

        # Expansion speeds differ per ring
        speeds = [1.0, 0.85, 0.72, 0.60, 0.48]

        for ring_idx, (ring_start, ring_end, npr) in enumerate(self._rings):
            base_r = self._ring_radii_base[ring_idx]
            # Current expanded radius based on frame
            speed = speeds[ring_idx % len(speeds)]
            t = (frame % cycle) / cycle  # 0..1 within cycle
            current_r = base_r + t * max_r * speed * 10.0

            # If outermost ring hits 90% of max — all rings reset (handled via frame modulo)
            # Wrap individual ring radius
            ring_max = max_r * (1.0 + ring_idx * 0.12)
            if current_r > ring_max * 0.9:
                current_r = base_r

            for i in range(ring_start, min(ring_end, len(nodes) - 1)):
                local_i = i - ring_start
                a = (math.tau * local_i) / npr
                nodes[i] = (
                    cx + math.cos(a) * current_r * 1.55,
                    cy + math.sin(a) * current_r * 0.58,
                )

    def step_star(self, star, frame, w, h, rng):
        cx = w / 2.0
        cy = h / 2.0
        dx = star[0] - cx
        dy = star[1] - cy
        dist = math.hypot(dx, dy)

        # Shockwave radius (outermost ring approximate)
        usable = min(w, h) * 0.45
        cycle = self._cycle_length
        t = (frame % cycle) / cycle
        shockwave_r = usable * t * 10.0
        shockwave_r = min(shockwave_r, usable * 0.9)

        # Stars near the shockwave front get pushed outward
        if dist > 0 and abs(dist - shockwave_r) < usable * 0.15:
            push = 0.20 * star[2]
            nx = dx / dist
            ny = dy / dist
            star[0] += nx * push
            star[1] += ny * push
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        angle = rng.uniform(0, math.tau)
        r = rng.uniform(0, min(w, h) * 0.08)
        x = w / 2 + math.cos(angle) * r
        y = h / 2 + math.sin(angle) * r * 0.5
        speed = rng.uniform(0.18, 0.55)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed * 0.5
        char = rng.choice("*·'")
        life = rng.randint(8, 18)
        return Particle(x, y, vx, vy, life, life, char)

    def particle_base_chance(self):
        return 0.06

    def particle_life_range(self):
        return (8, 18)

    def pulse_style(self):
        return "cloud"

    def pulse_params(self):
        return (0.40, 0.25)

    def node_glyph(self, idx, intensity, total):
        if idx == total - 1:
            return "◉"
        return "●" if intensity > 0.6 else "·"

    def node_color_key(self, idx, intensity, total):
        if idx == total - 1:
            return "warning"
        return "bright" if intensity > 0.7 else "accent"

    def edge_color_key(self, step, idx_a, frame):
        return "bright" if (step + frame) % 7 == 0 else "accent"

    def pulse_color_key(self):
        return "warning"

    def particle_color_key(self, age_ratio):
        return "warning" if age_ratio > 0.5 else "bright"

    def star_glyph(self, brightness, char_idx):
        return "*" if brightness > 0.8 else None


# ── Sol ───────────────────────────────────────────────────────────────────────

class SolPlugin(ThemePlugin):
    """The Sun's surface — convection cells and solar flares (legacy implementation)."""

    name = "legacy-sol"

    _cell_centers: list = []
    _cell_map: list = []  # list of (cell_idx, node_idx, base_angle)

    def build_nodes(self, w, h, cx, cy, count, rng):
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)
        nodes = []
        self._cell_centers = []
        self._cell_map = []

        # 7 convection cell centers spread across the screen
        num_cells = 7
        cell_positions = [
            (cx, cy),
            (cx - usable_w * 0.32, cy - usable_h * 0.22),
            (cx + usable_w * 0.32, cy - usable_h * 0.22),
            (cx - usable_w * 0.32, cy + usable_h * 0.22),
            (cx + usable_w * 0.32, cy + usable_h * 0.22),
            (cx - usable_w * 0.16, cy),
            (cx + usable_w * 0.16, cy),
        ]

        cell_r_x = usable_w * 0.20
        cell_r_y = usable_h * 0.18
        nodes_per_cell = 6  # hexagonal

        for cell_idx, (px, py) in enumerate(cell_positions[:num_cells]):
            self._cell_centers.append((px, py))
            for j in range(nodes_per_cell):
                a = (math.tau * j) / nodes_per_cell
                nx = px + math.cos(a) * cell_r_x
                ny = py + math.sin(a) * cell_r_y
                node_idx = len(nodes)
                nodes.append((nx, ny))
                self._cell_map.append((cell_idx, node_idx, a))

        return nodes

    def build_edges_extra(self, nodes, edges_set):
        # Connect hexagon rings within each cell
        npc = 6
        num_cells = len(self._cell_centers)
        for c in range(num_cells):
            base = c * npc
            for j in range(npc):
                a = base + j
                b = base + (j + 1) % npc
                if a < len(nodes) and b < len(nodes):
                    edges_set.add(tuple(sorted((a, b))))

    def step_nodes(self, nodes, frame, w, h):
        npc = 6
        # Different breathing frequencies per cell
        freqs = [0.04, 0.035, 0.05, 0.038, 0.042, 0.033, 0.048]

        for cell_idx, (px, py) in enumerate(self._cell_centers):
            freq = freqs[cell_idx % len(freqs)]
            breathe = 1.0 + math.sin(frame * freq + cell_idx * 1.1) * 0.12
            base = cell_idx * npc
            for j in range(npc):
                node_idx = base + j
                if node_idx >= len(nodes):
                    break
                _, _, a = self._cell_map[node_idx]
                usable_w = max(12.0, w - 8.0)
                usable_h = max(6.0, h - 6.0)
                cell_r_x = usable_w * 0.20
                cell_r_y = usable_h * 0.18
                nx = px + math.cos(a) * cell_r_x * breathe
                ny = py + math.sin(a) * cell_r_y * breathe
                nodes[node_idx] = (nx, ny)

    def step_star(self, star, frame, w, h, rng):
        # Gentle drift with slight pull toward nearest cell boundary
        if not self._cell_centers:
            return False

        # Find nearest cell center
        best_dist = float('inf')
        best_cx, best_cy = w / 2, h / 2
        for (px, py) in self._cell_centers:
            d = math.hypot(star[0] - px, star[1] - py)
            if d < best_dist:
                best_dist = d
                best_cx, best_cy = px, py

        # Slight drift in random direction
        star[0] += rng.uniform(-0.04, 0.04)
        star[1] += rng.uniform(-0.02, 0.02)

        # Very slight tendency toward cell boundary (~40% of cell radius)
        dx = best_cx - star[0]
        dy = best_cy - star[1]
        dist = math.hypot(dx, dy)
        target_r = min(w, h) * 0.15
        if dist < target_r * 0.5:
            # Too close to center — push outward
            if dist > 0.1:
                star[0] -= (dx / dist) * 0.03
                star[1] -= (dy / dist) * 0.02

        # Wrap stars at screen edges
        if star[0] < 1:
            star[0] = w - 2.0
        elif star[0] > w - 1:
            star[0] = 1.0
        if star[1] < 1:
            star[1] = h - 2.0
        elif star[1] > h - 1:
            star[1] = 1.0
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Solar flares: arc upward from cell boundaries
        if not self._cell_centers:
            return None
        cc = rng.choice(self._cell_centers)
        px, py = cc
        # Start at edge of cell
        a = rng.uniform(0, math.tau)
        cell_r = min(w, h) * 0.12
        x = px + math.cos(a) * cell_r * rng.uniform(0.7, 1.2)
        y = py + math.sin(a) * cell_r * rng.uniform(0.4, 0.8)
        # Arc upward (negative vy = up)
        vx = rng.uniform(-0.10, 0.10)
        vy = rng.uniform(-0.30, -0.10)
        char = rng.choice("*·°")
        life = rng.randint(8, 18)
        return Particle(x, y, vx, vy, life, life, char)

    def particle_base_chance(self):
        return 0.035

    def particle_life_range(self):
        return (8, 18)

    def pulse_style(self):
        return "cloud"

    def pulse_params(self):
        return (0.22, 0.15)

    def edge_glyph(self, dx, dy):
        if abs(dy) < abs(dx) * 0.4:
            return "─"
        elif abs(dx) < abs(dy) * 0.4:
            return "│"
        elif dx * dy < 0:
            return "╱"
        else:
            return "╲"

    def edge_color_key(self, step, idx_a, frame):
        return "bright" if (step + frame) % 11 == 0 else "accent"

    def node_glyph(self, idx, intensity, total):
        # Cell centers are every 6th starting at 0
        if idx % 6 == 0:
            return "◉"
        return "○"

    def node_color_key(self, idx, intensity, total):
        return "warning" if idx % 6 == 0 else "bright"

    def pulse_color_key(self):
        return "warning"

    def particle_color_key(self, age_ratio):
        return "warning" if age_ratio > 0.55 else "bright"

    def star_glyph(self, brightness, char_idx):
        return "·" if brightness > 0.5 else None

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        cx = state.width // 2
        cy = state.height // 2
        # Draw a faint solar corona ring hint
        r_x = int(state.width * 0.42)
        r_y = int(state.height * 0.38)
        corona_chars = "·"
        try:
            pair = curses.color_pair(color_pairs.get("soft", 1))
            for a_deg in range(0, 360, 8):
                a = math.radians(a_deg)
                x = cx + int(math.cos(a) * r_x)
                y = cy + int(math.sin(a) * r_y)
                if 0 < y < state.height - 1 and 0 < x < state.width - 1:
                    stdscr.addstr(y, x, corona_chars, pair)
        except Exception:
            pass


# ── Terra ─────────────────────────────────────────────────────────────────────

class TerraPlugin(ThemePlugin):
    """Earth from orbit — continents, atmosphere, orbiting satellites (legacy implementation)."""

    name = "legacy-terra"

    _earth_r_x: float = 0.0
    _earth_r_y: float = 0.0
    _coast_count: int = 0
    _land_count: int = 0
    _sat_count: int = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)
        nodes = []

        earth_r_x = usable_w * 0.32
        earth_r_y = usable_h * 0.38
        self._earth_r_x = earth_r_x
        self._earth_r_y = earth_r_y

        # Coastline ring (irregular)
        coast_count = max(20, count // 2)
        self._coast_count = coast_count
        for i in range(coast_count):
            a = (math.tau * i) / coast_count
            wobble = 1.0 + rng.uniform(-0.12, 0.12)
            nodes.append((
                cx + math.cos(a) * earth_r_x * wobble,
                cy + math.sin(a) * earth_r_y * wobble,
            ))

        # Land nodes inside the Earth circle
        land_count = max(8, count // 4)
        self._land_count = land_count
        for _ in range(land_count):
            # Random points inside ellipse
            while True:
                lx = cx + rng.uniform(-earth_r_x * 0.85, earth_r_x * 0.85)
                ly = cy + rng.uniform(-earth_r_y * 0.85, earth_r_y * 0.85)
                # Check inside ellipse
                if (lx - cx) ** 2 / earth_r_x ** 2 + (ly - cy) ** 2 / earth_r_y ** 2 < 0.72:
                    nodes.append((lx, ly))
                    break

        # Satellite nodes orbiting outside Earth
        sat_count = max(4, count // 8)
        self._sat_count = sat_count
        sat_r_x = earth_r_x * 1.35
        sat_r_y = earth_r_y * 1.30
        for i in range(sat_count):
            a = (math.tau * i) / sat_count
            nodes.append((
                cx + math.cos(a) * sat_r_x,
                cy + math.sin(a) * sat_r_y,
            ))

        return nodes

    def build_edges_extra(self, nodes, edges_set):
        # Connect coastline ring
        cc = self._coast_count
        for i in range(cc):
            edges_set.add(tuple(sorted((i, (i + 1) % cc))))
        # Satellite links to nearest coast node
        total = len(nodes)
        sat_start = self._coast_count + self._land_count
        for si in range(sat_start, total):
            # Connect each sat to a nearby coast node
            coast_idx = (si - sat_start) * max(1, self._coast_count // max(1, self._sat_count))
            coast_idx = coast_idx % self._coast_count
            edges_set.add(tuple(sorted((si, coast_idx))))

    def step_nodes(self, nodes, frame, w, h):
        cx = w / 2.0
        cy = h / 2.0
        cc = self._coast_count
        lc = self._land_count
        sc = self._sat_count
        total = len(nodes)

        # Coastline and land: very slow Earth rotation
        spin = 0.003
        for i in range(min(cc + lc, total)):
            dx = nodes[i][0] - cx
            dy = nodes[i][1] - cy
            radius = math.hypot(dx, dy)
            angle = math.atan2(dy, dx) + spin
            nodes[i] = (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)

        # Satellites: faster orbit
        sat_start = cc + lc
        for i in range(sat_start, min(sat_start + sc, total)):
            dx = nodes[i][0] - cx
            dy = nodes[i][1] - cy
            radius = math.hypot(dx, dy)
            angle = math.atan2(dy, dx) + 0.035
            nodes[i] = (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)

    def step_star(self, star, frame, w, h, rng):
        cx = w / 2.0
        cy = h / 2.0
        dx = star[0] - cx
        dy = star[1] - cy
        # Check if inside Earth ellipse
        er_x = self._earth_r_x if self._earth_r_x > 0 else w * 0.32
        er_y = self._earth_r_y if self._earth_r_y > 0 else h * 0.38
        inside = (dx ** 2 / er_x ** 2 + dy ** 2 / er_y ** 2) < 0.85

        if inside:
            # Land/ocean texture — mostly fixed, tiny drift
            star[0] += rng.uniform(-0.01, 0.01)
            star[1] += rng.uniform(-0.005, 0.005)
        else:
            # Space — slow drift
            star[0] += rng.uniform(-0.04, 0.04) * star[2]
            star[1] += rng.uniform(-0.02, 0.02) * star[2]

        # Wrap
        if star[0] < 1:
            star[0] = w - 2.0
        elif star[0] > w - 1:
            star[0] = 1.0
        if star[1] < 1:
            star[1] = h - 2.0
        elif star[1] > h - 1:
            star[1] = 1.0
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        cx = w / 2.0
        cy = h / 2.0
        er_x = self._earth_r_x if self._earth_r_x > 0 else w * 0.30
        er_y = self._earth_r_y if self._earth_r_y > 0 else h * 0.35
        # Cloud wisps drifting across Earth surface
        a = rng.uniform(0, math.tau)
        r_ratio = rng.uniform(0.2, 0.85)
        x = cx + math.cos(a) * er_x * r_ratio
        y = cy + math.sin(a) * er_y * r_ratio
        vx = rng.uniform(0.05, 0.15)
        vy = rng.uniform(-0.02, 0.02)
        char = rng.choice("~·")
        life = rng.randint(12, 24)
        return Particle(x, y, vx, vy, life, life, char)

    def particle_base_chance(self):
        return 0.03

    def particle_life_range(self):
        return (12, 24)

    def pulse_style(self):
        return "ripple"

    def pulse_params(self):
        return (0.20, 0.14)

    def edge_glyph(self, dx, dy):
        return "·"

    def edge_color_key(self, step, idx_a, frame):
        # Satellite links are brighter
        sat_start = self._coast_count + self._land_count
        if idx_a >= sat_start:
            return "bright"
        return "soft"

    def node_glyph(self, idx, intensity, total):
        sat_start = self._coast_count + self._land_count
        if idx >= sat_start:
            return "◉"
        if idx < self._coast_count:
            return "·"
        return "░"

    def node_color_key(self, idx, intensity, total):
        sat_start = self._coast_count + self._land_count
        if idx >= sat_start:
            return "bright"
        if idx < self._coast_count:
            return "soft"
        return "accent"

    def pulse_color_key(self):
        return "soft"

    def particle_color_key(self, age_ratio):
        return "bright" if age_ratio > 0.6 else "soft"

    def star_glyph(self, brightness, char_idx):
        return "·" if brightness > 0.65 else None

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        cx = state.width // 2
        cy = state.height // 2
        er_x = int(self._earth_r_x) if self._earth_r_x > 0 else int(state.width * 0.32)
        er_y = int(self._earth_r_y) if self._earth_r_y > 0 else int(state.height * 0.38)

        # Atmosphere glow — ring just outside Earth
        atm_x = er_x + 2
        atm_y = er_y + 1
        try:
            pair = curses.color_pair(color_pairs.get("soft", 1))
            for a_deg in range(0, 360, 5):
                a = math.radians(a_deg)
                x = cx + int(math.cos(a) * atm_x)
                y = cy + int(math.sin(a) * atm_y)
                if 0 < y < state.height - 1 and 0 < x < state.width - 1:
                    stdscr.addstr(y, x, "·", pair)
        except Exception:
            pass

        # Continental mass suggestion — fill lower portion inside Earth with ▓
        try:
            acc_pair = curses.color_pair(color_pairs.get("accent", 1))
            for row_off in range(int(er_y * 0.1), int(er_y * 0.55)):
                y = cy + row_off
                half_w = int(er_x * math.sqrt(max(0, 1 - (row_off / er_y) ** 2)) * 0.45)
                for col_off in range(-half_w, half_w + 1, 3):
                    x = cx + col_off
                    if 0 < y < state.height - 1 and 0 < x < state.width - 1:
                        stdscr.addstr(y, x, "▓", acc_pair)
        except Exception:
            pass


# ── Binary Star ───────────────────────────────────────────────────────────────

class BinaryStarPlugin(ThemePlugin):
    """Two stars orbiting each other around their shared center of mass (legacy implementation)."""

    name = "legacy-binary-star"

    _inner_a: int = 0
    _outer_a: int = 0
    _inner_b: int = 0
    _outer_b: int = 0
    _star_a_offset_x: float = 0.0
    _star_a_offset_y: float = 0.0
    _star_b_offset_x: float = 0.0
    _star_b_offset_y: float = 0.0

    def build_nodes(self, w, h, cx, cy, count, rng):
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)
        nodes = []

        # The two star centers orbit the screen center
        orbit_r_x = usable_w * 0.22
        orbit_r_y = usable_h * 0.18

        # Initial positions (will animate in step_nodes)
        # Star A: left side, Star B: right side
        sa_x = cx - orbit_r_x
        sa_y = cy
        sb_x = cx + orbit_r_x
        sb_y = cy

        # Rings around Star A
        inner_count_a = 8
        outer_count_a = 10
        ring_r_inner = min(usable_w, usable_h) * 0.10
        ring_r_outer = min(usable_w, usable_h) * 0.18

        # Star A center node (idx 0)
        nodes.append((sa_x, sa_y))
        # Inner ring A
        for i in range(inner_count_a):
            a = (math.tau * i) / inner_count_a
            nodes.append((sa_x + math.cos(a) * ring_r_inner, sa_y + math.sin(a) * ring_r_inner * 0.55))
        self._inner_a = inner_count_a

        # Outer ring A
        for i in range(outer_count_a):
            a = (math.tau * i) / outer_count_a
            nodes.append((sa_x + math.cos(a) * ring_r_outer, sa_y + math.sin(a) * ring_r_outer * 0.55))
        self._outer_a = outer_count_a

        # Star B center node
        nodes.append((sb_x, sb_y))
        # Inner ring B
        for i in range(inner_count_a):
            a = (math.tau * i) / inner_count_a
            nodes.append((sb_x + math.cos(a) * ring_r_inner, sb_y + math.sin(a) * ring_r_inner * 0.55))
        self._inner_b = inner_count_a

        # Outer ring B
        for i in range(outer_count_a):
            a = (math.tau * i) / outer_count_a
            nodes.append((sb_x + math.cos(a) * ring_r_outer, sb_y + math.sin(a) * ring_r_outer * 0.55))
        self._outer_b = outer_count_a

        return nodes

    def build_edges_extra(self, nodes, edges_set):
        # Star A system edges
        # center->inner ring
        a_center = 0
        a_inner_start = 1
        a_inner_end = 1 + self._inner_a
        a_outer_start = a_inner_end
        a_outer_end = a_outer_start + self._outer_a

        for i in range(a_inner_start, a_inner_end):
            edges_set.add(tuple(sorted((a_center, i))))
            edges_set.add(tuple(sorted((i, a_inner_start + (i - a_inner_start + 1) % self._inner_a))))

        for i in range(a_outer_start, a_outer_end):
            ring_i = i - a_outer_start
            edges_set.add(tuple(sorted((i, a_outer_start + (ring_i + 1) % self._outer_a))))

        # Star B system edges
        b_center = a_outer_end
        b_inner_start = b_center + 1
        b_inner_end = b_inner_start + self._inner_b
        b_outer_start = b_inner_end
        b_outer_end = b_outer_start + self._outer_b

        for i in range(b_inner_start, b_inner_end):
            edges_set.add(tuple(sorted((b_center, i))))
            edges_set.add(tuple(sorted((i, b_inner_start + (i - b_inner_start + 1) % self._inner_b))))

        for i in range(b_outer_start, b_outer_end):
            ring_i = i - b_outer_start
            edges_set.add(tuple(sorted((i, b_outer_start + (ring_i + 1) % self._outer_b))))

    def step_nodes(self, nodes, frame, w, h):
        cx = w / 2.0
        cy = h / 2.0
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)

        # System orbit around screen center
        sys_orbit_x = usable_w * 0.22
        sys_orbit_y = usable_h * 0.18
        sys_angle = frame * 0.012

        # Star A orbits one way, Star B the opposite
        sa_cx = cx + math.cos(sys_angle) * sys_orbit_x
        sa_cy = cy + math.sin(sys_angle) * sys_orbit_y * 0.55
        sb_cx = cx + math.cos(sys_angle + math.pi) * sys_orbit_x
        sb_cy = cy + math.sin(sys_angle + math.pi) * sys_orbit_y * 0.55

        ring_r_inner = min(usable_w, usable_h) * 0.10
        ring_r_outer = min(usable_w, usable_h) * 0.18

        # Star A center
        if len(nodes) > 0:
            nodes[0] = (sa_cx, sa_cy)

        # Inner ring A — fast rotation
        a_inner_start = 1
        a_inner_end = 1 + self._inner_a
        for i in range(a_inner_start, min(a_inner_end, len(nodes))):
            local_i = i - a_inner_start
            a = (math.tau * local_i) / self._inner_a + frame * 0.08
            nodes[i] = (
                sa_cx + math.cos(a) * ring_r_inner,
                sa_cy + math.sin(a) * ring_r_inner * 0.55,
            )

        # Outer ring A — slower rotation
        a_outer_start = a_inner_end
        a_outer_end = a_outer_start + self._outer_a
        for i in range(a_outer_start, min(a_outer_end, len(nodes))):
            local_i = i - a_outer_start
            a = (math.tau * local_i) / self._outer_a + frame * 0.04
            nodes[i] = (
                sa_cx + math.cos(a) * ring_r_outer,
                sa_cy + math.sin(a) * ring_r_outer * 0.55,
            )

        # Star B center
        b_center = a_outer_end
        if b_center < len(nodes):
            nodes[b_center] = (sb_cx, sb_cy)

        # Inner ring B — fast, opposite direction
        b_inner_start = b_center + 1
        b_inner_end = b_inner_start + self._inner_b
        for i in range(b_inner_start, min(b_inner_end, len(nodes))):
            local_i = i - b_inner_start
            a = (math.tau * local_i) / self._inner_b - frame * 0.08
            nodes[i] = (
                sb_cx + math.cos(a) * ring_r_inner,
                sb_cy + math.sin(a) * ring_r_inner * 0.55,
            )

        # Outer ring B — slower, opposite
        b_outer_start = b_inner_end
        b_outer_end = b_outer_start + self._outer_b
        for i in range(b_outer_start, min(b_outer_end, len(nodes))):
            local_i = i - b_outer_start
            a = (math.tau * local_i) / self._outer_b - frame * 0.04
            nodes[i] = (
                sb_cx + math.cos(a) * ring_r_outer,
                sb_cy + math.sin(a) * ring_r_outer * 0.55,
            )

    def step_star(self, star, frame, w, h, rng):
        cx = w / 2.0
        cy = h / 2.0
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)

        sys_orbit_x = usable_w * 0.22
        sys_orbit_y = usable_h * 0.18
        sys_angle = frame * 0.012

        sa_cx = cx + math.cos(sys_angle) * sys_orbit_x
        sa_cy = cy + math.sin(sys_angle) * sys_orbit_y * 0.55
        sb_cx = cx + math.cos(sys_angle + math.pi) * sys_orbit_x
        sb_cy = cy + math.sin(sys_angle + math.pi) * sys_orbit_y * 0.55

        dist_a = math.hypot(star[0] - sa_cx, star[1] - sa_cy)
        dist_b = math.hypot(star[0] - sb_cx, star[1] - sb_cy)
        influence_r = min(w, h) * 0.30

        if dist_a < dist_b and dist_a < influence_r:
            # Orbit around Star A
            dx = star[0] - sa_cx
            dy = star[1] - sa_cy
            radius = math.hypot(dx, dy)
            angle = math.atan2(dy, dx) + 0.006 * star[2]
            radius = radius * (0.9985 - 0.001 * star[2])
            if radius < 2.0:
                reset_a = rng.uniform(0, math.tau)
                reset_r = influence_r * rng.uniform(0.2, 0.45)
                star[0] = sa_cx + math.cos(reset_a) * reset_r
                star[1] = sa_cy + math.sin(reset_a) * reset_r * 0.55
                return True
            star[0] = sa_cx + math.cos(angle) * radius
            star[1] = sa_cy + math.sin(angle) * radius * 0.55
        elif dist_b < influence_r:
            # Orbit around Star B
            dx = star[0] - sb_cx
            dy = star[1] - sb_cy
            radius = math.hypot(dx, dy)
            angle = math.atan2(dy, dx) - 0.006 * star[2]  # opposite direction
            radius = radius * (0.9985 - 0.001 * star[2])
            if radius < 2.0:
                reset_a = rng.uniform(0, math.tau)
                reset_r = influence_r * rng.uniform(0.2, 0.45)
                star[0] = sb_cx + math.cos(reset_a) * reset_r
                star[1] = sb_cy + math.sin(reset_a) * reset_r * 0.55
                return True
            star[0] = sb_cx + math.cos(angle) * radius
            star[1] = sb_cy + math.sin(angle) * radius * 0.55
        else:
            # Far from both — slow general drift
            star[0] += rng.uniform(-0.06, 0.06) * star[2]
            star[1] += rng.uniform(-0.03, 0.03) * star[2]

        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        cx = w / 2.0
        cy = h / 2.0
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)
        sys_orbit_x = usable_w * 0.22
        sys_orbit_y = usable_h * 0.18

        # Matter transfer — particles arc between the two stars through midpoint
        sign = rng.choice([-1, 1])
        # Start near Star A or B
        start_x = cx + sign * sys_orbit_x + rng.uniform(-2, 2)
        start_y = cy + rng.uniform(-2, 2)
        # Arc toward the other star via cx
        end_x = cx - sign * sys_orbit_x
        # velocity roughly toward midpoint then curving
        vx = -sign * rng.uniform(0.12, 0.28)
        vy = rng.uniform(-0.08, 0.08)
        char = rng.choice("·:*")
        life = rng.randint(10, 20)
        return Particle(start_x, start_y, vx, vy, life, life, char)

    def particle_base_chance(self):
        return 0.035

    def particle_life_range(self):
        return (10, 20)

    def pulse_style(self):
        return "spoked"

    def pulse_params(self):
        return (0.26, 0.16)

    def node_glyph(self, idx, intensity, total):
        a_center = 0
        a_outer_end = 1 + self._inner_a + self._outer_a
        b_center = a_outer_end
        # Star centers
        if idx == a_center or idx == b_center:
            return "◉"
        # Inner rings
        a_inner_end = 1 + self._inner_a
        b_inner_end = b_center + 1 + self._inner_b
        if a_center < idx < a_inner_end or b_center < idx < b_inner_end:
            return "●"
        return "·"

    def node_color_key(self, idx, intensity, total):
        a_outer_end = 1 + self._inner_a + self._outer_a
        b_center = a_outer_end
        # Star A system
        if idx < b_center:
            return "accent"
        # Star B system
        return "bright"

    def edge_color_key(self, step, idx_a, frame):
        a_outer_end = 1 + self._inner_a + self._outer_a
        if idx_a < a_outer_end:
            return "accent"
        return "bright"

    def pulse_color_key(self):
        return "bright"

    def particle_color_key(self, age_ratio):
        return "bright" if age_ratio > 0.5 else "accent"

    def star_glyph(self, brightness, char_idx):
        return "·" if brightness > 0.55 else None


# ── Register all plugins ──────────────────────────────────────────────────────

for _cls in [
    QuasarPlugin,
    SupernovaPlugin,
    SolPlugin,
    TerraPlugin,
    BinaryStarPlugin,
]:
    register(_cls())
