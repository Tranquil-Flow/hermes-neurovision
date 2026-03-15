"""Hermes Vision CLI entry point."""

from __future__ import annotations

import argparse
import curses
import json
import os
import sys

from hermes_neurovision.themes import THEMES, LEGACY_THEMES, DEFAULT_THEME_SECONDS

_CONFIG_PATH = os.path.expanduser("~/.hermes/neurovision/config.json")


def _load_default_theme() -> str:
    """Return saved default theme, or 'neural-sky' if none saved."""
    try:
        with open(_CONFIG_PATH) as f:
            return json.load(f).get("default_theme", "neural-sky")
    except (OSError, json.JSONDecodeError, KeyError):
        return "neural-sky"


def _save_default_theme(theme: str) -> None:
    """Persist the default theme to config."""
    try:
        os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
        data = {}
        try:
            with open(_CONFIG_PATH) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
        data["default_theme"] = theme
        with open(_CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="hermes-neurovision",
        description="Terminal neurovisualizer for Hermes Agent",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true", help="Real-time event visualization (default)")
    mode.add_argument("--gallery", action="store_true", help="Theme rotation screensaver")
    mode.add_argument("--daemon", action="store_true", help="Gallery when idle, live when active")

    parser.add_argument("--theme", default=None, help="Theme to use (default: last selected, or neural-sky)")
    parser.add_argument("--theme-seconds", type=float, default=DEFAULT_THEME_SECONDS, help="Seconds per theme in gallery/daemon")
    parser.add_argument("--logs", action="store_true", help="Enable log overlay")
    parser.add_argument("--auto-exit", action="store_true", help="Exit 30s after last event")
    parser.add_argument("--seconds", type=float, default=None, help="Exit after N seconds (testing)")
    parser.add_argument("--no-aegis", action="store_true", help="Skip Aegis source")
    parser.add_argument("--animated", action="store_true", help="Enable passive background animations (default)")
    parser.add_argument("--quiet", action="store_true", help="Suppress ambient animation; only real agent events drive the visualizer")
    
    # Export/Import
    parser.add_argument("--export", metavar="THEME", help="Export theme to .hvtheme file")
    parser.add_argument("--import", metavar="FILE", dest="import_file", help="Import theme from .hvtheme file")
    parser.add_argument("--output", help="Output path for export")
    parser.add_argument("--author", help="Author name for export")
    parser.add_argument("--description", help="Description for export")
    parser.add_argument("--preview", action="store_true", help="Preview import without installing")
    parser.add_argument("--trust", action="store_true", help="Trust custom plugins without confirmation")
    parser.add_argument("--list-themes", action="store_true", help="List all imported themes")
    parser.add_argument("--custom-only", action="store_true", help="Show only custom/imported themes")
    parser.add_argument("--include-legacy", action="store_true", help="Include legacy themes in gallery rotation")
    parser.add_argument("--list-legacy", action="store_true", help="List all legacy theme names and exit")
    parser.add_argument("--disable", metavar="THEME", help="Disable a theme (hide from gallery) and exit")
    parser.add_argument("--enable", metavar="THEME", help="Re-enable a disabled theme and exit")

    # ── Background mode (neurovision-bg) ──────────────────────────────────────
    # This block is fully additive — it never affects live/gallery/daemon paths.
    # Activated only when --bg is present. All other flags behave identically.
    bg_group = parser.add_argument_group(
        "background mode",
        "Run neurovision behind your terminal (requires a transparent terminal emulator). "
        "No curses takeover — neurovision lives in its own detached process."
    )
    bg_group.add_argument(
        "--bg",
        metavar="ACTION",
        nargs="?",
        const="start",
        choices=["start", "stop", "status", "config"],
        help="Background mode: start | stop | status | config (default: start)",
    )
    bg_group.add_argument("--bg-theme", default=None, help="Theme for background mode")
    bg_group.add_argument("--bg-gallery", action="store_true", help="Use gallery rotation in background mode")
    bg_group.add_argument(
        "--bg-opacity",
        type=float,
        default=None,
        metavar="0.0-1.0",
        help="Suggested terminal opacity (saved to config, printed as a setup hint)",
    )
    bg_group.add_argument(
        "--bg-theme-seconds",
        type=float,
        default=None,
        metavar="N",
        help="Seconds per theme in background gallery rotation",
    )
    bg_group.add_argument(
        "--bg-window-mode",
        choices=["behind", "side-by-side", "fullscreen"],
        default=None,
        help="Window placement mode (default: behind)",
    )
    bg_group.add_argument("--bg-quiet", action="store_true", help="Suppress sim activity in background (saves CPU)")

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # ── Background mode early-exit ────────────────────────────────────────────
    # Must come first — if --bg is present we dispatch and return immediately.
    # Nothing below this block is touched when bg mode is active.
    if getattr(args, "bg", None) is not None:
        from hermes_neurovision.bg_mode import handle_bg_command
        handle_bg_command(args)
        return
    # ─────────────────────────────────────────────────────────────────────────

    if args.theme is None:
        args.theme = _load_default_theme()

    # Handle export
    if args.export:
        from hermes_neurovision.export import export_theme
        try:
            output = export_theme(
                args.export,
                output_path=args.output,
                author=args.author,
                description=args.description
            )
            print(f"✓ Exported theme to: {output}")
            return
        except ValueError as e:
            print(f"✗ Export failed: {e}")
            sys.exit(1)
    
    # Handle import
    if args.import_file:
        from hermes_neurovision.import_theme import import_theme, IncompatibleVersionError
        try:
            result = import_theme(args.import_file, preview_only=args.preview, trust=args.trust)
            
            if result.get("preview"):
                # Preview mode
                print(f"\nTheme: {result['title']}")
                print(f"Name: {result['name']}")
                print(f"Author: {result['author']}")
                if result.get('description'):
                    print(f"Description: {result['description']}")
                print(f"Created: {result.get('created', 'unknown')}")
                print(f"Custom Plugin: {'Yes' if result['has_plugin'] else 'No'}")
                print("\nUse --import without --preview to install\n")
            elif result.get("success"):
                # Install mode
                print(f"\n✓ Imported theme: {result['name']}")
                print(f"  Title: {result['title']}")
                print(f"  Saved to: {result['path']}")
                print(f"\nTest it with: hermes-neurovision --theme {result['name']}\n")
            elif result.get("cancelled"):
                # User cancelled
                pass
            else:
                print("✗ Import failed")
                sys.exit(1)
            return
        except IncompatibleVersionError as e:
            print(f"\n✗ {e}\n")
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"✗ {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"✗ Import failed: {e}")
            sys.exit(1)
    
    # Handle disable / enable
    if args.disable:
        from hermes_neurovision.disabled import add_disabled
        add_disabled(args.disable)
        print(f"Theme '{args.disable}' disabled.")
        return

    if args.enable:
        from hermes_neurovision.disabled import remove_disabled
        remove_disabled(args.enable)
        print(f"Theme '{args.enable}' enabled.")
        return

    # Handle list-legacy
    if args.list_legacy:
        from hermes_neurovision.themes import build_theme_config
        for name in LEGACY_THEMES:
            config = build_theme_config(name)
            print(f"{name}: {config.title}")
        sys.exit(0)

    # Handle list
    if args.list_themes:
        from hermes_neurovision.import_theme import list_themes
        list_themes(custom_only=args.custom_only)
        return

    if args.gallery:
        _run_gallery(args, include_legacy=args.include_legacy)
    elif args.daemon:
        _run_daemon(args)
    else:
        _run_live(args)  # --live is the default


def _run_gallery(args, include_legacy=False):
    from hermes_neurovision.app import GalleryApp
    from hermes_neurovision.disabled import load_disabled

    disabled = load_disabled()
    all_themes = list(THEMES) + (list(LEGACY_THEMES) if include_legacy else [])
    base_themes = [t for t in all_themes if t not in disabled]
    if not base_themes:
        print("Warning: all themes are disabled — showing full theme list as fallback.")
        base_themes = list(THEMES)

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        # Headless mode
        result = GalleryApp.run_headless(
            themes=[args.theme] if args.theme != "neural-sky" or not args.gallery else base_themes,
            seconds=args.seconds or 2.0,
            theme_seconds=args.theme_seconds,
        )
        print(f"headless: {result}")
        return

    themes = base_themes if args.gallery else [args.theme]

    # Run gallery and check if a theme was selected
    gallery_app = None
    def run_gallery_wrapper(stdscr):
        nonlocal gallery_app
        gallery_app = GalleryApp(stdscr, themes, args.theme_seconds, args.seconds,
                                 include_legacy=include_legacy)
        gallery_app.run()
    
    try:
        curses.wrapper(run_gallery_wrapper)
    except (SystemExit, KeyboardInterrupt):
        pass
    
    # If user selected a theme with 's', save it and launch live mode
    if gallery_app and gallery_app.selected_theme:
        _save_default_theme(gallery_app.selected_theme)
        args.theme = gallery_app.selected_theme
        _run_live(args)


def _run_live(args):
    from hermes_neurovision.app import LiveApp
    from hermes_neurovision.events import EventPoller
    from hermes_neurovision.bridge import Bridge
    from hermes_neurovision.log_overlay import LogOverlay
    from hermes_neurovision.sources.custom import CustomSource
    from hermes_neurovision.sources.state_db import StateDbSource
    from hermes_neurovision.sources.memories import MemoriesSource
    from hermes_neurovision.sources.cron import CronSource
    from hermes_neurovision.sources.aegis import AegisSource
    from hermes_neurovision.sources.trajectories import TrajectoriesSource
    from hermes_neurovision.sources.docker_tasks import DockerTaskSource

    sources = [
        CustomSource().poll,
        StateDbSource().poll,
        MemoriesSource().poll,
        CronSource().poll,
        TrajectoriesSource().poll,
        DockerTaskSource().poll,
    ]
    if not args.no_aegis:
        sources.append(AegisSource().poll)

    poller = EventPoller(sources=sources)
    bridge = Bridge()
    log_overlay = LogOverlay()

    def run_curses(stdscr):
        app = LiveApp(stdscr, args.theme, poller, bridge, log_overlay,
                      end_after=args.seconds, show_logs=args.logs, quiet=args.quiet)
        app.run()

    try:
        curses.wrapper(run_curses)
    except KeyboardInterrupt:
        pass


def _run_daemon(args):
    from hermes_neurovision.app import DaemonApp
    from hermes_neurovision.events import EventPoller
    from hermes_neurovision.bridge import Bridge
    from hermes_neurovision.log_overlay import LogOverlay
    from hermes_neurovision.sources.custom import CustomSource
    from hermes_neurovision.sources.state_db import StateDbSource
    from hermes_neurovision.sources.memories import MemoriesSource
    from hermes_neurovision.sources.cron import CronSource
    from hermes_neurovision.sources.aegis import AegisSource
    from hermes_neurovision.sources.trajectories import TrajectoriesSource
    from hermes_neurovision.sources.docker_tasks import DockerTaskSource

    sources = [
        CustomSource().poll,
        StateDbSource().poll,
        MemoriesSource().poll,
        CronSource().poll,
        TrajectoriesSource().poll,
        DockerTaskSource().poll,
    ]
    if not args.no_aegis:
        sources.append(AegisSource().poll)

    poller = EventPoller(sources=sources)
    bridge = Bridge()
    log_overlay = LogOverlay()

    # Use all themes for gallery rotation
    themes = list(THEMES)

    def run_curses(stdscr):
        app = DaemonApp(stdscr, themes, args.theme_seconds, poller, bridge, log_overlay, show_logs=args.logs, quiet=args.quiet)
        app.run()

    try:
        curses.wrapper(run_curses)
    except KeyboardInterrupt:
        pass
