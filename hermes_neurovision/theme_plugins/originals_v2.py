"""Redesigned original themes using full-screen ASCII field engine.

Themes: black-hole, neural-sky, storm-core, moonwire, rootsong, stormglass, spiral-galaxy
All use draw_extras() for per-cell rendering; build_nodes() returns [] to suppress graph.
"""

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


# ── Black Hole ─────────────────────────────────────────────────────────────────

class BlackHoleV2Plugin(ThemePlugin):
    """Relativistic black hole — Keplerian orbits, frame-drag, Doppler disk, relativistic jets.

    Every star particle orbits at its own angular velocity (omega ∝ r^-1.5) so
    inner orbits spin dramatically faster than outer ones.  The accretion disk
    co-rotates with the same Keplerian shear.  Frame-drag (Kerr metric approx)
    bends the lensed-star field each frame.  Captured stars are replaced at the
    outer edge so the field never empties.

    v0.2 upgrade:
      - neural_field_config: sparse Hawking radiation — rare, high-threshold sparks
        at the event horizon
      - warp_field: gravitational lensing — strong inward pull, proportional to
        1/r² from centre, mirrors the analytical Kerr frame-drag in draw_extras
      - echo_decay: 4 — orbital smear, trails linger
      - glow_radius: 2 — photon ring blooms
      - force_points: one gravity singularity at centre + two jet-axis attractors
        along the polar axis
      - intensity_curve: power 0.5 — quiescent at low, explosively bright at high
      - react() x11: agent_start → PULSE (accretion burst), llm_start → STREAM
        (infalling matter), llm_chunk → SPARK (photon flash), error/crash →
        SHATTER (Hawking event), memory_save → BLOOM (horizon expands),
        tool_call → RIPPLE (tidal disruption event), cron_tick → ORBIT (pulsar
        timing signal), dangerous_cmd → SPARK (radiation warning),
        context_pressure → GAUGE (Schwarzschild radius filling)
      - palette_shift: error → red/white (Hawking radiation), memory → cyan/white
        (gravitational blueshift)
      - special_effects: "hawking-burst" — bright ring flash at photon sphere
      - ambient_tick: quantum foam flicker at event horizon
    """
    name = "black-hole"

    _N_STARS = 90
    _AY      = 2.1   # terminal cell aspect ratio (height/width of a character)

    def __init__(self):
        super().__init__()
        self._stars = []   # [x, y, r, theta, omega, brightness, char_idx]
        self._rng   = random.Random(31415)
        self._rs    = 0.0  # cached Schwarzschild radius from last frame
        self._spin  = 0.9  # Kerr spin parameter 0–1 (affects frame-drag strength)
        self._accretion_boost = 1.0  # driven up by reactive events

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    # ── v0.2: Emergent ────────────────────────────────────────────────────────
    def neural_field_config(self):
        # Hawking radiation: extremely rare, random firing at the event horizon.
        # High threshold, long refractory — quantum foam is sparse.
        return {"threshold": 5, "fire_duration": 1, "refractory": 12}

    def emergent_layer(self):
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────
    def warp_field(self, x, y, w, h, frame, intensity):
        # Gravitational lensing: photons from (x,y) are deflected toward
        # the singularity at screen centre. Deflection ∝ 1/r² (weak field).
        cx, cy = w / 2.0, h / 2.0
        dx = x - cx
        dy = (y - cy) * self._AY
        r2 = dx * dx + dy * dy + 0.1
        r  = math.sqrt(r2)
        # Schwarzschild deflection angle ∝ rs/r, scaled to pixel units
        rs_px = min(w * 0.07, h * 0.14)
        # Cap to avoid singularity eating pixels
        if r < rs_px * 1.3:
            return (x, y)
        defl = (rs_px * rs_px) / r2 * intensity * 3.0
        wx = int(-dx / r * defl)
        wy = int(-dy / r / self._AY * defl)
        return (max(0, min(w - 1, x + wx)), max(0, min(h - 1, y + wy)))

    def echo_decay(self):
        # Orbital smear — trails linger 4 frames
        return 4

    def glow_radius(self):
        # Photon ring blooms outward
        return 2

    def force_points(self, w, h, frame, intensity):
        cx, cy = w // 2, h // 2
        rs_px = min(w * 0.07, h * 0.14)
        strength = (0.6 + intensity * 0.8) * self._accretion_boost
        pts = [
            # Central singularity — strong inward gravity
            {"x": cx, "y": cy, "strength": strength * 1.5, "type": "gravity"},
        ]
        # Relativistic jet exit points along polar axis — weak vortex repellers
        jet_len = int(h * 0.35)
        jet_str = 0.2 + intensity * 0.25
        pts.append({"x": cx, "y": max(1, cy - jet_len),
                    "strength": jet_str, "type": "vortex"})
        pts.append({"x": cx, "y": min(h - 2, cy + jet_len),
                    "strength": jet_str, "type": "vortex"})
        return pts

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────
    def intensity_curve(self, raw):
        # sqrt — extremely sensitive to low signal (dark energy budget)
        return raw ** 0.45

    # ── v0.2: Reactive ────────────────────────────────────────────────────────
    def react(self, event_kind, data):
        import random as _r
        cx, cy = 0.5, 0.5

        if event_kind == "agent_start":
            # Accretion burst — mass infalls, disk brightens — PULSE
            self._accretion_boost = 1.8
            return Reaction(element=ReactiveElement.PULSE, intensity=1.0,
                           origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "llm_start":
            # Infalling matter stream — STREAM from outer disc inward
            self._accretion_boost = 1.4
            return Reaction(element=ReactiveElement.STREAM, intensity=0.9,
                           origin=(_r.uniform(0.1, 0.4), _r.uniform(0.3, 0.7)),
                           color_key="accent", duration=3.5)
        if event_kind == "llm_chunk":
            # Photon escaping event horizon — SPARK at photon sphere ring
            theta = _r.uniform(0, math.tau)
            ox = 0.5 + math.cos(theta) * 0.15
            oy = 0.5 + math.sin(theta) * 0.08
            return Reaction(element=ReactiveElement.SPARK, intensity=0.5,
                           origin=(max(0.0, min(1.0, ox)), max(0.0, min(1.0, oy))),
                           color_key="bright", duration=0.4)
        if event_kind == "llm_end":
            self._accretion_boost = 1.0
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.5,
                           origin=(cx, cy), color_key="soft", duration=2.0)
        if event_kind in ("tool_call", "mcp_tool_call"):
            # Tidal disruption event — star torn apart, RIPPLE at approach position
            ox = _r.uniform(0.2, 0.8)
            oy = _r.uniform(0.2, 0.8)
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.8,
                           origin=(ox, oy), color_key="accent", duration=1.8)
        if event_kind in ("memory_save", "skill_create"):
            # Event horizon grows — BLOOM, the darkness expands
            self._spin = min(0.998, self._spin + 0.05)
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                           origin=(cx, cy), color_key="bright", duration=3.0)
        if event_kind in ("error", "crash"):
            # Hawking radiation event — SHATTER, white burst from horizon
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(cx, cy), color_key="warning", duration=2.5)
        if event_kind in ("cron_tick", "background_proc"):
            # Pulsar timing signal — ORBIT rings sweep around
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.45,
                           origin=(cx, cy), color_key="soft", duration=4.0)
        if event_kind == "subagent_started":
            # New infalling body — BLOOM at a random orbital position
            theta = _r.uniform(0, math.tau)
            ox = 0.5 + math.cos(theta) * 0.28
            oy = 0.5 + math.sin(theta) * 0.14
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.75,
                           origin=(max(0.0, min(1.0, ox)), max(0.0, min(1.0, oy))),
                           color_key="accent", duration=2.0)
        if event_kind in ("dangerous_cmd", "approval_request"):
            # Radiation alarm — SPARK at horizon, bright warning
            return Reaction(element=ReactiveElement.SPARK, intensity=1.0,
                           origin=(cx, cy), color_key="warning", duration=2.0)
        if event_kind in ("context_pressure", "token_usage"):
            # Mass budget — GAUGE at edge (Schwarzschild filling)
            return Reaction(element=ReactiveElement.GAUGE,
                           intensity=data.get("ratio", 0.7),
                           origin=(0.05, 0.9), color_key="warning", duration=3.5)
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────
    def palette_shift(self, trigger_effect, intensity, base_palette):
        if trigger_effect in ("error", "crash") or str(trigger_effect) == str(ReactiveElement.SHATTER):
            # Hawking radiation — blinding white, then red
            return (curses.COLOR_WHITE, curses.COLOR_RED, curses.COLOR_YELLOW, curses.COLOR_RED)
        if trigger_effect in ("memory_save", "skill_create") or str(trigger_effect) == str(ReactiveElement.BLOOM):
            # Gravitational blueshift — cyan/white as matter falls in
            return (curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_BLUE, curses.COLOR_CYAN)
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────
    def special_effects(self):
        return [
            SpecialEffect(name="hawking-burst",
                         trigger_kinds=["burst", "error"],
                         min_intensity=0.4, cooldown=5.0, duration=2.5),
        ]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        if special_name != "hawking-burst":
            return
        w, h = state.width, state.height
        cx, cy = w // 2, h // 2
        rs_px = min(w * 0.07, h * 0.14)
        # Two simultaneous rings: photon sphere (1.5rs) and outer Hawking ring
        rings = [
            (rs_px * 1.5, "◉●◎○·", 1.0),
            (rs_px * 2.8 * (0.3 + progress * 0.7), "·∘○◦", 0.6),
        ]
        attr_b = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        attr_a = curses.color_pair(color_pairs.get("accent", 0))
        for ring_r, chars, bright_frac in rings:
            r = int(ring_r * (0.5 + progress * 0.5))
            if r < 1:
                continue
            steps = max(24, r * 4)
            for i in range(steps):
                theta = (i / steps) * math.tau
                px = int(cx + r * math.cos(theta) * 2)
                py = int(cy + r * math.sin(theta))
                if 0 <= px < w and 0 <= py < h:
                    ci = int((theta / math.tau + progress) * len(chars)) % len(chars)
                    flash = (1.0 - progress) * bright_frac
                    attr = attr_b if flash > 0.4 else attr_a
                    _safe(stdscr, py, px, chars[ci], attr)

    # ── v0.2: Ambient tick — quantum foam at horizon ──────────────────────────
    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        if state.frame % 8 == 0 and self._rs > 0:
            w, h = state.width, state.height
            rs = self._rs
            cx, cy = w / 2.0, h / 2.0
            rng2 = self._rng
            # Scatter a handful of dim dots just outside event horizon
            for _ in range(2):
                theta = rng2.uniform(0, math.tau)
                jitter = rng2.uniform(rs * 1.01, rs * 1.35)
                px = int(cx + math.cos(theta) * jitter)
                py = int(cy + math.sin(theta) * jitter / self._AY)
                if 0 <= px < w and 1 <= py < h - 1:
                    attr = curses.color_pair(color_pairs.get("soft", 0)) | curses.A_DIM
                    _safe(stdscr, py, px, "·", attr)

    def _spawn_star(self, cx, cy, rs, rng, r=None):
        ay = self._AY
        if r is None:
            # Flat random in log-space so inner region has real coverage
            r = math.exp(rng.uniform(math.log(rs * 2.8), math.log(rs * 10.0)))
        theta = rng.uniform(0, math.tau)
        # Keplerian: omega = K * r^-1.5, calibrated so innermost stars lap ~every 60 frames
        omega = 0.55 * (rs / r) ** 1.5
        bright = rng.uniform(0.45, 1.0)
        ci = rng.randint(0, 3)
        x = cx + math.cos(theta) * r
        y = cy + math.sin(theta) * r / ay
        return [x, y, r, theta, omega, bright, ci]

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        cx, cy  = w / 2.0, h / 2.0
        intensity = state.intensity_multiplier
        ay = self._AY

        bright_attr = curses.color_pair(color_pairs.get("bright", 1)) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs.get("accent", 1)) | curses.A_BOLD
        soft_attr   = curses.color_pair(color_pairs.get("soft",   1))
        base_attr   = curses.color_pair(color_pairs.get("base",   1))
        base_dim    = curses.color_pair(color_pairs.get("base",   1)) | curses.A_DIM
        warn_attr   = curses.color_pair(color_pairs.get("warning",1)) | curses.A_BOLD

        rs = min(w * 0.07, h * 0.14)
        self._rs = rs

        # ── Initialise / re-init star pool on first frame or resize ──
        if not self._stars:
            for _ in range(self._N_STARS):
                self._stars.append(self._spawn_star(cx, cy, rs, self._rng))

        # ── Step every star: Keplerian orbit + slow inward spiral ──────
        stepped = []
        for star in self._stars:
            sx, sy, r, theta, omega, bright, ci = star
            theta += omega
            r     *= 0.99985      # tiny inward drift — accretion
            if r < rs * 1.25:
                # Captured — respawn far out
                star = self._spawn_star(cx, cy, rs, self._rng,
                                        r=self._rng.uniform(rs * 7.0, rs * 10.5))
                stepped.append(star)
                continue
            sx = cx + math.cos(theta) * r
            sy = cy + math.sin(theta) * r / ay
            stepped.append([sx, sy, r, theta, omega, bright, ci])
        self._stars = stepped

        # ── Per-pixel analytical field ──────────────────────────────────
        # Keplerian disk speed calibration constant (matches star omega formula)
        K_disk = 0.55

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                dx     = x - cx
                dy     = (y - cy) * ay
                r      = math.sqrt(dx * dx + dy * dy)
                theta  = math.atan2(dy, dx)

                # ── Event horizon void ──
                if r < rs * 0.92:
                    try: stdscr.addstr(y, x, " ", base_dim)
                    except curses.error: pass
                    continue

                if r < rs:
                    try: stdscr.addstr(y, x, "█", base_dim)
                    except curses.error: pass
                    continue

                # ── Kerr frame-drag: angular shift ∝ 1/r² ──────────────
                frame_drag   = (rs * rs) / (r * r + 0.01) * 1.2
                dragged_theta = theta + frame_drag

                # ── Photon sphere + Einstein ring ───────────────────────
                # Primary photon ring (r ≈ 1.5 rs) — bright glowing halo
                photon_r = rs * 1.5
                ph_dist  = abs(r - photon_r)
                if ph_dist < rs * 0.60:
                    glow      = 1.0 - ph_dist / (rs * 0.60)
                    # Characters advance around the ring at frame speed
                    ring_phase = (dragged_theta + f * 0.12) % math.tau
                    rchars     = "◉●◎○·∘"
                    rci        = int(ring_phase / math.tau * len(rchars)) % len(rchars)
                    ch         = rchars[rci]
                    if glow > 0.70:
                        attr = warn_attr
                    elif glow > 0.40:
                        attr = accent_attr
                    else:
                        attr = soft_attr
                    try:
                        stdscr.addstr(y, x, ch, attr)
                    except curses.error: pass
                    continue

                # Secondary lensing arc (inner Einstein ring, r ≈ 1.15 rs)
                inner_r  = rs * 1.15
                in_dist  = abs(r - inner_r)
                if in_dist < rs * 0.20:
                    glow2 = 1.0 - in_dist / (rs * 0.20)
                    ring_phase2 = (dragged_theta - f * 0.18) % math.tau
                    rchars2 = "·∘○◦"
                    rci2 = int(ring_phase2 / math.tau * len(rchars2)) % len(rchars2)
                    try:
                        stdscr.addstr(y, x, rchars2[rci2],
                                      warn_attr if glow2 > 0.6 else accent_attr)
                    except curses.error: pass
                    continue

                # ── Relativistic jets — very fast wave ─────────────────
                jet_hw = rs * 0.55
                if abs(dx) < jet_hw and r > rs * 1.05:
                    frac = 1.0 - abs(dx) / jet_hw
                    wave = math.sin(r * 0.5 - f * 0.30) * 0.5 + 0.5
                    v    = frac * wave * intensity
                    if v > 0.18:
                        jchars = "│║┃|!▒░"
                        jci    = min(len(jchars) - 1, int(v * len(jchars)))
                        try:
                            stdscr.addstr(y, x, jchars[jci],
                                          bright_attr if v > 0.6 else accent_attr)
                        except curses.error: pass
                        continue

                        # ── Accretion disk — Keplerian shear ───────────────────
                # Wider inclination so disk is easily visible (was 0.22, now 0.40)
                disk_latitude = abs(math.sin(dragged_theta))
                # Disk thickness itself flares near the inner edge (puffed-up inner rim)
                disk_thickness = 0.40 + max(0.0, 0.18 * (1.0 - (r - rs * 1.8) / (rs * 2.0)))
                in_disk = disk_latitude < disk_thickness
                if rs * 1.7 <= r <= rs * 8.5 and in_disk:
                    local_omega  = K_disk * (rs / r) ** 1.5
                    orbit_phase  = dragged_theta - f * local_omega
                    # Relativistic Doppler: approaching side is blueshift-bright
                    doppler      = math.cos(orbit_phase)
                    radial_fade  = 1.0 - (r - rs * 1.7) / (rs * 6.8)
                    # Latitude fade — dimmer near disk edges
                    lat_fade     = 1.0 - disk_latitude / max(disk_thickness, 0.01)
                    density      = radial_fade * lat_fade * (0.35 + 0.65 * (doppler + 1.0) / 2.0) * intensity
                    temp         = rs * 4.0 / r  # inner disk hotter
                    dchars       = " ·:+*#@█"
                    idx          = max(1, min(len(dchars) - 1, int(density * (len(dchars) - 1))))
                    ch           = dchars[idx]
                    if temp > 1.5:
                        attr = warn_attr if doppler > 0.15 else accent_attr
                    elif temp > 0.9:
                        attr = accent_attr if density > 0.4 else soft_attr
                    elif density > 0.55:
                        attr = accent_attr
                    else:
                        attr = soft_attr
                    try: stdscr.addstr(y, x, ch, attr)
                    except curses.error: pass
                    continue

                # ── Gravitationally lensed star background ─────────────
                # Lens bends apparent positions; add f-dependent shimmer
                lens       = (rs * rs) / (r * r + 0.01) * 2.0
                lens_theta = dragged_theta + lens * math.sin(dragged_theta + f * 0.003)
                sv         = (math.sin(lens_theta * 17.3)
                              * math.cos(r * 0.09 + lens_theta * 5.7))
                if sv > 0.82:
                    bright = (sv - 0.82) / 0.18
                    # Phase-shifted color so lensed stars aren't all one colour
                    phase  = (f * 0.003 + lens_theta / math.tau) % 1.0
                    if (bright + phase) % 1.0 > 0.55:
                        attr = bright_attr
                    else:
                        attr = soft_attr
                    try: stdscr.addstr(y, x, "*" if bright > 0.55 else "·", attr)
                    except curses.error: pass
                else:
                    try: stdscr.addstr(y, x, " ", base_dim)
                    except curses.error: pass

        # ── Draw live orbiting star particles on top ────────────────────
        schars = ["✦", "·", "*", "○"]
        for sx, sy, r, theta, omega, bright, ci in self._stars:
            px, py = int(sx), int(sy)
            if 1 <= py < h - 1 and 0 <= px < w - 1:
                blueshift = min(1.0, rs * 3.5 / max(r, 0.1))
                ch        = schars[ci % len(schars)]
                if blueshift > 0.65:
                    attr = warn_attr
                elif blueshift > 0.35 or bright > 0.75:
                    attr = bright_attr
                elif bright > 0.5:
                    attr = soft_attr
                else:
                    attr = base_attr
                try: stdscr.addstr(py, px, ch, attr)
                except curses.error: pass


