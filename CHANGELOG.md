# Changelog

All notable changes to Hermes Neurovision will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.1]: https://github.com/Tranquil-Flow/hermes-neurovision/releases/tag/v0.1.1
[0.1.0]: https://github.com/Tranquil-Flow/hermes-neurovision/releases/tag/v0.1.0
[0.0.1]: https://github.com/Tranquil-Flow/hermes-neurovision/releases/tag/v0.0.1
