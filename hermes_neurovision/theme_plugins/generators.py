"""Generator screens — 8 mathematically-driven full-screen visualizations.

Themes:
  lorenz-attractor  — 3D Lorenz strange attractor projected to terminal
  fourier-epicycles — Chain of rotating arms tracing Fourier curves
  sand-cascade      — Falling sand pixel physics simulation
  rorschach         — Symmetric evolving inkblot noise field
  dla-crystal       — Diffusion-limited aggregation crystal growth
  spirograph        — Hypotrochoid parametric curves with fading trails
  harmonograph      — Compound damped pendulum drawing machine
  julia-morph       — Julia set with continuously orbiting c parameter
"""
from __future__ import annotations

import curses
import math
import random
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


def _safe(stdscr, y: int, x: int, ch: str, attr: int = 0) -> None:
    try:
        stdscr.addstr(y, x, ch, attr)
    except curses.error:
        pass


# ── 1. Lorenz Attractor ───────────────────────────────────────────────────────

class LorenzAttractorPlugin(ThemePlugin):
    """3D Lorenz strange attractor projected onto the terminal plane.

    The classic σ=10, ρ=28, β=8/3 butterfly orbit accumulated into a density
    grid with slow decay. Projection rotates slowly so you see all three wings.
    Intensity multiplier controls iteration count and decay rate.
    """
    name = "lorenz-attractor"

    def __init__(self):
        super().__init__()
        self._grid: Optional[List[List[float]]] = None
        self._x, self._y, self._z = 0.1, 0.0, 0.0
        self._w = self._h = 0
        self._angle = 0.0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init(self, w, h):
        self._grid = [[0.0] * w for _ in range(h)]
        self._x, self._y, self._z = 0.1, 0.0, 0.0
        self._w, self._h = w, h

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        if self._grid is None or (w, h) != (self._w, self._h):
            self._init(w, h)

        intensity = state.intensity_multiplier
        grid = self._grid
        cx, cy = w / 2.0, h / 2.0

        # Lorenz parameters
        sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
        dt = 0.008
        self._angle += 0.004

        steps = int(600 * (0.5 + intensity))
        x, y, z = self._x, self._y, self._z
        cos_a, sin_a = math.cos(self._angle), math.sin(self._angle)
        # Tilt angle for y-z mix
        tilt = 0.4
        cos_t, sin_t = math.cos(tilt), math.sin(tilt)

        for _ in range(steps):
            dx = sigma * (y - x)
            dy = x * (rho - z) - y
            dz = x * y - beta * z
            x += dx * dt
            y += dy * dt
            z += dz * dt
            # Project: rotate around Z axis, then tilt
            px = x * cos_a - y * sin_a
            py_raw = x * sin_a + y * cos_a
            pz = py_raw * sin_t + (z - 25) * cos_t
            # Map to screen: attractor spans roughly ±25 in x/y, 0-50 in z
            sx = int(cx + px * (w / 60.0))
            sy = int(cy + pz * (h / 36.0))
            if 1 <= sy < h - 1 and 0 <= sx < w - 1:
                grid[sy][sx] = min(grid[sy][sx] + 0.07, 1.0)

        self._x, self._y, self._z = x, y, z

        # Decay and render
        decay = 0.972 - 0.008 * intensity
        chars = " ·.:;+=*#▓█"
        nc = len(chars) - 1
        bright = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent = curses.color_pair(color_pairs["accent"])
        soft   = curses.color_pair(color_pairs["soft"])
        dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        for gy in range(1, h - 1):
            row = grid[gy]
            for gx in range(w - 1):
                v = row[gx] * decay
                row[gx] = v
                ci = max(0, min(nc, int(v * nc)))
                ch = chars[ci]
                attr = bright if v > 0.75 else (accent if v > 0.45 else (soft if v > 0.18 else dim))
                _safe(stdscr, gy, gx, ch, attr)


    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "cron_tick" or event_kind == "background_proc":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.6,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        if event_kind == "llm_start" or event_kind == "llm_end":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.7,
                           origin=(0.0, 0.5), color_key="bright", duration=2.5)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.8,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        if event_kind == "tool_call" or event_kind == "mcp_tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.6,
                           origin=(random.random(), random.random()), color_key="soft", duration=1.5)
        return None

    def wave_config(self):
        return {'speed': 0.5, 'damping': 0.96}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


