"""hermes-neurovision background mode.

Runs neurovision as a non-interactive background process behind the active
terminal window. Designed for use with transparent terminals (iTerm2, Kitty,
Alacritty, WezTerm) so the animation shows through the terminal glass.

Auto-opacity: on launch the module sets terminal transparency automatically
using each emulator's native API. Opacity is restored to its original value
when the bg process is stopped (via atexit hook).

Supported auto-opacity terminals:
  iTerm2      osascript — set transparency on current session
  Kitty       kitty @ set-background-opacity (needs allow_remote_control yes)
  Alacritty   alacritty msg config window.opacity (v0.12+)
  WezTerm     modify wezterm.lua + wezterm cli reload-configuration
  Terminal.app  not supported — prints instructions instead

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
      "opacity": 0.45,
      "window_mode": "behind",
      "auto_size": true,
      "fade_lines": 0,
      "auto_opacity": true
    }
  }
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
    "opacity": 0.45,
    "window_mode": "behind",   # behind | side-by-side | fullscreen
    "auto_size": True,
    "fade_lines": 0,           # 0 = off, >0 = phase-2 fade (not yet implemented)
    "quiet": True,             # suppress sim activity in bg (saves CPU)
    "auto_opacity": True,      # automatically set terminal opacity on start/restore on stop
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
    """Return a one-liner fallback hint (shown only when auto-opacity fails)."""
    hints = {
        "iterm2":    "iTerm2 > Preferences > Profiles > Window > Transparency slider",
        "kitty":     "Add 'allow_remote_control yes' to kitty.conf, then retry",
        "alacritty": "Upgrade to Alacritty 0.12+ for automatic opacity control",
        "wezterm":   "Set window_background_opacity in wezterm.lua and reload",
        "terminal":  "Run: osascript -e 'tell application \"Terminal\" to set backgroundAlpha of front window to 0.5'",
    }
    return hints.get(term, "Set terminal background opacity to ~45% in your terminal emulator settings")


# ── Terminal.app ──────────────────────────────────────────────────────────────

def _terminal_get_opacity() -> Optional[float]:
    """Read backgroundAlpha of the front Terminal.app window via AppleScript."""
    script = 'tell application "Terminal" to return backgroundAlpha of front window'
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
        pass
    return None


def _terminal_set_opacity(opacity: float) -> bool:
    """Set backgroundAlpha of all Terminal.app windows via AppleScript.

    Sets every open window so tab/split setups are also covered.
    backgroundAlpha convention matches ours: 1.0 = opaque, 0.0 = transparent.
    """
    opacity = max(0.0, min(1.0, opacity))
    script = (
        f'tell application "Terminal" to repeat with w in windows\n'
        f'  set backgroundAlpha of w to {round(opacity, 4)}\n'
        f'end repeat'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=3
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Auto-opacity engine
# ──────────────────────────────────────────────────────────────────────────────

_ORIGINAL_OPACITY_FILE = Path.home() / ".hermes" / "neurovision" / "original_opacity.json"


def _save_original_opacity(term: str, value: float) -> None:
    """Persist the pre-bg opacity so we can restore it on stop."""
    _ORIGINAL_OPACITY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _ORIGINAL_OPACITY_FILE.write_text(json.dumps({"term": term, "opacity": value}))


def _load_original_opacity() -> Optional[tuple[str, float]]:
    """Return (terminal, opacity) saved before bg mode started, or None."""
    try:
        data = json.loads(_ORIGINAL_OPACITY_FILE.read_text())
        return data["term"], float(data["opacity"])
    except (OSError, KeyError, ValueError, json.JSONDecodeError):
        return None


def _clear_original_opacity() -> None:
    try:
        _ORIGINAL_OPACITY_FILE.unlink()
    except OSError:
        pass


# ── iTerm2 ────────────────────────────────────────────────────────────────────

def _iterm2_get_opacity() -> Optional[float]:
    """Read current iTerm2 session transparency via AppleScript (0=opaque, 1=clear)."""
    script = (
        'tell application "iTerm2" to tell current window '
        'to tell current session to return transparency'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
        pass
    return None


def _iterm2_set_opacity(opacity: float) -> bool:
    """Set iTerm2 session transparency. opacity 0.0=opaque, 1.0=fully clear."""
    # iTerm2 transparency is inverted from our opacity convention:
    # iTerm2 transparency=0 means opaque, transparency=1 means fully transparent
    # Our opacity=1.0 means opaque, opacity=0.0 means transparent
    transparency = 1.0 - max(0.0, min(1.0, opacity))
    script = (
        f'tell application "iTerm2" to tell current window '
        f'to tell current session to set transparency to {transparency}'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=3
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# ── Kitty ─────────────────────────────────────────────────────────────────────

def _kitty_get_opacity() -> Optional[float]:
    """Read current kitty background opacity via remote control."""
    # kitty @ ls returns JSON including the background_opacity per window
    try:
        result = subprocess.run(
            ["kitty", "@", "ls"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            import json as _json
            data = _json.loads(result.stdout)
            # Structure: list of OS windows, each has tabs, each has windows
            for os_win in data:
                for tab in os_win.get("tabs", []):
                    for win in tab.get("windows", []):
                        val = win.get("background_opacity")
                        if val is not None:
                            return float(val)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError,
            KeyError, TypeError):
        pass
    return None


def _kitty_set_opacity(opacity: float) -> bool:
    """Set kitty background opacity. Requires allow_remote_control yes."""
    opacity = max(0.1, min(1.0, opacity))
    try:
        result = subprocess.run(
            ["kitty", "@", "set-background-opacity", str(round(opacity, 2))],
            capture_output=True, text=True, timeout=3
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# ── Alacritty ─────────────────────────────────────────────────────────────────

_ALACRITTY_CONFIG_PATHS = [
    Path.home() / ".config" / "alacritty" / "alacritty.toml",
    Path.home() / ".config" / "alacritty" / "alacritty.yml",
    Path.home() / ".alacritty.toml",
    Path.home() / ".alacritty.yml",
]


def _alacritty_get_opacity() -> Optional[float]:
    """Read current Alacritty window opacity from config file."""
    import re
    for cfg_path in _ALACRITTY_CONFIG_PATHS:
        if not cfg_path.exists():
            continue
        try:
            text = cfg_path.read_text()
            # TOML: opacity = 0.9 or [window]\nopacity = 0.9
            m = re.search(r'(?:^|\n)\s*opacity\s*=\s*([0-9.]+)', text)
            if m:
                return float(m.group(1))
        except (OSError, ValueError):
            pass
    return None  # Assume 1.0 (opaque) if not found


def _alacritty_set_opacity(opacity: float) -> bool:
    """Set Alacritty opacity. Tries IPC first (v0.12+), falls back to config edit."""
    opacity = max(0.0, min(1.0, opacity))
    opacity_str = str(round(opacity, 2))

    # Try IPC method first (Alacritty 0.12+)
    try:
        result = subprocess.run(
            ["alacritty", "msg", "config", f"window.opacity={opacity_str}"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: edit config file (older Alacritty with live_config_reload)
    import re
    for cfg_path in _ALACRITTY_CONFIG_PATHS:
        if not cfg_path.exists():
            continue
        try:
            text = cfg_path.read_text()
            new_text = re.sub(
                r'((?:^|\n)\s*opacity\s*=\s*)[0-9.]+',
                lambda m: m.group(0).replace(m.group(0), m.group(1) + opacity_str),
                text
            )
            if new_text != text:
                cfg_path.write_text(new_text)
                return True
        except OSError:
            pass

    return False


# ── WezTerm ───────────────────────────────────────────────────────────────────

def _wezterm_find_config() -> Optional[Path]:
    """Find the wezterm.lua config file."""
    candidates = [
        Path.home() / ".config" / "wezterm" / "wezterm.lua",
        Path.home() / ".wezterm.lua",
    ]
    # Also check WEZTERM_CONFIG_FILE env var
    env_path = os.environ.get("WEZTERM_CONFIG_FILE")
    if env_path:
        candidates.insert(0, Path(env_path))
    for p in candidates:
        if p.exists():
            return p
    return None


def _wezterm_get_opacity() -> Optional[float]:
    """Read window_background_opacity from wezterm.lua."""
    import re
    cfg = _wezterm_find_config()
    if not cfg:
        return None
    try:
        text = cfg.read_text()
        m = re.search(r'window_background_opacity\s*=\s*([0-9.]+)', text)
        if m:
            return float(m.group(1))
    except (OSError, ValueError):
        pass
    return None


def _wezterm_set_opacity(opacity: float) -> bool:
    """Set WezTerm opacity by patching wezterm.lua then reloading config."""
    import re
    opacity = max(0.0, min(1.0, opacity))
    opacity_str = str(round(opacity, 2))
    cfg = _wezterm_find_config()
    if not cfg:
        return False
    try:
        text = cfg.read_text()
        if re.search(r'window_background_opacity\s*=', text):
            # Replace existing value
            new_text = re.sub(
                r'(window_background_opacity\s*=\s*)[0-9.]+',
                lambda m: m.group(1) + opacity_str,
                text
            )
        else:
            # Inject before the final `return config` line
            new_text = re.sub(
                r'(return\s+config\s*$)',
                f'config.window_background_opacity = {opacity_str}\n\\1',
                text,
                flags=re.MULTILINE
            )
            if new_text == text:
                # No `return config` found — append at end
                new_text = text.rstrip() + f'\nconfig.window_background_opacity = {opacity_str}\n'
        cfg.write_text(new_text)
        # Trigger reload
        subprocess.run(
            ["wezterm", "cli", "reload-configuration"],
            capture_output=True, timeout=3
        )
        return True
    except (OSError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


# ── Dispatch ──────────────────────────────────────────────────────────────────

def _get_current_opacity(term: str) -> Optional[float]:
    """Read the current terminal opacity for the given terminal type."""
    if term == "iterm2":
        raw = _iterm2_get_opacity()
        # iTerm2 returns transparency (0=opaque), we want opacity (1=opaque)
        return (1.0 - raw) if raw is not None else None
    if term == "kitty":
        return _kitty_get_opacity()
    if term == "alacritty":
        val = _alacritty_get_opacity()
        return val if val is not None else 1.0
    if term == "wezterm":
        val = _wezterm_get_opacity()
        return val if val is not None else 1.0
    if term == "terminal":
        val = _terminal_get_opacity()
        return val if val is not None else 1.0
    return None


def _set_opacity(term: str, opacity: float) -> bool:
    """Set opacity for the given terminal type. Returns True on success."""
    if term == "iterm2":
        return _iterm2_set_opacity(opacity)
    if term == "kitty":
        return _kitty_set_opacity(opacity)
    if term == "alacritty":
        return _alacritty_set_opacity(opacity)
    if term == "wezterm":
        return _wezterm_set_opacity(opacity)
    if term == "terminal":
        return _terminal_set_opacity(opacity)
    return False


def apply_auto_opacity(cfg: dict, verbose: bool = True) -> bool:
    """
    Save current terminal opacity then set the bg-mode opacity.

    Returns True if opacity was successfully applied.
    Saves original value to disk so restore_opacity() can undo it.
    """
    if not cfg.get("auto_opacity", True):
        return False

    term = _detect_terminal_app()
    target = cfg.get("opacity", 0.45)

    if term == "unknown":
        if verbose:
            print("[neurovision-bg] Unknown terminal — skipping auto-opacity.")
        return False

    # Read and save current opacity before we change anything
    current = _get_current_opacity(term)
    if current is None:
        current = 1.0  # safe default: assume opaque
    _save_original_opacity(term, current)

    if verbose:
        print(f"[neurovision-bg] Setting {term} opacity: {int(current * 100)}% → {int(target * 100)}%")

    success = _set_opacity(term, target)
    if not success and verbose:
        print(f"[neurovision-bg] Auto-opacity failed. Manual hint: {_opacity_hint_for_terminal(term)}")

    return success


def restore_opacity(verbose: bool = True) -> bool:
    """
    Restore the terminal opacity to what it was before bg mode started.

    Returns True if successfully restored.
    """
    saved = _load_original_opacity()
    if saved is None:
        return False

    term, original = saved
    if verbose:
        print(f"[neurovision-bg] Restoring {term} opacity to {int(original * 100)}%")

    success = _set_opacity(term, original)
    _clear_original_opacity()

    if not success and verbose:
        print(f"[neurovision-bg] Restore failed. Manual hint: {_opacity_hint_for_terminal(term)}")

    return success


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
        print(f"[neurovision-bg] Detected terminal: {term}")
        print(f"[neurovision-bg] Command: {' '.join(cmd)}")

    # Auto-set terminal opacity before spawning the process
    apply_auto_opacity(cfg, verbose=verbose)

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
    # Restore terminal opacity before killing the process
    restore_opacity(verbose=verbose)
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
            cfg["opacity"] = args.bg_opacity
        if getattr(args, "bg_no_auto_opacity", False):
            cfg["auto_opacity"] = False
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
        print(f"Theme:       {cfg.get('theme', 'neural-sky')}")
        print(f"Gallery:     {cfg.get('gallery', True)}")
        print(f"Opacity:     {int(cfg.get('opacity', 0.45) * 100)}%")
        print(f"Auto-opacity:{cfg.get('auto_opacity', True)}")
        if not cfg.get("auto_opacity", True):
            print(f"Hint:        {_opacity_hint_for_terminal(s['terminal'])}")

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
        updates["opacity"] = args.bg_opacity
    if getattr(args, "bg_no_auto_opacity", False):
        updates["auto_opacity"] = False
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
