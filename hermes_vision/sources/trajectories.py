"""Trajectory monitoring source — polls successful and failed trajectory logs."""

from __future__ import annotations

import json
import os
import time
from typing import List

from hermes_vision.events import VisionEvent

DEFAULT_SUCCESS_PATH = os.path.expanduser("~/.hermes/logs/trajectory_samples.jsonl")
DEFAULT_FAILED_PATH = os.path.expanduser("~/.hermes/logs/failed_trajectories.jsonl")


class TrajectoriesSource:
    def __init__(self, success_path: str = DEFAULT_SUCCESS_PATH, failed_path: str = DEFAULT_FAILED_PATH):
        self._success_path = success_path
        self._failed_path = failed_path
        self._success_offset = 0
        self._failed_offset = 0

    def poll(self, since: float) -> List[VisionEvent]:
        events: List[VisionEvent] = []
        events.extend(self._poll_file(self._success_path, "trajectory_logged", "info", is_success=True))
        events.extend(self._poll_file(self._failed_path, "trajectory_failed", "warning", is_success=False))
        return events

    def _poll_file(self, path: str, kind: str, severity: str, is_success: bool) -> List[VisionEvent]:
        if not os.path.exists(path):
            return []

        events = []
        offset_attr = "_success_offset" if is_success else "_failed_offset"
        current_offset = getattr(self, offset_attr)

        try:
            with open(path, "r") as f:
                f.seek(current_offset)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        events.append(VisionEvent(
                            timestamp=data.get("timestamp", time.time()),
                            source="trajectories",
                            kind=kind,
                            severity=severity,
                            data={
                                "trajectory_id": data.get("trajectory_id", "unknown"),
                                "session_id": data.get("session_id", ""),
                                "tool_calls": data.get("tool_calls", []),
                                "outcome": data.get("outcome", ""),
                            },
                        ))
                    except (json.JSONDecodeError, KeyError):
                        pass
                setattr(self, offset_attr, f.tell())
        except (OSError, IOError):
            pass

        return events
