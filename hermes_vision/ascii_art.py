"""ASCII art drawing helper for Hermes Vision theme plugins."""

from __future__ import annotations

import curses
from dataclasses import dataclass
from typing import List


@dataclass
class AsciiArt:
    """Multi-line ASCII art with screen-safe drawing."""

    lines: List[str]

    @property
    def width(self) -> int:
        return max((len(line) for line in self.lines), default=0)

    @property
    def height(self) -> int:
        return len(self.lines)

    def draw(self, stdscr, x: int, y: int, color_pair: int,
             attr: int = 0, anchor: str = "center") -> None:
        """Draw art on screen with clipping.

        anchor: "center", "topleft", "bottomleft"
        """
        h, w = stdscr.getmaxyx()
        art_w = self.width
        art_h = self.height

        if anchor == "center":
            x -= art_w // 2
            y -= art_h // 2
        elif anchor == "bottomleft":
            y -= art_h

        combined = curses.color_pair(color_pair) | attr

        for row_idx, line in enumerate(self.lines):
            sy = y + row_idx
            if sy < 0 or sy >= h:
                continue
            for col_idx, ch in enumerate(line):
                if ch == " ":
                    continue
                sx = x + col_idx
                if sx < 0 or sx >= w:
                    continue
                # Avoid writing to bottom-right corner
                if sy == h - 1 and sx == w - 1:
                    continue
                try:
                    stdscr.addstr(sy, sx, ch, combined)
                except curses.error:
                    pass


# ── Pre-built art constants ──────────────────────────────────────

MOON_ART = AsciiArt([
    "\u25dc\u25dd",
    "\u25df\u25de",
])

BLACK_HOLE_CORE = AsciiArt([
    "(( ",
    "\u2588\u2588",
    " ))",
])

HYDROTHERMAL_VENT = AsciiArt([
    "  \u00b0  ",
    " \u00b0\u00b0 ",
    " \u2593\u2592\u2593 ",
    "\u2593\u2592\u2591\u2592\u2593",
])

LIGHTHOUSE = AsciiArt([
    " \u25b2 ",
    "[*]",
    "| |",
    "| |",
    "|_|",
    "/X\\",
])

MOUNTAINS = AsciiArt([
    "       /\\        /\\    ",
    "    /\\/  \\  /\\  /  \\   ",
    "   /      \\/  \\/    \\  ",
    "  /                  \\ ",
    " /                    \\",
])

VOLCANO = AsciiArt([
    "    \u2571\u2593\u2572    ",
    "   \u2571\u2593\u2593\u2593\u2572   ",
    "  \u2571\u2591\u2591\u2593\u2591\u2591\u2572  ",
    " \u2571\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2572 ",
    "\u2571\u2592\u2592\u2592\u2592\u2592\u2592\u2592\u2592\u2592\u2572",
])

SPIDER = AsciiArt([
    " /\u2572 ",
    "\u2571\u25c9\u25c9\u2572",
    "\u2572  \u2571",
    " \u2572\u2571 ",
])

SNOW_GLOBE = AsciiArt([
    "   \u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e   ",
    "  \u2571             \u2572  ",
    " \u2502               \u2502 ",
    " \u2502               \u2502 ",
    "  \u2572             \u2571  ",
    "   \u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f   ",
])

PENDULUM = AsciiArt([
    "\u2564",
    "\u2502",
    "\u2502",
    "\u25cf",
])

CLOCK_FACE = AsciiArt([
    "   \u256d\u2500\u2500\u2500\u2500\u2500\u256e   ",
    "  \u2502 XII  \u2502  ",
    " \u2502   \u2502   \u2502 ",
    "\u2502 IX \u2502 III\u2502",
    " \u2502   \u25cf\u2500\u2500\u2500 \u2502 ",
    "  \u2502  VI  \u2502  ",
    "   \u2570\u2500\u2500\u2500\u2500\u2500\u256f   ",
])

GEAR_SMALL = AsciiArt([
    " \u2500 ",
    "\u2502\u25cb\u2502",
    " \u2500 ",
])

CAMPFIRE_LOGS = AsciiArt([
    "  \u2593\u2593  ",
    " \u2593\u2593\u2593\u2593 ",
    "\u2550\u2550\u2550\u2550\u2550\u2550",
])

BONFIRE = AsciiArt([
    "       (\u2588)       ",
    "      (\u2588\u2588\u2588)      ",
    "     (\u2588\u2588\u2588\u2588\u2588)     ",
    "    (\u2588\u2588\u2588\u2588\u2588\u2588\u2588)    ",
    "   (\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588)   ",
    "    \u2591\u2591\u2591\u2591\u2591\u2591\u2591    ",
    "   \u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591   ",
    "  \u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591  ",
    " \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 ",
    "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550",
])
