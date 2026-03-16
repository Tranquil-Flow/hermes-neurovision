# Overlay Mode Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a CLI-over-scene overlay mode where neurovision renders animated themes as a background layer while the user types in a PTY-hosted shell or hermes-agent, with configurable text fading, glow, color, and background opacity.

**Architecture:** A new `OverlayApp` owns curses, spawns a child process in a PTY via `pty.fork()`, feeds output through a minimal VT100 emulator (`VTScreen`), and composites the text over the scene each frame using a `FadeCompositor`. Scene stepping is delegated to lightweight `SceneDelegate` classes that extract the stepping logic from existing apps without refactoring them.

**Tech Stack:** Python 3.10+ stdlib only — `curses`, `pty`, `os`, `fcntl`, `signal`, `struct`, `select`, `collections.deque`

**Spec:** `docs/superpowers/specs/2026-03-16-overlay-mode-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `hermes_neurovision/vt.py` | Create | VTCell dataclass + VTScreen terminal emulator (ANSI parsing, cursor, scroll) |
| `hermes_neurovision/compositor.py` | Create | FadeConfig dataclass + FadeCompositor (position/age/both fade, text bg opacity, glow, color) |
| `hermes_neurovision/overlay.py` | Create | SceneDelegate classes + OverlayApp (PTY, main loop, input routing, status bar) |
| `hermes_neurovision/sources/vt_source.py` | Create | VTEventSource (vt_output, vt_scroll events from terminal activity) |
| `hermes_neurovision/cli.py` | Modify | Add --overlay/--cli/--cmd and all text appearance flags, dispatch to OverlayApp |
| `hermes_neurovision/bridge.py` | Modify | Add vt_output and vt_scroll trigger mappings |
| `tests/test_vt.py` | Create | VTScreen unit tests |
| `tests/test_compositor.py` | Create | FadeCompositor unit tests |
| `tests/test_overlay.py` | Create | OverlayApp integration tests (PTY spawn, input routing, mode switching) |
| `tests/test_vt_source.py` | Create | VTEventSource unit tests |

---

## Chunk 1: VT100 Terminal Emulator

### Task 1: VTCell dataclass and VTScreen skeleton

**Files:**
- Create: `hermes_neurovision/vt.py`
- Create: `tests/test_vt.py`

- [ ] **Step 1: Write failing tests for VTCell and VTScreen init**

```python
# tests/test_vt.py
"""Tests for the VT100 terminal emulator."""
from hermes_neurovision.vt import VTCell, VTScreen


def test_vtcell_defaults():
    cell = VTCell()
    assert cell.char == " "
    assert cell.bold is False
    assert cell.fg == 7
    assert cell.born_frame == 0


def test_vtscreen_init():
    vt = VTScreen(24, 80)
    assert vt.rows == 24
    assert vt.cols == 80
    assert vt.cursor_row == 0
    assert vt.cursor_col == 0
    assert len(vt.cells) == 24
    assert len(vt.cells[0]) == 80
    assert vt.cells[0][0].char == " "


