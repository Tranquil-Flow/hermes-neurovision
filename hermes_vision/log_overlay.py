"""Log overlay — fading scrolling text rendered over the neural network."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Tuple

from hermes_vision.events import VisionEvent

FADE_AFTER = 3.0    # seconds before dimming
EXPIRE_AFTER = 8.0  # seconds before removal

SOURCE_COLORS = {
    "agent": "cyan",
    "state_db": "white",
    "memory": "magenta",
    "cron": "cyan",
    "aegis": "yellow",
    "custom": "green",
}


@dataclass
class LogLine:
    text: str
    timestamp: float
    color: str


def _format_event(ev: VisionEvent) -> str:
    """Format event into a single log line."""
    ts = time.strftime("%H:%M:%S", time.localtime(ev.timestamp))
    data = ev.data

    if ev.kind == "agent_start":
        session = data.get("session_id", "")[:6]
        model = data.get("model", "")
        return f"[{ts}] agent:start session={session} model={model}"
    elif ev.kind == "agent_end":
        return f"[{ts}] agent:end"
    elif ev.kind == "agent_step":
        tools = data.get("tool_names", [])
        return f"[{ts}] agent:step tools={','.join(tools) if tools else 'none'}"
    elif ev.kind == "tool_call":
        name = data.get("tool_name", data.get("function_name", "?"))
        return f"[{ts}] > tool:{name}"
    elif ev.kind == "tool_complete":
        name = data.get("tool_name", "?")
        return f"[{ts}] < tool:{name}"
    elif ev.kind == "memory_created":
        name = data.get("name", data.get("path", "?"))
        return f"[{ts}] memory:created \"{name}\""
    elif ev.kind == "memory_accessed":
        name = data.get("name", "?")
        return f"[{ts}] memory:accessed \"{name}\""
    elif ev.kind == "token_update":
        inp = data.get("input_tokens", 0)
        out = data.get("output_tokens", 0)
        return f"[{ts}] tokens: {inp:,} in / {out:,} out"
    elif ev.kind == "cron_executing":
        return f"[{ts}] cron:executing"
    elif ev.kind == "cron_completed":
        job = data.get("output", "")
        return f"[{ts}] cron:completed {job}"
    elif ev.kind == "cron_failed":
        return f"[{ts}] cron:failed"
    elif ev.kind == "threat_blocked":
        cmd = data.get("decision", "")
        tool = data.get("tool_name", "")
        return f"[{ts}] aegis:blocked {cmd} ({tool})"
    elif ev.kind == "secret_redacted":
        return f"[{ts}] aegis:redacted"
    elif ev.kind == "secret_detected":
        return f"[{ts}] aegis:secret_detected"
    elif ev.kind == "model_switch":
        return f"[{ts}] model:{data.get('model', '?')}"
    elif ev.kind == "active_session":
        return f"[{ts}] session:{data.get('session_id', '?')[:6]}"
    elif ev.kind == "message_added":
        role = data.get("role", "?")
        tool = data.get("tool_name", "")
        suffix = f" ({tool})" if tool else ""
        return f"[{ts}] msg:{role}{suffix}"
    else:
        return f"[{ts}] {ev.kind}"


class LogOverlay:
    def __init__(self, max_lines: int = 20):
        self._lines: List[LogLine] = []
        self._max_lines = max_lines

    def add_event(self, event: VisionEvent) -> None:
        text = _format_event(event)
        color = SOURCE_COLORS.get(event.source, "white")
        self._lines.append(LogLine(text, event.timestamp, color))
        # Keep buffer bounded
        if len(self._lines) > self._max_lines * 2:
            self._lines = self._lines[-self._max_lines:]

    def get_visible_lines(self, now: float) -> List[Tuple[str, str, str]]:
        """Returns list of (text, brightness, color) tuples. brightness is 'bold' or 'dim'."""
        visible = []
        for line in self._lines:
            age = now - line.timestamp
            if age >= EXPIRE_AFTER:
                continue
            brightness = "dim" if age >= FADE_AFTER else "bold"
            visible.append((line.text, brightness, line.color))
        return visible[-self._max_lines:]
