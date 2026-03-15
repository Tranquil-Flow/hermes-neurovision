from hermes_neurovision.themes import THEMES, ThemeConfig, build_theme_config


def test_all_theme_names_are_defined():
    assert len(THEMES) == 60
    assert "neural-sky" in THEMES
    assert "black-hole" in THEMES
    assert "synaptic-plasma" in THEMES
    assert "pulse-matrix" in THEMES
    assert "fractal-engine" in THEMES
    assert "n-body" in THEMES
    assert "standing-waves" in THEMES
    assert "clifford-attractor" in THEMES
    assert "barnsley-fern" in THEMES
    assert "flow-field" in THEMES


def test_build_theme_config_returns_config():
    config = build_theme_config("neural-sky")
    assert isinstance(config, ThemeConfig)
    assert config.name == "neural-sky"


def test_all_themes_can_be_built():
    # Full-screen ASCII field themes intentionally have background_density=0
    full_screen_themes = {
        "synaptic-plasma", "oracle", "cellular-cortex", "reaction-field",
        "stellar-weave", "life-colony", "aurora-bands", "waveform-scope",
        "lissajous-mind", "pulse-matrix",
        # Redesigned cosmic themes (v2) — also full-screen field renderers
        "starfall", "quasar", "supernova", "sol", "terra", "binary-star",
        # Extreme field themes
        "fractal-engine", "n-body", "standing-waves",
        # Redesigned originals + nature (v2)
        "black-hole", "neural-sky", "storm-core", "moonwire", "rootsong",
        "stormglass", "spiral-galaxy",
        "deep-abyss", "storm-sea", "dark-forest", "mountain-stars", "beach-lighthouse",
        # Experimental
        "clifford-attractor", "barnsley-fern", "flow-field",
        # Hybrid themes — draw_background() provides the field; background_density unused
        "plasma-grid", "deep-signal",
    }
    for name in THEMES:
        config = build_theme_config(name)
        assert config.name == name
        if name not in full_screen_themes:
            assert config.background_density > 0
