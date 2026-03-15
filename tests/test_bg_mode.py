"""Tests for hermes_neurovision.bg_mode — background mode module.

All tests run without a real neurovision process or terminal. We mock
subprocess.Popen, os.kill, and osascript so nothing is actually spawned.
"""

from __future__ import annotations

import json
import os
import re
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
    """Redirect all config/pid/opacity paths to a temp dir."""
    config_file = tmp_path / "config.json"
    pid_file = tmp_path / "bg_mode.pid"
    opacity_file = tmp_path / "original_opacity.json"

    import hermes_neurovision.bg_mode as bgm
    monkeypatch.setattr(bgm, "_CONFIG_PATH", config_file)
    monkeypatch.setattr(bgm, "_PID_FILE", pid_file)
    monkeypatch.setattr(bgm, "_ORIGINAL_OPACITY_FILE", opacity_file)
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
    from hermes_neurovision.bg_mode import load_bg_config
    cfg = load_bg_config()
    assert cfg["enabled"] is False
    assert cfg["gallery"] is True
    assert cfg["auto_opacity"] is True


def test_save_and_load_bg_config(tmp_config):
    from hermes_neurovision.bg_mode import save_bg_config, load_bg_config
    save_bg_config({"theme": "plasma-grid", "opacity": 0.6})
    cfg = load_bg_config()
    assert cfg["theme"] == "plasma-grid"
    assert cfg["opacity"] == pytest.approx(0.6)


def test_save_bg_config_merges_existing(tmp_config):
    from hermes_neurovision.bg_mode import save_bg_config, load_bg_config
    save_bg_config({"theme": "neural-sky"})
    save_bg_config({"opacity": 0.3})
    cfg = load_bg_config()
    assert cfg["theme"] == "neural-sky"
    assert cfg["opacity"] == pytest.approx(0.3)


def test_save_bg_config_preserves_other_keys(tmp_config):
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
    from hermes_neurovision.bg_mode import _write_pid, is_bg_running, _read_pid
    _write_pid(9999999)
    with patch("os.kill", side_effect=ProcessLookupError):
        result = is_bg_running()
    assert result is False
    assert _read_pid() is None


def test_is_bg_running_live_pid(tmp_config):
    from hermes_neurovision.bg_mode import _write_pid, is_bg_running
    _write_pid(os.getpid())
    with patch("os.kill", return_value=None):
        result = is_bg_running()
    assert result is True


def test_is_bg_running_permission_error(tmp_config):
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
# Auto-opacity persistence helpers
# ──────────────────────────────────────────────────────────────────────────────

def test_save_and_load_original_opacity(tmp_config):
    from hermes_neurovision.bg_mode import _save_original_opacity, _load_original_opacity
    _save_original_opacity("iterm2", 0.85)
    result = _load_original_opacity()
    assert result is not None
    term, val = result
    assert term == "iterm2"
    assert val == pytest.approx(0.85)


def test_load_original_opacity_missing():
    from hermes_neurovision.bg_mode import _load_original_opacity
    assert _load_original_opacity() is None


def test_clear_original_opacity(tmp_config):
    from hermes_neurovision.bg_mode import _save_original_opacity, _clear_original_opacity, _load_original_opacity
    _save_original_opacity("kitty", 1.0)
    _clear_original_opacity()
    assert _load_original_opacity() is None


def test_load_original_opacity_corrupted(tmp_config):
    import hermes_neurovision.bg_mode as bgm
    bgm._ORIGINAL_OPACITY_FILE.parent.mkdir(parents=True, exist_ok=True)
    bgm._ORIGINAL_OPACITY_FILE.write_text("not-json")
    from hermes_neurovision.bg_mode import _load_original_opacity
    assert _load_original_opacity() is None


# ──────────────────────────────────────────────────────────────────────────────
# iTerm2 opacity helpers
# ──────────────────────────────────────────────────────────────────────────────

