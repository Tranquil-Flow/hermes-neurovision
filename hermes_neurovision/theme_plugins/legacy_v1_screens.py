"""Legacy v1 pre-v0.2-upgrade theme screens.

These are verbatim copies of 9 theme plugins extracted from git history,
preserved before they were upgraded to the v0.2 API (react(), emergent_config,
postfx overrides).  They are kept for reference, regression testing, and
visual comparison.

Registered under "legacy-*" names so they do not conflict with the v0.2 versions.

Sources:
  ascii_fields.py  @ HEAD (pre-upgrade, not yet committed)
  experimental.py  @ HEAD~1 (before the v0.2 upgrade commit)
  attractors.py    @ HEAD~1
  spectacular.py   @ HEAD~1
"""

from __future__ import annotations

import curses
import math
import random
from typing import List, Optional

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register

# Shared helpers imported from upgraded modules (the helpers themselves are
# unchanged by the v0.2 upgrade).
from hermes_neurovision.theme_plugins.ascii_fields import _hue_attr
from hermes_neurovision.theme_plugins.attractors import (
    _AttractorBase,
    _ensure_rainbow,
    _rainbow_pair,
    _rainbow_pair_angle,
    _density_char,
    _attr_by_density,
)


# ---------------------------------------------------------------------------
# _safe() helper (originally in spectacular.py)
# ---------------------------------------------------------------------------

def _safe(stdscr, y: int, x: int, ch: str, attr: int = 0) -> None:
    """Draw ch at (y, x) silently ignoring curses boundary errors."""
    try:
        stdscr.addstr(y, x, ch, attr)
    except curses.error:
        pass


# ===========================================================================
# 1. LegacySynapticPlasmaPlugin  (ascii_fields @ HEAD pre-upgrade)
# ===========================================================================

class LegacySynapticPlasmaPlugin(ThemePlugin):
    """Full-screen plasma interference pattern. (legacy v1)"""
    name = "legacy-synaptic-plasma"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        chars = " ·.:;+=*#%@"
        n = len(chars) - 1
        cx2 = w / 2.0
        cy2 = h / 2.0
        intensity = state.intensity_multiplier
        hue_base = (f * 0.0033) % 1.0

        for y in range(1, h - 1):
            dy = y - cy2
            for x in range(0, w - 1):
                dx = x - cx2
                dist = math.sqrt((dx * dx) / 2.0 + dy * dy)
                v = (
                    math.sin(x * 0.15 + f * 0.08)
                    + math.sin(y * 0.22 - f * 0.06)
                    + math.sin((x + y) * 0.10 + f * 0.04)
                    + math.sin(dist * 2.5 - f * 0.12)
                ) / 4.0
                v = (v + 1.0) / 2.0 * intensity
                v = max(0.0, min(1.0, v))
                ci = int(v * n)
                ch = chars[ci]
                phase = (hue_base + dist * 0.04) % 1.0
                attr = _hue_attr(v, phase, color_pairs)
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


# ===========================================================================
# 2. LegacyOraclePlugin  (ascii_fields @ HEAD pre-upgrade)
# ===========================================================================

class LegacyOraclePlugin(ThemePlugin):
    """Rotating vortex tunnel. (legacy v1)"""
    name = "legacy-oracle"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        chars = " ·.:oO@◎⊕"
        n = len(chars) - 1
        hw = w / 2.0
        hh = h / 2.0
        intensity = state.intensity_multiplier
        hue_base = (f * 0.004) % 1.0

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                nx = (x - hw) / max(hw, 1.0)
                ny = (y - hh) / max(hh, 1.0)
                dist = math.sqrt(nx * nx + ny * ny * 2.0)
                angle = math.atan2(ny, nx)
                twist = 4.5 + 2.0 * math.sin(f * 0.007)
                vortex = math.sin(dist * 8.0 + angle * twist - f * 0.09)
                tunnel = math.sin(1.0 / (dist * 1.2 + 0.06) * 8.0 - f * 0.18)
                v = max(0.0, min(1.0, (vortex * 0.6 + tunnel * 0.4 + 1.0) / 2.0))
                glow = max(0.0, 1.0 - dist * 3.0)
                v = min(1.0, v + glow * 0.4)
                v *= intensity
                ci = int(v * n)
                ch = chars[ci]
                phase = (hue_base + angle / (2 * math.pi) + dist * 0.06) % 1.0
                attr = _hue_attr(v, phase, color_pairs)
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

        # Bright center pip
        try:
            stdscr.addstr(
                h // 2, w // 2, "◎",
                curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
            )
        except curses.error:
            pass


# ===========================================================================
# 3. LegacyCellularCortexPlugin  (ascii_fields @ HEAD pre-upgrade)
# ===========================================================================

