"""Theme editor — full customization of ThemeConfig parameters + palette.

Multi-page modal with live preview. Changes apply immediately.
Can save/load custom configs to ~/.hermes/neurovision/custom_themes/.
"""

from __future__ import annotations

import curses
import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from hermes_neurovision.themes import ThemeConfig, build_theme_config

# ── Custom themes persistence ────────────────────────────────────────────────

CUSTOM_DIR = Path.home() / ".hermes" / "neurovision" / "custom_themes"

# Available curses colors for palette editing
_CURSES_COLORS: List[Tuple[str, int]] = [
    ("BLACK",   curses.COLOR_BLACK),
    ("RED",     curses.COLOR_RED),
    ("GREEN",   curses.COLOR_GREEN),
    ("YELLOW",  curses.COLOR_YELLOW),
    ("BLUE",    curses.COLOR_BLUE),
    ("MAGENTA", curses.COLOR_MAGENTA),
    ("CYAN",    curses.COLOR_CYAN),
    ("WHITE",   curses.COLOR_WHITE),
]

# Palette slot names
_PALETTE_SLOTS = ("base", "soft", "bright", "accent")


def _color_name(code: int) -> str:
    for name, c in _CURSES_COLORS:
        if c == code:
            return name
    return f"COLOR_{code}"


def _color_code(name: str) -> int:
    for n, c in _CURSES_COLORS:
        if n == name:
            return c
    return curses.COLOR_WHITE


# ── Config sliders ────────────────────────────────────────────────────────────

# (label, config_attr, min, max, step, format_str)
_CONFIG_SLIDERS: List[Tuple[str, str, float, float, float, str]] = [
    ("Background Density", "background_density", 0.0, 3.0, 0.05, ".2f"),
    ("Star Drift",         "star_drift",         0.0, 2.0, 0.05, ".2f"),
    ("Node Jitter",        "node_jitter",        0.0, 5.0, 0.1,  ".1f"),
    ("Packet Rate",        "packet_rate",         0.0, 1.0, 0.01, ".2f"),
    ("Packet Speed Min",   "_packet_speed_min",   0.01, 0.5, 0.01, ".2f"),
    ("Packet Speed Max",   "_packet_speed_max",   0.02, 1.0, 0.01, ".2f"),
    ("Pulse Rate",         "pulse_rate",          0.0, 1.0, 0.01, ".2f"),
    ("Edge Bias",          "edge_bias",           0.0, 1.0, 0.05, ".2f"),
    ("Cluster Count",      "cluster_count",       1,   8,   1,    ".0f"),
]


# ── ThemeEditor ───────────────────────────────────────────────────────────────