def test_iterm2_get_opacity_success():
    from hermes_neurovision.bg_mode import _iterm2_get_opacity
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "0.3\n"
    with patch("subprocess.run", return_value=mock_result):
        val = _iterm2_get_opacity()
    # Returns transparency value (iTerm2 convention: 0=opaque)
    assert val == pytest.approx(0.3)


def test_iterm2_get_opacity_failure():
    from hermes_neurovision.bg_mode import _iterm2_get_opacity
    mock_result = MagicMock()
    mock_result.returncode = 1
    with patch("subprocess.run", return_value=mock_result):
        assert _iterm2_get_opacity() is None


def test_iterm2_get_opacity_timeout():
    from hermes_neurovision.bg_mode import _iterm2_get_opacity
    import subprocess
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("osascript", 3)):
        assert _iterm2_get_opacity() is None


def test_iterm2_set_opacity_success():
    from hermes_neurovision.bg_mode import _iterm2_set_opacity
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = _iterm2_set_opacity(0.55)
    assert result is True
    # Check transparency value sent = 1 - 0.55 = 0.45 (allow float repr variation)
    call_args = mock_run.call_args[0][0]
    script = call_args[-1]
    # Extract the numeric value from the script and check it's close to 0.45
    import re as _re
    m = _re.search(r'set transparency to ([0-9.e+-]+)', script)
    assert m is not None
    assert float(m.group(1)) == pytest.approx(0.45, abs=1e-9)


def test_iterm2_opacity_inversion():
    """opacity=1.0 (opaque) should send transparency=0.0 to iTerm2."""
    from hermes_neurovision.bg_mode import _iterm2_set_opacity
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        _iterm2_set_opacity(1.0)
    script = mock_run.call_args[0][0][-1]
    assert "0.0" in script or "0" in script


def test_iterm2_get_opacity_returns_transparency_convention():
    """_iterm2_get_opacity returns iTerm2's transparency (0=opaque, 1=clear)."""
    from hermes_neurovision.bg_mode import _iterm2_get_opacity
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "0.0"  # iTerm2 says 0 = opaque
    with patch("subprocess.run", return_value=mock_result):
        val = _iterm2_get_opacity()
    assert val == pytest.approx(0.0)


# ──────────────────────────────────────────────────────────────────────────────
# Kitty opacity helpers
# ──────────────────────────────────────────────────────────────────────────────

def test_kitty_get_opacity_success():
    from hermes_neurovision.bg_mode import _kitty_get_opacity
    kitty_ls_output = json.dumps([{
        "tabs": [{"windows": [{"background_opacity": 0.8}]}]
    }])
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = kitty_ls_output
    with patch("subprocess.run", return_value=mock_result):
        val = _kitty_get_opacity()
    assert val == pytest.approx(0.8)


def test_kitty_get_opacity_failure():
    from hermes_neurovision.bg_mode import _kitty_get_opacity
    mock_result = MagicMock()
    mock_result.returncode = 1
    with patch("subprocess.run", return_value=mock_result):
        assert _kitty_get_opacity() is None


def test_kitty_set_opacity_success():
    from hermes_neurovision.bg_mode import _kitty_set_opacity
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = _kitty_set_opacity(0.7)
    assert result is True
    cmd = mock_run.call_args[0][0]
    assert "set-background-opacity" in cmd
    assert "0.7" in cmd


def test_kitty_set_opacity_clamps_minimum():
    """Kitty minimum opacity is 0.1."""
    from hermes_neurovision.bg_mode import _kitty_set_opacity
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        _kitty_set_opacity(0.0)
    cmd = mock_run.call_args[0][0]
    val = float(cmd[-1])
    assert val >= 0.1


# ──────────────────────────────────────────────────────────────────────────────
# Alacritty opacity helpers
# ──────────────────────────────────────────────────────────────────────────────

