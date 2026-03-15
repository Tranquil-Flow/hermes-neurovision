"""Industrial theme plugins for Hermes Vision."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


class LiquidMetalPlugin(ThemePlugin):
    """T-1000 mercury — amorphous chrome blobs with liquid bridges."""

    name = "liquid-metal"

    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        # Create 2-3 cluster centers, then scatter nodes around them
        cluster_centers = [
            (cx + rng.uniform(-w * 0.2, w * 0.2), cy + rng.uniform(-h * 0.2, h * 0.2)),
            (cx + rng.uniform(-w * 0.15, w * 0.15), cy + rng.uniform(-h * 0.15, h * 0.15)),
            (cx + rng.uniform(-w * 0.25, w * 0.25), cy + rng.uniform(-h * 0.1, h * 0.1)),
        ]
        for i in range(count):
            center = cluster_centers[i % len(cluster_centers)]
            # Heavy jitter — amorphous blob effect
            jitter_x = rng.uniform(-w * 0.18, w * 0.18)
            jitter_y = rng.uniform(-h * 0.18, h * 0.18)
            # Sinusoidal drift component
            drift = math.sin(i * 0.7) * w * 0.06
            x = max(4.0, min(w - 5.0, center[0] + jitter_x + drift))
            y = max(2.0, min(h - 3.0, center[1] + jitter_y))
            nodes.append((x, y))
        return nodes

    def step_star(self, star, frame, w, h, rng):
        # Chrome reflections — sparse bright flashes, rapid appear/disappear
        # Modulate brightness by varying the char_idx proxy stored in star[3]
        # star layout: [x, y, speed, seed_or_extra]
        star[3] = (star[3] + rng.uniform(-0.4, 0.6)) % 6.28
        # Slow drift
        star[0] += math.sin(frame * 0.04 + star[3]) * 0.04 * star[2]
        star[1] += math.cos(frame * 0.03 + star[3]) * 0.02 * star[2]
        # Wrap at edges
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
        # Flicker: high brightness = bright chrome flash, else invisible
        if brightness > 0.82:
            return "+"
        if brightness > 0.65:
            return "·"
        return " "  # invisible most of the time

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        if not nodes:
            return None
        node = rng.choice(nodes)
        x = node[0] + rng.uniform(-3, 3)
        y = node[1] + rng.uniform(-2, 2)
        vx = rng.uniform(-0.18, 0.18)
        vy = rng.uniform(-0.14, 0.14)
        char = rng.choice("•○◦")
        life = rng.randint(5, 11)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        # Liquid bridges — cycling between ≈ and ~
        return "≈" if abs(dx) > abs(dy) else "~"

    def pulse_params(self):
        return (0.36, 0.12)

    def node_glyph(self, idx, intensity, total):
        return "●" if intensity > 0.7 else "○"

    def node_color_key(self, idx, intensity, total):
        colors = ["bright", "soft", "accent", "soft"]
        return colors[idx % len(colors)]

    def packet_color_key(self):
        return "bright"

    def particle_color_key(self, age_ratio):
        return "bright" if age_ratio > 0.5 else "soft"

    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "memory_save" or event_kind == "checkpoint_created":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.9,
                           origin=(random.random(), random.random()), color_key="bright", duration=2.5)
        if event_kind == "compression_started" or event_kind == "compression_ended":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        if event_kind == "tool_call" or event_kind == "mcp_tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.6,
                           origin=(random.random(), random.random()), color_key="soft", duration=1.5)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.5)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.7,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.4,
                           origin=(random.random(), random.random()), color_key="soft", duration=0.8)
        return None

    def wave_config(self):
        return {'speed': 0.2, 'damping': 0.98}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 2


class FactoryFloorPlugin(ThemePlugin):
    """Assembly line — machines in grid with sparks and steam."""

    name = "factory-floor"

    def build_nodes(self, w, h, cx, cy, count, rng):
        usable_w = max(12.0, w - 10.0)
        usable_h = max(6.0, h - 6.0)
        # Dense 2D grid: machines at regular intervals
        cols = max(3, w // 12)
        rows = max(2, h // 6)
        nodes = []
        machine_idx = 0
        for row in range(rows):
            for col in range(cols):
                x = 5 + col * (usable_w / max(1, cols - 1))
                y = 3 + row * (usable_h / max(1, rows - 1))
                # Every 3rd machine: "large machine" — offset slightly for variety
                if machine_idx % 3 == 0:
                    x += rng.uniform(-0.8, 0.8)
                    y += rng.uniform(-0.4, 0.4)
                x = max(4.0, min(w - 5.0, x))
                y = max(2.0, min(h - 3.0, y))
                nodes.append((x, y))
                machine_idx += 1

        # Add conveyor nodes between machines on same row (horizontal connectors)
        conveyor_nodes = []
        for row in range(rows):
            for col in range(cols - 1):
                # Midpoint between adjacent machines on same row
                x1 = 5 + col * (usable_w / max(1, cols - 1))
                x2 = 5 + (col + 1) * (usable_w / max(1, cols - 1))
                cx_conv = (x1 + x2) / 2.0
                cy_conv = 3 + row * (usable_h / max(1, rows - 1))
                cx_conv = max(4.0, min(w - 5.0, cx_conv))
                cy_conv = max(2.0, min(h - 3.0, cy_conv))
                conveyor_nodes.append((cx_conv, cy_conv))

        nodes.extend(conveyor_nodes)
        return nodes

    def step_nodes(self, nodes, frame, w, h):
        # Conveyor nodes oscillate horizontally to simulate belt movement
        # Conveyor nodes are appended after machine nodes; detect by idx
        total = len(nodes)
        # Heuristic: last ~half are conveyors (added after machines)
        n_machines = 0
        cols = max(3, w // 12)
        rows = max(2, h // 6)
        n_machines = rows * cols
        for i in range(n_machines, total):
            x, y = nodes[i]
            # Small horizontal oscillation simulating belt motion
            dx = math.sin(frame * 0.12 + i * 0.5) * 0.3
            nodes[i] = (x + dx, y)

    def step_star(self, star, frame, w, h, rng):
        # Sparks fall downward and drift around — all over the place
        star[1] += 0.15 * star[2]  # fall down
        star[0] += rng.uniform(-0.15, 0.15) + math.sin(frame * 0.03 + star[3]) * 0.2  # more horizontal drift
        if star[1] >= h - 1:
            # Reset anywhere on screen — sparks everywhere
            star[0] = rng.uniform(2, max(3, w - 3))
            star[1] = rng.uniform(1, max(2, h - 2))  # spawn anywhere vertically
        # Wrap around horizontally
        if star[0] < 2:
            star[0] = w - 3
        elif star[0] > w - 3:
            star[0] = 2
        return True

    def star_glyph(self, brightness, char_idx):
        return "*" if brightness > 0.6 else "."

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        if rng.random() < 0.5:
            # Sparks fall downward
            x = rng.uniform(2, max(3, w - 3))
            y = rng.uniform(1, max(2, h * 0.4))
            vx = rng.uniform(-0.08, 0.08)
            vy = rng.uniform(0.10, 0.22)
            char = rng.choice("*'")
        else:
            # Steam rises upward from machine positions
            if nodes:
                node = rng.choice(nodes)
                x = node[0] + rng.uniform(-1, 1)
                y = node[1]
            else:
                x = rng.uniform(2, max(3, w - 3))
                y = h - 3
            vx = rng.uniform(-0.05, 0.05)
            vy = rng.uniform(-0.18, -0.06)
            char = rng.choice("^°")
        life = rng.randint(5, 12)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        # Horizontal conveyors, vertical pipes, crossings
        adx, ady = abs(dx), abs(dy)
        if adx > ady * 2:
            return "═"
        elif ady > adx * 2:
            return "║"
        else:
            return "┼"

    def node_glyph(self, idx, intensity, total):
        mod = idx % 5
        if mod == 0:
            return "⚙"   # large machine
        elif mod == 1:
            return "▪"   # conveyor node
        else:
            return "◼"   # standard machine

    def pulse_style(self):
        return "spoked"

    def packet_budget(self):
        return 6

    def node_color_key(self, idx, intensity, total):
        return "accent" if idx % 3 == 0 else "bright"

    def particle_color_key(self, age_ratio):
        return "accent" if age_ratio > 0.5 else "soft"

    def pulse_color_key(self):
        return "warning"

    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "llm_chunk" or event_kind == "llm_start":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.6,
                           origin=(0.0, random.random()), color_key="accent", duration=0.8)
        if event_kind == "git_commit" or event_kind == "file_edit":
            return Reaction(element=ReactiveElement.TRAIL, intensity=0.7,
                           origin=(0.0, random.random()), color_key="bright", duration=1.5)
        if event_kind == "dangerous_cmd" or event_kind == "approval_request":
            return Reaction(element=ReactiveElement.SPARK, intensity=1.0,
                           origin=(random.random(), random.random()), color_key="warning", duration=2.0)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.8,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        return None

    def automaton_config(self):
        return {'rule': 'brians_brain', 'density': 0.07, 'update_interval': 2}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


class PipeHellPlugin(ThemePlugin):
    """Infinite plumbing nightmare — pipe junctions everywhere."""

    name = "pipe-hell"

    def build_nodes(self, w, h, cx, cy, count, rng):
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)
        # Dense grid with random junctions — fills screen with pipe maze
        cols = max(3, w // 8)
        rows = max(3, h // 5)
        nodes = []
        for row in range(rows):
            for col in range(cols):
                # 70% chance of a junction node at each grid point
                if rng.random() > 0.70:
                    continue
                x = 4 + col * (usable_w / max(1, cols - 1))
                y = 2 + row * (usable_h / max(1, rows - 1))
                # Small jitter for organic feel
                x += rng.uniform(-0.8, 0.8)
                y += rng.uniform(-0.4, 0.4)
                x = max(4.0, min(w - 5.0, x))
                y = max(2.0, min(h - 3.0, y))
                nodes.append((x, y))
        # Ensure enough nodes
        while len(nodes) < max(8, count // 2):
            x = rng.uniform(4, max(5, w - 5))
            y = rng.uniform(2, max(3, h - 3))
            nodes.append((x, y))
        return nodes

    def build_edges_extra(self, nodes, edges_set):
        # Add orthogonal connections — connect to nearest node in each cardinal direction
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
                    # Horizontal neighbor
                    if dx < 0 and dist < best_d["left"]:
                        best["left"] = j
                        best_d["left"] = dist
                    elif dx > 0 and dist < best_d["right"]:
                        best["right"] = j
                        best_d["right"] = dist
                elif abs(dy) > abs(dx) * 1.5:
                    # Vertical neighbor
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

    def edge_keep_count(self):
        return 4

    def step_star(self, star, frame, w, h, rng):
        # Steam wisps drift all over the place — chaotic movement
        star[1] += rng.uniform(-0.15, 0.10) + math.cos(frame * 0.04 + star[3]) * 0.15  # vertical drift
        star[0] += rng.uniform(-0.12, 0.12) + math.sin(frame * 0.05 + star[3]) * 0.2  # horizontal drift
        # Wrap around edges
        if star[1] < 1:
            star[1] = h - 2
        elif star[1] > h - 1:
            star[1] = 2
        if star[0] < 2:
            star[0] = w - 3
        elif star[0] > w - 3:
            star[0] = 2
        return True

    def star_glyph(self, brightness, char_idx):
        return "~" if brightness > 0.55 else "≈"

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Leaks dripping downward from pipe junctions
        if nodes:
            node = rng.choice(nodes)
            x = node[0] + rng.uniform(-0.5, 0.5)
            y = node[1]
        else:
            x = rng.uniform(2, max(3, w - 3))
            y = rng.uniform(1, max(2, h * 0.6))
        vx = rng.uniform(-0.02, 0.02)
        vy = rng.uniform(0.08, 0.18)  # dripping down
        char = rng.choice("·.°")
        life = rng.randint(6, 13)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        # Proper box-drawing based on actual direction
        adx, ady = abs(dx), abs(dy)
        if adx > ady * 2:
            return "═"
        elif ady > adx * 2:
            return "║"
        else:
            return "╬"

    def node_glyph(self, idx, intensity, total):
        mod = idx % 4
        if mod == 0:
            return "╬"   # main junction
        elif mod == 1:
            return "╋"   # T-junction
        elif mod == 2:
            return "┼"   # cross
        else:
            return "╸"   # dead end

    def pulse_style(self):
        return "cloud"

    def edge_color_key(self, step, idx_a, frame):
        return "soft"

    def packet_color_key(self):
        return "accent"

    def particle_color_key(self, age_ratio):
        return "soft"

    def node_color_key(self, idx, intensity, total):
        return "bright" if idx % 3 == 0 else "soft"

    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "llm_chunk" or event_kind == "llm_start":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.7,
                           origin=(0.0, random.random()), color_key="accent", duration=1.0)
        if event_kind == "error" or event_kind == "crash" or event_kind == "threat_blocked":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(random.random(), random.random()), color_key="warning", duration=2.5)
        if event_kind == "tool_call" or event_kind == "mcp_tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.7,
                           origin=(random.random(), random.random()), color_key="bright", duration=1.5)
        if event_kind == "cron_tick" or event_kind == "background_proc":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.5,
                           origin=(0.5, 0.5), color_key="soft", duration=2.0)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.7,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        return None

    def physarum_config(self):
        return {'n_agents': 60, 'sensor_dist': 5.0, 'sensor_angle': 0.4, 'deposit': 1.5, 'decay': 0.92}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


class OilSlickPlugin(ThemePlugin):
    """Iridescent rainbow on black water — slow drifting shimmer."""

    name = "oil-slick"

    def build_nodes(self, w, h, cx, cy, count, rng):
        # Ring-like layout with heavy jitter — amorphous blob
        usable_w = max(12.0, w - 8.0)
        usable_h = max(6.0, h - 6.0)
        radius_x = usable_w * 0.30
        radius_y = usable_h * 0.32
        nodes = []
        for i in range(count):
            a = (math.tau * i) / count
            # Heavy jitter for amorphous look
            jitter_x = rng.uniform(-w * 0.10, w * 0.10)
            jitter_y = rng.uniform(-h * 0.10, h * 0.10)
            x = cx + math.cos(a) * radius_x + jitter_x
            y = cy + math.sin(a) * radius_y + jitter_y
            x = max(4.0, min(w - 5.0, x))
            y = max(2.0, min(h - 3.0, y))
            nodes.append((x, y))
        return nodes

    def step_star(self, star, frame, w, h, rng):
        # Iridescent shimmer — slow drift
        star[0] += math.sin(frame * 0.025 + star[3]) * 0.035 * star[2]
        star[1] += math.cos(frame * 0.018 + star[3] * 1.3) * 0.02 * star[2]
        # Wrap at edges
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
        # Color effect via different shimmer chars
        idx = int(brightness * 4) % 4
        return ["·", "~", "≈", "°"][idx]

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Oil drops — slow drift, long life
        x = rng.uniform(3, max(4, w - 4))
        y = rng.uniform(2, max(3, h - 3))
        vx = rng.uniform(-0.04, 0.04)
        vy = rng.uniform(-0.03, 0.03)
        char = rng.choice("●◉◦")
        life = rng.randint(12, 22)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        return "·" if abs(dx) > abs(dy) else "~"

    def pulse_params(self):
        # MUCH slower growth, larger radius — gentle iridescent ripples
        return (0.08, 0.28)

    def pulse_style(self):
        return "ripple"

    def particle_life_range(self):
        return (12, 22)

    def particle_base_chance(self):
        return 0.02

    def node_glyph(self, idx, intensity, total):
        return "◉" if intensity > 0.6 else "○"

    def node_color_key(self, idx, intensity, total):
        colors = ["accent", "soft", "bright", "base"]
        return colors[idx % len(colors)]

    def edge_color_key(self, step, idx_a, frame):
        # Cycle through all 4 color keys — iridescent rainbow effect
        color_keys = ["base", "soft", "bright", "accent"]
        return color_keys[(step + idx_a + frame // 3) % 4]

    def particle_color_key(self, age_ratio):
        # Cycle color based on age_ratio ranges — rainbow oil effect
        if age_ratio > 0.75:
            return "accent"
        elif age_ratio > 0.5:
            return "bright"
        elif age_ratio > 0.25:
            return "soft"
        else:
            return "base"

    def pulse_color_key(self):
        return "accent"



    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "reasoning_change" or event_kind == "personality_change":
            return Reaction(element=ReactiveElement.GLYPH, intensity=0.8,
                           origin=(0.5, 0.5), color_key="bright", duration=3.0)
        if event_kind == "memory_save" or event_kind == "skill_create":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.9,
                           origin=(0.5, 0.5), color_key="bright", duration=2.5)
        if event_kind == "tool_call" or event_kind == "mcp_tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.6,
                           origin=(random.random(), random.random()), color_key="soft", duration=1.5)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.7,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.3,
                           origin=(random.random(), random.random()), color_key="soft", duration=0.6)
        return None

    def wave_config(self):
        return {'speed': 0.1, 'damping': 0.995}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 2



# ── Register ─────────────────────────────────────────────────────

for _cls in [
    LiquidMetalPlugin,
    FactoryFloorPlugin,
    PipeHellPlugin,
    OilSlickPlugin,
]:
    register(_cls())
