"""Theme plugin base class for Hermes Vision.

API VERSION: 1.0 — FROZEN
══════════════════════════════════════════════════════════════════════════

This file defines the ThemePlugin base class that ALL theme plugins inherit.
Every method has a safe default (no-op or identity) so existing themes work
unchanged on newer versions of hermes-neurovision.

RULES (enforced):
  1. NEVER change the signature of an existing method.
  2. NEVER remove a method.
  3. New methods MUST have a default implementation that is a no-op or
     returns a safe identity value (None, [], {}, 0, etc.).
  4. New dataclasses (SpecialEffect, Reaction, etc.) are additive only.
  5. A v0.1.x theme running on v0.2.0+ MUST produce identical output.

Themes override only what they need. Everything else falls through to
these defaults with zero visual or behavioral impact.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from hermes_neurovision.scene import Particle


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

class ReactiveElement(enum.Enum):
    """12 visual treatment categories. Each has distinct motion physics."""
    PULSE = "pulse"                   # radial burst from center, one-shot, dramatic
    RIPPLE = "ripple"                 # concentric rings from a point, one-shot
    STREAM = "stream"                 # flowing particles in a direction, sustained
    BLOOM = "bloom"                   # organic growth, expands and holds, then fades
    SHATTER = "shatter"              # explosion of fragments, pieces scatter and fade
    ORBIT = "orbit"                   # persistent rotating elements, stays while alive
    GAUGE = "gauge"                   # fills/drains a bar or arc, changes color at thresholds
    SPARK = "spark"                   # bright flash + lingering afterglow, demands attention
    WAVE = "wave"                     # horizontal sweep across screen, transformative
    GLYPH = "glyph"                  # symbol/sigil that appears and persists, slowly morphing
    TRAIL = "trail"                   # path/line tracing movement across screen
    CONSTELLATION = "constellation"   # dots that connect/disconnect with lines, persistent


@dataclass
class SpecialEffect:
    """Declares a named special effect that a theme can draw."""
    name: str
    trigger_kinds: List[str] = field(default_factory=list)
    min_intensity: float = 0.0
    cooldown: float = 5.0
    duration: float = 2.0


@dataclass
class Reaction:
    """A themed response to a data event."""
    element: ReactiveElement
    intensity: float                     # 0.0-1.0, how dramatic
    origin: Tuple[float, float]          # where on screen (0-1 normalized)
    color_key: str                       # key into theme palette
    duration: float                      # seconds
    data: Dict[str, Any] = field(default_factory=dict)   # element-specific params
    sound: Optional[str] = None          # sound cue name, if any


# ---------------------------------------------------------------------------
# ThemePlugin — base class
# ---------------------------------------------------------------------------

class ThemePlugin:
    """Base class for theme plugins.

    Each method has a default that reproduces the generic (neural-sky) behavior.
    Themes override only what they need.
    """

    name: str = "base"

    # ══════════════════════════════════════════════════════════════════════
    # EXISTING METHODS — v1.0 API (frozen, never change signatures)
    # ══════════════════════════════════════════════════════════════════════

    # ── Node layout ──────────────────────────────────────────────

    def build_nodes(self, w: int, h: int, cx: float, cy: float,
                    count: int, rng) -> Optional[List[Tuple[float, float]]]:
        """Custom node positions. Return None to use default cluster logic."""
        return None

    def edge_keep_count(self) -> int:
        """Nearest-neighbor count for edge building."""
        return 3

    def build_edges_extra(self, nodes: List[Tuple[float, float]],
                          edges_set: set) -> None:
        """Add extra edges after nearest-neighbor pass."""
        pass

    # ── Star movement ────────────────────────────────────────────

    def step_star(self, star: list, frame: int, w: int, h: int, rng) -> bool:
        """Custom star movement. Return True if handled, False for default drift."""
        return False

    def step_star_post(self, star: list, frame: int, w: int, h: int, rng) -> None:
        """Post-drift star tweak (e.g. glass_mode vertical sway)."""
        pass

    # ── Particles ────────────────────────────────────────────────

    def spawn_particle(self, w: int, h: int, nodes: list, rng) -> Optional["Particle"]:
        """Custom particle. Return None to use default spawner."""
        return None

    def particle_base_chance(self) -> float:
        """Probability of spawning a particle per frame."""
        return 0.028

    def particle_life_range(self) -> Tuple[int, int]:
        """(min, max) life for particles."""
        return (7, 14)

    # ── Node animation ───────────────────────────────────────────

    def step_nodes(self, nodes: list, frame: int, w: int, h: int) -> None:
        """Per-frame node animation (e.g. orbital rotation)."""
        pass

    # ── Pulse params ─────────────────────────────────────────────

    def pulse_params(self) -> Tuple[float, float]:
        """(growth_rate, limit_ratio) for pulse expansion."""
        return (0.28, 0.16)

    def pulse_style(self) -> str:
        """Pulse visual style: 'ring', 'rays', 'spoked', 'ripple', 'cloud', 'diamond'."""
        return "ring"

    # ── Packet budget ────────────────────────────────────────────

    def packet_budget(self) -> int:
        """Max concurrent packets."""
        return 4

    # ── Glyph overrides ──────────────────────────────────────────

    def star_glyph(self, brightness: float, char_idx: int) -> Optional[str]:
        """Override star character. Return None to use STAR_CHARS."""
        return None

    def node_glyph(self, idx: int, intensity: float, total: int) -> str:
        """Node character."""
        return "\u25cf" if intensity > 0.72 else "\u2022"

    def node_color_key(self, idx: int, intensity: float, total: int) -> str:
        """Node color key."""
        return "bright" if intensity > 0.65 else "soft"

    def edge_glyph(self, dx: float, dy: float) -> Optional[str]:
        """Override edge character. Return None for default."""
        return None

    def edge_color_key(self, step: int, idx_a: int, frame: int) -> str:
        """Edge color key."""
        return "base"

    def packet_color_key(self) -> str:
        """Packet color key."""
        return "accent"

    def particle_color_key(self, age_ratio: float) -> str:
        """Particle color key."""
        return "accent" if age_ratio > 0.6 else "soft"

    def pulse_color_key(self) -> str:
        """Pulse color key."""
        return "soft"

    def node_position_adjust(self, x: float, y: float, idx: int,
                             frame: int, w: int, h: int) -> Optional[Tuple[float, float]]:
        """Extra node position tweak. Return None for no adjustment."""
        return None

    # ── Drawing extras ───────────────────────────────────────────

    def draw_background(self, stdscr, state, color_pairs: dict) -> None:
        """ASCII field or texture drawn BEFORE nodes/edges — use for hybrid themes.

        Called after stars, before edges/nodes/packets. This lets a theme render
        a full-screen ASCII field as a backdrop while still having nodes and
        event-driven packets/pulses rendered on top.
        """
        pass

    def draw_extras(self, stdscr, state, color_pairs: dict) -> None:
        """ASCII art and special FX drawn AFTER everything else — foreground layer.

        For pure ASCII field themes (no nodes), put all rendering here.
        For hybrid themes, use draw_background() for the field and draw_extras()
        for any foreground overlay effects.
        """
        pass

    # ══════════════════════════════════════════════════════════════════════
    # NEW METHODS — v0.2.0 (all with safe no-op defaults)
    # ══════════════════════════════════════════════════════════════════════

    # ── Reactive Primitives ──────────────────────────────────────

    def palette_shift(self, trigger_effect: str, intensity: float,
                      base_palette: Tuple[int, int, int, int]) -> Optional[Tuple[int, int, int, int]]:
        """Return a shifted palette in response to a trigger, or None to keep current."""
        return None

    def draw_overlay_effect(self, stdscr, state, color_pairs: dict,
                            trigger_effect: str, intensity: float,
                            progress: float) -> None:
        """Draw a transient overlay effect triggered by an event."""
        pass

    def special_effects(self) -> List[SpecialEffect]:
        """Declare up to 3 special effects. Default: none."""
        return []

    def draw_special(self, stdscr, state, color_pairs: dict,
                     special_name: str, progress: float,
                     intensity: float) -> None:
        """Draw a named special effect at a given progress (0-1)."""
        pass

    def effect_zones(self) -> Dict[str, Tuple[float, float, float, float]]:
        """Map zone names to (x, y, w, h) normalized rects. Default: no zones."""
        return {}

    def intensity_curve(self, raw: float) -> float:
        """Transform raw intensity through a theme-specific curve. Default: identity."""
        return raw

    def ambient_tick(self, stdscr, state, color_pairs: dict,
                     idle_seconds: float) -> None:
        """Per-frame ambient drawing when no events are firing. Default: no-op."""
        pass

    # ── Post-Processing ──────────────────────────────────────────

    def warp_field(self, x: int, y: int, w: int, h: int,
                   frame: int, intensity: float) -> Tuple[int, int]:
        """Displace (x, y) for warp effect. Default: identity (no warp)."""
        return (x, y)

    def void_points(self, w: int, h: int, frame: int,
                    intensity: float) -> List[Tuple[int, int]]:
        """Return list of (x, y) positions to erase. Default: none."""
        return []

    def echo_decay(self) -> int:
        """Number of frames for echo ring buffer. 0 = disabled."""
        return 0

    def force_points(self, w: int, h: int, frame: int,
                     intensity: float) -> List[Tuple[int, int, float, float]]:
        """Return list of (x, y, fx, fy) force vectors. Default: none."""
        return []

    def decay_sequence(self) -> Optional[str]:
        """Character sequence for cell aging. None = disabled."""
        return None

    def symmetry(self) -> Optional[str]:
        """Symmetry mode: 'horizontal', 'vertical', 'quad', 'radial', or None."""
        return None

    def depth_layers(self) -> int:
        """Number of parallax depth layers. 1 = flat (disabled)."""
        return 1

    def glow_radius(self) -> int:
        """Glow bleed radius in cells. 0 = disabled."""
        return 0

    def render_mask(self, w: int, h: int, frame: int,
                    intensity: float) -> Optional[List[List[bool]]]:
        """Return a 2D boolean mask (h rows x w cols). None = no mask."""
        return None

    # ── Emergent Systems ─────────────────────────────────────────

    def automaton_config(self) -> Optional[Dict[str, Any]]:
        """Cellular automaton config. None = disabled."""
        return None

    def physarum_config(self) -> Optional[Dict[str, Any]]:
        """Physarum simulation config. None = disabled."""
        return None

    def neural_field_config(self) -> Optional[Dict[str, Any]]:
        """Neural field config. None = disabled."""
        return None

    def wave_config(self) -> Optional[Dict[str, Any]]:
        """Wave field config. None = disabled."""
        return None

    def boids_config(self) -> Optional[Dict[str, Any]]:
        """Boids flocking config. None = disabled."""
        return None

    def reaction_diffusion_config(self) -> Optional[Dict[str, Any]]:
        """Reaction-diffusion config. None = disabled."""
        return None

    def emergent_layer(self) -> str:
        """Which render layer for emergent systems: 'background', 'midground', 'foreground'."""
        return "background"

    # ── Visual Effect Hooks ──────────────────────────────────────

    def streak_color_key(self) -> str:
        """Color key for streaks."""
        return "accent"

    # ── Reactive Element System ──────────────────────────────────

    REACTIVE_MAP: Dict[str, ReactiveElement] = {
        # Agent lifecycle → PULSE
        "agent_start":         ReactiveElement.PULSE,
        "agent_end":           ReactiveElement.PULSE,
        "session_resume":      ReactiveElement.PULSE,
        # Tool activity → RIPPLE
        "tool_call":           ReactiveElement.RIPPLE,
        "tool_complete":       ReactiveElement.RIPPLE,
        "tool_error":          ReactiveElement.RIPPLE,
        "mcp_tool_call":       ReactiveElement.RIPPLE,
        # LLM generation → STREAM
        "llm_start":           ReactiveElement.STREAM,
        "llm_chunk":           ReactiveElement.STREAM,
        "llm_end":             ReactiveElement.STREAM,
        # Knowledge creation → BLOOM
        "memory_save":         ReactiveElement.BLOOM,
        "skill_create":        ReactiveElement.BLOOM,
        "checkpoint_created":  ReactiveElement.BLOOM,
        # Errors & security → SHATTER
        "error":               ReactiveElement.SHATTER,
        "crash":               ReactiveElement.SHATTER,
        "threat_blocked":      ReactiveElement.SHATTER,
        # Persistent processes → ORBIT
        "cron_tick":           ReactiveElement.ORBIT,
        "background_proc":     ReactiveElement.ORBIT,
        "subagent_started":    ReactiveElement.ORBIT,
        # Metrics → GAUGE
        "context_pressure":    ReactiveElement.GAUGE,
        "token_usage":         ReactiveElement.GAUGE,
        "cost_update":         ReactiveElement.GAUGE,
        # Attention-demanding → SPARK
        "approval_request":    ReactiveElement.SPARK,
        "dangerous_cmd":       ReactiveElement.SPARK,
        # Transformative events → WAVE
        "compression_started": ReactiveElement.WAVE,
        "compression_ended":   ReactiveElement.WAVE,
        "checkpoint_rollback": ReactiveElement.WAVE,
        # State indicators → GLYPH
        "personality_change":  ReactiveElement.GLYPH,
        "reasoning_change":    ReactiveElement.GLYPH,
        # Movement/navigation → TRAIL
        "browser_navigate":    ReactiveElement.TRAIL,
        "file_edit":           ReactiveElement.TRAIL,
        "git_commit":          ReactiveElement.TRAIL,
        # Connections → CONSTELLATION
        "mcp_connected":       ReactiveElement.CONSTELLATION,
        "mcp_disconnected":    ReactiveElement.CONSTELLATION,
        "provider_health":     ReactiveElement.CONSTELLATION,
        "provider_fallback":   ReactiveElement.CONSTELLATION,
        "platform_connect":    ReactiveElement.CONSTELLATION,
    }

    def react(self, event_kind: str, data: Dict[str, Any]) -> Optional[Reaction]:
        """Dispatch an event kind to the appropriate reactive element.

        Themes can override this entirely or override individual render_*
        methods for finer control.  Default: returns None (no reaction).
        """
        return None

    def render_pulse(self, kind: str, data: Dict[str, Any]) -> None:
        """Render a PULSE reactive element. Default: no-op."""
        pass

    def render_ripple(self, kind: str, data: Dict[str, Any]) -> None:
        """Render a RIPPLE reactive element. Default: no-op."""
        pass

    def render_stream(self, kind: str, data: Dict[str, Any]) -> None:
        """Render a STREAM reactive element. Default: no-op."""
        pass

    def render_bloom(self, kind: str, data: Dict[str, Any]) -> None:
        """Render a BLOOM reactive element. Default: no-op."""
        pass

    def render_shatter(self, kind: str, data: Dict[str, Any]) -> None:
        """Render a SHATTER reactive element. Default: no-op."""
        pass

    def render_orbit(self, kind: str, data: Dict[str, Any]) -> None:
        """Render an ORBIT reactive element. Default: no-op."""
        pass

    def render_gauge(self, kind: str, data: Dict[str, Any]) -> None:
        """Render a GAUGE reactive element. Default: no-op."""
        pass

    def render_spark(self, kind: str, data: Dict[str, Any]) -> None:
        """Render a SPARK reactive element. Default: no-op."""
        pass

    def render_wave(self, kind: str, data: Dict[str, Any]) -> None:
        """Render a WAVE reactive element. Default: no-op."""
        pass

    def render_glyph(self, kind: str, data: Dict[str, Any]) -> None:
        """Render a GLYPH reactive element. Default: no-op."""
        pass

    def render_trail(self, kind: str, data: Dict[str, Any]) -> None:
        """Render a TRAIL reactive element. Default: no-op."""
        pass

    def render_constellation(self, kind: str, data: Dict[str, Any]) -> None:
        """Render a CONSTELLATION reactive element. Default: no-op."""
        pass

    # ── Sound System ─────────────────────────────────────────────

    def sound_cues(self) -> Dict[str, Any]:
        """Map event kinds to SoundCue objects. Default: no sounds."""
        return {}
