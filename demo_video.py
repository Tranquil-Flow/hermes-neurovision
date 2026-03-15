#!/usr/bin/env python3
"""
demo_video.py — Hermes Neurovision Demo Sequence (~90 seconds)

Plays a timed demo using the real theme engine with text overlays in curses.
Run from project venv: python3 demo_video.py
"""

import curses
import time
import sys

from hermes_neurovision.scene import ThemeState
from hermes_neurovision.themes import build_theme_config, FRAME_DELAY
from hermes_neurovision.renderer import Renderer
from hermes_neurovision.tune import TuneSettings
from hermes_neurovision.theme_editor import apply_custom_overrides


# ---------------------------------------------------------------------------
# Boot sequence lines
# ---------------------------------------------------------------------------
BOOT_LINES = [
    "[HERMES NEUROVISION v0.2.0 \u2014 SYSTEM UPDATE]",
    "\u2501" * 51,
    "[CORE]    FrameBuffer off-screen compositing ................ OK",
    "[CORE]    Cell-based render pipeline (char+color+attr+age) .. OK",
    "[CORE]    BufferShim curses-compatible wrapper .............. OK",
    "[CORE]    ThemeState scene simulation engine ................ OK",
    "[CORE]    Node graph generation (cluster layout) ........... OK",
    "[CORE]    Edge graph construction (nearest-neighbor) ....... OK",
    "[CORE]    Particle system (velocity, life, aging, frames) .. OK",
    "[CORE]    Packet system \u2014 glyphs traveling edges ........... OK",
    "[CORE]    Streak system \u2014 directional motion trails ........ OK",
    "[CORE]    Cascade queue \u2014 sequential node-flash chains ..... OK",
    "[CORE]    Dynamic node spawning (up to 64 nodes) ........... OK",
    "[CORE]    VisionEvent unified event model .................. OK",
    "[CORE]    EventPoller \u2014 multi-source aggregator ............ OK",
    "[CORE]    Terminal resize handling (auto rebuild) ........... OK",
    "[PLUGIN]  ThemePlugin base class \u2014 API v1.0 (frozen) ....... OK",
    "[PLUGIN]  30+ overridable methods with safe defaults ....... OK",
    "[PLUGIN]  draw_background() \u2014 ASCII field textures ......... OK",
    "[PLUGIN]  draw_extras() \u2014 foreground overlays .............. OK",
    "[PLUGIN]  draw_overlay_effect() \u2014 event-triggered FX ....... OK",
    "[PLUGIN]  palette_shift() \u2014 dynamic color response ......... OK",
    "[PLUGIN]  effect_zones() \u2014 named rectangular zones ......... OK",
    "[PLUGIN]  intensity_curve() \u2014 custom intensity transform ... OK",
    "[PLUGIN]  ambient_tick() \u2014 idle-time ambient drawing ....... OK",
    "[PLUGIN]  17 theme plugin files loaded ..................... OK",
    "[FX]      Warp field \u2014 displacement mapping ................ OK",
    "[FX]      Void points \u2014 darkness that breathes ............. OK",
    "[FX]      Echo trails \u2014 ghosting persistence ............... OK",
    "[FX]      Glow bloom \u2014 character luminance bleed ........... OK",
    "[FX]      Decay shimmer \u2014 entropy char sequence ............ OK",
    "[FX]      Symmetry mirror \u2014 bilateral/quad reflection ...... OK",
    "[FX]      Mask overlays \u2014 shaped viewport stencils ......... OK",
    "[FX]      Force field \u2014 radial/vortex displacement ......... OK",
    "[FX]      Snapshot buffer \u2014 frame capture for echo ring .... OK",
    "[FX]      Pulse: ring, rays, spoked, ripple, cloud, diamond  OK",
    "[EMRG]    Cellular Automata \u2014 Brian's Brain ................ OK",
    "[EMRG]    Cellular Automata \u2014 Cyclic CA (14 states) ........ OK",
    "[EMRG]    Cellular Automata \u2014 Rule 110 (1D scrolling) ...... OK",
    "[EMRG]    Cellular Automata \u2014 Conway's Game of Life ........ OK",
    "[EMRG]    Physarum slime mold \u2014 150 agents + trail grid .... OK",
    "[EMRG]    Neural field \u2014 excitable medium + cascade fire ... OK",
    "[EMRG]    Wave field \u2014 2D interference + damped propagation  OK",
    "[EMRG]    Boids flocking \u2014 separation/alignment/cohesion ... OK",
    "[EMRG]    Boids \u2014 directional glyph rendering (> \\ v < ^) . OK",
    "[EMRG]    Reaction-Diffusion \u2014 Gray-Scott Turing patterns .. OK",
    "[EMRG]    Emergent layer placement: bg / mid / foreground .. OK",
    "[EMRG]    Emergent speed + opacity controls ................ OK",
    "[REACT]   PULSE \u2014 radial burst, one-shot dramatic .......... OK",
    "[REACT]   RIPPLE \u2014 concentric rings from a point ........... OK",
    "[REACT]   STREAM \u2014 flowing particles, sustained ............ OK",
    "[REACT]   BLOOM \u2014 organic growth, expand + hold + fade ..... OK",
    "[REACT]   SHATTER \u2014 explosion of scattering fragments ...... OK",
    "[REACT]   ORBIT \u2014 persistent rotating elements ............. OK",
    "[REACT]   GAUGE \u2014 bar fill/drain with color thresholds ..... OK",
    "[REACT]   SPARK \u2014 bright flash + lingering afterglow ....... OK",
    "[REACT]   WAVE \u2014 horizontal sweep, transformative .......... OK",
    "[REACT]   GLYPH \u2014 morphing symbol/sigil .................... OK",
    "[REACT]   TRAIL \u2014 path tracing across screen ............... OK",
    "[REACT]   CONSTELLATION \u2014 dots connecting/disconnecting .... OK",
    "[REACT]   24 concurrent reaction cap ....................... OK",
    "[REACT]   35 event kinds mapped to reactive elements ....... OK",
    "[SOUND]   SoundEngine \u2014 zero-dependency audio .............. OK",
    "[SOUND]   Terminal bell (curses.beep) \u2014 cross-platform ..... OK",
    "[SOUND]   Visual bell (curses.flash) \u2014 cross-platform ...... OK",
    "[SOUND]   macOS text-to-speech (Whisper voice) ............. OK",
    "[SOUND]   macOS audio file playback (afplay) ............... OK",
    "[SOUND]   Event-reactive sound cues via plugin API ......... OK",
    "[SOUND]   Cooldown system (0.5s min between same cue) ...... OK",
    "[SOUND]   Volume control (0.0-1.0) ......................... OK",
    "[DATA]    CustomSource \u2014 JSONL file tailer ................. OK",
    "[DATA]    StateDbSource \u2014 SQLite poller (state.db) ......... OK",
    "[DATA]    StateDbSource \u2014 active session tracking .......... OK",
    "[DATA]    StateDbSource \u2014 model switch detection ........... OK",
    "[DATA]    StateDbSource \u2014 token usage delta tracking ....... OK",
    "[DATA]    StateDbSource \u2014 tool burst detection ............. OK",
    "[DATA]    StateDbSource \u2014 tool chain detection ............. OK",
    "[DATA]    MemoriesSource \u2014 filesystem watcher .............. OK",
    "[DATA]    CronSource \u2014 cron job execution poller ........... OK",
    "[DATA]    AegisSource \u2014 security audit trail tailer ........ OK",
    "[DATA]    TrajectoriesSource \u2014 trajectory log tailer ....... OK",
    "[DATA]    DockerTaskSource \u2014 container watcher ............. OK",
    "[DATA]    McpSource \u2014 MCP server connection monitor ........ OK",
    "[DATA]    SkillsSource \u2014 skill file change detector ........ OK",
    "[DATA]    CheckpointsSource \u2014 checkpoint/rollback monitor .. OK",
    "[DATA]    HookHandler \u2014 gateway hook (zero dependencies) ... OK",
    "[DATA]    17 hook event types mapped ....................... OK",
    "[DATA]    51 bridge event-to-trigger mappings .............. OK",
    "[BRIDGE]  Effect: packet (edge traversal) .................. OK",
    "[BRIDGE]  Effect: pulse (node glow) ........................ OK",
    "[BRIDGE]  Effect: burst (particle explosion) ............... OK",
    "[BRIDGE]  Effect: flash (screen flash) ..................... OK",
    "[BRIDGE]  Effect: spawn_node (dynamic creation) ............ OK",
    "[BRIDGE]  Effect: wake / cool_down / dim (intensity) ....... OK",
    "[BRIDGE]  Effect: ripple (multi-ring pulse) ................ OK",
    "[BRIDGE]  Effect: cascade (sequential node chain) .......... OK",
    "[BRIDGE]  Effect: converge (particle convergence) .......... OK",
    "[BRIDGE]  Effect: streak (directional motion trail) ........ OK",
    "[TUNE]    TuneOverlay \u2014 modal slider + toggle panel ........ OK",
    "[TUNE]    13 parameter sliders ............................ OK",
    "[TUNE]    16 element toggles .............................. OK",
    "[TUNE]    Reset all to defaults (r key) .................... OK",
    "[THEME]   65 active themes across 14 categories ............ OK",
    "[THEME]   18 legacy themes (hidden, toggleable with L) ..... OK",
    "[THEME]   83 total themes loaded ........................... OK",
    "[THEME]   4-color palette per theme ........................ OK",
    "[THEME]   Runtime theme registry for imports ............... OK",
    "[EDITOR]  ThemeEditor \u2014 3-page modal, live preview ......... OK",
    "[EDITOR]  Config sliders, palette editor, metadata ......... OK",
    "[EDITOR]  Save/load custom themes to JSON .................. OK",
    "[XPORT]   .hvtheme v1.1 format with plugin code ........... OK",
    "[XPORT]   Base64-encoded Python plugin export .............. OK",
    "[XPORT]   Format version migration (v0.x -> v1.0 -> v1.1)  OK",
    "[XPORT]   Preview mode (inspect before install) ............ OK",
    "[XPORT]   Trust confirmation for custom plugins ............ OK",
    "[LOG]     LogOverlay \u2014 3-stage brightness decay ............ OK",
    "[LOG]     60-second auto-expire, 60-line scrollback ........ OK",
    "[LOG]     Source-based color coding (10 colors) ............. OK",
    "[LOG]     35+ event kind formatters ........................ OK",
    "[DEBUG]   DebugPanel \u2014 right-anchored diagnostic overlay ... OK",
    "[DEBUG]   Intensity bar + recent events + triggers ......... OK",
    "[MENU]    CommandMenu \u2014 modal overlay, mode-aware .......... OK",
    "[KEYS]    22 keyboard shortcuts ............................ OK",
    "[CLI]     24 CLI flags .................................... OK",
    "[PERF]    Performance mode \u2014 toggle expensive effects ...... OK",
    "[SYS]     Config persistence ............................... OK",
    "[SYS]     Gateway hook handler ............................. OK",
    "[SYS]     Auto-launch on agent:start events ................ OK",
    "[SYS]     macOS native fullscreen (AppleScript) ............ OK",
    "[SYS]     LOCKED / MUTED / QUIET / PERF / TUNED HUD ....... OK",
    "\u2501" * 51,
    "[OK] 83 themes  |  14 categories  |  6 emergent systems",
    "[OK] 12 reactive types  |  9 post-FX  |  10 data sources",
    "[OK] 29 tunable parameters  |  22 shortcuts  |  54 event types",
    "[OK] v0.2.0 READY",
    "\u2501" * 51,
]

