"""Unified event model and poller for Hermes Vision."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class VisionEvent:
    timestamp: float
    source: str
    kind: str
    severity: str  # "info", "warning", "danger"
    data: Dict[str, Any] = field(default_factory=dict)


# Type alias for source poll functions
PollFn = Callable[[float], List[VisionEvent]]


class EventPoller:
    """Polls all registered sources and returns sorted events."""

    def __init__(self, sources: List[PollFn]):
        self._sources = sources
        self._last_poll: float = time.time()

    def poll(self) -> List[VisionEvent]:
        since = self._last_poll
        self._last_poll = time.time()

        events: List[VisionEvent] = []
        for source_fn in self._sources:
            try:
                events.extend(source_fn(since))
            except Exception:
                pass  # Sources must never crash the visualizer

        events.sort(key=lambda e: e.timestamp)
        return events
