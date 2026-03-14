from hermes_neurovision.themes import THEMES, ThemeConfig, build_theme_config


def test_all_theme_names_are_defined():
    assert len(THEMES) == 45
    assert "neural-sky" in THEMES
    assert "black-hole" in THEMES


def test_build_theme_config_returns_config():
    config = build_theme_config("neural-sky")
    assert isinstance(config, ThemeConfig)
    assert config.name == "neural-sky"


def test_all_themes_can_be_built():
    for name in THEMES:
        config = build_theme_config(name)
        assert config.name == name
        assert config.background_density > 0
