# Hermes Neurovision Installation

## Quick Install (Recommended)

```bash
git clone https://github.com/Tranquil-Flow/hermes-neurovision.git
cd hermes-neurovision
pip install -e .

# Setup script installs gateway hook + config directory
python3 install_helper.py
```

## Manual Install

```bash
# 1. Install package
git clone https://github.com/Tranquil-Flow/hermes-neurovision.git
cd hermes-neurovision
pip install -e .

# 2. Install gateway hook (enables live event capture)
mkdir -p ~/.hermes/hooks/hermes-neurovision
cp hermes_neurovision/sources/hook_handler.py ~/.hermes/hooks/hermes-neurovision/handler.py
cp hermes_neurovision/sources/HOOK.yaml ~/.hermes/hooks/hermes-neurovision/HOOK.yaml

# 3. (Optional) Enable auto-launch for cron jobs
echo '{"auto_launch": true}' > ~/.hermes/neurovision/config.json
```

## Grove Registration (Optional)

If you have grove installed:

```bash
grove add ~/Projects/hermes-neurovision
```

## Usage

```bash
# Live mode (default) - visualizes agent events in real-time
hermes-neurovision

# With log overlay
hermes-neurovision --logs

# Gallery mode - browse all 42 themes
hermes-neurovision --gallery

# Daemon mode - gallery when idle, live when agent is active
hermes-neurovision --daemon

# Specific theme
hermes-neurovision --theme neural-sky

# Test run (auto-exits after N seconds)
hermes-neurovision --seconds 10

# Export a theme
hermes-neurovision --export neural-sky --author "YourName"

# Import a theme
hermes-neurovision --import mytheme.hvtheme

# List imported themes
hermes-neurovision --list-themes
```

## Modes

- **--live** (default): Real-time event visualization
- **--gallery**: Browse all 85 themes with auto-rotation
- **--daemon**: Gallery when idle, switches to live on events
- **--logs**: Enable color-coded scrolling log overlay
- **--no-aegis**: Skip Aegis security audit source

## Keyboard Controls

**Gallery Mode:**
- `n` / Right Arrow - Next theme
- `p` / Left Arrow - Previous theme
- `Enter` - Lock current theme (stops rotation, keeps animating)
- `s` - Select this theme for live mode
- `Space` - Pause/Resume
- `Shift+→` / `Shift+←` - Jump forward/back in theme list
- `t` - Open tuner overlay (real-time parameter sliders)
- `d` - Toggle debug panel (live event diagnostics)
- `L` - Toggle legacy themes in gallery
- `X` - Disable current theme (skip in future rotations)
- `q` - Quit

**Live / Daemon Mode:**
- `l` - Toggle log overlay
- `t` - Open tuner overlay
- `d` - Toggle debug panel
- `q` - Quit

## Event Sources

Hermes Neurovision monitors 34 event types across 7 sources:
- Custom events (gateway hook → `~/.hermes/neurovision/events.jsonl`)
- Agent state (SQLite → `~/.hermes/state.db`)
- Memory operations (filesystem → `~/.hermes/memories/`)
- Cron jobs (status → `~/.hermes/cron/`)
- Trajectory logs (`~/.hermes/logs/`)
- Security events (optional → `~/.hermes-aegis/audit.jsonl`)

## Requirements

- Python 3.10+
- No external dependencies (pure stdlib)
- Terminal with 256 color support (recommended)
- Minimum terminal size: 80x24

## Themes

85 animated themes across 8 categories. See README.md for the full list, or browse live with `hermes-neurovision --gallery`.

## Troubleshooting

See the Troubleshooting section in [README.md](README.md) or [AUTOLAUNCH.md](AUTOLAUNCH.md) for auto-launch issues.
