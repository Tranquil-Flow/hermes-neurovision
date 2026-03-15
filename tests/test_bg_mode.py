"""Tests for hermes_neurovision.bg_mode — background mode module.

All tests run without a real neurovision process. We mock subprocess.Popen
and os.kill so nothing is actually spawned or signalled.
"""

from __future__ import annotations

import json
import os
import signal
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def tmp_config(tmp_path, monkeypatch):
    """Redirect config/pid paths to a temp dir so tests don't touch ~/.hermes."""
    config_file = tmp_path / "config.json"
    pid_file = tmp_path / "bg_mode.pid"

    import hermes_neurovision.bg_mode as bgm
    monkeypatch.setattr(bgm, "_CONFIG_PATH", config_file)
    monkeypatch.setattr(bgm, "_PID_FILE", pid_file)
    return tmp_path


# ──────────────────────────────────────────────────────────────────────────────
# Config helpers
# ──────────────────────────────────────────────────────────────────────────────

def test_load_bg_config_defaults():
    from hermes_neurovision.bg_mode import load_bg_config, _BG_DEFAULTS
    cfg = load_bg_config()
    for key in _BG_DEFAULTS:
        assert key in cfg


def test_load_bg_config_missing_file():
    """Missing config file should return defaults without error."""
    from hermes_neurovision.bg_mode import load_bg_config
    cfg = load_bg_config()
    assert cfg["enabled"] is False
    assert cfg["gallery"] is True


def test_save_and_load_bg_config(tmp_config):
    from hermes_neurovision.bg_mode import save_bg_config, load_bg_config
    save_bg_config({"theme": "plasma-grid", "opacity_hint": 0.6})
    cfg = load_bg_config()
    assert cfg["theme"] == "plasma-grid"
    assert cfg["opacity_hint"] == pytest.approx(0.6)


def test_save_bg_config_merges_existing(tmp_config):
    """save_bg_config should not clobber existing keys."""
    from hermes_neurovision.bg_mode import save_bg_config, load_bg_config
    save_bg_config({"theme": "neural-sky"})
    save_bg_config({"opacity_hint": 0.3})
    cfg = load_bg_config()
    assert cfg["theme"] == "neural-sky"
    assert cfg["opacity_hint"] == pytest.approx(0.3)


def test_save_bg_config_preserves_other_keys(tmp_config):
    """Other top-level config keys must not be touched."""
    import hermes_neurovision.bg_mode as bgm
    bgm._CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    bgm._CONFIG_PATH.write_text(json.dumps({"default_theme": "storm-core", "bg_mode": {}}))
    from hermes_neurovision.bg_mode import save_bg_config
    save_bg_config({"theme": "tide-pool"})
    data = json.loads(bgm._CONFIG_PATH.read_text())
    assert data["default_theme"] == "storm-core"
    assert data["bg_mode"]["theme"] == "tide-pool"


# ──────────────────────────────────────────────────────────────────────────────
# PID tracking
# ──────────────────────────────────────────────────────────────────────────────

def test_write_and_read_pid(tmp_config):
    from hermes_neurovision.bg_mode import _write_pid, _read_pid
    _write_pid(12345)
    assert _read_pid() == 12345


def test_read_pid_missing_file():
    from hermes_neurovision.bg_mode import _read_pid
    assert _read_pid() is None


def test_clear_pid(tmp_config):
    from hermes_neurovision.bg_mode import _write_pid, _clear_pid, _read_pid
    _write_pid(999)
    _clear_pid()
    assert _read_pid() is None


def test_is_bg_running_no_pid():
    from hermes_neurovision.bg_mode import is_bg_running
    assert is_bg_running() is False


def test_is_bg_running_stale_pid(tmp_config):
    """PID file pointing to a dead process should return False and clean up."""
    from hermes_neurovision.bg_mode import _write_pid, is_bg_running, _read_pid
    _write_pid(9999999)  # Almost certainly not a real PID
    with patch("os.kill", side_effect=ProcessLookupError):
        result = is_bg_running()
    assert result is False
    assert _read_pid() is None


