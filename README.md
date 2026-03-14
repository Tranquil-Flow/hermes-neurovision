# 🌌 Hermes Neurovision

**Terminal neurovisualizer for Hermes Agent**

A beautiful living neural network that reacts to your AI agent's activity in real-time. Watch as tool calls become traveling packets, memory updates spawn new nodes, and token usage creates pulsating waves across cosmic visualizations.

![Version](https://img.shields.io/badge/version-0.1.1-blue)
![First Public Release](https://img.shields.io/badge/release-first%20public-green)
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
💾 **Theme Export/Import** - Share custom themes as .hvtheme files  
⚡ **Pure Stdlib** - Zero external dependencies  
🧪 **63 Tests** - 100% passing, production-ready  
🎭 **Plugin System** - Extensible theme architecture  

---

## 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/Tranquil-Flow/hermes-neurovision.git
cd hermes-neurovision
pip install -e .

# Run setup script (installs gateway hook + auto-launch config)
python3 install_helper.py

# Start visualizing
hermes-neurovision
```

That's it! 🎉

---

## 📦 Manual Installation

If you prefer to set up manually:

```bash
# 1. Clone and install
git clone https://github.com/Tranquil-Flow/hermes-neurovision.git
cd hermes-neurovision
pip install -e .

# 2. Install gateway hook
mkdir -p ~/.hermes/hooks/hermes-neurovision
cp hermes_neurovision/sources/hook_handler.py ~/.hermes/hooks/hermes-neurovision/handler.py
cp hermes_neurovision/sources/HOOK.yaml ~/.hermes/hooks/hermes-neurovision/HOOK.yaml

# 3. (Optional) Enable auto-launch for cron jobs
echo '{"auto_launch": true}' > ~/.hermes/neurovision/config.json

# 4. Test it
hermes-neurovision --gallery
```

---

## 🎮 Usage

### Modes

```bash
# Live mode (default) - reacts to agent events
hermes-neurovision

# With log overlay to see event details
hermes-neurovision --logs

# Gallery mode - browse all 42 themes
hermes-neurovision --gallery

# Daemon mode - best of both worlds
hermes-neurovision --daemon

# Specific theme
hermes-neurovision --theme storm-core

# Test run (auto-exit after 10 seconds)
hermes-neurovision --seconds 10
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

42 animated themes across 8 categories. Browse with `hermes-neurovision --gallery`:

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

## 📊 How It Works

The neural network is not decorative — every visual change is triggered by a real event from your running Hermes Agent. The network is always animated as a baseline, but specific agent actions cause specific visual responses.

### Data Sources (polled every second)

| Source | File/DB | What it watches |
|--------|---------|-----------------|
| **Agent state** | `~/.hermes/state.db` | Sessions, messages, tool calls, token usage |
| **Gateway hook** | `~/.hermes/neurovision/events.jsonl` | Agent start/stop, session lifecycle |
| **Memories** | `~/.hermes/memories/` | Files created or modified |
| **Cron jobs** | `~/.hermes/cron/` | Scheduled job execution |
| **Trajectories** | `~/.hermes/logs/` | Success/failure logs |
| **Aegis** (optional) | `~/.hermes-aegis/audit.jsonl` | Security events |

### Agent Actions → Visual Effects

| What Hermes Does | What You See |
|-----------------|--------------|
| Session starts | **Wake** — entire network surges in brightness |
| Tool call executes | **Packet** — glyph travels along an edge |
| Message added to context | **Pulse** — expanding ring from a node |
| Memory is created | **Spawn node** — new node appears in the network |
| Task or session ends | **Burst** — particle explosion, then **Cool down** |
| Token usage increases | Network **intensity scales** proportionally |
| Error or security threat | **Flash** — all edges change color |
| Thinking/processing state | **Dim** — temporary brightness reduction |
| 5+ tool calls in 10s | **Tool burst** — cascade of rapid packets |
| Same tool used 3× in a row | **Tool chain** — sustained packet stream |
| Session running 5+ minutes | **Duration pulse** — periodic intensity wave |

### Log Overlay

Run with `--logs` (or press `l`) to see a live text stream of every event as it arrives — timestamps, event types, and source. This makes it easy to verify the visuals are responding to your actual agent activity.

---

## 🤖 Auto-Launch

Have hermes-neurovision automatically open when cron jobs start:

```bash
# Enable auto-launch
echo '{"auto_launch": true}' > ~/.hermes/neurovision/config.json

# Test it
python3 hermes_neurovision/launcher.py --test-launch
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
hermes-neurovision --daemon --logs
```

Starts in gallery (beautiful screensaver), automatically switches to live mode when you start working with Hermes, returns to gallery after 30 seconds idle.

### Custom Configuration

Create `~/.hermes/neurovision/config.json`:

```json
{
  "auto_launch": true,
  "preferred_terminal": "iterm2",
  "launch_command": "hermes-neurovision --daemon --logs"
}
```

### Theme Export/Import (NEW in v0.1.1)

Share custom themes as portable `.hvtheme` files:

```bash
# Export a theme
hermes-neurovision --export neural-sky --author "YourName"

# Preview a theme before importing
hermes-neurovision --import mytheme.hvtheme --preview

# Import a theme
hermes-neurovision --import mytheme.hvtheme

# List all imported themes
hermes-neurovision --list-themes

# Use an imported theme
hermes-neurovision --theme mytheme
```

**Theme Types:**
- **Config-only**: Just parameter tweaks (safe, no code)
- **Custom plugin**: Includes Python code (requires confirmation)

**Use Cases:**
- Share themes with the community
- Backup your custom themes
- Have AI agents design themes for you
- Download themes from others

See [RELEASE_NOTES_v0.1.1.md](RELEASE_NOTES_v0.1.1.md) for full details.

### Integration with Hermes Agent

Hermes Neurovision automatically monitors your agent activity through:
- SQLite database (`~/.hermes/state.db`)
- Gateway hooks (event stream)
- Filesystem watching (memories, cron)

No additional configuration needed - just install and run!

---

## 📚 Documentation

- **[INSTALL.md](INSTALL.md)** - Detailed installation guide
- **[QUICKSTART.md](QUICKSTART.md)** - 60-second setup guide
- **[AUTOLAUNCH.md](AUTOLAUNCH.md)** - Auto-launch setup & testing
- **[CHANGELOG.md](CHANGELOG.md)** - Version history
- **[PLAN_v0.1.2.md](PLAN_v0.1.2.md)** - Upcoming features (interactive theme editor)

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Quick smoke test
echo "" | hermes-neurovision --gallery --seconds 1

# Check if events are being captured
tail -f ~/.hermes/neurovision/events.jsonl
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
- Check config: `cat ~/.hermes/neurovision/config.json`
- Test launcher: `python3 hermes_neurovision/launcher.py --test-launch`
- Verify hook installed: `ls ~/.hermes/hooks/hermes-neurovision/`

**Q: "LOCKED" text flashing?**
- Update to latest version (fixed in commit 2f103b2)

---

## 💡 Tips

- **Best experience:** Run `hermes-neurovision --daemon --logs` in a dedicated terminal
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

Copyright (c) 2026 Tranquil-Flow

---

## 🚀 Quick Reference Card

```
MODES:
  hermes-neurovision              → Live (default)
  hermes-neurovision --gallery    → Gallery (browse themes)
  hermes-neurovision --daemon     → Daemon (auto-switch)

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
  echo '{"auto_launch": true}' > ~/.hermes/neurovision/config.json
  
TEST AUTO-LAUNCH:
  python3 hermes_neurovision/launcher.py --test-launch
```

---

**Enjoy watching your AI think! 🧠✨**
