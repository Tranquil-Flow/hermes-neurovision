"""Emergent Showcase — 5 themes demonstrating v0.2.0 engine features.

Themes:
  mycelium-network  — Physarum slime mold with persistent trails
  swarm-mind        — Boids flocking with vortex attractors
  neural-cascade    — Excitable neural field with cascading fire
  tide-pool         — Wave interference with kaleidoscope symmetry
  turing-garden     — Reaction-diffusion + cyclic automaton dual emergent
"""
from __future__ import annotations

import curses
import math
import random
from typing import Dict, List, Optional, Tuple

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

def _safe_addstr(stdscr, y: int, x: int, text: str, attr: int = 0) -> None:
    """Write to curses screen, silently ignoring out-of-bounds."""
    try:
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        pass


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


# ═══════════════════════════════════════════════════════════════════════════
# THEME 1: mycelium-network — Physarum Slime Mold Network
# ═══════════════════════════════════════════════════════════════════════════

class MyceliumNetworkTheme(ThemePlugin):
    """Organic slime mold network that grows toward agent activity."""

    def __init__(self) -> None:
        self.name = "mycelium-network"
        super().__init__()
        self._star_seeds: List[Tuple[float, float, str]] = []

    # -- palette --
    def palette(self) -> Dict[str, int]:
        return {
            "bright": curses.COLOR_WHITE,
            "accent": curses.COLOR_GREEN,
            "soft": curses.COLOR_CYAN,
            "base": curses.COLOR_YELLOW,
            "warning": curses.COLOR_RED,
        }

    # -- emergent --
    def physarum_config(self) -> Optional[Dict]:
        return {
            "n_agents": 200,
            "sensor_dist": 5,
            "sensor_angle": 0.6,
            "deposit": 1.0,
            "decay": 0.93,
        }

    def emergent_layer(self) -> str:
        return "background"

    # -- postfx --
    def glow_radius(self) -> int:
        return 2

    def echo_decay(self) -> int:
        return 4

    def decay_sequence(self) -> Optional[str]:
        return "█▓▒░·. "

    # -- layout: logarithmic spiral --
    def build_nodes(self, w: int, h: int, cx: int, cy: int,
                    count: int, rng: random.Random) -> Optional[List[Tuple]]:
        nodes: List[Tuple[int, int]] = []
        golden = 2.39996323  # golden angle in radians
        for i in range(count):
            r = 3.0 + 1.8 * math.sqrt(i + 1)
            theta = i * golden
            nx = int(cx + r * math.cos(theta) * 2)  # *2 for terminal aspect
            ny = int(cy + r * math.sin(theta))
            if 1 <= nx < w - 1 and 1 <= ny < h - 1:
                nodes.append((nx, ny))
        return nodes if nodes else None

    # -- glyphs --
    def node_glyph(self, idx: int, intensity: float, total: int) -> str:
        if intensity > 0.7:
            return "◉"
        elif intensity > 0.3:
            return "●"
        return "·"

    def node_color_key(self, idx: int, intensity: float, total: int) -> str:
        if intensity > 0.7:
            return "bright"
        elif intensity > 0.4:
            return "accent"
        return "soft"

    def pulse_style(self) -> str:
        return "cloud"

    # -- background: sparse drifting starfield --
    def draw_background(self, stdscr, state, color_pairs) -> None:
        w, h = state.width, state.height
        frame = state.frame
        if not self._star_seeds or len(self._star_seeds) < 30:
            rng = random.Random(42)
            self._star_seeds = [
                (rng.random(), rng.random(), rng.choice("·∙."))
                for _ in range(40)
            ]
        drift = frame * 0.02
        for fx, fy, ch in self._star_seeds:
            sx = int((fx * w + drift) % w)
            sy = int((fy * h + drift * 0.3) % h)
            attr = color_pairs.get("base", 0)
            _safe_addstr(stdscr, sy, sx, ch, attr)

    # -- reactive --
    def react(self, event_kind: str, data: dict) -> Optional[Reaction]:
        if event_kind == "tool_call":
            return Reaction(
                element=ReactiveElement.SPARK,
                intensity=0.8,
                origin=(random.random(), random.random()),
                color_key="accent",
                duration=1.5,
                data={"food": True},
            )
        if event_kind == "llm_start":
            return Reaction(
                element=ReactiveElement.STREAM,
                intensity=0.6,
                origin=(0.5, 0.5),
                color_key="soft",
                duration=3.0,
            )
        if event_kind == "error":
            return Reaction(
                element=ReactiveElement.SHATTER,
                intensity=1.0,
                origin=(random.random(), random.random()),
                color_key="warning",
                duration=2.0,
            )
        return None

    # -- ambient --
    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds: float) -> None:
        if idle_seconds > 2.0 and state.frame % 30 == 0:
            w, h = state.width, state.height
            fx = random.randint(2, max(3, w - 3))
            fy = random.randint(2, max(3, h - 3))
            ch = random.choice("·∙°")
            attr = color_pairs.get("accent", 0)
            _safe_addstr(stdscr, fy, fx, ch, attr)

    # -- particles --
    def particle_base_chance(self) -> float:
        return 0.15

    def spawn_particle(self, w: int, h: int, nodes, rng) -> Optional[Particle]:
        if nodes:
            nx, ny = rng.choice(nodes)
        else:
            nx, ny = rng.randint(1, max(2, w - 2)), rng.randint(1, max(2, h - 2))
        angle = rng.uniform(0, math.tau)
        speed = rng.uniform(0.1, 0.4)
        return Particle(
            x=float(nx), y=float(ny),
            vx=math.cos(angle) * speed * 2,
            vy=math.sin(angle) * speed,
            life=rng.randint(15, 40),
            max_life=40,
            char=rng.choice("·∙°"),
        )


