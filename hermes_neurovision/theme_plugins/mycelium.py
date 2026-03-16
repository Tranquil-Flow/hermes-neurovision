"""
mycelium-pulse — a living fungal network that grows, branches, and breathes.

Growth tips wander the terminal leaving density trails. Older filaments fade
slowly. Busy intersection nodes glow hot. Agent events trigger spore bursts
that seed new growth fronts from random positions.

Archetype: density accumulator + simulation (hybrid of both).
Layer: draw_extras only (no graph layer).
"""
from __future__ import annotations

import math
import random
import curses
from typing import List

from hermes_neurovision.plugin import ThemePlugin, ReactiveElement, Reaction
from hermes_neurovision.sound import SoundCue
from hermes_neurovision.theme_plugins import register


# ── helpers ──────────────────────────────────────────────────────────────────

def _safe(stdscr, y, x, ch, attr):
    try:
        stdscr.addstr(y, x, ch, attr)
    except curses.error:
        pass


# ── tip ──────────────────────────────────────────────────────────────────────

class Tip:
    """A single growth tip wandering the grid."""

    # 12 directions, x-doubled to compensate for character aspect ratio (~2:1)
    DIRS = [
        ( 2,  0), ( 2,  1), ( 1,  1), ( 0,  1),
        (-1,  1), (-2,  1), (-2,  0), (-2, -1),
        (-1, -1), ( 0, -1), ( 1, -1), ( 2, -1),
    ]

    def __init__(self, x: float, y: float, angle_idx: int,
                 rng: random.Random, energy: float = 1.0):
        self.x = x
        self.y = y
        self.angle = angle_idx
        self.rng = rng
        self.energy = energy
        self.age = 0
        self.branch_cooldown = 0

    def step(self, w: int, h: int, grid: list, intensity: float) -> "List[Tip]":
        """Advance one step. Returns list of newly spawned branch tips."""
        if self.energy <= 0:
            return []

        self.age += 1
        self.branch_cooldown = max(0, self.branch_cooldown - 1)

        # Biased random walk — mostly straight, small random drift
        r = self.rng.random()
        if r < 0.52:
            pass                              # straight
        elif r < 0.70:
            self.angle = (self.angle + 1) % 12
        elif r < 0.88:
            self.angle = (self.angle - 1) % 12
        elif r < 0.94:
            self.angle = (self.angle + 2) % 12
        else:
            self.angle = (self.angle - 2) % 12

        dx, dy = self.DIRS[self.angle]
        self.x += dx
        self.y += dy

        # Wrap horizontally, bounce vertically
        self.x = self.x % (w - 1)
        if self.y <= 1.0 or self.y >= h - 2.0:
            self.y = max(1.5, min(h - 2.5, self.y))
            self.angle = (self.angle + 6) % 12  # reverse

        # Deposit density — capped at 0.6 so the grid stays dynamic, not solid-white
        ix, iy = int(self.x), int(self.y)
        if 0 <= ix < w and 1 <= iy < h - 1:
            grid[iy][ix] = min(grid[iy][ix] + 0.025 + 0.015 * intensity, 0.60)
            # Hair-thin side deposit for width
            if ix + 1 < w - 1:
                grid[iy][ix + 1] = min(grid[iy][ix + 1] + 0.008, 0.40)
            if ix - 1 >= 0:
                grid[iy][ix - 1] = min(grid[iy][ix - 1] + 0.008, 0.40)

        # Drain energy slowly
        self.energy -= 0.0015 + 0.0005 * self.rng.random()

        # Branching
        ix2, iy2 = int(self.x), int(self.y)
        density_here = grid[iy2][ix2] if (0 <= ix2 < w and 1 <= iy2 < h - 1) else 0.0
        branch_chance = 0.006 + 0.004 * intensity + 0.01 * density_here
        new_tips: List[Tip] = []
        if (self.branch_cooldown == 0
                and self.age > 6
                and self.energy > 0.25
                and self.rng.random() < branch_chance):
            self.branch_cooldown = 15
            fork = (self.angle + self.rng.choice([-3, -2, 2, 3])) % 12
            child = Tip(self.x, self.y, fork, self.rng, energy=self.energy * 0.65)
            child.branch_cooldown = 10
            self.energy *= 0.82
            new_tips.append(child)

        return new_tips


