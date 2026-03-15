"""Redesigned themes 37-42 + 3 extreme new screens using full-screen ASCII field engine."""

from __future__ import annotations

import curses
import math
import random
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin, Reaction, ReactiveElement, SpecialEffect
from hermes_neurovision.theme_plugins import register


def _safe(stdscr, y: int, x: int, ch: str, attr: int = 0) -> None:
    try:
        stdscr.addstr(y, x, ch, attr)
    except curses.error:
        pass


# ── Starfall v2: 3D perspective starfield ─────────────────────────────────────

class StarfallV2Plugin(ThemePlugin):
    """3D perspective starfield — stars stream toward the viewer."""
    name = "starfall"

    def __init__(self):
        self._stars = None

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init_stars(self, w, h, rng):
        self._stars = [
            {'sx': rng.uniform(-1, 1), 'sy': rng.uniform(-1, 1), 'sz': rng.uniform(0.01, 1.0)}
            for _ in range(200)
        ]

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        rng = state.rng

        if self._stars is None:
            self._init_stars(w, h, rng)

        stars = self._stars
        intensity = state.intensity_multiplier

        # Move stars toward viewer
        for star in stars:
            star['sz'] -= 0.015 + 0.01 * intensity
            if star['sz'] <= 0:
                star['sx'] = rng.uniform(-1, 1)
                star['sy'] = rng.uniform(-1, 1)
                star['sz'] = 1.0

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr = curses.color_pair(color_pairs["soft"])
        base_dim_attr = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        depth_chars = " \u00b7\u2219\u2022\u25e6\u25cb\u25cf\u25c9"  # 8 chars

        for star in stars:
            sz = star['sz']
            scale = 1.0 / (sz + 0.01)
            px = int(w / 2 + star['sx'] * scale * w * 0.45)
            py = int(h / 2 + star['sy'] * scale * h * 0.42)

            if not (1 <= py <= h - 2 and 0 <= px <= w - 2):
                continue

            depth_idx = int((1 - sz) * 7)
            depth_idx = max(0, min(7, depth_idx))
            ch = depth_chars[depth_idx]

            if sz < 0.2:
                attr = bright_attr
            elif sz < 0.4:
                attr = accent_attr
            elif sz < 0.7:
                attr = soft_attr
            else:
                attr = base_dim_attr

            try:
                stdscr.addstr(py, px, ch, attr)
            except curses.error:
                pass

            # Short streak behind fast-moving near stars
            if sz < 0.25:
                streak_py = py - 1
                if 1 <= streak_py <= h - 2:
                    try:
                        stdscr.addstr(streak_py, px, "\u00b7", base_dim_attr)
                    except curses.error:
                        pass


# ── Quasar v2: Bipolar jets + accretion disk ──────────────────────────────────

