"""Gray-Scott reaction-diffusion system."""
from __future__ import annotations
import random
from typing import Optional, Tuple

class ReactionDiffusion:
    """Gray-Scott model creating Turing patterns.
    
    Runs on half-resolution grid for performance.
    """
    
    def __init__(self, w: int, h: int, feed: float = 0.055,
                 kill: float = 0.062, update_interval: int = 2):
        # Internal grid is half-res
        self.display_w = w
        self.display_h = h
        self.w = max(10, w // 2)
        self.h = max(5, h // 2)
        self.feed = feed
        self.kill = kill
        self.update_interval = max(1, update_interval)
        self._frame = 0
        self._rng = random.Random()
        # Two chemicals: u (substrate), v (catalyst)
        self.u = [[1.0] * self.w for _ in range(self.h)]
        self.v = [[0.0] * self.w for _ in range(self.h)]
        # Seed a small square of v in center
        cx, cy = self.w // 2, self.h // 2
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                nx = (cx + dx) % self.w
                ny = (cy + dy) % self.h
                self.v[ny][nx] = 0.25 + self._rng.uniform(0, 0.1)
                self.u[ny][nx] = 0.5
    
    def add_chemical(self, x: int, y: int, radius: int = 2) -> None:
        """Add catalyst chemical at display coordinates."""
        # Convert display coords to internal
        ix = max(0, min(self.w - 1, x // 2))
        iy = max(0, min(self.h - 1, y // 2))
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx = (ix + dx) % self.w
                ny = (iy + dy) % self.h
                self.v[ny][nx] = min(1.0, self.v[ny][nx] + 0.25)
                self.u[ny][nx] = max(0.0, self.u[ny][nx] - 0.1)
    
    def step(self) -> None:
        self._frame += 1
        if self._frame % self.update_interval != 0:
            return
        w, h = self.w, self.h
        du = 0.21  # diffusion rate for u
        dv = 0.105  # diffusion rate for v
        new_u = [[0.0] * w for _ in range(h)]
        new_v = [[0.0] * w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                u_val = self.u[y][x]
                v_val = self.v[y][x]
                # Laplacian (5-point stencil with wrapping)
                lu = (
                    self.u[(y-1)%h][x] + self.u[(y+1)%h][x] +
                    self.u[y][(x-1)%w] + self.u[y][(x+1)%w] -
                    4.0 * u_val
                )
                lv = (
                    self.v[(y-1)%h][x] + self.v[(y+1)%h][x] +
                    self.v[y][(x-1)%w] + self.v[y][(x+1)%w] -
                    4.0 * v_val
                )
                uvv = u_val * v_val * v_val
                new_u[y][x] = max(0.0, min(1.0,
                    u_val + du * lu - uvv + self.feed * (1.0 - u_val)))
                new_v[y][x] = max(0.0, min(1.0,
                    v_val + dv * lv + uvv - (self.feed + self.kill) * v_val))
        self.u = new_u
        self.v = new_v
    
    def render_char(self, x: int, y: int) -> Optional[Tuple[str, str]]:
        """Return char for display coordinates (upscaled from internal)."""
        ix = min(self.w - 1, x // 2)
        iy = min(self.h - 1, y // 2)
        v_val = self.v[iy][ix]
        if v_val < 0.05:
            return None
        if v_val > 0.3: return ('█', 'bright')
        if v_val > 0.15: return ('▓', 'accent')
        if v_val > 0.05: return ('░', 'soft')
        return None