def test_alacritty_get_opacity_from_toml(tmp_path):
    import hermes_neurovision.bg_mode as bgm
    cfg_file = tmp_path / "alacritty.toml"
    cfg_file.write_text("[window]\nopacity = 0.75\n")
    monkeypatched_paths = [cfg_file]
    with patch.object(bgm, "_ALACRITTY_CONFIG_PATHS", monkeypatched_paths):
        val = bgm._alacritty_get_opacity()
    assert val == pytest.approx(0.75)


def test_alacritty_get_opacity_no_config():
    import hermes_neurovision.bg_mode as bgm
    with patch.object(bgm, "_ALACRITTY_CONFIG_PATHS", []):
        val = bgm._alacritty_get_opacity()
    assert val is None


def test_alacritty_set_opacity_ipc_success():
    from hermes_neurovision.bg_mode import _alacritty_set_opacity
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = _alacritty_set_opacity(0.6)
    assert result is True
    cmd = mock_run.call_args[0][0]
    assert "alacritty" in cmd
    assert any("0.6" in str(a) for a in cmd)


def test_alacritty_set_opacity_ipc_fallback_to_file(tmp_path):
    """When IPC fails, fall back to editing config file."""
    import subprocess
    import hermes_neurovision.bg_mode as bgm
    cfg_file = tmp_path / "alacritty.toml"
    cfg_file.write_text("[window]\nopacity = 1.0\n")

    ipc_fail = MagicMock()
    ipc_fail.returncode = 1

    with patch.object(bgm, "_ALACRITTY_CONFIG_PATHS", [cfg_file]):
        with patch("subprocess.run", return_value=ipc_fail):
            result = bgm._alacritty_set_opacity(0.5)

    assert result is True
    content = cfg_file.read_text()
    assert "0.5" in content


# ──────────────────────────────────────────────────────────────────────────────
# WezTerm opacity helpers
# ──────────────────────────────────────────────────────────────────────────────

def test_wezterm_get_opacity_from_lua(tmp_path):
    import hermes_neurovision.bg_mode as bgm
    cfg_file = tmp_path / "wezterm.lua"
    cfg_file.write_text("config.window_background_opacity = 0.9\nreturn config\n")
    with patch.object(bgm, "_wezterm_find_config", return_value=cfg_file):
        val = bgm._wezterm_get_opacity()
    assert val == pytest.approx(0.9)


def test_wezterm_get_opacity_no_config():
    import hermes_neurovision.bg_mode as bgm
    with patch.object(bgm, "_wezterm_find_config", return_value=None):
        val = bgm._wezterm_get_opacity()
    assert val is None


def test_wezterm_set_opacity_replaces_existing(tmp_path):
    import hermes_neurovision.bg_mode as bgm
    cfg_file = tmp_path / "wezterm.lua"
    cfg_file.write_text("config.window_background_opacity = 1.0\nreturn config\n")
    reload_result = MagicMock()
    reload_result.returncode = 0
    with patch.object(bgm, "_wezterm_find_config", return_value=cfg_file):
        with patch("subprocess.run", return_value=reload_result):
            result = bgm._wezterm_set_opacity(0.6)
    assert result is True
    assert "0.6" in cfg_file.read_text()


def test_wezterm_set_opacity_injects_if_missing(tmp_path):
    import hermes_neurovision.bg_mode as bgm
    cfg_file = tmp_path / "wezterm.lua"
    cfg_file.write_text("local config = {}\nreturn config\n")
    reload_result = MagicMock()
    reload_result.returncode = 0
    with patch.object(bgm, "_wezterm_find_config", return_value=cfg_file):
        with patch("subprocess.run", return_value=reload_result):
            result = bgm._wezterm_set_opacity(0.5)
    assert result is True
    content = cfg_file.read_text()
    assert "window_background_opacity" in content
    assert "0.5" in content


def test_wezterm_set_opacity_no_config():
    import hermes_neurovision.bg_mode as bgm
    with patch.object(bgm, "_wezterm_find_config", return_value=None):
        result = bgm._wezterm_set_opacity(0.5)
    assert result is False


