"""Legacy v2b pre-v0.2-upgrade theme screens.

Verbatim copies of screens from generators.py, hostile.py, industrial.py,
mechanical.py, and new_screens.py, preserved before v0.2 API upgrade.

Registered under "legacy-v2-*" names. NOT in THEMES tuple.
"""

from __future__ import annotations

import curses
import math
import random
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register




# ======================================================================
# From generators.py
# ======================================================================

class Legacy2LorenzAttractorPlugin(ThemePlugin):
    """3D Lorenz strange attractor projected onto the terminal plane.

    The classic σ=10, ρ=28, β=8/3 butterfly orbit accumulated into a density
    grid with slow decay. Projection rotates slowly so you see all three wings.
    Intensity multiplier controls iteration count and decay rate.
    """
    name = "legacy-v2-lorenz-attractor"

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


# ── 2. Fourier Epicycles ─────────────────────────────────────────────────────

class Legacy2FourierEpicyclesPlugin(ThemePlugin):
    """Chain of rotating arms (epicycles) tracing a Fourier curve.

    Uses 8 harmonics with randomised amplitudes that slowly morph, so the
    drawn shape continuously evolves. The tip trail fades over ~400 points.
    Arm lengths shown as faint circles; tip shown bright.
    """
    name = "legacy-v2-fourier-epicycles"

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


# ── 3. Sand Cascade ──────────────────────────────────────────────────────────

class Legacy2SandCascadePlugin(ThemePlugin):
    """Falling sand / pixel physics simulation.

    Sand grains fall under gravity, pile up, and slide off slopes. New sand
    spawns at the top at random columns. Intensity drives spawn rate and
    periodically clears columns to restart the cascade.
    """
    name = "legacy-v2-sand-cascade"

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


# ── 4. Rorschach ─────────────────────────────────────────────────────────────

class Legacy2RorschachPlugin(ThemePlugin):
    """Symmetrically mirrored noise field creating evolving inkblot patterns.

    Four overlapping sine/cosine waves with slowly drifting parameters fill
    the left half of the screen; the right half is mirrored. A vertical center
    crease is drawn for the fold effect. Density mapped to block chars.
    """
    name = "legacy-v2-rorschach"

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


# ── 5. DLA Crystal ──────────────────────────────────────────────────────────

class Legacy2DlaCrystalPlugin(ThemePlugin):
    """Diffusion-Limited Aggregation: random walkers stick to a growing crystal.

    Seeded at center. New walkers spawn at the screen edge and walk randomly
    until they touch the crystal, then freeze. Periodically resets when the
    crystal fills. Crystal cells rendered with density-based characters.
    """
    name = "legacy-v2-dla-crystal"

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


# ── 6. Spirograph ────────────────────────────────────────────────────────────

class Legacy2SpirographPlugin(ThemePlugin):
    """Hypotrochoid spirograph curves with fading multi-colour trails.

    Draws x = (R-r)*cos(t) + d*cos((R-r)/r * t),
           y = (R-r)*sin(t) - d*sin((R-r)/r * t).
    R, r, d slowly morph between interesting ratio presets, creating different
    petal and loop patterns over time. Multiple overlapping trails.
    """
    name = "legacy-v2-spirograph"

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


# ── 7. Harmonograph ──────────────────────────────────────────────────────────

class Legacy2HarmonographPlugin(ThemePlugin):
    """Compound damped pendulum drawing machine.

    Two x-pendulums and two y-pendulums at slightly different frequencies
    produce Lissajous-like figures that precess and change shape as the
    phase relationship evolves. Damping is removed to keep it running.
    Trails wrap into a density grid that slowly decays.
    """
    name = "legacy-v2-harmonograph"

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


# ── 8. Julia Morph ───────────────────────────────────────────────────────────

class Legacy2JuliaMorphPlugin(ThemePlugin):
    """Julia set with continuously orbiting complex parameter c = r·e^(iθ).

    θ rotates slowly, sweeping through the full orbit and producing alien
    fractal geometries: dendrites, Douady's rabbit, Basilica, Siegel disk,
    etc. Density accumulated with decay so hot spots glow.
    """
    name = "legacy-v2-julia-morph"

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


# ── Registration ─────────────────────────────────────────────────────────────

register(Legacy2LorenzAttractorPlugin())
register(Legacy2FourierEpicyclesPlugin())
register(Legacy2SandCascadePlugin())
register(Legacy2RorschachPlugin())
register(Legacy2DlaCrystalPlugin())
register(Legacy2SpirographPlugin())
register(Legacy2HarmonographPlugin())
register(Legacy2JuliaMorphPlugin())


# ======================================================================
# From hostile.py
# ======================================================================

