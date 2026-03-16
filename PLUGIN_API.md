# Hermes Neurovision — Plugin API Reference (v0.2.0)

This document is the complete reference for writing theme plugins.
All themes are subclasses of `ThemePlugin` in `hermes_neurovision/plugin.py`.

---

## Quick Start

```python
from hermes_neurovision.plugin import ThemePlugin, ReactiveElement, Reaction
from hermes_neurovision.theme_plugins import register
import curses, math, random

class MyThemePlugin(ThemePlugin):
    name = "my-theme"   # unique slug — used with --theme CLI flag

    def __init__(self):
        self._grid = None
        self._rng = random.Random(42)   # own rng for per-frame stochastic work
        self._w = self._h = 0

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []  # [] = skip graph layer; use for pure ASCII field themes

    def draw_extras(self, stdscr, state, color_pairs):
        w, h, f = state.width, state.height, state.frame
        intensity = state.intensity_multiplier
        spd = state.tune.animation_speed if state.tune else 1.0
        bright = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        soft   = curses.color_pair(color_pairs["soft"])
        t = f * 0.04 * spd
        for y in range(1, h - 1):
            for x in range(0, w - 1):
                v = (math.sin(x * 0.1 + t) + 1.0) / 2.0 * intensity
                ch = "·:+*#"[min(4, int(v * 5))]
                try:
                    stdscr.addstr(y, x, ch, bright if v > 0.6 else soft)
                except curses.error:
                    pass

register(MyThemePlugin())
```

Then add to `themes.py`:
1. Add the name string to the `THEMES` tuple.
2. Add a `ThemeConfig(...)` entry to `build_theme_config()`.

---

## ThemeState — the `state` object

Every draw hook receives a `ThemeState` instance.

| Field | Type | Description |
|-------|------|-------------|
| `state.frame` | `int` | Frame counter, increments ~20fps |
| `state.width` | `int` | Terminal width in columns |
| `state.height` | `int` | Terminal height in rows |
| `state.intensity_multiplier` | `float` | Resting ~0.6, spikes to 1.5+ on events |
| `state.rng` | `random.Random` | Seeded RNG — use for init only, not per-frame |
| `state.quiet` | `bool` | True in daemon quiet mode — suppress passive spawns |
| `state.tune` | `TuneSettings\|None` | All slider/toggle values (None outside interactive mode) |
| `state.config` | `ThemeConfig` | Palette and layout parameters |
| `state.flash_until` | `float` | Unix timestamp — if > now, a flash event is active |
| `state.flash_color_key` | `str` | Color key for active flash |
| `state._last_event_time` | `float` | Unix timestamp of last agent event (for idle detection) |
| `state.nodes` | `list[(float,float)]` | Current node positions |
| `state.edges` | `list[(int,int)]` | Node index pairs |
| `state.particles` | `list[Particle]` | Active particles |
| `state.packets` | `list[Packet]` | Active network packets |
| `state.pulses` | `list[(x,y,radius)]` | Expanding pulse rings |
| `state.streaks` | `list[Streak]` | Active streak effects |
| `state.automaton` | `CellularAutomaton\|None` | Active if `automaton_config()` returned a config |
| `state.physarum` | `PhysarumSim\|None` | Active if `physarum_config()` returned a config |
| `state.neural_field` | `NeuralField\|None` | Active if `neural_field_config()` returned a config |
| `state.wave_field` | `WaveField\|None` | Active if `wave_config()` returned a config |
| `state.boids` | `BoidsFlock\|None` | Active if `boids_config()` returned a config |
| `state.reaction_diffusion` | `ReactionDiffusion\|None` | Active if `reaction_diffusion_config()` returned a config |

**Important:** `state.rng` is seeded once at init — use it only for initialization.
For per-frame stochastic work (particles, random positions), store `self._rng = random.Random(seed)` in `__init__`.

---

## TuneSettings — sliders and toggles

