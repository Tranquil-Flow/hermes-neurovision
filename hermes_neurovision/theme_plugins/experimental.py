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
from typing import Dict, List, Optional, Tuple, Any

from hermes_neurovision.plugin import (
    ThemePlugin,
    ReactiveElement,
    Reaction,
    SpecialEffect,
)
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
        # hue rotates around the attractor geometry — angle from center
        cx_f = w / 2.0
        cy_f = h / 2.0
        hue_base = (f * 0.0028) % 1.0

        for y in range(1, h - 1):
            row = grid[y]
            for x in range(0, w - 1):
                v = row[x] * decay
                row[x] = v
                idx = int(v * (n_chars - 1))
                idx = max(0, min(n_chars - 1, idx))
                ch  = chars[idx]
                if v < 0.05:
                    attr = base_dim
                else:
                    # phase: angle from center so colors form a slow angular sweep
                    angle = math.atan2(y - cy_f, x - cx_f)
                    phase = (hue_base + angle / (2 * math.pi)) % 1.0
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


    def react(self, event_kind, data):
        import random
        from hermes_neurovision.plugin import ReactiveElement, Reaction
        if event_kind == "agent_start" or event_kind == "session_resume":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.9,
                           origin=(0.5, 0.5), color_key="bright", duration=2.5)
        if event_kind == "reasoning_change" or event_kind == "personality_change":
            return Reaction(element=ReactiveElement.GLYPH, intensity=0.8,
                           origin=(0.5, 0.5), color_key="bright", duration=3.0)
        if event_kind == "memory_save" or event_kind == "skill_create":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.9,
                           origin=(0.5, 0.5), color_key="accent", duration=2.5)
        if event_kind == "error" or event_kind == "crash":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.5,
                           origin=(random.random(), random.random()), color_key="soft", duration=1.5)
        if event_kind == "cron_tick":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.5,
                           origin=(0.5, 0.5), color_key="soft", duration=2.0)
        return None

    def wave_config(self):
        return {'speed': 0.3, 'damping': 0.97}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 1


register(CliffordAttractorPlugin())


# ── Barnsley Fern — IFS Random Iteration (v0.2 Upgrade) ───────────────────────

