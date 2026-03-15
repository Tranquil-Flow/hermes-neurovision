"""ASCII field theme plugins — 10 full-screen generative visual screens."""

from __future__ import annotations

import curses
import math
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


# ---------------------------------------------------------------------------
# Shared color helper — phase-shifted so colors sweep dynamically over time
# ---------------------------------------------------------------------------

def _hue_attr(v: float, phase: float, cp: dict) -> int:
    """Map value v to a curses attr through a time/space rotating phase.

    phase is 0..1 and shifts which color tier v lands in, so the same pixel
    cycles through all palette colors as phase evolves — making colors move
    rather than sitting frozen at fixed intensity thresholds.
    """
    s = (v + phase) % 1.0
    if s > 0.72:
        return curses.color_pair(cp.get("bright", 1)) | curses.A_BOLD
    elif s > 0.48:
        return curses.color_pair(cp.get("accent", 1))
    elif s > 0.24:
        return curses.color_pair(cp.get("soft", 1))
    return curses.color_pair(cp.get("base", 1)) | curses.A_DIM


# ── Screen 1: Synaptic Plasma ─────────────────────────────────────────────────

class SynapticPlasmaPlugin(ThemePlugin):
    """Full-screen plasma interference pattern."""
    name = "synaptic-plasma"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        chars = " ·.:;+=*#%@"
        n = len(chars) - 1
        cx2 = w / 2.0
        cy2 = h / 2.0
        intensity = state.intensity_multiplier
        # global hue rotation: one full cycle every ~300 frames
        hue_base = (f * 0.0033) % 1.0

        for y in range(1, h - 1):
            dy = y - cy2
            for x in range(0, w - 1):
                dx = x - cx2
                dist = math.sqrt((dx * dx) / 2.0 + dy * dy)
                v = (
                    math.sin(x * 0.15 + f * 0.08)
                    + math.sin(y * 0.22 - f * 0.06)
                    + math.sin((x + y) * 0.10 + f * 0.04)
                    + math.sin(dist * 2.5 - f * 0.12)
                ) / 4.0
                v = (v + 1.0) / 2.0 * intensity
                v = max(0.0, min(1.0, v))
                ci = int(v * n)
                ch = chars[ci]
                # phase varies per-pixel: dist drives spatial rainbow bands
                phase = (hue_base + dist * 0.04) % 1.0
                attr = _hue_attr(v, phase, color_pairs)
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


# ── Screen 2: Oracle ──────────────────────────────────────────────────────────

class OraclePlugin(ThemePlugin):
    """Rotating vortex tunnel."""
    name = "oracle"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        chars = " ·.:oO@◎⊕"
        n = len(chars) - 1
        hw = w / 2.0
        hh = h / 2.0
        intensity = state.intensity_multiplier
        # hue spirals outward from center — different phase direction from Plasma
        hue_base = (f * 0.004) % 1.0

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                nx = (x - hw) / max(hw, 1.0)
                ny = (y - hh) / max(hh, 1.0)
                dist = math.sqrt(nx * nx + ny * ny * 2.0)
                angle = math.atan2(ny, nx)
                twist = 4.5 + 2.0 * math.sin(f * 0.007)
                vortex = math.sin(dist * 8.0 + angle * twist - f * 0.09)
                tunnel = math.sin(1.0 / (dist * 1.2 + 0.06) * 8.0 - f * 0.18)
                v = max(0.0, min(1.0, (vortex * 0.6 + tunnel * 0.4 + 1.0) / 2.0))
                glow = max(0.0, 1.0 - dist * 3.0)
                v = min(1.0, v + glow * 0.4)
                v *= intensity
                ci = int(v * n)
                ch = chars[ci]
                # phase rotates with angle + dist so colors swirl outward
                phase = (hue_base + angle / (2 * math.pi) + dist * 0.06) % 1.0
                attr = _hue_attr(v, phase, color_pairs)
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

        # Bright center pip
        try:
            stdscr.addstr(
                h // 2, w // 2, "◎",
                curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
            )
        except curses.error:
            pass