When `state.tune` is not None, plugins can read all user-adjustable parameters.
**Always guard:** `val = state.tune.animation_speed if state.tune else 1.0`

**Sliders** (all float):

| Attribute | Range | What it controls |
|-----------|-------|-----------------|
| `animation_speed` | 0.1–5.0 | Time multiplier — multiply your frame speed by this |
| `particle_density` | 0.0–3.0 | Multiplier on particle spawn probability |
| `packet_rate_mult` | 0.0–3.0 | Multiplier on packet spawn rate |
| `pulse_rate_mult` | 0.0–3.0 | Multiplier on pulse spawn rate |
| `burst_scale` | 0.0–3.0 | Scale of burst event visuals |
| `event_sensitivity` | 0.0–3.0 | How hard events spike intensity |
| `warp_strength` | 0.0–3.0 | PostFX warp displacement scale (0=disabled) |
| `void_intensity` | 0.0–3.0 | PostFX void/erase effect scale (0=disabled) |
| `force_strength` | 0.0–3.0 | PostFX force field scale (0=disabled) |
| `decay_rate` | 0.0–3.0 | PostFX cell decay multiplier (0=disabled) |
| `emergent_speed` | 0.0–3.0 | Emergent simulation speed (0=paused) |
| `emergent_opacity` | 0.0–1.0 | Emergent layer visibility |
| `sound_volume` | 0.0–1.0 | Sound engine volume |

**Toggles** (all bool):
`show_packets`, `show_particles`, `show_pulses`, `show_stars`, `show_background`,
`show_nodes`, `show_flash`, `show_spawn_node`, `show_streaks`, `show_specials`,
`show_overlays`, `color_shifts`, `mask_enabled`, `symmetry_enabled`,
`reactive_elements`, `sound_enabled`

---

## color_pairs — the standard 5 colour roles

The `color_pairs` dict maps role names to curses pair IDs.
Always use these by name — never by number — for theme portability.

| Key | Role |
|-----|------|
| `"bright"` | Primary highlight — use with `curses.A_BOLD` for maximum impact |
| `"accent"` | Secondary / warm complement |
| `"soft"` | Dim/muted — mid-range density fill |
| `"base"` | Near-background texture — use with `curses.A_DIM` |
| `"warning"` | Errors / alerts / hot spots |

Usage:
```python
bright = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
accent = curses.color_pair(color_pairs["accent"])
soft   = curses.color_pair(color_pairs["soft"])
dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM
danger = curses.color_pair(color_pairs["warning"]) | curses.A_BOLD
```

The actual colours come from the theme's `palette` tuple in `ThemeConfig`:
`palette = (C1, C2, C3, C4)` → `bright=C3, accent=C4, soft=C2, base=C1`.
`warning` (pair 5) is always YELLOW regardless of palette.

---

## Rainbow Colour Pairs (pairs 10–15)

For themes that need a full spectrum (strange attractors, plasma), use the
helpers from `attractors.py`:

```python
from hermes_neurovision.theme_plugins.attractors import (
    _ensure_rainbow,      # call once at draw start — idempotent
    _rainbow_pair,        # t ∈ [0,1] → full-spectrum curses.color_pair(N)
    _rainbow_pair_angle,  # radians → colour_pair by angle
)

def draw_extras(self, stdscr, state, color_pairs):
    _ensure_rainbow()
    pair = _rainbow_pair(x / state.width)          # sweeps R→Y→G→C→B→M
    pair = _rainbow_pair_angle(math.atan2(dy, dx))  # angle → colour wheel
```

Pairs 10–15 are R, Y, G, C, B, M. They never collide with the 5 engine pairs.

---

## ThemePlugin Hooks — Complete Reference

### Geometry

