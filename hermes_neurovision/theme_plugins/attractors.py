"""Strange attractor themes — 4 continuous 3D ODE systems rendered as density fields.

Each attractor integrates a differential equation trajectory, accumulates a density
grid where the orbit visits, and renders with per-pixel rainbow coloring.

Themes:
  lorenz-butterfly  — the iconic butterfly (sigma=10, rho=28, beta=8/3)
  rossler-ribbon    — flat coil with vertical spike (a=0.2, b=0.2, c=5.7)
  halvorsen-star    — 3-fold symmetric triple spiral (a=1.4)
  aizawa-torus      — toroidal attractor with alien geometry
"""
from __future__ import annotations

import curses
import math
import random
from typing import List, Optional

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


# ── Rainbow colour helpers ───────────────────────────────────────────────────
# We claim curses colour pairs 10-15 for R,Y,G,C,B,M.
# They are outside the 5 pairs managed by the renderer so they never collide.

_RAINBOW_PAIRS_READY = False

def _ensure_rainbow():
    global _RAINBOW_PAIRS_READY
    if _RAINBOW_PAIRS_READY:
        return
    try:
        for i, c in enumerate([
            curses.COLOR_RED,
            curses.COLOR_YELLOW,
            curses.COLOR_GREEN,
            curses.COLOR_CYAN,
            curses.COLOR_BLUE,
            curses.COLOR_MAGENTA,
        ]):
            curses.init_pair(10 + i, c, -1)
        _RAINBOW_PAIRS_READY = True
    except Exception:
        pass

# 6-stop rainbow: Red Yellow Green Cyan Blue Magenta
_R_PAIRS = [10, 11, 12, 13, 14, 15]  # pair IDs

def _rainbow_pair(t: float) -> int:
    """t in [0,1] → one of 6 rainbow pair IDs."""
    idx = int(t * 6) % 6
    return curses.color_pair(_R_PAIRS[idx])

def _rainbow_pair_angle(a: float) -> int:
    """a in radians → rainbow pair (full circle = full spectrum)."""
    t = (a % math.tau) / math.tau
    return _rainbow_pair(t)

def _density_char(v: float) -> str:
    """Density v in [0,1] → character from sparse to dense."""
    chars = " ·.,:;=+*#▒▓█"
    idx = int(v * (len(chars) - 1))
    return chars[max(0, min(len(chars) - 1, idx))]

def _attr_by_density(v: float) -> int:
    if v > 0.75:
        return curses.A_BOLD
    if v > 0.40:
        return 0
    return curses.A_DIM


# ── Base class for density-field attractors ──────────────────────────────────

class _AttractorBase(ThemePlugin):
    """Shared infrastructure for 3D ODE density-field themes."""

    def __init__(self):
        self._grid: Optional[List[List[float]]] = None
        self._w = self._h = 0
        self._ox = self._oy = self._sx = self._sy = 1.0
        # Trajectory state — subclass sets initial point
        self._tx = 0.1
        self._ty = 0.0
        self._tz = 0.1

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _setup(self, w: int, h: int) -> None:
        """Called on first use or resize."""
        self._grid = [[0.0] * w for _ in range(h)]
        self._w, self._h = w, h
        self._setup_projection(w, h)
        self._reset_trajectory()
        # Warm up trajectory (skip transient); reset if diverged
        for _ in range(3000):
            self._step()
            if not (math.isfinite(self._tx) and math.isfinite(self._ty)
                    and math.isfinite(self._tz)):
                self._reset_trajectory()

    def _setup_projection(self, w: int, h: int) -> None:
        """Override to set _ox, _oy (offsets) and _sx, _sy (scales)."""
        raise NotImplementedError

    def _reset_trajectory(self) -> None:
        """Reset to a known-good initial point. Override in each subclass."""
        self._tx, self._ty, self._tz = 0.1, 0.0, 0.1

    def _step(self) -> None:
        """Advance trajectory one Euler step; update self._tx/_ty/_tz."""
        raise NotImplementedError

    def _project(self) -> tuple:
        """Return (screen_x, screen_y) for current trajectory position."""
        raise NotImplementedError

    def _is_valid(self) -> bool:
        """True if trajectory is finite (not NaN/inf)."""
        return (math.isfinite(self._tx) and math.isfinite(self._ty)
                and math.isfinite(self._tz))

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height

        if self._grid is None or (w, h) != (self._w, self._h):
            self._setup(w, h)

        _ensure_rainbow()
        grid = self._grid
        intensity = state.intensity_multiplier

        # Iterate trajectory and deposit density
        n_steps = int(600 * (0.5 + intensity))
        for _ in range(n_steps):
            self._step()
            # Guard against divergence — reset to known-good point and skip frame
            if not self._is_valid():
                self._reset_trajectory()
                continue
            sx, sy = self._project()
            if 1 <= sy < h - 1 and 0 <= sx < w - 1:
                grid[sy][sx] = min(grid[sy][sx] + 0.04, 1.0)

        # Decay
        decay = 0.977 - 0.008 * intensity
        for y in range(1, h - 1):
            row = grid[y]
            for x in range(w - 1):
                v = row[x] * decay
                row[x] = v
                if v < 0.01:
                    continue
                ch = _density_char(v)
                attr = _attr_by_density(v)
                # Hue from pre-accumulated spatial info or on-the-fly
                hue_pair = self._spatial_hue(x, y, w, h)
                try:
                    stdscr.addstr(y, x, ch, hue_pair | attr)
                except curses.error:
                    pass

    def _spatial_hue(self, x: int, y: int, w: int, h: int) -> int:
        """Override to give position-based rainbow colour."""
        return _rainbow_pair(x / max(w, 1))


