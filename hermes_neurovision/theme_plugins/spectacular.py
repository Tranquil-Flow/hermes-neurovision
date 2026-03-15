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

from hermes_neurovision.plugin import ThemePlugin, Reaction, ReactiveElement, SpecialEffect
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

    Six overlapping sine waves summed to a smooth scalar field. Value selects
    both ASCII character (sparse → dense) AND the rainbow hue independently.
    Aurora curtains, bright plasma peaks, and self-referential warp distortion.

    v0.2 upgrade: reaction-diffusion Turing patterns, self-warp postfx,
    mirror_y aurora symmetry, full reactive event system, aurora-surge and
    color-storm special effects, frequency drift ambient, enhanced draw_extras
    with peaks, curtains, and horizon lines.
    """
    name = "plasma-rainbow"

    def __init__(self):
        super().__init__()
        # 6 wave frequencies — drift slowly during ambient_tick
        self._freqs = [7.0, 5.0, 4.0, 14.0, 9.0, 6.0]
        # which freq to drift next
        self._drift_idx = 0
        # palette state
        self._palette_state = "normal"
        # curtain phase for horizontal drift
        self._curtain_phase = 0.0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    # ── v0.2: Emergent system ─────────────────────────────────────────────────

    def reaction_diffusion_config(self):
        """Gray-Scott reaction-diffusion: Turing patterns on the plasma wave."""
        return {
            "feed": 0.042,
            "kill": 0.059,
            "update_interval": 2,
        }

    def emergent_layer(self):
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────

    def symmetry(self):
        """Mirror top/bottom like aurora reflecting in water."""
        return "mirror_y"

    def glow_radius(self):
        """Bright plasma peaks bloom outward."""
        return 2

    def echo_decay(self):
        """Plasma peaks leave brief aurora afterimages."""
        return 3

    def warp_field(self, x, y, w, h, frame, intensity):
        """Self-referential plasma warp: field warps itself."""
        xf = x / max(w, 1)
        yf = y / max(h, 1)
        t = frame * 0.035 * (1.0 + intensity * 0.8)
        # Compute local plasma value for self-warp
        v1 = math.sin(xf * self._freqs[0] + t)
        v2 = math.sin(yf * self._freqs[1] - t * 0.7)
        local_v = (v1 * 0.5 + v2 * 0.5 + 1.0) / 2.0
        amp = intensity * 2.5 * local_v
        wx = int(amp * math.sin(t * 1.3 + yf * 5.0))
        wy = int(amp * 0.5 * math.cos(t * 0.9 + xf * 4.0))
        nx = max(0, min(w - 1, x + wx))
        ny = max(0, min(h - 1, y + wy))
        return (nx, ny)

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────

    def intensity_curve(self, raw):
        """Power curve raw^0.5 — very sensitive, plasma always active."""
        return raw ** 0.5

    # ── v0.2: Reactive system ─────────────────────────────────────────────────

    def react(self, event_kind, data):
        cx, cy = 0.5, 0.5
        rng = random

        if event_kind == "agent_start":
            return Reaction(
                element=ReactiveElement.PULSE,
                intensity=0.9,
                origin=(cx, cy),
                color_key="bright",
                duration=2.5,
            )
        if event_kind == "llm_start":
            return Reaction(
                element=ReactiveElement.STREAM,
                intensity=0.85,
                origin=(0.0, cy),
                color_key="accent",
                duration=3.5,
                data={"direction": "horizontal"},
            )
        if event_kind == "llm_chunk":
            return Reaction(
                element=ReactiveElement.SPARK,
                intensity=0.45,
                origin=(rng.random(), rng.random()),
                color_key="bright",
                duration=0.6,
            )
        if event_kind == "llm_end":
            return Reaction(
                element=ReactiveElement.WAVE,
                intensity=0.7,
                origin=(cx, 0.0),
                color_key="soft",
                duration=2.0,
                data={"direction": "vertical"},
            )
        if event_kind == "tool_call":
            return Reaction(
                element=ReactiveElement.RIPPLE,
                intensity=0.75,
                origin=(rng.random(), rng.random()),
                color_key="accent",
                duration=1.8,
            )
        if event_kind == "tool_complete":
            return Reaction(
                element=ReactiveElement.RIPPLE,
                intensity=0.45,
                origin=(rng.random(), rng.random()),
                color_key="soft",
                duration=1.2,
            )
        if event_kind == "memory_save":
            return Reaction(
                element=ReactiveElement.BLOOM,
                intensity=0.8,
                origin=(cx, cy),
                color_key="bright",
                duration=2.5,
            )
        if event_kind == "skill_create":
            return Reaction(
                element=ReactiveElement.BLOOM,
                intensity=1.0,
                origin=(cx, cy),
                color_key="bright",
                duration=3.5,
                data={"maximal": True},
            )
        if event_kind == "error":
            return Reaction(
                element=ReactiveElement.SHATTER,
                intensity=1.0,
                origin=(rng.random(), rng.random()),
                color_key="warning",
                duration=2.0,
            )
        if event_kind == "agent_end":
            return Reaction(
                element=ReactiveElement.WAVE,
                intensity=0.6,
                origin=(cx, cy),
                color_key="soft",
                duration=2.5,
            )
        if event_kind == "context_pressure":
            return Reaction(
                element=ReactiveElement.GAUGE,
                intensity=data.get("level", 0.5),
                origin=(cx, cy),
                color_key="accent",
                duration=2.0,
            )
        if event_kind == "subagent_started":
            return Reaction(
                element=ReactiveElement.ORBIT,
                intensity=0.65,
                origin=(rng.random(), rng.random()),
                color_key="soft",
                duration=2.5,
            )
        if event_kind == "browser_navigate":
            return Reaction(
                element=ReactiveElement.TRAIL,
                intensity=0.6,
                origin=(0.0, rng.random()),
                color_key="accent",
                duration=2.0,
            )
        if event_kind == "reasoning_change":
            return Reaction(
                element=ReactiveElement.GLYPH,
                intensity=0.7,
                origin=(cx, cy),
                color_key="bright",
                duration=2.0,
            )
        if event_kind == "compression_started":
            return Reaction(
                element=ReactiveElement.WAVE,
                intensity=0.9,
                origin=(cx, cy),
                color_key="warning",
                duration=3.0,
                data={"compress": True},
            )
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────

    def palette_shift(self, trigger_effect, intensity, base_palette):
        if trigger_effect == "error":
            self._palette_state = "storm"
        elif trigger_effect == "skill_create":
            self._palette_state = "peak"
        elif trigger_effect == "llm_start":
            self._palette_state = "thinking"
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────

    def special_effects(self):
        return [
            SpecialEffect(
                name="aurora-surge",
                trigger_kinds=["burst", "llm_start"],
                min_intensity=0.4,
                cooldown=6.0,
                duration=4.0,
            ),
            SpecialEffect(
                name="color-storm",
                trigger_kinds=["error"],
                min_intensity=0.6,
                cooldown=8.0,
                duration=2.0,
            ),
        ]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        w, h = state.width, state.height
        _ensure_rainbow()

        if special_name == "aurora-surge":
            # Progressively densify the plasma render
            # At progress ~0.3 all chars become '#', then relaxes
            boost = math.sin(progress * math.pi)  # peaks in middle
            dense_chars = " ·.:;+=*%##▒▓"
            nc = len(dense_chars)
            f = state.frame
            speed = 1.0 + intensity * 2.0
            t = f * 0.035 * speed
            for y in range(1, h - 1):
                yf = y / max(h, 1)
                for x in range(0, w - 1):
                    xf = x / max(w, 1)
                    v1 = math.sin(xf * self._freqs[0] * (1 + boost) + t * 1.5)
                    v2 = math.sin(yf * self._freqs[1] * (1 + boost) - t * 0.9)
                    v3 = math.sin((xf + yf) * self._freqs[2] * (1 + boost) + t * 1.3)
                    dx2 = xf - 0.5
                    dy2 = (yf - 0.5) * 2.0
                    dist = math.sqrt(dx2*dx2 + dy2*dy2)
                    v4 = math.sin(dist * self._freqs[3] - t * 1.6)
                    v = (v1 * 0.3 + v2 * 0.25 + v3 * 0.25 + v4 * 0.2 + 1.0) / 2.0
                    v = min(1.0, v * (intensity + boost * 0.8))
                    ci = int(v * (nc - 1))
                    ch = dense_chars[ci]
                    angle = math.atan2(yf - 0.5, xf - 0.5)
                    pair = _rainbow_pair_angle(angle + f * 0.02)
                    bold = curses.A_BOLD if v > 0.6 else 0
                    _safe(stdscr, y, x, ch, pair | bold)

        elif special_name == "color-storm":
            # Rapid rainbow cycling across entire screen
            f = state.frame
            for y in range(1, h - 1):
                for x in range(0, w - 1):
                    hue_t = ((x + y + f * 8) % 60) / 60.0
                    pair = _rainbow_pair(hue_t)
                    ch = random.choice("▒▓#*+")
                    _safe(stdscr, y, x, ch, pair | curses.A_BOLD)

    # ── v0.2: Ambient tick ────────────────────────────────────────────────────

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        if idle_seconds > 2.0 and state.frame % 45 == 0:
            # One wave frequency drifts slightly each tick — slow morphing
            idx = self._drift_idx % len(self._freqs)
            self._freqs[idx] += random.uniform(-0.08, 0.08)
            # Keep frequencies in reasonable bounds
            self._freqs[idx] = max(2.0, min(20.0, self._freqs[idx]))
            self._drift_idx += 1

    # ── Enhanced draw_extras ──────────────────────────────────────────────────

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier
        _ensure_rainbow()

        chars = " ·.:;+=*%#▒▓"
        nc = len(chars)
        speed = 1.0 + intensity * 0.8
        t = f * 0.035 * speed

        # Advance curtain phase
        self._curtain_phase += 0.006

        for y in range(1, h - 1):
            yf = y / max(h, 1)
            for x in range(0, w - 1):
                xf = x / max(w, 1)

                # 6 independent waves using drifting frequencies
                f0, f1, f2, f3 = self._freqs[0], self._freqs[1], self._freqs[2], self._freqs[3]
                v1 = math.sin(xf * f0 + t)
                v2 = math.sin(yf * f1 - t * 0.7)
                v3 = math.sin((xf + yf) * f2 + t * 1.1)
                # Radial wave from centre
                dx2 = xf - 0.5
                dy2 = (yf - 0.5) * 2.0   # compensate terminal aspect
                dist = math.sqrt(dx2*dx2 + dy2*dy2)
                v4 = math.sin(dist * f3 - t * 1.4)
                # Two extra waves for richness
                v5 = math.sin(xf * self._freqs[4] - yf * self._freqs[5] + t * 0.6)
                v6 = math.sin((xf - yf) * 3.5 + t * 0.8)
                # Mix
                v = (v1*0.22 + v2*0.18 + v3*0.20 + v4*0.18 + v5*0.12 + v6*0.10 + 1.0) / 2.0

                # Aurora curtains: vertical bands drifting horizontally
                curtain = 0.5 + 0.5 * math.sin(xf * 8.0 + self._curtain_phase)
                v = v * (0.75 + 0.25 * curtain)

                v = max(0.0, min(1.0, v * intensity))

                # Char by density
                ci = int(v * (nc - 1))
                ch = chars[ci]

                # Bright peaks: plasma > 0.85 gets special char
                if v > 0.85:
                    ch = "✦" if (x + y + f) % 3 == 0 else "☼"

                # Hue — angle-based per-pixel for rainbow spread
                angle = math.atan2(yf - 0.5, xf - 0.5)
                hue_v = math.sin(xf * self._freqs[4] + yf * self._freqs[5] - t * 0.9 + 1.5)
                hue_t = (hue_v + 1.0) / 2.0
                # Blend angle-based with wave-based hue
                pair = _rainbow_pair_angle(angle + hue_t * math.tau * 0.5)

                bold = curses.A_BOLD if v > 0.7 else (curses.A_DIM if v < 0.25 else 0)
                _safe(stdscr, y, x, ch, pair | bold)

        # Horizon lines at top and bottom rows (mirror_y symmetry reflection)
        base_pair = _rainbow_pair(t * 0.1 % 1.0)
        for hx in range(0, w - 1):
            _safe(stdscr, 1, hx, "─", base_pair | curses.A_DIM)
            _safe(stdscr, h - 2, hx, "─", base_pair | curses.A_DIM)


register(PlasmaRainbowPlugin())


# ── 3. Fractal Zoom ───────────────────────────────────────────────────────────

class FractalZoomPlugin(ThemePlugin):
    """Mandelbrot set with continuous smooth zoom into boundary features.

    Uses a continuous float zoom parameter driven by frame so the animation
    never snaps between levels.  Zooms 8x into the target then crossfades
    (via a brief wide-view pause) to the next target location.
    Escape-time uses smooth iteration count for anti-banding.
    """
    name = "fractal-zoom"

    # (centre_re, centre_im, zoom_start, zoom_end, label)
    # zoom_start/end are the base-10 log of the view half-width
    _TARGETS = [
        (-0.7453, 0.1127,  0.5, -2.2),   # dendrite — classic spirals
        (-0.7269, 0.1889,  0.5, -2.4),   # seahorse valley
        (-0.2350, 0.8270,  0.5, -2.0),   # triple junction
        (-1.7491, 0.0001,  0.5, -2.1),   # period-doubling cascade
        ( 0.3600, 0.1000,  0.5, -2.3),   # mini-brot antenna
        (-0.5623, 0.6428,  0.5, -2.2),   # spiral arms
    ]

    # Duration in frames for each phase
    _ZOOM_FRAMES   = 360   # zoom in (continuous, one smooth sweep)
    _PAUSE_FRAMES  = 40    # brief wide-view pause before next target

    def __init__(self):
        self._target_idx = 0
        self._phase      = 0  # 0..ZOOM_FRAMES+PAUSE_FRAMES

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier
        _ensure_rainbow()

        cycle = self._ZOOM_FRAMES + self._PAUSE_FRAMES
        self._phase = f % cycle

        # Advance target at the start of each new cycle
        target_idx = (f // cycle) % len(self._TARGETS)
        cx_t, cy_t, log_start, log_end = self._TARGETS[target_idx][:4]

        if self._phase < self._ZOOM_FRAMES:
            # Smooth exponential zoom: t goes 0→1 over ZOOM_FRAMES
            t_zoom = self._phase / self._ZOOM_FRAMES
            # Ease in-out: slow start, slow end
            t_ease = t_zoom * t_zoom * (3.0 - 2.0 * t_zoom)
            log_w = log_start + (log_end - log_start) * t_ease
        else:
            # Pause: hold at the zoomed-out view briefly
            log_w = log_start

        half_w = 10.0 ** log_w
        aspect = (h / max(w, 1)) * 2.1  # terminal char aspect
        half_h = half_w * aspect

        re_min = cx_t - half_w
        re_max = cx_t + half_w
        im_min = cy_t - half_h
        im_max = cy_t + half_h

        # Iteration depth scales with zoom depth for detail preservation
        zoom_depth = max(0.0, (log_start - log_w) / (log_start - log_end + 0.001))
        max_iter = int(48 + zoom_depth * 140)

        base_dim = curses.color_pair(color_pairs.get("base", 0)) | curses.A_DIM

        for py in range(1, h - 1):
            for px in range(0, w - 1):
                c_re = re_min + (px / max(w - 2, 1)) * (re_max - re_min)
                c_im = im_min + (py / max(h - 2, 1)) * (im_max - im_min)

                # Mandelbrot — smooth (continuous) escape time for anti-banding
                z_re, z_im = 0.0, 0.0
                escaped = -1
                for i in range(max_iter):
                    zr2 = z_re * z_re
                    zi2 = z_im * z_im
                    if zr2 + zi2 > 4.0:
                        escaped = i
                        break
                    z_im = 2.0 * z_re * z_im + c_im
                    z_re = zr2 - zi2 + c_re

                if escaped < 0:
                    # Interior — black void
                    _safe(stdscr, py, px, " ", base_dim)
                    continue

                # Smooth iteration count (prevents banding)
                mod2 = z_re * z_re + z_im * z_im
                smooth = escaped - math.log2(max(math.log(max(mod2, 1e-10)), 1e-10))
                t = (smooth % max_iter) / max_iter

                # Animated hue: rotates at a speed that matches the zoom speed
                # so bands always appear to be flowing inward
                hue_t = (t * 4.0 - f * 0.012) % 1.0
                pair = _rainbow_pair(hue_t % 1.0)

                chars = " .·,:;+=*#▒▓█"
                ci = min(len(chars) - 1, int(t * len(chars)))
                ch = chars[ci]
                bold = curses.A_BOLD if t > 0.65 else 0
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