class LegacyCellularCortexPlugin(ThemePlugin):
    """Voronoi cells representing 6 agent modules. (legacy v1)"""
    name = "legacy-cellular-cortex"

    _MODULES = [
        ("memory",  0.18, 0.30, "∿"),
        ("model",   0.50, 0.22, "☿"),
        ("tools",   0.82, 0.30, "⚙"),
        ("cron",    0.22, 0.75, "⏱"),
        ("core",    0.50, 0.55, "◎"),
        ("aegis",   0.78, 0.75, "⚡"),
    ]

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        mods = self._MODULES

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                nx = x / max(w, 1)
                ny = y / max(h, 1)

                dists = []
                for i, (name, mx, my, icon) in enumerate(mods):
                    ddx = (nx - mx) * 1.5
                    ddy = ny - my
                    dists.append((ddx * ddx + ddy * ddy, i))
                dists.sort()
                d1, i1 = dists[0]
                d2, i2 = dists[1]
                edge_dist = math.sqrt(d2) - math.sqrt(d1)

                if edge_dist < 0.025:
                    pulse = abs(math.sin(f * 0.08 + i1 * 0.7))
                    border_chars = "│─╱╲┼"
                    bci = (i1 + i2) % len(border_chars)
                    ch = border_chars[bci]
                    phase = (f * 0.005 + (i1 + i2) * 0.17) % 1.0
                    attr = _hue_attr(pulse, phase, color_pairs)
                else:
                    name, mx, my, icon = mods[i1]
                    d_center = math.sqrt(d1)
                    ripple = (math.sin(d_center * 20.0 - f * 0.05) + 1.0) / 2.0
                    if ripple > 0.25:
                        ch = "·"
                        phase = (f * 0.004 + i1 * 0.16 + d_center * 0.1) % 1.0
                        attr = _hue_attr(ripple, phase, color_pairs)
                    else:
                        ch = " "
                        attr = curses.color_pair(color_pairs.get("base", 1)) | curses.A_DIM

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

        for i, (name, mx, my, icon) in enumerate(mods):
            pulse = 0.4 + 0.6 * abs(math.sin(f * 0.06 + i * 0.7))
            ax = int(mx * w)
            ay = int(my * h)
            if ay < 1:
                ay = 1
            if ay > h - 2:
                ay = h - 2
            ax = max(0, min(ax, w - 2))
            label = icon + name
            if pulse > 0.6:
                attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
            else:
                attr = curses.color_pair(color_pairs["accent"])
            try:
                stdscr.addstr(ay, ax, label, attr)
            except curses.error:
                pass


# ===========================================================================
# 4. LegacyLifeColonyPlugin  (ascii_fields @ HEAD pre-upgrade)
# ===========================================================================

class LegacyLifeColonyPlugin(ThemePlugin):
    """Conway's Game of Life. (legacy v1)"""
    name = "legacy-life-colony"

    def __init__(self):
        self._grid = None
        self._w = 0
        self._h = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init_grid(self, w, h, rng, density=0.30):
        self._w = w
        self._h = h
        size = w * h
        g = bytearray(size)
        for i in range(size):
            if rng.random() < density:
                g[i] = 1
        self._grid = g

    def _count_neighbors(self, g, x, y, w, h):
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % w
                ny = (y + dy) % h
                if g[ny * w + nx]:
                    count += 1
        return count

    def _step(self, w, h):
        g = self._grid
        new_g = bytearray(w * h)
        for y in range(h):
            for x in range(w):
                n = self._count_neighbors(g, x, y, w, h)
                alive = g[y * w + x]
                if alive:
                    new_g[y * w + x] = 1 if n in (2, 3) else 0
                else:
                    new_g[y * w + x] = 1 if n == 3 else 0
        self._grid = new_g

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        gw = max(4, w - 1)
        gh = max(4, h - 2)

        if self._grid is None or w != self._w or h != self._h:
            self._init_grid(gw, gh, state.rng)
            self._w = w
            self._h = h

        alive_count = sum(self._grid)
        total = gw * gh
        if state.frame % 500 == 0 and total > 0 and alive_count / total < 0.03:
            self._init_grid(gw, gh, state.rng, density=0.30)

        self._step(gw, gh)

        g = self._grid
        chars = "·:+*#@◈"
        bright_attr = curses.color_pair(color_pairs["bright"])
        soft_attr = curses.color_pair(color_pairs["soft"])
        base_attr = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        for y in range(1, h - 1):
            gy = y - 1
            if gy >= gh:
                continue
            for x in range(0, w - 1):
                gx = x
                if gx >= gw:
                    continue
                cell = g[gy * gw + gx]
                if cell:
                    n = self._count_neighbors(g, gx, gy, gw, gh)
                    ch = chars[min(n, len(chars) - 1)]
                    if (x + y) % 2 == 0:
                        attr = bright_attr
                    else:
                        attr = soft_attr
                else:
                    ch = " "
                    attr = base_attr
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


