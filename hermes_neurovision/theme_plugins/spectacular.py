"""Spectacular generative screens — 5 themes pushing colour and geometry to the limit.

Themes:
  hypnotic-tunnel   — 3D rotating tunnel with per-ring rainbow hue
  plasma-rainbow    — dense multi-harmonic plasma with full HSV colour sweep
  fractal-zoom      — Mandelbrot boundary zoom with escape-time rainbow
  particle-vortex   — 800-particle dual vortex with spiral trails
  chladni-sand      — Sand-on-plate standing wave patterns (Chladni figures)
"""
from __future__ import annotations

import curses
import math
import random
from typing import List, Optional

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register
from hermes_neurovision.theme_plugins.attractors import (
    _ensure_rainbow, _rainbow_pair, _rainbow_pair_angle,
    _density_char, _attr_by_density, _R_PAIRS,
)


def _safe(stdscr, y: int, x: int, ch: str, attr: int = 0) -> None:
    try:
        stdscr.addstr(y, x, ch, attr)
    except curses.error:
        pass


# ── 1. Hypnotic Tunnel ────────────────────────────────────────────────────────

class HypnoticTunnelPlugin(ThemePlugin):
    """Infinite 3D rectangular tunnel receding to a vanishing point.

    Each column of the tunnel wall gets a different hue that rotates forward
    as the camera flies through.  Vertical position shifts hue — the combined
    effect is a full rotating rainbow kaleidoscope.

    Controls:
      - Frame drives the z-scroll (forward motion)
      - intensity_multiplier controls speed and tunnel twist
    """
    name = "hypnotic-tunnel"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier
        _ensure_rainbow()

        cx2 = w / 2.0
        cy2 = h / 2.0
        speed = 0.08 + 0.12 * intensity
        depth_offset = f * speed

        # Number of depth rings to draw — sparse so you see the 3D layers
        num_rings = 14
        chars_h = "─═━"
        chars_v = "│║┃"

        for ring in range(num_rings):
            # Depth: small ring = close, big ring = far
            # Rings scroll: as frame increases, nearer rings expand out of frame
            # We use modulo to give infinite loop
            raw_depth = (ring + depth_offset) % num_rings
            t = raw_depth / num_rings  # 0 = near, 1 = far horizon
            # t=0 is near (big), t=1 is far (tiny)
            scale = max(0.02, 1.0 - t * 0.97)
            rw = cx2 * scale * 2.0
            rh = cy2 * scale * 1.1
            # Center in screen
            x0 = int(cx2 - rw)
            x1 = int(cx2 + rw)
            y0 = int(cy2 - rh)
            y1 = int(cy2 + rh)

            # Rainbow hue: full spectrum cycle per tunnel revolution
            hue_t = ((ring / num_rings) + f * 0.015) % 1.0
            pair = _rainbow_pair(hue_t)
            bold = curses.A_BOLD if t < 0.5 else 0

            # Draw the four sides of this tunnel ring
            if 0 < y0 < h - 1 and 0 < y1 < h - 1 and 0 < x0 < w - 1 and 0 < x1 < w - 1:
                # Top and bottom horizontal
                for x in range(max(1, x0), min(w - 2, x1 + 1), 1):
                    ch = chars_h[ring % len(chars_h)]
                    if 1 <= y0:
                        _safe(stdscr, y0, x, ch, pair | bold)
                    if y1 < h - 1:
                        _safe(stdscr, y1, x, ch, pair | bold)
                # Left and right vertical
                for y in range(max(1, y0), min(h - 2, y1 + 1)):
                    ch = chars_v[ring % len(chars_v)]
                    if 1 <= x0:
                        _safe(stdscr, y, x0, ch, pair | bold)
                    if x1 < w - 1:
                        _safe(stdscr, y, x1, ch, pair | bold)
                # Corner accents
                for cy3, cx3 in [(y0, x0), (y0, x1), (y1, x0), (y1, x1)]:
                    if 1 <= cy3 < h - 1 and 1 <= cx3 < w - 1:
                        _safe(stdscr, cy3, cx3, "◈", pair | curses.A_BOLD)

        # Vanishing-point pip at dead centre
        bright = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        glyph = "◉" if f % 20 < 10 else "◎"
        _safe(stdscr, int(cy2), int(cx2), glyph, bright)


