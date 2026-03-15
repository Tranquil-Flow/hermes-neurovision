"""Tests for Phase 4: Post-Processing Pipeline."""

import curses
import unittest.mock as mock

from hermes_neurovision.renderer import Cell, FrameBuffer
from hermes_neurovision import postfx


def _make_buf(w=20, h=10):
    return FrameBuffer(w, h)


# ── apply_warp ───────────────────────────────────────────────────────

def test_warp_disabled_when_strength_zero():
    buf = _make_buf()
    buf.put(5, 3, "X", 100)
    plugin = mock.MagicMock()
    postfx.apply_warp(buf, plugin, 0, 0.0)
    assert buf.get(5, 3).char == "X"
    plugin.warp_field.assert_not_called()


def test_warp_identity_leaves_buffer_unchanged():
    buf = _make_buf()
    buf.put(5, 3, "X", 100, 8)
    plugin = mock.MagicMock()
    plugin.warp_field.return_value = None  # will be called per-cell
    # Identity warp: return same position
    plugin.warp_field.side_effect = lambda x, y, w, h, f, s: (x, y)
    postfx.apply_warp(buf, plugin, 0, 1.0)
    assert buf.get(5, 3).char == "X"


def test_warp_displaces_content():
    buf = _make_buf()
    buf.put(5, 3, "X", 100)
    plugin = mock.MagicMock()
    # Shift everything 1 right: output (x,y) reads from (x-1, y)
    plugin.warp_field.side_effect = lambda x, y, w, h, f, s: (max(0, x - 1), y)
    postfx.apply_warp(buf, plugin, 0, 1.0)
    # X was at (5,3), should now appear at (6,3) because (6,3) reads from (5,3)
    assert buf.get(6, 3).char == "X"


# ── apply_void ───────────────────────────────────────────────────────

def test_void_disabled_when_intensity_zero():
    buf = _make_buf()
    buf.put(5, 3, "X", 100)
    plugin = mock.MagicMock()
    postfx.apply_void(buf, plugin, 0, 0.0)
    plugin.void_points.assert_not_called()
    assert buf.get(5, 3).char == "X"


def test_void_erases_points():
    buf = _make_buf()
    buf.put(5, 3, "X", 100, 8)
    plugin = mock.MagicMock()
    plugin.void_points.return_value = [(5, 3)]
    postfx.apply_void(buf, plugin, 0, 1.0)
    assert buf.get(5, 3).char == " "
    assert buf.get(5, 3).color_pair == 0


def test_void_ignores_out_of_bounds():
    buf = _make_buf()
    plugin = mock.MagicMock()
    plugin.void_points.return_value = [(-1, -1), (999, 999)]
    postfx.apply_void(buf, plugin, 0, 1.0)  # should not raise


# ── apply_echo ───────────────────────────────────────────────────────

def test_echo_disabled_when_zero_frames():
    buf = _make_buf()
    postfx.apply_echo(buf, [], 0)
    # No crash, no change


def test_echo_fills_empty_cells_from_ring():
    buf = _make_buf()
    # Create a snapshot with content
    snap = [[{'char': ' ', 'color_pair': 0, 'attr': 0} for _ in range(20)] for _ in range(10)]
    snap[3][5] = {'char': 'G', 'color_pair': 42, 'attr': 0}
    ring = [snap]
    postfx.apply_echo(buf, ring, 3)
    # Empty cell should get ghost content
    assert buf.get(5, 3).char == 'G'
    assert buf.get(5, 3).attr == curses.A_DIM


def test_echo_does_not_overwrite_existing():
    buf = _make_buf()
    buf.put(5, 3, "X", 100, curses.A_BOLD)
    snap = [[{'char': ' ', 'color_pair': 0, 'attr': 0} for _ in range(20)] for _ in range(10)]
    snap[3][5] = {'char': 'G', 'color_pair': 42, 'attr': 0}
    ring = [snap]
    postfx.apply_echo(buf, ring, 3)
    assert buf.get(5, 3).char == "X"  # not overwritten