# ── Screen 3: Cellular Cortex ─────────────────────────────────────────────────

class CellularCortexPlugin(ThemePlugin):
    """Voronoi cells representing 6 agent modules."""
    name = "cellular-cortex"

    _MODULES = [
        ("memory",  0.18, 0.30, "∿"),
        ("model",   0.50, 0.22, "☿"),
        ("tools",   0.82, 0.30, "⚙"),
        ("cron",    0.22, 0.75, "⏱"),
        ("core",    0.50, 0.55, "◎"),
        ("aegis",   0.78, 0.75, "⚡"),
    ]

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        mods = self._MODULES

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                nx = x / max(w, 1)
                ny = y / max(h, 1)

                # Find nearest and second nearest module
                dists = []
                for i, (name, mx, my, icon) in enumerate(mods):
                    ddx = (nx - mx) * 1.5  # anisotropy for terminal aspect
                    ddy = ny - my
                    dists.append((ddx * ddx + ddy * ddy, i))
                dists.sort()
                d1, i1 = dists[0]
                d2, i2 = dists[1]
                edge_dist = math.sqrt(d2) - math.sqrt(d1)

                if edge_dist < 0.025:
                    # Border cell — color drifts with frame + cell-pair index
                    pulse = abs(math.sin(f * 0.08 + i1 * 0.7))
                    border_chars = "│─╱╲┼"
                    bci = (i1 + i2) % len(border_chars)
                    ch = border_chars[bci]
                    phase = (f * 0.005 + (i1 + i2) * 0.17) % 1.0
                    attr = _hue_attr(pulse, phase, color_pairs)
                else:
                    # Interior — ripple color rotates per cell index over time
                    name, mx, my, icon = mods[i1]
                    d_center = math.sqrt(d1)
                    ripple = (math.sin(d_center * 20.0 - f * 0.05) + 1.0) / 2.0
                    if ripple > 0.25:
                        ch = "·"
                        phase = (f * 0.004 + i1 * 0.16 + d_center * 0.1) % 1.0
                        attr = _hue_attr(ripple, phase, color_pairs)
                    else:
                        ch = " "
                        attr = curses.color_pair(color_pairs.get("base", 1)) | curses.A_DIM

                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

        # Draw module icons + names at center positions
        for i, (name, mx, my, icon) in enumerate(mods):
            pulse = 0.4 + 0.6 * abs(math.sin(f * 0.06 + i * 0.7))
            ax = int(mx * w)
            ay = int(my * h)
            if ay < 1:
                ay = 1
            if ay > h - 2:
                ay = h - 2
            ax = max(0, min(ax, w - 2))
            label = icon + name
            if pulse > 0.6:
                attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
            else:
                attr = curses.color_pair(color_pairs["accent"])
            try:
                stdscr.addstr(ay, ax, label, attr)
            except curses.error:
                pass


# ── Screen 4: Reaction Field ──────────────────────────────────────────────────

