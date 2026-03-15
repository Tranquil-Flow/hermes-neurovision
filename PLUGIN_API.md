# Hermes Neurovision — Plugin API Reference (v0.2.0)

This document is the complete reference for writing theme plugins.
All themes are subclasses of `ThemePlugin` in `hermes_neurovision/plugin.py`.

---

## Quick Start

```python
from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register
import curses, math

class MyThemePlugin(ThemePlugin):
    name = "my-theme"   # must match the key in themes.py

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []  # pure ASCII field — no nodes

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        f    = state.frame
        intensity = state.intensity_multiplier
        for y in range(1, h - 1):
            for x in range(0, w - 1):
                v = math.sin(x * 0.1 + f * 0.05) * intensity
                ch = "·:+*#"[min(4, int((v + 1) * 2.5))]
                attr = curses.color_pair(color_pairs["bright"]) if v > 0.5 else 0
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

register(MyThemePlugin())
```

Then add to `themes.py`:
1. Add the name string to the `THEMES` tuple.
2. Add a `ThemeConfig(...)` entry to `build_theme_config()`.

---

## ThemeState — the `state` object

Every draw hook receives a `ThemeState` instance. Key fields:

| Field | Type | Description |
|-------|------|-------------|
| `state.frame` | `int` | Frame counter, increments ~20 fps |
| `state.width` | `int` | Terminal width in columns |
| `state.height` | `int` | Terminal height in rows |
| `state.intensity_multiplier` | `float` | 0.2 (idle) → 1.0 (heavy agent activity) |
| `state.rng` | `random.Random` | Seeded RNG — deterministic per session |
| `state.nodes` | `list[(float,float)]` | Current node positions |
| `state.edges` | `set[(int,int)]` | Node index pairs |
| `state.particles` | `list[Particle]` | Active particles |
| `state.packets` | `list[Packet]` | Active network packets |
| `state.pulses` | `list[(x,y,radius)]` | Expanding pulse rings |
| `state.config` | `ThemeConfig` | Palette and layout parameters |

---

## color_pairs — the standard 5 colour roles

The `color_pairs` dict maps role names to curses pair IDs.
Always use these by name — never by number — for theme portability.

| Key | Role | Default color |
|-----|------|---------------|
| `"bright"` | Primary foreground / highlights | WHITE |
| `"accent"` | Secondary colour | MAGENTA |
| `"soft"` | Dim secondary | CYAN |
| `"base"` | Very dim background texture | BLUE |
| `"warning"` | Errors / alerts | YELLOW |

Usage:
```python
attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
attr = curses.color_pair(color_pairs["soft"])   | curses.A_DIM
```

The actual colours are set by the theme's `palette` tuple in `ThemeConfig`.
`palette = (COLOR_CYAN, COLOR_GREEN, COLOR_YELLOW, COLOR_WHITE)` maps to
`base=pair1=CYAN, soft=pair2=GREEN, bright=pair3=YELLOW, accent=pair4=WHITE`.
`warning` (pair 5) is always YELLOW regardless of palette.

---

## Rainbow Colour Pairs (pairs 10-15)

For themes that need a full spectrum (e.g. strange attractors, plasma), use the
helpers from `attractors.py`:

```python
from hermes_neurovision.theme_plugins.attractors import (
    _ensure_rainbow,     # call once at draw start
    _rainbow_pair,       # t ∈ [0,1] → full-spectrum curses.color_pair(N)
    _rainbow_pair_angle, # radians → colour_pair by angle
)

def draw_extras(self, stdscr, state, color_pairs):
    _ensure_rainbow()
    pair = _rainbow_pair(x / state.width)      # sweeps R→Y→G→C→B→M left→right
    pair = _rainbow_pair_angle(math.atan2(dy, dx))  # angle → colour wheel
```

Pairs 10-15 are R, Y, G, C, B, M. They are outside the 5 engine pairs so
they never collide.

---

## ThemePlugin Hooks — Complete Reference

### Geometry

```python
def build_nodes(self, w, h, cx, cy, count, rng) -> list[(float,float)]:
    """Return list of (x,y) node positions. Return [] for pure ASCII field themes."""

def build_edges_extra(self, nodes, edges_set):
    """Add (a,b) tuples to edges_set for custom connectivity beyond auto-edges."""

def step_nodes(self, nodes, frame, w, h):
    """Mutate nodes list in-place every frame for animated node positions."""
```

