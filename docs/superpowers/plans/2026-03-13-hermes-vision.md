# Hermes Vision Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a terminal-native (curses) neurovisualizer that reacts to live Hermes Agent events, displaying a living neural network with 10 animated themes.

**Architecture:** Extract the existing `~/Desktop/neurovisualizer.py` (846 lines, 10 themes, particle/packet/pulse system) into a clean package with separate event polling, bridge mapping, and rendering layers. Event data comes from polling SQLite (`~/.hermes/state.db`), filesystem watching (`~/.hermes/memories/`), cron status, an optional Aegis audit trail, and a custom JSONL event channel fed by a gateway hook.

**Tech Stack:** Python 3.10+ stdlib only (curses, sqlite3, json, os, math, random, dataclasses, argparse, time, pathlib)

**Spec:** `docs/superpowers/specs/2026-03-13-hermes-vision-design.md`

**Existing code to extract from:** `~/Desktop/neurovisualizer.py`

---

## File Map

| File | Responsibility | Source |
|---|---|---|
| `pyproject.toml` | Package metadata, `hermes-vision` CLI entry point | New |
| `hermes_vision/__init__.py` | Package init, version | New |
| `hermes_vision/themes.py` | ThemeConfig dataclass + 10 theme definitions | Extract from neurovisualizer.py lines 85-737 |
| `hermes_vision/scene.py` | Particle, Packet, ThemeState — all simulation logic | Extract from neurovisualizer.py lines 40-456 |
| `hermes_vision/renderer.py` | Curses Renderer — all drawing code | Extract from neurovisualizer.py lines 459-721 |
| `hermes_vision/events.py` | VisionEvent dataclass + EventPoller | New |
| `hermes_vision/bridge.py` | VisualTrigger dataclass + event-to-visual mapping | New |
| `hermes_vision/log_overlay.py` | LogOverlay — fading scrolling text over visuals | New |
| `hermes_vision/app.py` | GalleryApp + LiveApp orchestrators | Partially extract from neurovisualizer.py lines 740-845, extend |
| `hermes_vision/cli.py` | argparse entry point | New |
| `hermes_vision/sources/__init__.py` | Source module init | New |
| `hermes_vision/sources/custom.py` | JSONL file tailer for `~/.hermes/vision/events.jsonl` | New |
| `hermes_vision/sources/state_db.py` | SQLite poller for `~/.hermes/state.db` | New |
| `hermes_vision/sources/memories.py` | Filesystem watcher for `~/.hermes/memories/` | New |
| `hermes_vision/sources/cron.py` | Cron job status poller from `~/.hermes/cron/` | New |
| `hermes_vision/sources/aegis.py` | Optional Aegis audit trail tailer | New |
| `hermes_vision/sources/hook_handler.py` | Standalone gateway hook — writes events to JSONL | New |
| `tests/test_events.py` | Tests for VisionEvent + EventPoller | New |
| `tests/test_bridge.py` | Tests for VisualTrigger mapping | New |
| `tests/test_sources.py` | Tests for each source poller | New |
| `tests/test_scene.py` | Tests for scene simulation (headless) | New |
| `tests/test_log_overlay.py` | Tests for log overlay logic | New |

---

## Chunk 1: Project Scaffold + Visual Engine Extraction

### Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `hermes_vision/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=64"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "hermes-vision"
version = "0.1.0"
description = "Terminal neurovisualizer for Hermes Agent"
requires-python = ">=3.10"

