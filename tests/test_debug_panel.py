"""Tests for debug_panel.py — DebugPanel."""
import time
import unittest.mock as mock

from hermes_neurovision.debug_panel import DebugPanel
from hermes_neurovision.events import VisionEvent


def _make_event(source="state_db", kind="active_session"):
    return VisionEvent(time.time(), source, kind, "info", {})


class FakeTrigger:
    def __init__(self, effect="packet", intensity=0.5):
        self.effect = effect
        self.intensity = intensity


# ── Construction ──────────────────────────────────────────────────────────────

def test_debug_panel_starts_hidden():
    panel = DebugPanel()
    assert panel.visible is False


def test_debug_panel_has_fixed_width():
    panel = DebugPanel()
    assert panel.width == 34


# ── record_event ──────────────────────────────────────────────────────────────

def test_debug_panel_record_event_stores_event():
    panel = DebugPanel()
    ev = _make_event()
    panel.record_event(ev)
    assert len(panel.recent_events) == 1
    assert panel.recent_events[0] is ev


def test_debug_panel_record_event_ring_buffer_capped_at_8():
    panel = DebugPanel()
    for _ in range(12):
        panel.record_event(_make_event())
    assert len(panel.recent_events) == 8


def test_debug_panel_record_event_oldest_dropped():
    panel = DebugPanel()
    events = [_make_event(kind=f"kind_{i}") for i in range(9)]
    for ev in events:
        panel.record_event(ev)
    # First event should be gone; last 8 remain
    assert events[0] not in panel.recent_events
    assert events[-1] in panel.recent_events


# ── record_trigger ────────────────────────────────────────────────────────────

def test_debug_panel_record_trigger_stores_trigger():
    panel = DebugPanel()
    t = FakeTrigger()
    panel.record_trigger(t)
    assert len(panel.recent_triggers) == 1
    assert panel.recent_triggers[0][0] is t


def test_debug_panel_record_trigger_with_source_event():
    panel = DebugPanel()
    ev = _make_event()
    t = FakeTrigger()
    panel.record_trigger(t, source_event=ev)
    stored_trigger, stored_event = panel.recent_triggers[0]
    assert stored_trigger is t
    assert stored_event is ev


def test_debug_panel_record_trigger_ring_buffer_capped_at_8():
    panel = DebugPanel()
    for _ in range(12):
        panel.record_trigger(FakeTrigger())
    assert len(panel.recent_triggers) == 8


# ── toggle ────────────────────────────────────────────────────────────────────

def test_debug_panel_toggle_shows_and_hides():
    panel = DebugPanel()
    assert panel.visible is False
    panel.toggle()
    assert panel.visible is True
    panel.toggle()
    assert panel.visible is False


# ── draw (headless smoke test) ────────────────────────────────────────────────

def test_debug_panel_draw_does_not_raise_when_hidden():
    """draw() is a no-op when not visible."""
    from hermes_neurovision.scene import ThemeState
    from hermes_neurovision.themes import build_theme_config
    panel = DebugPanel()
    panel.visible = False
    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (40, 120)
    state = ThemeState(build_theme_config("electric-mycelium"), 120, 40, seed=42)
    # Should not raise
    with mock.patch("curses.color_pair", return_value=0):
        panel.draw(mock_stdscr, state, {"bright": 0, "accent": 0, "soft": 0, "base": 0, "warning": 0})


def test_debug_panel_draw_does_not_raise_when_visible():
    """draw() runs without error when visible."""
    from hermes_neurovision.scene import ThemeState
    from hermes_neurovision.themes import build_theme_config
    panel = DebugPanel()
    panel.visible = True
    panel.record_event(_make_event("state_db", "active_session"))
    panel.record_trigger(FakeTrigger("packet", 0.7))
    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (40, 120)
    state = ThemeState(build_theme_config("electric-mycelium"), 120, 40, seed=42)
    with mock.patch("curses.color_pair", return_value=0), \
         mock.patch("curses.A_BOLD", 0), \
         mock.patch("curses.A_DIM", 0):
        panel.draw(mock_stdscr, state, {"bright": 0, "accent": 0, "soft": 0, "base": 0, "warning": 0})


# ── GalleryApp + LiveApp wiring ───────────────────────────────────────────────

def test_gallery_app_has_debug_panel():
    from hermes_neurovision.app import GalleryApp
    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (30, 100)
    with mock.patch("curses.has_colors", return_value=False):
        app = GalleryApp(mock_stdscr, ["electric-mycelium"], 8.0, None)
    assert isinstance(app.debug_panel, DebugPanel)


def test_gallery_app_d_key_toggles_debug_panel():
    from hermes_neurovision.app import GalleryApp
    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (30, 100)
    with mock.patch("curses.has_colors", return_value=False):
        app = GalleryApp(mock_stdscr, ["electric-mycelium"], 8.0, None)
    assert app.debug_panel.visible is False
    app._handle_key(ord("d"))
    assert app.debug_panel.visible is True
    app._handle_key(ord("d"))
    assert app.debug_panel.visible is False