# ── main plugin ──────────────────────────────────────────────────────────────

class MyceliumPulsePlugin(ThemePlugin):
    """
    mycelium-pulse — fungal network grows, branches, and breathes across the
    terminal. Agent events trigger spore bursts seeding new growth fronts.
    Decay is slow: the whole history of activity accumulates as a living map.
    """

    name = "mycelium-pulse"

    # Density → character mapping (21 levels, sparse to dense)
    _CHARS = " ·˙∙•·:;╌╍─━┄┅═╦╬█"

    # Spore characters
    _SPORE_CHARS = ["∘", "○", "◦", "·", "∙", "*", "+"]

    def __init__(self):
        self._grid: list = []
        self._tips: List[Tip] = []
        self._w = self._h = 0
        self._rng = random.Random(0xF0CA1)
        self._spores: list = []   # (x, y, vx, vy, life, max_life, ch, color_key)
        self._waves: list = []    # (cx, cy, radius, max_r, color_key)
        self._shimmer_nodes: list = []  # (x, y, age, max_age)

    # ── no graph layer ───────────────────────────────────────────────────────

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    # ── init / resize ────────────────────────────────────────────────────────

    def _init(self, w: int, h: int) -> None:
        self._grid = [[0.0] * w for _ in range(h)]
        self._w, self._h = w, h
        self._tips.clear()
        self._spores.clear()
        self._waves.clear()
        self._shimmer_nodes.clear()
        # Central seed — starts the colonisation from the middle
        self._seed_cluster(w, h, n_tips=12, cx=w / 2, cy=h / 2, energy=1.0)
        # A few peripheral seeds so coverage reaches edges in reasonable time
        for ex, ey in [
            (w * 0.25, h * 0.35), (w * 0.75, h * 0.35),
            (w * 0.25, h * 0.65), (w * 0.75, h * 0.65),
        ]:
            self._seed_cluster(w, h, n_tips=3, cx=ex, cy=ey, energy=0.80)

    def _seed_cluster(self, w: int, h: int, n_tips: int,
                      cx: float, cy: float, energy: float = 1.0) -> None:
        for _ in range(n_tips):
            angle = self._rng.randint(0, 11)
            jx = cx + self._rng.uniform(-4, 4)
            jy = cy + self._rng.uniform(-2, 2)
            jx = max(2.0, min(w - 3.0, jx))
            jy = max(2.0, min(h - 3.0, jy))
            self._tips.append(Tip(jx, jy, angle, self._rng, energy=energy))

    # ── postfx defaults ──────────────────────────────────────────────────────

    def glow_radius(self):
        return 1

    def echo_decay(self):
        return 0

    def symmetry(self):
        return None

    # ── emergent: physarum reinforces the trails ─────────────────────────────

    def physarum_config(self):
        return {
            "n_agents": 120,
            "sensor_dist": 3.0,
            "sensor_angle": 0.62,
            "deposit": 0.5,
            "decay": 0.97,
        }

    def emergent_layer(self):
        return "background"

    # ── react to agent events ────────────────────────────────────────────────

    def react(self, event_kind: str, data):
        w, h = self._w or 80, self._h or 24
        cx = self._rng.uniform(w * 0.15, w * 0.85)
        cy = self._rng.uniform(h * 0.15, h * 0.85)

        if event_kind in ("agent_start", "session_resume"):
            self._seed_cluster(w, h, n_tips=16, cx=w / 2, cy=h / 2, energy=1.0)
            self._waves.append([w / 2, h / 2, 0.0, min(w, h) * 0.6, "bright"])
            return Reaction(element=ReactiveElement.PULSE, intensity=1.0,
                            origin=(0.5, 0.5), color_key="bright", duration=3.0)

        if event_kind in ("tool_call", "mcp_tool_call"):
            self._seed_cluster(w, h, n_tips=6, cx=cx, cy=cy, energy=0.85)
            self._waves.append([cx, cy, 0.0, min(w, h) * 0.35, "accent"])
            self._spore_burst(cx, cy, n=14, color="accent")
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.7,
                            origin=(cx / w, cy / h), color_key="accent", duration=1.5)

        if event_kind in ("memory_save", "skill_create", "checkpoint_created"):
            for _ in range(3):
                bx = cx + self._rng.uniform(-10, 10)
                by = cy + self._rng.uniform(-4, 4)
                self._seed_cluster(w, h, n_tips=6, cx=bx, cy=by, energy=0.95)
            self._spore_burst(cx, cy, n=24, color="bright")
            self._waves.append([cx, cy, 0.0, min(w, h) * 0.5, "bright"])
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                            origin=(cx / w, cy / h), color_key="bright", duration=3.0)

        if event_kind in ("error", "crash", "threat_blocked"):
            # Burn a hole
            ix, iy = int(cx), int(cy)
            r_burn = 8
            for dy in range(-r_burn, r_burn + 1):
                for dx_b in range(-r_burn * 2, r_burn * 2 + 1):
                    if dx_b * dx_b / 4.0 + dy * dy < r_burn * r_burn:
                        gx, gy = ix + dx_b, iy + dy
                        if 0 <= gx < w and 1 <= gy < h - 1:
                            self._grid[gy][gx] = max(0.0, self._grid[gy][gx] - 0.5)
            self._spore_burst(cx, cy, n=20, color="warning")
            self._waves.append([cx, cy, 0.0, min(w, h) * 0.4, "warning"])
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                            origin=(cx / w, cy / h), color_key="warning", duration=2.0)

        if event_kind in ("llm_start", "llm_chunk"):
            self._waves.append([w / 2, h / 2, 0.0, min(w, h) * 0.2, "soft"])
            return Reaction(element=ReactiveElement.STREAM, intensity=0.4,
                            origin=(0.0, self._rng.random()), color_key="soft",
                            duration=0.6)

        if event_kind in ("cron_tick", "background_proc", "subagent_started"):
            edge = self._rng.choice([0, 1, 2, 3])
            if edge == 0:   ex2, ey2 = self._rng.uniform(0, w), 2.0
            elif edge == 1: ex2, ey2 = self._rng.uniform(0, w), float(h - 3)
            elif edge == 2: ex2, ey2 = 2.0, self._rng.uniform(1, h - 1)
            else:           ex2, ey2 = float(w - 3), self._rng.uniform(1, h - 1)
            self._seed_cluster(w, h, n_tips=4, cx=ex2, cy=ey2, energy=0.7)
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.5,
                            origin=(ex2 / w, ey2 / h), color_key="soft", duration=2.0)

        if event_kind in ("git_commit", "file_edit", "browser_navigate"):
            self._seed_cluster(w, h, n_tips=5, cx=cx, cy=cy, energy=0.8)
            self._spore_burst(cx, cy, n=8, color="accent")
            return Reaction(element=ReactiveElement.TRAIL, intensity=0.6,
                            origin=(cx / w, cy / h), color_key="accent", duration=1.5)

        if event_kind in ("approval_request", "dangerous_cmd"):
            for _ in range(10):
                sx = self._rng.uniform(4, w - 4)
                sy = self._rng.uniform(2, h - 2)
                self._shimmer_nodes.append([sx, sy, 0, 20])
            return Reaction(element=ReactiveElement.SPARK, intensity=1.0,
                            origin=(0.5, 0.5), color_key="warning", duration=2.0)

        return None

    # ── sound cues ───────────────────────────────────────────────────────────

    def sound_cues(self):
        return {
            "agent_start":  SoundCue("myc-wake",   "say",   "spreading", volume=0.6, priority=8),
            "memory_save":  SoundCue("myc-bloom",  "say",   "rooted",    volume=0.5, priority=6),
            "error":        SoundCue("myc-snap",   "bell",  "",          volume=1.0, priority=10),
            "tool_call":    SoundCue("myc-tick",   "flash", "",          volume=0.2, priority=2),
        }

    # ── internal helpers ─────────────────────────────────────────────────────

    def _spore_burst(self, cx: float, cy: float, n: int, color: str) -> None:
        for _ in range(n):
            angle = self._rng.uniform(0, math.tau)
            speed = self._rng.uniform(0.3, 0.9)
            ch = self._rng.choice(self._SPORE_CHARS)
            life = self._rng.randint(16, 32)
            self._spores.append([
                cx, cy,
                math.cos(angle) * speed * 2,
                math.sin(angle) * speed,
                life, life, ch, color
            ])

    # ── main draw ────────────────────────────────────────────────────────────

    def draw_extras(self, stdscr, state, color_pairs):
        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier

        tune = state.tune
        spd   = tune.animation_speed    if tune else 1.0
        dense = tune.particle_density   if tune else 1.0
        dr    = tune.decay_rate         if tune else 1.0

        # Init / resize
        if not self._grid or (w, h) != (self._w, self._h):
            self._init(w, h)

        grid = self._grid
        n_chars = len(self._CHARS)

        # ── colors ───────────────────────────────────────────────────────────
        bright = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent = curses.color_pair(color_pairs["accent"])
        soft   = curses.color_pair(color_pairs["soft"])
        dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        danger = curses.color_pair(color_pairs["warning"]) | curses.A_BOLD

        color_map = {
            "bright": bright, "accent": accent, "soft": soft,
            "base": dim, "warning": danger,
        }

        # ── step growth tips ─────────────────────────────────────────────────
        # Multiple steps per frame for visible movement
        steps_per_tip = max(2, int(3 * spd))
        new_tips: List[Tip] = []
        surviving: List[Tip] = []
        for tip in self._tips:
            for _ in range(steps_per_tip):
                spawned = tip.step(w, h, grid, intensity)
                new_tips.extend(spawned)
            if tip.energy > 0:
                surviving.append(tip)
        self._tips = surviving + new_tips

        # Maintain minimum tip population
        target_tips = max(20, int(35 * dense * (0.6 + intensity * 0.6)))
        while len(self._tips) < target_tips:
            # Prefer sprouting from a dense cell so the network self-reinforces
            if self._rng.random() < 0.65:
                best_v, bx, by = 0.0, w // 2, h // 2
                for _ in range(50):
                    tx = self._rng.randint(1, w - 2)
                    ty = self._rng.randint(1, h - 2)
                    if grid[ty][tx] > best_v:
                        best_v, bx, by = grid[ty][tx], tx, ty
                if best_v > 0.03:
                    angle = self._rng.randint(0, 11)
                    self._tips.append(Tip(float(bx), float(by), angle,
                                          self._rng, energy=0.7 + 0.3 * self._rng.random()))
                    continue
            tx = self._rng.uniform(2, w - 2)
            ty = self._rng.uniform(2, h - 2)
            self._tips.append(Tip(tx, ty, self._rng.randint(0, 11),
                                  self._rng, energy=0.6))

        # Cap to prevent excessive tip accumulation
        if len(self._tips) > target_tips * 3:
            # Kill oldest/lowest-energy first
            self._tips.sort(key=lambda t: t.energy, reverse=True)
            self._tips = self._tips[:target_tips * 2]

        # ── decay + render grid ───────────────────────────────────────────────
        # Decay factor: fast enough to keep the grid dynamic and avoid saturation
        # At dr=1.0: factor ~0.985 → full fade in ~300 frames (~15s at 20fps)
        # Tips constantly re-trace paths so active routes stay bright
        decay_factor = max(0.975, 0.9875 - 0.006 * dr)

        # Breathing pulse: per-cell shimmer with spatial phase offset
        shimmer_t = f * 0.06 * spd

        for y in range(1, h - 1):
            row = grid[y]
            for x in range(0, w - 1):
                v = row[x]
                row[x] = v * decay_factor

                if v < 0.008:
                    _safe(stdscr, y, x, " ", dim)
                    continue

                # Shimmer: add breathing offset so low-density cells still pulse
                shimmer = math.sin(shimmer_t + x * 0.28 + y * 0.41) * 0.12
                v_vis = max(0.0, min(1.0, v + shimmer * intensity))

                # Character from density
                ci = min(n_chars - 1, int(v_vis * (n_chars - 1)))
                ch = self._CHARS[ci]

                # Color thresholds — matched to realistic density range (0.0 – 0.55)
                # maxV in steady state ~0.25–0.35, so bands are spaced accordingly
                if v_vis > 0.25:
                    attr = bright
                elif v_vis > 0.12:
                    attr = accent
                elif v_vis > 0.04:
                    attr = soft
                else:
                    attr = dim

                _safe(stdscr, y, x, ch, attr)

        # ── pulse waves ───────────────────────────────────────────────────────
        wave_speed = 0.8 * spd
        surviving_waves = []
        for wave in self._waves:
            wave[2] += wave_speed
            r_w, max_r, ck = wave[2], wave[3], wave[4]
            if r_w < max_r:
                surviving_waves.append(wave)
                attr = color_map.get(ck, accent)
                fade = 1.0 - r_w / max_r
                if fade > 0.2:
                    circum = max(8, int(math.pi * r_w * 1.4))
                    for i in range(circum):
                        angle = math.tau * i / circum
                        wx = int(wave[0] + math.cos(angle) * r_w)
                        wy = int(wave[1] + math.sin(angle) * r_w * 0.5)
                        if 0 < wx < w - 1 and 1 < wy < h - 2:
                            ring_ch = "◌" if ck == "bright" else "○" if ck == "accent" else "·"
                            _safe(stdscr, wy, wx, ring_ch, attr)
        self._waves = surviving_waves

        # ── spore bursts ──────────────────────────────────────────────────────
        surviving_spores = []
        for sp in self._spores:
            sp[0] += sp[2] * spd
            sp[1] += sp[3] * spd
            sp[4] -= 1
            sx2, sy2 = int(sp[0]), int(sp[1])
            if sp[4] > 0 and 0 < sx2 < w - 1 and 1 < sy2 < h - 2:
                surviving_spores.append(sp)
                age_ratio = sp[4] / max(sp[5], 1)
                attr = color_map.get(sp[7], accent) if age_ratio > 0.5 else (soft if age_ratio > 0.25 else dim)
                _safe(stdscr, sy2, sx2, sp[6], attr)
        self._spores = surviving_spores

        # ── shimmer nodes ─────────────────────────────────────────────────────
        surviving_sh = []
        for sh in self._shimmer_nodes:
            sh[2] += 1
            if sh[2] < sh[3]:
                surviving_sh.append(sh)
                flash_ch = "✦" if sh[2] % 4 < 2 else "✧"
                attr = danger if sh[2] < sh[3] // 2 else bright
                _safe(stdscr, int(sh[1]), int(sh[0]), flash_ch, attr)
        self._shimmer_nodes = surviving_sh

        # ── active tip indicators ─────────────────────────────────────────────
        # Show tip heads so you can see the live growth front moving
        for tip in self._tips[:40]:
            tx, ty = int(tip.x), int(tip.y)
            if 0 < tx < w - 1 and 1 < ty < h - 2:
                if tip.energy > 0.7:
                    _safe(stdscr, ty, tx, "◉", bright)
                elif tip.energy > 0.4:
                    _safe(stdscr, ty, tx, "●", accent)
                else:
                    _safe(stdscr, ty, tx, "·", soft)

    # ── ambient tick ──────────────────────────────────────────────────────────

    def ambient_tick(self, stdscr, state, color_pairs, idle_seconds):
        # Keep the network growing and alive during idle
        if idle_seconds > 20 and self._rng.random() < 0.04:
            w, h = state.width, state.height
            cx = self._rng.uniform(w * 0.1, w * 0.9)
            cy = self._rng.uniform(h * 0.1, h * 0.9)
            self._seed_cluster(w, h, n_tips=4, cx=cx, cy=cy, energy=0.6)


register(MyceliumPulsePlugin())
