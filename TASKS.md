# Hermes Vision — Tasks

Read the full plan at `docs/superpowers/plans/2026-03-13-hermes-vision.md` for exact code, tests, and commands.

## Chunk 1: Project Scaffold + Visual Engine Extraction

- [x] Task 1: Create pyproject.toml, __init__.py, directory structure. Init git repo.
- [x] Task 2: Extract themes.py from ~/Desktop/neurovisualizer.py (THEMES tuple, ThemeConfig, build_theme_config, constants). Write tests first.
- [x] Task 3: Extract scene.py (Particle, Packet, ThemeState with all simulation logic). Keep _build_edges() as callable method. Add intensity_multiplier fields. Write tests first.
- [x] Task 4: Extract renderer.py (Renderer class, all drawing code). Signature: draw(state, gallery_index, gallery_total, end_time). Write tests first.
- [x] Task 5: Extract app.py — GalleryApp with run() and run_headless(). Write tests first.
- [x] Task 6: Create cli.py with argparse + __main__.py. Gallery mode working end-to-end.

## Chunk 2: Event System + Sources

- [x] Task 7: Create events.py — VisionEvent dataclass + EventPoller. Write tests first.
- [x] Task 8: Create sources/custom.py — JSONL file tailer for ~/.hermes/vision/events.jsonl. Write tests first.
- [x] Task 9: Create sources/state_db.py — SQLite poller for ~/.hermes/state.db (sessions + messages tables). Write tests first.
- [x] Task 10: Create sources/memories.py — Filesystem watcher for ~/.hermes/memories/. Write tests first.
- [x] Task 11: Create sources/cron.py — Cron job status poller from ~/.hermes/cron/. Write tests first.
- [x] Task 12: Create sources/aegis.py — Optional Aegis audit trail tailer (graceful if missing). Write tests first.
- [x] Task 13: Create sources/hook_handler.py — Standalone gateway hook + HOOK.yaml. Must NOT import hermes_vision. Write tests first.

## Chunk 3: Bridge + Log Overlay + Live Mode

- [x] Task 14: Create bridge.py — VisualTrigger dataclass + full event-to-visual mapping table (24 event types). Write tests first.
- [x] Task 15: Create log_overlay.py — LogOverlay with fading lines, color coding by source. Write tests first.
- [x] Task 16: Implement apply_trigger() in scene.py (8 effects: packet, pulse, burst, flash, spawn_node, wake, cool_down, dim). Add LiveApp to app.py. Wire up --live mode in cli.py. Write tests first.

## Chunk 4: Polish + Install

- [x] Task 17: pip install -e . and install gateway hook to ~/.hermes/hooks/hermes-vision/
- [x] Task 18: Run full test suite, smoke test gallery and live modes
- [x] Task 19: Register with grove (documented in INSTALL.md)
