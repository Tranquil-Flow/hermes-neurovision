"""
Gateway hook handler for Hermes Vision.

This file is STANDALONE — it runs inside the Hermes gateway process.
It must NOT import from hermes_vision or any non-stdlib package.

Install:
    mkdir -p ~/.hermes/hooks/hermes-vision
    cp this_file.py ~/.hermes/hooks/hermes-vision/handler.py
    # Create HOOK.yaml alongside it (see below)
"""

import json
import os
import subprocess
import time

_EVENTS_PATH = os.environ.get(
    "HERMES_VISION_EVENTS_PATH",
    os.path.expanduser("~/.hermes/vision/events.jsonl"),
)

_CONFIG_PATH = os.path.expanduser("~/.hermes/vision/config.json")


def _should_auto_launch(event_type: str, context: dict) -> bool:
    """Check if auto-launch should be triggered for this event."""
    # Only trigger on agent:start events
    if event_type != "agent:start":
        return False
    
    # Load config
    try:
        if not os.path.exists(_CONFIG_PATH):
            return False  # No config = no auto-launch (opt-in)
        
        with open(_CONFIG_PATH, "r") as f:
            config = json.load(f)
        
        if not config.get("auto_launch", False):
            return False
    except Exception:
        return False  # Config error = no launch (fail-safe)
    
    # Check if triggered by cron or automated process
    source = context.get("source", "")
    trigger = context.get("trigger", "")
    
    # Accept: source="cron", trigger="cron", or trigger="automated"
    is_automated = (
        source == "cron" or 
        trigger == "cron" or 
        trigger == "automated"
    )
    
    return is_automated


def _try_auto_launch() -> None:
    """Attempt to auto-launch hermes-vision. Never raises exceptions."""
    try:
        # Get config
        config = {}
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r") as f:
                config = json.load(f)
        
        # Check for custom launch command
        custom_cmd = config.get("launch_command")
        if custom_cmd:
            import shlex
            subprocess.Popen(
                shlex.split(custom_cmd),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return
        
        # Build command with config options
        cmd_parts = ["hermes-vision", "--daemon", "--auto-exit"]
        
        # Add theme if specified
        theme = config.get("launch_theme")
        if theme:
            cmd_parts.extend(["--theme", theme])
        
        # Add logs flag (default true)
        if config.get("show_logs", True):
            cmd_parts.append("--logs")
        
        vision_cmd = " ".join(cmd_parts)
        
        # Write debug log to track execution
        debug_log = os.path.expanduser("~/.hermes/vision/launch_attempts.log")
        try:
            with open(debug_log, "a") as f:
                f.write(f"{time.time()} Attempting launch: {vision_cmd}\n")
        except:
            pass
        
        # Use the launcher module to open a new terminal window
        # Call it as a script to avoid import issues in gateway environment
        subprocess.Popen(
            [
                "python3", "-c",
                f"from hermes_vision.launcher import auto_launch; "
                f"result = auto_launch('{vision_cmd}'); "
                f"open('{debug_log}', 'a').write(f'{{time.time()}} Launch result: {{result}}\\n')"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        pass  # Fail silently - never crash the gateway


def handle(event_type: str, context: dict) -> None:
    """Append event as JSON line. Called by Hermes gateway hook system."""
    os.makedirs(os.path.dirname(_EVENTS_PATH), exist_ok=True)

    entry = {
        "timestamp": time.time(),
        "event_type": event_type,
        "context": context or {},
    }

    # Always write event first (core functionality)
    try:
        with open(_EVENTS_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # Never crash the gateway
    
    # Then attempt auto-launch if conditions are met
    try:
        if _should_auto_launch(event_type, context):
            _try_auto_launch()
    except Exception:
        pass  # Never crash the gateway
