"""Cosmic V2 theme plugins — full-screen ASCII field renderers.

Redesigned versions of cosmic themes using draw_extras() for per-cell
rendering.  Legacy node-based variants are preserved in cosmic.py under
``legacy-<name>`` identifiers.
"""

from __future__ import annotations

import curses
import math
import random
from typing import List, Optional

from hermes_neurovision.plugin import ThemePlugin, Reaction, ReactiveElement, SpecialEffect
from hermes_neurovision.theme_plugins import register


# ── Katakana + symbol glyph pool for digital rain ─────────────────────────────
# Half-width katakana U+FF65..U+FF9F, plus digits and symbols
_RAIN_GLYPHS = (
    "01234567890"
    "ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿ"
    "ﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ"
    "@#$%&*+=-~<>|?!"
)
_GLYPH_COUNT = len(_RAIN_GLYPHS)


class _RainColumn:
    """State for one falling column of digital rain.

    Attributes:
        x: Column x-position (character cell index).
        head_y: Current y-position of the bright leading character.
        speed: Fractional cells per frame the column advances.
        length: Length of the fading tail in rows.
        glyphs: Per-row glyph character (randomised and mutated each frame).
        reveal: If True, this column pauses and highlights one glyph.
        reveal_row: Row being highlighted during a reveal pause.
        reveal_timer: Frames remaining in the current reveal pause.
        reveal_bright_timer: Frames to show the highlighted glyph brighter.
    """

    __slots__ = (
        "x", "head_y", "speed", "length",
        "glyphs", "_frac",
        "reveal", "reveal_row", "reveal_timer", "reveal_bright_timer",
    )

    def __init__(self, x: int, h: int, rng: random.Random) -> None:
        self.x = x
        self.head_y: float = -rng.randint(0, h)
        self.speed: float = rng.uniform(0.25, 0.75)
        self.length: int = rng.randint(4, min(20, h - 2))
        self.glyphs: List[str] = [
            _RAIN_GLYPHS[rng.randint(0, _GLYPH_COUNT - 1)]
            for _ in range(max(1, h))
        ]
        self._frac: float = 0.0
        self.reveal: bool = False
        self.reveal_row: int = 0
        self.reveal_timer: int = 0
        self.reveal_bright_timer: int = 0

    def advance(self, rng: random.Random, h: int) -> None:
        """Advance the column by one frame, mutating a random glyph."""
        if self.reveal and self.reveal_timer > 0:
            self.reveal_timer -= 1
            if self.reveal_timer == 0:
                self.reveal = False
        else:
            self._frac += self.speed
            if self._frac >= 1.0:
                steps = int(self._frac)
                self._frac -= steps
                self.head_y += steps

            # Occasionally mutate one glyph in the tail for shimmer
            if rng.random() < 0.15:
                mi = rng.randint(0, len(self.glyphs) - 1)
                self.glyphs[mi] = _RAIN_GLYPHS[rng.randint(0, _GLYPH_COUNT - 1)]

        # Wrap when column has scrolled fully off-screen
        if self.head_y - self.length > h:
            self.head_y = -rng.randint(0, max(1, h // 2))
            self.speed = rng.uniform(0.25, 0.75)
            self.length = rng.randint(4, min(20, h - 2))
            self.reveal = False


def _safe(stdscr, y: int, x: int, ch: str, attr: int) -> None:
    try:
        stdscr.addstr(y, x, ch, attr)
    except curses.error:
        pass


class BinaryRainV2Plugin(ThemePlugin):
    """Matrix digital rain — properly implemented with per-column state.

    Each column is an independent falling stream of katakana and digit
    glyphs.  The head of each column is bright white; the tail fades from
    bright green → dim green.  Occasional \"reveal\" columns pause and
    highlight one glyph with extra brightness.

    Intensity drives rain column density and falling speed.
    """

    name = "binary-rain"

    # Per-instance column state — keyed by (width, height) so resizes rebuild.
    def __init__(self) -> None:
        super().__init__()
        self._cols: List[_RainColumn] = []
        self._last_wh = (-1, -1)

    def build_nodes(self, w, h, cx, cy, count, rng):
        """Return empty nodes — this theme uses draw_extras() exclusively."""
        return []

    def _ensure_columns(self, w: int, h: int, intensity: float, rng: random.Random) -> None:
        """Build or rebuild the column list when dimensions change."""
        if (w, h) == self._last_wh and self._cols:
            return
        self._last_wh = (w, h)
        # Density: one column every 2 cells at minimum intensity, every cell at max
        col_step = max(1, int(2.5 - intensity))
        self._cols = [
            _RainColumn(x, h, rng)
            for x in range(0, w, col_step)
        ]

    def draw_extras(self, stdscr, state, color_pairs) -> None:  # type: ignore[override]
        """Draw the full-screen digital rain each frame.

        Args:
            stdscr: curses window object (full screen).
            state: ThemeState with frame, width, height, intensity_multiplier, rng.
            color_pairs: Dict mapping colour key strings to curses pair indices.
        """
        w = state.width
        h = state.height
        intensity = state.intensity_multiplier
        rng = state.rng

        self._ensure_columns(w, h, intensity, rng)

        # Speed multiplier driven by intensity
        speed_mult = 0.5 + intensity * 1.5

        # curses attributes
        pair_bright = curses.color_pair(color_pairs.get("bright", 0))
        pair_accent = curses.color_pair(color_pairs.get("accent", 0))
        pair_soft   = curses.color_pair(color_pairs.get("soft", 0))
        pair_base   = curses.color_pair(color_pairs.get("base", 0))

        attr_head    = pair_bright | curses.A_BOLD          # white head
        attr_near    = pair_accent | curses.A_BOLD          # bright green near head
        attr_mid     = pair_soft                            # mid-green tail
        attr_dim     = pair_base  | curses.A_DIM            # fading tail end
        attr_reveal  = pair_bright | curses.A_BOLD | curses.A_STANDOUT  # highlight

        frame = state.frame

        for col in self._cols:
            # Advance column with speed scaling
            if frame % max(1, int(1.0 / (col.speed * speed_mult) + 0.5)) == 0 or speed_mult > 1.2:
                col.advance(rng, h)

            # Possibly start a reveal pause
            if not col.reveal and rng.random() < 0.0005 * intensity:
                col.reveal = True
                col.reveal_row = max(1, int(col.head_y) - rng.randint(1, max(1, col.length - 1)))
                col.reveal_timer = rng.randint(12, 30)
                col.reveal_bright_timer = col.reveal_timer

            head = int(col.head_y)
            x = col.x
            if x >= w:
                continue

            # Draw visible rows of this column
            for row_offset in range(col.length + 1):
                gy = head - row_offset
                if gy < 1 or gy >= h - 1:
                    continue

                # Glyph character
                glyph_idx = gy % len(col.glyphs)
                ch = col.glyphs[glyph_idx]

                if row_offset == 0:
                    # Bright head
                    _safe(stdscr, gy, x, ch, attr_head)
                elif col.reveal and gy == col.reveal_row:
                    # Paused highlight glyph
                    _safe(stdscr, gy, x, ch, attr_reveal)
                else:
                    # Fading tail: bright near head, dim at end
                    fade = row_offset / max(1, col.length)
                    if fade < 0.25:
                        _safe(stdscr, gy, x, ch, attr_near)
                    elif fade < 0.60:
                        _safe(stdscr, gy, x, ch, attr_mid)
                    else:
                        _safe(stdscr, gy, x, ch, attr_dim)

    def react(self, event_kind, data):
        """React to Hermes events with appropriate visual responses."""
        if event_kind in ("agent_start", "llm_start"):
            return Reaction(element=ReactiveElement.PULSE, intensity=0.8,
                           origin=(0.5, 0.0), color_key="bright", duration=1.5)
        if event_kind in ("tool_call", "mcp_tool_call"):
            return Reaction(element=ReactiveElement.SPARK, intensity=0.6,
                           origin=(random.random(), 0.0), color_key="accent", duration=0.7)
        if event_kind in ("error", "crash"):
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                           origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "llm_end":
            return Reaction(element=ReactiveElement.STREAM, intensity=0.5,
                           origin=(random.random(), 0.0), color_key="soft", duration=1.0)
        return None

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds) -> None:
        """During idle, occasionally flash a stray glyph somewhere."""
        if idle_seconds > 1.0 and state.frame % 8 == 0:
            w, h = state.width, state.height
            x = state.rng.randint(0, max(0, w - 2))
            y = state.rng.randint(1, max(2, h - 2))
            ch = _RAIN_GLYPHS[state.rng.randint(0, _GLYPH_COUNT - 1)]
            attr = curses.color_pair(color_pairs.get("soft", 0)) | curses.A_DIM
            _safe(stdscr, y, x, ch, attr)


# Register the V2 plugin — overrides the legacy node-based binary-rain
register(BinaryRainV2Plugin())
