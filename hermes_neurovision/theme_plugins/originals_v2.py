"""Redesigned original themes using full-screen ASCII field engine.

Themes: black-hole, neural-sky, storm-core, moonwire, rootsong, stormglass, spiral-galaxy
All use draw_extras() for per-cell rendering; build_nodes() returns [] to suppress graph.
"""

from __future__ import annotations

import curses
import math
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


# ── Black Hole ─────────────────────────────────────────────────────────────────

class BlackHoleV2Plugin(ThemePlugin):
    """Relativistic black hole: event horizon, photon sphere, accretion disk, jets, lensed stars."""
    name = "black-hole"

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        cx, cy = w / 2.0, h / 2.0
        intensity = state.intensity_multiplier

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"]) | curses.A_BOLD
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_attr   = curses.color_pair(color_pairs["base"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        warn_attr   = curses.color_pair(color_pairs["warning"]) | curses.A_BOLD

        rs = min(w * 0.07, h * 0.14)   # Schwarzschild radius
        ay = 2.1                         # terminal cell aspect ratio

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                dx = x - cx
                dy = (y - cy) * ay
                r  = math.sqrt(dx * dx + dy * dy)
                theta = math.atan2(dy, dx)

                # Event horizon
                if r < rs:
                    try:
                        stdscr.addstr(y, x, "\u2588", base_dim)
                    except curses.error:
                        pass
                    continue

                # Photon sphere glowing ring
                if abs(r - rs * 1.5) < rs * 0.35:
                    glow = 1.0 - abs(r - rs * 1.5) / (rs * 0.35)
                    ch = "\u2593" if glow > 0.65 else "\u2592"
                    try:
                        stdscr.addstr(y, x, ch, warn_attr if glow > 0.65 else accent_attr)
                    except curses.error:
                        pass
                    continue

                # Relativistic jets (vertical bands above/below)
                jet_hw = rs * 0.45
                if abs(dx) < jet_hw and r > rs * 1.1:
                    frac = 1.0 - abs(dx) / jet_hw
                    wave = math.sin(r * 0.35 - f * 0.18) * 0.5 + 0.5
                    v = frac * wave * intensity
                    if v > 0.25:
                        ch = "\u2502\u2551\u2503|!"[int(v * 4.9)]
                        try:
                            stdscr.addstr(y, x, ch, bright_attr if v > 0.6 else accent_attr)
                        except curses.error:
                            pass
                        continue

                # Accretion disk (thin torus seen at ~15° inclination)
                # Disk plane: we see it foreshortened — sin(theta) measures out-of-plane
                in_disk = abs(math.sin(theta)) < 0.18
                if rs * 1.8 <= r <= rs * 6.5 and in_disk:
                    # Doppler: left side = approaching (bright), right = receding (dim)
                    doppler     = math.cos(theta - f * 0.007)
                    radial_fade = 1.0 - (r - rs * 1.8) / (rs * 4.7)
                    density     = radial_fade * (0.5 + 0.5 * doppler) * intensity
                    chars = " .:+*#@"
                    idx = max(1, min(len(chars) - 1, int(density * (len(chars) - 1))))
                    ch  = chars[idx]
                    attr = warn_attr if doppler > 0.4 else (accent_attr if density > 0.4 else soft_attr)
                    try:
                        stdscr.addstr(y, x, ch, attr)
                    except curses.error:
                        pass
                    continue

                # Gravitational lensing of background stars
                lens_angle = theta + (rs * rs) / (r * r + 0.1) * 0.4
                star_hash  = math.sin(lens_angle * 19.3) * math.cos(r * 0.07 + lens_angle * 7.1)
                if star_hash > 0.88:
                    bright = (star_hash - 0.88) / 0.12
                    try:
                        stdscr.addstr(y, x, "*" if bright > 0.6 else "\u00b7",
                                      bright_attr if bright > 0.6 else soft_attr)
                    except curses.error:
                        pass
                else:
                    try:
                        stdscr.addstr(y, x, " ", base_dim)
                    except curses.error:
                        pass


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
    """Lorenz strange attractor: chaotic butterfly orbit accumulated as ASCII density field."""
    name = "storm-core"

    _SIGMA = 10.0
    _RHO   = 28.0
    _BETA  = 8.0 / 3.0
    _DT    = 0.008
    _N_TRAJ = 4  # parallel trajectories

    def __init__(self):
        self._grid: Optional[List[List[float]]] = None
        self._trajs: Optional[List[List[float]]] = None
        self._w = self._h = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

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

        # Lorenz attractor spans: x ∈ [-25,25], z ∈ [0,50]
        # Map: sx = (x+25)/50 * w,  sy = (1 - z/50) * (h-2) + 1
        steps_per_frame = int(120 * (0.5 + intensity))
        s, r, b = self._SIGMA, self._RHO, self._BETA

        for traj in self._trajs:
            x, y, z = traj
            for _ in range(steps_per_frame):
                dx = s * (y - x)
                dy = x * (r - z) - y
                dz = x * y - b * z
                x += dx * self._DT
                y += dy * self._DT
                z += dz * self._DT
                sx = int((x + 25) / 50.0 * (w - 2))
                sy = int((1.0 - z / 50.0) * (h - 2)) + 1
                if 1 <= sy < h - 1 and 0 <= sx < w - 1:
                    grid[sy][sx] = min(grid[sy][sx] + 0.08, 1.0)
            traj[0], traj[1], traj[2] = x, y, z

        # Decay all cells
        decay = 0.988 - 0.006 * intensity
        chars  = " \u00b7.:;+=*#@"
        n_chars = len(chars)

        for y in range(1, h - 1):
            row = grid[y]
            for x in range(0, w - 1):
                v = row[x]
                row[x] = v * decay
                idx = int(v * (n_chars - 1))
                idx = max(0, min(n_chars - 1, idx))
                ch  = chars[idx]
                if v < 0.1:
                    attr = base_dim
                elif v < 0.4:
                    attr = soft_attr
                elif v < 0.75:
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
