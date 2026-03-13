from hermes_vision.bridge import Bridge, VisualTrigger
from hermes_vision.events import VisionEvent
import time


def test_visual_trigger_creation():
    t = VisualTrigger("packet", 0.7, "accent", "random_edge")
    assert t.effect == "packet"


def test_bridge_maps_agent_start():
    bridge = Bridge()
    ev = VisionEvent(time.time(), "agent", "agent_start", "info", {})
    triggers = bridge.translate(ev)
    assert len(triggers) == 1
    assert triggers[0].effect == "wake"
    assert triggers[0].intensity == 1.0


def test_bridge_maps_threat_blocked():
    bridge = Bridge()
    ev = VisionEvent(time.time(), "aegis", "threat_blocked", "danger", {})
    triggers = bridge.translate(ev)
    assert len(triggers) == 1
    assert triggers[0].effect == "pulse"
    assert triggers[0].color_key == "warning"


def test_bridge_maps_token_update():
    bridge = Bridge()
    ev = VisionEvent(time.time(), "state_db", "token_update", "info", {"delta_input": 500, "delta_output": 200})
    triggers = bridge.translate(ev)
    assert len(triggers) == 1
    assert triggers[0].effect == "pulse"
    intensity = triggers[0].intensity
    assert 0.1 <= intensity <= 1.0


def test_bridge_unknown_event():
    bridge = Bridge()
    ev = VisionEvent(time.time(), "unknown", "something_new", "info", {})
    triggers = bridge.translate(ev)
    assert triggers == []  # unknown events produce no triggers
