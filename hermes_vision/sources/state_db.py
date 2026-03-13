"""SQLite poller for ~/.hermes/state.db — sessions and messages."""

from __future__ import annotations

import os
import sqlite3
import time
from typing import Dict, List, Optional, Tuple

from hermes_vision.events import VisionEvent

DEFAULT_PATH = os.path.expanduser("~/.hermes/state.db")


class StateDbSource:
    def __init__(self, path: str = DEFAULT_PATH):
        self._path = path
        self._last_message_id: int = 0
        self._active_session_id: Optional[str] = None
        self._last_model: Optional[str] = None
        self._last_tokens: Tuple[int, int] = (0, 0)

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
            "SELECT id, session_id, role, tool_name, timestamp FROM messages WHERE id > ? ORDER BY id",
            (self._last_message_id,)
        ).fetchall()

        for row in rows:
            self._last_message_id = row["id"]
            events.append(VisionEvent(
                timestamp=row["timestamp"], source="state_db",
                kind="message_added", severity="info",
                data={
                    "message_id": row["id"],
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "tool_name": row["tool_name"],
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
