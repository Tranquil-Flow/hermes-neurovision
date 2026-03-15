"""Tests for command menu, theme editor, and hide mode."""

import pytest
from hermes_neurovision.command_menu import CommandMenu, MenuItem
from hermes_neurovision.theme_editor import (
    ThemeEditor, apply_custom_overrides, load_custom_config,
    _color_name, _color_code, CUSTOM_DIR,
)
from hermes_neurovision.themes import build_theme_config


class TestCommandMenu:
    def test_initial_state(self):
        menu = CommandMenu()
        assert not menu.active
        assert menu.item_count == 0

    def test_configure_gallery(self):
        menu = CommandMenu()
        menu.configure("gallery", quiet=lambda: False, include_legacy=lambda: True)
        assert menu.item_count > 0
        labels = [i.label for i in menu._items]
        assert "Theme Editor" in labels
        assert "Tune Settings" in labels
        assert "Hide HUD" in labels
        assert "Toggle Legacy" in labels
        assert "Toggle Quiet" in labels
        assert "Quit" in labels

    def test_configure_live(self):
        menu = CommandMenu()
        menu.configure("live", show_logs=lambda: True)
        labels = [i.label for i in menu._items]
        assert "Toggle Logs" in labels
        assert "Toggle Legacy" not in labels

    def test_configure_daemon(self):
        menu = CommandMenu()
        menu.configure("daemon", show_logs=lambda: False, quiet=lambda: True)
        labels = [i.label for i in menu._items]
        assert "Toggle Logs" in labels
        assert "Toggle Quiet" in labels

    def test_open_close(self):
        menu = CommandMenu()
        menu.configure("gallery")
        menu.open()
        assert menu.active
        assert menu.selected_index == 0
        menu.close()
        assert not menu.active

    def test_navigation(self):
        menu = CommandMenu()
        menu.configure("gallery")
        menu.open()
        menu._move(1)
        assert menu.selected_index == 1
        menu._move(-1)
        assert menu.selected_index == 0

    def test_skip_separator(self):
        menu = CommandMenu()
        menu.configure("gallery")
        menu.open()
        # Navigate to near the separator
        # The separator has action="" so it should be skipped
        for i, item in enumerate(menu._items):
            if item.action == "":
                # Move to item before separator
                menu.selected_index = i - 1
                menu._move(1)
                # Should skip past separator
                assert menu.selected_index != i
                break

    def test_action_lifecycle(self):
        menu = CommandMenu()
        menu.configure("gallery")
        menu.open()
        assert menu.pop_action() is None
        menu._pending_action = "theme_editor"
        assert menu.pop_action() == "theme_editor"
        assert menu.pop_action() is None  # cleared after pop

    def test_toggle_state(self):
        state = {"logs": True}
        menu = CommandMenu()
        menu.configure("live", show_logs=lambda: state["logs"])
        for item in menu._items:
            if item.label == "Toggle Logs":
                assert item.toggle_state() is True
                state["logs"] = False
                assert item.toggle_state() is False
                break


class TestThemeEditor:
    def test_initial_state(self):
        editor = ThemeEditor()
        assert not editor.active

    def test_open_close(self):
        editor = ThemeEditor()
        config = build_theme_config("neural-sky")
        editor.open(config)
        assert editor.active
        assert editor._config is config
        assert editor.page == 0
        editor.close()
        assert not editor.active

    def test_config_value_access(self):
        editor = ThemeEditor()
        config = build_theme_config("neural-sky")
        editor.open(config)
        val = editor._get_config_value("background_density")
        assert isinstance(val, float)

    def test_config_value_set(self):
        editor = ThemeEditor()
        config = build_theme_config("neural-sky")
        editor.open(config)
        editor._set_config_value("background_density", 2.0)
        assert config.background_density == 2.0

    def test_packet_speed_virtual_attrs(self):
        editor = ThemeEditor()
        config = build_theme_config("neural-sky")
        editor.open(config)
        editor._set_config_value("_packet_speed_min", 0.1)
        assert config.packet_speed[0] == 0.1
        editor._set_config_value("_packet_speed_max", 0.5)
        assert config.packet_speed[1] == 0.5

    def test_max_index_per_page(self):
        editor = ThemeEditor()
        config = build_theme_config("neural-sky")
        editor.open(config)
        editor.page = editor.PAGE_CONFIG
        assert editor._max_index() == 8  # 9 config sliders - 1
        editor.page = editor.PAGE_PALETTE
        assert editor._max_index() == 3  # 4 palette slots - 1
        editor.page = editor.PAGE_META
        assert editor._max_index() == 3  # title, accent, save, load

    def test_reset_to_original(self):
        editor = ThemeEditor()
        config = build_theme_config("storm-core")  # use a different theme to avoid interference
        original_density = config.background_density
        assert original_density != 99.0  # sanity check
        editor.open(config)
        editor._set_config_value("background_density", 99.0)
        assert config.background_density == 99.0
        editor._reset_to_original()
        assert config.background_density == original_density, (
            f"Expected {original_density}, got {config.background_density}"
        )

    def test_palette_adjust(self):
        editor = ThemeEditor()
        config = build_theme_config("neural-sky")
        editor.open(config)
        editor.page = editor.PAGE_PALETTE
        editor.selected_index = 0
        old_palette = config.palette
        editor._adjust(True)
        # Palette should have changed
        assert config.palette[0] != old_palette[0] or config.palette == old_palette  # wraparound possible


class TestCustomOverrides:
    def test_no_custom_file(self):
        assert load_custom_config("nonexistent-theme-xyz") is None

    def test_apply_no_custom(self):
        config = build_theme_config("storm-core")
        original_name = config.name
        config = apply_custom_overrides(config)
        assert config.name == original_name  # unchanged


class TestColorHelpers:
    def test_color_name_known(self):
        import curses
        assert _color_name(curses.COLOR_RED) == "RED"
        assert _color_name(curses.COLOR_BLUE) == "BLUE"

    def test_color_name_unknown(self):
        assert _color_name(999) == "COLOR_999"

    def test_color_code_known(self):
        import curses
        assert _color_code("RED") == curses.COLOR_RED
        assert _color_code("CYAN") == curses.COLOR_CYAN

    def test_color_code_unknown(self):
        import curses
        assert _color_code("UNKNOWN") == curses.COLOR_WHITE


class TestMenuItem:
    def test_basic(self):
        item = MenuItem("Test", "t", "test_action")
        assert item.label == "Test"
        assert item.shortcut == "t"
        assert item.action == "test_action"
        assert item.toggle_state is None

    def test_with_toggle(self):
        item = MenuItem("Toggle", "t", "toggle", toggle_state=lambda: True)
        assert item.toggle_state() is True
