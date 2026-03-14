"""Docker task watcher — detects delegate_task sub-agents running in containers."""

from __future__ import annotations

import subprocess
import time
from typing import List, Set

from hermes_neurovision.events import VisionEvent

# Container name prefixes used by Hermes delegate_task
_TASK_PREFIXES = ("minisweagent", "hermes-task", "hermes-agent-task")


def _running_task_containers() -> Set[str]:
    """Return set of task container names currently running. Returns empty set on any error."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=2.0,
        )
        if result.returncode != 0:
            return set()
        names = set()
        for name in result.stdout.splitlines():
            name = name.strip()
            if any(name.startswith(p) for p in _TASK_PREFIXES):
                names.add(name)
        return names
    except (OSError, subprocess.TimeoutExpired):
        return set()


class DockerTaskSource:
    """Emits events when delegate_task containers start or finish."""

    def __init__(self) -> None:
        self._known: Set[str] = set()
        self._docker_available: bool = True  # set False on first OSError to skip future calls

    def poll(self, since: float) -> List[VisionEvent]:
        if not self._docker_available:
            return []

        try:
            current = _running_task_containers()
        except Exception:
            self._docker_available = False
            return []

        events: List[VisionEvent] = []
        now = time.time()

        for name in current - self._known:
            events.append(VisionEvent(
                timestamp=now, source="docker",
                kind="delegate_task_started", severity="info",
                data={"container": name},
            ))

        for name in self._known - current:
            events.append(VisionEvent(
                timestamp=now, source="docker",
                kind="delegate_task_done", severity="info",
                data={"container": name},
            ))

        self._known = current
        return events
