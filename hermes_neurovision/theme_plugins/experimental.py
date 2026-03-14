"""Experimental screens: novel visual ideas that push terminal rendering limits.

New themes (not replacing any existing ones):
  clifford-attractor — 2D strange attractor accumulated as density field
  barnsley-fern      — IFS random-iteration fractal, grows in real time
  flow-field         — curl-noise vector field with streaming particles
"""

from __future__ import annotations

import curses
import math
import random
from typing import List, Optional

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


# ── Clifford Attractor ─────────────────────────────────────────────────────────

class CliffordAttractorPlugin(ThemePlugin):
    """2D strange attractor: x'=sin(a·y)+c·cos(a·x), y'=sin(b·x)+d·cos(b·y).

    Parameters morph slowly between preset configurations, producing entirely
    different alien geometries every ~60 seconds.
    """
    name = "clifford-attractor"

    # (a, b, c, d) — each produces a completely different orbit shape
    _PRESETS = [
        (-1.4,  1.6,  1.0, 0.7),
        ( 1.5, -1.8,  1.6, 0.9),
        (-2.0,  1.5, -0.5, 0.6),
        ( 1.7,  1.7,  0.6, 1.2),
        (-1.7, -1.3, -0.1,-0.9),
        ( 1.1, -1.1,  2.2, 0.4),
    ]

    def __init__(self):
        self._grid: Optional[List[List[float]]] = None
        self._px = 0.0
        self._py = 0.0
        self._preset_idx = 0
        self._morph_t    = 0.0     # 0..1 interpolation between presets
        self._w = self._h = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init(self, w, h):
        self._grid  = [[0.0] * w for _ in range(h)]
        self._px = 0.1
        self._py = 0.1
        self._w, self._h = w, h

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame

        if self._grid is None or (w, h) != (self._w, self._h):
            self._init(w, h)

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        intensity = state.intensity_multiplier
        grid = self._grid

        # Morph between presets
        self._morph_t += 0.0005 + 0.0003 * intensity
        if self._morph_t >= 1.0:
            self._morph_t     = 0.0
            self._preset_idx  = (self._preset_idx + 1) % len(self._PRESETS)

        p0  = self._PRESETS[self._preset_idx]
        p1  = self._PRESETS[(self._preset_idx + 1) % len(self._PRESETS)]
        mt  = self._morph_t
        a, b, c, d = (p0[i] + (p1[i] - p0[i]) * mt for i in range(4))

        # Iterate attractor
        steps = int(800 * (0.4 + intensity))
        px, py = self._px, self._py
        # Attractor range ≈ [-3, 3] × [-3, 3]
        scale_x = (w - 2) / 6.0
        scale_y = (h - 2) / 6.0
        cx_f = w / 2.0
        cy_f = h / 2.0

        for _ in range(steps):
            nx = math.sin(a * py) + c * math.cos(a * px)
            ny = math.sin(b * px) + d * math.cos(b * py)
            px, py = nx, ny
            sx = int(cx_f + px * scale_x)
            sy = int(cy_f + py * scale_y)
            if 1 <= sy < h - 1 and 0 <= sx < w - 1:
                grid[sy][sx] = min(grid[sy][sx] + 0.06, 1.0)

        self._px, self._py = px, py

        # Decay and render
        decay  = 0.975 - 0.01 * intensity
        chars  = " \u00b7.,:;=+*#\u2593\u2588"
        n_chars = len(chars)

        for y in range(1, h - 1):
            row = grid[y]
            for x in range(0, w - 1):
                v = row[x] * decay
                row[x] = v
                idx = int(v * (n_chars - 1))
                idx = max(0, min(n_chars - 1, idx))
                ch  = chars[idx]
                if v > 0.75:
                    attr = bright_attr
                elif v > 0.40:
                    attr = accent_attr
                elif v > 0.15:
                    attr = soft_attr
                else:
                    attr = base_dim
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


register(CliffordAttractorPlugin())


# ── Barnsley Fern — IFS Random Iteration ──────────────────────────────────────