# Lines that are final [OK] summary lines (rendered differently)
BOOT_SUMMARY_START = len(BOOT_LINES) - 5  # last separator + 4 OK lines + last separator

# ---------------------------------------------------------------------------
# Feature highlight cards
# ---------------------------------------------------------------------------
FEATURE_CARDS = [
    (3.0,  "RAW STATS",          "83 themes  \u00b7  12 reactive categories\n54 event types  \u00b7  9 post-processing effects\n6 emergent systems  \u00b7  10 data sources"),
    (2.5,  "AUDIO ENGINE",       "Sound that reacts to your agent's thoughts"),
    (2.0,  "GALLERY MODE",       "Auto-opens from scheduled jobs"),
    (1.5,  "AGENT TOOLING",      "AI builds screens for you"),
    (1.0,  "LIVE AGENT LOGS",    "See what your agent sees"),
    (0.6,  "IMPORT \u00b7 EXPORT \u00b7 SHARE", ""),
    (0.3,  "FULL CUSTOMIZATION", ""),
    (0.15, "PURE PYTHON  \u00b7  ZERO DEPENDENCIES", ""),
    (0.08, "OPEN SOURCE", ""),
]

# ---------------------------------------------------------------------------
# Finale banner (box-drawing ASCII art)
# ---------------------------------------------------------------------------
HERMES_BANNER = [
    " \u2588\u2588\u2557  \u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2557   \u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557",
    " \u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d",
    " \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2554\u2588\u2588\u2588\u2588\u2554\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557",
    " \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u255d  \u2588\u2588\u2554\u2550\u2550\u2588\u2557\u2588\u2588\u2551\u255a\u2588\u2588\u2554\u255d\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u255d  \u255a\u2550\u2550\u2550\u2550\u2588\u2588\u2551",
    " \u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551 \u255a\u2550\u255d \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551",
    " \u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u255d     \u255a\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d",
]