# ── snapshot_buffer ──────────────────────────────────────────────────

def test_snapshot_captures_content():
    buf = _make_buf(5, 3)
    buf.put(2, 1, "#", 50, 8)
    snap = postfx.snapshot_buffer(buf)
    assert len(snap) == 3
    assert len(snap[0]) == 5
    assert snap[1][2]['char'] == '#'
    assert snap[1][2]['color_pair'] == 50


# ── apply_glow ───────────────────────────────────────────────────────

def test_glow_disabled_when_radius_zero():
    buf = _make_buf()
    buf.put(5, 5, "X", 100)
    postfx.apply_glow(buf, 0)
    # Only the original cell should have content
    cells_written = sum(1 for row in buf.cells for c in row if c.char != ' ')
    assert cells_written == 1


def test_glow_bleeds_to_neighbors():
    buf = _make_buf()
    buf.put(5, 5, "X", 100, curses.A_BOLD)  # bright cell
    postfx.apply_glow(buf, 1)
    # Should have bled to at least some neighbors
    cells_written = sum(1 for row in buf.cells for c in row if c.char != ' ')
    assert cells_written > 1


def test_glow_neighbors_are_dim():
    buf = _make_buf()
    buf.put(5, 5, "X", 100, curses.A_BOLD)
    postfx.apply_glow(buf, 1)
    # Check a neighbor
    neighbor = buf.get(6, 5)
    if neighbor.char != ' ':
        assert neighbor.attr & curses.A_DIM


# ── apply_decay ──────────────────────────────────────────────────────

def test_decay_disabled_when_none():
    buf = _make_buf()
    buf.put(5, 3, "\u2588", 100)
    postfx.apply_decay(buf, None)
    assert buf.get(5, 3).char == "\u2588"


def test_decay_ages_cells():
    buf = _make_buf()
    buf.put(5, 3, "\u2588", 100)
    buf.get(5, 3).age = 5  # already aged
    seq = "\u2588\u2593\u2592\u2591\u00b7. "
    postfx.apply_decay(buf, seq)
    cell = buf.get(5, 3)
    # Should have advanced through sequence
    assert cell.age > 5


# ── apply_symmetry ───────────────────────────────────────────────────

def test_symmetry_disabled_when_none():
    buf = _make_buf()
    buf.put(2, 2, "X", 100)
    postfx.apply_symmetry(buf, None)
    # Only original cell
    cells = sum(1 for row in buf.cells for c in row if c.char == 'X')
    assert cells == 1


def test_symmetry_mirror_x():
    buf = _make_buf(20, 10)
    buf.put(3, 4, "X", 100)
    postfx.apply_symmetry(buf, "mirror_x")
    # Should appear mirrored on right side
    assert buf.get(20 - 1 - 3, 4).char == "X"


def test_symmetry_mirror_y():
    buf = _make_buf(20, 10)
    buf.put(5, 2, "Y", 100)
    postfx.apply_symmetry(buf, "mirror_y")
    assert buf.get(5, 10 - 1 - 2).char == "Y"


def test_symmetry_mirror_xy():
    buf = _make_buf(20, 10)
    buf.put(3, 2, "Z", 100)
    postfx.apply_symmetry(buf, "mirror_xy")
    # Should appear in all 4 quadrants
    assert buf.get(20 - 1 - 3, 2).char == "Z"
    assert buf.get(3, 10 - 1 - 2).char == "Z"
    assert buf.get(20 - 1 - 3, 10 - 1 - 2).char == "Z"


# ── apply_mask ───────────────────────────────────────────────────────

def test_mask_disabled_when_none():
    buf = _make_buf()
    buf.put(5, 3, "X", 100)
    postfx.apply_mask(buf, None)
    assert buf.get(5, 3).char == "X"


def test_mask_hides_cells():
    buf = _make_buf(5, 3)
    buf.put(2, 1, "X", 100)
    mask = [[True] * 5 for _ in range(3)]
    mask[1][2] = False  # hide this cell
    postfx.apply_mask(buf, mask)
    assert buf.get(2, 1).char == " "


