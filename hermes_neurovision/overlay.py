"""Overlay mode — CLI-over-scene terminal compositor.

OverlayApp renders neurovision scenes in the background while a PTY-hosted
child process (shell or hermes-agent) runs in the foreground. Text fades
toward the top of the screen, revealing the scene behind it.
"""

from __future__ import annotations

import curses
import fcntl
import os
import pty
import random
import select
import signal
import struct
import sys
import time
from typing import TYPE_CHECKING, Optional, Sequence

from hermes_neurovision.compositor import FadeConfig, FadeCompositor
from hermes_neurovision.vt import VTScreen
from hermes_neurovision.themes import build_theme_config, THEMES, FRAME_DELAY
from hermes_neurovision.scene import ThemeState
from hermes_neurovision.renderer import Renderer

if TYPE_CHECKING:
    from hermes_neurovision.bridge import Bridge, VisualTrigger
    from hermes_neurovision.events import EventPoller

_MODES = ("daemon", "gallery", "live")
_TEXT_COLORS = ("native", "auto", "theme", "white", "green", "cyan", "magenta", "yellow", "red")
_GLOW_COLORS = ("theme", "white", "green", "cyan", "magenta", "yellow", "red")
_FADE_MODES = ("position", "age", "both")


# ── Scene Delegates ───────────────────────────────────────────────────────


class SceneDelegate:
    """Base: steps scene state each frame. No curses, no input, no refresh."""

    def step(self, state: ThemeState, now: float) -> None:
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

    def step(self, state: ThemeState, now: float) -> None:
        self._simulate_activity(state, now)
        state.step()

    def should_switch_theme(self, now: float) -> bool:
        return now >= self._switch_at

    def _simulate_activity(self, state: ThemeState, now: float) -> None:
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

    def step(self, state: ThemeState, now: float) -> None:
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

    def step(self, state: ThemeState, now: float) -> None:
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


