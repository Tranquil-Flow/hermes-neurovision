# Hermes Vision — Neurovisualizer Design Spec

**Date:** 2026-03-13
**Status:** Approved
**Author:** Evi + Claude

## Overview

Hermes Vision is a terminal-native (curses) neurovisualizer that displays a living neural network animation reactive to real events from Hermes Agent. It shows glowing nodes, pulsating edges, travelling packets, expanding pulses, and particle bursts — all driven by actual agent activity (tool calls, token usage, memory operations, cron jobs, and optionally security events from Hermes Aegis).

## Prior Art

An existing `neurovisualizer.py` (846 lines, pure Python/curses) lives at `~/Desktop/neurovisualizer.py`. Built by Hermes Agent in a prior session. It has 10 themes, a particle/packet/pulse system, gallery rotation mode, and headless CI mode. Hermes Vision extracts and extends this into a proper project.

## Architecture

### Approach: Clean Architecture (B)

Separate package with extracted visual engine, new event system, and bridge layer mapping events to visual triggers.

### Rendering: Terminal-native (curses)

Pure Python, stdlib only (`curses`, `sqlite3`, `json`, `os`, `math`, `random`). No external dependencies for the `hermes_vision` package itself. Note: the gateway hook's `HOOK.yaml` manifest is consumed by the existing Hermes gateway process (which has PyYAML as a dependency). The hook's `handler.py` is stdlib-only.

### Data: Hybrid (C + A)

- **Primary:** Poll SQLite (`state.db`) + tail Aegis audit trail for rich historical data
- **Secondary:** Custom event channel (`~/.hermes/vision/events.jsonl`) fed by a gateway hook for real-time agent lifecycle events

### Aegis: Optional

All Aegis-related code gracefully degrades. If `~/.hermes-aegis/` doesn't exist, the Aegis source returns empty lists. Never raises, never blocks.

## Project Structure

```
~/Projects/hermes-vision/
  hermes_vision/
    __init__.py
    cli.py              # argparse entry: --live, --gallery, --theme, --daemon
    events.py           # EventPoller — unified polling across all sources
    bridge.py           # Maps unified events -> visual triggers
    scene.py            # ThemeState, Particle, Packet, Node, Edge
    themes.py           # ThemeConfig definitions (10 themes)
    renderer.py         # Curses Renderer
    app.py              # GalleryApp / LiveApp orchestrator
    sources/
      __init__.py
      state_db.py       # SQLite poller for state.db
      memories.py       # Filesystem watcher for ~/.hermes/memories/
      cron.py           # Cron job status poller
      aegis.py          # Audit trail tailer (optional)
      custom.py         # JSONL tailer for ~/.hermes/vision/events.jsonl
      hook_handler.py   # Gateway hook handler — standalone, stdlib-only, gets copied to ~/.hermes/hooks/hermes-vision/handler.py. Must not import from hermes_vision.
  pyproject.toml
  README.md
```

## Event System

### Unified Event Model

```python
@dataclass
class VisionEvent:
    timestamp: float
    source: str        # "agent", "state_db", "memory", "cron", "aegis", "custom"
    kind: str          # "tool_call", "token_update", "memory_created", etc.
    severity: str      # "info", "warning", "danger"
    data: dict         # Source-specific payload
```

### EventPoller

Runs on ~1s interval. Each source module exposes `poll(since: float) -> list[VisionEvent]`. Sources that don't exist return empty lists.

| Source | Poll Method | State Tracking |
|---|---|---|
| `state_db.py` | SELECT queries against sessions + messages tables | Last seen message rowid + session state snapshot |
| `memories.py` | os.scandir() + compare mtimes | Dict of path->mtime |
| `cron.py` | Read job files + check lock/output | Last known job states |
| `aegis.py` | Seek to last position in audit.jsonl | File seek offset |
| `custom.py` | Seek to last position in events.jsonl | File seek offset |

#### state_db.py Query Mapping

The `sessions` table uses `id TEXT PRIMARY KEY` (UUIDs) and the `messages` table uses `id INTEGER PRIMARY KEY AUTOINCREMENT`. Derivation logic for each event:

