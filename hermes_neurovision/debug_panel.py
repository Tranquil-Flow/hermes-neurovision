"""Debug panel — right-side diagnostic overlay showing events, triggers, and tune state."""

from __future__ import annotations

import curses
import time
from collections import deque
from typing import TYPE_CHECKING, Any, Deque, Optional, Tuple

if TYPE_CHECKING:
    from hermes_neurovision.events import VisionEvent
    from hermes_neurovision.scene import ThemeState


class DebugPanel:
    """Right-anchored 34-column panel showing live diagnostics.

    Toggle visibility with .toggle() or the 'd' key in GalleryApp/LiveApp.
    Feed data via record_event() and record_trigger() each poll cycle.
    """

    width: int = 34

    def __init__(self) -> None:
        self.visible: bool = False
        self.recent_events: Deque["VisionEvent"] = deque(maxlen=8)
        # Each entry: (trigger, source_event_or_None)
        self.recent_triggers: Deque[Tuple[Any, Optional["VisionEvent"]]] = deque(maxlen=8)

    # ── data feed ─────────────────────────────────────────────────────────────

    def record_event(self, event: "VisionEvent") -> None:
        self.recent_events.append(event)

    def record_trigger(self, trigger: Any, source_event: Optional["VisionEvent"] = None) -> None:
        self.recent_triggers.append((trigger, source_event))

    def toggle(self) -> None:
        self.visible = not self.visible

    # ── drawing ───────────────────────────────────────────────────────────────

    def draw(self, stdscr, state: "ThemeState", color_pairs: dict) -> None:
        if not self.visible:
            return

        h, w = stdscr.getmaxyx()
        if w < self.width + 10 or h < 10:
            return  # terminal too narrow

        left = w - self.width - 1
        bright = color_pairs.get("bright", 0)
        accent = color_pairs.get("accent", 0)
        soft = color_pairs.get("soft", 0)
        now = time.time()

        def put(y: int, x: int, text: str, attr: int = 0) -> None:
            if y < 0 or y >= h:
                return
            try:
                stdscr.addstr(y, left + x, text[: self.width - x], attr)
            except curses.error:
                pass

        row = 1
        # ── header ────────────────────────────────────────────────────────────
        put(row, 0, "┌" + "─" * (self.width - 2) + "┐", soft)
        row += 1
        header = " DEBUG ".center(self.width - 2)
        put(row, 0, "│" + header + "│", curses.color_pair(bright) | curses.A_BOLD)
        row += 1
        put(row, 0, "├" + "─" * (self.width - 2) + "┤", soft)
        row += 1

        # ── theme + frame ─────────────────────────────────────────────────────
        tune = getattr(state, "tune", None)
        quiet_str = "ON " if state.quiet else "off"
        tuned_str = "YES" if (tune and not tune.is_default()) else "no "
        put(row, 1, f" Theme: {state.config.name[:18]}", soft)
        row += 1
        put(row, 1, f" Frame: {state.frame:<6} I:{state.intensity_multiplier:.2f}", soft)
        row += 1

        # intensity bar
        bar_w = self.width - 6
        filled = int(state.intensity_multiplier * bar_w)
        bar = "█" * filled + "░" * (bar_w - filled)
        put(row, 1, f" {bar}", accent)
        row += 1
        put(row, 1, f" Quiet:{quiet_str}  Tuned:{tuned_str}", soft)
        row += 1

        # ── events section ────────────────────────────────────────────────────
        put(row, 0, "├" + "─" * (self.width - 2) + "┤", soft)
        row += 1
        put(row, 1, " ── EVENTS ──────────────────", accent)
        row += 1

        events_list = list(self.recent_events)[-6:]
        for ev in events_list:
            if row >= h - 6:
                break
            age = now - ev.timestamp
            ts = f"{int(age):>3}s" if age < 3600 else "---"
            line = f" {ts} {ev.source[:8]:<8} {ev.kind[:12]}"
            put(row, 1, line, soft)
            row += 1

        # pad to 6 rows
        while len(events_list) < 6 and row < h - 6:
            put(row, 1, "", soft)
            row += 1
            events_list.append(None)  # type: ignore

        # ── triggers section ──────────────────────────────────────────────────
        if row < h - 5:
            put(row, 0, "├" + "─" * (self.width - 2) + "┤", soft)
            row += 1
            put(row, 1, " ── TRIGGERS ────────────────", accent)
            row += 1

            triggers_list = list(self.recent_triggers)[-4:]
            for trig, src_ev in triggers_list:
                if row >= h - 3:
                    break
                age = now - src_ev.timestamp if src_ev else 0.0
                ts = f"{int(age):>3}s" if src_ev else "---"
                effect = getattr(trig, "effect", "?")[:10]
                intensity = getattr(trig, "intensity", 0.0)
                line = f" {ts} {effect:<10} I:{intensity:.2f}"
                put(row, 1, line, soft)
                row += 1

        # ── footer ────────────────────────────────────────────────────────────
        if row < h - 1:
            put(row, 0, "└" + "─" * (self.width - 2) + "┘", soft)
