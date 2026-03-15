"""Excitable neural field simulation."""
from __future__ import annotations
from typing import Optional, Tuple

class NeuralField:
    """Excitable medium: neurons fire, cascade, enter refractory period."""
    
    # Cell states: 0=resting, 1..fire_duration=firing, negative=refractory
    
    def __init__(self, w: int, h: int, threshold: int = 2,
                 fire_duration: int = 2, refractory: int = 5):
        self.w = w
        self.h = h
        self.threshold = threshold
        self.fire_duration = fire_duration
        self.refractory = refractory
        self.grid = [[0] * w for _ in range(h)]
    
    def fire(self, x: int, y: int, radius: int = 2) -> None:
        """Manually fire neurons at position."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx = (x + dx) % self.w
                ny = (y + dy) % self.h
                if self.grid[ny][nx] == 0:
                    self.grid[ny][nx] = self.fire_duration
    
    def step(self) -> None:
        new = [[0] * self.w for _ in range(self.h)]
        for y in range(self.h):
            for x in range(self.w):
                s = self.grid[y][x]
                if s > 1:  # still firing
                    new[y][x] = s - 1
                elif s == 1:  # fire -> refractory
                    new[y][x] = -self.refractory
                elif s < 0:  # refractory countdown
                    new[y][x] = s + 1
                else:  # resting: check if neighbors trigger firing
                    firing_neighbors = 0
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dx == 0 and dy == 0:
                                continue
                            nx = (x + dx) % self.w
                            ny = (y + dy) % self.h
                            if self.grid[ny][nx] > 0:
                                firing_neighbors += 1
                    if firing_neighbors >= self.threshold:
                        new[y][x] = self.fire_duration
        self.grid = new
    
    def render_char(self, x: int, y: int) -> Optional[Tuple[str, str]]:
        s = self.grid[y][x]
        if s > 0:  # firing
            return ('█', 'bright') if s == self.fire_duration else ('▓', 'accent')
        if s < 0:  # refractory
            return ('·', 'soft') if s > -2 else None
        return None  # resting