[project.scripts]
hermes-vision = "hermes_vision.cli:main"
```

- [ ] **Step 2: Create __init__.py**

```python
"""Hermes Vision — Terminal neurovisualizer for Hermes Agent."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create empty test and source directories**

```bash
mkdir -p ~/Projects/hermes-vision/tests
mkdir -p ~/Projects/hermes-vision/hermes_vision/sources
touch ~/Projects/hermes-vision/tests/__init__.py
touch ~/Projects/hermes-vision/hermes_vision/sources/__init__.py
```

- [ ] **Step 4: Commit**

```bash
cd ~/Projects/hermes-vision
git init
git add pyproject.toml hermes_vision/__init__.py hermes_vision/sources/__init__.py tests/__init__.py
git commit -m "chore: scaffold hermes-vision project"
```

### Task 2: Extract themes.py

**Files:**
- Create: `hermes_vision/themes.py`
- Reference: `~/Desktop/neurovisualizer.py` lines 25-36 (THEMES tuple), 85-106 (ThemeConfig), 724-737 (build_theme_config)

- [ ] **Step 1: Write test for theme loading**

Create `tests/test_themes.py`:

```python
from hermes_vision.themes import THEMES, ThemeConfig, build_theme_config


def test_all_theme_names_are_defined():
    assert len(THEMES) == 10
    assert "neural-sky" in THEMES
    assert "black-hole" in THEMES


def test_build_theme_config_returns_config():
    config = build_theme_config("neural-sky")
    assert isinstance(config, ThemeConfig)
    assert config.name == "neural-sky"


def test_all_themes_can_be_built():
    for name in THEMES:
        config = build_theme_config(name)
        assert config.name == name
        assert config.background_density > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_themes.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'hermes_vision.themes'`

- [ ] **Step 3: Extract ThemeConfig and build_theme_config from neurovisualizer.py**

Create `hermes_vision/themes.py` by extracting:
- The `THEMES` tuple (line 25-36)
- The `ThemeConfig` dataclass (lines 85-106)
- The `build_theme_config` function (lines 724-737)
- The constants: `FRAME_DELAY`, `DEFAULT_THEME_SECONDS`, `STAR_CHARS`, `PACKET_CHARS`, `PULSE_CHARS` (lines 38-42)

Important: `ThemeConfig` uses `curses.COLOR_*` constants in its palette field defaults. These must be kept as-is (they're integer constants available at import time even without initializing curses).

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_themes.py -v
```

Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add hermes_vision/themes.py tests/test_themes.py
git commit -m "feat: extract theme definitions from neurovisualizer"
```

### Task 3: Extract scene.py

**Files:**
- Create: `hermes_vision/scene.py`
- Reference: `~/Desktop/neurovisualizer.py` lines 40-456 (Particle, Packet, ThemeState)

- [ ] **Step 1: Write test for scene simulation**

Create `tests/test_scene.py`:

```python
from hermes_vision.themes import build_theme_config
from hermes_vision.scene import ThemeState, Particle, Packet


def test_theme_state_builds_scene():
    config = build_theme_config("neural-sky")
    state = ThemeState(config, 100, 30, seed=42)
    assert len(state.nodes) > 0
    assert len(state.edges) > 0
    assert len(state.stars) > 0


def test_theme_state_step_advances_frame():
    config = build_theme_config("neural-sky")
    state = ThemeState(config, 100, 30, seed=42)
    assert state.frame == 0
    state.step()
    assert state.frame == 1


def test_theme_state_resize():
    config = build_theme_config("neural-sky")
    state = ThemeState(config, 100, 30, seed=42)
    old_nodes = len(state.nodes)
    state.resize(200, 60)
    assert state.width == 200
    assert state.height == 60


def test_particle_step_decrements_life():
    p = Particle(10.0, 10.0, 0.1, 0.1, 5.0, 5.0, "*")
    alive = p.step()
    assert alive is True
    assert p.life == 4.0


def test_particle_dies_when_life_zero():
    p = Particle(10.0, 10.0, 0.1, 0.1, 1.0, 5.0, "*")
    alive = p.step()
    assert alive is False


def test_packet_step_advances_progress():
    p = Packet((0, 1), 0.0, 0.1)
    p.step()
    assert p.progress > 0.0


def test_all_themes_simulate_without_error():
    from hermes_vision.themes import THEMES
    for name in THEMES:
        config = build_theme_config(name)
        state = ThemeState(config, 80, 24, seed=42)
        for _ in range(20):
            state.step()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_scene.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Extract scene classes from neurovisualizer.py**

Create `hermes_vision/scene.py` by extracting:
- `Particle` dataclass (lines 46-67)
- `Packet` dataclass (lines 70-79)
- `ThemeState` dataclass (lines 109-456) — all simulation logic

Change imports: `from hermes_vision.themes import ThemeConfig, STAR_CHARS, PACKET_CHARS, PULSE_CHARS`

Important extraction notes:
- The original `neurovisualizer.py` already has `self.rng = random.Random(self.seed)` in `__post_init__` — preserve this.
- The original `_build_scene()` calls `_build_stars()`, `_build_nodes()`, `_build_edges()` — these must remain as separate callable methods (not inlined), because `apply_trigger()` (added in Task 16) will call `_build_edges()` directly to rebuild connections when new nodes are spawned.
- The original `resize()` method already calls `_build_scene()` — this is correct.

Add the new `intensity_multiplier` field to `ThemeState`:
```python
intensity_multiplier: float = 0.6  # base level
_intensity_target: float = 0.6
_intensity_rate: float = 0.0  # recovery rate per frame
_dynamic_nodes: List[int] = field(default_factory=list)
flash_until: float = 0.0
flash_color_key: str = "warning"
```

Add constants and methods to ThemeState:
```python
MAX_DYNAMIC_NODES = 64

def apply_trigger(self, trigger) -> None:
    """Apply a VisualTrigger to the scene state."""
    # This will be called by the bridge — stub for now
    pass

def _step_intensity(self) -> None:
    """Animate intensity multiplier toward target."""
    if abs(self.intensity_multiplier - self._intensity_target) > 0.01:
        diff = self._intensity_target - self.intensity_multiplier
        self.intensity_multiplier += diff * self._intensity_rate
    else:
        self.intensity_multiplier = self._intensity_target
```

Call `self._step_intensity()` at the start of `step()`.

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_scene.py -v
```

Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add hermes_vision/scene.py tests/test_scene.py
git commit -m "feat: extract scene simulation from neurovisualizer"
```

### Task 4: Extract renderer.py

**Files:**
- Create: `hermes_vision/renderer.py`
- Reference: `~/Desktop/neurovisualizer.py` lines 459-721 (Renderer class)

- [ ] **Step 1: Write test for renderer initialization**

Create `tests/test_renderer.py`:

```python
from hermes_vision.renderer import Renderer


def test_renderer_edge_glyph_horizontal():
    from hermes_vision.themes import build_theme_config
    config = build_theme_config("neural-sky")
    glyph = Renderer._edge_glyph(10.0, 1.0, config)
    assert glyph == "─"


def test_renderer_edge_glyph_vertical():
    from hermes_vision.themes import build_theme_config
    config = build_theme_config("neural-sky")
    glyph = Renderer._edge_glyph(1.0, 10.0, config)
    assert glyph == "│"


def test_renderer_ring_points():
    points = list(Renderer._ring_points(10.0, 10.0, 0.5))
    assert len(points) == 1  # small radius = single center point


def test_renderer_ring_points_large_radius():
    points = list(Renderer._ring_points(10.0, 10.0, 5.0))
    assert len(points) >= 8  # large radius = multiple points
```

Note: We can only test static/utility methods without a curses window. The main `draw()` method requires a live curses window and will be tested via the headless app mode.

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_renderer.py -v
```

Expected: FAIL

- [ ] **Step 3: Extract Renderer from neurovisualizer.py**

Create `hermes_vision/renderer.py` by extracting:
- `Renderer` class (lines 459-721)

Change imports: `from hermes_vision.themes import ThemeConfig, STAR_CHARS, PULSE_CHARS`
Add import: `from hermes_vision.scene import ThemeState`

The renderer stays mostly unchanged. It receives a `ThemeState` and draws it.

The `draw()` method signature is: `draw(self, state: ThemeState, gallery_index: int, gallery_total: int, end_time: Optional[float]) -> None`. This matches the original. `LiveApp` calls it as `draw(state, 0, 1, deadline)` for single-theme mode.

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_renderer.py -v
```

Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add hermes_vision/renderer.py tests/test_renderer.py
git commit -m "feat: extract curses renderer from neurovisualizer"
```

### Task 5: Extract app.py — Gallery mode

**Files:**
- Create: `hermes_vision/app.py`
- Reference: `~/Desktop/neurovisualizer.py` lines 740-845 (GalleryApp)

- [ ] **Step 1: Write test for GalleryApp construction**

Create `tests/test_app.py`:

```python
from hermes_vision.app import GalleryApp


def test_gallery_app_headless_runs():
    """Test that the headless gallery runs for a few frames without error."""
    from hermes_vision.themes import THEMES
    result = GalleryApp.run_headless(themes=list(THEMES), seconds=0.5, theme_seconds=0.2)
    assert result["frames"] > 0
    assert result["themes_shown"] >= 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_app.py -v
```

Expected: FAIL

- [ ] **Step 3: Create app.py with GalleryApp**

Create `hermes_vision/app.py` extracting `GalleryApp` from neurovisualizer.py lines 740-793. Adapt:
- Import from `hermes_vision.themes`, `hermes_vision.scene`, `hermes_vision.renderer`
- Add `run_headless` class method (extracted from `run_headless` function, lines 815-838)
- The curses `run()` method stays as-is

```python
class GalleryApp:
    def __init__(self, stdscr, themes, theme_seconds, end_after):
        ...  # same as original

    def run(self):
        ...  # same as original, curses main loop

    @classmethod
    def run_headless(cls, themes, seconds, theme_seconds=8.0):
        """Run without curses for testing. Returns stats dict."""
        from hermes_vision.themes import build_theme_config, FRAME_DELAY
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_app.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add hermes_vision/app.py tests/test_app.py
git commit -m "feat: extract gallery app with headless mode"
```

### Task 6: Create cli.py — Gallery mode working end-to-end

**Files:**
- Create: `hermes_vision/cli.py`

- [ ] **Step 1: Create cli.py with argparse and gallery mode**

```python
"""Hermes Vision CLI entry point."""

from __future__ import annotations

import argparse
import curses
import sys

from hermes_vision.themes import THEMES, DEFAULT_THEME_SECONDS


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="hermes-vision",
        description="Terminal neurovisualizer for Hermes Agent",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true", help="Real-time event visualization (default)")
    mode.add_argument("--gallery", action="store_true", help="Theme rotation screensaver")
    mode.add_argument("--daemon", action="store_true", help="Gallery when idle, live when active")

    parser.add_argument("--theme", choices=THEMES, default="neural-sky", help="Theme to use")
    parser.add_argument("--theme-seconds", type=float, default=DEFAULT_THEME_SECONDS, help="Seconds per theme in gallery/daemon")
    parser.add_argument("--logs", action="store_true", help="Enable log overlay")
    parser.add_argument("--auto-exit", action="store_true", help="Exit 30s after last event")
    parser.add_argument("--seconds", type=float, default=None, help="Exit after N seconds (testing)")
    parser.add_argument("--no-aegis", action="store_true", help="Skip Aegis source")

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.gallery or (not args.live and not args.daemon):
        # Gallery mode — this is a temporary default until live mode is built in Task 16.
        # Task 16 changes the default to --live.
        _run_gallery(args)
    elif args.live:
        # Live mode — will be implemented in Chunk 3
        print("Live mode not yet implemented. Use --gallery for now.", file=sys.stderr)
        sys.exit(1)
    elif args.daemon:
        print("Daemon mode not yet implemented.", file=sys.stderr)
        sys.exit(1)


def _run_gallery(args):
    from hermes_vision.app import GalleryApp

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        # Headless mode
        result = GalleryApp.run_headless(
            themes=[args.theme] if args.theme != "neural-sky" or not args.gallery else list(THEMES),
            seconds=args.seconds or 2.0,
            theme_seconds=args.theme_seconds,
        )
        print(f"headless: {result}")
        return

    themes = list(THEMES) if args.gallery else [args.theme]
    curses.wrapper(lambda stdscr: GalleryApp(stdscr, themes, args.theme_seconds, args.seconds).run())
```

- [ ] **Step 2: Test CLI headless mode**

```bash
cd ~/Projects/hermes-vision && echo "" | python -m hermes_vision.cli --gallery --seconds 1
```

Expected: `headless: {frames: ..., themes_shown: ..., final_theme: ...}`

- [ ] **Step 3: Test CLI interactive mode manually (quick smoke test)**

```bash
cd ~/Projects/hermes-vision && python -m hermes_vision.cli --gallery --seconds 3
```

Expected: Curses animation appears for 3 seconds, then exits cleanly.

- [ ] **Step 4: Add `__main__.py` for `python -m hermes_vision` support**

Create `hermes_vision/__main__.py`:

```python
from hermes_vision.cli import main

main()
```

- [ ] **Step 5: Commit**

```bash
git add hermes_vision/cli.py hermes_vision/__main__.py
git commit -m "feat: CLI entry point with gallery mode"
```

---

## Chunk 2: Event System + Sources

### Task 7: Create events.py — VisionEvent + EventPoller

**Files:**
- Create: `hermes_vision/events.py`
- Create: `tests/test_events.py`

- [ ] **Step 1: Write tests for VisionEvent and EventPoller**

```python
import time
from hermes_vision.events import VisionEvent, EventPoller


def test_vision_event_creation():
    ev = VisionEvent(
        timestamp=time.time(),
        source="test",
        kind="test_event",
        severity="info",
        data={"key": "value"},
    )
    assert ev.source == "test"
    assert ev.kind == "test_event"


def test_event_poller_with_no_sources():
    poller = EventPoller(sources=[])
    events = poller.poll()
    assert events == []


def test_event_poller_collects_from_sources():
    now = time.time()
    fake_event = VisionEvent(now, "fake", "test", "info", {})

    def fake_poll(since):
        return [fake_event]

    poller = EventPoller(sources=[fake_poll])
    events = poller.poll()
    assert len(events) == 1
    assert events[0].kind == "test"


def test_event_poller_sorts_by_timestamp():
    ev1 = VisionEvent(100.0, "a", "first", "info", {})
    ev2 = VisionEvent(200.0, "b", "second", "info", {})

    def source_a(since):
        return [ev2]

    def source_b(since):
        return [ev1]

    poller = EventPoller(sources=[source_a, source_b])
    events = poller.poll()
    assert events[0].kind == "first"
    assert events[1].kind == "second"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_events.py -v
```

- [ ] **Step 3: Implement events.py**

```python
"""Unified event model and poller for Hermes Vision."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class VisionEvent:
    timestamp: float
    source: str
    kind: str
    severity: str  # "info", "warning", "danger"
    data: Dict[str, Any] = field(default_factory=dict)


