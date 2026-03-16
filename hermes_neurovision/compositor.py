"""Fade compositor — blends VT text over neurovision scene.

Supports position-based, age-based, and combined fade modes.
Text can have configurable background opacity, glow (with color and intensity), and color override.
"""

from __future__ import annotations

import curses
from dataclasses import dataclass


# Map text_bg convenience names to opacity values
_BG_PRESETS = {
    "transparent": 0.0,
    "dim": 0.3,
    "solid": 1.0,
}

# Color name → (color_pair_key, force_bold)
_COLOR_MAP = {
    "white":   ("bright", False),
    "green":   ("base", False),
    "cyan":    ("soft", False),
    "magenta": ("accent", False),
    "yellow":  ("warning", False),
    "red":     ("warning", True),
    "theme":   ("bright", False),
}

# ANSI fg code (0-7) → nearest neurovision color pair key
# Note: "text" is a fixed white pair that's never theme-swapped
_ANSI_TO_PAIR = {
    0: "text",      # black → use text (white) since black-on-dark is invisible
    1: "warning",   # red
    2: "base",      # green
    3: "warning",   # yellow
    4: "soft",      # blue
    5: "accent",    # magenta
    6: "soft",      # cyan
    7: "text",      # white/default → use fixed white "text" pair
}


@dataclass
class FadeConfig:
    """Configuration for the text fade overlay."""
    mode: str = "position"          # "position", "age", "both"
    fade_start_pct: float = 0.0     # row % where fade begins (0.0 = top)
    fade_end_pct: float = 0.4       # row % where text is fully opaque
    text_opacity: float = 1.0       # global text brightness 0.0-1.0
    text_bg: str = "dim"            # convenience alias: "transparent", "dim", "solid"
    text_bg_opacity: float = 0.3    # 0.0=transparent, 1.0=solid (default: 30% for readability)
    text_glow: bool = False         # enable glow effect on text
    text_glow_color: str = "theme"  # glow color: "theme", "white", "green", "cyan", "magenta", "yellow", "red"
    text_glow_intensity: float = 1.0  # glow intensity 0.0-1.0 (scales brightness)
    text_color: str = "native"      # "native" (terminal default), "auto" (map ANSI→pairs),
                                    # or override: "white", "green", "cyan", "magenta", "yellow", "red", "theme"
    fade_lifetime: int = 1200       # frames for full age-based fade (60 seconds at 20fps)

    def __post_init__(self) -> None:
        pass  # text_bg_opacity is set directly by CLI; no auto-derivation needed


