"""Scene simulation for Hermes Vision."""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, List, Optional, Tuple

if TYPE_CHECKING:
    from hermes_neurovision.plugin import SpecialEffect

from hermes_neurovision.themes import ThemeConfig, STAR_CHARS, PACKET_CHARS


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    char: str
    frames: Optional[List[str]] = None

    def step(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.99
        self.vy *= 0.99
        self.life -= 1.0
        if self.frames:
            frame_idx = int(self.max_life - self.life) % len(self.frames)
            self.char = self.frames[frame_idx]
        return self.life > 0

    @property
    def age_ratio(self) -> float:
        if self.max_life <= 0:
            return 1.0
        return max(0.0, min(1.0, self.life / self.max_life))


@dataclass
class Packet:
    edge: Tuple[int, int]
    progress: float
    speed: float
    reverse: bool = False
    glyph: str = "o"

    def step(self) -> None:
        self.progress += self.speed
        if self.progress > 1.0:
            self.progress -= 1.0


@dataclass
class Streak:
    x: float
    y: float
    dx: float  # velocity x per frame
    dy: float  # velocity y per frame
    length: int  # trail length in chars
    char: str = '━'
    life: int = 30
    max_life: int = 30

    def step(self) -> bool:
        self.x += self.dx
        self.y += self.dy
        self.life -= 1
        return self.life > 0


@dataclass
class OverlayEffect:
    trigger_effect: str
    intensity: float
    start_time: float
    duration: float = 1.0


@dataclass
class ActiveSpecial:
    name: str
    intensity: float
    start_time: float
    duration: float = 1.0


@dataclass
class ThemeState:
    config: ThemeConfig
    width: int
    height: int
    seed: int
    nodes: List[Tuple[float, float]] = field(default_factory=list)
    edges: List[Tuple[int, int]] = field(default_factory=list)
    stars: List[List[float]] = field(default_factory=list)
    packets: List[Packet] = field(default_factory=list)
    particles: List[Particle] = field(default_factory=list)
    pulses: List[Tuple[float, float, float]] = field(default_factory=list)
    frame: int = 0
    rng: random.Random = field(init=False)

    # Intensity control for event reactions
    intensity_multiplier: float = 0.6
    _intensity_target: float = 0.6
    _intensity_rate: float = 0.0
    _dynamic_nodes: List[int] = field(default_factory=list)
    flash_until: float = 0.0
    flash_color_key: str = "warning"

    quiet: bool = False  # suppress passive spawning; only react to explicit events
    tune: Any = None    # Optional[TuneSettings], set by app code

    streaks: List[Streak] = field(default_factory=list)
    overlay_effects: List[OverlayEffect] = field(default_factory=list)
    active_specials: List[ActiveSpecial] = field(default_factory=list)
    _cascade_queue: List[Tuple[int, float]] = field(default_factory=list)
    _palette_shift_until: float = 0.0
    _shifted_palette: Optional[Tuple[int, int, int, int]] = None
    _last_event_time: float = 0.0  # for idle detection / ambient_tick

    # Emergent systems (all Optional, None = disabled)
    automaton: Any = None  # CellularAutomaton
    physarum: Any = None   # PhysarumSim
    neural_field: Any = None  # NeuralField
    wave_field: Any = None  # WaveField
    boids: Any = None  # BoidsFlock
    reaction_diffusion: Any = None  # ReactionDiffusion

    MAX_DYNAMIC_NODES = 64

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        from hermes_neurovision.theme_plugins import get_plugin
        self.plugin = get_plugin(self.config.name)
        self._build_scene()
        self._init_emergent()

    def resize(self, width: int, height: int) -> None:
        if width == self.width and height == self.height:
            return
        self.width = width
        self.height = height
        self.nodes.clear()
        self.edges.clear()
        self.stars.clear()
        self.packets.clear()
        self.particles.clear()
        self.pulses.clear()
        self.streaks.clear()
        self.overlay_effects.clear()
        self.active_specials.clear()
        self._cascade_queue.clear()
        self.automaton = None
        self.physarum = None
        self.neural_field = None
        self.wave_field = None
        self.boids = None
        self.reaction_diffusion = None
        self._build_scene()
        self._init_emergent()

    def _build_scene(self) -> None:
        w = max(20, self.width)
        h = max(10, self.height)
        self._build_stars(w, h)
        self._build_nodes(w, h)
        self._build_edges()

    def _build_stars(self, w: int, h: int) -> None:
        count = max(24, int(w * h * self.config.background_density))
        self.stars = []
        for _ in range(count):
            self.stars.append([
                self.rng.uniform(0, w - 1),
                self.rng.uniform(1, h - 2),
                self.rng.uniform(0.2, 1.0),
                self.rng.randint(0, len(STAR_CHARS) - 1),
            ])

    def _build_nodes(self, w: int, h: int) -> None:
        cx = w / 2.0
        cy = h / 2.0
        count = max(8, min(40, int((w * h) / 140)))

        # Try plugin first
        custom = self.plugin.build_nodes(w, h, cx, cy, count, self.rng)
        if custom is not None:
            self.nodes = custom[:max(10, min(len(custom), 56))]
            return

        # Default cluster logic
        usable_h = max(6.0, h - 6.0)
        usable_w = max(12.0, w - 8.0)
        nodes: List[Tuple[float, float]] = []
        clusters = max(2, self.config.cluster_count)
        centers = []
        # Random initial rotation ensures 2-cluster arrangements aren't always
        # purely horizontal (0°/180°) — they can be diagonal or vertical,
        # giving good x AND y coverage regardless of cluster count.
        base_angle = self.rng.uniform(0, math.tau / max(2, clusters))
        for i in range(clusters):
            a = base_angle + (math.tau * i) / clusters + self.rng.uniform(-0.2, 0.2)
            # Use separate x/y radii so clusters spread across the full screen,
            # not just a tiny box determined by the shorter dimension.
            r_x = usable_w * self.rng.uniform(0.22, 0.40)
            r_y = usable_h * self.rng.uniform(0.22, 0.40)
            centers.append((cx + math.cos(a) * r_x, cy + math.sin(a) * r_y * 0.7))
        per_cluster = max(4, count // clusters)
        # Node spread is sized relative to cluster separation, not screen size,
        # so clusters stay distinct rather than merging into one blob.
        spread_x = usable_w / max(clusters, 1) * 0.18
        spread_y = usable_h / max(clusters, 1) * 0.35
        for mx, my in centers:
            for _ in range(per_cluster):
                nodes.append((
                    mx + self.rng.uniform(-spread_x, spread_x),
                    my + self.rng.uniform(-spread_y, spread_y),
                ))

        self.nodes = nodes[: max(10, min(len(nodes), 56))]

    def _build_edges(self) -> None:
        edges = set()
        if not self.nodes:
            self.edges = []
            return

        keep = self.plugin.edge_keep_count()

        for idx, node in enumerate(self.nodes):
            distances = []
            for jdx, other in enumerate(self.nodes):
                if idx == jdx:
                    continue
                dx = node[0] - other[0]
                # Correct for terminal character aspect ratio (~2:1 height:width
                # in pixels). Without this, the algorithm treats 1 char of
                # vertical distance as equal to 1 char of horizontal, making
                # "nearest" neighbours cluster vertically and producing parallel
                # vertical lines. Multiplying dy by 2 matches visual distances.
                dy = (node[1] - other[1]) * 2.0
                distances.append((dx * dx + dy * dy, jdx))
            distances.sort(key=lambda item: item[0])
            for _, jdx in distances[:keep]:
                edge = tuple(sorted((idx, jdx)))
                edges.add(edge)

        self.plugin.build_edges_extra(self.nodes, edges)

        self.edges = sorted(edges)

    def _step_intensity(self) -> None:
        """Animate intensity multiplier toward target."""
        if abs(self.intensity_multiplier - self._intensity_target) > 0.01:
            diff = self._intensity_target - self.intensity_multiplier
            self.intensity_multiplier += diff * self._intensity_rate
        else:
            self.intensity_multiplier = self._intensity_target

    def apply_trigger(self, trigger) -> None:
        """Apply a VisualTrigger to the scene state."""
        _time = time

        effect = trigger.effect
        intensity = trigger.intensity
        if self.tune:
            intensity = intensity * self.tune.event_sensitivity

        if effect == "packet" and self.edges:
            if self.tune and not self.tune.show_packets:
                return
            edge_idx = self.rng.randrange(len(self.edges))
            edge = self.edges[edge_idx]
            speed = 0.04 + intensity * 0.06
            self.packets.append(Packet((edge[0], edge[1]), 0.0, speed))

        elif effect == "pulse" and self.nodes:
            if self.tune and not self.tune.show_pulses:
                return
            if trigger.target == "center":
                idx = len(self.nodes) // 2
            else:
                idx = self.rng.randrange(len(self.nodes))
            nx, ny = self.nodes[idx]
            self.pulses.append((nx, ny, 0.0))

        elif effect == "burst" and self.nodes:
            if self.tune and not self.tune.show_particles:
                return
            if trigger.target == "center":
                idx = len(self.nodes) // 2
            else:
                idx = self.rng.randrange(len(self.nodes))
            nx, ny = self.nodes[idx]
            count = int(3 + intensity * 5)
            if self.tune:
                count = max(0, int(count * self.tune.burst_scale))
            for _ in range(count):
                vx = self.rng.uniform(-0.3, 0.3) * intensity
                vy = self.rng.uniform(-0.2, 0.2) * intensity
                life = self.rng.randint(6, 14)
                self.particles.append(Particle(nx, ny, vx, vy, life, life, self.rng.choice(".:*+@")))

        elif effect == "flash":
            if self.tune and not self.tune.show_flash:
                return
            self.flash_until = _time.time() + 0.3 * intensity
            self.flash_color_key = trigger.color_key

        elif effect == "spawn_node":
            if self.tune and not self.tune.show_spawn_node:
                return
            if len(self._dynamic_nodes) >= self.MAX_DYNAMIC_NODES:
                oldest = self._dynamic_nodes.pop(0)
                if oldest < len(self.nodes):
                    self.nodes.pop(oldest)
            x = self.rng.uniform(4, max(5, self.width - 5))
            y = self.rng.uniform(2, max(3, self.height - 3))
            self.nodes.append((x, y))
            self._dynamic_nodes.append(len(self.nodes) - 1)
            self._build_edges()

        elif effect == "wake":
            self._intensity_target = 1.0
            self._intensity_rate = 0.15

        elif effect == "cool_down":
            self._intensity_target = 0.3
            self._intensity_rate = 0.05

        elif effect == "dim":
            self.intensity_multiplier = max(0.2, self.intensity_multiplier - 0.2)
            self._intensity_target = 0.6
            self._intensity_rate = 0.08

        elif effect == "ripple" and self.nodes:
            if self.tune and not self.tune.show_pulses:
                return
            if trigger.target == "center":
                idx = len(self.nodes) // 2
            else:
                idx = self.rng.randrange(len(self.nodes))
            nx, ny = self.nodes[idx]
            for offset in (0.0, -1.5, -3.0):
                self.pulses.append((nx, ny, max(0.0, offset)))

        elif effect == "cascade" and self.nodes:
            if self.tune and not self.tune.show_flash:
                return
            now = _time.time()
            if trigger.target == "all":
                indices = list(range(len(self.nodes)))
            else:
                indices = [self.rng.randrange(len(self.nodes)) for _ in range(min(5, len(self.nodes)))]
            for i, idx in enumerate(indices):
                self._cascade_queue.append((idx, now + i * 0.08))

        elif effect == "converge" and self.nodes:
            if self.tune and not self.tune.show_particles:
                return
            if trigger.target == "center":
                idx = len(self.nodes) // 2
            else:
                idx = self.rng.randrange(len(self.nodes))
            tx, ty = self.nodes[idx]
            count = self.rng.randint(5, 10)
            for _ in range(count):
                px = self.rng.uniform(0, self.width)
                py = self.rng.uniform(0, self.height)
                dx = tx - px
                dy = ty - py
                dist = math.hypot(dx, dy) or 1.0
                speed = self.rng.uniform(0.3, 0.7) * intensity
                vx = (dx / dist) * speed
                vy = (dy / dist) * speed
                life = max(6, int(dist / speed)) if speed > 0 else 10
                self.particles.append(Particle(px, py, vx, vy, life, life, self.rng.choice("·∙•◦")))

        elif effect == "streak":
            if self.tune and not getattr(self.tune, 'show_streaks', True):
                return
            edge = self.rng.randint(0, 3)  # 0=top, 1=bottom, 2=left, 3=right
            if edge == 0:
                x, y = self.rng.uniform(0, self.width), 0.0
                dx, dy = self.rng.uniform(-0.5, 0.5), self.rng.uniform(0.3, 0.8)
            elif edge == 1:
                x, y = self.rng.uniform(0, self.width), float(self.height)
                dx, dy = self.rng.uniform(-0.5, 0.5), self.rng.uniform(-0.8, -0.3)
            elif edge == 2:
                x, y = 0.0, self.rng.uniform(0, self.height)
                dx, dy = self.rng.uniform(0.5, 1.2), self.rng.uniform(-0.3, 0.3)
            else:
                x, y = float(self.width), self.rng.uniform(0, self.height)
                dx, dy = self.rng.uniform(-1.2, -0.5), self.rng.uniform(-0.3, 0.3)
            length = self.rng.randint(3, 8)
            life = self.rng.randint(20, 40)
            self.streaks.append(Streak(x, y, dx, dy, length, life=life, max_life=life))

        # --- Post-trigger bookkeeping ---
        self._last_event_time = _time.time()

        # Overlay effect tracking
        self.overlay_effects.append(OverlayEffect(
            trigger_effect=effect,
            intensity=intensity,
            start_time=_time.time(),
        ))

        # Palette shift (if plugin supports it)
        tune = getattr(self, 'tune', None)
        if not tune or getattr(tune, 'color_shifts', True):
            shifted = self.plugin.palette_shift(effect, intensity, self.config.palette)
            if shifted is not None:
                self._shifted_palette = shifted
                self._palette_shift_until = _time.time() + 1.0

        # Special effects (if plugin supports it)
        if hasattr(self.plugin, 'special_effects'):
            for spec in self.plugin.special_effects():
                if effect in (spec.trigger_kinds if hasattr(spec, 'trigger_kinds') else []):
                    self.active_specials.append(ActiveSpecial(
                        name=spec.name if hasattr(spec, 'name') else effect,
                        intensity=intensity,
                        start_time=_time.time(),
                        duration=spec.duration if hasattr(spec, 'duration') else 1.0,
                    ))

    def step(self) -> None:
        # Step emergent systems
        tune = getattr(self, 'tune', None)
        speed = getattr(tune, 'emergent_speed', 1.0) if tune else 1.0
        if speed > 0:
            steps = max(1, int(speed))
            for _ in range(steps):
                if self.automaton:
                    self.automaton.step()
                if self.physarum:
                    self.physarum.step()
                if self.neural_field:
                    self.neural_field.step()
                if self.wave_field:
                    self.wave_field.step()
                if self.boids:
                    self.boids.step()
                if self.reaction_diffusion:
                    self.reaction_diffusion.step()

        self._step_intensity()
        self.frame += 1
        self.plugin.step_nodes(self.nodes, self.frame, self.width, self.height)
        self._step_stars()
        self._spawn_packets()
        self._step_packets()
        self._spawn_particles()
        self._step_particles()
        self._step_pulses()
        self._step_streaks()
        self._step_overlay_effects()
        self._step_active_specials()
        self._step_cascade_queue()

    def _step_stars(self) -> None:
        if self.tune and not self.tune.show_stars:
            return
        drift = self.config.star_drift
        for star in self.stars:
            if self.plugin.step_star(star, self.frame, self.width, self.height, self.rng):
                # Plugin handled star movement
                pass
            else:
                star[0] -= drift * star[2]

            self.plugin.step_star_post(star, self.frame, self.width, self.height, self.rng)

            if star[0] < 0:
                star[0] = self.width - 2
                star[1] = self.rng.uniform(1, max(2, self.height - 2))
            elif star[0] >= self.width - 1 or star[1] < 1 or star[1] >= self.height - 1:
                star[0] = self.rng.uniform(1, max(2, self.width - 2))
                star[1] = self.rng.uniform(1, max(2, self.height - 2))

    def _spawn_packets(self) -> None:
        if self.tune and not self.tune.show_packets:
            return
        if self.quiet:
            return
        if not self.edges:
            return
        packet_budget = self.plugin.packet_budget()
        if len(self.packets) >= packet_budget:
            return
        rate = self.config.packet_rate
        if self.tune:
            rate *= self.tune.packet_rate_mult
        if rate <= 0.0 or self.rng.random() > rate:
            return
        edge_index = self.rng.randrange(len(self.edges))
        speed = self.rng.uniform(*self.config.packet_speed)
        glyph = self.config.accent_char if self.rng.random() < 0.55 else self.rng.choice(PACKET_CHARS)
        self.packets.append(Packet((self.edges[edge_index][0], self.edges[edge_index][1]), self.rng.random(), speed, glyph=glyph))

    def _step_packets(self) -> None:
        alive: List[Packet] = []
        for packet in self.packets:
            packet.step()
            if packet.progress <= 1.0:
                alive.append(packet)
        self.packets = alive[-12:]

    def _spawn_particles(self) -> None:
        if not self.quiet:
            pulse_rate = self.config.pulse_rate
            if self.tune:
                pulse_rate *= self.tune.pulse_rate_mult
            show_pulses = not (self.tune and not self.tune.show_pulses)
            if show_pulses and pulse_rate > 0.0 and self.rng.random() < pulse_rate and self.nodes:
                nx, ny = self.rng.choice(self.nodes)
                self.pulses.append((nx, ny, 0.0))

        base_chance = self.plugin.particle_base_chance()
        if self.tune:
            base_chance *= self.tune.particle_density
        show_particles = not (self.tune and not self.tune.show_particles)
        if self.quiet or not show_particles or base_chance <= 0.0 or self.rng.random() > base_chance:
            return

        # Try plugin particle first
        custom = self.plugin.spawn_particle(self.width, self.height, self.nodes, self.rng)
        if custom is not None:
            self.particles.append(custom)
            return

        # Default particle
        if not self.nodes:
            return
        x, y = self.rng.choice(self.nodes)
        vx = self.rng.uniform(-0.14, 0.14)
        vy = self.rng.uniform(-0.10, 0.10)
        char = self.rng.choice(".:*+")
        lo, hi = self.plugin.particle_life_range()
        life = self.rng.randint(lo, hi)
        self.particles.append(Particle(x, y, vx, vy, life, life, char))

    def _step_particles(self) -> None:
        next_particles: List[Particle] = []
        for particle in self.particles:
            if particle.step():
                if 0 <= particle.x < self.width and 0 <= particle.y < self.height:
                    next_particles.append(particle)
        self.particles = next_particles[-64:]

    def _step_pulses(self) -> None:
        growth, limit_ratio = self.plugin.pulse_params()
        limit = max(self.width, self.height) * limit_ratio
        next_pulses = []
        for x, y, radius in self.pulses:
            radius += growth
            if radius < limit:
                next_pulses.append((x, y, radius))
        self.pulses = next_pulses[-10:]

    def _step_streaks(self) -> None:
        next_streaks: List[Streak] = []
        for streak in self.streaks:
            if streak.step():
                if 0 <= streak.x < self.width and 0 <= streak.y < self.height:
                    next_streaks.append(streak)
        self.streaks = next_streaks[-16:]

    def _step_overlay_effects(self) -> None:
        now = time.time()
        self.overlay_effects = [
            oe for oe in self.overlay_effects
            if now - oe.start_time < oe.duration
        ][-16:]

    def _step_active_specials(self) -> None:
        now = time.time()
        self.active_specials = [
            sp for sp in self.active_specials
            if now - sp.start_time < sp.duration
        ][-8:]

    def _step_cascade_queue(self) -> None:
        if not self._cascade_queue:
            return
        now = time.time()
        remaining: List[Tuple[int, float]] = []
        for node_idx, flash_time in self._cascade_queue:
            if now >= flash_time:
                # Flash this node briefly
                self.flash_until = now + 0.12
                self.flash_color_key = "accent"
                # Also spawn a small pulse at the node
                if node_idx < len(self.nodes):
                    nx, ny = self.nodes[node_idx]
                    self.pulses.append((nx, ny, 0.0))
            else:
                remaining.append((node_idx, flash_time))
        self._cascade_queue = remaining

    def _init_emergent(self) -> None:
        """Initialize emergent systems from plugin config."""
        from hermes_neurovision.emergent import (
            CellularAutomaton, PhysarumSim, NeuralField,
            WaveField, BoidsFlock, ReactionDiffusion,
        )
        cfg = self.plugin.automaton_config()
        if cfg:
            self.automaton = CellularAutomaton(
                self.width, self.height,
                rule=cfg.get('rule', 'brians_brain'),
                density=cfg.get('density', 0.08),
                update_interval=cfg.get('update_interval', 2),
            )
        cfg = self.plugin.physarum_config()
        if cfg:
            self.physarum = PhysarumSim(
                self.width, self.height,
                n_agents=cfg.get('n_agents', 150),
                sensor_dist=cfg.get('sensor_dist', 4.0),
                sensor_angle=cfg.get('sensor_angle', 0.785),
                deposit=cfg.get('deposit', 1.0),
                decay=cfg.get('decay', 0.95),
            )
        cfg = self.plugin.neural_field_config()
        if cfg:
            self.neural_field = NeuralField(
                self.width, self.height,
                threshold=cfg.get('threshold', 2),
                fire_duration=cfg.get('fire_duration', 2),
                refractory=cfg.get('refractory', 5),
            )
        cfg = self.plugin.wave_config()
        if cfg:
            self.wave_field = WaveField(
                self.width, self.height,
                speed=cfg.get('speed', 0.3),
                damping=cfg.get('damping', 0.98),
            )
        cfg = self.plugin.boids_config()
        if cfg:
            self.boids = BoidsFlock(
                self.width, self.height,
                n_boids=cfg.get('n_boids', 40),
                sep_dist=cfg.get('sep_dist', 3.0),
                align_dist=cfg.get('align_dist', 8.0),
                cohesion_dist=cfg.get('cohesion_dist', 12.0),
                max_speed=cfg.get('max_speed', 1.5),
            )
        cfg = self.plugin.reaction_diffusion_config()
        if cfg:
            self.reaction_diffusion = ReactionDiffusion(
                self.width, self.height,
                feed=cfg.get('feed', 0.055),
                kill=cfg.get('kill', 0.062),
                update_interval=cfg.get('update_interval', 2),
            )
