#!/usr/bin/env python3
"""
demo_video.py — Hermes Neurovision Demo Sequence (~90 seconds)

RECORDING NOTES:
- Record fullscreen (any 16:9 terminal, min 120 cols wide)
- Keep original recording as-is for full quality
- Twitter 9:16 crop: ffmpeg -i input.mp4 -vf "crop=ih*9/16:ih:(iw-ih*9/16)/2:0" twitter.mp4
- Twitter square:    ffmpeg -i input.mp4 -vf "crop=ih:ih:(iw-ih)/2:0" twitter_sq.mp4
- All content is centered so any crop works cleanly

Run: cd hermes-neurovision && source .venv/bin/activate && python3 demo_video.py
"""

import curses
import time
import sys
import random
import math

from hermes_neurovision.scene import ThemeState
from hermes_neurovision.themes import build_theme_config, FRAME_DELAY
from hermes_neurovision.renderer import Renderer
from hermes_neurovision.tune import TuneSettings
from hermes_neurovision.theme_editor import apply_custom_overrides


# ---------------------------------------------------------------------------
# Big block font — 5 rows tall, for large readable overlays
# ---------------------------------------------------------------------------
FONT = {
    ' ': ["    ", "    ", "    ", "    ", "    "],
    'A': [" ▄█▄ ", "█   █", "█████", "█   █", "█   █"],
    'B': ["████ ", "█   █", "████ ", "█   █", "████ "],
    'C': [" ████", "█    ", "█    ", "█    ", " ████"],
    'D': ["████ ", "█   █", "█   █", "█   █", "████ "],
    'E': ["█████", "█    ", "████ ", "█    ", "█████"],
    'F': ["█████", "█    ", "████ ", "█    ", "█    "],
    'G': [" ████", "█    ", "█  ██", "█   █", " ████"],
    'H': ["█   █", "█   █", "█████", "█   █", "█   █"],
    'I': ["█████", "  █  ", "  █  ", "  █  ", "█████"],
    'J': ["█████", "   █ ", "   █ ", "█  █ ", " ██  "],
    'K': ["█   █", "█  █ ", "███  ", "█  █ ", "█   █"],
    'L': ["█    ", "█    ", "█    ", "█    ", "█████"],
    'M': ["█   █", "██ ██", "█ █ █", "█   █", "█   █"],
    'N': ["█   █", "██  █", "█ █ █", "█  ██", "█   █"],
    'O': [" ███ ", "█   █", "█   █", "█   █", " ███ "],
    'P': ["████ ", "█   █", "████ ", "█    ", "█    "],
    'Q': [" ███ ", "█   █", "█ █ █", "█  █ ", " ██▄█"],
    'R': ["████ ", "█   █", "████ ", "█  █ ", "█   █"],
    'S': [" ████", "█    ", " ███ ", "    █", "████ "],
    'T': ["█████", "  █  ", "  █  ", "  █  ", "  █  "],
    'U': ["█   █", "█   █", "█   █", "█   █", " ███ "],
    'V': ["█   █", "█   █", "█   █", " █ █ ", "  █  "],
    'W': ["█   █", "█   █", "█ █ █", "██ ██", "█   █"],
    'X': ["█   █", " █ █ ", "  █  ", " █ █ ", "█   █"],
    'Y': ["█   █", " █ █ ", "  █  ", "  █  ", "  █  "],
    'Z': ["█████", "   █ ", "  █  ", " █   ", "█████"],
    '0': [" ███ ", "█  ██", "█ █ █", "██  █", " ███ "],
    '1': [" ██  ", "  █  ", "  █  ", "  █  ", "█████"],
    '2': [" ███ ", "█   █", "  ██ ", " █   ", "█████"],
    '3': ["████ ", "    █", " ███ ", "    █", "████ "],
    '4': ["█   █", "█   █", "█████", "    █", "    █"],
    '5': ["█████", "█    ", "████ ", "    █", "████ "],
    '6': [" ███ ", "█    ", "████ ", "█   █", " ███ "],
    '7': ["█████", "    █", "   █ ", "  █  ", "  █  "],
    '8': [" ███ ", "█   █", " ███ ", "█   █", " ███ "],
    '9': [" ███ ", "█   █", " ████", "    █", " ███ "],
    '.': ["   ", "   ", "   ", " █ ", " █ "],
    '!': [" █ ", " █ ", " █ ", "   ", " █ "],
    ':': ["   ", " █ ", "   ", " █ ", "   "],
    '/': ["    █", "   █ ", "  █  ", " █   ", "█    "],
    '-': ["     ", "     ", "█████", "     ", "     "],
    '·': ["  ", "  ", " █", "  ", "  "],
}