### Glyphs and colours

```python
def node_glyph(self, idx, intensity, total) -> str:
    """Return glyph for node at idx. intensity ∈ [0,1] pulses with frame."""

def node_color_key(self, idx, intensity, total) -> str:
    """Return color_pairs key for node: "bright","accent","soft","base","warning"."""

def edge_glyph(self, dx, dy) -> str:
    """Return glyph for edge segment. dx/dy = direction of edge."""

def edge_color_key(self, step, idx_a, frame) -> str:
    """Return color_pairs key for edge at interpolation step."""

def star_glyph(self, brightness, char_idx) -> Optional[str]:
    """Override background star glyph. Return None for default."""

def particle_color_key(self, age_ratio) -> str:
    """Color for particle at this life fraction (0=just born, 1=dying)."""
```

### ASCII field rendering

```python
def draw_background(self, stdscr, state, color_pairs):
    """Rendered BEFORE nodes/edges. Use for ASCII field backdrops in hybrid themes."""

def draw_extras(self, stdscr, state, color_pairs):
    """Rendered AFTER packets/particles. Use for pure ASCII field themes."""
```

Both receive a `_BufferShim` that supports `stdscr.addstr(y, x, text, attr)` and
`stdscr.addch(y, x, ch, attr)`. Use `try/except curses.error: pass` on every write.

### Particle system

```python
def spawn_particle(self, w, h, nodes, rng) -> Optional[Particle]:
    """Return a Particle or None. Called probabilistically each frame."""

def particle_base_chance(self) -> float:
    """Base spawn probability per frame. Default 0.03."""
```

Particle constructor: `Particle(x, y, vx, vy, life, max_life, char)`

### Pulses

```python
def pulse_style(self) -> str:
    """One of: "ring" (default), "rays", "ripple", "cloud", "diamond", "spoked"."""

def pulse_params(self) -> tuple:
    """(rate, radius_max) — rate = pulses per frame, radius = max expansion."""

def pulse_color_key(self) -> str:
    """Color key for pulse glyphs."""
```

### Post-processing pipeline

Return non-None/non-zero values to activate the effect:

```python
def warp_field(self, x, y, w, h, frame, intensity) -> tuple:
    """Return (new_x, new_y) to distort every cell's source position."""

def symmetry(self) -> Optional[str]:
    """Mirror mode: "quad" (4-way), "octal" (8-way), "radial", None."""

def glow_radius(self) -> int:
    """Bloom radius in cells. 0 = disabled. Keep ≤ 1 for performance."""

def echo_decay(self) -> int:
    """Echo ring buffer depth. 0 = disabled. 2-4 = subtle trail."""

def void_intensity(self) -> float:
    """Hole-punching strength. 0.0 = disabled."""

def force_field(self, x, y, w, h, frame) -> tuple:
    """Return (vx, vy) force vector applied to each cell."""

def decay_sequence(self) -> Optional[str]:
    """Char substitution sequence for ageing cells, e.g. "█▓▒░· "."""

def render_mask(self, w, h, frame, intensity) -> Optional[list]:
    """2D boolean grid — False cells are cleared. For shaped themes."""
```

### Reactive system (agent events → visual effects)

```python
from hermes_neurovision.plugin import ReactiveElement, Reaction

def react(self, event_kind: str, data: dict) -> Optional[Reaction]:
    """Called on every agent event. Return a Reaction to trigger visual effect."""
    if event_kind == "tool_call":
        return Reaction(
            element=ReactiveElement.SPARK,
            intensity=0.8,
            origin=(0.5, 0.5),   # (x_ratio, y_ratio) — 0,0=top-left 1,1=bottom-right
            color_key="bright",
            duration=1.0,
        )
    return None
```

Event kinds: `"session_start"`, `"session_end"`, `"tool_call"`, `"memory_save"`,
`"message_added"`, `"error"`, `"llm_start"`, `"llm_end"`, `"token_usage"`.

ReactiveElement values: `SPARK`, `BLOOM`, `RIPPLE`, `WAVE`, `SHATTER`, `VOID`,
`PULSE_BURST`, `STREAK`.

