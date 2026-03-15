"""Tests for Phase 10 (ReactiveRenderer) and Phase 11 (Sound System)."""

import time
import unittest.mock as mock

import pytest

from hermes_neurovision.plugin import Reaction, ReactiveElement
from hermes_neurovision.renderer import FrameBuffer
from hermes_neurovision.reactive import (
    ActiveReaction,
    ReactiveRenderer,
    MAX_ACTIVE_REACTIONS,
)
from hermes_neurovision.sound import SoundCue, SoundEngine


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _make_reaction(
    element: ReactiveElement = ReactiveElement.PULSE,
    intensity: float = 0.8,
    origin: tuple = (0.5, 0.5),
    color_key: str = "accent",
    duration: float = 2.0,
    data: dict = None,
    sound: str = None,
) -> Reaction:
    return Reaction(
        element=element,
        intensity=intensity,
        origin=origin,
        color_key=color_key,
        duration=duration,
        data=data or {},
        sound=sound,
    )


def _buf_has_non_space(buf: FrameBuffer) -> bool:
    """Return True if any cell in the buffer is not a space."""
    for row in buf.cells:
        for cell in row:
            if cell.char != " ":
                return True
    return False


# ═══════════════════════════════════════════════════════════════════════
# Phase 10: ActiveReaction
# ═══════════════════════════════════════════════════════════════════════

class TestActiveReaction:
    def test_progress_starts_near_zero(self):
        r = _make_reaction(duration=10.0)
        ar = ActiveReaction(reaction=r)
        assert ar.progress < 0.1

    def test_progress_clamps_at_one(self):
        r = _make_reaction(duration=0.01)
        ar = ActiveReaction(reaction=r, start_time=time.time() - 1.0)
        assert ar.progress == 1.0

    def test_progress_zero_duration(self):
        r = _make_reaction(duration=0.0)
        ar = ActiveReaction(reaction=r)
        assert ar.progress == 1.0

    def test_alive_when_fresh(self):
        r = _make_reaction(duration=10.0)
        ar = ActiveReaction(reaction=r)
        assert ar.alive is True

    def test_not_alive_after_expiry(self):
        r = _make_reaction(duration=0.01)
        ar = ActiveReaction(reaction=r, start_time=time.time() - 1.0)
        assert ar.alive is False

    def test_elapsed_increases(self):
        r = _make_reaction(duration=10.0)
        ar = ActiveReaction(reaction=r, start_time=time.time() - 2.0)
        assert ar.elapsed >= 2.0


# ═══════════════════════════════════════════════════════════════════════
# Phase 10: ReactiveRenderer
# ═══════════════════════════════════════════════════════════════════════