# ── 2. Fourier Epicycles ─────────────────────────────────────────────────────
    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "cron_tick" or event_kind == "background_proc":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.6,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        if event_kind == "llm_start" or event_kind == "llm_end":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.7,
                           origin=(0.0, 0.5), color_key="bright", duration=2.5)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.8,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        if event_kind == "tool_call" or event_kind == "mcp_tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.6,
                           origin=(random.random(), random.random()), color_key="soft", duration=1.5)
        return None

    def wave_config(self):
        return {'speed': 0.5, 'damping': 0.96}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


class FourierEpicyclesPlugin(ThemePlugin):
    """Chain of rotating arms (epicycles) tracing a Fourier curve.

    Uses 8 harmonics with randomised amplitudes that slowly morph, so the
    drawn shape continuously evolves. The tip trail fades over ~400 points.
    Arm lengths shown as faint circles; tip shown bright.
    """
    name = "fourier-epicycles"

    def __init__(self):
        super().__init__()
        self._trail: List[Tuple[int, int]] = []
        self._phase = 0.0
        self._amps: Optional[List[float]] = None
        self._freqs: Optional[List[float]] = None
        self._phases: Optional[List[float]] = None
        self._morph_t = 0.0
        self._next_amps: Optional[List[float]] = None

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init_harmonics(self, rng):
        n = 8
        self._freqs  = [float(k + 1) for k in range(n)]
        self._amps   = [rng.uniform(0.4, 1.0) / (k + 1) for k in range(n)]
        self._phases = [rng.uniform(0, math.tau) for _ in range(n)]
        # Normalise so total arm span ≈ 1
        total = sum(self._amps)
        self._amps = [a / total for a in self._amps]
        self._next_amps = list(self._amps)

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        intensity = state.intensity_multiplier
        rng = state.rng

        if self._amps is None:
            self._init_harmonics(rng)

        cx, cy = w / 2.0, h / 2.0
        max_r = min(cx - 4, (cy - 2) * 1.8) * 0.85

        # Slowly morph amplitudes
        self._morph_t += 0.003 + 0.002 * intensity
        if self._morph_t >= 1.0:
            self._morph_t = 0.0
            self._amps = list(self._next_amps)
            new_raw = [rng.uniform(0.3, 1.0) / (k + 1) for k in range(8)]
            total = sum(new_raw)
            self._next_amps = [a / total for a in new_raw]
        mt = self._morph_t
        amps = [self._amps[i] + (self._next_amps[i] - self._amps[i]) * mt
                for i in range(8)]

        # Advance phase
        self._phase += 0.025 + 0.015 * intensity

        # Compute tip position from epicycle sum
        arm_x, arm_y = cx, cy
        for i in range(8):
            r = amps[i] * max_r
            a = self._freqs[i] * self._phase + self._phases[i]
            arm_x += math.cos(a) * r * 0.55  # aspect correction
            arm_y += math.sin(a) * r * 0.5

        tx, ty = int(arm_x), int(arm_y)
        if 1 <= ty < h - 1 and 0 <= tx < w - 1:
            self._trail.append((tx, ty))
        max_trail = int(300 + 200 * intensity)
        if len(self._trail) > max_trail:
            self._trail = self._trail[-max_trail:]

        # Clear background
        dim = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        for gy in range(1, h - 1):
            for gx in range(0, w - 1):
                _safe(stdscr, gy, gx, " ", dim)

        # Draw faint epicycle circles
        soft = curses.color_pair(color_pairs["soft"]) | curses.A_DIM
        arm_x2, arm_y2 = cx, cy
        for i in range(8):
            r = amps[i] * max_r
            a = self._freqs[i] * self._phase + self._phases[i]
            # Circle outline (sparse)
            steps = max(12, int(r * 3))
            for s in range(0, steps, 2):
                ang = math.tau * s / steps
                px = int(arm_x2 + math.cos(ang) * r * 0.55)
                py = int(arm_y2 + math.sin(ang) * r * 0.5)
                if 1 <= py < h - 1 and 0 <= px < w - 1:
                    _safe(stdscr, py, px, "·", soft)
            arm_x2 += math.cos(a) * r * 0.55
            arm_y2 += math.sin(a) * r * 0.5

        # Draw trail with age-based brightness
        trail_len = len(self._trail)
        bright = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent = curses.color_pair(color_pairs["accent"])
        soft2  = curses.color_pair(color_pairs["soft"])
        for i, (px, py) in enumerate(self._trail):
            age = i / max(trail_len, 1)
            if age < 0.2:
                ch, attr = "·", dim
            elif age < 0.5:
                ch, attr = ":", soft2
            elif age < 0.8:
                ch, attr = "+", accent
            else:
                ch, attr = "◈", bright
            _safe(stdscr, py, px, ch, attr)

        # Bright current tip
        if self._trail:
            _safe(stdscr, self._trail[-1][1], self._trail[-1][0], "◉", bright)


    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "memory_save" or event_kind == "checkpoint_created":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.9,
                           origin=(0.5, 0.5), color_key="bright", duration=2.5)
        if event_kind == "agent_start" or event_kind == "session_resume":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "git_commit" or event_kind == "file_edit":
            return Reaction(element=ReactiveElement.TRAIL, intensity=0.6,
                           origin=(0.5, 0.5), color_key="accent", duration=1.5)
        if event_kind == "tool_call" or event_kind == "mcp_tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.5,
                           origin=(0.5, 0.5), color_key="soft", duration=1.5)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.4,
                           origin=(0.0, 0.5), color_key="soft", duration=0.8)
        return None

    def wave_config(self):
        return {'speed': 0.3, 'damping': 0.97}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