register(BlackHoleV2Plugin())


# ── Neural Sky ─────────────────────────────────────────────────────────────────

class NeuralSkyV2Plugin(ThemePlugin):
    """Spiking neural network: membrane potentials, action potential propagation, synaptic fields."""
    name = "neural-sky"

    _N_NEURONS = 16
    _THRESH     = 1.0

    def __init__(self):
        self._neurons: Optional[List[dict]] = None
        self._signals: List[dict]           = []  # moving action potentials
        self._w = self._h = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init_neurons(self, w, h):
        import random
        rng = random.Random(42)
        self._neurons = []
        for i in range(self._N_NEURONS):
            self._neurons.append({
                "x":         rng.uniform(0.08, 0.92) * w,
                "y":         rng.uniform(0.12, 0.88) * h,
                "v":         rng.random() * 0.5,       # membrane potential
                "refractory": 0,
                "charge_rate": rng.uniform(0.004, 0.012),
                "connections": [],
            })
        # Wire up nearest 3 neighbours
        for i, n in enumerate(self._neurons):
            dists = sorted(range(self._N_NEURONS),
                           key=lambda j: (n["x"] - self._neurons[j]["x"])**2
                                        + (n["y"] - self._neurons[j]["y"])**2)
            n["connections"] = [j for j in dists[1:4]]
        self._w, self._h = w, h

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame

        if self._neurons is None or (w, h) != (self._w, self._h):
            self._init_neurons(w, h)

        intensity = state.intensity_multiplier
        neurons   = self._neurons

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        # Step neuron dynamics
        newly_fired = []
        for i, n in enumerate(neurons):
            if n["refractory"] > 0:
                n["refractory"] -= 1
                continue
            n["v"] += n["charge_rate"] * (1.0 + intensity * 2.0)
            if n["v"] >= self._THRESH:
                n["v"] = 0.0
                n["refractory"] = 18
                newly_fired.append(i)
                for j in n["connections"]:
                    nx2, ny2 = neurons[j]["x"], neurons[j]["y"]
                    dist = math.sqrt((n["x"] - nx2)**2 + (n["y"] - ny2)**2)
                    speed = max(0.5, dist / 18.0)
                    self._signals.append({
                        "x0": n["x"], "y0": n["y"],
                        "x1": nx2,    "y1": ny2,
                        "t":  0.0, "speed": speed / dist if dist > 0 else 0.1,
                        "target": j,
                    })

        # Step signals
        live_sigs = []
        for sig in self._signals:
            sig["t"] += sig["speed"]
            if sig["t"] < 1.0:
                live_sigs.append(sig)
            else:
                # Deliver post-synaptic current
                neurons[sig["target"]]["v"] = min(0.8, neurons[sig["target"]]["v"] + 0.3)
        self._signals = live_sigs[-40:]

        # Build voltage influence field per cell
        for y in range(1, h - 1):
            for x in range(0, w - 1):
                # Sum voltage influence from each neuron
                field = 0.0
                for n in neurons:
                    d2 = (x - n["x"])**2 + ((y - n["y"]) * 2.0)**2
                    field += n["v"] / (1.0 + d2 * 0.015)
                field = min(1.0, field * 0.12)

                chars = " \u00b7.:+*"
                idx = int(field * (len(chars) - 1))
                ch  = chars[max(0, min(len(chars) - 1, idx))]
                attr = base_dim if field < 0.15 else (soft_attr if field < 0.45 else accent_attr)
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

        # Draw axon connections (dim lines)
        for i, n in enumerate(neurons):
            for j in n["connections"]:
                if j <= i:
                    continue
                n2    = neurons[j]
                steps = max(abs(int(n2["x"]) - int(n["x"])), abs(int(n2["y"]) - int(n["y"])))
                steps = max(1, steps)
                for k in range(0, steps, 2):
                    t   = k / steps
                    ax  = int(n["x"] + (n2["x"] - n["x"]) * t)
                    ay  = int(n["y"] + (n2["y"] - n["y"]) * t)
                    if 1 <= ay < h - 1 and 0 <= ax < w - 1:
                        try:
                            stdscr.addstr(ay, ax, "\u00b7", base_dim)
                        except curses.error:
                            pass

        # Draw moving signals
        for sig in self._signals:
            sx = int(sig["x0"] + (sig["x1"] - sig["x0"]) * sig["t"])
            sy = int(sig["y0"] + (sig["y1"] - sig["y0"]) * sig["t"])
            if 1 <= sy < h - 1 and 0 <= sx < w - 1:
                try:
                    stdscr.addstr(sy, sx, "\u25cf", bright_attr)
                except curses.error:
                    pass

        # Draw neurons
        for i, n in enumerate(neurons):
            nx, ny = int(n["x"]), int(n["y"])
            if 1 <= ny < h - 1 and 0 <= nx < w - 1:
                if i in newly_fired:
                    ch   = "\u25c9"  # firing burst
                    attr = bright_attr
                elif n["refractory"] > 0:
                    ch   = "\u25cb"  # refractory
                    attr = base_dim
                else:
                    v    = n["v"] / self._THRESH
                    ch   = "\u25cf" if v > 0.7 else ("\u25cc" if v > 0.35 else "\u25cb")
                    attr = accent_attr if v > 0.7 else (soft_attr if v > 0.35 else base_dim)
                try:
                    stdscr.addstr(ny, nx, ch, attr)
                except curses.error:
                    pass


