"""Physarum polycephalum (slime mold) simulation."""
from __future__ import annotations
import math
import random
from typing import Optional, Tuple

class PhysarumSim:
    """Slime mold agents deposit trails, creating organic networks."""
    
    def __init__(self, w: int, h: int, n_agents: int = 150,
                 sensor_dist: float = 4.0, sensor_angle: float = 0.785,
                 deposit: float = 1.0, decay: float = 0.95):
        self.w = w
        self.h = h
        self.deposit = deposit
        self.decay = decay
        self.sensor_dist = sensor_dist
        self.sensor_angle = sensor_angle
        self._rng = random.Random()
        # Trail grid (float values 0.0 - 5.0)
        self.trails = [[0.0] * w for _ in range(h)]
        # Agents: (x, y, angle)
        self.agents = []
        for _ in range(n_agents):
            self.agents.append([
                self._rng.uniform(0, w - 1),
                self._rng.uniform(0, h - 1),
                self._rng.uniform(0, math.tau),
            ])
    
    def add_food(self, x: int, y: int, radius: int = 3, amount: float = 5.0) -> None:
        """Place food (strong trail) to attract agents."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx = int(x + dx) % self.w
                ny = int(y + dy) % self.h
                dist = math.sqrt(dx*dx + dy*dy)
                if dist <= radius:
                    self.trails[ny][nx] = min(5.0, self.trails[ny][nx] + amount * (1.0 - dist/radius))
    
    def step(self) -> None:
        # Move agents
        for agent in self.agents:
            ax, ay, angle = agent
            # Sense: check trail concentration at 3 sensor positions
            best_angle = angle
            best_val = -1.0
            for da in (-self.sensor_angle, 0.0, self.sensor_angle):
                sa = angle + da
                sx = int(round(ax + math.cos(sa) * self.sensor_dist)) % self.w
                sy = int(round(ay + math.sin(sa) * self.sensor_dist)) % self.h
                val = self.trails[sy][sx]
                if val > best_val:
                    best_val = val
                    best_angle = sa
            # Rotate toward best + small random jitter
            agent[2] = best_angle + self._rng.uniform(-0.2, 0.2)
            # Move forward
            agent[0] = (ax + math.cos(agent[2]) * 1.0) % self.w
            agent[1] = (ay + math.sin(agent[2]) * 1.0) % self.h
            # Deposit trail
            ix, iy = int(agent[0]) % self.w, int(agent[1]) % self.h
            self.trails[iy][ix] = min(5.0, self.trails[iy][ix] + self.deposit)
        
        # Decay trails
        for y in range(self.h):
            for x in range(self.w):
                self.trails[y][x] *= self.decay
                if self.trails[y][x] < 0.01:
                    self.trails[y][x] = 0.0
    
    def render_char(self, x: int, y: int) -> Optional[Tuple[str, str]]:
        val = self.trails[y][x]
        if val < 0.1:
            return None
        if val > 3.0: return ('▓', 'bright')
        if val > 1.5: return ('▒', 'accent')
        if val > 0.5: return ('░', 'soft')
        return ('·', 'base')