class QuasarV2Plugin(ThemePlugin):
    """Bipolar relativistic jets and accretion disk — stellar color scheme, high energy."""
    name = "quasar"

    # Rainbow pairs for stellar spectrum: claim pairs 20-25
    _RAINBOW_READY = False

    @classmethod
    def _ensure_stellar(cls):
        if cls._RAINBOW_READY:
            return
        try:
            # Hot stellar palette: white-blue core → gold disk → deep field
            curses.init_pair(20, curses.COLOR_WHITE,   -1)  # white-hot core
            curses.init_pair(21, curses.COLOR_CYAN,    -1)  # blue jet plasma
            curses.init_pair(22, curses.COLOR_YELLOW,  -1)  # gold inner disk
            curses.init_pair(23, curses.COLOR_RED,     -1)  # outer disk / corona
            curses.init_pair(24, curses.COLOR_BLUE,    -1)  # magnetic field
            curses.init_pair(25, curses.COLOR_MAGENTA, -1)  # jet shock front
            cls._RAINBOW_READY = True
        except Exception:
            pass

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        self._ensure_stellar()

        w = state.width
        h = state.height
        f = state.frame
        intensity = state.intensity_multiplier

        cx = w / 2.0
        cy = h / 2.0

        # Stellar palette — overrides the default theme palette
        core_attr    = curses.color_pair(20) | curses.A_BOLD   # white-hot
        jet_attr     = curses.color_pair(21) | curses.A_BOLD   # electric cyan
        jet_dim_attr = curses.color_pair(24)                   # deep blue
        disk_inner   = curses.color_pair(22) | curses.A_BOLD   # gold bright
        disk_mid     = curses.color_pair(22)                   # gold
        disk_outer   = curses.color_pair(23)                   # red-orange corona
        shock_attr   = curses.color_pair(25) | curses.A_BOLD   # magenta shock
        field_attr   = curses.color_pair(24) | curses.A_DIM    # dim blue field
        void_attr    = curses.color_pair(24) | curses.A_DIM    # deep space

        # Disk thickness pulses slightly with intensity
        disk_half   = 2.5 + intensity * 1.5
        disk_r_max  = w * 0.38
        disk_r_min  = 2.5
        jet_half_w  = 1.5 + intensity * 0.8

        # Jet energy: brightness surges with intensity
        jet_reach   = h * 0.48 * max(0.3, intensity)

        for y in range(1, h - 1):
            dy = y - cy
            for x in range(0, w - 1):
                dx = x - cx
                # Elliptical distance (terminal aspect: chars are ~2:1)
                dist_e = math.sqrt(dx * dx / 2.25 + dy * dy)
                dist   = math.sqrt(dx * dx + dy * dy)
                angle  = math.atan2(dy, dx)

                ch   = " "
                attr = void_attr

                # ── Bipolar jets (vertical axis, higher priority than disk) ──
                # Width widens slightly with distance from core (jet expansion)
                jet_w_at_y = jet_half_w + abs(dy) * 0.04
                if abs(dx) < jet_w_at_y and abs(dy) > disk_half:
                    jet_dist = abs(dy) - disk_half
                    jet_v    = max(0.0, 1.0 - jet_dist / max(1.0, jet_reach))
                    if jet_v > 0.0:
                        # Plasma columns — character varies with frame for flicker
                        phase = (y + f) % 5
                        if jet_v > 0.75:
                            ch   = "║" if phase < 3 else "┃"
                            attr = jet_attr
                        elif jet_v > 0.45:
                            ch   = "│" if phase < 3 else "╎"
                            attr = jet_attr if (x + y + f) % 3 != 0 else shock_attr
                        else:
                            # Jet fading edge — diffuse plasma
                            ch   = "·" if phase < 3 else ":"
                            attr = jet_dim_attr
                        # Shock knots: bright flares that travel up/down jet
                        knot_phase = (int(abs(dy)) + f // 4) % 12
                        if knot_phase < 2 and jet_v > 0.5:
                            ch   = "◈" if knot_phase == 0 else "●"
                            attr = shock_attr

                # ── Accretion disk (horizontal ellipse) ──────────────────────
                elif abs(dy) < disk_half + math.sin(x * 0.28 + f * 0.035) * 1.2 \
                        and disk_r_min < dist_e < disk_r_max:
                    disk_v = max(0.0, 1.0 - dist_e / disk_r_max)
                    # Doppler: left side redshifted, right blue-shifted
                    doppler = dx / max(cx, 1.0)   # -1=left(red), +1=right(blue)
                    # Disk scrolls: material orbits (inner faster)
                    scroll  = (x - f * max(0.3, 2.0 / max(dist_e, 1.0))) % w
                    turb    = math.sin(scroll * 0.4 + dy * 1.2 + f * 0.06) * 0.5 + 0.5

                    disk_chars = "─═≈~·"
                    idx = int(turb * (len(disk_chars) - 1))
                    ch  = disk_chars[idx]

                    if dist_e < disk_r_max * 0.25:
                        # Inner hot zone: gold-white, rapidly rotating
                        attr = disk_inner
                    elif dist_e < disk_r_max * 0.55:
                        # Mid disk: gold
                        attr = disk_mid
                    else:
                        # Outer corona: red-orange
                        attr = disk_outer

                # ── Magnetic field lines (rest of the space) ─────────────────
                else:
                    # Hourglass field topology: field lines loop from jet poles
                    # to disk equator — visualised as faint arc pattern
                    field_r   = math.sqrt(dx * dx / 1.5 + dy * dy)
                    # Dipole potential contours: sin(angle)*r^-2 analog
                    sin_lat   = abs(dy) / max(dist, 0.5)
                    field_v   = abs(math.sin(field_r * 0.22 - f * 0.015)
                                    * math.cos(sin_lat * 2.8)) * 0.5 * intensity
                    # Only draw field in the funnel region (|angle| close to 0 or pi)
                    if field_v > 0.08 and dist_e > disk_r_max * 0.6:
                        # Character conveys field direction
                        if abs(dy) > abs(dx) * 1.2:
                            ch = "│" if abs(dx) < 2 else "╲" if dx > 0 else "╱"
                        else:
                            ch = "─"
                        attr = field_attr if field_v < 0.25 else jet_dim_attr
                    else:
                        # Deep space: sparse background stars
                        star = math.sin(x * 37.3 + y * 19.7) * math.cos(x * 11.1 + y * 5.3)
                        if star > 0.90:
                            ch   = "·"
                            attr = field_attr

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

        # ── Core singularity ─────────────────────────────────────────────────
        core_y = int(cy)
        core_x = int(cx)
        # Pulsing core glyph — flickers rapidly
        core_ch = "◉" if (f // 2) % 2 == 0 else "⊕"
        for oy, ox, gch, gattr in [
            (0,  0,  core_ch, core_attr),
            (0, -1,  "◈",     disk_inner),
            (0,  1,  "◈",     disk_inner),
            (-1, 0,  "·",     jet_attr),
            (1,  0,  "·",     jet_attr),
        ]:
            gy, gx = core_y + oy, core_x + ox
            if 1 <= gy <= h - 2 and 0 <= gx <= w - 2:
                try:
                    stdscr.addstr(gy, gx, gch, gattr)
                except curses.error:
                    pass


# ── Supernova v2: Periodic explosion cycle ────────────────────────────────────

class SupernovaV2Plugin(ThemePlugin):
    """Periodic explosion cycle — implosion, shockwave, nebula, fade.

    v0.2: neural_field emergent (stellar plasma), warp_field (spacetime distortion),
    echo_decay (blast afterimages), force_points (blast pressure), full reactive
    event system (agent_start triggers detonation), palette_shift (phases shift hue),
    special_effects (cataclysm mode), intensity_curve (threshold ignition).
    """
    name = "supernova"

    # Phase durations (sum = 600)
    _PHASE_IMPLODE  = 100   # 0   – 99:  core collapse / implosion
    _PHASE_BLAST    = 250   # 100 – 349: shockwave ring
    _PHASE_NEBULA   = 200   # 350 – 549: nebula expansion
    _PHASE_FADE     = 50    # 550 – 599: remnant wisps
    _CYCLE          = 600

    def __init__(self):
        super().__init__()
        # Forced phase-skip: when agent_start fires we jump straight to blast
        self._force_phase: Optional[int] = None
        # Cycle offset — maintained so forced transitions continue naturally
        self._cycle_offset: int = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    # ── v0.2: Emergent ────────────────────────────────────────────────────────
    def neural_field_config(self):
        # Stellar plasma: fast-firing, short refractory — creates crackling texture
        return {"threshold": 2, "fire_duration": 2, "refractory": 3}

    def emergent_layer(self):
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────
    def warp_field(self, x, y, w, h, frame, intensity):
        # Spacetime curvature — gravity well at centre distorts surrounding space.
        # Strongest during implosion, fades away during nebula phase.
        phase = frame % self._CYCLE
        if phase >= self._PHASE_IMPLODE + self._PHASE_BLAST:
            return (x, y)   # nebula/fade: no warp
        cx, cy = w / 2.0, h / 2.0
        nx = (x - cx) / max(cx, 1.0)
        ny = (y - cy) / max(cy, 1.0)
        dist = math.sqrt(nx * nx + ny * ny * 2.0) + 0.001
        # Implode: inward pull; blast: outward push
        if phase < self._PHASE_IMPLODE:
            t = phase / self._PHASE_IMPLODE
            strength = intensity * 2.5 * (1.0 - t)   # fades as core ignites
            pull = -strength / dist                   # inward
        else:
            t = (phase - self._PHASE_IMPLODE) / self._PHASE_BLAST
            strength = intensity * 3.0 * math.exp(-t * 2.5)   # sharp blast, decays fast
            pull = strength / dist                    # outward
        wx = int(pull * nx * 0.5)
        wy = int(pull * ny * 0.5)
        return (max(0, min(w - 1, x + wx)), max(0, min(h - 1, y + wy)))

    def echo_decay(self):
        # Blast rings leave burning afterimages for 5 frames
        return 5

    def glow_radius(self):
        # Shockwave front glows
        return 2

    def force_points(self, w, h, frame, intensity):
        # During blast phase: radial pressure wave pushes outward from centre.
        phase = frame % self._CYCLE
        if self._PHASE_IMPLODE <= phase < self._PHASE_IMPLODE + self._PHASE_BLAST:
            t = (phase - self._PHASE_IMPLODE) / self._PHASE_BLAST
            strength = intensity * 1.5 * math.exp(-t * 3.0)
            return [{"x": w // 2, "y": h // 2, "strength": strength, "type": "radial"}]
        return []

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────
    def intensity_curve(self, raw):
        # Hard threshold: below 0.25 the star is dormant; above it ignites fast
        if raw < 0.25:
            return raw * 0.4
        return 0.1 + 0.9 * ((raw - 0.25) / 0.75) ** 0.7

    # ── v0.2: Reactive ────────────────────────────────────────────────────────
    def react(self, event_kind, data):
        # Agent start: the star ignites — jump straight to blast
        if event_kind == "agent_start":
            self._force_phase = self._PHASE_IMPLODE  # skip to shockwave
            return Reaction(
                element=ReactiveElement.PULSE,
                intensity=1.0,
                origin=(0.5, 0.5),
                color_key="bright",
                duration=2.5,
            )
        # LLM generating: pre-ignition stellar accretion — STREAM from edge
        if event_kind == "llm_start":
            return Reaction(
                element=ReactiveElement.STREAM,
                intensity=0.8,
                origin=(0.0, 0.5),
                color_key="accent",
                duration=2.5,
            )
        # Each token: photon ejection — SPARK at random sky position
        if event_kind == "llm_chunk":
            return Reaction(
                element=ReactiveElement.SPARK,
                intensity=0.35,
                origin=(random.random(), random.random()),
                color_key="soft",
                duration=0.5,
            )
        # LLM end: emission line fades — soft RIPPLE
        if event_kind == "llm_end":
            return Reaction(
                element=ReactiveElement.RIPPLE,
                intensity=0.5,
                origin=(0.5, 0.5),
                color_key="soft",
                duration=1.5,
            )
        # Tool call: instrument measuring the explosion — RIPPLE at field position
        if event_kind in ("tool_call", "mcp_tool_call"):
            return Reaction(
                element=ReactiveElement.RIPPLE,
                intensity=0.75,
                origin=(random.random(), random.random()),
                color_key="accent",
                duration=1.8,
            )
        # Memory/skill: heavy element synthesis — BLOOM (nucleosynthesis burst)
        if event_kind in ("memory_save", "skill_create"):
            return Reaction(
                element=ReactiveElement.BLOOM,
                intensity=1.0,
                origin=(0.5, 0.5),
                color_key="bright",
                duration=3.0,
            )
        # Error/crash: stellar instability — SHATTER + trigger cataclysm phase-skip
        if event_kind in ("error", "crash"):
            self._force_phase = self._PHASE_IMPLODE
            return Reaction(
                element=ReactiveElement.SHATTER,
                intensity=1.0,
                origin=(0.5, 0.5),
                color_key="warning",
                duration=2.5,
            )
        # Compression: stellar compression event — WAVE sweeping inward
        if event_kind in ("compression_started", "checkpoint_rollback"):
            return Reaction(
                element=ReactiveElement.WAVE,
                intensity=0.9,
                origin=(1.0, 0.5),
                color_key="accent",
                duration=2.0,
            )
        # Cron/background: pulsar timing signal — ORBIT
        if event_kind in ("cron_tick", "background_proc"):
            return Reaction(
                element=ReactiveElement.ORBIT,
                intensity=0.45,
                origin=(0.5, 0.5),
                color_key="soft",
                duration=3.5,
            )
        # Subagent: secondary stellar ignition — BLOOM off-centre
        if event_kind == "subagent_started":
            return Reaction(
                element=ReactiveElement.BLOOM,
                intensity=0.8,
                origin=(random.uniform(0.2, 0.8), random.uniform(0.2, 0.8)),
                color_key="accent",
                duration=2.0,
            )
        # Dangerous cmd / approval: radiation warning — SPARK at centre
        if event_kind in ("dangerous_cmd", "approval_request"):
            return Reaction(
                element=ReactiveElement.SPARK,
                intensity=1.0,
                origin=(0.5, 0.5),
                color_key="warning",
                duration=2.0,
            )
        # Context pressure: Chandrasekhar limit approaching — GAUGE
        if event_kind in ("context_pressure", "token_usage"):
            return Reaction(
                element=ReactiveElement.GAUGE,
                intensity=data.get("ratio", 0.7),
                origin=(0.05, 0.95),
                color_key="warning",
                duration=3.0,
            )
        return None

    def palette_shift(self, trigger_effect, intensity, base_palette):
        # Implosion/error phase: core collapse — deep red-white
        if trigger_effect in ("error", "crash") or str(trigger_effect) == str(ReactiveElement.SHATTER):
            return (curses.COLOR_RED, curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_RED)
        # Memory/skill: nucleosynthesis — cyan-white brilliance
        if trigger_effect in ("memory_save", "skill_create") or str(trigger_effect) == str(ReactiveElement.BLOOM):
            return (curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_WHITE, curses.COLOR_YELLOW)
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────
    def special_effects(self):
        return [
            # Cataclysm: full detonation on demand — resets cycle to blast
            SpecialEffect(
                name="supernova-cataclysm",
                trigger_kinds=["burst"],
                min_intensity=0.5,
                cooldown=8.0,
                duration=4.0,
            ),
        ]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        if special_name != "supernova-cataclysm":
            return
        w, h = state.width, state.height
        cx, cy = w // 2, h // 2
        attr_w = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        attr_a = curses.color_pair(color_pairs.get("accent", 0))
        attr_s = curses.color_pair(color_pairs.get("soft", 0))
        # Three concentric expanding rings at different speeds
        max_r = min(w // 2 - 1, h - 2)
        for ring, (speed, attr) in enumerate([(1.0, attr_w), (0.7, attr_a), (0.45, attr_s)]):
            r = int(max_r * progress * speed)
            if r < 1:
                continue
            chars = "◉●◎○·"
            ci = int(progress * (len(chars) - 1)) % len(chars)
            steps = max(24, r * 3)
            for i in range(steps):
                theta = (i / steps) * math.tau
                px = int(cx + r * math.cos(theta) * 2)
                py = int(cy + r * math.sin(theta))
                if 0 <= px < w and 0 <= py < h:
                    _safe(stdscr, py, px, chars[ci], attr)
        # Detonation core flash at centre
        if progress < 0.3:
            core_chars = "◉●◎"
            ci = int(progress / 0.3 * len(core_chars)) % len(core_chars)
            _safe(stdscr, cy, cx, core_chars[ci], attr_w)

    # ── v0.2: Ambient ─────────────────────────────────────────────────────────
    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        # When idle, the star gently pulses — a pre-main-sequence flicker
        if idle_seconds > 2.0 and state.frame % 20 == 0:
            w, h = state.width, state.height
            cx, cy = w // 2, h // 2
            r = int(2 + 2 * abs(math.sin(state.frame * 0.04)))
            attr = curses.color_pair(color_pairs.get("soft", 0)) | curses.A_DIM
            for deg in range(0, 360, 30):
                theta = math.radians(deg)
                px = int(cx + r * math.cos(theta) * 2)
                py = int(cy + r * math.sin(theta))
                if 0 <= px < w and 0 <= py < h:
                    _safe(stdscr, py, px, "·", attr)

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        intensity = state.intensity_multiplier

        cx = w / 2.0
        cy = h / 2.0

        # Honour forced phase-skip from reactive events.
        # We compute a persistent cycle_offset so the cycle continues running
        # smoothly from the forced position — not jumping back on the next frame.
        if self._force_phase is not None:
            # Align offset so that (f + offset) % CYCLE == force_phase
            self._cycle_offset = (self._force_phase - f) % self._CYCLE
            self._force_phase = None
        phase = (f + self._cycle_offset) % self._CYCLE

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr = curses.color_pair(color_pairs["soft"])
        base_dim_attr = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        density_chars = "\u00b7.:+*#@\u25c9"
        block_chars = "\u2591\u2592\u2593\u2588\u2593\u2592\u2591"

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                dx = x - cx
                dy = y - cy
                dist = math.sqrt(dx * dx / 2.25 + dy * dy)
                max_dist = math.sqrt((w / 2) ** 2 / 2.25 + (h / 2) ** 2)
                dist_n = dist / max(max_dist, 1.0)

                ch = " "
                attr = base_dim_attr

                if phase < 100:
                    # Implosion / core buildup
                    t = phase / 100.0
                    v = max(0.0, 1 - dist_n * (3 + t * 5)) * intensity
                    if v > 0:
                        ci = int(v * (len(density_chars) - 1))
                        ch = density_chars[ci]
                        if v > 0.5:
                            attr = bright_attr
                        elif v > 0.2:
                            attr = accent_attr
                        else:
                            attr = soft_attr

                elif phase < 350:
                    # Expanding shockwave
                    t = (phase - 100) / 250.0
                    ring_r = dist_n - t * 1.1
                    ring_v = max(0.0, 1 - abs(ring_r) * 15) * intensity
                    ring2_r = dist_n - t * 0.8
                    ring2_v = max(0.0, 1 - abs(ring2_r) * 20) * 0.5 * intensity
                    if ring_v > 0.05:
                        ci = int(ring_v * (len(block_chars) - 1))
                        ch = block_chars[ci]
                        if ring_v > 0.5:
                            attr = bright_attr
                        else:
                            attr = accent_attr
                    elif ring2_v > 0.1:
                        ch = "\u00b7"
                        attr = accent_attr

                elif phase < 550:
                    # Nebula expansion — shell grows outward, inner core clears.
                    # t 0→1: the hot shell front moves from dist_n≈0.15 to dist_n≈1.1
                    # so the nebula always marches AWAY from the origin.
                    t = (phase - 350) / 200.0
                    # Shell centre radius travels 0.12 → 1.1 (expands outward)
                    shell_r = 0.12 + t * 0.98
                    # Shell is thickest early, spreads thin as it expands
                    shell_w = 0.35 + t * 0.30
                    # Radial distance from the shell front
                    delta = abs(dist_n - shell_r)
                    envelope = max(0.0, 1.0 - delta / max(shell_w, 0.01))
                    # Turbulent texture — rippling waves on the ejecta shell
                    angle = math.atan2(dy, dx)
                    ripple = abs(math.sin(dist_n * 18 + angle * 4 - f * 0.035)) * 0.7 + 0.3
                    nebula_v = envelope * ripple * intensity
                    if nebula_v > 0.05:
                        dense_chars = " ·.:+*#"
                        ci = int(nebula_v * (len(dense_chars) - 1))
                        ch = dense_chars[ci]
                        # Angle-based color sweeping over time — sector rotates
                        sector = int((angle + math.pi + f * 0.015) / (math.pi / 3)) % 3
                        if sector == 0:
                            attr = soft_attr
                        elif sector == 1:
                            attr = accent_attr
                        else:
                            attr = bright_attr if nebula_v > 0.45 else accent_attr

                else:
                    # Fade — remnant wisps disperse at the outer edge, leaving
                    # a faint expanding ghost ring that slowly dissolves.
                    t = (phase - 550) / 50.0
                    angle = math.atan2(dy, dx)
                    # Ghost ring at dist_n ≈ 1.0–1.2, fading by t
                    ghost = max(0.0, 1.0 - abs(dist_n - (1.0 + t * 0.3)) * 6.0)
                    drift = abs(math.sin(angle * 3 + f * 0.02)) * 0.5
                    v = ghost * (0.3 + drift * 0.3) * (1.0 - t) * intensity
                    if v > 0.06:
                        ch = "·" if v < 0.18 else ":"
                        sector = int((angle + math.pi + f * 0.01) / (math.pi / 2)) % 2
                        attr = soft_attr if sector == 0 else accent_attr

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


# ── Sol v2: Solar plasma with convection cells ────────────────────────────────

class SolV2Plugin(ThemePlugin):
    """Living solar surface — granulation, eruptions, coronal loops, limb darkening.

    v0.2 upgrade:
      - neural_field: crackling photospheric convection fires as emergent substrate
      - warp_field: magnetic buoyancy warps the surface near active regions
      - echo_decay: solar flares leave burning 6-frame afterimages
      - glow_radius: bright granules bloom
      - force_points: 4 magnetic flux tubes orbit the equator as vortex attractors
      - intensity_curve: sigmoid — below 0.3 the sun is quiet, above it flares
      - react() x10: llm_start → coronal mass ejection WAVE, error → SHATTER
        (X-class flare), memory_save → BLOOM (new active region), tool_call
        → RIPPLE (pressure wave), agent_start → PULSE (photospheric shock)
      - palette_shift: error → red/orange (X-class flare), memory → white/gold
      - special_effects: "solar-eruption" — magnetic loop arcs from equator
      - ambient_tick: granule shimmer when idle
    """
    name = "sol"

    def __init__(self):
        self._cells = None
        self._w = 0
        self._h = 0
        # Track active-region centres for flare targeting
        self._active_region: Optional[Tuple[float, float]] = None
        self._flare_arm = 0  # which magnetic arm fires next

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    # ── v0.2: Emergent ────────────────────────────────────────────────────────
    def neural_field_config(self):
        # Photospheric convection: fast cells, short refractory — bright crackling
        return {"threshold": 2, "fire_duration": 3, "refractory": 4}

    def emergent_layer(self):
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────
    def warp_field(self, x, y, w, h, frame, intensity):
        # Magnetic buoyancy near active regions bends the visual field.
        # Strong near the equator (y ≈ 0.5), weak near poles.
        cx, cy = w / 2.0, h / 2.0
        ny = (y - cy) / max(cy, 1.0)
        # Equatorial buoyancy swell: strongest at latitude 0
        lat_weight = max(0.0, 1.0 - abs(ny) * 2.5)
        t = frame * 0.025
        amp = intensity * 2.0 * lat_weight
        wx = int(amp * math.sin(t * 1.4 + y * 0.22))
        wy = int(amp * 0.35 * math.cos(t * 0.9 + x * 0.15))
        return (max(0, min(w - 1, x + wx)), max(0, min(h - 1, y + wy)))

    def echo_decay(self):
        # Flares burn afterimages — bright streaks hang for 6 frames
        return 6

    def glow_radius(self):
        # Bright granules and flare tips bloom
        return 2

    def force_points(self, w, h, frame, intensity):
        # Four magnetic flux tube clusters orbit the equator.
        # They pull nearby field lines in, mimicking active-region magnetism.
        cx, cy = w / 2.0, h / 2.0
        r = min(w, h * 2.0) * 0.25
        t = frame * 0.018
        strength = 0.3 + intensity * 0.5
        return [
            {"x": int(cx + r * math.cos(t + i * math.pi / 2)),
             "y": int(cy + r * math.sin(t + i * math.pi / 2) * 0.35),
             "strength": strength, "type": "vortex"}
            for i in range(4)
        ]

    def depth_layers(self):
        # 2 depth layers: granules mid-depth, corona at back
        return 2

    # ── v0.2: Intensity curve — sigmoid, sun is quiet below 0.3 ──────────────
    def intensity_curve(self, raw):
        x = (raw - 0.35) * 8.0
        return 1.0 / (1.0 + math.exp(-x))

    # ── v0.2: Reactive ────────────────────────────────────────────────────────
    def react(self, event_kind, data):
        import random as _r
        if event_kind == "agent_start":
            # Photospheric shock wave — PULSE from centre
            return Reaction(element=ReactiveElement.PULSE, intensity=1.0,
                           origin=(0.5, 0.5), color_key="bright", duration=2.5)
        if event_kind == "llm_start":
            # Coronal mass ejection — WAVE sweeping from the limb
            return Reaction(element=ReactiveElement.WAVE, intensity=0.9,
                           origin=(0.0, 0.5), color_key="accent", duration=3.0)
        if event_kind == "llm_chunk":
            # Photon burst — SPARK at random active latitude
            lat = _r.uniform(0.3, 0.7)
            lon = _r.random()
            return Reaction(element=ReactiveElement.SPARK, intensity=0.45,
                           origin=(lon, lat), color_key="bright", duration=0.5)
        if event_kind == "llm_end":
            # Post-flare loop — soft RIPPLE from equatorial zone
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.55,
                           origin=(0.5, 0.5), color_key="soft", duration=1.8)
        if event_kind in ("tool_call", "mcp_tool_call"):
            # Pressure wave from a new active region — RIPPLE
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.75,
                           origin=(_r.uniform(0.2, 0.8), _r.uniform(0.35, 0.65)),
                           color_key="accent", duration=1.8)
        if event_kind in ("memory_save", "skill_create"):
            # New active magnetic region emerges — BLOOM, gold nucleosynthesis
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                           origin=(0.5, 0.5), color_key="bright", duration=3.0)
        if event_kind in ("error", "crash"):
            # X-class flare — SHATTER, red-orange eruption
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.5)
        if event_kind in ("cron_tick", "background_proc"):
            # Sunspot rotation — ORBIT at equatorial belt
            self._flare_arm = (self._flare_arm + 1) % 4
            ox = 0.25 + self._flare_arm * 0.165
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.45,
                           origin=(ox, 0.5), color_key="soft", duration=3.5)
        if event_kind == "subagent_started":
            # Secondary flare site — BLOOM off-axis
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.75,
                           origin=(_r.uniform(0.15, 0.85), _r.uniform(0.3, 0.7)),
                           color_key="accent", duration=2.0)
        if event_kind in ("context_pressure", "token_usage"):
            # Rising flux — GAUGE at bottom edge (chromosphere fill)
            return Reaction(element=ReactiveElement.GAUGE,
                           intensity=data.get("ratio", 0.6),
                           origin=(0.05, 0.9), color_key="warning", duration=3.0)
        if event_kind in ("dangerous_cmd", "approval_request"):
            return Reaction(element=ReactiveElement.SPARK, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────
    def palette_shift(self, trigger_effect, intensity, base_palette):
        if trigger_effect in ("error", "crash") or str(trigger_effect) == str(ReactiveElement.SHATTER):
            # X-class flare — red-orange chromosphere
            return (curses.COLOR_RED, curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_RED)
        if trigger_effect in ("memory_save", "skill_create") or str(trigger_effect) == str(ReactiveElement.BLOOM):
            # Active region — white-gold photosphere
            return (curses.COLOR_WHITE, curses.COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_RED)
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────
    def special_effects(self):
        return [
            SpecialEffect(name="solar-eruption",
                         trigger_kinds=["burst", "llm_start"],
                         min_intensity=0.5, cooldown=6.0, duration=3.5),
        ]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        if special_name != "solar-eruption":
            return
        w, h = state.width, state.height
        # Magnetic loop arc rises from equator — an inverted catenary arch
        # that peaks higher and wider as progress grows
        cx = w // 2
        base_y = int(h * 0.55)
        peak_rise = int(h * 0.35 * math.sin(progress * math.pi))
        half_w = int(w * 0.25 * progress)
        attr_b = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        attr_a = curses.color_pair(color_pairs.get("accent", 0))
        loop_chars = "◌○◎◉●"
        steps = max(40, half_w * 4)
        for i in range(steps + 1):
            t = i / max(steps, 1)
            # Catenary-ish arc: x goes -1 → +1, y follows sin-arch
            arc_x = int(cx + (t * 2 - 1) * half_w * 2)
            arc_height = math.sin(t * math.pi)  # 0→1→0
            arc_y = int(base_y - arc_height * peak_rise)
            if 0 <= arc_x < w and 0 <= arc_y < h:
                ci = int(t * (len(loop_chars) - 1)) % len(loop_chars)
                attr = attr_b if arc_height > 0.65 else attr_a
                _safe(stdscr, arc_y, arc_x, loop_chars[ci], attr)

    # ── v0.2: Ambient tick — quiet sun shimmer ────────────────────────────────
    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        # A gentle granule flicker at the disc limb when idle
        if idle_seconds > 1.5 and state.frame % 12 == 0:
            w, h = state.width, state.height
            import random as _r
            rng2 = _r.Random(state.frame % 1000)
            cx, cy = w / 2.0, h / 2.0
            for _ in range(3):
                # Random point on disc edge
                theta = rng2.uniform(0, math.tau)
                px = int(cx + math.cos(theta) * cx * 0.88)
                py = int(cy + math.sin(theta) * cy * 0.80)
                if 0 <= px < w and 1 <= py < h - 1:
                    attr = curses.color_pair(color_pairs.get("soft", 0))
                    _safe(stdscr, py, px, "·", attr)

    def _init_cells(self, rng):
        self._cells = [
            {
                'x': rng.uniform(0, 1),
                'y': rng.uniform(0, 1),
                'vx': rng.uniform(-0.001, 0.001),
                'vy': rng.uniform(-0.001, 0.001),
            }
            for _ in range(25)
        ]

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        intensity = state.intensity_multiplier
        rng = state.rng

        if self._cells is None or w != self._w or h != self._h:
            self._init_cells(rng)
            self._w = w
            self._h = h

        cells = self._cells

        # Drift cell centers
        for c in cells:
            c['x'] += c['vx']
            c['y'] += c['vy']
            if c['x'] < 0.0 or c['x'] > 1.0:
                c['vx'] = -c['vx']
                c['x'] = max(0.0, min(1.0, c['x']))
            if c['y'] < 0.0 or c['y'] > 1.0:
                c['vy'] = -c['vy']
                c['y'] = max(0.0, min(1.0, c['y']))

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr = curses.color_pair(color_pairs["soft"])
        base_dim_attr = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        granule_chars = "\u2591\u2592\u2593\u2588"
        density_chars = ".:+#@\u25c9"

        # Solar flare parameters
        flare_phase = f % 200
        draw_flare = flare_phase < 40

        for y in range(1, h - 1):
            ny = y / h
            for x in range(0, w - 1):
                nx = x / w

                # Limb darkening
                limb_dist = math.sqrt((nx - 0.5) ** 2 + (ny - 0.5) ** 2) * 2
                limb_v = max(0.0, 1 - limb_dist * 1.1)

                if limb_dist > 1.0:
                    # Corona
                    corona_v = max(0.0, 0.4 / (limb_dist + 0.1) - 0.3) * intensity
                    if corona_v > 0.02:
                        try:
                            stdscr.addstr(y, x, "\u00b7", base_dim_attr)
                        except curses.error:
                            pass
                    continue

                # Find 2 nearest Voronoi cell centers
                dists = []
                for ci, c in enumerate(cells):
                    ddx = nx - c['x']
                    ddy = ny - c['y']
                    dists.append(ddx * ddx + ddy * ddy)
                dists_sorted = sorted(range(len(dists)), key=lambda i: dists[i])
                dist_1st = math.sqrt(dists[dists_sorted[0]])
                dist_2nd = math.sqrt(dists[dists_sorted[1]])
                edge = dist_2nd - dist_1st

                ch = " "
                attr = base_dim_attr

                if edge < 0.02:
                    # Intergranular lane
                    if limb_v > 0.1:
                        ch = "\u2500" if (x + y) % 2 == 0 else "\u2502"
                        attr = base_dim_attr
                else:
                    # Cell interior
                    granule_v = limb_v * (0.6 + 0.4 * abs(math.sin(dist_1st * 40 + f * 0.04))) * intensity
                    if granule_v > 0.8:
                        ch = "\u2588"
                        attr = bright_attr
                    elif granule_v > 0.5:
                        idx = int(granule_v * (len(density_chars) - 1))
                        ch = density_chars[idx]
                        attr = accent_attr
                    elif granule_v > 0.2:
                        idx = int(granule_v * (len(granule_chars) - 1))
                        ch = granule_chars[idx]
                        attr = soft_attr
                    else:
                        ch = "\u00b7"
                        attr = base_dim_attr

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

        # Solar flare prominence arc at top of disk
        if draw_flare:
            t_flare = flare_phase / 40.0
            arc_cx = int(w * 0.5)
            arc_cy = int(h * 0.18)
            arc_r = int(h * 0.08 * t_flare)
            for ax in range(max(1, arc_cx - arc_r * 2), min(w - 1, arc_cx + arc_r * 2)):
                arc_dx = (ax - arc_cx) / max(arc_r * 2, 1)
                arc_y_off = int(arc_r * math.sqrt(max(0, 1 - arc_dx * arc_dx)))
                ay = arc_cy - arc_y_off
                if 1 <= ay <= h - 2:
                    try:
                        stdscr.addstr(ay, ax, "*",
                                      curses.color_pair(color_pairs["bright"]) | curses.A_BOLD)
                    except curses.error:
                        pass


# ── Terra v2: Rotating Earth globe ───────────────────────────────────────────

class TerraV2Plugin(ThemePlugin):
    """Spherical projection of Earth — continents, ocean, poles, day/night."""
    name = "terra"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        intensity = state.intensity_multiplier

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr = curses.color_pair(color_pairs["soft"])
        base_dim_attr = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        rng = state.rng

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                nx = (x / (w - 1)) * 2 - 1
                ny = (y / (h - 1)) * 2 - 1
                nx_adj = nx
                ny_adj = ny * 2.0
                r2 = nx_adj ** 2 + ny_adj ** 2

                if r2 > 1.0:
                    # Space — sparse stars
                    seed_val = (x * 1000 + y * 7 + 13) % 100
                    if seed_val < 5:
                        try:
                            stdscr.addstr(y, x, "·", base_dim_attr)
                        except curses.error:
                            pass
                    # Atmosphere glow at edge — pulses with frame
                    elif r2 < 1.3:
                        atm_v = (1.3 - r2) / 0.3
                        # Atmosphere shimmers — brighter on the day side
                        atm_angle = math.atan2(ny_adj, nx_adj)
                        atm_day = math.cos(atm_angle - f * 0.003)
                        if atm_v > 0.25 and atm_day > -0.3:
                            atm_ch = "░" if atm_day > 0.5 else "·"
                            atm_attr = soft_attr if atm_day > 0.3 else base_dim_attr
                            try:
                                stdscr.addstr(y, x, atm_ch, atm_attr)
                            except curses.error:
                                pass
                    continue

                z = math.sqrt(max(0.0, 1 - r2))
                lon = math.atan2(ny_adj, nx_adj) + f * 0.008
                lat = math.asin(max(-1.0, min(1.0, z)))

                terrain = (math.sin(lon * 4 + lat * 3) * math.sin(lon * 7) * math.sin(lat * 5))
                polar = abs(ny_adj) > 0.85

                edge_fade = max(0.0, 1.0 - r2)
                # Day/night terminator sweeps across over time
                terminator_angle = f * 0.003
                day_side = nx_adj * math.cos(terminator_angle) + ny_adj * math.sin(terminator_angle) * 0.4 + z * 0.2
                # Smooth transition across terminator
                night_mult = max(0.08, min(1.0, 0.5 + day_side * 3.0))

                ch = " "
                attr = base_dim_attr

                if polar:
                    ch = "*" if edge_fade > 0.5 else "█"
                    attr = bright_attr if night_mult > 0.7 else soft_attr
                elif terrain > 0:
                    # Land — lit by day/night + cloud shadows
                    cloud = math.sin(lon * 6 + f * 0.005) * 0.15
                    land_v = terrain * edge_fade * night_mult * intensity + cloud
                    if land_v > 0.35:
                        ch = "▓"
                        attr = accent_attr
                    elif land_v > 0.18:
                        ch = "▒"
                        attr = accent_attr
                    elif land_v > 0.08:
                        ch = "░"
                        attr = soft_attr
                    else:
                        # Night side land — city lights
                        if night_mult < 0.25 and (int(lon * 8 + lat * 5) % 7 == 0):
                            ch = "·"
                            attr = bright_attr
                        else:
                            ch = "·"
                            attr = base_dim_attr
                else:
                    # Ocean — waves animate at full speed per frame
                    wave = math.sin(lon * 9 + f * 0.07) * 0.5 + 0.5
                    ocean_v = edge_fade * night_mult * intensity
                    if ocean_v > 0.55:
                        ch = "≈" if wave > 0.6 else "~"
                        attr = soft_attr
                    elif ocean_v > 0.25:
                        ch = "~" if wave > 0.5 else "·"
                        attr = soft_attr if wave > 0.5 else base_dim_attr
                    elif ocean_v > 0.08:
                        ch = "·"
                        attr = base_dim_attr
                    else:
                        ch = " "
                        attr = base_dim_attr

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


# ── Binary Star v2: Two orbiting stars with Roche lobe + mass transfer ────────

class BinaryStarV2Plugin(ThemePlugin):
    """Binary star system — gravitational potential field, Roche lobe overflow,
    mass-transfer stream, and orbital mechanics.

    v0.2 upgrade:
      - physarum_config: slime-mold agents trace mass-transfer stream between stars
      - wave_config: tidal ripples in the potential field substrate
      - warp_field: gravitational lensing distortion — strongest near each star
      - echo_decay: 5-frame orbital smear leaves the stars' recent path visible
      - force_points: two gravity wells track the star positions — true
        gravitational sinks that pull particles in
      - depth_layers: 2 — stars in front, potential field behind
      - intensity_curve: linear — activity maps directly to brightness
      - react() x10: agent_start → PULSE (orbital resonance), llm_start → STREAM
        (mass-transfer jet), error → SHATTER (stellar merger), memory_save →
        BLOOM (common envelope), tool_call → RIPPLE (tidal pulse)
      - palette_shift: error → red (merger flash), memory → blue/white (CE phase)
      - special_effects: "roche-overflow" — mass stream arc between the two stars
      - ambient_tick: slow orbital sweep of Lagrange point marker
    """
    name = "binary-star"

    _AY = 2.1  # terminal cell aspect ratio

    def __init__(self):
        super().__init__()
        # Mass ratio — set by react/ambient, drives lobe asymmetry
        self._mass_ratio = 1.0   # 1 = equal masses
        self._transfer_active = False
        self._transfer_dir = 1   # which star is donor: +1 s1→s2, -1 s2→s1

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    # ── v0.2: Emergent ────────────────────────────────────────────────────────
    def physarum_config(self):
        # Slime mold traces the mass-transfer stream between the two stars
        return {
            "n_agents": 120,
            "sensor_angle": 0.5,
            "sensor_dist": 4,
            "turn_speed": 0.45,
            "speed": 1.2,
            "deposit": 1.0,
            "decay": 0.92,
        }

    def wave_config(self):
        # Tidal waves ripple through the potential field
        return {"speed": 0.35, "damping": 0.96}

    def emergent_layer(self):
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────
    def warp_field(self, x, y, w, h, frame, intensity):
        # Gravitational lensing: space bends toward each star.
        # Computed from analytical potential gradient.
        period = 150
        angle = frame * (math.tau / period)
        sep = min(w, h) * 0.22
        cx, cy = w / 2.0, h / 2.0
        s1x = cx + math.cos(angle) * sep
        s1y = cy + math.sin(angle) * sep * 0.42
        s2x = cx - math.cos(angle) * sep * self._mass_ratio
        s2y = cy - math.sin(angle) * sep * 0.42 * self._mass_ratio

        def _lens_pull(px, py, sx, sy, strength):
            ddx = (px - sx) / max(self._AY, 1)
            ddy = py - sy
            d = math.sqrt(ddx * ddx + ddy * ddy) + 0.5
            pull = strength / (d * d)
            return (ddx / d) * pull, (ddy / d) * pull

        p1x, p1y = _lens_pull(x, y, s1x, s1y, intensity * 1.8)
        p2x, p2y = _lens_pull(x, y, s2x, s2y, intensity * 1.8)
        wx = int(-(p1x + p2x))
        wy = int(-(p1y + p2y))
        return (max(0, min(w - 1, x + wx)), max(0, min(h - 1, y + wy)))

    def echo_decay(self):
        # Orbital smear — 5 frames of trailing position visible
        return 5

    def glow_radius(self):
        return 2

    def force_points(self, w, h, frame, intensity):
        # Gravity wells track both stars — particles spiral inward
        period = 150
        angle = frame * (math.tau / period)
        sep = min(w, h) * 0.22
        cx, cy = w / 2.0, h / 2.0
        strength = 0.5 + intensity * 0.6
        return [
            {"x": int(cx + math.cos(angle) * sep),
             "y": int(cy + math.sin(angle) * sep * 0.42),
             "strength": strength, "type": "gravity"},
            {"x": int(cx - math.cos(angle) * sep * self._mass_ratio),
             "y": int(cy - math.sin(angle) * sep * 0.42 * self._mass_ratio),
             "strength": strength * self._mass_ratio, "type": "gravity"},
        ]

    def depth_layers(self):
        return 2

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────
    def intensity_curve(self, raw):
        return raw ** 0.75

    # ── v0.2: Reactive ────────────────────────────────────────────────────────
    def react(self, event_kind, data):
        import random as _r
        if event_kind == "agent_start":
            # Orbital resonance kick — PULSE at centre of mass
            return Reaction(element=ReactiveElement.PULSE, intensity=1.0,
                           origin=(0.5, 0.5), color_key="bright", duration=2.5)
        if event_kind == "llm_start":
            # Mass-transfer jet fires — STREAM from L1 point toward donor
            self._transfer_active = True
            return Reaction(element=ReactiveElement.STREAM, intensity=0.85,
                           origin=(0.5, 0.5), color_key="accent", duration=3.0)
        if event_kind == "llm_chunk":
            # Infalling matter — SPARK near current star positions
            ox = 0.3 + _r.random() * 0.4
            return Reaction(element=ReactiveElement.SPARK, intensity=0.4,
                           origin=(ox, 0.5 + _r.uniform(-0.15, 0.15)),
                           color_key="soft", duration=0.5)
        if event_kind == "llm_end":
            self._transfer_active = False
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.5,
                           origin=(0.5, 0.5), color_key="soft", duration=1.5)
        if event_kind in ("tool_call", "mcp_tool_call"):
            # Tidal pulse — RIPPLE at L4/L5 Lagrange point (±60° from axis)
            lag_ang = _r.choice([-1, 1]) * math.pi / 3
            ox = 0.5 + math.cos(lag_ang) * 0.28
            oy = 0.5 + math.sin(lag_ang) * 0.15
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.7,
                           origin=(max(0, min(1, ox)), max(0, min(1, oy))),
                           color_key="accent", duration=1.8)
        if event_kind in ("memory_save", "skill_create"):
            # Common envelope phase — BLOOM engulfs the system
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                           origin=(0.5, 0.5), color_key="bright", duration=3.0)
        if event_kind in ("error", "crash"):
            # Stellar merger — SHATTER, system fragments
            self._mass_ratio = 1.0  # reset asymmetry
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.5)
        if event_kind in ("cron_tick", "background_proc"):
            # Orbital tick — ORBIT, star marker sweeps
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.4,
                           origin=(0.5, 0.5), color_key="soft", duration=3.0)
        if event_kind == "subagent_started":
            # New companion — BLOOM off-centre (secondary ignition)
            self._mass_ratio = _r.uniform(0.7, 1.4)
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.75,
                           origin=(_r.uniform(0.3, 0.7), _r.uniform(0.35, 0.65)),
                           color_key="accent", duration=2.0)
        if event_kind in ("context_pressure", "token_usage"):
            return Reaction(element=ReactiveElement.GAUGE,
                           intensity=data.get("ratio", 0.6),
                           origin=(0.05, 0.9), color_key="warning", duration=3.0)
        if event_kind in ("dangerous_cmd", "approval_request"):
            return Reaction(element=ReactiveElement.SPARK, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────
    def palette_shift(self, trigger_effect, intensity, base_palette):
        if trigger_effect in ("error", "crash") or str(trigger_effect) == str(ReactiveElement.SHATTER):
            # Merger flash — red/white
            return (curses.COLOR_RED, curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_RED)
        if trigger_effect in ("memory_save", "skill_create") or str(trigger_effect) == str(ReactiveElement.BLOOM):
            # Common envelope — blue/cyan/white
            return (curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_BLUE, curses.COLOR_CYAN)
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────
    def special_effects(self):
        return [
            SpecialEffect(name="roche-overflow",
                         trigger_kinds=["burst", "llm_start"],
                         min_intensity=0.4, cooldown=5.0, duration=3.0),
        ]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        if special_name != "roche-overflow":
            return
        w, h = state.width, state.height
        # Mass-transfer stream: a curved jet from star 1 to star 2 via L1 point.
        # The stream follows a parabolic arc that brightens at the accretion disc.
        f = state.frame
        period = 150
        angle = f * (math.tau / period)
        sep = min(w, h) * 0.22
        cx, cy = w // 2, h // 2
        s1x = cx + math.cos(angle) * sep
        s1y = cy + math.sin(angle) * sep * 0.42
        s2x = cx - math.cos(angle) * sep
        s2y = cy - math.sin(angle) * sep * 0.42
        # Interpolate stream points — curved path via L1 (midpoint offset)
        l1x = (s1x + s2x) / 2
        l1y = (s1y + s2y) / 2 - h * 0.06   # L1 slightly above midpoint
        attr_b = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        attr_a = curses.color_pair(color_pairs.get("accent", 0))
        stream_chars = "·:*◦○"
        steps = 60
        active_steps = int(steps * progress)
        for i in range(active_steps):
            t = i / steps
            # Quadratic Bezier from s1 → l1 → s2
            bx = int((1-t)**2 * s1x + 2*(1-t)*t * l1x + t**2 * s2x)
            by = int((1-t)**2 * s1y + 2*(1-t)*t * l1y + t**2 * s2y)
            if 0 <= bx < w and 0 <= by < h:
                ci = int(t * (len(stream_chars) - 1)) % len(stream_chars)
                attr = attr_b if t > 0.7 else attr_a
                _safe(stdscr, by, bx, stream_chars[ci], attr)

    # ── v0.2: Ambient tick — Lagrange point marker ────────────────────────────
    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        if state.frame % 25 == 0:
            w, h = state.width, state.height
            f = state.frame
            period = 150
            angle = f * (math.tau / period)
            sep = min(w, h) * 0.22
            cx, cy = w // 2, h // 2
            # L4 and L5 Lagrange points at ±60° from the line of apsides
            for sign in (+1, -1):
                lag_a = angle + sign * math.pi / 3
                lx = int(cx + math.cos(lag_a) * sep * 0.9)
                ly = int(cy + math.sin(lag_a) * sep * 0.38)
                if 0 <= lx < w and 1 <= ly < h - 1:
                    attr = curses.color_pair(color_pairs.get("soft", 0)) | curses.A_DIM
                    _safe(stdscr, ly, lx, "·", attr)

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        intensity = state.intensity_multiplier

        period = 150
        angle = f * (2 * math.pi / period)
        sep = min(w, h) * 0.22
        cx = w / 2.0
        cy = h / 2.0

        s1x = cx + math.cos(angle) * sep
        s1y = cy + math.sin(angle) * sep * 0.42
        s2x = cx - math.cos(angle) * sep * self._mass_ratio
        s2y = cy - math.sin(angle) * sep * 0.42 * self._mass_ratio

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr = curses.color_pair(color_pairs["soft"])
        base_dim_attr = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        warn_attr = curses.color_pair(color_pairs.get("warning", color_pairs["bright"])) | curses.A_BOLD

        potential_chars = " \u00b7.:;+=*#"
        # Hue phase sweeps slowly — gives potential surface a rippling color motion
        hue_base = (f * 0.004) % 1.0

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                r1 = math.sqrt((x - s1x) ** 2 / 2.25 + (y - s1y) ** 2)
                r2 = math.sqrt((x - s2x) ** 2 / 2.25 + (y - s2y) ** 2)
                # Effective Roche potential including centrifugal term
                r_cm = math.sqrt((x - cx) ** 2 / 2.25 + (y - cy) ** 2)
                V = -(1.0 / (r1 + 0.5) + self._mass_ratio / (r2 + 0.5)
                      + 0.5 * (r_cm / max(w, h) * 1.5) ** 2) * 3.0
                v = max(0.0, min(1.0, (-V - 0.5) / 4.0)) * intensity

                # Roche lobe boundary — equipotential contour
                # Detected as zero-crossing region of the Roche criterion
                # |∇V| ≈ 0 near the L1 surface — approximate as |V+V_L1| < threshold
                V_L1 = -(1.0 / (sep * 0.5 + 0.5) * 2) * 3.0
                lobe_edge = abs(V - V_L1) < 0.18

                if lobe_edge:
                    # Roche lobe surface — pulsing equipotential line
                    pulse = abs(math.sin(f * 0.06 + v * 8.0))
                    lobe_chars = "─│╱╲┼"
                    lci = int((angle + y * 0.3) % len(lobe_chars))
                    phase = (hue_base + pulse * 0.4) % 1.0
                    if (v + phase) % 1.0 > 0.65:
                        attr = accent_attr
                    else:
                        attr = soft_attr
                    ch = lobe_chars[lci]
                else:
                    ci = int(v * (len(potential_chars) - 1))
                    ch = potential_chars[ci]
                    # Phase ripple — potential wells glow inward over time
                    phase = (hue_base + v + (r1 - r2) * 0.04) % 1.0
                    if (v + phase) % 1.0 > 0.75:
                        attr = bright_attr
                    elif (v + phase) % 1.0 > 0.50:
                        attr = accent_attr
                    elif (v + phase) % 1.0 > 0.25:
                        attr = soft_attr
                    else:
                        attr = base_dim_attr

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

        # Draw star bodies with coronae
        star_glyphs = ["★", "✦"]
        for si, (sx, sy) in enumerate([(s1x, s1y), (s2x, s2y)]):
            sxi = int(sx)
            syi = int(sy)
            if 1 <= syi <= h - 2 and 0 <= sxi <= w - 2:
                _safe(stdscr, syi, sxi, star_glyphs[si % 2], bright_attr)
                # Corona halo — one ring of dots at r=2 (terminal units)
                for deg in range(0, 360, 45):
                    theta = math.radians(deg)
                    hx = int(sxi + math.cos(theta) * 2)
                    hy = int(syi + math.sin(theta))
                    if 1 <= hy <= h - 2 and 0 <= hx <= w - 2:
                        _safe(stdscr, hy, hx, "·", accent_attr)

        # Mass-transfer stream arc when active (reactive state)
        if self._transfer_active:
            l1x = (s1x + s2x) / 2
            l1y = (s1y + s2y) / 2 - h * 0.04
            steps = 30
            stream_chars = "·:·"
            for i in range(steps):
                t = i / steps
                bx = int((1-t)**2 * s1x + 2*(1-t)*t * l1x + t**2 * s2x)
                by = int((1-t)**2 * s1y + 2*(1-t)*t * l1y + t**2 * s2y)
                anim_t = (t + f * 0.04) % 1.0
                ci = int(anim_t * (len(stream_chars) - 1)) % len(stream_chars)
                if 1 <= by <= h - 2 and 0 <= bx <= w - 2:
                    _safe(stdscr, by, bx, stream_chars[ci], accent_attr)

        # L1 Lagrange point marker
        l1xi = int((s1x + s2x) / 2)
        l1yi = int((s1y + s2y) / 2)
        if 1 <= l1yi <= h - 2 and 0 <= l1xi <= w - 2:
            ch = "×" if self._transfer_active else "+"
            attr = warn_attr if self._transfer_active else soft_attr
            _safe(stdscr, l1yi, l1xi, ch, attr)


# ── Fractal Engine: Real-time ASCII Mandelbrot set ────────────────────────────

class FractalEnginePlugin(ThemePlugin):
    """Real-time Mandelbrot set zoom — iterative ASCII rendering."""
    name = "fractal-engine"

    # Zoom targets: interesting Mandelbrot coordinates to zoom into
    _TARGETS = [
        (-0.7269, 0.1889),   # classic spiral
        (-0.1592,  1.0317),  # spiraling tendril
        ( 0.3750,  0.1055),  # seahorse valley
        (-1.1786,  0.0),     # antenna tip
    ]

    def __init__(self):
        self._target_idx = 0
        self._cycle_start_frame = 0
        self._zoom = 3.5

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        intensity = state.intensity_multiplier
        f = state.frame

        # 400-frame zoom cycle: zoom from 3.5 → 0.0003 then reset
        CYCLE = 400
        phase = (f - self._cycle_start_frame) % CYCLE
        if phase == 0 and f != self._cycle_start_frame:
            self._cycle_start_frame = f
            self._target_idx = (self._target_idx + 1) % len(self._TARGETS)
            phase = 0

        t = phase / CYCLE  # 0 → 1
        self._zoom = 3.5 * (1.0 - t) ** 2.2 + 0.0003  # fast initial zoom, slow near target
        zoom = self._zoom

        target_cx, target_cy = self._TARGETS[self._target_idx]
        start_cx, start_cy = -0.7, 0.0
        view_cx = start_cx + (target_cx - start_cx) * t
        view_cy = start_cy + (target_cy - start_cy) * t

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr = curses.color_pair(color_pairs["soft"])
        base_dim_attr = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        base_attr = curses.color_pair(color_pairs["base"])

        MAX_ITER = 24
        mid_chars = "\u00b7.:;+="

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                re = view_cx + (x / max(w, 1) - 0.5) * zoom
                im = view_cy + (y / max(h, 1) - 0.5) * zoom * (h / max(w, 1)) * 2.2

                zr, zi = 0.0, 0.0
                i = 0
                for i in range(MAX_ITER):
                    zr2, zi2 = zr * zr, zi * zi
                    if zr2 + zi2 > 4.0:
                        break
                    zi = 2 * zr * zi + im
                    zr = zr2 - zi2 + re
                else:
                    i = MAX_ITER

                if i == MAX_ITER:
                    ch = "\u2588"
                    attr = base_attr
                else:
                    v = i / MAX_ITER
                    color_sel = i % 3
                    if v < 0.15:
                        ch = "\u2593"
                        attr = accent_attr | curses.A_BOLD
                    elif v < 0.5:
                        idx = int((v - 0.15) / 0.35 * (len(mid_chars) - 1))
                        ch = mid_chars[idx]
                        if color_sel == 0:
                            attr = base_dim_attr
                        elif color_sel == 1:
                            attr = soft_attr
                        else:
                            attr = accent_attr
                    else:
                        ch = "\u00b7" if v < 0.75 else " "
                        attr = base_dim_attr

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


# ── N-Body: Gravitational N-body simulation ───────────────────────────────────

class NBodyPlugin(ThemePlugin):
    """Gravitational N-body simulation with field visualization and trails."""
    name = "n-body"

    def __init__(self):
        self._bodies = None
        self._trails = None
        self._frame_count = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init_bodies(self):
        self._bodies = [
            {'x': 0.5,  'y': 0.35, 'vx':  0.008, 'vy':  0.0,   'mass': 2.0, 'c': 'bright'},
            {'x': 0.5,  'y': 0.65, 'vx': -0.008, 'vy':  0.0,   'mass': 2.0, 'c': 'accent'},
            {'x': 0.25, 'y': 0.5,  'vx':  0.0,   'vy':  0.006, 'mass': 1.0, 'c': 'soft'},
            {'x': 0.75, 'y': 0.5,  'vx':  0.0,   'vy': -0.006, 'mass': 1.0, 'c': 'soft'},
            {'x': 0.35, 'y': 0.35, 'vx':  0.004, 'vy':  0.004, 'mass': 0.5, 'c': 'base'},
            {'x': 0.65, 'y': 0.65, 'vx': -0.004, 'vy': -0.004, 'mass': 0.5, 'c': 'base'},
        ]
        self._trails = [[] for _ in range(6)]
        self._frame_count = 0

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        intensity = state.intensity_multiplier

        if self._bodies is None:
            self._init_bodies()

        bodies = self._bodies
        trails = self._trails
        self._frame_count += 1

        # Physics update — 3 substeps
        G = 0.00015
        dt = 1.0
        for substep in range(3):
            accels = [(0.0, 0.0)] * len(bodies)
            for i, b in enumerate(bodies):
                ax, ay = 0.0, 0.0
                for j, other in enumerate(bodies):
                    if i == j:
                        continue
                    dx = other['x'] - b['x']
                    dy = other['y'] - b['y']
                    r2 = dx * dx + dy * dy + 0.001
                    r = math.sqrt(r2)
                    F = G * other['mass'] / r2
                    ax += F * dx / r
                    ay += F * dy / r
                accels[i] = (ax, ay)
            for i, b in enumerate(bodies):
                b['vx'] += accels[i][0] * dt / 3
                b['vy'] += accels[i][1] * dt / 3
            for b in bodies:
                b['x'] += b['vx'] * dt / 3
                b['y'] += b['vy'] * dt / 3
                if b['x'] < 0.02 or b['x'] > 0.98:
                    b['vx'] *= -0.8
                if b['y'] < 0.02 or b['y'] > 0.98:
                    b['vy'] *= -0.8
                b['x'] = max(0.02, min(0.98, b['x']))
                b['y'] = max(0.02, min(0.98, b['y']))

        # Update trails
        for i, b in enumerate(bodies):
            sx = int(b['x'] * w)
            sy = int(b['y'] * h)
            trails[i].append((sx, sy))
            if len(trails[i]) > 40:
                trails[i].pop(0)

        # Reset check every 1000 frames
        if self._frame_count % 1000 == 0:
            all_close = all(
                math.sqrt((b['x'] - bodies[0]['x']) ** 2 + (b['y'] - bodies[0]['y']) ** 2) < 0.05
                for b in bodies[1:]
            )
            if all_close:
                self._init_bodies()

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr = curses.color_pair(color_pairs["soft"])
        base_dim_attr = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        base_attr = curses.color_pair(color_pairs["base"])

        # Gravity field background
        for y in range(1, h - 1):
            for x in range(0, w - 1):
                nx = x / max(w, 1)
                ny = y / max(h, 1)
                V = 0.0
                for b in bodies:
                    ddx = nx - b['x']
                    ddy = ny - b['y']
                    r2 = ddx * ddx + ddy * ddy
                    V += -b['mass'] / math.sqrt(r2 + 0.01)

                if V < -8:
                    ch = "\u2588"
                    attr = bright_attr
                elif V < -4:
                    ch = "\u2593"
                    attr = accent_attr
                elif V < -2:
                    ch = "\u2592"
                    attr = soft_attr
                elif V < -1:
                    ch = "\u2591"
                    attr = base_dim_attr
                else:
                    ch = " "
                    attr = base_dim_attr

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

        # Draw trails
        trail_chars = "\u00b7\u2219\u2022"
        for i, trail in enumerate(trails):
            tlen = len(trail)
            for ti, (tx, ty) in enumerate(trail):
                if not (1 <= ty <= h - 2 and 0 <= tx <= w - 2):
                    continue
                age = ti / max(tlen, 1)
                tch = trail_chars[int(age * 2)]
                if age > 0.6:
                    tattr = accent_attr
                elif age > 0.3:
                    tattr = base_attr
                else:
                    tattr = base_dim_attr
                try:
                    stdscr.addstr(ty, tx, tch, tattr)
                except curses.error:
                    pass

        # Draw bodies
        color_map = {
            'bright': bright_attr,
            'accent': accent_attr,
            'soft': soft_attr,
            'base': base_dim_attr,
        }
        body_chars = {2.0: "\u25c9", 1.0: "\u25cf", 0.5: "\u2022"}
        for b in bodies:
            bx = int(b['x'] * w)
            by = int(b['y'] * h)
            if 1 <= by <= h - 2 and 0 <= bx <= w - 2:
                mass = b['mass']
                bch = body_chars.get(mass, "\u2022")
                battr = color_map.get(b['c'], base_dim_attr)
                try:
                    stdscr.addstr(by, bx, bch, battr)
                except curses.error:
                    pass


# ── Standing Waves: 2D resonant membrane modes ───────────────────────────────

class StandingWavesPlugin(ThemePlugin):
    """Superposition of 2D sinusoidal resonant membrane modes."""
    name = "standing-waves"

    def __init__(self):
        self._modes = None

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init_modes(self):
        self._modes = [
            {'m': 1, 'n': 2, 'A': 0.8, 'phi': 0.0,  'omega': math.sqrt(5) * 0.06},
            {'m': 3, 'n': 1, 'A': 0.6, 'phi': 1.0,  'omega': math.sqrt(10) * 0.06},
            {'m': 2, 'n': 3, 'A': 0.5, 'phi': 2.1,  'omega': math.sqrt(13) * 0.06},
        ]

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        intensity = state.intensity_multiplier
        rng = state.rng

        if self._modes is None:
            self._init_modes()

        modes = self._modes

        # Decay amplitudes
        for mode in modes:
            mode['A'] *= 0.9997

        # Add new mode on intensity spike
        if intensity > 0.8 and rng.random() < 0.1 and len(modes) < 8:
            m = rng.randint(1, 5)
            n = rng.randint(1, 5)
            modes.append({
                'm': m, 'n': n, 'A': 0.7,
                'phi': rng.uniform(0, math.tau),
                'omega': math.sqrt(m * m + n * n) * 0.06,
            })

        # Remove dead modes
        self._modes = [mode for mode in modes if mode['A'] >= 0.01]
        modes = self._modes

        if not modes:
            self._init_modes()
            modes = self._modes

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr = curses.color_pair(color_pairs["soft"])
        base_dim_attr = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        block_chars = "\u2588\u2593\u2592\u2591"

        for y in range(1, h - 1):
            ny = y / max(h - 1, 1)
            for x in range(0, w - 1):
                nx = x / max(w - 1, 1)
                v = 0.0
                for mode in modes:
                    v += (mode['A'] *
                          math.sin(mode['m'] * math.pi * nx) *
                          math.sin(mode['n'] * math.pi * ny) *
                          math.cos(mode['omega'] * f + mode['phi']))

                v_norm = (v + 2) / 4.0
                v_norm = max(0.0, min(1.0, v_norm))
                v_norm_adj = v_norm * intensity

                if abs(v_norm - 0.5) < 0.04:
                    # Node line (zero crossing)
                    ch = "\u00b7"
                    attr = base_dim_attr
                elif v_norm_adj > 0.75:
                    ch = block_chars[0]
                    attr = bright_attr
                elif v_norm_adj > 0.6:
                    ch = block_chars[1]
                    attr = accent_attr
                elif v_norm_adj > 0.4:
                    ch = block_chars[2]
                    attr = soft_attr
                elif v_norm_adj > 0.25:
                    ch = block_chars[3]
                    attr = base_dim_attr
                else:
                    ch = " "
                    attr = base_dim_attr

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


# ── Registration ──────────────────────────────────────────────────────────────

register(StarfallV2Plugin())
register(QuasarV2Plugin())
register(SupernovaV2Plugin())
register(SolV2Plugin())
register(TerraV2Plugin())
register(BinaryStarV2Plugin())
register(FractalEnginePlugin())
register(NBodyPlugin())
register(StandingWavesPlugin())
