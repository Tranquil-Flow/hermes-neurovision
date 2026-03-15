import pytest
from unittest.mock import patch, MagicMock
from hermes_neurovision.cli import main
from hermes_neurovision.themes import THEMES, LEGACY_THEMES, build_theme_config


def test_list_legacy_flag(capsys):
    # Mock sys.argv to simulate --list-legacy
    with patch('sys.argv', ['cli.py', '--list-legacy']):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0

    # Capture stdout
    captured = capsys.readouterr()
    for theme_name in LEGACY_THEMES:
        title = build_theme_config()[theme_name].title
        assert f"{theme_name}: {title}" in captured.out

def test_include_legacy_flag(monkeypatch):
    # Mock sys.argv to simulate --include-legacy
    monkeypatch.setattr('sys.argv', ['cli.py', '--include-legacy'])

    # Patch build_theme_config() to get all themes
    with patch('hermes_neurovision.themes.build_theme_config') as mock_config:
        mock_config.return_value = {
            'regular-theme': Mock(title='Regular Theme'),
            'legacy-test': Mock(title='Legacy Test Theme'),
        }
        
        # Call main (this will rebuild themes list)
        main()

    # Verify legacy themes were included
    themes_list = ['regular-theme', 'legacy-test']
    assert sorted(themes_list) == sorted(THEMES + LEGACY_THEMES)