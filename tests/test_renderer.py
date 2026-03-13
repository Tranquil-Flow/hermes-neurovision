from hermes_vision.renderer import Renderer


def test_renderer_edge_glyph_horizontal():
    from hermes_vision.themes import build_theme_config
    config = build_theme_config("neural-sky")
    glyph = Renderer._edge_glyph(10.0, 1.0, config)
    assert glyph == "─"


def test_renderer_edge_glyph_vertical():
    from hermes_vision.themes import build_theme_config
    config = build_theme_config("neural-sky")
    glyph = Renderer._edge_glyph(1.0, 10.0, config)
    assert glyph == "│"


def test_renderer_ring_points():
    points = list(Renderer._ring_points(10.0, 10.0, 0.5))
    assert len(points) == 1  # small radius = single center point


def test_renderer_ring_points_large_radius():
    points = list(Renderer._ring_points(10.0, 10.0, 5.0))
    assert len(points) >= 8  # large radius = multiple points
