"""Redesigned nature themes using full-screen ASCII field engine.

Themes: deep-abyss, storm-sea, dark-forest, mountain-stars, beach-lighthouse
"""

from __future__ import annotations

import curses
import math
import random
from typing import List, Optional

from hermes_neurovision.plugin import ThemePlugin
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

        # Zones — sky takes top 45%, ocean next 30%, sand bottom 25%
        horizon = int(h * 0.45)
        sand    = int(h * 0.75)

        # Lighthouse: centred horizontally, cap sits at the ocean/sand boundary
        lhx = w // 2
        # Lantern room (rotating light source) — sits 2 rows above sand line
        lantern_y = sand - 2
        # Tower body: from lantern down to the bottom row
        tower_top = lantern_y + 1   # first tower body row

        # Rotating beam — full sweep every ~10s
        beam_angle = f * 0.020  # radians per frame

        # Lantern flicker: bright every other 3-frame window
        lantern_on = (f // 3) % 2 == 0

        for y in range(1, h - 1):
            for x in range(0, w - 1):

                # ── Lighthouse structure ──────────────────────────────────────
                # Lantern room: row = lantern_y, 3 chars wide
                if y == lantern_y and abs(x - lhx) <= 1:
                    if x == lhx:
                        # Core of the lantern — bright when on, dim when off
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

                # Lantern room platform (1 row below lantern)
                if y == lantern_y + 1 and abs(x - lhx) <= 2:
                    try:
                        stdscr.addstr(y, x, "─" if x != lhx else "┼", soft_attr)
                    except curses.error:
                        pass
                    continue

                # Tower body: single column from tower_top+1 to bottom
                if x == lhx and y > lantern_y + 1:
                    try:
                        stdscr.addstr(y, x, "┃", accent_attr)
                    except curses.error:
                        pass
                    continue

                # ── Sky ───────────────────────────────────────────────────────
                if y < horizon:
                    # Deterministic stars
                    star = math.sin(x * 31.1 + y * 19.3) * math.cos(x * 7.9 + y * 13.7)
                    star_bright = star > 0.88

                    # Beam: only when lantern is on
                    if lantern_on:
                        dx_b  = x - lhx
                        dy_b  = y - lantern_y  # negative (sky is above lantern)
                        dist  = math.sqrt(dx_b * dx_b + dy_b * dy_b)
                        if dist > 0.5:
                            # cell_angle: 0=right, pi/2=up, pi=left
                            cell_angle = math.atan2(-dy_b, dx_b)
                            angle_diff = abs((cell_angle - beam_angle + math.pi) % (2 * math.pi) - math.pi)
                            # Beam width narrows with distance (cone effect)
                            beam_width = max(0.03, 0.14 - dist * 0.0008)
                            beam_fade  = max(0.0, 1.0 - dist / (max(w, h) * 0.75)) * intensity
                            if angle_diff < beam_width and beam_fade > 0.04:
                                chars = "·.:\u2591\u2592\u2593"
                                idx   = int(beam_fade * (len(chars) - 1))
                                idx   = max(0, min(len(chars) - 1, idx))
                                try:
                                    stdscr.addstr(y, x, chars[idx],
                                                  bright_attr if beam_fade > 0.55 else soft_attr)
                                except curses.error:
                                    pass
                                continue

                    # Moon glow: upper-right corner, soft halo
                    moon_x = int(w * 0.78)
                    moon_y = int(h * 0.10)
                    mdx = x - moon_x
                    mdy = y - moon_y
                    moon_dist = math.sqrt(mdx * mdx + mdy * mdy * 2.0)
                    if moon_dist < 1.5:
                        try:
                            stdscr.addstr(y, x, "○" if moon_dist < 0.7 else "·", bright_attr)
                        except curses.error:
                            pass
                    elif moon_dist < 4.5:
                        glow_v = 1.0 - moon_dist / 4.5
                        try:
                            stdscr.addstr(y, x, "·" if glow_v > 0.4 else " ", soft_attr)
                        except curses.error:
                            pass
                    elif star_bright:
                        try:
                            stdscr.addstr(y, x, "*" if star > 0.94 else "·", soft_attr)
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
                    w1 = math.sin(x * 0.22 - t * 0.9 + y * 0.10)
                    w2 = math.sin(x * 0.35 + t * 0.60 - y * 0.07)
                    w3 = math.sin(x * 0.15 - t * 0.40 + 1.2)
                    wave = (w1 * 0.45 + w2 * 0.35 + w3 * 0.20) * (0.5 + 0.5 * intensity)

                    depth = (y - horizon) / max(1, sand - horizon)

                    # Moon reflection on water: column near moon_x
                    moon_refl = max(0.0, 1.0 - abs(x - int(w * 0.78)) / (w * 0.12))
                    moon_refl *= max(0.0, 1.0 - depth * 1.5)

                    # Beam reflection on ocean: column near current beam direction
                    beam_col = lhx + int(math.cos(beam_angle) * (h - y) * 0.5)
                    beam_refl = max(0.0, 1.0 - abs(x - beam_col) / max(3, w * 0.04)) if lantern_on else 0.0
                    beam_refl *= max(0.0, 1.0 - depth) * 0.6

                    effective = wave + moon_refl * 0.4 + beam_refl

                    if effective > 0.55 and depth < 0.35:
                        ch = "~" if effective < 0.8 else "^"
                        try:
                            stdscr.addstr(y, x, ch,
                                          bright_attr if effective > 0.8 else accent_attr)
                        except curses.error:
                            pass
                    elif effective > 0.2:
                        wv    = (effective + 1.0) * 0.5
                        chars = " ·.~≈"
                        idx   = int(wv * (1.0 - depth * 0.5) * (len(chars) - 1))
                        try:
                            stdscr.addstr(y, x, chars[max(0, min(len(chars) - 1, idx))],
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
                    # Wet sand near ocean edge
                    wet = max(0.0, 1.0 - (y - sand) / max(1, h - sand - 1))
                    chars = ".,·:`"
                    idx   = int(noise * (len(chars) - 1))
                    try:
                        stdscr.addstr(y, x, chars[idx],
                                      soft_attr if (noise > 0.55 or wet > 0.5) else base_dim)
                    except curses.error:
                        pass


register(BeachLighthouseV2Plugin())
