"""Advanced screens — 5 themes showcasing v0.2.0 engine features with novel visuals.

Themes:
  dna-helix         — Double helix with codon-colored base pairs, warp distortion
  pendulum-waves    — 15 pendulums forming traveling wave patterns
  kaleidoscope      — Mirror-symmetry mandala with boids and glow
  ghost-echo        — Afterimage echo trails with void erosion and decay
  magnetic-field    — Iron filing field lines with physarum + force points
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

class DnaHelixPlugin(ThemePlugin):
    """Double helix scrolling vertically with codon-colored base pairs.

    Uses: warp_field (sinusoidal distortion), echo_decay (afterimage trails),
          glow_radius, reactive events (BLOOM on memory_save, SPARK on tools).
    """

    name = "dna-strand"

    def __init__(self):
        super().__init__()
        self._codons = "ATCGATCGAATTCCGG"  # repeating pattern
        self._scroll = 0.0

    # -- emergent: none (pure procedural) --

    # -- postfx: keep it clean — subtle warp only, no glow halos or block smear --
    def warp_field(self, x: int, y: int, w: int, h: int,
                   frame: int, intensity: float) -> Tuple[int, int]:
        # Gentle horizontal wobble — amp capped so helix doesn't blur
        amp = min(intensity, 0.6) * 1.5
        t = frame * 0.05
        dx = int(amp * math.sin(t + y * 0.18))
        return (max(0, min(w - 1, x + dx)), y)

    # No echo_decay — smear obscures the paired base-pair rungs
    # No glow_radius — creates purple box halos with MAGENTA palette
    # No decay_sequence — block chars produce flashing fills

    # -- layout: two vertical columns of nodes (backbone) --
    def build_nodes(self, w: int, h: int, cx: float, cy: float,
                    count: int, rng) -> List[Tuple[float, float]]:
        nodes = []
        spacing = max(2, h // max(1, count // 2))
        for i in range(count):
            side = i % 2  # 0=left strand, 1=right strand
            row = (i // 2) * spacing + 2
            if row >= h - 2:
                break
            offset = 8
            x = cx - offset if side == 0 else cx + offset
            nodes.append((x, float(row)))
        return nodes

    def build_edges_extra(self, nodes, edges_set):
        # Connect paired nodes (base pairs across strands)
        for i in range(0, len(nodes) - 1, 2):
            edges_set.add((i, i + 1))
        # Connect along each backbone
        for i in range(0, len(nodes) - 2, 2):
            edges_set.add((i, i + 2))
        for i in range(1, len(nodes) - 2, 2):
            edges_set.add((i, i + 2))

    def step_nodes(self, nodes, frame, w, h):
        cx = w / 2.0
        self._scroll += 0.08
        for i in range(len(nodes)):
            side = i % 2
            row_base = (i // 2) * max(2, h // max(1, len(nodes) // 2)) + 2
            # Helix: x oscillates sinusoidally, phase offset between strands
            phase = self._scroll + row_base * 0.25
            if side == 0:
                x = cx + math.sin(phase) * 12
            else:
                x = cx + math.sin(phase + math.pi) * 12
            y = row_base
            if 2 <= y < h - 2:
                nodes[i] = (max(2, min(w - 3, x)), float(y))

    # -- glyphs --
    def node_glyph(self, idx: int, intensity: float, total: int) -> str:
        codon = self._codons[idx % len(self._codons)]
        return codon

    def node_color_key(self, idx: int, intensity: float, total: int) -> str:
        codon = self._codons[idx % len(self._codons)]
        return {"A": "bright", "T": "accent", "C": "soft", "G": "base"}.get(codon, "soft")

    def edge_glyph(self, dx: float, dy: float) -> str:
        if abs(dx) > abs(dy) * 2:
            return "═"  # base pair rungs
        return "│"  # backbone

    def edge_color_key(self, step: int, idx_a: int, frame: int) -> str:
        return "accent" if step % 2 == 0 else "soft"

    def pulse_style(self) -> str:
        return "ripple"

    def pulse_params(self) -> Tuple[float, float]:
        return (0.35, 0.20)

    # -- particles: nucleotide fragments --
    def particle_base_chance(self) -> float:
        return 0.06

    def spawn_particle(self, w: int, h: int, nodes, rng) -> Optional[Particle]:
        if nodes:
            nx, ny = rng.choice(nodes)
        else:
            nx, ny = w / 2, rng.uniform(2, h - 3)
        angle = rng.uniform(0, math.tau)
        speed = rng.uniform(0.1, 0.3)
        return Particle(
            x=float(nx), y=float(ny),
            vx=math.cos(angle) * speed * 2,
            vy=math.sin(angle) * speed,
            life=rng.randint(8, 20),
            max_life=20,
            char=rng.choice("ATCG·"),
        )

    def particle_color_key(self, age_ratio: float) -> str:
        return "bright" if age_ratio > 0.6 else "soft"

    # -- reactive --
    def react(self, event_kind: str, data: Dict[str, Any]) -> Optional[Reaction]:
        if event_kind == "memory_save" or event_kind == "skill_create":
            return Reaction(
                element=ReactiveElement.BLOOM,
                intensity=1.0,
                origin=(0.5, 0.5),
                color_key="accent",
                duration=3.0,
                data={"helix_bloom": True},
            )
        if event_kind == "tool_call":
            return Reaction(
                element=ReactiveElement.SPARK,
                intensity=0.7,
                origin=(random.random(), random.random()),
                color_key="bright",
                duration=1.5,
            )
        if event_kind == "error":
            return Reaction(
                element=ReactiveElement.SHATTER,
                intensity=1.0,
                origin=(0.5, 0.5),
                color_key="warning",
                duration=2.0,
            )
        return None

    # -- draw_extras: helix backbone highlight --
    def draw_extras(self, stdscr, state, color_pairs) -> None:
        w, h = state.width, state.height
        f = state.frame
        cx = w / 2.0
        intensity = state.intensity_multiplier

        soft_attr = curses.color_pair(color_pairs.get("soft", 0))
        accent_attr = curses.color_pair(color_pairs.get("accent", 0))

        # Draw faint helix backbone curves
        for y in range(1, h - 1):
            phase = self._scroll + y * 0.25
            x1 = int(cx + math.sin(phase) * 12)
            x2 = int(cx + math.sin(phase + math.pi) * 12)
            # Faint connecting rungs between strands (when close)
            if abs(x1 - x2) < 6 and y % 3 == 0:
                lo, hi = min(x1, x2), max(x1, x2)
                for rx in range(lo + 1, hi):
                    if 0 <= rx < w - 1:
                        v = abs(math.sin(phase * 2)) * intensity
                        if v > 0.3:
                            _safe(stdscr, y, rx, "─", soft_attr)


# ═══════════════════════════════════════════════════════════════════════════
# THEME 2: pendulum-waves — Phase-Shifted Pendulum Array
# ═══════════════════════════════════════════════════════════════════════════

class PendulumWavesPlugin(ThemePlugin):
    """15 pendulums with slightly different frequencies creating traveling waves.

    Uses: depth_layers (3-layer parallax), symmetry (mirror_x), echo_decay,
          reactive events (WAVE on llm_start, GAUGE on token_usage).
    """

    name = "pendulum-array"

    _N_PENDULUMS = 15

    # -- postfx --
    def depth_layers(self) -> int:
        return 3

    def symmetry(self) -> Optional[str]:
        return "mirror_x"

    def echo_decay(self) -> int:
        return 4

    def glow_radius(self) -> int:
        return 1

    # -- layout: pivots centred horizontally, placed at h*0.15 (upper area) --
    def build_nodes(self, w: int, h: int, cx: float, cy: float,
                    count: int, rng) -> List[Tuple[float, float]]:
        nodes = []
        n = self._N_PENDULUMS
        spacing = max(3, (w - 8) // max(1, n - 1))
        x_start = max(4, (w - spacing * (n - 1)) // 2)
        # Pivot row: 15% down — arms can swing to 85% of screen height
        pivot_y = max(2.0, h * 0.15)
        for i in range(n):
            x = x_start + i * spacing
            nodes.append((float(x), pivot_y))   # pivot
            nodes.append((float(x), pivot_y + h * 0.35))  # bob (initial)
        return nodes

    def build_edges_extra(self, nodes, edges_set):
        # Connect each pivot to its bob
        for i in range(0, len(nodes), 2):
            if i + 1 < len(nodes):
                edges_set.add((i, i + 1))

    def step_nodes(self, nodes, frame, w, h):
        n = self._N_PENDULUMS
        pivot_y = max(2.0, h * 0.15)
        # Arms can sweep from pivot down to near the bottom
        max_arm = h * 0.78
        for i in range(n):
            pivot_idx = i * 2
            bob_idx = i * 2 + 1
            if bob_idx >= len(nodes):
                break
            px, _ = nodes[pivot_idx]
            # Update pivot y in case of resize
            nodes[pivot_idx] = (px, pivot_y)
            # Each pendulum: frequency = base + i*delta (creates wave patterns)
            base_freq = 0.04
            freq = base_freq + i * 0.003
            angle = math.sin(frame * freq) * 1.2  # swing amplitude ~70 degrees
            arm = max_arm * (0.45 + 0.35 * (i / max(n - 1, 1)))
            bx = px + math.sin(angle) * arm * 0.55  # aspect correction
            by = pivot_y + math.cos(angle) * arm * 0.50
            by = max(pivot_y + 2, min(h - 2, by))
            bx = max(2, min(w - 3, bx))
            nodes[bob_idx] = (bx, by)

    # -- glyphs --
    def node_glyph(self, idx: int, intensity: float, total: int) -> str:
        if idx % 2 == 0:
            return "┬"  # pivot
        return "●" if intensity > 0.5 else "○"  # bob

    def node_color_key(self, idx: int, intensity: float, total: int) -> str:
        if idx % 2 == 0:
            return "soft"  # pivot dim
        # Bobs colored by position in array
        bob_i = idx // 2
        colors = ["bright", "accent", "soft"]
        return colors[bob_i % len(colors)]

    def edge_glyph(self, dx: float, dy: float) -> str:
        if abs(dy) > abs(dx) * 2:
            return "│"
        elif dx * dy < 0:
            return "╱"
        else:
            return "╲"

    def edge_color_key(self, step: int, idx_a: int, frame: int) -> str:
        return "soft"

    def pulse_style(self) -> str:
        return "rays"

    # -- particles: pendulum energy sparks --
    def particle_base_chance(self) -> float:
        return 0.04

    def spawn_particle(self, w: int, h: int, nodes, rng) -> Optional[Particle]:
        # Sparks from bob positions (odd indices)
        bobs = [(nodes[i][0], nodes[i][1]) for i in range(1, len(nodes), 2)]
        if bobs:
            bx, by = rng.choice(bobs)
        else:
            bx, by = w / 2, h / 2
        return Particle(
            x=float(bx), y=float(by),
            vx=rng.uniform(-0.2, 0.2),
            vy=rng.uniform(0.05, 0.15),
            life=rng.randint(6, 14),
            max_life=14,
            char=rng.choice("·∙°"),
        )

    # -- reactive --
    def react(self, event_kind: str, data: Dict[str, Any]) -> Optional[Reaction]:
        if event_kind == "llm_start":
            return Reaction(
                element=ReactiveElement.WAVE,
                intensity=0.9,
                origin=(0.0, 0.5),
                color_key="bright",
                duration=3.0,
                data={"direction": "right"},
            )
        if event_kind == "context_pressure" or event_kind == "token_usage":
            return Reaction(
                element=ReactiveElement.GAUGE,
                intensity=data.get("ratio", 0.5),
                origin=(0.9, 0.9),
                color_key="warning" if data.get("ratio", 0) > 0.8 else "accent",
                duration=5.0,
            )
        if event_kind == "tool_call":
            return Reaction(
                element=ReactiveElement.RIPPLE,
                intensity=0.6,
                origin=(random.random(), random.random()),
                color_key="accent",
                duration=1.5,
            )
        return None

    def intensity_curve(self, raw: float) -> float:
        # Quadratic: gentle ramp at low activity, steep at high
        return raw * raw

    # -- draw_extras: wave visualization at bottom --
    def draw_extras(self, stdscr, state, color_pairs) -> None:
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier
        soft_attr = curses.color_pair(color_pairs.get("soft", 0)) | curses.A_DIM

        # Draw the "virtual wave" formed by bob positions at bottom
        n = self._N_PENDULUMS
        bobs = []
        for i in range(1, min(len(state.nodes) if hasattr(state, 'nodes') else 0, n * 2), 2):
            pass  # nodes handled by engine

        # Faint wave trail at bottom
        trail_y = h - 3
        if trail_y > 1:
            for x in range(2, w - 2):
                base_freq = 0.04
                phase = 0.0
                v = 0.0
                for pi in range(n):
                    freq = base_freq + pi * 0.003
                    v += math.sin(f * freq + x * 0.15) / n
                v = (v + 1.0) / 2.0 * intensity
                if v > 0.3:
                    ch = "─" if v < 0.6 else "═"
                    _safe(stdscr, trail_y, x, ch, soft_attr)


# ═══════════════════════════════════════════════════════════════════════════
# THEME 3: kaleidoscope — Mirror-Symmetry Mandala with Boids
# ═══════════════════════════════════════════════════════════════════════════

class KaleidoscopePlugin(ThemePlugin):
    """Rotating mandala with boids swarming in one quadrant, mirrored 4-fold.

    Uses: boids_config, symmetry (mirror_xy), glow_radius, render_mask (circle),
          force_points (central vortex), reactive CONSTELLATION on connections.
    """

    name = "mandala-scope"

    # -- emergent --
    def boids_config(self) -> Optional[Dict[str, Any]]:
        return {
            "n_boids": 40,
            "sep_dist": 2.5,
            "align_dist": 6.0,
            "cohesion_dist": 10.0,
            "max_speed": 1.5,
        }

    def emergent_layer(self) -> str:
        return "midground"

    # -- postfx --
    def symmetry(self) -> Optional[str]:
        return "mirror_xy"

    def glow_radius(self) -> int:
        return 2

    def render_mask(self, w: int, h: int, frame: int,
                    intensity: float) -> Optional[List[List[bool]]]:
        cx, cy = w / 2, h / 2
        r_sq = (min(cx - 1, (cy - 1) * 2) * 0.92) ** 2 / 4
        mask: List[List[bool]] = []
        for row in range(h):
            line: List[bool] = []
            for col in range(w):
                dx = (col - cx) / 2.0
                dy = row - cy
                line.append((dx * dx + dy * dy) <= r_sq)
            mask.append(line)
        return mask

    def force_points(self, w: int, h: int, frame: int,
                     intensity: float) -> List[Tuple[int, int, float, float]]:
        cx, cy = w // 2, h // 2
        strength = 0.5 + intensity * 0.5
        return [(cx, cy, strength, "vortex")]

    def echo_decay(self) -> int:
        return 3

    # -- layout: radial ring of nodes --
    def build_nodes(self, w: int, h: int, cx: float, cy: float,
                    count: int, rng) -> List[Tuple[float, float]]:
        nodes = [(cx, cy)]  # center
        rings = [0.2, 0.45, 0.7]
        max_r = min(w / 2 - 4, (h / 2 - 2) * 2)
        for ri, frac in enumerate(rings):
            r = max_r * frac
            n_in_ring = max(4, count // (len(rings) + 1))
            for i in range(n_in_ring):
                a = (math.tau * i) / n_in_ring
                nodes.append((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.5))
        return nodes[:count]

    def step_nodes(self, nodes, frame, w, h):
        cx, cy = w / 2.0, h / 2.0
        spin = 0.012
        for i in range(1, len(nodes)):
            dx = nodes[i][0] - cx
            dy = nodes[i][1] - cy
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx) + spin
            nodes[i] = (cx + math.cos(a) * r, cy + math.sin(a) * r)

    # -- glyphs --
    def node_glyph(self, idx: int, intensity: float, total: int) -> str:
        if idx == 0:
            return "◎"
        glyphs = "◆◇✦✧●○"
        return glyphs[idx % len(glyphs)]

    def node_color_key(self, idx: int, intensity: float, total: int) -> str:
        if idx == 0:
            return "bright"
        colors = ["accent", "soft", "bright"]
        return colors[idx % len(colors)]

    def edge_glyph(self, dx: float, dy: float) -> str:
        if abs(dy) < abs(dx) * 0.4:
            return "─"
        elif abs(dx) < abs(dy) * 0.4:
            return "│"
        elif dx * dy < 0:
            return "╱"
        return "╲"

    def pulse_style(self) -> str:
        return "diamond"

    def pulse_params(self) -> Tuple[float, float]:
        return (0.30, 0.18)

    # -- particles --
    def particle_base_chance(self) -> float:
        return 0.08

    def spawn_particle(self, w: int, h: int, nodes, rng) -> Optional[Particle]:
        cx, cy = w / 2, h / 2
        a = rng.uniform(0, math.tau)
        r = rng.uniform(3, min(w, h) * 0.3)
        x = cx + math.cos(a) * r
        y = cy + math.sin(a) * r * 0.5
        # Tangential velocity (orbiting)
        vx = -math.sin(a) * 0.25
        vy = math.cos(a) * 0.12
        return Particle(
            x=x, y=y, vx=vx, vy=vy,
            life=rng.randint(15, 35),
            max_life=35,
            char=rng.choice("·✦✧∙"),
        )

    # -- reactive --
    def react(self, event_kind: str, data: Dict[str, Any]) -> Optional[Reaction]:
        if event_kind in ("mcp_connected", "platform_connect", "provider_health"):
            return Reaction(
                element=ReactiveElement.CONSTELLATION,
                intensity=0.8,
                origin=(0.5, 0.5),
                color_key="bright",
                duration=3.0,
            )
        if event_kind == "agent_start":
            return Reaction(
                element=ReactiveElement.PULSE,
                intensity=1.0,
                origin=(0.5, 0.5),
                color_key="accent",
                duration=2.5,
            )
        if event_kind == "compression_started":
            return Reaction(
                element=ReactiveElement.WAVE,
                intensity=0.9,
                origin=(0.5, 0.5),
                color_key="soft",
                duration=3.0,
            )
        return None

    # -- special effects --
    def special_effects(self) -> List[SpecialEffect]:
        return [
            SpecialEffect(
                name="mandala-bloom",
                trigger_kinds=["burst"],
                min_intensity=0.6,
                cooldown=6.0,
                duration=3.5,
            ),
        ]

    def draw_special(self, stdscr, state, color_pairs, special_name: str,
                     progress: float, intensity: float) -> None:
        if special_name != "mandala-bloom":
            return
        w, h = state.width, state.height
        cx, cy = w // 2, h // 2
        attr = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        # Expanding mandala ring
        n_petals = 8
        r = int(min(w // 2, h) * progress * 0.7)
        for petal in range(n_petals):
            base_a = (math.tau * petal) / n_petals + progress * math.pi
            for dr in range(0, r, 2):
                px = int(cx + dr * math.cos(base_a) * 2)
                py = int(cy + dr * math.sin(base_a))
                if 0 <= px < w and 0 <= py < h:
                    fade = 1.0 - dr / max(r, 1)
                    ch = "✦" if fade > 0.5 else "·"
                    _safe(stdscr, py, px, ch, attr)

    # -- ambient mandala rotation when idle --
    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds: float) -> None:
        if idle_seconds > 3.0 and state.frame % 15 == 0:
            w, h = state.width, state.height
            cx, cy = w // 2, h // 2
            a = random.uniform(0, math.tau)
            r = random.randint(3, min(w // 4, h // 3))
            px = int(cx + r * math.cos(a) * 2)
            py = int(cy + r * math.sin(a))
            if 0 <= px < w and 0 <= py < h:
                attr = curses.color_pair(color_pairs.get("soft", 0)) | curses.A_DIM
                _safe(stdscr, py, px, "✧", attr)


# ═══════════════════════════════════════════════════════════════════════════
# THEME 4: ghost-echo — Afterimage Echo Trails with Void Erosion
# ═══════════════════════════════════════════════════════════════════════════

class GhostEchoPlugin(ThemePlugin):
    """Spectral nodes that leave afterimage trails, with void holes eating the screen.

    Uses: echo_decay (6-frame deep trails), void_points (black holes),
          decay_sequence (fading chars), warp_field (wobble), depth_layers,
          reactive SHATTER on errors, GLYPH on personality changes.
    """

    name = "ghost-echo"

    def __init__(self):
        super().__init__()
        self._void_centers: List[Tuple[float, float, float]] = []  # (x_ratio, y_ratio, phase)

    # -- postfx --
    def echo_decay(self) -> int:
        return 6

    def decay_sequence(self) -> Optional[str]:
        return "◉●◎○◦·. "

    def depth_layers(self) -> int:
        return 2

    def glow_radius(self) -> int:
        return 1

    def warp_field(self, x: int, y: int, w: int, h: int,
                   frame: int, intensity: float) -> Tuple[int, int]:
        # Subtle wobble that increases with intensity
        amp = intensity * 1.2
        t = frame * 0.05
        dx = int(amp * math.sin(t + y * 0.2 + x * 0.05))
        dy = int(amp * 0.4 * math.cos(t * 1.3 + x * 0.15))
        nx = max(0, min(w - 1, x + dx))
        ny = max(0, min(h - 1, y + dy))
        return (nx, ny)

    def void_points(self, w: int, h: int, frame: int,
                    intensity: float) -> List[Tuple[int, int]]:
        # 2-3 void holes that orbit slowly, erasing content
        if not self._void_centers:
            rng = random.Random(77)
            self._void_centers = [
                (rng.random(), rng.random(), rng.uniform(0, math.tau))
                for _ in range(3)
            ]
        points: List[Tuple[int, int]] = []
        radius = int(2 + intensity * 3)
        for fx, fy, phase in self._void_centers:
            # Orbiting void centers
            t = frame * 0.02 + phase
            vx = int(fx * w + math.sin(t) * w * 0.15)
            vy = int(fy * h + math.cos(t * 0.7) * h * 0.12)
            # Fill small circle of void
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius * radius:
                        px, py = vx + dx, vy + dy
                        if 0 <= px < w and 0 <= py < h:
                            points.append((px, py))
        return points

    # -- layout: scattered ghost nodes --
    def build_nodes(self, w: int, h: int, cx: float, cy: float,
                    count: int, rng) -> List[Tuple[float, float]]:
        nodes = []
        for _ in range(count):
            x = rng.uniform(6, w - 7)
            y = rng.uniform(3, h - 4)
            nodes.append((x, y))
        return nodes

    def step_nodes(self, nodes, frame, w, h):
        # Nodes drift slowly in Lissajous-like paths
        for i in range(len(nodes)):
            x, y = nodes[i]
            phase = i * 0.7
            x += math.sin(frame * 0.015 + phase) * 0.3
            y += math.cos(frame * 0.012 + phase * 1.3) * 0.15
            nodes[i] = (max(3, min(w - 4, x)), max(2, min(h - 3, y)))

    # -- glyphs: ghostly --
    def node_glyph(self, idx: int, intensity: float, total: int) -> str:
        if intensity > 0.7:
            return "◉"
        elif intensity > 0.3:
            return "◎"
        return "○"

    def node_color_key(self, idx: int, intensity: float, total: int) -> str:
        return "bright" if intensity > 0.6 else "soft"

    def edge_glyph(self, dx: float, dy: float) -> str:
        return "┄" if abs(dx) > abs(dy) else "┆"

    def edge_color_key(self, step: int, idx_a: int, frame: int) -> str:
        # Edges flicker in and out
        return "soft" if (step + frame) % 8 < 5 else "base"

    def star_glyph(self, brightness: float, char_idx: int) -> Optional[str]:
        return "·" if brightness > 0.5 else None

    def pulse_style(self) -> str:
        return "cloud"

    def pulse_params(self) -> Tuple[float, float]:
        return (0.25, 0.20)

    # -- particles: spectral wisps --
    def particle_base_chance(self) -> float:
        return 0.05

    def spawn_particle(self, w: int, h: int, nodes, rng) -> Optional[Particle]:
        if nodes:
            nx, ny = rng.choice(nodes)
        else:
            nx, ny = rng.uniform(4, w - 5), rng.uniform(2, h - 3)
        vx = rng.uniform(-0.15, 0.15)
        vy = rng.uniform(-0.1, 0.1)
        return Particle(
            x=float(nx), y=float(ny),
            vx=vx, vy=vy,
            life=rng.randint(12, 30),
            max_life=30,
            char=rng.choice("◦·∙°"),
        )

    def particle_color_key(self, age_ratio: float) -> str:
        if age_ratio > 0.7:
            return "bright"
        elif age_ratio > 0.3:
            return "accent"
        return "soft"

    # -- reactive --
    def react(self, event_kind: str, data: Dict[str, Any]) -> Optional[Reaction]:
        if event_kind == "error" or event_kind == "crash":
            return Reaction(
                element=ReactiveElement.SHATTER,
                intensity=1.0,
                origin=(0.5, 0.5),
                color_key="warning",
                duration=2.5,
                sound="bell",
            )
        if event_kind == "personality_change" or event_kind == "reasoning_change":
            return Reaction(
                element=ReactiveElement.GLYPH,
                intensity=0.8,
                origin=(0.5, 0.3),
                color_key="accent",
                duration=4.0,
            )
        if event_kind == "llm_start":
            return Reaction(
                element=ReactiveElement.STREAM,
                intensity=0.6,
                origin=(0.5, 0.5),
                color_key="soft",
                duration=3.0,
            )
        if event_kind == "checkpoint_rollback":
            return Reaction(
                element=ReactiveElement.WAVE,
                intensity=1.0,
                origin=(0.0, 0.5),
                color_key="warning",
                duration=2.0,
            )
        return None

    def palette_shift(self, trigger_effect: str, intensity: float,
                      base_palette) -> Optional[Tuple[int, int, int, int]]:
        if trigger_effect == "error" or str(trigger_effect) == str(ReactiveElement.SHATTER):
            return (curses.COLOR_RED, curses.COLOR_YELLOW,
                    curses.COLOR_WHITE, curses.COLOR_RED)
        return None

    def intensity_curve(self, raw: float) -> float:
        # Logarithmic: responsive at low activity, saturates at high
        return math.log1p(raw * 4) / math.log1p(4)

    # -- sound --
    def sound_cues(self) -> Dict[str, SoundCue]:
        return {
            "error": SoundCue(
                name="ghost-shatter",
                type="bell",
                value="",
                volume=0.7,
                priority=10,
            ),
        }

    # -- draw_extras: void border glow --
    def draw_extras(self, stdscr, state, color_pairs) -> None:
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier
        dim_attr = curses.color_pair(color_pairs.get("base", 0)) | curses.A_DIM

        # Faint void glow rings around void centers
        for fx, fy, phase in self._void_centers:
            t = f * 0.02 + phase
            vx = int(fx * w + math.sin(t) * w * 0.15)
            vy = int(fy * h + math.cos(t * 0.7) * h * 0.12)
            radius = int(3 + intensity * 4)
            # Draw ring just outside void radius
            ring_r = radius + 1
            for a_step in range(0, 360, 15):
                a = math.radians(a_step)
                px = int(vx + ring_r * math.cos(a) * 1.5)
                py = int(vy + ring_r * math.sin(a))
                if 0 <= px < w - 1 and 0 <= py < h - 1:
                    _safe(stdscr, py, px, "·", dim_attr)

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds: float) -> None:
        if idle_seconds > 2.0 and state.frame % 25 == 0:
            w, h = state.width, state.height
            x = random.randint(3, max(4, w - 4))
            y = random.randint(2, max(3, h - 3))
            attr = curses.color_pair(color_pairs.get("soft", 0)) | curses.A_DIM
            _safe(stdscr, y, x, random.choice("◦·"), attr)


# ═══════════════════════════════════════════════════════════════════════════
# THEME 5: magnetic-field — Iron Filing Field Lines with Physarum
# ═══════════════════════════════════════════════════════════════════════════

class MagneticFieldPlugin(ThemePlugin):
    """Magnetic field lines visualized as iron filings, with physarum growth.

    Uses: physarum_config (slime mold traces field lines), force_points
          (two magnetic poles), glow_radius, decay_sequence,
          reactive ORBIT on cron, TRAIL on file edits.
    Full-screen draw_extras renders the field line pattern.
    """

    name = "magnetic-field"

    def __init__(self):
        super().__init__()
        self._pole_phase = 0.0

    # -- emergent --
    def physarum_config(self) -> Optional[Dict[str, Any]]:
        return {
            "n_agents": 150,
            "sensor_dist": 4,
            "sensor_angle": 0.5,
            "deposit": 0.8,
            "decay": 0.90,
        }

    def emergent_layer(self) -> str:
        return "background"

    # -- postfx --
    def glow_radius(self) -> int:
        return 1

    def decay_sequence(self) -> Optional[str]:
        return "▓▒░·. "

    def force_points(self, w: int, h: int, frame: int,
                     intensity: float) -> List[Tuple[int, int, float, float]]:
        cx, cy = w // 2, h // 2
        self._pole_phase = frame * 0.008
        sep = w * 0.25
        strength = 0.6 + intensity * 0.4
        # Two poles: N and S
        px1 = int(cx - sep * math.cos(self._pole_phase))
        py1 = int(cy - sep * 0.3 * math.sin(self._pole_phase))
        px2 = int(cx + sep * math.cos(self._pole_phase))
        py2 = int(cy + sep * 0.3 * math.sin(self._pole_phase))
        return [
            (px1, py1, strength, "radial"),     # N pole pushes
            (px2, py2, -strength, "radial"),     # S pole pulls
        ]

    def echo_decay(self) -> int:
        return 2

    # -- layout: nodes along field lines --
    def build_nodes(self, w: int, h: int, cx: float, cy: float,
                    count: int, rng) -> List[Tuple[float, float]]:
        nodes = []
        # Two pole positions
        sep = w * 0.25
        poles = [(cx - sep, cy), (cx + sep, cy)]
        # Place nodes along 6 field lines emanating from north pole
        n_lines = 6
        nodes_per_line = max(2, count // n_lines)
        for li in range(n_lines):
            start_angle = math.pi * 0.15 + (math.pi * 0.7) * li / (n_lines - 1)
            for ni in range(nodes_per_line):
                t = (ni + 1) / (nodes_per_line + 1)
                # Parametric field line: arc from N to S pole
                nx = poles[0][0] + (poles[1][0] - poles[0][0]) * t
                arc_height = math.sin(t * math.pi) * h * 0.3 * math.sin(start_angle)
                ny = cy + arc_height
                nodes.append((max(3, min(w - 4, nx)), max(2, min(h - 3, ny))))
        return nodes[:count]

    def step_nodes(self, nodes, frame, w, h):
        cx, cy = w / 2.0, h / 2.0
        sep = w * 0.25
        phase = frame * 0.008
        # Poles rotate slowly, field lines follow
        p1x = cx - sep * math.cos(phase)
        p1y = cy - sep * 0.3 * math.sin(phase)
        p2x = cx + sep * math.cos(phase)
        p2y = cy + sep * 0.3 * math.sin(phase)

        n_lines = 6
        nodes_per_line = max(2, len(nodes) // n_lines)
        for li in range(n_lines):
            start_angle = math.pi * 0.15 + (math.pi * 0.7) * li / max(1, n_lines - 1)
            for ni in range(nodes_per_line):
                idx = li * nodes_per_line + ni
                if idx >= len(nodes):
                    break
                t = (ni + 1) / (nodes_per_line + 1)
                nx = p1x + (p2x - p1x) * t
                arc = math.sin(t * math.pi) * h * 0.3 * math.sin(start_angle)
                ny = (p1y + p2y) / 2 + arc
                nodes[idx] = (max(3, min(w - 4, nx)), max(2, min(h - 3, ny)))

    # -- glyphs --
    def node_glyph(self, idx: int, intensity: float, total: int) -> str:
        return "◉" if intensity > 0.6 else "·"

    def node_color_key(self, idx: int, intensity: float, total: int) -> str:
        return "bright" if intensity > 0.6 else "accent"

    def edge_glyph(self, dx: float, dy: float) -> str:
        # Field line direction arrows
        if abs(dx) > abs(dy) * 2:
            return "→" if dx > 0 else "←"
        elif abs(dy) > abs(dx) * 2:
            return "↓" if dy > 0 else "↑"
        elif dx > 0:
            return "↗" if dy < 0 else "↘"
        else:
            return "↖" if dy < 0 else "↙"

    def edge_color_key(self, step: int, idx_a: int, frame: int) -> str:
        return "accent" if (step + frame) % 6 < 4 else "soft"

    def pulse_style(self) -> str:
        return "rays"

    def pulse_params(self) -> Tuple[float, float]:
        return (0.35, 0.22)

    # -- particles: field line sparks --
    def particle_base_chance(self) -> float:
        return 0.06

    def spawn_particle(self, w: int, h: int, nodes, rng) -> Optional[Particle]:
        if nodes:
            nx, ny = rng.choice(nodes)
        else:
            nx, ny = w / 2, h / 2
        # Follow field direction (roughly toward S pole)
        cx = w / 2.0
        dx_dir = 1.0 if nx < cx else -1.0
        return Particle(
            x=float(nx), y=float(ny),
            vx=dx_dir * rng.uniform(0.1, 0.3),
            vy=rng.uniform(-0.1, 0.1),
            life=rng.randint(8, 18),
            max_life=18,
            char=rng.choice("→·∙°"),
        )

    def particle_color_key(self, age_ratio: float) -> str:
        return "bright" if age_ratio > 0.5 else "soft"

    # -- reactive --
    def react(self, event_kind: str, data: Dict[str, Any]) -> Optional[Reaction]:
        if event_kind == "cron_tick" or event_kind == "background_proc":
            return Reaction(
                element=ReactiveElement.ORBIT,
                intensity=0.6,
                origin=(0.5, 0.5),
                color_key="accent",
                duration=4.0,
            )
        if event_kind == "file_edit" or event_kind == "git_commit":
            return Reaction(
                element=ReactiveElement.TRAIL,
                intensity=0.7,
                origin=(random.random(), random.random()),
                color_key="bright",
                duration=2.5,
            )
        if event_kind == "tool_call":
            return Reaction(
                element=ReactiveElement.RIPPLE,
                intensity=0.8,
                origin=(random.random(), random.random()),
                color_key="accent",
                duration=1.5,
            )
        if event_kind == "error":
            return Reaction(
                element=ReactiveElement.SHATTER,
                intensity=1.0,
                origin=(0.5, 0.5),
                color_key="warning",
                duration=2.0,
            )
        return None

    # -- special effects --
    def special_effects(self) -> List[SpecialEffect]:
        return [
            SpecialEffect(
                name="pole-reversal",
                trigger_kinds=["burst"],
                min_intensity=0.8,
                cooldown=8.0,
                duration=4.0,
            ),
        ]

    def draw_special(self, stdscr, state, color_pairs, special_name: str,
                     progress: float, intensity: float) -> None:
        if special_name != "pole-reversal":
            return
        w, h = state.width, state.height
        cx, cy = w // 2, h // 2
        attr = curses.color_pair(color_pairs.get("warning", 0)) | curses.A_BOLD
        # Field lines collapse toward center then re-expand
        if progress < 0.5:
            r = int((1.0 - progress * 2) * min(w // 2, h // 2))
        else:
            r = int((progress - 0.5) * 2 * min(w // 2, h // 2))
        n_rays = 12
        for ray in range(n_rays):
            a = (math.tau * ray) / n_rays
            for d in range(1, r, 2):
                px = int(cx + d * math.cos(a) * 1.5)
                py = int(cy + d * math.sin(a))
                if 0 <= px < w and 0 <= py < h:
                    _safe(stdscr, py, px, "·", attr)

    # -- draw_extras: field line arrows in background --
    def draw_extras(self, stdscr, state, color_pairs) -> None:
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier
        dim_attr = curses.color_pair(color_pairs.get("base", 0)) | curses.A_DIM
        soft_attr = curses.color_pair(color_pairs.get("soft", 0))

        cx, cy = w / 2.0, h / 2.0
        sep = w * 0.25
        phase = f * 0.008
        p1x = cx - sep * math.cos(phase)
        p1y = cy - sep * 0.3 * math.sin(phase)
        p2x = cx + sep * math.cos(phase)
        p2y = cy + sep * 0.3 * math.sin(phase)

        # Draw pole markers
        for px, py, label in [(int(p1x), int(p1y), "N"), (int(p2x), int(p2y), "S")]:
            if 0 <= px < w - 1 and 0 <= py < h - 1:
                attr = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
                _safe(stdscr, py, px, label, attr)

        # Sparse field direction arrows
        for y in range(2, h - 2, 3):
            for x in range(4, w - 4, 6):
                # Compute field direction from two poles
                d1x = x - p1x
                d1y = (y - p1y) * 2  # aspect
                d2x = x - p2x
                d2y = (y - p2y) * 2
                r1 = max(1, math.hypot(d1x, d1y))
                r2 = max(1, math.hypot(d2x, d2y))
                # Dipole: N pushes, S pulls
                fx = (d1x / r1 ** 2) - (d2x / r2 ** 2)
                fy = (d1y / r1 ** 2) - (d2y / r2 ** 2)
                mag = math.hypot(fx, fy)
                if mag < 0.001:
                    continue
                # Direction arrow
                angle = math.atan2(fy, fx)
                arrows = "→↗↑↖←↙↓↘"
                ai = int((angle + math.pi) / (2 * math.pi) * 8) % 8
                v = min(1.0, mag * 40) * intensity
                if v > 0.3:
                    ch = arrows[ai]
                    attr = soft_attr if v > 0.6 else dim_attr
                    _safe(stdscr, y, x, ch, attr)

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds: float) -> None:
        if idle_seconds > 2.0 and state.frame % 20 == 0:
            w, h = state.width, state.height
            x = random.randint(4, max(5, w - 5))
            y = random.randint(2, max(3, h - 3))
            attr = curses.color_pair(color_pairs.get("soft", 0)) | curses.A_DIM
            _safe(stdscr, y, x, "·", attr)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register(DnaHelixPlugin())
register(PendulumWavesPlugin())
register(KaleidoscopePlugin())
register(GhostEchoPlugin())
register(MagneticFieldPlugin())