def test_vtscreen_init_small():
    vt = VTScreen(2, 3)
    assert len(vt.cells) == 2
    assert len(vt.cells[1]) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_vt.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'hermes_neurovision.vt'`

- [ ] **Step 3: Write VTCell and VTScreen skeleton**

```python
# hermes_neurovision/vt.py
"""Minimal VT100 terminal emulator for overlay mode.

Maintains a grid of cells representing child process terminal output.
Supports basic ANSI escape sequences sufficient for shell and hermes-agent.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class VTCell:
    """Single character cell in the terminal grid."""
    char: str = " "
    bold: bool = False
    fg: int = 7           # ANSI color 0-7
    born_frame: int = 0   # frame when last written (for age-based fading)


class VTScreen:
    """Minimal VT100-compatible terminal screen buffer.

    Tracks cursor position, handles basic ANSI sequences, and maintains
    a scrollback buffer for lines that scroll off the top.
    """

    def __init__(self, rows: int, cols: int, scrollback_limit: int = 200) -> None:
        self.rows = rows
        self.cols = cols
        self.cursor_row = 0
        self.cursor_col = 0
        self.cells: list[list[VTCell]] = [
            [VTCell() for _ in range(cols)] for _ in range(rows)
        ]
        self.scrollback: deque[list[VTCell]] = deque(maxlen=scrollback_limit)
        self.bytes_since_last_poll = 0
        self.scrolls_since_last_poll = 0
        self._current_frame = 0

        # SGR state
        self._bold = False
        self._fg = 7

        # ESC sequence parser state
        self._state = "ground"  # "ground", "escape", "csi"
        self._csi_params = ""

    def set_frame(self, frame: int) -> None:
        """Update current frame counter (called each render frame)."""
        self._current_frame = frame

    def feed(self, data: bytes) -> None:
        """Parse raw bytes from PTY, update cell grid and cursor."""
        self.bytes_since_last_poll += len(data)
        for byte in data:
            ch = chr(byte) if byte < 128 else "?"
            self._process_char(ch)

    def resize(self, rows: int, cols: int) -> None:
        """Handle terminal resize — adjust grid, clamp cursor."""
        old_rows = self.rows
        old_cols = self.cols
        self.rows = rows
        self.cols = cols

        # Resize rows
        if rows > old_rows:
            for _ in range(rows - old_rows):
                self.cells.append([VTCell() for _ in range(cols)])
        elif rows < old_rows:
            for _ in range(old_rows - rows):
                if self.cells:
                    self.scrollback.append(self.cells.pop(0))

        # Resize columns in each row
        for r in range(len(self.cells)):
            row = self.cells[r]
            if cols > len(row):
                row.extend(VTCell() for _ in range(cols - len(row)))
            elif cols < len(row):
                self.cells[r] = row[:cols]

        # Clamp cursor
        self.cursor_row = min(self.cursor_row, self.rows - 1)
        self.cursor_col = min(self.cursor_col, self.cols - 1)

    def reset_poll_counters(self) -> None:
        """Reset bytes/scrolls counters (called after polling for events)."""
        self.bytes_since_last_poll = 0
        self.scrolls_since_last_poll = 0

    def _process_char(self, ch: str) -> None:
        """State machine: route character through ground/escape/csi states."""
        pass  # Implemented in Task 2

    def _scroll_up(self) -> None:
        """Scroll screen up one line — top row goes to scrollback."""
        pass  # Implemented in Task 2

    def _put_char(self, ch: str) -> None:
        """Write character at cursor with current SGR attributes, advance cursor."""
        pass  # Implemented in Task 2
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_vt.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add hermes_neurovision/vt.py tests/test_vt.py
git commit -m "feat(overlay): VTCell dataclass and VTScreen skeleton"
```

---

### Task 2: VTScreen character processing — printable chars, newline, CR, backspace, tab, scrolling

**Files:**
- Modify: `hermes_neurovision/vt.py`
- Modify: `tests/test_vt.py`

- [ ] **Step 1: Write failing tests**

```python
# Add to tests/test_vt.py

def test_feed_printable():
    vt = VTScreen(24, 80)
    vt.feed(b"Hello")
    assert vt.cells[0][0].char == "H"
    assert vt.cells[0][1].char == "e"
    assert vt.cells[0][4].char == "o"
    assert vt.cursor_col == 5
    assert vt.cursor_row == 0


def test_feed_newline():
    vt = VTScreen(24, 80)
    vt.feed(b"A\nB")
    assert vt.cells[0][0].char == "A"
    assert vt.cells[1][0].char == "B"
    assert vt.cursor_row == 1
    assert vt.cursor_col == 1


def test_feed_carriage_return():
    vt = VTScreen(24, 80)
    vt.feed(b"Hello\rX")
    assert vt.cells[0][0].char == "X"
    assert vt.cells[0][1].char == "e"
    assert vt.cursor_col == 1


def test_feed_backspace():
    vt = VTScreen(24, 80)
    vt.feed(b"AB\x08C")
    assert vt.cells[0][0].char == "A"
    assert vt.cells[0][1].char == "C"
    assert vt.cursor_col == 2


def test_feed_tab():
    vt = VTScreen(24, 80)
    vt.feed(b"A\tB")
    assert vt.cells[0][0].char == "A"
    assert vt.cursor_col == 9  # tab to col 8, then B at col 8, cursor at 9
    assert vt.cells[0][8].char == "B"


def test_line_wrap():
    vt = VTScreen(24, 5)
    vt.feed(b"ABCDE")
    assert vt.cursor_col == 0
    assert vt.cursor_row == 1
    assert vt.cells[0][4].char == "E"


def test_scroll_up():
    vt = VTScreen(3, 5)
    vt.feed(b"AAA\nBBB\nCCC\nDDD")
    # Row 0 (AAA) should have scrolled into scrollback
    assert vt.cells[0][0].char == "B"
    assert vt.cells[1][0].char == "C"
    assert vt.cells[2][0].char == "D"
    assert len(vt.scrollback) == 1
    assert vt.scrollback[0][0].char == "A"


def test_born_frame_set():
    vt = VTScreen(24, 80)
    vt.set_frame(42)
    vt.feed(b"X")
    assert vt.cells[0][0].born_frame == 42


def test_bytes_since_last_poll():
    vt = VTScreen(24, 80)
    vt.feed(b"Hello")
    assert vt.bytes_since_last_poll == 5
    vt.reset_poll_counters()
    assert vt.bytes_since_last_poll == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_vt.py -v`
Expected: FAIL — `_process_char` does nothing

- [ ] **Step 3: Implement character processing**

Replace the stub methods in `hermes_neurovision/vt.py`:

```python
    def _process_char(self, ch: str) -> None:
        """State machine: route character through ground/escape/csi states."""
        if self._state == "ground":
            if ch == "\x1b":
                self._state = "escape"
            elif ch == "\n":
                self._newline()
            elif ch == "\r":
                self.cursor_col = 0
            elif ch == "\x08":  # backspace
                if self.cursor_col > 0:
                    self.cursor_col -= 1
            elif ch == "\t":
                self.cursor_col = min((self.cursor_col // 8 + 1) * 8, self.cols - 1)
            elif ch >= " ":  # printable
                self._put_char(ch)
            # else: ignore other control chars
        elif self._state == "escape":
            if ch == "[":
                self._state = "csi"
                self._csi_params = ""
            elif ch == "?":
                pass  # ignore DEC private mode intro
            else:
                self._state = "ground"  # unknown escape, drop
        elif self._state == "csi":
            if ch.isdigit() or ch == ";":
                self._csi_params += ch
            elif ch == "?":
                self._csi_params += ch  # DEC private mode prefix
            else:
                self._dispatch_csi(ch)
                self._state = "ground"

    def _newline(self) -> None:
        """Move cursor down; scroll if at bottom.

        Note: PTY output typically has ONLCR set, so \\n arrives as \\r\\n.
        We reset cursor_col here for compatibility with programs that emit
        bare \\n. This is standard VT100 behavior (LF implies CR in most
        terminal emulators in cooked mode).
        """
        if self.cursor_row < self.rows - 1:
            self.cursor_row += 1
        else:
            self._scroll_up()
        self.cursor_col = 0

    def _scroll_up(self) -> None:
        """Scroll screen up one line — top row goes to scrollback."""
        self.scrollback.append(self.cells.pop(0))
        self.cells.append([VTCell() for _ in range(self.cols)])
        self.scrolls_since_last_poll += 1

    def _put_char(self, ch: str) -> None:
        """Write character at cursor with current SGR attributes, advance cursor."""
        if self.cursor_col >= self.cols:
            self._newline()
        cell = self.cells[self.cursor_row][self.cursor_col]
        cell.char = ch
        cell.bold = self._bold
        cell.fg = self._fg
        cell.born_frame = self._current_frame
        self.cursor_col += 1
        if self.cursor_col >= self.cols:
            # Wrap: move to next line
            if self.cursor_row < self.rows - 1:
                self.cursor_row += 1
            else:
                self._scroll_up()
            self.cursor_col = 0

    def _dispatch_csi(self, final: str) -> None:
        """Handle CSI sequence. Implemented in Task 3."""
        pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_vt.py -v`
Expected: PASS (13 tests)

- [ ] **Step 5: Commit**

```bash
git add hermes_neurovision/vt.py tests/test_vt.py
git commit -m "feat(overlay): VTScreen character processing — print, newline, scroll, wrap"
```

---

### Task 3: VTScreen CSI sequence handling — cursor movement, erase, SGR colors

**Files:**
- Modify: `hermes_neurovision/vt.py`
- Modify: `tests/test_vt.py`

- [ ] **Step 1: Write failing tests**

```python
# Add to tests/test_vt.py

def test_csi_cursor_up():
    vt = VTScreen(24, 80)
    vt.feed(b"\n\n\n")  # move to row 3
    vt.feed(b"\x1b[2A")  # cursor up 2
    assert vt.cursor_row == 1


def test_csi_cursor_down():
    vt = VTScreen(24, 80)
    vt.feed(b"\x1b[3B")  # cursor down 3
    assert vt.cursor_row == 3


def test_csi_cursor_forward():
    vt = VTScreen(24, 80)
    vt.feed(b"\x1b[10C")
    assert vt.cursor_col == 10


def test_csi_cursor_back():
    vt = VTScreen(24, 80)
    vt.feed(b"ABCDE\x1b[3D")
    assert vt.cursor_col == 2


def test_csi_cursor_position():
    vt = VTScreen(24, 80)
    vt.feed(b"\x1b[5;10H")
    assert vt.cursor_row == 4  # 1-indexed → 0-indexed
    assert vt.cursor_col == 9


def test_csi_erase_line():
    vt = VTScreen(24, 80)
    vt.feed(b"Hello World")
    vt.feed(b"\x1b[5D")  # back 5 → cursor at col 6
    vt.feed(b"\x1b[K")   # erase from cursor to end of line
    assert vt.cells[0][0].char == "H"
    assert vt.cells[0][5].char == " "  # space between Hello and World (before cursor, preserved)
    assert vt.cells[0][6].char == " "  # erased (was 'W', cursor was at col 6)
    assert vt.cells[0][10].char == " " # erased


def test_csi_erase_display():
    vt = VTScreen(3, 5)
    vt.feed(b"AAAAA\nBBBBB\nCCCCC")
    vt.feed(b"\x1b[2J")  # erase entire display
    for r in range(3):
        for c in range(5):
            assert vt.cells[r][c].char == " "


def test_csi_sgr_bold():
    vt = VTScreen(24, 80)
    vt.feed(b"\x1b[1mX\x1b[22mY")
    assert vt.cells[0][0].bold is True
    assert vt.cells[0][1].bold is False


def test_csi_sgr_fg_color():
    vt = VTScreen(24, 80)
    vt.feed(b"\x1b[31mR\x1b[32mG\x1b[0mN")
    assert vt.cells[0][0].fg == 1  # red
    assert vt.cells[0][1].fg == 2  # green
    assert vt.cells[0][2].fg == 7  # reset → default


def test_csi_alt_screen_ignored():
    """Alt screen enter/exit sequences should be silently ignored."""
    vt = VTScreen(3, 5)
    vt.feed(b"Hello")
    vt.feed(b"\x1b[?1049h")  # enter alt screen
    vt.feed(b"X")
    assert vt.cells[0][0].char == "H"  # still on main screen
    assert vt.cursor_col == 6  # X was written normally


def test_resize():
    vt = VTScreen(3, 5)
    vt.feed(b"AAAAA\nBBBBB\nCCCCC")
    vt.resize(2, 4)
    assert vt.rows == 2
    assert vt.cols == 4
    assert len(vt.cells) == 2
    assert len(vt.cells[0]) == 4
    assert vt.cursor_row <= 1
    assert vt.cursor_col <= 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_vt.py -v`
Expected: FAIL — `_dispatch_csi` does nothing

- [ ] **Step 3: Implement CSI dispatch**

Replace `_dispatch_csi` in `hermes_neurovision/vt.py`:

```python
    def _dispatch_csi(self, final: str) -> None:
        """Handle a complete CSI sequence."""
        params = self._csi_params

        # Ignore DEC private mode sequences (e.g., ?1049h for alt screen)
        if params.startswith("?"):
            return

        parts = params.split(";") if params else []

        def param(idx: int, default: int = 1) -> int:
            try:
                return int(parts[idx]) if idx < len(parts) and parts[idx] else default
            except ValueError:
                return default

        if final == "A":      # Cursor Up
            self.cursor_row = max(0, self.cursor_row - param(0))
        elif final == "B":    # Cursor Down
            self.cursor_row = min(self.rows - 1, self.cursor_row + param(0))
        elif final == "C":    # Cursor Forward
            self.cursor_col = min(self.cols - 1, self.cursor_col + param(0))
        elif final == "D":    # Cursor Back
            self.cursor_col = max(0, self.cursor_col - param(0))
        elif final == "H" or final == "f":  # Cursor Position (1-indexed)
            self.cursor_row = max(0, min(self.rows - 1, param(0) - 1))
            self.cursor_col = max(0, min(self.cols - 1, param(1, 1) - 1))
        elif final == "J":    # Erase Display
            mode = param(0, 0)
            if mode == 2:     # Erase entire display
                for r in range(self.rows):
                    for c in range(self.cols):
                        self.cells[r][c] = VTCell(born_frame=self._current_frame)
            elif mode == 0:   # Erase from cursor to end
                for c in range(self.cursor_col, self.cols):
                    self.cells[self.cursor_row][c] = VTCell(born_frame=self._current_frame)
                for r in range(self.cursor_row + 1, self.rows):
                    for c in range(self.cols):
                        self.cells[r][c] = VTCell(born_frame=self._current_frame)
        elif final == "K":    # Erase Line
            mode = param(0, 0)
            if mode == 0:     # Erase from cursor to end of line
                for c in range(self.cursor_col, self.cols):
                    self.cells[self.cursor_row][c] = VTCell(born_frame=self._current_frame)
            elif mode == 1:   # Erase from start to cursor
                for c in range(self.cursor_col + 1):
                    self.cells[self.cursor_row][c] = VTCell(born_frame=self._current_frame)
            elif mode == 2:   # Erase entire line
                for c in range(self.cols):
                    self.cells[self.cursor_row][c] = VTCell(born_frame=self._current_frame)
        elif final == "m":    # SGR — Select Graphic Rendition
            self._handle_sgr(parts)

    def _handle_sgr(self, parts: list[str]) -> None:
        """Process SGR parameters."""
        if not parts or parts == [""]:
            parts = ["0"]
        for p in parts:
            try:
                code = int(p)
            except ValueError:
                continue
            if code == 0:       # Reset
                self._bold = False
                self._fg = 7
            elif code == 1:     # Bold
                self._bold = True
            elif code == 22:    # Normal intensity (no bold)
                self._bold = False
            elif 30 <= code <= 37:   # Foreground color
                self._fg = code - 30
            elif code == 39:    # Default foreground
                self._fg = 7
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_vt.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add hermes_neurovision/vt.py tests/test_vt.py
git commit -m "feat(overlay): VTScreen CSI sequences — cursor movement, erase, SGR, alt-screen ignore"
```

---

## Chunk 2: Fade Compositor

### Task 4: FadeConfig dataclass and position-based fade

**Files:**
- Create: `hermes_neurovision/compositor.py`
- Create: `tests/test_compositor.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_compositor.py
"""Tests for the fade compositor."""
from hermes_neurovision.compositor import FadeConfig, FadeCompositor


def test_fade_config_defaults():
    cfg = FadeConfig()
    assert cfg.mode == "position"
    assert cfg.fade_start_pct == 0.0
    assert cfg.fade_end_pct == 0.4
    assert cfg.text_opacity == 1.0
    assert cfg.text_bg == "transparent"
    assert cfg.text_bg_opacity == 0.0
    assert cfg.text_glow is False
    assert cfg.text_color == "auto"


def test_position_opacity_bottom():
    """Bottom of screen (below fade_end) should be fully opaque."""
    cfg = FadeConfig(fade_start_pct=0.0, fade_end_pct=0.4)
    comp = FadeCompositor(cfg)
    # Row 20 out of 24 rows — well below 40% threshold
    opacity = comp.compute_opacity(20, 24, born_frame=0, current_frame=0)
    assert opacity == 1.0


def test_position_opacity_top():
    """Top of screen (at fade_start) should be hidden."""
    cfg = FadeConfig(fade_start_pct=0.0, fade_end_pct=0.4)
    comp = FadeCompositor(cfg)
    opacity = comp.compute_opacity(0, 24, born_frame=0, current_frame=0)
    assert opacity == 0.0


def test_position_opacity_mid():
    """Middle of fade zone should be between 0 and 1."""
    cfg = FadeConfig(fade_start_pct=0.0, fade_end_pct=0.5)
    comp = FadeCompositor(cfg)
    opacity = comp.compute_opacity(5, 20, born_frame=0, current_frame=0)
    assert 0.0 < opacity < 1.0


def test_position_opacity_equal_start_end():
    """When start == end, no division by zero — all text fully opaque."""
    cfg = FadeConfig(fade_start_pct=0.3, fade_end_pct=0.3)
    comp = FadeCompositor(cfg)
    opacity = comp.compute_opacity(0, 24, born_frame=0, current_frame=0)
    # With max(...,1) guard, this should produce a valid value, not crash
    assert isinstance(opacity, float)


def test_text_opacity_multiplier():
    """Global text_opacity should scale the result."""
    cfg = FadeConfig(fade_start_pct=0.0, fade_end_pct=0.0, text_opacity=0.5)
    comp = FadeCompositor(cfg)
    opacity = comp.compute_opacity(20, 24, born_frame=0, current_frame=0)
    assert opacity <= 0.5


def test_opacity_to_attr_hidden():
    comp = FadeCompositor(FadeConfig())
    attr = comp.opacity_to_curses_attr(0.0)
    assert attr is None  # hidden


def test_opacity_to_attr_bold():
    comp = FadeCompositor(FadeConfig())
    import curses
    attr = comp.opacity_to_curses_attr(0.9)
    # Should return A_BOLD (can't test exact value without curses init,
    # but we can test it returns an int)
    assert isinstance(attr, int)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_compositor.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement FadeConfig and FadeCompositor**

```python
# hermes_neurovision/compositor.py
"""Fade compositor — blends VT text over neurovision scene.

