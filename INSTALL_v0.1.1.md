# Hermes Neurovision v0.1.1 - Installation Guide

## Quick Install

```bash
cd ~/Projects/hermes-vision
pip install -e .
```

**Note**: Directory is still "hermes-vision" but package installs as "hermes-neurovision"

## Verify Installation

```bash
# Check command is available
which hermes-neurovision

# Should show: /usr/local/bin/hermes-neurovision (or similar)

# Test it
hermes-neurovision --help
```

## Quick Test

```bash
# Run gallery for 5 seconds
hermes-neurovision --gallery --seconds 5

# Or browse themes interactively
hermes-neurovision --gallery
# Press 'n' to cycle, 'q' to quit
```

## Full Setup (Optional)

### Install Gateway Hook

For live event monitoring:

```bash
mkdir -p ~/.hermes/hooks/hermes-neurovision
cp hermes_neurovision/sources/hook_handler.py ~/.hermes/hooks/hermes-neurovision/handler.py
cp hermes_neurovision/sources/HOOK.yaml ~/.hermes/hooks/hermes-neurovision/HOOK.yaml
```

Or use the helper:
```bash
python3 install_helper.py
```

### Enable Auto-Launch (Optional)

```bash
mkdir -p ~/.hermes/neurovision
echo '{"auto_launch": true}' > ~/.hermes/neurovision/config.json
```

## Common Installation Issues

### "command not found: pip"

Use pip3 instead:
```bash
pip3 install -e .
```

### "Permission denied"

Don't use sudo. If needed, install in user mode:
```bash
pip install -e . --user
```

### "Module not found" errors

Make sure you're in the project directory:
```bash
cd ~/Projects/hermes-vision
pwd  # Should show path ending in hermes-vision
ls   # Should show hermes_neurovision/ directory
pip install -e .
```

### Command still not found after install

Check Python's bin directory is in PATH:
```bash
python3 -m site --user-base
# Add /bin to the path shown above
```

Or run directly:
```bash
python3 -m hermes_neurovision --gallery
```

## Uninstall Old Version (If Applicable)

If you had the development version installed:
```bash
pip uninstall hermes-vision -y
pip install -e .
```

## Requirements

- Python 3.10+
- Terminal with 256 color support
- No external dependencies (pure stdlib!)

## Platform Notes

### macOS
Works with Terminal.app, iTerm2, or tmux

### Linux
Works with gnome-terminal, konsole, xterm, or tmux

### Windows
Should work with Windows Terminal or WSL

## Verification

After installation, all these should work:

```bash
hermes-neurovision --help
hermes-neurovision --gallery --seconds 2
hermes-neurovision --export neural-sky --output /tmp/test.hvtheme
hermes-neurovision --list-themes
```

If any fail, try:
```bash
python3 -m hermes_neurovision --help
```

## Getting Help

If installation fails:
1. Check Python version: `python3 --version` (need 3.10+)
2. Check pip location: `which pip` or `which pip3`
3. Try: `python3 -m pip install -e .`
4. Run directly: `python3 -m hermes_neurovision --gallery`

See README.md for more details.