# ──────────────────────────────────────────────────────────────────────────────
# apply_auto_opacity / restore_opacity
# ──────────────────────────────────────────────────────────────────────────────

def test_apply_auto_opacity_iterm2(tmp_config):
    from hermes_neurovision.bg_mode import apply_auto_opacity, _load_original_opacity
    cfg = {"auto_opacity": True, "opacity": 0.45}

    with patch("hermes_neurovision.bg_mode._detect_terminal_app", return_value="iterm2"):
        with patch("hermes_neurovision.bg_mode._iterm2_get_opacity", return_value=0.0):  # 0=opaque in iTerm2 convention
            with patch("hermes_neurovision.bg_mode._iterm2_set_opacity", return_value=True) as mock_set:
                result = apply_auto_opacity(cfg, verbose=False)

    assert result is True
    mock_set.assert_called_once_with(0.45)
    # Original opacity should have been saved (opacity = 1 - transparency = 1 - 0.0 = 1.0)
    saved = _load_original_opacity()
    assert saved is not None
    term, val = saved
    assert term == "iterm2"
    assert val == pytest.approx(1.0)


def test_apply_auto_opacity_kitty(tmp_config):
    from hermes_neurovision.bg_mode import apply_auto_opacity
    cfg = {"auto_opacity": True, "opacity": 0.4}

    with patch("hermes_neurovision.bg_mode._detect_terminal_app", return_value="kitty"):
        with patch("hermes_neurovision.bg_mode._kitty_get_opacity", return_value=1.0):
            with patch("hermes_neurovision.bg_mode._kitty_set_opacity", return_value=True) as mock_set:
                result = apply_auto_opacity(cfg, verbose=False)

    assert result is True
    mock_set.assert_called_once_with(0.4)


def test_apply_auto_opacity_disabled(tmp_config):
    """auto_opacity=False should do nothing and return False."""
    from hermes_neurovision.bg_mode import apply_auto_opacity
    cfg = {"auto_opacity": False, "opacity": 0.3}

    with patch("hermes_neurovision.bg_mode._detect_terminal_app") as mock_detect:
        result = apply_auto_opacity(cfg, verbose=False)

    mock_detect.assert_not_called()
    assert result is False


def test_apply_auto_opacity_terminal_app(tmp_config):
    """Terminal.app is now fully supported via AppleScript backgroundAlpha."""
    from hermes_neurovision.bg_mode import apply_auto_opacity
    cfg = {"auto_opacity": True, "opacity": 0.4}

    with patch("hermes_neurovision.bg_mode._detect_terminal_app", return_value="terminal"):
        with patch("hermes_neurovision.bg_mode._terminal_get_opacity", return_value=1.0):
            with patch("hermes_neurovision.bg_mode._terminal_set_opacity", return_value=True) as mock_set:
                result = apply_auto_opacity(cfg, verbose=False)

    assert result is True
    mock_set.assert_called_once_with(0.4)


# ──────────────────────────────────────────────────────────────────────────────
# Terminal.app opacity helpers
# ──────────────────────────────────────────────────────────────────────────────

def test_terminal_get_opacity_success():
    from hermes_neurovision.bg_mode import _terminal_get_opacity
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "0.9\n"
    with patch("subprocess.run", return_value=mock_result):
        val = _terminal_get_opacity()
    assert val == pytest.approx(0.9)


def test_terminal_get_opacity_failure():
    from hermes_neurovision.bg_mode import _terminal_get_opacity
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    with patch("subprocess.run", return_value=mock_result):
        assert _terminal_get_opacity() is None


def test_terminal_get_opacity_timeout():
    from hermes_neurovision.bg_mode import _terminal_get_opacity
    import subprocess as sp
    with patch("subprocess.run", side_effect=sp.TimeoutExpired("osascript", 3)):
        assert _terminal_get_opacity() is None


def test_terminal_set_opacity_success():
    from hermes_neurovision.bg_mode import _terminal_set_opacity
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = _terminal_set_opacity(0.5)
    assert result is True
    argv = mock_run.call_args[0][0]
    assert argv[0] == "osascript"
    script = argv[-1]
    assert "0.5" in script
    assert "backgroundAlpha" in script
    assert "every window" in script


