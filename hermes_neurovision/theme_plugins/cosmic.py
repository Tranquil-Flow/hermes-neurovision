"""Cosmic-themed plugins for Hermes Vision."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


class AuroraBorealisPlugin(ThemePlugin):
    """Northern lights — constellation patterns glowing in aurora colors."""

    name = "aurora-borealis"

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

    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "agent_start" or event_kind == "session_resume":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "llm_start" or event_kind == "llm_end":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.7,
                           origin=(0.0, 0.5), color_key="accent", duration=2.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.4,
                           origin=(0.0, random.random()), color_key="soft", duration=0.6)
        if event_kind == "memory_save" or event_kind == "skill_create":
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                           origin=(0.5, 0.5), color_key="bright", duration=3.0)
        if event_kind == "error" or event_kind == "crash" or event_kind == "threat_blocked":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "git_commit" or event_kind == "file_edit":
            return Reaction(element=ReactiveElement.TRAIL, intensity=0.6,
                           origin=(0.0, 0.5), color_key="accent", duration=1.5)
        if event_kind == "tool_call" or event_kind == "mcp_tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.7,
                           origin=(random.random(), random.random()), color_key="accent", duration=1.8)
        return None

    def wave_config(self):
        return {'speed': 0.4, 'damping': 0.97}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 2


class NebulaNurseryPlugin(ThemePlugin):
    """Stellar nursery — proto-star cloud clusters, stellar wind particles."""

    name = "nebula-nursery"

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

    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.9,
                           origin=(0.5, 0.5), color_key="bright", duration=2.5)
        if event_kind == "skill_create" or event_kind == "checkpoint_created":
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                           origin=(random.random(), random.random()), color_key="bright", duration=3.5)
        if event_kind == "error" or event_kind == "crash" or event_kind == "threat_blocked":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.8,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        if event_kind == "tool_call" or event_kind == "mcp_tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.6,
                           origin=(random.random(), random.random()), color_key="soft", duration=1.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.4,
                           origin=(random.random(), random.random()), color_key="soft", duration=0.8)
        return None

    def physarum_config(self):
        return {'n_agents': 120, 'sensor_dist': 5.0, 'sensor_angle': 0.785, 'deposit': 0.8, 'decay': 0.93}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 2


class BinaryRainPlugin(ThemePlugin):
    """Matrix digital rain — dense vertical columns of 0/1 falling at varied speeds."""

    name = "binary-rain"

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

    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "llm_chunk" or event_kind == "llm_start":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.6,
                           origin=(0.0, random.random()), color_key="accent", duration=1.0)
        if event_kind == "tool_call" or event_kind == "mcp_tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.7,
                           origin=(random.random(), 0.0), color_key="bright", duration=1.5)
        if event_kind == "dangerous_cmd" or event_kind == "approval_request":
            return Reaction(element=ReactiveElement.SPARK, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.8,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.5)
        return None

    def automaton_config(self):
        return {'rule': 'brians_brain', 'density': 0.06, 'update_interval': 3}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


class WormholePlugin(ThemePlugin):
    """Tunnel transit — 5 large concentric rings filling screen, rotating, stars pull inward."""

    name = "wormhole"

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



    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "agent_start" or event_kind == "session_resume":
            return Reaction(element=ReactiveElement.PULSE, intensity=1.0,
                           origin=(0.5, 0.5), color_key="bright", duration=3.0)
        if event_kind == "compression_started" or event_kind == "compression_ended":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.9,
                           origin=(0.5, 0.5), color_key="accent", duration=2.5)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "memory_save" or event_kind == "skill_create":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.9,
                           origin=(0.5, 0.5), color_key="bright", duration=2.5)
        if event_kind == "tool_call" or event_kind == "mcp_tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.7,
                           origin=(0.5, 0.5), color_key="accent", duration=1.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.TRAIL, intensity=0.4,
                           origin=(0.5, 0.5), color_key="soft", duration=0.6)
        return None

    def wave_config(self):
        return {'speed': 0.6, 'damping': 0.95}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 2

# ── Register all cosmic plugins ───────────────────────────────────

for _cls in [
    AuroraBorealisPlugin,
    NebulaNurseryPlugin,
    BinaryRainPlugin,
    WormholePlugin,
]:
    register(_cls())
