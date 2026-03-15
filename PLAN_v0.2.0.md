# Hermes Neurovision v0.2.0 — Complete System Plan

**Date:** 2026-03-15
**Goal:** Full foundation build-out before mass screen creation. Integrate hermes-agent v0.2.0 data, add new visual effects, new emergent primitives, post-processing pipeline, reactive element system (12 visual categories for forced diversity), sound system (stdlib + macOS), harden backward compat, update export/import format.

**Philosophy:** We are designing ATOMS, not molecules. Build the primitive toolkit so that AI agents composing screens have maximum creative vocabulary. Emergent visuals on emergent AI behavior.

---

## Table of Contents

1. Architecture Overview
2. Tier 1 — Hook Expansion + Bridge + Overlay + Export Format
3. Tier 2 — State DB Expansion
4. Tier 3 — New Source Modules
5. New Visual Effects (4 new trigger effects)
6. Reactive Primitives (palette shift, overlays, specials, zones, intensity curves, ambient)
7. Reactive Element System (12 visual categories, forced diversity)
8. Sound System (stdlib + macOS)
9. Post-Processing Pipeline (warp, void, echo, glow, mask, force, decay, symmetry, parallax)
10. Emergent Primitives (CA, physarum, neural field, waves, boids, reaction-diffusion)
11. Buffer-Based Rendering Pipeline
12. TuneSettings Additions
13. ThemePlugin API Additions
14. Backward Compatibility Guarantees
15. Performance Budget
16. Files Changed
17. Implementation Phases
18. What We Are NOT Doing

---

## 1. Architecture Overview

```
                    HERMES-AGENT v0.2.0
                    ────────────────────
  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
  │ state.db    │  │ events.jsonl │  │ audit.jsonl  │
  │ (SQLite)    │  │ (hook)      │  │ (aegis)      │
  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
         │               │               │
  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
  │ StateDb     │  │ Custom      │  │ Aegis       │
  │ Source      │  │ Source      │  │ Source      │
  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
         │               │               │
  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
  │ Memories    │  │ Cron        │  │ Docker      │
  │ Source      │  │ Source      │  │ Source      │
  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
         │               │               │
  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
  │ MCP Source  │  │ Skills      │  │ Checkpoints │
  │ (NEW)       │  │ Source (NEW)│  │ Source (NEW)│
  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
         │               │               │
  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
  │ Providers   │  │ Context     │  │ Sessions    │
  │ Source (NEW)│  │ Source (NEW)│  │ Source (NEW)│
  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
         │               │               │
         └───────────┬───┴───────────────┘
                     │
              ┌──────┴──────┐
              │ EventPoller │
              └──────┬──────┘
                     │
              ┌──────┴──────────────────────────┐
              │            Bridge                │
              │  event kind → VisualTrigger      │
              │  event kind → SpecialEffect      │
              │  event kind → ReactiveElement    │
              │  event kind → SoundCue           │
              └──────┬──────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
  ┌──────┴──────┐ ┌──┴───────┐ ┌┴────────────┐
  │ ThemeState  │ │ Reactive │ │ SoundEngine │
  │ apply()    │ │ Renderer │ │ (stdlib +   │
  │ step()     │ │ 12 types │ │  macOS)     │
  └──────┬──────┘ └──┬───────┘ └─────────────┘
         │           │
         └─────┬─────┘
               │
          ┌────┴─────────────────┐
          │   RENDER PIPELINE    │
          ├─────────────────────┤
          │ 1. Write to buffer  │
          │    stars, bg, edges │
          │    pulses, nodes    │
          │    packets, particles│
          │    streaks, extras  │
          │    specials, overlays│
          │ 2. Post-processing  │
          │    warp, symmetry   │
          │    glow, void, echo │
          │    decay, automaton │
          │    mask             │
          │ 3. Buffer → screen  │
          │ 4. HUD overlays    │
          └─────────────────────┘
```

---

## 2. Tier 1 — Hook Expansion + Bridge + Overlay + Export

### 2A. Expand HOOK.yaml

```yaml
events:
  # Existing
  - agent:start
  - agent:step
  - agent:end
  - session:start
  - session:reset
  - command:*
  # NEW — v0.2.0 events
  - tool:start
  - tool:end
  - tool:error
  - compression:start
  - compression:end
  - checkpoint:create
  - checkpoint:rollback
  - mcp:connect
  - mcp:disconnect
  - mcp:tool_call
  - provider:fallback
  - provider:error
  - subagent:start
  - subagent:end
```

### 2B. Expand custom.py EVENT_MAP

```python
# NEW entries
"tool:start":           ("agent",      "tool_call"),
"tool:end":             ("agent",      "tool_complete"),
"tool:error":           ("agent",      "tool_error"),
"compression:start":    ("agent",      "compression_started"),
"compression:end":      ("agent",      "compression_ended"),
"checkpoint:create":    ("agent",      "checkpoint_created"),
"checkpoint:rollback":  ("agent",      "checkpoint_rollback"),
"mcp:connect":          ("mcp",        "mcp_connected"),
"mcp:disconnect":       ("mcp",        "mcp_disconnected"),
"mcp:tool_call":        ("mcp",        "mcp_tool_call"),
"provider:fallback":    ("provider",   "provider_fallback"),
"provider:error":       ("provider",   "provider_error"),
"subagent:start":       ("agent",      "subagent_started"),
"subagent:end":         ("agent",      "subagent_ended"),
```

### 2C. Expand bridge.py _MAPPING

```python
# NEW event kind → (effect, intensity, color_key, target)
"tool_error":           ("flash",       0.7, "warning",  "random_node"),
"compression_started":  ("pulse",       0.6, "accent",   "center"),
"compression_ended":    ("ripple",      0.5, "soft",     "center"),
"checkpoint_created":   ("spawn_node",  0.7, "bright",   "new"),
"checkpoint_rollback":  ("flash",       0.9, "warning",  "all"),
"mcp_connected":        ("wake",        0.7, "accent",   "all"),
"mcp_disconnected":     ("flash",       0.6, "warning",  "all"),
"mcp_tool_call":        ("packet",      0.6, "accent",   "random_edge"),
"provider_fallback":    ("cascade",     0.8, "warning",  "all"),
"provider_error":       ("burst",       0.8, "warning",  "center"),
"subagent_started":     ("spawn_node",  0.9, "bright",   "new"),
"subagent_ended":       ("converge",    0.7, "bright",   "center"),
```

