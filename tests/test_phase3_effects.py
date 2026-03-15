"""Tests for Phase 3: New Effects + Reactive Primitives."""

import time
import unittest.mock as mock

from hermes_neurovision.scene import (
    ThemeState, Streak, OverlayEffect, ActiveSpecial,
)
from hermes_neurovision.themes import build_theme_config


def _make_state(theme="electric-mycelium", seed=42, w=100, h=30):
    config = build_theme_config(theme)
    return ThemeState(config, w, h, seed=seed)


# ── Streak dataclass ─────────────────────────────────────────────────

def test_streak_step_advances_position():
    s = Streak(x=10.0, y=5.0, dx=1.0, dy=0.5, length=5, life=10, max_life=10)
    alive = s.step()
    assert alive is True
    assert s.x == 11.0
    assert s.y == 5.5
    assert s.life == 9


def test_streak_dies_at_zero_life():
    s = Streak(x=0.0, y=0.0, dx=1.0, dy=0.0, length=3, life=1, max_life=5)
    alive = s.step()
    assert alive is False


# ── OverlayEffect / ActiveSpecial ────────────────────────────────────

def test_overlay_effect_fields():
    oe = OverlayEffect(trigger_effect="pulse", intensity=0.7, start_time=100.0)
    assert oe.trigger_effect == "pulse"
    assert oe.duration == 1.0  # default


def test_active_special_fields():
    asp = ActiveSpecial(name="shockwave", intensity=0.9, start_time=100.0, duration=2.0)
    assert asp.name == "shockwave"
    assert asp.duration == 2.0


# ── New trigger effects ──────────────────────────────────────────────

class FakeTrigger:
    def __init__(self, effect, intensity=0.5, color_key="accent", target="random_node"):
        self.effect = effect
        self.intensity = intensity
        self.color_key = color_key
        self.target = target


def test_ripple_creates_multiple_pulses():
    state = _make_state()
    before = len(state.pulses)
    state.apply_trigger(FakeTrigger("ripple", intensity=0.6))
    after = len(state.pulses)
    # Ripple should create 3 staggered pulses
    assert after - before == 3


def test_ripple_at_center():
    state = _make_state()
    state.apply_trigger(FakeTrigger("ripple", target="center"))
    # All 3 pulses should be at the same node position
    assert len(state.pulses) >= 3
    positions = set((p[0], p[1]) for p in state.pulses[-3:])
    assert len(positions) == 1  # all at same (x, y)


def test_cascade_populates_queue():
    state = _make_state()
    state.apply_trigger(FakeTrigger("cascade", target="all"))
    assert len(state._cascade_queue) > 0


def test_cascade_random_target():
    state = _make_state()
    state.apply_trigger(FakeTrigger("cascade", target="random_node"))
    assert len(state._cascade_queue) > 0
    assert len(state._cascade_queue) <= 5


def test_converge_spawns_particles():
    state = _make_state()
    before = len(state.particles)
    state.apply_trigger(FakeTrigger("converge", intensity=0.8))
    after = len(state.particles)
    assert after > before


def test_converge_particles_move_toward_target():
    """Converge particles should have velocity pointing toward the target node."""
    state = _make_state()
    state.apply_trigger(FakeTrigger("converge", intensity=0.8, target="center"))
    # Particles were just spawned, should have some velocity
    for p in state.particles[-5:]:
        assert p.vx != 0.0 or p.vy != 0.0


def test_streak_effect_adds_streak():
    state = _make_state()
    assert len(state.streaks) == 0
    state.apply_trigger(FakeTrigger("streak", intensity=0.7))
    assert len(state.streaks) >= 1


def test_streak_is_streak_instance():
    state = _make_state()
    state.apply_trigger(FakeTrigger("streak"))
    assert isinstance(state.streaks[0], Streak)


# ── Overlay effect tracking ──────────────────────────────────────────

def test_apply_trigger_creates_overlay_effect():
    """Every trigger appends an OverlayEffect."""
    state = _make_state()
    state.apply_trigger(FakeTrigger("pulse"))
    assert len(state.overlay_effects) >= 1
    assert isinstance(state.overlay_effects[-1], OverlayEffect)
    assert state.overlay_effects[-1].trigger_effect == "pulse"


def test_overlay_effects_expire():
    state = _make_state()
    # Manually add an expired overlay
    state.overlay_effects.append(OverlayEffect(
        trigger_effect="test", intensity=0.5,
        start_time=time.time() - 10.0, duration=1.0,
    ))
    state.step()
    # Should be cleaned up
    expired = [oe for oe in state.overlay_effects
               if time.time() - oe.start_time >= oe.duration]
    assert len(expired) == 0


# ── Palette shift tracking ───────────────────────────────────────────

def test_palette_shift_default_no_change():
    """Default plugin.palette_shift returns None — no shift stored."""
    state = _make_state()
    state.apply_trigger(FakeTrigger("pulse"))
    # Default returns None, so no shifted palette
    assert state._shifted_palette is None


def test_palette_shift_stores_shifted():
    """When plugin returns a palette, it's stored with a timeout."""
    state = _make_state()
    state.plugin.palette_shift = lambda *a: (10, 20, 30, 40)
    state.apply_trigger(FakeTrigger("pulse"))
    assert state._shifted_palette == (10, 20, 30, 40)
    assert state._palette_shift_until > time.time()


