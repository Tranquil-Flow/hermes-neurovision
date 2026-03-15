# Hermes Neurovision — Tasks

Read the full plan at `docs/superpowers/plans/2026-03-13-hermes-neurovision.md` for exact code, tests, and commands.

## Chunk 1: Project Scaffold + Visual Engine Extraction

- [x] Task 1: Create pyproject.toml, __init__.py, directory structure. Init git repo.
- [x] Task 2: Extract themes.py from ~/Desktop/neurovisualizer.py (THEMES tuple, ThemeConfig, build_theme_config, constants). Write tests first.
- [x] Task 3: Extract scene.py (Particle, Packet, ThemeState with all simulation logic). Keep _build_edges() as callable method. Add intensity_multiplier fields. Write tests first.
- [x] Task 4: Extract renderer.py (Renderer class, all drawing code). Signature: draw(state, gallery_index, gallery_total, end_time). Write tests first.
- [x] Task 5: Extract app.py — GalleryApp with run() and run_headless(). Write tests first.
- [x] Task 6: Create cli.py with argparse + __main__.py. Gallery mode working end-to-end.

## Chunk 2: Event System + Sources

- [x] Task 7: Create events.py — VisionEvent dataclass + EventPoller. Write tests first.
- [x] Task 8: Create sources/custom.py — JSONL file tailer for ~/.hermes/neurovision/events.jsonl. Write tests first.
- [x] Task 9: Create sources/state_db.py — SQLite poller for ~/.hermes/state.db (sessions + messages tables). Write tests first.
- [x] Task 10: Create sources/memories.py — Filesystem watcher for ~/.hermes/memories/. Write tests first.
- [x] Task 11: Create sources/cron.py — Cron job status poller from ~/.hermes/cron/. Write tests first.
- [x] Task 12: Create sources/aegis.py — Optional Aegis audit trail tailer (graceful if missing). Write tests first.
- [x] Task 13: Create sources/hook_handler.py — Standalone gateway hook + HOOK.yaml. Must NOT import hermes_neurovision. Write tests first.

## Chunk 3: Bridge + Log Overlay + Live Mode

- [x] Task 14: Create bridge.py — VisualTrigger dataclass + full event-to-visual mapping table (24 event types). Write tests first.
- [x] Task 15: Create log_overlay.py — LogOverlay with fading lines, color coding by source. Write tests first.
- [x] Task 16: Implement apply_trigger() in scene.py (8 effects: packet, pulse, burst, flash, spawn_node, wake, cool_down, dim). Add LiveApp to app.py. Wire up --live mode in cli.py. Write tests first.

## Chunk 4: Polish + Install

- [x] Task 17: pip install -e . and install gateway hook to ~/.hermes/hooks/hermes-neurovision/
- [x] Task 18: Run full test suite, smoke test gallery and live modes
- [x] Task 19: Register with grove (documented in INSTALL.md)

---

## v0.2.0 — Feature Additions (implement before theme conversions)

### Navigation + UI polish

