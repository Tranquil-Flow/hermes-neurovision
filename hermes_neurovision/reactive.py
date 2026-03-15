"""Reactive rendering engine for hermes-neurovision.

Manages active reactions (visual responses to events) and renders them
into the FrameBuffer each frame.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from hermes_neurovision.plugin import Reaction, ReactiveElement
from hermes_neurovision.renderer import FrameBuffer


MAX_ACTIVE_REACTIONS = 24


@dataclass
class ActiveReaction:
    """A reaction that is currently being rendered."""
    reaction: Reaction
    start_time: float = field(default_factory=time.time)

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def progress(self) -> float:
        """0.0 → 1.0 over the reaction's duration."""
        if self.reaction.duration <= 0:
            return 1.0
        return min(1.0, self.elapsed / self.reaction.duration)

    @property
    def alive(self) -> bool:
        return self.elapsed < self.reaction.duration


# ── Element renderers (write to FrameBuffer) ──────────────────────────

def _render_pulse(buf: FrameBuffer, ar: ActiveReaction) -> None:
    r = ar.reaction
    cx = int(r.origin[0] * buf.w)
    cy = int(r.origin[1] * buf.h)
    radius = int(ar.progress * min(buf.w, buf.h) * 0.3 * r.intensity)
    if radius < 1:
        buf.put(cx, cy, "*", 0)
        return
    steps = max(8, radius * 6)
    for i in range(steps):
        angle = math.tau * i / steps
        x = int(round(cx + math.cos(angle) * radius * 2))
        y = int(round(cy + math.sin(angle) * radius))
        buf.put(x, y, "·", 0)


def _render_ripple(buf: FrameBuffer, ar: ActiveReaction) -> None:
    r = ar.reaction
    cx = int(r.origin[0] * buf.w)
    cy = int(r.origin[1] * buf.h)
    for ring in range(3):
        radius = int((ar.progress * 0.3 + ring * 0.1) * min(buf.w, buf.h) * r.intensity)
        if radius < 1:
            continue
        steps = max(8, radius * 4)
        for i in range(steps):
            angle = math.tau * i / steps
            x = int(round(cx + math.cos(angle) * radius * 2))
            y = int(round(cy + math.sin(angle) * radius))
            buf.put(x, y, "○", 0)


def _render_stream(buf: FrameBuffer, ar: ActiveReaction) -> None:
    r = ar.reaction
    cx = int(r.origin[0] * buf.w)
    cy = int(r.origin[1] * buf.h)
    length = int(ar.progress * 10 * r.intensity)
    dx = r.data.get("dx", 1)
    for i in range(length):
        buf.put(cx + i * dx, cy, "~", 0)


def _render_bloom(buf: FrameBuffer, ar: ActiveReaction) -> None:
    r = ar.reaction
    cx = int(r.origin[0] * buf.w)
    cy = int(r.origin[1] * buf.h)
    size = int(ar.progress * 4 * r.intensity)
    for dy in range(-size, size + 1):
        for dx in range(-size, size + 1):
            if abs(dx) + abs(dy) <= size:
                buf.put(cx + dx, cy + dy, "❀", 0)


def _render_shatter(buf: FrameBuffer, ar: ActiveReaction) -> None:
    r = ar.reaction
    cx = int(r.origin[0] * buf.w)
    cy = int(r.origin[1] * buf.h)
    spread = int(ar.progress * 8 * r.intensity)
    chars = "▪▫◻◼"
    for i in range(8):
        angle = math.tau * i / 8
        x = int(round(cx + math.cos(angle) * spread * 2))
        y = int(round(cy + math.sin(angle) * spread))
        buf.put(x, y, chars[i % len(chars)], 0)


def _render_orbit(buf: FrameBuffer, ar: ActiveReaction) -> None:
    r = ar.reaction
    cx = int(r.origin[0] * buf.w)
    cy = int(r.origin[1] * buf.h)
    radius = int(5 * r.intensity)
    angle = ar.progress * math.tau * 3
    x = int(round(cx + math.cos(angle) * radius * 2))
    y = int(round(cy + math.sin(angle) * radius))
    buf.put(x, y, "◦", 0)


