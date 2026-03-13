"""Hermes Vision CLI entry point."""

from __future__ import annotations

import argparse
import curses
import sys

from hermes_vision.themes import THEMES, DEFAULT_THEME_SECONDS


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="hermes-vision",
        description="Terminal neurovisualizer for Hermes Agent",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true", help="Real-time event visualization (default)")
    mode.add_argument("--gallery", action="store_true", help="Theme rotation screensaver")
    mode.add_argument("--daemon", action="store_true", help="Gallery when idle, live when active")

    parser.add_argument("--theme", choices=THEMES, default="neural-sky", help="Theme to use")
    parser.add_argument("--theme-seconds", type=float, default=DEFAULT_THEME_SECONDS, help="Seconds per theme in gallery/daemon")
    parser.add_argument("--logs", action="store_true", help="Enable log overlay")
    parser.add_argument("--auto-exit", action="store_true", help="Exit 30s after last event")
    parser.add_argument("--seconds", type=float, default=None, help="Exit after N seconds (testing)")
    parser.add_argument("--no-aegis", action="store_true", help="Skip Aegis source")

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.gallery or (not args.live and not args.daemon):
        # Gallery mode — this is a temporary default until live mode is built in Task 16.
        # Task 16 changes the default to --live.
        _run_gallery(args)
    elif args.live:
        # Live mode — will be implemented in Chunk 3
        print("Live mode not yet implemented. Use --gallery for now.", file=sys.stderr)
        sys.exit(1)
    elif args.daemon:
        print("Daemon mode not yet implemented.", file=sys.stderr)
        sys.exit(1)


def _run_gallery(args):
    from hermes_vision.app import GalleryApp

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        # Headless mode
        result = GalleryApp.run_headless(
            themes=[args.theme] if args.theme != "neural-sky" or not args.gallery else list(THEMES),
            seconds=args.seconds or 2.0,
            theme_seconds=args.theme_seconds,
        )
        print(f"headless: {result}")
        return

    themes = list(THEMES) if args.gallery else [args.theme]
    curses.wrapper(lambda stdscr: GalleryApp(stdscr, themes, args.theme_seconds, args.seconds).run())
