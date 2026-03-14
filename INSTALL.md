# Hermes Neurovision Installation

## Installation

```bash
cd ~/Projects/hermes-neurovision
pip install -e .
```

## Gateway Hook Installation

```bash
mkdir -p ~/.hermes/hooks/hermes-neurovision
cp hermes_neurovision/sources/hook_handler.py ~/.hermes/hooks/hermes-neurovision/handler.py
cp hermes_neurovision/sources/HOOK.yaml ~/.hermes/hooks/hermes-neurovision/HOOK.yaml
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

# Gallery mode - theme screensaver
hermes-neurovision --gallery

# Specific theme
hermes-neurovision --theme neural-sky

# Test run
hermes-neurovision --seconds 10
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

Hermes Neurovision monitors:
- Custom events (gateway hook → ~/.hermes/neurovision/events.jsonl)
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