class ReactionFieldPlugin(ThemePlugin):
    """Gray-Scott reaction-diffusion simulation."""
    name = "reaction-field"

    def __init__(self):
        self._u = None
        self._v = None
        self._sw = 0
        self._sh = 0
        self._w = 0
        self._h = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init_grid(self, sw, sh, rng):
        size = sw * sh
        self._u = [1.0] * size
        self._v = [0.0] * size
        # Seed 8 patches of 4x4 with v=0.25
        for _ in range(8):
            px = rng.randint(2, max(3, sw - 6))
            py = rng.randint(2, max(3, sh - 6))
            for dy in range(4):
                for dx in range(4):
                    idx = (py + dy) * sw + (px + dx)
                    if 0 <= idx < size:
                        self._u[idx] = 0.5
                        self._v[idx] = 0.25
        self._sw = sw
        self._sh = sh

    def _step(self, sw, sh):
        F, k, Du, Dv = 0.037, 0.060, 0.16, 0.08
        u = self._u
        v = self._v
        new_u = u[:]
        new_v = v[:]
        for cy in range(sh):
            for cx in range(sw):
                idx = cy * sw + cx
                # 4-neighbor laplacian (periodic)
                left  = cy * sw + (cx - 1) % sw
                right = cy * sw + (cx + 1) % sw
                up    = ((cy - 1) % sh) * sw + cx
                down  = ((cy + 1) % sh) * sw + cx
                lu = u[left] + u[right] + u[up] + u[down] - 4.0 * u[idx]
                lv = v[left] + v[right] + v[up] + v[down] - 4.0 * v[idx]
                uvv = u[idx] * v[idx] * v[idx]
                new_u[idx] = max(0.0, min(1.0, u[idx] + Du * lu - uvv + F * (1.0 - u[idx])))
                new_v[idx] = max(0.0, min(1.0, v[idx] + Dv * lv + uvv - (F + k) * v[idx]))
        self._u = new_u
        self._v = new_v

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        sw = max(10, w // 3)
        sh = max(5, h // 3)

        if self._u is None or w != self._w or h != self._h:
            self._init_grid(sw, sh, state.rng)
            self._w = w
            self._h = h

        # Step simulation 2 times
        self._step(sw, sh)
        self._step(sw, sh)

        chars = " ·.:+*#█"
        n = len(chars) - 1
        v_arr = self._v
        # hue travels across x axis — creates crawling horizontal color bands
        hue_base = (state.frame * 0.003) % 1.0

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                sx = x * sw // max(w, 1)
                sy = y * sh // max(h, 1)
                sx = max(0, min(sx, sw - 1))
                sy = max(0, min(sy, sh - 1))
                val = v_arr[sy * sw + sx]
                ci = int(val * n)
                ch = chars[ci]
                # phase wanders with x position — bands scroll left/right
                phase = (hue_base + x / max(w, 1) * 0.8 + y / max(h, 1) * 0.2) % 1.0
                attr = _hue_attr(val, phase, color_pairs)
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


# ── Screen 5: Stellar Weave ───────────────────────────────────────────────────

class StellarWeavePlugin(ThemePlugin):
    """Drifting named stars forming constellations."""
    name = "stellar-weave"

    _NAMES = [
        "rust lifetimes", "async patterns", "memory design", "hooks system",
        "tool patterns", "agent lifecycle", "project structure", "type safety",
        "error handling", "concurrency",
    ]

    def __init__(self):
        self._stars = None

    def build_nodes(self, w, h, cx, cy, count, rng):
        return None  # Use default — but draw_extras will overlay

    def _init_stars(self, w, h, rng):
        stars = []
        for i, name in enumerate(self._NAMES):
            x = rng.uniform(8.0, max(9.0, w - 12.0))
            y = rng.uniform(3.0, max(4.0, h - 4.0))
            phase = rng.uniform(0.0, math.tau)
            stars.append({"name": name, "x": x, "y": y, "phase": phase})
        self._stars = stars

    def draw_extras(self, stdscr, state, color_pairs):
        import curses as _curses
        w = state.width
        h = state.height
        f = state.frame

        if self._stars is None:
            self._init_stars(w, h, state.rng)

        stars = self._stars

        # Drift stars
        for s in stars:
            drift_x = math.sin(f * 0.002 + s["phase"]) * 0.15
            drift_y = math.cos(f * 0.002 + s["phase"] * 1.3) * 0.08
            s["x"] = max(3.0, min(float(w - 14), s["x"] + drift_x))
            s["y"] = max(2.0, min(float(h - 3), s["y"] + drift_y))

        # Draw K=2 nearest-neighbor edges between stars
        n = len(stars)
        base_attr = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        for i, s1 in enumerate(stars):
            # Find 2 nearest
            dists = []
            for j, s2 in enumerate(stars):
                if i != j:
                    dx = s2["x"] - s1["x"]
                    dy = s2["y"] - s1["y"]
                    dists.append((dx * dx + dy * dy, j))
            dists.sort()
            for _, j in dists[:2]:
                s2 = stars[j]
                x1, y1 = int(s1["x"]), int(s1["y"])
                x2, y2 = int(s2["x"]), int(s2["y"])
                # Bresenham line
                dx = abs(x2 - x1)
                dy = abs(y2 - y1)
                sx = 1 if x1 < x2 else -1
                sy = 1 if y1 < y2 else -1
                err = dx - dy
                cx2, cy2 = x1, y1
                steps = 0
                while steps < 200:
                    if 1 <= cy2 <= h - 2 and 0 <= cx2 <= w - 2:
                        ddx = x2 - x1
                        ddy = y2 - y1
                        if abs(ddx) > abs(ddy):
                            ch = "─"
                        elif abs(ddy) > abs(ddx):
                            ch = "│"
                        else:
                            ch = "╱" if (ddx > 0) != (ddy > 0) else "╲"
                        try:
                            stdscr.addstr(cy2, cx2, ch, base_attr)
                        except curses.error:
                            pass
                    if cx2 == x2 and cy2 == y2:
                        break
                    e2 = 2 * err
                    if e2 > -dy:
                        err -= dy
                        cx2 += sx
                    if e2 < dx:
                        err += dx
                        cy2 += sy
                    steps += 1

        # Draw session core at center with pulse ring
        core_x = w // 2
        core_y = h // 2
        ring_r = int(2.0 + 1.5 * abs(math.sin(f * 0.08)))
        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        soft_attr = curses.color_pair(color_pairs["soft"])
        for angle_deg in range(0, 360, 15):
            angle = math.radians(angle_deg)
            rx = core_x + int(ring_r * 2.0 * math.cos(angle))
            ry = core_y + int(ring_r * math.sin(angle))
            if 1 <= ry <= h - 2 and 0 <= rx <= w - 2:
                try:
                    stdscr.addstr(ry, rx, "·", soft_attr)
                except curses.error:
                    pass
        try:
            stdscr.addstr(core_y, core_x, "◎", bright_attr)
        except curses.error:
            pass

        # Draw stars
        for s in stars:
            sx = int(s["x"])
            sy = int(s["y"])
            if 1 <= sy <= h - 2 and 0 <= sx <= w - 2:
                try:
                    stdscr.addstr(sy, sx, "✦", bright_attr)
                except curses.error:
                    pass
                label = '"' + s["name"] + '"'
                lx = sx + 2
                if lx + len(label) < w - 1:
                    try:
                        stdscr.addstr(sy, lx, label, soft_attr)
                    except curses.error:
                        pass


# ── Screen 6: Life Colony ─────────────────────────────────────────────────────

class LifeColonyPlugin(ThemePlugin):
    """Conway's Game of Life."""
    name = "life-colony"

    def __init__(self):
        self._grid = None
        self._w = 0
        self._h = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _init_grid(self, w, h, rng, density=0.30):
        self._w = w
        self._h = h
        size = w * h
        g = bytearray(size)
        for i in range(size):
            if rng.random() < density:
                g[i] = 1
        self._grid = g

    def _count_neighbors(self, g, x, y, w, h):
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % w
                ny = (y + dy) % h
                if g[ny * w + nx]:
                    count += 1
        return count

    def _step(self, w, h):
        g = self._grid
        new_g = bytearray(w * h)
        for y in range(h):
            for x in range(w):
                n = self._count_neighbors(g, x, y, w, h)
                alive = g[y * w + x]
                if alive:
                    new_g[y * w + x] = 1 if n in (2, 3) else 0
                else:
                    new_g[y * w + x] = 1 if n == 3 else 0
        self._grid = new_g

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        # Use a slightly smaller grid to avoid edge issues
        gw = max(4, w - 1)
        gh = max(4, h - 2)

        if self._grid is None or w != self._w or h != self._h:
            self._init_grid(gw, gh, state.rng)
            self._w = w
            self._h = h

        # Check population and reseed if too low
        alive_count = sum(self._grid)
        total = gw * gh
        if state.frame % 500 == 0 and total > 0 and alive_count / total < 0.03:
            self._init_grid(gw, gh, state.rng, density=0.30)

        # Step every frame
        self._step(gw, gh)

        g = self._grid
        chars = "·:+*#@◈"
        bright_attr = curses.color_pair(color_pairs["bright"])
        soft_attr = curses.color_pair(color_pairs["soft"])
        base_attr = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        for y in range(1, h - 1):
            gy = y - 1
            if gy >= gh:
                continue
            for x in range(0, w - 1):
                gx = x
                if gx >= gw:
                    continue
                cell = g[gy * gw + gx]
                if cell:
                    n = self._count_neighbors(g, gx, gy, gw, gh)
                    ch = chars[min(n, len(chars) - 1)]
                    if (x + y) % 2 == 0:
                        attr = bright_attr
                    else:
                        attr = soft_attr
                else:
                    ch = " "
                    attr = base_attr
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


# ── Screen 7: Aurora Bands ────────────────────────────────────────────────────

class AuroraBandsPlugin(ThemePlugin):
    """5 undulating horizontal aurora bands."""
    name = "aurora-bands"

    # (center_y_ratio, hue_key, freq, amplitude, speed, label)
    _BANDS = [
        (0.18, "soft",    0.8, 0.10, 0.07, "tools"),
        (0.35, "accent",  1.1, 0.08, 0.10, "memory"),
        (0.52, "bright",  0.6, 0.12, 0.05, "core"),
        (0.67, "soft",    0.9, 0.09, 0.08, "cron"),
        (0.82, "warning", 1.3, 0.07, 0.12, "aegis"),
    ]

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        intensity = state.intensity_multiplier
        bands = self._BANDS

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                max_v = 0.0
                winning_key = "base"
                winning_band = 0
                for bi, (cy_r, hue_key, freq, amplitude, speed, label) in enumerate(bands):
                    center_y = cy_r * h + amplitude * h * math.sin(x * freq + f * speed)
                    dist = abs(y - center_y)
                    thickness = 1.5 + 0.5 * math.sin(f * 0.04 + bi)
                    v = max(0.0, 1.0 - dist / max(thickness, 0.01))
                    if v > max_v:
                        max_v = v
                        winning_key = hue_key
                        winning_band = bi

                max_v *= intensity
                # phase shifts per-band at its own speed, creating independent
                # color migration along each aurora ribbon
                band_phase = (f * bands[winning_band][4] * 0.5
                              + winning_band * 0.2
                              + x / max(w, 1) * 0.3) % 1.0
                if max_v > 0.8:
                    ch = "█"
                elif max_v > 0.6:
                    ch = "▓"
                elif max_v > 0.4:
                    ch = "▒"
                elif max_v > 0.2:
                    ch = "░"
                else:
                    ch = " "
                if ch == " ":
                    attr = curses.color_pair(color_pairs.get("base", 1)) | curses.A_DIM
                else:
                    attr = _hue_attr(max_v, band_phase, color_pairs)
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

        # Draw band labels at right edge
        for bi, (cy_r, hue_key, freq, amplitude, speed, label) in enumerate(bands):
            center_y = int(cy_r * h)
            if 1 <= center_y <= h - 2:
                lx = max(0, w - 8)
                try:
                    stdscr.addstr(
                        center_y, lx, label[:6],
                        curses.color_pair(color_pairs[hue_key]) | curses.A_BOLD
                    )
                except curses.error:
                    pass


# ── Screen 8: Waveform Scope ──────────────────────────────────────────────────

class WaveformScopePlugin(ThemePlugin):
    """Oscilloscope display with 5 channels."""
    name = "waveform-scope"

    # (y_ratio, color_key, label)
    _CHANNELS = [
        (0.15, "soft",   "TOOLS"),
        (0.30, "accent", "MEMORY"),
        (0.47, "bright", "CRON"),
        (0.63, "soft",   "AEGIS"),
        (0.79, "accent", "DOCKER"),
    ]

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def _wave(self, ch_idx, x_norm, f):
        """Compute waveform value for channel."""
        if ch_idx == 0:
            return math.sin(x_norm * 4.0 + f * 0.10) * 0.6 + math.sin(x_norm * 7.0 + f * 0.15) * 0.3
        elif ch_idx == 1:
            return math.sin(x_norm * 2.0 + f * 0.04) * (0.4 + 0.3 * math.sin(f * 0.025))
        elif ch_idx == 2:
            return 0.6 if math.sin(x_norm * 5.0 + f * 0.05) > 0 else -0.2
        elif ch_idx == 3:
            return 0.1 * math.sin(x_norm * 20.0 + f * 0.25) + 0.05
        else:  # 4 - DOCKER
            return math.sin(x_norm * 3.0 + f * 0.08) * 0.5 * max(0.0, math.sin(f * 0.015))

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        channels = self._CHANNELS

        # Draw grid
        grid_attr = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        for gy in range(1, h - 1, max(1, h // 6)):
            for gx in range(0, w - 1, max(1, w // 8)):
                try:
                    stdscr.addstr(gy, gx, "·", grid_attr)
                except curses.error:
                    pass

        # Draw channels
        for ci, (y_ratio, color_key, label) in enumerate(channels):
            center_y = y_ratio * h
            # Draw waveform — color drifts along x driven by wave phase
            for x in range(0, w - 1):
                x_norm = x * 8.0 / max(w, 1)
                vy = self._wave(ci, x_norm, f)
                py = int(round(center_y - vy * h * 0.07))
                if 1 <= py <= h - 2:
                    ch = "═" if abs(vy) < 0.02 else "─"
                    # phase: each channel's hue flows rightward at its own speed
                    phase = (f * 0.003 * (ci + 1) + x / max(w, 1) + ci * 0.2) % 1.0
                    v = (abs(vy) + 0.1)
                    attr = _hue_attr(v, phase, color_pairs)
                    if abs(vy) < 0.02:
                        attr |= curses.A_BOLD
                    try:
                        stdscr.addstr(py, x, ch, attr)
                    except curses.error:
                        pass
            # Draw label in the channel's nominal color (stable reference)
            label_y = max(1, int(center_y) - 1)
            if label_y < 1:
                label_y = 1
            if label_y > h - 2:
                label_y = h - 2
            label_attr = curses.color_pair(color_pairs.get(color_key, 1)) | curses.A_BOLD
            try:
                stdscr.addstr(label_y, 2, label, label_attr)
            except curses.error:
                pass

        # Scanning cursor
        cursor_x = (f // 3) % max(1, w - 1)
        cursor_attr = curses.color_pair(color_pairs["accent"]) | curses.A_DIM
        for cy in range(1, h - 1):
            try:
                stdscr.addstr(cy, cursor_x, "│", cursor_attr)
            except curses.error:
                pass


# ── Screen 9: Lissajous Mind ──────────────────────────────────────────────────

class LissajousMindPlugin(ThemePlugin):
    """Lissajous figure trace with fading trail."""
    name = "lissajous-mind"

    def __init__(self):
        self._trail = []

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        intensity = state.intensity_multiplier

        fx_freq = 2.0 + 0.5 * math.sin(f * 0.0035)
        fy_freq = 3.0 + 0.5 * math.sin(f * 0.0055)
        phi = f * 0.02
        phase = f * 0.0015

        sx = 0.5 + 0.42 * math.sin(fx_freq * phase + phi)
        sy = 0.5 + 0.42 * math.sin(fy_freq * phase)
        px = int(sx * (w - 2)) + 1
        py = int(sy * (h - 2)) + 1
        px = max(1, min(px, w - 2))
        py = max(1, min(py, h - 2))
        self._trail.append((px, py))
        if len(self._trail) > 300:
            self._trail.pop(0)

        trail_len = len(self._trail)
        bright_attr = curses.color_pair(color_pairs.get("bright", 1)) | curses.A_BOLD
        # hue races around the trail loop — one full revolution every ~200 frames
        hue_base = (f * 0.005) % 1.0

        for i, (tx, ty) in enumerate(self._trail):
            age_ratio = i / max(trail_len, 1)
            # Skip old points if low intensity
            if intensity < 0.5 and age_ratio < 0.3:
                continue
            if 1 <= ty <= h - 2 and 1 <= tx <= w - 2:
                if age_ratio < 0.3:
                    ch = "·"
                elif age_ratio < 0.6:
                    ch = ":"
                elif age_ratio < 0.8:
                    ch = "+"
                elif age_ratio < 0.95:
                    ch = "*"
                else:
                    ch = "◈"
                # phase marches along the trail length — colors chase the head
                phase = (hue_base + age_ratio * 0.6) % 1.0
                attr = _hue_attr(age_ratio, phase, color_pairs)
                try:
                    stdscr.addstr(ty, tx, ch, attr)
                except curses.error:
                    pass

        # Bright current tip
        if self._trail:
            htx, hty = self._trail[-1]
            if 1 <= hty <= h - 2 and 1 <= htx <= w - 2:
                try:
                    stdscr.addstr(hty, htx, "◈", bright_attr)
                except curses.error:
                    pass

        # Show current frequencies in bottom-right
        info = f"fx:{fx_freq:.2f} fy:{fy_freq:.2f}"
        info_x = max(0, w - len(info) - 2)
        if h - 2 >= 1:
            try:
                stdscr.addstr(h - 2, info_x, info,
                              curses.color_pair(color_pairs["soft"]) | curses.A_DIM)
            except curses.error:
                pass


# ── Screen 10: Pulse Matrix ───────────────────────────────────────────────────

class PulseMatrixPlugin(ThemePlugin):
    """Full-screen compound interference dot matrix."""
    name = "pulse-matrix"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w = state.width
        h = state.height
        f = state.frame
        intensity = state.intensity_multiplier
        chars = "·.:;+*#@●"
        n = len(chars) - 1
        cx2 = w / 2.0
        cy2 = h / 2.0

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                dx = (x - cx2) / max(cx2, 1.0)
                dy = (y - cy2) / max(cy2, 1.0)
                dist = math.sqrt(dx * dx + dy * dy)
                angle = math.atan2(dy, dx)
                w1 = math.sin(dist * 12.0 - f * 0.12)
                w2 = math.sin(dx * 8.0 + f * 0.065)
                w3 = math.sin(dy * 10.0 - f * 0.09)
                w4 = math.sin((dx + dy) * 7.0 + angle * 3.0 - f * 0.10)
                v = (w1 * 0.4 + w2 * 0.25 + w3 * 0.2 + w4 * 0.15 + 1.0) / 2.0
                v = max(0.0, min(1.0, v)) * intensity
                ci = int(v * n)
                ch = chars[ci]
                # phase uses angle so colors rotate around the center ring by ring
                hue_base = (f * 0.0035) % 1.0
                phase = (hue_base + angle / (2 * math.pi) + dist * 0.05) % 1.0
                attr = _hue_attr(v, phase, color_pairs)
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass


# ── Registration ──────────────────────────────────────────────────────────────

register(SynapticPlasmaPlugin())
register(OraclePlugin())
register(CellularCortexPlugin())
register(ReactionFieldPlugin())
register(StellarWeavePlugin())
register(LifeColonyPlugin())
register(AuroraBandsPlugin())
register(WaveformScopePlugin())
register(LissajousMindPlugin())
register(PulseMatrixPlugin())