class Legacy2NoxiousFumesPlugin(ThemePlugin):
    """Poisonous gas clouds — dense fog with toxic bubbles."""

    name = "legacy-v2-noxious-fumes"

    def build_nodes(self, w, h, cx, cy, count, rng):
        # Nodes hidden in fog — scattered randomly
        nodes = []
        for _ in range(count):
            x = rng.uniform(4, max(5, w - 5))
            y = rng.uniform(2, max(3, h - 3))
            nodes.append((x, y))
        return nodes

    def step_star(self, star, frame, w, h, rng):
        # Dense fog drifting horizontally
        star[0] += 0.04 * star[2]  # drift right
        star[1] += math.sin(frame * 0.02 + star[3]) * 0.015  # slight vertical wobble
        if star[0] >= w - 1:
            # Wrap to left side
            star[0] = 1.0
            star[1] = rng.uniform(1, max(2, h - 2))
        return True

    def star_glyph(self, brightness, char_idx):
        # Dense fog characters
        if brightness > 0.65:
            return "▒"
        return "░"

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Toxic bubbles rising and popping
        x = rng.uniform(3, max(4, w - 4))
        y = rng.uniform(max(2, h * 0.4), max(h * 0.4 + 1, h - 2))
        vx = rng.uniform(-0.04, 0.04)
        vy = rng.uniform(-0.12, -0.04)  # rising
        char = rng.choice("°○")
        life = rng.randint(6, 14)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        # Barely visible wisps
        return "·" if abs(dx) > abs(dy) else "."

    def pulse_params(self):
        return (0.14, 0.24)

    def node_glyph(self, idx, intensity, total):
        return "○" if intensity > 0.65 else "◌"

    def node_color_key(self, idx, intensity, total):
        return "soft"

    def particle_color_key(self, age_ratio):
        return "soft"  # always dim toxic

    def edge_color_key(self, step, idx_a, frame):
        return "soft"

    def pulse_color_key(self):
        return "base"

    def packet_color_key(self):
        return "soft"


class Legacy2MazeRunnerPlugin(ThemePlugin):
    """Shifting dimensional maze — walls phase in/out, reality tears, recursive portals."""

    name = "legacy-v2-maze-runner"

    def build_nodes(self, w, h, cx, cy, count, rng):
        # Three layers of reality at different depths
        nodes = []
        for layer in range(3):
            layer_count = count // 3
            for _ in range(layer_count):
                # Each layer has different clustering
                if layer == 0:
                    # Front layer: scattered wide
                    x = rng.uniform(4, max(5, w - 5))
                    y = rng.uniform(2, max(3, h - 3))
                elif layer == 1:
                    # Middle layer: ring formation
                    angle = rng.uniform(0, math.tau)
                    radius = min(w, h) * 0.25
                    x = cx + math.cos(angle) * radius * 1.2
                    y = cy + math.sin(angle) * radius * 0.6
                else:
                    # Deep layer: central vortex
                    angle = rng.uniform(0, math.tau)
                    radius = rng.uniform(0, min(w, h) * 0.15)
                    x = cx + math.cos(angle) * radius * 1.0
                    y = cy + math.sin(angle) * radius * 0.5
                nodes.append((x, y))
        return nodes

    def step_nodes(self, nodes, frame, w, h):
        # Nodes phase between dimensions with sine-wave oscillation
        cx = w / 2.0
        cy = h / 2.0
        for i in range(len(nodes)):
            x, y = nodes[i]
            # Oscillate radius from center
            dx = x - cx
            dy = y - cy
            dist = max(0.5, math.hypot(dx, dy))
            angle = math.atan2(dy, dx)
            
            # Each layer phases differently
            layer = i % 3
            if layer == 0:
                # Front: slow expansion/contraction
                pulse = math.sin(frame * 0.03 + i * 0.5) * 2.0
            elif layer == 1:
                # Middle: rotation and pulse
                angle += 0.015
                pulse = math.cos(frame * 0.04 + i * 0.7) * 1.5
            else:
                # Deep: intense pulsing
                pulse = math.sin(frame * 0.06 + i * 1.2) * 3.0
            
            new_dist = dist + pulse
            new_x = cx + math.cos(angle) * new_dist * 1.2
            new_y = cy + math.sin(angle) * new_dist * 0.6
            
            nodes[i] = (
                max(3.0, min(w - 4.0, new_x)),
                max(2.0, min(h - 3.0, new_y))
            )

    def step_star(self, star, frame, w, h, rng):
        # Reality tears drifting through dimensions
        star[0] += math.sin(frame * 0.02 + star[3]) * 0.3
        star[1] += math.cos(frame * 0.025 + star[3] * 0.7) * 0.2
        # Wrap around
        if star[0] < 2:
            star[0] = w - 3
        elif star[0] > w - 3:
            star[0] = 2
        if star[1] < 1:
            star[1] = h - 2
        elif star[1] > h - 2:
            star[1] = 1
        return True

    def star_glyph(self, brightness, char_idx):
        # Dimensional rifts and tears
        if brightness > 0.8:
            return "※"
        elif brightness > 0.5:
            return "◊"
        return "·"

    def spawn_particle(self, w, h, nodes, rng):
        from hermes_neurovision.scene import Particle
        # Dimensional sparks ejected from portals
        if nodes:
            node = rng.choice(nodes)
            angle = rng.uniform(0, math.tau)
            speed = rng.uniform(0.08, 0.25)
            x = node[0]
            y = node[1]
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed * 0.6
        else:
            x = rng.uniform(3, max(4, w - 4))
            y = rng.uniform(2, max(3, h - 3))
            vx = rng.uniform(-0.15, 0.15)
            vy = rng.uniform(-0.10, 0.10)
        char = rng.choice("※◊*·")
        life = rng.randint(8, 18)
        return Particle(x, y, vx, vy, life, life, char)

    def edge_glyph(self, dx, dy):
        # Reality bridges between dimensions
        return "╌" if abs(dx) > abs(dy) else "┆"

    def node_glyph(self, idx, intensity, total):
        layer = idx % 3
        if intensity > 0.75:
            return "⊗"  # Active portal
        elif layer == 0:
            return "◎"  # Front layer
        elif layer == 1:
            return "◉"  # Middle layer
        else:
            return "●"  # Deep layer

    def packet_budget(self):
        return 6

    def node_color_key(self, idx, intensity, total):
        layer = idx % 3
        if intensity > 0.75:
            return "warning"
        elif layer == 2:
            return "accent"
        elif layer == 1:
            return "bright"
        return "soft"

    def edge_color_key(self, step, idx_a, frame):
        # Edges phase in and out of visibility
        phase = (step + frame * 0.5) % 40
        if phase < 10:
            return "bright"
        elif phase < 20:
            return "accent"
        return "soft"

    def particle_color_key(self, age_ratio):
        return "bright" if age_ratio > 0.6 else "accent" if age_ratio > 0.3 else "soft"

    def packet_color_key(self):
        return "warning"

    def pulse_style(self):
        return "ripple"

    def pulse_style(self):
        return "diamond"

    def pulse_color_key(self):
        return "soft"

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        w = state.width
        h = state.height
        pair = curses.color_pair(color_pairs.get("soft", 0))
        # Top border: ╔══...══╗
        try:
            top_mid = "═" * max(0, w - 4)
            stdscr.addstr(0, 2, "╔" + top_mid + "╗", pair)
        except curses.error:
            pass
        # Side borders
        for row in range(1, h - 2):
            try:
                stdscr.addstr(row, 2, "║", pair)
            except curses.error:
                pass
            try:
                stdscr.addstr(row, w - 2, "║", pair)
            except curses.error:
                pass
        # Bottom border: ╚══...══╝
        try:
            bot_mid = "═" * max(0, w - 4)
            stdscr.addstr(h - 2, 2, "╚" + bot_mid + "╝", pair)
        except curses.error:
            pass