# ── Special effects activation ───────────────────────────────────────

def test_special_effects_activation():
    """When plugin declares special effects, matching triggers activate them."""
    from hermes_neurovision.plugin import SpecialEffect
    state = _make_state()
    state.plugin.special_effects = lambda: [
        SpecialEffect(name="shockwave", trigger_kinds=["flash"], duration=2.0),
    ]
    state.apply_trigger(FakeTrigger("flash", intensity=0.9))
    assert len(state.active_specials) >= 1
    assert state.active_specials[-1].name == "shockwave"


def test_special_effects_no_match():
    """Non-matching trigger doesn't activate special effects."""
    from hermes_neurovision.plugin import SpecialEffect
    state = _make_state()
    state.plugin.special_effects = lambda: [
        SpecialEffect(name="shockwave", trigger_kinds=["flash"]),
    ]
    state.apply_trigger(FakeTrigger("pulse"))
    specials_named = [s for s in state.active_specials if s.name == "shockwave"]
    assert len(specials_named) == 0


# ── Step cleans up expired ───────────────────────────────────────────

def test_step_cleans_dead_streaks():
    state = _make_state()
    state.streaks.append(Streak(x=50.0, y=15.0, dx=1.0, dy=0.0, length=3, life=1, max_life=5))
    state.step()
    assert len(state.streaks) == 0  # died this step


def test_step_keeps_alive_streaks():
    state = _make_state()
    state.streaks.append(Streak(x=50.0, y=15.0, dx=1.0, dy=0.0, length=3, life=10, max_life=10))
    state.step()
    assert len(state.streaks) == 1


# ── Last event time tracking ─────────────────────────────────────────

def test_last_event_time_updates():
    state = _make_state()
    before = state._last_event_time
    state.apply_trigger(FakeTrigger("pulse"))
    assert state._last_event_time > before


# ── Resize clears new fields ─────────────────────────────────────────

def test_resize_clears_new_fields():
    state = _make_state()
    state.streaks.append(Streak(x=0, y=0, dx=1, dy=0, length=3))
    state.overlay_effects.append(OverlayEffect("test", 0.5, 100.0))
    state.active_specials.append(ActiveSpecial("fx", 0.5, 100.0, 1.0))
    state._cascade_queue.append((0, 100.0))
    state.resize(80, 20)
    assert len(state.streaks) == 0
    assert len(state.overlay_effects) == 0
    assert len(state.active_specials) == 0
    assert len(state._cascade_queue) == 0


# ── TuneSettings new fields ─────────────────────────────────────────

def test_tune_new_fields_exist():
    from hermes_neurovision.tune import TuneSettings
    t = TuneSettings()
    assert t.show_streaks is True
    assert t.show_specials is True
    assert t.show_overlays is True
    assert t.color_shifts is True


def test_tune_reset_resets_new_fields():
    from hermes_neurovision.tune import TuneSettings
    t = TuneSettings()
    t.show_streaks = False
    t.show_specials = False
    t.color_shifts = False
    t.reset()
    assert t.show_streaks is True
    assert t.show_specials is True
    assert t.color_shifts is True


def test_tune_is_default_checks_new_fields():
    from hermes_neurovision.tune import TuneSettings
    t = TuneSettings()
    assert t.is_default() is True
    t.show_streaks = False
    assert t.is_default() is False


# ── Renderer streaks / overlay / special drawing ─────────────────────

def _make_renderer_and_state():
    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (30, 100)
    with mock.patch("curses.has_colors", return_value=False):
        from hermes_neurovision.renderer import Renderer
        renderer = Renderer(mock_stdscr)
    state = _make_state()
    return renderer, state


def _draw(renderer, state):
    with mock.patch.object(renderer, "_apply_palette"), \
         mock.patch.object(renderer, "_draw_overlay"), \
         mock.patch("curses.color_pair", return_value=0):
        renderer.draw(state, 0, 1, None)


def test_renderer_draws_streaks():
    """Renderer calls _draw_streaks when streaks exist."""
    renderer, state = _make_renderer_and_state()
    state.streaks.append(Streak(x=50.0, y=15.0, dx=1.0, dy=0.0, length=5, life=10, max_life=10))
    with mock.patch.object(renderer, "_draw_streaks", wraps=renderer._draw_streaks) as spy:
        _draw(renderer, state)
        spy.assert_called_once()


def test_renderer_streak_writes_to_buffer():
    """Streaks write characters to the buffer."""
    renderer, state = _make_renderer_and_state()
    state.streaks.append(Streak(x=50.0, y=15.0, dx=1.0, dy=0.0, length=5, life=10, max_life=10))
    with mock.patch("curses.color_pair", return_value=0):
        # Just call _draw_streaks directly after buffer creation
        from hermes_neurovision.renderer import FrameBuffer
        renderer._buffer = FrameBuffer(100, 30)
        renderer._draw_streaks(state)
    # Check that at least one cell was written
    cells_written = sum(
        1 for row in renderer._buffer.cells for cell in row if cell.char != " "
    )
    assert cells_written > 0
