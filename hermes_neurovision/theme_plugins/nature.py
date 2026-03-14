"""Nature-themed plugins for Hermes Vision."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


class DeepAbyssPlugin(ThemePlugin):
    """Bioluminescent deep ocean — scattered organisms, bubble drift, hydrothermal vent."""

    name = "deep-abyss"

    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        usable_w = max(12.0, w - 6.0)
        usable_h = max(6.0, h - 4.0)
        for i in range(count):
            # Vertical bias: deeper (higher y) = denser clustering
            t = rng.random() ** 0.6  # skew toward higher values (bottom)
            y = 2.0 + t * usable_h
            # Horizontal scatter, slightly narrower toward top
            x_spread = usable_w * (0.4 + 0.5 * t)
            x = cx + rng.uniform(-x_spread * 0.5, x_spread * 0.5)
            nodes.append((x, y))
        return nodes

    def step_star(self, star, frame, w, h, rng):
        # Sparse bubbles drifting upward slowly
        star[1] -= 0.04 * star[2]  # move upward
        star[0] += math.sin(frame * 0.04 + star[3]) * 0.015  # gentle sway
        if star[1] < 1.0:
            # Respawn at bottom
            star[0] = rng.uniform(2.0, max(3.0, w - 3.0))
            star[1] = float(h - 2)
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        if not nodes:
            x = rng.uniform(2, max(3, w - 3))
            y = rng.uniform(2, max(3, h - 3))
        else:
            base = rng.choice(nodes)
            x = base[0] + rng.uniform(-1.5, 1.5)
            y = base[1] + rng.uniform(-1.0, 1.0)
        vx = rng.uniform(-0.04, 0.04)
        vy = rng.uniform(-0.06, -0.02)  # rise upward
        char = rng.choice("*\u2727\u00b7.")
        life = rng.randint(4, 8)  # rapid fade
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        return "~" if abs(dy) < abs(dx) * 0.6 else "\u2248"

    def edge_color_key(self, step, idx_a, frame):
        return "base"

    def particle_base_chance(self):
        return 0.035

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        from hermes_neurovision.ascii_art import HYDROTHERMAL_VENT
        vent_x = max(4, state.width // 2)
        vent_y = max(4, state.height - HYDROTHERMAL_VENT.height - 1)
        HYDROTHERMAL_VENT.draw(
            stdscr, vent_x, vent_y, color_pairs["base"], anchor="topleft"
        )

    def star_glyph(self, brightness, char_idx):
        return "\u2609" if brightness > 0.8 else "\u25c9" if brightness > 0.5 else "\u00b0"

    def node_glyph(self, idx, intensity, total):
        return "\u262a" if idx % 7 == 0 else "\u25c9"

    def node_color_key(self, idx, intensity, total):
        return "bright" if intensity > 0.7 else "soft"

    def particle_color_key(self, age_ratio):
        return "bright" if age_ratio > 0.7 else "soft"


class StormSeaPlugin(ThemePlugin):
    """Violent ocean surface — wave curves across screen, diagonal rain, spray particles."""

    name = "storm-sea"

    def build_nodes(self, w, h, cx, cy, count, rng):
        # 3-4 wave CURVES across screen — each is a sine wave with different amplitude/phase
        usable_w = max(12.0, w - 6.0)
        wave_count = rng.randint(3, 4)
        nodes = []
        per_wave = max(4, count // wave_count)
        for wave_idx in range(wave_count):
            # Different amplitude, phase, and vertical position for each wave
            amplitude = 2.0 + wave_idx * 1.5 + rng.uniform(-0.5, 0.5)
            phase = rng.uniform(0, math.tau)
            freq = 0.10 + wave_idx * 0.04
            base_y = 2.0 + wave_idx * (max(6.0, h - 6.0) / max(1, wave_count - 1))
            for j in range(per_wave):
                t = j / max(1, per_wave - 1)
                x = 3.0 + t * usable_w
                wave_y = base_y + math.sin(x * freq + phase) * amplitude
                wave_y += rng.uniform(-0.5, 0.5)
                nodes.append((x, wave_y))
        # Fill remaining
        while len(nodes) < count:
            x = rng.uniform(3, max(4, w - 4))
            y = rng.uniform(2, max(3, h - 3))
            nodes.append((x, y))
        return nodes[:count]

    def step_nodes(self, nodes, frame, w, h):
        # Animate nodes along their wave curves with horizontal oscillation
        # Different wave rows move at different speeds
        wave_count = 4
        for i, (ox, oy) in enumerate(nodes):
            # Determine wave index by rough y-position grouping
            wave_idx = i % wave_count
            speed = 0.015 + wave_idx * 0.008
            # Horizontal oscillation
            new_x = ox + math.sin(frame * speed * 0.5 + wave_idx) * 0.3
            new_x = max(2.0, min(float(w - 2), new_x))
            new_y = oy + math.sin(frame * speed + wave_idx * 1.2) * 0.15
            nodes[i] = (new_x, new_y)

    def step_star(self, star, frame, w, h, rng):
        # Rain falls DIAGONALLY left-to-right (not straight down)
        star[1] += 0.22 * star[2]   # fall down
        star[0] += 0.08 * star[2]   # drift right (diagonal)
        if star[1] > h - 1 or star[0] > w - 1:
            star[0] = rng.uniform(0.0, float(w))
            star[1] = 0.0
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Spray launching upward from wave crests
        if nodes:
            crest = rng.choice(nodes[:max(1, len(nodes) // 2)])
            x = crest[0] + rng.uniform(-2, 2)
            y = crest[1]
        else:
            x = rng.uniform(2, max(3, w - 3))
            y = h * 0.4
        vx = rng.uniform(-0.15, 0.15)
        vy = rng.uniform(-0.20, -0.06)
        char = rng.choice("\u00b7.'")
        life = rng.randint(5, 10)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        return "~"  # wave character always

    def pulse_style(self):
        return "rays"  # lightning bolts

    def pulse_params(self):
        return (0.34, 0.18)

    def pulse_color_key(self):
        return "warning"

    def node_glyph(self, idx, intensity, total):
        return "\u25cc" if intensity < 0.5 else "\u25c9"

    def node_color_key(self, idx, intensity, total):
        return "bright" if intensity > 0.7 else "soft"

    def star_glyph(self, brightness, char_idx):
        return "|" if brightness > 0.6 else "/" if brightness > 0.3 else "'"

    def particle_color_key(self, age_ratio):
        return "bright" if age_ratio > 0.5 else "soft"


class DarkForestPlugin(ThemePlugin):
    """Dense canopy with fireflies — 8-12 tree trunks filling screen, falling leaves, ground terrain."""

    name = "dark-forest"

    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        usable_h = max(6.0, h - 6.0)
        # 8-12 tree trunks spread across full width
        trunk_count = rng.randint(8, 12)
        spacing = max(4.0, (w - 6.0) / max(1, trunk_count - 1))

        for t in range(trunk_count):
            tx = 3.0 + t * spacing
            # Trunk: 3-4 nodes vertically
            trunk_levels = rng.randint(3, 4)
            trunk_bottom = usable_h * 0.90
            trunk_top = usable_h * 0.45
            for row in range(trunk_levels):
                frac = row / max(1, trunk_levels - 1)
                y = 2.0 + trunk_bottom - frac * (trunk_bottom - trunk_top)
                sway = math.sin(row * 0.6 + t * 0.8) * 1.0
                nodes.append((tx + sway, y))
            # Canopy nodes spreading above trunk top
            canopy_top_y = 2.0 + trunk_top - 3.0
            canopy_spread = 3.0 + t * 0.3
            for c in range(5):
                offset = (c - 2) * canopy_spread * 0.5
                y = canopy_top_y + rng.uniform(-2.0, 2.0)
                y = max(2.0, y)
                nodes.append((tx + offset, y))

        # Fill remaining with scattered understory nodes
        while len(nodes) < count:
            x = rng.uniform(3, max(4, w - 4))
            y = rng.uniform(usable_h * 0.15, usable_h * 0.90)
            nodes.append((x, y))
        return nodes[:count]

    def edge_keep_count(self):
        return 4  # more branch connections

    def step_star(self, star, frame, w, h, rng):
        # Fireflies: slow random drift with sin-wave flickering brightness
        star[0] += math.sin(frame * 0.07 + star[3]) * 0.06
        star[1] += math.cos(frame * 0.05 + star[3] * 1.3) * 0.04
        # Wrap within screen
        if star[0] < 2:
            star[0] = float(w - 3)
        elif star[0] > w - 2:
            star[0] = 2.0
        if star[1] < 2:
            star[1] = float(h - 3)
        elif star[1] > h - 2:
            star[1] = 2.0
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Falling leaves with diagonal drift and horizontal sway
        x = rng.uniform(2, max(3, w - 3))
        y = rng.uniform(1, max(2, h * 0.3))
        vx = rng.uniform(-0.12, 0.12)
        vy = rng.uniform(0.06, 0.16)
        char = rng.choice("\u2218,'\u2219")
        life = rng.randint(10, 18)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        if abs(dy) > abs(dx) * 1.5:
            return "\u2502"
        return "\u2571" if dx * dy < 0 else "\u2572"

    def node_glyph(self, idx, intensity, total):
        return "\u25c9" if idx % 4 == 0 else "\u2022"

    def node_color_key(self, idx, intensity, total):
        return "accent" if idx % 4 == 0 else ("bright" if intensity > 0.65 else "soft")

    def packet_color_key(self):
        return "accent"

    def star_glyph(self, brightness, char_idx):
        return "\u2727" if brightness > 0.75 else "\u00b7"

    def particle_color_key(self, age_ratio):
        return "soft" if age_ratio > 0.4 else "base"

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        ground_y = state.height - 2
        ground_pat = "\u25c1\u25c1\u25c2\u25c1\u25c3\u25c1\u25c1\u25c2\u25c1"
        # Repeat to fill width
        full = (ground_pat * (state.width // len(ground_pat) + 1))[:state.width - 2]
        try:
            stdscr.addstr(
                ground_y, 1, full,
                curses.color_pair(color_pairs["soft"])
            )
        except curses.error:
            pass


class MountainStarsPlugin(ThemePlugin):
    """Silhouetted peaks under starfield — constellations, shooting stars, mountain silhouette."""

    name = "mountain-stars"

    def build_nodes(self, w, h, cx, cy, count, rng):
        # Constellation patterns in upper 60% only
        nodes = []
        usable_w = max(12.0, w - 8.0)
        upper_h = h * 0.60
        for _ in range(count):
            x = 4.0 + rng.uniform(0, usable_w)
            y = 2.0 + rng.uniform(0, upper_h - 2.0)
            nodes.append((x, y))
        return nodes

    def step_star(self, star, frame, w, h, rng):
        # Static starfield — no movement
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Shooting stars — fast horizontal, short life
        y = rng.uniform(1, max(2, h * 0.55))
        x = rng.uniform(max(3, w * 0.1), max(4, w * 0.5))
        vx = rng.uniform(0.30, 0.60)
        vy = rng.uniform(-0.04, 0.04)
        char = rng.choice("\u2500\u2550~")
        life = rng.randint(3, 6)
        return Particle(x, y, vx, vy, life, life, char)

    def particle_base_chance(self):
        return 0.015

    def edge_color_key(self, step, idx_a, frame):
        return "base"

    def edge_glyph(self, dx, dy):
        return "\u00b7"

    def node_glyph(self, idx, intensity, total):
        return "\u2726" if intensity > 0.8 else "\u2022"

    def node_color_key(self, idx, intensity, total):
        return "bright" if intensity > 0.7 else "soft"

    def star_glyph(self, brightness, char_idx):
        return "\u2605" if brightness > 0.85 else "\u2022" if brightness > 0.5 else "\u00b7"

    def particle_color_key(self, age_ratio):
        return "bright" if age_ratio > 0.5 else "soft"

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        h = state.height
        w = state.width
        frame = state.frame
        # Mountain range across bottom 35% of screen, scrolling left based on frame
        base_y = int(h * 0.65)
        mountain_h = h - 1 - base_y  # rows available for mountains

        # Build mountain profile using sine-wave composition, shifted by frame
        scroll_offset = frame * 0.3
        col_pair = color_pairs.get("soft", 1)
        mountain_pair = curses.color_pair(col_pair)

        # For each column, compute peak elevation (0.0 = flat, 1.0 = tallest)
        profile = []
        for col in range(w + 2):
            t = (col + scroll_offset) / max(1.0, w * 0.8)
            elev = (
                0.50 * math.sin(t * 3.1)
                + 0.30 * math.sin(t * 7.3 + 1.2)
                + 0.20 * math.sin(t * 13.7 + 2.5)
            )
            elev = (elev + 1.0) * 0.5  # normalize to 0..1
            profile.append(elev)

        # Peak row per column (higher elev = higher up on screen = lower row number)
        peak_rows = []
        for col in range(w):
            elev = profile[col]
            peak_row = base_y + int((1.0 - elev) * mountain_h * 0.8)
            peak_rows.append(peak_row)

        # Draw slope characters on the peak row
        for col in range(1, w - 1):
            peak_row = peak_rows[col]
            if peak_row < 1 or peak_row >= h - 1:
                continue
            # Determine slope direction from neighbours
            left_peak = peak_rows[col - 1]
            right_peak = peak_rows[col + 1]
            if left_peak > peak_row and right_peak > peak_row:
                slope_char = "^"  # local peak
            elif left_peak > peak_row:
                slope_char = "/"  # ascending left to right
            elif right_peak > peak_row:
                slope_char = "\\"  # descending left to right
            else:
                slope_char = "_"
            try:
                stdscr.addstr(peak_row, col, slope_char, mountain_pair)
            except curses.error:
                pass

        # Fill mountain body with ▓ below each peak row
        for col in range(1, w - 1):
            peak_row = peak_rows[col]
            for row in range(peak_row + 1, h - 1):
                try:
                    stdscr.addstr(row, col, "\u2593", mountain_pair)
                except curses.error:
                    pass


class BeachLighthousePlugin(ThemePlugin):
    """Calm shore with sweeping beam — sea nodes, wave foam, rotating light beam."""

    name = "beach-lighthouse"

    def build_nodes(self, w, h, cx, cy, count, rng):
        # Sparse nodes in upper 60% (sea area)
        nodes = []
        usable_w = max(12.0, w - 12.0)
        sea_h = h * 0.60
        for _ in range(count):
            x = 4.0 + rng.uniform(0, usable_w)
            y = 2.0 + rng.uniform(0, sea_h - 2.0)
            nodes.append((x, y))
        return nodes

    def step_star(self, star, frame, w, h, rng):
        # Stars in lower 40% (ocean area): move horizontally (ocean current)
        if star[1] > h * 0.60:
            star[0] += 0.04 * star[2]  # horizontal ocean current
            if star[0] > w - 2:
                star[0] = 2.0
            return True
        # Sky stars: gentle rightward drift
        star[0] += 0.012 * star[2]
        if star[0] > w - 2:
            star[0] = 2.0
        return True

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Wave foam along shoreline at ~65% height
        shoreline_y = h * 0.65
        x = rng.uniform(2, max(3, w - 3))
        y = shoreline_y + rng.uniform(-1.0, 1.0)
        vx = rng.uniform(-0.10, 0.10)
        vy = rng.uniform(-0.04, 0.04)
        char = rng.choice(".\u007e")
        life = rng.randint(6, 12)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        return "~"

    def node_glyph(self, idx, intensity, total):
        return "\u2022" if intensity > 0.5 else "\u00b7"

    def node_color_key(self, idx, intensity, total):
        return "soft" if intensity > 0.5 else "base"

    def particle_color_key(self, age_ratio):
        return "soft" if age_ratio > 0.5 else "base"

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        from hermes_neurovision.ascii_art import LIGHTHOUSE
        h = state.height
        w = state.width
        frame = state.frame

        # Draw lighthouse on right side
        lh_x = max(4, w - 8)
        lh_y = max(2, int(h * 0.40))
        LIGHTHOUSE.draw(stdscr, lh_x, lh_y, color_pairs["bright"], anchor="topleft")

        # WAVE ZONE: from 70% to bottom of screen (100%)
        wave_top = int(h * 0.70)
        wave_bot = h  # All the way to bottom
        wave_pair = curses.color_pair(color_pairs["soft"])
        for row in range(wave_top, h - 1):
            row_offset = (row - wave_top) * 0.4
            wave_str = ""
            for col in range(w - 2):
                # Shift wave horizontally with sin(frame) + row offset
                phase = col * 0.15 + frame * 0.08 + row_offset
                wave_str += "≈" if math.sin(phase) > 0 else "~"
            try:
                stdscr.addstr(row, 1, wave_str[:w - 2], wave_pair)
            except curses.error:
                pass

        # Shoreline using ░ at wave top edge
        shore_y = wave_top
        shore_pair = curses.color_pair(color_pairs["base"])
        shore_str = "░" * (w - 2)
        try:
            stdscr.addstr(shore_y, 1, shore_str[:w - 2], shore_pair)
        except curses.error:
            pass

        # Rotating beam: sweep angle based on frame (drawn LAST so it's on top)
        beam_angle = (frame * 0.04) % math.tau
        beam_len = max(8, w // 3)
        origin_x = lh_x + 1  # tip of lighthouse
        origin_y = lh_y + 1
        beam_pair = curses.color_pair(color_pairs["warning"])
        for step in range(1, beam_len):
            bx = int(origin_x + math.cos(beam_angle) * step * 1.8)
            by = int(origin_y + math.sin(beam_angle) * step * 0.7)
            if bx < 1 or bx >= w - 1 or by < 1 or by >= h - 1:
                break
            dot = "." if step % 3 == 0 else "·"
            try:
                stdscr.addstr(by, bx, dot, beam_pair)
            except curses.error:
                pass


# ── Register all nature plugins ───────────────────────────────────

for _cls in [
    DeepAbyssPlugin,
    StormSeaPlugin,
    DarkForestPlugin,
    MountainStarsPlugin,
    BeachLighthousePlugin,
]:
    register(_cls())
