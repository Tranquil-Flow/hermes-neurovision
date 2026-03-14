"""Tests for theme export/import functionality."""

import json
import pytest
from pathlib import Path

from hermes_vision.export import export_theme
from hermes_vision.import_theme import import_theme, Version, IncompatibleVersionError


def test_version_parsing():
    """Test version parsing and comparison."""
    v1_0 = Version.parse("1.0")
    assert v1_0.major == 1
    assert v1_0.minor == 0
    
    v1_1 = Version.parse("1.1")
    assert v1_1 >= v1_0
    assert not (v1_0 >= v1_1)
    
    v2_0 = Version.parse("2.0")
    assert v2_0 >= v1_1
    assert not (v1_1 >= v2_0)


def test_export_builtin_theme(tmp_path):
    """Test exporting a built-in theme."""
    output = tmp_path / "neural-sky.hvtheme"
    
    result = export_theme("neural-sky", output_path=str(output), author="TestUser")
    
    assert result.exists()
    
    # Verify JSON structure
    with open(result) as f:
        data = json.load(f)
    
    assert data["format_version"] == "1.0"
    assert data["metadata"]["name"] == "neural-sky"
    assert data["metadata"]["author"] == "TestUser"
    assert data["config"]["background_density"] == 0.030
    assert data["plugin"]["type"] == "base"


def test_import_preview_mode(tmp_path):
    """Test importing in preview mode."""
    # Export first
    export_file = tmp_path / "test.hvtheme"
    export_theme("neural-sky", output_path=str(export_file))
    
    # Import in preview mode
    result = import_theme(str(export_file), preview_only=True)
    
    assert result["preview"] is True
    assert result["name"] == "neural-sky"
    assert result["has_plugin"] is False


def test_import_install_mode(tmp_path):
    """Test installing an imported theme."""
    # Export first
    export_file = tmp_path / "test.hvtheme"
    export_theme("neural-sky", output_path=str(export_file), author="TestUser")
    
    # Import with trust flag (skip confirmation)
    result = import_theme(str(export_file), preview_only=False, trust=True)
    
    assert result["success"] is True
    assert result["name"] == "neural-sky"
    
    # Check that theme was registered
    from hermes_vision.themes import _runtime_configs
    assert "neural-sky" in _runtime_configs


def test_incompatible_version_error(tmp_path):
    """Test that incompatible versions are rejected."""
    # Create a theme with future major version
    future_theme = {
        "format_version": "2.0",
        "metadata": {"name": "future-theme"},
        "config": {},
        "plugin": {"type": "base"}
    }
    
    theme_file = tmp_path / "future.hvtheme"
    with open(theme_file, 'w') as f:
        json.dump(future_theme, f)
    
    # Should raise IncompatibleVersionError
    with pytest.raises(IncompatibleVersionError):
        import_theme(str(theme_file))


def test_export_nonexistent_theme():
    """Test exporting a theme that doesn't exist."""
    with pytest.raises(ValueError, match="not found"):
        export_theme("nonexistent-theme")


def test_import_nonexistent_file():
    """Test importing a file that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        import_theme("/nonexistent/path.hvtheme")


def test_import_invalid_json(tmp_path):
    """Test importing invalid JSON."""
    bad_file = tmp_path / "bad.hvtheme"
    with open(bad_file, 'w') as f:
        f.write("not json at all")
    
    with pytest.raises(ValueError, match="Invalid JSON"):
        import_theme(str(bad_file))