register(NeuralSkyV2Plugin())


# ── Storm Core — Lorenz Attractor ─────────────────────────────────────────────

class StormCoreV2Plugin(ThemePlugin):
    """Lorenz strange attractor — chaotic butterfly orbit as an ASCII density field.

    Four parallel trajectories with slightly different starting conditions
    accumulate a glowing density field that forms the classic two-lobe butterfly
    shape.  The system is deterministic-chaotic: trajectories diverge slowly but
    stay on the attractor.

    v0.2 upgrade:
      - reaction_diffusion_config: Turing-pattern chemical waves pulse behind
        the attractor, giving depth to the chaos
      - warp_field: saddle-point velocity distortion — the high-velocity region
        between the two wings warps the background field
      - echo_decay: 6 — deep orbital memory
      - glow_radius: 2 — density hotspots bloom
      - force_points: vortex attractors at the two lobe centres
      - depth_layers: 2
      - intensity_curve: power 0.6
      - react() x11 with chaos metaphors
      - palette_shift: error → red (bifurcation), memory → cyan (order)
      - special_effects: "bifurcation" — lobe centres alternately flash
      - ambient_tick: saddle-point wisp when idle
    """
    name = "storm-core"

    _SIGMA  = 10.0
    _RHO    = 28.0
    _BETA   = 8.0 / 3.0
    _DT     = 0.008
    _N_TRAJ = 4  # parallel trajectories

    def __init__(self):
        self._grid: Optional[List[List[float]]] = None
        self._trajs: Optional[List[List[float]]] = None
        self._w = self._h = 0
        self._heat: float = 0.0       # extra brightness from reactive events
        self._perturb: float = 0.0    # trajectory perturbation magnitude

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    # ── v0.2: Emergent ────────────────────────────────────────────────────────
    def reaction_diffusion_config(self):
        return {"feed": 0.035, "kill": 0.065, "update_interval": 3}

    def emergent_layer(self):
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────
    def warp_field(self, x, y, w, h, frame, intensity):
        # Saddle-point wind: strongest at (cx, z=27 row) — between the wings.
        cx = w / 2.0
        saddle_sy = int((1.0 - 27.0 / 50.0) * (h - 2)) + 1
        dx = x - cx
        dy = y - saddle_sy
        d2 = dx * dx + dy * dy + 1.0
        # Gaussian peak at saddle, wind direction tangential (perpendicular to radial)
        amp = intensity * 2.5 * math.exp(-d2 / (w * 0.06) ** 2)
        t = frame * 0.04
        wx = int(amp * math.sin(t + dy * 0.18))
        wy = int(amp * 0.4 * math.cos(t + dx * 0.13))
        return (max(0, min(w - 1, x + wx)), max(0, min(h - 1, y + wy)))

    def echo_decay(self):
        return 6

    def glow_radius(self):
        return 2

    def force_points(self, w, h, frame, intensity):
        sy = int((1.0 - 27.0 / 50.0) * (h - 2)) + 1
        sl = int(16.0 / 50.0 * (w - 2))
        sr = int(34.0 / 50.0 * (w - 2))
        strength = 0.4 + intensity * 0.55 + self._heat * 0.3
        return [
            {"x": sl, "y": sy, "strength": strength, "type": "vortex"},
            {"x": sr, "y": sy, "strength": strength, "type": "vortex"},
        ]

    def depth_layers(self):
        return 2

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────
    def intensity_curve(self, raw):
        return raw ** 0.6

    # ── v0.2: Reactive ────────────────────────────────────────────────────────
    def react(self, event_kind, data):
        import random as _r
        cx, cy = 0.5, 0.5

        if event_kind == "agent_start":
            self._perturb = 0.8
            self._heat = 0.5
            return Reaction(element=ReactiveElement.PULSE, intensity=1.0,
                           origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "llm_start":
            self._heat = 0.4
            return Reaction(element=ReactiveElement.STREAM, intensity=0.85,
                           origin=(0.0, 0.5), color_key="accent", duration=3.0)
        if event_kind == "llm_chunk":
            lobe = _r.choice([-1, 1])
            ox = max(0.0, min(1.0, 0.5 + lobe * 0.22))
            oy = max(0.0, min(1.0, 0.4 + _r.uniform(-0.1, 0.1)))
            return Reaction(element=ReactiveElement.SPARK, intensity=0.45,
                           origin=(ox, oy), color_key="accent", duration=0.4)
        if event_kind == "llm_end":
            self._heat = max(0.0, self._heat - 0.3)
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.5,
                           origin=(cx, cy), color_key="soft", duration=1.5)
        if event_kind in ("tool_call", "mcp_tool_call"):
            self._perturb = 0.35
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.7,
                           origin=(_r.uniform(0.2, 0.8), _r.uniform(0.3, 0.7)),
                           color_key="accent", duration=1.8)
        if event_kind in ("memory_save", "skill_create"):
            self._heat = 0.6
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                           origin=(cx, cy), color_key="bright", duration=3.0)
        if event_kind in ("error", "crash"):
            self._perturb = 1.5
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(_r.uniform(0.3, 0.7), 0.5),
                           color_key="warning", duration=2.5)
        if event_kind in ("cron_tick", "background_proc"):
            lobe = _r.choice([0.28, 0.72])
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.4,
                           origin=(lobe, 0.46), color_key="soft", duration=3.5)
        if event_kind == "subagent_started":
            lobe = _r.choice([-1, 1])
            ox = max(0.0, min(1.0, 0.5 + lobe * 0.22))
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.7,
                           origin=(ox, 0.45), color_key="accent", duration=2.0)
        if event_kind in ("dangerous_cmd", "approval_request"):
            return Reaction(element=ReactiveElement.SPARK, intensity=1.0,
                           origin=(cx, cy), color_key="warning", duration=2.0)
        if event_kind in ("context_pressure", "token_usage"):
            return Reaction(element=ReactiveElement.GAUGE,
                           intensity=data.get("ratio", 0.6),
                           origin=(0.05, 0.9), color_key="warning", duration=3.0)
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────
    def palette_shift(self, trigger_effect, intensity, base_palette):
        if trigger_effect in ("error", "crash") or str(trigger_effect) == str(ReactiveElement.SHATTER):
            return (curses.COLOR_RED, curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_RED)
        if trigger_effect in ("memory_save", "skill_create") or str(trigger_effect) == str(ReactiveElement.BLOOM):
            return (curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_BLUE, curses.COLOR_CYAN)
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────
    def special_effects(self):
        return [
            SpecialEffect(name="bifurcation",
                         trigger_kinds=["burst", "error"],
                         min_intensity=0.5, cooldown=6.0, duration=3.0),
        ]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        if special_name != "bifurcation":
            return
        w, h = state.width, state.height
        sl = int(16.0 / 50.0 * (w - 2))
        sr = int(34.0 / 50.0 * (w - 2))
        sy = int((1.0 - 27.0 / 50.0) * (h - 2)) + 1
        beat = math.sin(progress * math.pi * 6)
        attr_b = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        attr_a = curses.color_pair(color_pairs.get("accent", 0))
        attr_s = curses.color_pair(color_pairs.get("soft", 0))
        r = int(3 + progress * 8)
        la = attr_b if beat > 0 else attr_s
        ra = attr_b if beat < 0 else attr_s
        for lx, lattr in [(sl, la), (sr, ra)]:
            for deg in range(0, 360, 20):
                theta = math.radians(deg)
                px = int(lx + r * math.cos(theta) * 2)
                py = int(sy + r * math.sin(theta))
                if 0 <= px < w and 0 <= py < h:
                    _safe(stdscr, py, px, "◉" if abs(beat) > 0.5 else "○", lattr)
            if 0 <= lx < w and 0 <= sy < h:
                _safe(stdscr, sy, lx, "✦" if abs(beat) > 0.5 else "·", lattr)

    # ── v0.2: Ambient tick ────────────────────────────────────────────────────
    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        if idle_seconds > 1.5 and state.frame % 18 == 0 and self._trajs:
            w, h = state.width, state.height
            saddle_sx = w // 2
            saddle_sy = int((1.0 - 27.0 / 50.0) * (h - 2)) + 1
            import random as _r2
            rng2 = _r2.Random(state.frame % 500)
            ox = saddle_sx + rng2.randint(-2, 2)
            oy = saddle_sy + rng2.randint(-1, 1)
            if 0 <= ox < w and 1 <= oy < h - 1:
                attr = curses.color_pair(color_pairs.get("soft", 0)) | curses.A_DIM
                _safe(stdscr, oy, ox, "·", attr)
            self._heat    = max(0.0, self._heat - 0.02)
            self._perturb = max(0.0, self._perturb - 0.05)

    def _init(self, w, h):
        self._grid  = [[0.0] * w for _ in range(h)]
        self._trajs = [
            [0.1 + i * 0.3, 0.0, 14.0 + i * 0.5]
            for i in range(self._N_TRAJ)
        ]
        self._w, self._h = w, h

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height

        if self._grid is None or (w, h) != (self._w, self._h):
            self._init(w, h)

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        intensity = state.intensity_multiplier
        grid = self._grid

        # Lorenz: x ∈ [-25,25], z ∈ [0,50]
        # Map: sx=(x+25)/50*w, sy=(1-z/50)*(h-2)+1
        steps_per_frame = int(120 * (0.5 + intensity))
        s, r_param, b = self._SIGMA, self._RHO, self._BETA
        # Apply perturbation to deposit multiplier
        deposit = 0.08 + self._perturb * 0.06

        for traj in self._trajs:
            x, y, z = traj
            for _ in range(steps_per_frame):
                dx = s * (y - x)
                dy = x * (r_param - z) - y
                dz = x * y - b * z
                x += dx * self._DT
                y += dy * self._DT
                z += dz * self._DT
                sx = int((x + 25) / 50.0 * (w - 2))
                sy = int((1.0 - z / 50.0) * (h - 2)) + 1
                if 1 <= sy < h - 1 and 0 <= sx < w - 1:
                    grid[sy][sx] = min(grid[sy][sx] + deposit, 1.0)
            traj[0], traj[1], traj[2] = x, y, z

        # Decay — faster with heat (heat = recent activity = faster fade = more dynamic)
        decay  = 0.988 - 0.006 * intensity - 0.003 * self._heat
        chars  = " \u00b7.:;+=*#@"
        n_chars = len(chars)
        # Hue phase sweeps slowly — colors walk around the attractor over time
        hue_base = (state.frame * 0.004) % 1.0

        for y in range(1, h - 1):
            row = grid[y]
            for x in range(0, w - 1):
                v = row[x]
                row[x] = v * decay
                idx = int(v * (n_chars - 1))
                idx = max(0, min(n_chars - 1, idx))
                ch  = chars[idx]
                # Phase-shifted color: same value lands in different color tiers
                # over time — makes the attractor slowly change color
                xf = x / max(w, 1)
                phase = (hue_base + xf * 0.3) % 1.0
                vp = (v + phase) % 1.0
                if v < 0.08:
                    attr = base_dim
                elif vp < 0.35:
                    attr = soft_attr
                elif vp < 0.65:
                    attr = accent_attr
                else:
                    attr = bright_attr
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


