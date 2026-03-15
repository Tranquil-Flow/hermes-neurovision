"""Emergent V2 — 5 new screens leveraging v0.2.0 engine features.

Each theme demonstrates a different combination of emergent systems, postfx,
and reactive event handling — filling the gap where most existing themes use
only v1.0 frozen API.

Themes:
  dna-helix         — Rotating double-helix node structure + wave field backdrop
  pendulum-waves    — N coupled pendulums with mesmerizing phase beats
  kaleidoscope      — 4-fold rotational symmetry with physarum-driven patterns
  electric-storm    — Lightning bolts + rain field with neural-field excitation
  coral-growth      — L-system branching coral with reaction-diffusion backdrop
"""

from __future__ import annotations

import curses
import math
import random
from typing import Any, Dict, List, Optional, Tuple

from hermes_neurovision.plugin import (
    ThemePlugin,
    ReactiveElement,
    Reaction,
    SpecialEffect,
)
from hermes_neurovision.sound import SoundCue
from hermes_neurovision.scene import Particle
from hermes_neurovision.theme_plugins import register


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe(stdscr, y: int, x: int, text: str, attr: int = 0) -> None:
    try:
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        pass


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


# ═══════════════════════════════════════════════════════════════════════════
# THEME 1: dna-helix — Rotating Double Helix
# ═══════════════════════════════════════════════════════════════════════════