### 2D. Expand log_overlay.py

New format strings for all new event kinds + new SOURCE_COLORS:
```python
"mcp": "green",
"provider": "yellow",
```

### 2E. Export format bump to v1.1

```python
export_data = {
    "format_version": "1.1",
    "metadata": {
        "name": ...,
        "title": ...,
        "author": ...,
        "description": ...,
        "created": ...,
        "hermes_neurovision_version": "0.2.0",
        "hermes_agent_version": "0.2.0",     # NEW
        "min_api_version": "1.0",              # NEW
    },
    "config": { ... },
    "plugin": { ... },
}
```

Update import_theme.py to handle 1.0 → 1.1 gracefully (defaults for missing fields).

---

## 3. Tier 2 — State DB Expansion

### 3A. New column queries with graceful fallback

Try new v0.2.0 columns (provider, platform, reasoning_effort, compression_count), fall back to v0.1.x schema on OperationalError.

### 3B. New events from state_db

- `provider_active` — when provider column detected
- `platform_detected` — when platform column detected
- `compression_event` — when compression_count increases
- `reasoning_change` — when reasoning_effort changes
- Enhanced `message_added` with duration_ms and tokens if available

### 3C. Session Lineage Data (NEW)

Query session parent_id and name fields for family tree visualization:
```python
# Session lineage: parent-child relationships
"SELECT id, name, parent_id, created_at FROM sessions WHERE parent_id IS NOT NULL"
```
Emits: `session_lineage` events with tree structure data. Enables session family tree visualization in themes.

### 3D. Context Pressure Metrics (NEW)

Track before/after token counts on compression events:
```python
# Context pressure: token count over time
"SELECT tokens_before, tokens_after, timestamp FROM compressions ORDER BY timestamp DESC LIMIT 10"
```
Emits: `context_pressure` events with value 0.0-1.0 (% of context window filled). Feeds GAUGE reactive elements.

---

## 4. Tier 3 — New Source Modules

### 4A. sources/mcp.py — MCP Connection State
Watch for MCP state files, emit mcp_server_active, mcp_tool_count_changed.

### 4B. sources/skills.py — Skill Activity
Watch ~/.hermes/skills/ for file changes, emit skill_loaded, skill_created, skill_updated.

### 4C. sources/checkpoints.py — Filesystem Checkpoints
Watch for checkpoint creation/rollback markers.

### 4D. sources/providers.py — Provider Health Monitoring (NEW)
Poll hermes-agent provider state. Emit `provider_health` (up/down per provider), `provider_fallback` (fallback chain triggered). Feeds CONSTELLATION reactive elements — healthy providers glow green, erroring ones flash red.

### 4E. sources/context.py — Context Pressure Metrics (NEW)
Monitor context window usage. Emit `context_pressure` (% filled), `token_usage` (absolute count), `cost_update` (running cost estimate). Feeds GAUGE reactive elements.

### 4F. sources/sessions.py — Session Lineage (NEW)
Watch for session creation/resume. Emit `session_lineage` (parent-child tree data), `session_resume`. Enables session family tree visualization.

### 4G. Source Enable/Disable

Config in ~/.hermes/neurovision/config.json:
```json
{ "sources": { "state_db": true, "mcp": true, "skills": true, ... } }
```
CLI flags: `--enable-source`, `--disable-source`, `--list-sources`.

---

## 5. New Visual Effects (4 new trigger effects)

Total: 8 existing + 4 new = 12 effects.

### 5A. `ripple` — Multi-ring concentric pulse
Spawns 3 staggered concentric rings. "Dropped in water" feel.
Semantic: compression, context shift, state transitions.

### 5B. `cascade` — Sequential node chain flash
Flashes nodes one-by-one in domino sequence.
Semantic: fallback chains, error propagation, sequential failures.

### 5C. `converge` — Particles pull inward
Spawns particles at random positions accelerating toward a target node.
Semantic: subagent completion, results returning, aggregation.

### 5D. `streak` — Fast line sweep
Bright horizontal or vertical line that sweeps across the screen.
Semantic: fast data transfer, MCP calls, high-throughput events.

---

## 6. Reactive Primitives

### 6A. Palette Shifts (opt-in per theme)

```python
def palette_shift(self, trigger_effect: str, intensity: float,
                  base_palette: Tuple[int,int,int,int]
                  ) -> Optional[Tuple[int,int,int,int]]:
    """Return shifted palette or None. ONLY called if overridden."""
    return None
```

Temporary shift (~1s) tracked by `_palette_shift_until` in ThemeState. Default returns None — zero impact on existing themes.

### 6B. Overlay Effects

```python
def draw_overlay_effect(self, stdscr, state, color_pairs: dict,
                        trigger_effect: str, intensity: float,
                        progress: float) -> None:
    """Screen-wide cosmetic overlay triggered by events. Default: no-op."""
    pass
```

Tracked as OverlayEffect dataclass list in ThemeState.

### 6C. Special Effects — 3 Per Screen

```python
@dataclass
class SpecialEffect:
    name: str
    trigger_kinds: List[str]
    min_intensity: float = 0.0
    cooldown: float = 5.0
    duration: float = 2.0

def special_effects(self) -> List[SpecialEffect]:
    """Declare up to 3 special effects. Default: []."""
    return []

def draw_special(self, stdscr, state, color_pairs: dict,
                 special_name: str, progress: float,
                 intensity: float) -> None:
    """Render named special. Called every frame while active. Default: no-op."""
    pass
```

Processing: Bridge checks plugin.special_effects() on each event. If event.kind matches trigger_kinds and cooldown elapsed, activate. ThemeState tracks active_specials list.

### 6D. Effect Zones (named screen regions)

```python
def effect_zones(self) -> Dict[str, Tuple[float, float, float, float]]:
    """Named zones as (x%, y%, w%, h%) normalized 0-1.
    Used by specials and regional effects. Default: {}."""
    return {}
```

### 6E. Intensity Curves

```python
def intensity_curve(self, raw: float) -> float:
    """Transform raw intensity. Default: linear (return raw).
    Override for exponential, logarithmic, step-function response."""
    return raw
```

### 6F. Ambient Tick

```python
def ambient_tick(self, stdscr, state, color_pairs: dict,
                 idle_seconds: float) -> None:
    """Called each frame when idle. For idle animations. Default: no-op."""
    pass
```

---


---

## 7. Reactive Element System