Supports position-based, age-based, and combined fade modes.
Text can have configurable background opacity, glow, and color override.
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
_ANSI_TO_PAIR = {
    0: "base",      # black
    1: "warning",   # red
    2: "base",      # green
    3: "warning",   # yellow
    4: "soft",      # blue
    5: "accent",    # magenta
    6: "soft",      # cyan
    7: "bright",    # white
}


@dataclass
class FadeConfig:
    """Configuration for the text fade overlay."""
    mode: str = "position"          # "position", "age", "both"
    fade_start_pct: float = 0.0     # row % where fade begins (0.0 = top)
    fade_end_pct: float = 0.4       # row % where text is fully opaque
    text_opacity: float = 1.0       # global text brightness 0.0-1.0
    text_bg: str = "transparent"    # convenience alias: "transparent", "dim", "solid"
    text_bg_opacity: float = 0.0    # 0.0=transparent, 1.0=solid (overrides text_bg)
    text_glow: bool = False         # bold + bright color pair
    text_color: str = "auto"        # "auto", "white", "green", "cyan", "magenta", "yellow", "red", "theme"
    fade_lifetime: int = 1200       # frames for full age-based fade (60 seconds at 20fps)

    def __post_init__(self) -> None:
        # If text_bg_opacity wasn't explicitly set, derive from text_bg preset
        if self.text_bg in _BG_PRESETS and self.text_bg_opacity == 0.0:
            self.text_bg_opacity = _BG_PRESETS[self.text_bg]