register(HypnoticTunnelPlugin())


# ── 2. Plasma Rainbow ─────────────────────────────────────────────────────────

class PlasmaRainbowPlugin(ThemePlugin):
    """Dense multi-harmonic plasma interference — every pixel gets its own rainbow hue.

    Four overlapping sine waves (frequency, phase, and direction all different)
    are summed to produce a smooth scalar field.  That value selects both
    the ASCII character (sparse → dense) AND the rainbow hue independently,
    so you get a swirling full-colour field that looks like liquid neon.

    Uses colour pairs 10-15 (rainbow) + the engine's 5 standard pairs.
    Agent intensity drives the speed and contrast of the interference.
    """
    name = "plasma-rainbow"

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
                # Four independent waves
                v1 = math.sin(xf * 7.0 + t)
                v2 = math.sin(yf * 5.0 - t * 0.7)
                v3 = math.sin((xf + yf) * 4.0 + t * 1.1)
                # Radial wave from centre
                dx = xf - 0.5
                dy = (yf - 0.5) * 2.0   # compensate terminal aspect
                dist = math.sqrt(dx*dx + dy*dy)
                v4 = math.sin(dist * 14.0 - t * 1.4)
                # Mix
                v = (v1 * 0.3 + v2 * 0.25 + v3 * 0.25 + v4 * 0.2 + 1.0) / 2.0
                v = max(0.0, min(1.0, v * intensity))

                # Char by density
                ci = int(v * (nc - 1))
                ch = chars[ci]

                # Hue — separate wave so colour and brightness are independent
                hue_v = math.sin(xf * 9.0 + yf * 6.0 - t * 0.9 + 1.5)
                hue_t = (hue_v + 1.0) / 2.0
                pair = _rainbow_pair(hue_t)
                bold = curses.A_BOLD if v > 0.7 else (curses.A_DIM if v < 0.25 else 0)
                _safe(stdscr, y, x, ch, pair | bold)


register(PlasmaRainbowPlugin())


# ── 3. Fractal Zoom ───────────────────────────────────────────────────────────

class FractalZoomPlugin(ThemePlugin):
    """Mandelbrot set rendered at multiple successive zoom levels.

    Slowly spirals into the boundary near the junction of the main cardioid
    and the period-2 bulb (c ≈ -0.75 + 0.1i) — the richest detail region.
    Escape-time mapped to rainbow hue; the set interior is filled black.

    One zoom pass every ~120 frames; zoom resets after 8 levels for variety.
    """
    name = "fractal-zoom"

    # Target region centres (different boundary features to explore)
    _TARGETS = [
        (-0.745, 0.113),   # classic dendrite
        (-0.722, 0.246),   # seahorse valley
        (-0.235, 0.827),   # triple junction
        (-1.749, 0.0),     # period-doubling cascade
        (0.360, 0.100),    # mini-brot antenna
    ]

    def __init__(self):
        self._zoom_level = 0
        self._target_idx = 0
        self._cx = -0.745
        self._cy = 0.113

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier
        _ensure_rainbow()

        # Zoom level increases over time; reset after 8 levels
        phase = f % 960           # 960 frames = full zoom sequence
        zoom_level = phase // 120  # 0..7, changes every 120 frames
        if zoom_level == 0 and phase < 5:
            # Advance to next target
            self._target_idx = (self._target_idx + 1) % len(self._TARGETS)
            self._cx, self._cy = self._TARGETS[self._target_idx]

        zoom = 3.5 / (1.5 ** zoom_level)
        # Window into complex plane
        re_min = self._cx - zoom * 1.5
        re_max = self._cx + zoom * 1.5
        im_min = self._cy - zoom * 0.7
        im_max = self._cy + zoom * 0.7

        max_iter = 32 + zoom_level * 12  # more detail as we zoom

        # Draw every pixel
        for py in range(1, h - 1):
            for px in range(0, w - 1):
                c_re = re_min + (px / max(w - 2, 1)) * (re_max - re_min)
                c_im = im_min + (py / max(h - 2, 1)) * (im_max - im_min)

                # Mandelbrot iteration
                z_re = c_re
                z_im = c_im
                escaped = 0
                for i in range(max_iter):
                    zr2 = z_re * z_re
                    zi2 = z_im * z_im
                    if zr2 + zi2 > 4.0:
                        escaped = i
                        break
                    z_im = 2.0 * z_re * z_im + c_im
                    z_re = zr2 - zi2 + c_re
                else:
                    # Interior of the set — black space
                    _safe(stdscr, py, px, " ",
                          curses.color_pair(color_pairs.get("base", 0)) | curses.A_DIM)
                    continue

                # Map escape iteration → char + rainbow colour
                t = escaped / max_iter
                # Animated hue rotation so it's always moving
                hue_t = (t * 3.0 + f * 0.008) % 1.0
                pair = _rainbow_pair(hue_t)
                chars = ".,:;+=*#▒▓"
                ci = min(len(chars) - 1, int(t * len(chars)))
                ch = chars[ci]
                bold = curses.A_BOLD if t > 0.6 else 0
                _safe(stdscr, py, px, ch, pair | bold)


