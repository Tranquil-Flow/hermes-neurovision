from hermes_neurovision.renderer import Renderer


def test_renderer_edge_glyph_horizontal():
    from hermes_neurovision.themes import build_theme_config
    config = build_theme_config("neural-sky")
    glyph = Renderer._edge_glyph(10.0, 1.0, config)
    assert glyph == "─"


def test_renderer_edge_glyph_vertical():
    from hermes_neurovision.themes import build_theme_config
    config = build_theme_config("neural-sky")
    glyph = Renderer._edge_glyph(1.0, 10.0, config)
    assert glyph == "│"


def test_renderer_ring_points():
    points = list(Renderer._ring_points(10.0, 10.0, 0.5))
    assert len(points) == 1  # small radius = single center point


def test_renderer_ring_points_large_radius():
    points = list(Renderer._ring_points(10.0, 10.0, 5.0))
    assert len(points) >= 8  # large radius = multiple points


# Task 46: renderer respects tune flags

def _make_renderer_and_state():
    import unittest.mock as mock
    from hermes_neurovision.scene import ThemeState
    from hermes_neurovision.themes import build_theme_config
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 100, 30, seed=42)
    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (30, 100)
    with mock.patch("curses.has_colors", return_value=False):
        renderer = Renderer(mock_stdscr)
    return renderer, state


def _draw(renderer, state):
    """Call renderer.draw() with curses functions that need initscr patched out."""
    import unittest.mock as mock
    with mock.patch.object(renderer, "_apply_palette"), \
         mock.patch.object(renderer, "_draw_overlay"), \
         mock.patch("curses.color_pair", return_value=0):
        renderer.draw(state, 0, 1, None)


def test_renderer_skips_draw_extras_when_background_disabled():
    import unittest.mock as mock
    from hermes_neurovision.tune import TuneSettings
    renderer, state = _make_renderer_and_state()
    state.tune = TuneSettings()
    state.tune.show_background = False

    spy = mock.MagicMock(return_value=None)
    state.plugin.draw_extras = spy
    _draw(renderer, state)
    spy.assert_not_called()


def test_renderer_calls_draw_extras_when_background_enabled():
    import unittest.mock as mock
    from hermes_neurovision.tune import TuneSettings
    renderer, state = _make_renderer_and_state()
    state.tune = TuneSettings()
    state.tune.show_background = True

    spy = mock.MagicMock(return_value=None)
    state.plugin.draw_extras = spy
    _draw(renderer, state)
    spy.assert_called_once()


def test_renderer_skips_nodes_and_edges_when_nodes_disabled():
    import unittest.mock as mock
    from hermes_neurovision.tune import TuneSettings
    renderer, state = _make_renderer_and_state()
    state.tune = TuneSettings()
    state.tune.show_nodes = False

    with mock.patch.object(renderer, "_draw_nodes") as mock_nodes, \
         mock.patch.object(renderer, "_draw_edges") as mock_edges:
        _draw(renderer, state)
    mock_nodes.assert_not_called()
    mock_edges.assert_not_called()


def test_renderer_skips_stars_draw_when_stars_disabled():
    import unittest.mock as mock
    from hermes_neurovision.tune import TuneSettings
    renderer, state = _make_renderer_and_state()
    state.tune = TuneSettings()
    state.tune.show_stars = False

    with mock.patch.object(renderer, "_draw_stars") as mock_stars:
        _draw(renderer, state)
    mock_stars.assert_not_called()