# ── 3. Sand Cascade ──────────────────────────────────────────────────────────
    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "memory_save" or event_kind == "checkpoint_created":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.9,
                           origin=(0.5, 0.5), color_key="bright", duration=2.5)
        if event_kind == "agent_start" or event_kind == "session_resume":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "git_commit" or event_kind == "file_edit":
            return Reaction(element=ReactiveElement.TRAIL, intensity=0.6,
                           origin=(0.5, 0.5), color_key="accent", duration=1.5)
        if event_kind == "tool_call" or event_kind == "mcp_tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.5,
                           origin=(0.5, 0.5), color_key="soft", duration=1.5)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.4,
                           origin=(0.0, 0.5), color_key="soft", duration=0.8)
        return None

    def wave_config(self):
        return {'speed': 0.3, 'damping': 0.97}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


class SandCascadePlugin(ThemePlugin):
    """Falling sand / pixel physics simulation.

    Sand grains fall under gravity, pile up, and slide off slopes. New sand
    spawns at the top at random columns. Intensity drives spawn rate and
    periodically clears columns to restart the cascade.
    """
    name = "sand-cascade"

    # Cell states: 0=empty, 1=sand, 2=rock (boundary), 3=water
    _EMPTY = 0
    _SAND  = 1
    _ROCK  = 2

    def __init__(self):
        super().__init__()
        self._grid: Optional[bytearray] = None
        self._w = self._h = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init(self, w, h, rng):
        self._w, self._h = w, h
        self._grid = bytearray(w * h)
        # Place a few rock platforms
        for _ in range(4):
            rx = rng.randint(w // 5, w * 4 // 5)
            ry = rng.randint(h // 4, h * 3 // 4)
            rlen = rng.randint(w // 6, w // 3)
            for dx in range(rlen):
                gx = rx + dx
                if 0 <= gx < w:
                    self._grid[ry * w + gx] = self._ROCK

    def _step(self, w, h):
        g = self._grid
        # Bottom to top, left to right (shuffled direction each call)
        for gy in range(h - 2, 0, -1):
            for gx in range(w - 1):
                if g[gy * w + gx] != self._SAND:
                    continue
                below = gy + 1
                # Fall straight down
                if below < h and g[below * w + gx] == self._EMPTY:
                    g[below * w + gx] = self._SAND
                    g[gy * w + gx] = self._EMPTY
                    continue
                # Slide diagonally
                dl = gx - 1
                dr = gx + 1
                can_l = dl >= 0 and g[below * w + dl] == self._EMPTY if below < h else False
                can_r = dr < w and g[below * w + dr] == self._EMPTY if below < h else False
                if can_l and can_r:
                    target = dl if (gx + gy) % 2 == 0 else dr
                    g[below * w + target] = self._SAND
                    g[gy * w + gx] = self._EMPTY
                elif can_l:
                    g[below * w + dl] = self._SAND
                    g[gy * w + gx] = self._EMPTY
                elif can_r:
                    g[below * w + dr] = self._SAND
                    g[gy * w + gx] = self._EMPTY

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        rng = state.rng
        intensity = state.intensity_multiplier

        if self._grid is None or w != self._w or h != self._h:
            self._init(w, h, rng)

        # Spawn sand at top
        n_spawn = int(1 + 3 * intensity)
        for _ in range(n_spawn):
            sx = rng.randint(1, w - 2)
            if self._grid[1 * w + sx] == self._EMPTY:
                self._grid[1 * w + sx] = self._SAND

        # Periodically clear a column to make room
        if f % 150 == 0:
            cx2 = rng.randint(0, w - 1)
            for gy in range(h):
                if self._grid[gy * w + cx2] == self._SAND:
                    self._grid[gy * w + cx2] = self._EMPTY

        # Step simulation
        self._step(w, h)

        # Render
        g = self._grid
        bright = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent = curses.color_pair(color_pairs["accent"])
        soft   = curses.color_pair(color_pairs["soft"])
        rock_a = curses.color_pair(color_pairs["base"])
        empty_a = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        for gy in range(1, h - 1):
            for gx in range(w - 1):
                cell = g[gy * w + gx]
                if cell == self._SAND:
                    # Depth shading: surface grains bright, buried grains soft
                    above = g[(gy - 1) * w + gx] if gy > 0 else self._EMPTY
                    if above == self._EMPTY:
                        ch, attr = "░", accent
                    else:
                        ch, attr = "▓", soft
                    _safe(stdscr, gy, gx, ch, attr)
                elif cell == self._ROCK:
                    _safe(stdscr, gy, gx, "█", rock_a)
                else:
                    _safe(stdscr, gy, gx, " ", empty_a)


    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "tool_call" or event_kind == "mcp_tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.7,
                           origin=(random.random(), 0.0), color_key="bright", duration=1.5)
        if event_kind == "error" or event_kind == "crash" or event_kind == "threat_blocked":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.4,
                           origin=(random.random(), 0.0), color_key="soft", duration=0.6)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.8,
                           origin=(0.5, 0.0), color_key="bright", duration=2.0)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.8,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        if event_kind == "compression_started":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.7,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        return None

    def automaton_config(self):
        return {'rule': 'brians_brain', 'density': 0.4, 'update_interval': 1}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