```python
def build_nodes(self, w, h, cx, cy, count, rng) -> list:
    """Return list of (x,y) node positions. Return [] for pure ASCII field themes.
    Return None to use default cluster logic."""

def build_edges_extra(self, nodes, edges_set):
    """Add tuple(sorted((a,b))) pairs to edges_set for custom connectivity."""

def step_nodes(self, nodes, frame, w, h):
    """Mutate nodes list in-place every frame for animated positions."""

def node_position_adjust(self, x, y, idx, frame, w, h) -> Optional[tuple]:
    """Extra per-node position tweak. Return (x, y) or None."""

def edge_keep_count(self) -> int:
    """Nearest-neighbour count for automatic edge building. Default 3."""
```

### Glyphs and colours

```python
def node_glyph(self, idx, intensity, total) -> str:
    """Glyph for node at idx. intensity ∈ [0,1] pulses with frame."""

def node_color_key(self, idx, intensity, total) -> str:
    """Color key for node: "bright","accent","soft","base","warning"."""

def edge_glyph(self, dx, dy) -> Optional[str]:
    """Glyph for edge segment direction. Return None for default."""

def edge_color_key(self, step, idx_a, frame) -> str:
    """Color key for edge at interpolation step."""

def star_glyph(self, brightness, char_idx) -> Optional[str]:
    """Override background star glyph. Return None for default."""

def particle_color_key(self, age_ratio) -> str:
    """Color for particle at this life fraction (0=just born, 1=dying)."""

def packet_color_key(self) -> str:
    """Color key for data packets traversing edges."""

def pulse_color_key(self) -> str:
    """Color key for pulse ring glyphs."""

def streak_color_key(self) -> str:
    """Color key for streak effects."""
```

### ASCII field rendering

```python
def draw_background(self, stdscr, state, color_pairs):
    """Called BEFORE nodes/edges. Use for ASCII field backdrops in hybrid themes
    where you want both a generative field AND the graph layer on top."""

def draw_extras(self, stdscr, state, color_pairs):
    """Called AFTER all other layers. Main hook for pure ASCII field themes.
    Also use for foreground overlays in hybrid themes."""
```

Both receive a live curses window. Use `try/except curses.error: pass` on every write.

### Particle system

```python
def spawn_particle(self, w, h, nodes, rng) -> Optional[Particle]:
    """Return a Particle or None. Called probabilistically each frame."""

def particle_base_chance(self) -> float:
    """Base spawn probability per frame. Default 0.028."""

def particle_life_range(self) -> tuple:
    """(min_life, max_life) integers. Default (7, 14)."""
```

Particle constructor: `Particle(x, y, vx, vy, life, max_life, char, frames=None)`

The optional `frames` list cycles through characters each step — enables
animated particles (e.g. `frames=["·", ":", "*", "✦", "*", ":", "·"]`).

### Pulses

```python
def pulse_style(self) -> str:
    """One of: "ring" (default), "rays", "ripple", "cloud", "diamond", "spoked"."""

def pulse_params(self) -> tuple:
    """(growth_rate, limit_ratio) — growth per frame, max radius as fraction of screen."""

def pulse_color_key(self) -> str:
    """Color key for pulse glyphs."""
```

### Packet system

```python
def packet_budget(self) -> int:
    """Max simultaneous data packets on edges. Default 4."""
```

### Star movement

```python
def step_star(self, star, frame, w, h, rng) -> bool:
    """Custom star movement. Return True if handled, False for default drift.
    star = [x, y, brightness, char_idx] — mutate in-place."""

def step_star_post(self, star, frame, w, h, rng):
    """Post-drift tweak (runs after default drift if step_star returned False)."""
```

### Post-processing pipeline

All PostFX run on the FrameBuffer after drawing. Return non-default values to activate.

