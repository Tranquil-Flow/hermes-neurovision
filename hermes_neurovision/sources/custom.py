"""JSONL file tailer for custom events written by the gateway hook."""

from __future__ import annotations

import json
import os
import time
from typing import List

from hermes_neurovision.events import VisionEvent

DEFAULT_PATH = os.path.expanduser("~/.hermes/neurovision/events.jsonl")

# Map hook event_type strings to (source, kind) tuples
EVENT_MAP = {
    "agent:start": ("agent", "agent_start"),
    "agent:step": ("agent", "agent_step"),
    "agent:end": ("agent", "agent_end"),
    "session:start": ("agent", "session_start"),
    "session:reset": ("agent", "session_reset"),
}


class CustomSource:
    def __init__(self, path: str = DEFAULT_PATH):
        self._path = path
        self._offset: int = 0

    def poll(self, since: float) -> List[VisionEvent]:
        if not os.path.exists(self._path):
            return []

        events: List[VisionEvent] = []
        try:
            with open(self._path, "r") as f:
                f.seek(self._offset)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        event_type = data.get("event_type", "")
                        context = data.get("context", {})
                        timestamp = data.get("timestamp", time.time())
                        source, kind = EVENT_MAP.get(event_type, ("custom", event_type.replace(":", "_")))
                        events.append(VisionEvent(
                            timestamp=timestamp,
                            source=source,
                            kind=kind,
                            severity="info",
                            data=context,
                        ))
                    except (json.JSONDecodeError, KeyError):
                        continue
                self._offset = f.tell()
        except OSError:
            pass

        return events


def poll(since: float) -> List[VisionEvent]:
    """Module-level poll function for EventPoller compatibility."""
    return _default_source.poll(since)


_default_source = CustomSource()