# ── Register all hostile plugins ─────────────────────────────────

for _cls in [
    NoxiousFumesPlugin, MazeRunnerPlugin,
]:
    register(_cls())


# ======================================================================
# From industrial.py
# ======================================================================

class Legacy2LiquidMetalPlugin(ThemePlugin):
    """T-1000 mercury — amorphous chrome blobs with liquid bridges."""

    name = "legacy-v2-liquid-metal"

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


class Legacy2FactoryFloorPlugin(ThemePlugin):
    """Assembly line — machines in grid with sparks and steam."""

    name = "legacy-v2-factory-floor"

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


class Legacy2PipeHellPlugin(ThemePlugin):
    """Infinite plumbing nightmare — pipe junctions everywhere."""

    name = "legacy-v2-pipe-hell"

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


class Legacy2OilSlickPlugin(ThemePlugin):
    """Iridescent rainbow on black water — slow drifting shimmer."""

    name = "legacy-v2-oil-slick"

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


# ── Register all industrial plugins ──────────────────────────────

for _cls in [
    LiquidMetalPlugin, FactoryFloorPlugin, PipeHellPlugin, OilSlickPlugin,
]:
    register(_cls())


# ======================================================================
# From mechanical.py
# ======================================================================

class Legacy2ClockworkPlugin(ThemePlugin):
    """Victorian steampunk mechanism."""
    name = "legacy-v2-clockwork"

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


class Legacy2CoralReefPlugin(ThemePlugin):
    """Vibrant underwater reef."""
    name = "legacy-v2-coral-reef"

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


class Legacy2AntColonyPlugin(ThemePlugin):
    """Underground tunnel network."""
    name = "legacy-v2-ant-colony"

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


class Legacy2SatelliteOrbitPlugin(ThemePlugin):
    """Earth from space with orbiting satellites."""
    name = "legacy-v2-satellite-orbit"

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


class Legacy2StarfallPlugin(ThemePlugin):
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


# ======================================================================
# From new_screens.py
# ======================================================================

