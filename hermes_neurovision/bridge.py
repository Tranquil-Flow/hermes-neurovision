"""Bridge — maps VisionEvents to VisualTriggers for the scene."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from hermes_neurovision.events import VisionEvent


@dataclass
class VisualTrigger:
    effect: str       # "packet", "pulse", "spawn_node", "burst", "flash", "dim", "wake", "cool_down"
    intensity: float  # 0.0 - 1.0
    color_key: str    # "accent", "warning", "bright", "soft", "base"
    target: str       # "random_node", "center", "random_edge", "all", "new"


# Static mapping: kind -> (effect, intensity, color_key, target)
# For token_update, intensity is computed dynamically
_MAPPING = {
    "agent_start":       ("wake",       1.0, "accent",  "all"),
    "agent_end":         ("cool_down",  1.0, "soft",    "all"),
    "agent_step":        ("pulse",      0.3, "soft",    "random_node"),
    "session_start":     ("spawn_node", 0.8, "bright",  "new"),
    "session_reset":     ("burst",      0.6, "accent",  "center"),
    "command_executed":  ("packet",     0.4, "soft",    "random_edge"),
    "tool_call":         ("packet",     0.7, "accent",  "random_edge"),
    "tool_complete":     ("pulse",      0.5, "bright",  "random_node"),
    "thinking":          ("dim",        0.3, "soft",    "all"),
    "token_update":      ("pulse",      0.5, "base",    "all"),  # intensity overridden dynamically below
    "model_switch":      ("flash",      0.6, "accent",  "all"),
    "memory_created":    ("spawn_node", 0.9, "bright",  "new"),
    "memory_accessed":   ("pulse",      0.4, "soft",    "random_node"),
    "memory_count_changed": ("pulse",   0.3, "soft",    "all"),
    "cron_executing":    ("pulse",      0.7, "accent",  "center"),
    "cron_completed":    ("burst",      0.8, "bright",  "random_node"),
    "cron_failed":       ("flash",      0.9, "warning", "center"),
    "threat_blocked":    ("pulse",      1.0, "warning", "center"),
    "secret_redacted":   ("flash",      0.8, "warning", "random_edge"),
    "secret_detected":   ("flash",      0.9, "warning", "random_node"),
    "rate_anomaly":      ("dim",        0.6, "warning", "all"),
    "task_completed":    ("burst",      0.8, "bright",  "random_node"),
    "skill_activated":   ("packet",     0.6, "accent",  "random_edge"),
    "error":             ("flash",      0.7, "warning", "random_node"),
    "file_written":      ("packet",     0.4, "soft",    "random_edge"),
    "web_search":        ("pulse",      0.5, "accent",  "center"),
    "image_generated":   ("burst",      0.7, "bright",  "random_node"),
    "active_session":    ("pulse",      0.3, "soft",    "center"),
    "message_added":     ("packet",     0.3, "soft",    "random_edge"),
    "trajectory_logged": ("pulse",      0.4, "soft",    "random_node"),
    "trajectory_failed": ("flash",      0.8, "warning", "random_node"),
    "session_duration":  ("pulse",      0.5, "accent",  "all"),
    "tool_burst":        ("burst",      0.9, "bright",  "center"),
    "tool_chain":        ("packet",     0.7, "accent",  "random_edge"),
}


class Bridge:
    """Translates VisionEvents into VisualTriggers."""

    def translate(self, event: VisionEvent) -> List[VisualTrigger]:
        entry = _MAPPING.get(event.kind)
        if entry is None:
            return []

        effect, intensity, color_key, target = entry

        # Dynamic intensity for token_update
        if event.kind == "token_update":
            delta = event.data.get("delta_input", 0) + event.data.get("delta_output", 0)
            intensity = max(0.1, min(1.0, delta / 1000.0))
        
        # Dynamic intensity for session_duration (proportional to hours, max 1.0)
        if event.kind == "session_duration":
            duration_seconds = event.data.get("duration_seconds", 0)
            intensity = max(0.3, min(1.0, duration_seconds / 3600.0))

        return [VisualTrigger(effect, intensity, color_key, target)]