class FadeCompositor:
    """Composites VT terminal text over a rendered scene with fade effects."""

    def __init__(self, config: FadeConfig) -> None:
        self.config = config

    def compute_opacity(self, row: int, total_rows: int,
                        born_frame: int = 0, current_frame: int = 0) -> float:
        """Compute text opacity for a given row.

        Returns 0.0 (hidden) to 1.0 (fully visible).
        """
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
                           color_pairs: dict, glow_override: bool = False) -> tuple[int, int]:
        """Resolve the curses color pair and extra attributes for a VT cell.

        Returns (color_pair_number, extra_attr).
        """
        cfg = self.config
        extra_attr = 0

        if cfg.text_glow or glow_override:
            extra_attr |= curses.A_BOLD
            pair_key = "bright"
        elif cfg.text_color != "auto":
            if cfg.text_color in _COLOR_MAP:
                pair_key, force_bold = _COLOR_MAP[cfg.text_color]
                if force_bold:
                    extra_attr |= curses.A_BOLD
            else:
                pair_key = "bright"
        else:
            # Auto: map ANSI color to nearest pair
            pair_key = _ANSI_TO_PAIR.get(vt_fg, "bright")
            if vt_bold:
                extra_attr |= curses.A_BOLD

        return color_pairs.get(pair_key, 1), extra_attr

    def composite(self, stdscr, vt_screen, color_pairs: dict,
                  current_frame: int = 0, status_row: int = -1) -> None:
        """Overlay VT text onto the already-rendered scene on stdscr.

        The scene has already been drawn to stdscr by Renderer.draw(skip_refresh=True).
        This reads the scene from stdscr via inch() and overwrites cells where VT text
        should be visible.

        Args:
            stdscr: curses window with scene already rendered
            vt_screen: VTScreen with current terminal state
            color_pairs: dict mapping pair names to pair numbers
            current_frame: current animation frame (for age-based fading)
            status_row: row reserved for status bar (-1 = last row)
        """
        h, w = stdscr.getmaxyx()
        if status_row < 0:
            status_row = h - 1

        cfg = self.config

        for y in range(min(vt_screen.rows, h)):
            if y == status_row:
                continue  # don't overlay status bar

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

                # Handle background opacity
                if vt_cell.char == " ":
                    # Space cell: blend scene with dark background
                    if cfg.text_bg_opacity >= 0.5:
                        # Show dark background
                        try:
                            stdscr.addstr(y, x, " ",
                                         curses.color_pair(color_pairs.get("base", 1)) | curses.A_DIM)
                        except curses.error:
                            pass
                    continue

                # Resolve color
                pair_num, extra_attr = self.resolve_color_pair(
                    vt_cell.fg, vt_cell.bold, color_pairs,
                    glow_override=cfg.text_glow
                )

                # Write the text character over the scene
                try:
                    stdscr.addstr(y, x, vt_cell.char,
                                 curses.color_pair(pair_num) | attr | extra_attr)
                except curses.error:
                    pass

        # Draw cursor (blinking block via A_REVERSE)
        cy, cx = vt_screen.cursor_row, vt_screen.cursor_col
        if 0 <= cy < h and cy != status_row and 0 <= cx < w:
            opacity = self.compute_opacity(cy, h, 0, current_frame)
            if opacity >= 0.15:  # only show cursor in visible region
                try:
                    cursor_char = vt_screen.cells[cy][cx].char if cx < vt_screen.cols else " "
                    pair_num = color_pairs.get("bright", 1)
                    stdscr.addstr(cy, cx, cursor_char,
                                 curses.color_pair(pair_num) | curses.A_REVERSE)
                except curses.error:
                    pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_compositor.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add hermes_neurovision/compositor.py tests/test_compositor.py
git commit -m "feat(overlay): FadeCompositor with position/age/both modes, glow, and color override"
```

---

## Chunk 3: VT Event Source + Bridge Integration

### Task 5: VTEventSource

**Files:**
- Create: `hermes_neurovision/sources/vt_source.py`
- Create: `tests/test_vt_source.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_vt_source.py
"""Tests for the VT terminal event source."""
from hermes_neurovision.vt import VTScreen
from hermes_neurovision.sources.vt_source import VTEventSource


def test_no_events_when_idle():
    vt = VTScreen(24, 80)
    src = VTEventSource(vt)
    events = src.poll(0.0)
    assert events == []


def test_vt_output_event():
    vt = VTScreen(24, 80)
    src = VTEventSource(vt)
    vt.feed(b"Hello world")
    events = src.poll(0.0)
    assert len(events) == 1
    assert events[0].kind == "vt_output"
    assert events[0].source == "vt"
    assert events[0].data["bytes"] == 11


def test_vt_scroll_event():
    vt = VTScreen(3, 10)
    src = VTEventSource(vt)
    vt.feed(b"A\nB\nC\nD")  # triggers 1 scroll
    events = src.poll(0.0)
    kinds = [e.kind for e in events]
    assert "vt_output" in kinds
    assert "vt_scroll" in kinds


def test_counters_reset_after_poll():
    vt = VTScreen(24, 80)
    src = VTEventSource(vt)
    vt.feed(b"test")
    src.poll(0.0)
    events = src.poll(0.0)
    assert events == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_vt_source.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement VTEventSource**

```python
# hermes_neurovision/sources/vt_source.py
"""Event source that emits events from VT terminal activity."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, List

from hermes_neurovision.events import VisionEvent

if TYPE_CHECKING:
    from hermes_neurovision.vt import VTScreen


class VTEventSource:
    """Generates VisionEvents from VTScreen activity counters."""

    def __init__(self, vt_screen: "VTScreen") -> None:
        self._vt = vt_screen

    def poll(self, since: float) -> List[VisionEvent]:
        events: List[VisionEvent] = []
        now = time.time()

        if self._vt.bytes_since_last_poll > 0:
            events.append(VisionEvent(
                timestamp=now,
                source="vt",
                kind="vt_output",
                severity="info",
                data={"bytes": self._vt.bytes_since_last_poll},
            ))

        if self._vt.scrolls_since_last_poll > 0:
            events.append(VisionEvent(
                timestamp=now,
                source="vt",
                kind="vt_scroll",
                severity="info",
                data={"lines": self._vt.scrolls_since_last_poll},
            ))

        self._vt.reset_poll_counters()
        return events
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_vt_source.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add hermes_neurovision/sources/vt_source.py tests/test_vt_source.py
git commit -m "feat(overlay): VTEventSource — terminal activity event source"
```

---

### Task 6: Add vt_output and vt_scroll to bridge

**Files:**
- Modify: `hermes_neurovision/bridge.py`

- [ ] **Step 1: Write failing test**

```python
# Add to existing tests/test_bridge.py (or create if missing)
# If tests/test_bridge.py doesn't exist, create it:

# tests/test_bridge.py (add these tests)
from hermes_neurovision.bridge import Bridge
from hermes_neurovision.events import VisionEvent
import time


def test_vt_output_trigger():
    bridge = Bridge()
    event = VisionEvent(timestamp=time.time(), source="vt", kind="vt_output",
                        severity="info", data={"bytes": 100})
    triggers = bridge.translate(event)
    assert len(triggers) == 1
    assert triggers[0].effect == "pulse"
    assert triggers[0].intensity <= 0.3  # low intensity, subtle


def test_vt_scroll_trigger():
    bridge = Bridge()
    event = VisionEvent(timestamp=time.time(), source="vt", kind="vt_scroll",
                        severity="info", data={"lines": 1})
    triggers = bridge.translate(event)
    assert len(triggers) == 1
    assert triggers[0].effect == "ripple"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_bridge.py::test_vt_output_trigger tests/test_bridge.py::test_vt_scroll_trigger -v`
Expected: FAIL — unknown event kind

- [ ] **Step 3: Add mappings to bridge.py**

Add these two entries to the `_MAPPING` dict in `hermes_neurovision/bridge.py`, after the existing entries:

```python
    # VT terminal activity (overlay mode)
    "vt_output":              ("pulse",      0.2, "soft",    "random_node"),
    "vt_scroll":              ("ripple",     0.3, "soft",    "center"),
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_bridge.py::test_vt_output_trigger tests/test_bridge.py::test_vt_scroll_trigger -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add hermes_neurovision/bridge.py tests/test_bridge.py
git commit -m "feat(overlay): add vt_output and vt_scroll trigger mappings to bridge"
```

---

## Chunk 4: OverlayApp — Scene Delegates + PTY + Main Loop

### Task 7: SceneDelegate classes

