import time
from hermes_neurovision.log_overlay import LogOverlay
from hermes_neurovision.events import VisionEvent


def test_log_overlay_add_event():
    overlay = LogOverlay(max_lines=10)
    ev = VisionEvent(time.time(), "agent", "agent_start", "info", {"session_id": "abc", "model": "gpt-4"})
    overlay.add_event(ev)
    lines = overlay.get_visible_lines(time.time())
    assert len(lines) == 1
    assert "agent:start" in lines[0][0]


def test_log_overlay_fading():
    overlay = LogOverlay(max_lines=10)
    now = time.time()
    # Fresh (< 15s) → bold
    ev_fresh = VisionEvent(now - 5.0, "agent", "tool_call", "info", {"tool_name": "web_search"})
    overlay.add_event(ev_fresh)
    # Mid-age (15-40s) → normal
    ev_mid = VisionEvent(now - 20.0, "agent", "tool_call", "info", {"tool_name": "read"})
    overlay.add_event(ev_mid)
    # Old (40-60s) → dim
    ev_old = VisionEvent(now - 50.0, "agent", "tool_call", "info", {"tool_name": "write"})
    overlay.add_event(ev_old)
    lines = overlay.get_visible_lines(now)
    assert len(lines) == 3
    assert lines[0][1] == "bold"
    assert lines[1][1] == "normal"
    assert lines[2][1] == "dim"


def test_log_overlay_expiry():
    overlay = LogOverlay(max_lines=10)
    old_time = time.time() - 61.0  # 61 seconds ago — past the 60s expiry
    ev = VisionEvent(old_time, "agent", "tool_call", "info", {})
    overlay.add_event(ev)
    lines = overlay.get_visible_lines(time.time())
    assert len(lines) == 0  # expired


def test_log_overlay_max_lines():
    overlay = LogOverlay(max_lines=3)
    now = time.time()
    for i in range(5):
        overlay.add_event(VisionEvent(now + i * 0.1, "agent", "agent_step", "info", {}))
    lines = overlay.get_visible_lines(now + 1.0)
    assert len(lines) <= 3


def test_log_overlay_color_by_source():
    overlay = LogOverlay(max_lines=10)
    now = time.time()
    overlay.add_event(VisionEvent(now, "agent", "agent_start", "info", {}))
    overlay.add_event(VisionEvent(now, "aegis", "threat_blocked", "danger", {}))
    lines = overlay.get_visible_lines(now)
    # First line (agent) should be cyan, second (aegis) should be yellow
    assert lines[0][2] == "cyan"
    assert lines[1][2] == "yellow"
