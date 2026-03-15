"""Command menu — modal overlay accessible from any mode.

Opens with 'm' key. Supersedes logs while open. Animation continues behind it.
Provides access to all neurovision features from a single menu.
"""

from __future__ import annotations

import curses
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

if TYPE_CHECKING:
    pass


class MenuItem:
    """A single menu item with label, optional shortcut hint, and action."""

    def __init__(self, label: str, shortcut: str = "", action: str = "",
                 toggle_state: Optional[Callable[[], bool]] = None) -> None:
        self.label = label
        self.shortcut = shortcut
        self.action = action  # action key returned when selected
        self.toggle_state = toggle_state  # callable returning current bool state


class CommandMenu:
    """Centered modal menu overlay that supersedes logs.

    Navigation: ↑↓ move, Enter selects, Escape/m closes.
    The menu reports which action was selected; the app handles it.
    """

    def __init__(self) -> None:
        self.active: bool = False
        self.selected_index: int = 0
        self._items: List[MenuItem] = []
        self._pending_action: Optional[str] = None
        self._mode_label: str = ""

    def configure(self, mode: str, **toggle_getters) -> None:
        """Build menu items appropriate for the current mode.

        Args:
            mode: "gallery", "live", or "daemon"
            toggle_getters: keyword callables like show_logs=lambda: self.show_logs
        """
        self._mode_label = mode.upper()
        self._items = []

        # Common items for all modes
        self._items.append(MenuItem("Theme Editor", "e", "theme_editor"))
        self._items.append(MenuItem("Tune Settings", "t", "tune"))
        self._items.append(MenuItem("Debug Panel", "d", "debug"))

        if mode in ("live", "daemon"):
            self._items.append(MenuItem(
                "Toggle Logs", "l", "toggle_logs",
                toggle_state=toggle_getters.get("show_logs"),
            ))

        if mode in ("gallery", "daemon"):
            self._items.append(MenuItem(
                "Toggle Quiet", "q", "toggle_quiet",
                toggle_state=toggle_getters.get("quiet"),
            ))

        if mode == "gallery":
            self._items.append(MenuItem(
                "Toggle Legacy", "L", "toggle_legacy",
                toggle_state=toggle_getters.get("include_legacy"),
            ))
            self._items.append(MenuItem("Disable Theme", "X", "disable_theme"))

        self._items.append(MenuItem("Hide HUD", "h", "hide"))

        if mode in ("live", "gallery"):
            self._items.append(MenuItem(
                "Export Theme", "", "export_theme",
            ))
            self._items.append(MenuItem(
                "Import Theme", "", "import_theme",
            ))

        self._items.append(MenuItem("─────────────", "", ""))  # separator
        self._items.append(MenuItem("Close Menu", "m/Esc", "close"))
        self._items.append(MenuItem("Quit", "Q", "quit"))

    @property
    def item_count(self) -> int:
        return len(self._items)

    def open(self) -> None:
        self.active = True
        self.selected_index = 0
        self._pending_action = None

    def close(self) -> None:
        self.active = False

    def pop_action(self) -> Optional[str]:
        """Return and clear any pending action from menu selection."""
        action = self._pending_action
        self._pending_action = None
        return action

    def handle_key(self, ch: int) -> bool:
        """Process a keypress. Returns True if consumed."""
        if not self.active:
            return False

        if ch == curses.KEY_DOWN:
            self._move(1)
            return True

        if ch == curses.KEY_UP:
            self._move(-1)
            return True

        if ch in (ord("\n"), ord("\r"), curses.KEY_ENTER, 10, 13):
            item = self._items[self.selected_index]
            if item.action and item.action != "":
                if item.action == "close":
                    self.close()
                else:
                    self._pending_action = item.action
            return True

        if ch == 27 or ch == ord("m"):  # Escape or m to close
            self.close()
            return True

        return True  # consume all keys while menu is open

    def _move(self, direction: int) -> None:
        """Move selection, skipping separators."""
        count = len(self._items)
        idx = self.selected_index
        for _ in range(count):
            idx = (idx + direction) % count
            if self._items[idx].action != "":
                break
        self.selected_index = idx

    # ── drawing ────────────────────────────────────────────────────────────────

    def draw(self, stdscr, color_pairs: dict) -> None:
        """Draw the command menu centered on screen."""
        if not self.active:
            return

        h, w = stdscr.getmaxyx()
        modal_w = min(44, w - 4)
        # 2 for header/footer borders + items + 1 title + 1 mode label
        modal_h = min(len(self._items) + 4, h - 2)
        top = max(0, (h - modal_h) // 2)
        left = max(0, (w - modal_w) // 2)

        bright = color_pairs.get("bright", 0)
        accent = color_pairs.get("accent", 0)
        soft = color_pairs.get("soft", 0)

        def put(y: int, x: int, text: str, attr: int = 0) -> None:
            try:
                stdscr.addstr(top + y, left + x, text[:modal_w - 2], attr)
            except curses.error:
                pass

        # Background fill
        for row in range(modal_h):
            try:
                stdscr.addstr(top + row, left, " " * modal_w, soft)
            except curses.error:
                pass

        # Header
        put(0, 1, "─" * (modal_w - 2), soft)
        title = " NEUROVISION "
        put(0, (modal_w - len(title)) // 2, title, bright | curses.A_BOLD)

        # Mode label
        mode_str = f"  mode: {self._mode_label}"
        put(1, 1, mode_str, accent)

        # Menu items
        for i, item in enumerate(self._items):
            row = i + 2
            if row >= modal_h - 1:
                break

            is_sel = (i == self.selected_index)

            # Separator
            if item.action == "":
                put(row, 1, "─" * (modal_w - 2), soft | curses.A_DIM)
                continue

            prefix = "▶ " if is_sel else "  "
            label_attr = bright | curses.A_BOLD if is_sel else soft

            # Build line: prefix + label + toggle state + shortcut
            line = f"{prefix}{item.label}"

            # Toggle state indicator
            if item.toggle_state is not None:
                try:
                    state = item.toggle_state()
                    tag = " [ON]" if state else " [OFF]"
                    line += tag
                except Exception:
                    pass

            # Right-align shortcut hint
            if item.shortcut:
                shortcut_str = f"  {item.shortcut}"
                pad = modal_w - 3 - len(line) - len(shortcut_str)
                if pad > 0:
                    line += " " * pad + shortcut_str

            put(row, 1, line, label_attr)

        # Footer
        footer_row = modal_h - 1
        put(footer_row, 1, "─" * (modal_w - 2), soft)
        hint = "↑↓ select  Enter choose  m close"
        put(footer_row, (modal_w - len(hint)) // 2, hint, soft | curses.A_DIM)
