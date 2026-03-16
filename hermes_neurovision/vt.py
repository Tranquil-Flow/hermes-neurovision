"""Minimal VT100 terminal emulator for overlay mode.

Maintains a grid of cells representing child process terminal output.
Supports basic ANSI escape sequences sufficient for shell and hermes-agent.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass


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
        self.cursor_row = min(self.cursor_row, max(0, self.rows - 1))
        self.cursor_col = min(self.cursor_col, max(0, self.cols - 1))

    def reset_poll_counters(self) -> None:
        """Reset bytes/scrolls counters (called after polling for events)."""
        self.bytes_since_last_poll = 0
        self.scrolls_since_last_poll = 0

    # ── Character processing ──────────────────────────────────────────────

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
        bare \\n. This is standard VT100 behavior in cooked mode.
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

    # ── CSI sequence dispatch ─────────────────────────────────────────────

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
