"""Tests for the fade compositor."""
import curses

from hermes_neurovision.compositor import FadeConfig, FadeCompositor


def test_fade_config_defaults():
    cfg = FadeConfig()
    assert cfg.mode == "position"
    assert cfg.fade_start_pct == 0.0
    assert cfg.fade_end_pct == 0.4
    assert cfg.text_opacity == 1.0
    assert cfg.text_bg == "transparent"
    assert cfg.text_bg_opacity == 0.0
    assert cfg.text_glow is False
    assert cfg.text_glow_color == "theme"
    assert cfg.text_glow_intensity == 1.0
    assert cfg.text_color == "auto"


def test_position_opacity_bottom():
    """Bottom of screen (below fade_end) should be fully opaque."""
    cfg = FadeConfig(fade_start_pct=0.0, fade_end_pct=0.4)
    comp = FadeCompositor(cfg)
    opacity = comp.compute_opacity(20, 24, born_frame=0, current_frame=0)
    assert opacity == 1.0


def test_position_opacity_top():
    """Top of screen (at fade_start) should be hidden."""
    cfg = FadeConfig(fade_start_pct=0.0, fade_end_pct=0.4)
    comp = FadeCompositor(cfg)
    opacity = comp.compute_opacity(0, 24, born_frame=0, current_frame=0)
    assert opacity == 0.0


def test_position_opacity_mid():
    """Middle of fade zone should be between 0 and 1."""
    cfg = FadeConfig(fade_start_pct=0.0, fade_end_pct=0.5)
    comp = FadeCompositor(cfg)
    opacity = comp.compute_opacity(5, 20, born_frame=0, current_frame=0)
    assert 0.0 < opacity < 1.0


def test_position_opacity_equal_start_end():
    """When start == end, no division by zero."""
    cfg = FadeConfig(fade_start_pct=0.3, fade_end_pct=0.3)
    comp = FadeCompositor(cfg)
    opacity = comp.compute_opacity(0, 24, born_frame=0, current_frame=0)
    assert isinstance(opacity, float)


def test_age_mode():
    """Age mode: fresh text is opaque, old text fades."""
    cfg = FadeConfig(mode="age", fade_lifetime=100)
    comp = FadeCompositor(cfg)
    fresh = comp.compute_opacity(0, 24, born_frame=90, current_frame=100)
    old = comp.compute_opacity(0, 24, born_frame=0, current_frame=100)
    assert fresh > old


def test_both_mode():
    """Both mode multiplies position and age."""
    cfg = FadeConfig(mode="both", fade_start_pct=0.0, fade_end_pct=0.5, fade_lifetime=100)
    comp = FadeCompositor(cfg)
    # Top + old = very hidden
    opacity = comp.compute_opacity(0, 20, born_frame=0, current_frame=100)
    assert opacity == 0.0


def test_text_opacity_multiplier():
    """Global text_opacity should scale the result."""
    cfg = FadeConfig(fade_start_pct=0.0, fade_end_pct=0.0, text_opacity=0.5)
    comp = FadeCompositor(cfg)
    opacity = comp.compute_opacity(20, 24, born_frame=0, current_frame=0)
    assert opacity <= 0.5


def test_opacity_to_attr_hidden():
    comp = FadeCompositor(FadeConfig())
    attr = comp.opacity_to_curses_attr(0.0)
    assert attr is None


def test_opacity_to_attr_dim():
    comp = FadeCompositor(FadeConfig())
    attr = comp.opacity_to_curses_attr(0.2)
    assert attr == curses.A_DIM


def test_opacity_to_attr_normal():
    comp = FadeCompositor(FadeConfig())
    attr = comp.opacity_to_curses_attr(0.5)
    assert attr == curses.A_NORMAL


def test_opacity_to_attr_bold():
    comp = FadeCompositor(FadeConfig())
    attr = comp.opacity_to_curses_attr(0.9)
    assert attr == curses.A_BOLD


def test_resolve_color_auto():
    """Auto mode maps default text to soft (not blinding white)."""
    comp = FadeCompositor(FadeConfig(text_color="auto"))
    pairs = {"base": 1, "soft": 2, "bright": 3, "accent": 4, "warning": 5}
    pair_num, extra = comp.resolve_color_pair(7, False, pairs)
    assert pair_num == 2  # default fg → soft (readable, not glaring)


def test_resolve_color_override():
    """Color override uses specified color regardless of VT color."""
    comp = FadeCompositor(FadeConfig(text_color="cyan"))
    pairs = {"base": 1, "soft": 2, "bright": 3, "accent": 4, "warning": 5}
    pair_num, extra = comp.resolve_color_pair(1, False, pairs)  # VT says red
    assert pair_num == 2  # but we override to cyan → soft


def test_resolve_color_glow():
    """Glow mode uses glow_color with bold at high intensity."""
    comp = FadeCompositor(FadeConfig(text_glow=True, text_glow_color="magenta", text_glow_intensity=1.0))
    pairs = {"base": 1, "soft": 2, "bright": 3, "accent": 4, "warning": 5}
    pair_num, extra = comp.resolve_color_pair(7, False, pairs)
    assert pair_num == 4  # magenta → accent
    assert extra & curses.A_BOLD  # high intensity → bold


def test_resolve_color_glow_low_intensity():
    """Glow at low intensity uses DIM instead of BOLD."""
    comp = FadeCompositor(FadeConfig(text_glow=True, text_glow_color="green", text_glow_intensity=0.2))
    pairs = {"base": 1, "soft": 2, "bright": 3, "accent": 4, "warning": 5}
    pair_num, extra = comp.resolve_color_pair(7, False, pairs)
    assert pair_num == 1  # green → base
    assert extra & curses.A_DIM


def test_bg_preset_transparent():
    cfg = FadeConfig(text_bg="transparent")
    assert cfg.text_bg_opacity == 0.0


def test_bg_preset_dim():
    cfg = FadeConfig(text_bg="dim")
    assert cfg.text_bg_opacity == 0.3


def test_bg_preset_solid():
    cfg = FadeConfig(text_bg="solid")
    assert cfg.text_bg_opacity == 1.0
