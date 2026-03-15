"""Cellular automaton systems: Brian's Brain, Cyclic CA, Rule 110."""
from __future__ import annotations
import random
from typing import Optional, Tuple

class CellularAutomaton:
    """Multi-rule cellular automaton on a 2D grid."""
    
    def __init__(self, w: int, h: int, rule: str = 'brians_brain',
                 density: float = 0.08, update_interval: int = 2):
        self.w = w
        self.h = h
        self.rule = rule
        self.update_interval = max(1, update_interval)
        self._frame = 0
        self._rng = random.Random()
        # Grid: 0=off, 1=on, 2=dying (for brians_brain)
        #        0..N-1 states for cyclic
        self.grid = [[0] * w for _ in range(h)]
        self._n_states = 14 if rule == 'cyclic' else 3
        # Seed initial density
        for y in range(h):
            for x in range(w):
                if self._rng.random() < density:
                    self.grid[y][x] = 1
    
    def inject(self, x: int, y: int, radius: int = 3) -> None:
        """Inject live cells around (x,y)."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = (x + dx) % self.w, (y + dy) % self.h
                if self._rng.random() < 0.5:
                    self.grid[ny][nx] = 1
    
    def step(self) -> None:
        self._frame += 1
        if self._frame % self.update_interval != 0:
            return
        if self.rule == 'brians_brain':
            self._step_brians_brain()
        elif self.rule == 'cyclic':
            self._step_cyclic()
        elif self.rule == 'rule110':
            self._step_rule110()
        elif self.rule == 'game_of_life':
            self._step_game_of_life()
    
    def _count_neighbors(self, x: int, y: int, state: int) -> int:
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.w
                ny = (y + dy) % self.h
                if self.grid[ny][nx] == state:
                    count += 1
        return count
    
    def _step_brians_brain(self) -> None:
        new = [[0] * self.w for _ in range(self.h)]
        for y in range(self.h):
            for x in range(self.w):
                s = self.grid[y][x]
                if s == 0:  # off -> on if exactly 2 neighbors are on
                    if self._count_neighbors(x, y, 1) == 2:
                        new[y][x] = 1
                elif s == 1:  # on -> dying
                    new[y][x] = 2
                # dying -> off (stays 0)
        self.grid = new
    
    def _step_cyclic(self) -> None:
        new = [[self.grid[y][x] for x in range(self.w)] for y in range(self.h)]
        for y in range(self.h):
            for x in range(self.w):
                s = self.grid[y][x]
                next_s = (s + 1) % self._n_states
                if self._count_neighbors(x, y, next_s) >= 1:
                    new[y][x] = next_s
        self.grid = new
    
    def _step_rule110(self) -> None:
        """1D CA scrolling vertically. Process bottom row, scroll up."""
        # Scroll grid up by one row
        self.grid.pop(0)
        # Generate new bottom row from current bottom
        old_row = self.grid[-1] if self.grid else [0] * self.w
        new_row = [0] * self.w
        # Rule 110 lookup: 3-bit neighborhood -> output
        rule110 = {7:0, 6:1, 5:1, 4:0, 3:1, 2:1, 1:1, 0:0}
        for x in range(self.w):
            left = old_row[(x - 1) % self.w]
            center = old_row[x]
            right = old_row[(x + 1) % self.w]
            pattern = (left << 2) | (center << 1) | right
            new_row[x] = rule110.get(pattern, 0)
        self.grid.append(new_row)
    
    def _step_game_of_life(self) -> None:
        new = [[0] * self.w for _ in range(self.h)]
        for y in range(self.h):
            for x in range(self.w):
                alive = self.grid[y][x] == 1
                n = self._count_neighbors(x, y, 1)
                if alive and n in (2, 3):
                    new[y][x] = 1
                elif not alive and n == 3:
                    new[y][x] = 1
        self.grid = new
    
    def render_char(self, x: int, y: int) -> Optional[Tuple[str, str]]:
        """Return (char, color_key) for cell or None if off."""
        s = self.grid[y][x]
        if s == 0:
            return None
        if self.rule == 'brians_brain':
            if s == 1: return ('▓', 'bright')
            if s == 2: return ('░', 'soft')
        elif self.rule == 'cyclic':
            chars = '█▓▒░·.:+*#@%&'
            colors = ['bright', 'accent', 'soft', 'base'] * 4
            return (chars[s % len(chars)], colors[s % len(colors)])
        elif self.rule in ('rule110', 'game_of_life'):
            if s == 1: return ('█', 'bright')
        return None
