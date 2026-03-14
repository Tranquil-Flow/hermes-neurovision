# 🌌 Hermes Neurovisualizer

**Terminal neurovisualizer for Hermes Agent**

A beautiful living neural network that reacts to your AI agent's activity in real-time. Watch as tool calls become traveling packets, memory updates spawn new nodes, and token usage creates pulsating waves across cosmic visualizations.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Tests](https://img.shields.io/badge/tests-63%20passing-brightgreen)
![Dependencies](https://img.shields.io/badge/dependencies-stdlib%20only-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

🎨 **42 Animated Themes** - From cosmic phenomena to industrial machinery  
🔴 **Live Event Visualization** - See your agent's activity in real-time  
📊 **7 Data Sources** - Monitors sessions, tools, memory, cron, security  
📝 **Log Overlay** - Color-coded event stream with fading text  
🌓 **Daemon Mode** - Gallery when idle, live when active  
🚀 **Auto-Launch** - Opens automatically with cron jobs  
⚡ **Pure Stdlib** - Zero external dependencies  
🧪 **63 Tests** - 100% passing, production-ready  
🎭 **Plugin System** - Extensible theme architecture  

---

## 🚀 Quick Start

```bash
# Install
cd ~/Projects/hermes-vision
pip install -e .

# Run setup script (does everything!)
python3 install_helper.py

# Start visualizing
hermes-vision
```

That's it! 🎉

---

## 📦 Manual Installation

If you prefer to set up manually:

```bash
# 1. Install package
cd ~/Projects/hermes-vision
pip install -e .

# 2. Install gateway hook
mkdir -p ~/.hermes/hooks/hermes-vision
cp hermes_vision/sources/hook_handler.py ~/.hermes/hooks/hermes-vision/handler.py
cp hermes_vision/sources/HOOK.yaml ~/.hermes/hooks/hermes-vision/HOOK.yaml

# 3. (Optional) Enable auto-launch for cron jobs
echo '{"auto_launch": true}' > ~/.hermes/vision/config.json

# 4. Test it
hermes-vision --gallery
```

---

## 🎮 Usage

### Modes

```bash
# Live mode (default) - reacts to agent events
hermes-vision

# With log overlay to see event details
hermes-vision --logs

# Gallery mode - browse all 10 themes
hermes-vision --gallery

# Daemon mode - best of both worlds
hermes-vision --daemon

# Specific theme
hermes-vision --theme storm-core

# Test run (auto-exit after 10 seconds)
hermes-vision --seconds 10
```

### Keyboard Controls

**Gallery Mode:**
- `n` / `→` - Next theme
- `p` / `←` - Previous theme
- `Enter` - Lock current theme (stays animated)
- `s` - Select theme for live mode
- `Space` - Pause/Resume
- `q` - Quit

**Live Mode:**
- `l` - Toggle log overlay
- `q` - Quit

**Daemon Mode:**
- `l` - Toggle log overlay
- `q` - Quit

---

## 🎨 Themes

42 animated themes across 8 categories. Browse with `hermes-vision --gallery`:

### Originals (7)
1. **black-hole** ⭐ - Rotating singularity with event horizon
2. **neural-sky** - Classic cyan/blue network (default live theme)
3. **storm-core** - Chaotic energy storms
4. **moonwire** - Minimal silver elegance
5. **rootsong** - Earth-tone organic growth
6. **stormglass** - Aqua crystalline structures
7. **spiral-galaxy** - 3-arm cosmic spiral

### Nature (5)
- **deep-abyss** - Ocean depths with bioluminescence
- **storm-sea** - Turbulent waters
- **dark-forest** - Mysterious woodland
- **mountain-stars** - Alpine night sky
- **beach-lighthouse** ⭐ - Coastal waves with sweeping beam

### Cosmic (4)
- **aurora-borealis** ⭐ - Constellation patterns in northern lights
- **nebula-nursery** - Stellar birth clouds
- **binary-rain** ⭐ - Matrix-style code with cloud layer
- **wormhole** - Tunnel through spacetime

### Industrial (4)
- **liquid-metal** - Molten flow patterns
- **factory-floor** ⭐ - Assembly line with sparks
- **pipe-hell** ⭐ - Plumbing nightmare
- **oil-slick** - Rainbow surface tension

### Whimsical (5)
- **campfire** ⭐ - Large bonfire with embers
- **aquarium** - Tropical fish tank
- **circuit-board** ⭐ - PCB close-up
- **lava-lamp** - Hypnotic blobs
- **firefly-field** - Bioluminescent meadow

### Hostile (2)
- **noxious-fumes** - Toxic gas clouds
- **maze-runner** ⭐ - Shifting dimensional portals

### Exotic (5)
- **neon-rain** - Cyberpunk downpour
- **volcanic** - Lava flows
- **crystal-cave** - Geode interior
- **spider-web** - Silk patterns
- **snow-globe** - Winter scene

### Mechanical/Retro (5)
- **clockwork** ⭐ - Giant swinging pendulum
- **coral-reef** - Underwater ecosystem
- **ant-colony** - Foraging patterns
- **satellite-orbit** - Space station paths
- **starfall** - Meteor shower

### Cosmic Advanced (5)
- **quasar** - Supermassive black hole jets
- **supernova** - Star explosion
- **sol** - Solar surface
- **terra** - Earth from space
- **binary-star** - Twin suns orbit

⭐ = Enhanced in v0.1.0

---

## 📊 What It Monitors

Hermes Vision tracks 34 event types across 7 data sources:

### Agent Activity
- Sessions starting/ending
- Tool calls and completions
- Token usage (proportional visual intensity)
- Model switches
- Thinking states

### Memory Operations
- New memories created
- Memories accessed
- Memory count changes

### Scheduled Jobs
- Cron jobs executing
- Jobs completing/failing

### Security (Optional)
- Threats blocked
- Secrets detected/redacted
- Rate anomalies

### Learning
- Trajectory logs (success/failure)
- Tool usage patterns (bursts & chains)
- Session duration milestones

---

## 🎯 Visual Effects

Events trigger one of 8 visual effects:

| Effect | Description | Example Trigger |
|--------|-------------|-----------------|
| **packet** | Glyph travels along edge | Tool call |
| **pulse** | Expanding ring from node | Message added |
| **burst** | Particle explosion | Task completed |
| **flash** | All edges change color | Error or threat |
| **spawn_node** | New node appears | Memory created |
| **wake** | Global intensity surge | Agent starts |
| **cool_down** | Global intensity fade | Agent ends |
| **dim** | Temporary reduction | Thinking state |

---

## 🤖 Auto-Launch

Have hermes-vision automatically open when cron jobs start:

```bash
# Enable auto-launch
echo '{"auto_launch": true}' > ~/.hermes/vision/config.json

# Test it
python3 hermes_vision/launcher.py --test-launch
```

**Supported platforms:**
- macOS (iTerm2, Terminal.app)
- Linux (gnome-terminal, konsole, xterm)
- tmux (any platform)

See [AUTOLAUNCH.md](AUTOLAUNCH.md) for detailed testing guide.

---

## 🛠️ Advanced Usage

### Daemon Mode (Recommended for Always-On Monitoring)

```bash
hermes-vision --daemon --logs
```

Starts in gallery (beautiful screensaver), automatically switches to live mode when you start working with Hermes, returns to gallery after 30 seconds idle.

### Custom Configuration

Create `~/.hermes/vision/config.json`:

```json
{
  "auto_launch": true,
  "preferred_terminal": "iterm2",
  "launch_command": "hermes-vision --daemon --logs"
}
```

### Integration with Hermes Agent

Hermes Vision automatically monitors your agent activity through:
- SQLite database (`~/.hermes/state.db`)
- Gateway hooks (event stream)
- Filesystem watching (memories, cron)

No additional configuration needed - just install and run!

---

## 📚 Documentation

- **[INSTALL.md](INSTALL.md)** - Detailed installation guide
- **[AUTOLAUNCH.md](AUTOLAUNCH.md)** - Auto-launch setup & testing
- **[COMPLETE.md](COMPLETE.md)** - Full feature reference
- **[ENHANCEMENTS.md](ENHANCEMENTS.md)** - Development roadmap

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Quick smoke test
echo "" | hermes-vision --gallery --seconds 1

# Check if events are being captured
tail -f ~/.hermes/vision/events.jsonl
```

**Test Coverage:** 63 tests, 100% passing ✅

---

## 🔧 Requirements

- Python 3.10+
- No external dependencies (pure stdlib!)
- Terminal with 256 color support (recommended)
- Minimum terminal size: 80x24 (for log overlay)

---

## 🐛 Troubleshooting

**Q: No events showing in live mode?**
- Press `l` to toggle log overlay
- Check: `ls ~/.hermes/state.db` (should exist)
- Verify Hermes Agent is running and creating sessions

**Q: Keyboard controls not working?**
- Make sure you're using the right mode:
  - Gallery: `n`/`p` work
  - Live: Only `l` and `q` work
- Try pressing keys twice
- Check your terminal supports key events

**Q: Auto-launch not working?**
- Check config: `cat ~/.hermes/vision/config.json`
- Test launcher: `python3 hermes_vision/launcher.py --test-launch`
- Verify hook installed: `ls ~/.hermes/hooks/hermes-vision/`

**Q: "LOCKED" text flashing?**
- Update to latest version (fixed in commit 2f103b2)

---

## 💡 Tips

- **Best experience:** Run `hermes-vision --daemon --logs` in a dedicated terminal
- **Theme browsing:** Use `--gallery`, press `Enter` to lock your favorite
- **Theme selection:** In gallery, press `s` to select for live mode
- **Performance:** Daemon mode is efficient - safe to leave running 24/7

---

## 🏗️ Architecture

Pure Python stdlib implementation:
- **curses** - Terminal UI rendering
- **sqlite3** - Database polling (state.db)
- **json** - Event parsing
- **subprocess** - Platform launching

No external dependencies means:
- ✅ Fast installation
- ✅ No version conflicts
- ✅ Works everywhere Python 3.10+ does
- ✅ Minimal maintenance

---

## 🌙 Credits

Built with Test-Driven Development by Hermes Agent  
Inspired by the Moonsong vision of beautiful, useful tools  

**Technology:** Python · curses · TDD  
**Philosophy:** Liberation through beauty and privacy  

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

Copyright (c) 2026 Nous Research

---

## 🚀 Quick Reference Card

```
MODES:
  hermes-vision              → Live (default)
  hermes-vision --gallery    → Gallery (browse themes)
  hermes-vision --daemon     → Daemon (auto-switch)

KEYS (Gallery):
  n/p     → Next/Previous theme
  Enter   → Lock current theme
  s       → Select for live mode
  Space   → Pause/Resume
  q       → Quit

KEYS (Live):
  l       → Toggle log overlay
  q       → Quit

SETUP AUTO-LAUNCH:
  echo '{"auto_launch": true}' > ~/.hermes/vision/config.json
  
TEST AUTO-LAUNCH:
  python3 hermes_vision/launcher.py --test-launch
```

---

**Enjoy watching your AI think! 🧠✨**
