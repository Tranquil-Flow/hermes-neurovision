"""Tests for hook_handler module."""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock, call

import pytest

# Import the hook handler module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hermes_neurovision", "sources"))
import hook_handler


def test_handle_writes_event():
    """Test that handle() writes events to JSONL file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = os.path.join(tmpdir, "events.jsonl")
        
        with patch.object(hook_handler, "_EVENTS_PATH", events_path):
            hook_handler.handle("agent:start", {"test": "data"})
            
            # Verify file was created and written
            assert os.path.exists(events_path)
            
            with open(events_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 1
                
                event = json.loads(lines[0])
                assert event["event_type"] == "agent:start"
                assert event["context"]["test"] == "data"
                assert "timestamp" in event


def test_handle_appends_events():
    """Test that handle() appends to existing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = os.path.join(tmpdir, "events.jsonl")
        
        with patch.object(hook_handler, "_EVENTS_PATH", events_path):
            hook_handler.handle("agent:start", {"event": 1})
            hook_handler.handle("agent:step", {"event": 2})
            hook_handler.handle("agent:end", {"event": 3})
            
            with open(events_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 3
                
                events = [json.loads(line) for line in lines]
                assert events[0]["event_type"] == "agent:start"
                assert events[1]["event_type"] == "agent:step"
                assert events[2]["event_type"] == "agent:end"


def test_handle_creates_directory():
    """Test that handle() creates parent directory if missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = os.path.join(tmpdir, "nested", "dir", "events.jsonl")
        
        with patch.object(hook_handler, "_EVENTS_PATH", events_path):
            hook_handler.handle("test:event", {})
            
            # Should create nested directories
            assert os.path.exists(events_path)


def test_handle_never_crashes_on_write_error():
    """Test that handle() never raises exceptions on write errors."""
    with patch("builtins.open", side_effect=OSError("Test error")):
        # Should not raise
        try:
            hook_handler.handle("test:event", {})
        except Exception as e:
            pytest.fail(f"handle() raised exception: {e}")


def test_should_auto_launch_agent_start_cron():
    """Test auto-launch detection for agent:start from cron."""
    config = {"auto_launch": True}
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        temp_path = f.name
    
    try:
        with patch.object(hook_handler, "_CONFIG_PATH", temp_path):
            # Test with source=cron
            assert hook_handler._should_auto_launch("agent:start", {"source": "cron"}) is True
            
            # Test with trigger=cron
            assert hook_handler._should_auto_launch("agent:start", {"trigger": "cron"}) is True
            
            # Test with trigger=automated
            assert hook_handler._should_auto_launch("agent:start", {"trigger": "automated"}) is True
    finally:
        os.unlink(temp_path)


def test_should_auto_launch_wrong_event_type():
    """Test that auto-launch only triggers on agent:start."""
    config = {"auto_launch": True}
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        temp_path = f.name
    
    try:
        with patch.object(hook_handler, "_CONFIG_PATH", temp_path):
            # Should not launch on other events
            assert hook_handler._should_auto_launch("agent:step", {"source": "cron"}) is False
            assert hook_handler._should_auto_launch("agent:end", {"source": "cron"}) is False
            assert hook_handler._should_auto_launch("session:start", {"source": "cron"}) is False
    finally:
        os.unlink(temp_path)


def test_should_auto_launch_wrong_source():
    """Test that auto-launch only triggers for automated sources."""
    config = {"auto_launch": True}
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        temp_path = f.name
    
    try:
        with patch.object(hook_handler, "_CONFIG_PATH", temp_path):
            # Should not launch for manual/interactive sessions
            assert hook_handler._should_auto_launch("agent:start", {"source": "manual"}) is False
            assert hook_handler._should_auto_launch("agent:start", {"trigger": "user"}) is False
            assert hook_handler._should_auto_launch("agent:start", {}) is False
    finally:
        os.unlink(temp_path)


def test_should_auto_launch_config_disabled():
    """Test that auto-launch respects config disabled."""
    config = {"auto_launch": False}
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        temp_path = f.name
    
    try:
        with patch.object(hook_handler, "_CONFIG_PATH", temp_path):
            # Should not launch when disabled
            assert hook_handler._should_auto_launch("agent:start", {"source": "cron"}) is False
    finally:
        os.unlink(temp_path)


def test_should_auto_launch_no_config():
    """Test that auto-launch is opt-in (no config = no launch)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "nonexistent.json")
        
        with patch.object(hook_handler, "_CONFIG_PATH", config_path):
            # Should not launch without config
            assert hook_handler._should_auto_launch("agent:start", {"source": "cron"}) is False