class RorschachPlugin(ThemePlugin):
    """Symmetrically mirrored noise field creating evolving inkblot patterns.

    Four overlapping sine/cosine waves with slowly drifting parameters fill
    the left half of the screen; the right half is mirrored. A vertical center
    crease is drawn for the fold effect. Density mapped to block chars.
    """
    name = "rorschach"

    def __init__(self):
        super().__init__()
        # Wave parameters: (freq_x, freq_y, speed, phase_offset)
        self._waves = [
            (0.12, 0.18, 0.04, 0.0),
            (0.07, 0.11, 0.03, 1.2),
            (0.19, 0.08, 0.05, 2.4),
            (0.05, 0.22, 0.02, 3.7),
        ]

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        intensity = state.intensity_multiplier
        cx, cy = w // 2, h // 2

        bright = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent = curses.color_pair(color_pairs["accent"])
        soft   = curses.color_pair(color_pairs["soft"])
        dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        chars  = " ·░▒▓█"

        for gy in range(1, h - 1):
            dy = gy - cy
            for gx in range(0, cx):
                dx = gx - cx  # always negative (left side)
                v = 0.0
                for fx, fy, spd, ph in self._waves:
                    v += math.sin(gx * fx + f * spd + ph) * math.cos(gy * fy - f * spd * 0.7 + ph * 1.3)
                # Radial falloff from center
                r = math.hypot(dx / (cx or 1), dy / (cy or 1))
                v = (v / len(self._waves) + 1.0) / 2.0
                v = v * max(0.0, 1.0 - r * 0.4) * intensity
                v = max(0.0, min(1.0, v))

                ci = int(v * (len(chars) - 1))
                ch = chars[ci]
                attr = bright if v > 0.78 else (accent if v > 0.55 else (soft if v > 0.30 else dim))

                # Left half
                _safe(stdscr, gy, gx, ch, attr)
                # Mirror to right half
                rx = w - 1 - gx
                if 0 <= rx < w - 1:
                    _safe(stdscr, gy, rx, ch, attr)

        # Center crease
        crease = curses.color_pair(color_pairs["soft"]) | curses.A_DIM
        for gy in range(1, h - 1):
            _safe(stdscr, gy, cx, "│", crease)


    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "reasoning_change" or event_kind == "personality_change":
            return Reaction(element=ReactiveElement.GLYPH, intensity=0.9,
                           origin=(0.5, 0.5), color_key="bright", duration=3.0)
        if event_kind == "memory_save" or event_kind == "skill_create":
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                           origin=(0.5, 0.5), color_key="bright", duration=2.5)
        if event_kind == "compression_started" or event_kind == "compression_ended":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="accent", duration=2.5)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.7,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.5,
                           origin=(0.5, 0.5), color_key="soft", duration=1.5)
        return None

    def physarum_config(self):
        return {'n_agents': 100, 'sensor_dist': 4.0, 'sensor_angle': 0.785, 'deposit': 0.9, 'decay': 0.94}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