# Type alias for source poll functions
PollFn = Callable[[float], List[VisionEvent]]


class EventPoller:
    """Polls all registered sources and returns sorted events."""

    def __init__(self, sources: List[PollFn]):
        self._sources = sources
        self._last_poll: float = time.time()

    def poll(self) -> List[VisionEvent]:
        since = self._last_poll
        self._last_poll = time.time()

        events: List[VisionEvent] = []
        for source_fn in self._sources:
            try:
                events.extend(source_fn(since))
            except Exception:
                pass  # Sources must never crash the visualizer

        events.sort(key=lambda e: e.timestamp)
        return events
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_events.py -v
```

- [ ] **Step 5: Commit**

```bash
git add hermes_vision/events.py tests/test_events.py
git commit -m "feat: VisionEvent model and EventPoller"
```

### Task 8: Create sources/custom.py — JSONL tailer

**Files:**
- Create: `hermes_vision/sources/custom.py`
- Create: `tests/test_sources.py`

- [ ] **Step 1: Write test for JSONL tailer**

```python
import json
import os
import tempfile
import time

from hermes_vision.sources.custom import poll as custom_poll, CustomSource


def test_custom_source_empty_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = f.name
    try:
        source = CustomSource(path)
        events = source.poll(0.0)
        assert events == []
    finally:
        os.unlink(path)


def test_custom_source_reads_new_lines():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = f.name
        f.write(json.dumps({"timestamp": time.time(), "event_type": "agent:start", "context": {"session_id": "abc"}}) + "\n")
    try:
        source = CustomSource(path)
        events = source.poll(0.0)
        assert len(events) == 1
        assert events[0].kind == "agent_start"
        assert events[0].source == "agent"

        # Second poll with no new data
        events2 = source.poll(time.time())
        assert events2 == []
    finally:
        os.unlink(path)


def test_custom_source_missing_file():
    source = CustomSource("/nonexistent/path.jsonl")
    events = source.poll(0.0)
    assert events == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_sources.py -v
```

- [ ] **Step 3: Implement sources/custom.py**

```python
"""JSONL file tailer for custom events written by the gateway hook."""

from __future__ import annotations

import json
import os
import time
from typing import List

from hermes_vision.events import VisionEvent

DEFAULT_PATH = os.path.expanduser("~/.hermes/vision/events.jsonl")

# Map hook event_type strings to (source, kind) tuples
EVENT_MAP = {
    "agent:start": ("agent", "agent_start"),
    "agent:step": ("agent", "agent_step"),
    "agent:end": ("agent", "agent_end"),
    "session:start": ("agent", "session_start"),
    "session:reset": ("agent", "session_reset"),
}


class CustomSource:
    def __init__(self, path: str = DEFAULT_PATH):
        self._path = path
        self._offset: int = 0

    def poll(self, since: float) -> List[VisionEvent]:
        if not os.path.exists(self._path):
            return []

        events: List[VisionEvent] = []
        try:
            with open(self._path, "r") as f:
                f.seek(self._offset)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        event_type = data.get("event_type", "")
                        context = data.get("context", {})
                        timestamp = data.get("timestamp", time.time())
                        source, kind = EVENT_MAP.get(event_type, ("custom", event_type.replace(":", "_")))
                        events.append(VisionEvent(
                            timestamp=timestamp,
                            source=source,
                            kind=kind,
                            severity="info",
                            data=context,
                        ))
                    except (json.JSONDecodeError, KeyError):
                        continue
                self._offset = f.tell()
        except OSError:
            pass

        return events


def poll(since: float) -> List[VisionEvent]:
    """Module-level poll function for EventPoller compatibility."""
    return _default_source.poll(since)


_default_source = CustomSource()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_sources.py -v
```

- [ ] **Step 5: Commit**

```bash
git add hermes_vision/sources/custom.py tests/test_sources.py
git commit -m "feat: custom JSONL event source"
```

### Task 9: Create sources/state_db.py — SQLite poller

**Files:**
- Create: `hermes_vision/sources/state_db.py`
- Append to: `tests/test_sources.py`

The `state.db` schema:
```sql
sessions(id TEXT PK, source TEXT, model TEXT, started_at REAL, ended_at REAL,
         message_count INT, tool_call_count INT, input_tokens INT, output_tokens INT, title TEXT)
messages(id INTEGER PK AUTO, session_id TEXT FK, role TEXT, content TEXT,
         tool_name TEXT, timestamp REAL, token_count INT)
```

- [ ] **Step 1: Write tests for state_db source**

Append to `tests/test_sources.py`:

```python
import sqlite3
from hermes_vision.sources.state_db import StateDbSource


