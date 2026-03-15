"""Monitor skill file changes."""
from __future__ import annotations
import os
import time
from typing import Dict, List
from hermes_neurovision.events import VisionEvent

SKILLS_DIR = os.path.expanduser("~/.hermes/skills/")

class SkillsSource:
    def __init__(self):
        self._mtimes: Dict[str, float] = {}
        self._last_check: float = 0.0
    
    def poll(self, since: float) -> List[VisionEvent]:
        now = time.time()
        if now - self._last_check < 5.0:
            return []
        self._last_check = now
        events = []
        if not os.path.isdir(SKILLS_DIR):
            return events
        current = {}
        for root, dirs, files in os.walk(SKILLS_DIR):
            for f in files:
                if f == 'SKILL.md':
                    path = os.path.join(root, f)
                    try:
                        mtime = os.path.getmtime(path)
                    except OSError:
                        continue
                    skill_name = os.path.basename(root)
                    current[skill_name] = mtime
                    if skill_name not in self._mtimes:
                        events.append(VisionEvent(
                            timestamp=now, source='agent',
                            kind='skill_create', severity='info',
                            data={'skill': skill_name},
                        ))
                    elif mtime > self._mtimes[skill_name]:
                        events.append(VisionEvent(
                            timestamp=now, source='agent',
                            kind='skill_activated', severity='info',
                            data={'skill': skill_name},
                        ))
        self._mtimes = current
        return events

_default = SkillsSource()
def poll(since: float) -> List[VisionEvent]:
    return _default.poll(since)