# ── 5. DLA Crystal ──────────────────────────────────────────────────────────
    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "reasoning_change" or event_kind == "personality_change":
            return Reaction(element=ReactiveElement.GLYPH, intensity=0.9,
                           origin=(0.5, 0.5), color_key="bright", duration=3.0)
        if event_kind == "memory_save" or event_kind == "skill_create":
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                           origin=(0.5, 0.5), color_key="bright", duration=2.5)
        if event_kind == "compression_started" or event_kind == "compression_ended":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="accent", duration=2.5)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.7,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.5,
                           origin=(0.5, 0.5), color_key="soft", duration=1.5)
        return None

    def physarum_config(self):
        return {'n_agents': 100, 'sensor_dist': 4.0, 'sensor_angle': 0.785, 'deposit': 0.9, 'decay': 0.94}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


class DlaCrystalPlugin(ThemePlugin):
    """Diffusion-Limited Aggregation: random walkers stick to a growing crystal.

    Seeded at center. New walkers spawn at the screen edge and walk randomly
    until they touch the crystal, then freeze. Periodically resets when the
    crystal fills. Crystal cells rendered with density-based characters.
    """
    name = "dla-crystal"

    def __init__(self):
        super().__init__()
        self._crystal: Optional[bytearray] = None
        self._walkers: List[List[int]] = []
        self._w = self._h = 0
        self._crystal_size = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init(self, w, h):
        self._w, self._h = w, h
        self._crystal = bytearray(w * h)
        # Seed at center
        cx, cy = w // 2, h // 2
        self._crystal[cy * w + cx] = 1
        self._crystal_size = 1
        self._walkers = []

    def _touches_crystal(self, x, y, w, h):
        g = self._crystal
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and g[ny * w + nx]:
                    return True
        return False

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        rng = state.rng
        intensity = state.intensity_multiplier

        if self._crystal is None or w != self._w or h != self._h:
            self._init(w, h)

        # Reset when too full
        if self._crystal_size > w * h * 0.35:
            self._init(w, h)

        # Spawn walkers at edges
        n_walkers = int(4 + 8 * intensity)
        while len(self._walkers) < n_walkers:
            side = rng.randint(0, 3)
            if side == 0:
                wx, wy = rng.randint(0, w - 1), 1
            elif side == 1:
                wx, wy = rng.randint(0, w - 1), h - 2
            elif side == 2:
                wx, wy = 1, rng.randint(1, h - 2)
            else:
                wx, wy = w - 2, rng.randint(1, h - 2)
            self._walkers.append([wx, wy])

        # Step each walker
        still_walking = []
        for walker in self._walkers:
            wx, wy = walker
            # Random walk
            wx += rng.randint(-1, 1)
            wy += rng.randint(-1, 1)
            wx = max(1, min(w - 2, wx))
            wy = max(1, min(h - 2, wy))
            if self._touches_crystal(wx, wy, w, h):
                if not self._crystal[wy * w + wx]:
                    self._crystal[wy * w + wx] = 1
                    self._crystal_size += 1
                # Walker is absorbed
            else:
                walker[0], walker[1] = wx, wy
                still_walking.append(walker)
        self._walkers = still_walking

        # Render
        g = self._crystal
        bright = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent = curses.color_pair(color_pairs["accent"])
        soft   = curses.color_pair(color_pairs["soft"])
        dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        cx, cy = w // 2, h // 2

        for gy in range(1, h - 1):
            for gx in range(w - 1):
                if g[gy * w + gx]:
                    # Distance from center for shading
                    dist = math.hypot((gx - cx) / max(w, 1), (gy - cy) / max(h, 1))
                    if dist < 0.1:
                        ch, attr = "◉", bright
                    elif dist < 0.25:
                        ch, attr = "●", accent
                    else:
                        ch, attr = "·", soft
                    _safe(stdscr, gy, gx, ch, attr)
                else:
                    _safe(stdscr, gy, gx, " ", dim)

        # Draw walkers
        for wx, wy in self._walkers:
            if 1 <= wy < h - 1 and 0 <= wx < w - 1:
                _safe(stdscr, wy, wx, "○", bright)


    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "skill_create" or event_kind == "checkpoint_created":
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                           origin=(random.random(), random.random()), color_key="bright", duration=4.0)
        if event_kind == "mcp_connected" or event_kind == "mcp_disconnected":
            return Reaction(element=ReactiveElement.CONSTELLATION, intensity=0.8,
                           origin=(0.5, 0.5), color_key="accent", duration=3.0)
        if event_kind == "git_commit" or event_kind == "file_edit":
            return Reaction(element=ReactiveElement.TRAIL, intensity=0.7,
                           origin=(random.random(), random.random()), color_key="soft", duration=2.0)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.7,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.5,
                           origin=(random.random(), random.random()), color_key="soft", duration=1.5)
        return None

    def automaton_config(self):
        return {'rule': 'brians_brain', 'density': 0.03, 'update_interval': 5}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 2