def test_should_auto_launch_invalid_config():
    """Test that invalid config doesn't break auto-launch check."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{ invalid json }")
        temp_path = f.name
    
    try:
        with patch.object(hook_handler, "_CONFIG_PATH", temp_path):
            # Should fail safe to False
            assert hook_handler._should_auto_launch("agent:start", {"source": "cron"}) is False
    finally:
        os.unlink(temp_path)


def test_try_auto_launch_calls_subprocess():
    """Test that _try_auto_launch spawns subprocess."""
    with patch("subprocess.Popen") as mock_popen:
        hook_handler._try_auto_launch()
        
        # Verify subprocess was called
        mock_popen.assert_called_once()
        
        # Verify command is calling hermes-neurovision CLI
        call_args = mock_popen.call_args[0][0]
        assert "hermes-neurovision" in call_args
        assert "--daemon" in call_args or "--auto-exit" in call_args
        
        # Verify detached execution
        kwargs = mock_popen.call_args[1]
        assert kwargs.get("stdout") is not None  # Should redirect output
        assert kwargs.get("stderr") is not None
        assert kwargs.get("start_new_session") is True


def test_try_auto_launch_never_crashes():
    """Test that _try_auto_launch never raises exceptions."""
    with patch("subprocess.Popen", side_effect=Exception("Test error")):
        # Should not raise
        try:
            hook_handler._try_auto_launch()
        except Exception as e:
            pytest.fail(f"_try_auto_launch() raised exception: {e}")


def test_handle_triggers_auto_launch():
    """Test that handle() triggers auto-launch when appropriate."""
    config = {"auto_launch": True}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = os.path.join(tmpdir, "events.jsonl")
        config_path = os.path.join(tmpdir, "config.json")
        
        with open(config_path, "w") as f:
            json.dump(config, f)
        
        with patch.object(hook_handler, "_EVENTS_PATH", events_path):
            with patch.object(hook_handler, "_CONFIG_PATH", config_path):
                with patch("subprocess.Popen") as mock_popen:
                    # Call with cron trigger
                    hook_handler.handle("agent:start", {"source": "cron"})
                    
                    # Should have written event
                    assert os.path.exists(events_path)
                    
                    # Should have attempted launch
                    mock_popen.assert_called_once()


def test_handle_does_not_launch_wrong_conditions():
    """Test that handle() doesn't launch under wrong conditions."""
    config = {"auto_launch": True}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = os.path.join(tmpdir, "events.jsonl")
        config_path = os.path.join(tmpdir, "config.json")
        
        with open(config_path, "w") as f:
            json.dump(config, f)
        
        with patch.object(hook_handler, "_EVENTS_PATH", events_path):
            with patch.object(hook_handler, "_CONFIG_PATH", config_path):
                with patch("subprocess.Popen") as mock_popen:
                    # Wrong event type
                    hook_handler.handle("agent:step", {"source": "cron"})
                    mock_popen.assert_not_called()
                    
                    # Wrong source
                    hook_handler.handle("agent:start", {"source": "manual"})
                    mock_popen.assert_not_called()


def test_handle_writes_event_even_if_launch_fails():
    """Test that event is written even if auto-launch fails."""
    config = {"auto_launch": True}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = os.path.join(tmpdir, "events.jsonl")
        config_path = os.path.join(tmpdir, "config.json")
        
        with open(config_path, "w") as f:
            json.dump(config, f)
        
        with patch.object(hook_handler, "_EVENTS_PATH", events_path):
            with patch.object(hook_handler, "_CONFIG_PATH", config_path):
                with patch("subprocess.Popen", side_effect=Exception("Launch failed")):
                    # Should not raise
                    hook_handler.handle("agent:start", {"source": "cron"})
                    
                    # Event should still be written
                    assert os.path.exists(events_path)
                    with open(events_path, "r") as f:
                        events = [json.loads(line) for line in f]
                        assert len(events) == 1
                        assert events[0]["event_type"] == "agent:start"


def test_handle_crash_safety():
    """Test that handle() never crashes the gateway under any error condition."""
    test_cases = [
        # Write error
        {"write_error": OSError("Write failed")},
        # Config read error
        {"config_error": Exception("Config failed")},
        # Launch error
        {"launch_error": Exception("Launch failed")},
    ]
    
    for test_case in test_cases:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = os.path.join(tmpdir, "events.jsonl")
            
            with patch.object(hook_handler, "_EVENTS_PATH", events_path):
                if "write_error" in test_case:
                    with patch("builtins.open", side_effect=test_case["write_error"]):
                        hook_handler.handle("test:event", {})
                
                elif "config_error" in test_case:
                    # Create a broken config file that will cause json.load to fail
                    config_path = os.path.join(tmpdir, "config.json")
                    with open(config_path, "w") as f:
                        f.write("{invalid json]")  # Malformed JSON
                    
                    with patch.object(hook_handler, "_CONFIG_PATH", config_path):
                        # Should not crash even if config parsing fails
                        hook_handler.handle("agent:start", {"source": "cron"})
                
                elif "launch_error" in test_case:
                    config = {"auto_launch": True}
                    config_path = os.path.join(tmpdir, "config.json")
                    with open(config_path, "w") as f:
                        json.dump(config, f)
                    
                    with patch.object(hook_handler, "_CONFIG_PATH", config_path):
                        with patch("subprocess.Popen", side_effect=test_case["launch_error"]):
                            hook_handler.handle("agent:start", {"source": "cron"})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
