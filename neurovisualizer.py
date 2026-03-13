#!/usr/bin/env python3
"""Curses-based ASCII animation gallery for Hermes-Agent visualizer themes.

Run a single theme:
    python3 neurovisualizer.py --theme neural-sky

Run the full gallery:
    python3 neurovisualizer.py --gallery

Non-interactive verification for CI/local checks:
    python3 neurovisualizer.py --theme storm-core --seconds 5
"""

from __future__ import annotations

import argparse
import curses
import math
import random
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

THEMES: Tuple[str, ...] = (
    "neural-sky",
    "electric-mycelium",
    "cathedral-circuit",
    "storm-core",
    "hybrid",
    "moonwire",
    "rootsong",
    "stormglass",
    "spiral-galaxy",
    "black-hole",
)

FRAME_DELAY = 0.05
DEFAULT_THEME_SECONDS = 8.0
STAR_CHARS = ".·*+"
PACKET_CHARS = "o*+x"
PULSE_CHARS = ".:oO@"


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
class ThemeConfig:
    name: str
    title: str
    accent_char: str
    background_density: float
    star_drift: float
    node_jitter: float
    packet_rate: float
    packet_speed: Tuple[float, float]
    pulse_rate: float
    edge_bias: float
    cluster_count: int
    ring_mode: bool = False
    storm_mode: bool = False
    root_mode: bool = False
    cathedral_mode: bool = False
    glass_mode: bool = False
    moon_mode: bool = False
    hybrid_mode: bool = False
    galaxy_mode: bool = False
    black_hole_mode: bool = False
    palette: Tuple[int, int, int, int] = (curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_MAGENTA)


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
            arms = 4
            disc_radius = min(usable_w, usable_h) * 0.42
            core_nodes = max(5, count // 5)
            for i in range(count):
                arm = i % arms
                ratio = i / max(1, count - 1)
                base_angle = arm * (math.tau / arms)
                twist = ratio * math.tau * 1.15
                angle = base_angle + twist + self.rng.uniform(-0.16, 0.16)
                radius = disc_radius * (0.10 + ratio * 0.92)
                radius *= self.rng.uniform(0.88, 1.08)
                x = cx + math.cos(angle) * radius + self.rng.uniform(-0.7, 0.7)
                y = cy + math.sin(angle) * radius + self.rng.uniform(-0.7, 0.7)
                nodes.append((x, y))
            for i in range(core_nodes):
                angle = (math.tau * i) / core_nodes
                radius = disc_radius * self.rng.uniform(0.02, 0.12)
                nodes.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
            nodes.append((cx, cy))
        elif self.config.black_hole_mode:
            ring_count = max(12, count)
            radius_x = usable_w * 0.20
            radius_y = usable_h * 0.24
            for i in range(ring_count):
                a = (math.tau * i) / ring_count
                wobble = 1.0 + math.sin(i * 0.9) * 0.10
                nodes.append((cx + math.cos(a) * radius_x * wobble, cy + math.sin(a) * radius_y * wobble))
            for i in range(max(6, ring_count // 3)):
                a = (math.tau * i) / max(1, ring_count // 3) + 0.4
                nodes.append((cx + math.cos(a) * radius_x * 1.55, cy + math.sin(a) * radius_y * 0.65))
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

    def step(self) -> None:
        self.frame += 1
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


class Renderer:
    def __init__(self, stdscr: "curses._CursesWindow") -> None:
        self.stdscr = stdscr
        self.color_pairs = self._init_colors()

    def _init_colors(self) -> Dict[str, int]:
        pairs = {
            "base": 0,
            "soft": 0,
            "bright": 0,
            "accent": 0,
            "warning": 0,
        }
        if not curses.has_colors():
            return pairs

        curses.start_color()
        curses.use_default_colors()
        palette = [
            (1, curses.COLOR_BLUE, -1),
            (2, curses.COLOR_CYAN, -1),
            (3, curses.COLOR_WHITE, -1),
            (4, curses.COLOR_MAGENTA, -1),
            (5, curses.COLOR_YELLOW, -1),
        ]
        for pair_id, fg, bg in palette:
            try:
                curses.init_pair(pair_id, fg, bg)
            except curses.error:
                pass
        pairs.update({"base": 1, "soft": 2, "bright": 3, "accent": 4, "warning": 5})
        return pairs

    def draw(self, state: ThemeState, gallery_index: int, gallery_total: int, end_time: Optional[float]) -> None:
        stdscr = self.stdscr
        h, w = stdscr.getmaxyx()
        state.resize(w, h)
        stdscr.erase()

        self._draw_stars(state)
        self._draw_edges(state)
        self._draw_pulses(state)
        self._draw_nodes(state)
        self._draw_packets(state)
        self._draw_particles(state)
        self._draw_overlay(state, gallery_index, gallery_total, end_time)
        stdscr.refresh()

    def _draw_stars(self, state: ThemeState) -> None:
        attr = curses.color_pair(self.color_pairs["base"]) | curses.A_DIM
        if state.config.moon_mode or state.config.glass_mode:
            attr = curses.color_pair(self.color_pairs["soft"]) | curses.A_DIM
        for x, y, brightness, char_idx in state.stars:
            glyph = STAR_CHARS[min(len(STAR_CHARS) - 1, char_idx)]
            if state.config.galaxy_mode and brightness > 0.75:
                glyph = "✦"
            elif state.config.black_hole_mode and brightness > 0.7:
                glyph = "·"
            try:
                self.stdscr.addstr(int(y), int(x), glyph, attr if brightness < 0.8 else curses.color_pair(self.color_pairs["soft"]))
            except curses.error:
                pass

        if state.config.black_hole_mode:
            cx = max(2, state.width // 2)
            cy = max(2, state.height // 2)
            disk = ((cx - 2, cy, "(( "), (cx + 1, cy, "))"), (cx - 1, cy, "██"))
            for x, y, text in disk:
                try:
                    self.stdscr.addstr(y, x, text, curses.color_pair(self.color_pairs["warning"]))
                except curses.error:
                    pass

        if state.config.moon_mode:
            moon_x = max(3, state.width - 10)
            moon_y = 2
            moon = ((moon_x, moon_y, "◜◝"), (moon_x, moon_y + 1, "◟◞"))
            for x, y, text in moon:
                try:
                    self.stdscr.addstr(y, x, text, curses.color_pair(self.color_pairs["bright"]))
                except curses.error:
                    pass

    def _draw_edges(self, state: ThemeState) -> None:
        for idx_a, idx_b in state.edges:
            ax, ay = self._node_position(state, idx_a)
            bx, by = self._node_position(state, idx_b)
            dx = bx - ax
            dy = by - ay
            steps = max(abs(int(dx)), abs(int(dy)), 1)
            for step in range(1, steps):
                t = step / steps
                x = int(round(ax + dx * t))
                y = int(round(ay + dy * t))
                glyph = self._edge_glyph(dx, dy, state.config)
                attr = curses.color_pair(self.color_pairs["base"]) | curses.A_DIM
                if state.config.cathedral_mode:
                    attr = curses.color_pair(self.color_pairs["soft"])
                elif state.config.storm_mode:
                    attr = curses.color_pair(self.color_pairs["accent"]) if (step + state.frame) % 9 == 0 else attr
                elif state.config.glass_mode:
                    attr = curses.color_pair(self.color_pairs["bright"]) if (x + y + state.frame) % 13 == 0 else curses.color_pair(self.color_pairs["soft"])
                elif state.config.galaxy_mode:
                    attr = curses.color_pair(self.color_pairs["soft"]) if (step + idx_a) % 5 else curses.color_pair(self.color_pairs["accent"])
                elif state.config.black_hole_mode:
                    attr = curses.color_pair(self.color_pairs["warning"]) if step % 6 == 0 else curses.color_pair(self.color_pairs["base"])
                try:
                    self.stdscr.addstr(y, x, glyph, attr)
                except curses.error:
                    pass

    def _draw_nodes(self, state: ThemeState) -> None:
        for idx, _ in enumerate(state.nodes):
            x, y = self._node_position(state, idx)
            intensity = 0.5 + 0.5 * math.sin(state.frame * 0.12 + idx * 0.6)
            glyph = "●" if intensity > 0.72 else "•"
            if state.config.cathedral_mode:
                glyph = "✦" if idx % 5 == 0 else "◆"
            elif state.config.root_mode:
                glyph = "◉" if idx % 3 == 0 else "•"
            elif state.config.storm_mode:
                glyph = "◌" if intensity < 0.5 else "◉"
            elif state.config.galaxy_mode:
                glyph = "✦" if idx % 6 == 0 else "•"
            elif state.config.black_hole_mode:
                glyph = "◍" if idx == len(state.nodes) - 1 else "•"
            attr = curses.color_pair(self.color_pairs["bright"] if intensity > 0.65 else self.color_pairs["soft"])
            if state.config.hybrid_mode and idx % 4 == 0:
                attr = curses.color_pair(self.color_pairs["accent"])
            elif state.config.galaxy_mode and idx % 5 == 0:
                attr = curses.color_pair(self.color_pairs["accent"])
            elif state.config.black_hole_mode:
                attr = curses.color_pair(self.color_pairs["warning"] if idx == len(state.nodes) - 1 else self.color_pairs["soft"])
            try:
                self.stdscr.addstr(y, x, glyph, attr)
            except curses.error:
                pass

    def _draw_packets(self, state: ThemeState) -> None:
        for packet in state.packets:
            ax, ay = self._node_position(state, packet.edge[0])
            bx, by = self._node_position(state, packet.edge[1])
            x = int(round(ax + (bx - ax) * packet.progress))
            y = int(round(ay + (by - ay) * packet.progress))
            attr = curses.color_pair(self.color_pairs["accent"]) | curses.A_BOLD
            if state.config.moon_mode:
                attr = curses.color_pair(self.color_pairs["bright"])
            elif state.config.black_hole_mode:
                attr = curses.color_pair(self.color_pairs["warning"])
            try:
                self.stdscr.addstr(y, x, packet.glyph, attr)
            except curses.error:
                pass

    def _draw_particles(self, state: ThemeState) -> None:
        for particle in state.particles:
            x = int(round(particle.x))
            y = int(round(particle.y))
            if not (0 <= x < state.width and 0 <= y < state.height):
                continue
            attr = curses.color_pair(self.color_pairs["soft"]) | curses.A_DIM
            if particle.age_ratio > 0.6:
                attr = curses.color_pair(self.color_pairs["accent"])
            if state.config.black_hole_mode:
                attr = curses.color_pair(self.color_pairs["warning"] if particle.age_ratio > 0.55 else self.color_pairs["base"])
            try:
                self.stdscr.addstr(y, x, particle.char, attr)
            except curses.error:
                pass

    def _draw_pulses(self, state: ThemeState) -> None:
        for x, y, radius in state.pulses:
            points = self._ring_points(x, y, radius)
            for px, py, glyph in points:
                attr = curses.color_pair(self.color_pairs["soft"]) | curses.A_DIM
                if state.config.storm_mode:
                    attr = curses.color_pair(self.color_pairs["warning"])
                elif state.config.glass_mode:
                    attr = curses.color_pair(self.color_pairs["bright"])
                elif state.config.galaxy_mode:
                    attr = curses.color_pair(self.color_pairs["accent"])
                elif state.config.black_hole_mode:
                    attr = curses.color_pair(self.color_pairs["base"])
                try:
                    self.stdscr.addstr(py, px, glyph, attr)
                except curses.error:
                    pass

    def _draw_overlay(self, state: ThemeState, gallery_index: int, gallery_total: int, end_time: Optional[float]) -> None:
        title = f" Hermes visualizer // {state.config.name} "
        footer = " q quit  n next  p prev  space pause "
        if gallery_total > 1:
            footer = f" theme {gallery_index + 1}/{gallery_total} |" + footer
        if end_time is not None:
            remaining = max(0.0, end_time - time.time())
            footer += f" | auto-exit {remaining:0.1f}s "

        try:
            self.stdscr.addstr(0, 1, title[: max(0, state.width - 2)], curses.color_pair(self.color_pairs["bright"]) | curses.A_BOLD)
        except curses.error:
            pass
        try:
            self.stdscr.addstr(state.height - 1, 1, footer[: max(0, state.width - 2)], curses.color_pair(self.color_pairs["soft"]))
        except curses.error:
            pass

    def _node_position(self, state: ThemeState, idx: int) -> Tuple[int, int]:
        x, y = state.nodes[idx]
        jitter = state.config.node_jitter
        xf = x + math.sin(state.frame * 0.05 + idx * 0.9) * jitter
        yf = y + math.cos(state.frame * 0.04 + idx * 1.1) * jitter * 0.6
        if state.config.storm_mode:
            yf += math.sin(state.frame * 0.08 + idx * 0.5) * 0.8
        if state.config.glass_mode:
            xf += math.sin(state.frame * 0.03 + y * 0.2) * 0.5
        if state.config.galaxy_mode:
            cx = state.width / 2.0
            cy = state.height / 2.0
            dx = x - cx
            dy = y - cy
            radius = max(0.8, math.hypot(dx, dy))
            angle = math.atan2(dy, dx) + 0.008 / max(0.6, radius * 0.06) + idx * 0.0005
            xf = cx + math.cos(angle) * radius
            yf = cy + math.sin(angle) * radius
        elif state.config.black_hole_mode:
            cx = state.width / 2.0
            cy = state.height / 2.0
            dx = x - cx
            dy = y - cy
            angle = math.atan2(dy, dx) + 0.015
            radius = max(1.5, math.hypot(dx, dy) * (0.9985 - idx * 0.00002))
            xf = cx + math.cos(angle) * radius * 1.1
            yf = cy + math.sin(angle) * radius * 0.45
        return int(max(1, min(state.width - 2, round(xf)))), int(max(1, min(state.height - 2, round(yf))))

    @staticmethod
    def _edge_glyph(dx: float, dy: float, config: ThemeConfig) -> str:
        if config.root_mode:
            return "│" if abs(dy) > abs(dx) else "╱" if dx * dy < 0 else "╲"
        if config.cathedral_mode:
            return "║" if abs(dy) > abs(dx) else "═"
        if config.galaxy_mode:
            return "·" if abs(dy) < abs(dx) * 0.35 else "╱" if dx * dy < 0 else "╲"
        if config.black_hole_mode:
            return "~" if abs(dy) < abs(dx) * 0.35 else "(" if dx * dy < 0 else ")"
        if abs(dy) < abs(dx) * 0.35:
            return "─"
        if abs(dx) < abs(dy) * 0.45:
            return "│"
        return "╱" if dx * dy < 0 else "╲"

    @staticmethod
    def _ring_points(cx: float, cy: float, radius: float) -> Iterable[Tuple[int, int, str]]:
        if radius < 1.2:
            yield int(round(cx)), int(round(cy)), PULSE_CHARS[2]
            return
        steps = max(8, int(radius * 8))
        glyph = PULSE_CHARS[min(len(PULSE_CHARS) - 1, int(radius) % len(PULSE_CHARS))]
        for step in range(steps):
            angle = math.tau * step / steps
            x = int(round(cx + math.cos(angle) * radius * 2.0))
            y = int(round(cy + math.sin(angle) * radius))
            yield x, y, glyph


def build_theme_config(name: str) -> ThemeConfig:
    configs = {
        "neural-sky": ThemeConfig(name, "Neural Sky", "*", 0.030, 0.10, 0.40, 0.32, (0.04, 0.08), 0.10, 0.4, 3, palette=(curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_MAGENTA)),
        "electric-mycelium": ThemeConfig(name, "Electric Mycelium", "o", 0.020, 0.05, 0.18, 0.40, (0.05, 0.10), 0.12, 0.55, 4, palette=(curses.COLOR_GREEN, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "cathedral-circuit": ThemeConfig(name, "Cathedral Circuit", "#", 0.015, 0.03, 0.08, 0.24, (0.03, 0.06), 0.07, 0.70, 2, cathedral_mode=True, palette=(curses.COLOR_BLUE, curses.COLOR_WHITE, curses.COLOR_CYAN, curses.COLOR_MAGENTA)),
        "storm-core": ThemeConfig(name, "Storm Core", "x", 0.024, 0.18, 0.52, 0.42, (0.06, 0.10), 0.12, 0.35, 3, storm_mode=True, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "hybrid": ThemeConfig(name, "Hybrid", "@", 0.028, 0.11, 0.28, 0.38, (0.05, 0.09), 0.12, 0.50, 4, hybrid_mode=True, palette=(curses.COLOR_CYAN, curses.COLOR_MAGENTA, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
        "moonwire": ThemeConfig(name, "Moonwire", "•", 0.026, 0.04, 0.16, 0.20, (0.02, 0.05), 0.07, 0.48, 2, ring_mode=True, moon_mode=True, palette=(curses.COLOR_WHITE, curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_MAGENTA)),
        "rootsong": ThemeConfig(name, "Rootsong", ":", 0.014, 0.02, 0.14, 0.28, (0.03, 0.06), 0.10, 0.66, 2, root_mode=True, palette=(curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_WHITE, curses.COLOR_CYAN)),
        "stormglass": ThemeConfig(name, "Stormglass", "+", 0.032, 0.08, 0.30, 0.34, (0.04, 0.08), 0.12, 0.58, 3, glass_mode=True, palette=(curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_BLUE, curses.COLOR_MAGENTA)),
        "spiral-galaxy": ThemeConfig(name, "Spiral Galaxy", "✦", 0.040, 0.00, 0.10, 0.26, (0.02, 0.05), 0.07, 0.62, 3, galaxy_mode=True, palette=(curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_MAGENTA)),
        "black-hole": ThemeConfig(name, "Black Hole", "·", 0.036, 0.00, 0.06, 0.18, (0.02, 0.04), 0.05, 0.74, 2, black_hole_mode=True, palette=(curses.COLOR_BLUE, curses.COLOR_MAGENTA, curses.COLOR_WHITE, curses.COLOR_YELLOW)),
    }
    return configs[name]


class GalleryApp:
    def __init__(self, stdscr: "curses._CursesWindow", themes: Sequence[str], theme_seconds: float, end_after: Optional[float]) -> None:
        self.stdscr = stdscr
        self.themes = list(themes)
        self.theme_seconds = max(1.0, theme_seconds)
        self.end_after = end_after
        self.renderer = Renderer(stdscr)
        self.theme_index = 0
        self.paused = False
        self.state = self._make_state(self.themes[self.theme_index])
        self.switch_at = time.time() + self.theme_seconds if len(self.themes) > 1 else float("inf")

    def _make_state(self, theme_name: str) -> ThemeState:
        h, w = self.stdscr.getmaxyx()
        return ThemeState(build_theme_config(theme_name), w, h, seed=(hash(theme_name) & 0xFFFF))

    def run(self) -> None:
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.timeout(0)

        deadline = time.time() + self.end_after if self.end_after is not None else None
        while True:
            now = time.time()
            if deadline is not None and now >= deadline:
                break

            self._handle_input()
            if not self.paused:
                self.state.step()
                if len(self.themes) > 1 and now >= self.switch_at:
                    self._advance_theme(1)
            self.renderer.draw(self.state, self.theme_index, len(self.themes), deadline)
            time.sleep(FRAME_DELAY)

    def _advance_theme(self, direction: int) -> None:
        self.theme_index = (self.theme_index + direction) % len(self.themes)
        self.state = self._make_state(self.themes[self.theme_index])
        self.switch_at = time.time() + self.theme_seconds

    def _handle_input(self) -> None:
        while True:
            ch = self.stdscr.getch()
            if ch == -1:
                return
            if ch in (ord("q"), ord("Q")):
                raise SystemExit(0)
            if ch in (ord("n"), curses.KEY_RIGHT):
                self._advance_theme(1)
            elif ch in (ord("p"), curses.KEY_LEFT):
                self._advance_theme(-1)
            elif ch == ord(" "):
                self.paused = not self.paused


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hermes-Agent ASCII visualizer gallery")
    parser.add_argument("--theme", choices=THEMES, help="Run a single named theme")
    parser.add_argument("--gallery", action="store_true", help="Cycle through all themes")
    parser.add_argument("--theme-seconds", type=float, default=DEFAULT_THEME_SECONDS, help="Seconds per theme in gallery mode")
    parser.add_argument("--seconds", type=float, default=None, help="Auto-exit after N seconds for local verification")
    return parser.parse_args()


def main(stdscr: "curses._CursesWindow", args: argparse.Namespace) -> None:
    if args.theme:
        themes = [args.theme]
    elif args.gallery or not args.theme:
        themes = list(THEMES)
    else:
        themes = list(THEMES)
    app = GalleryApp(stdscr, themes, args.theme_seconds, args.seconds)
    app.run()


def run_headless(args: argparse.Namespace) -> int:
    if args.theme:
        themes = [args.theme]
    else:
        themes = list(THEMES)
    total_seconds = args.seconds if args.seconds is not None else max(2.0, args.theme_seconds * len(themes))
    frame_count = max(1, int(total_seconds / FRAME_DELAY))
    width, height = 100, 30
    state = ThemeState(build_theme_config(themes[0]), width, height, seed=(hash(themes[0]) & 0xFFFF))
    theme_index = 0
    next_switch = max(1, int(args.theme_seconds / FRAME_DELAY))

    for frame in range(frame_count):
        if len(themes) > 1 and frame > 0 and frame % next_switch == 0:
            theme_index = (theme_index + 1) % len(themes)
            state = ThemeState(build_theme_config(themes[theme_index]), width, height, seed=(hash(themes[theme_index]) & 0xFFFF))
        state.step()

    print(
        "headless verification complete | "
        f"theme={themes[theme_index]} frames={frame_count} nodes={len(state.nodes)} "
        f"edges={len(state.edges)} packets={len(state.packets)} particles={len(state.particles)} pulses={len(state.pulses)}"
    )
    return 0


if __name__ == "__main__":
    arguments = parse_args()
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise SystemExit(run_headless(arguments))
    curses.wrapper(lambda stdscr: main(stdscr, arguments))