The core innovation for visual diversity. Instead of themes manually mapping events to generic particles, we define 12 DISTINCT visual treatment categories. Each data point type maps to a specific visual category with unique physics/motion. A minimum-effort theme automatically gets 12 different visual behaviors.

### 7A. ReactiveElement Enum

```python
class ReactiveElement(Enum):
    """12 visual treatment categories. Each has distinct motion physics."""
    PULSE = "pulse"           # radial burst from center, one-shot, dramatic
    RIPPLE = "ripple"         # concentric rings from a point, one-shot
    STREAM = "stream"         # flowing particles in a direction, sustained
    BLOOM = "bloom"           # organic growth, expands and holds, then fades
    SHATTER = "shatter"       # explosion of fragments, pieces scatter and fade
    ORBIT = "orbit"           # persistent rotating elements, stays while alive
    GAUGE = "gauge"           # fills/drains a bar or arc, changes color at thresholds
    SPARK = "spark"           # bright flash + lingering afterglow, demands attention
    WAVE = "wave"             # horizontal sweep across screen, transformative
    GLYPH = "glyph"          # symbol/sigil that appears and persists, slowly morphing
    TRAIL = "trail"           # path/line tracing movement across screen
    CONSTELLATION = "constellation"  # dots that connect/disconnect with lines, persistent
```

### 7B. Reaction Dataclass

```python
@dataclass
class Reaction:
    """A themed response to a data event."""
    element: ReactiveElement
    intensity: float          # 0.0-1.0, how dramatic
    origin: Tuple[float, float]  # where on screen (0-1 normalized)
    color_key: str            # key into theme palette
    duration: float           # seconds
    data: Dict[str, Any]      # element-specific params (particle_char, spread, etc.)
    sound: Optional[str]      # sound cue name, if any
```

### 7C. REACTIVE_MAP — Default Event-to-Element Mapping

Lives in ThemePlugin base class. Themes can override individual mappings.

```python
REACTIVE_MAP: Dict[str, ReactiveElement] = {
    # ── Agent lifecycle → PULSE (dramatic, one-shot) ──
    "agent_start":        ReactiveElement.PULSE,
    "agent_end":          ReactiveElement.PULSE,
    "session_resume":     ReactiveElement.PULSE,

    # ── Tool activity → RIPPLE (concentric rings) ──
    "tool_call":          ReactiveElement.RIPPLE,
    "tool_complete":      ReactiveElement.RIPPLE,
    "tool_error":         ReactiveElement.RIPPLE,   # with warning color
    "mcp_tool_call":      ReactiveElement.RIPPLE,

    # ── LLM generation → STREAM (flowing particles) ──
    "llm_start":          ReactiveElement.STREAM,
    "llm_chunk":          ReactiveElement.STREAM,
    "llm_end":            ReactiveElement.STREAM,

    # ── Knowledge creation → BLOOM (organic growth) ──
    "memory_save":        ReactiveElement.BLOOM,
    "skill_create":       ReactiveElement.BLOOM,
    "checkpoint_created": ReactiveElement.BLOOM,

    # ── Errors & security → SHATTER (explosion) ──
    "error":              ReactiveElement.SHATTER,
    "crash":              ReactiveElement.SHATTER,
    "threat_blocked":     ReactiveElement.SHATTER,

    # ── Persistent processes → ORBIT (rotating) ──
    "cron_tick":          ReactiveElement.ORBIT,
    "background_proc":    ReactiveElement.ORBIT,
    "subagent_started":   ReactiveElement.ORBIT,

    # ── Metrics → GAUGE (fill/drain) ──
    "context_pressure":   ReactiveElement.GAUGE,
    "token_usage":        ReactiveElement.GAUGE,
    "cost_update":        ReactiveElement.GAUGE,

    # ── Attention-demanding → SPARK (flash + afterglow) ──
    "approval_request":   ReactiveElement.SPARK,
    "dangerous_cmd":      ReactiveElement.SPARK,

    # ── Transformative events → WAVE (horizontal sweep) ──
    "compression_started": ReactiveElement.WAVE,
    "compression_ended":  ReactiveElement.WAVE,
    "checkpoint_rollback": ReactiveElement.WAVE,

    # ── State indicators → GLYPH (persistent symbol) ──
    "personality_change": ReactiveElement.GLYPH,
    "reasoning_change":   ReactiveElement.GLYPH,

    # ── Movement/navigation → TRAIL (path trace) ──
    "browser_navigate":   ReactiveElement.TRAIL,
    "file_edit":          ReactiveElement.TRAIL,
    "git_commit":         ReactiveElement.TRAIL,

    # ── Connections → CONSTELLATION (connected dots) ──
    "mcp_connected":      ReactiveElement.CONSTELLATION,
    "mcp_disconnected":   ReactiveElement.CONSTELLATION,
    "provider_health":    ReactiveElement.CONSTELLATION,
    "provider_fallback":  ReactiveElement.CONSTELLATION,
    "platform_connect":   ReactiveElement.CONSTELLATION,
}
```

### 7D. ReactiveRenderer — Physics Engine for Each Element

Lives in renderer.py or reactive.py. Handles MOTION — themes provide AESTHETICS.

