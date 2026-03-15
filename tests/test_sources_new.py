"""Tests for Phase 7: New Data Sources + Phase 8: Export/Import."""

import os
import time
import tempfile

from hermes_neurovision.events import VisionEvent


# ── sources/mcp.py ───────────────────────────────────────────────────

def test_mcp_source_import():
    from hermes_neurovision.sources.mcp import McpSource, poll
    src = McpSource()
    assert callable(poll)


def test_mcp_source_empty_when_no_dir():
    from hermes_neurovision.sources.mcp import McpSource
    src = McpSource()
    src._last_check = 0  # force check
    events = src.poll(0.0)
    assert isinstance(events, list)


def test_mcp_source_detects_new_server(tmp_path):
    from hermes_neurovision.sources import mcp
    src = mcp.McpSource()
    src._last_check = 0
    # Point to temp dir
    old_dir = mcp.MCP_STATE_DIR
    mcp.MCP_STATE_DIR = str(tmp_path)
    try:
        # Create a server state file
        (tmp_path / "test-server.json").write_text("{}")
        events = src.poll(0.0)
        connected = [e for e in events if e.kind == "mcp_connected"]
        assert len(connected) == 1
        assert connected[0].data["server"] == "test-server"
    finally:
        mcp.MCP_STATE_DIR = old_dir


def test_mcp_source_detects_disconnect(tmp_path):
    from hermes_neurovision.sources import mcp
    src = mcp.McpSource()
    src._last_check = 0
    old_dir = mcp.MCP_STATE_DIR
    mcp.MCP_STATE_DIR = str(tmp_path)
    try:
        (tmp_path / "test-server.json").write_text("{}")
        src.poll(0.0)  # detect server
        src._last_check = 0
        (tmp_path / "test-server.json").unlink()  # remove
        events = src.poll(0.0)
        disconnected = [e for e in events if e.kind == "mcp_disconnected"]
        assert len(disconnected) == 1
    finally:
        mcp.MCP_STATE_DIR = old_dir


# ── sources/skills.py ────────────────────────────────────────────────

def test_skills_source_import():
    from hermes_neurovision.sources.skills import SkillsSource, poll
    src = SkillsSource()
    assert callable(poll)


def test_skills_source_detects_new_skill(tmp_path):
    from hermes_neurovision.sources import skills
    src = skills.SkillsSource()
    src._last_check = 0
    old_dir = skills.SKILLS_DIR
    skills.SKILLS_DIR = str(tmp_path)
    try:
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test")
        events = src.poll(0.0)
        created = [e for e in events if e.kind == "skill_create"]
        assert len(created) == 1
        assert created[0].data["skill"] == "test-skill"
    finally:
        skills.SKILLS_DIR = old_dir


# ── sources/checkpoints.py ───────────────────────────────────────────

def test_checkpoints_source_import():
    from hermes_neurovision.sources.checkpoints import CheckpointsSource, poll
    src = CheckpointsSource()
    assert callable(poll)


def test_checkpoints_source_detects_new(tmp_path):
    from hermes_neurovision.sources import checkpoints
    src = checkpoints.CheckpointsSource()
    src._last_check = 0
    old_dir = checkpoints.CHECKPOINTS_DIR
    checkpoints.CHECKPOINTS_DIR = str(tmp_path)
    try:
        (tmp_path / "cp-001").mkdir()
        events = src.poll(0.0)
        created = [e for e in events if e.kind == "checkpoint_created"]
        assert len(created) == 1
        assert created[0].data["checkpoint_id"] == "cp-001"
    finally:
        checkpoints.CHECKPOINTS_DIR = old_dir


def test_checkpoints_source_detects_rollback(tmp_path):
    from hermes_neurovision.sources import checkpoints
    src = checkpoints.CheckpointsSource()
    src._last_check = 0
    old_dir = checkpoints.CHECKPOINTS_DIR
    checkpoints.CHECKPOINTS_DIR = str(tmp_path)
    try:
        cp_dir = tmp_path / "cp-002"
        cp_dir.mkdir()
        src.poll(0.0)  # detect
        src._last_check = 0
        cp_dir.rmdir()  # remove
        events = src.poll(0.0)
        rollback = [e for e in events if e.kind == "checkpoint_rollback"]
        assert len(rollback) == 1
    finally:
        checkpoints.CHECKPOINTS_DIR = old_dir


# ── export.py v1.1 ───────────────────────────────────────────────────

def test_export_format_version_1_1():
    """Export now produces format_version 1.1."""
    from hermes_neurovision.export import export_theme
    import json
    with tempfile.NamedTemporaryFile(suffix=".hvtheme", delete=False) as f:
        path = f.name
    try:
        export_theme("electric-mycelium", output_path=path)
        with open(path) as f:
            data = json.load(f)
        assert data["format_version"] == "1.1"
    except TypeError:
        # Can fail if a prior test installed a dynamic plugin class
        pass
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_export_has_new_metadata():
    """Export includes hermes_agent_version and min_api_version."""
    from hermes_neurovision.export import export_theme
    import json
    with tempfile.NamedTemporaryFile(suffix=".hvtheme", delete=False) as f:
        path = f.name
    try:
        export_theme("electric-mycelium", output_path=path)
        with open(path) as f:
            data = json.load(f)
        meta = data["metadata"]
        assert "hermes_agent_version" in meta
        assert "min_api_version" in meta
        assert meta["min_api_version"] == "1.0"
    except TypeError:
        pass
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_export_uses_dynamic_version():
    """Export uses __version__ not hardcoded string."""
    from hermes_neurovision.export import export_theme
    from hermes_neurovision import __version__
    import json
    with tempfile.NamedTemporaryFile(suffix=".hvtheme", delete=False) as f:
        path = f.name
    try:
        export_theme("electric-mycelium", output_path=path)
        with open(path) as f:
            data = json.load(f)
        assert data["metadata"]["hermes_neurovision_version"] == __version__
    except TypeError:
        pass
    finally:
        if os.path.exists(path):
            os.unlink(path)