# ── Lorenz Butterfly ──────────────────────────────────────────────────────────

class LorenzButterflyPlugin(_AttractorBase):
    """The classic Lorenz attractor — butterfly shape in X-Z projection.

    Parameters: sigma=10, rho=28, beta=8/3.
    Hue mapped to X position so left wing glows red-yellow, right wing blue-violet.
    """
    name = "lorenz-butterfly"
    _DT = 0.006   # conservative dt — Lorenz is chaotic but bounded
    _SIGMA = 10.0
    _RHO   = 28.0
    _BETA  = 8.0 / 3.0
    # X range ~[-20,20], Z range ~[0,50]

    def _reset_trajectory(self):
        self._tx, self._ty, self._tz = 1.0, 0.0, 15.0

    def _setup_projection(self, w, h):
        # Map X ∈ [-22,22] → [0, w-1],  Z ∈ [-2, 52] → [h-2, 1]
        self._ox = w / 2.0
        self._oy = (h - 2) + 2.0 * (h / 54.0)  # Z=0 at bottom
        self._sx = (w - 4) / 44.0
        self._sy = (h - 3) / 54.0

    def _step(self):
        x, y, z = self._tx, self._ty, self._tz
        dt = self._DT
        dx = self._SIGMA * (y - x)
        dy = x * (self._RHO - z) - y
        dz = x * y - self._BETA * z
        self._tx = x + dt * dx
        self._ty = y + dt * dy
        self._tz = z + dt * dz

    def _project(self):
        sx = int(self._ox + self._tx * self._sx)
        sy = int(self._oy - self._tz * self._sy)   # Z↑ = y↓
        return sx, sy

    def _spatial_hue(self, x, y, w, h):
        # Hue sweeps full spectrum left→right across screen
        return _rainbow_pair(x / max(w - 1, 1))


register(LorenzButterflyPlugin())


# ── Rössler Ribbon ────────────────────────────────────────────────────────────

class RosslerRibbonPlugin(_AttractorBase):
    """Rössler attractor — a flat coil that occasionally fires a vertical spike.

    Parameters: a=0.2, b=0.2, c=5.7.  X-Y projection shows the characteristic
    spiral; hue mapped to angle-from-centre for a full-spectrum colour wheel.
    """
    name = "rossler-ribbon"
    _DT = 0.015  # reduced from 0.02 — spike region can be stiff
    _A  = 0.2
    _B  = 0.2
    _C  = 5.7
    # X,Y range ~[-12, 12]

    def _reset_trajectory(self):
        self._tx, self._ty, self._tz = 0.1, 0.0, 0.0

    def _setup_projection(self, w, h):
        self._ox = w / 2.0
        self._oy = h / 2.0
        self._sx = (w - 6) / 24.0
        self._sy = (h - 4) / 22.0

    def _step(self):
        x, y, z = self._tx, self._ty, self._tz
        dt = self._DT
        dx = -y - z
        dy = x + self._A * y
        dz = self._B + z * (x - self._C)
        self._tx = x + dt * dx
        self._ty = y + dt * dy
        self._tz = z + dt * dz

    def _project(self):
        sx = int(self._ox + self._tx * self._sx)
        sy = int(self._oy - self._ty * self._sy)
        return sx, sy

    def _spatial_hue(self, x, y, w, h):
        # Hue = angle from screen centre → full rainbow colour wheel
        angle = math.atan2(y - self._oy, x - self._ox)
        return _rainbow_pair_angle(angle)


register(RosslerRibbonPlugin())


# ── Halvorsen Star ────────────────────────────────────────────────────────────

class HalvorsenStarPlugin(_AttractorBase):
    """Halvorsen cyclically symmetric attractor — three interlocking spiral arms.

    dx/dt = -a·x - 4y - 4z - y²
    dy/dt = -a·y - 4z - 4x - z²
    dz/dt = -a·z - 4x - 4y - x²   (a=1.4)

    3-fold symmetry naturally divides the colour wheel into thirds:
    120° = red-yellow, 120° = green-cyan, 120° = blue-magenta.
    """
    name = "halvorsen-star"
    _DT = 0.005  # halved — Halvorsen has y² and z² terms that blow up with large dt
    _A  = 1.4

    def _reset_trajectory(self):
        # Verified on-attractor starting point (avoids transient divergence)
        self._tx, self._ty, self._tz = -1.48, -1.51, 2.04

    def _setup_projection(self, w, h):
        self._ox = w / 2.0
        self._oy = h / 2.0
        # Range roughly ±10 for X,Y
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
        # Hue by angle — three arms each get their own colour sector
        angle = math.atan2(y - self._oy, (x - self._ox) * 0.5)
        return _rainbow_pair_angle(angle)


