# Changelog

All notable changes to Hermes Neurovision will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-16

**Major Release — v0.2.0 Engine Overhaul** 🚀

### Added (post-tag additions — included in final v0.2.0 release)

- **Background Mode (`--bg`)** — run neurovision silently behind a transparent terminal.
  Fully isolated from live/gallery/daemon. Supports iTerm2, Kitty, Alacritty, WezTerm.
  Auto-sets and restores terminal opacity on start/stop. PID-tracked, config persisted.
  Commands: `--bg start|stop|status|config` with `--bg-theme`, `--bg-opacity`,
  `--bg-gallery`, `--bg-theme-seconds`, `--bg-window-mode`, `--bg-no-auto-opacity`.
- **Boot sequence** — animated startup screen with blinking label before first frame.
- **Transparent background renderer** — forced black fill removed; bg-mode themes
  layer correctly over the terminal glass when opacity < 1.0.
- **Soundtrack assets** — lyrics, tags, and generation scripts for 3 companion tracks.
- **Demo video** — rapid-flash montage section, fractal-zoom warmup, updated stats.
- Full v0.2 engine upgrades across 20+ existing themes (reactive, emergent, postfx).

### Fixed (post-tag)

- Attractors NaN crash — guard divergence, conservative dt, `_reset_trajectory()`.
- Rossler/Thomas tumbling 3D camera and fractal-zoom continuous zoom.
- Beach-lighthouse broken layout; quasar stellar rework.
- `--bg` dispatch: `handle_bg_command` read `args.bg_action` (nonexistent) instead of
  `args.bg`, causing status/stop/config to all fall through to start. Fixed.
- `--bg-theme` now sets `gallery=False` so the specific theme actually runs.
- Gallery simulated activity pump restored after accidental removal.

### Known Issues / Post-v0.2.0

- **bg mode on Terminal.app**: requires macOS Automation permission for osascript.
  Stashed for v0.2.1 polish.
- **bg mode text fade**: per-line ANSI fade-up effect not yet implemented.
  Planned as a TUI wrapper mode for v0.3.



### Added

#### New Visual Engine
- **Post-Processing Pipeline** — 7 compositable effects applied per-frame:
  - `warp_field` — per-pixel coordinate distortion (sinusoidal, rotation, etc.)
  - `symmetry` — 4-way / 8-way / radial mirror modes
  - `glow_radius` — bloom halo around bright cells
  - `void_intensity` — dynamic hole-punching / negative space
  - `echo_decay` — afterimage trail persistence (N-frame ring buffer)
  - `force_field` — vector field nudge applied to all cell positions
  - `decay_sequence` — char-substitution trail as cells age
- **Reactive Element System** — 8 named reactive effects any plugin can trigger:
  `SPARK`, `BLOOM`, `RIPPLE`, `WAVE`, `SHATTER`, `VOID`, `PULSE_BURST`, `STREAK`
- **Sound System** — optional terminal bell cues mapped to agent events
- **Emergent Systems** — 5 autonomous grid-based simulations that run alongside nodes:
  - Cellular automaton (custom rule sets)
  - Neural field (excitatory/inhibitory wave propagation)
  - Wave field (2D wave equation)
  - Physarum (slime-mold network formation)
  - Reaction-diffusion (Gray-Scott model)
- **Boids** — N-body flocking simulation rendered as directional glyphs
- **Depth Layers** — parallax rendering with multiple z-planes
- **Tuner Overlay** — press `t` for real-time per-element sliders and toggles
- **Debug Panel** — press `d` for live event/trigger diagnostic overlay
- **Performance Mode** — press `P` to halve render resolution for slow terminals
- **Mute Toggle** — press `M` to silence all sound cues
- **Fullscreen Toggle** — press `F` to enter native macOS fullscreen