```python
class ReactiveRenderer:
    """Built-in physics for 12 reactive element types."""

    def render_pulse(self, reaction, buffer, t):
        """Expanding ring of particles from origin. Fast out, fade."""
        radius = t * reaction.data.get("spread_speed", 10)
        char = reaction.data.get("particle_char", "*")
        # Draw ring at radius from origin, fading with distance

    def render_ripple(self, reaction, buffer, t):
        """Multiple expanding rings with staggered delay."""
        for i in range(3):
            ring_t = t - i * 0.3
            if ring_t > 0:
                # Draw ring at ring_t * 8 radius

    def render_stream(self, reaction, buffer, t):
        """Flowing particles in a direction while sustained."""
        direction = reaction.data.get("direction", "down")
        # Spawn particles at origin, move in direction

    def render_bloom(self, reaction, buffer, t):
        """Organic growth: expand outward, hold, then fade."""
        phase = "grow" if t < 0.5 else "hold" if t < 0.8 else "fade"
        # Grow: cells appear outward from origin
        # Hold: all cells visible, gently pulsing
        # Fade: cells disappear from edges inward

    def render_shatter(self, reaction, buffer, t):
        """Fragment explosion: pieces fly outward with physics."""
        n_fragments = reaction.data.get("fragments", 15)
        # Each fragment: random angle, speed, deceleration, character

    def render_orbit(self, reaction, buffer, t):
        """Rotating element(s) around a center. Persistent."""
        n_orbiters = reaction.data.get("count", 3)
        radius = reaction.data.get("orbit_radius", 5)
        # Circular motion, staggered phase

    def render_gauge(self, reaction, buffer, t):
        """Horizontal bar that fills/drains. Color changes at thresholds."""
        value = reaction.data.get("value", 0.5)
        width = reaction.data.get("width", 20)
        # [████████░░░░░░░░░░░░] 42%
        # Green < 50%, yellow < 80%, red >= 80%

    def render_spark(self, reaction, buffer, t):
        """Bright flash then lingering afterglow."""
        if t < 0.1:  # Flash phase
            pass  # Full brightness, large area
        else:  # Afterglow phase
            pass  # Shrinking, dimming point of light

    def render_wave(self, reaction, buffer, t):
        """Horizontal line sweeping left-to-right across screen."""
        x_pos = int(t * buffer.w)
        # Draw vertical line at x_pos, with trail behind

    def render_glyph(self, reaction, buffer, t):
        """Persistent symbol that slowly morphs character set."""
        glyphs = reaction.data.get("sequence", "◆◇○●◎")
        idx = int(t * 2) % len(glyphs)
        # Draw glyph at fixed position, cycling through sequence

    def render_trail(self, reaction, buffer, t):
        """Path trace with fading tail."""
        points = reaction.data.get("path", [])
        tail_length = reaction.data.get("tail", 8)
        # Draw path up to current progress, older segments fade

    def render_constellation(self, reaction, buffer, t):
        """Connected dots with lines. Dots appear/disappear."""
        nodes = reaction.data.get("nodes", [])
        # Draw nodes as bright points
        # Draw lines between connected nodes using ─│┌┐└┘
        # Pulse lines when connection is active
```

### 7E. Theme Override Pattern

Themes override render_* methods to customize AESTHETICS while core handles PHYSICS:

```python
class VolcanoTheme(ThemePlugin):
    def render_pulse(self, kind, data):
        # Magma eruption from volcano peak
        return Reaction(ReactiveElement.PULSE, 0.9, (0.5, 0.2),
            "lava", 2.0, {"particle_char": "▓", "spread": "radial"}, "rumble")

    def render_stream(self, kind, data):
        # Lava flowing down sides
        return Reaction(ReactiveElement.STREAM, 0.5, (0.5, 0.3),
            "lava_flow", 0, {"direction": "down", "particle_char": "░"})

    def render_shatter(self, kind, data):
        # Volcanic rocks everywhere
        return Reaction(ReactiveElement.SHATTER, 1.0, (0.5, 0.5),
            "obsidian", 1.5, {"fragments": 20, "particle_char": "●"}, "explosion")

    def render_constellation(self, kind, data):
        # Underground magma veins
        return Reaction(ReactiveElement.CONSTELLATION, 0.3, (0.5, 0.8),
            "magma_vein", 0, {"line_char": "─", "node_char": "◆"})

# Meanwhile ForestTheme renders the SAME data completely differently:
#   PULSE → wind gust rustling trees
#   STREAM → falling leaves
#   SHATTER → lightning splitting a tree
#   BLOOM → mushroom growing from forest floor
#   CONSTELLATION → root network connecting trees underground
```

**Key guarantee:** A theme that implements ZERO render_* methods still gets 12 distinct visual behaviors from the base class defaults. Visual diversity is ARCHITECTURAL, not optional.

---

## 8. Sound System

Promoted from v0.3.0 roadmap. Pure stdlib core, macOS features optional. Zero external dependencies.

### 8A. SoundCue Dataclass

```python
@dataclass
class SoundCue:
    """A sound that can be triggered by events."""
    name: str
    type: str        # "bell", "flash", "say", "file"
    value: str       # text for say, path for file, pattern for tone
    volume: float    # 0.0-1.0
    priority: int    # higher = override lower sounds
```

### 8B. SoundEngine Class

```python
class SoundEngine:
    """Manages sound output. Pure stdlib + optional macOS."""

    def __init__(self, enabled: bool = True, volume: float = 0.5):
        self._enabled = enabled
        self._is_macos = sys.platform == "darwin"
        self._last_played: Dict[str, float] = {}  # cooldowns
        self._volume = volume

    def play(self, cue: SoundCue) -> None:
        if not self._enabled:
            return
        # Cooldown check (don't spam sounds)
        now = time.time()
        if now - self._last_played.get(cue.name, 0) < 0.5:
            return
        self._last_played[cue.name] = now

        if cue.type == "bell":
            curses.beep()
        elif cue.type == "flash":
            curses.flash()
        elif cue.type == "say" and self._is_macos:
            subprocess.Popen(
                ["say", "-v", "Whisper", cue.value],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        elif cue.type == "file" and self._is_macos:
            subprocess.Popen(
                ["afplay", "-v", str(cue.volume * self._volume), cue.value],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
```

### 8C. Available Sound Primitives

**Tier 1 — Zero deps (works everywhere):**
- `curses.beep()` — terminal bell
- `curses.flash()` — visual flash (inverts screen briefly)
- `sys.stdout.write('\a')` — raw BEL character

**Tier 2 — macOS native (detected via sys.platform == 'darwin'):**
- `afplay file.mp3` — play any audio file (non-blocking with Popen)
- `say "text"` — text-to-speech
- `say -v Whisper "text"` — specific voice
- `osascript -e 'beep'` — system beep
- All fire-and-forget via `subprocess.Popen(start_new_session=True)`

**Tier 3 — Generated audio (optional, heavyweight):**
- HeartMuLa — AI music generation for theme-specific loops
- hermes-agent text_to_speech tool — generates MP3s
- Pre-bundled sound files in `~/.hermes/neurovision/sounds/`

### 8D. Plugin Hook

```python
def sound_cues(self) -> Dict[str, SoundCue]:
    """Map event kinds to sounds. Default: {} (silent).
    Example:
        {"agent_start": SoundCue("wake", "say", "online", 0.5, 1),
         "threat_blocked": SoundCue("alert", "bell", "", 1.0, 10)}
    """
    return {}
```

### 8E. CLI & Config

```
CLI flags:
  --sound / --no-sound      Enable/disable sound
  --volume 0.5              Set volume (0.0-1.0)
  --sound-test              Play all configured sounds and exit

Config (~/.hermes/neurovision/config.json):
  "sound": {
      "enabled": true,
      "volume": 0.5,
      "use_tts": true,
      "custom_sounds_dir": "~/.hermes/neurovision/sounds/"
  }
```