class BarnsleyFernPlugin(ThemePlugin):
    """Iterated function system fractal rendered via the random chaos game.

    Cycles through several IFS configurations (fern, maple leaf, tree, spiral)
    by slowly fading the old attractor and growing the new one.
    """
    name = "barnsley-fern"

    # Each IFS: list of (a,b,c,d,e,f,p) — affine transform + probability
    _SYSTEMS = {
        "fern": [
            ( 0.00,  0.00,  0.00,  0.16, 0.00, 0.00, 0.01),
            ( 0.85,  0.04, -0.04,  0.85, 0.00, 1.60, 0.85),
            ( 0.20, -0.26,  0.23,  0.22, 0.00, 1.60, 0.07),
            (-0.15,  0.28,  0.26,  0.24, 0.00, 0.44, 0.07),
        ],
        "maple": [
            ( 0.14,  0.01,  0.00,  0.51,-0.08,-1.31, 0.02),
            ( 0.43,  0.52, -0.45,  0.50, 1.49,-0.75, 0.40),
            ( 0.45, -0.49,  0.47,  0.47,-1.62,-0.74, 0.40),
            ( 0.49,  0.00,  0.00,  0.51, 0.02, 1.62, 0.18),
        ],
        "dragon": [
            ( 0.824074,  0.281482, -0.212346,  0.864198, -1.882290, -0.110607, 0.787473),
            (-0.077846,  0.125205, -0.268429, -0.063006,  0.785069,  0.170080, 0.212527),
        ],
        "spiral": [
            ( 0.787879, -0.424242,  0.242424,  0.859848, -0.985286, -0.115970, 0.895652),
            (-0.121212,  0.257576,  0.000000,  0.000000, -0.469286,  0.843217, 0.052174),
            ( 0.181818, -0.136364,  0.090909,  0.181818,  0.024323,  0.396423, 0.052174),
        ],
    }
    _ORDER = ["fern", "maple", "dragon", "spiral"]

    def __init__(self):
        self._grid: Optional[List[List[float]]] = None
        self._px    = 0.0
        self._py    = 0.0
        self._rng   = random.Random(99)
        self._sys_idx = 0
        self._w = self._h = 0
        self._accum = 0  # frames accumulating current system

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init(self, w, h):
        self._grid  = [[0.0] * w for _ in range(h)]
        self._px, self._py = 0.0, 0.0
        self._w, self._h = w, h

    def _pick_transform(self, transforms):
        r = self._rng.random()
        acc = 0.0
        for t in transforms:
            acc += t[6]
            if r < acc:
                return t
        return transforms[-1]

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame

        if self._grid is None or (w, h) != (self._w, self._h):
            self._init(w, h)

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        intensity = state.intensity_multiplier
        grid = self._grid

        sys_name   = self._ORDER[self._sys_idx]
        transforms = self._SYSTEMS[sys_name]

        # Run iterations: chaos game
        steps = int(1200 * (0.3 + intensity))
        px, py = self._px, self._py

        # Map IFS output (range ≈ [-3,3] × [-3,10]) to screen
        scale   = min(w, h * 2.5) / 12.0
        ox      = w / 2.0
        oy      = h - 2.0

        for _ in range(steps):
            a, b, c, d, e, fg_, _ = self._pick_transform(transforms)
            nx = a * px + b * py + e
            ny = c * px + d * py + fg_
            px, py = nx, ny
            sx = int(ox + px * scale)
            sy = int(oy - py * scale * 0.5)
            if 1 <= sy < h - 1 and 0 <= sx < w - 1:
                grid[sy][sx] = min(grid[sy][sx] + 0.04, 1.0)

        self._px, self._py = px, py
        self._accum += 1

        # Switch system after ~300 frames
        if self._accum > 300:
            self._accum = 0
            self._sys_idx = (self._sys_idx + 1) % len(self._ORDER)
            # Fade grid instead of clearing
            for row in grid:
                for xi in range(w):
                    row[xi] *= 0.4

        # Decay and render
        decay  = 0.984
        chars  = " \u00b7.;+*@\u2593\u2588"
        n_chars = len(chars)

        for y in range(1, h - 1):
            row = grid[y]
            for x in range(0, w - 1):
                v = row[x] * decay
                row[x] = v
                idx = max(0, min(n_chars - 1, int(v * (n_chars - 1))))
                ch  = chars[idx]
                if v > 0.7:
                    attr = bright_attr
                elif v > 0.35:
                    attr = accent_attr
                elif v > 0.12:
                    attr = soft_attr
                else:
                    attr = base_dim
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


register(BarnsleyFernPlugin())


# ── Flow Field — Curl Noise Particle Streams ──────────────────────────────────