def _create_test_db(path):
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY, source TEXT NOT NULL, model TEXT,
            started_at REAL NOT NULL, ended_at REAL,
            message_count INTEGER DEFAULT 0, tool_call_count INTEGER DEFAULT 0,
            input_tokens INTEGER DEFAULT 0, output_tokens INTEGER DEFAULT 0, title TEXT
        );
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES sessions(id),
            role TEXT NOT NULL, content TEXT, tool_name TEXT,
            timestamp REAL NOT NULL, token_count INTEGER
        );
    """)
    return conn


def test_state_db_no_file():
    source = StateDbSource("/nonexistent/state.db")
    events = source.poll(0.0)
    assert events == []


def test_state_db_detects_new_messages():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        conn = _create_test_db(path)
        conn.execute("INSERT INTO sessions VALUES ('s1','local','gpt-4',1000.0,NULL,0,0,0,0,NULL)")
        conn.execute("INSERT INTO messages VALUES (1,'s1','user','hello',NULL,1000.1,10)")
        conn.commit()
        conn.close()

        source = StateDbSource(path)
        events = source.poll(0.0)
        kinds = [e.kind for e in events]
        assert "active_session" in kinds
        assert "message_added" in kinds
    finally:
        os.unlink(path)


def test_state_db_detects_token_update():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        conn = _create_test_db(path)
        conn.execute("INSERT INTO sessions VALUES ('s1','local','gpt-4',1000.0,NULL,1,0,100,50,NULL)")
        conn.commit()

        source = StateDbSource(path)
        source.poll(0.0)  # initial poll sets baseline

        # Update tokens
        conn.execute("UPDATE sessions SET input_tokens=500, output_tokens=200 WHERE id='s1'")
        conn.commit()
        conn.close()

        events = source.poll(time.time())
        kinds = [e.kind for e in events]
        assert "token_update" in kinds
        token_ev = [e for e in events if e.kind == "token_update"][0]
        assert token_ev.data["delta_input"] == 400
    finally:
        os.unlink(path)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_sources.py::test_state_db_no_file tests/test_sources.py::test_state_db_detects_new_messages tests/test_sources.py::test_state_db_detects_token_update -v
```

- [ ] **Step 3: Implement sources/state_db.py**

```python
"""SQLite poller for ~/.hermes/state.db — sessions and messages."""

from __future__ import annotations

import os
import sqlite3
import time
from typing import Dict, List, Optional, Tuple

from hermes_vision.events import VisionEvent

DEFAULT_PATH = os.path.expanduser("~/.hermes/state.db")


class StateDbSource:
    def __init__(self, path: str = DEFAULT_PATH):
        self._path = path
        self._last_message_id: int = 0
        self._active_session_id: Optional[str] = None
        self._last_model: Optional[str] = None
        self._last_tokens: Tuple[int, int] = (0, 0)

    def poll(self, since: float) -> List[VisionEvent]:
        if not os.path.exists(self._path):
            return []

        events: List[VisionEvent] = []
        try:
            conn = sqlite3.connect(self._path, timeout=1.0)
            conn.row_factory = sqlite3.Row
            try:
                self._poll_active_session(conn, events)
                self._poll_messages(conn, events)
                self._poll_tokens(conn, events)
            finally:
                conn.close()
        except (sqlite3.Error, OSError):
            pass

        return events

    def _poll_active_session(self, conn, events):
        row = conn.execute(
            "SELECT id, model FROM sessions WHERE ended_at IS NULL ORDER BY started_at DESC LIMIT 1"
        ).fetchone()

        if row is None:
            return

        session_id = row["id"]
        model = row["model"]

        if session_id != self._active_session_id:
            self._active_session_id = session_id
            self._last_model = model
            events.append(VisionEvent(
                timestamp=time.time(), source="state_db",
                kind="active_session", severity="info",
                data={"session_id": session_id, "model": model},
            ))

        if model != self._last_model:
            self._last_model = model
            events.append(VisionEvent(
                timestamp=time.time(), source="state_db",
                kind="model_switch", severity="info",
                data={"model": model, "session_id": session_id},
            ))

    def _poll_messages(self, conn, events):
        rows = conn.execute(
            "SELECT id, session_id, role, tool_name, timestamp FROM messages WHERE id > ? ORDER BY id",
            (self._last_message_id,)
        ).fetchall()

        for row in rows:
            self._last_message_id = row["id"]
            events.append(VisionEvent(
                timestamp=row["timestamp"], source="state_db",
                kind="message_added", severity="info",
                data={
                    "message_id": row["id"],
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "tool_name": row["tool_name"],
                },
            ))

    def _poll_tokens(self, conn, events):
        if self._active_session_id is None:
            return

        row = conn.execute(
            "SELECT input_tokens, output_tokens FROM sessions WHERE id = ?",
            (self._active_session_id,)
        ).fetchone()

        if row is None:
            return

        input_t, output_t = row["input_tokens"] or 0, row["output_tokens"] or 0
        prev_in, prev_out = self._last_tokens

        if (input_t, output_t) != (prev_in, prev_out) and (prev_in > 0 or prev_out > 0):
            events.append(VisionEvent(
                timestamp=time.time(), source="state_db",
                kind="token_update", severity="info",
                data={
                    "input_tokens": input_t,
                    "output_tokens": output_t,
                    "delta_input": input_t - prev_in,
                    "delta_output": output_t - prev_out,
                },
            ))

        self._last_tokens = (input_t, output_t)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_sources.py -v
```

- [ ] **Step 5: Commit**

```bash
git add hermes_vision/sources/state_db.py tests/test_sources.py
git commit -m "feat: SQLite state.db event source"
```

### Task 10: Create sources/memories.py — Filesystem watcher

**Files:**
- Create: `hermes_vision/sources/memories.py`
- Append to: `tests/test_sources.py`

- [ ] **Step 1: Write tests**

Append to `tests/test_sources.py`:

```python
from hermes_vision.sources.memories import MemoriesSource


def test_memories_source_no_dir():
    source = MemoriesSource("/nonexistent/memories/")
    events = source.poll(0.0)
    assert events == []


def test_memories_source_detects_new_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        source = MemoriesSource(tmpdir)
        source.poll(0.0)  # baseline

        # Create a new file
        with open(os.path.join(tmpdir, "test.md"), "w") as f:
            f.write("memory content")

        events = source.poll(0.0)
        kinds = [e.kind for e in events]
        assert "memory_created" in kinds
```

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Implement sources/memories.py**

```python
"""Filesystem watcher for ~/.hermes/memories/ directory."""

from __future__ import annotations

import os
import time
from typing import Dict, List

from hermes_vision.events import VisionEvent

DEFAULT_PATH = os.path.expanduser("~/.hermes/memories")


class MemoriesSource:
    def __init__(self, path: str = DEFAULT_PATH):
        self._path = path
        self._known: Dict[str, float] = {}  # path -> mtime
        self._last_count: int = 0

    def poll(self, since: float) -> List[VisionEvent]:
        if not os.path.isdir(self._path):
            return []

        events: List[VisionEvent] = []
        current: Dict[str, float] = {}
        now = time.time()

        try:
            for entry in os.scandir(self._path):
                if not entry.is_file():
                    continue
                mtime = entry.stat().st_mtime
                current[entry.path] = mtime

                if entry.path not in self._known:
                    events.append(VisionEvent(
                        timestamp=now, source="memory",
                        kind="memory_created", severity="info",
                        data={"path": entry.path, "name": entry.name},
                    ))
                elif mtime > self._known[entry.path]:
                    events.append(VisionEvent(
                        timestamp=now, source="memory",
                        kind="memory_accessed", severity="info",
                        data={"path": entry.path, "name": entry.name},
                    ))
        except OSError:
            pass

        if self._last_count > 0 and len(current) != self._last_count:
            events.append(VisionEvent(
                timestamp=now, source="memory",
                kind="memory_count_changed", severity="info",
                data={"count": len(current), "previous": self._last_count},
            ))

        self._known = current
        self._last_count = len(current)
        return events
```

- [ ] **Step 4: Run tests**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_sources.py -v
```

- [ ] **Step 5: Commit**

```bash
git add hermes_vision/sources/memories.py tests/test_sources.py
git commit -m "feat: memory filesystem event source"
```

### Task 11: Create sources/cron.py — Cron job status

**Files:**
- Create: `hermes_vision/sources/cron.py`
- Append to: `tests/test_sources.py`

- [ ] **Step 1: Write tests**

Append to `tests/test_sources.py`:

```python
from hermes_vision.sources.cron import CronSource


def test_cron_source_no_dir():
    source = CronSource("/nonexistent/cron/")
    events = source.poll(0.0)
    assert events == []


def test_cron_source_detects_lock():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write a jobs.json
        jobs_path = os.path.join(tmpdir, "jobs.json")
        with open(jobs_path, "w") as f:
            json.dump({"jobs": [{"id": "j1", "name": "test-job", "status": "active"}], "updated_at": ""}, f)

        source = CronSource(tmpdir)
        source.poll(0.0)  # baseline

        # Create lock file (indicates executing)
        with open(os.path.join(tmpdir, ".tick.lock"), "w") as f:
            f.write("locked")

        events = source.poll(0.0)
        kinds = [e.kind for e in events]
        assert "cron_executing" in kinds
```

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Implement sources/cron.py**

```python
"""Cron job status poller for ~/.hermes/cron/ directory."""

from __future__ import annotations

import json
import os
import time
from typing import Dict, List

from hermes_vision.events import VisionEvent

DEFAULT_PATH = os.path.expanduser("~/.hermes/cron")


class CronSource:
    def __init__(self, path: str = DEFAULT_PATH):
        self._path = path
        self._was_locked: bool = False
        self._known_outputs: set = set()

    def poll(self, since: float) -> List[VisionEvent]:
        if not os.path.isdir(self._path):
            return []

        events: List[VisionEvent] = []
        now = time.time()

        # Check lock file for execution state
        lock_path = os.path.join(self._path, ".tick.lock")
        is_locked = os.path.exists(lock_path)

        if is_locked and not self._was_locked:
            events.append(VisionEvent(
                timestamp=now, source="cron",
                kind="cron_executing", severity="info",
                data={},
            ))

        if not is_locked and self._was_locked:
            events.append(VisionEvent(
                timestamp=now, source="cron",
                kind="cron_completed", severity="info",
                data={},
            ))

        self._was_locked = is_locked

        # Check for new output files
        output_dir = os.path.join(self._path, "output")
        if os.path.isdir(output_dir):
            try:
                for entry in os.scandir(output_dir):
                    if entry.is_file() and entry.path not in self._known_outputs:
                        self._known_outputs.add(entry.path)
                        events.append(VisionEvent(
                            timestamp=now, source="cron",
                            kind="cron_completed", severity="info",
                            data={"output": entry.name},
                        ))
            except OSError:
                pass

        return events
```

- [ ] **Step 4: Run tests**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_sources.py -v
```

- [ ] **Step 5: Commit**

```bash
git add hermes_vision/sources/cron.py tests/test_sources.py
git commit -m "feat: cron job event source"
```

### Task 12: Create sources/aegis.py — Optional audit trail

**Files:**
- Create: `hermes_vision/sources/aegis.py`
- Append to: `tests/test_sources.py`

- [ ] **Step 1: Write tests**

Append to `tests/test_sources.py`:

```python
from hermes_vision.sources.aegis import AegisSource


def test_aegis_source_no_dir():
    source = AegisSource("/nonexistent/audit.jsonl")
    events = source.poll(0.0)
    assert events == []


def test_aegis_source_reads_events():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = f.name
        f.write(json.dumps({
            "timestamp": 1710417293.567,
            "tool_name": "terminal",
            "decision": "DANGEROUS_COMMAND",
            "middleware": "AuditTrailMiddleware",
            "args_redacted": {"command": "rm -rf /", "_danger_type": "destructive file operation"},
        }) + "\n")
    try:
        source = AegisSource(path)
        events = source.poll(0.0)
        assert len(events) == 1
        assert events[0].kind == "threat_blocked"
        assert events[0].severity == "danger"
    finally:
        os.unlink(path)


def test_aegis_disabled():
    source = AegisSource("/nonexistent", enabled=False)
    events = source.poll(0.0)
    assert events == []
```

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Implement sources/aegis.py**

```python
"""Optional Aegis audit trail tailer. Gracefully returns empty if unavailable."""

from __future__ import annotations

import json
import os
import time
from typing import List

from hermes_vision.events import VisionEvent

DEFAULT_PATH = os.path.expanduser("~/.hermes-aegis/audit.jsonl")

DECISION_MAP = {
    "DANGEROUS_COMMAND": ("threat_blocked", "danger"),
    "BLOCKED": ("threat_blocked", "danger"),
    "OUTPUT_REDACTED": ("secret_redacted", "warning"),
    "SECRET_DETECTED": ("secret_detected", "warning"),
    "ANOMALY": ("rate_anomaly", "warning"),
    "INITIATED": (None, None),  # skip routine audit entries
    "COMPLETED": (None, None),
}


class AegisSource:
    def __init__(self, path: str = DEFAULT_PATH, enabled: bool = True):
        self._path = path
        self._enabled = enabled
        self._offset: int = 0

    def poll(self, since: float) -> List[VisionEvent]:
        if not self._enabled or not os.path.exists(self._path):
            return []

        events: List[VisionEvent] = []
        try:
            with open(self._path, "r") as f:
                f.seek(self._offset)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        decision = data.get("decision", "")
                        kind, severity = DECISION_MAP.get(decision, ("threat_blocked", "warning"))
                        if kind is None:
                            continue
                        events.append(VisionEvent(
                            timestamp=data.get("timestamp", time.time()),
                            source="aegis",
                            kind=kind,
                            severity=severity,
                            data={
                                "tool_name": data.get("tool_name", ""),
                                "decision": decision,
                                "args": data.get("args_redacted", {}),
                            },
                        ))
                    except (json.JSONDecodeError, KeyError):
                        continue
                self._offset = f.tell()
        except OSError:
            pass

        return events
```

- [ ] **Step 4: Run tests**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_sources.py -v
```

- [ ] **Step 5: Commit**

```bash
git add hermes_vision/sources/aegis.py tests/test_sources.py
git commit -m "feat: optional Aegis audit trail event source"
```

### Task 13: Create sources/hook_handler.py — Gateway hook

**Files:**
- Create: `hermes_vision/sources/hook_handler.py`

This file is standalone — it runs inside the Hermes gateway process, not inside hermes-vision. It must not import from `hermes_vision`.

- [ ] **Step 1: Write test for hook handler**

Append to `tests/test_sources.py`:

```python
def test_hook_handler_writes_jsonl():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "events.jsonl")

        # Import and test the handle function directly
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "hook_handler",
            os.path.join(os.path.dirname(__file__), "..", "hermes_vision", "sources", "hook_handler.py")
        )
        module = importlib.util.module_from_spec(spec)

        # Patch the output path before loading
        os.environ["HERMES_VISION_EVENTS_PATH"] = output_path
        spec.loader.exec_module(module)

        # Simulate a hook call
        module.handle("agent:start", {"session_id": "test123", "platform": "local"})

        # Verify output
        with open(output_path) as f:
            line = f.readline()
            data = json.loads(line)
            assert data["event_type"] == "agent:start"
            assert data["context"]["session_id"] == "test123"
            assert "timestamp" in data

        del os.environ["HERMES_VISION_EVENTS_PATH"]
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement hook_handler.py**

```python
"""
Gateway hook handler for Hermes Vision.