#### New Themes (85 total, was 42 in v0.1.x)
**Strange Attractors** (5 new) — real continuous ODE systems rendered as density fields
with full per-pixel rainbow colouring:
- `lorenz-butterfly` — iconic butterfly attractor (sigma=10, rho=28, beta=8/3)
- `rossler-ribbon` — flat spiral coil with vertical spike (a=0.2, b=0.2, c=5.7)
- `halvorsen-star` — 3-fold cyclically symmetric triple spiral
- `aizawa-torus` — toroidal orbit with alien geometry
- `thomas-labyrinth` — space-filling labyrinthine web (edge-of-chaos parameter)

**Spectacular** (5 new) — maximally visual, experimental screens:
- `plasma-rainbow` — dense multi-harmonic interference with full HSV sweep
- `hypnotic-tunnel` — infinite 3D rectangular tunnel with rotating rainbow hues
- `fractal-zoom` — Mandelbrot boundary zoom with escape-time rainbow colouring
- `particle-vortex` — dual counter-rotating vortices with 700 rainbow-hued particles
- `chladni-sand` — sand-on-plate standing wave Chladni figures, cycling 16 modes

**Emergent V2** (5 new) — v0.2.0 engine feature showcases:
- `dna-helix`, `pendulum-waves`, `kaleidoscope`, `electric-storm`, `coral-growth`

**Advanced Screens** (5 new) — postfx + reactive hybrids:
- `dna-strand`, `pendulum-array`, `mandala-scope`, `ghost-echo`, `magnetic-field`

**Emergent Showcase** (5) — `mycelium-network`, `swarm-mind`, `neural-cascade`,
`tide-pool`, `turing-garden`

**Hybrid** (2) — `plasma-grid`, `deep-signal`

#### Agent API for Theme Authoring
- Full `plugin.py` API documented with all hooks
- Rainbow colour pair system (pairs 10-15) available to all `draw_extras` plugins
- `state.intensity_multiplier` (0.2–1.0) drives all agent-reactive visuals
- `state.frame` (int, ~20fps), `state.rng` (seeded), `state.width/height`

### Changed
- Theme count: **85 non-legacy** (was 42 in v0.1.2)
- README updated to reflect all new themes and engine features
- Architecture section updated with full render pipeline order
- `build_theme_config` now handles all 85 themes + 18 legacy variants
- Lightning bolt format in `electric-storm` changed from plain list to
  `[age, points]` to fix Python 3.14 `AttributeError` on list attribute set
- `dna-strand` glow/echo/decay postfx removed (was causing purple block flash)
- `dna-strand` palette: MAGENTA → YELLOW (biological codon colours)

### Fixed
- `electric-storm` crash on Python 3.14: `bolt._age = 0` on plain list
- `dna-strand` purple flashing boxes (over-aggressive postfx + MAGENTA palette)
- Gallery crash when `emergent_v2.py` / `advanced_screens.py` not auto-imported

## [0.1.2] - 2026-03-15

**AI-Driven Live Mode + Docker Visibility**

### Added
- Live mode uses AI event injection by default
- Docker container visibility improvements
- Theme persistence between sessions

## [0.1.1] - 2026-03-14

**First Public Release** 🎉

### Added
- **Theme Export/Import System**: Share themes as portable .hvtheme files
  - `--export THEME` command to export any theme
  - `--import FILE` command to import themes
  - `--preview` flag to preview themes before installing
  - `--list-themes` command to show all imported themes
  - Theme registry tracking imported themes
  - Version compatibility checking with graceful degradation
  - Security warnings and confirmation for custom plugin themes
  - Metadata support (author, description, timestamp)
- **Runtime Theme Registration**: Import themes without code installation
  - Runtime config registry for imported theme parameters
  - Runtime plugin registry for imported custom plugins
- **AI-Assisted Theme Design**: Agents can design custom themes via skill system
- **Documentation**:
  - `VERSION_COMPATIBILITY.md` - Version strategy
  - `PLAN_v0.1.2.md` - Future slider features
  - `V0.1.1_IMPLEMENTATION_COMPLETE.md` - Implementation summary
  - `RELEASE_NOTES_v0.1.1.md` - User-facing release notes

