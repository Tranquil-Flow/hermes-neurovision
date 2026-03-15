"""Log overlay — fading scrolling text rendered over the neural network."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Tuple

from hermes_neurovision.events import VisionEvent

EXPIRE_AFTER = 60.0   # seconds before removal
_STAGE_NORMAL = 15.0  # bold → normal after 15s
_STAGE_DIM    = 40.0  # normal → dim after 40s

SOURCE_COLORS = {
    "agent": "cyan",
    "state_db": "white",
    "memory": "magenta",
    "cron": "cyan",
    "aegis": "yellow",
    "custom": "green",
    "trajectories": "cyan",
    "docker": "green",
    "mcp": "green",
    "provider": "yellow",
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
    elif ev.kind == "trajectory_logged":
        tid = data.get("trajectory_id", "?")[:8]
        return f"[{ts}] trajectory:logged {tid}"
    elif ev.kind == "trajectory_failed":
        tid = data.get("trajectory_id", "?")[:8]
        return f"[{ts}] trajectory:failed {tid}"
    elif ev.kind == "session_duration":
        duration_fmt = data.get("duration_formatted", "?")
        return f"[{ts}] Session: {duration_fmt}"
    elif ev.kind == "tool_burst":
        count = data.get("tool_count", 0)
        time_span = data.get("time_span", 0)
        return f"[{ts}] Tool burst: {count} calls in {time_span}s"
    elif ev.kind == "tool_chain":
        tool = data.get("tool_name", "?")
        count = data.get("repeat_count", 0)
        return f"[{ts}] Tool chain: {tool} x{count}"
    elif ev.kind == "delegate_task_started":
        name = data.get("container", "?")
        return f"[{ts}] delegate:started [{name[:24]}]"
    elif ev.kind == "delegate_task_done":
        name = data.get("container", "?")
        return f"[{ts}] delegate:done [{name[:24]}]"
    # NEW — v0.2.0 event kinds
    elif ev.kind == "tool_error":
        name = data.get("tool_name", "?")
        err = data.get("error", "")[:40]
        return f"[{ts}] tool:error {name} — {err}"
    elif ev.kind == "compression_started":
        return f"[{ts}] compression:start"
    elif ev.kind == "compression_ended":
        before = data.get("tokens_before", "?")
        after = data.get("tokens_after", "?")
        return f"[{ts}] compression:end {before}→{after} tokens"
    elif ev.kind == "checkpoint_created":
        cid = data.get("checkpoint_id", "?")[:8]
        return f"[{ts}] checkpoint:created {cid}"
    elif ev.kind == "checkpoint_rollback":
        cid = data.get("checkpoint_id", "?")[:8]
        return f"[{ts}] checkpoint:rollback {cid}"
    elif ev.kind == "mcp_connected":
        server = data.get("server", "?")
        return f"[{ts}] mcp:connected {server}"
    elif ev.kind == "mcp_disconnected":
        server = data.get("server", "?")
        return f"[{ts}] mcp:disconnected {server}"
    elif ev.kind == "mcp_tool_call":
        tool = data.get("tool_name", "?")
        server = data.get("server", "")
        return f"[{ts}] mcp:tool {tool} ({server})"
    elif ev.kind == "provider_fallback":
        frm = data.get("from", "?")
        to = data.get("to", "?")
        return f"[{ts}] provider:fallback {frm}→{to}"
    elif ev.kind == "provider_error":
        provider = data.get("provider", "?")
        err = data.get("error", "")[:30]
        return f"[{ts}] provider:error {provider} — {err}"
    elif ev.kind == "subagent_started":
        name = data.get("name", data.get("goal", "?"))[:30]
        return f"[{ts}] subagent:start [{name}]"
    elif ev.kind == "subagent_ended":
        name = data.get("name", "?")[:30]
        return f"[{ts}] subagent:end [{name}]"
    else:
        return f"[{ts}] {ev.kind}"


class LogOverlay:
    def __init__(self, max_lines: int = 60):
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
        """Returns list of (text, brightness, color) tuples.
        brightness is 'bold' (0-15s), 'normal' (15-40s), or 'dim' (40-60s)."""
        visible = []
        for line in self._lines:
            age = now - line.timestamp
            if age >= EXPIRE_AFTER:
                continue
            if age < _STAGE_NORMAL:
                brightness = "bold"
            elif age < _STAGE_DIM:
                brightness = "normal"
            else:
                brightness = "dim"
            visible.append((line.text, brightness, line.color))
        return visible[-self._max_lines:]
