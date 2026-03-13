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


def test_state_db_detects_session_duration():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        # Create session that started 6 minutes ago
        start_time = time.time() - 360.0  # 6 minutes
        conn = _create_test_db(path)
        conn.execute("INSERT INTO sessions VALUES ('s1','local','gpt-4',?,NULL,0,0,0,0,NULL)", (start_time,))
        conn.commit()
        conn.close()

        source = StateDbSource(path)
        # Set short interval for testing
        source._duration_event_interval = 300.0
        events = source.poll(0.0)
        
        # Should get active_session and session_duration
        kinds = [e.kind for e in events]
        assert "active_session" in kinds
        assert "session_duration" in kinds
        
        duration_ev = [e for e in events if e.kind == "session_duration"][0]
        assert duration_ev.data["duration_seconds"] >= 360
        assert "duration_formatted" in duration_ev.data
    finally:
        os.unlink(path)


def test_state_db_detects_tool_burst():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        conn = _create_test_db(path)
        conn.execute("INSERT INTO sessions VALUES ('s1','local','gpt-4',1000.0,NULL,0,0,0,0,NULL)")
        conn.commit()

        source = StateDbSource(path)
        source.poll(0.0)  # initial poll to establish session
        
        # Insert 5 tool calls in quick succession
        now = time.time()
        for i in range(5):
            conn.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?)",
                        (i+1, 's1', 'assistant', '', f'tool{i}', now + i, 10))
        conn.commit()
        
        events = source.poll(time.time())
        kinds = [e.kind for e in events]
        assert "tool_burst" in kinds, f"Expected tool_burst, got: {kinds}"
        
        burst_ev = [e for e in events if e.kind == "tool_burst"][0]
        assert burst_ev.data["tool_count"] == 5
        conn.close()
    finally:
        os.unlink(path)


def test_state_db_detects_tool_chain():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        conn = _create_test_db(path)
        conn.execute("INSERT INTO sessions VALUES ('s1','local','gpt-4',1000.0,NULL,0,0,0,0,NULL)")
        conn.commit()

        source = StateDbSource(path)
        source.poll(0.0)  # initial poll to establish session
        
        # Insert same tool 3 times
        now = time.time()
        for i in range(3):
            conn.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?)",
                        (i+1, 's1', 'assistant', '', 'read_file', now + i*2, 10))
        conn.commit()
        
        events = source.poll(time.time())
        kinds = [e.kind for e in events]
        assert "tool_chain" in kinds, f"Expected tool_chain, got: {kinds}"
        
        chain_ev = [e for e in events if e.kind == "tool_chain"][0]
        assert chain_ev.data["tool_name"] == "read_file"
        assert chain_ev.data["repeat_count"] >= 3
        conn.close()
    finally:
        os.unlink(path)


from hermes_vision.sources.memories import MemoriesSource


def test_memories_source_no_dir():
    source = MemoriesSource("/nonexistent/memories/")
    events = source.poll(0.0)
    assert events == []


def test_memories_source_detects_new_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        source = MemoriesSource(tmpdir)
        source.poll(0.0)  # baseline

        # Create a new file
        with open(os.path.join(tmpdir, "test.md"), "w") as f:
            f.write("memory content")

        events = source.poll(0.0)
        kinds = [e.kind for e in events]
        assert "memory_created" in kinds


from hermes_vision.sources.cron import CronSource


def test_cron_source_no_dir():
    source = CronSource("/nonexistent/cron/")
    events = source.poll(0.0)
    assert events == []


def test_cron_source_detects_lock():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write a jobs.json
        jobs_path = os.path.join(tmpdir, "jobs.json")
        with open(jobs_path, "w") as f:
            json.dump({"jobs": [{"id": "j1", "name": "test-job", "status": "active"}], "updated_at": ""}, f)

        source = CronSource(tmpdir)
        source.poll(0.0)  # baseline

        # Create lock file (indicates executing)
        with open(os.path.join(tmpdir, ".tick.lock"), "w") as f:
            f.write("locked")

        events = source.poll(0.0)
        kinds = [e.kind for e in events]
        assert "cron_executing" in kinds


from hermes_vision.sources.aegis import AegisSource


def test_aegis_source_no_dir():
    source = AegisSource("/nonexistent/audit.jsonl")
    events = source.poll(0.0)
    assert events == []


def test_aegis_source_reads_events():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = f.name
        f.write(json.dumps({
            "timestamp": 1710417293.567,
            "tool_name": "terminal",
            "decision": "DANGEROUS_COMMAND",
            "middleware": "AuditTrailMiddleware",
            "args_redacted": {"command": "rm -rf /", "_danger_type": "destructive file operation"},
        }) + "\n")
    try:
        source = AegisSource(path)
        events = source.poll(0.0)
        assert len(events) == 1
        assert events[0].kind == "threat_blocked"
        assert events[0].severity == "danger"
    finally:
        os.unlink(path)


def test_aegis_disabled():
    source = AegisSource("/nonexistent", enabled=False)
    events = source.poll(0.0)
    assert events == []


def test_hook_handler_writes_jsonl():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "events.jsonl")

        # Import and test the handle function directly
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "hook_handler",
            os.path.join(os.path.dirname(__file__), "..", "hermes_vision", "sources", "hook_handler.py")
        )
        module = importlib.util.module_from_spec(spec)

        # Patch the output path before loading
        os.environ["HERMES_VISION_EVENTS_PATH"] = output_path
        spec.loader.exec_module(module)

        # Simulate a hook call
        module.handle("agent:start", {"session_id": "test123", "platform": "local"})

        # Verify output
        with open(output_path) as f:
            line = f.readline()
            data = json.loads(line)
            assert data["event_type"] == "agent:start"
            assert data["context"]["session_id"] == "test123"
            assert "timestamp" in data

        del os.environ["HERMES_VISION_EVENTS_PATH"]


from hermes_vision.sources.trajectories import TrajectoriesSource


def test_trajectories_source_no_files():
    source = TrajectoriesSource("/nonexistent/success.jsonl", "/nonexistent/failed.jsonl")
    events = source.poll(0.0)
    assert events == []


def test_trajectories_source_reads_success():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = f.name
        f.write(json.dumps({
            "timestamp": time.time(),
            "trajectory_id": "traj123",
            "session_id": "sess456",
            "tool_calls": ["tool1", "tool2"],
            "outcome": "success",
        }) + "\n")
    try:
        source = TrajectoriesSource(success_path=path, failed_path="/nonexistent")
        events = source.poll(0.0)
        assert len(events) == 1
        assert events[0].kind == "trajectory_logged"
        assert events[0].source == "trajectories"
        assert events[0].data["trajectory_id"] == "traj123"
    finally:
        os.unlink(path)


def test_trajectories_source_reads_failed():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = f.name
        f.write(json.dumps({
            "timestamp": time.time(),
            "trajectory_id": "traj789",
            "session_id": "sess999",
            "tool_calls": [],
            "outcome": "failed",
        }) + "\n")
    try:
        source = TrajectoriesSource(success_path="/nonexistent", failed_path=path)
        events = source.poll(0.0)
        assert len(events) == 1
        assert events[0].kind == "trajectory_failed"
        assert events[0].severity == "warning"
        assert events[0].data["trajectory_id"] == "traj789"
    finally:
        os.unlink(path)