def test_mask_keeps_visible_cells():
    buf = _make_buf(5, 3)
    buf.put(2, 1, "X", 100)
    buf.put(3, 1, "Y", 200)
    mask = [[True] * 5 for _ in range(3)]
    mask[1][2] = False  # hide X only
    postfx.apply_mask(buf, mask)
    assert buf.get(2, 1).char == " "
    assert buf.get(3, 1).char == "Y"


# ── apply_force_field ────────────────────────────────────────────────

def test_force_disabled_when_strength_zero():
    buf = _make_buf()
    buf.put(5, 5, "X", 100)
    plugin = mock.MagicMock()
    postfx.apply_force_field(buf, plugin, 0, 0.0)
    plugin.force_points.assert_not_called()


def test_force_no_points_no_change():
    buf = _make_buf()
    buf.put(5, 5, "X", 100)
    plugin = mock.MagicMock()
    plugin.force_points.return_value = []
    postfx.apply_force_field(buf, plugin, 0, 1.0)
    assert buf.get(5, 5).char == "X"


# ── TuneSettings new fields ─────────────────────────────────────────

def test_tune_postfx_fields_exist():
    from hermes_neurovision.tune import TuneSettings
    t = TuneSettings()
    assert t.warp_strength == 1.0
    assert t.void_intensity == 1.0
    assert t.echo_frames == 0
    assert t.glow_radius == 0
    assert t.mask_enabled is True
    assert t.force_strength == 1.0
    assert t.decay_rate == 1.0
    assert t.parallax_depth == 1
    assert t.symmetry_enabled is True


def test_tune_emergent_fields_exist():
    from hermes_neurovision.tune import TuneSettings
    t = TuneSettings()
    assert t.emergent_speed == 1.0
    assert t.emergent_opacity == 1.0


def test_tune_reactive_sound_fields_exist():
    from hermes_neurovision.tune import TuneSettings
    t = TuneSettings()
    assert t.reactive_elements is True
    assert t.sound_enabled is True
    assert t.sound_volume == 0.5


def test_tune_reset_resets_postfx():
    from hermes_neurovision.tune import TuneSettings
    t = TuneSettings()
    t.warp_strength = 2.5
    t.echo_frames = 5
    t.mask_enabled = False
    t.sound_volume = 0.1
    t.reset()
    assert t.warp_strength == 1.0
    assert t.echo_frames == 0
    assert t.mask_enabled is True
    assert t.sound_volume == 0.5


# ── Integration: renderer wires postfx ───────────────────────────────

def test_renderer_has_echo_ring():
    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (30, 100)
    with mock.patch("curses.has_colors", return_value=False):
        from hermes_neurovision.renderer import Renderer
        renderer = Renderer(mock_stdscr)
    assert hasattr(renderer, '_echo_ring')
    assert isinstance(renderer._echo_ring, list)


def test_renderer_calls_postfx_in_draw():
    """Post-processing functions are called during draw()."""
    from hermes_neurovision.scene import ThemeState
    from hermes_neurovision.themes import build_theme_config
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 100, 30, seed=42)

    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (30, 100)
    with mock.patch("curses.has_colors", return_value=False):
        from hermes_neurovision.renderer import Renderer
        renderer = Renderer(mock_stdscr)

    # Patch postfx to verify it's called
    with mock.patch.object(renderer, "_apply_palette"), \
         mock.patch.object(renderer, "_draw_overlay"), \
         mock.patch("curses.color_pair", return_value=0), \
         mock.patch("hermes_neurovision.postfx.apply_warp") as mock_warp, \
         mock.patch("hermes_neurovision.postfx.apply_symmetry") as mock_sym, \
         mock.patch("hermes_neurovision.postfx.apply_mask") as mock_mask:
        renderer.draw(state, 0, 1, None)
    # At least some postfx should have been called
    mock_warp.assert_called_once()
    mock_sym.assert_called_once()
    mock_mask.assert_called_once()