def test_is_bg_running_live_pid(tmp_config):
    from hermes_neurovision.bg_mode import _write_pid, is_bg_running
    _write_pid(os.getpid())  # Use our own PID — definitely alive
    with patch("os.kill", return_value=None):
        result = is_bg_running()
    assert result is True


def test_is_bg_running_permission_error(tmp_config):
    """PermissionError means the process exists but we don't own it."""
    from hermes_neurovision.bg_mode import _write_pid, is_bg_running
    _write_pid(1)
    with patch("os.kill", side_effect=PermissionError):
        result = is_bg_running()
    assert result is True


# ──────────────────────────────────────────────────────────────────────────────
# Platform / terminal detection
# ──────────────────────────────────────────────────────────────────────────────

def test_opacity_hint_known_terminals():
    from hermes_neurovision.bg_mode import _opacity_hint_for_terminal
    for term in ["iterm2", "kitty", "alacritty", "wezterm", "terminal"]:
        hint = _opacity_hint_for_terminal(term)
        assert isinstance(hint, str) and len(hint) > 10


def test_opacity_hint_unknown_terminal():
    from hermes_neurovision.bg_mode import _opacity_hint_for_terminal
    hint = _opacity_hint_for_terminal("unknown")
    assert "opacity" in hint.lower() or "terminal" in hint.lower()


# ──────────────────────────────────────────────────────────────────────────────
# Command builder
# ──────────────────────────────────────────────────────────────────────────────

def test_build_nv_command_gallery():
    from hermes_neurovision.bg_mode import _build_nv_command
    with patch("shutil.which", return_value="/usr/local/bin/hermes-neurovision"):
        cmd = _build_nv_command({"gallery": True, "theme_seconds": 20, "quiet": True})
    assert "--gallery" in cmd
    assert "--theme-seconds" in cmd
    assert "20" in cmd
    assert "--quiet" in cmd
    assert "--theme" not in cmd


def test_build_nv_command_single_theme():
    from hermes_neurovision.bg_mode import _build_nv_command
    with patch("shutil.which", return_value="/usr/local/bin/hermes-neurovision"):
        cmd = _build_nv_command({"gallery": False, "theme": "plasma-grid", "quiet": False})
    assert "--theme" in cmd
    assert "plasma-grid" in cmd
    assert "--gallery" not in cmd


def test_build_nv_command_no_binary_raises():
    from hermes_neurovision.bg_mode import _build_nv_command
    with patch("shutil.which", return_value=None):
        with patch("os.path.exists", return_value=False):
            with pytest.raises(RuntimeError, match="not found"):
                _build_nv_command({"gallery": False, "theme": "neural-sky"})


# ──────────────────────────────────────────────────────────────────────────────
# launch_bg
# ──────────────────────────────────────────────────────────────────────────────

def test_launch_bg_starts_process(tmp_config):
    from hermes_neurovision.bg_mode import launch_bg, _read_pid
    mock_proc = MagicMock()
    mock_proc.pid = 54321
    cfg = {"gallery": True, "theme": "neural-sky", "theme_seconds": 30, "quiet": True, "opacity_hint": 0.45}
    with patch("hermes_neurovision.bg_mode._build_nv_command", return_value=["hermes-neurovision", "--gallery"]):
        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            pid = launch_bg(cfg, verbose=False)
    assert pid == 54321
    assert _read_pid() == 54321
    mock_popen.assert_called_once()
    # Verify it's spawned detached
    call_kwargs = mock_popen.call_args[1]
    assert call_kwargs.get("start_new_session") is True
    assert call_kwargs.get("stdin") is not None  # DEVNULL


def test_launch_bg_skips_if_already_running(tmp_config):
    from hermes_neurovision.bg_mode import launch_bg, _write_pid
    _write_pid(11111)
    with patch("hermes_neurovision.bg_mode.is_bg_running", return_value=True):
        with patch("subprocess.Popen") as mock_popen:
            pid = launch_bg(verbose=False)
    mock_popen.assert_not_called()
    assert pid == 11111


