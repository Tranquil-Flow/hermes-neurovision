"""Gallery and Live apps for Hermes Vision."""

from __future__ import annotations

import curses
import time
from typing import Optional, Sequence

from hermes_neurovision.themes import build_theme_config, FRAME_DELAY, THEMES, LEGACY_THEMES
from hermes_neurovision.scene import ThemeState
from hermes_neurovision.renderer import Renderer
from hermes_neurovision.tune import TuneSettings, TuneOverlay
from hermes_neurovision.debug_panel import DebugPanel
from hermes_neurovision.command_menu import CommandMenu
from hermes_neurovision.theme_editor import ThemeEditor, apply_custom_overrides


class GalleryApp:
    def __init__(self, stdscr: "curses._CursesWindow", themes: Sequence[str], theme_seconds: float, end_after: Optional[float], include_legacy: bool = False) -> None:
        self.stdscr = stdscr
        self._base_themes = list(themes)
        self.include_legacy = include_legacy
        self.themes = self._base_themes + (list(LEGACY_THEMES) if include_legacy else [])
        self.theme_seconds = max(1.0, theme_seconds)
        self.end_after = end_after
        self.renderer = Renderer(stdscr)
        self.theme_index = 0
        self.paused = False
        self.locked = False
        self.quiet = False
        self.hide_hud = False
        self.selected_theme = None
        self.tune = TuneSettings()
        self.tune_overlay = TuneOverlay(self.tune)
        self.debug_panel = DebugPanel()
        self.command_menu = CommandMenu()
        self.theme_editor = ThemeEditor()
        self._escape_buf = ""
        self._fullscreen = False
        self.state = self._make_state(self.themes[self.theme_index])
        self.switch_at = time.time() + self.theme_seconds if len(self.themes) > 1 else float("inf")
        self._configure_menu()

    def _configure_menu(self) -> None:
        self.command_menu.configure(
            "gallery",
            quiet=lambda: self.quiet,
            include_legacy=lambda: self.include_legacy,
        )

    def _make_state(self, theme_name: str) -> ThemeState:
        h, w = self.stdscr.getmaxyx()
        config = build_theme_config(theme_name)
        config = apply_custom_overrides(config)
        state = ThemeState(config, w, h, seed=(hash(theme_name) & 0xFFFF), quiet=self.quiet)
        state.tune = self.tune
        return state

    def run(self) -> None:
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.timeout(0)

        deadline = time.time() + self.end_after if self.end_after is not None else None
        try:
            while True:
                now = time.time()
                if deadline is not None and now >= deadline:
                    break

                self._handle_input()
                self._process_menu_action()
                if not self.paused:
                    self.state.step()
                    if len(self.themes) > 1 and not self.locked and now >= self.switch_at:
                        self._advance_theme(1)
                self._draw_with_indicators()
                self.stdscr.refresh()
                time.sleep(FRAME_DELAY / max(0.1, self.tune.animation_speed))
        finally:
            if self._fullscreen:
                import sys
                sys.stdout.write("\033[?1049l\033[?25h")
                sys.stdout.flush()

    def _draw_with_indicators(self) -> None:
        """Draw scene with lock and selection indicators."""
        h, w = self.stdscr.getmaxyx()
        self.renderer.draw(self.state, self.theme_index, len(self.themes),
                          time.time() + (self.end_after or 0) if self.end_after else None,
                          hide_hud=self.hide_hud)

        # When HUD is hidden, skip all overlays except command menu
        if self.hide_hud:
            if self.command_menu.active:
                self.command_menu.draw(self.stdscr, self.renderer.color_pairs)
            if self.theme_editor.active:
                self.theme_editor.draw(self.stdscr, self.renderer.color_pairs)
            return

        # Top-right: LOCKED indicator
        if self.locked:
            text = " LOCKED "
            try:
                self.stdscr.addstr(0, w - len(text) - 1, text, curses.color_pair(5) | curses.A_BOLD)
            except curses.error:
                pass

        # Top-right: MUTED indicator
        if not self.tune.sound_enabled:
            mtext = " MUTED "
            right_offset = 1 + (len(" LOCKED ") + 1 if self.locked else 0)
            try:
                self.stdscr.addstr(0, w - len(mtext) - right_offset,
                                   mtext, curses.color_pair(5) | curses.A_DIM)
            except curses.error:
                pass
            right_offset += len(mtext) + 1
        else:
            right_offset = 1 + (len(" LOCKED ") + 1 if self.locked else 0)

        # Top-right: QUIET indicator
        if self.quiet:
            qtext = " QUIET "
            try:
                self.stdscr.addstr(0, w - len(qtext) - right_offset,
                                   qtext, curses.color_pair(2) | curses.A_BOLD)
            except curses.error:
                pass

        # Draw overlays (command menu supersedes others when active)
        if self.command_menu.active:
            self.command_menu.draw(self.stdscr, self.renderer.color_pairs)
        elif self.theme_editor.active:
            self.theme_editor.draw(self.stdscr, self.renderer.color_pairs)
        elif self.tune_overlay.active:
            self.tune_overlay.draw(self.stdscr, self.renderer.color_pairs)

        if self.debug_panel.visible and not self.command_menu.active:
            self.debug_panel.draw(self.stdscr, self.state, self.renderer.color_pairs)

        # Bottom: single consolidated footer with all hints
        tuned_flag = " [TUNED]" if not self.tune.is_default() else ""
        quiet_flag = " [QUIET]" if self.quiet else ""
        legacy_flag = " [+LEGACY]" if self.include_legacy else ""
        hide_flag = " [HIDDEN]" if self.hide_hud else ""
        # Left side: navigation + controls
        muted_flag = " [MUTED]" if not self.tune.sound_enabled else ""
        left = f" theme {self.theme_index + 1}/{len(self.themes)}{quiet_flag}{legacy_flag}{tuned_flag}{muted_flag} | Q quit  ←/→ nav  m menu  h hide  M mute  F full  space pause"
        # Right side: selection hints
        right = "enter lock  s use theme "
        gap = w - len(left) - len(right) - 1
        if gap < 2:
            # Narrow terminal — just show the essentials
            footer = left[:w - 2]
        else:
            footer = left + " " * gap + right

        try:
            self.stdscr.addstr(h - 1, 1, footer[:max(0, w - 2)], curses.color_pair(2) | curses.A_DIM)
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
            self._handle_key(ch)

    def _process_menu_action(self) -> None:
        """Check for and execute any pending command menu action."""
        action = self.command_menu.pop_action()
        if action is None:
            return

        if action == "quit":
            raise SystemExit(0)
        elif action == "theme_editor":
            self.command_menu.close()
            self.theme_editor.open(self.state.config)
        elif action == "tune":
            self.command_menu.close()
            self.tune_overlay.active = True
        elif action == "debug":
            self.command_menu.close()
            self.debug_panel.toggle()
        elif action == "toggle_quiet":
            self.quiet = not self.quiet
            self.state.quiet = self.quiet
            self._configure_menu()
        elif action == "toggle_legacy":
            self.include_legacy = not self.include_legacy
            self.themes = self._base_themes + (list(LEGACY_THEMES) if self.include_legacy else [])
            self.theme_index = 0
            self.state = self._make_state(self.themes[self.theme_index])
            self.switch_at = time.time() + self.theme_seconds
            self._configure_menu()
        elif action == "disable_theme":
            from hermes_neurovision.disabled import add_disabled
            current = self.themes[self.theme_index]
            add_disabled(current)
            self.themes = [t for t in self.themes if t != current]
            if not self.themes:
                from hermes_neurovision.themes import THEMES as _ALL
                self.themes = list(_ALL)
            self.theme_index = self.theme_index % len(self.themes)
            self.state = self._make_state(self.themes[self.theme_index])
            self.switch_at = time.time() + self.theme_seconds
        elif action == "hide":
            self.hide_hud = True
            self.command_menu.close()
        elif action == "export_theme":
            self._do_export()
            self.command_menu.close()
        elif action == "import_theme":
            self._do_import()
            self.command_menu.close()

    def _do_export(self) -> None:
        """Export current theme to .hvtheme file."""
        try:
            from hermes_neurovision.export import export_theme
            theme_name = self.themes[self.theme_index]
            export_theme(theme_name)
        except Exception:
            pass

    def _do_import(self) -> None:
        """Import themes from default import directory."""
        try:
            from hermes_neurovision.import_theme import scan_and_import
            scan_and_import()
        except Exception:
            pass

    def _handle_key(self, ch: int) -> None:
        """Process a single key code. Handles escape sequences internally."""
        # Escape sequence buffering for Shift+Arrow terminals
        if ch == 27 or self._escape_buf:
            if ch == 27:
                self._escape_buf = "\x1b"
                return
            self._escape_buf += chr(ch)
            if self._escape_buf == "\x1b[1;2C":
                self._escape_buf = ""
                self._advance_theme(1)
            elif self._escape_buf == "\x1b[1;2D":
                self._escape_buf = ""
                self._advance_theme(-1)
            elif len(self._escape_buf) >= 7:
                self._escape_buf = ""
            return

        if ch == ord("Q"):
            raise SystemExit(0)

        # Command menu takes priority
        if self.command_menu.active:
            self.command_menu.handle_key(ch)
            return

        # Theme editor takes priority
        if self.theme_editor.active:
            self.theme_editor.handle_key(ch)
            return

        # Tune overlay
        if self.tune_overlay.active:
            if self.tune_overlay.handle_key(ch):
                return

        # Toggle hide mode
        if ch == ord("h"):
            self.hide_hud = not self.hide_hud
            return

        # Toggle mute
        if ch == ord("M"):
            self.tune.sound_enabled = not self.tune.sound_enabled
            return

        # Toggle fullscreen (via terminal escape sequences)
        if ch == ord("F"):
            self._fullscreen = not self._fullscreen
            import sys
            if self._fullscreen:
                sys.stdout.write("\033[?1049h\033[?25l")  # alt screen + hide cursor
            else:
                sys.stdout.write("\033[?1049l\033[?25h")  # restore + show cursor
            sys.stdout.flush()
            curses.resizeterm(*self.stdscr.getmaxyx())
            return

        # Open command menu
        if ch == ord("m"):
            self._configure_menu()
            self.command_menu.open()
            return

        # Open theme editor directly
        if ch == ord("e"):
            self.theme_editor.open(self.state.config)
            return

        # Open tune overlay
        if ch == ord("t"):
            self.tune_overlay.active = True
            return

        if ch == ord("d"):
            self.debug_panel.toggle()
            return
        if ch == ord("q"):
            self.quiet = not self.quiet
            self.state.quiet = self.quiet
        if ch == ord("L"):
            self.include_legacy = not self.include_legacy
            self.themes = self._base_themes + (list(LEGACY_THEMES) if self.include_legacy else [])
            self.theme_index = 0
            self.state = self._make_state(self.themes[self.theme_index])
            self.switch_at = time.time() + self.theme_seconds
        if ch == ord("X"):
            from hermes_neurovision.disabled import add_disabled
            current = self.themes[self.theme_index]
            add_disabled(current)
            self.themes = [t for t in self.themes if t != current]
            if not self.themes:
                from hermes_neurovision.themes import THEMES as _ALL
                self.themes = list(_ALL)
            self.theme_index = self.theme_index % len(self.themes)
            self.state = self._make_state(self.themes[self.theme_index])
            self.switch_at = time.time() + self.theme_seconds
        if ch in (curses.KEY_RIGHT, curses.KEY_SRIGHT, ord("n")):
            self._advance_theme(1)
        elif ch in (curses.KEY_LEFT, curses.KEY_SLEFT, ord("p")):
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

    def __init__(self, stdscr: "curses._CursesWindow", theme_name: str, poller, bridge, log_overlay, end_after: Optional[float] = None, show_logs: bool = False, quiet: bool = False) -> None:
        self.stdscr = stdscr
        self.theme_name = theme_name
        self.poller = poller
        self.bridge = bridge
        self.log_overlay = log_overlay
        self.show_logs = show_logs
        self.end_after = end_after
        self.hide_hud = False
        self._fullscreen = False
        self.renderer = Renderer(stdscr)
        h, w = stdscr.getmaxyx()
        self.tune = TuneSettings()
        self.tune_overlay = TuneOverlay(self.tune)
        self.debug_panel = DebugPanel()
        self.command_menu = CommandMenu()
        self.theme_editor = ThemeEditor()
        config = build_theme_config(theme_name)
        config = apply_custom_overrides(config)
        self.state = ThemeState(config, w, h, seed=hash(theme_name) & 0xFFFF, quiet=quiet)
        self.state.tune = self.tune
        self._last_event_time = time.time()
        self._idle_threshold = 10.0
        self._poll_counter = 0
        self._configure_menu()

    def _configure_menu(self) -> None:
        self.command_menu.configure(
            "live",
            show_logs=lambda: self.show_logs,
        )

    def run(self) -> None:
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        deadline = time.time() + self.end_after if self.end_after else None

        try:
            while True:
                now = time.time()
                if deadline and now >= deadline:
                    break

                self._handle_input()
                self._process_menu_action()
                self.state.step()

                # Poll every ~5 frames (0.25 seconds at 50ms/frame)
                self._poll_counter += 1
                if self._poll_counter >= 5:
                    self._poll_counter = 0
                    events = self.poller.poll()
                    if events:
                        self._last_event_time = now
                    for ev in events:
                        triggers = self.bridge.translate(ev)
                        for trigger in triggers:
                            self.state.apply_trigger(trigger)
                            self.debug_panel.record_trigger(trigger, source_event=ev)
                        self.debug_panel.record_event(ev)
                        if self.show_logs:
                            self.log_overlay.add_event(ev)

                # Idle fallback — generative mode kicks in
                # (already handled by scene.py's normal step())

                self.renderer.draw(self.state, 0, 1, deadline, hide_hud=self.hide_hud)

                # Draw log overlay if enabled (but not when HUD hidden or menu active)
                if self.show_logs and not self.hide_hud and not self.command_menu.active:
                    self._draw_logs(now)
                    self._draw_status_indicator()

                # Overlays — command menu supersedes logs and other overlays
                if self.hide_hud:
                    if self.command_menu.active:
                        self.command_menu.draw(self.stdscr, self.renderer.color_pairs)
                    if self.theme_editor.active:
                        self.theme_editor.draw(self.stdscr, self.renderer.color_pairs)
                else:
                    if self.command_menu.active:
                        self.command_menu.draw(self.stdscr, self.renderer.color_pairs)
                    elif self.theme_editor.active:
                        self.theme_editor.draw(self.stdscr, self.renderer.color_pairs)
                    elif self.tune_overlay.active:
                        self.tune_overlay.draw(self.stdscr, self.renderer.color_pairs)
                    if self.debug_panel.visible and not self.command_menu.active:
                        self.debug_panel.draw(self.stdscr, self.state, self.renderer.color_pairs)

                self.stdscr.refresh()
                time.sleep(FRAME_DELAY / max(0.1, self.tune.animation_speed))
        finally:
            if self._fullscreen:
                import sys
                sys.stdout.write("\033[?1049l\033[?25h")
                sys.stdout.flush()

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
            elif brightness == "dim":
                attr |= curses.A_DIM
            # "normal" — no modifier, just the color
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

    def _process_menu_action(self) -> None:
        """Check for and execute any pending command menu action."""
        action = self.command_menu.pop_action()
        if action is None:
            return

        if action == "quit":
            raise SystemExit(0)
        elif action == "theme_editor":
            self.command_menu.close()
            self.theme_editor.open(self.state.config)
        elif action == "tune":
            self.command_menu.close()
            self.tune_overlay.active = True
        elif action == "debug":
            self.command_menu.close()
            self.debug_panel.toggle()
        elif action == "toggle_logs":
            self.show_logs = not self.show_logs
            self._configure_menu()
        elif action == "hide":
            self.hide_hud = True
            self.command_menu.close()
        elif action == "export_theme":
            try:
                from hermes_neurovision.export import export_theme
                export_theme(self.theme_name)
            except Exception:
                pass
            self.command_menu.close()
        elif action == "import_theme":
            try:
                from hermes_neurovision.import_theme import scan_and_import
                scan_and_import()
            except Exception:
                pass
            self.command_menu.close()

    def _handle_input(self) -> None:
        while True:
            ch = self.stdscr.getch()
            if ch == -1:
                return

            if ch in (ord("Q"),):
                raise SystemExit(0)

            # Command menu takes priority
            if self.command_menu.active:
                self.command_menu.handle_key(ch)
                continue

            # Theme editor takes priority
            if self.theme_editor.active:
                self.theme_editor.handle_key(ch)
                continue

            # Tune overlay
            if self.tune_overlay.active:
                if self.tune_overlay.handle_key(ch):
                    continue

            # Toggle hide
            if ch == ord("h"):
                self.hide_hud = not self.hide_hud
                continue

            # Toggle mute
            if ch == ord("M"):
                self.tune.sound_enabled = not self.tune.sound_enabled
                continue

            # Toggle fullscreen
            if ch == ord("F"):
                self._fullscreen = not self._fullscreen
                import sys
                if self._fullscreen:
                    sys.stdout.write("\033[?1049h\033[?25l")
                else:
                    sys.stdout.write("\033[?1049l\033[?25h")
                sys.stdout.flush()
                curses.resizeterm(*self.stdscr.getmaxyx())
                continue

            # Open menu
            if ch == ord("m"):
                self._configure_menu()
                self.command_menu.open()
                continue

            # Direct shortcuts
            if ch == ord("e"):
                self.theme_editor.open(self.state.config)
                continue
            if ch == ord("t"):
                self.tune_overlay.active = True
                continue
            if ch == ord("d"):
                self.debug_panel.toggle()
            if ch == ord("l"):
                self.show_logs = not self.show_logs
            if ch == ord("q"):
                raise SystemExit(0)
            if ch == ord(" "):
                pass  # pause not yet wired


