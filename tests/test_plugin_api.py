"""Tests for Phase 2: Plugin API Expansion — all new methods have safe defaults."""

from hermes_neurovision.plugin import (
    ThemePlugin, SpecialEffect, Reaction, ReactiveElement,
)


# ── Dataclass tests ───────────────────────────────────────────────────

def test_reactive_element_enum_has_12_members():
    assert len(ReactiveElement) == 12


def test_reactive_element_values():
    expected = {
        "pulse", "ripple", "stream", "bloom", "shatter", "orbit",
        "gauge", "spark", "wave", "glyph", "trail", "constellation",
    }
    assert {e.value for e in ReactiveElement} == expected


def test_special_effect_defaults():
    se = SpecialEffect(name="test_fx", trigger_kinds=["error"])
    assert se.name == "test_fx"
    assert se.trigger_kinds == ["error"]
    assert se.min_intensity == 0.0
    assert se.cooldown == 5.0
    assert se.duration == 2.0


def test_reaction_defaults():
    r = Reaction(
        element=ReactiveElement.PULSE,
        intensity=0.8,
        origin=(0.5, 0.5),
        color_key="bright",
        duration=1.5,
    )
    assert r.element == ReactiveElement.PULSE
    assert r.data == {}
    assert r.sound is None


def test_reaction_with_data():
    r = Reaction(
        element=ReactiveElement.STREAM,
        intensity=0.6,
        origin=(0.0, 1.0),
        color_key="accent",
        duration=2.0,
        data={"direction": "down", "particle_char": "."},
        sound="whoosh",
    )
    assert r.data["direction"] == "down"
    assert r.sound == "whoosh"


# ── Existing methods still work ──────────────────────────────────────

def test_existing_methods_unchanged():
    """All v1.0 methods exist and return expected defaults."""
    p = ThemePlugin()
    assert p.build_nodes(80, 24, 40.0, 12.0, 20, None) is None
    assert p.edge_keep_count() == 3
    assert p.step_star([], 0, 80, 24, None) is False
    assert p.spawn_particle(80, 24, [], None) is None
    assert p.particle_base_chance() == 0.028
    assert p.particle_life_range() == (7, 14)
    assert p.pulse_params() == (0.28, 0.16)
    assert p.pulse_style() == "ring"
    assert p.packet_budget() == 4
    assert p.star_glyph(0.5, 0) is None
    assert p.node_glyph(0, 0.8, 10) == "\u25cf"
    assert p.node_glyph(0, 0.5, 10) == "\u2022"
    assert p.node_color_key(0, 0.8, 10) == "bright"
    assert p.node_color_key(0, 0.3, 10) == "soft"
    assert p.edge_glyph(1.0, 0.0) is None
    assert p.edge_color_key(0, 0, 0) == "base"
    assert p.packet_color_key() == "accent"
    assert p.particle_color_key(0.8) == "accent"
    assert p.particle_color_key(0.3) == "soft"
    assert p.pulse_color_key() == "soft"
    assert p.node_position_adjust(10.0, 5.0, 0, 0, 80, 24) is None


def test_existing_draw_hooks_are_noops():
    p = ThemePlugin()
    assert p.draw_background(None, None, {}) is None
    assert p.draw_extras(None, None, {}) is None


# ── New: Reactive Primitives ─────────────────────────────────────────

def test_palette_shift_default_none():
    assert ThemePlugin().palette_shift("pulse", 0.5, (1, 2, 3, 4)) is None


def test_draw_overlay_effect_noop():
    """draw_overlay_effect is a no-op by default."""
    result = ThemePlugin().draw_overlay_effect(None, None, {}, "pulse", 0.5, 0.3)
    assert result is None


def test_special_effects_default_empty():
    assert ThemePlugin().special_effects() == []


def test_draw_special_noop():
    result = ThemePlugin().draw_special(None, None, {}, "fx", 0.5, 0.8)
    assert result is None


def test_effect_zones_default_empty():
    assert ThemePlugin().effect_zones() == {}


def test_intensity_curve_identity():
    p = ThemePlugin()
    assert p.intensity_curve(0.0) == 0.0
    assert p.intensity_curve(0.5) == 0.5
    assert p.intensity_curve(1.0) == 1.0


def test_ambient_tick_noop():
    result = ThemePlugin().ambient_tick(None, None, {}, 5.0)
    assert result is None


# ── New: Post-Processing ─────────────────────────────────────────────

def test_warp_field_identity():
    p = ThemePlugin()
    assert p.warp_field(10, 5, 80, 24, 0, 1.0) == (10, 5)