class TestReactiveRenderer:
    def test_activate_stores_reaction(self):
        rr = ReactiveRenderer()
        r = _make_reaction(duration=10.0)
        ar = rr.activate(r)
        assert ar is not None
        assert len(rr.active) == 1
        assert rr.active[0].reaction is r

    def test_activate_returns_active_reaction(self):
        rr = ReactiveRenderer()
        r = _make_reaction()
        ar = rr.activate(r)
        assert isinstance(ar, ActiveReaction)
        assert ar.reaction is r

    def test_activate_cap_at_max(self):
        rr = ReactiveRenderer()
        for i in range(MAX_ACTIVE_REACTIONS):
            ar = rr.activate(_make_reaction(duration=60.0))
            assert ar is not None
        # One more should be rejected
        ar = rr.activate(_make_reaction(duration=60.0))
        assert ar is None
        assert len(rr.active) == MAX_ACTIVE_REACTIONS

    def test_expired_reactions_pruned(self):
        rr = ReactiveRenderer()
        # Add an already-expired reaction
        r = _make_reaction(duration=0.001)
        ar = ActiveReaction(reaction=r, start_time=time.time() - 1.0)
        rr._active.append(ar)
        assert len(rr._active) == 1
        # Activating another should prune the dead one
        rr.activate(_make_reaction(duration=60.0))
        assert len(rr.active) == 1  # only the new one

    def test_step_and_render_empty(self):
        rr = ReactiveRenderer()
        buf = FrameBuffer(40, 20)
        rr.step_and_render(buf)
        assert not _buf_has_non_space(buf)

    # ── Test each of the 12 element types writes to buffer ────────

    @pytest.mark.parametrize("element", list(ReactiveElement))
    def test_step_and_render_element_writes_to_buffer(self, element):
        rr = ReactiveRenderer()
        r = _make_reaction(
            element=element,
            intensity=0.8,
            origin=(0.5, 0.5),
            duration=10.0,
            data={"dx": 1},
        )
        ar = rr.activate(r)
        # Set start_time in the past so progress is significant (~50%)
        ar.start_time = time.time() - 5.0
        buf = FrameBuffer(80, 24)
        rr.step_and_render(buf)
        assert _buf_has_non_space(buf), f"{element.value} did not write to buffer"

    def test_step_and_render_prunes_expired(self):
        rr = ReactiveRenderer()
        expired = _make_reaction(duration=0.001)
        ar = ActiveReaction(reaction=expired, start_time=time.time() - 1.0)
        rr._active.append(ar)
        live = _make_reaction(duration=60.0)
        rr.activate(live)
        buf = FrameBuffer(40, 20)
        rr.step_and_render(buf)
        assert len(rr.active) == 1

    def test_multiple_reactions_render(self):
        rr = ReactiveRenderer()
        rr.activate(_make_reaction(element=ReactiveElement.PULSE, duration=60.0, origin=(0.2, 0.2)))
        rr.activate(_make_reaction(element=ReactiveElement.SPARK, duration=60.0, origin=(0.8, 0.8)))
        buf = FrameBuffer(80, 24)
        rr.step_and_render(buf)
        assert _buf_has_non_space(buf)
        assert len(rr.active) == 2


# ═══════════════════════════════════════════════════════════════════════
# Phase 11: SoundCue
# ═══════════════════════════════════════════════════════════════════════

class TestSoundCue:
    def test_dataclass_fields(self):
        cue = SoundCue(name="ping", type="bell")
        assert cue.name == "ping"
        assert cue.type == "bell"
        assert cue.value == ""
        assert cue.volume == 0.5
        assert cue.priority == 0

    def test_custom_fields(self):
        cue = SoundCue(name="alert", type="say", value="warning", volume=0.9, priority=5)
        assert cue.name == "alert"
        assert cue.type == "say"
        assert cue.value == "warning"
        assert cue.volume == 0.9
        assert cue.priority == 5


# ═══════════════════════════════════════════════════════════════════════
# Phase 11: SoundEngine
# ═══════════════════════════════════════════════════════════════════════