# ──────────────────────────────────────────────────────────────────────────────
# stop_bg
# ──────────────────────────────────────────────────────────────────────────────

def test_stop_bg_not_running():
    from hermes_neurovision.bg_mode import stop_bg
    with patch("hermes_neurovision.bg_mode.is_bg_running", return_value=False):
        result = stop_bg(verbose=False)
    assert result is False


def test_stop_bg_kills_process(tmp_config):
    from hermes_neurovision.bg_mode import stop_bg, _write_pid, _read_pid
    _write_pid(77777)
    kill_calls = []
    def fake_kill(pid, sig):
        kill_calls.append((pid, sig))
        if sig == signal.SIGTERM:
            raise ProcessLookupError  # simulate fast clean exit

    with patch("hermes_neurovision.bg_mode.is_bg_running", return_value=True):
        with patch("os.kill", side_effect=fake_kill):
            result = stop_bg(verbose=False)

    assert result is True
    assert (77777, signal.SIGTERM) in kill_calls
    assert _read_pid() is None  # pid file cleaned up


# ──────────────────────────────────────────────────────────────────────────────
# status_bg
# ──────────────────────────────────────────────────────────────────────────────

def test_status_bg_not_running():
    from hermes_neurovision.bg_mode import status_bg
    with patch("hermes_neurovision.bg_mode.is_bg_running", return_value=False):
        s = status_bg()
    assert s["running"] is False
    assert s["pid"] is None
    assert "config" in s
    assert "terminal" in s


def test_status_bg_running(tmp_config):
    from hermes_neurovision.bg_mode import status_bg, _write_pid
    _write_pid(42)
    with patch("hermes_neurovision.bg_mode.is_bg_running", return_value=True):
        s = status_bg()
    assert s["running"] is True
    assert s["pid"] == 42


# ──────────────────────────────────────────────────────────────────────────────
# CLI integration — parse_args picks up --bg flags
# ──────────────────────────────────────────────────────────────────────────────

def test_parse_args_bg_start():
    from hermes_neurovision.cli import parse_args
    args = parse_args(["--bg"])
    assert args.bg == "start"


def test_parse_args_bg_stop():
    from hermes_neurovision.cli import parse_args
    args = parse_args(["--bg", "stop"])
    assert args.bg == "stop"


def test_parse_args_bg_status():
    from hermes_neurovision.cli import parse_args
    args = parse_args(["--bg", "status"])
    assert args.bg == "status"


def test_parse_args_bg_config():
    from hermes_neurovision.cli import parse_args
    args = parse_args(["--bg", "config", "--bg-theme", "plasma-grid", "--bg-opacity", "0.4"])
    assert args.bg == "config"
    assert args.bg_theme == "plasma-grid"
    assert args.bg_opacity == pytest.approx(0.4)


def test_parse_args_bg_with_options():
    from hermes_neurovision.cli import parse_args
    args = parse_args(["--bg", "start", "--bg-gallery", "--bg-theme-seconds", "15", "--bg-quiet"])
    assert args.bg_gallery is True
    assert args.bg_theme_seconds == pytest.approx(15.0)
    assert args.bg_quiet is True


def test_parse_args_no_bg_flag():
    """Without --bg, args.bg should be None — existing paths unaffected."""
    from hermes_neurovision.cli import parse_args
    args = parse_args([])
    assert args.bg is None


# ──────────────────────────────────────────────────────────────────────────────
# CLI main() early-exit dispatch
# ──────────────────────────────────────────────────────────────────────────────

def test_main_bg_dispatches_and_returns(tmp_config):
    """main() with --bg must call handle_bg_command and return before any curses."""
    from hermes_neurovision import cli
    dispatched = []
    def fake_handle(args):
        dispatched.append(args.bg)

    with patch("hermes_neurovision.bg_mode.handle_bg_command", fake_handle):
        cli.main(["--bg", "status"])

    assert dispatched == ["status"]