class Legacy2AsciiRainPlugin(ThemePlugin):
    """Matrix-style columnar rain with variable-speed streams, pooling at base.

    Each column maintains an independent falling head and a fading trail.
    Head characters are drawn from a wide Unicode katakana + symbol set.
    When a stream hits the bottom it pools into a spreading puddle of dim chars.
    Color travels down each trail so the head is bright and decays through
    accent → soft → base → gone.
    """
    name = "legacy-v2-ascii-rain"

    _GLYPHS = (
        "アイウエオカキクケコサシスセソタチツテトナニヌネノ"
        "ハヒフヘホマミムメモヤユヨラリルレロワヲン"
        "0123456789ABCDEF@#$%&*<>?!+=~"
    )

    def __init__(self):
        super().__init__()
        self._cols: dict = {}   # col_x -> {y, speed, trail, char_seq}
        self._pools: List[List] = []  # [x, y, age, max_age]
        self._rng = random.Random(7331)
        self._w = self._h = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init_cols(self, w, h):
        rng = self._rng
        self._cols = {}
        # Spawn a stream in ~60% of columns initially, staggered start
        for x in range(0, w - 1):
            if rng.random() < 0.55:
                self._cols[x] = {
                    "y":     rng.uniform(-h, 0),
                    "speed": rng.uniform(0.35, 1.2),
                    "trail": [],     # list of (y_int, char, age)
                    "seq":   [rng.choice(self._GLYPHS) for _ in range(rng.randint(6, 20))],
                    "len":   rng.randint(6, 20),
                }
        self._pools = []
        self._w, self._h = w, h

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        intensity = state.intensity_multiplier

        if not self._cols or w != self._w or h != self._h:
            self._init_cols(w, h)

        rng = self._rng
        cp = color_pairs

        bright_attr = curses.color_pair(cp.get("bright", 1)) | curses.A_BOLD
        accent_attr = curses.color_pair(cp.get("accent", 1))
        soft_attr   = curses.color_pair(cp.get("soft",   1))
        base_dim    = curses.color_pair(cp.get("base",   1)) | curses.A_DIM

        # Clear with spaces first
        for y in range(1, h - 1):
            for x in range(0, w - 1):
                _safe(stdscr, y, x, " ", base_dim)

        # Draw pools first (background)
        new_pools = []
        for pool in self._pools:
            px, py, age, max_age = pool
            if age >= max_age:
                continue
            pool[2] += 1
            ratio = 1.0 - age / max_age
            # Spread radius grows then shrinks
            spread = int(min(age, max_age - age) * 0.6)
            for dx in range(-spread, spread + 1):
                rx = px + dx
                if 0 <= rx < w - 1 and 1 <= py < h - 1:
                    v = ratio * (1.0 - abs(dx) / max(spread + 1, 1))
                    if v > 0.1:
                        ch = rng.choice("·~░")
                        _safe(stdscr, py, rx, ch, soft_attr if v > 0.4 else base_dim)
            new_pools.append(pool)
        self._pools = new_pools

        # Step and draw streams
        for x, col in list(self._cols.items()):
            col["y"] += col["speed"] * (0.6 + 0.4 * intensity)
            head_y = int(col["y"])

            # Spawn new stream once this one exits
            if head_y > h + col["len"] + 4:
                if rng.random() < 0.85:
                    col["y"]     = rng.uniform(-col["len"] - 4, 0)
                    col["speed"] = rng.uniform(0.35, 1.2)
                    col["len"]   = rng.randint(6, 20)
                    col["seq"]   = [rng.choice(self._GLYPHS)
                                    for _ in range(col["len"])]
                else:
                    del self._cols[x]
                    continue

            # Pool spawn when head touches bottom
            if head_y >= h - 2 and rng.random() < 0.25:
                self._pools.append([x, h - 2, 0, rng.randint(15, 40)])

            # Draw trail — each position in the trail has a different age
            trail_len = col["len"]
            for i in range(trail_len):
                ty = head_y - i
                if ty < 1 or ty >= h - 1:
                    continue
                seq_i  = i % len(col["seq"])
                ch     = col["seq"][seq_i]
                # Mutate head character each frame for flicker
                if i == 0:
                    col["seq"][0] = rng.choice(self._GLYPHS)
                    attr = bright_attr
                elif i < 3:
                    attr = accent_attr
                elif i < trail_len * 0.55:
                    attr = soft_attr
                else:
                    attr = base_dim
                _safe(stdscr, ty, x, ch, attr)

        # Spawn new columns occasionally
        if rng.random() < 0.08 and len(self._cols) < w - 2:
            nx = rng.randint(0, w - 2)
            if nx not in self._cols:
                self._cols[nx] = {
                    "y":     rng.uniform(-8, 0),
                    "speed": rng.uniform(0.35, 1.2),
                    "trail": [],
                    "seq":   [rng.choice(self._GLYPHS) for _ in range(rng.randint(6, 20))],
                    "len":   rng.randint(6, 20),
                }


