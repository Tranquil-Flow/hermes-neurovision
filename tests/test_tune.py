"""Tests for tune.py — TuneSettings and TuneOverlay."""
import curses

from hermes_neurovision.tune import TuneSettings, TuneOverlay


# ── TuneSettings ─────────────────────────────────────────────────────────────

def test_tune_settings_slider_defaults():
    t = TuneSettings()
    assert t.burst_scale == 1.0
    assert t.packet_rate_mult == 1.0
    assert t.pulse_rate_mult == 1.0
    assert t.particle_density == 1.0
    assert t.event_sensitivity == 1.0
    assert t.animation_speed == 1.0


def test_tune_settings_toggle_defaults():
    t = TuneSettings()
    assert t.show_packets is True
    assert t.show_particles is True
    assert t.show_pulses is True
    assert t.show_stars is True
    assert t.show_background is True
    assert t.show_nodes is True
    assert t.show_flash is True
    assert t.show_spawn_node is True


def test_tune_settings_is_default_when_untouched():
    assert TuneSettings().is_default() is True


def test_tune_settings_is_default_false_after_slider_change():
    t = TuneSettings()
    t.burst_scale = 1.5
    assert t.is_default() is False


def test_tune_settings_is_default_false_after_toggle_change():
    t = TuneSettings()
    t.show_packets = False
    assert t.is_default() is False


def test_tune_settings_reset_restores_sliders():
    t = TuneSettings()
    t.burst_scale = 2.0
    t.packet_rate_mult = 0.5
    t.animation_speed = 3.0
    t.reset()
    assert t.burst_scale == 1.0
    assert t.packet_rate_mult == 1.0
    assert t.animation_speed == 1.0
    assert t.is_default() is True


def test_tune_settings_reset_restores_toggles():
    t = TuneSettings()
    t.show_packets = False
    t.show_stars = False
    t.show_background = False
    t.reset()
    assert t.show_packets is True
    assert t.show_stars is True
    assert t.show_background is True
    assert t.is_default() is True


# ── TuneOverlay construction ──────────────────────────────────────────────────

def test_tune_overlay_starts_inactive():
    overlay = TuneOverlay(TuneSettings())
    assert overlay.active is False


def test_tune_overlay_exposes_current_settings():
    t = TuneSettings()
    overlay = TuneOverlay(t)
    assert overlay.current_settings is t


def test_tune_overlay_slider_count():
    overlay = TuneOverlay(TuneSettings())
    assert overlay.slider_count == 6


def test_tune_overlay_toggle_count():
    overlay = TuneOverlay(TuneSettings())
    assert overlay.toggle_count == 12


def test_tune_overlay_row_count_equals_slider_plus_toggle():
    overlay = TuneOverlay(TuneSettings())
    assert overlay.row_count == overlay.slider_count + overlay.toggle_count


# ── TuneOverlay navigation ────────────────────────────────────────────────────

def test_tune_overlay_down_increments_index():
    overlay = TuneOverlay(TuneSettings())
    overlay.active = True
    overlay.selected_index = 0
    overlay.handle_key(curses.KEY_DOWN)
    assert overlay.selected_index == 1


def test_tune_overlay_up_decrements_index():
    overlay = TuneOverlay(TuneSettings())
    overlay.active = True
    overlay.selected_index = 2
    overlay.handle_key(curses.KEY_UP)
    assert overlay.selected_index == 1


def test_tune_overlay_down_wraps_at_bottom():
    overlay = TuneOverlay(TuneSettings())
    overlay.active = True
    overlay.selected_index = overlay.row_count - 1
    overlay.handle_key(curses.KEY_DOWN)
    assert overlay.selected_index == 0


def test_tune_overlay_up_wraps_at_top():
    overlay = TuneOverlay(TuneSettings())
    overlay.active = True
    overlay.selected_index = 0
    overlay.handle_key(curses.KEY_UP)
    assert overlay.selected_index == overlay.row_count - 1


# ── TuneOverlay slider adjustment ─────────────────────────────────────────────

def test_tune_overlay_right_on_slider_increases_value():
    t = TuneSettings()
    overlay = TuneOverlay(t)
    overlay.active = True
    overlay.selected_index = 0  # burst_scale
    before = t.burst_scale
    overlay.handle_key(curses.KEY_RIGHT)
    assert t.burst_scale > before