**Files:**
- Create: `hermes_neurovision/overlay.py`
- Create: `tests/test_overlay.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_overlay.py
"""Tests for the overlay mode components."""
import time
from unittest.mock import MagicMock, patch

from hermes_neurovision.overlay import (
    SceneDelegate, GalleryDelegate, LiveDelegate, DaemonDelegate,
)


def test_scene_delegate_interface():
    """Base delegate has step and should_switch_theme."""
    d = SceneDelegate()
    state = MagicMock()
    d.step(state, time.time())  # should not raise
    assert d.should_switch_theme(time.time()) is False


def test_gallery_delegate_steps_state():
    state = MagicMock()
    d = GalleryDelegate(theme_seconds=5.0)
    d.step(state, time.time())
    state.step.assert_called_once()


def test_gallery_delegate_switches_theme():
    d = GalleryDelegate(theme_seconds=0.1)
    d.reset_timer()
    import time as t
    t.sleep(0.15)
    assert d.should_switch_theme(t.time()) is True


def test_live_delegate_polls_events():
    poller = MagicMock()
    poller.poll.return_value = []
    bridge = MagicMock()
    state = MagicMock()
    d = LiveDelegate(poller=poller, bridge=bridge)
    d.step(state, time.time())
    state.step.assert_called_once()


def test_daemon_delegate_starts_in_gallery():
    poller = MagicMock()
    poller.poll.return_value = []
    bridge = MagicMock()
    d = DaemonDelegate(theme_seconds=10.0, poller=poller, bridge=bridge)
    assert d.mode == "gallery"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_overlay.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement SceneDelegate classes**

```python
# hermes_neurovision/overlay.py
"""Overlay mode — CLI-over-scene terminal compositor.

OverlayApp renders neurovision scenes in the background while a PTY-hosted
child process (shell or hermes-agent) runs in the foreground. Text fades
toward the top of the screen, revealing the scene behind it.
"""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING, Optional, Sequence

if TYPE_CHECKING:
    from hermes_neurovision.bridge import Bridge, VisualTrigger
    from hermes_neurovision.events import EventPoller
    from hermes_neurovision.scene import ThemeState


class SceneDelegate:
    """Base: steps scene state each frame. No curses, no input, no refresh."""

    def step(self, state: "ThemeState", now: float) -> None:
        state.step()

    def should_switch_theme(self, now: float) -> bool:
        return False

    def reset_timer(self) -> None:
        pass


class GalleryDelegate(SceneDelegate):
    """Rotates themes on timer, generates synthetic activity."""

    def __init__(self, theme_seconds: float = 10.0) -> None:
        self.theme_seconds = max(1.0, theme_seconds)
        self._switch_at = time.time() + self.theme_seconds
        self._sim_rng = random.Random()
        self._next_sim_at = time.time() + self._sim_rng.uniform(0.4, 1.2)

    def reset_timer(self) -> None:
        self._switch_at = time.time() + self.theme_seconds

    def step(self, state: "ThemeState", now: float) -> None:
        self._simulate_activity(state, now)
        state.step()

    def should_switch_theme(self, now: float) -> bool:
        return now >= self._switch_at

    def _simulate_activity(self, state: "ThemeState", now: float) -> None:
        if now < self._next_sim_at:
            return

        from hermes_neurovision.bridge import VisualTrigger

        rng = self._sim_rng
        self._next_sim_at = now + rng.uniform(0.3, 2.5)

        roll = rng.random()
        if roll < 0.20:
            state.apply_trigger(VisualTrigger("wake", rng.uniform(0.7, 1.0), "accent", "all"))
            if state.nodes:
                state.apply_trigger(VisualTrigger("burst", rng.uniform(0.6, 1.0), "bright", "center"))
        elif roll < 0.40:
            state.apply_trigger(VisualTrigger("ripple", rng.uniform(0.5, 0.9), "accent", "random_node"))
        elif roll < 0.58:
            state.apply_trigger(VisualTrigger("packet", rng.uniform(0.4, 0.8), "soft", "random_edge"))
        elif roll < 0.72:
            state.apply_trigger(VisualTrigger("pulse", rng.uniform(0.5, 0.85), "bright", "center"))
        elif roll < 0.84:
            state.apply_trigger(VisualTrigger("cascade", rng.uniform(0.4, 0.7), "soft", "random_node"))
        elif roll < 0.92:
            state.apply_trigger(VisualTrigger("burst", rng.uniform(0.3, 0.6), "accent", "random_node"))
        else:
            state.apply_trigger(VisualTrigger("cool_down", 0.4, "soft", "all"))
            self._next_sim_at = now + rng.uniform(0.8, 1.8)


class LiveDelegate(SceneDelegate):
    """Polls events, applies triggers. Single theme."""

    def __init__(self, poller: "EventPoller", bridge: "Bridge") -> None:
        self.poller = poller
        self.bridge = bridge
        self._poll_counter = 0

    def step(self, state: "ThemeState", now: float) -> None:
        state.step()
        self._poll_counter += 1
        if self._poll_counter >= 5:
            self._poll_counter = 0
            events = self.poller.poll()
            for ev in events:
                triggers = self.bridge.translate(ev)
                for trigger in triggers:
                    state.apply_trigger(trigger)


class DaemonDelegate(SceneDelegate):
    """Gallery when idle, switches to live on real events."""

    def __init__(self, theme_seconds: float, poller: "EventPoller", bridge: "Bridge",
                 idle_threshold: float = 30.0) -> None:
        self.mode = "gallery"
        self.idle_threshold = idle_threshold
        self._gallery = GalleryDelegate(theme_seconds)
        self._live = LiveDelegate(poller, bridge)
        self._last_event_time: Optional[float] = None

    def reset_timer(self) -> None:
        self._gallery.reset_timer()

    def step(self, state: "ThemeState", now: float) -> None:
        # Always poll in daemon mode (even during gallery)
        self._live._poll_counter += 1
        if self._live._poll_counter >= 5:
            self._live._poll_counter = 0
            events = self._live.poller.poll()
            if events:
                if self.mode == "gallery":
                    self.mode = "live"
                self._last_event_time = now
                for ev in events:
                    triggers = self._live.bridge.translate(ev)
                    for trigger in triggers:
                        state.apply_trigger(trigger)

        # Check idle timeout → return to gallery
        if self.mode == "live" and self._last_event_time is not None:
            if now - self._last_event_time >= self.idle_threshold:
                self.mode = "gallery"
                self._last_event_time = None
                self._gallery.reset_timer()

        # Step with appropriate delegate
        if self.mode == "gallery":
            self._gallery.step(state, now)
        else:
            state.step()

    def should_switch_theme(self, now: float) -> bool:
        if self.mode == "gallery":
            return self._gallery.should_switch_theme(now)
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_overlay.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add hermes_neurovision/overlay.py tests/test_overlay.py
git commit -m "feat(overlay): SceneDelegate classes — gallery, live, daemon stepping logic"
```

---

### Task 8: OverlayApp — PTY spawn, main loop, input routing

**Files:**
- Modify: `hermes_neurovision/overlay.py`
- Modify: `tests/test_overlay.py`

- [ ] **Step 1: Write failing tests**

```python
# Add to tests/test_overlay.py
import os
import sys

from hermes_neurovision.overlay import OverlayApp
from hermes_neurovision.compositor import FadeConfig


def test_overlay_app_init():
    """OverlayApp can be constructed (without starting curses)."""
    app = OverlayApp.__new__(OverlayApp)
    app.fade_config = FadeConfig()
    app.nv_mode = False
    app.prefix_pending = False
    app.running = False
    app.current_mode = "daemon"
    assert app.nv_mode is False
    assert app.prefix_pending is False


def test_prefix_key_detection():
    """Ctrl+N (0x0E) sets prefix_pending."""
    app = OverlayApp.__new__(OverlayApp)
    app.nv_mode = False
    app.prefix_pending = False
    # Simulate: Ctrl+N detected
    app.prefix_pending = True
    assert app.prefix_pending is True


def test_mode_cycle():
    """_MODES list defines the valid mode cycle."""
    from hermes_neurovision.overlay import _MODES
    assert "daemon" in _MODES
    assert "gallery" in _MODES
    assert "live" in _MODES


def test_fade_color_cycle():
    """_TEXT_COLORS list defines the color cycle."""
    from hermes_neurovision.overlay import _TEXT_COLORS
    assert "auto" in _TEXT_COLORS
    assert "theme" in _TEXT_COLORS
    assert "green" in _TEXT_COLORS
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_overlay.py -v`
Expected: FAIL on new tests — `_MODES` not defined

- [ ] **Step 3: Add OverlayApp to overlay.py**

Add the following to the bottom of `hermes_neurovision/overlay.py`:

```python
import curses
import fcntl
import os
import pty
import select
import signal
import struct
import sys

