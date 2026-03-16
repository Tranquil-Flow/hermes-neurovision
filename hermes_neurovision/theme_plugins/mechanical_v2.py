"""Mechanical V2 theme plugins — full-screen ASCII engine redesigns.

Themes: clockwork (epicycloid gear chain)
"""

from __future__ import annotations

import curses
import math
from typing import List, Optional, Tuple

from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register


def _safe(stdscr, y: int, x: int, ch: str, attr: int = 0) -> None:
    """Draw character safely, ignoring curses boundary errors."""
    try:
        stdscr.addstr(y, x, ch, attr)
    except curses.error:
        pass


# ── Clockwork V2: Epicycloid gear chain ───────────────────────────────────────

class ClockworkV2Plugin(ThemePlugin):
    """Epicycloid gear chain animation.

    5–7 meshing gears of varying radius. Angular velocity is inversely
    proportional to tooth count (conservation of meshing). The output shaft
    of the outermost gear traces an epicycloid curve which accumulates as a
    fading density trail.

    Colors: yellow/white gears on dark background (canonical steampunk palette).
    """

    name = "clockwork"

    # Gear definitions: (rel_radius, offset_angle_from_center)
    # Gear 0 is the drive gear at center. Subsequent gears are arranged so
    # their pitch circles are tangent to the previous gear.
    _GEAR_DEFS = [
        {"r_norm": 0.22, "teeth": 22},  # drive gear — largest
        {"r_norm": 0.13, "teeth": 13},  # meshed right
        {"r_norm": 0.09, "teeth":  9},  # meshed to #1, upper-right
        {"r_norm": 0.13, "teeth": 13},  # meshed left of drive
        {"r_norm": 0.07, "teeth":  7},  # meshed to #3, upper-left
        {"r_norm": 0.09, "teeth":  9},  # idler below drive
    ]
    _ARM_LENGTH_NORM = 0.10  # arm on outermost gear (relative to screen height)
    _TRAIL_MAX = 600          # how many epicycloid trail points to keep
    _TRAIL_CHARS = " ·∙•◦○◎"   # fading trail characters (least → most dense)

    def __init__(self):
        self._trail: list[tuple[int, int]] = []
        self._gear_centers: list[tuple[float, float]] = []
        self._initialized = False

    # ── Geometry helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _draw_circle(stdscr, cy: float, cx: float, ry: float, rx: float,
                     char: str, attr: int, w: int, h: int) -> None:
        """Draw an ellipse outline (y-radius ry, x-radius rx) using ASCII."""
        # Sample enough points for smooth outline
        steps = max(16, int(math.pi * (rx + ry)))
        for i in range(steps):
            a = math.tau * i / steps
            sx = int(cx + rx * math.cos(a))
            sy = int(cy + ry * math.sin(a))
            if 1 <= sy <= h - 2 and 0 <= sx <= w - 2:
                _safe(stdscr, sy, sx, char, attr)

    @staticmethod
    def _draw_teeth(stdscr, cy: float, cx: float, ry: float, rx: float,
                    teeth: int, angle_offset: float,
                    char: str, attr: int, w: int, h: int) -> None:
        """Draw gear teeth as radial spokes protruding beyond gear rim."""
        tooth_length_y = max(1.5, ry * 0.18)
        tooth_length_x = max(1.5, rx * 0.18)
        for i in range(teeth):
            a = math.tau * i / teeth + angle_offset
            ca, sa = math.cos(a), math.sin(a)
            # Inner point (on rim)
            ix = cx + rx * ca
            iy = cy + ry * sa
            # Outer point (tooth tip)
            ox = cx + (rx + tooth_length_x) * ca
            oy = cy + (ry + tooth_length_y) * sa
            # Draw short line along the tooth
            steps = max(2, int(math.hypot(ox - ix, oy - iy)) + 1)
            for s in range(steps + 1):
                t = s / max(1, steps)
                tx = int(ix + t * (ox - ix))
                ty = int(iy + t * (oy - iy))
                if 1 <= ty <= h - 2 and 0 <= tx <= w - 2:
                    _safe(stdscr, ty, tx, char, attr)

    @staticmethod
    def _draw_spoke(stdscr, cy: float, cx: float, angle: float,
                    ry: float, rx: float, char: str, attr: int,
                    w: int, h: int) -> None:
        """Draw a single radial spoke (hub line) for the output arm."""
        ex = cx + rx * math.cos(angle)
        ey = cy + ry * math.sin(angle)
        steps = max(2, int(math.hypot(ex - cx, ey - cy)) + 1)
        for s in range(steps + 1):
            t = s / max(1, steps)
            tx = int(cx + t * (ex - cx))
            ty = int(cy + t * (ey - cy))
            if 1 <= ty <= h - 2 and 0 <= tx <= w - 2:
                _safe(stdscr, ty, tx, char, attr)

    # ── Gear layout (computed once per screen size) ────────────────────────────

    def _init_gears(self, w: int, h: int) -> list[dict]:
        """Compute gear centres from the gear defs, placing them tangentially.

        Gear 0 is at screen centre. Each subsequent gear sits to the right of
        the previous one with pitch circles tangent, then wrapped around in a
        rough ring to avoid collision.
        """
        cx, cy = w / 2.0, h / 2.0
        # Convert normalised radii → pixel radii (use height as reference)
        scale = h * 0.55  # scale so drive gear fills ~55% of half-height
        gears = []
        for i, gd in enumerate(self._GEAR_DEFS):
            g = {
                "r_px": gd["r_norm"] * scale,        # pixel radius (y)
                "r_px_x": gd["r_norm"] * scale * 0.50, # x-radius (terminal cells are ~2:1)
                "teeth": gd["teeth"],
                # Angular velocity: ω ∝ 1/r (teeth meshing rule)
                # Drive gear (#0) has ω=1.0; signs alternate for meshing
                "omega": 0.0,
                "cx": 0.0,
                "cy": 0.0,
            }
            gears.append(g)

        # Place gear 0 at centre
        gears[0]["cx"] = cx
        gears[0]["cy"] = cy
        gears[0]["omega"] = 1.0

        # Angular velocity sign: adjacent gears rotate opposite directions
        # Gear arrangement: mesh in a ring around the drive gear
        placement_angles = [0, math.pi / 6, math.pi * 5 / 6, math.pi,
                            math.pi * 7 / 6, math.pi * 11 / 6]

        for i in range(1, len(gears)):
            pa = placement_angles[i - 1]
            prev_idx = 0  # all outer gears mesh with drive gear for simplicity
            dist = (gears[prev_idx]["r_px"] + gears[i]["r_px"]) * 1.05
            # Use an asymmetric distance because x/y pixel ratio ~0.5
            dist_x = dist * 0.50
            dist_y = dist
            gears[i]["cx"] = gears[prev_idx]["cx"] + dist_x * math.cos(pa)
            gears[i]["cy"] = gears[prev_idx]["cy"] + dist_y * math.sin(pa)
            # Teeth meshing: ω_i = -ω_prev * r_prev / r_i
            sign = -1 if i % 2 == 1 else 1
            gears[i]["omega"] = sign * (gears[prev_idx]["r_px"] / gears[i]["r_px"])

        self._gear_centers = [(g["cx"], g["cy"]) for g in gears]
        return gears

    # ── Plugin interface ───────────────────────────────────────────────────────

    def build_nodes(self, w, h, cx, cy, count, rng):
        """No particle graph — we render everything in draw_extras."""
        return []

    def draw_extras(self, stdscr, state, color_pairs) -> None:
        """Draw the full gear assembly and epicycloid trail each frame."""
        w = state.width
        h = state.height
        f = state.frame
        intensity = state.intensity_multiplier

        # Re-initialise if screen size changed or first frame
        if not self._initialized or len(self._gear_centers) != len(self._GEAR_DEFS):
            self._gears = self._init_gears(w, h)
            self._trail = []
            self._initialized = True
            self._last_w = w
            self._last_h = h
        elif w != self._last_w or h != self._last_h:
            self._gears = self._init_gears(w, h)
            self._trail = []
            self._last_w = w
            self._last_h = h

        gears = self._gears

        # Base rotation speed (frames are ~20fps)
        base_speed = 0.025 + 0.015 * intensity

        # Current rotation angle for each gear
        angles = [g["omega"] * f * base_speed for g in gears]

        # ── Colour attributes ────────────────────────────────────────────────
        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_attr   = curses.color_pair(color_pairs["base"]) | curses.A_DIM

        # ── Draw epicycloid trail ────────────────────────────────────────────
        # The output arm sits on gear index 1 (first outer gear)
        arm_gear_idx = 1
        ag = gears[arm_gear_idx]
        arm_angle = angles[arm_gear_idx] + math.pi * 0.5
        arm_len_y = self._ARM_LENGTH_NORM * h
        arm_len_x = arm_len_y * 0.50  # x-correction for terminal aspect ratio
        tip_x = int(ag["cx"] + arm_len_x * math.cos(arm_angle))
        tip_y = int(ag["cy"] + arm_len_y * math.sin(arm_angle))

        # Add new trail point
        self._trail.append((tip_x, tip_y))
        if len(self._trail) > self._TRAIL_MAX:
            self._trail = self._trail[-self._TRAIL_MAX:]

        # Draw trail — older = dimmer
        n_trail = len(self._trail)
        n_chars = len(self._TRAIL_CHARS)
        for ti, (tx, ty) in enumerate(self._trail):
            if not (1 <= ty <= h - 2 and 0 <= tx <= w - 2):
                continue
            age_frac = ti / max(1, n_trail - 1)  # 0 = oldest, 1 = newest
            char_idx = int(age_frac * (n_chars - 1))
            ch = self._TRAIL_CHARS[char_idx]
            if age_frac > 0.85:
                attr = accent_attr
            elif age_frac > 0.5:
                attr = soft_attr
            else:
                attr = base_attr
            _safe(stdscr, ty, tx, ch, attr)

        # ── Draw each gear ────────────────────────────────────────────────────
        for i, g in enumerate(gears):
            gx, gy = g["cx"], g["cy"]
            ry = g["r_px"]
            rx = g["r_px_x"]
            teeth = g["teeth"]
            angle = angles[i]

            # Gear rim
            rim_attr = bright_attr if i == 0 else accent_attr
            self._draw_circle(stdscr, gy, gx, ry, rx, "◯", soft_attr, w, h)

            # Gear teeth
            tooth_char = "│" if abs(math.sin(angle)) > 0.5 else "─"
            self._draw_teeth(stdscr, gy, gx, ry, rx, teeth, angle,
                             tooth_char, rim_attr, w, h)

            # Hub dot
            hub_y, hub_x = int(gy), int(gx)
            if 1 <= hub_y <= h - 2 and 0 <= hub_x <= w - 2:
                _safe(stdscr, hub_y, hub_x, "⊙", bright_attr)

            # Cross-spokes for drive gear
            if i == 0:
                for spoke_angle in [angle, angle + math.pi / 2,
                                    angle + math.pi, angle + math.pi * 3 / 2]:
                    self._draw_spoke(stdscr, gy, gx, spoke_angle,
                                     ry * 0.80, rx * 0.80,
                                     "·", soft_attr, w, h)

        # ── Draw output arm ───────────────────────────────────────────────────
        self._draw_spoke(stdscr, ag["cy"], ag["cx"], arm_angle,
                         arm_len_y * 0.99, arm_len_x * 0.99,
                         "─", accent_attr, w, h)
        # Arm tip marker
        if 1 <= tip_y <= h - 2 and 0 <= tip_x <= w - 2:
            _safe(stdscr, tip_y, tip_x, "★", bright_attr)


register(ClockworkV2Plugin())
