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
        self.locked = False
        self.selected_theme = None
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
                if len(self.themes) > 1 and not self.locked and now >= self.switch_at:
                    self._advance_theme(1)
            self._draw_with_indicators()
            self.stdscr.refresh()
            time.sleep(FRAME_DELAY)

    def _draw_with_indicators(self) -> None:
        """Draw scene with lock and selection indicators."""
        h, w = self.stdscr.getmaxyx()
        self.renderer.draw(self.state, self.theme_index, len(self.themes), 
                          time.time() + (self.end_after or 0) if self.end_after else None)
        
        # Draw status indicators on a black background to prevent flashing
        # Top-right: LOCKED indicator
        if self.locked:
            text = " LOCKED "
            try:
                # Clear the area first with black background
                for i in range(len(text)):
                    self.stdscr.addch(0, w - len(text) - 1 + i, ' ', curses.color_pair(0))
                self.stdscr.addstr(0, w - len(text) - 1, text, curses.color_pair(5) | curses.A_BOLD)
            except curses.error:
                pass
        
        # Bottom-left: hint for staying on current theme
        lock_hint = " Enter to stay on current "
        try:
            self.stdscr.addstr(h - 1, 1, lock_hint, curses.color_pair(2) | curses.A_DIM)
        except curses.error:
            pass
        
        # Bottom-right: selection hint
        select_hint = " 's' to select for live "
        try:
            self.stdscr.addstr(h - 1, w - len(select_hint) - 1, select_hint, curses.color_pair(2) | curses.A_DIM)
        except curses.error:
            pass

    def _advance_theme(self, direction: int) -> None:
        self.theme_index = (self.theme_index + direction) % len(self.themes)
        self.state = self._make_state(self.themes[self.theme_index])
        if not self.locked:
            self.switch_at = time.time() + self.theme_seconds

    def _handle_input(self) -> None:
        while True:
            ch = self.stdscr.getch()
            if ch == -1:
                return
            if ch in (ord("q"), ord("Q")):
                if self.selected_theme:
                    # Exit to launch live mode with selected theme
                    raise SystemExit(0)
                raise SystemExit(0)
            if ch in (ord("n"), curses.KEY_RIGHT):
                self._advance_theme(1)
            elif ch in (ord("p"), curses.KEY_LEFT):
                self._advance_theme(-1)
            elif ch == ord(" "):
                self.paused = not self.paused
            elif ch in (ord("\n"), ord("\r"), curses.KEY_ENTER, 10, 13):
                # Enter key toggles lock mode
                self.locked = not self.locked
                if self.locked:
                    self.switch_at = float("inf")  # Stop timer
            elif ch == ord("s"):
                # Select current theme for live mode
                self.selected_theme = self.themes[self.theme_index]
                raise SystemExit(0)

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
                # Draw status indicator
                self._draw_status_indicator()

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

    def _draw_status_indicator(self) -> None:
        """Draw a status indicator showing log overlay is active."""
        h, w = self.stdscr.getmaxyx()
        status = " LOGS: ON "
        try:
            self.stdscr.addstr(0, w - len(status) - 1, status, curses.color_pair(2) | curses.A_BOLD)
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


