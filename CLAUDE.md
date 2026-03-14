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
  themes.py       # 55+ ThemeConfig definitions (includes legacy-NAME variants)
  scene.py        # Particle, Packet, ThemeState simulation
  renderer.py     # Curses drawing
  events.py       # VisionEvent + EventPoller
  bridge.py       # Event -> VisualTrigger mapping
  log_overlay.py  # Fading text overlay
  app.py          # GalleryApp + LiveApp
  cli.py          # Entry point
  sources/        # Event sources (state_db, memories, cron, aegis, custom)
  theme_plugins/
    ascii_fields.py   # 10 full-screen generative ASCII field themes
    redesigned.py     # 6 redesigned cosmic themes (v2) + 3 extreme screens
    cosmic_new.py     # Legacy implementations (registered as legacy-NAME)
    mechanical.py     # Legacy starfall (registered as legacy-starfall)
    originals.py      # Original 7 themes
    nature.py / cosmic.py / industrial.py / whimsical.py / hostile.py / exotic.py
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

## Visual Engine

The primary mechanism for full-screen generative effects is the `draw_extras(stdscr, state, color_pairs)` hook on `ThemePlugin`. Themes in `theme_plugins/ascii_fields.py` and `theme_plugins/redesigned.py` use full-screen field rendering — every character cell is computed and drawn each frame.

Key patterns for full-screen renderers:
- Iterate `for y in range(1, h-1): for x in range(0, w-1):`
- Wrap every `stdscr.addstr()` call in `try/except curses.error: pass`
- Map float values 0.0–1.0 to character density palettes (e.g. `" ·.:+*#@"`)
- `state.frame` (int, 20fps) drives animation timing
- `state.intensity_multiplier` (float 0.2–1.0) drives event reactivity — scale brightness/speed by this
- `state.rng` is a seeded `random.Random` — use for deterministic procedural effects
- `state.width` / `state.height` give current terminal dimensions

Color keys available in `color_pairs`: `"bright"`, `"accent"`, `"soft"`, `"base"`, `"warning"`.
Combine with `curses.A_BOLD` or `curses.A_DIM` modifiers.

Themes that use `draw_extras()` as their primary renderer should return `[]` from `build_nodes()`.

## Aegis Integration

`sources/aegis.py` polls `~/.hermes-aegis/audit.jsonl` for security events from the Hermes Aegis module.

**Aegis is OPTIONAL.** The source returns `[]` silently when `~/.hermes-aegis/` does not exist. Never assume Aegis is installed. All theme plugins and visual effects must work without it.

The `--no-aegis` CLI flag disables Aegis polling entirely, even if the path exists.

When writing new event sources or themes: never import from or depend on Aegis-specific paths. If you reference Aegis in a module name or label (e.g. aurora-bands' "aegis" band), it must be cosmetic only — the effect runs regardless.

## Legacy Themes

Themes at positions 37–42 in the original design (starfall, quasar, supernova, sol, terra, binary-star) have been redesigned as full-screen ASCII field renderers in `theme_plugins/redesigned.py`.

The original node-based implementations are preserved under `legacy-NAME` identifiers:
- `legacy-starfall` — original meteor shower with treeline
- `legacy-quasar` — original relativistic jet with node graph
- `legacy-supernova` — original expanding ring shockwave
- `legacy-sol` — original convection cell hexagons
- `legacy-terra` — original coastline + satellite orbit nodes
- `legacy-binary-star` — original two-star ring system

Legacy themes are **not** in the `THEMES` tuple and do not appear in the gallery. Access them directly with `--theme legacy-quasar` etc.
