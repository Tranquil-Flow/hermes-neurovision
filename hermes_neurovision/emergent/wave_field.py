"""2D wave propagation with interference."""
from __future__ import annotations
from typing import Optional, Tuple

class WaveField:
    """2D wave equation simulation."""
    
    def __init__(self, w: int, h: int, speed: float = 0.3, damping: float = 0.98):
        self.w = w
        self.h = h
        self.speed = speed
        self.damping = damping
        # Two buffers for wave equation (current + previous)
        self.current = [[0.0] * w for _ in range(h)]
        self.previous = [[0.0] * w for _ in range(h)]
    
    def drop(self, x: int, y: int, amplitude: float = 3.0) -> None:
        """Drop a disturbance at position."""
        if 0 <= x < self.w and 0 <= y < self.h:
            self.current[y][x] = amplitude
    
    def step(self) -> None:
        w, h = self.w, self.h
        speed_sq = self.speed * self.speed
        new = [[0.0] * w for _ in range(h)]
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                # Discrete 2D wave equation
                laplacian = (
                    self.current[y-1][x] + self.current[y+1][x] +
                    self.current[y][x-1] + self.current[y][x+1] -
                    4.0 * self.current[y][x]
                )
                new[y][x] = (
                    2.0 * self.current[y][x] - self.previous[y][x] +
                    speed_sq * laplacian
                ) * self.damping
        self.previous = self.current
        self.current = new
    
    def render_char(self, x: int, y: int) -> Optional[Tuple[str, str]]:
        val = self.current[y][x]
        if abs(val) < 0.1:
            return None
        if val > 1.5: return ('█', 'bright')
        if val > 0.5: return ('▓', 'accent')
        if val > 0.1: return ('░', 'soft')
        if val < -1.5: return ('█', 'warning')
        if val < -0.5: return ('▒', 'accent')
        if val < -0.1: return ('·', 'base')
        return None