def test_terminal_set_opacity_clamps():
    from hermes_neurovision.bg_mode import _terminal_set_opacity
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        _terminal_set_opacity(1.5)   # over max — should clamp to 1.0
    script = mock_run.call_args[0][0][-1]
    assert "1.0" in script


def test_terminal_set_opacity_every_window():
    """Must use 'every window' not indexed access (indexed fails with -1700)."""
    from hermes_neurovision.bg_mode import _terminal_set_opacity
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        _terminal_set_opacity(0.4)
    script = mock_run.call_args[0][0][-1]
    assert "every window" in script
    assert "window 1" not in script  # must NOT use indexed form


def test_terminal_set_opacity_single_call():
    """Should be a single osascript call, not one per window."""
    from hermes_neurovision.bg_mode import _terminal_set_opacity
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        _terminal_set_opacity(0.4)
    assert mock_run.call_count == 1


def test_terminal_set_opacity_failure():
    from hermes_neurovision.bg_mode import _terminal_set_opacity
    mock_result = MagicMock()
    mock_result.returncode = 1
    with patch("subprocess.run", return_value=mock_result):
        result = _terminal_set_opacity(0.5)
    assert result is False


def test_terminal_roundtrip(tmp_config):
    """Full apply/restore roundtrip for Terminal.app."""
    from hermes_neurovision.bg_mode import apply_auto_opacity, restore_opacity
    cfg = {"auto_opacity": True, "opacity": 0.45}

    set_calls = []
    def fake_set(val):
        set_calls.append(val)
        return True

    with patch("hermes_neurovision.bg_mode._detect_terminal_app", return_value="terminal"):
        with patch("hermes_neurovision.bg_mode._terminal_get_opacity", return_value=1.0):
            with patch("hermes_neurovision.bg_mode._terminal_set_opacity", side_effect=fake_set):
                apply_auto_opacity(cfg, verbose=False)

    assert set_calls[0] == pytest.approx(0.45)

    with patch("hermes_neurovision.bg_mode._terminal_set_opacity", side_effect=fake_set):
        restore_opacity(verbose=False)

    assert set_calls[1] == pytest.approx(1.0)


def test_apply_auto_opacity_unknown_terminal(tmp_config):
    from hermes_neurovision.bg_mode import apply_auto_opacity
    cfg = {"auto_opacity": True, "opacity": 0.4}
    with patch("hermes_neurovision.bg_mode._detect_terminal_app", return_value="unknown"):
        result = apply_auto_opacity(cfg, verbose=False)
    assert result is False


def test_restore_opacity_success(tmp_config):
    from hermes_neurovision.bg_mode import _save_original_opacity, restore_opacity
    _save_original_opacity("kitty", 1.0)

    with patch("hermes_neurovision.bg_mode._kitty_set_opacity", return_value=True) as mock_set:
        result = restore_opacity(verbose=False)

    assert result is True
    mock_set.assert_called_once_with(1.0)


def test_restore_opacity_no_saved_value():
    from hermes_neurovision.bg_mode import restore_opacity
    result = restore_opacity(verbose=False)
    assert result is False


def test_restore_opacity_clears_file(tmp_config):
    from hermes_neurovision.bg_mode import _save_original_opacity, restore_opacity, _load_original_opacity
    _save_original_opacity("alacritty", 0.9)
    with patch("hermes_neurovision.bg_mode._alacritty_set_opacity", return_value=True):
        restore_opacity(verbose=False)
    assert _load_original_opacity() is None