### Changed
- **Package name**: Now officially `hermes-neurovision` (more descriptive)
- **CLI command**: `hermes-neurovision` (was `hermes-vision` in development)
- CLI `--theme` argument now accepts any string (not limited to built-in themes)
- Config paths: `~/.hermes/neurovision/` (was `~/.hermes/vision/` in development)
- Version bumped to 0.1.1

### Fixed
- Plugin execution namespace now includes required imports (ThemePlugin, Particle, math)

## [0.1.0] - 2026-03-14

**Internal Development Release** (not published)

### Added
- **42 Animated Themes** across 8 categories (Cosmic, Nature, Industrial, Whimsical, Hostile, Exotic, Mechanical, and Originals)
- **Theme Plugin System** - Extensible architecture for creating custom visualizations
- **Enhanced Visual Effects**:
  - Beach Lighthouse with animated waves covering bottom 30%
  - Aurora Borealis showing constellation patterns (Big Dipper, Orion, Cassiopeia, etc.)
  - Binary Rain with dense animated cloud layer at top
  - Clockwork with giant swinging pendulum across entire screen
  - Nebula Nursery with slow-drifting stellar wind particles
  - Maze Runner completely redesigned as "Shifting Dimensional Maze" with reality tears and phasing portals
  - Bonfire visualization with large, visible flames
  - Circuit Board with components spread across entire screen
- **Live Event Monitoring**: Monitors state.db, memories, cron, trajectories, aegis, custom events
- **Gallery Mode**: Browse all 42 themes with auto-rotation
- **Daemon Mode**: Gallery when idle, switches to live mode when agent is active
- **Log Overlay**: Color-coded event stream with fading text
- **Auto-Launch**: Opens automatically with cron jobs
- **Hook System**: Gateway hook integration for event capture

### Changed
- **Black Hole moved to #1 position** (first theme in gallery)
- **Removed themes**: electric-mycelium, cathedral-circuit, hybrid (reduced to core set)
- **Industrial themes** (factory-floor, pipe-hell, clockwork, circuit-board) now spawn particles/stars everywhere across the screen, not just at top
- **Campfire** upgraded to large bonfire with enhanced flame visibility
- **Display name**: "Hermes Neurovisualizer" (was "Hermes visualizer")
- **Version display**: Now shows "v0.1.0" in footer
- **Theme count**: 42 themes (was 10 in prototype)

### Fixed
- IndexError when node indices go out of range in edge and packet rendering
- Bounds checking added to prevent crashes during theme transitions
- Lighthouse beam now always renders on top of waves (draw order fixed)
- Nebula nursery particle speeds reduced significantly for better aesthetics

### Technical
- Pure Python stdlib implementation (no external dependencies)
- 63 passing tests with full coverage
- Optimized rendering pipeline for smooth 30+ FPS
- Plugin-based theme architecture for easy extensibility

## [0.0.1] - 2026-03-13

### Added
- Initial prototype release
- 10 base themes
- Live mode with event visualization
- Gallery mode for theme browsing
- Daemon mode (auto-switching)
- Log overlay system
- Auto-launch support for cronjobs
- Gateway hook integration
- SQLite state.db monitoring
- 7 data sources (sessions, tools, memory, cron, security, custom, aegis)
- 34 event types
- 8 visual effects (packet, pulse, burst, flash, spawn_node, wake, cool_down, dim)

[0.2.0]: https://github.com/Tranquil-Flow/hermes-neurovision/releases/tag/v0.2.0
[0.1.2]: https://github.com/Tranquil-Flow/hermes-neurovision/releases/tag/v0.1.2
[0.1.1]: https://github.com/Tranquil-Flow/hermes-neurovision/releases/tag/v0.1.1
[0.1.0]: https://github.com/Tranquil-Flow/hermes-neurovision/releases/tag/v0.1.0
[0.0.1]: https://github.com/Tranquil-Flow/hermes-neurovision/releases/tag/v0.0.1