```python
def glow_radius(self) -> int:
    """Color bleed radius. 0=disabled, 1=subtle, 2=medium, 3=strong.
    Bright non-space cells propagate color as dim '·' into empty neighbors."""

def echo_decay(self) -> int:
    """Afterimage buffer depth. 0=disabled. 3-5=subtle trail, 8+=strong ghost.
    Empty cells get filled with dimmed content from N frames ago."""

def decay_sequence(self) -> Optional[str]:
    """Char aging sequence, e.g. '█▓▒░·. ' — cells age through this.
    Advance every 3 frames. Good for crystallization/erosion effects."""

def symmetry(self) -> Optional[str]:
    """Mirror mode: 'mirror_x' | 'mirror_y' | 'mirror_xy' | 'rotate_4' | None.
    Can be toggled off by user via tune.symmetry_enabled."""

def depth_layers(self) -> int:
    """Parallax depth simulation. 1=flat (disabled), 2-4=layered parallax."""

def warp_field(self, x, y, w, h, frame, strength) -> tuple:
    """Displacement mapping. Return (src_x, src_y) to sample for each (x, y).
    strength comes from tune.warp_strength — check before computing."""

def void_points(self, w, h, frame, intensity) -> list:
    """Return list of (x, y) positions to erase each frame.
    intensity comes from tune.void_intensity."""

def force_points(self, w, h, frame, strength) -> list:
    """Return list of (x, y, force_strength, force_type) descriptors.
    force_type: 'radial' (push/pull) or 'vortex' (tangential spin).
    strength comes from tune.force_strength."""

def render_mask(self, w, h, frame, intensity) -> Optional[list]:
    """2D list[list[bool]] stencil — False cells are cleared.
    Can be toggled by tune.mask_enabled."""
```

**Corrections from old docs:**
- `symmetry()` modes are `'mirror_x'`, `'mirror_y'`, `'mirror_xy'`, `'rotate_4'` — NOT "quad"/"octal"/"radial"
- `void_points()` returns positions to erase — there is no `void_intensity()` method
- `force_points()` returns force descriptors — there is no `force_field()` method

### Reactive system (agent events → visual effects)

```python
from hermes_neurovision.plugin import ReactiveElement, Reaction

def react(self, event_kind: str, data) -> Optional[Reaction]:
    """Called on every agent event. Return a Reaction to trigger visual effect.
    IMPORTANT: only fires in live/daemon mode, NOT in gallery mode."""
    if event_kind == "tool_call":
        return Reaction(
            element=ReactiveElement.RIPPLE,
            intensity=0.7,
            origin=(0.5, 0.5),   # (x_ratio, y_ratio) — 0,0=top-left 1,1=bottom-right
            color_key="accent",
            duration=1.8,
            sound="tool_ping",   # optional: SoundCue name to fire
        )
    return None
```

**Complete `event_kind` list:**

| Event | Default element |
|-------|----------------|
| `"agent_start"`, `"agent_end"`, `"session_resume"` | PULSE |
| `"tool_call"`, `"tool_complete"`, `"tool_error"`, `"mcp_tool_call"` | RIPPLE |
| `"llm_start"`, `"llm_chunk"`, `"llm_end"` | STREAM |
| `"memory_save"`, `"skill_create"`, `"checkpoint_created"` | BLOOM |
| `"error"`, `"crash"`, `"threat_blocked"` | SHATTER |
| `"cron_tick"`, `"background_proc"`, `"subagent_started"` | ORBIT |
| `"context_pressure"`, `"token_usage"`, `"cost_update"` | GAUGE |
| `"approval_request"`, `"dangerous_cmd"` | SPARK |
| `"compression_started"`, `"compression_ended"`, `"checkpoint_rollback"` | WAVE |
| `"personality_change"`, `"reasoning_change"` | GLYPH |
| `"browser_navigate"`, `"file_edit"`, `"git_commit"` | TRAIL |
| `"mcp_connected"`, `"mcp_disconnected"`, `"provider_health"` | CONSTELLATION |

**Complete `ReactiveElement` enum:**
`PULSE`, `RIPPLE`, `STREAM`, `BLOOM`, `SHATTER`, `ORBIT`, `GAUGE`, `SPARK`,
`WAVE`, `GLYPH`, `TRAIL`, `CONSTELLATION`

