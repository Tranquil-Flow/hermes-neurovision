# Overlay Mode — CLI-Over-Scene Terminal Compositor

**Date:** 2026-03-16
**Status:** Draft
**Goal:** Run neurovision scenes as a background visual layer while the user types in a CLI (hermes-agent or any shell) in the same terminal. Text fades to transparent toward the top of the screen, revealing the scene behind it.

---

## 1. Architecture

A single `OverlayApp` class owns the curses terminal, a PTY-hosted child process, a minimal VT100 terminal emulator, and the existing scene/event engine. Each frame:

1. Poll PTY for child output → feed to VT emulator
2. Poll event sources → bridge → visual triggers
3. Step scene (theme state, particles, post-fx)
4. Render scene via `Renderer.draw()` with `skip_refresh=True` and `hide_hud=True` — this writes everything to `stdscr` (buffer blit + overlay effects + specials) but suppresses the existing HUD (which would conflict with the overlay's own status bar)
5. Composite: read `stdscr` scene state, overlay VT text with fade gradient, write back to `stdscr`
6. Draw overlay status bar (bottom row) — replaces the suppressed HUD
7. `stdscr.refresh()`

Note: The existing `Renderer.draw()` writes overlay effects and specials directly to `stdscr` after the buffer blit (not into the FrameBuffer). Rather than refactoring the renderer, the compositor reads the fully-rendered scene from `stdscr` via `stdscr.inch(y, x)` and composites text on top. This means the compositor operates on the final rendered scene including all effects. The existing HUD is suppressed via `hide_hud=True` because `OverlayApp` draws its own status bar with overlay-specific info (mode, child command, Ctrl+N hint).

```
┌──────────────────────────────────────────────┐
│              OverlayApp (curses)              │
│                                              │
│  ┌───────────┐      ┌─────────────────────┐  │
│  │ PTY       │      │ Scene Engine        │  │
│  │ Master FD │      │ ThemeState + Poller  │  │
│  │           │      │ + Bridge + Renderer  │  │
│  │ Spawns:   │      │                     │  │
│  │ shell /   │      │ Renders to          │  │
│  │ hermes    │      │ FrameBuffer         │  │
│  └─────┬─────┘      └──────────┬──────────┘  │
│        │                       │              │
│  ┌─────▼─────┐      ┌─────────▼──────────┐  │
│  │ VTScreen  │─────►│ FadeCompositor     │  │
│  │ (vt.py)   │      │                    │  │
│  │           │      │ scene cell (bg)    │  │
│  │ char grid │      │ text cell (fg)     │  │
│  │ + cursor  │      │ fade mask (alpha)  │  │
│  └───────────┘      └─────────┬──────────┘  │
│                               │              │
│                      ┌────────▼──────────┐  │
│                      │ stdscr.refresh()  │  │
│                      └──────────────────┘  │
└──────────────────────────────────────────────┘
```

All stdlib — `pty`, `os`, `select`, `fcntl`, `signal`, `struct`, `curses`.

---

## 2. New Modules

### 2.1 `hermes_neurovision/vt.py` — Minimal VT100 Emulator

Maintains a grid of cells representing the child process's terminal output.

```python
@dataclass
class VTCell:
    char: str = " "
    bold: bool = False
    fg: int = 7  # ANSI color 0-7
    born_frame: int = 0  # frame when this cell was last written (for age-based fading)

class VTScreen:
    def __init__(self, rows: int, cols: int, scrollback_limit: int = 200):
        self.rows = rows
        self.cols = cols
        self.cells: list[list[VTCell]]  # rows x cols
        self.cursor_row: int = 0
        self.cursor_col: int = 0
        self.scrollback: deque[list[VTCell]]

    def feed(self, data: bytes) -> None:
        """Parse raw bytes from PTY, update cell grid and cursor."""

    def resize(self, rows: int, cols: int) -> None:
        """Handle terminal resize."""
```

**Supported sequences:**
- Printable characters (write at cursor, advance)
- `\n` (newline + scroll if at bottom), `\r` (carriage return), `\b` (backspace), `\t` (tab to next 8-col stop)
- CSI cursor movement: `A` (up), `B` (down), `C` (right), `D` (left), `H` (position), `J` (erase display), `K` (erase line)
- CSI SGR: `0` (reset), `1` (bold), `22` (no bold), `30-37` (fg color), `39` (default fg)
- Line wrapping at right margin
- Scroll region: entire screen (no split scroll regions)

**Alternate screen buffer handling:**
- Many CLI tools (vim, less, htop) switch to the alternate screen buffer via `\x1b[?1049h` and restore via `\x1b[?1049l`.
- `hermes chat` uses standard line-based I/O (not curses), so this is not a blocker for the primary use case.
- The VT emulator recognizes these sequences and silently ignores them (does not switch buffers). Output from alt-screen programs will render inline in the main grid — potentially garbled, but it won't crash. This is an acceptable degradation for a v1.
- If a child program is known to use alt-screen (e.g., `vim`), the user should use `--cmd` to run their shell and launch such programs there, understanding the limitation.

**Not supported** (YAGNI):
- Mouse events, bracketed paste mode
- Full alternate screen buffer switching (sequences recognized but ignored)
- 256-color / truecolor (map to nearest basic color)
- Unicode combining characters
- OSC sequences (title changes, etc.)

### 2.2 `hermes_neurovision/compositor.py` — Fade Compositor

Blends the scene FrameBuffer with the VT text grid using a configurable fade function.

```python
@dataclass
class FadeConfig:
    mode: str = "position"          # "position", "age", "both"
    fade_start_pct: float = 0.0     # row % where fade begins (0.0 = top)
    fade_end_pct: float = 0.4       # row % where text is fully opaque
    text_opacity: float = 1.0       # global text brightness 0.0-1.0
    text_bg: str = "transparent"    # "transparent" or "dim"

class FadeCompositor:
    def __init__(self, config: FadeConfig):
        self.config = config

    def composite(
        self,
        stdscr,
        vt_screen: VTScreen,
        color_pairs: dict,
        current_frame: int = 0,
    ) -> None:
        """Overlay VT text onto the already-rendered scene on stdscr.

        The scene (including overlay effects and specials) has already been
        drawn to stdscr by Renderer.draw(skip_refresh=True). This method
        reads the scene state from stdscr via inch(), then overwrites cells
        where VT text should be visible based on the fade function.
        """
```

**Fade function** (position mode):
```
opacity(y, h) = clamp((y - fade_start_row) / max(fade_end_row - fade_start_row, 1), 0.0, 1.0)
```

Where `fade_start_row = h * fade_start_pct` and `fade_end_row = h * fade_end_pct`. The `max(..., 1)` prevents division by zero when `fade_start_pct == fade_end_pct` (all text renders at full opacity in that case).

**Opacity → curses attribute mapping:**

| Opacity | Curses attribute | Visual |
|---------|-----------------|--------|
| 0.0–0.15 | (hidden) | Scene shows through |
| 0.15–0.4 | `A_DIM` | Ghostly text, scene visible |
| 0.4–0.7 | `A_NORMAL` | Readable text |
| 0.7–1.0 | `A_BOLD` | Bright text |

**Age mode:** Each VTCell gets a `born_frame` timestamp. Opacity = `1.0 - (current_frame - born_frame) / fade_lifetime`. Combined mode multiplies position and age opacities.

**`text_bg: "dim"`:** Darken scene cells behind visible text by rendering them with `A_DIM` for improved readability.

### 2.3 `hermes_neurovision/overlay.py` — OverlayApp

The main application class for overlay mode. Owns the PTY, VT screen, scene delegate, and compositor.

```python
class OverlayApp:
    def __init__(
        self,
        stdscr,
        child_cmd: list[str],
        themes: list[str],
        theme_seconds: int,
        mode: str,           # "daemon", "gallery", "live"
        fade_config: FadeConfig,
        poller: EventPoller | None,
        bridge: Bridge | None,
        **kwargs,
    ):
        self.stdscr = stdscr
        self.pty_master: int       # PTY file descriptor
        self.child_pid: int
        self.vt: VTScreen
        self.compositor: FadeCompositor
        self.scene_delegate: GalleryApp | LiveApp | DaemonApp
        self.nv_mode: bool = False
        self.prefix_pending: bool = False

    def run(self) -> None:
        """Main loop."""

    def _spawn_child(self, cmd: list[str]) -> tuple[int, int]:
        """Fork PTY, exec child, return (master_fd, pid)."""

    def _poll_pty(self) -> None:
        """Non-blocking read from PTY, feed to VTScreen."""

    def _route_input(self) -> None:
        """Read curses input, route to PTY or neurovision controls."""

    def _step_frame(self) -> None:
        """Step scene, composite, refresh."""

    def _switch_mode(self, mode: str) -> None:
        """Switch scene delegate between gallery/live/daemon."""
```

**PTY lifecycle:**
1. `pty.fork()` creates master fd + forks (handles setsid, dup2 of slave to stdin/stdout/stderr, and closing master in child automatically)
2. Child: set `TERM=vt100` in environment, `ioctl` master fd to set terminal size (propagates to slave), `os.execvp(cmd)`
3. Parent: set master fd non-blocking via `fcntl` (`pty.fork()` already closes the slave fd in the parent, ensuring proper EOF detection when child exits)
4. `SIGWINCH` handler: resize VT screen + `ioctl(TIOCSWINSZ)` on master fd (propagates to slave) + `SIGWINCH` to child pid
5. `SIGCHLD` or EOF on master: child exited

**Child environment:** `TERM` is set to `vt100` so the child and programs it runs (readline, less, etc.) only emit sequences our VT emulator supports. `SHELL`, `HOME`, `PATH`, `USER` are inherited from the parent.

**Main loop (50ms frames):**
```python
while self.running:
    self._route_input()        # curses getch → PTY or NV controls
    self._poll_pty()           # read child output → VT
    self._step_scene()         # event poll + scene step
    self._composite()          # scene buffer + VT → screen
    self.stdscr.refresh()
    time.sleep(FRAME_DELAY)
```

---

## 3. Input Handling

### 3.1 Key Routing

All input goes to the PTY by default. `Ctrl+N` (0x0E) is the prefix key.

```python
def _route_input(self):
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
```

### 3.2 Prefix Commands (`Ctrl+N` then key)

| Key | Action |
|-----|--------|
| `t` | Next theme |
| `T` | Previous theme |
| `f` | Cycle fade mode (position → age → both) |
| `d` | Toggle debug panel |
| `1` | Daemon mode |
| `2` | Gallery mode |
| `3` | Live mode |
| `m` | Enter neurovision mode (extended controls) |
| `q` | Quit overlay |
| `Ctrl+N` | Send literal Ctrl+N to PTY |

### 3.3 Neurovision Mode

Entered via `Ctrl+N m`. All keys route to neurovision controls (theme navigation, tuner sliders, etc.). Reuses existing `_handle_key()` logic from `GalleryApp`.

Status bar shows `[NV MODE — Esc to exit]`.

Exit with `Esc` or `Ctrl+N`.

---

## 4. Event Integration

### 4.1 Existing Sources

The existing event poller (state.db, events.jsonl, memories, cron, aegis) works unchanged. The child hermes process writes to the same files, neurovision's poller picks them up.

### 4.2 VT Event Source

New source `hermes_neurovision/sources/vt_source.py` that observes terminal activity:

```python
class VTEventSource:
    def __init__(self, vt_screen: VTScreen):
        self.vt = vt_screen
        self._last_output_frame: int = 0

    def poll(self) -> list[VisionEvent]:
        events = []
        if self.vt.bytes_since_last_poll > 0:
            events.append(VisionEvent(
                kind="vt_output",
                timestamp=time.time(),
                source="vt",
                data={"bytes": self.vt.bytes_since_last_poll},
            ))
        return events
```

Events emitted:
- `vt_output` — child process printed text. Intensity scales with byte count.
- `vt_scroll` — screen scrolled. Triggers ripple effect.

These register in the bridge with low-intensity defaults so they add subtle ambiance without overwhelming the hermes-specific triggers.

---

## 5. Scene Mode Switching

`OverlayApp` holds a scene delegate that can be swapped at runtime.

The existing `GalleryApp`, `LiveApp`, and `DaemonApp` are full app classes that own the curses loop, input handling, and screen refresh. We do NOT refactor them — they remain standalone for their existing modes.

Instead, `OverlayApp` creates new lightweight **`SceneDelegate`** classes that extract only the scene-stepping logic:

```python
class SceneDelegate:
    """Base: steps scene state each frame. No curses, no input, no refresh."""
    def step(self, state: ThemeState) -> None: ...
    def should_switch_theme(self) -> bool: ...

class GalleryDelegate(SceneDelegate):
    """Rotates themes on timer, generates synthetic activity."""
    def __init__(self, themes, theme_seconds, ...): ...

class LiveDelegate(SceneDelegate):
    """Polls events, applies triggers. Single theme."""
    def __init__(self, theme, poller, bridge, ...): ...

class DaemonDelegate(SceneDelegate):
    """Gallery when idle, switches to live on real events."""
    def __init__(self, themes, theme_seconds, poller, bridge, ...): ...
```

These delegates reuse the same stepping/polling logic from the existing apps but without owning curses or calling `stdscr.refresh()`. They live in `overlay.py` alongside `OverlayApp`.

```python
def _switch_mode(self, mode: str):
    if mode == self.current_mode:
        return
    self.current_mode = mode
    if mode == "daemon":
        self.delegate = DaemonDelegate(self.themes, ...)
    elif mode == "gallery":
        self.delegate = GalleryDelegate(self.themes, ...)
    elif mode == "live":
        self.delegate = LiveDelegate(self.theme, ...)
```

Default: `daemon`. Switchable via `Ctrl+N 1/2/3`.

---

## 6. CLI Interface

```bash
# Spawn shell with neurovision background
neurovision --overlay

# Spawn specific command
neurovision --overlay --cmd "hermes chat"

# Quick hermes shortcut
neurovision --cli

# With options
neurovision --cli --theme aurora-borealis --fade-end 0.5 --mode live

# Fade customization
neurovision --cli --fade-mode position  # default
neurovision --cli --fade-mode age
neurovision --cli --fade-mode both
neurovision --cli --fade-start 0.0 --fade-end 0.6  # more opaque area
neurovision --cli --text-bg dim                      # darken scene behind text
```

`--cli` is sugar for `--overlay --cmd "hermes chat"`. If `hermes-aegis` is on PATH and `--aegis` is passed, uses `hermes-aegis run -- hermes chat`.

### Arguments added to `cli.py`:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--overlay` | store_true | False | Enable overlay mode (spawn PTY) |
| `--cli` | store_true | False | Shortcut: overlay + hermes chat |
| `--cmd` | str | user's $SHELL | Command to spawn in PTY |
| `--mode` | choice | "daemon" | Scene mode: daemon/gallery/live |
| `--fade-mode` | choice | "position" | Fade type: position/age/both |
| `--fade-start` | float | 0.0 | Fade start position (0.0 = top) |
| `--fade-end` | float | 0.4 | Fade end position (fully opaque below) |
| `--text-opacity` | float | 1.0 | Global text brightness |
| `--text-bg` | choice | "transparent" | Text background: transparent/dim |

---

## 7. Status Bar

Bottom row of terminal, always visible:

```
[aurora-borealis] [daemon] [hermes chat] [Ctrl+N: controls]
```

When in neurovision mode:
```
[aurora-borealis] [NV MODE] [↑↓←→ tune | t theme | Esc exit]
```

Status bar occupies 1 row. Both scene and text rendering exclude this row.

---

## 8. Lifecycle & Edge Cases

**Startup:**
1. `curses.wrapper()` inits terminal
2. Spawn PTY with child command
3. Init VT screen, scene engine, compositor, event poller
4. Enter main loop

**Child exit:**
- Detect via `os.waitpid(WNOHANG)` or EOF on PTY master
- Display `[Process exited: code N]` in status bar
- Auto-exit after 3 seconds, or wait for `Ctrl+N q`

**Terminal resize (`SIGWINCH`):**
- Resize curses via `curses.resizeterm()`
- Resize VT screen (reflow text)
- Propagate to child via `ioctl(TIOCSWINSZ)` on master fd (propagates to slave) + `SIGWINCH` to child pid

**Ctrl+C:**
- Forwarded to PTY child (it's a normal `SIGINT` to the child process)
- Does NOT quit neurovision — only `Ctrl+N q` quits

---

## 9. Files Changed

| File | Action | Description |
|------|--------|-------------|
| `hermes_neurovision/vt.py` | **New** | VT100 terminal emulator (~300 lines) |
| `hermes_neurovision/compositor.py` | **New** | Fade compositor (~150 lines) |
| `hermes_neurovision/overlay.py` | **New** | OverlayApp main class (~350 lines) |
| `hermes_neurovision/sources/vt_source.py` | **New** | VT event source (~40 lines) |
| `hermes_neurovision/cli.py` | **Modify** | Add --overlay/--cli/--cmd/--fade-* flags, dispatch to OverlayApp |
| `hermes_neurovision/bridge.py` | **Modify** | Add vt_output/vt_scroll trigger mappings |
| `tests/test_vt.py` | **New** | VT emulator tests (~200 lines) |
| `tests/test_compositor.py` | **New** | Compositor tests (~100 lines) |
| `tests/test_overlay.py` | **New** | OverlayApp integration tests (~150 lines) |

**Estimated total: ~1300 lines of implementation + tests.**

---

## 10. What We Are NOT Doing

- Full xterm emulation (no mouse, no alt screen, no 256-color)
- Running multiple PTY sessions (tabs/splits)
- Persistent scrollback / scroll-up through history
- Recording/replaying terminal sessions
- Custom font rendering or image protocol support (iTerm2 inline images, sixel)