register(FractalZoomPlugin())


# ── 4. Particle Vortex ────────────────────────────────────────────────────────

class ParticleVortexPlugin(ThemePlugin):
    """Two counter-rotating vortices with 400 particles each.

    Each particle orbits its vortex centre with a slowly decaying radius,
    leaving a fading density trail. When a particle reaches the vortex core
    it is re-spawned at a large random radius.

    Particle hue = angle in orbit, so each vortex paints a full rainbow spiral.
    The two vortices use opposite rotation directions for contrast.
    """
    name = "particle-vortex"

    _N = 350  # particles per vortex

    def __init__(self):
        self._particles_a: Optional[List] = None  # vortex A (CCW)
        self._particles_b: Optional[List] = None  # vortex B (CW)
        self._trail: Optional[List[List[float]]] = None
        self._w = self._h = 0
        self._rng = random.Random(42)

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _make_particle(self, cx, cy, rng, min_r=4.0, max_r=30.0):
        angle = rng.uniform(0, math.tau)
        r = rng.uniform(min_r, max_r)
        return [cx + math.cos(angle) * r * 2, cy + math.sin(angle) * r,
                r, angle]  # [x, y, radius, angle]

    def _init(self, w, h):
        rng = self._rng
        ax = w * 0.30
        bx = w * 0.70
        cy = h / 2.0
        self._particles_a = [self._make_particle(ax, cy, rng) for _ in range(self._N)]
        self._particles_b = [self._make_particle(bx, cy, rng) for _ in range(self._N)]
        self._trail = [[0.0] * w for _ in range(h)]
        self._w, self._h = w, h

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier
        _ensure_rainbow()

        if self._trail is None or (w, h) != (self._w, self._h):
            self._init(w, h)

        trail = self._trail
        rng = self._rng

        ax = w * 0.30
        bx = w * 0.70
        cy_f = h / 2.0

        # Rotation speed driven by intensity
        omega = 0.018 + 0.022 * intensity
        infall = 0.004 + 0.002 * intensity  # radius decay per frame

        for particles, cx_v, sign in [
            (self._particles_a, ax, +1.0),
            (self._particles_b, bx, -1.0),
        ]:
            for p in particles:
                px, py, r, angle = p
                # Orbit
                angle += sign * omega / max(r * 0.12, 0.4)
                r -= infall
                if r < 1.5:
                    # Re-spawn
                    angle = rng.uniform(0, math.tau)
                    r = rng.uniform(6.0, min(w * 0.25, h * 0.45))
                p[2] = r
                p[3] = angle
                p[0] = cx_v + math.cos(angle) * r * 2.1
                p[1] = cy_f + math.sin(angle) * r * 0.9
                # Deposit into trail
                tx, ty = int(p[0]), int(p[1])
                if 1 <= ty < h - 1 and 0 <= tx < w - 1:
                    trail[ty][tx] = min(trail[ty][tx] + 0.20, 1.0)

        # Decay trail and render
        decay = 0.88 - 0.04 * intensity
        for y in range(1, h - 1):
            row = trail[y]
            for x in range(w - 1):
                v = row[x] * decay
                row[x] = v
                if v < 0.04:
                    continue
                # Hue by angle from nearest vortex centre
                nx = x - (ax if x < w * 0.5 else bx)
                ny = (y - cy_f) * 2
                angle = math.atan2(ny, nx)
                pair = _rainbow_pair_angle(angle)
                ch = _density_char(v)
                bold = curses.A_BOLD if v > 0.55 else (curses.A_DIM if v < 0.20 else 0)
                _safe(stdscr, y, x, ch, pair | bold)

        # Bright particle heads
        for particles, cx_v, _ in [
            (self._particles_a, ax, None),
            (self._particles_b, bx, None),
        ]:
            for p in particles:
                tx, ty = int(p[0]), int(p[1])
                if 1 <= ty < h - 1 and 0 <= tx < w - 1:
                    angle = math.atan2(ty - cy_f, tx - cx_v)
                    pair = _rainbow_pair_angle(angle)
                    _safe(stdscr, ty, tx, "●", pair | curses.A_BOLD)

        # Vortex eye glyphs
        for cx_v in (ax, bx):
            _safe(stdscr, int(cy_f), int(cx_v), "◉",
                  curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD)