class BarnsleyFernPlugin(ThemePlugin):
    """Iterated function system fractal rendered via the random chaos game.

    v0.2 upgrade: physarum slime mold traces fern veins, reactive events drive
    growth behaviors, ambient sway, organic char rendering and palette shifts.
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
        # palette shift state
        self._palette_mode = "normal"  # "normal", "luminous", "wilt", "spring"
        self._palette_timer = 0.0
        # sway offset
        self._sway_offset = 0.0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    # ── v0.2: Emergent system — physarum slime mold traces fern veins ──────────

    def physarum_config(self) -> Optional[Dict[str, Any]]:
        return {
            "n_agents": 150,
            "sensor_angle": 0.4,
            "sensor_dist": 3,
            "turn_speed": 0.3,
            "speed": 1.0,
            "deposit": 1.0,
            "decay": 0.95,
        }

    def emergent_layer(self) -> str:
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────

    def glow_radius(self) -> int:
        return 2

    def echo_decay(self) -> int:
        return 5

    def symmetry(self) -> Optional[str]:
        return None  # ferns are asymmetric and proud of it

    def decay_sequence(self) -> Optional[str]:
        return "\u2588\u2593\u2592\u2591\u00b7. "  # █▓▒░·. — cells age like browning leaves

    # ── v0.2: Intensity curve — exponential, sensitive to low activity ─────────

    def intensity_curve(self, raw: float) -> float:
        return raw ** 0.6

    # ── v0.2: Special effects ─────────────────────────────────────────────────

    def special_effects(self) -> List[SpecialEffect]:
        return [
            SpecialEffect(
                name="fern-unfurl",
                trigger_kinds=["skill_create", "burst"],
                min_intensity=0.5,
                cooldown=6.0,
                duration=3.0,
            ),
        ]

    def draw_special(self, stdscr, state, color_pairs: dict,
                     special_name: str, progress: float,
                     intensity: float) -> None:
        if special_name != "fern-unfurl":
            return
        w, h = state.width, state.height
        cx = w // 3  # fern is offset left-center
        cy = h // 2
        bright_attr = curses.color_pair(color_pairs.get("bright", 1)) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs.get("accent", 2))
        frond_chars = "\u2310\u223f\u224b~"
        # Expanding arc of frond chars from center-left outward
        max_radius = int((w // 2) * progress)
        for r in range(1, max_radius + 1):
            for angle_deg in range(-60, 61, 15):
                angle_rad = math.radians(angle_deg)
                fx = int(cx + r * math.cos(angle_rad))
                fy = int(cy - int(r * math.sin(angle_rad) * 0.5))
                if 1 <= fy < h - 1 and 0 <= fx < w - 1:
                    ch = frond_chars[(r + angle_deg // 15) % len(frond_chars)]
                    attr = bright_attr if r == max_radius else accent_attr
                    try:
                        stdscr.addstr(fy, fx, ch, attr)
                    except curses.error:
                        pass

    # ── v0.2: React to events ─────────────────────────────────────────────────

    def react(self, event_kind: str, data: Dict[str, Any]) -> Optional[Reaction]:
        rng = random.random
        if event_kind == "agent_start":
            return Reaction(
                element=ReactiveElement.PULSE,
                intensity=0.9,
                origin=(0.5, 0.95),    # base of fern — bottom center
                color_key="bright",
                duration=2.0,
            )
        if event_kind == "llm_start":
            return Reaction(
                element=ReactiveElement.STREAM,
                intensity=0.8,
                origin=(0.4, 0.05),   # top of fern — ideas shoot upward
                color_key="accent",
                duration=3.0,
            )
        if event_kind == "llm_chunk":
            return Reaction(
                element=ReactiveElement.SPARK,
                intensity=0.5,
                origin=(rng() * 0.6 + 0.2, rng() * 0.5 + 0.1),  # random frond tip
                color_key="bright",
                duration=0.4,
            )
        if event_kind == "llm_end":
            return Reaction(
                element=ReactiveElement.BLOOM,
                intensity=0.7,
                origin=(0.4, 0.5),    # fern center — frond unfurls
                color_key="accent",
                duration=2.0,
            )
        if event_kind == "tool_call":
            return Reaction(
                element=ReactiveElement.RIPPLE,
                intensity=0.7,
                origin=(rng() * 0.4 + 0.2, rng() * 0.6 + 0.1),
                color_key="soft",
                duration=1.5,
            )
        if event_kind == "tool_complete":
            return Reaction(
                element=ReactiveElement.RIPPLE,
                intensity=0.4,
                origin=(rng() * 0.4 + 0.2, rng() * 0.6 + 0.1),
                color_key="soft",
                duration=1.0,
            )
        if event_kind == "memory_save":
            return Reaction(
                element=ReactiveElement.BLOOM,
                intensity=0.8,
                origin=(0.4, 0.9),    # base — new root system
                color_key="accent",
                duration=2.5,
            )
        if event_kind == "skill_create":
            return Reaction(
                element=ReactiveElement.BLOOM,
                intensity=1.0,
                origin=(0.4, 0.5),    # entire new branch system
                color_key="bright",
                duration=3.0,
            )
        if event_kind == "error":
            return Reaction(
                element=ReactiveElement.SHATTER,
                intensity=0.9,
                origin=(0.4, 0.5),
                color_key="bright",   # will be shifted to red by palette_shift
                duration=2.0,
            )
        if event_kind == "agent_end":
            return Reaction(
                element=ReactiveElement.WAVE,
                intensity=0.6,
                origin=(0.4, 0.5),    # fern sways before sleeping
                color_key="soft",
                duration=3.0,
            )
        if event_kind == "git_commit":
            return Reaction(
                element=ReactiveElement.TRAIL,
                intensity=0.6,
                origin=(0.4, 0.9),    # along stem — branch recorded
                color_key="accent",
                duration=2.0,
            )
        if event_kind == "file_edit":
            return Reaction(
                element=ReactiveElement.TRAIL,
                intensity=0.5,
                origin=(rng() * 0.5 + 0.15, rng() * 0.7 + 0.05),
                color_key="soft",
                duration=1.5,
            )
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────

    def palette_shift(self, trigger_effect: str, intensity: float,
                      base_palette: Tuple[int, int, int, int]) -> Optional[Tuple[int, int, int, int]]:
        # base_palette is (bright, accent, soft, base) as color ints
        if trigger_effect == "skill_create":
            # Brighten to white/cyan — the fern becomes luminous
            return (curses.COLOR_WHITE, curses.COLOR_CYAN,
                    curses.COLOR_CYAN, curses.COLOR_GREEN)
        if trigger_effect == "error":
            # Shift to red/orange — wilting
            return (curses.COLOR_RED, curses.COLOR_YELLOW,
                    curses.COLOR_RED, curses.COLOR_RED)
        if trigger_effect == "agent_start":
            # Bright green/white — fern springs to life
            return (curses.COLOR_WHITE, curses.COLOR_GREEN,
                    curses.COLOR_GREEN, curses.COLOR_GREEN)
        return None

    # ── v0.2: Ambient tick — idle sway ────────────────────────────────────────

    def ambient_tick(self, stdscr, state, color_pairs: dict,
                     idle_seconds: float) -> None:
        # When idle, nudge the sway sinusoidally
        self._sway_offset = math.sin(idle_seconds * 0.5) * 2.0

    # ── Internal helpers ──────────────────────────────────────────────────────

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

        # Wind sway offset — whole fern sways sinusoidally
        sway = math.sin(f * 0.01) * 2 * intensity + self._sway_offset

        # Run iterations: chaos game
        steps = int(1200 * (0.3 + intensity))
        px, py = self._px, self._py

        # Map IFS output (range ≈ [-3,3] × [-3,10]) to screen
        scale   = min(w, h * 2.5) / 12.0
        ox      = w / 2.0 + sway
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

        # Decay and render with organic chars and phase-shifted colors
        decay   = 0.984
        # Organic char set: density-graduated
        chars   = " \u00b7\u2219\u2022\u25e6\u25cb\u25cf"  # ·∙•◦○●
        n_chars = len(chars)
        # Hue flows along y axis (growth direction) + time
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
                    # Phase: frond tips (top, edges) are bright; interior is soft
                    tip_factor = (h - y) / max(h, 1)   # 1.0 at top tip
                    phase = (hue_base + tip_factor * 0.5 + x / max(w, 1) * 0.15) % 1.0
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

        # Draw stem/trunk at fern base — vertical line of trunk chars
        stem_x = int(w / 2.0 + sway)
        stem_chars = "\u2502\u2551\u2502\u2502"  # │║││
        for i, sy in enumerate(range(h - 4, h - 1)):
            if 1 <= sy < h - 1 and 0 <= stem_x < w - 1:
                ch = stem_chars[i % len(stem_chars)]
                try:
                    stdscr.addstr(sy, stem_x, ch, bright_attr)
                except curses.error:
                    pass


register(BarnsleyFernPlugin())


# ── Flow Field — Curl Noise Particle Streams (v0.2 Upgrade) ───────────────────

class FlowFieldPlugin(ThemePlugin):
    """Particles ride a smoothly evolving curl-noise vector field.

    v0.2 upgrade: wave-field substrate, vortex force attractors, reactive events
    disturb the field, density map, graduated particle chars, flow tracer.
    """
    name = "flow-field"

    _MAX_PARTICLES = 600

    def __init__(self):
        self._trail: Optional[List[List[float]]] = None  # density grid
        self._particles: List[dict] = []
        self._rng  = random.Random(55)
        self._w = self._h = 0
        # Flow tracer — a single long-trail particle
        self._tracer: Optional[dict] = None
        self._tracer_trail: List[Tuple[int, int]] = []
        # Vortex storm state
        self._storm_vortices: List[dict] = []
        self._storm_timer = 0.0
        # Idle attractor
        self._idle_attractor: Optional[dict] = None

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    # ── v0.2: Emergent system — wave field as flow substrate ─────────────────

    def wave_config(self) -> Optional[Dict[str, Any]]:
        return {
            "speed": 0.5,
            "damping": 0.97,
        }

    def emergent_layer(self) -> str:
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────

    def warp_field(self, x: int, y: int, w: int, h: int,
                   frame: int, intensity: float) -> Tuple[int, int]:
        """Warp coordinates using the curl-noise formula for self-similar distortion."""
        t = frame * 0.02
        nx = x / max(w, 1)
        ny = y / max(h, 1)
        freq = 3.0
        eps = 0.01
        psi_dy = math.sin(nx * freq + t * 0.5) * (-math.sin((ny + eps) * freq * 1.3 - t * 0.3)) * freq * 1.3
        psi_dx = math.cos(nx * freq + t * 0.5) * freq * math.cos(ny * freq * 1.3 - t * 0.3)
        warp_strength = 1.5 * intensity
        wx = int(x + psi_dy * warp_strength)
        wy = int(y - psi_dx * warp_strength * 0.5)
        return (max(0, min(w - 1, wx)), max(0, min(h - 1, wy)))

    def glow_radius(self) -> int:
        return 1

    def echo_decay(self) -> int:
        return 4

    def symmetry(self) -> Optional[str]:
        return None  # flows are directional

    def force_points(self, w: int, h: int, frame: int,
                     intensity: float) -> List[Dict]:
        """Three vortex attractors orbiting center at different radii/speeds."""
        cx, cy = w / 2.0, h / 2.0
        t = frame * 0.025
        points = []

        # Storm vortices override normal ones temporarily
        if self._storm_vortices and self._storm_timer > 0:
            self._storm_timer -= 1.0 / 60.0  # approximate
            return list(self._storm_vortices)

        # Normal: 3 orbiting vortex attractors
        configs = [
            (0.28, 0.021, 0.6 + intensity * 0.4, "vortex"),
            (0.18, -0.034, 0.45 + intensity * 0.3, "vortex"),
            (0.38, 0.016, 0.35 + intensity * 0.25, "vortex"),
        ]
        for radius_ratio, speed_mul, strength, ftype in configs:
            r = min(w, h * 2) * radius_ratio
            angle = t * (speed_mul * 2 * math.pi)
            points.append({
                "x": int(cx + r * math.cos(angle)),
                "y": int(cy + r * math.sin(angle) * 0.5),
                "strength": strength,
                "type": ftype,
            })

        # Add idle attractor if present
        if self._idle_attractor:
            points.append(self._idle_attractor)

        return points

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────

    def intensity_curve(self, raw: float) -> float:
        return raw ** 0.7

    # ── v0.2: Special effects ─────────────────────────────────────────────────

    def special_effects(self) -> List[SpecialEffect]:
        return [
            SpecialEffect(
                name="vortex-storm",
                trigger_kinds=["burst"],
                min_intensity=0.4,
                cooldown=8.0,
                duration=4.0,
            ),
        ]

    def draw_special(self, stdscr, state, color_pairs: dict,
                     special_name: str, progress: float,
                     intensity: float) -> None:
        if special_name != "vortex-storm":
            return
        w, h = state.width, state.height
        bright_attr = curses.color_pair(color_pairs.get("bright", 1)) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs.get("accent", 2))
        swirl_chars = "\u25cc\u25ce\u25c9"  # ◌◎◉
        # Draw expanding circular attractors at 3 random-seeded positions
        rng = random.Random(int(progress * 1000) % 100)
        for i in range(3):
            vx = int(w * rng.uniform(0.15, 0.85))
            vy = int(h * rng.uniform(0.15, 0.85))
            radius = int(4 + progress * 8)
            # Draw ring
            for angle_deg in range(0, 360, 20):
                rad = math.radians(angle_deg)
                rx = int(vx + radius * math.cos(rad))
                ry = int(vy + radius * math.sin(rad) * 0.5)
                if 1 <= ry < h - 1 and 0 <= rx < w - 1:
                    try:
                        stdscr.addstr(ry, rx, ".", accent_attr)
                    except curses.error:
                        pass
            # Center glyph
            ch = swirl_chars[int(progress * 3 + i) % 3]
            if 1 <= vy < h - 1 and 0 <= vx < w - 1:
                try:
                    stdscr.addstr(vy, vx, ch, bright_attr)
                except curses.error:
                    pass

    # ── v0.2: React to events ─────────────────────────────────────────────────

    def react(self, event_kind: str, data: Dict[str, Any]) -> Optional[Reaction]:
        rng = random.random
        if event_kind == "agent_start":
            return Reaction(
                element=ReactiveElement.PULSE,
                intensity=1.0,
                origin=(0.5, 0.5),   # center — massive disturbance
                color_key="bright",
                duration=2.5,
            )
        if event_kind == "llm_start":
            return Reaction(
                element=ReactiveElement.STREAM,
                intensity=0.85,
                origin=(0.0, 0.5),   # horizontal stream
                color_key="bright",
                duration=4.0,
            )
        if event_kind == "llm_chunk":
            return Reaction(
                element=ReactiveElement.SPARK,
                intensity=0.5,
                origin=(rng(), rng()),
                color_key="accent",
                duration=0.3,
            )
        if event_kind == "llm_end":
            return Reaction(
                element=ReactiveElement.WAVE,
                intensity=0.6,
                origin=(0.5, 0.5),   # flow resets to equilibrium
                color_key="soft",
                duration=2.0,
            )
        if event_kind == "tool_call":
            return Reaction(
                element=ReactiveElement.RIPPLE,
                intensity=0.7,
                origin=(rng(), rng()),
                color_key="accent",
                duration=1.5,
            )
        if event_kind == "tool_complete":
            return Reaction(
                element=ReactiveElement.RIPPLE,
                intensity=0.4,
                origin=(rng(), rng()),
                color_key="soft",
                duration=1.0,
            )
        if event_kind == "memory_save":
            return Reaction(
                element=ReactiveElement.BLOOM,
                intensity=0.9,
                origin=(0.5, 0.5),   # particles spiral inward — memory crystallizing
                color_key="bright",
                duration=2.5,
            )
        if event_kind == "error":
            return Reaction(
                element=ReactiveElement.SHATTER,
                intensity=1.0,
                origin=(rng(), rng()),
                color_key="bright",  # shifted to red by palette_shift
                duration=2.0,
            )
        if event_kind == "subagent_started":
            return Reaction(
                element=ReactiveElement.ORBIT,
                intensity=0.7,
                origin=(0.5, 0.5),   # new sub-flow spawns, circles main flow
                color_key="accent",
                duration=5.0,
            )
        if event_kind == "context_pressure":
            return Reaction(
                element=ReactiveElement.GAUGE,
                intensity=data.get("pressure", 0.5),
                origin=(0.5, 0.05),
                color_key="soft",
                duration=2.0,
            )
        if event_kind == "compression_started":
            return Reaction(
                element=ReactiveElement.WAVE,
                intensity=0.8,
                origin=(0.5, 0.5),   # entire field compresses
                color_key="soft",
                duration=3.0,
            )
        if event_kind == "browser_navigate":
            return Reaction(
                element=ReactiveElement.TRAIL,
                intensity=0.6,
                origin=(rng(), rng()),
                color_key="accent",
                duration=2.0,
            )
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────

    def palette_shift(self, trigger_effect: str, intensity: float,
                      base_palette: Tuple[int, int, int, int]) -> Optional[Tuple[int, int, int, int]]:
        if trigger_effect == "llm_start":
            # Brighten to cyan/white — high-energy thinking
            return (curses.COLOR_WHITE, curses.COLOR_CYAN,
                    curses.COLOR_CYAN, curses.COLOR_BLUE)
        if trigger_effect == "error":
            # Red/yellow
            return (curses.COLOR_RED, curses.COLOR_YELLOW,
                    curses.COLOR_RED, curses.COLOR_RED)
        if trigger_effect in ("compression_started", "compression"):
            # Dim to dark blue
            return (curses.COLOR_BLUE, curses.COLOR_CYAN,
                    curses.COLOR_BLUE, curses.COLOR_BLACK)
        return None

    # ── v0.2: Ambient tick — idle attractor ───────────────────────────────────

    def ambient_tick(self, stdscr, state, color_pairs: dict,
                     idle_seconds: float) -> None:
        if idle_seconds > 2.0 and state.frame % 120 == 0:
            w, h = state.width, state.height
            # Spawn a gentle random attractor that pulls particles into clusters
            self._idle_attractor = {
                "x": random.randint(w // 4, 3 * w // 4),
                "y": random.randint(h // 4, 3 * h // 4),
                "strength": 0.3,
                "type": "vortex",
            }
        elif idle_seconds < 0.5:
            self._idle_attractor = None

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _init(self, w, h):
        self._trail = [[0.0] * w for _ in range(h)]
        self._particles = []
        for _ in range(120):
            self._spawn_particle(w, h)
        self._w, self._h = w, h
        # Initialize tracer
        self._tracer = {
            "x": float(w // 2),
            "y": float(h // 2),
            "life": 9999,
            "speed": 1.2,
            "color": "bright",
        }
        self._tracer_trail = []

    def _spawn_particle(self, w, h):
        rng = self._rng
        self._particles.append({
            "x":    rng.uniform(0, w),
            "y":    rng.uniform(1, h - 1),
            "life": rng.randint(40, 120),
            "speed": rng.uniform(0.3, 1.4),
            "color": rng.choice(["bright", "accent", "soft"]),
            "vx": 0.0,
            "vy": 0.0,
        })

    def _field(self, x, y, t, w, h):
        """Curl-like noise field: vx, vy derived from overlapping sine waves."""
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

        # Target particle count: up to 600
        target_n = int(120 + 480 * intensity)
        while len(self._particles) < min(target_n, self._MAX_PARTICLES):
            self._spawn_particle(w, h)

        # Particle chars graduated by speed
        def _speed_char(speed: float) -> str:
            if speed < 0.5:
                return "\u00b7"   # ·  slow
            elif speed < 0.8:
                return "."         # . medium
            elif speed < 1.1:
                return "\u2022"   # • fast
            else:
                return "\u25e6"   # ◦ very fast

        live = []
        for p in self._particles:
            vx, vy = self._field(p["x"], p["y"], t, w, h)
            p["vx"] = vx * p["speed"]
            p["vy"] = vy * p["speed"]
            p["x"] += p["vx"]
            p["y"] += p["vy"] * 0.5  # terminal aspect
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

        # Step the flow tracer
        if self._tracer:
            tr = self._tracer
            tvx, tvy = self._field(tr["x"], tr["y"], t, w, h)
            tr["x"] = (tr["x"] + tvx * 1.2) % w
            tr["y"] = tr["y"] + tvy * 0.6
            if tr["y"] < 1:
                tr["y"] = 1.0
            elif tr["y"] >= h - 1:
                tr["y"] = float(h - 2)
            self._tracer_trail.append((int(tr["x"]), int(tr["y"])))
            if len(self._tracer_trail) > 20:
                self._tracer_trail.pop(0)

        # Direction arrows for density map
        arrows = "\u2190\u2196\u2191\u2197\u2192\u2198\u2193\u2199"  # ←↖↑↗→↘↓↙

        # Decay trail and render
        decay  = 0.90 - 0.05 * intensity
        for y in range(1, h - 1):
            row = trail[y]
            for x in range(0, w - 1):
                v = row[x] * decay
                row[x] = v

                if v > 0.08:
                    fchars = "\u00b7.:+*\u2593"
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
                elif (x % 6 == 3) and (y % 4 == 2):
                    # Sparse density map: faint field direction arrow
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

        # Draw flow tracer trail with '━' chars
        tracer_attr = bright_attr
        for i, (tx, ty) in enumerate(self._tracer_trail[:-1]):
            if 1 <= ty < h - 1 and 0 <= tx < w - 1:
                try:
                    stdscr.addstr(ty, tx, "\u2501", accent_attr if i < 10 else soft_attr)
                except curses.error:
                    pass
        # Draw tracer head
        if self._tracer:
            tx, ty = int(self._tracer["x"]), int(self._tracer["y"])
            if 1 <= ty < h - 1 and 0 <= tx < w - 1:
                try:
                    stdscr.addstr(ty, tx, "\u2501", bright_attr)
                except curses.error:
                    pass

        # Bright particle heads with velocity-angle color and graduated chars
        for p in self._particles:
            if p["life"] > 8:
                px, py = int(p["x"]), int(p["y"])
                if 1 <= py < h - 1 and 0 <= px < w - 1:
                    speed = math.sqrt(p["vx"]**2 + p["vy"]**2)
                    ch = _speed_char(speed)
                    # Color by velocity angle
                    angle = math.atan2(p["vy"], p["vx"])
                    angle_phase = (angle + math.pi) / (2 * math.pi)
                    if angle_phase > 0.66:
                        attr = bright_attr
                    elif angle_phase > 0.33:
                        attr = accent_attr
                    else:
                        attr = soft_attr
                    try:
                        stdscr.addstr(py, px, ch, attr)
                    except curses.error:
                        pass


register(FlowFieldPlugin())