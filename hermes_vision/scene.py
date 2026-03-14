"""Scene simulation for Hermes Vision."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from hermes_vision.themes import ThemeConfig, STAR_CHARS, PACKET_CHARS


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

    MAX_DYNAMIC_NODES = 64

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        from hermes_vision.theme_plugins import get_plugin
        self.plugin = get_plugin(self.config.name)
        self._build_scene()

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
        self._build_scene()

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
        for i in range(clusters):
            a = (math.tau * i) / clusters + self.rng.uniform(-0.2, 0.2)
            r = min(usable_w, usable_h) * self.rng.uniform(0.15, 0.32)
            centers.append((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.7))
        per_cluster = max(4, count // clusters)
        for mx, my in centers:
            for _ in range(per_cluster):
                nodes.append((
                    mx + self.rng.uniform(-usable_w * 0.10, usable_w * 0.10),
                    my + self.rng.uniform(-usable_h * 0.10, usable_h * 0.10),
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
                dy = node[1] - other[1]
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
        import time as _time

        effect = trigger.effect
        intensity = trigger.intensity

        if effect == "packet" and self.edges:
            edge_idx = self.rng.randrange(len(self.edges))
            edge = self.edges[edge_idx]
            speed = 0.04 + intensity * 0.06
            self.packets.append(Packet((edge[0], edge[1]), 0.0, speed))

        elif effect == "pulse" and self.nodes:
            if trigger.target == "center":
                idx = len(self.nodes) // 2
            else:
                idx = self.rng.randrange(len(self.nodes))
            nx, ny = self.nodes[idx]
            self.pulses.append((nx, ny, 0.0))

        elif effect == "burst" and self.nodes:
            if trigger.target == "center":
                idx = len(self.nodes) // 2
            else:
                idx = self.rng.randrange(len(self.nodes))
            nx, ny = self.nodes[idx]
            for _ in range(int(3 + intensity * 5)):
                vx = self.rng.uniform(-0.3, 0.3) * intensity
                vy = self.rng.uniform(-0.2, 0.2) * intensity
                life = self.rng.randint(6, 14)
                self.particles.append(Particle(nx, ny, vx, vy, life, life, self.rng.choice(".:*+@")))

        elif effect == "flash":
            self.flash_until = _time.time() + 0.3 * intensity
            self.flash_color_key = trigger.color_key

        elif effect == "spawn_node":
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

    def step(self) -> None:
        self._step_intensity()
        self.frame += 1
        self.plugin.step_nodes(self.nodes, self.frame, self.width, self.height)
        self._step_stars()
        self._spawn_packets()
        self._step_packets()
        self._spawn_particles()
        self._step_particles()
        self._step_pulses()

    def _step_stars(self) -> None:
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
        if not self.edges:
            return
        packet_budget = self.plugin.packet_budget()
        if len(self.packets) >= packet_budget:
            return
        if self.rng.random() > self.config.packet_rate:
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
        if self.rng.random() < self.config.pulse_rate and self.nodes:
            nx, ny = self.rng.choice(self.nodes)
            self.pulses.append((nx, ny, 0.0))

        base_chance = self.plugin.particle_base_chance()
        if self.rng.random() > base_chance:
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