register(ParticleVortexPlugin())


# ── 5. Chladni Sand ───────────────────────────────────────────────────────────

class ChladniSandPlugin(ThemePlugin):
    """Chladni figures — sand collects at the nodes of standing wave vibration.

    A membrane vibrates at mode (m, n): z = cos(m·π·x)·cos(n·π·y).
    Sand accumulates where |z| < threshold (the nodal lines = standing wave nodes).
    Mode numbers cycle every ~180 frames, creating visually distinct patterns.

    Each mode gets a different rainbow hue so consecutive figures are fully distinct.
    The fade-in/fade-out between modes is smooth — sand dissolves then reforms.
    """
    name = "chladni-sand"

    # (m, n) mode pairs — each produces a unique Chladni figure
    _MODES = [
        (1, 2), (2, 1), (2, 3), (3, 2), (3, 4), (4, 3),
        (1, 4), (4, 1), (2, 5), (5, 2), (3, 5), (5, 3),
        (1, 6), (6, 1), (4, 5), (5, 4),
    ]

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier
        _ensure_rainbow()

        mode_period = 180
        mode_idx = (f // mode_period) % len(self._MODES)
        phase = f % mode_period
        m, n = self._MODES[mode_idx]

        # Cross-fade alpha: ease in for first 30 frames, hold, ease out for last 30
        if phase < 30:
            alpha = phase / 30.0
        elif phase > mode_period - 30:
            alpha = (mode_period - phase) / 30.0
        else:
            alpha = 1.0

        # This mode's hue — one of the 6 rainbow slots
        base_hue = (mode_idx / len(self._MODES))

        # Nodal threshold — lower = thinner lines = more complex pattern
        threshold = 0.12 + 0.06 * math.sin(f * 0.01)

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                # Normalise to [0, 1]
                xn = x / max(w - 1, 1)
                yn = y / max(h - 1, 1)

                # Chladni standing wave
                zx = math.cos(m * math.pi * xn)
                zy = math.cos(n * math.pi * yn)
                z = zx * zy

                # Near nodal line?
                near = abs(z) < threshold

                if near:
                    # Sand grain at node
                    density = 1.0 - abs(z) / threshold  # 1 at exact node, 0 at edge
                    density *= alpha * intensity

                    # Hue: base hue + slight variation by position
                    hue_t = (base_hue + abs(z) * 0.3 + xn * 0.1) % 1.0
                    pair = _rainbow_pair(hue_t)

                    # Sand chars — grainy texture
                    chars = "·:;+*#▒▓"
                    ci = int(density * (len(chars) - 1))
                    ch = chars[max(0, min(len(chars) - 1, ci))]
                    bold = curses.A_BOLD if density > 0.7 else 0
                    _safe(stdscr, y, x, ch, pair | bold)
                else:
                    # Empty plate interior — dimly show the plate
                    v = abs(z)
                    if v > 0.8:
                        _safe(stdscr, y, x, " ",
                              curses.color_pair(color_pairs.get("base", 0)) | curses.A_DIM)

        # Mode label in top-right
        label = f"m={m} n={n}"
        lx = max(0, w - len(label) - 3)
        if h > 4:
            pair = _rainbow_pair(base_hue)
            _safe(stdscr, 1, lx, label, pair | curses.A_BOLD)


register(ChladniSandPlugin())
