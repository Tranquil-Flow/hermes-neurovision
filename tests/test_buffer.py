"""Tests for Phase 1: Buffer Foundation (FrameBuffer, Cell, _BufferShim)."""

import unittest.mock as mock

from hermes_neurovision.renderer import Cell, FrameBuffer, _BufferShim


# ── Cell tests ────────────────────────────────────────────────────────

def test_cell_defaults():
    c = Cell()
    assert c.char == " "
    assert c.color_pair == 0
    assert c.attr == 0
    assert c.age == 0


def test_cell_custom():
    c = Cell(char="@", color_pair=42, attr=8, age=3)
    assert c.char == "@"
    assert c.color_pair == 42
    assert c.attr == 8
    assert c.age == 3


# ── FrameBuffer tests ─────────────────────────────────────────────────

def test_framebuffer_dimensions():
    buf = FrameBuffer(80, 24)
    assert buf.w == 80
    assert buf.h == 24
    assert len(buf.cells) == 24
    assert len(buf.cells[0]) == 80


def test_framebuffer_put_get_roundtrip():
    buf = FrameBuffer(10, 5)
    buf.put(3, 2, "#", 100, 8)
    cell = buf.get(3, 2)
    assert cell.char == "#"
    assert cell.color_pair == 100
    assert cell.attr == 8
    assert cell.age == 0  # age resets on write


def test_framebuffer_put_resets_age():
    buf = FrameBuffer(10, 5)
    cell = buf.get(3, 2)
    cell.age = 7
    buf.put(3, 2, "X", 0)
    assert buf.get(3, 2).age == 0


def test_framebuffer_put_out_of_bounds():
    """Out-of-bounds writes are silently ignored."""
    buf = FrameBuffer(10, 5)
    buf.put(-1, 0, "X", 0)
    buf.put(0, -1, "X", 0)
    buf.put(10, 0, "X", 0)
    buf.put(0, 5, "X", 0)
    # Should not raise, all cells still default
    for row in buf.cells:
        for cell in row:
            assert cell.char == " "


def test_framebuffer_get_out_of_bounds():
    """Out-of-bounds reads return a default Cell."""
    buf = FrameBuffer(10, 5)
    cell = buf.get(-1, 0)
    assert cell.char == " "
    cell = buf.get(100, 100)
    assert cell.char == " "


def test_framebuffer_clear():
    buf = FrameBuffer(10, 5)
    buf.put(3, 2, "#", 100, 8)
    buf.put(7, 4, "@", 200, 16)
    buf.clear()
    for row in buf.cells:
        for cell in row:
            assert cell.char == " "
            assert cell.color_pair == 0
            assert cell.attr == 0
            assert cell.age == 0


def test_framebuffer_blit_to_screen():
    """blit_to_screen writes non-space cells to stdscr."""
    buf = FrameBuffer(5, 3)
    buf.put(1, 0, "#", 256, 8)  # color_pair | attr
    buf.put(3, 2, "@", 512, 16)

    stdscr = mock.MagicMock()
    buf.blit_to_screen(stdscr)

    # Should have called addstr for the two non-space cells
    calls = stdscr.addstr.call_args_list
    assert len(calls) == 2
    # First: (y=0, x=1, "#", 256|8)
    assert calls[0] == mock.call(0, 1, "#", 256 | 8)
    # Second: (y=2, x=3, "@", 512|16)
    assert calls[1] == mock.call(2, 3, "@", 512 | 16)


def test_framebuffer_blit_skips_spaces():
    """Spaces with no attr are not written to screen."""
    buf = FrameBuffer(3, 2)
    # Only write to one cell
    buf.put(0, 0, "X", 0)
    stdscr = mock.MagicMock()
    buf.blit_to_screen(stdscr)
    assert stdscr.addstr.call_count == 1


def test_framebuffer_blit_curses_error_safe():
    """blit handles curses.error at screen edges gracefully."""
    import curses
    buf = FrameBuffer(3, 2)
    buf.put(2, 1, "X", 0)
    stdscr = mock.MagicMock()
    stdscr.addstr.side_effect = curses.error("addstr() returned ERR")
    # Should not raise
    buf.blit_to_screen(stdscr)


# ── _BufferShim tests ─────────────────────────────────────────────────

def test_buffer_shim_addstr():
    buf = FrameBuffer(20, 10)
    shim = _BufferShim(buf)
    # addstr(y, x, text, attr)
    shim.addstr(3, 5, "Hi", 0)
    assert buf.get(5, 3).char == "H"
    assert buf.get(6, 3).char == "i"


def test_buffer_shim_addstr_with_attr():
    """_BufferShim correctly splits combined attr into color_pair + style."""
    buf = FrameBuffer(20, 10)
    shim = _BufferShim(buf)
    # Simulate curses.color_pair(2) | curses.A_BOLD
    # color_pair(2) is typically 0x200 = 512
    combined = 0x200 | 0x200000  # pair bits + A_BOLD (on typical ncurses)
    shim.addstr(1, 1, "X", combined)
    cell = buf.get(1, 1)
    assert cell.char == "X"
    # The pair and style should be separated
    assert cell.color_pair | cell.attr == combined