# ===========================================================================
# 5. LegacyPulseMatrixPlugin  (ascii_fields @ HEAD pre-upgrade)
# ===========================================================================

class LegacyPulseMatrixPlugin(ThemePlugin):
    """Full-screen compound interference dot matrix. (legacy v1)"""
    name = "legacy-pulse-matrix"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        intensity = state.intensity_multiplier
        chars = "·.:;+*#@●"
        n = len(chars) - 1
        cx2 = w / 2.0
        cy2 = h / 2.0

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                dx = (x - cx2) / max(cx2, 1.0)
                dy = (y - cy2) / max(cy2, 1.0)
                dist = math.sqrt(dx * dx + dy * dy)
                angle = math.atan2(dy, dx)
                w1 = math.sin(dist * 12.0 - f * 0.12)
                w2 = math.sin(dx * 8.0 + f * 0.065)
                w3 = math.sin(dy * 10.0 - f * 0.09)
                w4 = math.sin((dx + dy) * 7.0 + angle * 3.0 - f * 0.10)
                v = (w1 * 0.4 + w2 * 0.25 + w3 * 0.2 + w4 * 0.15 + 1.0) / 2.0
                v = max(0.0, min(1.0, v)) * intensity
                ci = int(v * n)
                ch = chars[ci]
                hue_base = (f * 0.0035) % 1.0
                phase = (hue_base + angle / (2 * math.pi) + dist * 0.05) % 1.0
                attr = _hue_attr(v, phase, color_pairs)
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


# ===========================================================================
# 6. LegacyBarnsleyFernPlugin  (experimental @ HEAD~1 pre-upgrade)
# ===========================================================================

class LegacyBarnsleyFernPlugin(ThemePlugin):
    """Iterated function system fractal (Barnsley Fern). (legacy v1)"""
    name = "legacy-barnsley-fern"

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
        self._accum = 0

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

        steps = int(1200 * (0.3 + intensity))
        px, py = self._px, self._py

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

        if self._accum > 300:
            self._accum = 0
            self._sys_idx = (self._sys_idx + 1) % len(self._ORDER)
            for row in grid:
                for xi in range(w):
                    row[xi] *= 0.4

        decay  = 0.984
        chars  = " ·.;+*@▓█"
        n_chars = len(chars)
        hue_base = (f * 0.0032) % 1.0

        for y in range(1, h - 1):
            row = grid[y]
            for x in range(0, w - 1):
                v = row[x] * decay
                row[x] = v
                idx = max(0, min(n_chars - 1, int(v * (n_chars - 1))))
                ch  = chars[idx]
                if v < 0.04:
                    attr = base_dim
                else:
                    phase = (hue_base + (h - y) / max(h, 1) * 0.5
                             + x / max(w, 1) * 0.15) % 1.0
                    if (v + phase) % 1.0 > 0.72:
                        attr = bright_attr
                    elif (v + phase) % 1.0 > 0.48:
                        attr = accent_attr
                    elif (v + phase) % 1.0 > 0.24:
                        attr = soft_attr
                    else:
                        attr = base_dim
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


# ===========================================================================
# 7. LegacyFlowFieldPlugin  (experimental @ HEAD~1 pre-upgrade)
# ===========================================================================

class LegacyFlowFieldPlugin(ThemePlugin):
    """Particles on a curl-noise vector field. (legacy v1)"""
    name = "legacy-flow-field"

    _MAX_PARTICLES = 200

    def __init__(self):
        self._trail: Optional[List[List[float]]] = None
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
        nx = x / max(w, 1)
        ny = y / max(h, 1)
        freq = 3.0
        psi1  = math.sin(nx * freq + t * 0.5) * math.cos(ny * freq * 1.3 - t * 0.3)
        psi2  = math.sin(nx * freq * 2.1 - t * 0.4 + 1.0) * math.cos(ny * freq * 0.8 + t * 0.6)
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

        target_n = int(60 + 140 * intensity)
        while len(self._particles) < min(target_n, self._MAX_PARTICLES):
            self._spawn_particle(w, h)

        live = []
        for p in self._particles:
            vx, vy = self._field(p["x"], p["y"], t, w, h)
            p["x"] += vx * p["speed"]
            p["y"] += vy * p["speed"] * 0.5
            p["life"] -= 1

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

        arrows = "←↖↑↗→↘↓↙"

        decay  = 0.90 - 0.05 * intensity
        for y in range(1, h - 1):
            row = trail[y]
            for x in range(0, w - 1):
                v = row[x] * decay
                row[x] = v

                if v > 0.08:
                    fchars = "·.:+*▓"
                    idx   = int(v * (len(fchars) - 1))
                    idx   = max(0, min(len(fchars) - 1, idx))
                    fvx, fvy = self._field(x, y, t, w, h)
                    fang  = math.atan2(fvy, fvx)
                    phase = (t * 0.08 + fang / (2 * math.pi) + v * 0.3) % 1.0
                    if (v + phase) % 1.0 > 0.72:
                        attr = bright_attr
                    elif (v + phase) % 1.0 > 0.48:
                        attr = accent_attr
                    else:
                        attr = soft_attr
                    try:
                        stdscr.addstr(y, x, fchars[idx], attr)
                    except curses.error:
                        pass
                elif (x % 5 == 2) and (y % 3 == 1):
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

        for p in self._particles:
            if p["life"] > 8:
                px, py = int(p["x"]), int(p["y"])
                if 1 <= py < h - 1 and 0 <= px < w - 1:
                    try:
                        stdscr.addstr(py, px, "●",
                                      color_map.get(p["color"], bright_attr))
                    except curses.error:
                        pass


