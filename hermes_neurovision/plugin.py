"""Theme plugin base class for Hermes Vision."""

from __future__ import annotations

from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from hermes_neurovision.scene import Particle


class ThemePlugin:
    """Base class for theme plugins.

    Each method has a default that reproduces the generic (neural-sky) behavior.
    Themes override only what they need.
    """

    name: str = "base"

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

    def draw_extras(self, stdscr, state, color_pairs: dict) -> None:
        """ASCII art and special FX drawn after everything else."""
        pass