register(StormCoreV2Plugin())


# ── Moonwire — Hexagonal Phase Waves ──────────────────────────────────────────

class MoonwireV2Plugin(ThemePlugin):
    """Three traveling wave sources create interference moiré patterns on a hex-inspired grid."""
    name = "moonwire"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        intensity = state.intensity_multiplier

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        # Three wave sources orbiting the screen centre
        t = f * 0.012
        sources = [
            (0.5 + 0.32 * math.cos(t        ),  0.5 + 0.28 * math.sin(t        ),  1.0, 0.22),
            (0.5 + 0.32 * math.cos(t + 2.094),  0.5 + 0.28 * math.sin(t + 2.094), 0.85, 0.18),
            (0.5 + 0.28 * math.cos(t + 4.189),  0.5 + 0.26 * math.sin(t + 4.189), 0.7,  0.25),
        ]
        # Intensity-driven fourth pulse source
        if intensity > 0.55:
            pulse_t = f * 0.04
            sources.append((0.5 + 0.15 * math.cos(pulse_t * 2.7),
                             0.5 + 0.12 * math.sin(pulse_t * 3.1),
                             intensity, 0.30))

        # Hex-distorted coordinates: shift odd rows right by half a cell
        chars = " \u00b7.:+*\u2592\u2593\u2588"

        for y in range(1, h - 1):
            # Hexagonal offset: shift x by 0.5 on odd rows
            hex_ox = 0.5 if (y % 2 == 1) else 0.0
            for x in range(0, w - 1):
                nx = (x + hex_ox) / max(w, 1)
                ny = y / max(h, 1)
                ax = 1.0
                ay = 2.2 / max(1, h / max(w, 1))

                wave_sum = 0.0
                for sx, sy, amp, freq in sources:
                    dx = (nx - sx) * ax * w
                    dy = (ny - sy) * ay * h
                    dist = math.sqrt(dx * dx + dy * dy)
                    wave = math.sin(dist * freq * 2 * math.pi - f * 0.14)
                    wave_sum += amp * wave

                v = (wave_sum / len(sources) + 1.0) * 0.5  # 0..1
                idx = int(v * (len(chars) - 1))
                idx = max(0, min(len(chars) - 1, idx))
                ch  = chars[idx]

                if v < 0.2:
                    attr = base_dim
                elif v < 0.45:
                    attr = soft_attr
                elif v < 0.72:
                    attr = accent_attr
                else:
                    attr = bright_attr

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


