"""Redesigned nature themes using full-screen ASCII field engine.

Themes: deep-abyss, storm-sea, dark-forest, mountain-stars, beach-lighthouse
"""

from __future__ import annotations

import curses
import math
import random
from typing import List, Optional

from hermes_neurovision.plugin import ThemePlugin, Reaction, ReactiveElement, SpecialEffect
from hermes_neurovision.theme_plugins import register


# ── Deep Abyss — Bioluminescent Ocean ─────────────────────────────────────────

class DeepAbyssV2Plugin(ThemePlugin):
    """Bioluminescent deep-ocean: drifting creatures, marine snow, pressure waves."""
    name = "deep-abyss"

    _N_CREATURES = 5

    def __init__(self):
        self._creatures: Optional[List[dict]] = None
        self._snow: List[List[float]] = []   # [x, y, brightness, speed]
        self._rng  = random.Random(77)
        self._w = self._h = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init(self, w, h):
        rng = self._rng
        self._creatures = []
        for _ in range(self._N_CREATURES):
            self._creatures.append({
                "x":    rng.uniform(0.05, 0.95) * w,
                "y":    rng.uniform(0.1,  0.9)  * h,
                "vx":   rng.uniform(-0.04, 0.04),
                "vy":   rng.uniform(-0.02, 0.02),
                "radius": rng.uniform(3.0, 7.0),
                "phase":  rng.uniform(0, math.tau),
                "freq":   rng.uniform(0.03, 0.08),
                "color":  rng.choice(["bright", "accent", "soft"]),
            })
        # Marine snow particles
        self._snow = [
            [rng.uniform(0, w), rng.uniform(0, h),
             rng.uniform(0.3, 1.0), rng.uniform(0.01, 0.04)]
            for _ in range(60)
        ]
        self._w, self._h = w, h

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame

        if self._creatures is None or (w, h) != (self._w, self._h):
            self._init(w, h)

        intensity = state.intensity_multiplier
        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        color_map   = {"bright": bright_attr, "accent": accent_attr, "soft": soft_attr}

        # Step creatures
        for c in self._creatures:
            c["x"] = (c["x"] + c["vx"] + self._rng.uniform(-0.02, 0.02)) % w
            c["y"] = (c["y"] + c["vy"] + self._rng.uniform(-0.01, 0.01)) % h
            c["phase"] += c["freq"]

        # Step marine snow
        for p in self._snow:
            p[1] += p[3]
            if p[1] >= h:
                p[1] = 0.0
                p[0] = self._rng.uniform(0, w)

        # Render field
        for y in range(1, h - 1):
            # Depth gradient: darker near bottom
            depth_fade = 0.06 + (y / h) * 0.12
            for x in range(0, w - 1):
                # Bio-luminescence: sum Gaussian glow from each creature
                glow = 0.0
                dominant_c = None
                for c in self._creatures:
                    pulse = (math.sin(c["phase"]) + 1.0) * 0.5
                    ax  = 1.0
                    ay  = 2.2
                    d2  = ((x - c["x"]) / ax)**2 + ((y - c["y"]) / ay)**2
                    g   = c["radius"] * pulse * math.exp(-d2 / (c["radius"]**2)) * intensity
                    if g > glow:
                        glow = g
                        dominant_c = c

                v = min(1.0, glow + depth_fade)

                chars = " \u00b7.:\u2591\u2592"
                idx   = int(v * (len(chars) - 1))
                ch    = chars[max(0, min(len(chars) - 1, idx))]

                if dominant_c and glow > 0.35:
                    attr = color_map.get(dominant_c["color"], soft_attr)
                elif v > 0.2:
                    attr = base_dim
                else:
                    attr = base_dim

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

        # Marine snow overlay
        for p in self._snow:
            sx, sy = int(p[0]), int(p[1])
            if 1 <= sy < h - 1 and 0 <= sx < w - 1:
                if self._rng.random() < p[2] * 0.6:
                    try:
                        stdscr.addstr(sy, sx, "\u00b7", soft_attr)
                    except curses.error:
                        pass

        # Anglerfish lure: rare, random, pulsing single point
        if f % 180 < 30:
            lx = int(w * 0.6 + math.sin(f * 0.1) * w * 0.15)
            ly = int(h * 0.55 + math.cos(f * 0.07) * h * 0.1)
            brightness = math.sin(f * 0.18) * 0.5 + 0.5
            if 1 <= ly < h - 1 and 0 <= lx < w - 1 and brightness > 0.4:
                try:
                    stdscr.addstr(ly, lx, "*", bright_attr)
                except curses.error:
                    pass


    # ── v0.2: Emergent system ─────────────────────────────────────────────────

    def physarum_config(self):
        return {"n_agents": 120, "sensor_angle": 0.4, "sensor_dist": 4,
                "speed": 0.5, "deposit": 0.8, "decay": 0.97}

    def emergent_layer(self):
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────

    def glow_radius(self):
        return 2

    def echo_decay(self):
        return 5

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────

    def intensity_curve(self, raw):
        return raw ** 0.5

    # ── v0.2: Reactive system ─────────────────────────────────────────────────

    def react(self, event_kind, data):
        cx, cy = 0.5, 0.5
        rng = random
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.9,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "llm_start":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.8,
                            origin=(cx, cy), color_key="accent", duration=3.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.4,
                            origin=(rng.random(), rng.random()),
                            color_key="bright", duration=0.5)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.65,
                            origin=(rng.random(), rng.random()),
                            color_key="accent", duration=1.5)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.75,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "error":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                            origin=(rng.random(), rng.random()),
                            color_key="warning", duration=2.0)
        if event_kind == "dangerous_cmd":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.9,
                            origin=(rng.random(), rng.random()),
                            color_key="warning", duration=1.0)
        if event_kind == "cron_tick":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.5,
                            origin=(rng.random(), rng.random()),
                            color_key="soft", duration=2.0)
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────

    def palette_shift(self, trigger_effect, intensity, base_palette):
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────

    def special_effects(self):
        return [SpecialEffect(name="abyss-bloom", trigger_kinds=["burst"],
                              min_intensity=0.3, cooldown=5.0, duration=3.0)]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        if special_name != "abyss-bloom":
            return
        w, h = state.width, state.height
        cx, cy = w // 2, h // 2
        max_r = int(min(w, h) * 0.4 * math.sin(progress * math.pi))
        bright_attr = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        for r in range(1, max(2, max_r), 2):
            for angle_deg in range(0, 360, 20):
                angle = math.radians(angle_deg)
                px = cx + int(r * math.cos(angle) * 2)
                py = cy + int(r * math.sin(angle))
                if 1 <= py < h - 1 and 0 <= px < w - 1:
                    try:
                        stdscr.addstr(py, px, "*", bright_attr)
                    except curses.error:
                        pass

    # ── v0.2: Ambient tick ────────────────────────────────────────────────────

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        pass  # creatures drift and pulse continuously via draw_extras