**`Reaction` fields:**
```python
Reaction(
    element=ReactiveElement.BLOOM,
    intensity=1.0,           # 0.0–1.0, how dramatic
    origin=(0.5, 0.5),       # (x_ratio, y_ratio) normalized screen position
    color_key="bright",      # "bright"|"accent"|"soft"|"base"|"warning"
    duration=2.5,            # seconds
    data={},                 # element-specific params (e.g. {"dx": 1} for STREAM)
    sound=None,              # optional SoundCue name to fire when reaction triggers
)
```

**Gallery mode:** `react()` does NOT fire in gallery. Gallery uses a synthetic
activity pump that triggers `draw_overlay_effect()` and `special_effects()` instead,
via string events: `"wake"`, `"ripple"`, `"burst"`, `"pulse"`, `"packet"`,
`"cascade"`, `"cool_down"`.

### Draw overlay effect (gallery-mode event visuals)

```python
def draw_overlay_effect(self, stdscr, state, color_pairs,
                        trigger_effect: str, intensity: float, progress: float):
    """Called for gallery synthetic events. progress ∈ [0,1] over duration."""
    pass
```

### Special effects

```python
from hermes_neurovision.plugin import SpecialEffect

def special_effects(self) -> list:
    """Declare up to 3 named special effects. Default: none."""
    return [
        SpecialEffect(
            name="supernova",
            trigger_kinds=["burst", "pulse"],
            min_intensity=0.7,
            cooldown=8.0,
            duration=3.0,
        ),
    ]

def draw_special(self, stdscr, state, color_pairs,
                 special_name: str, progress: float, intensity: float):
    """Draw a named special effect. progress ∈ [0,1] over the effect's duration."""
    pass
```

Note: the method is `special_effects()` — not `specials()`.

### Ambient tick (idle animation)

```python
def ambient_tick(self, stdscr, state, color_pairs, idle_seconds: float):
    """Called every frame when no events are firing.
    idle_seconds = time since last agent event. Grows the longer the agent is quiet.
    Use to transition from active → calm state (slow animations, breathe)."""
    pass
```

### Intensity curve

```python
def intensity_curve(self, raw: float) -> float:
    """Transform raw intensity (0..1.5) through a theme-specific curve.
    Default: identity. Use to compress, expand, or shape the feel."""
    return raw  # or: math.pow(raw, 1.5) for dramatic peaks
```

### Palette shift

```python
def palette_shift(self, trigger_effect: str, intensity: float,
                  base_palette: tuple) -> Optional[tuple]:
    """Return a (C, C, C, C) colour tuple to temporarily swap the palette,
    or None to keep current."""
    import curses
    if trigger_effect == "burst":
        return (curses.COLOR_RED, curses.COLOR_YELLOW,
                curses.COLOR_WHITE, curses.COLOR_MAGENTA)
    return None
```

### Sound

Sound is triggered via the `sound` field on `Reaction`. No `sound_cues()` method exists.

```python
from hermes_neurovision.sound import SoundCue

# Sound types:
#   'bell'  — curses.beep(), universal, falls back to \a
#   'flash' — curses.flash(), universal screen flash
#   'say'   — macOS only: say -v Whisper <text> (fire-and-forget TTS)
#   'file'  — macOS only: afplay -v <vol> <path> (WAV/AIFF/MP3)
#
# Attach to a Reaction:
def react(self, event_kind, data):
    if event_kind == "memory_save":
        return Reaction(ReactiveElement.BLOOM, 1.0, (0.5, 0.5), "bright", 2.5,
                        sound="remembered")  # fires the SoundCue named "remembered"
```

### Emergent systems

Each system has its own config method. Return a dict to enable, `None` to disable.
The engine creates and manages the simulation automatically.

