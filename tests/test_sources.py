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