class FadeCompositor:
    """Composites VT terminal text over a rendered scene with fade effects."""

    def __init__(self, config: FadeConfig) -> None:
        self.config = config

    def compute_opacity(self, row: int, total_rows: int,
                        born_frame: int = 0, current_frame: int = 0) -> float:
        """Compute text opacity for a given row. Returns 0.0–1.0."""
        cfg = self.config

        if cfg.mode == "position" or cfg.mode == "both":
            fade_start = total_rows * cfg.fade_start_pct
            fade_end = total_rows * cfg.fade_end_pct
            denom = max(fade_end - fade_start, 1.0)
            pos_opacity = max(0.0, min(1.0, (row - fade_start) / denom))
        else:
            pos_opacity = 1.0

        if cfg.mode == "age" or cfg.mode == "both":
            if cfg.fade_lifetime > 0:
                age = current_frame - born_frame
                age_opacity = max(0.0, 1.0 - age / cfg.fade_lifetime)
            else:
                age_opacity = 1.0
        else:
            age_opacity = 1.0

        if cfg.mode == "both":
            opacity = pos_opacity * age_opacity
        elif cfg.mode == "age":
            opacity = age_opacity
        else:
            opacity = pos_opacity

        return max(0.0, min(1.0, opacity * cfg.text_opacity))

    def opacity_to_curses_attr(self, opacity: float) -> int | None:
        """Map opacity to a curses attribute. Returns None if text should be hidden."""
        if opacity < 0.15:
            return None  # hidden
        elif opacity < 0.4:
            return curses.A_DIM
        elif opacity < 0.7:
            return curses.A_NORMAL
        else:
            return curses.A_BOLD

    def resolve_color_pair(self, vt_fg: int, vt_bold: bool,
                           color_pairs: dict) -> tuple[int, int]:
        """Resolve the curses color pair and extra attributes for a VT cell.

        Returns (color_pair_number, extra_attr).
        """
        cfg = self.config
        extra_attr = 0

        if cfg.text_glow:
            # Glow: use glow_color with bold, intensity modulates via attr
            glow_key = _COLOR_MAP.get(cfg.text_glow_color, ("bright", False))[0]
            if cfg.text_glow_intensity >= 0.7:
                extra_attr |= curses.A_BOLD
            elif cfg.text_glow_intensity < 0.3:
                extra_attr |= curses.A_DIM
            return color_pairs.get(glow_key, 1), extra_attr
        elif cfg.text_color == "native":
            # Use ANSI passthrough pairs (7-14) — maps VT fg color directly
            # to a fixed curses pair that matches the ANSI color.
            # This preserves colored prompts, ls output, etc.
            ansi_key = f"ansi_{vt_fg}"
            pair_num = color_pairs.get(ansi_key, color_pairs.get("ansi_7", 14))
            if vt_bold:
                extra_attr |= curses.A_BOLD
            return pair_num, extra_attr
        elif cfg.text_color == "auto":
            # Map ANSI color to nearest neurovision pair
            pair_key = _ANSI_TO_PAIR.get(vt_fg, "text")
            if vt_bold:
                extra_attr |= curses.A_BOLD
                if vt_fg != 7:
                    pair_key = "bright"
            return color_pairs.get(pair_key, 1), extra_attr
        else:
            # Explicit color override
            if cfg.text_color in _COLOR_MAP:
                pair_key, force_bold = _COLOR_MAP[cfg.text_color]
                if force_bold:
                    extra_attr |= curses.A_BOLD
            else:
                pair_key = "bright"
            return color_pairs.get(pair_key, 1), extra_attr

    def composite(self, stdscr, vt_screen, color_pairs: dict,
                  current_frame: int = 0, status_row: int = -1) -> None:
        """Overlay VT text onto the already-rendered scene on stdscr.

        The scene has already been drawn to stdscr by Renderer.draw(skip_refresh=True).
        This overwrites cells where VT text should be visible.
        """
        h, w = stdscr.getmaxyx()
        if status_row < 0:
            status_row = h - 1

        cfg = self.config

        for y in range(min(vt_screen.rows, h)):
            if y == status_row:
                continue

            for x in range(min(vt_screen.cols, w)):
                vt_cell = vt_screen.cells[y][x]

                # Skip empty VT cells (let scene show through)
                if vt_cell.char == " " and cfg.text_bg_opacity < 0.5:
                    continue

                opacity = self.compute_opacity(
                    y, h, vt_cell.born_frame, current_frame
                )

                attr = self.opacity_to_curses_attr(opacity)
                if attr is None:
                    continue  # hidden — scene shows through

                # Handle space cells with high bg opacity
                if vt_cell.char == " ":
                    if cfg.text_bg_opacity >= 0.5:
                        try:
                            stdscr.addstr(y, x, " ",
                                         curses.color_pair(color_pairs.get("base", 1)) | curses.A_DIM)
                        except curses.error:
                            pass
                    continue

                # Resolve color
                pair_num, extra_attr = self.resolve_color_pair(
                    vt_cell.fg, vt_cell.bold, color_pairs
                )

                # Write text character over the scene
                try:
                    stdscr.addstr(y, x, vt_cell.char,
                                 curses.color_pair(pair_num) | attr | extra_attr)
                except curses.error:
                    pass

        # Draw cursor (block via A_REVERSE)
        cy, cx = vt_screen.cursor_row, vt_screen.cursor_col
        if 0 <= cy < h and cy != status_row and 0 <= cx < w:
            opacity = self.compute_opacity(cy, h, 0, current_frame)
            if opacity >= 0.15:
                try:
                    cursor_char = vt_screen.cells[cy][cx].char if cx < vt_screen.cols else " "
                    pair_num = color_pairs.get("bright", 1)
                    stdscr.addstr(cy, cx, cursor_char,
                                 curses.color_pair(pair_num) | curses.A_REVERSE)
                except curses.error:
                    pass