register(MoonwireV2Plugin())


# ── Rootsong — L-System Fractal Plant ─────────────────────────────────────────

class RootsongV2Plugin(ThemePlugin):
    """L-system fractal plant: grows branch-by-branch, then restarts with a new variant."""
    name = "rootsong"

    # L-system rules + params
    _SYSTEMS = [
        # (axiom, rules, angle, iters)
        ("X", {"X": "F+[[X]-X]-F[-FX]+X", "F": "FF"}, 22.5, 5),
        ("F", {"F": "F[+F]F[-F][F]"},                  25.7, 4),
        ("X", {"X": "F[+X]F[-X]+X",       "F": "FF"}, 20.0, 5),
    ]

    def __init__(self):
        self._segments: List[Tuple[int,int,int,int,int]] = []  # (x0,y0,x1,y1,depth)
        self._reveal    = 0
        self._speed     = 3
        self._system_idx = 0
        self._w = self._h = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _expand(self, axiom, rules, iters):
        s = axiom
        for _ in range(iters):
            s = "".join(rules.get(c, c) for c in s)
            if len(s) > 60000:
                break
        return s

    def _build(self, w, h):
        axiom, rules, angle_deg, iters = self._SYSTEMS[self._system_idx]
        string = self._expand(axiom, rules, iters)
        angle  = math.radians(angle_deg)

        # Start at bottom-centre, pointing up
        x, y, a = w / 2.0, h - 2.0, -math.pi / 2.0
        stack: List[Tuple[float,float,float]] = []
        segs: List[Tuple[int,int,int,int,int]] = []
        step_len = h * 0.022
        depth    = 0

        for ch in string:
            if ch == "F":
                nx = x + math.cos(a) * step_len
                ny = y + math.sin(a) * step_len
                segs.append((int(x), int(y), int(nx), int(ny), depth))
                x, y = nx, ny
            elif ch == "+":
                a += angle
            elif ch == "-":
                a -= angle
            elif ch == "[":
                stack.append((x, y, a))
                depth += 1
                step_len *= 0.96
            elif ch == "]":
                if stack:
                    x, y, a = stack.pop()
                depth = max(0, depth - 1)
                step_len /= 0.96

        self._segments  = segs
        self._reveal    = 0
        self._w, self._h = w, h

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height

        if not self._segments or (w, h) != (self._w, self._h):
            self._build(w, h)

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        # Clear
        for y in range(1, h - 1):
            for x in range(0, w - 1):
                try:
                    stdscr.addstr(y, x, " ", base_dim)
                except curses.error:
                    pass

        # Advance reveal
        self._reveal = min(self._reveal + self._speed, len(self._segments))
        if self._reveal >= len(self._segments):
            # Pause then reset with next system
            if state.frame % 80 == 0:
                self._system_idx = (self._system_idx + 1) % len(self._SYSTEMS)
                self._build(w, h)

        # Draw revealed segments
        for i in range(self._reveal):
            x0, y0, x1, y1, depth = self._segments[i]
            max_depth  = 6
            depth_frac = min(1.0, depth / max_depth)

            if depth_frac < 0.3:
                attr = accent_attr  # trunk: amber
            elif depth_frac < 0.65:
                attr = soft_attr    # branches: green
            else:
                attr = bright_attr  # leaves: bright white/cyan

            # Bresenham line
            dx = abs(x1 - x0)
            dy = abs(y1 - y0)
            sx = 1 if x0 < x1 else -1
            sy = 1 if y0 < y1 else -1
            err = dx - dy
            px, py = x0, y0
            for _ in range(max(dx, dy) + 1):
                if 1 <= py < h - 1 and 0 <= px < w - 1:
                    ch = "|" if dy > dx else ("-" if dx > dy * 2 else "/")
                    if dx == dy:
                        ch = "/" if sx == sy else "\\"
                    try:
                        stdscr.addstr(py, px, ch, attr)
                    except curses.error:
                        pass
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    px  += sx
                if e2 < dx:
                    err += dx
                    py  += sy


