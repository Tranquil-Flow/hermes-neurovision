from hermes_neurovision.app import GalleryApp


def test_gallery_app_headless_runs():
    """Test that the headless gallery runs for a few frames without error."""
    from hermes_neurovision.themes import THEMES
    result = GalleryApp.run_headless(themes=list(THEMES), seconds=0.5, theme_seconds=0.2)
    assert result["frames"] > 0
    assert result["themes_shown"] >= 1