NEUROVISION_BANNER = [
    " \u2588\u2588\u2588\u2557   \u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2557   \u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2557   \u2588\u2588\u2557\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2557   \u2588\u2588\u2557",
    " \u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2551",
    " \u2588\u2588\u2554\u2588\u2588\u2557 \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2554\u2588\u2588\u2557 \u2588\u2588\u2551",
    " \u2588\u2588\u2551\u255a\u2588\u2588\u2557\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u255d  \u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2588\u2557\u2588\u2588\u2551   \u2588\u2588\u2551\u255a\u2588\u2588\u2557 \u2588\u2588\u2554\u255d\u2588\u2588\u2551\u255a\u2550\u2550\u2550\u2550\u2588\u2588\u2551\u2588\u2588\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2551\u255a\u2588\u2588\u2557\u2588\u2588\u2551",
    " \u2588\u2588\u2551 \u255a\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u255a\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2551  \u2588\u2588\u2551\u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d \u255a\u2588\u2588\u2588\u2588\u2554\u255d \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2551\u255a\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2551 \u255a\u2588\u2588\u2588\u2588\u2551",
    " \u255a\u2550\u255d  \u255a\u2550\u2550\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u255d \u255a\u2550\u255d  \u255a\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u255d   \u255a\u2550\u2550\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u255d \u255a\u2550\u255d  \u255a\u2550\u2550\u2550\u255d",
]


