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

from hermes_neurovision.plugin import ThemePlugin, Reaction, ReactiveElement, SpecialEffect
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


    # ── v0.2: Emergent system ─────────────────────────────────────────────────

    def emergent_layer(self):
        return "background"

    def neural_field_config(self):
        """Neural field excitations at butterfly density maxima."""
        return {"threshold": 2, "fire_duration": 3, "refractory": 5}

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────

    def echo_decay(self):
        """Butterfly trails linger for 5 frames."""
        return 5

    def glow_radius(self):
        return 1

    def symmetry(self):
        return None

    def depth_layers(self):
        return 3

    def decay_sequence(self):
        return "▓▒░·."

    def warp_field(self, x, y, w, h, frame, intensity):
        """Saddle-point instability warp — strongest at the centre transition between lobes."""
        xf = x / max(w, 1) - 0.5
        yf = y / max(h, 1) - 0.5
        # Gaussian peak at center (saddle transition zone between the two lobes)
        gauss = math.exp(-(xf * xf * 16.0 + yf * yf * 16.0))
        t = frame * 0.04
        amp = intensity * 2.0 * gauss
        wx = int(amp * math.sin(t + yf * 0.2 * math.tau))
        wy = int(amp * 0.5 * math.cos(t * 0.85 + xf * 5.0))
        nx = max(0, min(w - 1, x + wx))
        ny = max(0, min(h - 1, y + wy))
        return (nx, ny)

    def force_points(self, w, h, frame, intensity):
        """2 vortex attractors at the two lobe centres (x ±25%, y at lobe centroid)."""
        cx = w / 2.0
        cy = h * 0.40
        lobe_x = w * 0.25
        strength = 0.35 + intensity * 0.35
        return [
            {"x": int(cx - lobe_x), "y": int(cy),
             "strength": strength, "type": "vortex"},
            {"x": int(cx + lobe_x), "y": int(cy),
             "strength": strength, "type": "vortex"},
        ]

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────

    def intensity_curve(self, raw):
        return raw ** 0.8

    # ── v0.2: Reactive system ─────────────────────────────────────────────────

    def react(self, event_kind, data):
        cx, cy = 0.5, 0.5
        rng = random
        # Left lobe ≈ x=0.25, right lobe ≈ x=0.75; lobes sit in upper half
        left_lobe  = (0.25, 0.40)
        right_lobe = (0.75, 0.40)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.9,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "agent_end":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.5,
                            origin=(cx, cy), color_key="soft", duration=2.0)
        if event_kind == "llm_start":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.8,
                            origin=(0.0, cy), color_key="accent", duration=3.5,
                            data={"direction": "horizontal"})
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.4,
                            origin=(rng.random(), rng.random()),
                            color_key="bright", duration=0.5)
        if event_kind == "llm_end":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.65,
                            origin=(cx, cy), color_key="soft", duration=1.8)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.65,
                            origin=(rng.random(), rng.random()),
                            color_key="accent", duration=1.5)
        if event_kind == "tool_complete":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.45,
                            origin=(rng.random(), rng.random()),
                            color_key="soft", duration=1.2)
        if event_kind == "mcp_tool_call":
            lobe = rng.choice([left_lobe, right_lobe])
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.55,
                            origin=lobe, color_key="accent", duration=1.4)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.75,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "skill_create":
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                            origin=(cx, cy), color_key="bright", duration=3.5,
                            data={"maximal": True})
        if event_kind == "error":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                            origin=(rng.random(), rng.random()),
                            color_key="warning", duration=2.0)
        if event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                            origin=(cx, cy), color_key="warning", duration=3.0)
        if event_kind == "cron_tick":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.50,
                            origin=left_lobe, color_key="soft", duration=2.0)
        if event_kind == "background_proc":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.3,
                            origin=(rng.random(), rng.random()),
                            color_key="base", duration=0.8)
        if event_kind == "subagent_started":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.65,
                            origin=right_lobe, color_key="soft", duration=2.5)
        if event_kind == "context_pressure":
            return Reaction(element=ReactiveElement.GAUGE,
                            intensity=data.get("level", 0.5),
                            origin=(cx, cy), color_key="accent", duration=2.0)
        if event_kind == "token_usage":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.25,
                            origin=(rng.random(), rng.random()),
                            color_key="base", duration=0.6)
        if event_kind == "dangerous_cmd":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.9,
                            origin=(cx, cy), color_key="warning", duration=1.5)
        if event_kind == "approval_request":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.7,
                            origin=(cx, cy), color_key="warning", duration=2.0)
        if event_kind == "compression_started":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.8,
                            origin=(cx, cy), color_key="accent", duration=3.0)
        if event_kind == "reasoning_change":
            return Reaction(element=ReactiveElement.GLYPH, intensity=0.7,
                            origin=(cx, cy), color_key="accent", duration=2.0,
                            data={"bifurcation": True})
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────

    def palette_shift(self, trigger_effect, intensity, base_palette):
        if trigger_effect == "error":
            # Chaotic divergence — red/yellow alarm colours
            self._palette_state = "error"
        elif trigger_effect == "skill_create":
            # Strange attractor peak — white/cyan clarity
            self._palette_state = "skill"
        elif trigger_effect == "agent_start":
            self._palette_state = "bright"
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────

    def special_effects(self):
        return [
            SpecialEffect(name="butterfly-effect", trigger_kinds=["burst"],
                          min_intensity=0.3, cooldown=5.0, duration=3.0),
            SpecialEffect(name="bifurcation",
                          trigger_kinds=["error", "crash"],
                          min_intensity=0.5, cooldown=8.0, duration=2.5),
        ]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        w, h = state.width, state.height
        _ensure_rainbow()
        cx2, cy2 = w // 2, h // 2
        if special_name == "butterfly-effect":
            # Two expanding wings — butterfly shape
            for wing in (-1, 1):
                max_r = int(min(w // 2, h // 2) * progress * 1.5)
                for r in range(1, max(2, max_r), 2):
                    for a_deg in range(-60, 61, 8):
                        a = math.radians(a_deg)
                        px = cx2 + wing * int(r * math.cos(a) * 2)
                        py = cy2 + int(r * math.sin(a))
                        if 1 <= py < h - 1 and 0 <= px < w - 1:
                            hue_t = (r / max(max_r, 1) + state.frame * 0.01) % 1.0
                            pair = _rainbow_pair(hue_t)
                            try:
                                stdscr.addstr(py, px, "·", pair | curses.A_BOLD)
                            except curses.error:
                                pass
        elif special_name == "bifurcation":
            # Period-doubling cascade — brief double-image of the trajectory
            boost = math.sin(progress * math.pi)
            offsets = [(-3, -1), (3, 1)]
            for ox_off, oy_off in offsets:
                max_r = int(min(w // 3, h // 3) * max(boost, 0.1))
                for r in range(1, max(2, max_r), 3):
                    for a_deg in range(0, 360, 10):
                        a = math.radians(a_deg)
                        # Butterfly lobe silhouette — wide horizontally
                        px = cx2 + ox_off + int(r * math.cos(a) * 2.3)
                        py = cy2 + oy_off + int(r * math.sin(a) * 0.65)
                        if 1 <= py < h - 1 and 0 <= px < w - 1:
                            hue_t = (r / max(max_r, 1) + state.frame * 0.015) % 1.0
                            pair = _rainbow_pair(hue_t)
                            try:
                                stdscr.addstr(py, px, "░", pair | curses.A_DIM)
                            except curses.error:
                                pass

    # ── v0.2: Ambient tick ────────────────────────────────────────────────────

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        """Tiny random perturbation — faint dim dot at a random lobe position."""
        if idle_seconds < 1.0:
            return
        w, h = state.width, state.height
        if w < 8 or h < 4:
            return
        _ensure_rainbow()
        if random.random() < 0.30:
            lobe = random.choice([-1, 1])
            cx2 = w // 2
            cy2 = int(h * 0.38)
            lobe_ox = int(w * 0.22)
            px = cx2 + lobe * lobe_ox + random.randint(-5, 5)
            py = cy2 + random.randint(-3, 3)
            if 1 <= py < h - 1 and 0 <= px < w - 1:
                pair = _rainbow_pair(random.random())
                try:
                    stdscr.addstr(py, px, "·", pair | curses.A_DIM)
                except curses.error:
                    pass


register(LorenzButterflyPlugin())


# ── Rössler Ribbon ────────────────────────────────────────────────────────────

class RosslerRibbonPlugin(_AttractorBase):
    """Rössler attractor — tumbling 3D camera reveals the coil + spike from all angles.

    Parameters: a=0.2, b=0.2, c=5.7.
    Camera slowly rotates around the attractor's Y axis, so the view alternates
    between the flat X-Y spiral, the X-Z spike cross-section, and every angle
    between. A secondary hue shift makes the colour wheel orbit continuously.
    """
    name = "rossler-ribbon"
    _DT = 0.012   # slightly shorter step — smoother ribbon at higher density
    _A  = 0.2
    _B  = 0.2
    _C  = 5.7

    def __init__(self):
        super().__init__()
        self._roll   = 0.0   # camera rotation angle (around attractor Y axis)
        self._hue_s  = 0.0   # colour wheel phase shift
        self._tilt   = 0.0   # secondary tilt (nods up/down slowly)

    def _reset_trajectory(self):
        self._tx, self._ty, self._tz = 0.1, 0.0, 0.0

    def _setup_projection(self, w, h):
        self._ox = w / 2.0
        self._oy = h / 2.0
        # X,Y range ≈ ±12;  Z range ≈ 0..12 (spike up to ~40 occasionally)
        self._sx = (w - 6) / 26.0
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
        # Rotating camera around the Y axis: mixes X and Z into the horizontal
        # axis, so the flat spiral gradually tilts and the Z-spike cycles in/out
        ca, sa = math.cos(self._roll), math.sin(self._roll)
        ct, st = math.cos(self._tilt), math.sin(self._tilt)
        # Rotate around Y: new_x = x*ca + z*sa,  new_z = -x*sa + z*ca
        rx = self._tx * ca + self._tz * sa
        rz = -self._tx * sa + self._tz * ca
        # Tilt around X: new_y = y*ct - rz*st
        ry = self._ty * ct - rz * st
        sx = int(self._ox + rx * self._sx)
        sy = int(self._oy - ry * self._sy)
        return sx, sy

    def _spatial_hue(self, x, y, w, h):
        # Angle-from-centre + slow orbit offset
        angle = math.atan2(y - self._oy, x - self._ox)
        t = (angle / math.tau + self._hue_s) % 1.0
        return _rainbow_pair(t)

    def draw_extras(self, stdscr, state, color_pairs):
        # Advance camera rotation — full 360° every ~1050 frames (~17s at 60fps)
        self._roll  = (self._roll  + 0.006) % math.tau
        # Secondary nod: ±25° over a ~700 frame cycle
        self._tilt  = math.sin(state.frame * 0.009) * 0.44
        # Hue orbit: full cycle every ~330 frames
        self._hue_s = (self._hue_s + 0.003) % 1.0
        # Use faster decay so rotating view doesn't blur into smear
        # (patch the grid decay via a subclass trick: temporarily lower decay)
        self._fast_decay = True
        super().draw_extras(stdscr, state, color_pairs)
        self._fast_decay = False

    # ── v0.2: Emergent system ─────────────────────────────────────────────────

    def emergent_layer(self):
        return "background"

    def wave_config(self):
        """Ribbon flutter — gentle, damped wave oscillation."""
        return {"speed": 0.4, "damping": 0.97}

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────

    def echo_decay(self):
        """Ribbon orbits persist for 6 frames."""
        return 6

    def glow_radius(self):
        return 1

    def symmetry(self):
        return None

    def depth_layers(self):
        return 3

    def decay_sequence(self):
        return "▓▒░·."

    def warp_field(self, x, y, w, h, frame, intensity):
        """Ribbon-flutter warp — x oscillates, mimicking the coil ripple."""
        yf = y / max(h, 1)
        t = frame * 0.05
        amp = intensity * 1.5
        wx = int(amp * math.sin(t + yf * 0.15 * math.tau))
        wy = int(amp * 0.3 * math.cos(t * 0.65 + yf * 3.0))
        nx = max(0, min(w - 1, x + wx))
        ny = max(0, min(h - 1, y + wy))
        return (nx, ny)

    def force_points(self, w, h, frame, intensity):
        """1 vortex at coil center, 1 repulsor at spike tip (top of screen)."""
        cx = w / 2.0
        cy = h / 2.0
        strength = 0.35 + intensity * 0.35
        return [
            {"x": int(cx), "y": int(cy),
             "strength": strength, "type": "vortex"},
            {"x": int(cx), "y": 2,
             "strength": strength * 0.6, "type": "repulsor"},
        ]

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────

    def intensity_curve(self, raw):
        return raw ** 0.8

    # ── v0.2: Reactive system ─────────────────────────────────────────────────

    def react(self, event_kind, data):
        cx, cy = 0.5, 0.5
        rng = random
        coil_center = (0.5, 0.55)   # flat coil centre
        spike_tip   = (0.5, 0.05)   # top of the spike
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.9,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "agent_end":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.5,
                            origin=(cx, cy), color_key="soft", duration=2.0)
        if event_kind == "llm_start":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.8,
                            origin=(cx, cy), color_key="accent", duration=3.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.4,
                            origin=(rng.random(), rng.random()),
                            color_key="bright", duration=0.5)
        if event_kind == "llm_end":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.65,
                            origin=coil_center, color_key="soft", duration=2.0)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.65,
                            origin=(rng.random(), rng.random()),
                            color_key="accent", duration=1.5)
        if event_kind == "tool_complete":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.45,
                            origin=(rng.random(), rng.random()),
                            color_key="soft", duration=1.2)
        if event_kind == "mcp_tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.55,
                            origin=coil_center, color_key="accent", duration=1.4)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.75,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "skill_create":
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                            origin=(cx, cy), color_key="bright", duration=3.5,
                            data={"maximal": True})
        if event_kind == "error":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                            origin=(rng.random(), rng.random()),
                            color_key="warning", duration=2.0)
        if event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                            origin=spike_tip, color_key="warning", duration=3.0)
        if event_kind == "cron_tick":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.50,
                            origin=coil_center, color_key="soft", duration=2.0)
        if event_kind == "background_proc":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.3,
                            origin=(rng.random(), rng.random()),
                            color_key="base", duration=0.8)
        if event_kind == "subagent_started":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.65,
                            origin=(rng.random(), 0.3), color_key="soft", duration=2.5)
        if event_kind == "context_pressure":
            return Reaction(element=ReactiveElement.GAUGE,
                            intensity=data.get("level", 0.5),
                            origin=(cx, cy), color_key="accent", duration=2.0)
        if event_kind == "token_usage":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.25,
                            origin=(rng.random(), rng.random()),
                            color_key="base", duration=0.6)
        if event_kind == "dangerous_cmd":
            # Spike eruption
            return Reaction(element=ReactiveElement.SPARK, intensity=0.9,
                            origin=spike_tip, color_key="warning", duration=1.5)
        if event_kind == "approval_request":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.7,
                            origin=(cx, cy), color_key="warning", duration=2.0)
        if event_kind == "compression_started":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.8,
                            origin=(cx, cy), color_key="accent", duration=3.0)
        if event_kind == "reasoning_change":
            return Reaction(element=ReactiveElement.GLYPH, intensity=0.7,
                            origin=(cx, cy), color_key="accent", duration=2.0)
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────

    def palette_shift(self, trigger_effect, intensity, base_palette):
        if trigger_effect == "error":
            self._palette_state = "error"   # spike eruption — red
        elif trigger_effect == "skill_create":
            self._palette_state = "skill"   # ribbon unfurling — cyan/white
        elif trigger_effect == "agent_start":
            self._palette_state = "bright"
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────

    def special_effects(self):
        return [
            SpecialEffect(name="ribbon-spiral", trigger_kinds=["burst"],
                          min_intensity=0.3, cooldown=5.0, duration=3.0),
            SpecialEffect(name="spike-eruption",
                          trigger_kinds=["error", "dangerous_cmd"],
                          min_intensity=0.5, cooldown=7.0, duration=2.0),
        ]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        w, h = state.width, state.height
        _ensure_rainbow()
        cx2, cy2 = w // 2, h // 2
        if special_name == "ribbon-spiral":
            # Expanding coil spiral + spike morph overlay
            t = state.frame * 0.05
            max_turns = int(progress * 5)
            for i in range(max_turns * 30):
                frac = i / max(max_turns * 30, 1)
                angle = frac * math.tau * max_turns + t
                r = frac * min(w // 2, h // 2)
                px = cx2 + int(r * math.cos(angle) * 2)
                py = cy2 + int(r * math.sin(angle))
                if 1 <= py < h - 1 and 0 <= px < w - 1:
                    hue_t = (frac + state.frame * 0.005) % 1.0
                    pair = _rainbow_pair(hue_t)
                    try:
                        stdscr.addstr(py, px, "·", pair | curses.A_BOLD)
                    except curses.error:
                        pass
            # Spike accent: vertical line at center rising out of coil
            spike_h = int(cy2 * progress)
            for sy in range(max(1, cy2 - spike_h), cy2):
                hue_t = (1.0 - sy / max(cy2, 1) + state.frame * 0.01) % 1.0
                pair = _rainbow_pair(hue_t)
                try:
                    stdscr.addstr(sy, cx2, "│", pair | curses.A_BOLD)
                except curses.error:
                    pass
        elif special_name == "spike-eruption":
            # Bright vertical burst from spike tip (top) downward
            burst_len = int(h * 0.6 * math.sin(progress * math.pi))
            for sy in range(1, max(2, burst_len)):
                hue_t = (sy / max(burst_len, 1) + state.frame * 0.02) % 1.0
                pair = _rainbow_pair(hue_t)
                ch = "║" if sy % 3 == 0 else "│"
                try:
                    stdscr.addstr(sy, cx2, ch, pair | curses.A_BOLD)
                except curses.error:
                    pass

    # ── v0.2: Ambient tick ────────────────────────────────────────────────────

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        """Very occasional spike event — single bright char near the spike tip."""
        if idle_seconds < 1.5:
            return
        w, h = state.width, state.height
        if w < 8 or h < 4:
            return
        _ensure_rainbow()
        if random.random() < 0.12:
            # Spike is roughly at center-x, upper-quarter of screen
            cx2 = w // 2
            sy = random.randint(1, max(2, h // 4))
            pair = _rainbow_pair(0.5 + random.uniform(-0.15, 0.15))  # cyan/blue
            try:
                stdscr.addstr(sy, cx2 + random.randint(-1, 1), "◆",
                              pair | curses.A_BOLD)
            except curses.error:
                pass


# Patch _AttractorBase.draw_extras to respect _fast_decay flag on subclasses
_orig_attractor_draw = _AttractorBase.draw_extras

def _patched_attractor_draw(self, stdscr, state, color_pairs):
    import curses as _curses
    w, h = state.width, state.height
    if self._grid is None or (w, h) != (self._w, self._h):
        self._setup(w, h)
    _ensure_rainbow()
    grid = self._grid
    intensity = state.intensity_multiplier

    n_steps = int(600 * (0.5 + intensity))
    for _ in range(n_steps):
        self._step()
        if not self._is_valid():
            self._reset_trajectory()
            continue
        sx, sy = self._project()
        if 1 <= sy < h - 1 and 0 <= sx < w - 1:
            grid[sy][sx] = min(grid[sy][sx] + 0.04, 1.0)

    fast = getattr(self, '_fast_decay', False)
    if fast:
        decay = 0.88 - 0.04 * intensity   # fast: clears in ~8 frames
    else:
        decay = 0.977 - 0.008 * intensity  # normal: long persistence

    chars = " ·.,:;=+*#▒▓█"
    n_chars = len(chars)
    for y in range(1, h - 1):
        row = grid[y]
        for x in range(w - 1):
            v = row[x] * decay
            row[x] = v
            if v < 0.01:
                continue
            ch   = chars[max(0, min(n_chars - 1, int(v * (n_chars - 1))))]
            attr = _attr_by_density(v)
            hue  = self._spatial_hue(x, y, w, h)
            try:
                stdscr.addstr(y, x, ch, hue | attr)
            except _curses.error:
                pass

_AttractorBase.draw_extras = _patched_attractor_draw


register(RosslerRibbonPlugin())


# ── Halvorsen Star ────────────────────────────────────────────────────────────

class HalvorsenStarPlugin(_AttractorBase):
    """Halvorsen cyclically symmetric attractor — three interlocking spiral arms.

    dx/dt = -a·x - 4y - 4z - y²
    dy/dt = -a·y - 4z - 4x - z²
    dz/dt = -a·z - 4x - 4y - x²   (a=1.4)

    v0.2 upgrade: neural field resonance, 12-pointed mandala via rotate_4
    symmetry, gravitational lensing warp, 3 vortex force points, full
    reactive event system, special star-resonance effect, and enhanced
    draw_extras with particle overlays and arm indicators.
    """
    name = "halvorsen-star"
    _DT = 0.005  # halved — Halvorsen has y² and z² terms that blow up with large dt
    _A  = 1.4

    # 3 arm angles: 0°, 120°, 240° (in radians)
    _ARM_ANGLES = [0.0, math.tau / 3.0, 2 * math.tau / 3.0]

    def __init__(self):
        super().__init__()
        # cron arm rotation counter
        self._cron_arm_idx = 0
        # palette state: 'normal', 'error', 'skill', 'bright'
        self._palette_state = 'normal'
        # wobble phase for ambient rotation
        self._wobble_phase = 0.0
        # previous trajectory positions for velocity display
        self._prev_tx = -1.48
        self._prev_ty = -1.51
        self._prev_tz = 2.04

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

    # ── v0.2: Emergent system ─────────────────────────────────────────────────

    def neural_field_config(self):
        """Neural field resonance: attractor density maxima trigger neural firing."""
        return {
            "threshold": 3,
            "fire_duration": 4,
            "refractory": 6,
        }

    def emergent_layer(self):
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────

    def symmetry(self):
        """4-fold rotation × 3-fold Halvorsen = 12-pointed mandala."""
        return "rotate_4"

    def glow_radius(self):
        """Arms glow with radius 2."""
        return 2

    def echo_decay(self):
        """Orbit trails linger for 4 frames."""
        return 4

    def warp_field(self, x, y, w, h, frame, intensity):
        """Gravitational lensing: dense regions bend space via sinusoidal warp."""
        xf = x / max(w, 1)
        yf = y / max(h, 1)
        cx = 0.5
        cy = 0.5
        dx = xf - cx
        dy = yf - cy
        dist = math.sqrt(dx * dx + dy * dy * 4) + 0.001
        # Warp magnitude scales with intensity and proximity to center
        amp = intensity * 1.8 * max(0.0, 0.4 - dist)
        t = frame * 0.04
        wx = int(amp * math.sin(t + dist * 12.0) * 2)
        wy = int(amp * 0.6 * math.cos(t * 0.7 + dist * 10.0))
        nx = max(0, min(w - 1, x + wx))
        ny = max(0, min(h - 1, y + wy))
        return (nx, ny)

    def force_points(self, w, h, frame, intensity):
        """3 vortex attractors at the 3 Halvorsen arm tips, rotating slowly."""
        cx = w / 2.0
        cy = h / 2.0
        arm_r_x = (w - 6) / 20.0 * 7.0   # ~7 units out in attractor space
        arm_r_y = (h - 4) / 14.0 * 5.0
        t = frame * 0.012  # slow rotation
        strength = 0.3 + intensity * 0.4
        points = []
        for ang in self._ARM_ANGLES:
            rot_ang = ang + t
            points.append({
                "x": int(cx + math.cos(rot_ang) * arm_r_x),
                "y": int(cy + math.sin(rot_ang) * arm_r_y),
                "strength": strength,
                "type": "vortex",
            })
        return points

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────

    def intensity_curve(self, raw):
        """Power curve raw^0.8 — moderate sensitivity."""
        return raw ** 0.8

    # ── v0.2: Reactive system ─────────────────────────────────────────────────

    def react(self, event_kind, data):
        cx, cy = 0.5, 0.5
        rng = random

        if event_kind == "agent_start":
            return Reaction(
                element=ReactiveElement.PULSE,
                intensity=1.0,
                origin=(cx, cy),
                color_key="bright",
                duration=2.5,
                data={"style": "rays"},
            )
        if event_kind == "agent_end":
            return Reaction(
                element=ReactiveElement.PULSE,
                intensity=0.3,
                origin=(cx, cy),
                color_key="soft",
                duration=2.0,
            )
        if event_kind == "llm_start":
            return Reaction(
                element=ReactiveElement.STREAM,
                intensity=0.8,
                origin=(cx, cy),
                color_key="accent",
                duration=4.0,
                data={"direction": "outward"},
            )
        if event_kind == "llm_chunk":
            # SPARK at random arm position
            arm_ang = rng.choice(self._ARM_ANGLES)
            ox = 0.5 + math.cos(arm_ang) * 0.3
            oy = 0.5 + math.sin(arm_ang) * 0.2
            return Reaction(
                element=ReactiveElement.SPARK,
                intensity=0.5,
                origin=(max(0.0, min(1.0, ox)), max(0.0, min(1.0, oy))),
                color_key="accent",
                duration=0.7,
            )
        if event_kind == "llm_end":
            return Reaction(
                element=ReactiveElement.RIPPLE,
                intensity=0.6,
                origin=(cx, cy),
                color_key="soft",
                duration=1.5,
            )
        if event_kind == "tool_call":
            return Reaction(
                element=ReactiveElement.ORBIT,
                intensity=0.7,
                origin=(cx, cy),
                color_key="accent",
                duration=3.0,
                data={"tool": data.get("name", "")},
            )
        if event_kind == "memory_save":
            return Reaction(
                element=ReactiveElement.BLOOM,
                intensity=0.75,
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
        if event_kind == "subagent_started":
            return Reaction(
                element=ReactiveElement.ORBIT,
                intensity=0.65,
                origin=(rng.random(), rng.random()),
                color_key="soft",
                duration=2.5,
            )
        if event_kind == "cron_tick":
            # Rotate which arm each tick
            arm_ang = self._ARM_ANGLES[self._cron_arm_idx % 3]
            self._cron_arm_idx += 1
            ox = 0.5 + math.cos(arm_ang) * 0.35
            oy = 0.5 + math.sin(arm_ang) * 0.25
            return Reaction(
                element=ReactiveElement.ORBIT,
                intensity=0.55,
                origin=(max(0.0, min(1.0, ox)), max(0.0, min(1.0, oy))),
                color_key="soft",
                duration=2.0,
            )
        if event_kind == "reasoning_change":
            return Reaction(
                element=ReactiveElement.GLYPH,
                intensity=0.7,
                origin=(cx, cy),
                color_key="accent",
                duration=2.0,
                data={"morph": True},
            )
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────

    def palette_shift(self, trigger_effect, intensity, base_palette):
        if trigger_effect == "error":
            self._palette_state = "error"
        elif trigger_effect == "skill_create":
            self._palette_state = "skill"
        elif trigger_effect == "agent_start":
            self._palette_state = "bright"
        return None  # actual curses palette management deferred to engine

    # ── v0.2: Special effects ─────────────────────────────────────────────────

    def special_effects(self):
        return [
            SpecialEffect(
                name="star-resonance",
                trigger_kinds=["burst", "skill_create"],
                min_intensity=0.5,
                cooldown=4.0,
                duration=3.0,
            ),
        ]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        if special_name != "star-resonance":
            return
        w, h = state.width, state.height
        cx, cy = w // 2, h // 2
        _ensure_rainbow()
        star_chars = "✦✧⟡◆"
        # 3 expanding arcs at 120° each, filling out over progress
        max_r = int(min(w // 2, h // 2) * progress * 1.2)
        for arm_idx, arm_ang in enumerate(self._ARM_ANGLES):
            pair = _rainbow_pair_angle(arm_ang)
            bold = curses.A_BOLD
            # Draw expanding arc radiating from center along arm direction
            for r in range(1, max(1, max_r)):
                # arc spans ±30° around arm angle
                for dang in range(-30, 31, 6):
                    theta = arm_ang + math.radians(dang)
                    px = int(cx + r * math.cos(theta) * 2)
                    py = int(cy + r * math.sin(theta))
                    if 1 <= py < h - 1 and 1 <= px < w - 1:
                        ch_idx = (r + arm_idx) % len(star_chars)
                        try:
                            stdscr.addstr(py, px, star_chars[ch_idx], pair | bold)
                        except curses.error:
                            pass

    # ── v0.2: Ambient tick ────────────────────────────────────────────────────

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        if idle_seconds > 1.5:
            # Add a subtle wobble to the projection offset
            self._wobble_phase += 0.03
            wobble = math.sin(self._wobble_phase) * 0.5
            if self._grid is not None:
                self._oy = self._h / 2.0 + wobble

    # ── v0.2: Enhanced draw_extras ────────────────────────────────────────────

    def draw_extras(self, stdscr, state, color_pairs):
        # Save pre-step trajectory for velocity vector
        self._prev_tx = self._tx
        self._prev_ty = self._ty

        # Parent renders the full density grid
        super().draw_extras(stdscr, state, color_pairs)

        if self._grid is None:
            return
        w, h = state.width, state.height
        _ensure_rainbow()
        f = state.frame

        # ── Center of mass indicator ────────────────────────────────────────
        cx = int(self._ox)
        cy = int(self._oy)
        # Pulse between ◉ and ◎ based on frame
        com_ch = "◉" if (f // 8) % 2 == 0 else "◎"
        pair_bright = _rainbow_pair(0.55)  # cyan
        try:
            stdscr.addstr(cy, cx, com_ch, pair_bright | curses.A_BOLD)
        except curses.error:
            pass

        # ── 3 arm tip indicators (dots at arm tips) ────────────────────────
        arm_r_x = self._sx * 7.0
        arm_r_y = self._sy * 5.0
        t_rot = f * 0.012
        for idx, arm_ang in enumerate(self._ARM_ANGLES):
            rot_ang = arm_ang + t_rot
            ax = int(cx + math.cos(rot_ang) * arm_r_x)
            ay = int(cy + math.sin(rot_ang) * arm_r_y)
            pair = _rainbow_pair_angle(arm_ang)
            if 1 <= ay < h - 1 and 1 <= ax < w - 1:
                try:
                    stdscr.addstr(ay, ax, "✦", pair | curses.A_BOLD)
                except curses.error:
                    pass

        # ── Current particle position as bright star + velocity vector ──────
        px_cur, py_cur = self._project()
        if 1 <= py_cur < h - 1 and 1 <= px_cur < w - 1:
            pair_cur = _rainbow_pair(0.15)  # yellow
            try:
                stdscr.addstr(py_cur, px_cur, "✦", pair_cur | curses.A_BOLD)
            except curses.error:
                pass
            # Velocity vector (difference from prev projected position)
            prev_px = int(self._ox + self._prev_tx * self._sx)
            prev_py = int(self._oy - self._prev_ty * self._sy)
            vx = px_cur - prev_px
            vy = py_cur - prev_py
            # Draw 2-step velocity line
            for step in (1, 2):
                lx = px_cur + vx * step
                ly = py_cur + vy * step
                if 1 <= ly < h - 1 and 1 <= lx < w - 1:
                    try:
                        stdscr.addstr(ly, lx, "·", pair_cur)
                    except curses.error:
                        pass


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


    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────

    def emergent_layer(self):
        return "background"

    def echo_decay(self):
        """Torus orbit trails linger for 5 frames."""
        return 5

    def glow_radius(self):
        return 2

    def symmetry(self):
        return None

    def depth_layers(self):
        return 3

    def decay_sequence(self):
        return "▓▒░·."

    def warp_field(self, x, y, w, h, frame, intensity):
        """Toroidal warp — pixels curve around the torus axis."""
        xf = x / max(w, 1) - 0.5
        yf = y / max(h, 1) - 0.5
        t = frame * 0.01
        dist = math.sqrt(xf * xf + yf * yf) + 0.001
        angle = math.atan2(yf, xf)
        warp_angle = angle + intensity * 0.15 * math.sin(t + dist * 6.0)
        r_warped = dist * (1.0 + 0.08 * math.sin(t * 2.0 + angle * 4.0) * intensity)
        nx = max(0, min(w - 1, int(w * (0.5 + r_warped * math.cos(warp_angle)))))
        ny = max(0, min(h - 1, int(h * (0.5 + r_warped * math.sin(warp_angle)))))
        return (nx, ny)

    def force_points(self, w, h, frame, intensity):
        """2 vortex attractors orbiting the torus at ±60° from vertical."""
        cx = w / 2.0
        cy = h / 2.0
        t = frame * 0.010  # slow orbit
        r_x = w * 0.28
        r_y = h * 0.22
        strength = 0.35 + intensity * 0.35
        ang1 = t + math.pi / 3.0   # +60°
        ang2 = t - math.pi / 3.0   # -60°
        return [
            {"x": int(cx + math.cos(ang1) * r_x),
             "y": int(cy + math.sin(ang1) * r_y),
             "strength": strength, "type": "vortex"},
            {"x": int(cx + math.cos(ang2) * r_x),
             "y": int(cy + math.sin(ang2) * r_y),
             "strength": strength, "type": "vortex"},
        ]

    def wave_config(self):
        return {"speed": 0.2, "damping": 0.99}

    def physarum_config(self):
        """Slime-mould agents trace the torus surface."""
        return {"n_agents": 100, "sensor_angle": 0.5, "sensor_dist": 4,
                "turn_speed": 0.35, "speed": 1.0, "deposit": 1.0, "decay": 0.95}

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────

    def intensity_curve(self, raw):
        return raw ** 0.9

    # ── v0.2: Reactive system ─────────────────────────────────────────────────

    def react(self, event_kind, data):
        cx, cy = 0.5, 0.5
        rng = random
        # Torus orbits at ±60° from vertical, roughly quarter-way from edge
        inner_torus = (0.5, 0.38)   # inner torus centre
        torus_rim1  = (0.65, 0.45)
        torus_rim2  = (0.35, 0.45)
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.9,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "agent_end":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.5,
                            origin=(cx, cy), color_key="soft", duration=2.0)
        if event_kind == "llm_start":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.8,
                            origin=(cx, cy), color_key="accent", duration=3.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.4,
                            origin=(rng.random(), rng.random()),
                            color_key="bright", duration=0.5)
        if event_kind == "llm_end":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.65,
                            origin=(cx, cy), color_key="soft", duration=2.0)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.65,
                            origin=(cx, cy), color_key="accent", duration=3.0)
        if event_kind == "tool_complete":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.45,
                            origin=rng.choice([torus_rim1, torus_rim2]),
                            color_key="soft", duration=1.2)
        if event_kind == "mcp_tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.55,
                            origin=rng.choice([torus_rim1, torus_rim2]),
                            color_key="accent", duration=1.4)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.75,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "skill_create":
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                            origin=(cx, cy), color_key="bright", duration=3.5,
                            data={"maximal": True})
        if event_kind == "error":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                            origin=(rng.random(), rng.random()),
                            color_key="warning", duration=2.0)
        if event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                            origin=(cx, cy), color_key="warning", duration=3.0)
        if event_kind == "cron_tick":
            # Torus revolution — orbit at rim
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.5,
                            origin=rng.choice([torus_rim1, torus_rim2]),
                            color_key="soft", duration=2.0)
        if event_kind == "background_proc":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.3,
                            origin=(rng.random(), rng.random()),
                            color_key="base", duration=0.8)
        if event_kind == "subagent_started":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.65,
                            origin=inner_torus, color_key="soft", duration=2.5)
        if event_kind == "context_pressure":
            return Reaction(element=ReactiveElement.GAUGE,
                            intensity=data.get("level", 0.5),
                            origin=(cx, cy), color_key="accent", duration=2.0)
        if event_kind == "token_usage":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.25,
                            origin=(rng.random(), rng.random()),
                            color_key="base", duration=0.6)
        if event_kind == "dangerous_cmd":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.9,
                            origin=(cx, cy), color_key="warning", duration=1.5)
        if event_kind == "approval_request":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.7,
                            origin=(cx, cy), color_key="warning", duration=2.0)
        if event_kind == "compression_started":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.8,
                            origin=(cx, cy), color_key="accent", duration=3.0)
        if event_kind == "reasoning_change":
            return Reaction(element=ReactiveElement.GLYPH, intensity=0.7,
                            origin=(cx, cy), color_key="accent", duration=2.0)
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────

    def palette_shift(self, trigger_effect, intensity, base_palette):
        if trigger_effect == "error":
            self._palette_state = "error"       # red disruption
        elif trigger_effect == "skill_create":
            self._palette_state = "skill"       # cyan/white revelation
        elif trigger_effect == "agent_start":
            self._palette_state = "bright"      # white/magenta ignition
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────

    def special_effects(self):
        return [
            SpecialEffect(name="torus-resonance", trigger_kinds=["burst"],
                          min_intensity=0.3, cooldown=5.0, duration=3.0),
            SpecialEffect(name="torus-flip",
                          trigger_kinds=["skill_create", "agent_start"],
                          min_intensity=0.5, cooldown=8.0, duration=2.5),
        ]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        w, h = state.width, state.height
        _ensure_rainbow()
        cx2, cy2 = w // 2, h // 2
        if special_name == "torus-resonance":
            # Concentric torus rings radiating outward
            max_rings = int(progress * 8)
            for ring in range(1, max_rings + 1):
                r_x = int(w * 0.35 * ring / max(max_rings, 1))
                r_y = int(h * 0.35 * ring / max(max_rings, 1))
                hue_t = (ring / max(max_rings, 1) + state.frame * 0.01) % 1.0
                pair = _rainbow_pair(hue_t)
                for a_deg in range(0, 360, 5):
                    a = math.radians(a_deg)
                    px = cx2 + int(r_x * math.cos(a))
                    py = cy2 + int(r_y * math.sin(a) * 0.6)
                    if 1 <= py < h - 1 and 0 <= px < w - 1:
                        try:
                            stdscr.addstr(py, px, "○", pair | curses.A_BOLD)
                        except curses.error:
                            pass
        elif special_name == "torus-flip":
            # Brief view from a tilted angle — squished/stretched torus silhouette
            flip_angle = progress * math.pi   # 0 → π (full flip)
            squeeze = abs(math.cos(flip_angle))  # 1→0→1 (squish through edge-on)
            r_x = int(w * 0.38)
            r_y = max(1, int(h * 0.28 * squeeze + 1))
            hue_t = (progress + state.frame * 0.01) % 1.0
            for a_deg in range(0, 360, 4):
                a = math.radians(a_deg)
                px = cx2 + int(r_x * math.cos(a))
                py = cy2 + int(r_y * math.sin(a) * 0.5)
                if 1 <= py < h - 1 and 0 <= px < w - 1:
                    pair = _rainbow_pair_angle(a + hue_t * math.tau)
                    try:
                        stdscr.addstr(py, px, "◎", pair | curses.A_BOLD)
                    except curses.error:
                        pass
            # Inner tube trace
            r_x2 = int(r_x * 0.45)
            r_y2 = max(1, int(r_y * 0.6 + 1))
            for a_deg in range(0, 360, 6):
                a = math.radians(a_deg)
                px = cx2 + int(r_x2 * math.cos(a))
                py = cy2 + int(r_y2 * math.sin(a) * 0.5)
                if 1 <= py < h - 1 and 0 <= px < w - 1:
                    pair = _rainbow_pair_angle(a + hue_t * math.tau * 0.5)
                    try:
                        stdscr.addstr(py, px, "·", pair | curses.A_DIM)
                    except curses.error:
                        pass

    # ── v0.2: Ambient tick ────────────────────────────────────────────────────

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        """Slow torus rotation indicator — dim arc at the torus rim."""
        if idle_seconds < 1.0:
            return
        w, h = state.width, state.height
        if w < 8 or h < 4:
            return
        _ensure_rainbow()
        if state.frame % 6 == 0:
            cx2, cy2 = w // 2, h // 2
            t = state.frame * 0.015  # slow rotation
            # Draw a single dim arc segment at the rotating rim point
            arc_start = t % math.tau
            r_x = int(w * 0.30)
            r_y = int(h * 0.20)
            for d_deg in range(-12, 13, 4):
                a = arc_start + math.radians(d_deg)
                px = cx2 + int(r_x * math.cos(a))
                py = cy2 + int(r_y * math.sin(a) * 0.55)
                if 1 <= py < h - 1 and 0 <= px < w - 1:
                    pair = _rainbow_pair_angle(a)
                    try:
                        stdscr.addstr(py, px, "·", pair | curses.A_DIM)
                    except curses.error:
                        pass


