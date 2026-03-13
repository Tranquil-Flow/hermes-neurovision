"""Tests for event source implementations."""

import json
import os
import tempfile
import time

from hermes_vision.sources.custom import poll as custom_poll, CustomSource


def test_custom_source_empty_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = f.name
    try:
        source = CustomSource(path)
        events = source.poll(0.0)
        assert events == []
    finally:
        os.unlink(path)


def test_custom_source_reads_new_lines():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = f.name
        f.write(json.dumps({"timestamp": time.time(), "event_type": "agent:start", "context": {"session_id": "abc"}}) + "\n")
    try:
        source = CustomSource(path)
        events = source.poll(0.0)
        assert len(events) == 1
        assert events[0].kind == "agent_start"
        assert events[0].source == "agent"

        # Second poll with no new data
        events2 = source.poll(time.time())
        assert events2 == []
    finally:
        os.unlink(path)


def test_custom_source_missing_file():
    source = CustomSource("/nonexistent/path.jsonl")
    events = source.poll(0.0)
    assert events == []


import sqlite3
from hermes_vision.sources.state_db import StateDbSource


def _create_test_db(path):
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY, source TEXT NOT NULL, model TEXT,
            started_at REAL NOT NULL, ended_at REAL,
            message_count INTEGER DEFAULT 0, tool_call_count INTEGER DEFAULT 0,
            input_tokens INTEGER DEFAULT 0, output_tokens INTEGER DEFAULT 0, title TEXT
        );
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES sessions(id),
            role TEXT NOT NULL, content TEXT, tool_name TEXT,
            timestamp REAL NOT NULL, token_count INTEGER
        );
    """)
    return conn


def test_state_db_no_file():
    source = StateDbSource("/nonexistent/state.db")
    events = source.poll(0.0)
    assert events == []


def test_state_db_detects_new_messages():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        conn = _create_test_db(path)
        conn.execute("INSERT INTO sessions VALUES ('s1','local','gpt-4',1000.0,NULL,0,0,0,0,NULL)")
        conn.execute("INSERT INTO messages VALUES (1,'s1','user','hello',NULL,1000.1,10)")
        conn.commit()
        conn.close()

        source = StateDbSource(path)
        events = source.poll(0.0)
        kinds = [e.kind for e in events]
        assert "active_session" in kinds
        assert "message_added" in kinds
    finally:
        os.unlink(path)


def test_state_db_detects_token_update():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        conn = _create_test_db(path)
        conn.execute("INSERT INTO sessions VALUES ('s1','local','gpt-4',1000.0,NULL,1,0,100,50,NULL)")
        conn.commit()

        source = StateDbSource(path)
        source.poll(0.0)  # initial poll sets baseline

        # Update tokens
        conn.execute("UPDATE sessions SET input_tokens=200, output_tokens=100 WHERE id='s1'")
        conn.commit()
        conn.close()

        events = source.poll(time.time())
        kinds = [e.kind for e in events]
        assert "token_update" in kinds
        token_ev = [e for e in events if e.kind == "token_update"][0]
        assert token_ev.data["delta_input"] == 100
    finally:
        os.unlink(path)