| Event | Query / Derivation |
|---|---|
| `message_added` | `SELECT * FROM messages WHERE id > last_seen_rowid` |
| `active_session` | `SELECT id, model FROM sessions WHERE ended_at IS NULL ORDER BY started_at DESC LIMIT 1` |
| `token_update` | Compare `sessions.input_tokens + output_tokens` for the active session against last seen values |
| `model_switch` | Detect when `sessions.model` changes between polls for the active session |
| `session_duration` | Compute from `started_at` of the active session vs current time |
| `tool_usage_pattern` | Derive from message content/role patterns in new messages (post-MVP — can stub initially) |

### Gateway Hook

Subscribes to: `agent:start`, `agent:step`, `agent:end`, `session:start`, `session:reset`, `command:*`

On each event, appends a JSON line to `~/.hermes/vision/events.jsonl`. Installed at `~/.hermes/hooks/hermes-vision/` with `HOOK.yaml` + `handler.py`.

### Complete Event Catalog (35+ types)

**Core (always available):**
- `agent_start`, `agent_end`, `agent_step`
- `session_start`, `session_reset`
- `command_executed`
- `tool_call`, `tool_complete`, `thinking`

**SQLite (polled):**
- `token_update`, `message_added`, `tool_usage_pattern`
- `active_session`, `model_switch`, `session_duration`

**Memory (polled):**
- `memory_created`, `memory_accessed`, `memory_count_changed`

**Cron (polled):**
- `cron_scheduled`, `cron_executing`, `cron_completed`, `cron_failed`, `cron_next_tick`

**Trajectory (post-MVP, polled):**
- `trajectory_logged`, `trajectory_failed`
- Source: `~/.hermes/logs/trajectory_samples.jsonl` and `failed_trajectories.jsonl`
- Deferred from MVP — the other sources provide sufficient signal

**Aegis (optional, polled):**
- `threat_blocked`, `secret_redacted`, `secret_detected`
- `rate_anomaly`, `chain_integrity`, `aegis_tier`

**Custom (tailed):**
- `task_completed`, `skill_activated`, `error`
- `file_written`, `web_search`, `image_generated`

## Bridge — Event to Visual Mapping

### Visual Trigger Model

```python
@dataclass
class VisualTrigger:
    effect: str          # "packet", "pulse", "spawn_node", "burst", "flash", "dim", "wake", "cool_down"
    intensity: float     # 0.0 - 1.0
    color_key: str       # "accent", "warning", "bright", "soft", "base"
    target: str          # "random_node", "center", "random_edge", "all", "new"
```

### Mapping Table

| Event Kind | Effect | Intensity | Color | Target |
|---|---|---|---|---|
| `agent_start` | wake | 1.0 | accent | all |
| `agent_end` | cool_down | 1.0 | soft | all |
| `session_start` | spawn_node | 0.8 | bright | new |
| `session_reset` | burst | 0.6 | accent | center |
| `tool_call` | packet | 0.7 | accent | random_edge |
| `tool_complete` | pulse | 0.5 | bright | random_node |
| `thinking` | dim | 0.3 | soft | all |
| `token_update` | pulse | proportional to delta_tokens / 1000, clamped [0.1, 1.0] | base | all |
| `model_switch` | flash | 0.6 | accent | all |
| `memory_created` | spawn_node | 0.9 | bright | new |
| `memory_accessed` | pulse | 0.4 | soft | random_node |
| `cron_executing` | pulse | 0.7 | accent | center |
| `cron_completed` | burst | 0.8 | bright | random_node |
| `cron_failed` | flash | 0.9 | warning | center |
| `threat_blocked` | pulse | 1.0 | warning | center |
| `secret_redacted` | flash | 0.8 | warning | random_edge |
| `secret_detected` | flash | 0.9 | warning | random_node |
| `rate_anomaly` | dim | 0.6 | warning | all |
| `task_completed` | burst | 0.8 | bright | random_node |
| `skill_activated` | packet | 0.6 | accent | random_edge |
| `error` | flash | 0.7 | warning | random_node |
| `file_written` | packet | 0.4 | soft | random_edge |
| `web_search` | pulse | 0.5 | accent | center |
| `image_generated` | burst | 0.7 | bright | random_node |

### Visual Effects

- **packet** — travelling glyph along an edge
- **pulse** — expanding ring from a node
- **burst** — multiple particles explode outward from a node
- **flash** — all edges briefly change color
- **spawn_node** — new node appears with edges to nearest neighbors. Max 64 dynamic nodes; when the limit is reached, the oldest dynamically-spawned node is removed before adding a new one.
- **wake** — sets a global intensity multiplier to 1.0 that decays back to the base level (0.6) over 5 seconds. Overrides any active cool_down.
- **cool_down** — sets the global intensity multiplier to 0.3, recovering to base level over 10 seconds. A new wake event overrides it immediately.
- **dim** — temporarily reduces global intensity multiplier by 0.2 for 3 seconds, then recovers

