"""Auto-launch hermes-neurovision in a new terminal window."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Optional


def is_already_running() -> bool:
    """Check if hermes-neurovision is already running."""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=2
        )
        # Look for hermes-neurovision processes (excluding this one and grep)
        lines = result.stdout.split('\n')
        count = sum(1 for line in lines if 'hermes-neurovision' in line and 'grep' not in line and str(os.getpid()) not in line)
        return count > 0
    except Exception:
        return False  # Assume not running if we can't check


def detect_platform() -> str:
    """Detect the platform: macos, linux, or unknown."""
    if sys.platform == "darwin":
        return "macos"
    elif sys.platform.startswith("linux"):
        return "linux"
    return "unknown"


def detect_terminal() -> Optional[str]:
    """Detect which terminal emulator is available/active."""
    platform = detect_platform()
    
    if platform == "macos":
        # Check for iTerm2 first (preferred)
        if os.path.exists("/Applications/iTerm.app"):
            return "iterm2"
        # Fall back to Terminal.app
        if os.path.exists("/System/Applications/Utilities/Terminal.app"):
            return "terminal"
    
    # Check for tmux
    if os.environ.get("TMUX"):
        return "tmux"
    
    # Check for screen
    if os.environ.get("STY"):
        return "screen"
    
    if platform == "linux":
        # Check common Linux terminals
        for term in ["gnome-terminal", "konsole", "xterm", "xfce4-terminal"]:
            try:
                subprocess.run(["which", term], capture_output=True, check=True, timeout=1)
                return term
            except Exception:
                continue
    
    return None


def launch_iterm2(command: str) -> bool:
    """Launch in iTerm2 using AppleScript."""
    script = f'''
    tell application "iTerm"
        create window with default profile
        tell current session of current window
            write text "{command}"
        end tell
        tell current window
            set bounds to {{100, 100, 1200, 800}}
        end tell
    end tell
    '''
    try:
        subprocess.Popen(
            ["osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        return True
    except Exception:
        return False


def launch_terminal_app(command: str) -> bool:
    """Launch in Terminal.app using AppleScript."""
    script = f'''
    tell application "Terminal"
        set newWindow to do script "{command}"
        tell window 1
            set bounds to {{100, 100, 1200, 800}}
        end tell
        activate
    end tell
    '''
    try:
        subprocess.Popen(
            ["osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        return True
    except Exception:
        return False


def launch_tmux(command: str) -> bool:
    """Launch in a new tmux window."""
    try:
        subprocess.Popen(
            ["tmux", "new-window", "-n", "hermes-neurovision", command],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        return True
    except Exception:
        return False


def launch_gnome_terminal(command: str) -> bool:
    """Launch in gnome-terminal."""
    try:
        subprocess.Popen(
            ["gnome-terminal", "--", "bash", "-c", f"{command}; exec bash"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        return True
    except Exception:
        return False


def launch_xterm(command: str) -> bool:
    """Launch in xterm."""
    try:
        subprocess.Popen(
            ["xterm", "-e", command],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        return True
    except Exception:
        return False


def auto_launch(command: str = "hermes-neurovision --auto-exit --logs") -> bool:
    """
    Auto-launch hermes-neurovision in a new terminal.
    
    Returns True if successfully launched, False otherwise.
    """
    # Check if already running
    if is_already_running():
        return False  # Don't launch duplicate
    
    # Detect terminal
    terminal = detect_terminal()
    
    if terminal == "iterm2":
        return launch_iterm2(command)
    elif terminal == "terminal":
        return launch_terminal_app(command)
    elif terminal == "tmux":
        return launch_tmux(command)
    elif terminal == "gnome-terminal":
        return launch_gnome_terminal(command)
    elif terminal == "xterm":
        return launch_xterm(command)
    
    return False  # No suitable terminal found


if __name__ == "__main__":
    # Test the launcher
    print(f"Platform: {detect_platform()}")
    print(f"Terminal: {detect_terminal()}")
    print(f"Already running: {is_already_running()}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test-launch":
        result = auto_launch()
        print(f"Launch {'succeeded' if result else 'failed'}")
        sys.exit(0 if result else 1)
