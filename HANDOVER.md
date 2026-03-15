# Hermes Neurovision v0.2.0 — Build Handover

**Last updated:** 2026-03-15
**Status:** PLAN LOCKED — Ready to build Phase 1

---

## What Is This Project

hermes-neurovision is a curses-based TUI visualizer for hermes-agent. It renders real-time visual themes driven by agent activity data (tool calls, LLM streaming, errors, memory saves, etc). v0.1.x is shipped and working. v0.2.0 is a major foundation expansion before mass screen creation.

## Where Everything Lives

```
/workspace/Projects/hermes-neurovision/
├── PLAN_v0.2.0.md          ← THE PLAN (1406 lines, 18 sections, 11 phases)
├── HANDOVER.md             ← THIS FILE
├── hermes_neurovision/
│   ├── plugin.py           ← ThemePlugin base class (frozen v1.0 API)
│   ├── renderer.py         ← Main render loop
│   ├── scene.py            ← ThemeState, effects, particles
│   ├── bridge.py           ← Event → VisualTrigger mapping
│   ├── events.py           ← VisionEvent dataclass
│   ├── tune.py             ← TuneSettings (live sliders)
│   ├── export.py           ← .hvtheme export
│   ├── import_theme.py     ← .hvtheme import
│   ├── log_overlay.py      ← HUD event log
│   ├── sources/
│   │   ├── custom.py       ← Hook-based event source
│   │   ├── state_db.py     ← SQLite state.db polling
│   │   └── HOOK.yaml       ← Event subscriptions
│   └── theme_plugins/      ← Existing themes (nature_v2, exotic, hybrid, redesigned, etc)
├── tests/
└── pyproject.toml
```

## Build Order (11 Phases, ~37 hours)

### Phase 1: Buffer Foundation (~3h) ← START HERE
- FrameBuffer class in renderer.py (Cell dataclass, put/get/blit_to_screen)
- Refactor Renderer.draw() to write to buffer first, then blit
- ALL existing themes must render identically through buffer
- Tests for buffer round-trip

### Phase 2: Plugin API Expansion (~2h)
- Add ALL new method stubs to plugin.py (safe defaults, no-ops)
- SpecialEffect dataclass
- API FROZEN docstring
- Tests

### Phase 3: New Effects + Reactive Primitives (~4h)
- ripple, cascade, converge, streak effects in scene.py
- Streak dataclass + renderer support
- palette_shift, overlay_effect, special_effects wiring
- effect_zones, intensity_curve, ambient_tick

### Phase 4: Post-Processing Pipeline (~5h)
- postfx.py: warp, void, echo, glow, mask, decay, symmetry
- Wire after buffer write, before blit
- Echo ring buffer
- TuneSettings controls

### Phase 5: Emergent Systems (~6h)
- emergent/ package: automaton, physarum, neural_field, wave_field, boids, reaction_diffusion
- Wire into ThemeState + Bridge injection
- Buffer pipeline integration

### Phase 6: Event Pipeline (~3h)
- Expand HOOK.yaml, custom.py EVENT_MAP, bridge.py _MAPPING
- log_overlay.py format strings

### Phase 7: Data Sources (~4h)
- Update state_db.py (new columns, fallback)
- New: sources/mcp.py, skills.py, checkpoints.py, providers.py, context.py, sessions.py
- Source config + CLI flags

### Phase 8: Export/Import + Docs (~2h)
- Export format v1.1, import compat, docs

### Phase 9: Integration + Polish (~3h)
- Full test suite, visual testing, performance profiling

### Phase 10: Reactive Element System (~3h)
- reactive.py: ReactiveElement enum (12 types), Reaction dataclass, REACTIVE_MAP
- ReactiveRenderer: 12 element physics engines
- Wire into Bridge dispatch
- Theme render_* method stubs

### Phase 11: Sound System (~2h)
- sound.py: SoundCue, SoundEngine (curses.beep + macOS afplay/say)
- Plugin hook: sound_cues()
- CLI: --sound/--no-sound/--volume

## Key Design Principles

1. **ATOMS not molecules** — build primitives, AI agents compose screens later
2. **All new features are opt-in** — defaults disable everything new
3. **v0.1.x themes run unchanged on v0.2.0** — zero breaking changes
4. **Reactive Element System forces diversity** — 12 visual categories, themes can't be lazy
5. **Pure stdlib** — zero external deps (macOS sound via subprocess only)
6. **Performance: 20 FPS on 120×40** — everything has TuneSettings kill switch

## Critical Rules

- NEVER change existing method signatures in plugin.py
- NEVER remove event kinds from bridge.py
- NEVER break .hvtheme v1.0 import
- ALL post-processing defaults to OFF
- ALL emergent systems default to None (disabled)
- Test every phase before moving to next

## Git

- Branch: main
- Last commit: plan v0.2.0 with reactive elements + sound system
- User: Tranquil-Flow <tranquil_flow@protonmail.com>

## How To Start Building

```bash
cd /workspace/Projects/hermes-neurovision
cat PLAN_v0.2.0.md    # read the full plan
# Start Phase 1: Buffer Foundation
# Read renderer.py, understand current draw() flow
# Add FrameBuffer class, refactor draw() to use it
# Run tests: uv run pytest tests/ -q
```
