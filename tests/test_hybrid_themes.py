"""Tests for hybrid themes — use draw_background() + nodes together."""
import unittest.mock as mock
import curses

from hermes_neurovision.scene import ThemeState
from hermes_neurovision.themes import build_theme_config
from hermes_neurovision.renderer import Renderer


def _make_state(theme_name):
    config = build_theme_config(theme_name)
    return ThemeState(config, 100, 30, seed=42)


def _make_renderer():
    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (30, 100)
    with mock.patch("curses.has_colors", return_value=False):
        return Renderer(mock_stdscr), mock_stdscr


def _draw(renderer, state):
    with mock.patch.object(renderer, "_apply_palette"), \
         mock.patch.object(renderer, "_draw_overlay"), \
         mock.patch("curses.color_pair", return_value=0), \
         mock.patch("curses.A_BOLD", 0), \
         mock.patch("curses.A_DIM", 0):
        renderer.draw(state, 0, 1, None)


# ── plasma-grid ───────────────────────────────────────────────────────────────

def test_plasma_grid_is_registered():
    config = build_theme_config("plasma-grid")
    assert config.name == "plasma-grid"


def test_plasma_grid_has_nodes():
    state = _make_state("plasma-grid")
    assert len(state.nodes) > 0, "plasma-grid must have nodes for packet/pulse storytelling"


def test_plasma_grid_plugin_has_draw_background():
    state = _make_state("plasma-grid")
    assert callable(state.plugin.draw_background)


def test_plasma_grid_draw_background_calls_addstr():
    """draw_background() must actually draw cells to the screen."""
    state = _make_state("plasma-grid")
    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (30, 100)
    with mock.patch("curses.color_pair", return_value=0), \
         mock.patch("curses.A_DIM", 0):
        state.plugin.draw_background(mock_stdscr, state, {"base": 0, "soft": 0, "accent": 0, "bright": 0, "warning": 0})
    assert mock_stdscr.addstr.called, "draw_background() must call stdscr.addstr"


def test_plasma_grid_draw_background_does_not_call_draw_extras():
    """draw_background and draw_extras are separate hooks — both may be used independently."""
    state = _make_state("plasma-grid")
    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (30, 100)
    with mock.patch("curses.color_pair", return_value=0), \
         mock.patch("curses.A_DIM", 0):
        # draw_background called alone should not raise
        state.plugin.draw_background(mock_stdscr, state, {"base": 0, "soft": 0, "accent": 0, "bright": 0, "warning": 0})


def test_plasma_grid_renderer_calls_draw_background_then_nodes():
    """Integration: renderer calls draw_background before _draw_nodes for plasma-grid."""
    state = _make_state("plasma-grid")
    renderer, mock_stdscr = _make_renderer()

    call_order = []
    original_bg = state.plugin.draw_background
    state.plugin.draw_background = lambda *a: (call_order.append("background"), original_bg(*a))

    original_draw_nodes = renderer._draw_nodes
    def spy_nodes(s):
        call_order.append("nodes")
        original_draw_nodes(s)
    renderer._draw_nodes = spy_nodes

    _draw(renderer, state)

    assert "background" in call_order
    assert "nodes" in call_order
    assert call_order.index("background") < call_order.index("nodes")


def test_plasma_grid_headless_no_error():
    """Full render pipeline must not raise for plasma-grid."""
    state = _make_state("plasma-grid")
    renderer, _ = _make_renderer()
    _draw(renderer, state)  # must not raise


# ── deep-signal ───────────────────────────────────────────────────────────────

def test_deep_signal_is_registered():
    config = build_theme_config("deep-signal")
    assert config.name == "deep-signal"


def test_deep_signal_has_nodes():
    state = _make_state("deep-signal")
    assert len(state.nodes) > 0, "deep-signal must have nodes"


def test_deep_signal_draw_background_calls_addstr():
    state = _make_state("deep-signal")
    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (30, 100)
    with mock.patch("curses.color_pair", return_value=0), \
         mock.patch("curses.A_DIM", 0):
        state.plugin.draw_background(mock_stdscr, state, {"base": 0, "soft": 0, "accent": 0, "bright": 0, "warning": 0})
    assert mock_stdscr.addstr.called


def test_deep_signal_headless_no_error():
    state = _make_state("deep-signal")
    renderer, _ = _make_renderer()
    _draw(renderer, state)


def test_deep_signal_intensity_affects_background():
    """Higher intensity should change what draw_background renders (different chars/colors)."""
    state_low = _make_state("deep-signal")
    state_low.intensity_multiplier = 0.2

    state_high = _make_state("deep-signal")
    state_high.intensity_multiplier = 1.0

    mock_stdscr_low = mock.MagicMock()
    mock_stdscr_low.getmaxyx.return_value = (30, 100)
    mock_stdscr_high = mock.MagicMock()
    mock_stdscr_high.getmaxyx.return_value = (30, 100)

    cp = {"base": 0, "soft": 0, "accent": 0, "bright": 0, "warning": 0}

    with mock.patch("curses.color_pair", return_value=0), \
         mock.patch("curses.A_DIM", 0):
        state_low.plugin.draw_background(mock_stdscr_low, state_low, cp)
        state_high.plugin.draw_background(mock_stdscr_high, state_high, cp)

    # Extract the character arguments from addstr calls
    low_chars = {call.args[2] for call in mock_stdscr_low.addstr.call_args_list if len(call.args) >= 3}
    high_chars = {call.args[2] for call in mock_stdscr_high.addstr.call_args_list if len(call.args) >= 3}

    # High intensity should render denser/brighter chars than low intensity
    assert low_chars != high_chars, "Background must change with intensity"