register(DeepAbyssV2Plugin())


# ── Storm Sea — Gerstner Wave Ocean ───────────────────────────────────────────

class StormSeaV2Plugin(ThemePlugin):
    """Ocean surface via superimposed wave trains; storm intensity drives amplitude."""
    name = "storm-sea"

    # (amplitude_frac, spatial_freq, temporal_freq, phase_offset, direction_x)
    _WAVES = [
        (0.28, 0.18, 0.10, 0.00,  1.0),
        (0.18, 0.28, 0.14, 1.57,  0.7),
        (0.12, 0.40, 0.20, 0.79,  1.3),
        (0.08, 0.60, 0.28, 2.36,  0.9),
        (0.05, 0.90, 0.38, 3.14,  1.1),
    ]

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        intensity = state.intensity_multiplier

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        horizon = int(h * 0.32)  # row where sky meets sea
        amp_scale = 0.5 + intensity * 1.5

        # Precompute wave height profile per column
        t = f * 0.05
        profile = []
        for x in range(w):
            elev = 0.0
            for amp, kx, omega, phase, dirx in self._WAVES:
                elev += amp * amp_scale * math.sin(kx * x * dirx * 0.3 - omega * t + phase)
            profile.append(elev)

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                if y < horizon - 1:
                    # Sky: sparse stars
                    star = math.sin(x * 17.3 + 0.1) * math.sin(y * 11.7 + 0.2)
                    if star > 0.93:
                        try:
                            stdscr.addstr(y, x, "\u00b7" if star < 0.97 else "*", soft_attr)
                        except curses.error:
                            pass
                    else:
                        try:
                            stdscr.addstr(y, x, " ", base_dim)
                        except curses.error:
                            pass
                    continue

                # Ocean: map y relative to animated surface
                wave_row = horizon + profile[x]
                depth    = y - wave_row

                if depth < 0:
                    # Above wave surface — sky continuation
                    try:
                        stdscr.addstr(y, x, " ", base_dim)
                    except curses.error:
                        pass
                elif depth < 0.8:
                    # Wave surface / crest
                    choppiness = abs(profile[x]) / (amp_scale + 0.1)
                    if choppiness > 0.65:
                        ch = "^" if intensity > 0.7 else "~"
                        try:
                            stdscr.addstr(y, x, ch, bright_attr)
                        except curses.error:
                            pass
                    else:
                        slope = profile[x] - profile[x - 1] if x > 0 else 0
                        ch = "/" if slope > 0.4 else ("\\" if slope < -0.4 else "~")
                        try:
                            stdscr.addstr(y, x, ch, accent_attr)
                        except curses.error:
                            pass
                elif depth < 3.0:
                    # Subsurface — wave body
                    sub   = 1.0 - depth / 3.0
                    chars = "~\u2248=\u2014"
                    idx   = int((1 - sub) * (len(chars) - 1))
                    try:
                        stdscr.addstr(y, x, chars[idx], soft_attr if sub > 0.5 else base_dim)
                    except curses.error:
                        pass
                else:
                    # Deep water
                    deep_wave = math.sin(x * 0.15 + y * 0.08 - t * 0.05) * 0.5 + 0.5
                    chars = " \u00b7."
                    idx   = int(deep_wave * (len(chars) - 1))
                    try:
                        stdscr.addstr(y, x, chars[idx], base_dim)
                    except curses.error:
                        pass


    # ── v0.2: Emergent system ─────────────────────────────────────────────────

    def wave_config(self):
        return {"speed": 0.6, "damping": 0.94}

    def emergent_layer(self):
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────

    def glow_radius(self):
        return 1

    def echo_decay(self):
        return 2

    def warp_field(self, x, y, w, h, frame, intensity):
        """Wave orbital motion — pixels near crests pushed forward, troughs back."""
        xf = x / max(w, 1)
        yf = y / max(h, 1)
        t = frame * 0.05
        # Horizontal wave push
        wave = math.sin(xf * 3.0 - t) * intensity * 2.0
        ny = max(0, min(h - 1, y + int(wave * 0.4)))
        nx = max(0, min(w - 1, x + int(wave * 0.2)))
        return (nx, ny)

    def force_points(self, w, h, frame, intensity):
        """3 storm vortex cells drifting across the surface."""
        t = frame * 0.003
        strength = 0.3 + intensity * 0.3
        return [
            {"x": int(w * (0.2 + 0.1 * math.sin(t))),
             "y": int(h * 0.4), "strength": strength, "type": "vortex"},
            {"x": int(w * (0.5 + 0.1 * math.cos(t * 0.7))),
             "y": int(h * 0.35), "strength": strength, "type": "vortex"},
            {"x": int(w * (0.8 + 0.1 * math.sin(t * 1.3))),
             "y": int(h * 0.45), "strength": strength, "type": "vortex"},
        ]

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────

    def intensity_curve(self, raw):
        return raw ** 0.7

    # ── v0.2: Reactive system ─────────────────────────────────────────────────

    def react(self, event_kind, data):
        cx, cy = 0.5, 0.5
        rng = random
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.9,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "llm_start":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.85,
                            origin=(0.0, cy), color_key="accent", duration=3.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.5,
                            origin=(rng.random(), rng.random()),
                            color_key="bright", duration=0.5)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.65,
                            origin=(rng.random(), rng.random()),
                            color_key="accent", duration=1.5)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.75,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "error":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                            origin=(rng.random(), rng.random()),
                            color_key="warning", duration=2.0)
        if event_kind == "context_pressure":
            return Reaction(element=ReactiveElement.GAUGE,
                            intensity=data.get("level", 0.5),
                            origin=(cx, cy), color_key="accent", duration=2.0)
        if event_kind == "compression_started":
            return Reaction(element=ReactiveElement.WAVE, intensity=0.9,
                            origin=(cx, cy), color_key="warning", duration=3.0)
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────

    def palette_shift(self, trigger_effect, intensity, base_palette):
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────

    def special_effects(self):
        return [SpecialEffect(name="rogue-wave", trigger_kinds=["burst"],
                              min_intensity=0.4, cooldown=6.0, duration=2.5)]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        if special_name != "rogue-wave":
            return
        w, h = state.width, state.height
        bright_attr = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs.get("accent", 0))
        # A single massive wave sweeping upward
        wave_y = int(h * (1.0 - progress))
        for y_off in range(3):
            wy = wave_y + y_off
            if 1 <= wy < h - 1:
                for x in range(0, w - 1):
                    ch = "^" if y_off == 0 else "~"
                    attr = bright_attr if y_off == 0 else accent_attr
                    try:
                        stdscr.addstr(wy, x, ch, attr)
                    except curses.error:
                        pass

    # ── v0.2: Ambient tick ────────────────────────────────────────────────────

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        pass  # sea swell evolves continuously via draw_extras