def test_tune_overlay_left_on_slider_decreases_value():
    t = TuneSettings()
    overlay = TuneOverlay(t)
    overlay.active = True
    overlay.selected_index = 0  # burst_scale
    before = t.burst_scale
    overlay.handle_key(curses.KEY_LEFT)
    assert t.burst_scale < before


def test_tune_overlay_slider_clamped_at_min():
    t = TuneSettings()
    overlay = TuneOverlay(t)
    overlay.active = True
    overlay.selected_index = 0
    for _ in range(200):
        overlay.handle_key(curses.KEY_LEFT)
    assert t.burst_scale >= 0.0


def test_tune_overlay_slider_clamped_at_max():
    t = TuneSettings()
    overlay = TuneOverlay(t)
    overlay.active = True
    overlay.selected_index = 0
    for _ in range(200):
        overlay.handle_key(curses.KEY_RIGHT)
    assert t.burst_scale <= 5.0  # some reasonable upper bound


def test_tune_overlay_all_six_sliders_adjustable():
    """Each slider row (0-5) responds to KEY_RIGHT."""
    t = TuneSettings()
    overlay = TuneOverlay(t)
    overlay.active = True
    slider_attrs = ["burst_scale", "packet_rate_mult", "pulse_rate_mult",
                    "particle_density", "event_sensitivity", "animation_speed"]
    for idx, attr in enumerate(slider_attrs):
        overlay.selected_index = idx
        before = getattr(t, attr)
        overlay.handle_key(curses.KEY_RIGHT)
        assert getattr(t, attr) > before, f"slider {attr} at index {idx} did not increase"


# ── TuneOverlay toggle flipping ───────────────────────────────────────────────

def test_tune_overlay_right_on_toggle_flips_it():
    t = TuneSettings()
    overlay = TuneOverlay(t)
    overlay.active = True
    overlay.selected_index = overlay.slider_count  # first toggle row
    before = t.show_packets
    overlay.handle_key(curses.KEY_RIGHT)
    assert t.show_packets is not before


def test_tune_overlay_left_on_toggle_also_flips():
    t = TuneSettings()
    overlay = TuneOverlay(t)
    overlay.active = True
    overlay.selected_index = overlay.slider_count
    before = t.show_packets
    overlay.handle_key(curses.KEY_LEFT)
    assert t.show_packets is not before


def test_tune_overlay_all_eight_toggles_flippable():
    """Each toggle row (slider_count..row_count-1) flips on KEY_RIGHT."""
    t = TuneSettings()
    overlay = TuneOverlay(t)
    overlay.active = True
    toggle_attrs = ["show_packets", "show_particles", "show_pulses", "show_stars",
                    "show_background", "show_nodes", "show_flash", "show_spawn_node"]
    for i, attr in enumerate(toggle_attrs):
        overlay.selected_index = overlay.slider_count + i
        before = getattr(t, attr)
        overlay.handle_key(curses.KEY_RIGHT)
        assert getattr(t, attr) is not before, f"toggle {attr} at index {i} did not flip"
        # flip back
        overlay.handle_key(curses.KEY_RIGHT)
        assert getattr(t, attr) is before


# ── TuneOverlay special keys ──────────────────────────────────────────────────

def test_tune_overlay_r_resets_all():
    t = TuneSettings()
    overlay = TuneOverlay(t)
    overlay.active = True
    t.burst_scale = 2.0
    t.show_packets = False
    overlay.handle_key(ord('r'))
    assert t.burst_scale == 1.0
    assert t.show_packets is True


def test_tune_overlay_t_closes_overlay():
    overlay = TuneOverlay(TuneSettings())
    overlay.active = True
    overlay.handle_key(ord('t'))
    assert overlay.active is False


# ── TuneOverlay key consumption ───────────────────────────────────────────────

def test_tune_overlay_consumes_navigation_and_control_keys():
    overlay = TuneOverlay(TuneSettings())
    overlay.active = True
    for key in (curses.KEY_DOWN, curses.KEY_UP, curses.KEY_LEFT, curses.KEY_RIGHT,
                ord('r'), ord('t')):
        assert overlay.handle_key(key) is True, f"key {key} should be consumed"


def test_tune_overlay_does_not_consume_unrelated_keys():
    overlay = TuneOverlay(TuneSettings())
    overlay.active = True
    for key in (ord('q'), ord('Q'), ord(' '), ord('l'), ord('d')):
        assert overlay.handle_key(key) is False, f"key {key} should not be consumed"
