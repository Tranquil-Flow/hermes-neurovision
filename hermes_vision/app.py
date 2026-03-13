"""Gallery and Live apps for Hermes Vision."""

from __future__ import annotations

import curses
import time
from typing import Optional, Sequence

from hermes_vision.themes import build_theme_config, FRAME_DELAY
from hermes_vision.scene import ThemeState
from hermes_vision.renderer import Renderer


class GalleryApp:
    def __init__(self, stdscr: "curses._CursesWindow", themes: Sequence[str], theme_seconds: float, end_after: Optional[float]) -> None:
        self.stdscr = stdscr
        self.themes = list(themes)
        self.theme_seconds = max(1.0, theme_seconds)
        self.end_after = end_after
        self.renderer = Renderer(stdscr)
        self.theme_index = 0
        self.paused = False
        self.state = self._make_state(self.themes[self.theme_index])
        self.switch_at = time.time() + self.theme_seconds if len(self.themes) > 1 else float("inf")

    def _make_state(self, theme_name: str) -> ThemeState:
        h, w = self.stdscr.getmaxyx()
        return ThemeState(build_theme_config(theme_name), w, h, seed=(hash(theme_name) & 0xFFFF))

    def run(self) -> None:
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.timeout(0)

        deadline = time.time() + self.end_after if self.end_after is not None else None
        while True:
            now = time.time()
            if deadline is not None and now >= deadline:
                break

            self._handle_input()
            if not self.paused:
                self.state.step()
                if len(self.themes) > 1 and now >= self.switch_at:
                    self._advance_theme(1)
            self.renderer.draw(self.state, self.theme_index, len(self.themes), deadline)
            time.sleep(FRAME_DELAY)

    def _advance_theme(self, direction: int) -> None:
        self.theme_index = (self.theme_index + direction) % len(self.themes)
        self.state = self._make_state(self.themes[self.theme_index])
        self.switch_at = time.time() + self.theme_seconds

    def _handle_input(self) -> None:
        while True:
            ch = self.stdscr.getch()
            if ch == -1:
                return
            if ch in (ord("q"), ord("Q")):
                raise SystemExit(0)
            if ch in (ord("n"), curses.KEY_RIGHT):
                self._advance_theme(1)
            elif ch in (ord("p"), curses.KEY_LEFT):
                self._advance_theme(-1)
            elif ch == ord(" "):
                self.paused = not self.paused

    @classmethod
    def run_headless(cls, themes: Sequence[str], seconds: float, theme_seconds: float = 8.0) -> dict:
        """Run without curses for testing. Returns stats dict."""
        frame_count = max(1, int(seconds / FRAME_DELAY))
        state = ThemeState(build_theme_config(themes[0]), 100, 30, seed=hash(themes[0]) & 0xFFFF)
        theme_index = 0
        next_switch = max(1, int(theme_seconds / FRAME_DELAY))
        themes_shown = 1

        for frame in range(frame_count):
            if len(themes) > 1 and frame > 0 and frame % next_switch == 0:
                theme_index = (theme_index + 1) % len(themes)
                state = ThemeState(build_theme_config(themes[theme_index]), 100, 30, seed=hash(themes[theme_index]) & 0xFFFF)
                themes_shown += 1
            state.step()

        return {"frames": frame_count, "themes_shown": themes_shown, "final_theme": themes[theme_index]}


class LiveApp:
    """Live mode — polls events and maps them to visual triggers."""

    def __init__(self, stdscr: "curses._CursesWindow", theme_name: str, poller, bridge, log_overlay, end_after: Optional[float] = None, show_logs: bool = False) -> None:
        self.stdscr = stdscr
        self.theme_name = theme_name
        self.poller = poller
        self.bridge = bridge
        self.log_overlay = log_overlay
        self.show_logs = show_logs
        self.end_after = end_after
        self.renderer = Renderer(stdscr)
        h, w = stdscr.getmaxyx()
        self.state = ThemeState(build_theme_config(theme_name), w, h, seed=hash(theme_name) & 0xFFFF)
        self._last_event_time = time.time()
        self._idle_threshold = 10.0
        self._poll_counter = 0

    def run(self) -> None:
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        deadline = time.time() + self.end_after if self.end_after else None

        while True:
            now = time.time()
            if deadline and now >= deadline:
                break

            self._handle_input()
            self.state.step()

            # Poll every ~20 frames (1 second at 50ms/frame)
            self._poll_counter += 1
            if self._poll_counter >= 20:
                self._poll_counter = 0
                events = self.poller.poll()
                if events:
                    self._last_event_time = now
                for ev in events:
                    triggers = self.bridge.translate(ev)
                    for trigger in triggers:
                        self.state.apply_trigger(trigger)
                    if self.show_logs:
                        self.log_overlay.add_event(ev)

            # Idle fallback — generative mode kicks in
            # (already handled by scene.py's normal step())

            self.renderer.draw(self.state, 0, 1, deadline)

            # Draw log overlay if enabled
            if self.show_logs:
                self._draw_logs(now)

            self.stdscr.refresh()
            time.sleep(FRAME_DELAY)

    def _draw_logs(self, now: float) -> None:
        h, w = self.stdscr.getmaxyx()
        if h < 24 or w < 80:
            return  # too small for overlay
        lines = self.log_overlay.get_visible_lines(now)
        color_map = {"cyan": 2, "green": 2, "white": 3, "magenta": 4, "yellow": 5}
        for i, (text, brightness, color) in enumerate(lines):
            y = h - 2 - len(lines) + i
            if y < 1:
                continue
            attr = curses.color_pair(color_map.get(color, 3))
            if brightness == "bold":
                attr |= curses.A_BOLD
            else:
                attr |= curses.A_DIM
            try:
                self.stdscr.addstr(y, 1, text[:w - 2], attr)
            except curses.error:
                pass

    def _handle_input(self) -> None:
        while True:
            ch = self.stdscr.getch()
            if ch == -1:
                return
            if ch in (ord("q"), ord("Q")):
                raise SystemExit(0)
            if ch == ord("l"):
                self.show_logs = not self.show_logs
            if ch == ord(" "):
                pass  # pause not yet wired
