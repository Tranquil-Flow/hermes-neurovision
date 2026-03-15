"""hermes-neurovision background mode.

Runs neurovision as a non-interactive background process behind the active
terminal window. Designed for use with transparent terminals (iTerm2, Kitty,
Alacritty, WezTerm) so the animation shows through the terminal glass.

This module is only activated when --bg is passed. It never affects any
existing mode (live, gallery, daemon). All existing code paths are untouched.

Config lives in ~/.hermes/neurovision/config.json under the key "bg_mode".

Example config:
  {
    "bg_mode": {
      "enabled": false,
      "theme": "neural-sky",
      "gallery": false,
      "theme_seconds": 30,
      "opacity_hint": 0.45,
      "window_mode": "behind",
      "auto_size": true,
      "fade_lines": 0
    }
  }

opacity_hint is informational only — the actual terminal opacity is set by the
user in their terminal emulator prefs. We print a one-time setup hint on first
launch if the user has not yet configured their terminal.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

_CONFIG_PATH = Path.home() / ".hermes" / "neurovision" / "config.json"
_PID_FILE = Path.home() / ".hermes" / "neurovision" / "bg_mode.pid"

# ──────────────────────────────────────────────────────────────────────────────
# Config helpers
# ──────────────────────────────────────────────────────────────────────────────

_BG_DEFAULTS = {
    "enabled": False,
    "theme": "neural-sky",
    "gallery": True,
    "theme_seconds": 30,
    "opacity_hint": 0.45,
    "window_mode": "behind",   # behind | side-by-side | fullscreen
    "auto_size": True,
    "fade_lines": 0,           # 0 = off, >0 = phase-2 fade (not yet implemented)
    "quiet": True,             # suppress sim activity in bg (saves CPU)
}


def load_bg_config() -> dict:
    """Load bg_mode config, falling back to defaults for missing keys."""
    try:
        with open(_CONFIG_PATH) as f:
            data = json.load(f)
        cfg = _BG_DEFAULTS.copy()
        cfg.update(data.get("bg_mode", {}))
        return cfg
    except (OSError, json.JSONDecodeError):
        return _BG_DEFAULTS.copy()


def save_bg_config(updates: dict) -> None:
    """Merge updates into the bg_mode section of config.json."""
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {}
    try:
        with open(_CONFIG_PATH) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        pass
    current = data.get("bg_mode", {})
    current.update(updates)
    data["bg_mode"] = current
    with open(_CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ──────────────────────────────────────────────────────────────────────────────
# PID tracking
# ──────────────────────────────────────────────────────────────────────────────

def _write_pid(pid: int) -> None:
    _PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PID_FILE.write_text(str(pid))


def _read_pid() -> Optional[int]:
    try:
        return int(_PID_FILE.read_text().strip())
    except (OSError, ValueError):
        return None


def _clear_pid() -> None:
    try:
        _PID_FILE.unlink()
    except OSError:
        pass


def is_bg_running() -> bool:
    """Return True if a bg_mode process is alive."""
    pid = _read_pid()
    if pid is None:
        return False
    try:
        os.kill(pid, 0)  # signal 0 = existence check, no kill
        return True
    except ProcessLookupError:
        _clear_pid()
        return False
    except PermissionError:
        return True  # exists but owned differently


# ──────────────────────────────────────────────────────────────────────────────
# Platform / terminal detection
# ──────────────────────────────────────────────────────────────────────────────

def _detect_terminal_app() -> str:
    """Return: iterm2 | kitty | alacritty | wezterm | terminal | unknown."""
    if sys.platform == "darwin":
        # Check common macOS terminals in preference order
        checks = [
            ("iterm2",    "/Applications/iTerm.app"),
            ("wezterm",   "/Applications/WezTerm.app"),
            ("alacritty", "/Applications/Alacritty.app"),
            ("kitty",     "/Applications/kitty.app"),
        ]
        for name, path in checks:
            if os.path.exists(path):
                return name
        return "terminal"  # Terminal.app fallback
    # Linux: check $TERM and KITTY_WINDOW_ID
    if os.environ.get("KITTY_WINDOW_ID"):
        return "kitty"
    if os.environ.get("TERM_PROGRAM") == "WezTerm":
        return "wezterm"
    return "unknown"


def _opacity_hint_for_terminal(term: str) -> str:
    """Return a one-liner setup hint for opacity configuration."""
    hints = {
        "iterm2":    "iTerm2 > Preferences > Profiles > Window > Transparency slider",
        "kitty":     "Add 'background_opacity 0.45' to ~/.config/kitty/kitty.conf",
        "alacritty": "Add 'opacity: 0.45' under [window] in alacritty.toml",
        "wezterm":   "Add 'window_background_opacity = 0.45' to wezterm.lua",
        "terminal":  "Terminal.app > Preferences > Profiles > Background (color opacity)",
    }
    return hints.get(term, "Set terminal background opacity to ~45% in your terminal emulator settings")


# ──────────────────────────────────────────────────────────────────────────────
# Background process launcher
# ──────────────────────────────────────────────────────────────────────────────

def _build_nv_command(cfg: dict) -> list[str]:
    """Build the hermes-neurovision argv for background mode."""
    # Find the hermes-neurovision binary
    import shutil
    nv_bin = shutil.which("hermes-neurovision")
    if nv_bin is None:
        # Try the same Python env we are running in
        nv_bin = str(Path(sys.executable).parent / "hermes-neurovision")
        if not os.path.exists(nv_bin):
            raise RuntimeError(
                "hermes-neurovision binary not found on PATH. "
                "Install with: pip install hermes-neurovision"
            )

    cmd = [nv_bin]
    if cfg.get("gallery"):
        cmd.append("--gallery")
    if cfg.get("theme") and not cfg.get("gallery"):
        cmd += ["--theme", cfg["theme"]]
    if cfg.get("theme_seconds") and cfg.get("gallery"):
        cmd += ["--theme-seconds", str(cfg["theme_seconds"])]
    if cfg.get("quiet"):
        cmd.append("--quiet")
    # No --logs, no --daemon — keep it clean in the background
    return cmd


def launch_bg(cfg: Optional[dict] = None, verbose: bool = True) -> int:
    """
    Launch neurovision as a detached background process.

    Returns the PID of the spawned process, or raises RuntimeError on failure.
    Prints user-facing status if verbose=True.
    """
    if cfg is None:
        cfg = load_bg_config()

    if is_bg_running():
        pid = _read_pid()
        if verbose:
            print(f"[neurovision-bg] Already running (PID {pid})")
        return pid  # type: ignore[return-value]

    cmd = _build_nv_command(cfg)

    if verbose:
        print("[neurovision-bg] Launching neurovision in background...")
        term = _detect_terminal_app()
        opacity = cfg.get("opacity_hint", 0.45)
        print(f"[neurovision-bg] Detected terminal: {term}")
        print(f"[neurovision-bg] Suggested opacity: {int(opacity * 100)}%")
        print(f"[neurovision-bg] Hint: {_opacity_hint_for_terminal(term)}")
        print(f"[neurovision-bg] Command: {' '.join(cmd)}")

    # Spawn fully detached — no stdin/stdout/stderr inheritance
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,  # detach from our process group
        close_fds=True,
    )

    _write_pid(proc.pid)

    if verbose:
        print(f"[neurovision-bg] Started (PID {proc.pid})")

    return proc.pid


def stop_bg(verbose: bool = True) -> bool:
    """
    Stop the background neurovision process.

    Returns True if a process was stopped, False if nothing was running.
    """
    if not is_bg_running():
        if verbose:
            print("[neurovision-bg] Not running")
        return False

    pid = _read_pid()
    try:
        os.kill(pid, signal.SIGTERM)
        # Wait up to 3s for clean exit
        for _ in range(30):
            time.sleep(0.1)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
        else:
            # Force kill if still alive
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if verbose:
            print(f"[neurovision-bg] Stopped (PID {pid})")
    except ProcessLookupError:
        if verbose:
            print(f"[neurovision-bg] Process {pid} already gone")
    finally:
        _clear_pid()

    return True


def status_bg() -> dict:
    """Return a dict with current bg_mode status info."""
    running = is_bg_running()
    pid = _read_pid() if running else None
    cfg = load_bg_config()
    return {
        "running": running,
        "pid": pid,
        "config": cfg,
        "terminal": _detect_terminal_app(),
    }


# ──────────────────────────────────────────────────────────────────────────────
# CLI sub-commands (called from cli.py when --bg is present)
# ──────────────────────────────────────────────────────────────────────────────

def handle_bg_command(args) -> None:
    """
    Dispatch --bg sub-commands.

    args.bg_action: start | stop | status | config
    """
    action = getattr(args, "bg_action", "start")

    if action == "start":
        cfg = load_bg_config()
        # CLI overrides
        if getattr(args, "bg_theme", None):
            cfg["theme"] = args.bg_theme
        if getattr(args, "bg_gallery", False):
            cfg["gallery"] = True
        if getattr(args, "bg_opacity", None) is not None:
            cfg["opacity_hint"] = args.bg_opacity
        if getattr(args, "bg_quiet", False):
            cfg["quiet"] = True
        launch_bg(cfg, verbose=True)

    elif action == "stop":
        stop_bg(verbose=True)

    elif action == "status":
        s = status_bg()
        print(f"Running:  {s['running']}")
        if s["pid"]:
            print(f"PID:      {s['pid']}")
        print(f"Terminal: {s['terminal']}")
        cfg = s["config"]
        print(f"Theme:    {cfg.get('theme', 'neural-sky')}")
        print(f"Gallery:  {cfg.get('gallery', True)}")
        print(f"Opacity:  {int(cfg.get('opacity_hint', 0.45) * 100)}%")
        print(f"Hint:     {_opacity_hint_for_terminal(s['terminal'])}")

    elif action == "config":
        _handle_bg_config(args)

    else:
        print(f"[neurovision-bg] Unknown action: {action}")
        sys.exit(1)


def _handle_bg_config(args) -> None:
    """Interactive config setter for bg_mode settings."""
    cfg = load_bg_config()
    updates = {}

    if getattr(args, "bg_theme", None):
        updates["theme"] = args.bg_theme
    if getattr(args, "bg_gallery", False):
        updates["gallery"] = True
    if getattr(args, "bg_opacity", None) is not None:
        updates["opacity_hint"] = args.bg_opacity
    if getattr(args, "bg_theme_seconds", None) is not None:
        updates["theme_seconds"] = args.bg_theme_seconds
    if getattr(args, "bg_window_mode", None):
        updates["window_mode"] = args.bg_window_mode
    if getattr(args, "bg_quiet", False):
        updates["quiet"] = True

    if updates:
        save_bg_config(updates)
        cfg.update(updates)
        print("[neurovision-bg] Config updated:")
        for k, v in updates.items():
            print(f"  {k} = {v}")
    else:
        print("[neurovision-bg] Current config:")
        for k, v in cfg.items():
            print(f"  {k} = {v}")
