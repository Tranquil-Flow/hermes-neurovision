# Hermes Neurovision

Terminal neurovisualizer for Hermes Agent. Displays a living neural network that reacts to real agent events.

## Quick Reference

- **Spec:** `docs/superpowers/specs/2026-03-13-hermes-neurovision-design.md`
- **Plan:** `docs/superpowers/plans/2026-03-13-hermes-neurovision.md`
- **Source to extract from:** `~/Desktop/neurovisualizer.py` (846 lines, 10 themes, curses)
- **Tech:** Python 3.10+ stdlib only (curses, sqlite3, json, os, math, random)
- **No external dependencies**

## Architecture

```
hermes_neurovision/
  themes.py       # 10 ThemeConfig definitions
  scene.py        # Particle, Packet, ThemeState simulation
  renderer.py     # Curses drawing
  events.py       # VisionEvent + EventPoller
  bridge.py       # Event -> VisualTrigger mapping
  log_overlay.py  # Fading text overlay
  app.py          # GalleryApp + LiveApp
  cli.py          # Entry point
  sources/        # Event sources (state_db, memories, cron, aegis, custom)
```

## How to Work

1. Read the plan file — it has exact code, file paths, tests, and commands for every step
2. Follow TDD: write test first, verify it fails, implement, verify it passes, commit
3. Each task is self-contained — complete one fully before starting the next
4. Tasks are ordered by dependency — do them in sequence

## Testing

```bash
python -m pytest tests/ -v
```

## Key Constraints

- Pure stdlib — no pip install of external packages
- Each file must be independently understandable
- `sources/hook_handler.py` is standalone — must NOT import from hermes_neurovision
- Aegis features must gracefully degrade if `~/.hermes-aegis/` doesn't exist
- `self.rng` in ThemeState uses `random.Random(seed)` — preserve from original
- `_build_edges()` must be a callable method (not inlined) — needed by `apply_trigger()`