### Idle Behavior

When no events arrive for 10+ seconds, falls back to gentle generative mode (random particles/packets) so it never looks dead.

## Log Overlay Mode

Toggled via `--logs` flag or `l` key at runtime.

### Rendering

- Log lines render over the neural network visuals using full overlay
- Lines appear at bottom, scroll upward
- Max 15-20 visible lines depending on terminal height. Minimum terminal size for log overlay: 80x24. If terminal is smaller, log overlay is automatically disabled with a brief status message.
- Each line starts `A_BOLD`, fades to `A_DIM` after 3s, disappears after 8s
- Visual elements render behind — if a log line occupies a cell, the log text wins

### Color Coding

- Cyan: agent lifecycle
- Green: tool calls
- Magenta: memory operations
- Yellow: aegis/security events
- White: token/cost updates

### Log Format

```
[14:23:01] agent:start session=a3f2c1 model=claude-sonnet-4-6
[14:23:01] > tool:web_search query="python curses tutorial"
[14:23:03] < tool:web_search 3 results (1.2s, 847 tokens)
[14:23:06] > tool:write_file path="project/utils.py"
[14:23:07] memory:created "project architecture notes"
[14:23:08] cron:completed job="daily-summary" (success)
[14:23:09] aegis:blocked DANGEROUS_COMMAND "rm -rf /"
[14:23:10] tokens: 2,847 in / 1,203 out ($0.012)
[14:23:12] agent:end 6 turns, 4 tools, 4.1k tokens
```

## App Modes & CLI

### Modes

1. **Live** (`hermes-vision --live`) — Real-time event visualization. Default mode.
2. **Gallery** (`hermes-vision --gallery`) — Theme rotation screensaver. Generative only, no event polling.
3. **Daemon** (`hermes-vision --daemon`) — Gallery when idle, switches to live when events arrive, fades back when they stop. Log overlay state and theme selection persist across gallery/live transitions. Mode is fixed at launch — no runtime switching between live/gallery/daemon.
4. **Auto-launch** — Gateway hook spawns `hermes-vision --live --auto-exit` in a new terminal window/tmux pane when a cron job triggers `agent:start`. Exits 30s after last event.

### CLI

```
hermes-vision [mode] [options]

Modes:
  --live              Real-time event visualization (default)
  --gallery           Theme rotation screensaver
  --daemon            Persistent: gallery when idle, live when active

Options:
  --theme NAME        Theme to use (default: neural-sky)
  --theme-seconds N   Seconds per theme in gallery/daemon (default: 8)
  --logs              Enable log overlay
  --auto-exit         Exit 30s after last event
  --seconds N         Exit after N seconds (for testing)
  --no-aegis          Skip Aegis source even if available
```

### Keyboard Controls

```
q       quit
l       toggle log overlay
n/right next theme
p/left  previous theme
space   pause/resume
```

## Themes

All 10 themes from the existing neurovisualizer carry over:

1. neural-sky
2. electric-mycelium
3. cathedral-circuit
4. storm-core
5. hybrid
6. moonwire
7. rootsong
8. stormglass
9. spiral-galaxy
10. black-hole

## Hermes Agent Buildability

This project is designed to be built by Hermes Agent using its existing tools:

- `write_file_tool` for all Python files
- `terminal_tool` for running/testing
- `code_execution_tool` for validation
- No npm, no browser, no external deps
- Each file is small enough for Hermes's 40K context window
- The existing `neurovisualizer.py` code can be extracted and refactored into the new structure

## Installation

```bash
cd ~/Projects/hermes-vision
pip install -e .
```

Gateway hook installation:
```bash
mkdir -p ~/.hermes/hooks/hermes-vision
cp hermes_vision/sources/hook_handler.py ~/.hermes/hooks/hermes-vision/handler.py
# HOOK.yaml created by install script
```

## MVP Scope

For the first version:
- Extract existing neurovisualizer into the clean architecture
- Implement EventPoller with at least: custom events, state_db, and memories sources
- Implement Bridge with the full mapping table
- Live mode and gallery mode working
- Log overlay mode working
- Gateway hook writing events
- Aegis source present but optional
- Daemon mode and auto-launch can be post-MVP