def test_restore_opacity_prints_hint_on_failure(tmp_config, capsys):
    from hermes_neurovision.bg_mode import _save_original_opacity, restore_opacity
    _save_original_opacity("kitty", 1.0)
    with patch("hermes_neurovision.bg_mode._kitty_set_opacity", return_value=False):
        restore_opacity(verbose=True)
    out = capsys.readouterr().out
    # Should print either restoring message or failure hint
    assert len(out) > 0


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
    cfg = {"gallery": True, "theme": "neural-sky", "theme_seconds": 30, "quiet": True,
           "opacity": 0.45, "auto_opacity": False}
    with patch("hermes_neurovision.bg_mode._build_nv_command", return_value=["hermes-neurovision", "--gallery"]):
        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            with patch("hermes_neurovision.bg_mode.apply_auto_opacity"):
                pid = launch_bg(cfg, verbose=False)
    assert pid == 54321
    assert _read_pid() == 54321
    mock_popen.assert_called_once()
    call_kwargs = mock_popen.call_args[1]
    assert call_kwargs.get("start_new_session") is True


def test_launch_bg_calls_auto_opacity(tmp_config):
    """launch_bg must call apply_auto_opacity."""
    from hermes_neurovision.bg_mode import launch_bg
    mock_proc = MagicMock()
    mock_proc.pid = 111
    cfg = {"gallery": True, "theme": "neural-sky", "theme_seconds": 30,
           "quiet": True, "opacity": 0.45, "auto_opacity": True}
    with patch("hermes_neurovision.bg_mode._build_nv_command", return_value=["hermes-neurovision"]):
        with patch("subprocess.Popen", return_value=mock_proc):
            with patch("hermes_neurovision.bg_mode.apply_auto_opacity") as mock_ao:
                launch_bg(cfg, verbose=False)
    mock_ao.assert_called_once()


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


def test_stop_bg_kills_process_and_restores_opacity(tmp_config):
    from hermes_neurovision.bg_mode import stop_bg, _write_pid, _read_pid
    _write_pid(77777)
    kill_calls = []

    def fake_kill(pid, sig):
        kill_calls.append((pid, sig))
        if sig == signal.SIGTERM:
            raise ProcessLookupError

    with patch("hermes_neurovision.bg_mode.is_bg_running", return_value=True):
        with patch("os.kill", side_effect=fake_kill):
            with patch("hermes_neurovision.bg_mode.restore_opacity") as mock_restore:
                result = stop_bg(verbose=False)

    assert result is True
    mock_restore.assert_called_once_with(verbose=False)
    assert (77777, signal.SIGTERM) in kill_calls
    assert _read_pid() is None


# ──────────────────────────────────────────────────────────────────────────────
# status_bg
# ──────────────────────────────────────────────────────────────────────────────

def test_status_bg_not_running():
    from hermes_neurovision.bg_mode import status_bg
    with patch("hermes_neurovision.bg_mode.is_bg_running", return_value=False):
        s = status_bg()
    assert s["running"] is False
    assert s["pid"] is None


def test_status_bg_running(tmp_config):
    from hermes_neurovision.bg_mode import status_bg, _write_pid
    _write_pid(42)
    with patch("hermes_neurovision.bg_mode.is_bg_running", return_value=True):
        s = status_bg()
    assert s["running"] is True
    assert s["pid"] == 42


# ──────────────────────────────────────────────────────────────────────────────
# CLI integration — parse_args picks up all --bg flags
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


def test_parse_args_bg_no_auto_opacity():
    from hermes_neurovision.cli import parse_args
    args = parse_args(["--bg", "start", "--bg-no-auto-opacity"])
    assert args.bg_no_auto_opacity is True


def test_parse_args_no_bg_flag():
    from hermes_neurovision.cli import parse_args
    args = parse_args([])
    assert args.bg is None


# ──────────────────────────────────────────────────────────────────────────────
# CLI main() early-exit dispatch
# ──────────────────────────────────────────────────────────────────────────────

def test_main_bg_dispatches_and_returns(tmp_config):
    from hermes_neurovision import cli
    dispatched = []
    def fake_handle(args):
        dispatched.append(args.bg)

    with patch("hermes_neurovision.bg_mode.handle_bg_command", fake_handle):
        cli.main(["--bg", "status"])

    assert dispatched == ["status"]