class TestSoundEngine:
    def test_enabled_toggle(self):
        eng = SoundEngine(enabled=True)
        assert eng.enabled is True
        eng.enabled = False
        assert eng.enabled is False

    def test_disabled_by_default_arg(self):
        eng = SoundEngine(enabled=False)
        assert eng.enabled is False

    def test_volume_clamping_high(self):
        eng = SoundEngine(volume=5.0)
        assert eng.volume == 1.0

    def test_volume_clamping_low(self):
        eng = SoundEngine(volume=-1.0)
        assert eng.volume == 0.0

    def test_volume_setter_clamps(self):
        eng = SoundEngine()
        eng.volume = 2.0
        assert eng.volume == 1.0
        eng.volume = -0.5
        assert eng.volume == 0.0
        eng.volume = 0.7
        assert eng.volume == pytest.approx(0.7)

    def test_play_returns_false_when_disabled(self):
        eng = SoundEngine(enabled=False)
        cue = SoundCue(name="test", type="bell")
        assert eng.play(cue) is False

    def test_play_bell(self):
        eng = SoundEngine(enabled=True)
        cue = SoundCue(name="beep", type="bell")
        mock_curses = mock.MagicMock()
        with mock.patch.dict("sys.modules", {"curses": mock_curses}):
            result = eng.play(cue)
        assert result is True
        mock_curses.beep.assert_called_once()

    def test_play_flash(self):
        eng = SoundEngine(enabled=True)
        cue = SoundCue(name="blink", type="flash")
        mock_curses = mock.MagicMock()
        with mock.patch.dict("sys.modules", {"curses": mock_curses}):
            result = eng.play(cue)
        assert result is True
        mock_curses.flash.assert_called_once()

    def test_play_cooldown(self):
        eng = SoundEngine(enabled=True)
        cue = SoundCue(name="cooldown_test", type="bell")
        with mock.patch.object(eng, "_play_bell"):
            first = eng.play(cue)
            assert first is True
            # Same sound immediately should be blocked by cooldown
            second = eng.play(cue)
            assert second is False

    def test_play_different_sounds_no_cooldown(self):
        eng = SoundEngine(enabled=True)
        cue1 = SoundCue(name="sound_a", type="bell")
        cue2 = SoundCue(name="sound_b", type="bell")
        with mock.patch.object(eng, "_play_bell"):
            assert eng.play(cue1) is True
            assert eng.play(cue2) is True

    def test_play_for_event_found(self):
        eng = SoundEngine(enabled=True)
        cue = SoundCue(name="tool_beep", type="bell")
        cues = {"tool_call": cue}
        with mock.patch.object(eng, "_play_bell"):
            result = eng.play_for_event("tool_call", cues)
        assert result is True

    def test_play_for_event_unknown(self):
        eng = SoundEngine(enabled=True)
        cues = {"tool_call": SoundCue(name="beep", type="bell")}
        result = eng.play_for_event("nonexistent_event", cues)
        assert result is False

    def test_play_for_event_disabled(self):
        eng = SoundEngine(enabled=False)
        cue = SoundCue(name="beep", type="bell")
        cues = {"tool_call": cue}
        result = eng.play_for_event("tool_call", cues)
        assert result is False

    def test_play_say_macos(self):
        eng = SoundEngine(enabled=True)
        eng._is_macos = True
        cue = SoundCue(name="speak", type="say", value="hello")
        with mock.patch("subprocess.Popen") as mock_popen:
            result = eng.play(cue)
        assert result is True
        mock_popen.assert_called_once()
        args = mock_popen.call_args
        assert "say" in args[0][0]

    def test_play_file_macos(self):
        eng = SoundEngine(enabled=True)
        eng._is_macos = True
        cue = SoundCue(name="sfx", type="file", value="/tmp/sound.wav", volume=0.8)
        with mock.patch("subprocess.Popen") as mock_popen:
            result = eng.play(cue)
        assert result is True
        mock_popen.assert_called_once()
        args = mock_popen.call_args
        assert "afplay" in args[0][0]

    def test_play_say_not_macos_returns_false(self):
        eng = SoundEngine(enabled=True)
        eng._is_macos = False
        cue = SoundCue(name="speak", type="say", value="hello")
        result = eng.play(cue)
        assert result is False

    def test_play_file_not_macos_returns_false(self):
        eng = SoundEngine(enabled=True)
        eng._is_macos = False
        cue = SoundCue(name="sfx", type="file", value="/tmp/sound.wav")
        result = eng.play(cue)
        assert result is False

    def test_play_unknown_type_returns_false(self):
        eng = SoundEngine(enabled=True)
        eng._is_macos = False
        cue = SoundCue(name="x", type="unknown_type")
        result = eng.play(cue)
        assert result is False

    def test_bell_fallback_on_curses_error(self):
        """If curses.beep() raises, fallback writes BEL to stdout."""
        import curses as real_curses
        mock_curses = mock.MagicMock()
        mock_curses.error = real_curses.error
        mock_curses.beep.side_effect = real_curses.error("no beep")
        eng = SoundEngine(enabled=True)
        with mock.patch.dict("sys.modules", {"curses": mock_curses}):
            with mock.patch("sys.stdout") as mock_stdout:
                result = eng.play(SoundCue(name="bell_fb", type="bell"))
        assert result is True
        mock_stdout.write.assert_called_with("\a")

    def test_flash_error_swallowed(self):
        """If curses.flash() raises, it's silently caught."""
        import curses as real_curses
        mock_curses = mock.MagicMock()
        mock_curses.error = real_curses.error
        mock_curses.flash.side_effect = real_curses.error("no flash")
        eng = SoundEngine(enabled=True)
        with mock.patch.dict("sys.modules", {"curses": mock_curses}):
            result = eng.play(SoundCue(name="flash_err", type="flash"))
        # flash error is swallowed, play still returns True
        assert result is True