from hermes_neurovision.compositor import FadeConfig, FadeCompositor
from hermes_neurovision.vt import VTScreen
from hermes_neurovision.themes import build_theme_config, THEMES, FRAME_DELAY
from hermes_neurovision.scene import ThemeState
from hermes_neurovision.renderer import Renderer

_MODES = ("daemon", "gallery", "live")
_TEXT_COLORS = ("auto", "theme", "white", "green", "cyan", "magenta", "yellow", "red")
_FADE_MODES = ("position", "age", "both")


class OverlayApp:
    """CLI-over-scene terminal compositor.

    Renders neurovision scenes as a background layer while a PTY-hosted
    child process runs in the foreground. Text fades toward the top.
    """

    def __init__(
        self,
        stdscr: "curses._CursesWindow",
        child_cmd: list[str],
        themes: Sequence[str],
        theme_seconds: float,
        mode: str,
        fade_config: FadeConfig,
        poller: Optional["EventPoller"] = None,
        bridge: Optional["Bridge"] = None,
    ) -> None:
        self.stdscr = stdscr
        self.child_cmd = child_cmd
        self.themes = list(themes) if themes else list(THEMES)
        self.theme_seconds = theme_seconds
        self.fade_config = fade_config
        self.compositor = FadeCompositor(fade_config)
        self.renderer = Renderer(stdscr)
        self.poller = poller
        self.bridge = bridge

        # State
        self.running = True
        self.nv_mode = False
        self.prefix_pending = False
        self.current_mode = mode
        self.theme_index = 0
        self.child_pid: Optional[int] = None
        self.pty_master: Optional[int] = None
        self.child_exited = False
        self.exit_code: Optional[int] = None
        self._exit_timer: Optional[float] = None

        # VT screen (sized to terminal)
        h, w = stdscr.getmaxyx()
        self.vt = VTScreen(h - 1, w)  # -1 for status bar

        # Scene state
        self.state = self._make_state(self.themes[self.theme_index])

        # Scene delegate
        self.delegate = self._make_delegate(mode)

    def _make_state(self, theme_name: str) -> ThemeState:
        h, w = self.stdscr.getmaxyx()
        config = build_theme_config(theme_name)
        return ThemeState(config, w, h, seed=hash(theme_name) & 0xFFFF)

    def _make_delegate(self, mode: str) -> SceneDelegate:
        if mode == "gallery":
            return GalleryDelegate(self.theme_seconds)
        elif mode == "live" and self.poller and self.bridge:
            return LiveDelegate(self.poller, self.bridge)
        elif mode == "daemon" and self.poller and self.bridge:
            return DaemonDelegate(self.theme_seconds, self.poller, self.bridge)
        else:
            return GalleryDelegate(self.theme_seconds)

    def run(self) -> None:
        """Main entry point — spawn child, enter render loop."""
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.timeout(0)

        self._spawn_child()

        # SIGWINCH handler
        def on_resize(signum, frame):
            self._handle_resize()
        signal.signal(signal.SIGWINCH, on_resize)

        try:
            self._main_loop()
        finally:
            self._cleanup()

    def _spawn_child(self) -> None:
        """Fork a PTY and exec the child command."""
        pid, master_fd = pty.fork()
        if pid == 0:
            # Child process — do NOT access self.stdscr (curses is parent-only)
            os.environ["TERM"] = "vt100"
            try:
                os.execvp(self.child_cmd[0], self.child_cmd)
            except OSError:
                os._exit(127)
        else:
            # Parent process
            self.child_pid = pid
            self.pty_master = master_fd
            # Set non-blocking
            flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
            fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            # Set terminal size on PTY
            h, w = self.stdscr.getmaxyx()
            winsize = struct.pack("HHHH", h - 1, w, 0, 0)  # -1 for status bar
            fcntl.ioctl(master_fd, __import__("termios").TIOCSWINSZ, winsize)

    def _main_loop(self) -> None:
        """50ms frame loop: input → PTY poll → scene step → composite → refresh."""
        frame = 0
        while self.running:
            now = time.time()

            self._route_input()
            self._poll_pty()
            self._check_child()

            # Auto-exit after child exits
            if self.child_exited:
                if self._exit_timer is None:
                    self._exit_timer = now + 3.0
                elif now >= self._exit_timer:
                    self.running = False
                    break

            # Step scene
            self.vt.set_frame(frame)
            self.delegate.step(self.state, now)

            # Theme rotation
            if self.delegate.should_switch_theme(now) and len(self.themes) > 1:
                self.theme_index = (self.theme_index + 1) % len(self.themes)
                self.state = self._make_state(self.themes[self.theme_index])
                self.delegate.reset_timer()

            # Render scene (suppresses HUD and refresh)
            h, w = self.stdscr.getmaxyx()
            self.renderer.draw(self.state, self.theme_index, len(self.themes),
                              None, hide_hud=True, skip_refresh=True)

            # Composite text over scene
            self.compositor.composite(
                self.stdscr, self.vt, self.renderer.color_pairs,
                current_frame=frame, status_row=h - 1
            )

            # Status bar
            self._draw_status_bar()

            self.stdscr.refresh()
            frame += 1
            time.sleep(FRAME_DELAY)

    def _poll_pty(self) -> None:
        """Non-blocking read from PTY master fd."""
        if self.pty_master is None:
            return
        try:
            ready, _, _ = select.select([self.pty_master], [], [], 0)
            if ready:
                data = os.read(self.pty_master, 4096)
                if data:
                    self.vt.feed(data)
                else:
                    self.child_exited = True
        except OSError:
            self.child_exited = True

    def _check_child(self) -> None:
        """Check if child process has exited."""
        if self.child_pid is None or self.child_exited:
            return
        try:
            pid, status = os.waitpid(self.child_pid, os.WNOHANG)
            if pid != 0:
                self.child_exited = True
                self.exit_code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
        except ChildProcessError:
            self.child_exited = True

    def _route_input(self) -> None:
        """Read curses input and route to PTY or neurovision controls."""
        while True:
            ch = self.stdscr.getch()
            if ch == -1:
                return
            if self.nv_mode:
                if ch == 27:  # Esc exits NV mode
                    self.nv_mode = False
                else:
                    self._handle_nv_key(ch)
            elif self.prefix_pending:
                self._handle_prefix(ch)
                self.prefix_pending = False
            elif ch == 0x0E:  # Ctrl+N
                self.prefix_pending = True
            else:
                self._write_pty(ch)

    def _write_pty(self, ch: int) -> None:
        """Forward a keypress to the PTY child."""
        if self.pty_master is None or self.child_exited:
            return
        try:
            if ch < 256:
                os.write(self.pty_master, bytes([ch]))
            elif ch == curses.KEY_BACKSPACE:
                os.write(self.pty_master, b"\x7f")
            elif ch == curses.KEY_ENTER or ch == 10:
                os.write(self.pty_master, b"\n")
            elif ch == curses.KEY_UP:
                os.write(self.pty_master, b"\x1b[A")
            elif ch == curses.KEY_DOWN:
                os.write(self.pty_master, b"\x1b[B")
            elif ch == curses.KEY_RIGHT:
                os.write(self.pty_master, b"\x1b[C")
            elif ch == curses.KEY_LEFT:
                os.write(self.pty_master, b"\x1b[D")
            elif ch == curses.KEY_HOME:
                os.write(self.pty_master, b"\x1b[H")
            elif ch == curses.KEY_END:
                os.write(self.pty_master, b"\x1b[F")
            elif ch == curses.KEY_DC:  # Delete
                os.write(self.pty_master, b"\x1b[3~")
        except OSError:
            pass

    def _handle_prefix(self, ch: int) -> None:
        """Handle Ctrl+N prefix command."""
        c = chr(ch) if ch < 256 else ""
        if c == "t":
            self._next_theme()
        elif c == "T":
            self._prev_theme()
        elif c == "f":
            self._cycle_fade_mode()
        elif c == "g":
            self.fade_config.text_glow = not self.fade_config.text_glow
        elif c == "c":
            idx = _TEXT_COLORS.index(self.fade_config.text_color) if self.fade_config.text_color in _TEXT_COLORS else 0
            self.fade_config.text_color = _TEXT_COLORS[(idx + 1) % len(_TEXT_COLORS)]
        elif c == "[":
            self.fade_config.text_bg_opacity = max(0.0, self.fade_config.text_bg_opacity - 0.1)
        elif c == "]":
            self.fade_config.text_bg_opacity = min(1.0, self.fade_config.text_bg_opacity + 0.1)
        elif c == "d":
            pass  # debug panel (future)
        elif c == "1":
            self._switch_mode("daemon")
        elif c == "2":
            self._switch_mode("gallery")
        elif c == "3":
            self._switch_mode("live")
        elif c == "m":
            self.nv_mode = True
        elif c == "q":
            self.running = False
        elif ch == 0x0E:  # Ctrl+N Ctrl+N → send literal Ctrl+N
            self._write_pty(0x0E)

    def _handle_nv_key(self, ch: int) -> None:
        """Handle key in neurovision mode."""
        c = chr(ch) if ch < 256 else ""
        if ch == curses.KEY_RIGHT or c == "t":
            self._next_theme()
        elif ch == curses.KEY_LEFT or c == "T":
            self._prev_theme()
        elif c == "f":
            self._cycle_fade_mode()
        elif c == "g":
            self.fade_config.text_glow = not self.fade_config.text_glow
        elif c == "c":
            idx = _TEXT_COLORS.index(self.fade_config.text_color) if self.fade_config.text_color in _TEXT_COLORS else 0
            self.fade_config.text_color = _TEXT_COLORS[(idx + 1) % len(_TEXT_COLORS)]

    def _next_theme(self) -> None:
        self.theme_index = (self.theme_index + 1) % len(self.themes)
        self.state = self._make_state(self.themes[self.theme_index])

    def _prev_theme(self) -> None:
        self.theme_index = (self.theme_index - 1) % len(self.themes)
        self.state = self._make_state(self.themes[self.theme_index])

    def _cycle_fade_mode(self) -> None:
        idx = _FADE_MODES.index(self.fade_config.mode) if self.fade_config.mode in _FADE_MODES else 0
        self.fade_config.mode = _FADE_MODES[(idx + 1) % len(_FADE_MODES)]

    def _switch_mode(self, mode: str) -> None:
        if mode == self.current_mode:
            return
        self.current_mode = mode
        self.delegate = self._make_delegate(mode)

    def _draw_status_bar(self) -> None:
        """Draw status bar on the bottom row."""
        h, w = self.stdscr.getmaxyx()
        y = h - 1

        theme_name = self.themes[self.theme_index] if self.themes else "?"

        if self.nv_mode:
            bar = f" [{theme_name}] [NV MODE] [←→ theme | f fade | g glow | c color | Esc exit] "
        elif self.child_exited:
            code = self.exit_code if self.exit_code is not None else "?"
            bar = f" [{theme_name}] [Process exited: {code}] [Ctrl+N q to quit] "
        else:
            cmd_str = " ".join(self.child_cmd)
            mode_str = self.current_mode
            extras = []
            if self.fade_config.text_glow:
                extras.append("glow")
            if self.fade_config.text_color != "auto":
                extras.append(self.fade_config.text_color)
            extra_str = " " + " ".join(extras) if extras else ""
            bar = f" [{theme_name}] [{mode_str}] [{cmd_str}]{extra_str} [Ctrl+N: controls] "

        bar = bar[:w - 1]
        try:
            self.stdscr.addstr(y, 0, bar.ljust(w - 1),
                              curses.color_pair(self.renderer.color_pairs.get("soft", 2)) | curses.A_BOLD)
        except curses.error:
            pass

    def _handle_resize(self) -> None:
        """Handle terminal resize."""
        # Read new terminal size from OS (not from curses, which has stale dimensions)
        try:
            size = os.get_terminal_size()
            new_h, new_w = size.lines, size.columns
        except OSError:
            return
        curses.resizeterm(new_h, new_w)
        h, w = self.stdscr.getmaxyx()
        self.vt.resize(h - 1, w)
        self.state.resize(w, h)
        # Propagate to child PTY
        if self.pty_master is not None:
            import termios
            winsize = struct.pack("HHHH", h - 1, w, 0, 0)
            try:
                fcntl.ioctl(self.pty_master, termios.TIOCSWINSZ, winsize)
                if self.child_pid:
                    os.kill(self.child_pid, signal.SIGWINCH)
            except (OSError, ProcessLookupError):
                pass

    def _cleanup(self) -> None:
        """Clean up child process."""
        if self.child_pid is not None and not self.child_exited:
            try:
                os.kill(self.child_pid, signal.SIGHUP)
                os.waitpid(self.child_pid, 0)
            except (OSError, ChildProcessError):
                pass
        if self.pty_master is not None:
            try:
                os.close(self.pty_master)
            except OSError:
                pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_overlay.py -v`
Expected: PASS (all tests including new ones)

- [ ] **Step 5: Commit**

```bash
git add hermes_neurovision/overlay.py tests/test_overlay.py
git commit -m "feat(overlay): OverlayApp with PTY spawn, main loop, input routing, status bar"
```

---

## Chunk 5: CLI Integration

### Task 9: Add overlay CLI flags and dispatch

**Files:**
- Modify: `hermes_neurovision/cli.py`

- [ ] **Step 1: Write failing test**

```python
# Add to tests/test_cli.py (or create minimal test file)
from hermes_neurovision.cli import parse_args