register(StormSeaV2Plugin())


# ── Dark Forest — Silhouette + Fireflies ──────────────────────────────────────

class DarkForestV2Plugin(ThemePlugin):
    """Dark forest silhouette against night sky, with fireflies and a moonbeam."""
    name = "dark-forest"

    _N_FLIES = 28

    def __init__(self):
        self._flies: Optional[List[dict]] = None
        self._rng   = random.Random(33)
        self._w = self._h = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init(self, w, h):
        rng = self._rng
        self._flies = []
        for _ in range(self._N_FLIES):
            self._flies.append({
                "x":    rng.uniform(0, w),
                "y":    rng.uniform(int(h * 0.35), h - 2),
                "phase": rng.uniform(0, math.tau),
                "freq":  rng.uniform(0.04, 0.12),
                "vx":    rng.uniform(-0.06, 0.06),
                "vy":    rng.uniform(-0.02, 0.02),
            })
        self._w, self._h = w, h

    def _silhouette(self, x, w, h):
        """Returns the row of the forest/hill silhouette at column x."""
        nx = x / max(w - 1, 1)
        # Multi-harmonic hill profile
        y = (0.52
             + 0.10 * math.sin(nx * math.pi * 3.0)
             + 0.06 * math.sin(nx * math.pi * 7.3 + 1.1)
             + 0.04 * math.sin(nx * math.pi * 14.0 + 2.3)
             + 0.03 * math.cos(nx * math.pi * 21.0))
        return int(y * h)

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame

        if self._flies is None or (w, h) != (self._w, self._h):
            self._init(w, h)

        intensity = state.intensity_multiplier
        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        # Step fireflies
        for fly in self._flies:
            fly["x"] = (fly["x"] + fly["vx"] + self._rng.uniform(-0.05, 0.05)) % w
            fly["y"] = max(1.0, min(h - 2.0,
                           fly["y"] + fly["vy"] + self._rng.uniform(-0.02, 0.02)))
            fly["phase"] += fly["freq"]

        moon_x = int(w * 0.80)
        moon_y = int(h * 0.12)

        # Precompute silhouette per column
        sil = [self._silhouette(x, w, h) for x in range(w)]

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                above_sil = y < sil[x]

                if above_sil:
                    # Sky region
                    # Moonbeam: vertical column from moon
                    beam_dist = abs(x - moon_x)
                    if beam_dist < 2:
                        beam_frac = 1.0 - beam_dist * 0.5
                        beam_frac *= max(0.0, 1.0 - y / moon_y) if y < moon_y else (
                                      (y - moon_y) / max(1, sil[x] - moon_y))
                        beam_frac = max(0.0, min(1.0, beam_frac))
                        if beam_frac > 0.2:
                            try:
                                stdscr.addstr(y, x, "|", soft_attr)
                            except curses.error:
                                pass
                            continue

                    # Moon
                    if abs(y - moon_y) <= 1 and abs(x - moon_x) <= 2:
                        try:
                            stdscr.addstr(y, x, "\u25cf", bright_attr)
                        except curses.error:
                            pass
                        continue

                    # Stars
                    star = math.sin(x * 23.1 + 0.1) * math.sin(y * 17.9 + 0.3)
                    if star > 0.92:
                        try:
                            stdscr.addstr(y, x, "*" if star > 0.96 else "\u00b7", soft_attr)
                        except curses.error:
                            pass
                    else:
                        try:
                            stdscr.addstr(y, x, " ", base_dim)
                        except curses.error:
                            pass
                else:
                    # Forest interior: dark, sparse texture
                    depth = (y - sil[x]) / max(1, h - sil[x])
                    noise = math.sin(x * 5.7 + y * 3.3) * 0.5 + 0.5
                    if depth < 0.15:
                        # Canopy line
                        ch = "|" if noise > 0.7 else ("Y" if noise > 0.55 else "^")
                        try:
                            stdscr.addstr(y, x, ch, soft_attr if noise > 0.6 else base_dim)
                        except curses.error:
                            pass
                    elif noise * (1 - depth) > 0.65:
                        try:
                            stdscr.addstr(y, x, "\u00b7", base_dim)
                        except curses.error:
                            pass
                    else:
                        try:
                            stdscr.addstr(y, x, " ", base_dim)
                        except curses.error:
                            pass

        # Firefly overlay
        for fly in self._flies:
            glow = max(0.0, math.sin(fly["phase"]))
            if glow > 0.55:
                fx, fy = int(fly["x"]), int(fly["y"])
                if 1 <= fy < h - 1 and 0 <= fx < w - 1 and fy >= sil[fx]:
                    try:
                        stdscr.addstr(fy, fx, "*" if glow > 0.85 else "\u00b7",
                                      bright_attr if glow > 0.85 else accent_attr)
                    except curses.error:
                        pass


    # ── v0.2: Emergent system ─────────────────────────────────────────────────

    def physarum_config(self):
        return {"n_agents": 180, "sensor_angle": 0.5, "sensor_dist": 3,
                "speed": 0.7, "deposit": 1.0, "decay": 0.95}

    def emergent_layer(self):
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────

    def glow_radius(self):
        return 1

    def echo_decay(self):
        return 6

    def decay_sequence(self):
        return "▓▒░·. "

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────

    def intensity_curve(self, raw):
        return raw ** 0.5

    # ── v0.2: Reactive system ─────────────────────────────────────────────────

    def react(self, event_kind, data):
        cx, cy = 0.5, 0.5
        rng = random
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.85,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "llm_start":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.8,
                            origin=(cx, cy), color_key="accent", duration=3.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.4,
                            origin=(rng.random(), rng.random()),
                            color_key="bright", duration=0.5)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.6,
                            origin=(rng.random(), rng.random()),
                            color_key="accent", duration=1.5)
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
        if event_kind == "dangerous_cmd":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.95,
                            origin=(rng.random(), rng.random()),
                            color_key="warning", duration=1.0)
        if event_kind == "file_edit":
            return Reaction(element=ReactiveElement.TRAIL, intensity=0.5,
                            origin=(0.0, rng.random()),
                            color_key="soft", duration=2.0)
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────

    def palette_shift(self, trigger_effect, intensity, base_palette):
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────

    def special_effects(self):
        return [SpecialEffect(name="forest-breath", trigger_kinds=["burst"],
                              min_intensity=0.3, cooldown=5.0, duration=2.0)]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        if special_name != "forest-breath":
            return
        # All fireflies flash simultaneously
        if self._flies is None:
            return
        w, h = state.width, state.height
        bright_attr = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        flash = math.sin(progress * math.pi)
        if flash > 0.3 and self._w > 0:
            sil = [self._silhouette(x, w, h) for x in range(min(w, self._w))]
            for fly in self._flies:
                fx, fy = int(fly["x"]), int(fly["y"])
                if (1 <= fy < h - 1 and 0 <= fx < w - 1
                        and fx < len(sil) and fy >= sil[fx]):
                    try:
                        stdscr.addstr(fy, fx, "*", bright_attr)
                    except curses.error:
                        pass

    # ── v0.2: Ambient tick ────────────────────────────────────────────────────

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        pass  # fireflies and forest textures animate continuously