class DaemonApp:
    """Daemon mode — gallery when idle, switches to live on events."""

    def __init__(self, stdscr: "curses._CursesWindow", themes: Sequence[str], theme_seconds: float, poller, bridge, log_overlay, show_logs: bool = False) -> None:
        self.stdscr = stdscr
        self.themes = list(themes)
        self.theme_seconds = max(1.0, theme_seconds)
        self.poller = poller
        self.bridge = bridge
        self.log_overlay = log_overlay
        self.show_logs = show_logs
        self.renderer = Renderer(stdscr)
        
        # Gallery state
        self.theme_index = 0
        self.selected_theme_name = themes[0] if themes else "neural-sky"
        
        # Mode tracking
        self.mode = "gallery"  # "gallery" or "live"
        self.last_event_time: Optional[float] = None
        self.idle_threshold = 30.0  # seconds to wait before returning to gallery
        self.transition_alpha = 0.0  # for visual transitions
        
        # Initialize with gallery state
        self.gallery_state = self._make_gallery_state(self.themes[self.theme_index])
        self.live_state: Optional[ThemeState] = None
        self.switch_at = time.time() + self.theme_seconds if len(self.themes) > 1 else float("inf")
        
        self._poll_counter = 0

    def _make_gallery_state(self, theme_name: str) -> ThemeState:
        h, w = self.stdscr.getmaxyx()
        return ThemeState(build_theme_config(theme_name), w, h, seed=(hash(theme_name) & 0xFFFF))

    def _make_live_state(self) -> ThemeState:
        h, w = self.stdscr.getmaxyx()
        return ThemeState(build_theme_config(self.selected_theme_name), w, h, seed=hash(self.selected_theme_name) & 0xFFFF)

    def run(self) -> None:
        curses.curs_set(0)
        self.stdscr.nodelay(True)

        while True:
            now = time.time()
            self._handle_input()
            
            # Poll for events every ~20 frames (1 second)
            self._poll_counter += 1
            if self._poll_counter >= 20:
                self._poll_counter = 0
                events = self.poller.poll()
                
                if events:
                    # Transition to live mode on first event
                    if self.mode == "gallery":
                        self._transition_to_live()
                    
                    self.last_event_time = now
                    
                    # Apply events to live state
                    for ev in events:
                        triggers = self.bridge.translate(ev)
                        for trigger in triggers:
                            if self.live_state:
                                self.live_state.apply_trigger(trigger)
                        if self.show_logs:
                            self.log_overlay.add_event(ev)
            
            # Check idle timeout
            if self.mode == "live" and self.last_event_time is not None:
                idle_time = now - self.last_event_time
                if idle_time >= self.idle_threshold:
                    self._transition_to_gallery()
            
            # Step the appropriate state
            if self.mode == "gallery":
                self.gallery_state.step()
                # Auto-advance themes in gallery mode
                if len(self.themes) > 1 and now >= self.switch_at:
                    self._advance_theme(1)
                self._draw_gallery()
            else:  # live mode
                if self.live_state:
                    self.live_state.step()
                self._draw_live(now)
            
            self.stdscr.refresh()
            time.sleep(FRAME_DELAY)

    def _transition_to_live(self) -> None:
        """Transition from gallery to live mode."""
        self.mode = "live"
        # Preserve selected theme from gallery
        self.selected_theme_name = self.themes[self.theme_index]
        self.live_state = self._make_live_state()
        self.last_event_time = time.time()

    def _transition_to_gallery(self) -> None:
        """Transition from live to gallery mode."""
        self.mode = "gallery"
        self.last_event_time = None
        # Reset gallery state to current theme
        self.gallery_state = self._make_gallery_state(self.themes[self.theme_index])
        self.switch_at = time.time() + self.theme_seconds if len(self.themes) > 1 else float("inf")

    def _advance_theme(self, direction: int) -> None:
        """Advance to next/previous theme in gallery mode."""
        self.theme_index = (self.theme_index + direction) % len(self.themes)
        self.gallery_state = self._make_gallery_state(self.themes[self.theme_index])
        self.switch_at = time.time() + self.theme_seconds

    def _draw_gallery(self) -> None:
        """Draw gallery mode with indicator."""
        h, w = self.stdscr.getmaxyx()
        self.renderer.draw(self.gallery_state, self.theme_index, len(self.themes), None)
        
        # Draw mode indicator
        mode_text = " DAEMON: gallery "
        try:
            self.stdscr.addstr(0, w - len(mode_text) - 1, mode_text, curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass

    def _draw_live(self, now: float) -> None:
        """Draw live mode with indicator and optional logs."""
        h, w = self.stdscr.getmaxyx()
        if self.live_state:
            self.renderer.draw(self.live_state, 0, 1, None)
        
        # Draw mode indicator
        mode_text = " DAEMON: live "
        try:
            self.stdscr.addstr(0, w - len(mode_text) - 1, mode_text, curses.color_pair(5) | curses.A_BOLD)
        except curses.error:
            pass
        
        # Draw log overlay if enabled
        if self.show_logs:
            self._draw_logs(now)

    def _draw_logs(self, now: float) -> None:
        """Draw log overlay (same as LiveApp)."""
        h, w = self.stdscr.getmaxyx()
        if h < 24 or w < 80:
            return
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
        """Handle keyboard input."""
        while True:
            ch = self.stdscr.getch()
            if ch == -1:
                return
            if ch in (ord("q"), ord("Q")):
                raise SystemExit(0)
            if ch == ord("l"):
                self.show_logs = not self.show_logs
            if self.mode == "gallery":
                if ch in (ord("n"), curses.KEY_RIGHT):
                    self._advance_theme(1)
                elif ch in (ord("p"), curses.KEY_LEFT):
                    self._advance_theme(-1)
