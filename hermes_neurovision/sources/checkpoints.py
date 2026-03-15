"""Monitor checkpoint creation and rollback."""
from __future__ import annotations
import os
import time
from typing import Dict, List
from hermes_neurovision.events import VisionEvent

CHECKPOINTS_DIR = os.path.expanduser("~/.hermes/checkpoints/")

class CheckpointsSource:
    def __init__(self):
        self._known: Dict[str, float] = {}
        self._last_check: float = 0.0
    
    def poll(self, since: float) -> List[VisionEvent]:
        now = time.time()
        if now - self._last_check < 3.0:
            return []
        self._last_check = now
        events = []
        if not os.path.isdir(CHECKPOINTS_DIR):
            return events
        current = {}
        try:
            for entry in os.listdir(CHECKPOINTS_DIR):
                path = os.path.join(CHECKPOINTS_DIR, entry)
                if os.path.isdir(path):
                    try:
                        mtime = os.path.getmtime(path)
                    except OSError:
                        continue
                    current[entry] = mtime
                    if entry not in self._known:
                        events.append(VisionEvent(
                            timestamp=now, source='agent',
                            kind='checkpoint_created', severity='info',
                            data={'checkpoint_id': entry},
                        ))
        except OSError:
            pass
        # Check for deletions (rollback)
        for cid in self._known:
            if cid not in current:
                events.append(VisionEvent(
                    timestamp=now, source='agent',
                    kind='checkpoint_rollback', severity='warning',
                    data={'checkpoint_id': cid},
                ))
        self._known = current
        return events

_default = CheckpointsSource()
def poll(since: float) -> List[VisionEvent]:
    return _default.poll(since)
