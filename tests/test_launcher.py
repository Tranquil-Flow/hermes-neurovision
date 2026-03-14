"""Tests for auto-launch functionality."""

import os
from hermes_neurovision.launcher import (
    detect_platform,
    detect_terminal,
    is_already_running,
)


def test_detect_platform():
    """Test platform detection returns valid value."""
    platform = detect_platform()
    assert platform in ("macos", "linux", "unknown")


def test_detect_terminal():
    """Test terminal detection returns None or valid terminal name."""
    terminal = detect_terminal()
    # Can be None (no terminal) or a known terminal name
    if terminal is not None:
        assert isinstance(terminal, str)
        assert len(terminal) > 0


def test_is_already_running():
    """Test duplicate detection."""
    # Should return False since we're running tests, not the visualizer
    result = is_already_running()
    assert isinstance(result, bool)