def test_void_points_empty():
    assert ThemePlugin().void_points(80, 24, 0, 1.0) == []


def test_echo_decay_zero():
    assert ThemePlugin().echo_decay() == 0


def test_force_points_empty():
    assert ThemePlugin().force_points(80, 24, 0, 1.0) == []


def test_decay_sequence_none():
    assert ThemePlugin().decay_sequence() is None


def test_symmetry_none():
    assert ThemePlugin().symmetry() is None


def test_depth_layers_one():
    assert ThemePlugin().depth_layers() == 1


def test_glow_radius_zero():
    assert ThemePlugin().glow_radius() == 0


def test_render_mask_none():
    assert ThemePlugin().render_mask(80, 24, 0, 1.0) is None


# ── New: Emergent Systems ────────────────────────────────────────────

def test_emergent_configs_all_none():
    p = ThemePlugin()
    assert p.automaton_config() is None
    assert p.physarum_config() is None
    assert p.neural_field_config() is None
    assert p.wave_config() is None
    assert p.boids_config() is None
    assert p.reaction_diffusion_config() is None


def test_emergent_layer_default():
    assert ThemePlugin().emergent_layer() == "background"


# ── New: Visual Effect Hooks ─────────────────────────────────────────

def test_streak_color_key():
    assert ThemePlugin().streak_color_key() == "accent"


# ── New: Reactive Element System ─────────────────────────────────────

def test_reactive_map_exists_and_covers_all_elements():
    """REACTIVE_MAP maps event kinds to all 12 ReactiveElement types."""
    p = ThemePlugin()
    assert isinstance(p.REACTIVE_MAP, dict)
    mapped_elements = set(p.REACTIVE_MAP.values())
    all_elements = set(ReactiveElement)
    assert mapped_elements == all_elements, (
        f"Missing elements in REACTIVE_MAP: {all_elements - mapped_elements}"
    )


def test_reactive_map_has_expected_mappings():
    m = ThemePlugin.REACTIVE_MAP
    assert m["agent_start"] == ReactiveElement.PULSE
    assert m["tool_call"] == ReactiveElement.RIPPLE
    assert m["llm_start"] == ReactiveElement.STREAM
    assert m["memory_save"] == ReactiveElement.BLOOM
    assert m["error"] == ReactiveElement.SHATTER
    assert m["cron_tick"] == ReactiveElement.ORBIT
    assert m["context_pressure"] == ReactiveElement.GAUGE
    assert m["approval_request"] == ReactiveElement.SPARK
    assert m["compression_started"] == ReactiveElement.WAVE
    assert m["personality_change"] == ReactiveElement.GLYPH
    assert m["browser_navigate"] == ReactiveElement.TRAIL
    assert m["mcp_connected"] == ReactiveElement.CONSTELLATION


def test_react_default_none():
    assert ThemePlugin().react("agent_start", {}) is None


def test_render_methods_all_noop():
    """All 12 render_* methods are no-ops by default."""
    p = ThemePlugin()
    for method_name in [
        "render_pulse", "render_ripple", "render_stream", "render_bloom",
        "render_shatter", "render_orbit", "render_gauge", "render_spark",
        "render_wave", "render_glyph", "render_trail", "render_constellation",
    ]:
        method = getattr(p, method_name)
        result = method("test_kind", {})
        assert result is None, f"{method_name} should return None"


# ── New: Sound System ────────────────────────────────────────────────

def test_sound_cues_default_empty():
    assert ThemePlugin().sound_cues() == {}


# ── API Frozen docstring ─────────────────────────────────────────────

def test_module_docstring_contains_frozen():
    """The plugin module docstring documents the API FROZEN contract."""
    import hermes_neurovision.plugin as mod
    assert "FROZEN" in mod.__doc__


# ── Subclass backward compat ─────────────────────────────────────────

def test_subclass_inherits_all_new_defaults():
    """A minimal subclass (like v0.1.x themes) gets all new defaults for free."""

    class OldTheme(ThemePlugin):
        name = "old-theme"
        def node_glyph(self, idx, intensity, total):
            return "X"

    t = OldTheme()
    # Old method overridden
    assert t.node_glyph(0, 0.5, 10) == "X"
    # New methods all have safe defaults
    assert t.palette_shift("pulse", 0.5, (1, 2, 3, 4)) is None
    assert t.special_effects() == []
    assert t.warp_field(5, 5, 80, 24, 0, 1.0) == (5, 5)
    assert t.automaton_config() is None
    assert t.react("agent_start", {}) is None
    assert t.sound_cues() == {}
    assert t.streak_color_key() == "accent"
    assert t.intensity_curve(0.7) == 0.7
