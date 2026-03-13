"""Scene simulation for Hermes Vision."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple

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

    def step(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.99
        self.vy *= 0.99
        self.life -= 1.0
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
        usable_h = max(6.0, h - 6.0)
        usable_w = max(12.0, w - 8.0)
        nodes: List[Tuple[float, float]] = []
        count = max(8, min(40, int((w * h) / 140)))

        if self.config.galaxy_mode:
            # 3 distinct spiral arms with varied density
            arms = 3
            disc_radius = min(usable_w, usable_h) * 0.44
            
            # Distribute nodes by arm with varying density
            arm_distributions = [0.40, 0.35, 0.25]  # Asymmetric arms add realism
            nodes_per_arm = [int(count * ratio) for ratio in arm_distributions]
            
            for arm_idx in range(arms):
                arm_nodes = nodes_per_arm[arm_idx]
                for i in range(arm_nodes):
                    ratio = i / max(1, arm_nodes - 1)
                    base_angle = arm_idx * (math.tau / arms)
                    # Increased twist for more dramatic spiral
                    twist = ratio * math.tau * 1.8
                    angle = base_angle + twist
                    
                    # Vary radius with some randomness for natural look
                    radius = disc_radius * (0.12 + ratio * 0.88)
                    radius *= self.rng.uniform(0.85, 1.12)
                    
                    # Add slight randomness perpendicular to arm
                    perp_offset = self.rng.uniform(-0.9, 0.9)
                    x = cx + math.cos(angle) * radius + math.cos(angle + math.pi/2) * perp_offset
                    y = cy + math.sin(angle) * radius + math.sin(angle + math.pi/2) * perp_offset
                    nodes.append((x, y))
            
            # Bright galactic core
            core_nodes = max(6, count // 6)
            for i in range(core_nodes):
                angle = (math.tau * i) / core_nodes
                radius = disc_radius * self.rng.uniform(0.02, 0.10)
                nodes.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
            
            # Central bulge
            nodes.append((cx, cy))
        elif self.config.black_hole_mode:
            # Inner event horizon ring (spins fastest)
            inner_count = 8
            radius_x = usable_w * 0.12
            radius_y = usable_h * 0.14
            for i in range(inner_count):
                a = (math.tau * i) / inner_count
                nodes.append((cx + math.cos(a) * radius_x, cy + math.sin(a) * radius_y))
            
            # Middle accretion disk ring
            mid_count = max(12, count // 2)
            radius_x = usable_w * 0.22
            radius_y = usable_h * 0.26
            for i in range(mid_count):
                a = (math.tau * i) / mid_count
                wobble = 1.0 + math.sin(i * 0.9) * 0.08
                nodes.append((cx + math.cos(a) * radius_x * wobble, cy + math.sin(a) * radius_y * wobble))
            
            # Outer ring (slower)
            outer_count = max(6, count // 3)
            for i in range(outer_count):
                a = (math.tau * i) / outer_count + 0.4
                nodes.append((cx + math.cos(a) * usable_w * 0.32, cy + math.sin(a) * usable_h * 0.38))
            
            # Singularity at center
            nodes.append((cx, cy))
        elif self.config.ring_mode:
            radius_x = usable_w * 0.28
            radius_y = usable_h * 0.30
            for i in range(count):
                a = (math.tau * i) / count
                nodes.append((cx + math.cos(a) * radius_x, cy + math.sin(a) * radius_y))
            nodes.append((cx, cy))
        elif self.config.cathedral_mode:
            cols = max(4, min(8, w // 14))
            rows = max(3, min(7, h // 6))
            for row in range(rows):
                for col in range(cols):
                    x = 6 + col * (usable_w / max(1, cols - 1))
                    y = 3 + row * (usable_h / max(1, rows - 1))
                    arch = math.sin((col / max(1, cols - 1)) * math.pi) * 2.5
                    nodes.append((x, y + arch))
        elif self.config.root_mode:
            trunk_x = cx
            for row in range(max(8, h // 3)):
                y = 2 + row * (usable_h / max(1, (h // 3) - 1))
                sway = math.sin(row * 0.7) * 2.0
                nodes.append((trunk_x + sway, y))
                branch_span = 4 + row * 0.9
                if row > 1:
                    nodes.append((trunk_x - branch_span, y + self.rng.uniform(-1.0, 1.0)))
                    nodes.append((trunk_x + branch_span, y + self.rng.uniform(-1.0, 1.0)))
        elif self.config.storm_mode:
            bands = max(3, h // 7)
            for band in range(bands):
                y = 2 + band * (usable_h / max(1, bands - 1))
                for _ in range(max(3, w // 18)):
                    x = self.rng.uniform(4, w - 5)
                    nodes.append((x, y + self.rng.uniform(-1.5, 1.5)))
        else:
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

        for idx, node in enumerate(self.nodes):
            distances = []
            for jdx, other in enumerate(self.nodes):
                if idx == jdx:
                    continue
                dx = node[0] - other[0]
                dy = node[1] - other[1]
                distances.append((dx * dx + dy * dy, jdx))
            distances.sort(key=lambda item: item[0])
            keep = 2 if self.config.storm_mode else 3
            if self.config.cathedral_mode:
                keep = 4
            for _, jdx in distances[:keep]:
                edge = tuple(sorted((idx, jdx)))
                edges.add(edge)

        if self.config.ring_mode:
            for idx in range(len(self.nodes) - 1):
                edges.add(tuple(sorted((idx, (idx + 1) % (len(self.nodes) - 1)))))
                edges.add(tuple(sorted((idx, len(self.nodes) - 1))))

        if self.config.galaxy_mode:
            center_idx = len(self.nodes) - 1
            for idx in range(len(self.nodes) - 2):
                if idx + 3 < len(self.nodes) - 1:
                    edges.add(tuple(sorted((idx, idx + 3))))
                if idx % 4 == 0:
                    edges.add(tuple(sorted((idx, center_idx))))

        if self.config.black_hole_mode:
            center_idx = len(self.nodes) - 1
            ring_nodes = max(1, len(self.nodes) - 1)
            for idx in range(ring_nodes):
                edges.add(tuple(sorted((idx, (idx + 1) % ring_nodes))))
                if idx % 2 == 0:
                    edges.add(tuple(sorted((idx, center_idx))))

        if self.config.root_mode:
            for idx in range(len(self.nodes) - 3):
                edges.add(tuple(sorted((idx, idx + 1))))
                if idx + 3 < len(self.nodes) and idx % 2 == 0:
                    edges.add(tuple(sorted((idx, idx + 3))))

        self.edges = sorted(edges)

    def _step_intensity(self) -> None:
        """Animate intensity multiplier toward target."""
        if abs(self.intensity_multiplier - self._intensity_target) > 0.01:
            diff = self._intensity_target - self.intensity_multiplier
            self.intensity_multiplier += diff * self._intensity_rate
        else:
            self.intensity_multiplier = self._intensity_target

    def _step_node_animation(self) -> None:
        """Animate nodes for black hole spinning effect."""
        if not self.config.black_hole_mode or not self.nodes:
            return
        
        cx = self.width / 2.0
        cy = self.height / 2.0
        
        # Animate inner ring (fastest rotation)
        inner_count = 8
        for i in range(min(inner_count, len(self.nodes))):
            dx = self.nodes[i][0] - cx
            dy = self.nodes[i][1] - cy
            radius = math.hypot(dx, dy)
            angle = math.atan2(dy, dx)
            # Fast rotation for event horizon
            angle += 0.08  # ~4.5 degrees per frame
            self.nodes[i] = (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)
        
        # Animate middle ring (medium rotation)
        mid_start = inner_count
        mid_count = max(12, (len(self.nodes) - inner_count - 1) // 2)
        for i in range(mid_start, min(mid_start + mid_count, len(self.nodes) - 1)):
            dx = self.nodes[i][0] - cx
            dy = self.nodes[i][1] - cy
            radius = math.hypot(dx, dy)
            angle = math.atan2(dy, dx)
            # Medium rotation for accretion disk
            angle += 0.04  # ~2.3 degrees per frame
            self.nodes[i] = (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)
        
        # Animate outer ring (slowest rotation)
        outer_start = mid_start + mid_count
        for i in range(outer_start, len(self.nodes) - 1):
            dx = self.nodes[i][0] - cx
            dy = self.nodes[i][1] - cy
            radius = math.hypot(dx, dy)
            angle = math.atan2(dy, dx)
            # Slow rotation for outer ring
            angle += 0.02  # ~1.1 degrees per frame
            self.nodes[i] = (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)

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
            self._intensity_rate = 0.15  # fast ramp up

        elif effect == "cool_down":
            self._intensity_target = 0.3
            self._intensity_rate = 0.05  # slow fade

        elif effect == "dim":
            self.intensity_multiplier = max(0.2, self.intensity_multiplier - 0.2)
            self._intensity_target = 0.6  # recover to base
            self._intensity_rate = 0.08

    def step(self) -> None:
        self._step_intensity()
        self.frame += 1
        self._step_node_animation()
        self._step_stars()
        self._spawn_packets()
        self._step_packets()
        self._spawn_particles()
        self._step_particles()
        self._step_pulses()

    def _step_stars(self) -> None:
        drift = self.config.star_drift
        for star in self.stars:
            if self.config.galaxy_mode:
                cx = self.width / 2.0
                cy = self.height / 2.0
                dx = star[0] - cx
                dy = star[1] - cy
                radius = max(1.0, math.hypot(dx, dy))
                angle = math.atan2(dy, dx) + 0.0045 * star[2] / max(1.0, radius * 0.08)
                radius = radius * (0.9996 + math.sin(self.frame * 0.01 + star[3]) * 0.0008)
                star[0] = cx + math.cos(angle) * radius
                star[1] = cy + math.sin(angle) * radius
            elif self.config.black_hole_mode:
                cx = self.width / 2.0
                cy = self.height / 2.0
                dx = star[0] - cx
                dy = star[1] - cy
                radius = math.hypot(dx, dy)
                angle = math.atan2(dy, dx) + 0.010 * star[2]
                radius = radius * (0.996 - 0.0015 * star[2])
                if radius < 3.0:
                    reset_angle = self.rng.uniform(0, math.tau)
                    reset_radius = min(self.width, self.height) * self.rng.uniform(0.34, 0.48)
                    star[0] = cx + math.cos(reset_angle) * reset_radius * 1.8
                    star[1] = cy + math.sin(reset_angle) * reset_radius * 0.6
                    continue
                star[0] = cx + math.cos(angle) * radius * 1.15
                star[1] = cy + math.sin(angle) * radius * 0.42
            else:
                star[0] -= drift * star[2]
            if self.config.storm_mode:
                star[0] -= 0.08 * star[2]
            if star[0] < 0:
                star[0] = self.width - 2
                star[1] = self.rng.uniform(1, max(2, self.height - 2))
            elif star[0] >= self.width - 1 or star[1] < 1 or star[1] >= self.height - 1:
                star[0] = self.rng.uniform(1, max(2, self.width - 2))
                star[1] = self.rng.uniform(1, max(2, self.height - 2))
            if self.config.glass_mode:
                star[1] += math.sin(self.frame * 0.03 + star[0] * 0.1) * 0.02

    def _spawn_packets(self) -> None:
        if not self.edges:
            return
        packet_budget = 6 if self.config.hybrid_mode else 4
        if self.config.galaxy_mode:
            packet_budget = 5
        elif self.config.black_hole_mode:
            packet_budget = 3
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

        base_chance = 0.05 if self.config.storm_mode else 0.028
        if self.config.galaxy_mode:
            base_chance = 0.022
        elif self.config.black_hole_mode:
            base_chance = 0.018
        if self.rng.random() > base_chance:
            return

        if self.config.storm_mode:
            x = self.rng.uniform(2, max(3, self.width - 3))
            y = self.rng.uniform(1, max(2, self.height / 2))
            vx = self.rng.uniform(-0.10, 0.10)
            vy = self.rng.uniform(0.12, 0.26)
            char = self.rng.choice("'|/\\")
        elif self.config.root_mode:
            x = self.width / 2 + self.rng.uniform(-4, 4)
            y = self.height - 3
            vx = self.rng.uniform(-0.12, 0.12)
            vy = self.rng.uniform(-0.22, -0.08)
            char = self.rng.choice(",.;`")
        elif self.config.galaxy_mode:
            angle = self.rng.uniform(0, math.tau)
            radius = min(self.width, self.height) * self.rng.uniform(0.10, 0.26)
            x = self.width / 2 + math.cos(angle) * radius
            y = self.height / 2 + math.sin(angle) * radius
            speed = self.rng.uniform(0.025, 0.06)
            vx = -math.sin(angle) * speed
            vy = math.cos(angle) * speed
            char = self.rng.choice(".:*")
        elif self.config.black_hole_mode:
            angle = self.rng.uniform(0, math.tau)
            radius = min(self.width, self.height) * self.rng.uniform(0.18, 0.34)
            x = self.width / 2 + math.cos(angle) * radius * 1.6
            y = self.height / 2 + math.sin(angle) * radius * 0.48
            vx = -math.cos(angle) * self.rng.uniform(0.04, 0.08)
            vy = -math.sin(angle) * self.rng.uniform(0.02, 0.05)
            char = self.rng.choice(".:·")
        else:
            x, y = self.rng.choice(self.nodes)
            vx = self.rng.uniform(-0.14, 0.14)
            vy = self.rng.uniform(-0.10, 0.10)
            char = self.rng.choice(".:*+")

        life = self.rng.randint(7, 14)
        if self.config.galaxy_mode:
            life = self.rng.randint(8, 16)
        elif self.config.black_hole_mode:
            life = self.rng.randint(6, 12)
        self.particles.append(Particle(x, y, vx, vy, life, life, char))

    def _step_particles(self) -> None:
        next_particles: List[Particle] = []
        for particle in self.particles:
            if particle.step():
                if 0 <= particle.x < self.width and 0 <= particle.y < self.height:
                    next_particles.append(particle)
        self.particles = next_particles[-64:]

    def _step_pulses(self) -> None:
        next_pulses = []
        for x, y, radius in self.pulses:
            growth = 0.28
            limit = max(self.width, self.height) * 0.16
            if self.config.storm_mode:
                growth = 0.34
                limit = max(self.width, self.height) * 0.18
            elif self.config.galaxy_mode:
                growth = 0.24
                limit = max(self.width, self.height) * 0.14
            elif self.config.black_hole_mode:
                growth = 0.18
                limit = max(self.width, self.height) * 0.10
            radius += growth
            if radius < limit:
                next_pulses.append((x, y, radius))
        self.pulses = next_pulses[-10:]