```python
def automaton_config(self) -> Optional[dict]:
    """Cellular automaton. rule options: 'brians_brain'"""
    return {"rule": "brians_brain", "density": 0.08, "update_interval": 2}

def physarum_config(self) -> Optional[dict]:
    """Physarum slime-mold network formation."""
    return {"n_agents": 150, "sensor_dist": 4.0, "sensor_angle": 0.785,
            "deposit": 1.0, "decay": 0.95}

def neural_field_config(self) -> Optional[dict]:
    """Spreading activation / neural field."""
    return {"threshold": 2, "fire_duration": 2, "refractory": 5}

def wave_config(self) -> Optional[dict]:
    """Wave propagation field."""
    return {"speed": 0.3, "damping": 0.98}

def boids_config(self) -> Optional[dict]:
    """Flocking / boids simulation."""
    return {"n_boids": 40, "sep_dist": 3.0, "align_dist": 8.0,
            "cohesion_dist": 12.0, "max_speed": 1.5}

def reaction_diffusion_config(self) -> Optional[dict]:
    """Gray-Scott reaction-diffusion. F=feed, k=kill."""
    # Coral/fingerprints: F=0.037, k=0.060 | Spots: F=0.035, k=0.065
    # Spirals: F=0.014, k=0.054            | Labyrinth: F=0.029, k=0.057
    return {"feed": 0.037, "kill": 0.060, "update_interval": 2}

def emergent_layer(self) -> str:
    """Composite layer: 'background' | 'midground' | 'foreground'."""
    return "background"
```

**Correction from old docs:** There is no single `emergent_config()` method.
Each system has its own dedicated config method as shown above.

Speed and opacity are controlled by `tune.emergent_speed` and `tune.emergent_opacity` automatically.

### Effect zones

```python
def effect_zones(self) -> dict:
    """Map zone names to (x, y, w, h) normalized rects. Default: no zones."""
    return {"center": (0.3, 0.3, 0.4, 0.4)}
```

---

## ThemeConfig — registration

Every theme needs an entry in `build_theme_config()` in `themes.py`:

```python
ThemeConfig(
    name,                  # str   — must match plugin.name exactly
    "My Theme",            # str   — human title shown in HUD
    "·",                   # str   — accent glyph (packets, some pulse styles)
    background_density=0.025,  # float — star density (0.01=sparse, 0.05=dense)
    star_drift=0.04,           # float — star movement speed
    node_jitter=0.20,          # float — node position variation radius
    packet_rate=0.28,          # float — packet spawn probability per frame
    packet_speed=(0.04, 0.08), # tuple — (min, max) packet travel speed
    pulse_rate=0.09,           # float — pulse spawn rate
    edge_bias=0.50,            # float — edge clustering (0=random, 1=tight)
    cluster_count=3,           # int   — number of node clusters
    palette=(
        curses.COLOR_CYAN, curses.COLOR_BLUE,
        curses.COLOR_WHITE, curses.COLOR_MAGENTA,
    ),
    # palette[0]=base, palette[1]=soft, palette[2]=bright, palette[3]=accent
)
```

For pure ASCII field themes that don't use the node engine, set all numeric
parameters to 0.0 / 0 — only `palette` matters for colour.

---

## Best Practices

### For pure ASCII field themes

- Return `[]` from `build_nodes()`.
- All rendering goes in `draw_extras()`.
- Iterate `for y in range(1, h-1): for x in range(0, w-1)` — leave row 0 and
  `h-1` for the HUD title/footer.
- Always wrap `stdscr.addstr(...)` in `try/except curses.error: pass`.
- Scale everything to `state.width` and `state.height` — terminals resize.
- Use `state.intensity_multiplier` to scale animation speed, density, brightness.
- Use `state.frame` for time — it's an integer at ~20fps.
- Guard tune: `spd = state.tune.animation_speed if state.tune else 1.0`

### Intensity coupling

```python
intensity = state.intensity_multiplier  # resting ~0.6, spikes to 1.5+ on events
spd = state.tune.animation_speed if state.tune else 1.0

t = f * 0.04 * spd                          # time variable
steps = int(800 * (0.4 + intensity) * spd)  # iteration count
decay = 0.975 - 0.01 * intensity            # density grid decay
thresh = max(0.45, 0.75 - 0.15 * intensity) # reactive brightness threshold
```