register(DarkForestV2Plugin())


# ── Mountain Stars — Silhouette + Aurora ──────────────────────────────────────

class MountainStarsV2Plugin(ThemePlugin):
    """Mountain ridgeline with aurora curtains and a parallax star field."""
    name = "mountain-stars"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _ridgeline(self, x, w, h, offset=0.0):
        nx  = (x + offset) / max(w - 1, 1)
        alt = (0.62
               + 0.18 * math.sin(nx * math.pi * 2.0 + 0.5)
               + 0.10 * math.sin(nx * math.pi * 5.3 + 1.2)
               + 0.06 * math.sin(nx * math.pi * 11.0 + 2.4))
        return int(alt * h)

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        intensity = state.intensity_multiplier

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        # Parallax offsets for 3 ridgelines (near ridge moves faster)
        scroll = f * 0.15
        ridges = [
            (scroll * 0.05, soft_attr,   0.55),   # far
            (scroll * 0.12, accent_attr, 0.65),   # mid
            (scroll * 0.20, base_dim,    0.75),   # near (darkest)
        ]

        # Precompute ridgelines
        ridge_rows = [[self._ridgeline(x, w, h, off) for x in range(w)]
                      for off, _, _ in ridges]

        # Aurora bands
        aurora_base = int(h * 0.22)
        aurora_height = int(h * 0.18)
        t = f * 0.015

        for y in range(1, h - 1):
            # Find which ridgeline this y is under
            under_near = False
            for rr in ridge_rows:
                if y >= rr[min(w // 2, len(rr) - 1)]:
                    under_near = True
                    break

            for x in range(0, w - 1):
                near_row = ridge_rows[2][x]
                mid_row  = ridge_rows[1][x]
                far_row  = ridge_rows[0][x]

                if y >= near_row:
                    # Near mountain fill
                    try:
                        stdscr.addstr(y, x, "\u2588" if y == near_row else " ", base_dim)
                    except curses.error:
                        pass
                    continue

                if y >= mid_row:
                    # Mid ridge
                    ch   = "\u2584" if y == mid_row else " "
                    try:
                        stdscr.addstr(y, x, ch, ridges[1][1])
                    except curses.error:
                        pass
                    continue

                if y >= far_row:
                    # Far ridge
                    ch = "\u2580" if y == far_row else " "
                    try:
                        stdscr.addstr(y, x, ch, ridges[0][1])
                    except curses.error:
                        pass
                    continue

                # Sky: aurora + stars
                aurora_y = aurora_base + int(math.sin(x * 0.12 + t) * aurora_height * 0.4)
                aurora_dist = abs(y - aurora_y)

                if aurora_dist < aurora_height * 0.8 and intensity > 0.25:
                    wave = math.sin(x * 0.08 + t * 1.3) * 0.5 + 0.5
                    curtain = math.exp(-aurora_dist**2 / (aurora_height * 0.3)**2)
                    aurora_v = curtain * wave * intensity
                    if aurora_v > 0.12:
                        chars = " \u00b7:|\u2502\u2551"
                        idx   = int(aurora_v * (len(chars) - 1))
                        attr  = accent_attr if aurora_v > 0.5 else soft_attr
                        try:
                            stdscr.addstr(y, x, chars[max(0, min(len(chars)-1, idx))], attr)
                        except curses.error:
                            pass
                        continue

                # Stars (parallax via slight horizontal shift per row)
                star_x = (x + int(y * 0.05 * scroll)) % w
                star   = math.sin(star_x * 29.3 + y * 17.7) * math.cos(star_x * 7.1 + y * 11.3)
                if star > 0.88:
                    try:
                        stdscr.addstr(y, x, "*" if star > 0.94 else "\u00b7",
                                      bright_attr if star > 0.94 else soft_attr)
                    except curses.error:
                        pass
                else:
                    try:
                        stdscr.addstr(y, x, " ", base_dim)
                    except curses.error:
                        pass


    # ── v0.2: Emergent system ─────────────────────────────────────────────────

    def neural_field_config(self):
        return {"threshold": 3, "fire_duration": 2, "refractory": 8}

    def emergent_layer(self):
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────

    def glow_radius(self):
        return 1

    def echo_decay(self):
        return 6

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────

    def intensity_curve(self, raw):
        return raw ** 0.6

    # ── v0.2: Reactive system ─────────────────────────────────────────────────

    def react(self, event_kind, data):
        cx, cy = 0.5, 0.5
        rng = random
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.9,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "llm_start":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.8,
                            origin=(cx, cy), color_key="accent", duration=3.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.4,
                            origin=(rng.random(), rng.random()),
                            color_key="bright", duration=0.5)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.6,
                            origin=(rng.random(), rng.random()),
                            color_key="accent", duration=1.5)
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
        if event_kind == "cron_tick":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.5,
                            origin=(rng.random(), rng.random()),
                            color_key="soft", duration=2.0)
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────

    def palette_shift(self, trigger_effect, intensity, base_palette):
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────

    def special_effects(self):
        return [SpecialEffect(name="meteor-shower", trigger_kinds=["burst"],
                              min_intensity=0.3, cooldown=6.0, duration=3.0)]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        if special_name != "meteor-shower":
            return
        w, h = state.width, state.height
        bright_attr = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        soft_attr = curses.color_pair(color_pairs.get("soft", 0))
        # Streaks of light across sky
        f = state.frame
        for i in range(12):
            t = (progress * 2.5 + i * 0.25) % 1.0
            sx = int(w * (0.1 + (i * 0.07 % 0.8)))
            sy = int(h * 0.05 + h * 0.45 * t)
            # Draw a short diagonal streak
            for step in range(5):
                px = sx + step * 2
                py = sy + step
                if 1 <= py < h - 1 and 0 <= px < w - 1:
                    attr = bright_attr if step < 2 else soft_attr
                    try:
                        stdscr.addstr(py, px, "\\" if step < 2 else "·", attr)
                    except curses.error:
                        pass

    # ── v0.2: Ambient tick ────────────────────────────────────────────────────

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        pass  # star twinkling and aurora animate continuously via draw_extras


