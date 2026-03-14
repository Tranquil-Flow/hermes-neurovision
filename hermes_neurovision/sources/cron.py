"""Cron job status poller for ~/.hermes/cron/ directory."""

from __future__ import annotations

import json
import os
import time
from typing import Dict, List

from hermes_neurovision.events import VisionEvent

DEFAULT_PATH = os.path.expanduser("~/.hermes/cron")


class CronSource:
    def __init__(self, path: str = DEFAULT_PATH):
        self._path = path
        self._was_locked: bool = False
        self._known_outputs: set = set()

    def poll(self, since: float) -> List[VisionEvent]:
        if not os.path.isdir(self._path):
            return []

        events: List[VisionEvent] = []
        now = time.time()

        # Check lock file for execution state
        lock_path = os.path.join(self._path, ".tick.lock")
        is_locked = os.path.exists(lock_path)

        if is_locked and not self._was_locked:
            events.append(VisionEvent(
                timestamp=now, source="cron",
                kind="cron_executing", severity="info",
                data={},
            ))

        if not is_locked and self._was_locked:
            events.append(VisionEvent(
                timestamp=now, source="cron",
                kind="cron_completed", severity="info",
                data={},
            ))

        self._was_locked = is_locked

        # Check for new output files
        output_dir = os.path.join(self._path, "output")
        if os.path.isdir(output_dir):
            try:
                for entry in os.scandir(output_dir):
                    if entry.is_file() and entry.path not in self._known_outputs:
                        self._known_outputs.add(entry.path)
                        events.append(VisionEvent(
                            timestamp=now, source="cron",
                            kind="cron_completed", severity="info",
                            data={"output": entry.name},
                        ))
            except OSError:
                pass

        return events
