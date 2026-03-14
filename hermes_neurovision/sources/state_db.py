"""SQLite poller for ~/.hermes/state.db — sessions and messages."""

from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Dict, List, Optional, Tuple

from hermes_neurovision.events import VisionEvent

DEFAULT_PATH = os.path.expanduser("~/.hermes/state.db")


class StateDbSource:
    def __init__(self, path: str = DEFAULT_PATH):
        self._path = path
        self._last_message_id: int = self._get_current_max_message_id(path)
        self._active_session_id: Optional[str] = None
        self._last_model: Optional[str] = None
        self._last_tokens: Tuple[int, int] = (0, 0)
        self._session_start_time: Optional[float] = None
        self._last_duration_event: float = 0.0
        self._duration_event_interval = 300.0  # 5 minutes in seconds
        # Tool usage pattern tracking
        self._tool_history: List[Tuple[str, float]] = []  # (tool_name, timestamp)
        self._last_tool_name: Optional[str] = None
        self._tool_repeat_count: int = 0

    @staticmethod
    def _get_current_max_message_id(path: str) -> int:
        """Initialize to current max message ID so we only pick up new messages."""
        if not os.path.exists(path):
            return 0
        try:
            conn = sqlite3.connect(path, timeout=1.0)
            try:
                row = conn.execute("SELECT MAX(id) FROM messages").fetchone()
                return row[0] or 0
            finally:
                conn.close()
        except (sqlite3.Error, OSError):
            return 0

    def poll(self, since: float) -> List[VisionEvent]:
        if not os.path.exists(self._path):
            return []

        events: List[VisionEvent] = []
        try:
            conn = sqlite3.connect(self._path, timeout=1.0)
            conn.row_factory = sqlite3.Row
            try:
                self._poll_active_session(conn, events)
                self._poll_messages(conn, events)
                self._poll_tokens(conn, events)
                self._poll_session_duration(conn, events)
                self._detect_tool_patterns(events)
            finally:
                conn.close()
        except (sqlite3.Error, OSError):
            pass

        return events

    def _poll_active_session(self, conn, events):
        row = conn.execute(
            "SELECT id, model FROM sessions WHERE ended_at IS NULL ORDER BY started_at DESC LIMIT 1"
        ).fetchone()

        if row is None:
            return

        session_id = row["id"]
        model = row["model"]

        if session_id != self._active_session_id:
            self._active_session_id = session_id
            self._last_model = model
            # Get session start time for duration tracking
            start_row = conn.execute(
                "SELECT started_at FROM sessions WHERE id = ?",
                (session_id,)
            ).fetchone()
            if start_row:
                self._session_start_time = start_row["started_at"]
                self._last_duration_event = 0.0  # Reset duration tracker
            events.append(VisionEvent(
                timestamp=time.time(), source="state_db",
                kind="active_session", severity="info",
                data={"session_id": session_id, "model": model},
            ))

        if model != self._last_model:
            self._last_model = model
            events.append(VisionEvent(
                timestamp=time.time(), source="state_db",
                kind="model_switch", severity="info",
                data={"model": model, "session_id": session_id},
            ))

    def _poll_messages(self, conn, events):
        rows = conn.execute(
            "SELECT id, session_id, role, tool_name, tool_calls, timestamp FROM messages WHERE id > ? ORDER BY id",
            (self._last_message_id,)
        ).fetchall()

        for row in rows:
            self._last_message_id = row["id"]
            # Extract tool name: prefer tool_name column, fall back to parsing tool_calls JSON
            tool_name = row["tool_name"] or ""
            if not tool_name and row["tool_calls"]:
                try:
                    calls = json.loads(row["tool_calls"])
                    if calls and isinstance(calls, list):
                        tool_name = calls[0].get("function", {}).get("name", "")
                except (json.JSONDecodeError, (AttributeError, KeyError, IndexError)):
                    pass
            events.append(VisionEvent(
                timestamp=row["timestamp"], source="state_db",
                kind="message_added", severity="info",
                data={
                    "message_id": row["id"],
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "tool_name": tool_name,
                },
            ))

    def _poll_tokens(self, conn, events):
        if self._active_session_id is None:
            return

        row = conn.execute(
            "SELECT input_tokens, output_tokens FROM sessions WHERE id = ?",
            (self._active_session_id,)
        ).fetchone()

        if row is None:
            return

        input_t, output_t = row["input_tokens"] or 0, row["output_tokens"] or 0
        prev_in, prev_out = self._last_tokens

        if (input_t, output_t) != (prev_in, prev_out) and (prev_in > 0 or prev_out > 0):
            events.append(VisionEvent(
                timestamp=time.time(), source="state_db",
                kind="token_update", severity="info",
                data={
                    "input_tokens": input_t,
                    "output_tokens": output_t,
                    "delta_input": input_t - prev_in,
                    "delta_output": output_t - prev_out,
                },
            ))

        self._last_tokens = (input_t, output_t)

    def _poll_session_duration(self, conn, events):
        """Emit session duration events every 5 minutes."""
        if self._active_session_id is None or self._session_start_time is None:
            return

        now = time.time()
        duration = now - self._session_start_time

        # Emit event every 5 minutes
        if duration - self._last_duration_event >= self._duration_event_interval:
            self._last_duration_event = duration
            
            # Format duration nicely
            minutes = int(duration / 60)
            hours = minutes // 60
            remaining_mins = minutes % 60
            
            if hours > 0:
                duration_fmt = f"{hours}h{remaining_mins}m"
            else:
                duration_fmt = f"{minutes}m"
            
            events.append(VisionEvent(
                timestamp=now, source="state_db",
                kind="session_duration", severity="info",
                data={
                    "session_id": self._active_session_id,
                    "duration_seconds": int(duration),
                    "duration_formatted": duration_fmt,
                },
            ))

    def _detect_tool_patterns(self, events):
        """Detect tool usage patterns from recent events."""
        now = time.time()
        
        # Extract tool calls from message_added events and update history
        new_tool_count = 0
        for ev in events:
            if ev.kind == "message_added" and ev.data.get("tool_name"):
                tool_name = ev.data["tool_name"]
                self._tool_history.append((tool_name, ev.timestamp))
                new_tool_count += 1
                
                # Track tool chains (same tool repeated)
                if tool_name == self._last_tool_name:
                    self._tool_repeat_count += 1
                else:
                    self._last_tool_name = tool_name
                    self._tool_repeat_count = 1
        
        # Emit tool_chain if we hit the threshold
        if self._tool_repeat_count >= 3:
            events.append(VisionEvent(
                timestamp=now, source="state_db",
                kind="tool_chain", severity="info",
                data={
                    "tool_name": self._last_tool_name,
                    "repeat_count": self._tool_repeat_count,
                },
            ))
            self._tool_repeat_count = 0  # Reset after emitting
        
        # Detect tool bursts (5+ tools in 10 seconds)
        # Clean old entries first
        cutoff = now - 10.0
        self._tool_history = [(t, ts) for t, ts in self._tool_history if ts >= cutoff]
        
        # Check if we have a burst (5+ tools in recent history)
        if len(self._tool_history) >= 5 and new_tool_count > 0:
            # Only emit if we haven't emitted a burst event in the last second
            if not hasattr(self, '_last_burst_time') or (now - self._last_burst_time) > 1.0:
                time_span = now - self._tool_history[0][1] if self._tool_history else 0
                events.append(VisionEvent(
                    timestamp=now, source="state_db",
                    kind="tool_burst", severity="info",
                    data={
                        "tool_count": len(self._tool_history),
                        "time_span": round(time_span, 1),
                    },
                ))
                self._last_burst_time = now