def test_buffer_shim_getmaxyx():
    buf = FrameBuffer(80, 24)
    shim = _BufferShim(buf)
    assert shim.getmaxyx() == (24, 80)


def test_buffer_shim_multichar_string():
    """Multi-character strings spread across consecutive x positions."""
    buf = FrameBuffer(20, 5)
    shim = _BufferShim(buf)
    shim.addstr(0, 2, "Hello", 0)
    assert buf.get(2, 0).char == "H"
    assert buf.get(3, 0).char == "e"
    assert buf.get(4, 0).char == "l"
    assert buf.get(5, 0).char == "l"
    assert buf.get(6, 0).char == "o"


# ── Integration: draw() uses buffer ──────────────────────────────────

def _make_renderer_and_state():
    from hermes_neurovision.scene import ThemeState
    from hermes_neurovision.themes import build_theme_config
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 100, 30, seed=42)
    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (30, 100)
    with mock.patch("curses.has_colors", return_value=False):
        from hermes_neurovision.renderer import Renderer
        renderer = Renderer(mock_stdscr)
    return renderer, state


def test_draw_creates_buffer():
    """Renderer.draw() creates a FrameBuffer."""
    renderer, state = _make_renderer_and_state()
    assert renderer._buffer is None
    with mock.patch.object(renderer, "_apply_palette"), \
         mock.patch.object(renderer, "_draw_overlay"), \
         mock.patch("curses.color_pair", return_value=0):
        renderer.draw(state, 0, 1, None)
    assert renderer._buffer is not None
    assert isinstance(renderer._buffer, FrameBuffer)
    assert renderer._buffer.w == 100
    assert renderer._buffer.h == 30


def test_draw_blits_buffer_then_hud():
    """Buffer is blitted before HUD overlay is drawn."""
    renderer, state = _make_renderer_and_state()
    call_order = []

    original_blit = FrameBuffer.blit_to_screen
    def spy_blit(self, stdscr):
        call_order.append("blit")
        original_blit(self, stdscr)

    def spy_overlay(*args, **kwargs):
        call_order.append("overlay")

    with mock.patch.object(renderer, "_apply_palette"), \
         mock.patch("curses.color_pair", return_value=0), \
         mock.patch.object(FrameBuffer, "blit_to_screen", spy_blit), \
         mock.patch.object(renderer, "_draw_overlay", spy_overlay):
        renderer.draw(state, 0, 1, None)

    assert "blit" in call_order
    assert "overlay" in call_order
    assert call_order.index("blit") < call_order.index("overlay")


def test_draw_erase_before_blit():
    """stdscr.erase() is called before blit_to_screen()."""
    renderer, state = _make_renderer_and_state()
    call_order = []

    renderer.stdscr.erase = lambda: call_order.append("erase")

    original_blit = FrameBuffer.blit_to_screen
    def spy_blit(self, stdscr):
        call_order.append("blit")
        original_blit(self, stdscr)

    with mock.patch.object(renderer, "_apply_palette"), \
         mock.patch.object(renderer, "_draw_overlay"), \
         mock.patch("curses.color_pair", return_value=0), \
         mock.patch.object(FrameBuffer, "blit_to_screen", spy_blit):
        renderer.draw(state, 0, 1, None)

    assert call_order.index("erase") < call_order.index("blit")


def test_buffer_resizes_on_terminal_change():
    """Buffer is recreated when terminal size changes."""
    renderer, state = _make_renderer_and_state()

    with mock.patch.object(renderer, "_apply_palette"), \
         mock.patch.object(renderer, "_draw_overlay"), \
         mock.patch("curses.color_pair", return_value=0):
        renderer.draw(state, 0, 1, None)
    assert renderer._buffer.w == 100
    assert renderer._buffer.h == 30

    # Simulate terminal resize
    renderer.stdscr.getmaxyx.return_value = (40, 120)
    with mock.patch.object(renderer, "_apply_palette"), \
         mock.patch.object(renderer, "_draw_overlay"), \
         mock.patch("curses.color_pair", return_value=0):
        renderer.draw(state, 0, 1, None)
    assert renderer._buffer.w == 120
    assert renderer._buffer.h == 40


def test_plugin_hooks_receive_shim_not_stdscr():
    """draw_background and draw_extras receive _BufferShim, not raw stdscr."""
    renderer, state = _make_renderer_and_state()
    from hermes_neurovision.tune import TuneSettings
    state.tune = TuneSettings()

    received_args = []
    def spy_bg(screen, st, cp):
        received_args.append(("bg", type(screen).__name__))
    def spy_extras(screen, st, cp):
        received_args.append(("extras", type(screen).__name__))

    state.plugin.draw_background = spy_bg
    state.plugin.draw_extras = spy_extras

    with mock.patch.object(renderer, "_apply_palette"), \
         mock.patch.object(renderer, "_draw_overlay"), \
         mock.patch("curses.color_pair", return_value=0):
        renderer.draw(state, 0, 1, None)

    assert ("bg", "_BufferShim") in received_args
    assert ("extras", "_BufferShim") in received_args