# ── 6. Spirograph ────────────────────────────────────────────────────────────
    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "skill_create" or event_kind == "checkpoint_created":
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                           origin=(random.random(), random.random()), color_key="bright", duration=4.0)
        if event_kind == "mcp_connected" or event_kind == "mcp_disconnected":
            return Reaction(element=ReactiveElement.CONSTELLATION, intensity=0.8,
                           origin=(0.5, 0.5), color_key="accent", duration=3.0)
        if event_kind == "git_commit" or event_kind == "file_edit":
            return Reaction(element=ReactiveElement.TRAIL, intensity=0.7,
                           origin=(random.random(), random.random()), color_key="soft", duration=2.0)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.7,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.5,
                           origin=(random.random(), random.random()), color_key="soft", duration=1.5)
        return None

    def automaton_config(self):
        return {'rule': 'brians_brain', 'density': 0.03, 'update_interval': 5}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 2


class SpirographPlugin(ThemePlugin):
    """Hypotrochoid spirograph curves with fading multi-colour trails.

    Draws x = (R-r)*cos(t) + d*cos((R-r)/r * t),
           y = (R-r)*sin(t) - d*sin((R-r)/r * t).
    R, r, d slowly morph between interesting ratio presets, creating different
    petal and loop patterns over time. Multiple overlapping trails.
    """
    name = "spirograph"

    _PRESETS = [
        # (R, r, d_ratio) — d = d_ratio * r
        (5, 3, 5),
        (7, 2, 1),
        (5, 1, 3),
        (8, 3, 7),
        (7, 3, 4),
        (11, 4, 6),
        (13, 5, 8),
        (6, 5, 6),
    ]

    def __init__(self):
        super().__init__()
        self._trails: List[List[Tuple[int, int, int]]] = [[], [], []]  # (x, y, color_idx)
        self._t = [0.0, math.tau / 3, math.tau * 2 / 3]
        self._preset_idx = 0
        self._morph_t = 0.0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        intensity = state.intensity_multiplier
        cx, cy = w / 2.0, h / 2.0
        scale = min(cx - 3, (cy - 2) * 1.8) * 0.88

        # Morph between presets
        self._morph_t += 0.001 + 0.0008 * intensity
        if self._morph_t >= 1.0:
            self._morph_t = 0.0
            self._preset_idx = (self._preset_idx + 1) % len(self._PRESETS)
            for trail in self._trails:
                trail.clear()

        mt = self._morph_t
        p0 = self._PRESETS[self._preset_idx]
        p1 = self._PRESETS[(self._preset_idx + 1) % len(self._PRESETS)]
        R = p0[0] + (p1[0] - p0[0]) * mt
        r = p0[1] + (p1[1] - p0[1]) * mt
        d = (p0[2] + (p1[2] - p0[2]) * mt) * (r / max(R, 1))
        ratio = (R - r) / max(r, 0.01)

        speed = 0.04 + 0.03 * intensity
        color_keys = ["bright", "accent", "soft"]

        # Advance each curve arm with phase offset
        for arm in range(3):
            self._t[arm] += speed
            t = self._t[arm]
            x = int(cx + ((R - r) * math.cos(t) + d * math.cos(ratio * t)) / R * scale * 0.55)
            y = int(cy + ((R - r) * math.sin(t) - d * math.sin(ratio * t)) / R * scale * 0.5)
            if 1 <= y < h - 1 and 0 <= x < w - 1:
                self._trails[arm].append((x, y, arm))
            max_trail = int(200 + 200 * intensity)
            if len(self._trails[arm]) > max_trail:
                self._trails[arm] = self._trails[arm][-max_trail:]

        # Clear
        base_dim = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        for gy in range(1, h - 1):
            for gx in range(w - 1):
                _safe(stdscr, gy, gx, " ", base_dim)

        # Render trails
        attrs = [
            curses.color_pair(color_pairs["bright"]) | curses.A_BOLD,
            curses.color_pair(color_pairs["accent"]),
            curses.color_pair(color_pairs["soft"]),
        ]
        trail_chars = "·:+*◈"

        for arm in range(3):
            trail = self._trails[arm]
            tl = len(trail)
            for i, (px, py, _) in enumerate(trail):
                age = i / max(tl, 1)
                ci = min(len(trail_chars) - 1, int(age * len(trail_chars)))
                ch = trail_chars[ci]
                attr = attrs[arm] if age > 0.6 else base_dim
                _safe(stdscr, py, px, ch, attr)

        # Tips
        for arm in range(3):
            if self._trails[arm]:
                px, py, _ = self._trails[arm][-1]
                _safe(stdscr, py, px, "◉", attrs[arm])


    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "cron_tick" or event_kind == "background_proc":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.6,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.TRAIL, intensity=0.5,
                           origin=(0.5, 0.5), color_key="soft", duration=0.8)
        if event_kind == "agent_start" or event_kind == "session_resume":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.8,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.5,
                           origin=(0.5, 0.5), color_key="soft", duration=1.5)
        return None

    def wave_config(self):
        return {'speed': 0.25, 'damping': 0.98}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


