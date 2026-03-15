"""Boids flocking simulation."""
from __future__ import annotations
import math
import random
from typing import List, Optional, Tuple

class BoidsFlock:
    """Classic separation/alignment/cohesion flocking."""
    
    def __init__(self, w: int, h: int, n_boids: int = 40,
                 sep_dist: float = 3.0, align_dist: float = 8.0,
                 cohesion_dist: float = 12.0, max_speed: float = 1.5):
        self.w = w
        self.h = h
        self.max_speed = max_speed
        self.sep_dist = sep_dist
        self.align_dist = align_dist
        self.cohesion_dist = cohesion_dist
        self._rng = random.Random()
        self._attractors: List[Tuple[float, float, int]] = []  # (x, y, ttl)
        # Boids: [x, y, vx, vy]
        self.boids = []
        for _ in range(n_boids):
            self.boids.append([
                self._rng.uniform(0, w),
                self._rng.uniform(0, h),
                self._rng.uniform(-1, 1),
                self._rng.uniform(-0.5, 0.5),
            ])
    
    def add_attractor(self, x: float, y: float, ttl: int = 60) -> None:
        self._attractors.append((x, y, ttl))
        if len(self._attractors) > 8:
            self._attractors.pop(0)
    
    def step(self) -> None:
        # Decay attractors
        self._attractors = [(x, y, t-1) for x, y, t in self._attractors if t > 1]
        
        for boid in self.boids:
            bx, by, bvx, bvy = boid
            sep_x, sep_y = 0.0, 0.0
            align_x, align_y = 0.0, 0.0
            coh_x, coh_y = 0.0, 0.0
            align_n, coh_n = 0, 0
            
            for other in self.boids:
                if other is boid:
                    continue
                dx = other[0] - bx
                dy = other[1] - by
                dist = max(0.1, math.sqrt(dx*dx + dy*dy))
                if dist < self.sep_dist:
                    sep_x -= dx / dist
                    sep_y -= dy / dist
                if dist < self.align_dist:
                    align_x += other[2]
                    align_y += other[3]
                    align_n += 1
                if dist < self.cohesion_dist:
                    coh_x += other[0]
                    coh_y += other[1]
                    coh_n += 1
            
            # Apply rules
            boid[2] += sep_x * 0.05
            boid[3] += sep_y * 0.05
            if align_n > 0:
                boid[2] += (align_x / align_n - bvx) * 0.03
                boid[3] += (align_y / align_n - bvy) * 0.03
            if coh_n > 0:
                boid[2] += (coh_x / coh_n - bx) * 0.005
                boid[3] += (coh_y / coh_n - by) * 0.005
            
            # Attractors
            for ax, ay, _ in self._attractors:
                dx = ax - bx
                dy = ay - by
                dist = max(1.0, math.sqrt(dx*dx + dy*dy))
                boid[2] += dx / dist * 0.05
                boid[3] += dy / dist * 0.05
            
            # Clamp speed
            speed = math.sqrt(boid[2]**2 + boid[3]**2)
            if speed > self.max_speed:
                boid[2] = boid[2] / speed * self.max_speed
                boid[3] = boid[3] / speed * self.max_speed
            
            # Move + wrap
            boid[0] = (boid[0] + boid[2]) % self.w
            boid[1] = (boid[1] + boid[3]) % self.h
    
    def render_boids(self) -> List[Tuple[int, int, str, str]]:
        """Return list of (x, y, char, color_key) for all boids."""
        result = []
        for boid in self.boids:
            x, y, vx, vy = boid
            # Directional character based on velocity
            angle = math.atan2(vy, vx)
            if -0.4 < angle < 0.4: ch = '>'
            elif 0.4 <= angle < 1.2: ch = '\\'
            elif 1.2 <= angle < 1.95: ch = 'v'
            elif angle >= 1.95 or angle <= -1.95: ch = '<'
            elif -1.95 < angle <= -1.2: ch = '^'
            elif -1.2 < angle <= -0.4: ch = '/'
            else: ch = '*'
            result.append((int(x) % self.w, int(y) % self.h, ch, 'accent'))
        return result