class ThemeEditor:
    """Multi-page theme config editor with live preview.

    Page 1: Config sliders (density, drift, jitter, rates, etc.)
    Page 2: Palette editor (4 color slots)
    Page 3: Metadata (title, accent_char) + Save/Load

    Navigation: Tab/Shift+Tab between pages, ↑↓ rows, ←→ adjust.
    """

    PAGE_CONFIG = 0
    PAGE_PALETTE = 1
    PAGE_META = 2
    PAGE_COUNT = 3
    PAGE_NAMES = ("CONFIG", "PALETTE", "META / SAVE")

    def __init__(self) -> None:
        self.active: bool = False
        self.page: int = 0
        self.selected_index: int = 0
        self._config: Optional[ThemeConfig] = None
        self._original_name: str = ""
        self._custom_title: str = ""
        self._custom_accent: str = ""
        self._editing_text: bool = False
        self._text_buffer: str = ""
        self._text_field: str = ""  # which field is being edited
        self._status_msg: str = ""
        self._save_confirmed: bool = False

    def open(self, config: ThemeConfig) -> None:
        """Open editor for the given theme config (modifies in place)."""
        self.active = True
        self.page = 0
        self.selected_index = 0
        self._config = config
        self._original_name = config.name
        self._custom_title = config.title
        self._custom_accent = config.accent_char
        self._editing_text = False
        self._status_msg = ""
        self._save_confirmed = False

    def close(self) -> None:
        self.active = False
        self._editing_text = False

    def _get_config_value(self, attr: str) -> float:
        """Get value from config, handling virtual packet_speed attrs."""
        if attr == "_packet_speed_min":
            return self._config.packet_speed[0]
        elif attr == "_packet_speed_max":
            return self._config.packet_speed[1]
        return getattr(self._config, attr)

    def _set_config_value(self, attr: str, val: float) -> None:
        """Set value on config, handling virtual packet_speed attrs."""
        if attr == "_packet_speed_min":
            old = self._config.packet_speed
            self._config.packet_speed = (val, max(val + 0.01, old[1]))
        elif attr == "_packet_speed_max":
            old = self._config.packet_speed
            self._config.packet_speed = (min(val - 0.01, old[0]), val)
        else:
            setattr(self._config, attr, val if attr != "cluster_count" else int(val))

    # ── key handling ──────────────────────────────────────────────────────────

    def handle_key(self, ch: int) -> bool:
        """Process a keypress. Returns True if consumed."""
        if not self.active:
            return False

        # Text editing mode
        if self._editing_text:
            return self._handle_text_key(ch)

        # Page switching: Tab / Shift+Tab
        if ch == ord("\t"):
            self.page = (self.page + 1) % self.PAGE_COUNT
            self.selected_index = 0
            return True
        if ch == curses.KEY_BTAB:  # Shift+Tab
            self.page = (self.page - 1) % self.PAGE_COUNT
            self.selected_index = 0
            return True

        # Close
        if ch == ord("e") or ch == 27:
            self.close()
            return True

        # Navigation
        if ch == curses.KEY_DOWN:
            max_idx = self._max_index()
            self.selected_index = (self.selected_index + 1) % (max_idx + 1)
            return True
        if ch == curses.KEY_UP:
            max_idx = self._max_index()
            self.selected_index = (self.selected_index - 1) % (max_idx + 1)
            return True

        # Adjust
        if ch in (curses.KEY_LEFT, curses.KEY_RIGHT):
            self._adjust(ch == curses.KEY_RIGHT)
            return True

        # Enter for text fields / save
        if ch in (ord("\n"), ord("\r"), curses.KEY_ENTER, 10, 13):
            self._activate_item()
            return True

        # Reset
        if ch == ord("r"):
            self._reset_to_original()
            return True

        return True  # consume all keys while editor is open

    def _handle_text_key(self, ch: int) -> bool:
        """Handle keypresses in text editing mode."""
        if ch in (ord("\n"), ord("\r"), curses.KEY_ENTER, 10, 13):
            # Commit text
            if self._text_field == "title":
                self._custom_title = self._text_buffer
                self._config.title = self._custom_title
            elif self._text_field == "accent":
                if self._text_buffer:
                    self._custom_accent = self._text_buffer[0]
                    self._config.accent_char = self._custom_accent
            self._editing_text = False
            return True
        if ch == 27:
            self._editing_text = False
            return True
        if ch in (curses.KEY_BACKSPACE, 127, 8):
            self._text_buffer = self._text_buffer[:-1]
            return True
        if 32 <= ch <= 126:
            self._text_buffer += chr(ch)
            return True
        return True

    def _max_index(self) -> int:
        if self.page == self.PAGE_CONFIG:
            return len(_CONFIG_SLIDERS) - 1
        elif self.page == self.PAGE_PALETTE:
            return len(_PALETTE_SLOTS) - 1
        else:  # META
            return 3  # title, accent, save, load

    def _adjust(self, increase: bool) -> None:
        if self.page == self.PAGE_CONFIG:
            if self.selected_index < len(_CONFIG_SLIDERS):
                label, attr, lo, hi, step, _ = _CONFIG_SLIDERS[self.selected_index]
                val = self._get_config_value(attr)
                val = val + step if increase else val - step
                val = round(max(lo, min(hi, val)), 10)
                self._set_config_value(attr, val)
        elif self.page == self.PAGE_PALETTE:
            # Cycle through curses colors
            slot_idx = self.selected_index
            if slot_idx < len(_PALETTE_SLOTS):
                current = self._config.palette[slot_idx]
                color_idx = next(
                    (i for i, (_, c) in enumerate(_CURSES_COLORS) if c == current),
                    0
                )
                if increase:
                    color_idx = (color_idx + 1) % len(_CURSES_COLORS)
                else:
                    color_idx = (color_idx - 1) % len(_CURSES_COLORS)
                new_color = _CURSES_COLORS[color_idx][1]
                palette = list(self._config.palette)
                palette[slot_idx] = new_color
                self._config.palette = tuple(palette)

    def _activate_item(self) -> None:
        if self.page == self.PAGE_META:
            if self.selected_index == 0:
                # Edit title
                self._editing_text = True
                self._text_field = "title"
                self._text_buffer = self._custom_title
            elif self.selected_index == 1:
                # Edit accent char
                self._editing_text = True
                self._text_field = "accent"
                self._text_buffer = self._custom_accent
            elif self.selected_index == 2:
                # Save
                self._save_custom()
            elif self.selected_index == 3:
                # Load
                self._load_custom()

    def _reset_to_original(self) -> None:
        """Reset config to the original built-in values."""
        try:
            original = build_theme_config(self._original_name)
        except Exception:
            self._status_msg = "Reset failed: theme not found"
            return
        self._config.accent_char = original.accent_char
        self._config.background_density = original.background_density
        self._config.star_drift = original.star_drift
        self._config.node_jitter = original.node_jitter
        self._config.packet_rate = original.packet_rate
        self._config.packet_speed = original.packet_speed
        self._config.pulse_rate = original.pulse_rate
        self._config.edge_bias = original.edge_bias
        self._config.cluster_count = original.cluster_count
        self._config.palette = original.palette
        self._config.title = original.title
        self._custom_title = original.title
        self._custom_accent = original.accent_char
        self._status_msg = "Reset to defaults"

    def _save_custom(self) -> None:
        """Save current config to JSON file."""
        try:
            CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "name": self._config.name,
                "title": self._config.title,
                "accent_char": self._config.accent_char,
                "background_density": self._config.background_density,
                "star_drift": self._config.star_drift,
                "node_jitter": self._config.node_jitter,
                "packet_rate": self._config.packet_rate,
                "packet_speed": list(self._config.packet_speed),
                "pulse_rate": self._config.pulse_rate,
                "edge_bias": self._config.edge_bias,
                "cluster_count": self._config.cluster_count,
                "palette": [_color_name(c) for c in self._config.palette],
            }
            path = CUSTOM_DIR / f"{self._config.name}.json"
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            self._status_msg = f"Saved to {path.name}"
        except Exception as e:
            self._status_msg = f"Save failed: {e}"

    def _load_custom(self) -> None:
        """Load custom config from JSON file if it exists."""
        try:
            path = CUSTOM_DIR / f"{self._config.name}.json"
            if not path.exists():
                self._status_msg = "No saved config found"
                return
            with open(path) as f:
                data = json.load(f)
            self._config.title = data.get("title", self._config.title)
            self._config.accent_char = data.get("accent_char", self._config.accent_char)
            self._config.background_density = data.get("background_density", self._config.background_density)
            self._config.star_drift = data.get("star_drift", self._config.star_drift)
            self._config.node_jitter = data.get("node_jitter", self._config.node_jitter)
            self._config.packet_rate = data.get("packet_rate", self._config.packet_rate)
            self._config.packet_speed = tuple(data.get("packet_speed", list(self._config.packet_speed)))
            self._config.pulse_rate = data.get("pulse_rate", self._config.pulse_rate)
            self._config.edge_bias = data.get("edge_bias", self._config.edge_bias)
            self._config.cluster_count = data.get("cluster_count", self._config.cluster_count)
            palette_names = data.get("palette", [])
            if len(palette_names) == 4:
                self._config.palette = tuple(_color_code(n) for n in palette_names)
            self._custom_title = self._config.title
            self._custom_accent = self._config.accent_char
            self._status_msg = f"Loaded from {path.name}"
        except Exception as e:
            self._status_msg = f"Load failed: {e}"

    # ── drawing ───────────────────────────────────────────────────────────────

    def draw(self, stdscr, color_pairs: dict) -> None:
        """Draw the theme editor modal."""
        if not self.active or self._config is None:
            return

        h, w = stdscr.getmaxyx()
        modal_w = min(50, w - 4)
        modal_h = min(24, h - 2)
        top = max(0, (h - modal_h) // 2)
        left = max(0, (w - modal_w) // 2)

        bright = color_pairs.get("bright", 0)
        accent = color_pairs.get("accent", 0)
        soft = color_pairs.get("soft", 0)
        warning = color_pairs.get("warning", 0)

        def put(y: int, x: int, text: str, attr: int = 0) -> None:
            try:
                stdscr.addstr(top + y, left + x, text[:modal_w - 2], attr)
            except curses.error:
                pass

        # Background fill
        for row in range(modal_h):
            try:
                stdscr.addstr(top + row, left, " " * modal_w, soft)
            except curses.error:
                pass

        # Header with page tabs
        put(0, 1, "─" * (modal_w - 2), soft)
        title = f" THEME EDITOR: {self._config.name} "
        put(0, max(1, (modal_w - len(title)) // 2), title, bright | curses.A_BOLD)

        # Page tabs
        tab_str = ""
        for i, name in enumerate(self.PAGE_NAMES):
            if i == self.page:
                tab_str += f" [{name}] "
            else:
                tab_str += f"  {name}  "
        put(1, max(1, (modal_w - len(tab_str)) // 2), tab_str,
            accent if not self._editing_text else soft)

        # Page content
        row = 3
        if self.page == self.PAGE_CONFIG:
            row = self._draw_config_page(stdscr, put, row, modal_w, modal_h,
                                          bright, accent, soft)
        elif self.page == self.PAGE_PALETTE:
            row = self._draw_palette_page(stdscr, put, row, modal_w, modal_h,
                                           bright, accent, soft, warning)
        elif self.page == self.PAGE_META:
            row = self._draw_meta_page(stdscr, put, row, modal_w, modal_h,
                                        bright, accent, soft, warning)

        # Status message
        if self._status_msg and row < modal_h - 2:
            put(modal_h - 3, 1, f"  {self._status_msg}", warning | curses.A_BOLD)

        # Footer
        put(modal_h - 2, 1, "─" * (modal_w - 2), soft)
        hint = "Tab page  ↑↓ select  ←→ adjust  r reset  e close"
        put(modal_h - 1, max(1, (modal_w - len(hint)) // 2), hint, soft | curses.A_DIM)

    def _draw_config_page(self, stdscr, put, row, modal_w, modal_h,
                           bright, accent, soft) -> int:
        """Draw config sliders page."""
        for i, (label, attr, lo, hi, step, fmt) in enumerate(_CONFIG_SLIDERS):
            if row >= modal_h - 3:
                break
            val = self._get_config_value(attr)
            is_sel = (self.selected_index == i)
            prefix = "▶ " if is_sel else "  "
            val_str = f"{val:{fmt}}"
            label_attr = bright | curses.A_BOLD if is_sel else soft
            put(row, 1, f"{prefix}{label:<22} {val_str:>6}", label_attr)
            row += 1

            # Mini slider bar
            bar_w = modal_w - 8
            filled = int((val - lo) / max(hi - lo, 0.001) * bar_w)
            bar = "═" * filled + "●" + "═" * max(0, bar_w - filled - 1)
            put(row, 4, f"[{bar[:bar_w]}]", accent if is_sel else soft | curses.A_DIM)
            row += 1

        return row

    def _draw_palette_page(self, stdscr, put, row, modal_w, modal_h,
                            bright, accent, soft, warning) -> int:
        """Draw palette editor page."""
        put(row, 1, "── COLOR PALETTE ──", accent)
        row += 1

        for i, slot_name in enumerate(_PALETTE_SLOTS):
            if row >= modal_h - 3:
                break
            is_sel = (self.selected_index == i)
            prefix = "▶ " if is_sel else "  "
            color_code = self._config.palette[i]
            color_name = _color_name(color_code)
            label_attr = bright | curses.A_BOLD if is_sel else soft

            # Show slot name and current color with a preview swatch
            put(row, 1, f"{prefix}{slot_name:<10} ← {color_name:>8} →", label_attr)

            # Preview: draw a colored block
            try:
                preview = " ███ "
                stdscr.addstr(
                    row + (stdscr.getmaxyx()[0] - stdscr.getmaxyx()[0]) + row,  # hack avoid
                    0, "", 0  # dummy
                )
            except curses.error:
                pass
            # Actually show colored preview inline
            preview_x = 30
            if preview_x + 5 < modal_w:
                try:
                    preview_pair = i + 1  # pairs 1-4 map to palette slots
                    stdscr.addstr(
                        row + (stdscr.getmaxyx()[0] - stdscr.getmaxyx()[0]),  # == row
                        left + preview_x,  # absolute position
                        "■■■■",
                        curses.color_pair(preview_pair) | curses.A_BOLD
                    )
                except curses.error:
                    pass

            row += 2

        put(row, 1, "  ←→ to cycle colors for selected slot", soft | curses.A_DIM)
        row += 1
        put(row, 1, "  Changes apply live — palette updates instantly", soft | curses.A_DIM)
        row += 1

        return row

    def _draw_meta_page(self, stdscr, put, row, modal_w, modal_h,
                         bright, accent, soft, warning) -> int:
        """Draw metadata + save/load page."""
        items = [
            ("Title", self._custom_title),
            ("Accent Char", self._custom_accent),
            ("Save Custom Config", "→ Enter"),
            ("Load Custom Config", "→ Enter"),
        ]

        for i, (label, value) in enumerate(items):
            if row >= modal_h - 3:
                break
            is_sel = (self.selected_index == i)
            prefix = "▶ " if is_sel else "  "
            label_attr = bright | curses.A_BOLD if is_sel else soft

            if self._editing_text and is_sel:
                # Show text input
                cursor = "▌"
                put(row, 1, f"{prefix}{label}: {self._text_buffer}{cursor}", warning | curses.A_BOLD)
            else:
                put(row, 1, f"{prefix}{label}: {value}", label_attr)
            row += 1

        row += 1
        put(row, 1, "── CURRENT CONFIG ──", accent)
        row += 1
        info = [
            f"  Name: {self._config.name}",
            f"  Density: {self._config.background_density:.2f}  Drift: {self._config.star_drift:.2f}",
            f"  Jitter: {self._config.node_jitter:.1f}  Clusters: {self._config.cluster_count}",
            f"  Packets: {self._config.packet_rate:.2f}  Pulses: {self._config.pulse_rate:.2f}",
        ]
        for line in info:
            if row >= modal_h - 3:
                break
            put(row, 1, line, soft | curses.A_DIM)
            row += 1

        return row


def load_custom_config(theme_name: str) -> Optional[Dict]:
    """Load custom config overrides for a theme if they exist.

    Returns dict of overrides or None.
    """
    path = CUSTOM_DIR / f"{theme_name}.json"
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def apply_custom_overrides(config: ThemeConfig) -> ThemeConfig:
    """Apply any saved custom overrides to a theme config."""
    data = load_custom_config(config.name)
    if data is None:
        return config

    if "title" in data:
        config.title = data["title"]
    if "accent_char" in data:
        config.accent_char = data["accent_char"]
    if "background_density" in data:
        config.background_density = data["background_density"]
    if "star_drift" in data:
        config.star_drift = data["star_drift"]
    if "node_jitter" in data:
        config.node_jitter = data["node_jitter"]
    if "packet_rate" in data:
        config.packet_rate = data["packet_rate"]
    if "packet_speed" in data:
        config.packet_speed = tuple(data["packet_speed"])
    if "pulse_rate" in data:
        config.pulse_rate = data["pulse_rate"]
    if "edge_bias" in data:
        config.edge_bias = data["edge_bias"]
    if "cluster_count" in data:
        config.cluster_count = data["cluster_count"]
    if "palette" in data and len(data["palette"]) == 4:
        config.palette = tuple(_color_code(n) for n in data["palette"])

    return config
