# Hermes Neurovision v0.2.0 — Build Handover

**Last updated:** 2026-03-16
**Status:** v0.2.0 SHIPPED — 85 themes, full ASCII engine, all features complete

---

## What Is This Project

hermes-neurovision is a curses-based TUI visualizer for hermes-agent. It renders real-time visual themes driven by agent activity data (tool calls, LLM streaming, errors, memory saves, etc).

v0.2.0 has been shipped. All 11 phases of the build plan have been completed.

---

## Current State

- **Version:** 0.2.0
- **Themes:** 85 (60 full-screen ASCII field, 25 node-based, 25 legacy variants)
- **Tests:** 435 passing, 2 known failures (test_themes.py count + full_screen set — update these when adding more themes)
- **Dependencies:** Zero — pure stdlib

---

## Where Everything Lives

```
/workspace/Projects/hermes-neurovision/
├── hermes_neurovision/
│   ├── plugin.py           ← ThemePlugin base class (frozen API)
│   ├── renderer.py         ← Main render loop
│   ├── scene.py            ← ThemeState, effects, particles
│   ├── bridge.py           ← Event → VisualTrigger mapping
│   ├── events.py           ← VisionEvent dataclass
│   ├── tune.py             ← TuneSettings (live sliders)
│   ├── postfx.py           ← Post-processing pipeline
│   ├── reactive.py         ← Reactive Element System
│   ├── export.py           ← .hvtheme export
│   ├── import_theme.py     ← .hvtheme import
│   ├── log_overlay.py      ← HUD event log
│   ├── debug_panel.py      ← Diagnostic overlay
│   ├── sound.py            ← Sound cue system
│   ├── sources/
│   │   ├── custom.py       ← Hook-based event source
│   │   ├── state_db.py     ← SQLite state.db polling
│   │   └── HOOK.yaml       ← Event subscriptions
│   └── theme_plugins/      ← All 85+ themes
├── PLUGIN_API.md           ← Complete plugin authoring reference
├── tests/                  ← 437 tests
└── pyproject.toml          ← version = "0.2.0"
```

---

## What Still Needs Work

- Some legacy node-based themes not yet redesigned (tracked in PLAN_v0.2.0.md tasks 20-43)
- Video demo needs final recording
- Phase 2 (100 themes) not started — see PLAN_v0.2.0.md

---

## Git

- Branch: main
- User: Tranquil-Flow <tranquil_flow@protonmail.com>
- Release commands documented in RELEASE_COMMANDS.md