class DNAHelixPlugin(ThemePlugin):
    """Double-helix DNA strand rotating in 3D with base-pair connections.

    Combines:
      - wave_config emergent system for rippling backdrop
      - warp_field postfx for subtle distortion near the helix
      - echo_decay for trailing afterglow on the helix rotation
      - reactive: tool_call → RIPPLE along the helix, error → SHATTER
    """

    name = "dna-helix"

    def __init__(self):
        super().__init__()
        self._base_pairs = "ATCGATCGTAGCATCG"

    # -- emergent --
    def wave_config(self) -> Optional[Dict]:
        return {
            "speed": 0.25,
            "damping": 0.97,
        }

    def emergent_layer(self) -> str:
        return "background"

    # -- postfx --
    def warp_field(self, x: int, y: int, w: int, h: int,
                   frame: int, intensity: float) -> Tuple[int, int]:
        cx = w / 2
        dist_x = abs(x - cx)
        if dist_x < w * 0.15:
            amp = intensity * 0.8 * (1.0 - dist_x / (w * 0.15))
            dy = int(amp * math.sin(frame * 0.12 + y * 0.4))
            ny = max(0, min(h - 1, y + dy))
            return (x, ny)
        return (x, y)

    def echo_decay(self) -> int:
        return 3

    def glow_radius(self) -> int:
        return 1

    def decay_sequence(self) -> Optional[str]:
        return "●◉○◦·. "

    # -- node layout: helix --
    def build_nodes(self, w: int, h: int, cx: float, cy: float,
                    count: int, rng) -> List[Tuple[float, float]]:
        nodes = []
        n_rungs = min(count // 2, 16)
        spacing = max(1, (h - 4) / max(1, n_rungs - 1))
        for i in range(n_rungs):
            y = 2 + i * spacing
            # Two strands offset by pi
            nodes.append((cx - 6, y))  # strand A
            nodes.append((cx + 6, y))  # strand B
        return nodes[:count]

    def build_edges_extra(self, nodes, edges_set):
        # Connect rungs (base pairs) and backbone
        n = len(nodes)
        for i in range(0, n - 1, 2):
            # Base pair connection
            if i + 1 < n:
                edges_set.add((i, i + 1))
            # Backbone A
            if i + 2 < n:
                edges_set.add((i, i + 2))
            # Backbone B
            if i + 3 < n:
                edges_set.add((i + 1, i + 3))

    def step_nodes(self, nodes, frame, w, h):
        cx = w / 2.0
        n = len(nodes)
        helix_radius = min(w * 0.18, 14)
        for i in range(n):
            rung = i // 2
            strand = i % 2
            y = nodes[i][1]
            # 3D rotation projected to 2D
            phase = frame * 0.06 + rung * 0.45
            if strand == 1:
                phase += math.pi
            x_offset = math.cos(phase) * helix_radius
            # Depth (z) affects brightness — we encode via x spread
            depth = math.sin(phase)  # -1 to 1
            x = cx + x_offset * (0.6 + 0.4 * abs(depth))
            nodes[i] = (max(2, min(w - 3, x)), y)

    def step_star(self, star, frame, w, h, rng):
        # Gentle upward drift like cellular material
        star[1] -= 0.03 + star[2] * 0.01
        star[0] += math.sin(frame * 0.015 + star[3]) * 0.06
        if star[1] < 1:
            star[1] = h - 2
            star[0] = rng.uniform(2, w - 3)
        return True

    def spawn_particle(self, w, h, nodes, rng):
        cx = w / 2.0
        x = cx + rng.uniform(-w * 0.2, w * 0.2)
        y = rng.uniform(2, h - 3)
        vx = rng.uniform(-0.05, 0.05)
        vy = rng.uniform(-0.12, -0.03)
        char = rng.choice("·∙°")
        life = rng.randint(10, 25)
        return Particle(x, y, vx, vy, life, life, char)

    def particle_base_chance(self):
        return 0.06

    def node_glyph(self, idx, intensity, total):
        strand = idx % 2
        rung = idx // 2
        bp = self._base_pairs[rung % len(self._base_pairs)]
        if strand == 0:
            return bp
        else:
            complement = {"A": "T", "T": "A", "C": "G", "G": "C"}
            return complement.get(bp, "·")

    def node_color_key(self, idx, intensity, total):
        rung = idx // 2
        bp = self._base_pairs[rung % len(self._base_pairs)]
        if bp in "AT":
            return "accent"
        return "bright"

    def edge_glyph(self, dx, dy):
        if abs(dx) > abs(dy) * 2:
            return "═"
        return "│" if abs(dy) > abs(dx) else "─"

    def edge_color_key(self, step, idx_a, frame):
        return "soft" if idx_a % 2 == 0 else "accent"

    def pulse_style(self):
        return "ripple"

    def pulse_params(self):
        return (0.30, 0.20)

    def packet_color_key(self):
        return "bright"

    # -- reactive --
    def react(self, event_kind: str, data: Dict) -> Optional[Reaction]:
        if event_kind == "tool_call":
            return Reaction(
                element=ReactiveElement.RIPPLE,
                intensity=0.7,
                origin=(0.5, random.random()),
                color_key="accent",
                duration=2.0,
                data={"along_helix": True},
            )
        if event_kind == "memory_save":
            return Reaction(
                element=ReactiveElement.BLOOM,
                intensity=0.9,
                origin=(0.5, 0.5),
                color_key="bright",
                duration=3.0,
            )
        if event_kind == "error":
            return Reaction(
                element=ReactiveElement.SHATTER,
                intensity=1.0,
                origin=(0.5, 0.5),
                color_key="warning",
                duration=2.5,
            )
        return None

    def intensity_curve(self, raw: float) -> float:
        # Gentle exponential — low activity is calm, high spikes
        return raw ** 1.5

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        f = state.frame
        cx = w // 2
        soft_attr = curses.color_pair(color_pairs.get("soft", 0)) | curses.A_DIM
        # Draw helix guide rails — faint sinusoidal tracks
        for y in range(2, h - 2):
            phase = f * 0.06 + (y - 2) * 0.45 / max(1, (h - 4) / 16)
            for strand_phase in [0, math.pi]:
                p = phase + strand_phase
                x_off = math.cos(p) * min(w * 0.18, 14)
                depth = math.sin(p)
                x = int(cx + x_off * (0.6 + 0.4 * abs(depth)))
                if 0 <= x < w - 1:
                    ch = ":" if depth > 0 else "·"
                    _safe(stdscr, y, x, ch, soft_attr)


# ═══════════════════════════════════════════════════════════════════════════
# THEME 2: pendulum-waves — Phase-Beating Pendulum Array
# ═══════════════════════════════════════════════════════════════════════════

class PendulumWavesPlugin(ThemePlugin):
    """Array of pendulums with slightly different frequencies creating wave patterns.

    Combines:
      - boids_config for ambient particle swarm reacting to pendulum motion
      - symmetry mirror_x for mirrored visual
      - force_points for vortex attractors at pendulum bobs
      - reactive: llm events → WAVE, tool calls → SPARK at pendulum positions
    """

    name = "pendulum-waves"
    _N_PENDULUMS = 15
    _BASE_PERIOD = 60.0  # frames for longest pendulum

    def __init__(self):
        super().__init__()

    # -- emergent --
    def boids_config(self) -> Optional[Dict]:
        return {
            "n_boids": 40,
            "sep_dist": 2.5,
            "align_dist": 6.0,
            "cohesion_dist": 10.0,
            "max_speed": 1.5,
        }

    def emergent_layer(self) -> str:
        return "background"

    # -- postfx --
    def symmetry(self) -> Optional[str]:
        return "mirror_x"

    def glow_radius(self) -> int:
        return 1

    def force_points(self, w: int, h: int, frame: int,
                     intensity: float) -> List[Tuple[int, int, float, float]]:
        # Place vortex attractors at the bob positions of 3 pendulums
        points = []
        n = self._N_PENDULUMS
        spacing = max(3, (w - 8) // max(1, n - 1))
        pivot_y = 2
        length_max = h * 0.7
        for idx in [0, n // 2, n - 1]:
            period = self._BASE_PERIOD + idx * 2
            omega = math.tau / period
            theta = 0.6 * math.sin(omega * frame)
            bob_x = 4 + idx * spacing + int(math.sin(theta) * length_max * 0.3)
            bob_y = pivot_y + int(math.cos(theta) * length_max * 0.8)
            bob_x = max(0, min(w - 1, bob_x))
            bob_y = max(0, min(h - 1, bob_y))
            points.append((bob_x, bob_y, 0.3 + intensity * 0.5, 0.0))  # type: vortex as float
        return points

    # -- layout: no explicit nodes, all rendering in draw_extras --
    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def pulse_style(self):
        return "rays"

    # -- reactive --
    def react(self, event_kind: str, data: Dict) -> Optional[Reaction]:
        if event_kind in ("llm_start", "llm_end"):
            return Reaction(
                element=ReactiveElement.WAVE,
                intensity=0.8,
                origin=(0.0, 0.5),
                color_key="accent",
                duration=3.0,
            )
        if event_kind == "tool_call":
            return Reaction(
                element=ReactiveElement.SPARK,
                intensity=0.7,
                origin=(random.random(), 0.8),
                color_key="bright",
                duration=1.5,
            )
        if event_kind == "agent_start":
            return Reaction(
                element=ReactiveElement.PULSE,
                intensity=1.0,
                origin=(0.5, 0.3),
                color_key="accent",
                duration=2.0,
            )
        return None

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds: float):
        if idle_seconds > 3.0 and state.frame % 40 == 0:
            w, h = state.width, state.height
            x = random.randint(2, max(3, w - 3))
            y = random.randint(2, max(3, h - 3))
            _safe(stdscr, y, x, "·", color_pairs.get("soft", 0))

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier

        n = self._N_PENDULUMS
        spacing = max(3, (w - 8) // max(1, n - 1))
        pivot_y = 2
        length_max = h * 0.7

        bright_attr = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs.get("accent", 0))
        soft_attr = curses.color_pair(color_pairs.get("soft", 0))
        base_attr = curses.color_pair(color_pairs.get("base", 0)) | curses.A_DIM

        # Draw pivot bar
        bar_x1 = 3
        bar_x2 = min(w - 2, 4 + (n - 1) * spacing + 1)
        if pivot_y < h:
            for x in range(bar_x1, bar_x2 + 1):
                if 0 <= x < w - 1:
                    _safe(stdscr, pivot_y, x, "═", soft_attr)

        # Draw each pendulum
        for idx in range(n):
            pivot_x = 4 + idx * spacing
            if pivot_x >= w - 1:
                break

            # Each pendulum has slightly different period
            period = self._BASE_PERIOD + idx * 2
            omega = math.tau / period
            # Amplitude modulated by intensity
            amp = 0.5 + 0.3 * intensity
            theta = amp * math.sin(omega * f)

            # Bob position
            arm_len = length_max * (0.6 + 0.3 * (idx / max(1, n - 1)))
            bob_x = pivot_x + int(math.sin(theta) * arm_len * 0.4)
            bob_y = pivot_y + int(math.cos(theta) * arm_len * 0.85)
            bob_x = max(1, min(w - 2, bob_x))
            bob_y = max(pivot_y + 1, min(h - 2, bob_y))

            # Draw arm using Bresenham
            dx = abs(bob_x - pivot_x)
            dy = abs(bob_y - pivot_y)
            sx = 1 if bob_x > pivot_x else -1
            sy = 1 if bob_y > pivot_y else -1
            err = dx - dy
            cx2, cy2 = pivot_x, pivot_y
            steps = 0
            while steps < 200:
                if 1 <= cy2 < h - 1 and 0 <= cx2 < w - 1:
                    _safe(stdscr, cy2, cx2, "│", base_attr)
                if cx2 == bob_x and cy2 == bob_y:
                    break
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    cx2 += sx
                if e2 < dx:
                    err += dx
                    cy2 += sy
                steps += 1

            # Draw bob
            if 1 <= bob_y < h - 1 and 0 <= bob_x < w - 1:
                # Color based on velocity (angular momentum)
                vel = abs(math.cos(omega * f))
                if vel > 0.8:
                    _safe(stdscr, bob_y, bob_x, "●", bright_attr)
                elif vel > 0.4:
                    _safe(stdscr, bob_y, bob_x, "◉", accent_attr)
                else:
                    _safe(stdscr, bob_y, bob_x, "○", soft_attr)

        # Phase pattern label
        cycle_frac = (f % int(self._BASE_PERIOD * n)) / (self._BASE_PERIOD * n)
        pattern_name = "converge" if cycle_frac < 0.1 else ("scatter" if cycle_frac < 0.5 else "reform")
        info = f"phase: {pattern_name}"
        info_x = max(0, w - len(info) - 2)
        if h > 3:
            _safe(stdscr, h - 2, info_x, info,
                  curses.color_pair(color_pairs.get("soft", 0)) | curses.A_DIM)


# ═══════════════════════════════════════════════════════════════════════════
# THEME 3: kaleidoscope — 4-Fold Rotational Symmetry with Physarum
# ═══════════════════════════════════════════════════════════════════════════

class KaleidoscopePlugin(ThemePlugin):
    """Rotating kaleidoscope pattern with 4-fold symmetry.

    Combines:
      - physarum_config emergent for organic trail patterns
      - rotate_4 symmetry postfx for kaleidoscope mirror effect
      - glow_radius for soft bloom
      - render_mask for circular aperture
      - reactive: all events trigger RIPPLE from center
    """

    name = "kaleidoscope"

    def __init__(self):
        super().__init__()
        self._angle = 0.0

    # -- emergent --
    def physarum_config(self) -> Optional[Dict]:
        return {
            "n_agents": 120,
            "sensor_dist": 4,
            "sensor_angle": 0.5,
            "deposit": 0.8,
            "decay": 0.94,
        }

    def emergent_layer(self) -> str:
        return "background"

    # -- postfx --
    def symmetry(self) -> Optional[str]:
        return "rotate_4"

    def glow_radius(self) -> int:
        return 2

    def render_mask(self, w: int, h: int, frame: int,
                    intensity: float) -> Optional[List[List[bool]]]:
        """Slow-rotating diamond aperture — distinct from round kaleidoscopes.

        The diamond itself rotates one full turn every ~1200 frames so the
        mask shape evolves while the physarum patterns grow inside it.
        """
        cx, cy = w / 2.0, h / 2.0
        rx = cx * 0.90
        ry = cy * 0.88
        # Rotate the test angle slowly
        rot = frame * 0.00524  # 2pi / 1200 frames
        cos_r, sin_r = math.cos(rot), math.sin(rot)
        mask = []
        for row in range(h):
            line = []
            for col in range(w):
                # Aspect-corrected displacement
                ndx = (col - cx) / max(rx, 1.0)
                ndy = (row - cy) / max(ry, 1.0)
                # Rotate point into diamond's local frame
                lx = ndx * cos_r + ndy * sin_r
                ly = -ndx * sin_r + ndy * cos_r
                # Diamond: L1 norm <= 1
                line.append(abs(lx) + abs(ly) <= 0.97)
            mask.append(line)
        return mask

    # -- layout: no explicit nodes, pure field --
    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    # -- reactive --
    def react(self, event_kind: str, data: Dict) -> Optional[Reaction]:
        element_map = {
            "tool_call": (ReactiveElement.RIPPLE, 0.7, "accent", 2.0),
            "llm_start": (ReactiveElement.STREAM, 0.5, "soft", 3.0),
            "agent_start": (ReactiveElement.PULSE, 1.0, "bright", 2.5),
            "memory_save": (ReactiveElement.BLOOM, 0.8, "accent", 3.0),
            "error": (ReactiveElement.SHATTER, 1.0, "warning", 2.0),
        }
        cfg = element_map.get(event_kind)
        if cfg:
            elem, inten, color, dur = cfg
            return Reaction(
                element=elem, intensity=inten,
                origin=(0.5, 0.5), color_key=color, duration=dur,
            )
        return None

    def intensity_curve(self, raw: float) -> float:
        # Smooth sigmoid for gradual visual response
        x = (raw - 0.5) * 8.0
        return 1.0 / (1.0 + math.exp(-x))

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier
        self._angle += 0.008 + 0.004 * intensity

        cx, cy = w / 2.0, h / 2.0
        max_r = min(cx, cy) * 0.9

        bright_attr = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs.get("accent", 0))
        soft_attr = curses.color_pair(color_pairs.get("soft", 0))
        base_attr = curses.color_pair(color_pairs.get("base", 0)) | curses.A_DIM

        chars = " ·.:;*+#@"
        n_chars = len(chars) - 1

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                dx = (x - cx) / 2.0  # aspect correction
                dy = y - cy
                dist = math.sqrt(dx * dx + dy * dy)

                if dist > max_r:
                    continue

                angle = math.atan2(dy, dx) + self._angle
                # Fold angle into one quadrant (kaleidoscope effect in shader)
                fold_angle = abs(math.fmod(angle, math.pi / 2))

                # Multi-wave interference
                v = (
                    math.sin(fold_angle * 6 + f * 0.05) * 0.4
                    + math.sin(dist * 0.4 - f * 0.08) * 0.3
                    + math.sin(fold_angle * 3 - dist * 0.2 + f * 0.03) * 0.3
                )
                v = (v + 1.0) / 2.0
                v *= intensity
                v *= 1.0 - (dist / max_r) * 0.4  # fade toward edges

                v = _clamp(v)
                ci = int(v * n_chars)
                ch = chars[ci]
                if ch == " ":
                    continue

                if v > 0.75:
                    attr = bright_attr
                elif v > 0.50:
                    attr = accent_attr
                elif v > 0.25:
                    attr = soft_attr
                else:
                    attr = base_attr

                _safe(stdscr, y, x, ch, attr)

        # Center jewel
        icx, icy = int(cx), int(cy)
        if 1 <= icy < h - 1 and 0 <= icx < w - 1:
            pulse = abs(math.sin(f * 0.1))
            ch = "◈" if pulse > 0.5 else "◇"
            _safe(stdscr, icy, icx, ch, bright_attr)


# ═══════════════════════════════════════════════════════════════════════════
# THEME 4: electric-storm — Lightning + Rain with Neural Excitation
# ═══════════════════════════════════════════════════════════════════════════

class ElectricStormPlugin(ThemePlugin):
    """Raging electrical storm with branching lightning and driving rain.

    Combines:
      - neural_field_config emergent for cascading excitation on lightning
      - echo_decay for lightning afterglow persistence
      - warp_field for wind-driven distortion
      - decay_sequence for fading lightning trails
      - reactive: errors → SHATTER (thunder), tool_call → SPARK (lightning)
    """

    name = "electric-storm"

    def __init__(self):
        super().__init__()
        self._lightning_bolts: List[List[Tuple[int, int]]] = []
        self._bolt_timer = 0
        self._rng = random.Random(77)

    # -- emergent --
    def neural_field_config(self) -> Optional[Dict]:
        return {
            "threshold": 3,
            "fire_duration": 2,
            "refractory": 5,
        }

    def emergent_layer(self) -> str:
        return "background"

    # -- postfx --
    def warp_field(self, x: int, y: int, w: int, h: int,
                   frame: int, intensity: float) -> Tuple[int, int]:
        # Wind-driven horizontal warp — stronger near top
        wind_strength = intensity * 1.2 * (1.0 - y / max(h, 1))
        dx = int(wind_strength * math.sin(frame * 0.05 + y * 0.15))
        nx = max(0, min(w - 1, x + dx))
        return (nx, y)

    def echo_decay(self) -> int:
        return 5

    def glow_radius(self) -> int:
        return 2

    def decay_sequence(self) -> Optional[str]:
        return "█▓▒░·. "

    # -- layout: cloud nodes across the top --
    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        cloud_y_range = (1, max(2, int(h * 0.2)))
        for _ in range(min(count, 12)):
            x = rng.uniform(4, w - 5)
            y = rng.uniform(cloud_y_range[0], cloud_y_range[1])
            nodes.append((x, y))
        return nodes

    def step_star(self, star, frame, w, h, rng):
        # Rain: diagonal fall with wind
        wind = 0.15 + 0.1 * math.sin(frame * 0.01)
        star[1] += star[2] * 0.5 + 0.4
        star[0] += wind
        if star[1] >= h - 1:
            star[1] = rng.uniform(0, 2)
            star[0] = rng.uniform(0, w - 1)
        if star[0] >= w - 1:
            star[0] = 0
        return True

    def star_glyph(self, brightness, char_idx):
        return "│" if brightness > 0.5 else "|"

    def spawn_particle(self, w, h, nodes, rng):
        # Ground splashes
        x = rng.uniform(2, w - 3)
        y = h - rng.uniform(1, 3)
        vx = rng.uniform(-0.1, 0.1)
        vy = rng.uniform(-0.08, 0.0)
        char = rng.choice("·~")
        life = rng.randint(3, 7)
        return Particle(x, y, vx, vy, life, life, char)

    def particle_base_chance(self):
        return 0.08

    def node_glyph(self, idx, intensity, total):
        if intensity > 0.6:
            return "▓"
        return "░"

    def node_color_key(self, idx, intensity, total):
        return "soft"

    def edge_glyph(self, dx, dy):
        return "─"

    def edge_color_key(self, step, idx_a, frame):
        return "soft"

    def pulse_style(self):
        return "cloud"

    def pulse_params(self):
        return (0.35, 0.25)

    # -- reactive --
    def react(self, event_kind: str, data: Dict) -> Optional[Reaction]:
        if event_kind == "tool_call":
            return Reaction(
                element=ReactiveElement.SPARK,
                intensity=0.9,
                origin=(random.random(), 0.15),
                color_key="bright",
                duration=1.0,
                data={"lightning": True},
            )
        if event_kind == "error":
            return Reaction(
                element=ReactiveElement.SHATTER,
                intensity=1.0,
                origin=(0.5, 0.2),
                color_key="warning",
                duration=3.0,
                sound="thunder",
            )
        if event_kind == "llm_start":
            return Reaction(
                element=ReactiveElement.WAVE,
                intensity=0.6,
                origin=(0.0, 0.5),
                color_key="soft",
                duration=2.5,
            )
        return None

    def palette_shift(self, trigger_effect, intensity: float,
                      base_palette) -> Optional[Tuple]:
        if trigger_effect == "error":
            return (
                curses.COLOR_WHITE,
                curses.COLOR_YELLOW,
                curses.COLOR_WHITE,
                curses.COLOR_BLUE,
            )
        return None

    def special_effects(self) -> List[SpecialEffect]:
        return [
            SpecialEffect(
                name="thunder-flash",
                trigger_kinds=["burst", "error"],
                min_intensity=0.6,
                cooldown=3.0,
                duration=1.5,
            ),
        ]

    def draw_special(self, stdscr, state, color_pairs,
                     special_name: str, progress: float,
                     intensity: float) -> None:
        if special_name != "thunder-flash":
            return
        w, h = state.width, state.height
        # Brief full-screen flash that fades
        if progress < 0.15:
            bright_attr = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
            for y in range(1, min(h - 1, 4)):
                for x in range(0, w - 1, 3):
                    _safe(stdscr, y, x, "▓", bright_attr)

    def sound_cues(self) -> Dict[str, SoundCue]:
        return {
            "error": SoundCue(
                name="thunder",
                type="bell",
                value="",
                volume=1.0,
                priority=10,
            ),
        }

    def _generate_bolt(self, w, h):
        """Generate a branching lightning bolt path.

        Returns [age, [(x,y), ...]] — age starts at 0 and is incremented
        each frame in draw_extras. Branches are appended in the same format.
        """
        rng = self._rng
        start_x = rng.randint(int(w * 0.15), int(w * 0.85))
        points = [(start_x, 1)]
        x, y = start_x, 1
        while y < h - 2:
            y += rng.randint(1, 3)
            x += rng.randint(-3, 3)
            x = max(1, min(w - 2, x))
            y = min(h - 2, y)
            points.append((x, y))
            # Branch chance
            if rng.random() < 0.15 and len(points) > 3:
                branch = [(x, y)]
                bx, by = x, y
                for _ in range(rng.randint(2, 5)):
                    by += rng.randint(1, 2)
                    bx += rng.choice([-2, -1, 1, 2])
                    bx = max(1, min(w - 2, bx))
                    by = min(h - 2, by)
                    branch.append((bx, by))
                self._lightning_bolts.append([0, branch])
        return [0, points]

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier

        bright_attr = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs.get("accent", 0))
        soft_attr = curses.color_pair(color_pairs.get("soft", 0))
        base_attr = curses.color_pair(color_pairs.get("base", 0)) | curses.A_DIM

        # Cloud layer — dense dark blocks at top
        cloud_h = max(2, int(h * 0.18))
        for y in range(0, cloud_h):
            for x in range(0, w - 1):
                v = (math.sin(x * 0.15 + f * 0.02 + y * 0.3)
                     + math.sin(x * 0.08 - f * 0.015) + 1.0) / 3.0
                if v > 0.4:
                    ch = "▓" if v > 0.65 else "▒"
                    _safe(stdscr, y, x, ch, soft_attr)

        # Generate new lightning periodically
        self._bolt_timer += 1
        bolt_interval = max(15, int(60 - 40 * intensity))
        if self._bolt_timer >= bolt_interval:
            self._bolt_timer = 0
            bolt = self._generate_bolt(w, h)
            self._lightning_bolts.append(bolt)

        # Draw and age lightning bolts
        # Each bolt is stored as [age, [(x,y), ...]] to avoid setting attrs on lists
        new_bolts = []
        for bolt in self._lightning_bolts:
            if not bolt:
                continue
            # Support both old plain-list bolts (no age) and new [age, points] pairs
            if isinstance(bolt[0], int):
                # New format: [age, points_list]
                age_val = bolt[0] + 1
                points = bolt[1]
                updated = [age_val, points]
            else:
                # Plain list of (x,y) — upgrade to new format on first encounter
                age_val = 1
                points = bolt
                updated = [age_val, points]

            if age_val > 8:
                continue
            new_bolts.append(updated)

            for bx, by in points:
                if not (0 <= by < h and 0 <= bx < w - 1):
                    continue
                if age_val <= 2:
                    _safe(stdscr, by, bx, "█", bright_attr)
                elif age_val <= 4:
                    _safe(stdscr, by, bx, "▓", accent_attr)
                elif age_val <= 6:
                    _safe(stdscr, by, bx, "▒", soft_attr)
                else:
                    _safe(stdscr, by, bx, "░", base_attr)

        self._lightning_bolts = new_bolts

        # Ground line
        if h > 4:
            for x in range(0, w - 1, 2):
                _safe(stdscr, h - 2, x, "▁", base_attr)