# ---------------------------------------------------------------------------
# Color pair constants
# ---------------------------------------------------------------------------
CP_GREEN = 1       # green on black  (boot [TAG] + OK)
CP_CYAN = 2        # cyan on black   (boot headers/separators)
CP_WHITE = 3       # white on black  (boot body text)
CP_MAGENTA = 4     # magenta on black (v0.2.0 labels + banner)
CP_BRIGHT = 5      # bright white    (feature card titles)


def init_colors():
    """Initialize all curses color pairs."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CP_GREEN,   curses.COLOR_GREEN,   curses.COLOR_BLACK)
    curses.init_pair(CP_CYAN,    curses.COLOR_CYAN,    curses.COLOR_BLACK)
    curses.init_pair(CP_WHITE,   curses.COLOR_WHITE,   curses.COLOR_BLACK)
    curses.init_pair(CP_MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(CP_BRIGHT,  curses.COLOR_WHITE,   curses.COLOR_BLACK)


# ---------------------------------------------------------------------------
# Helper: safe addstr that won't crash at screen edge
# ---------------------------------------------------------------------------
def safe_addstr(win, y, x, text, attr=0):
    h, w = win.getmaxyx()
    if y < 0 or y >= h:
        return
    if x >= w:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    max_len = w - x - 1  # leave last col safe
    if max_len <= 0:
        return
    try:
        win.addstr(y, x, text[:max_len], attr)
    except curses.error:
        pass


def draw_centered(win, row, text, attr=0):
    """Draw text centered horizontally at the given row."""
    h, w = win.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    safe_addstr(win, row, x, text, attr)


# ---------------------------------------------------------------------------
# Theme screen helpers
# ---------------------------------------------------------------------------
def make_state(theme_name, w, h, seed=42):
    """Build a ThemeState for the given theme name."""
    config = build_theme_config(theme_name)
    config = apply_custom_overrides(config)
    state = ThemeState(config, w, h, seed=seed, quiet=True)
    state.tune = TuneSettings()
    return state


def draw_version_label(win, version, row=3):
    """Draw bold white version label centered at the given row."""
    h, w = win.getmaxyx()
    label = f"  {version}  "
    attr = curses.color_pair(CP_WHITE) | curses.A_BOLD
    draw_centered(win, row, label, attr)


def draw_body_text(win, text, base_row=None):
    """Draw normal-weight cyan body text centered, optionally multiline."""
    h, w = win.getmaxyx()
    if base_row is None:
        base_row = h // 2 + 2
    lines = text.split("\n")
    attr = curses.color_pair(CP_CYAN)
    for i, line in enumerate(lines):
        draw_centered(win, base_row + i, line, attr)


def run_theme_screen(stdscr, renderer, theme_name, duration, version_label, body_text="", seed=42):
    """Run a single themed screen for the given duration with overlays."""
    h, w = stdscr.getmaxyx()
    state = make_state(theme_name, w, h, seed=seed)
    deadline = time.time() + duration

    while time.time() < deadline:
        h, w = stdscr.getmaxyx()
        state.step()
        try:
            renderer.draw(state, 0, 1, deadline, hide_hud=True)
        except Exception:
            pass

        # Draw version label overlay
        draw_version_label(stdscr, version_label)

        # Draw body text if provided
        if body_text:
            draw_body_text(stdscr, body_text)

        stdscr.refresh()
        time.sleep(FRAME_DELAY)


# ---------------------------------------------------------------------------
# SECTION 1: Early Builds
# ---------------------------------------------------------------------------
def section_early_builds(stdscr, renderer):
    screens = [
        # v0.1.0 — no body text
        ("black-hole",      "v0.1.0", ""),
        ("neural-sky",      "v0.1.0", ""),
        ("binary-rain",     "v0.1.0", ""),
        # v0.1.1
        ("aurora-borealis", "v0.1.1", "Built for Hermes Agent. Reacts to your agent \u2014 live."),
        ("lava-lamp",       "v0.1.1", "Every tool call, memory write, and session is a signal."),
        ("beach-lighthouse","v0.1.1", "A visual language for AI activity. Not a screensaver."),
        # v0.1.2
        ("starfall",        "v0.1.2", "Hook it in. One install. Your agent starts talking."),
        ("stellar-weave",   "v0.1.2", "10 live data sources. 54 event types. All wired up."),
        ("sol",             "v0.1.2", "Build your own screens. The plugin API is yours."),
    ]
    for i, (theme, ver, body) in enumerate(screens):
        run_theme_screen(stdscr, renderer, theme, 3.0, ver, body, seed=100 + i)


# ---------------------------------------------------------------------------
# SECTION 2: Terminal Boot Sequence
# ---------------------------------------------------------------------------
def draw_boot_line(stdscr, line, row):
    """Draw a single boot line with appropriate coloring."""
    h, w = stdscr.getmaxyx()
    if row >= h - 1:
        return

    # Determine line type and color
    stripped = line.strip()

    # Separator lines ━━━
    if stripped and all(c in '\u2501\u2500-=' for c in stripped[:3]):
        safe_addstr(stdscr, row, 1, line[:w-2], curses.color_pair(CP_CYAN) | curses.A_BOLD)
        return

    # Header line (first line)
    if stripped.startswith("[HERMES NEUROVISION"):
        safe_addstr(stdscr, row, 1, line[:w-2], curses.color_pair(CP_CYAN) | curses.A_BOLD)
        return

    # Final [OK] summary lines
    if stripped.startswith("[OK]"):
        safe_addstr(stdscr, row, 1, line[:w-2], curses.color_pair(CP_GREEN) | curses.A_BOLD)
        return

    # Regular [TAG] ... OK lines
    # Find the tag portion [XXX]
    if line.startswith("["):
        bracket_end = line.find("]")
        if bracket_end != -1:
            tag_part = line[:bracket_end + 1]
            rest = line[bracket_end + 1:]

            # Find " OK" at end
            ok_suffix = ""
            middle_part = rest
            if rest.rstrip().endswith(" OK"):
                ok_pos = rest.rfind(" OK")
                middle_part = rest[:ok_pos]
                ok_suffix = rest[ok_pos:]

            x = 1
            # Draw tag in dim green
            tag_attr = curses.color_pair(CP_GREEN) | curses.A_DIM
            safe_addstr(stdscr, row, x, tag_part, tag_attr)
            x += len(tag_part)

            # Draw middle in white
            mid_attr = curses.color_pair(CP_WHITE)
            avail = w - x - len(ok_suffix) - 2
            middle_disp = middle_part[:avail] if avail > 0 else ""
            safe_addstr(stdscr, row, x, middle_disp, mid_attr)
            x += len(middle_disp)

            # Draw OK in bright green
            if ok_suffix:
                ok_attr = curses.color_pair(CP_GREEN) | curses.A_BOLD
                safe_addstr(stdscr, row, x, ok_suffix[:w - x - 1], ok_attr)
            return

    # Fallback: white
    safe_addstr(stdscr, row, 1, line[:w-2], curses.color_pair(CP_WHITE))


def section_terminal_boot(stdscr):
    h, w = stdscr.getmaxyx()

    # Fade to black (instant clear)
    stdscr.clear()
    stdscr.refresh()
    time.sleep(0.5)  # Hold 0.5s black

    # Compute timing: 4 seconds for all lines
    n_lines = len(BOOT_LINES)
    per_line_delay = 4.0 / max(n_lines, 1)

    displayed_lines = []
    start_time = time.time()

    for line in BOOT_LINES:
        displayed_lines.append(line)
        stdscr.clear()
        stdscr.bkgd(' ', curses.color_pair(CP_WHITE))

        # Show last (h-2) lines
        visible = displayed_lines[-(h - 2):]
        for i, dl in enumerate(visible):
            draw_boot_line(stdscr, dl, i + 1)

        stdscr.refresh()
        time.sleep(per_line_delay)

    # Hold 2 seconds on final summary
    time.sleep(2.0)


# ---------------------------------------------------------------------------
# SECTION 3: v0.2.0 Showcase
# ---------------------------------------------------------------------------
def section_v020_showcase(stdscr, renderer):
    screens = [
        "pulse-matrix",
        "electric-storm",
        "dna-strand",
        "mandala-scope",
        "storm-core",
        "swarm-mind",
        "quasar",
        "fractal-engine",
        "barnsley-fern",   # last: fade out v0.2.0 label
    ]

    label_attr_full = curses.color_pair(CP_MAGENTA) | curses.A_BOLD

    for i, theme_name in enumerate(screens):
        h, w = stdscr.getmaxyx()
        state = make_state(theme_name, w, h, seed=200 + i)
        duration = 3.0
        deadline = time.time() + duration
        is_last = (i == len(screens) - 1)
        screen_start = time.time()

        while time.time() < deadline:
            h, w = stdscr.getmaxyx()
            state.step()
            try:
                renderer.draw(state, 0, 1, deadline, hide_hud=True)
            except Exception:
                pass

            # On last screen, fade out label over the 3 seconds
            if is_last:
                elapsed = time.time() - screen_start
                fade_frac = 1.0 - min(1.0, elapsed / duration)
                # Simulate fade: only show label in first 2/3 of duration
                if fade_frac > 0.33:
                    draw_centered(stdscr, 3, "  v0.2.0  ", label_attr_full)
                # else: label gone (faded out)
            else:
                draw_centered(stdscr, 3, "  v0.2.0  ", label_attr_full)

            stdscr.refresh()
            time.sleep(FRAME_DELAY)


# ---------------------------------------------------------------------------
# SECTION 4: Feature Highlights
# ---------------------------------------------------------------------------
def draw_feature_card(stdscr, title, subtitle):
    """Draw a centered feature card on black background."""
    stdscr.clear()
    stdscr.bkgd(' ', curses.color_pair(CP_WHITE))
    h, w = stdscr.getmaxyx()

    subtitle_lines = [l for l in subtitle.split("\n") if subtitle] if subtitle else []
    total_lines = 1 + (1 if subtitle_lines else 0) + len(subtitle_lines)
    start_row = max(0, h // 2 - total_lines // 2)

    # Title
    title_attr = curses.color_pair(CP_BRIGHT) | curses.A_BOLD
    draw_centered(stdscr, start_row, title, title_attr)

    # Subtitle lines
    if subtitle_lines:
        sub_attr = curses.color_pair(CP_WHITE) | curses.A_DIM
        for j, sl in enumerate(subtitle_lines):
            draw_centered(stdscr, start_row + 2 + j, sl, sub_attr)

    stdscr.refresh()


def section_feature_highlights(stdscr):
    for (dur, title, subtitle) in FEATURE_CARDS:
        draw_feature_card(stdscr, title, subtitle)
        time.sleep(dur)

        # Fade to black (instant)
        stdscr.clear()
        stdscr.refresh()
        time.sleep(0.05)


# ---------------------------------------------------------------------------
# SECTION 5: Finale
# ---------------------------------------------------------------------------
def draw_outro_overlay(stdscr, alpha=1.0):
    """Draw the finale text overlay. alpha: 0.0 (invisible) to 1.0 (full)."""
    h, w = stdscr.getmaxyx()

    # Determine attrs based on alpha
    if alpha <= 0:
        return

    banner_attr = curses.color_pair(CP_MAGENTA) | curses.A_BOLD
    link_attr   = curses.color_pair(CP_MAGENTA) | curses.A_BOLD
    sub1_attr   = curses.color_pair(CP_WHITE) | curses.A_DIM
    sub2_attr   = curses.color_pair(CP_WHITE) | curses.A_DIM

    # If alpha < 0.5, use dim versions
    if alpha < 0.5:
        banner_attr = curses.color_pair(CP_MAGENTA) | curses.A_DIM
        link_attr   = curses.color_pair(CP_MAGENTA) | curses.A_DIM
        sub1_attr   = curses.color_pair(CP_WHITE) | curses.A_DIM
        sub2_attr   = curses.color_pair(CP_WHITE) | curses.A_DIM

    # Total block height:
    # 6 lines HERMES + 1 blank + 6 lines NEUROVISION + 1 blank + 1 link + 1 blank + 1 tagline + 1 sub
    total_height = 6 + 1 + 6 + 1 + 1 + 1 + 1 + 1
    start_row = max(0, (h - total_height) // 2)

    row = start_row

    # HERMES banner
    for bline in HERMES_BANNER:
        # Center it
        x = max(0, (w - len(bline)) // 2)
        safe_addstr(stdscr, row, x, bline, banner_attr)
        row += 1

    row += 1  # blank line

    # NEUROVISION banner
    for bline in NEUROVISION_BANNER:
        x = max(0, (w - len(bline)) // 2)
        safe_addstr(stdscr, row, x, bline, banner_attr)
        row += 1

    row += 1  # blank line

    # Link
    link = "github.com/Tranquil-Flow/hermes-neurovision"
    draw_centered(stdscr, row, link, link_attr)
    row += 1

    row += 1  # blank line

    # Taglines
    draw_centered(stdscr, row, "Build your own screen today!", sub1_attr)
    row += 1
    draw_centered(stdscr, row, "Then ask your agent to generate a screen based on your idea!", sub2_attr)


def section_finale(stdscr, renderer):
    h, w = stdscr.getmaxyx()

    # Black hold 3 seconds
    stdscr.clear()
    stdscr.refresh()
    time.sleep(3.0)

    # Fade in synaptic-plasma + outro text over remaining ~4 seconds
    state = make_state("synaptic-plasma", w, h, seed=999)
    fade_duration = 4.0
    total_hold = 7.0
    fade_start = time.time()
    deadline = fade_start + total_hold

    while time.time() < deadline:
        h, w = stdscr.getmaxyx()
        elapsed = time.time() - fade_start
        alpha = min(1.0, elapsed / fade_duration)

        state.step()

        if alpha > 0.1:
            # Only render theme once fading in begins
            try:
                renderer.draw(state, 0, 1, deadline, hide_hud=True)
            except Exception:
                pass
        else:
            stdscr.clear()

        # Draw outro overlay
        draw_outro_overlay(stdscr, alpha)

        stdscr.refresh()
        time.sleep(FRAME_DELAY)


# ---------------------------------------------------------------------------
# Main demo runner
# ---------------------------------------------------------------------------
def run_demo(stdscr):
    """Main demo sequence entry point (called by curses.wrapper)."""
    # Basic curses setup
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    init_colors()
    stdscr.bkgd(' ', curses.color_pair(CP_WHITE))

    # Build renderer once (reused for all theme screens)
    renderer = Renderer(stdscr)

    try:
        # --- SECTION 1: Early Builds (27 sec) ---
        section_early_builds(stdscr, renderer)

        # --- SECTION 2: Terminal Boot (6 sec) ---
        section_terminal_boot(stdscr)

        # --- SECTION 3: v0.2.0 Showcase (27 sec) ---
        section_v020_showcase(stdscr, renderer)

        # --- SECTION 4: Feature Highlights (~14 sec) ---
        section_feature_highlights(stdscr)

        # --- SECTION 5: Finale (7 sec) ---
        section_finale(stdscr, renderer)

    except KeyboardInterrupt:
        pass

    # Clean exit
    stdscr.clear()
    stdscr.refresh()


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------
def main():
    """CLI entry point."""
    try:
        curses.wrapper(run_demo)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Demo error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
