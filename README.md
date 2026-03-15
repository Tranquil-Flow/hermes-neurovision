# Hermes Neurovision

**Terminal neurovisualizer for Hermes Agent**

A full-screen ASCII art visualizer that reacts to your AI agent's activity in real-time. Every event your agent fires — tool calls, memory writes, session lifecycle — drives the visuals: field brightness, density, traveling packets, expanding pulses, particle bursts.

![Version](https://img.shields.io/badge/version-0.2.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Tests](https://img.shields.io/badge/tests-174%20passing-brightgreen)
![Dependencies](https://img.shields.io/badge/dependencies-stdlib%20only-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **58 Animated Themes** — Full-screen generative fields, hybrid node/field screens, and classic node graphs
- **Live Event Visualization** — Agent activity directly drives visual intensity, packets, pulses, and bursts
- **7 Data Sources** — Sessions, tool calls, memory writes, cron jobs, trajectories, security events
- **Log Overlay** — Color-coded live event stream with fading text
- **Tuner Overlay** — Real-time per-element controls: sliders for speed/density/sensitivity, on/off toggles for every visual layer
- **Debug Panel** — Live diagnostic overlay showing recent events and triggers with timing
- **Daemon Mode** — Gallery screensaver when idle, live mode when agent is active
- **Legacy Mode** — Access original node-based versions of redesigned themes
- **Pure Stdlib** — Zero external dependencies

---

## Quick Start

```bash
git clone https://github.com/Tranquil-Flow/hermes-neurovision.git
cd hermes-neurovision
pip install -e .
python3 install_helper.py   # installs gateway hook + auto-launch config
hermes-neurovision
```

---

## Usage

### Modes

```bash
# Live mode (default) — reacts to agent events, animated background
hermes-neurovision

# Quiet mode — only real agent events drive the visuals, no ambient animation
hermes-neurovision --quiet

# With log overlay to see event details
hermes-neurovision --logs

# Gallery mode — browse all themes
hermes-neurovision --gallery

# Gallery including legacy (original node-based) themes
hermes-neurovision --gallery --include-legacy

# Daemon mode — gallery when idle, live when active
hermes-neurovision --daemon

# Specific theme
hermes-neurovision --theme storm-core

# Test run (auto-exit)
hermes-neurovision --seconds 10

# List legacy themes
hermes-neurovision --list-legacy
```

### Keyboard Controls

**Gallery Mode:**
- `n` / `→` — Next theme
- `p` / `←` — Previous theme
- `Shift+→` / `Shift+←` — Jump forward/back in theme list
- `Enter` — Lock current theme
- `s` — Select theme for live mode
- `Space` — Pause/Resume
- `t` — Open tuner overlay
- `d` — Toggle debug panel
- `q` — Quit

**Live Mode:**
- `l` — Toggle log overlay
- `t` — Open tuner overlay
- `d` — Toggle debug panel
- `q` — Quit

**Tuner Overlay (press `t`):**
- `↑` / `↓` — Navigate rows
- `←` / `→` — Adjust slider / toggle on/off
- `r` — Reset all to defaults
- `t` — Close

---

## Visual Engine

Hermes Neurovision has two rendering engines. Every theme uses one or both.

### ASCII Field Engine

The primary engine for v0.2.0. Every character cell on screen is computed each frame from a mathematical function — fluid simulation, particle fields, strange attractors, wave equations. The entire terminal is a live canvas.

Agent events drive `intensity_multiplier`: as your agent works, the field brightens, speeds up, and densifies. When the agent is idle, the field settles to a calm ambient state.

Themes using the ASCII field engine return no nodes — the field is the entire visual.

### Node-Based Engine (Legacy / Hybrid)

The original engine. A graph of nodes is positioned on screen, connected by edges. Agent events cause packets to travel along edges, pulses to radiate from nodes, and particle bursts on task completion.

This engine is more *legible* — you can literally watch a packet travel from one node to another when a tool call fires. The tradeoff is that screens are sparser.

Node-based themes are being progressively redesigned to the ASCII field engine. The originals are preserved as `legacy-NAME` variants (see [Legacy Mode](#legacy-mode) below).

### Hybrid Engine

Themes can use both engines simultaneously:

- `draw_background()` — renders an ASCII field as a backdrop, called **before** nodes/edges
- `draw_extras()` — renders foreground effects, called **after** packets/particles

This allows a theme to have a rich generative field texture *and* retain the legible event storytelling of traveling packets and expanding pulses on top.

---

## Data Sources

Polled every second while running:

| Source | File/DB | What it watches |
|--------|---------|-----------------|
| **Agent state** | `~/.hermes/state.db` | Sessions, messages, tool calls, token usage |
| **Gateway hook** | `~/.hermes/neurovision/events.jsonl` | Agent start/stop, session lifecycle |
| **Memories** | `~/.hermes/memories/` | Files created or modified |
| **Cron jobs** | `~/.hermes/cron/` | Scheduled job execution |
| **Trajectories** | `~/.hermes/logs/` | Success/failure logs |
| **Aegis** (optional) | `~/.hermes-aegis/audit.jsonl` | Security events |

---

## Agent Activity → Visuals

Every visual change is caused by a real event. The baseline animation is always running, but agent actions trigger specific responses on top of it.

| What Hermes Does | What You See |
|-----------------|--------------|
| Session starts | **Wake** — network surges in brightness; field density spikes |
| Tool call executes | **Packet** — glyph travels along an edge (node themes); field brightens |
| Message added to context | **Pulse** — expanding ring from a node |
| Memory is created | **Spawn node** — new node appears |
| Task or session ends | **Burst** — particle explosion, then cool down |
| Token usage increases | **Intensity scales** — field density/speed proportional to load |
| Error or security threat | **Flash** — all edges change color; field flares |
| Thinking/processing state | **Dim** — temporary brightness reduction |
| 5+ tool calls in 10s | **Tool burst** — cascade of rapid packets |
| Same tool used 3× in a row | **Tool chain** — sustained packet stream |

Use `--logs` (or press `l`) to see a live text stream of every event as it arrives.

---

## Legacy Mode

Legacy themes are the **original node-based implementations** of screens that have been redesigned as full-screen ASCII field renderers. They are preserved for comparison and are not shown in the default gallery.

Available legacy themes:

```
legacy-starfall       legacy-quasar        legacy-supernova
legacy-sol            legacy-terra         legacy-binary-star
legacy-black-hole     legacy-neural-sky    legacy-storm-core
legacy-moonwire       legacy-rootsong      legacy-stormglass
legacy-spiral-galaxy  legacy-deep-abyss    legacy-storm-sea
legacy-dark-forest    legacy-mountain-stars legacy-beach-lighthouse
```

Access them:

```bash
# Use a specific legacy theme
hermes-neurovision --theme legacy-quasar

# See all legacy theme names and titles
hermes-neurovision --list-legacy

# Include legacy themes in gallery rotation
hermes-neurovision --gallery --include-legacy
```

Legacy themes use the node-based engine exclusively. If you prefer the more legible packet/pulse style where you can watch your agent's tool calls literally travel the network, legacy mode is for you.

---

## Themes (58 total)

Browse with `hermes-neurovision --gallery`. All themes respond to agent activity via `intensity_multiplier`.

### ASCII Field Themes (33)

Full-screen generative renderers. Agent events drive field brightness, density, and speed.

**Redesigned Originals** — classic themes rebuilt on the ASCII field engine:
`black-hole` `neural-sky` `storm-core` `moonwire` `rootsong` `stormglass`
`spiral-galaxy` `deep-abyss` `storm-sea` `dark-forest` `mountain-stars` `beach-lighthouse`
`starfall` `quasar` `supernova` `sol` `terra` `binary-star`

**New Screens** — original designs built for the ASCII engine:
`synaptic-plasma` `oracle` `cellular-cortex` `reaction-field` `life-colony` `aurora-bands`
`waveform-scope` `lissajous-mind` `pulse-matrix` `fractal-engine` `n-body` `standing-waves`
`clifford-attractor` `barnsley-fern` `flow-field`

### Node-Based Themes (25) — Being Redesigned

These use the original graph engine. Packets travel edges, pulses radiate from nodes. Each is scheduled for ASCII field redesign in v0.2.0.

`aurora-borealis` `nebula-nursery` `binary-rain` `wormhole` `liquid-metal`
`factory-floor` `pipe-hell` `oil-slick` `campfire` `aquarium`
`circuit-board` `lava-lamp` `firefly-field` `noxious-fumes` `maze-runner`
`neon-rain` `volcanic` `crystal-cave` `spider-web` `snow-globe`
`clockwork` `coral-reef` `ant-colony` `satellite-orbit` `stellar-weave`

---

## Tuner

Press `t` to open the tuner overlay. Controls all visual parameters in real-time without restarting.

**Sliders:**
- `Burst Scale` — size of particle bursts on task completion
- `Packet Rate` — ambient packet frequency
- `Pulse Rate` — ambient pulse frequency
- `Particle Density` — ambient particle density
- `Event Sensitivity` — how strongly agent events affect intensity
- `Animation Speed` — global animation speed multiplier

**Toggles (on/off per element):**
- Packets, Particles, Pulses, Stars, Background field, Nodes/Edges, Flash, Spawn Node

The HUD footer shows `[TUNED]` when any setting is non-default. Press `r` inside the tuner to reset all.

---

## Debug Panel

Press `d` to toggle the debug panel — a 34-column right-side overlay showing:

- Current theme name, frame number, intensity multiplier
- Intensity bar (visual gauge of current agent load)
- Quiet/Tuned state flags
- Last 6 events with source, kind, and age
- Last 4 triggers with effect type, intensity, and age

Useful for verifying that events are being received and mapped to the correct visual effects.

---

## Architecture

```
hermes_neurovision/
  plugin.py           # ThemePlugin base class — draw_background(), draw_extras(), node hooks
  themes.py           # ThemeConfig definitions + THEMES/LEGACY_THEMES tuples
  scene.py            # Particle, Packet, ThemeState simulation
  renderer.py         # Curses drawing — draw_background before nodes, draw_extras after
  events.py           # VisionEvent + EventPoller
  bridge.py           # Event → VisualTrigger mapping
  tune.py             # TuneSettings dataclass + TuneOverlay UI
  debug_panel.py      # Diagnostic overlay
  log_overlay.py      # Fading text event stream
  app.py              # GalleryApp + LiveApp + DaemonApp
  cli.py              # Entry point
  sources/            # Event sources (state_db, memories, cron, aegis, hook)
  theme_plugins/
    ascii_fields.py       # 10 pure ASCII field themes
    redesigned.py         # 15 redesigned themes (v2)
    originals_v2.py       # 7 original themes redesigned
    nature_v2.py          # Nature themes redesigned
    originals.py          # Original node-based implementations
    nature.py / cosmic.py / industrial.py / whimsical.py
    hostile.py / exotic.py / mechanical.py
    cosmic_new.py         # Legacy cosmic implementations
```

### Render Order

Each frame renders in this order, enabling hybrid themes:

```
1. Stars               (background scatter)
2. draw_background()   (ASCII field backdrop — hybrid themes)
3. Edges               (node graph connections)
4. Pulses              (expanding rings from nodes)
5. Nodes               (node glyphs)
6. Packets             (traveling event markers)
7. Particles           (burst/spawn particles)
8. draw_extras()       (foreground FX / pure ASCII field themes)
9. HUD overlay         (title bar, footer, tuner, debug panel)
```

---

## Advanced Usage

### Daemon Mode

```bash
hermes-neurovision --daemon --logs
```

Starts in gallery (screensaver), automatically switches to live mode when Hermes Agent starts a session, returns to gallery after 30 seconds idle.

### Custom Configuration

```json
{
  "auto_launch": true,
  "preferred_terminal": "iterm2",
  "launch_command": "hermes-neurovision --daemon --logs"
}
```

Save to `~/.hermes/neurovision/config.json`.

### Theme Export/Import

```bash
hermes-neurovision --export neural-sky --author "YourName"
hermes-neurovision --import mytheme.hvtheme --preview
hermes-neurovision --import mytheme.hvtheme
hermes-neurovision --list-themes
```

---

## Writing Hybrid Themes

To create a theme that combines an ASCII field backdrop with node-based event storytelling:

```python
from hermes_neurovision.plugin import ThemePlugin

class MyHybridPlugin(ThemePlugin):
    def build_nodes(self, w, h, cx, cy, count, rng):
        # Return node positions — these get packets/pulses on agent events
        return [(cx + rng.uniform(-20, 20), cy + rng.uniform(-10, 10))
                for _ in range(count)]

    def draw_background(self, stdscr, state, color_pairs):
        # Render ASCII field BEFORE nodes — this is the backdrop
        h, w = stdscr.getmaxyx()
        intensity = state.intensity_multiplier
        for y in range(1, h - 1):
            for x in range(0, w - 1):
                v = some_field_function(x, y, state.frame) * intensity
                char = " ·:+*#"[min(5, int(v * 6))]
                try:
                    stdscr.addstr(y, x, char)
                except curses.error:
                    pass

    def draw_extras(self, stdscr, state, color_pairs):
        # Optional: foreground effects drawn AFTER packets/particles
        pass
```

Available in `color_pairs`: `"bright"`, `"accent"`, `"soft"`, `"base"`, `"warning"`.
Use `state.frame` (int, 20fps), `state.intensity_multiplier` (0.2–1.0), `state.rng` (seeded `random.Random`).

---

## Testing

```bash
python -m pytest tests/ -v
```

174 tests, 100% passing.

---

## Requirements

- Python 3.10+
- No external dependencies (pure stdlib)
- Terminal with 256 color support (recommended)
- Minimum 80×24 terminal size

---

## License

MIT — see [LICENSE](LICENSE).

Copyright (c) 2026 Tranquil-Flow

---

**Enjoy watching your AI think.**
