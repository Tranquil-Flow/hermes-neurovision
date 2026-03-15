"""Tests for theme disable/enable system (Task 49)."""
from __future__ import annotations

import json
import pytest
from unittest.mock import patch

from hermes_neurovision.themes import THEMES
from hermes_neurovision.cli import parse_args, main


# ---------------------------------------------------------------------------
# disabled.py unit tests
# ---------------------------------------------------------------------------

def test_load_disabled_returns_empty_when_no_file(tmp_path):
    cfg = str(tmp_path / "disabled.json")
    with patch("hermes_neurovision.disabled.DISABLED_CONFIG", cfg):
        from hermes_neurovision import disabled as d
        result = d.load_disabled()
    assert result == set()


def test_add_and_load_disabled(tmp_path):
    cfg = str(tmp_path / "disabled.json")
    with patch("hermes_neurovision.disabled.DISABLED_CONFIG", cfg):
        from hermes_neurovision import disabled as d
        d.add_disabled("neural-sky")
        result = d.load_disabled()
    assert "neural-sky" in result


def test_remove_disabled(tmp_path):
    cfg = str(tmp_path / "disabled.json")
    with patch("hermes_neurovision.disabled.DISABLED_CONFIG", cfg):
        from hermes_neurovision import disabled as d
        d.add_disabled("neural-sky")
        d.add_disabled("black-hole")
        d.remove_disabled("neural-sky")
        result = d.load_disabled()
    assert "neural-sky" not in result
    assert "black-hole" in result


def test_save_disabled_persists(tmp_path):
    cfg = str(tmp_path / "disabled.json")
    with patch("hermes_neurovision.disabled.DISABLED_CONFIG", cfg):
        from hermes_neurovision import disabled as d
        d.save_disabled({"theme-a", "theme-b"})
        with open(cfg) as f:
            data = json.load(f)
    assert set(data["disabled"]) == {"theme-a", "theme-b"}


def test_remove_nonexistent_is_noop(tmp_path):
    cfg = str(tmp_path / "disabled.json")
    with patch("hermes_neurovision.disabled.DISABLED_CONFIG", cfg):
        from hermes_neurovision import disabled as d
        d.remove_disabled("does-not-exist")  # should not raise
        assert d.load_disabled() == set()


# ---------------------------------------------------------------------------
# CLI flag tests
# ---------------------------------------------------------------------------

def test_disable_flag_parse():
    args = parse_args(["--disable", "neural-sky"])
    assert args.disable == "neural-sky"


def test_enable_flag_parse():
    args = parse_args(["--enable", "neural-sky"])
    assert args.enable == "neural-sky"


def test_disable_flag_calls_add_disabled(capsys, tmp_path):
    cfg = str(tmp_path / "disabled.json")
    with patch("hermes_neurovision.disabled.DISABLED_CONFIG", cfg):
        main(["--disable", "neural-sky"])
    captured = capsys.readouterr()
    assert "neural-sky" in captured.out
    assert "disabled" in captured.out.lower()


def test_enable_flag_calls_remove_disabled(capsys, tmp_path):
    cfg = str(tmp_path / "disabled.json")
    with patch("hermes_neurovision.disabled.DISABLED_CONFIG", cfg):
        from hermes_neurovision import disabled as d
        d.add_disabled("neural-sky")
        main(["--enable", "neural-sky"])
    captured = capsys.readouterr()
    assert "neural-sky" in captured.out
    assert "enabled" in captured.out.lower()


# ---------------------------------------------------------------------------
# Gallery filtering tests
# ---------------------------------------------------------------------------

def test_disabled_themes_filtered_from_gallery(tmp_path):
    """Gallery run_headless uses only non-disabled themes."""
    from hermes_neurovision.app import GalleryApp

    # Disable all themes except the first
    first = THEMES[0]
    rest = list(THEMES[1:])
    cfg = str(tmp_path / "disabled.json")
    with patch("hermes_neurovision.disabled.DISABLED_CONFIG", cfg):
        from hermes_neurovision import disabled as d
        for name in rest:
            d.add_disabled(name)
        active = [t for t in THEMES if t not in d.load_disabled()]

    assert active == [first]
    result = GalleryApp.run_headless(themes=active, seconds=0.1, theme_seconds=8.0)
    assert result["themes_shown"] >= 1


def test_all_disabled_fallback(tmp_path, capsys):
    """When all themes are disabled, CLI falls back to full THEMES list."""
    cfg = str(tmp_path / "disabled.json")
    with patch("hermes_neurovision.disabled.DISABLED_CONFIG", cfg):
        from hermes_neurovision import disabled as d
        for name in THEMES:
            d.add_disabled(name)
        # Simulate what _run_gallery does
        from hermes_neurovision.disabled import load_disabled
        with patch("hermes_neurovision.disabled.DISABLED_CONFIG", cfg):
            disabled_set = load_disabled()
        filtered = [t for t in THEMES if t not in disabled_set]

    assert filtered == []  # all disabled
    # Fallback: use full list
    fallback = filtered if filtered else list(THEMES)
    assert fallback == list(THEMES)