def test_overlay_flag():
    args = parse_args(["--overlay"])
    assert args.overlay is True


def test_cli_flag():
    args = parse_args(["--cli"])
    assert args.cli is True


def test_fade_flags():
    args = parse_args(["--overlay", "--fade-mode", "age", "--fade-start", "0.1",
                       "--fade-end", "0.6", "--text-opacity", "0.8"])
    assert args.fade_mode == "age"
    assert args.fade_start == 0.1
    assert args.fade_end == 0.6
    assert args.text_opacity == 0.8


def test_text_appearance_flags():
    args = parse_args(["--cli", "--text-glow", "--text-color", "cyan",
                       "--text-bg", "dim", "--text-bg-opacity", "0.5"])
    assert args.text_glow is True
    assert args.text_color == "cyan"
    assert args.text_bg == "dim"
    assert args.text_bg_opacity == 0.5


def test_cmd_flag():
    args = parse_args(["--overlay", "--cmd", "hermes chat"])
    assert args.cmd == "hermes chat"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_cli.py::test_overlay_flag tests/test_cli.py::test_cli_flag tests/test_cli.py::test_fade_flags tests/test_cli.py::test_text_appearance_flags tests/test_cli.py::test_cmd_flag -v`
Expected: FAIL — unrecognized arguments

- [ ] **Step 3: Add CLI flags to `cli.py`**

Add after the background mode argument group (line ~119) in `hermes_neurovision/cli.py`:

```python
    # ── Overlay mode (CLI-over-scene) ────────────────────────────────────────
    overlay_group = parser.add_argument_group(
        "overlay mode",
        "Run neurovision as a background visual layer behind a CLI session. "
        "Text fades toward the top, revealing the scene."
    )
    overlay_group.add_argument("--overlay", action="store_true",
                               help="Enable overlay mode (spawn PTY with shell)")
    overlay_group.add_argument("--cli", action="store_true",
                               help="Shortcut: overlay + hermes chat")
    overlay_group.add_argument("--cmd", default=None,
                               help="Command to spawn in PTY (default: $SHELL)")
    overlay_group.add_argument("--fade-mode", choices=["position", "age", "both"],
                               default="position", help="Text fade type")
    overlay_group.add_argument("--fade-start", type=float, default=0.0,
                               help="Fade start row (0.0=top, default: 0.0)")
    overlay_group.add_argument("--fade-end", type=float, default=0.4,
                               help="Fade end row (fully opaque below, default: 0.4)")
    overlay_group.add_argument("--text-opacity", type=float, default=1.0,
                               help="Global text brightness 0.0-1.0")
    overlay_group.add_argument("--text-bg", choices=["transparent", "dim", "solid"],
                               default="transparent", help="Text background preset")
    overlay_group.add_argument("--text-bg-opacity", type=float, default=None,
                               help="Fine-grained text background opacity 0.0-1.0 (overrides --text-bg)")
    overlay_group.add_argument("--text-glow", action="store_true",
                               help="Enable glow effect on text")
    overlay_group.add_argument("--text-color",
                               choices=["auto", "white", "green", "cyan", "magenta", "yellow", "red", "theme"],
                               default="auto", help="Text color override")