# ── 7. Harmonograph ──────────────────────────────────────────────────────────
    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "cron_tick" or event_kind == "background_proc":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.6,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.TRAIL, intensity=0.5,
                           origin=(0.5, 0.5), color_key="soft", duration=0.8)
        if event_kind == "agent_start" or event_kind == "session_resume":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.8,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.5,
                           origin=(0.5, 0.5), color_key="soft", duration=1.5)
        return None

    def wave_config(self):
        return {'speed': 0.25, 'damping': 0.98}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


class HarmonographPlugin(ThemePlugin):
    """Compound damped pendulum drawing machine.

    Two x-pendulums and two y-pendulums at slightly different frequencies
    produce Lissajous-like figures that precess and change shape as the
    phase relationship evolves. Damping is removed to keep it running.
    Trails wrap into a density grid that slowly decays.
    """
    name = "harmonograph"

    def __init__(self):
        super().__init__()
        self._grid: Optional[List[List[float]]] = None
        self._t = 0.0
        self._w = self._h = 0
        # (freq, phase, amp) for x1, x2, y1, y2
        self._params = [
            (3.001, 0.0,   1.0),  # x1
            (2.0,   0.5,   0.8),  # x2
            (2.0,   1.5,   1.0),  # y1
            (3.0,   0.0,   0.8),  # y2
        ]

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init(self, w, h):
        self._grid = [[0.0] * w for _ in range(h)]
        self._t = 0.0
        self._w, self._h = w, h

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        if self._grid is None or (w, h) != (self._w, self._h):
            self._init(w, h)

        intensity = state.intensity_multiplier
        grid = self._grid
        cx, cy = w / 2.0, h / 2.0
        rx = (w / 2.0 - 3) * 0.88
        ry = (h / 2.0 - 2) * 0.85

        # Slowly drift frequencies to change shape
        drift = f * 0.000015
        p = self._params
        freqs = [p[0][0] + drift, p[1][0], p[2][0], p[3][0] + drift * 0.7]

        steps = int(80 + 120 * intensity)
        dt = 0.04
        t = self._t
        for _ in range(steps):
            x = (math.sin(freqs[0] * t + p[0][1]) * p[0][2] +
                 math.sin(freqs[1] * t + p[1][1]) * p[1][2]) / (p[0][2] + p[1][2])
            y = (math.sin(freqs[2] * t + p[2][1]) * p[2][2] +
                 math.sin(freqs[3] * t + p[3][1]) * p[3][2]) / (p[2][2] + p[3][2])
            t += dt
            sx = int(cx + x * rx * 0.55)
            sy = int(cy + y * ry * 0.5)
            if 1 <= sy < h - 1 and 0 <= sx < w - 1:
                grid[sy][sx] = min(grid[sy][sx] + 0.08, 1.0)

        self._t = t

        # Decay and render
        decay = 0.980 - 0.005 * intensity
        chars = " ·.:;=+*#█"
        nc = len(chars) - 1
        bright = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent = curses.color_pair(color_pairs["accent"])
        soft   = curses.color_pair(color_pairs["soft"])
        dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        for gy in range(1, h - 1):
            row = grid[gy]
            for gx in range(w - 1):
                v = row[gx] * decay
                row[gx] = v
                ci = max(0, min(nc, int(v * nc)))
                ch = chars[ci]
                attr = bright if v > 0.72 else (accent if v > 0.42 else (soft if v > 0.16 else dim))
                _safe(stdscr, gy, gx, ch, attr)


    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "llm_start" or event_kind == "llm_end":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        if event_kind == "memory_save" or event_kind == "checkpoint_created":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.9,
                           origin=(0.5, 0.5), color_key="bright", duration=2.5)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.5)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.5,
                           origin=(0.5, 0.5), color_key="soft", duration=1.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.3,
                           origin=(0.0, 0.5), color_key="soft", duration=0.6)
        return None

    def wave_config(self):
        return {'speed': 0.35, 'damping': 0.97}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


