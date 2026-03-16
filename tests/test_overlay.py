"""Tests for the overlay mode components."""
import time
from unittest.mock import MagicMock

from hermes_neurovision.overlay import (
    SceneDelegate, GalleryDelegate, LiveDelegate, DaemonDelegate,
    _MODES, _TEXT_COLORS, _GLOW_COLORS, _FADE_MODES,
)
from hermes_neurovision.compositor import FadeConfig


# ── SceneDelegate ──────────────────────────────────────────────────────

def test_scene_delegate_interface():
    d = SceneDelegate()
    state = MagicMock()
    d.step(state, time.time())
    state.step.assert_called_once()
    assert d.should_switch_theme(time.time()) is False


# ── GalleryDelegate ───────────────────────────────────────────────────

def test_gallery_delegate_steps_state():
    state = MagicMock()
    d = GalleryDelegate(theme_seconds=5.0)
    d.step(state, time.time())
    state.step.assert_called_once()


def test_gallery_delegate_switches_theme():
    d = GalleryDelegate(theme_seconds=0.1)
    d.reset_timer()
    # Force the switch time to be in the past
    d._switch_at = time.time() - 1.0
    assert d.should_switch_theme(time.time()) is True


# ── LiveDelegate ──────────────────────────────────────────────────────

def test_live_delegate_polls_events():
    poller = MagicMock()
    poller.poll.return_value = []
    bridge = MagicMock()
    state = MagicMock()
    d = LiveDelegate(poller=poller, bridge=bridge)
    d.step(state, time.time())
    state.step.assert_called_once()


# ── DaemonDelegate ───────────────────────────────────────────────────

def test_daemon_delegate_starts_in_gallery():
    poller = MagicMock()
    poller.poll.return_value = []
    bridge = MagicMock()
    d = DaemonDelegate(theme_seconds=10.0, poller=poller, bridge=bridge)
    assert d.mode == "gallery"


# ── Constants ─────────────────────────────────────────────────────────

def test_modes():
    assert "daemon" in _MODES
    assert "gallery" in _MODES
    assert "live" in _MODES


def test_text_colors():
    assert "auto" in _TEXT_COLORS
    assert "theme" in _TEXT_COLORS
    assert "green" in _TEXT_COLORS


def test_glow_colors():
    assert "theme" in _GLOW_COLORS
    assert "magenta" in _GLOW_COLORS
    assert "cyan" in _GLOW_COLORS


def test_fade_modes():
    assert "position" in _FADE_MODES
    assert "age" in _FADE_MODES
    assert "both" in _FADE_MODES