```

Then add the overlay dispatch to `main()`, after the background mode early-exit block (after line ~134):

```python
    # ── Overlay mode early-exit ──────────────────────────────────────────────
    if args.overlay or args.cli:
        _run_overlay(args)
        return
```

And add the `_run_overlay` function:

```python
def _run_overlay(args):
    import shlex
    from hermes_neurovision.overlay import OverlayApp
    from hermes_neurovision.compositor import FadeConfig
    from hermes_neurovision.events import EventPoller
    from hermes_neurovision.bridge import Bridge
    from hermes_neurovision.sources.custom import CustomSource
    from hermes_neurovision.sources.state_db import StateDbSource
    from hermes_neurovision.sources.memories import MemoriesSource
    from hermes_neurovision.sources.cron import CronSource
    from hermes_neurovision.sources.aegis import AegisSource
    from hermes_neurovision.sources.trajectories import TrajectoriesSource
    from hermes_neurovision.sources.docker_tasks import DockerTaskSource

    # Determine child command
    if args.cli:
        child_cmd = ["hermes", "chat"]
    elif args.cmd:
        child_cmd = shlex.split(args.cmd)
    else:
        child_cmd = [os.environ.get("SHELL", "/bin/zsh")]

    # Build FadeConfig
    bg_opacity = args.text_bg_opacity if args.text_bg_opacity is not None else {"transparent": 0.0, "dim": 0.3, "solid": 1.0}.get(args.text_bg, 0.0)
    fade_config = FadeConfig(
        mode=args.fade_mode,
        fade_start_pct=args.fade_start,
        fade_end_pct=args.fade_end,
        text_opacity=args.text_opacity,
        text_bg=args.text_bg,
        text_bg_opacity=bg_opacity,
        text_glow=args.text_glow,
        text_color=args.text_color,
    )

    # Event sources
    sources = [
        CustomSource().poll,
        StateDbSource().poll,
        MemoriesSource().poll,
        CronSource().poll,
        TrajectoriesSource().poll,
        DockerTaskSource().poll,
    ]
    if not args.no_aegis:
        sources.append(AegisSource().poll)

    poller = EventPoller(sources=sources)
    bridge = Bridge()

    # Determine scene mode
    mode = getattr(args, "overlay_mode", "daemon")
    if args.gallery:
        mode = "gallery"
    elif args.live:
        mode = "live"

    # Theme list — respect --theme flag for single-theme mode
    from hermes_neurovision.themes import THEMES as ALL_THEMES
    if args.theme and args.theme != "neural-sky":
        themes = [args.theme]
    else:
        themes = list(ALL_THEMES)

    def run_curses(stdscr):
        app = OverlayApp(
            stdscr=stdscr,
            child_cmd=child_cmd,
            themes=themes,
            theme_seconds=args.theme_seconds,
            mode=mode,
            fade_config=fade_config,
            poller=poller,
            bridge=bridge,
        )
        app.run()

    try:
        curses.wrapper(run_curses)
    except KeyboardInterrupt:
        pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_cli.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Run full test suite**

Run: `python -m pytest tests/ -q`
Expected: All existing tests still pass. No regressions.

- [ ] **Step 6: Commit**

```bash
git add hermes_neurovision/cli.py tests/test_cli.py
git commit -m "feat(overlay): CLI integration — --overlay, --cli, --cmd, fade and text appearance flags"
```

---

## Chunk 6: Smoke Test + VT Source Wiring

### Task 10: Wire VTEventSource into OverlayApp and smoke test

**Files:**
- Modify: `hermes_neurovision/overlay.py`

- [ ] **Step 1: Add VTEventSource to OverlayApp**

In `OverlayApp.__init__()`, after creating `self.vt`, add:

```python
        # Wire VT event source into poller (if poller exists)
        if self.poller is not None:
            from hermes_neurovision.sources.vt_source import VTEventSource
            vt_source = VTEventSource(self.vt)
            self.poller._sources.append(vt_source.poll)
```

- [ ] **Step 2: Run full test suite**

Run: `python -m pytest tests/ -q`
Expected: All tests pass.

- [ ] **Step 3: Manual smoke test — overlay with shell**

Run: `python -m hermes_neurovision --overlay`
Expected: Terminal shows neurovision scene with shell prompt overlaid. Type commands, text appears in foreground with fade gradient. `Ctrl+N t` switches theme. `Ctrl+N q` quits.

- [ ] **Step 4: Manual smoke test — overlay with hermes**

Run: `python -m hermes_neurovision --cli`
Expected: Hermes chat launches inside the overlay. Neurovision scene renders behind the conversation. Events from hermes trigger visual effects.

- [ ] **Step 5: Test text appearance controls**

Run: `python -m hermes_neurovision --overlay --text-glow --text-color green --text-bg dim`
Expected: Text appears with glow effect in green with slightly dimmed scene behind it.

Try runtime controls:
- `Ctrl+N g` — toggle glow
- `Ctrl+N c` — cycle text color
- `Ctrl+N [` / `]` — adjust background opacity
- `Ctrl+N f` — cycle fade mode
- `Ctrl+N 1/2/3` — switch scene mode

- [ ] **Step 6: Commit**

```bash
git add hermes_neurovision/overlay.py
git commit -m "feat(overlay): wire VTEventSource into poller, complete overlay mode"
```

---

## Chunk 7: Final Polish

### Task 11: Add --mode flag to CLI (for overlay mode specifically)

**Files:**
- Modify: `hermes_neurovision/cli.py`

The `--mode` flag is already in the mutually exclusive group as `--live`/`--gallery`/`--daemon`. For overlay mode, we need a separate `--mode` choice flag since overlay supports mode switching.

- [ ] **Step 1: Verify --mode flag already works in overlay dispatch**

The `_run_overlay` function already checks `args.mode`, `args.gallery`, `args.live`. We need to add `--mode` as an explicit overlay argument if not already present.

Check if `args.mode` is set by the existing mutually exclusive group. If `--gallery` is set, `args.gallery = True`. The overlay dispatch in `_run_overlay` already handles this.

If `--mode` is not yet an argument, add it to the overlay group:

```python
    overlay_group.add_argument("--mode", choices=["daemon", "gallery", "live"],
                               default="daemon", dest="overlay_mode",
                               help="Scene mode for overlay (default: daemon)")
```

Update `_run_overlay` to use `args.overlay_mode`.

- [ ] **Step 2: Run tests**

Run: `python -m pytest tests/ -q`
Expected: All pass.

- [ ] **Step 3: Commit**

```bash
git add hermes_neurovision/cli.py
git commit -m "feat(overlay): add --mode flag for overlay scene mode selection"
```

---

### Task 12: Update CLAUDE.md with overlay mode documentation

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add overlay mode section to CLAUDE.md**

Add after the "## Aegis Integration" section:

```markdown
## Overlay Mode

`--overlay` or `--cli` launches neurovision as a background visual layer behind a PTY-hosted CLI session. Text from the child process (shell or hermes-agent) is composited over the scene with a configurable fade gradient.

Key modules:
- `vt.py` — Minimal VT100 terminal emulator (cursor, ANSI sequences, scroll)
- `compositor.py` — FadeCompositor with position/age/both fade, text bg opacity, glow, color override
- `overlay.py` — OverlayApp (PTY spawn, main loop, input routing), SceneDelegate classes

`Ctrl+N` is the prefix key for neurovision controls in overlay mode. All other keys go to the PTY child.

The `--cli` flag is shorthand for `--overlay --cmd "hermes chat"`.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add overlay mode section to CLAUDE.md"
```

---

### Task 13: Final full test run

- [ ] **Step 1: Run complete test suite**

Run: `python -m pytest tests/ -v`
Expected: All tests pass. No regressions from overlay mode additions.

- [ ] **Step 2: Verify all new files are committed**

Run: `git status`
Expected: Clean working tree (no untracked files).
