"""Tests for Phase 6: Event Pipeline Expansion."""

from hermes_neurovision.events import VisionEvent
from hermes_neurovision.bridge import Bridge, VisualTrigger
from hermes_neurovision.sources.custom import EVENT_MAP
from hermes_neurovision.log_overlay import SOURCE_COLORS, LogOverlay, _format_event


# ── custom.py EVENT_MAP ──────────────────────────────────────────────

def test_event_map_has_new_entries():
    new_keys = [
        "tool:start", "tool:end", "tool:error",
        "compression:start", "compression:end",
        "checkpoint:create", "checkpoint:rollback",
        "mcp:connect", "mcp:disconnect", "mcp:tool_call",
        "provider:fallback", "provider:error",
        "subagent:start", "subagent:end",
    ]
    for key in new_keys:
        assert key in EVENT_MAP, f"Missing EVENT_MAP entry: {key}"


def test_event_map_mcp_source():
    assert EVENT_MAP["mcp:connect"][0] == "mcp"
    assert EVENT_MAP["mcp:disconnect"][0] == "mcp"
    assert EVENT_MAP["mcp:tool_call"][0] == "mcp"


def test_event_map_provider_source():
    assert EVENT_MAP["provider:fallback"][0] == "provider"
    assert EVENT_MAP["provider:error"][0] == "provider"


# ── bridge.py _MAPPING ───────────────────────────────────────────────

def test_bridge_new_event_kinds():
    bridge = Bridge()
    new_kinds = {
        "tool_error": "flash",
        "compression_started": "pulse",
        "compression_ended": "ripple",
        "checkpoint_created": "spawn_node",
        "checkpoint_rollback": "flash",
        "mcp_connected": "wake",
        "mcp_disconnected": "flash",
        "mcp_tool_call": "packet",
        "provider_fallback": "cascade",
        "provider_error": "burst",
        "subagent_started": "spawn_node",
        "subagent_ended": "converge",
    }
    for kind, expected_effect in new_kinds.items():
        ev = VisionEvent(timestamp=0.0, source="test", kind=kind, severity="info", data={})
        triggers = bridge.translate(ev)
        assert len(triggers) == 1, f"No trigger for {kind}"
        assert triggers[0].effect == expected_effect, (
            f"{kind}: expected effect={expected_effect}, got {triggers[0].effect}"
        )


def test_bridge_new_effects_use_v020_effects():
    """New mappings use the v0.2.0 effects (ripple, cascade, converge)."""
    bridge = Bridge()
    # ripple
    ev = VisionEvent(timestamp=0, source="agent", kind="compression_ended", severity="info", data={})
    assert bridge.translate(ev)[0].effect == "ripple"
    # cascade
    ev = VisionEvent(timestamp=0, source="provider", kind="provider_fallback", severity="info", data={})
    assert bridge.translate(ev)[0].effect == "cascade"
    # converge
    ev = VisionEvent(timestamp=0, source="agent", kind="subagent_ended", severity="info", data={})
    assert bridge.translate(ev)[0].effect == "converge"


def test_bridge_existing_mappings_unchanged():
    """Existing event kinds still produce the same triggers."""
    bridge = Bridge()
    ev = VisionEvent(timestamp=0, source="agent", kind="agent_start", severity="info", data={})
    triggers = bridge.translate(ev)
    assert triggers[0].effect == "wake"
    assert triggers[0].intensity == 1.0


# ── log_overlay.py ───────────────────────────────────────────────────

def test_source_colors_has_mcp_provider():
    assert "mcp" in SOURCE_COLORS
    assert "provider" in SOURCE_COLORS
    assert SOURCE_COLORS["mcp"] == "green"
    assert SOURCE_COLORS["provider"] == "yellow"


def test_format_event_new_kinds():
    """All new event kinds produce formatted log strings."""
    kinds_and_data = [
        ("tool_error", {"tool_name": "terminal", "error": "timeout"}),
        ("compression_started", {}),
        ("compression_ended", {"tokens_before": 5000, "tokens_after": 2000}),
        ("checkpoint_created", {"checkpoint_id": "abc12345"}),
        ("checkpoint_rollback", {"checkpoint_id": "def67890"}),
        ("mcp_connected", {"server": "my-server"}),
        ("mcp_disconnected", {"server": "my-server"}),
        ("mcp_tool_call", {"tool_name": "search", "server": "brave"}),
        ("provider_fallback", {"from": "gpt-4", "to": "claude"}),
        ("provider_error", {"provider": "openai", "error": "rate limited"}),
        ("subagent_started", {"name": "code-review"}),
        ("subagent_ended", {"name": "code-review"}),
    ]
    for kind, data in kinds_and_data:
        ev = VisionEvent(timestamp=1000000.0, source="test", kind=kind, severity="info", data=data)
        text = _format_event(ev)
        assert text.startswith("["), f"Bad format for {kind}: {text}"
        assert kind.split("_")[0] in text.lower() or "mcp" in text.lower() or "provider" in text.lower() or "subagent" in text.lower() or "compression" in text.lower() or "checkpoint" in text.lower() or "tool" in text.lower(), f"Kind not reflected in text for {kind}: {text}"


def test_format_compression_ended_shows_tokens():
    ev = VisionEvent(timestamp=1000000.0, source="agent", kind="compression_ended",
                     severity="info", data={"tokens_before": 5000, "tokens_after": 2000})
    text = _format_event(ev)
    assert "5000" in text
    assert "2000" in text


def test_format_mcp_tool_call_shows_server():
    ev = VisionEvent(timestamp=1000000.0, source="mcp", kind="mcp_tool_call",
                     severity="info", data={"tool_name": "search", "server": "brave"})
    text = _format_event(ev)
    assert "search" in text
    assert "brave" in text


def test_format_provider_fallback_shows_chain():
    ev = VisionEvent(timestamp=1000000.0, source="provider", kind="provider_fallback",
                     severity="info", data={"from": "gpt-4o", "to": "claude-3"})
    text = _format_event(ev)
    assert "gpt-4o" in text
    assert "claude-3" in text


def test_log_overlay_new_source_colors():
    """LogOverlay uses correct colors for new sources."""
    overlay = LogOverlay()
    ev = VisionEvent(timestamp=1000000.0, source="mcp", kind="mcp_connected",
                     severity="info", data={"server": "test"})
    overlay.add_event(ev)
    import time
    lines = overlay.get_visible_lines(1000000.0 + 1)
    assert len(lines) >= 1
    assert lines[-1][2] == "green"  # mcp color