### Special effects overlay

```python
def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity):
    """Draw a named special effect. progress ∈ [0,1] is lifetime fraction."""

def specials(self) -> list:
    """Return list of SpecialEffect definitions for this plugin."""
```

### Sound

```python
from hermes_neurovision.sound import SoundCue

def sound_cues(self) -> dict:
    """Map event_kind → SoundCue. Terminal bell is the only backend."""
    return {"error": SoundCue(name="alert", type="bell", value="", volume=1.0, priority=10)}
```

### Palette shift (reactive palette change)

```python
def palette_shift(self, trigger_effect, intensity, base_palette) -> Optional[tuple]:
    """Return a (C,C,C,C) colour tuple to temporarily swap the palette."""
    if trigger_effect == "error":
        return (curses.COLOR_RED, curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_BLUE)
    return None
```

### Emergent systems

Plugins can declare emergent grid-based systems that run automatically:

```python
def emergent_config(self) -> Optional[dict]:
    """Return a config dict for one emergent system. Examples:

    Reaction-diffusion (Gray-Scott):
      {"type": "reaction_diffusion", "F": 0.037, "k": 0.060, "Du": 0.16, "Dv": 0.08}

    Cellular automaton:
      {"type": "automaton", "rule": "B3/S23"}  # Conway's Life

    Physarum (slime-mold):
      {"type": "physarum", "agents": 200, "sensor_angle": 0.5, "decay": 0.95}

    Wave field:
      {"type": "wave_field", "speed": 0.4, "damping": 0.01}

    Neural field:
      {"type": "neural_field", "excite": 0.8, "inhibit": 0.3}
    """
    return None

def emergent_layer(self) -> str:
    """Where to composite the emergent system: "background", "midground", "foreground"."""
    return "background"
```

---

## ThemeConfig — registration

Every theme needs an entry in `build_theme_config()` in `themes.py`:

```python
ThemeConfig(
    name,           # str  — theme key (must match plugin.name)
    "My Theme",     # str  — human title shown in HUD
    "·",            # str  — accent glyph (used in some pulse styles)
    0.0,            # float — background density (star density)
    0.0,            # float — star drift speed
    0.0,            # float — node jitter radius
    0.0,            # float — packet rate
    (0.02, 0.05),   # tuple — packet speed range (min, max)
    0.0,            # float — pulse rate
    0.5,            # float — edge bias (0=sparse, 1=dense)
    2,              # int   — cluster count
    palette=(curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_WHITE),
    # palette maps to: base=pair1, soft=pair2, bright=pair3, accent=pair4
)
```

For pure ASCII field themes that don't use the node engine, set the numeric
parameters to 0.0 / 0 — only `palette` matters.

---

## Best Practices

### For pure ASCII field themes

- Return `[]` from `build_nodes()`.
- All rendering goes in `draw_extras()`.
- Iterate `for y in range(1, h-1): for x in range(0, w-1)` — leave row 0 and
  `h-1` for the HUD title/footer.
- Always wrap `stdscr.addstr(...)` in `try/except curses.error: pass`.
- Scale everything to `state.width` and `state.height` — terminals resize.
- Use `state.intensity_multiplier` to scale animation speed and density.
- Use `state.frame` for time — it's an integer at ~20fps.

### For rainbow colour themes

- Call `_ensure_rainbow()` at the top of `draw_extras()` — it's idempotent.
- `_rainbow_pair(t)` for t ∈ [0,1] gives the full R→Y→G→C→B→M sweep.
- `_rainbow_pair_angle(a)` maps a radian angle to a colour (full circle = full spectrum).
- Vary hue by position AND by time: `hue_t = (x/w + f*0.01) % 1.0`.

### For density-field attractors

- Maintain a `_grid: list[list[float]]` — accumulate where the orbit visits.
- Apply `decay` each frame: `v *= decay; if v < 0.01: continue`.
- Use `_density_char(v)` for the char and `_attr_by_density(v)` for bold/dim.
- Warm up the trajectory in `_setup()` (3000+ steps) to skip the transient.

### Avoiding common mistakes