This file is STANDALONE — it runs inside the Hermes gateway process.
It must NOT import from hermes_vision or any non-stdlib package.

Install:
    mkdir -p ~/.hermes/hooks/hermes-vision
    cp this_file.py ~/.hermes/hooks/hermes-vision/handler.py
    # Create HOOK.yaml alongside it (see below)
"""

import json
import os
import time

_EVENTS_PATH = os.environ.get(
    "HERMES_VISION_EVENTS_PATH",
    os.path.expanduser("~/.hermes/vision/events.jsonl"),
)


def handle(event_type: str, context: dict) -> None:
    """Append event as JSON line. Called by Hermes gateway hook system."""
    os.makedirs(os.path.dirname(_EVENTS_PATH), exist_ok=True)

    entry = {
        "timestamp": time.time(),
        "event_type": event_type,
        "context": context or {},
    }

    try:
        with open(_EVENTS_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # Never crash the gateway
```

- [ ] **Step 4: Create HOOK.yaml template**

Create `hermes_vision/sources/HOOK.yaml`:

```yaml
name: hermes-vision
description: Emits agent lifecycle events to the Hermes Vision neurovisualizer
events:
  - agent:start
  - agent:step
  - agent:end
  - session:start
  - session:reset
  - command:*
```

- [ ] **Step 5: Run tests**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_sources.py -v
```

- [ ] **Step 6: Commit**

```bash
git add hermes_vision/sources/hook_handler.py hermes_vision/sources/HOOK.yaml tests/test_sources.py
git commit -m "feat: gateway hook handler for custom events"
```

---

## Chunk 3: Bridge + Log Overlay + Live Mode

### Task 14: Create bridge.py — Event to visual mapping

**Files:**
- Create: `hermes_vision/bridge.py`
- Create: `tests/test_bridge.py`

- [ ] **Step 1: Write tests**

```python
from hermes_vision.bridge import Bridge, VisualTrigger
from hermes_vision.events import VisionEvent
import time


def test_visual_trigger_creation():
    t = VisualTrigger("packet", 0.7, "accent", "random_edge")
    assert t.effect == "packet"


def test_bridge_maps_agent_start():
    bridge = Bridge()
    ev = VisionEvent(time.time(), "agent", "agent_start", "info", {})
    triggers = bridge.translate(ev)
    assert len(triggers) == 1
    assert triggers[0].effect == "wake"
    assert triggers[0].intensity == 1.0


def test_bridge_maps_threat_blocked():
    bridge = Bridge()
    ev = VisionEvent(time.time(), "aegis", "threat_blocked", "danger", {})
    triggers = bridge.translate(ev)
    assert len(triggers) == 1
    assert triggers[0].effect == "pulse"
    assert triggers[0].color_key == "warning"


def test_bridge_maps_token_update():
    bridge = Bridge()
    ev = VisionEvent(time.time(), "state_db", "token_update", "info", {"delta_input": 500, "delta_output": 200})
    triggers = bridge.translate(ev)
    assert len(triggers) == 1
    assert triggers[0].effect == "pulse"
    intensity = triggers[0].intensity
    assert 0.1 <= intensity <= 1.0


def test_bridge_unknown_event():
    bridge = Bridge()
    ev = VisionEvent(time.time(), "unknown", "something_new", "info", {})
    triggers = bridge.translate(ev)
    assert triggers == []  # unknown events produce no triggers
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement bridge.py**

```python
"""Bridge — maps VisionEvents to VisualTriggers for the scene."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from hermes_vision.events import VisionEvent


