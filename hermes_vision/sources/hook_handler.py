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
        # Get launch command from config or use default
        config = {}
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r") as f:
                config = json.load(f)
        
        # Check for custom launch command
        custom_cmd = config.get("launch_command")
        if custom_cmd:
            cmd = custom_cmd.split()
        else:
            # Default: use hermes-vision CLI with auto-exit and logs
            cmd = ["hermes-vision", "--daemon", "--auto-exit", "--logs"]
        
        # Launch in detached subprocess
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,  # Detach from parent
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
