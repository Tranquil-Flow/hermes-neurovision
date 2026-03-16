"""Tests for the VT terminal event source."""
from hermes_neurovision.vt import VTScreen
from hermes_neurovision.sources.vt_source import VTEventSource


def test_no_events_when_idle():
    vt = VTScreen(24, 80)
    src = VTEventSource(vt)
    events = src.poll(0.0)
    assert events == []


def test_vt_output_event():
    vt = VTScreen(24, 80)
    src = VTEventSource(vt)
    vt.feed(b"Hello world")
    events = src.poll(0.0)
    assert len(events) == 1
    assert events[0].kind == "vt_output"
    assert events[0].source == "vt"
    assert events[0].data["bytes"] == 11


def test_vt_scroll_event():
    vt = VTScreen(3, 10)
    src = VTEventSource(vt)
    vt.feed(b"A\nB\nC\nD")  # triggers 1 scroll
    events = src.poll(0.0)
    kinds = [e.kind for e in events]
    assert "vt_output" in kinds
    assert "vt_scroll" in kinds


def test_counters_reset_after_poll():
    vt = VTScreen(24, 80)
    src = VTEventSource(vt)
    vt.feed(b"test")
    src.poll(0.0)
    events = src.poll(0.0)
    assert events == []