### 8F. New File: sound.py

Contains SoundCue, SoundEngine, DEFAULT_CUES dict.
~80 lines. Zero external dependencies.

---

## 9. Post-Processing Pipeline

ALL post-processing operates on a buffer (2D array of char+color+attr), applied AFTER all layers render, BEFORE copying to screen. ALL are opt-in with defaults that disable them. ALL have TuneSettings sliders.

### P1. Warp Field (displacement mapping)

```python
def warp_field(self, x: int, y: int, w: int, h: int,
               frame: int, intensity: float) -> Tuple[int, int]:
    """Given output position, return source position. Default: identity."""
    return (x, y)
```

Enables: gravity lens, ripple, vortex, heat shimmer, earthquake.
Cost: ~3-5ms.

### P2. Void / Erosion (negative space)

```python
def void_points(self, w: int, h: int, frame: int,
                intensity: float) -> List[Tuple[int, int, str]]:
    """Cells to ERASE after rendering. (x, y, border_char). Default: []."""
    return []
```

Enables: error holes, corruption spread, portals, cracks.
Cost: ~0.5ms.

### P3. Afterimage / Echo (temporal bleed)

```python
def echo_decay(self) -> int:
    """Frames that old content persists as afterimage. Default: 0 (off)."""
    return 0
```

Ring buffer of N previous frames. Empty cells show dimmed content from previous frames.
Enables: motion blur, persistence of vision, ghost nodes.
Cost: ~1-2ms.

### P4. Force Field (character physics)

```python
def force_points(self, w: int, h: int, frame: int,
                 intensity: float) -> List[Tuple[float, float, float, str]]:
    """(x, y, strength, type). strength>0=attract, <0=repel.
    type: 'radial' or 'vortex'. Applied to stars/particles. Default: []."""
    return []
```

Enables: gravity wells, repulsors, vortex spirals, explosion shockwaves.
Cost: ~0.5ms.

### P5. Character Decay / Entropy

```python
def decay_sequence(self) -> Optional[str]:
    """Char decay from 'full' to 'empty'. Default: None (off).
    Example: '█▓▒░·. ' — characters age through this sequence."""
    return None
```

Each cell tracks age. New writes reset age.
Enables: screen rot, healing, fading text, organic growth, rust.
Cost: ~1ms.

### P6. Symmetry Operations

```python
def symmetry(self) -> Optional[str]:
    """'mirror_x', 'mirror_y', 'mirror_xy', 'rotate_4'. Default: None."""
    return None
```

Post-processing buffer transform.
Enables: kaleidoscope, Rorschach, mandala, water reflection.
Cost: ~1ms.

### P7. Depth / Parallax

```python
def depth_layers(self) -> int:
    """Parallax depth layers. 1=flat (default). Stars drift at 1/layer speed."""
    return 1
```

Stars distributed across layers, deeper = dimmer + slower.
Cost: ~0ms (modifies existing drift calc).

### P8. Color Glow / Bleed

```python
def glow_radius(self) -> int:
    """Radius for color propagation. 0=off (default). 1-3 = subtle to strong."""
    return 0
```

Bright cells bleed color to empty neighbors as DIM.
Enables: neon glow, bioluminescence, heat radiation, node auras.
Cost: ~2-4ms.

### P9. Render Mask / Stencil

```python
def render_mask(self, w: int, h: int, frame: int,
                intensity: float) -> Optional[List[List[bool]]]:
    """Boolean grid. True=visible, False=hidden. Default: None (all visible)."""
    return None
```

Enables: iris aperture, spotlight, curtain reveal, shaped windows.
Cost: ~1ms.

---

## 10. Emergent Primitives

These are self-contained simulation systems that themes can opt into. They run as layers that compose with the existing rendering. Each has an `inject()` or similar method for events to seed/stimulate the system.

### E1. Cellular Automaton Layer

Multiple rule sets available as presets:

```python
def automaton_config(self) -> Optional[Dict]:
    """Return CA config or None to disable. Default: None.
    Supported rules: 'game_of_life', 'brians_brain', 'cyclic',
    'wireworld', 'rule110'.
    Config: {'rule': 'brians_brain', 'density': 0.08, 'update_interval': 2}
    """
    return None
```

**Brian's Brain:** 3-state (off/on/dying). Never-settling chaotic sparking. Perfect for neural activity aesthetic. ~40 lines.

**Cyclic CA:** N states cycling in order. Self-organizing spiral waves. Hypnotic, organic. ~35 lines.

**Rule 110:** 1D Turing-complete CA scrolling vertically. Fractal triangle patterns. ~20 lines.

Events inject cells at activity points → patterns propagate outward.

### E2. Physarum Slime Mold Simulation

```python
def physarum_config(self) -> Optional[Dict]:
    """Return physarum config or None. Default: None.
    Config: {'n_agents': 150, 'sensor_dist': 4.0, 'sensor_angle': pi/4,
             'deposit': 1.0, 'decay': 0.95}
    """
    return None
```

Agents follow and deposit chemical trails. Creates ORGANIC NETWORK STRUCTURES — veins, highways, branching paths connecting food sources. Events place "food" → agents self-organize paths to it.

THIS IS THE KILLER METAPHOR: slime mold networks connecting points of AI agent activity = visual representation of information flow. The network grows and adapts as the agent works.

~80 lines. 150 agents + diffusion grid at 20 FPS.

### E3. Neural Activation Field

```python
def neural_field_config(self) -> Optional[Dict]:
    """Return neural field config or None. Default: None.
    Config: {'threshold': 2, 'fire_duration': 2, 'refractory': 5}
    """
    return None
```

Excitable medium with activation threshold and refractory period. Creates cascading waves of neural firing. Events literally "fire neurons" that cascade across the display.

PERFECT METAPHOR: Agent decisions create neural activation cascades that propagate visually, exactly mirroring how the AI processes information.

~50 lines.

### E4. Wave Propagation / Interference

```python
def wave_config(self) -> Optional[Dict]:
    """Return wave config or None. Default: None.
    Config: {'speed': 0.3, 'damping': 0.98}
    """
    return None
```

2D wave equation. Events "drop" disturbances → ripples expand → overlapping ripples create interference patterns. Multiple concurrent events = complex standing waves.

~40 lines. Guaranteed 20+ FPS.

### E5. Boids Flocking