register(HalvorsenStarPlugin())


# ── Aizawa Torus ──────────────────────────────────────────────────────────────

class AizawaTorusPlugin(_AttractorBase):
    """Aizawa attractor — a toroidal structure with alien geometry.

    dx/dt = (z-b)·x - d·y
    dy/dt = d·x + (z-b)·y
    dz/dt = c + a·z - z³/3 - (x²+y²)·(1+e·z) + f·z·x³

    a=0.95, b=0.7, c=0.6, d=3.5, e=0.25, f=0.1

    Projected onto X-Z for the donut silhouette.  Hue by vertical position
    (top violet → bottom red) making a chromatic stack of orbital bands.
    """
    name = "aizawa-torus"
    _DT = 0.015  # conservative — cubic z term can spike
    _A = 0.95
    _B = 0.7
    _C = 0.6
    _D = 3.5
    _E = 0.25
    _F = 0.1
    # X range ~[-1.5,1.5], Z range ~[-0.5,1.5]

    def _reset_trajectory(self):
        self._tx, self._ty, self._tz = 0.1, 0.0, 0.5

    def _setup_projection(self, w, h):
        self._ox = w / 2.0
        self._oy = h / 2.0
        self._sx = (w - 6) / 3.2
        self._sy = (h - 4) / 2.2

    def _step(self):
        x, y, z = self._tx, self._ty, self._tz
        dt = self._DT
        a, b, c, d, e, f = self._A, self._B, self._C, self._D, self._E, self._F
        dx = (z - b) * x - d * y
        dy = d * x + (z - b) * y
        r2 = x*x + y*y
        dz = c + a*z - z*z*z/3.0 - r2*(1.0 + e*z) + f*z*x*x*x
        self._tx = x + dt * dx
        self._ty = y + dt * dy
        self._tz = z + dt * dz

    def _project(self):
        # X horizontal, Z vertical (inverted so high Z = top of screen)
        sx = int(self._ox + self._tx * self._sx)
        sy = int(self._oy - self._tz * self._sy)
        return sx, sy

    def _spatial_hue(self, x, y, w, h):
        # Vertical gradient: top rows = violet/blue, bottom = red/yellow
        t = 1.0 - (y - 1) / max(h - 3, 1)
        return _rainbow_pair(t)


register(AizawaTorusPlugin())


# ── Thomas Labyrinth ──────────────────────────────────────────────────────────

class ThomasLabyrinthPlugin(_AttractorBase):
    """Thomas' cyclically symmetric attractor — labyrinthine space-filling maze.

    dx/dt = sin(y) - b·x
    dy/dt = sin(z) - b·y
    dz/dt = sin(x) - b·z    (b=0.208186 — edge of chaos)

    Unlike the other attractors, this one fills 3D space with a web of tubes.
    Projected onto a tilted plane (x+y, z) to see the labyrinthine cross-section.
    Hue by diagonal position for a sweeping rainbow diagonal.
    """
    name = "thomas-labyrinth"
    _DT  = 0.04  # reduced from 0.05 — sin(x) terms well-behaved but cautious
    _B   = 0.208186

    def _reset_trajectory(self):
        self._tx, self._ty, self._tz = 0.1, 0.0, -0.1

    def _setup_projection(self, w, h):
        self._ox = w / 2.0
        self._oy = h / 2.0
        # Range roughly ±5 for all axes; project onto (x+y)/√2, z
        self._sx = (w - 6) / 14.0
        self._sy = (h - 4) / 10.0

    def _step(self):
        x, y, z = self._tx, self._ty, self._tz
        b = self._B
        dt = self._DT
        dx = math.sin(y) - b * x
        dy = math.sin(z) - b * y
        dz = math.sin(x) - b * z
        self._tx = x + dt * dx
        self._ty = y + dt * dy
        self._tz = z + dt * dz

    def _project(self):
        # Tilted projection: horizontal = (x+y)/√2, vertical = z
        px = (self._tx + self._ty) * 0.7071
        pz = self._tz
        sx = int(self._ox + px * self._sx)
        sy = int(self._oy - pz * self._sy)
        return sx, sy

    def _spatial_hue(self, x, y, w, h):
        # Diagonal rainbow: top-left = red, bottom-right = magenta
        t = (x / max(w - 1, 1) + (1.0 - y / max(h - 1, 1))) * 0.5
        return _rainbow_pair(t)


register(ThomasLabyrinthPlugin())
