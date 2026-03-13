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
import time

_EVENTS_PATH = os.environ.get(
    "HERMES_VISION_EVENTS_PATH",
    os.path.expanduser("~/.hermes/vision/events.jsonl"),
)


def handle(event_type: str, context: dict) -> None:
    """Append event as JSON line. Called by Hermes gateway hook system."""
    os.makedirs(os.path.dirname(_EVENTS_PATH), exist_ok=True)

    entry = {
        "timestamp": time.time(),
        "event_type": event_type,
        "context": context or {},
    }

    try:
        with open(_EVENTS_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # Never crash the gateway