# ═══════════════════════════════════════════════════════════════════════════
# ASCII ENGINE 2: sand-automaton — Falling sand cellular automaton
# ═══════════════════════════════════════════════════════════════════════════

class Legacy2SandAutomatonPlugin(ThemePlugin):
    """Falling-sand simulation: gravity, stacking, erosion, and rain seeding.

    Rules per tick:
      - Empty cell above a full cell: fall (swap)
      - Full cell on flat ground: stay
      - Full cell on slope: slide left/right with probability
    Sand rains in from the top and erodes from the bottom.  Color encodes
    age: fresh sand is bright, settled sand fades to base.
    """
    name = "legacy-v2-sand-automaton"

    def __init__(self):
        super().__init__()
        self._grid  = None   # bytearray: 0=empty, 1=sand
        self._age   = None   # bytearray: age 0-255
        self._w = self._h = 0
        self._rng = random.Random(2718)

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init(self, w, h, rng):
        size = w * h
        self._grid = bytearray(size)
        self._age  = bytearray(size)
        # Seed bottom third with random sand
        for y in range(h * 2 // 3, h):
            for x in range(w):
                if rng.random() < 0.35:
                    idx = y * w + x
                    self._grid[idx] = 1
                    self._age[idx]  = rng.randint(30, 200)
        self._w, self._h = w, h

    def _step(self, w, h, intensity):
        g   = self._grid
        age = self._age
        rng = self._rng
        # Iterate bottom-up so sand falls in one pass
        for y in range(h - 2, 0, -1):
            for x in range(w):
                idx = y * w + x
                if not g[idx]:
                    continue
                below = (y + 1) * w + x
                if y + 1 < h and not g[below]:
                    # Fall straight down
                    g[below]   = 1
                    age[below] = age[idx]
                    g[idx]     = 0
                    age[idx]   = 0
                else:
                    # Try to slide diagonally
                    dirs = [-1, 1]
                    rng.shuffle(dirs)
                    moved = False
                    for dx in dirs:
                        nx = x + dx
                        if 0 <= nx < w:
                            diag = (y + 1) * w + nx
                            side = y * w + nx
                            if y + 1 < h and not g[diag] and not g[side]:
                                g[diag]   = 1
                                age[diag] = age[idx]
                                g[idx]    = 0
                                age[idx]  = 0
                                moved     = True
                                break
                    if not moved and age[idx] < 254:
                        age[idx] += 1

        # Rain: seed top rows
        rain_density = 0.04 + 0.06 * intensity
        for x in range(w):
            if rng.random() < rain_density and not g[x]:  # y=0
                g[x]   = 1
                age[x] = 0

        # Erosion: remove random bottom cells
        for x in range(w):
            idx = (h - 1) * w + x
            if g[idx] and rng.random() < 0.015:
                g[idx]   = 0
                age[idx] = 0

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        intensity = state.intensity_multiplier

        if self._grid is None or w != self._w or h != self._h:
            self._init(w, h, self._rng)

        # Run 2-3 simulation steps per frame
        steps = 3 if intensity > 0.6 else 2
        for _ in range(steps):
            self._step(w, h, intensity)

        cp          = color_pairs
        bright_attr = curses.color_pair(cp.get("bright", 1)) | curses.A_BOLD
        accent_attr = curses.color_pair(cp.get("accent", 1))
        soft_attr   = curses.color_pair(cp.get("soft",   1))
        base_dim    = curses.color_pair(cp.get("base",   1)) | curses.A_DIM

        g   = self._grid
        age = self._age

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                idx = y * w + x
                if g[idx]:
                    a  = age[idx]
                    # Color based on age: fresh=bright, old=base
                    if a < 15:
                        attr = bright_attr
                        ch   = "█"
                    elif a < 60:
                        attr = accent_attr
                        ch   = "▓"
                    elif a < 140:
                        attr = soft_attr
                        ch   = "▒"
                    else:
                        attr = base_dim
                        ch   = "░"
                    _safe(stdscr, y, x, ch, attr)
                else:
                    _safe(stdscr, y, x, " ", base_dim)


# ═══════════════════════════════════════════════════════════════════════════
# ASCII ENGINE 3: ascii-rorschach — Bilateral ink-blot growth field
# ═══════════════════════════════════════════════════════════════════════════

class Legacy2AsciiRorschachPlugin(ThemePlugin):
    """Procedural ink-blot: a density grid grows outward from random seeds,
    is mirrored across the vertical axis, and slowly evaporates.

    The growth rule: each cell's value is nudged toward the average of its
    neighbours plus a small noise term.  New ink seeds erupt periodically.
    Colors cycle through the hue helper so the blot shimmers between palette
    entries as it evolves.  Completely different from every other screen —
    no oscillations, no particles, just emergent diffusive growth + mirror.
    """
    name = "legacy-v2-ascii-rorschach"

    def __init__(self):
        super().__init__()
        self._ink  = None   # float grid, 0-1
        self._w = self._h = 0
        self._rng = random.Random(9999)
        self._seed_timer = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init(self, w, h):
        hw = w // 2
        size = hw * h
        self._ink  = [0.0] * size
        self._w, self._h = w, h
        # Seed initial blot
        rng = self._rng
        for _ in range(6):
            sx = rng.randint(1, max(2, hw - 2))
            sy = rng.randint(h // 4, max(h // 4 + 1, h * 3 // 4))
            r  = rng.randint(1, 3)
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    nx, ny = sx + dx, sy + dy
                    if 0 <= nx < hw and 0 <= ny < h:
                        self._ink[ny * hw + nx] = min(1.0, rng.uniform(0.4, 0.9))

    def _step(self, w, h, intensity):
        hw   = w // 2
        ink  = self._ink
        rng  = self._rng
        new  = ink[:]

        evap  = 0.992 - 0.004 * intensity   # slow evaporation
        noise = 0.008

        for y in range(1, h - 1):
            for x in range(1, hw - 1):
                idx   = y * hw + x
                # Neighbour average
                nbr = (ink[(y-1)*hw+x] + ink[(y+1)*hw+x]
                       + ink[y*hw+x-1] + ink[y*hw+x+1]) / 4.0
                v = ink[idx] * evap + nbr * 0.12 + rng.uniform(-noise, noise)
                new[idx] = max(0.0, min(1.0, v))

        # Periodic seed eruption
        self._seed_timer += 1
        interval = max(20, int(80 - 50 * intensity))
        if self._seed_timer >= interval:
            self._seed_timer = 0
            sx = rng.randint(2, max(3, hw - 3))
            sy = rng.randint(h // 5, max(h // 5 + 1, h * 4 // 5))
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    nx, ny = sx + dx, sy + dy
                    if 0 <= nx < hw and 0 <= ny < h:
                        new[ny * hw + nx] = min(1.0,
                            new[ny * hw + nx] + rng.uniform(0.3, 0.7))
        self._ink = new

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        intensity = state.intensity_multiplier

        if self._ink is None or w != self._w or h != self._h:
            self._init(w, h)

        self._step(w, h, intensity)

        hw       = w // 2
        ink      = self._ink
        hue_base = (f * 0.003) % 1.0
        cp       = color_pairs
        chars    = " ·.:;+=*#▓█"
        nc       = len(chars) - 1

        for y in range(1, h - 1):
            for xh in range(0, hw):
                v   = ink[y * hw + xh]
                ci  = int(v * nc)
                ch  = chars[ci]
                if ch == " ":
                    attr = curses.color_pair(cp.get("base", 1)) | curses.A_DIM
                else:
                    phase = (hue_base + xh / max(hw, 1) * 0.4
                             + y / max(h, 1) * 0.3) % 1.0
                    attr = _hue(v, phase, cp)

                # Left half
                _safe(stdscr, y, xh, ch, attr)
                # Mirror to right half (bilateral symmetry)
                rx = w - 2 - xh
                if rx >= 0 and rx < w - 1:
                    _safe(stdscr, y, rx, ch, attr)


# ═══════════════════════════════════════════════════════════════════════════
# GEOMETRIC 1: wireframe-cube — Spinning 3D wireframe cube + inner octahedron
# ═══════════════════════════════════════════════════════════════════════════

class Legacy2WireframeCubePlugin(ThemePlugin):
    """3D wireframe cube rotating on all three axes simultaneously.

    An octahedron spins inside at a different rate.  Edges are drawn with
    Bresenham lines; depth is encoded in character density and color.
    Vertices are drawn as bright dots.  No external geometry library needed —
    pure 4x4 rotation matrix math inline.
    """
    name = "legacy-v2-wireframe-cube"

    # Cube vertices: unit cube centred at origin
    _CUBE_V = [
        (-1,-1,-1),( 1,-1,-1),( 1, 1,-1),(-1, 1,-1),
        (-1,-1, 1),( 1,-1, 1),( 1, 1, 1),(-1, 1, 1),
    ]
    _CUBE_E = [
        (0,1),(1,2),(2,3),(3,0),  # back face
        (4,5),(5,6),(6,7),(7,4),  # front face
        (0,4),(1,5),(2,6),(3,7),  # connecting edges
    ]
    # Octahedron vertices: unit octahedron
    _OCTA_V = [
        ( 0, 0,-1),( 0, 0, 1),
        (-1, 0, 0),( 1, 0, 0),
        ( 0,-1, 0),( 0, 1, 0),
    ]
    _OCTA_E = [
        (0,2),(0,3),(0,4),(0,5),
        (1,2),(1,3),(1,4),(1,5),
    ]

    def __init__(self):
        super().__init__()

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    @staticmethod
    def _rot(verts, ax, ay, az):
        """Rotate list of (x,y,z) by Euler angles ax,ay,az."""
        cx, sx = math.cos(ax), math.sin(ax)
        cy, sy = math.cos(ay), math.sin(ay)
        cz, sz = math.cos(az), math.sin(az)
        out = []
        for x, y, z in verts:
            # Rx
            y, z = cy*y - cz*z, cy*z + cz*y   # wrong — use proper matrices
            # Redo properly
            x0, y0, z0 = x, y, z
            # Rx
            y1 =  cx*y0 - sx*z0
            z1 =  sx*y0 + cx*z0
            # Ry
            x2 =  cy*x0 + sy*z1
            z2 = -sy*x0 + cy*z1
            # Rz
            x3 =  cz*x2 - sz*y1
            y3 =  sz*x2 + cz*y1
            out.append((x3, y3, z2))
        return out

    @staticmethod
    def _project(x, y, z, cx, cy, scale, ay):
        """Simple perspective projection."""
        fov = 3.5
        dz  = fov + z
        if dz < 0.1:
            dz = 0.1
        px = int(cx + x * scale / dz)
        py = int(cy + y * scale / dz / ay)
        return px, py

    @staticmethod
    def _line(x0, y0, x1, y1, w, h):
        """Bresenham line iterator, yields (x,y) within bounds."""
        dx = abs(x1 - x0);  sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0); sy = 1 if y0 < y1 else -1
        err = dx + dy
        cx2, cy2 = x0, y0
        for _ in range(400):
            if 1 <= cy2 < h - 1 and 0 <= cx2 < w - 1:
                yield cx2, cy2
            if cx2 == x1 and cy2 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; cx2 += sx
            if e2 <= dx:
                err += dx; cy2 += sy

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        cy_screen = h / 2.0
        cx_screen = w / 2.0
        intensity = state.intensity_multiplier
        ay = 2.1   # terminal aspect

        cp = color_pairs
        bright_attr = curses.color_pair(cp.get("bright", 1)) | curses.A_BOLD
        accent_attr = curses.color_pair(cp.get("accent", 1))
        soft_attr   = curses.color_pair(cp.get("soft",   1))
        base_dim    = curses.color_pair(cp.get("base",   1)) | curses.A_DIM

        # Clear
        for y in range(1, h - 1):
            for x in range(0, w - 1):
                _safe(stdscr, y, x, " ", base_dim)

        # Rotation angles: cube and octahedron spin at different rates
        t   = f * 0.022
        ax  = t * 0.7
        ay_ = t * 1.0
        az  = t * 0.5
        # Octahedron spins opposite + faster
        oax = -t * 1.1
        oay =  t * 0.8
        oaz =  t * 1.4

        scale = min(w * 0.28, h * 0.55)
        hue_base = (f * 0.003) % 1.0

        def _draw_wire(verts_3d, edges, rotation, base_phase):
            rv = self._rot(verts_3d, *rotation)
            pts = [self._project(x, y, z, cx_screen, cy_screen, scale, ay)
                   for x, y, z in rv]
            zvals = [z for _, _, z in rv]

            for i, (a, b) in enumerate(edges):
                px0, py0 = pts[a]
                px1, py1 = pts[b]
                avg_z = (zvals[a] + zvals[b]) / 2.0
                depth = (avg_z + 2.0) / 4.0   # 0=far, 1=near
                phase = (hue_base + base_phase + i * 0.07 + depth * 0.3) % 1.0
                edge_chars = "·:=≡"
                eci = int(depth * (len(edge_chars) - 1))
                ech = edge_chars[eci]
                attr = _hue(depth, phase, cp)
                for lx, ly in self._line(px0, py0, px1, py1, w, h):
                    _safe(stdscr, ly, lx, ech, attr)

            # Draw vertices
            for vi, (px, py) in enumerate(pts):
                if 1 <= py < h - 1 and 0 <= px < w - 1:
                    phase = (hue_base + base_phase + vi * 0.13) % 1.0
                    attr = _hue(1.0, phase, cp)
                    _safe(stdscr, py, px, "●", attr)

        _draw_wire(self._CUBE_V,  self._CUBE_E,  (ax, ay_, az),   0.0)
        _draw_wire(self._OCTA_V,  self._OCTA_E,  (oax, oay, oaz), 0.33)


# ═══════════════════════════════════════════════════════════════════════════
# GEOMETRIC 2: hypercube-fold — Rotating 4D tesseract projection
# ═══════════════════════════════════════════════════════════════════════════

class Legacy2HypercubePlugin(ThemePlugin):
    """4D hypercube (tesseract) projected to 2D through sequential 4D→3D→2D.

    6 independent rotation planes (XY, XZ, XW, YZ, YW, ZW) each spin at
    slightly different speeds.  The 4D→3D perspective projection and then
    3D→2D perspective projection produce the characteristic nested-cube
    morphing shape.  16 vertices, 32 edges.  Edge colour encodes which
    of the two 4D 'shells' (inner/outer cube) it belongs to.
    """
    name = "legacy-v2-hypercube-fold"

    def __init__(self):
        super().__init__()

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    @staticmethod
    def _rot4(verts4, planes):
        """Apply 6-plane 4D rotation to list of (x,y,z,w) vertices.
        planes: dict of {(i,j): angle} where i<j in {0,1,2,3}.
        """
        out = [list(v) for v in verts4]
        for (i, j), angle in planes.items():
            c, s = math.cos(angle), math.sin(angle)
            for v in out:
                vi, vj = v[i], v[j]
                v[i] =  c * vi - s * vj
                v[j] =  s * vi + c * vj
        return [tuple(v) for v in out]

    @staticmethod
    def _proj4to3(verts4, w_dist=2.5):
        """4D perspective projection: (x,y,z,w) → (x',y',z')."""
        return [(x / (w_dist - w), y / (w_dist - w), z / (w_dist - w))
                for x, y, z, w in verts4]

    @staticmethod
    def _proj3to2(verts3, cx, cy, scale, ay, z_dist=3.5):
        """3D perspective projection: (x,y,z) → (px,py)."""
        pts = []
        for x, y, z in verts3:
            dz = z_dist + z
            if abs(dz) < 0.1:
                dz = 0.1 if dz >= 0 else -0.1
            pts.append((
                int(cx + x * scale / dz),
                int(cy + y * scale / dz / ay),
                z,
            ))
        return pts

    @staticmethod
    def _line(x0, y0, x1, y1, w, h):
        dx = abs(x1-x0); sx = 1 if x0 < x1 else -1
        dy = -abs(y1-y0); sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        for _ in range(500):
            if 1 <= y < h - 1 and 0 <= x < w - 1:
                yield x, y
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy: err += dy; x += sx
            if e2 <= dx: err += dx; y += sy

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        cx_s, cy_s = w / 2.0, h / 2.0
        intensity = state.intensity_multiplier
        ay = 2.1

        cp          = color_pairs
        bright_attr = curses.color_pair(cp.get("bright", 1)) | curses.A_BOLD
        base_dim    = curses.color_pair(cp.get("base",   1)) | curses.A_DIM

        # Clear
        for y in range(1, h - 1):
            for x in range(0, w - 1):
                _safe(stdscr, y, x, " ", base_dim)

        # 16 hypercube vertices: all (±1,±1,±1,±1)
        verts4 = [(x, y, z, wv)
                  for x in (-1.0, 1.0)
                  for y in (-1.0, 1.0)
                  for z in (-1.0, 1.0)
                  for wv in (-1.0, 1.0)]

        # 32 edges: connect vertices that differ in exactly one coordinate
        edges = []
        for i in range(16):
            for j in range(i + 1, 16):
                diffs = sum(1 for k in range(4) if verts4[i][k] != verts4[j][k])
                if diffs == 1:
                    edges.append((i, j))

        # 6 rotation planes, each at a slightly different speed
        t = f * 0.018
        planes = {
            (0, 1): t * 0.70,
            (0, 2): t * 0.55,
            (0, 3): t * 1.10,
            (1, 2): t * 0.40,
            (1, 3): t * 0.85,
            (2, 3): t * 0.60,
        }

        rotated4 = self._rot4(verts4, planes)
        verts3   = self._proj4to3(rotated4, w_dist=2.8)
        scale    = min(w * 0.22, h * 0.44)
        pts      = self._proj3to2(verts3, cx_s, cy_s, scale, ay, z_dist=3.5)

        hue_base = (f * 0.004) % 1.0

        for ei, (a, b) in enumerate(edges):
            px0, py0, za = pts[a]
            px1, py1, zb = pts[b]
            avg_z = (za + zb) / 2.0
            depth = (avg_z + 2.0) / 4.0
            # Edges connecting w=-1 side (vertices 0-7) vs w=+1 (8-15)
            inner = (a < 8 and b < 8)
            outer = (a >= 8 and b >= 8)
            base_phase = 0.0 if inner else (0.33 if outer else 0.66)
            phase = (hue_base + base_phase + depth * 0.25) % 1.0
            ech   = "─" if inner else ("═" if outer else "·")
            attr  = _hue(depth, phase, cp)
            for lx, ly in self._line(px0, py0, px1, py1, w, h):
                _safe(stdscr, ly, lx, ech, attr)

        # Vertices
        vchars = ["◈", "◇", "◆", "○"]
        for vi, (px, py, z) in enumerate(pts):
            if 1 <= py < h - 1 and 0 <= px < w - 1:
                depth = (z + 2.0) / 4.0
                phase = (hue_base + vi * 0.0625) % 1.0
                attr  = _hue(depth, phase, cp)
                vch   = vchars[vi % len(vchars)]
                _safe(stdscr, py, px, vch, attr)


# ── Registration ──────────────────────────────────────────────────────────

register(Legacy2AsciiRainPlugin())
register(Legacy2SandAutomatonPlugin())
register(Legacy2AsciiRorschachPlugin())
register(Legacy2WireframeCubePlugin())
register(Legacy2HypercubePlugin())