# ===========================================================================
# 8. LegacyHalvorsenStarPlugin  (attractors @ HEAD~1 pre-upgrade)
# ===========================================================================

class LegacyHalvorsenStarPlugin(_AttractorBase):
    """Halvorsen cyclically symmetric attractor — three interlocking spiral arms. (legacy v1)"""
    name = "legacy-halvorsen-star"
    _DT = 0.005
    _A  = 1.4

    def _reset_trajectory(self):
        self._tx, self._ty, self._tz = -1.48, -1.51, 2.04

    def _setup_projection(self, w, h):
        self._ox = w / 2.0
        self._oy = h / 2.0
        self._sx = (w - 6) / 20.0
        self._sy = (h - 4) / 14.0

    def _step(self):
        x, y, z = self._tx, self._ty, self._tz
        dt = self._DT
        a = self._A
        dx = -a*x - 4*y - 4*z - y*y
        dy = -a*y - 4*z - 4*x - z*z
        dz = -a*z - 4*x - 4*y - x*x
        self._tx = x + dt * dx
        self._ty = y + dt * dy
        self._tz = z + dt * dz

    def _project(self):
        sx = int(self._ox + self._tx * self._sx)
        sy = int(self._oy - self._ty * self._sy)
        return sx, sy

    def _spatial_hue(self, x, y, w, h):
        angle = math.atan2(y - self._oy, (x - self._ox) * 0.5)
        return _rainbow_pair_angle(angle)


# ===========================================================================
# 9. LegacyPlasmaRainbowPlugin  (spectacular @ HEAD~1 pre-upgrade)
# ===========================================================================

class LegacyPlasmaRainbowPlugin(ThemePlugin):
    """Dense multi-harmonic plasma interference with rainbow hues. (legacy v1)"""
    name = "legacy-plasma-rainbow"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier
        _ensure_rainbow()

        chars = " ·.:;+=*%#▒▓"
        nc = len(chars)
        speed = 1.0 + intensity * 0.8
        t = f * 0.035 * speed

        for y in range(1, h - 1):
            yf = y / max(h, 1)
            for x in range(0, w - 1):
                xf = x / max(w, 1)
                v1 = math.sin(xf * 7.0 + t)
                v2 = math.sin(yf * 5.0 - t * 0.7)
                v3 = math.sin((xf + yf) * 4.0 + t * 1.1)
                dx = xf - 0.5
                dy = (yf - 0.5) * 2.0
                dist = math.sqrt(dx*dx + dy*dy)
                v4 = math.sin(dist * 14.0 - t * 1.4)
                v = (v1 * 0.3 + v2 * 0.25 + v3 * 0.25 + v4 * 0.2 + 1.0) / 2.0
                v = max(0.0, min(1.0, v * intensity))

                ci = int(v * (nc - 1))
                ch = chars[ci]

                hue_v = math.sin(xf * 9.0 + yf * 6.0 - t * 0.9 + 1.5)
                hue_t = (hue_v + 1.0) / 2.0
                pair = _rainbow_pair(hue_t)
                bold = curses.A_BOLD if v > 0.7 else (curses.A_DIM if v < 0.25 else 0)
                _safe(stdscr, y, x, ch, pair | bold)


# ===========================================================================
# Registration
# ===========================================================================

register(LegacySynapticPlasmaPlugin())
register(LegacyOraclePlugin())
register(LegacyCellularCortexPlugin())
register(LegacyLifeColonyPlugin())
register(LegacyPulseMatrixPlugin())
register(LegacyBarnsleyFernPlugin())
register(LegacyFlowFieldPlugin())
register(LegacyHalvorsenStarPlugin())
register(LegacyPlasmaRainbowPlugin())