class DaemonApp:
    """Daemon mode — gallery when idle, switches to live on events."""

    def __init__(self, stdscr: "curses._CursesWindow", themes: Sequence[str], theme_seconds: float, poller, bridge, log_overlay, show_logs: bool = False, quiet: bool = False) -> None:
        self.stdscr = stdscr
        self.themes = list(themes)
        self.theme_seconds = max(1.0, theme_seconds)
        self.poller = poller
        self.bridge = bridge
        self.log_overlay = log_overlay
        self.show_logs = show_logs
        self.quiet = quiet
        self.hide_hud = False
        self._fullscreen = False
        self.renderer = Renderer(stdscr)
        self.command_menu = CommandMenu()
        self.theme_editor = ThemeEditor()
        self.tune = TuneSettings()
        self.tune_overlay = TuneOverlay(self.tune)
        self.debug_panel = DebugPanel()

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
        self._configure_menu()

    def _configure_menu(self) -> None:
        self.command_menu.configure(
            "daemon",
            show_logs=lambda: self.show_logs,
            quiet=lambda: self.quiet,
        )

    def _make_gallery_state(self, theme_name: str) -> ThemeState:
        h, w = self.stdscr.getmaxyx()
        config = build_theme_config(theme_name)
        config = apply_custom_overrides(config)
        state = ThemeState(config, w, h, seed=(hash(theme_name) & 0xFFFF), quiet=False)
        state.tune = self.tune
        return state

    def _make_live_state(self) -> ThemeState:
        h, w = self.stdscr.getmaxyx()
        config = build_theme_config(self.selected_theme_name)
        config = apply_custom_overrides(config)
        state = ThemeState(config, w, h, seed=hash(self.selected_theme_name) & 0xFFFF, quiet=self.quiet)
        state.tune = self.tune
        return state

    def run(self) -> None:
        curses.curs_set(0)
        self.stdscr.nodelay(True)

        try:
            while True:
                now = time.time()
                self._handle_input()
                self._process_menu_action()

                # Poll for events every ~5 frames
                self._poll_counter += 1
                if self._poll_counter >= 5:
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
                                self.debug_panel.record_trigger(trigger, source_event=ev)
                            self.debug_panel.record_event(ev)
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
                    self._draw_gallery(now)
                else:  # live mode
                    if self.live_state:
                        self.live_state.step()
                    self._draw_live(now)

                self.stdscr.refresh()
                time.sleep(FRAME_DELAY / max(0.1, self.tune.animation_speed))
        finally:
            if self._fullscreen:
                import sys
                sys.stdout.write("\033[?1049l\033[?25h")
                sys.stdout.flush()

    def _transition_to_live(self) -> None:
        """Transition from gallery to live mode."""
        self.mode = "live"
        # Preserve selected theme from gallery
        self.selected_theme_name = self.themes[self.theme_index]
        self.live_state = self._make_live_state()
        self.last_event_time = time.time()
        self._configure_menu()

    def _transition_to_gallery(self) -> None:
        """Transition from live to gallery mode."""
        self.mode = "gallery"
        self.last_event_time = None
        # Reset gallery state to current theme
        self.gallery_state = self._make_gallery_state(self.themes[self.theme_index])
        self.switch_at = time.time() + self.theme_seconds if len(self.themes) > 1 else float("inf")
        self._configure_menu()

    def _advance_theme(self, direction: int) -> None:
        """Advance to next/previous theme in gallery mode."""
        self.theme_index = (self.theme_index + direction) % len(self.themes)
        self.gallery_state = self._make_gallery_state(self.themes[self.theme_index])
        self.switch_at = time.time() + self.theme_seconds

    def _current_state(self) -> ThemeState:
        """Return the currently active state (gallery or live)."""
        if self.mode == "live" and self.live_state:
            return self.live_state
        return self.gallery_state

    def _draw_gallery(self, now: float) -> None:
        """Draw gallery mode with indicator."""
        h, w = self.stdscr.getmaxyx()
        self.renderer.draw(self.gallery_state, self.theme_index, len(self.themes), None,
                          hide_hud=self.hide_hud)

        if self.hide_hud:
            self._draw_modals()
            return

        # Draw mode indicator
        mode_text = " DAEMON: gallery "
        try:
            self.stdscr.addstr(0, w - len(mode_text) - 1, mode_text, curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass

        # Footer
        footer = f" theme {self.theme_index + 1}/{len(self.themes)} | Q quit  ←/→ nav  m menu  h hide"
        try:
            self.stdscr.addstr(h - 1, 1, footer[:max(0, w - 2)], curses.color_pair(2) | curses.A_DIM)
        except curses.error:
            pass

        self._draw_modals()

    def _draw_live(self, now: float) -> None:
        """Draw live mode with indicator and optional logs."""
        h, w = self.stdscr.getmaxyx()
        if self.live_state:
            self.renderer.draw(self.live_state, 0, 1, None, hide_hud=self.hide_hud)

        if self.hide_hud:
            self._draw_modals()
            return

        # Draw mode indicator
        mode_text = " DAEMON: live "
        try:
            self.stdscr.addstr(0, w - len(mode_text) - 1, mode_text, curses.color_pair(5) | curses.A_BOLD)
        except curses.error:
            pass

        # Draw log overlay if enabled (but not when menu is open — menu supersedes)
        if self.show_logs and not self.command_menu.active:
            self._draw_logs(now)

        # Footer
        footer = f" Q quit  m menu  h hide  l logs  e editor"
        try:
            self.stdscr.addstr(h - 1, 1, footer[:max(0, w - 2)], curses.color_pair(2) | curses.A_DIM)
        except curses.error:
            pass

        self._draw_modals()

    def _draw_modals(self) -> None:
        """Draw modal overlays (menu supersedes others)."""
        if self.command_menu.active:
            self.command_menu.draw(self.stdscr, self.renderer.color_pairs)
        elif self.theme_editor.active:
            self.theme_editor.draw(self.stdscr, self.renderer.color_pairs)
        elif self.tune_overlay.active:
            self.tune_overlay.draw(self.stdscr, self.renderer.color_pairs)
        if self.debug_panel.visible and not self.command_menu.active:
            self.debug_panel.draw(self.stdscr, self._current_state(), self.renderer.color_pairs)

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
            elif brightness == "dim":
                attr |= curses.A_DIM
            # "normal" — no modifier, just the color
            try:
                self.stdscr.addstr(y, 1, text[:w - 2], attr)
            except curses.error:
                pass

    def _process_menu_action(self) -> None:
        """Check for and execute any pending command menu action."""
        action = self.command_menu.pop_action()
        if action is None:
            return

        current_state = self._current_state()

        if action == "quit":
            raise SystemExit(0)
        elif action == "theme_editor":
            self.command_menu.close()
            self.theme_editor.open(current_state.config)
        elif action == "tune":
            self.command_menu.close()
            self.tune_overlay.active = True
        elif action == "debug":
            self.command_menu.close()
            self.debug_panel.toggle()
        elif action == "toggle_logs":
            self.show_logs = not self.show_logs
            self._configure_menu()
        elif action == "toggle_quiet":
            self.quiet = not self.quiet
            if self.gallery_state:
                self.gallery_state.quiet = self.quiet
            if self.live_state:
                self.live_state.quiet = self.quiet
            self._configure_menu()
        elif action == "hide":
            self.hide_hud = True
            self.command_menu.close()
        elif action == "export_theme":
            try:
                from hermes_neurovision.export import export_theme
                theme_name = self.themes[self.theme_index]
                export_theme(theme_name)
            except Exception:
                pass
            self.command_menu.close()
        elif action == "import_theme":
            try:
                from hermes_neurovision.import_theme import scan_and_import
                scan_and_import()
            except Exception:
                pass
            self.command_menu.close()

    def _handle_input(self) -> None:
        """Handle keyboard input."""
        while True:
            ch = self.stdscr.getch()
            if ch == -1:
                return

            if ch == ord("Q"):
                raise SystemExit(0)

            # Command menu takes priority
            if self.command_menu.active:
                self.command_menu.handle_key(ch)
                continue

            # Theme editor takes priority
            if self.theme_editor.active:
                self.theme_editor.handle_key(ch)
                continue

            # Tune overlay
            if self.tune_overlay.active:
                if self.tune_overlay.handle_key(ch):
                    continue

            # Toggle hide
            if ch == ord("h"):
                self.hide_hud = not self.hide_hud
                continue

            # Toggle mute
            if ch == ord("M"):
                self.tune.sound_enabled = not self.tune.sound_enabled
                continue

            # Toggle fullscreen
            if ch == ord("F"):
                self._fullscreen = not self._fullscreen
                import sys
                if self._fullscreen:
                    sys.stdout.write("\033[?1049h\033[?25l")
                else:
                    sys.stdout.write("\033[?1049l\033[?25h")
                sys.stdout.flush()
                curses.resizeterm(*self.stdscr.getmaxyx())
                continue

            # Open menu
            if ch == ord("m"):
                self._configure_menu()
                self.command_menu.open()
                continue

            # Direct shortcuts
            if ch == ord("e"):
                self.theme_editor.open(self._current_state().config)
                continue
            if ch == ord("t"):
                self.tune_overlay.active = True
                continue

            if ch == ord("q"):
                self.quiet = not self.quiet
                if self.gallery_state:
                    self.gallery_state.quiet = self.quiet
                if self.live_state:
                    self.live_state.quiet = self.quiet
            if ch == ord("d"):
                self.debug_panel.toggle()
            if ch == ord("l"):
                self.show_logs = not self.show_logs
            if self.mode == "gallery":
                if ch in (curses.KEY_RIGHT, ord("n")):
                    self._advance_theme(1)
                elif ch in (curses.KEY_LEFT, ord("p")):
                    self._advance_theme(-1)