```python
def boids_config(self) -> Optional[Dict]:
    """Return boids config or None. Default: None.
    Config: {'n_boids': 40, 'sep_dist': 3.0, 'align_dist': 8.0,
             'cohesion_dist': 12.0, 'max_speed': 1.5}
    """
    return None
```

Classic separation/alignment/cohesion. Events create temporary attractors/repulsors. Directional characters (> < ^ v / \) show movement. Flocks form, split, reform.

~60 lines.

### E6. Reaction-Diffusion (Gray-Scott)

```python
def reaction_diffusion_config(self) -> Optional[Dict]:
    """Return RD config or None. Default: None.
    Config: {'feed': 0.055, 'kill': 0.062, 'update_interval': 2}
    Needs optimization: runs on half-res grid (60x20), updates every other frame.
    """
    return None
```

Two-chemical system creating Turing patterns: spots, stripes, maze-like structures, mitosis-like splitting. THE most visually stunning emergent system. Events add chemical to seed new pattern growth.

~80 lines. Needs subsampled grid (60×20 internal → 120×40 display) for 20 FPS. Update every 2nd frame.

### Emergent Event Integration

The Bridge gets a new method:
```python
def inject_emergent(self, state: ThemeState, event: VisionEvent) -> None:
    """Inject event into active emergent systems."""
    x = random.randint(5, state.width - 5)
    y = random.randint(2, state.height - 3)
    if state.automaton:
        state.automaton.inject(x, y)
    if state.physarum:
        state.physarum.add_food(x, y)
    if state.neural_field:
        state.neural_field.fire(x, y)
    if state.wave_field:
        state.wave_field.drop(x, y)
    if state.boids:
        state.boids.add_attractor(x, y)
    if state.reaction_diffusion:
        state.reaction_diffusion.add_chemical(x, y)
```

### Compositing

Emergent systems render to the buffer BEFORE post-processing:
- CA/neural/waves/RD: full-screen background layer (like draw_background)
- Physarum: trail network as mid-layer
- Boids: individual agent chars as foreground overlay

Themes choose their composition order via a new plugin method:
```python
def emergent_layer(self) -> str:
    """Where to render emergent systems: 'background', 'midground', 'foreground'.
    Default: 'background'. Controls z-order relative to nodes/edges."""
    return "background"
```

---

## 11. Buffer-Based Rendering Pipeline

### Prerequisite: FrameBuffer class

```python
@dataclass
class Cell:
    char: str = " "
    color_pair: int = 0
    attr: int = 0
    age: int = 0  # for decay

class FrameBuffer:
    def __init__(self, w: int, h: int):
        self.w = w
        self.h = h
        self.cells = [[Cell() for _ in range(w)] for _ in range(h)]

    def put(self, x: int, y: int, char: str, color_pair: int, attr: int = 0) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            cell = self.cells[y][x]
            cell.char = char
            cell.color_pair = color_pair
            cell.attr = attr
            cell.age = 0  # reset age on write

    def get(self, x: int, y: int) -> Cell:
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.cells[y][x]
        return Cell()

    def blit_to_screen(self, stdscr) -> None:
        for y in range(self.h):
            for x in range(self.w):
                cell = self.cells[y][x]
                if cell.char != " " or cell.attr != 0:
                    try:
                        stdscr.addstr(y, x, cell.char, cell.color_pair | cell.attr)
                    except curses.error:
                        pass
```

### Full Render Order

```
Frame N:
  1.  Clear buffer
  2.  Emergent background (CA/neural/waves/RD if layer="background")
  3.  Stars (with force_field displacement + parallax depth)
  4.  plugin.draw_background()
  5.  Emergent midground (physarum trails if layer="midground")
  6.  Edges
  7.  Pulses (ring, ripple, rays, etc.)
  8.  Nodes
  9.  Packets
  10. Particles (with force_field displacement)
  11. Streaks
  12. plugin.draw_extras()
  13. Emergent foreground (boids if layer="foreground")
  14. Active specials → plugin.draw_special()
  15. Overlay effects → plugin.draw_overlay_effect()
  16. ── POST-PROCESSING ──
  17. Apply warp_field (displacement)
  18. Apply symmetry (mirror/rotate)
  19. Apply glow (color bleed)
  20. Apply void_points (erosion)
  21. Apply echo (afterimage from ring buffer)
  22. Apply decay (age characters)
  23. Apply render_mask (stencil)
  24. ── OUTPUT ──
  25. Buffer → screen (blit_to_screen)
  26. HUD overlays (logs, debug, tune — ALWAYS on top, not buffered)
  27. curses.refresh()
  28. Save buffer to echo ring buffer
```

---

## 12. TuneSettings Additions

```python
@dataclass
class TuneSettings:
    # Existing
    burst_scale: float = 1.0
    packet_rate_mult: float = 1.0
    pulse_rate_mult: float = 1.0
    particle_density: float = 1.0
    event_sensitivity: float = 1.0
    animation_speed: float = 1.0
    show_packets: bool = True
    show_particles: bool = True
    show_pulses: bool = True
    show_stars: bool = True
    show_background: bool = True
    show_nodes: bool = True
    show_flash: bool = True
    show_spawn_node: bool = True

    # NEW — visual effects
    show_streaks: bool = True
    show_specials: bool = True
    show_overlays: bool = True
    color_shifts: bool = True

    # NEW — post-processing
    warp_strength: float = 1.0       # 0 = disabled
    void_intensity: float = 1.0      # 0 = disabled
    echo_frames: int = 0             # 0 = disabled
    glow_radius: int = 0             # 0 = disabled
    mask_enabled: bool = True
    force_strength: float = 1.0      # 0 = disabled
    decay_rate: float = 1.0          # 0 = disabled
    parallax_depth: int = 1          # 1 = flat (disabled)
    symmetry_enabled: bool = True

    # NEW — emergent systems
    emergent_speed: float = 1.0      # 0 = paused, 2.0 = double speed
    emergent_opacity: float = 1.0    # 0 = invisible, 1.0 = full

    # NEW — reactive element system
    reactive_elements: bool = True   # master toggle for reactive elements

    # NEW — sound system
    sound_enabled: bool = True       # master toggle for sound
    sound_volume: float = 0.5        # 0.0-1.0
```

---

## 13. ThemePlugin API Additions

Summary of ALL new plugin methods (all with safe defaults):

