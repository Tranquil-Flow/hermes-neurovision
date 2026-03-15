import curses
import unittest.mock as mock

from hermes_neurovision.app import GalleryApp


def test_gallery_app_headless_runs():
    """Test that the headless gallery runs for a few frames without error."""
    from hermes_neurovision.themes import THEMES
    result = GalleryApp.run_headless(themes=list(THEMES), seconds=0.5, theme_seconds=0.2)
    assert result["frames"] > 0
    assert result["themes_shown"] >= 1


# Task 46: GalleryApp tune wiring

def _make_gallery_app():
    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (30, 100)
    with mock.patch("curses.has_colors", return_value=False):
        app = GalleryApp(mock_stdscr, ["electric-mycelium"], 8.0, None)
    return app


def test_gallery_app_has_tune_and_tune_overlay():
    from hermes_neurovision.tune import TuneSettings, TuneOverlay
    app = _make_gallery_app()
    assert isinstance(app.tune, TuneSettings)
    assert isinstance(app.tune_overlay, TuneOverlay)


def test_gallery_app_state_tune_is_app_tune():
    """ThemeState.tune is the same object as GalleryApp.tune."""
    app = _make_gallery_app()
    assert app.state.tune is app.tune


def test_gallery_app_new_state_inherits_tune():
    """After _advance_theme, new state.tune still points to app.tune."""
    app = _make_gallery_app()
    app.themes = ["electric-mycelium", "neural-sky"]
    app._advance_theme(1)
    assert app.state.tune is app.tune


# Task 44: Shift+Left / Shift+Right gallery navigation

def test_gallery_shift_right_advances_theme():
    app = _make_gallery_app()
    app.themes = ["electric-mycelium", "neural-sky", "storm-core"]
    before = app.theme_index
    app._handle_key(curses.KEY_SRIGHT)
    assert app.theme_index == (before + 1) % len(app.themes)


def test_gallery_shift_left_retreats_theme():
    app = _make_gallery_app()
    app.themes = ["electric-mycelium", "neural-sky", "storm-core"]
    app.theme_index = 1
    app._handle_key(curses.KEY_SLEFT)
    assert app.theme_index == 0


def test_gallery_shift_right_escape_sequence():
    """Terminal escape sequence \\x1b[1;2C also advances."""
    app = _make_gallery_app()
    app.themes = ["electric-mycelium", "neural-sky", "storm-core"]
    before = app.theme_index
    for ch in b"\x1b[1;2C":
        app._handle_key(ch)
    assert app.theme_index == (before + 1) % len(app.themes)


def test_gallery_shift_left_escape_sequence():
    """Terminal escape sequence \\x1b[1;2D also retreats."""
    app = _make_gallery_app()
    app.themes = ["electric-mycelium", "neural-sky", "storm-core"]
    app.theme_index = 2
    for ch in b"\x1b[1;2D":
        app._handle_key(ch)
    assert app.theme_index == 1