def _render_gauge(buf: FrameBuffer, ar: ActiveReaction) -> None:
    r = ar.reaction
    cx = int(r.origin[0] * buf.w)
    cy = int(r.origin[1] * buf.h)
    width = int(10 * r.intensity)
    filled = int(ar.progress * width)
    for i in range(width):
        ch = "█" if i < filled else "░"
        buf.put(cx + i, cy, ch, 0)


def _render_spark(buf: FrameBuffer, ar: ActiveReaction) -> None:
    r = ar.reaction
    cx = int(r.origin[0] * buf.w)
    cy = int(r.origin[1] * buf.h)
    if ar.progress < 0.3:
        buf.put(cx, cy, "✦", 0)
    else:
        buf.put(cx, cy, "✧", 0)


def _render_wave(buf: FrameBuffer, ar: ActiveReaction) -> None:
    r = ar.reaction
    sweep_x = int(ar.progress * buf.w)
    for y in range(buf.h):
        buf.put(sweep_x, y, "│", 0)


def _render_glyph(buf: FrameBuffer, ar: ActiveReaction) -> None:
    r = ar.reaction
    cx = int(r.origin[0] * buf.w)
    cy = int(r.origin[1] * buf.h)
    glyphs = "⟁⟐⟟⟠⟡"
    idx = int(ar.progress * (len(glyphs) - 1))
    buf.put(cx, cy, glyphs[idx], 0)


def _render_trail(buf: FrameBuffer, ar: ActiveReaction) -> None:
    r = ar.reaction
    sx = int(r.origin[0] * buf.w)
    sy = int(r.origin[1] * buf.h)
    length = int(ar.progress * 15 * r.intensity)
    for i in range(length):
        buf.put(sx + i, sy, "─", 0)


def _render_constellation(buf: FrameBuffer, ar: ActiveReaction) -> None:
    r = ar.reaction
    cx = int(r.origin[0] * buf.w)
    cy = int(r.origin[1] * buf.h)
    count = int(3 + ar.progress * 4 * r.intensity)
    for i in range(count):
        angle = math.tau * i / max(count, 1)
        radius = 4 * r.intensity
        x = int(round(cx + math.cos(angle) * radius * 2))
        y = int(round(cy + math.sin(angle) * radius))
        buf.put(x, y, "•", 0)


_ELEMENT_RENDERERS = {
    ReactiveElement.PULSE: _render_pulse,
    ReactiveElement.RIPPLE: _render_ripple,
    ReactiveElement.STREAM: _render_stream,
    ReactiveElement.BLOOM: _render_bloom,
    ReactiveElement.SHATTER: _render_shatter,
    ReactiveElement.ORBIT: _render_orbit,
    ReactiveElement.GAUGE: _render_gauge,
    ReactiveElement.SPARK: _render_spark,
    ReactiveElement.WAVE: _render_wave,
    ReactiveElement.GLYPH: _render_glyph,
    ReactiveElement.TRAIL: _render_trail,
    ReactiveElement.CONSTELLATION: _render_constellation,
}


class ReactiveRenderer:
    """Manages and renders active reactions into a FrameBuffer."""

    def __init__(self) -> None:
        self._active: List[ActiveReaction] = []

    @property
    def active(self) -> List[ActiveReaction]:
        return list(self._active)

    def activate(self, reaction: Reaction) -> Optional[ActiveReaction]:
        """Start rendering a reaction. Returns the ActiveReaction, or None if at cap."""
        # Prune expired first
        self._prune()
        if len(self._active) >= MAX_ACTIVE_REACTIONS:
            return None
        ar = ActiveReaction(reaction=reaction)
        self._active.append(ar)
        return ar

    def step_and_render(self, buf: FrameBuffer) -> None:
        """Advance one frame: prune expired, render all active reactions."""
        self._prune()
        for ar in self._active:
            renderer = _ELEMENT_RENDERERS.get(ar.reaction.element)
            if renderer:
                renderer(buf, ar)

    def _prune(self) -> None:
        self._active = [ar for ar in self._active if ar.alive]