```python
class ThemePlugin:
    # ── EXISTING (frozen, never change signatures) ──
    # build_nodes, edge_keep_count, build_edges_extra
    # step_star, step_star_post
    # spawn_particle, particle_base_chance, particle_life_range
    # step_nodes
    # pulse_params, pulse_style
    # packet_budget
    # star_glyph, node_glyph, node_color_key, edge_glyph, edge_color_key
    # packet_color_key, particle_color_key, pulse_color_key
    # node_position_adjust
    # draw_background, draw_extras

    # ── NEW: Reactive Primitives ──
    def palette_shift(self, trigger_effect, intensity, base_palette): return None
    def draw_overlay_effect(self, stdscr, state, color_pairs, trigger_effect, intensity, progress): pass
    def special_effects(self): return []
    def draw_special(self, stdscr, state, color_pairs, special_name, progress, intensity): pass
    def effect_zones(self): return {}
    def intensity_curve(self, raw): return raw
    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds): pass

    # ── NEW: Post-Processing ──
    def warp_field(self, x, y, w, h, frame, intensity): return (x, y)
    def void_points(self, w, h, frame, intensity): return []
    def echo_decay(self): return 0
    def force_points(self, w, h, frame, intensity): return []
    def decay_sequence(self): return None
    def symmetry(self): return None
    def depth_layers(self): return 1
    def glow_radius(self): return 0
    def render_mask(self, w, h, frame, intensity): return None

    # ── NEW: Emergent Systems ──
    def automaton_config(self): return None
    def physarum_config(self): return None
    def neural_field_config(self): return None
    def wave_config(self): return None
    def boids_config(self): return None
    def reaction_diffusion_config(self): return None
    def emergent_layer(self): return "background"

    # ── NEW: Visual Effect Hooks ──
    def streak_color_key(self): return "accent"

    # ── NEW: Reactive Element System ──
    REACTIVE_MAP: Dict[str, ReactiveElement] = { ... }  # see Section 7C
    def react(self, event_kind, data): ...  # dispatch to render_* methods
    def render_pulse(self, kind, data): return None
    def render_ripple(self, kind, data): return None
    def render_stream(self, kind, data): return None
    def render_bloom(self, kind, data): return None
    def render_shatter(self, kind, data): return None
    def render_orbit(self, kind, data): return None
    def render_gauge(self, kind, data): return None
    def render_spark(self, kind, data): return None
    def render_wave(self, kind, data): return None
    def render_glyph(self, kind, data): return None
    def render_trail(self, kind, data): return None
    def render_constellation(self, kind, data): return None

    # ── NEW: Sound System ──
    def sound_cues(self): return {}  # Dict[str, SoundCue]
```

Total: ~20 existing + ~25 reactive/postfx/emergent + ~14 reactive element + 1 sound = ~60 methods.
All new methods have safe no-op defaults. Zero impact on existing themes.

---

## 14. Backward Compatibility Guarantees

### Rules (enforced in code and docs)

1. **Bridge is append-only.** Never remove event kinds from _MAPPING. Never rename effect types. Only add.

2. **ThemePlugin API is frozen at v1.0.** Existing method signatures NEVER change. New methods added with default implementations only.

3. **ThemeConfig is frozen.** New fields use defaults. Never remove or retype existing fields.

4. **VisualTrigger is frozen.** The 4-field contract (effect, intensity, color_key, target) never changes. New effects are just new string values in the `effect` field.

5. **Particle/Packet/Pulse dataclasses are frozen.** New visual elements (Streak, OverlayEffect, etc.) get their own dataclasses.

6. **Source poll interface is frozen.** `PollFn = Callable[[float], List[VisionEvent]]` never changes. VisionEvent fields never change.

7. **.hvtheme format v1.x is backward compatible.** v1.0 themes import into v1.1+ with defaults. v1.1 themes import into v1.0 with a warning.

8. **Emergent systems are fully opt-in.** A plugin returning None from automaton_config() etc. gets zero overhead. No emergent system runs unless explicitly configured.

9. **Post-processing is fully opt-in.** All post-processing defaults to disabled (identity warp, empty void, 0 echo, 0 glow, no mask, no decay, no symmetry, 1 depth layer).

10. **An old theme from v0.1.x will run on v0.2.0 with zero changes and identical visual output.** It just won't use any new features.

---

## 15. Performance Budget

Target: 20 FPS (50ms per frame) on 120×40 terminal.

### Current baseline
- Complex ASCII field theme: ~15-25ms

### New overhead (all enabled, worst case)
- FrameBuffer allocation: ~0.5ms (one-time per resize)
- Buffer write (vs direct screen write): ~2ms additional
- Warp field: ~3-5ms
- Symmetry: ~1ms
- Glow (radius 2): ~2-4ms
- Void: ~0.5ms
- Echo: ~1-2ms
- Decay: ~1ms
- Mask: ~1ms
- Force fields: ~0.5ms
- Emergent CA: ~3-5ms
- Emergent physarum: ~5-8ms
- Emergent neural field: ~3-5ms
- Emergent waves: ~3-5ms
- Emergent boids: ~1-2ms
- Specials/overlays: ~1-2ms

### Scenarios
- **Typical theme (2-3 post-fx, 1 emergent):** +8-12ms → 25-35ms total → 28-40 FPS ✓
- **Heavy theme (5 post-fx, 2 emergent):** +18-25ms → 35-50ms total → 20-28 FPS ✓
- **Maximum everything:** +30-40ms → 50-65ms total → 15-20 FPS ⚠️ (TuneSettings can reduce)

### Mitigations
- `--performance` CLI flag: disables all post-processing
- TuneSettings: every primitive has a slider/toggle to zero it out
- Emergent systems: `update_interval` config (run every Nth frame)
- Reaction-diffusion: subsampled grid (60×20 internal)
- Warp field: can be cached if static across frames
- Row-based rendering: build and write strings per-row, not per-char

---

## 16. Files Changed

### Tier 1 (modify existing)
- `sources/HOOK.yaml` — add 14 new event subscriptions
- `sources/custom.py` — expand EVENT_MAP
- `bridge.py` — add new event kinds, add emergent injection, API contract docstring
- `log_overlay.py` — add format strings + SOURCE_COLORS
- `scene.py` — add 4 new effects, Streak/OverlayEffect dataclasses, buffer support, emergent system integration
- `renderer.py` — FrameBuffer class, buffer-based rendering, post-processing pipeline, streak drawing
- `plugin.py` — all new method stubs with defaults, API FROZEN docstring
- `export.py` — format v1.1, new metadata
- `import_theme.py` — v1.1 compat, 1.0 defaults
- `tune.py` — all new sliders/toggles
- `events.py` — API FROZEN docstring
- `VERSION_COMPATIBILITY.md` — v1.1 format docs

