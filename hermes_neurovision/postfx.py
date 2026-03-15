"""Post-processing pipeline for hermes-neurovision.

Nine opt-in post-processing operations that operate on a FrameBuffer.
Each function is standalone with defaults that disable the effect.
"""
from __future__ import annotations

import math
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from hermes_neurovision.renderer import FrameBuffer


def apply_warp(buf: FrameBuffer, plugin, frame: int, strength: float) -> None:
    """Displacement mapping. Moves cell contents based on plugin.warp_field().
    strength=0 means disabled (skip entirely).
    Creates a new cells grid, for each (x,y) looks up source via plugin.warp_field(),
    copies source cell to output position."""
    if strength <= 0:
        return
    w, h = buf.w, buf.h
    from hermes_neurovision.renderer import Cell
    old = [[Cell(c.char, c.color_pair, c.attr, c.age) for c in row] for row in buf.cells]
    for y in range(h):
        for x in range(w):
            sx, sy = plugin.warp_field(x, y, w, h, frame, strength)
            sx = max(0, min(w - 1, int(round(sx))))
            sy = max(0, min(h - 1, int(round(sy))))
            src = old[sy][sx]
            cell = buf.cells[y][x]
            cell.char = src.char
            cell.color_pair = src.color_pair
            cell.attr = src.attr


def apply_void(buf: FrameBuffer, plugin, frame: int, intensity: float) -> None:
    """Erase cells at void points. intensity=0 means disabled."""
    if intensity <= 0:
        return
    points = plugin.void_points(buf.w, buf.h, frame, intensity)
    for point in points:
        if len(point) >= 2:
            x, y = int(point[0]), int(point[1])
            if 0 <= x < buf.w and 0 <= y < buf.h:
                cell = buf.cells[y][x]
                cell.char = ' '
                cell.color_pair = 0
                cell.attr = 0


def apply_echo(buf: FrameBuffer, echo_ring: list, echo_frames: int) -> None:
    """Afterimage effect using a ring buffer of previous frames.
    echo_frames=0 means disabled.
    echo_ring is a list of previous FrameBuffer snapshots (list of list of Cell).
    Empty cells in current buffer get filled with dimmed content from oldest echo frame."""
    if echo_frames <= 0 or not echo_ring:
        return
    import curses
    # Use the oldest frame in the ring for echo
    oldest = echo_ring[0]
    w, h = buf.w, buf.h
    for y in range(min(h, len(oldest))):
        for x in range(min(w, len(oldest[y]))):
            current = buf.cells[y][x]
            if current.char == ' ' and current.attr == 0:
                echo_cell = oldest[y][x]
                if echo_cell['char'] != ' ':
                    current.char = echo_cell['char']
                    current.color_pair = echo_cell['color_pair']
                    current.attr = curses.A_DIM


def snapshot_buffer(buf: FrameBuffer) -> list:
    """Take a snapshot of the buffer for the echo ring buffer.
    Returns a list of rows, each row a list of dicts."""
    return [
        [{'char': c.char, 'color_pair': c.color_pair, 'attr': c.attr}
         for c in row]
        for row in buf.cells
    ]


def apply_glow(buf: FrameBuffer, radius: int) -> None:
    """Color bleed: bright cells propagate color to empty neighbors.
    radius=0 means disabled. 1-3 = subtle to strong."""
    if radius <= 0:
        return
    import curses
    w, h = buf.w, buf.h
    # Collect bright cells (non-space cells with BOLD attr or non-DIM)
    bright_cells = []
    for y in range(h):
        for x in range(w):
            cell = buf.cells[y][x]
            if cell.char != ' ' and not (cell.attr & curses.A_DIM):
                bright_cells.append((x, y, cell.color_pair))
    # Bleed to neighbors
    for bx, by, cp in bright_cells:
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = bx + dx, by + dy
                if 0 <= nx < w and 0 <= ny < h:
                    target = buf.cells[ny][nx]
                    if target.char == ' ' and target.attr == 0:
                        target.char = '·'
                        target.color_pair = cp
                        target.attr = curses.A_DIM


