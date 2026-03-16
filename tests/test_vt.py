"""Tests for the VT100 terminal emulator."""
from hermes_neurovision.vt import VTCell, VTScreen


# ── VTCell ──────────────────────────────────────────────────────────────

def test_vtcell_defaults():
    cell = VTCell()
    assert cell.char == " "
    assert cell.bold is False
    assert cell.fg == 7
    assert cell.born_frame == 0


# ── VTScreen init ───────────────────────────────────────────────────────

def test_vtscreen_init():
    vt = VTScreen(24, 80)
    assert vt.rows == 24
    assert vt.cols == 80
    assert vt.cursor_row == 0
    assert vt.cursor_col == 0
    assert len(vt.cells) == 24
    assert len(vt.cells[0]) == 80
    assert vt.cells[0][0].char == " "


def test_vtscreen_init_small():
    vt = VTScreen(2, 3)
    assert len(vt.cells) == 2
    assert len(vt.cells[1]) == 3


# ── Character processing ───────────────────────────────────────────────

def test_feed_printable():
    vt = VTScreen(24, 80)
    vt.feed(b"Hello")
    assert vt.cells[0][0].char == "H"
    assert vt.cells[0][1].char == "e"
    assert vt.cells[0][4].char == "o"
    assert vt.cursor_col == 5
    assert vt.cursor_row == 0


def test_feed_newline():
    vt = VTScreen(24, 80)
    vt.feed(b"A\nB")
    assert vt.cells[0][0].char == "A"
    assert vt.cells[1][0].char == "B"
    assert vt.cursor_row == 1
    assert vt.cursor_col == 1


def test_feed_carriage_return():
    vt = VTScreen(24, 80)
    vt.feed(b"Hello\rX")
    assert vt.cells[0][0].char == "X"
    assert vt.cells[0][1].char == "e"
    assert vt.cursor_col == 1


def test_feed_backspace():
    vt = VTScreen(24, 80)
    vt.feed(b"AB\x08C")
    assert vt.cells[0][0].char == "A"
    assert vt.cells[0][1].char == "C"
    assert vt.cursor_col == 2


def test_feed_tab():
    vt = VTScreen(24, 80)
    vt.feed(b"A\tB")
    assert vt.cells[0][0].char == "A"
    assert vt.cursor_col == 9  # tab to col 8, then B at col 8, cursor at 9
    assert vt.cells[0][8].char == "B"


def test_line_wrap():
    vt = VTScreen(24, 5)
    vt.feed(b"ABCDE")
    assert vt.cursor_col == 0
    assert vt.cursor_row == 1
    assert vt.cells[0][4].char == "E"


def test_scroll_up():
    vt = VTScreen(3, 5)
    vt.feed(b"AAA\nBBB\nCCC\nDDD")
    # Row 0 (AAA) should have scrolled into scrollback
    assert vt.cells[0][0].char == "B"
    assert vt.cells[1][0].char == "C"
    assert vt.cells[2][0].char == "D"
    assert len(vt.scrollback) == 1
    assert vt.scrollback[0][0].char == "A"


def test_born_frame_set():
    vt = VTScreen(24, 80)
    vt.set_frame(42)
    vt.feed(b"X")
    assert vt.cells[0][0].born_frame == 42


def test_bytes_since_last_poll():
    vt = VTScreen(24, 80)
    vt.feed(b"Hello")
    assert vt.bytes_since_last_poll == 5
    vt.reset_poll_counters()
    assert vt.bytes_since_last_poll == 0


def test_scrolls_since_last_poll():
    vt = VTScreen(3, 10)
    vt.feed(b"A\nB\nC\nD")  # triggers 1 scroll
    assert vt.scrolls_since_last_poll == 1
    vt.reset_poll_counters()
    assert vt.scrolls_since_last_poll == 0


# ── CSI sequences ──────────────────────────────────────────────────────

def test_csi_cursor_up():
    vt = VTScreen(24, 80)
    vt.feed(b"\n\n\n")  # move to row 3
    vt.feed(b"\x1b[2A")  # cursor up 2
    assert vt.cursor_row == 1


def test_csi_cursor_down():
    vt = VTScreen(24, 80)
    vt.feed(b"\x1b[3B")  # cursor down 3
    assert vt.cursor_row == 3


def test_csi_cursor_forward():
    vt = VTScreen(24, 80)
    vt.feed(b"\x1b[10C")
    assert vt.cursor_col == 10


def test_csi_cursor_back():
    vt = VTScreen(24, 80)
    vt.feed(b"ABCDE\x1b[3D")
    assert vt.cursor_col == 2


def test_csi_cursor_position():
    vt = VTScreen(24, 80)
    vt.feed(b"\x1b[5;10H")
    assert vt.cursor_row == 4  # 1-indexed → 0-indexed
    assert vt.cursor_col == 9


def test_csi_erase_line():
    vt = VTScreen(24, 80)
    vt.feed(b"Hello World")
    vt.feed(b"\x1b[5D")  # back 5 → cursor at col 6
    vt.feed(b"\x1b[K")   # erase from cursor to end of line
    assert vt.cells[0][0].char == "H"
    assert vt.cells[0][5].char == " "  # space between Hello and World (preserved)
    assert vt.cells[0][6].char == " "  # erased (was 'W')
    assert vt.cells[0][10].char == " "  # erased


def test_csi_erase_display():
    vt = VTScreen(3, 5)
    vt.feed(b"AAAAA\nBBBBB\nCCCCC")
    vt.feed(b"\x1b[2J")  # erase entire display
    for r in range(3):
        for c in range(5):
            assert vt.cells[r][c].char == " "


def test_csi_sgr_bold():
    vt = VTScreen(24, 80)
    vt.feed(b"\x1b[1mX\x1b[22mY")
    assert vt.cells[0][0].bold is True
    assert vt.cells[0][1].bold is False


def test_csi_sgr_fg_color():
    vt = VTScreen(24, 80)
    vt.feed(b"\x1b[31mR\x1b[32mG\x1b[0mN")
    assert vt.cells[0][0].fg == 1  # red
    assert vt.cells[0][1].fg == 2  # green
    assert vt.cells[0][2].fg == 7  # reset → default


def test_csi_alt_screen_ignored():
    """Alt screen enter/exit sequences should be silently ignored."""
    vt = VTScreen(3, 10)
    vt.feed(b"Hello")
    vt.feed(b"\x1b[?1049h")  # enter alt screen
    vt.feed(b"X")
    assert vt.cells[0][0].char == "H"  # still on main screen


def test_resize():
    vt = VTScreen(3, 5)
    vt.feed(b"AAAAA\nBBBBB\nCCCCC")
    vt.resize(2, 4)
    assert vt.rows == 2
    assert vt.cols == 4
    assert len(vt.cells) == 2
    assert len(vt.cells[0]) == 4
    assert vt.cursor_row <= 1
    assert vt.cursor_col <= 3