### Tier 2 (modify existing)
- `sources/state_db.py` — new columns, fallback queries

### Tier 3 (new files)
- `sources/mcp.py`
- `sources/skills.py`
- `sources/checkpoints.py`
- `sources/providers.py`
- `sources/context.py`
- `sources/sessions.py`
- `cli.py` — wire new sources, source enable/disable

### Reactive Element System (new files)
- `reactive.py` — ReactiveElement enum, Reaction dataclass, REACTIVE_MAP, ReactiveRenderer

### Sound System (new files)
- `sound.py` — SoundCue dataclass, SoundEngine class, DEFAULT_CUES

### Emergent systems (new files)
- `emergent/__init__.py`
- `emergent/automaton.py` — CyclicCA, BriansBrain, Rule110
- `emergent/physarum.py` — PhysarumSim
- `emergent/neural_field.py` — NeuralField
- `emergent/wave_field.py` — WaveField
- `emergent/boids.py` — BoidsSystem
- `emergent/reaction_diffusion.py` — GrayScott

### Post-processing (new file)
- `postfx.py` — warp, void, echo, glow, mask, decay, symmetry pipeline

### Tests (new/updated)
- `test_bridge.py` — new event kinds
- `test_scene.py` — new effects, emergent integration
- `test_renderer.py` — buffer pipeline, post-processing
- `test_postfx.py` — each post-fx primitive
- `test_emergent.py` — each emergent system (step, inject, render)
- `test_export_import.py` — v1.1 format
- `test_sources.py` — new sources
- `test_tune.py` — new toggles/sliders
- `test_plugin.py` — new method defaults
- `test_reactive.py` — ReactiveElement mapping, Reaction generation, ReactiveRenderer physics
- `test_sound.py` — SoundCue, SoundEngine (mock subprocess), cooldown, macOS detection

---

## 17. Implementation Phases

### Phase 1: Buffer Foundation (~3h)
1. Implement FrameBuffer class in renderer.py
2. Refactor Renderer.draw() to write to buffer first, then blit
3. Verify all existing themes render identically through buffer
4. Tests for buffer round-trip

### Phase 2: Plugin API Expansion (~2h)
5. Add ALL new plugin methods with safe defaults to plugin.py
6. Add API FROZEN docstring
7. Add SpecialEffect dataclass
8. Tests for default behavior (all no-ops)

### Phase 3: New Effects + Reactive Primitives (~4h)
9. Add ripple, cascade, converge, streak to scene.py apply_trigger()
10. Add Streak dataclass + _draw_streaks() to renderer.py
11. Add palette_shift processing to renderer
12. Add OverlayEffect tracking + draw_overlay_effect calls
13. Add special effects activation + draw_special calls
14. Add effect_zones, intensity_curve, ambient_tick wiring
15. Tests for each

### Phase 4: Post-Processing Pipeline (~5h)
16. Implement postfx.py with all 9 post-processing operations
17. Wire into renderer after buffer write, before blit
18. Add TuneSettings controls
19. Implement echo ring buffer
20. Tests for each post-fx

### Phase 5: Emergent Systems (~6h)
21. Implement emergent/automaton.py (BriansBrain, CyclicCA, Rule110)
22. Implement emergent/physarum.py
23. Implement emergent/neural_field.py
24. Implement emergent/wave_field.py
25. Implement emergent/boids.py
26. Implement emergent/reaction_diffusion.py
27. Wire into ThemeState (init from plugin config, step each frame)
28. Wire event injection through Bridge
29. Wire rendering into buffer pipeline
30. Tests for each system

### Phase 6: Event Pipeline (~3h)
31. Expand HOOK.yaml
32. Expand custom.py EVENT_MAP
33. Expand bridge.py _MAPPING
34. Expand log_overlay.py formats
35. Tests

### Phase 7: Data Sources (~4h)
36. Update state_db.py with new columns + fallback
37. Implement sources/mcp.py
38. Implement sources/skills.py
39. Implement sources/checkpoints.py
40. Add source config + CLI flags
41. Tests

### Phase 8: Export/Import + Docs (~2h)
42. Bump export.py to v1.1
43. Update import_theme.py for compat
44. Update VERSION_COMPATIBILITY.md
45. Update README.md
46. Update CHANGELOG.md
47. Tests

### Phase 9: Integration + Polish (~3h)
48. Full test suite pass
49. Manual visual testing of each new primitive
50. Performance profiling + optimization if needed
51. Gallery mode testing (all themes cycle without crash)

### Phase 10: Reactive Element System (~3h)
52. Implement ReactiveElement enum + Reaction dataclass in reactive.py
53. Implement REACTIVE_MAP defaults (30 event→element mappings)
54. Implement ReactiveRenderer with 12 element physics engines
55. Wire into Bridge dispatch (event → react() → Reaction → ReactiveRenderer)
56. Add render_* method stubs to ThemePlugin base class
57. Update existing themes to optionally override render_* methods
58. Tests for mapping, dispatch, each element renderer

### Phase 11: Sound System (~2h)
59. Implement SoundCue dataclass + SoundEngine class in sound.py
60. Implement curses.beep()/flash() tier (zero-dep)
61. Implement macOS detection + afplay/say/osascript tier
62. Add plugin hook: sound_cues() → Dict[str, SoundCue]
63. Wire SoundEngine into Bridge (event → sound_cues lookup → play)
64. Add TuneSettings: sound_enabled, sound_volume
65. Add CLI flags: --sound/--no-sound/--volume
66. Tests (mock subprocess for macOS, test cooldowns)

**Total estimate: ~37 hours**

---

## 18. What We Are NOT Doing

1. ❌ **Prometheus/metrics** — post-stable, separate sidecar package
2. ❌ **New themes** — build system first, THEN mass-create screens using new primitives
3. ❌ **Sprites** — needs art asset system, defer to v0.3.0
4. ❌ **Full trail system** — TRAIL reactive element covers basic path tracing; full trail persistence/replay deferred to v0.3.0
6. ❌ **Platform-aware color coding** — defer to v0.2.1
7. ❌ **Web dashboard companion** — roadmap item
8. ❌ **Breaking any existing theme, plugin, or export format** — NEVER