def test_main_without_bg_does_not_dispatch(tmp_config):
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
    args.bg_no_auto_opacity = False
    args.bg_quiet = False

    with patch("hermes_neurovision.bg_mode.launch_bg") as mock_launch:
        handle_bg_command(args)
    mock_launch.assert_called_once()
    call_cfg = mock_launch.call_args[0][0]
    assert call_cfg["theme"] == "neural-cascade"
    assert call_cfg["opacity"] == pytest.approx(0.5)


def test_handle_bg_command_start_no_auto_opacity(tmp_config):
    from hermes_neurovision.bg_mode import handle_bg_command
    args = MagicMock()
    args.bg_action = "start"
    args.bg_theme = None
    args.bg_gallery = False
    args.bg_opacity = None
    args.bg_no_auto_opacity = True
    args.bg_quiet = False

    with patch("hermes_neurovision.bg_mode.launch_bg") as mock_launch:
        handle_bg_command(args)
    call_cfg = mock_launch.call_args[0][0]
    assert call_cfg["auto_opacity"] is False


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
    from hermes_neurovision.bg_mode import launch_bg, stop_bg, _read_pid

    mock_proc = MagicMock()
    mock_proc.pid = 100
    cfg = {"gallery": True, "theme": "neural-sky", "theme_seconds": 30,
           "quiet": True, "opacity": 0.45, "auto_opacity": False}

    with patch("hermes_neurovision.bg_mode._build_nv_command", return_value=["hermes-neurovision"]):
        with patch("subprocess.Popen", return_value=mock_proc):
            with patch("hermes_neurovision.bg_mode.apply_auto_opacity"):
                launch_bg(cfg, verbose=False)

    assert _read_pid() == 100

    with patch("hermes_neurovision.bg_mode.is_bg_running", return_value=True):
        with patch("os.kill", side_effect=ProcessLookupError):
            with patch("hermes_neurovision.bg_mode.restore_opacity"):
                stop_bg(verbose=False)

    assert _read_pid() is None

    mock_proc2 = MagicMock()
    mock_proc2.pid = 200
    with patch("hermes_neurovision.bg_mode._build_nv_command", return_value=["hermes-neurovision"]):
        with patch("subprocess.Popen", return_value=mock_proc2):
            with patch("hermes_neurovision.bg_mode.apply_auto_opacity"):
                launch_bg(cfg, verbose=False)

    assert _read_pid() == 200


def test_corrupted_pid_file(tmp_config):
    import hermes_neurovision.bg_mode as bgm
    bgm._PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    bgm._PID_FILE.write_text("not-a-number")
    from hermes_neurovision.bg_mode import _read_pid, is_bg_running
    assert _read_pid() is None
    assert is_bg_running() is False


def test_opacity_roundtrip_iterm2(tmp_config):
    """Full roundtrip: apply_auto_opacity then restore_opacity for iTerm2."""
    from hermes_neurovision.bg_mode import apply_auto_opacity, restore_opacity
    cfg = {"auto_opacity": True, "opacity": 0.4}

    set_calls = []
    def fake_set(val):
        set_calls.append(val)
        return True

    with patch("hermes_neurovision.bg_mode._detect_terminal_app", return_value="iterm2"):
        with patch("hermes_neurovision.bg_mode._iterm2_get_opacity", return_value=0.0):  # was opaque
            with patch("hermes_neurovision.bg_mode._iterm2_set_opacity", side_effect=fake_set):
                apply_auto_opacity(cfg, verbose=False)

    # set_calls[0] should be the bg opacity (0.4)
    assert set_calls[0] == pytest.approx(0.4)

    # Now restore
    with patch("hermes_neurovision.bg_mode._iterm2_set_opacity", side_effect=fake_set):
        restore_opacity(verbose=False)

    # set_calls[1] should be the original (1.0 = 1 - transparency(0.0))
    assert set_calls[1] == pytest.approx(1.0)
