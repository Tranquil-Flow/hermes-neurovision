"""Event source that emits events from VT terminal activity."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, List

from hermes_neurovision.events import VisionEvent

if TYPE_CHECKING:
    from hermes_neurovision.vt import VTScreen


class VTEventSource:
    """Generates VisionEvents from VTScreen activity counters."""

    def __init__(self, vt_screen: "VTScreen") -> None:
        self._vt = vt_screen

    def poll(self, since: float) -> List[VisionEvent]:
        events: List[VisionEvent] = []
        now = time.time()

        if self._vt.bytes_since_last_poll > 0:
            events.append(VisionEvent(
                timestamp=now,
                source="vt",
                kind="vt_output",
                severity="info",
                data={"bytes": self._vt.bytes_since_last_poll},
            ))

        if self._vt.scrolls_since_last_poll > 0:
            events.append(VisionEvent(
                timestamp=now,
                source="vt",
                kind="vt_scroll",
                severity="info",
                data={"lines": self._vt.scrolls_since_last_poll},
            ))

        self._vt.reset_poll_counters()
        return events