### For rainbow colour themes

- Call `_ensure_rainbow()` at the top of `draw_extras()` — it's idempotent.
- `_rainbow_pair(t)` for t ∈ [0,1] gives the full R→Y→G→C→B→M sweep.
- `_rainbow_pair_angle(a)` maps a radian angle to a colour (full circle = full spectrum).
- Vary hue by position AND time: `hue_t = (x / w + f * 0.01) % 1.0`

### For density-field attractors

- Maintain `self._grid = [[0.0] * w for _ in range(h)]` — accumulate hits.
- Resize guard every frame: `if self._grid is None or (w, h) != (self._w, self._h)`
- Apply decay: `v *= decay` — tune decay from 0.88 (fast, ~8 frames) to 0.977 (slow, ~40 frames).
- For 3D attractors: rotate azimuth `az += 0.006/frame`, nod elevation with sine.
- Use fast decay (~0.88) when the projection changes to prevent smear.

### Terminal aspect ratio

Characters are ~2× taller than wide. Compensate for isotropic shapes:
```python
dist = math.sqrt(dx * dx / 2.0 + dy * dy)   # isotropic distance
# For radii: rx = 2 * ry to draw circles that look round
```

### Avoiding common mistakes

- Never use `glow_radius > 1` with dark palettes — bleeds '·' everywhere.
- `echo_decay` + block chars (`█▓▒`) + high intensity = smearing artefacts.
  Use echo only with point chars (`.·:+`) or keep decay ≤ 4.
- Don't return `None` from `build_nodes()` to skip nodes — return `[]`.
- `state.rng` is for initialization only. Per-frame random: use `self._rng` (own instance).
- `state.color_theme` does not exist. Colors come from `color_pairs` dict argument.
- `state.tune` may be `None` outside interactive mode. Always guard.
- `symmetry()` modes are `'mirror_x'`, `'mirror_y'`, `'mirror_xy'`, `'rotate_4'`.
  There are no "quad", "octal", or "radial" modes.

---

## Walkthrough: Writing a Strange Attractor Theme

A minimal but complete example — the Duffing oscillator:

```python
from hermes_neurovision.plugin import ThemePlugin, ReactiveElement, Reaction
from hermes_neurovision.theme_plugins import register
from hermes_neurovision.theme_plugins.attractors import (
    _ensure_rainbow, _rainbow_pair_angle,
)
import curses, math, random

class DuffingPlugin(ThemePlugin):
    name = "duffing"

    def __init__(self):
        self._grid = None
        self._w = self._h = 0
        self._x = 0.1
        self._y = 0.0
        self._rng = random.Random(99)

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def glow_radius(self):
        return 1

    def echo_decay(self):
        return 3  # subtle trail

    def react(self, event_kind, data):
        if event_kind == "agent_start":
            return Reaction(ReactiveElement.PULSE, 0.9, (0.5, 0.5), "bright", 2.5)
        if event_kind in ("error", "crash"):
            return Reaction(ReactiveElement.SHATTER, 1.0, (0.5, 0.5), "warning", 2.0)
        return None

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier
        spd = state.tune.animation_speed if state.tune else 1.0

        _ensure_rainbow()

        if self._grid is None or (w, h) != (self._w, self._h):
            self._grid = [[0.0] * w for _ in range(h)]
            self._w, self._h = w, h
            self._x, self._y = 0.1, 0.0

        dt = 0.02
        alpha, beta, delta, gamma, omega = 1.0, -1.0, 0.3, 0.5, 1.2
        t = f * dt * 20 * spd

        for _ in range(int(300 * intensity * spd)):
            dx = self._y
            dy = (-delta * self._y - alpha * self._x
                  - beta * self._x ** 3 + gamma * math.cos(omega * t))
            self._x += dx * dt
            self._y += dy * dt
            sx = int(w / 2 + self._x * w * 0.15)
            sy = int(h / 2 - self._y * h * 0.25)
            if 1 <= sy < h - 1 and 0 <= sx < w - 1:
                self._grid[sy][sx] = min(self._grid[sy][sx] + 0.05, 1.0)

        decay = 0.975 - 0.01 * intensity
        chars = " ·.,:;=+*#▒▓█"
        nc = len(chars)

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                v = self._grid[y][x] * decay
                self._grid[y][x] = v
                if v < 0.01:
                    continue
                angle = math.atan2(y - h / 2, (x - w / 2) / 2.0)
                pair = _rainbow_pair_angle(angle)
                ch = chars[max(0, min(nc - 1, int(v * (nc - 1))))]
                attr = pair | (curses.A_BOLD if v > 0.7 else 0)
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

register(DuffingPlugin())
```