register(RootsongV2Plugin())


# ── Stormglass — Rotating Pressure Systems ────────────────────────────────────

class StormglassV2Plugin(ThemePlugin):
    """Atmospheric pressure field: isobar contours, H/L centres, gradient wind arrows."""
    name = "stormglass"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        intensity = state.intensity_multiplier

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        t = f * 0.008
        # Pressure centres: (x_frac, y_frac, strength_-1..1, orbital_radius, orbital_speed)
        centres = [
            (0.5 + 0.30 * math.cos(t       ), 0.5 + 0.25 * math.sin(t        ),  1.5),  # high
            (0.5 + 0.30 * math.cos(t + 3.14), 0.5 + 0.25 * math.sin(t + 3.14), -1.5),  # low
            (0.5 + 0.20 * math.cos(t * 1.5 + 1.0), 0.5 + 0.18 * math.sin(t * 1.5), 0.8),
            (0.5 + 0.22 * math.cos(t * 0.8 + 2.0), 0.5 + 0.20 * math.sin(t * 0.8 + 4.0), -0.9),
        ]

        ay = 2.1
        # Arrow characters for gradient direction
        arrows = "\u2190\u2196\u2191\u2197\u2192\u2198\u2193\u2199"  # ←↖↑↗→↘↓↙

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                nx = x / max(w - 1, 1)
                ny = y / max(h - 1, 1)

                # Pressure = sum of inverse-distance-squared Gaussians
                pressure = 0.0
                grad_x   = 0.0
                grad_y   = 0.0
                for cx2, cy2, strength in centres:
                    dx = (nx - cx2) * w
                    dy = (ny - cy2) * h / ay
                    d2 = dx * dx + dy * dy + 0.5
                    pressure += strength * 20.0 / d2
                    grad_x   += -strength * 40.0 * dx / (d2 * d2)
                    grad_y   += -strength * 40.0 * dy / (d2 * d2)

                # Isobar lines: where pressure ≈ integer multiple of 2
                iso_dist = abs(pressure % 2.0 - 1.0)  # 0 = on isobar, 1 = midway
                on_isobar = iso_dist < 0.18

                # Wind arrow every 6 cols, 3 rows
                is_arrow_cell = (x % 6 == 3) and (y % 3 == 1)

                if on_isobar:
                    attr = bright_attr if pressure > 0 else accent_attr
                    # Align isobar char to gradient direction
                    gm   = math.sqrt(grad_x * grad_x + grad_y * grad_y) + 1e-6
                    perp_angle = math.atan2(grad_y / gm, grad_x / gm) + math.pi / 2
                    perp_angle_deg = math.degrees(perp_angle) % 180
                    ch = "─" if perp_angle_deg < 22.5 or perp_angle_deg > 157.5 else (
                         "/" if perp_angle_deg < 67.5 else (
                         "|" if perp_angle_deg < 112.5 else "\\"))
                    try:
                        stdscr.addstr(y, x, ch, attr)
                    except curses.error:
                        pass
                elif is_arrow_cell:
                    gm  = math.sqrt(grad_x * grad_x + grad_y * grad_y) + 1e-6
                    ang = math.atan2(grad_y / gm, grad_x / gm)
                    idx = int((ang + math.pi) / (2 * math.pi) * 8) % 8
                    try:
                        stdscr.addstr(y, x, arrows[idx], soft_attr)
                    except curses.error:
                        pass
                else:
                    v    = max(0.0, min(1.0, (pressure + 3) / 6.0))
                    chars = " \u00b7.:"
                    idx  = int(v * (len(chars) - 1))
                    try:
                        stdscr.addstr(y, x, chars[idx], base_dim)
                    except curses.error:
                        pass

        # Draw H/L labels at pressure centres
        for cx2, cy2, strength in centres:
            lx = int(cx2 * (w - 2))
            ly = int(cy2 * (h - 2)) + 1
            if 1 <= ly < h - 1 and 0 <= lx < w - 1:
                label = "H" if strength > 0 else "L"
                attr  = bright_attr if strength > 0 else accent_attr
                try:
                    stdscr.addstr(ly, lx, label, attr)
                except curses.error:
                    pass