# ═══════════════════════════════════════════════════════════════════════════
# THEME 5: coral-growth — L-System Branching with Reaction-Diffusion
# ═══════════════════════════════════════════════════════════════════════════

class CoralGrowthPlugin(ThemePlugin):
    """Living coral structure that grows via L-system rules with chemical backdrop.

    Combines:
      - reaction_diffusion_config emergent for chemical field backdrop
      - automaton_config for cyclic cellular automaton overlay
      - echo_decay for growth trail persistence
      - depth_layers for parallax depth effect
      - reactive: memory_save → BLOOM (new growth), tool_call → RIPPLE
    """

    name = "coral-growth"

    def __init__(self):
        super().__init__()
        self._branches: List[Dict] = []
        self._growth_timer = 0
        self._rng = random.Random(42)
        self._max_branches = 80

    # -- emergent: dual systems --
    def reaction_diffusion_config(self) -> Optional[Dict]:
        return {
            "feed": 0.040,
            "kill": 0.062,
            "update_interval": 2,
        }

    def automaton_config(self) -> Optional[Dict]:
        return {
            "rule": "cyclic",
            "density": 0.3,
            "update_interval": 4,
        }

    def emergent_layer(self) -> str:
        return "background"

    # -- postfx --
    def echo_decay(self) -> int:
        return 6

    def depth_layers(self) -> int:
        return 3

    def glow_radius(self) -> int:
        return 1

    def decay_sequence(self) -> Optional[str]:
        return "█▓▒░·. "

    # -- layout: base anchor nodes --
    def build_nodes(self, w, h, cx, cy, count, rng):
        nodes = []
        # Anchor points along the bottom
        n_anchors = min(count, 5)
        for i in range(n_anchors):
            x = w * (0.15 + 0.7 * i / max(1, n_anchors - 1))
            y = h - 3
            nodes.append((x, y))
        return nodes

    def node_glyph(self, idx, intensity, total):
        return "◉" if intensity > 0.5 else "●"

    def node_color_key(self, idx, intensity, total):
        return "accent"

    def edge_glyph(self, dx, dy):
        if abs(dy) > abs(dx) * 2:
            return "│"
        elif abs(dx) > abs(dy) * 2:
            return "─"
        elif dx * dy < 0:
            return "╱"
        else:
            return "╲"

    def pulse_style(self):
        return "cloud"

    def pulse_params(self):
        return (0.20, 0.18)

    # -- reactive --
    def react(self, event_kind: str, data: Dict) -> Optional[Reaction]:
        if event_kind == "memory_save" or event_kind == "skill_create":
            return Reaction(
                element=ReactiveElement.BLOOM,
                intensity=1.0,
                origin=(random.random(), 0.8),
                color_key="accent",
                duration=4.0,
                data={"growth_burst": True},
            )
        if event_kind == "tool_call":
            return Reaction(
                element=ReactiveElement.RIPPLE,
                intensity=0.6,
                origin=(random.random(), random.random()),
                color_key="soft",
                duration=2.0,
            )
        if event_kind == "agent_start":
            return Reaction(
                element=ReactiveElement.CONSTELLATION,
                intensity=0.9,
                origin=(0.5, 0.9),
                color_key="bright",
                duration=3.0,
            )
        if event_kind == "error":
            return Reaction(
                element=ReactiveElement.SHATTER,
                intensity=0.8,
                origin=(0.5, 0.5),
                color_key="warning",
                duration=2.0,
            )
        return None

    def special_effects(self) -> List[SpecialEffect]:
        return [
            SpecialEffect(
                name="growth-surge",
                trigger_kinds=["burst", "memory_save"],
                min_intensity=0.5,
                cooldown=6.0,
                duration=4.0,
            ),
        ]

    def draw_special(self, stdscr, state, color_pairs,
                     special_name: str, progress: float,
                     intensity: float) -> None:
        if special_name != "growth-surge":
            return
        w, h = state.width, state.height
        accent_attr = curses.color_pair(color_pairs.get("accent", 0)) | curses.A_BOLD
        # Expanding rings of coral dots from bottom center
        cx = w // 2
        base_y = h - 3
        n_rings = int(progress * 5) + 1
        for ring in range(n_rings):
            r = int((ring + 1) * min(w, h) * 0.08 * progress)
            for ang in range(0, 360, 12):
                theta = math.radians(ang)
                px = int(cx + r * math.cos(theta) * 2)
                py = int(base_y - r * math.sin(theta) * 0.6)
                if 1 <= py < h - 1 and 0 <= px < w - 1:
                    _safe(stdscr, py, px, "·", accent_attr)

    def _grow_branch(self, x, y, angle, depth, w, h):
        """Recursively grow a coral branch."""
        if depth <= 0 or len(self._branches) >= self._max_branches:
            return
        rng = self._rng
        length = rng.randint(2, 5)
        points = []
        cx, cy = x, y
        for _ in range(length):
            cx += math.cos(angle) * 2  # aspect correction
            cy += math.sin(angle)
            ix, iy = int(cx), int(cy)
            if not (1 <= iy < h - 1 and 0 <= ix < w - 1):
                break
            points.append((ix, iy))

        if points:
            self._branches.append({
                "points": points,
                "depth": depth,
                "age": 0,
            })
            end_x, end_y = points[-1]
            # Branch: 1-3 sub-branches at varied angles
            n_sub = rng.randint(1, min(3, depth))
            for _ in range(n_sub):
                sub_angle = angle + rng.uniform(-0.8, 0.8)
                # Bias upward
                sub_angle = min(-0.2, sub_angle) if angle < 0 else max(-math.pi + 0.2, sub_angle)
                self._grow_branch(end_x, end_y, sub_angle, depth - 1, w, h)

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier

        bright_attr = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs.get("accent", 0))
        soft_attr = curses.color_pair(color_pairs.get("soft", 0))
        base_attr = curses.color_pair(color_pairs.get("base", 0)) | curses.A_DIM

        # Grow new branches periodically from anchor points
        self._growth_timer += 1
        grow_interval = max(30, int(100 - 60 * intensity))
        if self._growth_timer >= grow_interval and len(self._branches) < self._max_branches:
            self._growth_timer = 0
            # Pick a random anchor point along bottom
            anchor_x = self._rng.randint(int(w * 0.1), int(w * 0.9))
            anchor_y = h - 3
            # Grow upward with slight random angle
            angle = -math.pi / 2 + self._rng.uniform(-0.5, 0.5)
            depth = self._rng.randint(2, 4)
            self._grow_branch(anchor_x, anchor_y, angle, depth, w, h)

        # Age and cull branches
        new_branches = []
        for branch in self._branches:
            branch["age"] += 1
            if branch["age"] < 500:  # persist a long time
                new_branches.append(branch)
        self._branches = new_branches

        # Draw all branches
        coral_chars = {
            4: "█", 3: "▓", 2: "▒", 1: "░",
        }
        for branch in self._branches:
            depth = branch["depth"]
            age = branch["age"]
            ch = coral_chars.get(depth, "·")

            if age < 10:
                attr = bright_attr
            elif age < 50:
                attr = accent_attr
            elif age < 200:
                attr = soft_attr
            else:
                attr = base_attr

            for px, py in branch["points"]:
                if 1 <= py < h - 1 and 0 <= px < w - 1:
                    _safe(stdscr, py, px, ch, attr)

        # Seafloor base
        if h > 4:
            for x in range(0, w - 1):
                v = math.sin(x * 0.2 + f * 0.01) * 0.5 + 0.5
                ch = "▄" if v > 0.6 else "▁"
                _safe(stdscr, h - 2, x, ch, soft_attr)

        # Bubble particles drifting up
        if f % 8 == 0:
            bx = self._rng.randint(2, w - 3)
            by = h - self._rng.randint(3, 6)
            if 1 <= by < h - 1:
                _safe(stdscr, by, bx, "°", base_attr)

        # Growth counter
        info = f"branches: {len(self._branches)}"
        info_x = max(0, w - len(info) - 2)
        if h > 3:
            _safe(stdscr, h - 1, info_x, info,
                  curses.color_pair(color_pairs.get("soft", 0)) | curses.A_DIM)

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds: float):
        if idle_seconds > 5.0 and state.frame % 60 == 0:
            w, h = state.width, state.height
            # Gentle current particles
            x = random.randint(1, max(2, w - 2))
            y = random.randint(int(h * 0.3), max(int(h * 0.3) + 1, h - 4))
            _safe(stdscr, y, x, "~",
                  curses.color_pair(color_pairs.get("soft", 0)) | curses.A_DIM)

    def particle_base_chance(self):
        return 0.04

    def spawn_particle(self, w, h, nodes, rng):
        # Rising bubbles
        x = rng.uniform(3, w - 4)
        y = rng.uniform(h * 0.4, h - 4)
        vx = rng.uniform(-0.03, 0.03)
        vy = rng.uniform(-0.15, -0.05)
        char = rng.choice("°○·")
        life = rng.randint(15, 35)
        return Particle(x, y, vx, vy, life, life, char)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register(DNAHelixPlugin())
register(PendulumWavesPlugin())
register(KaleidoscopePlugin())
register(ElectricStormPlugin())
register(CoralGrowthPlugin())