register(AizawaTorusPlugin())


# ── Thomas Labyrinth ──────────────────────────────────────────────────────────

class ThomasLabyrinthPlugin(_AttractorBase):
    """Thomas' cyclically symmetric attractor — slowly rotating 3D camera + hue shift.

    dx/dt = sin(y) - b·x
    dy/dt = sin(z) - b·y
    dz/dt = sin(x) - b·z    (b=0.208186 — edge of chaos)

    The cyclically symmetric 3D web looks totally different from each viewing
    angle.  Camera rotates slowly through all three projection planes (XY, YZ, XZ)
    and a second oscillation tilts it up/down, exposing the full spatial structure.
    Hue uses a time-shifted diagonal so the rainbow sweeps across the screen.
    """
    name = "thomas-labyrinth"
    _DT  = 0.04
    _B   = 0.208186
    # 3-fold symmetry points at 120° spacing — used for ORBIT events and force_points
    _SYM_ANGLES = [0.0, math.tau / 3.0, 2 * math.tau / 3.0]

    def __init__(self):
        super().__init__()
        self._az   = 0.0   # azimuth  (rotation around Z axis)
        self._el   = 0.0   # elevation (tilt around X axis)
        self._hue_shift = 0.0
        self._palette_state = "normal"
        self._sym_idx = 0   # for cron_tick cycling

    def _reset_trajectory(self):
        self._tx, self._ty, self._tz = 0.1, 0.0, -0.1

    def _setup_projection(self, w, h):
        self._ox = w / 2.0
        self._oy = h / 2.0
        # Range ±5 for all axes
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
        x, y, z = self._tx, self._ty, self._tz
        # Azimuth rotation (around Z): mixes X and Y
        ca, sa = math.cos(self._az), math.sin(self._az)
        rx = x * ca - y * sa
        ry = x * sa + y * ca
        # Elevation rotation (around new X): tilts Z into Y
        ce, se = math.cos(self._el), math.sin(self._el)
        # projected: px = rx (horizontal), py = ry*ce - z*se (vertical)
        px = rx
        py = ry * ce - z * se
        sx = int(self._ox + px * self._sx)
        sy = int(self._oy - py * self._sy)
        return sx, sy

    def _spatial_hue(self, x, y, w, h):
        # Diagonal band + time shift — bands travel across the screen
        t_diag = (x / max(w - 1, 1) + (1.0 - y / max(h - 1, 1))) * 0.5
        return _rainbow_pair((t_diag + self._hue_shift) % 1.0)

    def draw_extras(self, stdscr, state, color_pairs):
        f = state.frame
        # Slow azimuth sweep: full 360° every ~1400 frames (~23s)
        self._az = (f * 0.0045) % math.tau
        # Elevation nods between -40° and +40° on a different period
        self._el = math.sin(f * 0.0033) * 0.70
        # Hue shift: full cycle every ~830 frames
        self._hue_shift = (f * 0.0012) % 1.0
        # Fast decay so rotating view stays sharp
        self._fast_decay = True
        super().draw_extras(stdscr, state, color_pairs)
        self._fast_decay = False


    # ── v0.2: Emergent system ─────────────────────────────────────────────────

    def emergent_layer(self):
        return "background"

    def neural_field_config(self):
        """Labyrinth path firing — high threshold, long refractory."""
        return {"threshold": 3, "fire_duration": 2, "refractory": 7}

    def physarum_config(self):
        return {"n_agents": 200, "sensor_angle": 0.4, "sensor_dist": 4,
                "speed": 0.9, "deposit": 1.2, "decay": 0.96}

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────

    def glow_radius(self):
        return 1

    def echo_decay(self):
        """Labyrinth paths echo for 4 frames."""
        return 4

    def symmetry(self):
        return None

    def depth_layers(self):
        return 3

    def decay_sequence(self):
        return "▓▒░·."

    def warp_field(self, x, y, w, h, frame, intensity):
        """Cubic lattice distortion — 3-fold symmetry warps space like a crystal."""
        xf = x / max(w, 1)
        yf = y / max(h, 1)
        t = frame * 0.03
        amp = intensity * 1.5
        wx = int(amp * math.sin(xf * 0.3 * math.tau + t) * math.cos(yf * 0.3 * math.tau))
        wy = int(amp * 0.7 * math.cos(xf * 0.3 * math.tau) * math.sin(yf * 0.3 * math.tau + t))
        nx = max(0, min(w - 1, x + wx))
        ny = max(0, min(h - 1, y + wy))
        return (nx, ny)

    def force_points(self, w, h, frame, intensity):
        """3 vortex attractors at the 3-fold symmetry points (120° apart)."""
        cx = w / 2.0
        cy = h / 2.0
        r_x = w * 0.28
        r_y = h * 0.22
        t = frame * 0.008  # slow rotation
        strength = 0.30 + intensity * 0.35
        return [
            {"x": int(cx + math.cos(ang + t) * r_x),
             "y": int(cy + math.sin(ang + t) * r_y),
             "strength": strength, "type": "vortex"}
            for ang in self._SYM_ANGLES
        ]

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────

    def intensity_curve(self, raw):
        return raw ** 0.8

    # ── v0.2: Reactive system ─────────────────────────────────────────────────

    def react(self, event_kind, data):
        cx, cy = 0.5, 0.5
        rng = random
        # 3-fold symmetry points in screen-space
        sym_pts = [
            (0.5 + math.cos(a) * 0.28, 0.5 + math.sin(a) * 0.20)
            for a in self._SYM_ANGLES
        ]
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.9,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "agent_end":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.5,
                            origin=(cx, cy), color_key="soft", duration=2.0)
        if event_kind == "llm_start":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.8,
                            origin=(cx, cy), color_key="accent", duration=3.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.4,
                            origin=(rng.random(), rng.random()),
                            color_key="bright", duration=0.5)
        if event_kind == "llm_end":
            # Path resolved
            return Reaction(element=ReactiveElement.WAVE, intensity=0.65,
                            origin=(cx, cy), color_key="soft", duration=2.0)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.65,
                            origin=(rng.random(), rng.random()),
                            color_key="accent", duration=1.5)
        if event_kind == "tool_complete":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.45,
                            origin=(rng.random(), rng.random()),
                            color_key="soft", duration=1.2)
        if event_kind == "mcp_tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.55,
                            origin=rng.choice(sym_pts),
                            color_key="accent", duration=1.4)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.75,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "skill_create":
            # New labyrinth path found
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                            origin=(cx, cy), color_key="bright", duration=3.5,
                            data={"maximal": True})
        if event_kind == "error":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                            origin=(rng.random(), rng.random()),
                            color_key="warning", duration=2.0)
        if event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                            origin=(cx, cy), color_key="warning", duration=3.0)
        if event_kind == "cron_tick":
            pt = sym_pts[self._sym_idx % 3]
            self._sym_idx += 1
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.50,
                            origin=pt, color_key="soft", duration=2.0)
        if event_kind == "background_proc":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.3,
                            origin=(rng.random(), rng.random()),
                            color_key="base", duration=0.8)
        if event_kind == "subagent_started":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.65,
                            origin=rng.choice(sym_pts),
                            color_key="soft", duration=2.5)
        if event_kind == "context_pressure":
            return Reaction(element=ReactiveElement.GAUGE,
                            intensity=data.get("level", 0.5),
                            origin=(cx, cy), color_key="accent", duration=2.0)
        if event_kind == "token_usage":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.25,
                            origin=(rng.random(), rng.random()),
                            color_key="base", duration=0.6)
        if event_kind == "dangerous_cmd":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.9,
                            origin=(cx, cy), color_key="warning", duration=1.5)
        if event_kind == "approval_request":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.7,
                            origin=(cx, cy), color_key="warning", duration=2.0)
        if event_kind == "compression_started":
            # Labyrinth compresses
            return Reaction(element=ReactiveElement.WAVE, intensity=0.8,
                            origin=(cx, cy), color_key="accent", duration=3.0)
        if event_kind == "browser_navigate":
            return Reaction(element=ReactiveElement.TRAIL, intensity=0.55,
                            origin=(0.0, rng.random()),
                            color_key="accent", duration=2.0)
        if event_kind == "file_edit":
            return Reaction(element=ReactiveElement.TRAIL, intensity=0.5,
                            origin=(0.0, rng.random()),
                            color_key="soft", duration=2.0)
        if event_kind == "reasoning_change":
            return Reaction(element=ReactiveElement.GLYPH, intensity=0.7,
                            origin=(cx, cy), color_key="accent", duration=2.0)
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────

    def palette_shift(self, trigger_effect, intensity, base_palette):
        if trigger_effect == "error":
            self._palette_state = "error"   # lost in labyrinth — red
        elif trigger_effect == "skill_create":
            self._palette_state = "skill"   # path found — green/cyan
        elif trigger_effect == "agent_start":
            self._palette_state = "bright"  # cyan/white entry
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────

    def special_effects(self):
        return [
            SpecialEffect(name="maze-solve", trigger_kinds=["burst"],
                          min_intensity=0.3, cooldown=5.0, duration=3.0),
            SpecialEffect(name="labyrinth-solve",
                          trigger_kinds=["skill_create", "llm_end"],
                          min_intensity=0.4, cooldown=7.0, duration=3.0),
        ]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        w, h = state.width, state.height
        _ensure_rainbow()
        cx2, cy2 = w // 2, h // 2
        f = state.frame
        if special_name == "maze-solve":
            # A bright path traces from edge to center
            steps = int(progress * max(w, h) * 0.7)
            x = int(w * 0.1)
            y = int(h * 0.5)
            for i in range(steps):
                t = i / max(steps, 1)
                hue_t = (t + f * 0.005) % 1.0
                pair = _rainbow_pair(hue_t)
                dx = cx2 - x + int(math.sin(i * 0.3) * 3)
                dy = cy2 - y + int(math.cos(i * 0.4) * 2)
                if abs(dx) > abs(dy):
                    x += 1 if dx > 0 else -1
                else:
                    y += 1 if dy > 0 else -1
                if 1 <= y < h - 1 and 0 <= x < w - 1:
                    try:
                        stdscr.addstr(y, x, "·", pair | curses.A_BOLD)
                    except curses.error:
                        pass
        elif special_name == "labyrinth-solve":
            # 3 paths radiate from center outward toward the 3-fold symmetry points
            reach = int(progress * min(w * 0.4, h * 0.35))
            for arm_idx, ang in enumerate(self._SYM_ANGLES):
                pair = _rainbow_pair_angle(ang + f * 0.02)
                for step in range(1, max(2, reach)):
                    t_step = step / max(reach, 1)
                    # Sinuous labyrinth path
                    theta = ang + math.sin(step * 0.25) * 0.35
                    px = cx2 + int(step * math.cos(theta) * 2.0)
                    py = cy2 + int(step * math.sin(theta) * 0.75)
                    if 1 <= py < h - 1 and 0 <= px < w - 1:
                        ch = "─" if abs(math.cos(theta)) > abs(math.sin(theta)) else "│"
                        try:
                            stdscr.addstr(py, px, ch, pair | curses.A_BOLD)
                        except curses.error:
                            pass

    # ── v0.2: Ambient tick ────────────────────────────────────────────────────

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        """Single dim path segment slowly exploring the labyrinth."""
        if idle_seconds < 1.0:
            return
        w, h = state.width, state.height
        if w < 8 or h < 4:
            return
        _ensure_rainbow()
        if state.frame % 8 == 0:
            cx2, cy2 = w // 2, h // 2
            # Slow spiral exploration from center
            t = state.frame * 0.007
            r = (state.frame % 80) / 80.0 * min(w * 0.35, h * 0.28)
            angle = t * 1.3
            px = cx2 + int(r * math.cos(angle) * 1.8)
            py = cy2 + int(r * math.sin(angle) * 0.75)
            if 1 <= py < h - 1 and 0 <= px < w - 1:
                pair = _rainbow_pair_angle(angle)
                try:
                    stdscr.addstr(py, px, "·", pair | curses.A_DIM)
                except curses.error:
                    pass


register(ThomasLabyrinthPlugin())