register(MountainStarsV2Plugin())


# ── Beach Lighthouse ──────────────────────────────────────────────────────────

class BeachLighthouseV2Plugin(ThemePlugin):
    """Rotating lighthouse beam sweeps night sky; ocean wave interference below."""
    name = "beach-lighthouse"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        intensity = state.intensity_multiplier

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        # Zones: sky top 55%, ocean next 20%, sand bottom 25%
        horizon = int(h * 0.55)
        sand    = int(h * 0.75)

        # Lighthouse on the right side of the beach, standing on sand
        lhx = int(w * 0.72)

        # Lantern sits high up in the sky — gives a tall visible tower
        lantern_y = max(2, int(h * 0.18))

        # Rotating beam — full sweep every ~12s (0.017 rad/frame at ~30fps)
        beam_angle = f * 0.017

        # Lantern flicker: on for 4 frames, off for 1 (mostly on)
        lantern_on = (f % 5) != 0

        for y in range(1, h - 1):
            for x in range(0, w - 1):

                # ── Lighthouse structure (drawn in priority over zone fills) ──

                # Lantern room cap: 1 row above lantern (tiny roof)
                if y == lantern_y - 1 and x == lhx:
                    try:
                        stdscr.addstr(y, x, "▲", accent_attr)
                    except curses.error:
                        pass
                    continue

                # Lantern room: 3 chars wide at lantern_y
                if y == lantern_y and abs(x - lhx) <= 1:
                    if x == lhx:
                        ch = "◉" if lantern_on else "○"
                        try:
                            stdscr.addstr(y, x, ch, bright_attr if lantern_on else soft_attr)
                        except curses.error:
                            pass
                    else:
                        try:
                            stdscr.addstr(y, x, "▐" if x < lhx else "▌", accent_attr)
                        except curses.error:
                            pass
                    continue

                # Lantern gallery (platform below lantern): 5 chars wide
                if y == lantern_y + 1 and abs(x - lhx) <= 2:
                    try:
                        stdscr.addstr(y, x, "─" if x != lhx else "┼", soft_attr)
                    except curses.error:
                        pass
                    continue

                # Tower body: single column from gallery down to sand line only
                if x == lhx and lantern_y + 2 <= y <= sand:
                    # Widen to 3 at the base (last 3 rows before sand)
                    if y >= sand - 2 and abs(x - lhx) <= 1:
                        pass  # handled below
                    try:
                        stdscr.addstr(y, x, "┃", accent_attr)
                    except curses.error:
                        pass
                    continue

                # Tower base: 3 wide for the bottom 3 rows before sand
                if sand - 3 <= y <= sand and abs(x - lhx) == 1:
                    try:
                        stdscr.addstr(y, x, "▌" if x < lhx else "▐", accent_attr)
                    except curses.error:
                        pass
                    continue

                # ── Sky ───────────────────────────────────────────────────────
                if y < horizon:
                    # Deterministic stars from hash function
                    star_v = math.sin(x * 31.1 + y * 19.3) * math.cos(x * 7.9 + y * 13.7)

                    # Rotating beam — only cast into sky, only when lantern on
                    if lantern_on:
                        dx_b = x - lhx
                        dy_b = y - lantern_y   # negative: sky rows are above lantern
                        dist = math.sqrt(dx_b * dx_b / 2.0 + dy_b * dy_b)
                        if dist > 1.0:
                            cell_angle = math.atan2(-dy_b, dx_b)
                            angle_diff = abs((cell_angle - beam_angle + math.pi) % (2 * math.pi) - math.pi)
                            # Cone: narrow at distance, wider near source
                            beam_width = max(0.04, 0.18 - dist * 0.001)
                            beam_fade  = max(0.0, 1.0 - dist / (max(w, h) * 0.80)) * intensity
                            if angle_diff < beam_width and beam_fade > 0.03:
                                chars_b = "·.:\u2591\u2592\u2593"
                                idx = max(0, min(len(chars_b) - 1, int(beam_fade * (len(chars_b) - 1))))
                                try:
                                    stdscr.addstr(y, x, chars_b[idx],
                                                  bright_attr if beam_fade > 0.5 else soft_attr)
                                except curses.error:
                                    pass
                                continue

                    # Moon: upper-left corner (opposite side from lighthouse)
                    moon_x = int(w * 0.18)
                    moon_y = int(h * 0.10)
                    mdx = x - moon_x
                    mdy = y - moon_y
                    moon_dist = math.sqrt(mdx * mdx / 2.0 + mdy * mdy)
                    if moon_dist < 1.2:
                        try:
                            stdscr.addstr(y, x, "○", bright_attr)
                        except curses.error:
                            pass
                        continue
                    elif moon_dist < 5.0:
                        glow = 1.0 - moon_dist / 5.0
                        try:
                            stdscr.addstr(y, x, "·" if glow > 0.35 else " ", soft_attr)
                        except curses.error:
                            pass
                        continue

                    # Stars
                    if star_v > 0.88:
                        try:
                            stdscr.addstr(y, x, "*" if star_v > 0.94 else "·", soft_attr)
                        except curses.error:
                            pass
                    else:
                        try:
                            stdscr.addstr(y, x, " ", base_dim)
                        except curses.error:
                            pass

                # ── Ocean ─────────────────────────────────────────────────────
                elif y < sand:
                    t = f * 0.05
                    w1 = math.sin(x * 0.22 - t * 0.9  + y * 0.10)
                    w2 = math.sin(x * 0.35 + t * 0.60 - y * 0.07)
                    w3 = math.sin(x * 0.15 - t * 0.40 + 1.2)
                    wave = (w1 * 0.45 + w2 * 0.35 + w3 * 0.20) * (0.5 + 0.5 * intensity)
                    depth = (y - horizon) / max(1, sand - horizon)

                    # Moon reflection: column near moon_x
                    moon_refl = max(0.0, 1.0 - abs(x - int(w * 0.18)) / max(1, w * 0.12))
                    moon_refl *= max(0.0, 1.0 - depth * 1.5)

                    # Beam reflection: where beam hits the water
                    beam_col = lhx + int(math.cos(beam_angle) * (y - lantern_y) * 0.5)
                    beam_refl = max(0.0, 1.0 - abs(x - beam_col) / max(3, w * 0.04)) if lantern_on else 0.0
                    beam_refl *= max(0.0, 1.0 - depth) * 0.7

                    effective = wave + moon_refl * 0.4 + beam_refl

                    if effective > 0.55 and depth < 0.4:
                        ch = "~" if effective < 0.8 else "^"
                        try:
                            stdscr.addstr(y, x, ch,
                                          bright_attr if effective > 0.8 else accent_attr)
                        except curses.error:
                            pass
                    elif effective > 0.15:
                        chars_w = " ·.~≈"
                        wv  = (effective + 1.0) * 0.5
                        idx = int(wv * (1.0 - depth * 0.5) * (len(chars_w) - 1))
                        try:
                            stdscr.addstr(y, x, chars_w[max(0, min(len(chars_w) - 1, idx))],
                                          soft_attr if wv > 0.55 else base_dim)
                        except curses.error:
                            pass
                    else:
                        try:
                            stdscr.addstr(y, x, " ", base_dim)
                        except curses.error:
                            pass

                # ── Sand ──────────────────────────────────────────────────────
                else:
                    noise = math.sin(x * 11.7 + y * 8.3) * 0.5 + 0.5
                    wet   = max(0.0, 1.0 - (y - sand) / max(1, h - sand - 1))
                    chars_s = ".,·:`"
                    idx = int(noise * (len(chars_s) - 1))
                    try:
                        stdscr.addstr(y, x, chars_s[idx],
                                      soft_attr if (noise > 0.55 or wet > 0.5) else base_dim)
                    except curses.error:
                        pass


    # ── v0.2: Emergent system ─────────────────────────────────────────────────

    def wave_config(self):
        return {"speed": 0.4, "damping": 0.97}

    def emergent_layer(self):
        return "background"

    # ── v0.2: Post-FX ─────────────────────────────────────────────────────────

    def glow_radius(self):
        return 2

    def echo_decay(self):
        return 3

    def warp_field(self, x, y, w, h, frame, intensity):
        """Lighthouse beam distortion — radial displacement in beam path."""
        lhx = int(w * 0.72)
        lantern_y = max(2, int(h * 0.18))
        beam_angle = frame * 0.017
        dx = x - lhx
        dy = y - lantern_y
        dist = math.sqrt(dx * dx / 2.0 + dy * dy) + 0.001
        cell_angle = math.atan2(-dy, dx)
        angle_diff = abs((cell_angle - beam_angle + math.pi) % (2 * math.pi) - math.pi)
        if angle_diff < 0.2 and dist > 2.0:
            # Radial displacement in beam direction
            amp = intensity * 1.5 * max(0.0, 1.0 - angle_diff / 0.2)
            nx = max(0, min(w - 1, x + int(amp * dx / dist)))
            ny = max(0, min(h - 1, y + int(amp * dy / dist * 0.5)))
            return (nx, ny)
        return (x, y)

    # ── v0.2: Intensity curve ─────────────────────────────────────────────────

    def intensity_curve(self, raw):
        return raw ** 0.7

    # ── v0.2: Reactive system ─────────────────────────────────────────────────

    def react(self, event_kind, data):
        cx, cy = 0.5, 0.5
        rng = random
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=0.9,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "llm_start":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.8,
                            origin=(cx, cy), color_key="accent", duration=3.5)
        if event_kind == "llm_chunk":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.4,
                            origin=(rng.random(), rng.random()),
                            color_key="bright", duration=0.5)
        if event_kind == "tool_call":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.6,
                            origin=(rng.random(), rng.random()),
                            color_key="accent", duration=1.5)
        if event_kind == "memory_save":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.75,
                            origin=(cx, cy), color_key="bright", duration=2.5)
        if event_kind == "error":
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                            origin=(rng.random(), rng.random()),
                            color_key="warning", duration=2.0)
        if event_kind == "browser_navigate":
            return Reaction(element=ReactiveElement.TRAIL, intensity=0.55,
                            origin=(0.0, rng.random()),
                            color_key="accent", duration=2.0)
        if event_kind == "approval_request":
            return Reaction(element=ReactiveElement.SPARK, intensity=0.9,
                            origin=(cx, cy), color_key="warning", duration=1.5)
        return None

    # ── v0.2: Palette shift ───────────────────────────────────────────────────

    def palette_shift(self, trigger_effect, intensity, base_palette):
        return None

    # ── v0.2: Special effects ─────────────────────────────────────────────────

    def special_effects(self):
        return [SpecialEffect(name="sos-signal", trigger_kinds=["burst"],
                              min_intensity=0.3, cooldown=6.0, duration=3.0)]

    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
        if special_name != "sos-signal":
            return
        w, h = state.width, state.height
        bright_attr = curses.color_pair(color_pairs.get("bright", 0)) | curses.A_BOLD
        warning_attr = curses.color_pair(color_pairs.get("warning", 0)) | curses.A_BOLD
        # Morse code SOS flash: ... --- ...
        # Flash whole lighthouse column in pattern
        lhx = int(w * 0.72)
        # SOS pattern: 9 symbols, timing
        sos = [1, 1, 1, 0, 2, 2, 2, 0, 1, 1, 1]  # 1=short, 2=long, 0=gap
        t = int(progress * len(sos))
        symbol = sos[min(t, len(sos) - 1)]
        if symbol > 0:
            for y in range(1, h - 1):
                try:
                    stdscr.addstr(y, lhx, "*", bright_attr if symbol == 1 else warning_attr)
                except curses.error:
                    pass

    # ── v0.2: Ambient tick ────────────────────────────────────────────────────

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        pass  # waves and beam sweep continuously via draw_extras


register(BeachLighthouseV2Plugin())
