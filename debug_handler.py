#!/usr/bin/env python3
"""Debug version of handler with logging."""

import json
import os
import subprocess
import time

_DEBUG_LOG = os.path.expanduser("~/.hermes/neurovision/handler_debug.log")
_EVENTS_PATH = os.path.expanduser("~/.hermes/neurovision/events.jsonl")
_CONFIG_PATH = os.path.expanduser("~/.hermes/neurovision/config.json")

def _log(msg):
    """Write to debug log."""
    try:
        with open(_DEBUG_LOG, "a") as f:
            f.write(f"[{time.time()}] {msg}\n")
    except:
        pass

def _should_auto_launch(event_type: str, context: dict) -> bool:
    """Check if auto-launch should be triggered for this event."""
    _log(f"_should_auto_launch called: type={event_type}, context={context}")
    
    # Only trigger on agent:start events
    if event_type != "agent:start":
        _log("  -> Not agent:start, returning False")
        return False
    
    # Load config
    try:
        if not os.path.exists(_CONFIG_PATH):
            _log(f"  -> Config not found at {_CONFIG_PATH}")
            return False
        
        with open(_CONFIG_PATH, "r") as f:
            config = json.load(f)
        
        _log(f"  -> Config loaded: {config}")
        
        if not config.get("auto_launch", False):
            _log("  -> auto_launch is False")
            return False
    except Exception as e:
        _log(f"  -> Config error: {e}")
        return False
    
    # Check if triggered by cron or automated process
    source = context.get("source", "")
    trigger = context.get("trigger", "")
    
    is_automated = (
        source == "cron" or 
        trigger == "cron" or 
        trigger == "automated"
    )
    
    _log(f"  -> source={source}, trigger={trigger}, is_automated={is_automated}")
    return is_automated


def _try_auto_launch() -> None:
    """Attempt to auto-launch hermes-neurovision. Never raises exceptions."""
    _log("_try_auto_launch called")
    try:
        # Get config
        config = {}
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r") as f:
                config = json.load(f)
        
        # Check for custom launch command
        custom_cmd = config.get("launch_command")
        if custom_cmd:
            _log(f"  -> Using custom command: {custom_cmd}")
            import shlex
            subprocess.Popen(
                shlex.split(custom_cmd),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            _log("  -> Custom command launched")
            return
        
        _log("  -> Using launcher module via python3 -c")
        # Use the launcher module to open a new terminal window
        result = subprocess.Popen(
            [
                "python3", "-c",
                "from hermes_neurovision.launcher import auto_launch; "
                "result = auto_launch('hermes-neurovision --daemon --auto-exit --logs'); "
                "print(f'Launch result: {result}')"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        _log(f"  -> Subprocess started: pid={result.pid}")
        
    except Exception as e:
        _log(f"  -> Exception: {e}")
        pass  # Fail silently - never crash the gateway


def handle(event_type: str, context: dict) -> None:
    """Append event as JSON line. Called by Hermes gateway hook system."""
    _log(f"handle() called: type={event_type}, context={context}")
    
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
        _log("  -> Event written to events.jsonl")
    except OSError as e:
        _log(f"  -> Event write failed: {e}")
        pass  # Never crash the gateway
    
    # Then attempt auto-launch if conditions are met
    try:
        if _should_auto_launch(event_type, context):
            _log("  -> Should auto-launch: YES, calling _try_auto_launch()")
            _try_auto_launch()
        else:
            _log("  -> Should auto-launch: NO")
    except Exception as e:
        _log(f"  -> Auto-launch exception: {e}")
        pass  # Never crash the gateway
    
    _log("handle() complete")


if __name__ == "__main__":
    # Test from command line
    handle("agent:start", {"source": "cron", "session_id": "cli-test"})
    print(f"Check debug log: {_DEBUG_LOG}")