# ── 8. Julia Morph ───────────────────────────────────────────────────────────
    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "llm_start" or event_kind == "llm_end":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="accent", duration=2.0)
        if event_kind == "memory_save" or event_kind == "checkpoint_created":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.9,
                           origin=(0.5, 0.5), color_key="bright", duration=2.5)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.5)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.5,
                           origin=(0.5, 0.5), color_key="soft", duration=1.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.3,
                           origin=(0.0, 0.5), color_key="soft", duration=0.6)
        return None

    def wave_config(self):
        return {'speed': 0.35, 'damping': 0.97}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


class JuliaMorphPlugin(ThemePlugin):
    """Julia set with continuously orbiting complex parameter c = r·e^(iθ).

    θ rotates slowly, sweeping through the full orbit and producing alien
    fractal geometries: dendrites, Douady's rabbit, Basilica, Siegel disk,
    etc. Density accumulated with decay so hot spots glow.
    """
    name = "julia-morph"

    def __init__(self):
        super().__init__()
        self._grid: Optional[List[List[float]]] = None
        self._theta = 0.0
        self._w = self._h = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init(self, w, h):
        self._grid = [[0.0] * w for _ in range(h)]
        self._w, self._h = w, h

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        if self._grid is None or (w, h) != (self._w, self._h):
            self._init(w, h)

        intensity = state.intensity_multiplier
        grid = self._grid

        # Orbit radius stays at ~0.7885 — the "interesting" boundary
        self._theta += 0.006 + 0.003 * intensity
        r_c = 0.7885
        cr = r_c * math.cos(self._theta)
        ci_val = r_c * math.sin(self._theta)

        MAX_ITER = 32
        # Viewport: [-1.6, 1.6] × [-1.0, 1.0] (aspect-corrected)
        x_range = 1.6
        y_range = x_range * h / max(w * 0.55, 1)

        # Render directly (no accumulation for Julia — just threshold map)
        bright = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent = curses.color_pair(color_pairs["accent"])
        soft   = curses.color_pair(color_pairs["soft"])
        dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        base   = curses.color_pair(color_pairs["base"])

        chars = " ·.:;=+*▓█"
        nc = len(chars) - 1

        for gy in range(1, h - 1):
            zy = (gy / h - 0.5) * 2.0 * y_range
            row = grid[gy]
            for gx in range(w - 1):
                zx = (gx / max(w, 1) - 0.5) * 2.0 * x_range

                # Julia iteration
                it = 0
                while zx * zx + zy * zy < 4.0 and it < MAX_ITER:
                    zx, zy = zx * zx - zy * zy + cr, 2.0 * zx * zy + ci_val
                    it += 1

                # Accumulate density in grid
                if it == MAX_ITER:
                    row[gx] = min(row[gx] + 0.04, 1.0)
                else:
                    row[gx] *= 0.96

                v = row[gx]
                band = it / MAX_ITER

                if it == MAX_ITER:
                    ch = "█" if v > 0.6 else "▓"
                    attr = base if v < 0.3 else (soft if v < 0.6 else accent)
                else:
                    ci = max(0, min(nc - 2, int(band * (nc - 2))))
                    ch = chars[ci + 1]
                    if band < 0.15:
                        attr = bright
                    elif band < 0.40:
                        attr = accent
                    elif band < 0.70:
                        attr = soft
                    else:
                        attr = dim

                _safe(stdscr, gy, gx, ch, attr)
    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "reasoning_change" or event_kind == "personality_change":
            return Reaction(element=ReactiveElement.GLYPH, intensity=1.0,
                           origin=(0.5, 0.5), color_key="bright", duration=3.0)
        if event_kind == "compression_started" or event_kind == "compression_ended":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.9,
                           origin=(0.5, 0.5), color_key="accent", duration=3.0)
        if event_kind == "memory_save" or event_kind == "skill_create":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.9,
                           origin=(0.5, 0.5), color_key="bright", duration=2.5)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.8,
                           origin=(0.5, 0.5), color_key="bright", duration=2.0)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.5,
                           origin=(0.5, 0.5), color_key="soft", duration=1.5)
        return None

    def automaton_config(self):
        return {'rule': 'brians_brain', 'density': 0.05, 'update_interval': 3}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


# ── Registration ─────────────────────────────────────────────────────────────

register(LorenzAttractorPlugin())
register(FourierEpicyclesPlugin())
register(SandCascadePlugin())
register(RorschachPlugin())
register(DlaCrystalPlugin())
register(SpirographPlugin())
register(HarmonographPlugin())
register(JuliaMorphPlugin())