"""Optional Aegis audit trail tailer. Gracefully returns empty if unavailable."""

from __future__ import annotations

import json
import os
import time
from typing import List

from hermes_neurovision.events import VisionEvent

DEFAULT_PATH = os.path.expanduser("~/.hermes-aegis/audit.jsonl")

DECISION_MAP = {
    "DANGEROUS_COMMAND": ("threat_blocked", "danger"),
    "BLOCKED": ("threat_blocked", "danger"),
    "OUTPUT_REDACTED": ("secret_redacted", "warning"),
    "SECRET_DETECTED": ("secret_detected", "warning"),
    "ANOMALY": ("rate_anomaly", "warning"),
    "INITIATED": (None, None),  # skip routine audit entries
    "COMPLETED": (None, None),
}


class AegisSource:
    def __init__(self, path: str = DEFAULT_PATH, enabled: bool = True):
        self._path = path
        self._enabled = enabled
        self._offset: int = 0

    def poll(self, since: float) -> List[VisionEvent]:
        if not self._enabled or not os.path.exists(self._path):
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
                        decision = data.get("decision", "")
                        kind, severity = DECISION_MAP.get(decision, ("threat_blocked", "warning"))
                        if kind is None:
                            continue
                        events.append(VisionEvent(
                            timestamp=data.get("timestamp", time.time()),
                            source="aegis",
                            kind=kind,
                            severity=severity,
                            data={
                                "tool_name": data.get("tool_name", ""),
                                "decision": decision,
                                "args": data.get("args_redacted", {}),
                            },
                        ))
                    except (json.JSONDecodeError, KeyError):
                        continue
                self._offset = f.tell()
        except OSError:
            pass

        return events