# ═══════════════════════════════════════════════════════════════════════════
# THEME 2: swarm-mind — Boids Flocking Intelligence
# ═══════════════════════════════════════════════════════════════════════════

class SwarmMindTheme(ThemePlugin):
    """A living swarm of boids that reacts to agent events."""

    def __init__(self) -> None:
        self.name = "swarm-mind"
        super().__init__()

    def palette(self) -> Dict[str, int]:
        return {
            "bright": curses.COLOR_WHITE,
            "accent": curses.COLOR_MAGENTA,
            "soft": curses.COLOR_CYAN,
            "base": curses.COLOR_BLUE,
            "warning": curses.COLOR_RED,
        }

    # -- emergent --
    def boids_config(self) -> Optional[Dict]:
        return {
            "n_boids": 60,
            "sep_dist": 3.0,
            "align_dist": 8.0,
            "cohesion_dist": 12.0,
            "max_speed": 2.0,
        }

    def emergent_layer(self) -> str:
        return "midground"

    # -- postfx --
    def force_points(self, w: int, h: int, frame: int,
                     intensity: float) -> List[Dict]:
        cx, cy = w / 2, h / 2
        r = min(w, h) * 0.3
        t = frame * 0.03
        strength = 0.4 + intensity * 0.6
        return [
            {
                "x": int(cx + r * math.cos(t)),
                "y": int(cy + r * math.sin(t) * 0.5),
                "strength": strength,
                "type": "vortex",
            },
            {
                "x": int(cx + r * math.cos(t + math.pi)),
                "y": int(cy + r * math.sin(t + math.pi) * 0.5),
                "strength": strength * 0.8,
                "type": "vortex",
            },
        ]

    def symmetry(self) -> Optional[str]:
        return "mirror_x"

    def glow_radius(self) -> int:
        return 1

    # -- layout: ring --
    def build_nodes(self, w: int, h: int, cx: int, cy: int,
                    count: int, rng: random.Random) -> Optional[List[Tuple]]:
        nodes: List[Tuple[int, int]] = []
        r = min(w // 2 - 4, h // 2 - 2, 20)
        for i in range(count):
            theta = (i / count) * math.tau
            nx = int(cx + r * math.cos(theta) * 2)
            ny = int(cy + r * math.sin(theta))
            if 1 <= nx < w - 1 and 1 <= ny < h - 1:
                nodes.append((nx, ny))
        return nodes if nodes else None

    # -- glyphs --
    def node_glyph(self, idx: int, intensity: float, total: int) -> str:
        return "◆" if intensity > 0.5 else "◇"

    def node_color_key(self, idx: int, intensity: float, total: int) -> str:
        return "accent" if intensity > 0.5 else "soft"

    def edge_glyph(self, dx: int, dy: int) -> Optional[str]:
        if abs(dx) > abs(dy):
            return "─"
        return "│"

    def pulse_style(self) -> str:
        return "ring"

    # -- reactive --
    def react(self, event_kind: str, data: dict) -> Optional[Reaction]:
        if event_kind == "agent_start":
            return Reaction(
                element=ReactiveElement.PULSE,
                intensity=0.9,
                origin=(0.5, 0.5),
                color_key="accent",
                duration=2.0,
            )
        if event_kind == "tool_call":
            ox = data.get("x", random.random())
            oy = data.get("y", random.random())
            return Reaction(
                element=ReactiveElement.TRAIL,
                intensity=0.7,
                origin=(ox, oy),
                color_key="soft",
                duration=2.0,
                data={"attractor": True},
            )
        if event_kind == "subagent_spawn":
            return Reaction(
                element=ReactiveElement.BLOOM,
                intensity=1.0,
                origin=(random.random(), random.random()),
                color_key="bright",
                duration=2.5,
            )
        return None

    # -- special effects --
    def special_effects(self) -> List[SpecialEffect]:
        return [
            SpecialEffect(
                name="swarm-surge",
                trigger_kinds=["burst"],
                min_intensity=0.7,
                cooldown=5.0,
                duration=3.0,
            ),
        ]

    def draw_special(self, stdscr, state, color_pairs, special_name: str,
                     progress: float, intensity: float) -> None:
        if special_name != "swarm-surge":
            return
        w, h = state.width, state.height
        cx, cy = w // 2, h // 2
        max_r = min(w // 2, h) - 2
        r = int(max_r * progress)
        attr = color_pairs.get("accent", 0)
        # expanding ring of symbols
        for angle_step in range(0, 360, 5):
            theta = math.radians(angle_step)
            px = int(cx + r * math.cos(theta) * 2)
            py = int(cy + r * math.sin(theta))
            if 0 <= px < w and 0 <= py < h:
                ch = random.choice("◆◇·")
                _safe_addstr(stdscr, py, px, ch, attr)

    # -- draw_extras: pulsing circle border --
    def draw_extras(self, stdscr, state, color_pairs) -> None:
        w, h = state.width, state.height
        cx, cy = w // 2, h // 2
        intensity = getattr(state, "intensity_multiplier", 0.5)
        pulse = 0.8 + 0.2 * math.sin(state.frame * 0.1)
        r = int((min(w // 2 - 2, h // 2 - 1)) * pulse)
        attr = color_pairs.get("base", 0)
        steps = max(60, int(r * 4))
        for i in range(steps):
            theta = (i / steps) * math.tau
            px = int(cx + r * math.cos(theta) * 2)
            py = int(cy + r * math.sin(theta))
            if 0 <= px < w and 0 <= py < h:
                bright = (i + state.frame) % 12 < 6
                ch = "·" if bright else " "
                _safe_addstr(stdscr, py, px, ch, attr)

    def particle_base_chance(self) -> float:
        return 0.1


# ═══════════════════════════════════════════════════════════════════════════
# THEME 3: neural-cascade — Neural Field Excitable Medium
# ═══════════════════════════════════════════════════════════════════════════

class NeuralCascadeTheme(ThemePlugin):
    """Brain-like excitable neural field that cascades with activity."""

    def __init__(self) -> None:
        self.name = "neural-cascade"
        super().__init__()

    def palette(self) -> Dict[str, int]:
        return {
            "bright": curses.COLOR_WHITE,
            "accent": curses.COLOR_CYAN,
            "soft": curses.COLOR_BLUE,
            "base": curses.COLOR_MAGENTA,
            "warning": curses.COLOR_RED,
        }

    # -- emergent --
    def neural_field_config(self) -> Optional[Dict]:
        return {
            "threshold": 2,
            "fire_duration": 3,
            "refractory": 4,
        }

    def emergent_layer(self) -> str:
        return "background"

    # -- postfx --
    def warp_field(self, x: int, y: int, w: int, h: int,
                   frame: int, intensity: float) -> Tuple[int, int]:
        amp = intensity * 1.5
        t = frame * 0.08
        dx = int(amp * math.sin(t + y * 0.3))
        dy = int(amp * 0.5 * math.cos(t + x * 0.2))
        nx = max(0, min(w - 1, x + dx))
        ny = max(0, min(h - 1, y + dy))
        return (nx, ny)

    def glow_radius(self) -> int:
        return 1

    def echo_decay(self) -> int:
        return 3

    # -- layout: grid --
    def build_nodes(self, w: int, h: int, cx: int, cy: int,
                    count: int, rng: random.Random) -> Optional[List[Tuple]]:
        cols = max(2, int(math.sqrt(count * 2)))
        rows = max(2, count // cols)
        spacing_x = max(4, (w - 8) // max(1, cols - 1))
        spacing_y = max(3, (h - 4) // max(1, rows - 1))
        x0 = cx - (cols - 1) * spacing_x // 2
        y0 = cy - (rows - 1) * spacing_y // 2
        nodes: List[Tuple[int, int]] = []
        for r in range(rows):
            for c in range(cols):
                nx = x0 + c * spacing_x
                ny = y0 + r * spacing_y
                if 1 <= nx < w - 1 and 1 <= ny < h - 1:
                    nodes.append((nx, ny))
                if len(nodes) >= count:
                    break
            if len(nodes) >= count:
                break
        return nodes if nodes else None

    # -- glyphs --
    def node_glyph(self, idx: int, intensity: float, total: int) -> str:
        if intensity > 0.7:
            return "⬡"  # firing
        elif intensity > 0.3:
            return "⬢"  # refractory
        return "·"  # resting

    def node_color_key(self, idx: int, intensity: float, total: int) -> str:
        if intensity > 0.7:
            return "bright"
        elif intensity > 0.3:
            return "accent"
        return "soft"

    def pulse_style(self) -> str:
        return "ripple"

    # -- reactive --
    def react(self, event_kind: str, data: dict) -> Optional[Reaction]:
        if event_kind == "llm_token":
            return Reaction(
                element=ReactiveElement.SPARK,
                intensity=0.5,
                origin=(random.random(), random.random()),
                color_key="accent",
                duration=0.8,
                data={"fire": True},
            )
        if event_kind == "tool_result":
            return Reaction(
                element=ReactiveElement.RIPPLE,
                intensity=0.8,
                origin=(random.random(), random.random()),
                color_key="bright",
                duration=2.0,
            )
        if event_kind == "error":
            return Reaction(
                element=ReactiveElement.SHATTER,
                intensity=1.0,
                origin=(0.5, 0.5),
                color_key="warning",
                duration=2.5,
                sound="bell",
            )
        return None

    def palette_shift(self, trigger_effect, intensity: float,
                      base_palette) -> Optional[Tuple]:
        if trigger_effect == "error" or trigger_effect == ReactiveElement.SHATTER:
            # shift toward red/warning tones
            return (
                curses.COLOR_RED,
                curses.COLOR_YELLOW,
                curses.COLOR_WHITE,
                curses.COLOR_RED,
            )
        return None

    # -- intensity curve: sigmoid --
    def intensity_curve(self, raw: float) -> float:
        # sigmoid: low activity barely visible, high activity explodes
        x = (raw - 0.5) * 10.0
        return 1.0 / (1.0 + math.exp(-x))

    # -- sound --
    def sound_cues(self) -> Dict[str, SoundCue]:
        return {
            "error": SoundCue(
                name="cascade-error",
                type="bell",
                value="",
                volume=0.8,
                priority=10,
            ),
        }

    def particle_base_chance(self) -> float:
        return 0.08

    def spawn_particle(self, w: int, h: int, nodes, rng) -> Optional[Particle]:
        x = rng.randint(2, max(3, w - 3))
        y = rng.randint(2, max(3, h - 3))
        return Particle(
            x=float(x), y=float(y),
            vx=rng.uniform(-0.3, 0.3),
            vy=rng.uniform(-0.2, 0.2),
            life=rng.randint(5, 15),
            max_life=15,
            char=rng.choice("·∙⁘"),
        )


# ═══════════════════════════════════════════════════════════════════════════
# THEME 4: tide-pool — Wave Field Interference
# ═══════════════════════════════════════════════════════════════════════════

class TidePoolTheme(ThemePlugin):
    """Rippling water surface with interference patterns."""

    def __init__(self) -> None:
        self.name = "tide-pool"
        super().__init__()

    def palette(self) -> Dict[str, int]:
        return {
            "bright": curses.COLOR_WHITE,
            "accent": curses.COLOR_CYAN,
            "soft": curses.COLOR_BLUE,
            "base": curses.COLOR_GREEN,
            "warning": curses.COLOR_RED,
        }

    # -- emergent --
    def wave_config(self) -> Optional[Dict]:
        return {
            "speed": 0.4,
            "damping": 0.96,
        }

    def emergent_layer(self) -> str:
        return "background"

    # -- postfx --
    def symmetry(self) -> Optional[str]:
        return "mirror_xy"

    def glow_radius(self) -> int:
        return 1

    def decay_sequence(self) -> Optional[str]:
        return "▓▒░·. "

    def render_mask(self, w: int, h: int, frame: int,
                    intensity: float) -> Optional[List[List[bool]]]:
        """Circular stencil mask — only render inside a large circle."""
        cx, cy = w / 2, h / 2
        r = min(cx - 2, (cy - 1) * 2) * 0.9  # adjusted for aspect
        mask: List[List[bool]] = []
        for row in range(h):
            line: List[bool] = []
            for col in range(w):
                dx = (col - cx) / 2.0  # aspect correction
                dy = row - cy
                line.append((dx * dx + dy * dy) <= (r / 2) ** 2)
            mask.append(line)
        return mask

    # -- layout: no nodes, pure field --
    def build_nodes(self, w: int, h: int, cx: int, cy: int,
                    count: int, rng: random.Random) -> Optional[List[Tuple]]:
        return []

    def pulse_style(self) -> str:
        return "ripple"

    # -- reactive: every event drops a wave --
    def react(self, event_kind: str, data: dict) -> Optional[Reaction]:
        event_map = {
            "tool_call": (ReactiveElement.RIPPLE, 0.9, "accent", 2.0),
            "tool_result": (ReactiveElement.RIPPLE, 0.6, "soft", 1.5),
            "llm_start": (ReactiveElement.WAVE, 1.0, "bright", 3.0),
            "llm_token": (ReactiveElement.SPARK, 0.3, "accent", 0.5),
            "llm_end": (ReactiveElement.RIPPLE, 0.5, "base", 1.5),
            "agent_start": (ReactiveElement.WAVE, 0.8, "bright", 2.5),
            "agent_end": (ReactiveElement.RIPPLE, 0.4, "soft", 1.0),
            "error": (ReactiveElement.SHATTER, 1.0, "warning", 2.0),
            "subagent_spawn": (ReactiveElement.BLOOM, 0.8, "accent", 2.0),
            "memory_save": (ReactiveElement.RIPPLE, 0.5, "base", 1.5),
        }
        cfg = event_map.get(event_kind)
        if cfg is None:
            return None
        elem, inten, color, dur = cfg
        return Reaction(
            element=elem,
            intensity=inten,
            origin=(random.random(), random.random()),
            color_key=color,
            duration=dur,
        )

    # -- draw_extras: wave field char gradient --
    def draw_extras(self, stdscr, state, color_pairs) -> None:
        w, h = state.width, state.height
        frame = state.frame
        cx, cy = w / 2, h / 2
        gradient = " .·░▒▓"
        levels = len(gradient) - 1
        intensity = getattr(state, "intensity_multiplier", 0.3)
        max_r = min(w // 2, h // 2)

        for row in range(1, h - 1, 2):
            for col in range(2, w - 2, 3):
                dx = (col - cx) / 2.0
                dy = row - cy
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > max_r:
                    continue
                # interference of multiple waves
                v = 0.0
                v += math.sin(dist * 0.5 - frame * 0.15) * 0.4
                v += math.sin(dist * 0.3 + frame * 0.08 + col * 0.1) * 0.3
                v += math.sin(row * 0.2 + frame * 0.06) * 0.2 * intensity
                v = (v + 1.0) / 2.0  # normalize 0-1
                idx = int(v * levels)
                idx = max(0, min(levels, idx))
                ch = gradient[idx]
                if ch == " ":
                    continue
                color_key = "accent" if v > 0.6 else ("soft" if v > 0.3 else "base")
                attr = color_pairs.get(color_key, 0)
                _safe_addstr(stdscr, row, col, ch, attr)

    # -- ambient --
    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds: float) -> None:
        if idle_seconds > 1.5 and state.frame % 20 == 0:
            w, h = state.width, state.height
            x = random.randint(4, max(5, w - 5))
            y = random.randint(2, max(3, h - 3))
            attr = color_pairs.get("soft", 0)
            _safe_addstr(stdscr, y, x, "·", attr)

    # -- sound --
    def sound_cues(self) -> Dict[str, SoundCue]:
        return {
            "tool_call": SoundCue(
                name="tide-drop",
                type="flash",
                value="",
                volume=0.4,
                priority=5,
            ),
        }

    def particle_base_chance(self) -> float:
        return 0.05


# ═══════════════════════════════════════════════════════════════════════════
# THEME 5: turing-garden — Reaction-Diffusion Turing Patterns
# ═══════════════════════════════════════════════════════════════════════════

class TuringGardenTheme(ThemePlugin):
    """Living Turing patterns that bloom with agent activity — dual emergent."""

    def __init__(self) -> None:
        self.name = "turing-garden"
        super().__init__()

    def palette(self) -> Dict[str, int]:
        return {
            "bright": curses.COLOR_WHITE,
            "accent": curses.COLOR_MAGENTA,
            "soft": curses.COLOR_CYAN,
            "base": curses.COLOR_GREEN,
            "warning": curses.COLOR_RED,
        }

    # -- dual emergent --
    def reaction_diffusion_config(self) -> Optional[Dict]:
        return {
            "feed": 0.055,
            "kill": 0.062,
            "update_interval": 1,
        }

    def automaton_config(self) -> Optional[Dict]:
        return {
            "rule": "cyclic",
            "density": 0.4,
            "update_interval": 3,
        }

    def emergent_layer(self) -> str:
        return "foreground"

    # -- postfx --
    def glow_radius(self) -> int:
        return 2

    def echo_decay(self) -> int:
        return 5

    def force_points(self, w: int, h: int, frame: int,
                     intensity: float) -> List[Dict]:
        cx, cy = w // 2, h // 2
        strength = 0.3 + intensity * 0.7
        return [
            {
                "x": cx,
                "y": cy,
                "strength": strength,
                "type": "radial",
            },
        ]

    # -- layout: tiny 4-node cluster in center --
    def build_nodes(self, w: int, h: int, cx: int, cy: int,
                    count: int, rng: random.Random) -> Optional[List[Tuple]]:
        offsets = [(-3, -1), (3, -1), (-3, 1), (3, 1)]
        nodes: List[Tuple[int, int]] = []
        for dx, dy in offsets:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h:
                nodes.append((nx, ny))
        return nodes

    # -- glyphs --
    def node_glyph(self, idx: int, intensity: float, total: int) -> str:
        return "✦" if intensity > 0.5 else "✧"

    def node_color_key(self, idx: int, intensity: float, total: int) -> str:
        return "accent" if intensity > 0.5 else "soft"

    def pulse_style(self) -> str:
        return "diamond"

    # -- reactive --
    def react(self, event_kind: str, data: dict) -> Optional[Reaction]:
        if event_kind == "tool_call":
            return Reaction(
                element=ReactiveElement.SPARK,
                intensity=0.8,
                origin=(random.random(), random.random()),
                color_key="accent",
                duration=2.0,
                data={"chemical": True},
            )
        if event_kind == "memory_save":
            return Reaction(
                element=ReactiveElement.BLOOM,
                intensity=1.0,
                origin=(0.5, 0.5),
                color_key="soft",
                duration=3.0,
            )
        if event_kind == "agent_start":
            return Reaction(
                element=ReactiveElement.CONSTELLATION,
                intensity=0.9,
                origin=(0.5, 0.5),
                color_key="bright",
                duration=4.0,
            )
        return None

    # -- special effects --
    def special_effects(self) -> List[SpecialEffect]:
        return [
            SpecialEffect(
                name="bloom-burst",
                trigger_kinds=["burst"],
                min_intensity=0.5,
                cooldown=4.0,
                duration=3.0,
            ),
        ]

    def draw_special(self, stdscr, state, color_pairs, special_name: str,
                     progress: float, intensity: float) -> None:
        if special_name != "bloom-burst":
            return
        w, h = state.width, state.height
        cx, cy = w // 2, h // 2
        attr = color_pairs.get("accent", 0)
        # ring of chemical deposits expanding outward
        n_points = 12
        r = int(min(w // 2, h // 2) * progress * 0.8)
        for i in range(n_points):
            theta = (i / n_points) * math.tau + progress * 0.5
            px = int(cx + r * math.cos(theta) * 2)
            py = int(cy + r * math.sin(theta))
            if 0 <= px < w and 0 <= py < h:
                ch = "✦" if (i + int(progress * 10)) % 3 == 0 else "·"
                _safe_addstr(stdscr, py, px, ch, attr)

    # -- draw_background: render automaton as subtle layer --
    def draw_background(self, stdscr, state, color_pairs) -> None:
        w, h = state.width, state.height
        frame = state.frame
        intensity = getattr(state, "intensity_multiplier", 0.3)
        attr_dim = color_pairs.get("base", 0)
        attr_mid = color_pairs.get("soft", 0)
        # procedural cyclic pattern as background texture
        bg_chars = " ·.·"
        for row in range(1, h - 1, 3):
            for col in range(2, w - 2, 4):
                v = math.sin(col * 0.15 + frame * 0.04) + \
                    math.cos(row * 0.2 + frame * 0.03)
                v += intensity * math.sin((col + row) * 0.1 + frame * 0.06)
                v = (v + 2.0) / 4.0  # normalize
                idx = int(v * (len(bg_chars) - 1))
                idx = max(0, min(len(bg_chars) - 1, idx))
                ch = bg_chars[idx]
                if ch == " ":
                    continue
                attr = attr_mid if v > 0.5 else attr_dim
                _safe_addstr(stdscr, row, col, ch, attr)

    def particle_base_chance(self) -> float:
        return 0.12

    def spawn_particle(self, w: int, h: int, nodes, rng) -> Optional[Particle]:
        cx, cy = w / 2, h / 2
        angle = rng.uniform(0, math.tau)
        dist = rng.uniform(2, min(w, h) * 0.3)
        x = cx + math.cos(angle) * dist * 2
        y = cy + math.sin(angle) * dist
        return Particle(
            x=x, y=y,
            vx=math.cos(angle) * 0.3,
            vy=math.sin(angle) * 0.15,
            life=rng.randint(20, 50),
            max_life=50,
            char=rng.choice("✧·∙"),
        )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register(MyceliumNetworkTheme())
register(SwarmMindTheme())
register(NeuralCascadeTheme())
register(TidePoolTheme())
register(TuringGardenTheme())