class FlowFieldPlugin(ThemePlugin):
    """Particles ride a smoothly evolving curl-noise vector field.

    Each particle leaves a fading density trail. The field itself is rendered
    as subtle directional glyphs. Intensity drives particle count and trail life.
    """
    name = "flow-field"

    _MAX_PARTICLES = 200

    def __init__(self):
        self._trail: Optional[List[List[float]]] = None  # density grid
        self._particles: List[dict] = []
        self._rng  = random.Random(55)
        self._w = self._h = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init(self, w, h):
        self._trail = [[0.0] * w for _ in range(h)]
        self._particles = []
        for _ in range(80):
            self._spawn_particle(w, h)
        self._w, self._h = w, h

    def _spawn_particle(self, w, h):
        rng = self._rng
        self._particles.append({
            "x":    rng.uniform(0, w),
            "y":    rng.uniform(1, h - 1),
            "life": rng.randint(40, 120),
            "speed": rng.uniform(0.3, 0.9),
            "color": rng.choice(["bright", "accent", "soft"]),
        })

    def _field(self, x, y, t, w, h):
        """Curl-like noise field: vx, vy derived from overlapping sine waves."""
        nx = x / max(w, 1)
        ny = y / max(h, 1)
        # Potential function ψ(x,y,t) — curl gives (dψ/dy, -dψ/dx)
        freq = 3.0
        psi1  = math.sin(nx * freq + t * 0.5) * math.cos(ny * freq * 1.3 - t * 0.3)
        psi2  = math.sin(nx * freq * 2.1 - t * 0.4 + 1.0) * math.cos(ny * freq * 0.8 + t * 0.6)
        # Numerical curl approximation
        eps   = 0.01
        psi_dy = math.sin(nx * freq + t * 0.5) * (-math.sin((ny + eps) * freq * 1.3 - t * 0.3)) * freq * 1.3
        psi_dx = math.cos(nx * freq + t * 0.5) * freq * math.cos(ny * freq * 1.3 - t * 0.3)
        vx = (psi1 + psi2) * 0.5 + psi_dy * 0.3
        vy = -(psi_dx) * 0.3 + (psi1 - psi2) * 0.2
        return vx, vy

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame

        if self._trail is None or (w, h) != (self._w, self._h):
            self._init(w, h)

        intensity  = state.intensity_multiplier
        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        color_map   = {"bright": bright_attr, "accent": accent_attr, "soft": soft_attr}

        trail = self._trail
        t     = f * 0.02

        # Step particles
        target_n = int(60 + 140 * intensity)
        while len(self._particles) < min(target_n, self._MAX_PARTICLES):
            self._spawn_particle(w, h)

        live = []
        for p in self._particles:
            vx, vy = self._field(p["x"], p["y"], t, w, h)
            p["x"] += vx * p["speed"]
            p["y"] += vy * p["speed"] * 0.5  # terminal aspect
            p["life"] -= 1

            # Wrap
            if p["x"] < 0:
                p["x"] += w
            elif p["x"] >= w:
                p["x"] -= w
            if p["y"] < 1:
                p["y"] = 1.0
            elif p["y"] >= h - 1:
                p["y"] = float(h - 2)

            if p["life"] > 0:
                live.append(p)
                tx, ty = int(p["x"]), int(p["y"])
                if 1 <= ty < h - 1 and 0 <= tx < w - 1:
                    trail[ty][tx] = min(trail[ty][tx] + 0.35, 1.0)

        self._particles = live

        # Direction glyphs for field arrows (sampled every 5 cols, 3 rows)
        arrows = "\u2190\u2196\u2191\u2197\u2192\u2198\u2193\u2199"

        # Decay trail and render background
        decay  = 0.90 - 0.05 * intensity
        for y in range(1, h - 1):
            row = trail[y]
            for x in range(0, w - 1):
                v = row[x] * decay
                row[x] = v

                if v > 0.08:
                    chars = "\u00b7.:+*\u2593"
                    idx   = int(v * (len(chars) - 1))
                    idx   = max(0, min(len(chars) - 1, idx))
                    attr  = soft_attr if v < 0.4 else (accent_attr if v < 0.75 else bright_attr)
                    try:
                        stdscr.addstr(y, x, chars[idx], attr)
                    except curses.error:
                        pass
                elif (x % 5 == 2) and (y % 3 == 1):
                    # Field direction glyph
                    vx, vy = self._field(x, y, t, w, h)
                    ang   = math.atan2(vy, vx)
                    idx   = int((ang + math.pi) / (2 * math.pi) * 8) % 8
                    try:
                        stdscr.addstr(y, x, arrows[idx], base_dim)
                    except curses.error:
                        pass
                else:
                    try:
                        stdscr.addstr(y, x, " ", base_dim)
                    except curses.error:
                        pass

        # Bright particle heads
        for p in self._particles:
            if p["life"] > 8:
                px, py = int(p["x"]), int(p["y"])
                if 1 <= py < h - 1 and 0 <= px < w - 1:
                    try:
                        stdscr.addstr(py, px, "\u25cf",
                                      color_map.get(p["color"], bright_attr))
                    except curses.error:
                        pass


register(FlowFieldPlugin())