@dataclass
class VisualTrigger:
    effect: str       # "packet", "pulse", "spawn_node", "burst", "flash", "dim", "wake", "cool_down"
    intensity: float  # 0.0 - 1.0
    color_key: str    # "accent", "warning", "bright", "soft", "base"
    target: str       # "random_node", "center", "random_edge", "all", "new"


# Static mapping: kind -> (effect, intensity, color_key, target)
# For token_update, intensity is computed dynamically
_MAPPING = {
    "agent_start":       ("wake",       1.0, "accent",  "all"),
    "agent_end":         ("cool_down",  1.0, "soft",    "all"),
    "agent_step":        ("pulse",      0.3, "soft",    "random_node"),
    "session_start":     ("spawn_node", 0.8, "bright",  "new"),
    "session_reset":     ("burst",      0.6, "accent",  "center"),
    "command_executed":  ("packet",     0.4, "soft",    "random_edge"),
    "tool_call":         ("packet",     0.7, "accent",  "random_edge"),
    "tool_complete":     ("pulse",      0.5, "bright",  "random_node"),
    "thinking":          ("dim",        0.3, "soft",    "all"),
    "token_update":      ("pulse",      0.5, "base",    "all"),  # intensity overridden dynamically below
    "model_switch":      ("flash",      0.6, "accent",  "all"),
    "memory_created":    ("spawn_node", 0.9, "bright",  "new"),
    "memory_accessed":   ("pulse",      0.4, "soft",    "random_node"),
    "memory_count_changed": ("pulse",   0.3, "soft",    "all"),
    "cron_executing":    ("pulse",      0.7, "accent",  "center"),
    "cron_completed":    ("burst",      0.8, "bright",  "random_node"),
    "cron_failed":       ("flash",      0.9, "warning", "center"),
    "threat_blocked":    ("pulse",      1.0, "warning", "center"),
    "secret_redacted":   ("flash",      0.8, "warning", "random_edge"),
    "secret_detected":   ("flash",      0.9, "warning", "random_node"),
    "rate_anomaly":      ("dim",        0.6, "warning", "all"),
    "task_completed":    ("burst",      0.8, "bright",  "random_node"),
    "skill_activated":   ("packet",     0.6, "accent",  "random_edge"),
    "error":             ("flash",      0.7, "warning", "random_node"),
    "file_written":      ("packet",     0.4, "soft",    "random_edge"),
    "web_search":        ("pulse",      0.5, "accent",  "center"),
    "image_generated":   ("burst",      0.7, "bright",  "random_node"),
    "active_session":    ("pulse",      0.3, "soft",    "center"),
    "message_added":     ("packet",     0.3, "soft",    "random_edge"),
}


class Bridge:
    """Translates VisionEvents into VisualTriggers."""

    def translate(self, event: VisionEvent) -> List[VisualTrigger]:
        entry = _MAPPING.get(event.kind)
        if entry is None:
            return []

        effect, intensity, color_key, target = entry

        # Dynamic intensity for token_update
        if event.kind == "token_update":
            delta = event.data.get("delta_input", 0) + event.data.get("delta_output", 0)
            intensity = max(0.1, min(1.0, delta / 1000.0))

        return [VisualTrigger(effect, intensity, color_key, target)]
```

- [ ] **Step 4: Run tests**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_bridge.py -v
```

- [ ] **Step 5: Commit**

```bash
git add hermes_vision/bridge.py tests/test_bridge.py
git commit -m "feat: event-to-visual bridge with full mapping table"
```

### Task 15: Create log_overlay.py

**Files:**
- Create: `hermes_vision/log_overlay.py`
- Create: `tests/test_log_overlay.py`

- [ ] **Step 1: Write tests**

