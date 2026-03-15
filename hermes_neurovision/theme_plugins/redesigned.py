"""Redesigned themes 37-42 + 3 extreme new screens using full-screen ASCII field engine."""

from __future__ import annotations

import curses
import math
import random
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


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
    """Periodic explosion cycle — implosion, shockwave, nebula, fade."""
    name = "supernova"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        intensity = state.intensity_multiplier

        cx = w / 2.0
        cy = h / 2.0
        phase = f % 600

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
                    # Nebula expansion — colors sweep by angle + time
                    t = (phase - 350) / 200.0
                    nebula_v = max(0.0, (1 - dist_n * (0.8 + t * 0.4)) * abs(math.sin(dist_n * 15 + f * 0.03)) * 0.8) * intensity
                    if nebula_v > 0.05:
                        dense_chars = " ·.:+*"
                        ci = int(nebula_v * (len(dense_chars) - 1))
                        ch = dense_chars[ci]
                        # Angle-based color sweeping over time — sector rotates
                        angle = math.atan2(dy, dx)
                        sector = int((angle + math.pi + f * 0.015) / (math.pi / 3)) % 3
                        if sector == 0:
                            attr = soft_attr
                        elif sector == 1:
                            attr = accent_attr
                        else:
                            attr = bright_attr if nebula_v > 0.45 else accent_attr

                else:
                    # Fade — remnant wisps drift outward
                    t = (phase - 550) / 50.0
                    angle = math.atan2(dy, dx)
                    v = max(0.0, math.sin(x * 0.5 + y * 0.4 + f * 0.025 + angle) * 0.35 * (1 - t)) * intensity
                    if v > 0.08:
                        ch = "·" if v < 0.2 else ":"
                        sector = int((angle + math.pi + f * 0.01) / (math.pi / 2)) % 2
                        attr = soft_attr if sector == 0 else accent_attr

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


# ── Sol v2: Solar plasma with convection cells ────────────────────────────────

class SolV2Plugin(ThemePlugin):
    """Solar plasma surface with Voronoi convection cells and limb darkening."""
    name = "sol"

    def __init__(self):
        self._cells = None
        self._w = 0
        self._h = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

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


# ── Binary Star v2: Two orbiting stars with gravitational field ───────────────

class BinaryStarV2Plugin(ThemePlugin):
    """Two orbiting stars with equipotential gravitational field visualization."""
    name = "binary-star"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        intensity = state.intensity_multiplier

        period = 120
        angle = f * (2 * math.pi / period)
        sep = min(w, h) * 0.22
        cx = w / 2.0
        cy = h / 2.0

        s1x = cx + math.cos(angle) * sep
        s1y = cy + math.sin(angle) * sep * 0.45
        s2x = cx - math.cos(angle) * sep
        s2y = cy - math.sin(angle) * sep * 0.45

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr = curses.color_pair(color_pairs["soft"])
        base_dim_attr = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        potential_chars = " \u00b7.:;+=*#"

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                r1 = math.sqrt((x - s1x) ** 2 / 2.25 + (y - s1y) ** 2)
                r2 = math.sqrt((x - s2x) ** 2 / 2.25 + (y - s2y) ** 2)
                V = -(1.0 / (r1 + 0.5) + 1.0 / (r2 + 0.5)) * 3.0
                v = max(0.0, min(1.0, (-V - 0.5) / 3.0)) * intensity

                if abs(r1 - r2) < 0.8:
                    ch = "\u2500"
                    attr = accent_attr
                else:
                    ci = int(v * (len(potential_chars) - 1))
                    ch = potential_chars[ci]
                    if v > 0.8:
                        attr = bright_attr
                    elif v > 0.5:
                        attr = accent_attr
                    elif v > 0.3:
                        attr = soft_attr
                    else:
                        attr = base_dim_attr

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

        # Draw star bodies
        for sx, sy in [(s1x, s1y), (s2x, s2y)]:
            sxi = int(sx)
            syi = int(sy)
            if 1 <= syi <= h - 2 and 0 <= sxi <= w - 2:
                try:
                    stdscr.addstr(syi, sxi, "\u2605", bright_attr)
                except curses.error:
                    pass

        # Trailing light from 3 and 6 frames ago
        for lag in (3, 6):
            past_angle = f * (2 * math.pi / period) - lag * (2 * math.pi / period)
            p1x = int(cx + math.cos(past_angle) * sep)
            p1y = int(cy + math.sin(past_angle) * sep * 0.45)
            p2x = int(cx - math.cos(past_angle) * sep)
            p2y = int(cy - math.sin(past_angle) * sep * 0.45)
            for px, py in [(p1x, p1y), (p2x, p2y)]:
                if 1 <= py <= h - 2 and 0 <= px <= w - 2:
                    try:
                        stdscr.addstr(py, px, "\u00b7", base_dim_attr)
                    except curses.error:
                        pass


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