# ── OverlayApp ────────────────────────────────────────────────────────────


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

        # VT screen (sized to terminal, -1 for status bar)
        h, w = stdscr.getmaxyx()
        self.vt = VTScreen(h - 1, w)

        # Wire VT event source into poller
        if self.poller is not None:
            from hermes_neurovision.sources.vt_source import VTEventSource
            vt_source = VTEventSource(self.vt)
            self.poller._sources.append(vt_source.poll)

        # Performance mode — enabled by default for smooth overlay experience
        from hermes_neurovision.tune import TuneSettings
        from hermes_neurovision.app import _apply_performance_mode
        self.tune = TuneSettings()
        _apply_performance_mode(self.tune, True)

        # Scene state
        self.state = self._make_state(self.themes[self.theme_index])

        # Scene delegate
        self.delegate = self._make_delegate(mode)

    def _make_state(self, theme_name: str) -> ThemeState:
        h, w = self.stdscr.getmaxyx()
        config = build_theme_config(theme_name)
        state = ThemeState(config, w, h, seed=hash(theme_name) & 0xFFFF)
        state.tune = self.tune
        return state

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

        # Disable alternate screen scroll — on macOS, trackpad scroll in
        # alternate screen mode (which curses uses) sends arrow key escape
        # sequences that get forwarded to the PTY, cycling shell history.
        # These xterm sequences disable that behavior:
        sys.stdout.buffer.write(b"\x1b[?1007l")  # disable alternate scroll
        sys.stdout.buffer.write(b"\x1b[?1003l")  # disable all mouse tracking
        sys.stdout.buffer.flush()

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
        """Fork a PTY and exec the child command.

        Sets terminal size on the PTY master fd BEFORE the child shell
        reads its dimensions, then sends SIGWINCH to force a re-read.
        This avoids a race where the shell sees the default 80x24 size.
        """
        import termios

        h, w = self.stdscr.getmaxyx()
        child_rows = h - 1  # reserve bottom row for status bar

        pid, master_fd = pty.fork()
        if pid == 0:
            # Child process — do NOT access self.stdscr (curses is parent-only)
            os.environ["TERM"] = "xterm-256color"
            os.environ["COLUMNS"] = str(w)
            os.environ["LINES"] = str(child_rows)
            try:
                os.execvp(self.child_cmd[0], self.child_cmd)
            except OSError:
                os._exit(127)
        else:
            # Parent process
            self.child_pid = pid
            self.pty_master = master_fd

            # Set terminal size IMMEDIATELY — before child shell starts
            winsize = struct.pack("HHHH", child_rows, w, 0, 0)
            try:
                fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
            except OSError:
                pass

            # Send SIGWINCH so child re-reads terminal size if it already started
            try:
                os.kill(pid, signal.SIGWINCH)
            except OSError:
                pass

            # Set non-blocking for polling
            flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
            fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

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
            self.renderer.draw(self.state, self.theme_index, len(self.themes),
                              None, hide_hud=True, skip_refresh=True)

            # Composite text over scene
            h, w = self.stdscr.getmaxyx()
            self.compositor.composite(
                self.stdscr, self.vt, self.renderer.color_pairs,
                current_frame=frame, status_row=h - 1
            )

            # Status bar
            self._draw_status_bar()

            self.stdscr.refresh()
            frame += 1
            time.sleep(FRAME_DELAY)

    # ── PTY I/O ───────────────────────────────────────────────────────────

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

    def _write_pty(self, ch: int) -> None:
        """Forward a keypress to the PTY child."""
        if self.pty_master is None or self.child_exited:
            return

        # Filter out mouse events and resize — don't forward to PTY
        if ch == curses.KEY_MOUSE:
            return
        if ch == curses.KEY_RESIZE:
            return
        # Filter scroll wheel (some terminals send these as key events)
        if ch in (curses.KEY_SR, curses.KEY_SF):  # scroll reverse/forward
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
            # Ignore other high keycodes (function keys, etc.) unless mapped
        except OSError:
            pass

    # ── Input routing ─────────────────────────────────────────────────────

    def _route_input(self) -> None:
        """Read curses input and route to PTY or neurovision controls.

        Prefix key: Ctrl+B (0x02). Works reliably on macOS Terminal.app and iTerm2.
        Ctrl+N (0x0E) also supported as alternative.
        """
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
            elif ch == 0x02 or ch == 0x0E:  # Ctrl+B or Ctrl+N
                self.prefix_pending = True
            else:
                self._write_pty(ch)

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
        elif c == "G":
            # Cycle glow color
            idx = _GLOW_COLORS.index(self.fade_config.text_glow_color) if self.fade_config.text_glow_color in _GLOW_COLORS else 0
            self.fade_config.text_glow_color = _GLOW_COLORS[(idx + 1) % len(_GLOW_COLORS)]
        elif c == "+":
            # Increase glow intensity
            self.fade_config.text_glow_intensity = min(1.0, self.fade_config.text_glow_intensity + 0.1)
        elif c == "-":
            # Decrease glow intensity
            self.fade_config.text_glow_intensity = max(0.0, self.fade_config.text_glow_intensity - 0.1)
        elif c == "c":
            idx = _TEXT_COLORS.index(self.fade_config.text_color) if self.fade_config.text_color in _TEXT_COLORS else 0
            self.fade_config.text_color = _TEXT_COLORS[(idx + 1) % len(_TEXT_COLORS)]
        elif c == "[":
            self.fade_config.text_bg_opacity = max(0.0, self.fade_config.text_bg_opacity - 0.1)
        elif c == "]":
            self.fade_config.text_bg_opacity = min(1.0, self.fade_config.text_bg_opacity + 0.1)
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
        elif ch == 0x02 or ch == 0x0E:  # double-tap → send literal to PTY
            self._write_pty(ch)

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
        elif c == "G":
            idx = _GLOW_COLORS.index(self.fade_config.text_glow_color) if self.fade_config.text_glow_color in _GLOW_COLORS else 0
            self.fade_config.text_glow_color = _GLOW_COLORS[(idx + 1) % len(_GLOW_COLORS)]
        elif c == "c":
            idx = _TEXT_COLORS.index(self.fade_config.text_color) if self.fade_config.text_color in _TEXT_COLORS else 0
            self.fade_config.text_color = _TEXT_COLORS[(idx + 1) % len(_TEXT_COLORS)]

    # ── Theme / mode control ──────────────────────────────────────────────

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

    # ── Status bar ────────────────────────────────────────────────────────

    def _draw_status_bar(self) -> None:
        """Draw status bar on the bottom row."""
        h, w = self.stdscr.getmaxyx()
        y = h - 1

        theme_name = self.themes[self.theme_index] if self.themes else "?"

        if self.prefix_pending:
            bar = f" [{theme_name}] [CTRL+B pressed — t:theme g:glow c:color [/]:bg 1/2/3:mode m:menu q:quit] "
        elif self.nv_mode:
            bar = f" [{theme_name}] [NV MODE] [t/T theme | f fade | g glow | G glow-color | +/- intensity | c color | Esc exit] "
        elif self.child_exited:
            code = self.exit_code if self.exit_code is not None else "?"
            bar = f" [{theme_name}] [Process exited: {code}] [Ctrl+N q to quit] "
        else:
            cmd_str = " ".join(self.child_cmd)
            mode_str = self.current_mode
            extras = []
            if self.fade_config.text_glow:
                extras.append(f"glow:{self.fade_config.text_glow_color}")
            if self.fade_config.text_color != "auto":
                extras.append(self.fade_config.text_color)
            extra_str = " " + " ".join(extras) if extras else ""
            bar = f" [{theme_name}] [{mode_str}] [{cmd_str}]{extra_str} [Ctrl+B: controls] "

        bar = bar[:w - 1]
        try:
            self.stdscr.addstr(y, 0, bar.ljust(w - 1),
                              curses.color_pair(self.renderer.color_pairs.get("soft", 2)) | curses.A_BOLD)
        except curses.error:
            pass

    # ── Resize / cleanup ──────────────────────────────────────────────────

    def _handle_resize(self) -> None:
        """Handle terminal resize."""
        try:
            size = os.get_terminal_size()
            new_h, new_w = size.lines, size.columns
        except OSError:
            return
        curses.resizeterm(new_h, new_w)
        self.vt.resize(new_h - 1, new_w)
        self.state.resize(new_w, new_h)
        # Propagate to child PTY
        if self.pty_master is not None:
            import termios
            winsize = struct.pack("HHHH", new_h - 1, new_w, 0, 0)
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