```python
import time
from hermes_vision.log_overlay import LogOverlay
from hermes_vision.events import VisionEvent


def test_log_overlay_add_event():
    overlay = LogOverlay(max_lines=10)
    ev = VisionEvent(time.time(), "agent", "agent_start", "info", {"session_id": "abc", "model": "gpt-4"})
    overlay.add_event(ev)
    lines = overlay.get_visible_lines(time.time())
    assert len(lines) == 1
    assert "agent:start" in lines[0][0]


def test_log_overlay_fading():
    overlay = LogOverlay(max_lines=10)
    old_time = time.time() - 5.0  # 5 seconds ago
    ev = VisionEvent(old_time, "agent", "tool_call", "info", {"tool_name": "web_search"})
    overlay.add_event(ev)
    lines = overlay.get_visible_lines(time.time())
    # Should still be visible (< 8s) but dimmed (> 3s)
    assert len(lines) == 1
    assert lines[0][1] == "dim"


def test_log_overlay_expiry():
    overlay = LogOverlay(max_lines=10)
    old_time = time.time() - 10.0  # 10 seconds ago
    ev = VisionEvent(old_time, "agent", "tool_call", "info", {})
    overlay.add_event(ev)
    lines = overlay.get_visible_lines(time.time())
    assert len(lines) == 0  # expired


def test_log_overlay_max_lines():
    overlay = LogOverlay(max_lines=3)
    now = time.time()
    for i in range(5):
        overlay.add_event(VisionEvent(now + i * 0.1, "agent", "agent_step", "info", {}))
    lines = overlay.get_visible_lines(now + 1.0)
    assert len(lines) <= 3


def test_log_overlay_color_by_source():
    overlay = LogOverlay(max_lines=10)
    now = time.time()
    overlay.add_event(VisionEvent(now, "agent", "agent_start", "info", {}))
    overlay.add_event(VisionEvent(now, "aegis", "threat_blocked", "danger", {}))
    lines = overlay.get_visible_lines(now)
    # First line (agent) should be cyan, second (aegis) should be yellow
    assert lines[0][2] == "cyan"
    assert lines[1][2] == "yellow"
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement log_overlay.py**

```python
"""Log overlay — fading scrolling text rendered over the neural network."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Tuple

from hermes_vision.events import VisionEvent

FADE_AFTER = 3.0    # seconds before dimming
EXPIRE_AFTER = 8.0  # seconds before removal

SOURCE_COLORS = {
    "agent": "cyan",
    "state_db": "white",
    "memory": "magenta",
    "cron": "cyan",
    "aegis": "yellow",
    "custom": "green",
}


@dataclass
class LogLine:
    text: str
    timestamp: float
    color: str


def _format_event(ev: VisionEvent) -> str:
    """Format event into a single log line."""
    ts = time.strftime("%H:%M:%S", time.localtime(ev.timestamp))
    data = ev.data

    if ev.kind == "agent_start":
        session = data.get("session_id", "")[:6]
        model = data.get("model", "")
        return f"[{ts}] agent:start session={session} model={model}"
    elif ev.kind == "agent_end":
        return f"[{ts}] agent:end"
    elif ev.kind == "agent_step":
        tools = data.get("tool_names", [])
        return f"[{ts}] agent:step tools={','.join(tools) if tools else 'none'}"
    elif ev.kind == "tool_call":
        name = data.get("tool_name", data.get("function_name", "?"))
        return f"[{ts}] > tool:{name}"
    elif ev.kind == "tool_complete":
        name = data.get("tool_name", "?")
        return f"[{ts}] < tool:{name}"
    elif ev.kind == "memory_created":
        name = data.get("name", data.get("path", "?"))
        return f"[{ts}] memory:created \"{name}\""
    elif ev.kind == "memory_accessed":
        name = data.get("name", "?")
        return f"[{ts}] memory:accessed \"{name}\""
    elif ev.kind == "token_update":
        inp = data.get("input_tokens", 0)
        out = data.get("output_tokens", 0)
        return f"[{ts}] tokens: {inp:,} in / {out:,} out"
    elif ev.kind == "cron_executing":
        return f"[{ts}] cron:executing"
    elif ev.kind == "cron_completed":
        job = data.get("output", "")
        return f"[{ts}] cron:completed {job}"
    elif ev.kind == "cron_failed":
        return f"[{ts}] cron:failed"
    elif ev.kind == "threat_blocked":
        cmd = data.get("decision", "")
        tool = data.get("tool_name", "")
        return f"[{ts}] aegis:blocked {cmd} ({tool})"
    elif ev.kind == "secret_redacted":
        return f"[{ts}] aegis:redacted"
    elif ev.kind == "secret_detected":
        return f"[{ts}] aegis:secret_detected"
    elif ev.kind == "model_switch":
        return f"[{ts}] model:{data.get('model', '?')}"
    elif ev.kind == "active_session":
        return f"[{ts}] session:{data.get('session_id', '?')[:6]}"
    elif ev.kind == "message_added":
        role = data.get("role", "?")
        tool = data.get("tool_name", "")
        suffix = f" ({tool})" if tool else ""
        return f"[{ts}] msg:{role}{suffix}"
    else:
        return f"[{ts}] {ev.kind}"


class LogOverlay:
    def __init__(self, max_lines: int = 20):
        self._lines: List[LogLine] = []
        self._max_lines = max_lines

    def add_event(self, event: VisionEvent) -> None:
        text = _format_event(event)
        color = SOURCE_COLORS.get(event.source, "white")
        self._lines.append(LogLine(text, event.timestamp, color))
        # Keep buffer bounded
        if len(self._lines) > self._max_lines * 2:
            self._lines = self._lines[-self._max_lines:]

    def get_visible_lines(self, now: float) -> List[Tuple[str, str, str]]:
        """Returns list of (text, brightness, color) tuples. brightness is 'bold' or 'dim'."""
        visible = []
        for line in self._lines:
            age = now - line.timestamp
            if age >= EXPIRE_AFTER:
                continue
            brightness = "dim" if age >= FADE_AFTER else "bold"
            visible.append((line.text, brightness, line.color))
        return visible[-self._max_lines:]
```

- [ ] **Step 4: Run tests**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_log_overlay.py -v
```

- [ ] **Step 5: Commit**

```bash
git add hermes_vision/log_overlay.py tests/test_log_overlay.py
git commit -m "feat: fading log overlay for event display"
```

### Task 16: Wire up Live mode + apply_trigger in scene.py

**Files:**
- Modify: `hermes_vision/scene.py` — implement `apply_trigger()`
- Modify: `hermes_vision/app.py` — add `LiveApp` class
- Modify: `hermes_vision/renderer.py` — add log overlay rendering
- Modify: `hermes_vision/cli.py` — wire up `--live` mode

- [ ] **Step 1: Add tests for apply_trigger**

Append to `tests/test_scene.py`:

```python
from hermes_vision.scene import ThemeState
from hermes_vision.themes import build_theme_config


class FakeTrigger:
    def __init__(self, effect, intensity=0.7, color_key="accent", target="random_node"):
        self.effect = effect
        self.intensity = intensity
        self.color_key = color_key
        self.target = target


def test_apply_trigger_packet():
    config = build_theme_config("neural-sky")
    state = ThemeState(config, 100, 30, seed=42)
    before = len(state.packets)
    state.apply_trigger(FakeTrigger("packet", target="random_edge"))
    assert len(state.packets) > before


def test_apply_trigger_burst():
    config = build_theme_config("neural-sky")
    state = ThemeState(config, 100, 30, seed=42)
    before = len(state.particles)
    state.apply_trigger(FakeTrigger("burst", intensity=0.8))
    assert len(state.particles) > before


def test_apply_trigger_pulse():
    config = build_theme_config("neural-sky")
    state = ThemeState(config, 100, 30, seed=42)
    before = len(state.pulses)
    state.apply_trigger(FakeTrigger("pulse"))
    assert len(state.pulses) > before


def test_apply_trigger_wake():
    config = build_theme_config("neural-sky")
    state = ThemeState(config, 100, 30, seed=42)
    state.apply_trigger(FakeTrigger("wake"))
    assert state._intensity_target == 1.0


def test_apply_trigger_cool_down():
    config = build_theme_config("neural-sky")
    state = ThemeState(config, 100, 30, seed=42)
    state.apply_trigger(FakeTrigger("cool_down"))
    assert state._intensity_target == 0.3


def test_apply_trigger_spawn_node():
    config = build_theme_config("neural-sky")
    state = ThemeState(config, 100, 30, seed=42)
    before = len(state.nodes)
    state.apply_trigger(FakeTrigger("spawn_node", target="new"))
    assert len(state.nodes) == before + 1
```

Run: `python -m pytest tests/test_scene.py -v -k "apply_trigger"` — Expected: FAIL (apply_trigger is still a stub)

- [ ] **Step 2: Implement apply_trigger in scene.py**

Replace the stub `apply_trigger()` from Task 3 with the full implementation.

Add to `ThemeState.apply_trigger()`:

```python
def apply_trigger(self, trigger) -> None:
    """Apply a VisualTrigger to the scene state."""
    effect = trigger.effect
    intensity = trigger.intensity

    if effect == "packet" and self.edges:
        edge_idx = self.rng.randrange(len(self.edges))
        edge = self.edges[edge_idx]
        speed = 0.04 + intensity * 0.06
        self.packets.append(Packet((edge[0], edge[1]), 0.0, speed))

    elif effect == "pulse" and self.nodes:
        if trigger.target == "center":
            idx = len(self.nodes) // 2
        else:
            idx = self.rng.randrange(len(self.nodes))
        nx, ny = self.nodes[idx]
        self.pulses.append((nx, ny, 0.0))

    elif effect == "burst" and self.nodes:
        if trigger.target == "center":
            idx = len(self.nodes) // 2
        else:
            idx = self.rng.randrange(len(self.nodes))
        nx, ny = self.nodes[idx]
        for _ in range(int(3 + intensity * 5)):
            vx = self.rng.uniform(-0.3, 0.3) * intensity
            vy = self.rng.uniform(-0.2, 0.2) * intensity
            life = self.rng.randint(6, 14)
            self.particles.append(Particle(nx, ny, vx, vy, life, life, self.rng.choice(".:*+@")))

    elif effect == "flash":
        pass  # Flash is handled by renderer checking a flash_until timestamp

    elif effect == "spawn_node":
        if len(self._dynamic_nodes) >= self.MAX_DYNAMIC_NODES:
            oldest = self._dynamic_nodes.pop(0)
            if oldest < len(self.nodes):
                self.nodes.pop(oldest)
        x = self.rng.uniform(4, max(5, self.width - 5))
        y = self.rng.uniform(2, max(3, self.height - 3))
        self.nodes.append((x, y))
        self._dynamic_nodes.append(len(self.nodes) - 1)
        self._build_edges()

    elif effect == "wake":
        self._intensity_target = 1.0
        self._intensity_rate = 0.15  # fast ramp up

    elif effect == "cool_down":
        self._intensity_target = 0.3
        self._intensity_rate = 0.05  # slow fade

    elif effect == "dim":
        self.intensity_multiplier = max(0.2, self.intensity_multiplier - 0.2)
        self._intensity_target = 0.6  # recover to base
        self._intensity_rate = 0.08
```

Add `_dynamic_nodes: List[int] = field(default_factory=list)` to ThemeState.

Add `flash_until: float = 0.0` and `flash_color_key: str = "warning"` fields to ThemeState.

For flash effect:
```python
elif effect == "flash":
    import time as _time
    self.flash_until = _time.time() + 0.3 * intensity
    self.flash_color_key = trigger.color_key
```

- [ ] **Step 3: Run apply_trigger tests**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/test_scene.py -v -k "apply_trigger"
```

Expected: All 6 apply_trigger tests PASS

- [ ] **Step 4: Add LiveApp to app.py**

```python
class LiveApp:
    """Live mode — polls events and maps them to visual triggers."""

    def __init__(self, stdscr, theme_name, poller, bridge, log_overlay, end_after=None, show_logs=False):
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

    def run(self):
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

    def _draw_logs(self, now):
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

    def _handle_input(self):
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
```

- [ ] **Step 5: Wire up CLI --live mode**

Update `cli.py` `main()` to handle `--live`:

```python
def _run_live(args):
    from hermes_vision.app import LiveApp
    from hermes_vision.events import EventPoller
    from hermes_vision.bridge import Bridge
    from hermes_vision.log_overlay import LogOverlay
    from hermes_vision.sources.custom import CustomSource
    from hermes_vision.sources.state_db import StateDbSource
    from hermes_vision.sources.memories import MemoriesSource
    from hermes_vision.sources.cron import CronSource
    from hermes_vision.sources.aegis import AegisSource

    sources = [
        CustomSource().poll,
        StateDbSource().poll,
        MemoriesSource().poll,
        CronSource().poll,
    ]
    if not args.no_aegis:
        sources.append(AegisSource().poll)

    poller = EventPoller(sources=sources)
    bridge = Bridge()
    log_overlay = LogOverlay()

    def run_curses(stdscr):
        app = LiveApp(stdscr, args.theme, poller, bridge, log_overlay,
                      end_after=args.seconds, show_logs=args.logs)
        app.run()

    curses.wrapper(run_curses)
```

Update the mode dispatch in `main()`:
```python
if args.gallery:
    _run_gallery(args)
elif args.daemon:
    print("Daemon mode not yet implemented.", file=sys.stderr)
    sys.exit(1)
else:
    _run_live(args)  # --live is the default
```

- [ ] **Step 6: Smoke test live mode**

```bash
cd ~/Projects/hermes-vision && python -m hermes_vision --live --seconds 5
```

Expected: Neural network animation runs for 5 seconds, reading live data from state.db.

```bash
cd ~/Projects/hermes-vision && python -m hermes_vision --live --logs --seconds 5
```

Expected: Same, but with log overlay showing any detected events.

- [ ] **Step 7: Commit**

```bash
git add hermes_vision/scene.py hermes_vision/app.py hermes_vision/renderer.py hermes_vision/cli.py tests/test_scene.py
git commit -m "feat: live mode with event polling, bridge, and log overlay"
```

---

## Chunk 4: Polish + Install

### Task 17: Install as CLI tool + hook installation

**Files:**
- Modify: `pyproject.toml` (verify entry point)
- Create install helper

- [ ] **Step 1: Install package in editable mode**

```bash
cd ~/Projects/hermes-vision && pip install -e .
```

- [ ] **Step 2: Test CLI entry point**

```bash
hermes-vision --gallery --seconds 3
hermes-vision --live --seconds 3
hermes-vision --live --logs --seconds 3
```

- [ ] **Step 3: Install gateway hook**

```bash
mkdir -p ~/.hermes/hooks/hermes-vision
cp ~/Projects/hermes-vision/hermes_vision/sources/hook_handler.py ~/.hermes/hooks/hermes-vision/handler.py
cp ~/Projects/hermes-vision/hermes_vision/sources/HOOK.yaml ~/.hermes/hooks/hermes-vision/HOOK.yaml
```

- [ ] **Step 4: Verify hook loads**

Restart hermes gateway (or run a hermes command) and check for:
```
[hooks] Loaded hook 'hermes-vision' for events: [...]
```

- [ ] **Step 5: Commit any final adjustments**

```bash
git add -A
git commit -m "chore: finalize installation and hook setup"
```

### Task 18: Run full test suite

- [ ] **Step 1: Run all tests**

```bash
cd ~/Projects/hermes-vision && python -m pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 2: Run headless gallery verification**

```bash
cd ~/Projects/hermes-vision && echo "" | hermes-vision --gallery --seconds 2
```

Expected: Headless output with stats.

- [ ] **Step 3: Run live mode with log overlay for 10 seconds to visually verify**

```bash
hermes-vision --live --logs --seconds 10
```

Expected: Neural network animates, picks up any current state.db activity, log lines appear if events are flowing.

### Task 19: Create CLAUDE.md for the project

**Files:**
- Create: `~/Projects/hermes-vision/CLAUDE.md`

- [ ] **Step 1: Write CLAUDE.md**

```markdown
# Hermes Vision

Terminal neurovisualizer for Hermes Agent. Pure Python, stdlib only.

## Quick Start

```bash
pip install -e .
hermes-vision --gallery    # screensaver mode
hermes-vision --live       # real-time event visualization
hermes-vision --live --logs # with scrolling log overlay
```

## Architecture

- `themes.py` — 10 theme configs
- `scene.py` — particle/packet/pulse simulation
- `renderer.py` — curses drawing
- `events.py` — unified event model + poller
- `bridge.py` — event → visual trigger mapping
- `log_overlay.py` — fading text overlay
- `app.py` — GalleryApp + LiveApp
- `cli.py` — entry point
- `sources/` — event sources (state_db, memories, cron, aegis, custom)

## Testing

```bash
python -m pytest tests/ -v
```

## Gateway Hook

Install to `~/.hermes/hooks/hermes-vision/` — see sources/hook_handler.py and sources/HOOK.yaml.
```

- [ ] **Step 2: Register with grove**

```bash
grove register ~/Projects/hermes-vision --priority 3
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md project guide"
```
