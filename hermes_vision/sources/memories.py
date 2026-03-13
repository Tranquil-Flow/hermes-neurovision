"""Filesystem watcher for ~/.hermes/memories/ directory."""

from __future__ import annotations

import os
import time
from typing import Dict, List

from hermes_vision.events import VisionEvent

DEFAULT_PATH = os.path.expanduser("~/.hermes/memories")


class MemoriesSource:
    def __init__(self, path: str = DEFAULT_PATH):
        self._path = path
        self._known: Dict[str, float] = {}  # path -> mtime
        self._last_count: int = 0

    def poll(self, since: float) -> List[VisionEvent]:
        if not os.path.isdir(self._path):
            return []

        events: List[VisionEvent] = []
        current: Dict[str, float] = {}
        now = time.time()

        try:
            for entry in os.scandir(self._path):
                if not entry.is_file():
                    continue
                mtime = entry.stat().st_mtime
                current[entry.path] = mtime

                if entry.path not in self._known:
                    events.append(VisionEvent(
                        timestamp=now, source="memory",
                        kind="memory_created", severity="info",
                        data={"path": entry.path, "name": entry.name},
                    ))
                elif mtime > self._known[entry.path]:
                    events.append(VisionEvent(
                        timestamp=now, source="memory",
                        kind="memory_accessed", severity="info",
                        data={"path": entry.path, "name": entry.name},
                    ))
        except OSError:
            pass

        if self._last_count > 0 and len(current) != self._last_count:
            events.append(VisionEvent(
                timestamp=now, source="memory",
                kind="memory_count_changed", severity="info",
                data={"count": len(current), "previous": self._last_count},
            ))

        self._known = current
        self._last_count = len(current)
        return events