- [x] Task 44: Shift+Left/Right gallery nav — DONE (commit 908e1d0)
  Refactored _handle_input → _handle_key(ch). Handles KEY_SLEFT/KEY_SRIGHT
  and escape sequences \x1b[1;2D / \x1b[1;2C. 4 tests passing.

### Tuner — live parameter sliders

- [x] Task 45: TuneSettings + TuneOverlay — DONE (commit 75bb973)
  hermes_neurovision/tune.py: 6 sliders, 8 element toggles, unified
  ↑↓ navigation, ←→ adjust/toggle, t close, r reset. 28 tests passing.

- [x] Task 46: Wire TuneSettings into all effect pathways — DONE (commit 68d3147)
  scene.py: ThemeState.tune field; all spawn/trigger methods gated on toggles
  and scaled by sliders. renderer.py: stars/nodes/background gated. app.py:
  GalleryApp + LiveApp hold TuneSettings+TuneOverlay, wired to state.

### Debug panel

- [x] Task 47: Debug panel — DONE (commit 46101c7)
  hermes_neurovision/debug_panel.py: 34-col right-anchored overlay with
  ring buffers (8 events, 8 triggers), intensity bar, theme/frame info.
  GalleryApp + LiveApp: 'd' toggles, LiveApp feeds events+triggers. 13 tests.

### Legacy theme management

- [ ] Task 48: Add --include-legacy flag and legacy subcommand to CLI. [QWEN14B]
  cli.py changes:
    Add --include-legacy flag: if set, append all legacy-* themes from build_theme_config()
    to the gallery themes list (load them from themes.py by scanning for "legacy-" prefix keys).
    Add --list-legacy flag: print all legacy-* theme names with their titles and exit.
  Gallery key 'L': toggles include-legacy at runtime (rebuilds themes list, resets to first theme).
  HUD: show "[+LEGACY]" indicator when legacy themes are included.
  New helper in themes.py: LEGACY_THEMES: Tuple[str,...] = all keys in build_theme_config() starting with "legacy-".
  Test: test_legacy_themes_accessible(), test_include_legacy_flag().

### Disable / enable themes

- [ ] Task 49: Add theme disable/enable system. [QWEN14B]
  Config file: ~/.hermes/neurovision/disabled.json → {"disabled": ["theme-a", "theme-b"]}
  New module: hermes_neurovision/disabled.py with:
    load_disabled() -> set[str]
    save_disabled(names: set[str]) -> None
    add_disabled(name: str) -> None
    remove_disabled(name: str) -> None
    DISABLED_CONFIG = "~/.hermes/neurovision/disabled.json"
  cli.py: add --disable THEME and --enable THEME flags.
    --disable THEME: call add_disabled(), print confirmation, exit.
    --enable THEME: call remove_disabled(), print confirmation, exit.
    --list-themes already exists — add "(disabled)" marker for disabled themes.
  Gallery: at startup, filter THEMES through load_disabled() to get active themes.
  If all themes disabled: print warning, use full THEMES list as fallback.
  Gallery key 'X': disables current theme and advances to next. Print brief notice.
  Test: test_disable_theme(), test_enable_theme(), test_disabled_themes_filtered_from_gallery().

- [ ] Task 50: Create 5 new original screens. [QWEN30B]
  Each screen must be a completely original ASCII visualization not already in the theme list.
  Add each to themes.py, theme_plugins/__init__.py, and tests/test_themes.py full_screen_themes set.
  Run tests after each addition. Commit after all 5 are done.

---

## v0.2.0: Full ASCII Field Engine Overhaul

Convert remaining 24 old node-based themes to full-screen ASCII field renderers.
Read CLAUDE.md ##Visual Engine section for the draw_extras() API and patterns.
Pattern: rename old plugin name to "legacy-NAME" in its file, create V2 plugin with original name.
Add legacy ThemeConfig to build_theme_config() but NOT to THEMES tuple.
After each task: run `python -m pytest tests/ -q` — expect 4 pre-existing failures, nothing new.

### Cosmic themes (theme_plugins/cosmic.py)

- [ ] Task 20: Redesign `aurora-borealis` [HAIKU] — Full-screen aurora curtain simulation.
  Vertical sine curtains that drift horizontally, layered with parallax star field.
  Colors: green/cyan bands in upper half, with magenta wisps. Intensity drives curtain brightness
  and adds particle showers (solar wind). Rename AuroraBorealisPlugin.name to "legacy-aurora-borealis",
  create AuroraBorealisV2Plugin(name="aurora-borealis") in new file cosmic_v2.py.
  Add ThemeConfig("aurora-borealis", ..., palette=(GREEN, CYAN, MAGENTA, WHITE)).
  Add ThemeConfig("legacy-aurora-borealis", ...) with original parameters.

- [ ] Task 21: Redesign `nebula-nursery` [QWEN14B] — Volumetric nebula density field.
  Multi-octave noise using overlapping sine waves creates pillars of creation.
  Voronoi-like cell structure for dark dust lanes (find nearest of ~20 dust centres).
  Bright ionised gas around hot star clusters. Tendrils of gas reach outward.
  Intensity drives star formation bursts (bright flashes at random positions).
  Colors: magenta/cyan/yellow on near-black background.
  Create NebulaNurseryV2Plugin in cosmic_v2.py.

- [ ] Task 22: Redesign `binary-rain` [HAIKU] — Matrix digital rain, properly done.
  Falling columns of random glyphs (katakana-range Unicode + digits + symbols).
  Each column: random speed, random start position, fading trail (bright head → dim tail).
  Occasional "reveal" columns that pause and highlight a glyph brighter.
  Intensity drives rain density and speed. Columns spawn from top, wrap around.
  Colors: bright green head, soft green body, base dim tail.
  Create BinaryRainV2Plugin in cosmic_v2.py.

- [ ] Task 23: Redesign `wormhole` [QWEN14B] — Einstein-Rosen bridge visualization.
  Spacetime grid rendered as a distorted mesh. Center pulls all grid lines inward.
  Two funnel mouths: one on left half, one on right half of screen.
  Grid lines warp toward each centre following a 1/r field.
  Particles travel through the throat (left → right along the curvature).
  Intensity drives particle stream density and grid deformation strength.
  Colors: magenta/blue on dark background. Center singularity in accent.
  Create WormholeV2Plugin in cosmic_v2.py. Add all four ThemeConfigs to build_theme_config().

### Industrial themes (theme_plugins/industrial.py)

- [ ] Task 24: Redesign `liquid-metal` [HAIKU] — Metallic fluid surface.
  Procedural metallic sheen using overlapping reflection waves.
  Value field = sin(x*f1 + sin(y*f2 + t)) — creates ripple interference.
  Characters mapped by value: space for valleys, ░▒▓█ for peaks.
  "Droplets": small Gaussian bumps that appear and spread outward.
  Intensity drives droplet frequency and wave amplitude.
  Colors: white/cyan (reflection highlights) on blue/magenta (deep metal).
  Rename LiquidMetalPlugin.name to "legacy-liquid-metal", create LiquidMetalV2Plugin
  in new file industrial_v2.py.

- [ ] Task 25: Redesign `factory-floor` [QWEN14B] — Cellular automaton factory.
  Grid of "machines" at regular intervals, each running a simple CA rule.
  Between machines: conveyor belts (animated dashes → arrows showing direction).
  Machines cycle through states (idle → active → output → idle) asynchronously.
  When active: emit "products" (characters) that travel along belts.
  Intensity drives machine cycle speed and conveyor density.
  Colors: yellow/green on dark background. Active machines in bright.
  Create FactoryFloorV2Plugin in industrial_v2.py.

- [ ] Task 26: Redesign `pipe-hell` [QWEN14B] — Infinite pipe labyrinth (3D scrolling).
  Isometric-view pipe grid that slowly scrolls toward viewer.
  Pipes: ║═╔╗╚╝╠╣╦╩╬ characters forming a connected network.
  Each frame: shift pipes down-right (isometric perspective scroll).
  T-junctions and elbow joints at intersections.
  Fluids flow through pipes: animated particles moving along pipe directions.
  Colors: green/cyan for pipe walls, bright white for fluid.
  Create PipeHellV2Plugin in industrial_v2.py.

- [ ] Task 27: Redesign `oil-slick` [HAIKU] — Thin film interference rainbow.
  Iridescent surface using hue-cycling technique.
  Base: slowly undulating height field (multi-freq sine).
  Color: hue = (height + phase_angle) mod 1.0 → map to nearest terminal color.
  Use all 4 color pairs cycling based on local field value and gradient.
  Turbulence patches drift across surface.
  Intensity drives turbulence amplitude and color cycling speed.
  Create OilSlickV2Plugin in industrial_v2.py. Add all four ThemeConfigs.

### Whimsical themes (theme_plugins/whimsical.py)

- [ ] Task 28: Redesign `campfire` [QWEN14B] — Fluid fire simulation.
  Bottom rows: ember bed (random bright dots decaying).
  Above: flame columns rising with turbulence (shift-left/right each row up).
  Each column of flame: independent height governed by noise.
  Heat distortion: chars above flame shimmer (shift x position by small sin).
  Intensity drives flame height and ember density.
  Colors: yellow→magenta→white gradient from base to tip.
  Create CampfireV2Plugin in new file whimsical_v2.py.

- [ ] Task 29: Redesign `aquarium` [QWEN30B] — Boids flocking fish.
  20-40 fish (boids) with separation, alignment, cohesion forces.
  Fish rendered as directional glyphs: ><> >=> >> based on velocity direction.
  Bubble trail: particles drifting upward from random fish.
  Seaweed: vertical sine-wave columns at left/right edges.
  Caustic light: slowly-moving bright patches on background (Voronoi-like).
  Intensity drives school density and swimming speed.
  Create AquariumV2Plugin in whimsical_v2.py.

- [ ] Task 30: Redesign `circuit-board` [QWEN14B] — PCB signals propagating.
  Orthogonal wire grid: horizontal and vertical trace lines at intervals.
  Signals: bright packets travelling along traces (animated along wire paths).
  Components at intersections: small ■ □ ○ shapes.
  Idle traces: dim line characters (─│┼).
  Active traces briefly brighten as signal passes.
  Intensity drives signal spawn rate and trace density.
  Create CircuitBoardV2Plugin in whimsical_v2.py.

- [ ] Task 31: Redesign `lava-lamp` [QWEN14B] — SDF metaballs.
  5-8 metaballs with slowly drifting positions (sine orbit paths).
  Per-cell: sum of 1/distance² from each metaball centre.
  Threshold: cells above threshold = "lava blob" (bright chars), below = fluid (dim).
  Surface normals from gradient give shading.
  Intensity drives blob count and drift speed.
  Colors: magenta/yellow blobs on dark cyan background.
  Create LavaLampV2Plugin in whimsical_v2.py.

- [ ] Task 32: Redesign `firefly-field` [QWEN14B] — Synchronized firefly oscillators.
  40 fireflies each with a Kuramoto oscillator phase.
  Coupling: nearby fireflies nudge each other's phase toward synchrony.
  Glow: bright when phase near 0, dark otherwise.
  Near-synchrony: many fireflies flash simultaneously — beautiful strobe.
  Background: gentle noise field (dim).
  Intensity drives coupling strength (faster synchronization).
  Create FireflyFieldV2Plugin in whimsical_v2.py. Add all five ThemeConfigs.

### Hostile themes (theme_plugins/hostile.py)

- [ ] Task 33: Redesign `noxious-fumes` [HAIKU] — Perlin-like turbulent fluid.
  Multi-octave value noise using 4 overlapping sine/cos terms at different scales.
  Renders as character density: dense fog = ▓▒░, thin wisps = : . ·
  Slow drift vector causes entire field to translate.
  "Toxic bloom" patches: occasional Gaussian bursts of brighter density.
  Intensity drives drift speed and bloom frequency.
  Colors: green/yellow on dark background (poison aesthetic).
  Create NoxiousFumesV2Plugin in new file hostile_v2.py.

- [ ] Task 34: Redesign `maze-runner` [QWEN30B] — Real-time maze generation + flood fill solve.
  Use recursive DFS to generate a maze (15x8 cells at standard terminal size).
  Draw maze walls using box-drawing chars (─│┌┐└┘├┤┬┴┼).
  After maze is complete (~60 frames to animate drawing): run BFS flood fill from
  start to end, animating the frontier expanding cell by cell.
  After solve: show solution path highlighted, then regenerate.
  Intensity drives maze size and solve speed.
  Create MazeRunnerV2Plugin in hostile_v2.py. Add both ThemeConfigs.

### Exotic themes (theme_plugins/exotic.py)

- [ ] Task 35: Redesign `neon-rain` [HAIKU] — Fiber optic chromatic dispersion.
  Vertical light pipes: bright streaks descending at slight angles.
  Each fiber: independent angle, speed, color.
  Chromatic aberration: same fiber rendered with slight x-offset per color pair.
  Caustic end: bright dots at bottom where fibers terminate.
  Intensity drives fiber count and brightness.
  Create NeonRainV2Plugin in new file exotic_v2.py.

- [ ] Task 36: Redesign `volcanic` [QWEN14B] — Voronoi lava flow.
  20 Voronoi sites: compute nearest-site distance per cell.
  Cell edges (where two sites are equidistant) = lava flow channels (bright).
  Cell interiors = cooling lava (dim, mottled texture).
  Sites slowly drift. Occasionally a "eruption" spawns a burst of bright particles.
  Intensity drives eruption frequency and lava channel brightness.
  Create VolcanicV2Plugin in exotic_v2.py.

- [ ] Task 37: Redesign `crystal-cave` [QWEN14B] — IFS crystal formation.
  Iterated Function System with 4-6 affine transforms producing crystal lattice shapes.
  Random iteration algorithm accumulates points into density grid.
  Crystalline shapes: hexagonal IFS parameters producing snowflake/quartz patterns.
  Slowly rotate IFS transforms (rotate the affine matrices by small angle each frame).
  Colors: cyan/white/magenta (gem-like).
  Create CrystalCaveV2Plugin in exotic_v2.py.

- [ ] Task 38: Redesign `spider-web` [QWEN30B] — Differential growth + tension network.
  Start with a circle of nodes.
  Apply spring forces: edge lengths want to be equal, nodes repel each other.
  Grow new nodes at random edge midpoints (differential growth).
  Render edges as line characters (Bresenham).
  Oscillation: pluck random edges causing wave propagation along web.
  Colors: white/cyan (silk), with bright nodes.
  Create SpiderWebV2Plugin in exotic_v2.py.

- [ ] Task 39: Redesign `snow-globe` [QWEN14B] — Atmospheric particle simulation.
  Clear glass dome outline (circle drawn with arc characters).
  Inside dome: snow particles with physics (gravity + gentle brownian motion).
  Particles accumulate at bottom (pile up, stop moving when y > threshold).
  Wind gusts: periodic horizontal force applied to all particles.
  Scene inside dome: simple mountain/tree silhouette at bottom.
  Intensity drives wind gust frequency.
  Create SnowGlobeV2Plugin in exotic_v2.py. Add all five ThemeConfigs.

### Mechanical themes (theme_plugins/mechanical.py)

- [ ] Task 40: Redesign `clockwork` [QWEN14B] — Epicycloid gear chain animation.
  5-7 gears of varying sizes, teeth count proportional to radius.
  Each gear: draw circle + teeth (radial spokes at gear_tooth_spacing intervals).
  Rotation: angular velocity inversely proportional to radius (teeth meshing).
  Output shaft: small arm attached to outermost gear traces an epicycloid curve.
  Render epicycloid trail as fading density.
  Colors: yellow/white gears on dark background.
  Create ClockworkV2Plugin in new file mechanical_v2.py.

- [ ] Task 41: Redesign `coral-reef` [QWEN30B] — Diffusion-limited aggregation.
  Start with 3-5 seed clusters at fixed positions.
  Random walkers: spawn at random positions, do Brownian motion.
  When a walker touches the cluster, it sticks (DLA).
  Render cluster: color by time of accretion (recent = bright, old = dim).
  After cluster fills screen, fade and restart.
  Intensity drives walker count (faster growth).
  Create CoralReefV2Plugin in mechanical_v2.py.

- [ ] Task 42: Redesign `ant-colony` [QWEN14B] — Multi-ant Langton's Ant.
  10 ants, each following Langton's Ant rules (or extended RLRR/LRRL variants).
  Each ant has its own rule string and color.
  Grid state: 0=empty, 1-4=pheromone levels.
  Render: pheromone level → character density. Ants as bright glyphs.
  After ant builds a highway (~10000 steps), reset with new rule.
  Intensity drives step count per frame.
  Create AntColonyV2Plugin in mechanical_v2.py.

- [ ] Task 43: Redesign `satellite-orbit` [QWEN30B] — Kepler orbital mechanics.
  5-8 satellites in elliptical orbits around central body.
  Each orbit: semi-major axis a, eccentricity e, inclination i (for visual tilt).
  Orbital position: solve Kepler's equation numerically (Newton's method on M=E-e*sin(E)).
  Draw orbit ellipse as faint path. Draw satellite as bright glyph + trail.
  Gravitational potential field: background rendered as dim field proportional to -1/r.
  Intensity drives orbit speed multiplier.
  Create SatelliteOrbitV2Plugin in mechanical_v2.py. Add all four ThemeConfigs.
  Import all _v2 modules in theme_plugins/__init__.py _load_all().

---

## Notes for Moondance

- Each task above is self-contained: rename old plugin, create V2 plugin, update themes.py, update __init__.py
- Always run `python -m pytest tests/ -q` after each task — expect exactly 4 failures (pre-existing)
- The V2 plugins use draw_extras(stdscr, state, color_pairs) — see CLAUDE.md ##Visual Engine
- Legacy themes (legacy-NAME) get a ThemeConfig in build_theme_config() but NOT in THEMES tuple
- Commit message format: "feat: redesign [theme-name] with full-screen ASCII engine"
- Group related tasks into one commit if they're in the same file (e.g., all 4 industrial themes)

---

## v0.2.0 Phase 2 — 100 Themes (separate planning phase, do not start yet)

Current: 58 themes. Target: 100 total. Need 42 new unique designs.
This phase uses a 4-step process: rough ideas → flesh out → build → test.
Claude Code (Sonnet) will brainstorm the 42 concepts with user approval before any implementation begins.
Implementation will be assigned to Haiku/qwen3:30b per model strategy below.
DO NOT start this phase until explicitly instructed by the user.

---

## Model Strategy for Theme Implementation

Use the least powerful model that can succeed. Match model to task complexity:

[HAIKU] claude-haiku-4-5 — Simple sine/cosine field screens, ~1-2 math functions, <150 lines:
  - Plasma fields, wave interference, colour cycling, gradient backgrounds
  - Any screen whose draw_extras() is essentially: for each cell, compute one formula, pick a char

[QWEN14B] qwen3:14b (Moondance default, 40K ctx) — Medium complexity, 150-300 lines:
  - Single physics system, particle trails, Voronoi, cellular automata
  - Screens with instance state but no complex multi-body simulation

[QWEN30B] qwen3:30b (18GB, 256K ctx) — Complex physics, multi-system screens, 300+ lines:
  - N-body gravity, fluid simulation, neural networks, attractor accumulation
  - Screens where getting the math right requires more reasoning

[SONNET] claude-sonnet-4-6 (interactive only) — Architecture decisions, review, debugging
  - Used for Tasks 44-49 (new features), final integration review, fixing broken implementations
  - NOT used for routine theme implementation (too expensive)

Assignment hints already in each task via [MODEL] tag.
For untagged tasks, Moondance should assess: if < 150 lines → HAIKU, else default → QWEN14B.