---

## File Layout

```
hermes_neurovision/
  plugin.py              # ThemePlugin base class, ReactiveElement, Reaction,
                         #   SpecialEffect, ReactiveElement enum (12 values)
  themes.py              # THEMES tuple + build_theme_config() + ThemeConfig
  scene.py               # ThemeState, Particle, Packet, Streak, OverlayEffect
  tune.py                # TuneSettings (all sliders/toggles) + TuneOverlay
  sound.py               # SoundCue, SoundEngine (bell/flash/say/file)
  renderer.py            # FrameBuffer, Cell, Renderer
  postfx.py              # apply_warp, apply_void, apply_echo, apply_glow,
                         #   apply_decay, apply_symmetry, apply_mask,
                         #   apply_force_field, snapshot_buffer
  reactive.py            # ReactiveRenderer, ActiveReaction, element renderers
  emergent/
    automaton.py         # CellularAutomaton (brians_brain rule)
    physarum.py          # PhysarumSim (slime-mold)
    neural_field.py      # NeuralField (spreading activation)
    wave_field.py        # WaveField (wave propagation)
    boids.py             # BoidsFlock (flocking)
    reaction_diffusion.py  # ReactionDiffusion (Gray-Scott)
  theme_plugins/
    __init__.py          # register() + auto-importer (all .py files)
    attractors.py        # lorenz, rossler-ribbon, halvorsen-star, aizawa-torus,
                         #   thomas-labyrinth + rainbow colour helpers
    spectacular.py       # hypnotic-tunnel, plasma-rainbow, fractal-zoom,
                         #   particle-vortex, chladni-sand
    ascii_fields.py      # synaptic-plasma, oracle, cellular-cortex, reaction-field,
                         #   stellar-weave, life-colony, aurora-bands,
                         #   waveform-scope, lissajous-mind, pulse-matrix
    experimental.py      # clifford-attractor, barnsley-fern, flow-field
    emergent_showcase.py # mycelium-network, swarm-mind, neural-cascade,
                         #   tide-pool, turing-garden
    emergent_v2.py       # dna-helix, pendulum-waves, kaleidoscope,
                         #   electric-storm, coral-growth
    advanced_screens.py  # dna-strand, pendulum-array, mandala-scope,
                         #   ghost-echo, magnetic-field
    generated_screens.py # fourier-epicycles, harmonograph, spirograph,
                         #   julia-morph, wireframe-cube, hypercube-fold, ...
    new_screens.py       # lorenz-butterfly, quantum-foam, ascii-rain,
                         #   sand-automaton, ascii-rorschach, ...
    redesigned.py        # redesigned classic themes
    originals_v2.py      # black-hole and other originals (v2)
    nature_v2.py         # nature themes (v2)
    originals.py / nature.py / cosmic.py / industrial.py / whimsical.py
    hostile.py / exotic.py / mechanical.py / cosmic_new.py / hybrid.py
    legacy_v1_screens.py / legacy_v2_screens.py / legacy_v2b_screens.py
```

---

*For practical patterns, read `attractors.py` (density accumulator),
`spectacular.py` (full-field math), `ascii_fields.py` (simpler per-pixel fields),
and `emergent_v2.py` (emergent system integration).*