register(StormglassV2Plugin())


# ── Spiral Galaxy ─────────────────────────────────────────────────────────────

class SpiralGalaxyV2Plugin(ThemePlugin):
    """Logarithmic spiral arms with density waves, differential rotation, and a glowing bulge."""
    name = "spiral-galaxy"

    _N_ARMS  = 2
    _B       = 0.25   # spiral tightness (log spiral parameter)

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        intensity = state.intensity_multiplier

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        cx_f, cy_f = w / 2.0, h / 2.0
        ay = 2.2  # terminal aspect
        max_r  = min(cx_f, cy_f * ay) * 0.9
        rot    = f * 0.004  # galactic rotation
        spread = 2.2        # arm width in pixels

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                dx = x - cx_f
                dy = (y - cy_f) * ay
                r  = math.sqrt(dx * dx + dy * dy)
                if r < 0.5:
                    try:
                        stdscr.addstr(y, x, "\u2588", bright_attr)
                    except curses.error:
                        pass
                    continue

                theta = math.atan2(dy, dx)
                r_norm = r / max_r

                # Galactic bulge: Gaussian core
                bulge = math.exp(-r_norm * r_norm * 8.0)

                # Differential rotation: inner orbits faster
                omega  = rot / (r_norm + 0.1)
                theta_rot = theta - omega  # current rotated angle

                # Distance to nearest spiral arm
                min_arm_dist = float("inf")
                for arm in range(self._N_ARMS):
                    arm_offset = (2 * math.pi / self._N_ARMS) * arm
                    # Logarithmic spiral: r = a * exp(b * theta) → theta = ln(r/a) / b
                    theta_arm  = (math.log(max(r, 0.5)) - math.log(1.0)) / self._B + arm_offset
                    # Angular difference (wrapped)
                    d_theta = (theta_rot - theta_arm) % (2 * math.pi)
                    if d_theta > math.pi:
                        d_theta = 2 * math.pi - d_theta
                    arc_dist = d_theta * r  # arc length distance
                    min_arm_dist = min(min_arm_dist, arc_dist)

                arm_glow = math.exp(-min_arm_dist * min_arm_dist / (spread * spread * 2))
                density_wave = 0.5 + 0.5 * math.cos(r_norm * math.pi * 4 - f * 0.02)
                brightness   = min(1.0, bulge * 3.0 + arm_glow * density_wave * (0.5 + 0.5 * intensity))

                if r_norm > 1.02:
                    brightness = 0.0

                chars = " \u00b7.:\u00b7*+\u2726"
                idx   = int(brightness * (len(chars) - 1))
                idx   = max(0, min(len(chars) - 1, idx))
                ch    = chars[idx]

                if brightness > 0.75:
                    attr = bright_attr
                elif brightness > 0.4:
                    attr = accent_attr
                elif brightness > 0.15:
                    attr = soft_attr
                else:
                    attr = base_dim

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


register(SpiralGalaxyV2Plugin())