def apply_decay(buf: FrameBuffer, sequence: Optional[str]) -> None:
    """Age cells through a character decay sequence.
    sequence=None means disabled.
    Example sequence: '█▓▒░·. ' — chars age through this."""
    if not sequence:
        return
    import curses
    seq_map = {ch: i for i, ch in enumerate(sequence)}
    for row in buf.cells:
        for cell in row:
            if cell.char == ' ':
                continue
            cell.age += 1
            idx = seq_map.get(cell.char)
            if cell.age > 0 and idx is not None:
                # Advance through sequence every few frames
                new_idx = min(idx + (cell.age // 3), len(sequence) - 1)
                cell.char = sequence[new_idx]
                if new_idx >= len(sequence) - 2:
                    cell.attr = curses.A_DIM


def apply_symmetry(buf: FrameBuffer, mode: Optional[str]) -> None:
    """Mirror/rotate buffer contents.
    mode: 'mirror_x' (left->right), 'mirror_y' (top->bottom),
          'mirror_xy' (both), 'rotate_4' (4-fold rotational).
    None means disabled."""
    if mode is None:
        return
    w, h = buf.w, buf.h
    if mode == 'mirror_x':
        # Copy left half to right half (mirrored)
        for y in range(h):
            for x in range(w // 2):
                src = buf.cells[y][x]
                dst = buf.cells[y][w - 1 - x]
                if src.char != ' ':
                    dst.char = src.char
                    dst.color_pair = src.color_pair
                    dst.attr = src.attr
    elif mode == 'mirror_y':
        for y in range(h // 2):
            for x in range(w):
                src = buf.cells[y][x]
                dst = buf.cells[h - 1 - y][x]
                if src.char != ' ':
                    dst.char = src.char
                    dst.color_pair = src.color_pair
                    dst.attr = src.attr
    elif mode == 'mirror_xy':
        # Mirror both axes
        for y in range(h // 2):
            for x in range(w // 2):
                src = buf.cells[y][x]
                if src.char != ' ':
                    for ty, tx in [(y, w - 1 - x), (h - 1 - y, x), (h - 1 - y, w - 1 - x)]:
                        buf.cells[ty][tx].char = src.char
                        buf.cells[ty][tx].color_pair = src.color_pair
                        buf.cells[ty][tx].attr = src.attr
    elif mode == 'rotate_4':
        # 4-fold rotational symmetry from top-left quadrant
        hw, hh = w // 2, h // 2
        for y in range(hh):
            for x in range(hw):
                src = buf.cells[y][x]
                if src.char != ' ':
                    # 90 degree rotation mappings (approximate for non-square)
                    positions = [
                        (y, w - 1 - x),          # top-right
                        (h - 1 - y, x),           # bottom-left
                        (h - 1 - y, w - 1 - x),   # bottom-right
                    ]
                    for py, px in positions:
                        if 0 <= py < h and 0 <= px < w:
                            buf.cells[py][px].char = src.char
                            buf.cells[py][px].color_pair = src.color_pair
                            buf.cells[py][px].attr = src.attr


def apply_mask(buf: FrameBuffer, mask: Optional[list]) -> None:
    """Apply boolean stencil mask. True=visible, False=hidden.
    mask is a 2D list[list[bool]] (h rows x w cols). None means no mask."""
    if mask is None:
        return
    h = min(buf.h, len(mask))
    for y in range(h):
        w = min(buf.w, len(mask[y]))
        for x in range(w):
            if not mask[y][x]:
                cell = buf.cells[y][x]
                cell.char = ' '
                cell.color_pair = 0
                cell.attr = 0


def apply_force_field(buf: FrameBuffer, plugin, frame: int, strength: float) -> None:
    """Displace non-space cells based on force points.
    strength=0 means disabled. This is a simplified version that nudges cells."""
    if strength <= 0:
        return
    points = plugin.force_points(buf.w, buf.h, frame, strength)
    if not points:
        return
    from hermes_neurovision.renderer import Cell
    w, h = buf.w, buf.h
    # Collect moveable cells
    movers = []
    for y in range(h):
        for x in range(w):
            cell = buf.cells[y][x]
            if cell.char != ' ':
                # Calculate net force
                fx_total, fy_total = 0.0, 0.0
                for fp in points:
                    try:
                        if isinstance(fp, dict):
                            px = fp["x"]
                            py = fp["y"]
                            fstrength = fp["strength"]
                            ftype = fp.get("type", "radial")
                        elif hasattr(fp, '__len__') and len(fp) >= 4:
                            px, py, fstrength, ftype = fp[0], fp[1], fp[2], fp[3]
                        else:
                            continue
                    except (KeyError, IndexError, TypeError):
                        continue
                    dx = x - px
                    dy = y - py
                    dist = max(1.0, math.sqrt(dx * dx + dy * dy))
                    if dist < 15:  # influence radius
                        force = fstrength * strength / (dist * dist)
                        if ftype == 'vortex':
                            fx_total += -dy / dist * force
                            fy_total += dx / dist * force
                        else:  # radial
                            fx_total += dx / dist * force
                            fy_total += dy / dist * force
                # Only move if force is significant
                if abs(fx_total) > 0.3 or abs(fy_total) > 0.3:
                    nx = max(0, min(w - 1, int(round(x + fx_total))))
                    ny = max(0, min(h - 1, int(round(y + fy_total))))
                    if nx != x or ny != y:
                        movers.append((x, y, nx, ny, cell.char, cell.color_pair, cell.attr))
    # Apply moves with collision detection (first-writer wins)
    occupied: dict = {}
    for ox, oy, nx, ny, ch, cp, attr in movers:
        dest = (nx, ny)
        if dest in occupied:
            continue  # skip — another cell already claimed this spot
        occupied[dest] = True
        buf.cells[oy][ox].char = ' '
        buf.cells[oy][ox].color_pair = 0
        buf.cells[oy][ox].attr = 0
        buf.cells[ny][nx].char = ch
        buf.cells[ny][nx].color_pair = cp
        buf.cells[ny][nx].attr = attr
