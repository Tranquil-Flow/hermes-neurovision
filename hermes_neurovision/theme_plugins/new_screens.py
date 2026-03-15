"""Five new theme screens.

ASCII engine exploration (3):
  ascii-rain        -- Matrix-style columnar character rain with pooling glyphs
  sand-automaton    -- Falling-sand cellular automaton: gravity, bounce, erosion
  ascii-rorschach   -- Ink-blot bilaterally symmetric random growth + decay field

Geometric rotating objects (2):
  wireframe-cube    -- 3D wireframe cube + inner octahedron, both spinning
  hypercube-fold    -- Rotating 4D hypercube projected to 2D with depth coloring
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


def _hue(v: float, phase: float, cp: dict) -> int:
    s = (v + phase) % 1.0
    if s > 0.72:
        return curses.color_pair(cp.get("bright", 1)) | curses.A_BOLD
    elif s > 0.48:
        return curses.color_pair(cp.get("accent", 1))
    elif s > 0.24:
        return curses.color_pair(cp.get("soft", 1))
    return curses.color_pair(cp.get("base", 1)) | curses.A_DIM


# ═══════════════════════════════════════════════════════════════════════════
# ASCII ENGINE 1: ascii-rain — Columnar character rain
# ═══════════════════════════════════════════════════════════════════════════

class AsciiRainPlugin(ThemePlugin):
    """Matrix-style columnar rain with variable-speed streams, pooling at base.

    Each column maintains an independent falling head and a fading trail.
    Head characters are drawn from a wide Unicode katakana + symbol set.
    When a stream hits the bottom it pools into a spreading puddle of dim chars.
    Color travels down each trail so the head is bright and decays through
    accent → soft → base → gone.
    """
    name = "ascii-rain"

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

class SandAutomatonPlugin(ThemePlugin):
    """Falling-sand simulation: gravity, stacking, erosion, and rain seeding.

    Rules per tick:
      - Empty cell above a full cell: fall (swap)
      - Full cell on flat ground: stay
      - Full cell on slope: slide left/right with probability
    Sand rains in from the top and erodes from the bottom.  Color encodes
    age: fresh sand is bright, settled sand fades to base.
    """
    name = "sand-automaton"

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

class AsciiRorschachPlugin(ThemePlugin):
    """Procedural ink-blot: a density grid grows outward from random seeds,
    is mirrored across the vertical axis, and slowly evaporates.

    The growth rule: each cell's value is nudged toward the average of its
    neighbours plus a small noise term.  New ink seeds erupt periodically.
    Colors cycle through the hue helper so the blot shimmers between palette
    entries as it evolves.  Completely different from every other screen —
    no oscillations, no particles, just emergent diffusive growth + mirror.
    """
    name = "ascii-rorschach"

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

class WireframeCubePlugin(ThemePlugin):
    """3D wireframe cube rotating on all three axes simultaneously.

    An octahedron spins inside at a different rate.  Edges are drawn with
    Bresenham lines; depth is encoded in character density and color.
    Vertices are drawn as bright dots.  No external geometry library needed —
    pure 4x4 rotation matrix math inline.
    """
    name = "wireframe-cube"

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

class HypercubePlugin(ThemePlugin):
    """4D hypercube (tesseract) projected to 2D through sequential 4D→3D→2D.

    6 independent rotation planes (XY, XZ, XW, YZ, YW, ZW) each spin at
    slightly different speeds.  The 4D→3D perspective projection and then
    3D→2D perspective projection produce the characteristic nested-cube
    morphing shape.  16 vertices, 32 edges.  Edge colour encodes which
    of the two 4D 'shells' (inner/outer cube) it belongs to.
    """
    name = "hypercube-fold"

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

register(AsciiRainPlugin())
register(SandAutomatonPlugin())
register(AsciiRorschachPlugin())
register(WireframeCubePlugin())
register(HypercubePlugin())
