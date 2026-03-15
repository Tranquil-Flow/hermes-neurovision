"""Tests for CLI legacy theme flags (Task 48)."""
import pytest
from hermes_neurovision.themes import THEMES, LEGACY_THEMES, build_theme_config
from hermes_neurovision.cli import parse_args, main


def test_legacy_themes_tuple_not_empty():
    assert len(LEGACY_THEMES) > 0


def test_legacy_themes_all_start_with_legacy_prefix():
    for name in LEGACY_THEMES:
        assert name.startswith("legacy-"), f"{name!r} should start with 'legacy-'"


def test_legacy_themes_not_in_main_themes():
    for name in LEGACY_THEMES:
        assert name not in THEMES, f"{name!r} should not be in THEMES"


def test_legacy_themes_all_have_configs():
    for name in LEGACY_THEMES:
        config = build_theme_config(name)
        assert config.name == name


def test_list_legacy_flag(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--list-legacy"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    for name in LEGACY_THEMES:
        assert name in captured.out


def test_list_legacy_output_format(capsys):
    with pytest.raises(SystemExit):
        main(["--list-legacy"])
    captured = capsys.readouterr()
    lines = [ln for ln in captured.out.strip().splitlines() if ln]
    assert len(lines) == len(LEGACY_THEMES)
    for line in lines:
        assert ": " in line


def test_include_legacy_flag_parse():
    args = parse_args(["--gallery", "--include-legacy"])
    assert args.include_legacy is True


def test_include_legacy_flag_default():
    args = parse_args(["--gallery"])
    assert args.include_legacy is False


def test_legacy_configs_build_without_error():
    """All legacy themes can be built into ThemeConfig objects."""
    for name in LEGACY_THEMES:
        config = build_theme_config(name)
        assert config is not None
        assert "(Legacy)" in config.title