def test_main_without_bg_does_not_dispatch(tmp_config):
    """main() without --bg must never call handle_bg_command."""
    from hermes_neurovision import cli
    dispatched = []
    def fake_handle(args):
        dispatched.append(True)

    with patch("hermes_neurovision.bg_mode.handle_bg_command", fake_handle):
        with patch("hermes_neurovision.cli._run_live"):
            cli.main([])

    assert dispatched == []


# ──────────────────────────────────────────────────────────────────────────────
# handle_bg_command dispatch
# ──────────────────────────────────────────────────────────────────────────────

def test_handle_bg_command_start(tmp_config):
    from hermes_neurovision.bg_mode import handle_bg_command
    args = MagicMock()
    args.bg_action = "start"
    args.bg_theme = "neural-cascade"
    args.bg_gallery = False
    args.bg_opacity = 0.5
    args.bg_quiet = False

    with patch("hermes_neurovision.bg_mode.launch_bg") as mock_launch:
        # Provide bg attr via MagicMock (handle_bg_command reads args.bg_action)
        handle_bg_command(args)
    mock_launch.assert_called_once()


def test_handle_bg_command_stop(tmp_config):
    from hermes_neurovision.bg_mode import handle_bg_command
    args = MagicMock()
    args.bg_action = "stop"

    with patch("hermes_neurovision.bg_mode.stop_bg") as mock_stop:
        handle_bg_command(args)
    mock_stop.assert_called_once_with(verbose=True)


def test_handle_bg_command_status_prints(tmp_config, capsys):
    from hermes_neurovision.bg_mode import handle_bg_command
    args = MagicMock()
    args.bg_action = "status"

    with patch("hermes_neurovision.bg_mode.is_bg_running", return_value=False):
        with patch("hermes_neurovision.bg_mode._detect_terminal_app", return_value="kitty"):
            handle_bg_command(args)

    out = capsys.readouterr().out
    assert "Running" in out
    assert "kitty" in out.lower() or "Terminal" in out


def test_handle_bg_command_unknown_action(tmp_config):
    from hermes_neurovision.bg_mode import handle_bg_command
    args = MagicMock()
    args.bg_action = "explode"

    with pytest.raises(SystemExit):
        handle_bg_command(args)


# ──────────────────────────────────────────────────────────────────────────────
# Idempotency / edge cases
# ──────────────────────────────────────────────────────────────────────────────

def test_stop_then_start_cycle(tmp_config):
    """Start → stop → start should work cleanly."""
    from hermes_neurovision.bg_mode import launch_bg, stop_bg, _read_pid

    mock_proc = MagicMock()
    mock_proc.pid = 100
    cfg = {"gallery": True, "theme": "neural-sky", "theme_seconds": 30, "quiet": True, "opacity_hint": 0.45}

    with patch("hermes_neurovision.bg_mode._build_nv_command", return_value=["hermes-neurovision"]):
        with patch("subprocess.Popen", return_value=mock_proc):
            launch_bg(cfg, verbose=False)

    assert _read_pid() == 100

    with patch("hermes_neurovision.bg_mode.is_bg_running", return_value=True):
        with patch("os.kill", side_effect=ProcessLookupError):
            stop_bg(verbose=False)

    assert _read_pid() is None

    mock_proc2 = MagicMock()
    mock_proc2.pid = 200
    with patch("hermes_neurovision.bg_mode._build_nv_command", return_value=["hermes-neurovision"]):
        with patch("subprocess.Popen", return_value=mock_proc2):
            launch_bg(cfg, verbose=False)

    assert _read_pid() == 200


def test_corrupted_pid_file(tmp_config):
    """Corrupted PID file should be handled gracefully."""
    import hermes_neurovision.bg_mode as bgm
    bgm._PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    bgm._PID_FILE.write_text("not-a-number")
    from hermes_neurovision.bg_mode import _read_pid, is_bg_running
    assert _read_pid() is None
    assert is_bg_running() is False
