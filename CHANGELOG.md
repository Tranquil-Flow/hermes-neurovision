# Changelog

All notable changes to Hermes Vision will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-14

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

[0.1.0]: https://github.com/NousResearch/hermes-vision/releases/tag/v0.1.0
[0.0.1]: https://github.com/NousResearch/hermes-vision/releases/tag/v0.0.1
