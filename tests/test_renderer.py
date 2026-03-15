from hermes_neurovision.renderer import Renderer


def test_renderer_edge_glyph_horizontal():
    glyph = Renderer._default_edge_glyph(10.0, 1.0)
    assert glyph == "─"


def test_renderer_edge_glyph_vertical():
    glyph = Renderer._default_edge_glyph(1.0, 10.0)
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


# draw_background hook (hybrid engine support)

def test_theme_plugin_has_draw_background_method():
    """ThemePlugin base class must expose draw_background()."""
    from hermes_neurovision.plugin import ThemePlugin
    plugin = ThemePlugin()
    assert hasattr(plugin, "draw_background")
    assert callable(plugin.draw_background)


def test_theme_plugin_draw_background_is_noop_by_default():
    """Default draw_background() must not raise and return None."""
    from hermes_neurovision.plugin import ThemePlugin
    result = ThemePlugin().draw_background(None, None, {})
    assert result is None


def test_renderer_calls_draw_background():
    """Renderer calls draw_background() on every frame when background enabled."""
    import unittest.mock as mock
    from hermes_neurovision.tune import TuneSettings
    renderer, state = _make_renderer_and_state()
    state.tune = TuneSettings()
    state.tune.show_background = True

    spy = mock.MagicMock(return_value=None)
    state.plugin.draw_background = spy
    _draw(renderer, state)
    spy.assert_called_once()


def test_renderer_skips_draw_background_when_background_disabled():
    """show_background=False skips both draw_background and draw_extras."""
    import unittest.mock as mock
    from hermes_neurovision.tune import TuneSettings
    renderer, state = _make_renderer_and_state()
    state.tune = TuneSettings()
    state.tune.show_background = False

    bg_spy = mock.MagicMock(return_value=None)
    ex_spy = mock.MagicMock(return_value=None)
    state.plugin.draw_background = bg_spy
    state.plugin.draw_extras = ex_spy
    _draw(renderer, state)
    bg_spy.assert_not_called()
    ex_spy.assert_not_called()


def test_renderer_draw_background_called_before_draw_nodes():
    """draw_background() must be called before _draw_nodes() so the field is a backdrop."""
    import unittest.mock as mock
    from hermes_neurovision.tune import TuneSettings
    from hermes_neurovision.scene import ThemeState
    from hermes_neurovision.themes import build_theme_config

    # Use a node-based theme so _draw_nodes actually runs
    config = build_theme_config("aurora-borealis")
    state = ThemeState(config, 100, 30, seed=42)
    state.tune = TuneSettings()

    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (30, 100)
    with mock.patch("curses.has_colors", return_value=False):
        renderer = Renderer(mock_stdscr)

    call_order = []
    state.plugin.draw_background = lambda *a: call_order.append("background")

    original_draw_nodes = renderer._draw_nodes
    def spy_draw_nodes(s):
        call_order.append("nodes")
        original_draw_nodes(s)
    renderer._draw_nodes = spy_draw_nodes

    with mock.patch.object(renderer, "_apply_palette"), \
         mock.patch.object(renderer, "_draw_overlay"), \
         mock.patch("curses.color_pair", return_value=0):
        renderer.draw(state, 0, 1, None)

    assert "background" in call_order
    assert "nodes" in call_order
    assert call_order.index("background") < call_order.index("nodes")
