# Hermes Vision Installation

## Installation

```bash
cd ~/Projects/hermes-vision
pip install -e .
```

## Gateway Hook Installation

```bash
mkdir -p ~/.hermes/hooks/hermes-vision
cp hermes_vision/sources/hook_handler.py ~/.hermes/hooks/hermes-vision/handler.py
cp hermes_vision/sources/HOOK.yaml ~/.hermes/hooks/hermes-vision/HOOK.yaml
```

## Grove Registration (Optional)

If you have grove installed:

```bash
grove add ~/Projects/hermes-vision
```

## Usage

```bash
# Live mode (default) - visualizes agent events in real-time
hermes-vision

# With log overlay
hermes-vision --logs

# Gallery mode - theme screensaver
hermes-vision --gallery

# Specific theme
hermes-vision --theme neural-sky

# Test run
hermes-vision --seconds 10
```

## Modes

- **--live**: Real-time event visualization (default)
- **--gallery**: Theme rotation screensaver
- **--daemon**: Gallery when idle, live when events arrive
- **--logs**: Enable scrolling log overlay
- **--no-aegis**: Skip Aegis audit source

## Keyboard Controls

- `q` - Quit
- `l` - Toggle log overlay
- `n` / Right Arrow - Next theme
- `p` / Left Arrow - Previous theme
- `Space` - Pause/Resume

## Event Sources

Hermes Vision monitors:
- Custom events (gateway hook → ~/.hermes/vision/events.jsonl)
- Agent state (SQLite → ~/.hermes/state.db)
- Memory operations (filesystem → ~/.hermes/memories/)
- Cron jobs (status → ~/.hermes/cron/)
- Security events (optional → ~/.hermes-aegis/audit.jsonl)

## Themes

1. neural-sky
2. electric-mycelium
3. cathedral-circuit
4. storm-core
5. hybrid
6. moonwire
7. rootsong
8. stormglass
9. spiral-galaxy
10. black-hole