def big_text_width(text, scale_x=1, gap=1):
    """Return pixel width of text rendered in FONT."""
    total = 0
    letters = [FONT.get(ch.upper(), FONT[' ']) for ch in text.upper()]
    for l in letters:
        total += len(l[0]) * scale_x + gap * scale_x
    return max(0, total - gap * scale_x)

def draw_big_text(stdscr, row, text, attr, center=True, gap=1, scale_x=1, scale_y=1):
    """Draw text using 5-row-tall block font.
    scale_x: horizontal pixel multiplier (2 = double width)
    scale_y: vertical pixel multiplier   (2 = double height)
    Skips space chars so theme background shows through.
    Returns the row after the last drawn row."""
    h, w = stdscr.getmaxyx()
    text = text.upper()
    letters = [FONT.get(ch, FONT[' ']) for ch in text]
    total_w = sum(len(l[0]) * scale_x for l in letters) + gap * scale_x * max(0, len(letters) - 1)
    start_x = max(0, (w - total_w) // 2) if center else 0
    x = start_x
    for li, letter in enumerate(letters):
        for r in range(5):
            for sy in range(scale_y):
                actual_row = row + r * scale_y + sy
                if actual_row >= h - 1:
                    continue
                line = letter[r]
                for ci, ch in enumerate(line):
                    if ch != ' ':
                        for sx in range(scale_x):
                            try:
                                stdscr.addstr(actual_row, x + ci * scale_x + sx, ch, attr)
                            except curses.error:
                                pass
        x += len(letter[0]) * scale_x + gap * scale_x
    return row + 5 * scale_y


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

# ---------------------------------------------------------------------------
# Feature highlight cards (duration, title, subtitle)
# ---------------------------------------------------------------------------
FEATURE_CARDS = [
    (3.0,  "100+ SCREENS",       "83 active themes  \u00b7  18 legacy themes\n14 categories  \u00b7  and growing"),
    (2.5,  "RAW STATS",          "12 reactive types  \u00b7  9 post-FX\n6 emergent systems  \u00b7  54 event types"),
    (2.0,  "AUDIO ENGINE",       "Sound that reacts to your agent's thoughts"),
    (1.5,  "GALLERY MODE",       "Auto-opens from scheduled jobs"),
    (1.0,  "AGENT TOOLING",      "AI builds screens for you"),
    (0.6,  "LIVE AGENT LOGS",    "See what your agent sees"),
    (0.4,  "IMPORT EXPORT SHARE", ""),
    (0.25, "FULL CUSTOMIZATION", ""),
    (0.12, "PURE PYTHON",        ""),
    (0.06, "OPEN SOURCE",        ""),
]

# ---------------------------------------------------------------------------
# Finale banner (box-drawing ASCII art, pre-encoded)
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
# Color pair constants — use pairs 10+ so renderer._apply_palette() (pairs 1-5)
# never overwrites our overlay pairs.  Re-init after every renderer.draw() call.
# ---------------------------------------------------------------------------
CP_GREEN   = 10  # green on black   — boot [TAG] + OK
CP_CYAN    = 11  # cyan on black    — boot headers
CP_WHITE   = 12  # white on black   — body text, boot middle
CP_MAGENTA = 13  # magenta on black — v0.2.0 label
CP_YELLOW  = 14  # yellow on black  — energy/warning
CP_BLACK   = 15  # black on black   — backing strips
# Purple gradient pairs for outro banner (16-21)
CP_PUR0    = 16  # brightest magenta-purple
CP_PUR1    = 17
CP_PUR2    = 18
CP_PUR3    = 19
CP_PUR4    = 20
CP_PUR5    = 21  # deepest violet
CP_PINK    = 22  # pink-magenta for link text


def init_colors():
    """Init all overlay color pairs. Call once at startup AND after every renderer.draw()."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CP_GREEN,   curses.COLOR_GREEN,   curses.COLOR_BLACK)
    curses.init_pair(CP_CYAN,    curses.COLOR_CYAN,    curses.COLOR_BLACK)
    curses.init_pair(CP_WHITE,   curses.COLOR_WHITE,   curses.COLOR_BLACK)
    curses.init_pair(CP_MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(CP_YELLOW,  curses.COLOR_YELLOW,  curses.COLOR_BLACK)
    curses.init_pair(CP_BLACK,   curses.COLOR_BLACK,   curses.COLOR_BLACK)
    # Purple gradient — all map to MAGENTA since curses only has 8 base colors.
    # A_BOLD gives the bright variant, A_DIM gives the dim. Combined they make a gradient.
    for cp in [CP_PUR0, CP_PUR1, CP_PUR2, CP_PUR3, CP_PUR4, CP_PUR5, CP_PINK]:
        curses.init_pair(cp, curses.COLOR_MAGENTA, curses.COLOR_BLACK)


def reinit_overlay_colors():
    """Re-assert overlay pairs after renderer.draw() stomps pairs 1-5."""
    # Renderer only touches 1-5, ours are 10-22, so actually safe — but call
    # init_colors() here defensively in case curses resets.
    try:
        init_colors()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_addstr(win, y, x, text, attr=0):
    h, w = win.getmaxyx()
    if y < 0 or y >= h - 1:
        return
    if x >= w - 1:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    max_len = w - x - 1
    if max_len <= 0:
        return
    try:
        win.addstr(y, x, text[:max_len], attr)
    except curses.error:
        pass


def draw_centered(win, row, text, attr=0):
    h, w = win.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    safe_addstr(win, row, x, text, attr)


def draw_black_strip(stdscr, start_row, num_rows):
    """Draw black-on-black strip to back overlays."""
    h, w = stdscr.getmaxyx()
    blank = " " * (w - 2)
    attr = curses.color_pair(CP_BLACK)
    for r in range(start_row, min(start_row + num_rows, h - 1)):
        safe_addstr(stdscr, r, 0, blank, attr)


def make_state(theme_name, w, h, seed=42, speed=1.0):
    config = build_theme_config(theme_name)
    config = apply_custom_overrides(config)
    state = ThemeState(config, w, h, seed=seed, quiet=True)
    tune = TuneSettings()
    tune.animation_speed = speed
    state.tune = tune
    return state


def draw_version_label(stdscr, version, is_v020=False):
    """Draw big version label near top at 1.5x scale (scale_x=2, scale_y=2)."""
    row = 1
    attr = curses.color_pair(CP_MAGENTA) | curses.A_BOLD if is_v020 else curses.color_pair(CP_WHITE) | curses.A_BOLD
    draw_big_text(stdscr, row, version, attr, scale_x=2, scale_y=2)


def draw_body_big(stdscr, text, is_v020=False):
    """Draw big body text centered vertically, floating over theme."""
    h, w = stdscr.getmaxyx()
    # version label is 5*2=10 rows tall + 1 row padding = starts at row 12
    row = max(12, h // 2 - 3)
    attr = curses.color_pair(CP_WHITE) | curses.A_BOLD if not is_v020 else curses.color_pair(CP_MAGENTA) | curses.A_BOLD
    draw_big_text(stdscr, row, text, attr)


# ---------------------------------------------------------------------------
# Theme screen runner
# ---------------------------------------------------------------------------
def run_theme_screen(stdscr, renderer, theme_name, duration, version, body="", seed=42, is_v020=False, speed=1.0):
    h, w = stdscr.getmaxyx()
    state = make_state(theme_name, w, h, seed=seed, speed=speed)
    deadline = time.time() + duration
    while time.time() < deadline:
        h, w = stdscr.getmaxyx()
        state.step()
        try:
            renderer.draw(state, 0, 1, deadline, hide_hud=True, skip_refresh=True)
        except Exception:
            pass
        reinit_overlay_colors()
        draw_version_label(stdscr, version, is_v020=is_v020)
        if body:
            draw_body_big(stdscr, body, is_v020=is_v020)
        stdscr.refresh()
        time.sleep(FRAME_DELAY)


# ---------------------------------------------------------------------------
# SECTION 1: Early Builds (27 sec)
# ---------------------------------------------------------------------------
def section_early_builds(stdscr, renderer):
    screens = [
        # theme                      version   body text                      seed
        ("legacy-black-hole",       "V0.1.0", "",                             100),
        ("binary-rain",             "V0.1.0", "",                             101),
        ("legacy-binary-star",      "V0.1.0", "",                             102),
        ("lava-lamp",               "V0.1.1", "BUILT FOR HERMES AGENT",       103),
        ("aurora-borealis",         "V0.1.1", "EVERY EVENT IS A SIGNAL",      104),
        ("legacy-beach-lighthouse", "V0.1.1", "NOT A SCREENSAVER",            105),
        ("sol",                     "V0.1.2", "ONE INSTALL. AGENT TALKS.",    106),
        ("starfall",                "V0.1.2", "10 SOURCES. 54 EVENT TYPES.",  107),
        ("stellar-weave",           "V0.1.2", "BUILD YOUR OWN SCREENS.",      108),
    ]
    for (theme, ver, body, seed) in screens:
        run_theme_screen(stdscr, renderer, theme, 3.0, ver, body, seed=seed)


# ---------------------------------------------------------------------------
# SECTION 2: Terminal Boot — custom ASCII particle system builds up, then EXPLODES
# ---------------------------------------------------------------------------

# Particle chars — sparse at first, dense later
SPARK_CHARS   = list("·∙•*+×✦✧⋆⋅")
STREAK_CHARS  = list("─│╱╲╮╯╭╰═║╔╗╚╝╠╣╦╩╬")
GLYPH_CHARS   = list("░▒▓█▄▀▌▐▖▗▘▙▚▛▜▝▞▟")
ENERGY_CHARS  = list("◆◇◈◉○●◎⬡⬢⬣▲△▼▽◀▶◁▷")
MATRIX_CHARS  = list("01アイウエオカキクケコサシスセソタチツテトナニヌネノ")
RUNE_CHARS    = list("ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ")
MATH_CHARS    = list("∑∏∫∂∇∞∈∉∩∪⊂⊃⊆⊇∧∨¬⊕⊗⊥∥∦∠∡∢")

ALL_PHASE_CHARS = {
    0.0: SPARK_CHARS,
    0.2: SPARK_CHARS + STREAK_CHARS,
    0.4: SPARK_CHARS + STREAK_CHARS + GLYPH_CHARS,
    0.55: SPARK_CHARS + STREAK_CHARS + GLYPH_CHARS + ENERGY_CHARS,
    0.7: SPARK_CHARS + STREAK_CHARS + GLYPH_CHARS + ENERGY_CHARS + MATRIX_CHARS,
    0.85: SPARK_CHARS + STREAK_CHARS + GLYPH_CHARS + ENERGY_CHARS + MATRIX_CHARS + RUNE_CHARS + MATH_CHARS,
}

def chars_for_phase(phase):
    best = SPARK_CHARS
    for threshold, chars in sorted(ALL_PHASE_CHARS.items()):
        if phase >= threshold:
            best = chars
    return best


class BootParticle:
    """A single animated particle in the boot sequence."""
    MODE_DRIFT   = 0   # random drift across screen
    MODE_RAIN    = 1   # falling column (matrix rain)
    MODE_ORBIT   = 2   # circular orbit around a point
    MODE_SPIRAL  = 3   # outward spiral from center
    MODE_STREAK  = 4   # fast horizontal/diagonal streak

    def __init__(self, h, w, phase):
        self.h = h
        self.w = w
        self.mode = MODE_DRIFT = 0
        self.reset(phase)

    def reset(self, phase=0):
        self.age = 0.0
        chars = chars_for_phase(phase)
        self.char = random.choice(chars)

        # Mode selection — more variety at higher phase
        if phase < 0.25:
            self.mode = self.MODE_DRIFT
        elif phase < 0.45:
            self.mode = random.choice([self.MODE_DRIFT, self.MODE_RAIN])
        elif phase < 0.65:
            self.mode = random.choice([self.MODE_DRIFT, self.MODE_RAIN, self.MODE_ORBIT])
        elif phase < 0.80:
            self.mode = random.choice([self.MODE_DRIFT, self.MODE_RAIN, self.MODE_ORBIT, self.MODE_SPIRAL])
        else:
            self.mode = random.choice([self.MODE_DRIFT, self.MODE_RAIN, self.MODE_ORBIT,
                                       self.MODE_SPIRAL, self.MODE_STREAK])

        if self.mode == self.MODE_DRIFT:
            self.x = random.uniform(0, self.w - 1)
            self.y = random.uniform(0, self.h - 1)
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.05, 0.3 + phase * 2.0)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed * 0.45
            self.life = random.uniform(1.0, 3.0 + phase * 2.0)

        elif self.mode == self.MODE_RAIN:
            self.x = random.uniform(0, self.w - 1)
            self.y = random.uniform(-self.h, 0)
            self.vx = random.uniform(-0.05, 0.05)
            self.vy = random.uniform(0.5 + phase * 1.5, 1.5 + phase * 3.0)
            self.life = self.h / max(self.vy, 0.1) * 0.05
            self.char = random.choice(MATRIX_CHARS + GLYPH_CHARS)

        elif self.mode == self.MODE_ORBIT:
            self.cx = random.uniform(self.w * 0.2, self.w * 0.8)
            self.cy = random.uniform(self.h * 0.2, self.h * 0.8)
            self.radius = random.uniform(3, min(self.w, self.h * 2) * 0.2)
            self.angle = random.uniform(0, math.pi * 2)
            self.omega = random.uniform(1.0, 3.0) * random.choice([-1, 1])
            self.x = self.cx + math.cos(self.angle) * self.radius
            self.y = self.cy + math.sin(self.angle) * self.radius * 0.45
            self.vx = self.vy = 0
            self.life = random.uniform(2.0, 5.0)

        elif self.mode == self.MODE_SPIRAL:
            self.cx = self.w / 2
            self.cy = self.h / 2
            self.angle = random.uniform(0, math.pi * 2)
            self.r = random.uniform(0, 2)
            self.omega = random.uniform(2.0, 5.0) * random.choice([-1, 1])
            self.dr = random.uniform(0.3, 1.0) * (phase + 0.2)
            self.x = self.cx
            self.y = self.cy
            self.vx = self.vy = 0
            self.life = random.uniform(1.5, 4.0)

        elif self.mode == self.MODE_STREAK:
            side = random.choice(['l', 'r', 't', 'b'])
            if side == 'l':
                self.x, self.y = 0, random.uniform(0, self.h)
                self.vx = random.uniform(3, 8 + phase * 6)
                self.vy = random.uniform(-0.5, 0.5)
            elif side == 'r':
                self.x, self.y = self.w, random.uniform(0, self.h)
                self.vx = -random.uniform(3, 8 + phase * 6)
                self.vy = random.uniform(-0.5, 0.5)
            elif side == 't':
                self.x, self.y = random.uniform(0, self.w), 0
                self.vx = random.uniform(-1, 1)
                self.vy = random.uniform(1, 3 + phase * 3)
            else:
                self.x, self.y = random.uniform(0, self.w), self.h
                self.vx = random.uniform(-1, 1)
                self.vy = -random.uniform(1, 3 + phase * 3)
            self.life = random.uniform(0.3, 1.0)
            self.char = random.choice(STREAK_CHARS + ENERGY_CHARS)

        # Color
        if phase < 0.25:
            self.cp = CP_CYAN
        elif phase < 0.45:
            self.cp = random.choice([CP_CYAN, CP_GREEN])
        elif phase < 0.65:
            self.cp = random.choice([CP_CYAN, CP_GREEN, CP_WHITE])
        elif phase < 0.80:
            self.cp = random.choice([CP_CYAN, CP_GREEN, CP_WHITE, CP_YELLOW])
        else:
            self.cp = random.choice([CP_CYAN, CP_GREEN, CP_WHITE, CP_YELLOW, CP_MAGENTA])
        self.bold = phase > 0.4 and random.random() < phase

    def step(self, dt):
        self.age += dt
        if self.mode == self.MODE_ORBIT:
            self.angle += self.omega * dt
            self.x = self.cx + math.cos(self.angle) * self.radius
            self.y = self.cy + math.sin(self.angle) * self.radius * 0.45
        elif self.mode == self.MODE_SPIRAL:
            self.angle += self.omega * dt
            self.r += self.dr * dt * 20
            self.x = self.cx + math.cos(self.angle) * self.r
            self.y = self.cy + math.sin(self.angle) * self.r * 0.45
        else:
            self.x += self.vx * dt * 20
            self.y += self.vy * dt * 20
        # Wrap for drift/rain
        if self.mode in (self.MODE_DRIFT,):
            if self.x < 0: self.x += self.w
            if self.x >= self.w: self.x -= self.w
            if self.y < 0: self.y += self.h
            if self.y >= self.h: self.y -= self.h

    @property
    def dead(self):
        if self.mode == self.MODE_SPIRAL:
            return self.r > max(self.w, self.h) or self.age >= self.life
        if self.mode == self.MODE_STREAK:
            return (self.x < -2 or self.x >= self.w + 2 or
                    self.y < -2 or self.y >= self.h + 2 or self.age >= self.life)
        return self.age >= self.life

    def draw(self, stdscr):
        ix, iy = int(self.x), int(self.y)
        if iy < 0 or iy >= self.h - 1 or ix < 0 or ix >= self.w - 1:
            return
        attr = curses.color_pair(self.cp)
        if self.bold:
            attr |= curses.A_BOLD
        try:
            stdscr.addstr(iy, ix, self.char, attr)
        except curses.error:
            pass


def draw_boot_line(stdscr, line, row):
    h, w = stdscr.getmaxyx()
    if row >= h - 1:
        return
    stripped = line.strip()
    if stripped and all(c in '\u2501\u2500-=' for c in stripped[:3]):
        safe_addstr(stdscr, row, 1, line[:w-2], curses.color_pair(CP_CYAN) | curses.A_BOLD)
        return
    if stripped.startswith("[HERMES NEUROVISION"):
        safe_addstr(stdscr, row, 1, line[:w-2], curses.color_pair(CP_CYAN) | curses.A_BOLD)
        return
    if stripped.startswith("[OK]"):
        safe_addstr(stdscr, row, 1, line[:w-2], curses.color_pair(CP_GREEN) | curses.A_BOLD)
        return
    if line.startswith("["):
        bracket_end = line.find("]")
        if bracket_end != -1:
            tag_part = line[:bracket_end + 1]
            rest = line[bracket_end + 1:]
            ok_suffix = ""
            middle_part = rest
            if rest.rstrip().endswith(" OK"):
                ok_pos = rest.rfind(" OK")
                middle_part = rest[:ok_pos]
                ok_suffix = rest[ok_pos:]
            x = 1
            safe_addstr(stdscr, row, x, tag_part, curses.color_pair(CP_GREEN) | curses.A_DIM)
            x += len(tag_part)
            avail = w - x - len(ok_suffix) - 2
            mid_disp = middle_part[:avail] if avail > 0 else ""
            safe_addstr(stdscr, row, x, mid_disp, curses.color_pair(CP_WHITE))
            x += len(mid_disp)
            if ok_suffix:
                safe_addstr(stdscr, row, x, ok_suffix[:w-x-1], curses.color_pair(CP_GREEN) | curses.A_BOLD)
            return
    safe_addstr(stdscr, row, 1, line[:w-2], curses.color_pair(CP_WHITE))


def section_terminal_boot(stdscr, renderer):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    stdscr.refresh()
    time.sleep(0.3)

    n_lines = len(BOOT_LINES)
    print_duration = 4.0
    per_line = print_duration / max(n_lines, 1)

    # Particle pool — starts empty, grows as phase increases
    particles = []
    MAX_PARTICLES = 600

    displayed = []
    print_start = time.time()
    last_frame = time.time()

    for line_idx, line in enumerate(BOOT_LINES):
        displayed.append(line)
        phase = line_idx / max(n_lines - 1, 1)  # 0.0 → 1.0

        # Spawn new particles proportional to phase
        target_count = int(phase * phase * MAX_PARTICLES)  # quadratic ramp
        while len(particles) < target_count:
            particles.append(BootParticle(h, w, phase))

        line_deadline = print_start + (line_idx + 1) * per_line

        while time.time() < line_deadline:
            now = time.time()
            dt = now - last_frame
            last_frame = now

            # Force black background
            stdscr.erase()
            h2, w2 = stdscr.getmaxyx()
            black_attr = curses.color_pair(CP_BLACK)
            blank = " " * (w2 - 1)
            for _r in range(h2 - 1):
                try:
                    stdscr.addstr(_r, 0, blank, black_attr)
                except curses.error:
                    pass

            # Step and draw particles
            alive = []
            for p in particles:
                p.step(dt)
                if p.dead:
                    p.reset(phase)  # recycle
                p.draw(stdscr)
                alive.append(p)
            particles[:] = alive

            # Draw boot text ON TOP of particles
            visible = displayed[-(h - 2):]
            for i, dl in enumerate(visible):
                draw_boot_line(stdscr, dl, i + 1)

            stdscr.refresh()
            time.sleep(FRAME_DELAY)

    # Hold 2 seconds at max density
    hold_end = time.time() + 2.0
    phase = 1.0
    # Top up to max particles
    while len(particles) < MAX_PARTICLES:
        particles.append(BootParticle(h, w, phase))

    while time.time() < hold_end:
        now = time.time()
        dt = now - last_frame
        last_frame = now
        stdscr.erase()
        h2, w2 = stdscr.getmaxyx()
        black_attr = curses.color_pair(CP_BLACK)
        blank = " " * (w2 - 1)
        for _r in range(h2 - 1):
            try:
                stdscr.addstr(_r, 0, blank, black_attr)
            except curses.error:
                pass
        for p in particles:
            p.step(dt)
            if p.dead:
                p.reset(phase)
            p.draw(stdscr)
        visible = displayed[-(h - 2):]
        for i, dl in enumerate(visible):
            draw_boot_line(stdscr, dl, i + 1)
        stdscr.refresh()
        time.sleep(FRAME_DELAY)

    # === EXPLOSION ===
    # Convergence: particles race toward center
    cx, cy = w // 2, h // 2
    for p in particles:
        dx = cx - p.x
        dy = cy - p.y
        dist = max(1.0, math.sqrt(dx*dx + dy*dy))
        speed = random.uniform(3.0, 8.0)
        p.vx = (dx / dist) * speed
        p.vy = (dy / dist) * speed * 0.5
        p.life = 9999
        p.cp = random.choice([CP_WHITE, CP_YELLOW, CP_MAGENTA, CP_CYAN])
        p.bold = True

    conv_end = time.time() + 0.5
    while time.time() < conv_end:
        now = time.time()
        dt = now - last_frame
        last_frame = now
        stdscr.erase()
        h2, w2 = stdscr.getmaxyx()
        black_attr = curses.color_pair(CP_BLACK)
        blank = " " * (w2 - 1)
        for _r in range(h2 - 1):
            try:
                stdscr.addstr(_r, 0, blank, black_attr)
            except curses.error:
                pass
        for p in particles:
            p.step(dt)
            p.draw(stdscr)
        stdscr.refresh()
        time.sleep(FRAME_DELAY)

    # Flash white
    flash_attr = curses.color_pair(CP_WHITE) | curses.A_BOLD | curses.A_REVERSE
    blank = " " * (w - 1)
    for r in range(h - 1):
        safe_addstr(stdscr, r, 0, blank, flash_attr)
    stdscr.refresh()
    time.sleep(0.1)

    # Explode outward — particles scatter from center
    for p in particles:
        p.x = cx + random.uniform(-3, 3)
        p.y = cy + random.uniform(-2, 2)
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(5.0, 15.0)
        p.vx = math.cos(angle) * speed
        p.vy = math.sin(angle) * speed * 0.5
        p.cp = random.choice([CP_WHITE, CP_YELLOW, CP_MAGENTA, CP_CYAN, CP_GREEN])
        p.bold = True
        p.life = 9999

    blast_end = time.time() + 0.6
    while time.time() < blast_end:
        now = time.time()
        dt = now - last_frame
        last_frame = now
        stdscr.erase()
        h2, w2 = stdscr.getmaxyx()
        black_attr = curses.color_pair(CP_BLACK)
        blank = " " * (w2 - 1)
        for _r in range(h2 - 1):
            try:
                stdscr.addstr(_r, 0, blank, black_attr)
            except curses.error:
                pass
        for p in particles:
            p.step(dt)
            p.draw(stdscr)
        stdscr.refresh()
        time.sleep(FRAME_DELAY)

    # Final flash
    for r in range(h - 1):
        safe_addstr(stdscr, r, 0, blank, flash_attr)
    stdscr.refresh()
    time.sleep(0.1)

    stdscr.clear()
    stdscr.refresh()
    time.sleep(0.1)


# ---------------------------------------------------------------------------
# SECTION 3: v0.2.0 Showcase — accelerating
# ---------------------------------------------------------------------------
def section_v020_showcase(stdscr, renderer):
    # Each entry: (theme, duration, card_title, card_subtitle)
    screens = [
        ("plasma-rainbow",  4.0,  "100+ SCREENS",        "83 active  ·  18 legacy\n14 categories  ·  and growing"),
        ("electric-storm",  3.5,  "RAW STATS",            "12 reactive  ·  9 post-FX\n6 emergent systems  ·  54 events"),
        ("synaptic-plasma", 3.0,  "AUDIO ENGINE",         "Sound reacts to your agent"),
        ("dna-strand",      2.5,  "GALLERY MODE",         "Auto-opens from cron jobs"),
        ("storm-core",      2.0,  "AGENT TOOLING",        "AI builds screens for you"),
        ("swarm-mind",      1.5,  "LIVE AGENT LOGS",      "See what your agent sees"),
        ("quasar",          1.0,  "IMPORT EXPORT SHARE",  ""),
        ("fractal-engine",  0.75, "FULL CUSTOMIZATION",   ""),
        ("barnsley-fern",   0.5,  "PURE PYTHON",          ""),
    ]

    label_attr = curses.color_pair(CP_MAGENTA) | curses.A_BOLD
    title_attr = curses.color_pair(CP_MAGENTA) | curses.A_BOLD
    sub_attr   = curses.color_pair(CP_CYAN)    | curses.A_BOLD

    for i, (theme_name, duration, card_title, card_sub) in enumerate(screens):
        h, w = stdscr.getmaxyx()
        state = make_state(theme_name, w, h, seed=200 + i)
        deadline = time.time() + duration
        is_last = (i == len(screens) - 1)
        screen_start = time.time()

        while time.time() < deadline:
            h, w = stdscr.getmaxyx()
            state.step()
            try:
                renderer.draw(state, 0, 1, deadline, hide_hud=True, skip_refresh=True)
            except Exception:
                pass
            reinit_overlay_colors()

            elapsed = time.time() - screen_start
            show_label = not is_last or elapsed < (duration * 0.7)

            if show_label:
                # Version label top at 2x scale
                draw_big_text(stdscr, 1, "V0.2.0", label_attr, scale_x=2, scale_y=2)

                # Card title + subtitle centered in the lower portion of the screen
                sub_lines = card_sub.split("\n") if card_sub else []
                # total height: title=5 rows + 2 gap + sub lines * 6 (5+1) each
                total_text_h = 5 + (2 + len(sub_lines) * 6 if sub_lines else 0)
                title_row = max(13, (h - total_text_h) // 2 + 3)

                next_row = draw_big_text(stdscr, title_row, card_title, title_attr)

                if sub_lines:
                    sub_row = next_row + 2
                    for line in sub_lines:
                        draw_big_text(stdscr, sub_row, line, sub_attr)
                        sub_row += 6  # 5 + 1 gap

            stdscr.refresh()
            time.sleep(FRAME_DELAY)


# ---------------------------------------------------------------------------
# SECTION 4: Feature Highlights — pure black, accelerating
# ---------------------------------------------------------------------------
def draw_feature_card(stdscr, title, subtitle):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    # Compute vertical center for big title (5 rows) + subtitle lines
    sub_lines = [l for l in subtitle.split("\n")] if subtitle else []
    total_h = 5 + (2 + len(sub_lines) if sub_lines else 0)
    start_row = max(1, (h - total_h) // 2)

    title_attr = curses.color_pair(CP_WHITE) | curses.A_BOLD
    draw_big_text(stdscr, start_row, title, title_attr)

    if sub_lines:
        sub_attr = curses.color_pair(CP_CYAN) | curses.A_DIM
        sub_row = start_row + 7
        for sl in sub_lines:
            draw_centered(stdscr, sub_row, sl, sub_attr)
            sub_row += 1

    stdscr.refresh()


def section_feature_highlights(stdscr):
    for (dur, title, subtitle) in FEATURE_CARDS:
        draw_feature_card(stdscr, title, subtitle)
        time.sleep(dur)
        stdscr.clear()
        stdscr.refresh()
        time.sleep(0.04)


# ---------------------------------------------------------------------------
# SECTION 5: Finale — synaptic-plasma + banner overlay
# ---------------------------------------------------------------------------
def draw_outro_overlay(stdscr, alpha=1.0):
    if alpha <= 0:
        return
    h, w = stdscr.getmaxyx()

    # Purple gradient — 6 rows of HERMES, 6 rows of NEUROVISION
    # Row 0 = brightest, row 5 = deepest. Use A_BOLD for top half, A_DIM for bottom.
    HERMES_GRAD = [
        curses.color_pair(CP_PUR0) | curses.A_BOLD,
        curses.color_pair(CP_PUR1) | curses.A_BOLD,
        curses.color_pair(CP_PUR2) | curses.A_BOLD,
        curses.color_pair(CP_PUR3),
        curses.color_pair(CP_PUR4),
        curses.color_pair(CP_PUR5) | curses.A_DIM,
    ]
    NEURO_GRAD = [
        curses.color_pair(CP_PUR1) | curses.A_BOLD,
        curses.color_pair(CP_PUR2) | curses.A_BOLD,
        curses.color_pair(CP_PUR3),
        curses.color_pair(CP_PUR4),
        curses.color_pair(CP_PUR5),
        curses.color_pair(CP_PUR5) | curses.A_DIM,
    ]
    if alpha < 0.5:
        HERMES_GRAD = [a | curses.A_DIM for a in HERMES_GRAD]
        NEURO_GRAD  = [a | curses.A_DIM for a in NEURO_GRAD]

    link_attr = curses.color_pair(CP_PINK) | curses.A_BOLD
    sub_attr  = curses.color_pair(CP_WHITE) | curses.A_DIM

    # Total block height: 6 + 1 + 6 + 1 + 1 + 1 + 1 + 1 = 18
    total_height = 18
    start_row = max(0, (h - total_height) // 2)
    row = start_row

    for ri, bline in enumerate(HERMES_BANNER):
        x = max(0, (w - len(bline)) // 2)
        attr = HERMES_GRAD[ri] if ri < len(HERMES_GRAD) else HERMES_GRAD[-1]
        for ci, ch in enumerate(bline):
            if ch != ' ':
                try:
                    stdscr.addstr(row, x + ci, ch, attr)
                except curses.error:
                    pass
        row += 1
    row += 1  # blank
    for ri, bline in enumerate(NEUROVISION_BANNER):
        x = max(0, (w - len(bline)) // 2)
        attr = NEURO_GRAD[ri] if ri < len(NEURO_GRAD) else NEURO_GRAD[-1]
        for ci, ch in enumerate(bline):
            if ch != ' ':
                try:
                    stdscr.addstr(row, x + ci, ch, attr)
                except curses.error:
                    pass
        row += 1
    row += 1  # blank
    draw_centered(stdscr, row, "github.com/Tranquil-Flow/hermes-neurovision", link_attr)
    row += 2
    draw_centered(stdscr, row, "Build your own screen today!", sub_attr)
    row += 1
    draw_centered(stdscr, row, "Then ask your agent to generate a screen based on your idea!", sub_attr)


def section_finale(stdscr, renderer):
    h, w = stdscr.getmaxyx()

    # Black hold 3 seconds
    stdscr.clear()
    stdscr.refresh()
    time.sleep(3.0)

    state = make_state("halvorsen-star", w, h, seed=999)
    fade_duration = 2.0
    total_hold = 7.0
    fade_start = time.time()
    deadline = fade_start + total_hold

    while time.time() < deadline:
        h, w = stdscr.getmaxyx()
        elapsed = time.time() - fade_start
        alpha = min(1.0, elapsed / fade_duration)

        state.step()
        if alpha > 0.05:
            try:
                renderer.draw(state, 0, 1, deadline, hide_hud=True, skip_refresh=True)
            except Exception:
                pass
            reinit_overlay_colors()
        else:
            stdscr.clear()

        draw_outro_overlay(stdscr, alpha)
        stdscr.refresh()
        time.sleep(FRAME_DELAY)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run_demo(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)
    init_colors()

    renderer = Renderer(stdscr)

    try:
        section_early_builds(stdscr, renderer)
        section_terminal_boot(stdscr, renderer)
        section_v020_showcase(stdscr, renderer)
        section_finale(stdscr, renderer)
    except KeyboardInterrupt:
        pass

    stdscr.clear()
    stdscr.refresh()


def main():
    try:
        curses.wrapper(run_demo)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Demo error: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