- Never use `glow_radius > 0` with MAGENTA in the palette — it paints purple
  block halos around every glyph. Use glow only with white/cyan palettes.
- `echo_decay` + block chars (`█▓▒`) + high intensity = smearing artefacts.
  Use echo only with point chars (`.·:+`) or set decay to 0.
- Don't set attributes on plain Python lists — Python 3.14 forbids it.
  Use `[age, data]` wrapper lists or dataclasses instead.
- Keep `fractal_zoom` and similar compute-heavy loops bounded — target < 1ms
  per frame on an M-series Mac at 80×24.

---

## Walkthrough: Writing a Strange Attractor Theme

A minimal but complete example — the Duffing oscillator:

```python
from hermes_neurovision.plugin import ThemePlugin
from hermes_neurovision.theme_plugins import register
from hermes_neurovision.theme_plugins.attractors import (
    _ensure_rainbow, _rainbow_pair_angle, _density_char, _attr_by_density,
)
import curses, math

class DuffingPlugin(ThemePlugin):
    name = "duffing"

    def __init__(self):
        self._grid = None
        self._w = self._h = 0
        self._x = 0.1
        self._y = 0.0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        _ensure_rainbow()

        if self._grid is None or (w, h) != (self._w, self._h):
            self._grid = [[0.0] * w for _ in range(h)]
            self._w, self._h = w, h
            self._x, self._y = 0.1, 0.0

        intensity = state.intensity_multiplier
        dt = 0.02
        alpha, beta, delta, gamma, omega = 1.0, -1.0, 0.3, 0.5, 1.2
        t = state.frame * dt * 20

        for _ in range(int(300 * intensity)):
            # Duffing ODE: dx = y, dy = -delta·y - alpha·x - beta·x³ + gamma·cos(omega·t)
            dx = self._y
            dy = -delta*self._y - alpha*self._x - beta*self._x**3 + gamma*math.cos(omega*t)
            self._x += dx * dt
            self._y += dy * dt
            sx = int(w/2 + self._x * w * 0.15)
            sy = int(h/2 - self._y * h * 0.25)
            if 1 <= sy < h-1 and 0 <= sx < w-1:
                self._grid[sy][sx] = min(self._grid[sy][sx] + 0.05, 1.0)

        decay = 0.975
        for y in range(1, h-1):
            for x in range(w-1):
                v = self._grid[y][x] * decay
                self._grid[y][x] = v
                if v < 0.01:
                    continue
                angle = math.atan2(y - h/2, x - w/2)
                pair = _rainbow_pair_angle(angle)
                ch = _density_char(v)
                try:
                    stdscr.addstr(y, x, ch, pair | _attr_by_density(v))
                except curses.error:
                    pass

register(DuffingPlugin())
```

---

## File Layout

```
hermes_neurovision/
  plugin.py              # ThemePlugin base class + ReactiveElement + Reaction
  themes.py              # THEMES tuple + build_theme_config()
  scene.py               # ThemeState, Particle, Packet, Streak
  renderer.py            # Frame buffer + render pipeline
  postfx.py              # apply_warp, apply_glow, apply_echo, apply_symmetry, etc.
  theme_plugins/
    __init__.py          # register() function + _load_all() auto-importer
    attractors.py        # 5 strange attractors + rainbow colour helpers
    spectacular.py       # 5 spectacle themes (plasma, tunnel, fractal, vortex, chladni)
    ascii_fields.py      # 10 field themes (plasma, oracle, life-colony, etc.)
    experimental.py      # 3 experimental (clifford, barnsley-fern, flow-field)
    emergent_showcase.py # 5 emergent system showcase themes
    emergent_v2.py       # 5 v0.2.0 engine feature demos
    advanced_screens.py  # 5 postfx + reactive hybrid themes
    redesigned.py        # 15 redesigned classic themes
    originals_v2.py      # Original 7 themes (v2)
    nature_v2.py         # Nature themes (v2)
    originals.py         # Node-based originals (legacy backend)
    nature.py / cosmic.py / industrial.py / whimsical.py
    hostile.py / exotic.py / mechanical.py / cosmic_new.py
```

---

*For questions, see the source of `attractors.py` and `spectacular.py` for
patterns, or `ascii_fields.py` for simpler per-pixel field examples.*
