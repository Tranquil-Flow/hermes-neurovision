import time
from hermes_neurovision.events import VisionEvent, EventPoller


def test_vision_event_creation():
    ev = VisionEvent(
        timestamp=time.time(),
        source="test",
        kind="test_event",
        severity="info",
        data={"key": "value"},
    )
    assert ev.source == "test"
    assert ev.kind == "test_event"


def test_event_poller_with_no_sources():
    poller = EventPoller(sources=[])
    events = poller.poll()
    assert events == []


def test_event_poller_collects_from_sources():
    now = time.time()
    fake_event = VisionEvent(now, "fake", "test", "info", {})

    def fake_poll(since):
        return [fake_event]

    poller = EventPoller(sources=[fake_poll])
    events = poller.poll()
    assert len(events) == 1
    assert events[0].kind == "test"


def test_event_poller_sorts_by_timestamp():
    ev1 = VisionEvent(100.0, "a", "first", "info", {})
    ev2 = VisionEvent(200.0, "b", "second", "info", {})

    def source_a(since):
        return [ev2]

    def source_b(since):
        return [ev1]

    poller = EventPoller(sources=[source_a, source_b])
    events = poller.poll()
    assert events[0].kind == "first"
    assert events[1].kind == "second"
