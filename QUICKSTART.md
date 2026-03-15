# ⚡ Hermes Neurovision - 60 Second Setup

## For First-Time Users

```bash
# 1. Clone and install
git clone https://github.com/Tranquil-Flow/hermes-neurovision.git
cd hermes-neurovision
pip install -e .

# 2. Run setup (installs gateway hook, creates config)
python3 install_helper.py

# 3. Run it!
hermes-neurovision --gallery

# 4. Browse 85 themes with 'n' key
# 5. Lock your favorite with 'Enter'
# 6. Press 's' to select for live mode
```

That's it! 🎉

---

## Gallery Mode Workflow

```bash
hermes-neurovision --gallery
```

1. **Browse**: Press `n` or `p` to cycle through 42 themes
2. **Lock**: Press `Enter` when you find one you like (keeps animating)
3. **Select**: Press `s` to use it in live mode
4. **Quit**: Press `q`

Bottom hints show what keys to press!

---

## Live Mode (Event Monitoring)

```bash
hermes-neurovision
```

- Automatically reacts to Hermes Agent activity
- Press `l` to see event logs
- Shows "LOGS: ON" indicator when enabled
- Events trigger visual effects instantly

---

## Daemon Mode (Best of Both)

```bash
hermes-neurovision --daemon --logs
```

- Starts as beautiful gallery screensaver
- Auto-switches to live mode when agent is active
- Returns to gallery after 30 seconds idle
- Perfect for always-on monitoring!

---

## Testing Auto-Launch

```bash
# Enable auto-launch
echo '{"auto_launch": true}' > ~/.hermes/neurovision/config.json

# Test the launcher
python3 hermes_neurovision/launcher.py --test-launch

# Should open a new terminal window with hermes-neurovision running!
```

---

## Common Commands

```bash
# Quick test (runs for 10 seconds)
hermes-neurovision --seconds 10

# Specific theme
hermes-neurovision --theme spiral-galaxy

# With logs from start
hermes-neurovision --logs

# Daemon with specific theme
hermes-neurovision --daemon --theme moonwire

# Export a theme
hermes-neurovision --export neural-sky --author "YourName"

# Import a theme
hermes-neurovision --import mytheme.hvtheme

# Preview before importing
hermes-neurovision --import mytheme.hvtheme --preview

# List imported themes
hermes-neurovision --list-themes
```

---

## Keyboard Cheat Sheet

```
Gallery Mode:
  n / →     Next theme
  p / ←     Previous theme
  Enter     Lock (stay on current, keep animating)
  s         Select this theme for live mode
  Space     Pause/Resume
  q         Quit

Live Mode:
  l         Toggle log overlay
  q         Quit

Daemon Mode:
  l         Toggle log overlay (in both gallery and live)
  q         Quit
```

---

## What You'll See

**Gallery Mode:**
- Beautiful generative animation (85 themes across 8 categories)
- Each theme has unique visual style
- Can lock to stay on one theme
- Smooth transitions between themes

**Live Mode:**
- Neural network reacts to agent activity
- Packets travel when tools are called
- Pulses expand when messages arrive
- New nodes spawn for memory creation
- Log overlay shows what's happening

**Daemon Mode:**
- Gallery screensaver when idle
- Seamless switch to live on first event
- Shows "DAEMON: gallery" or "DAEMON: live" indicator
- Auto-returns to gallery after idle period

---

## Pro Tips

💡 **Always-on monitoring:** Run `hermes-neurovision --daemon` in a dedicated tmux pane
💡 **Browse themes:** Use `--gallery` to find your favorite, then use it in live/daemon
💡 **Debug events:** Enable `--logs` to see what events are triggering effects
💡 **Auto-launch:** Great for scheduled agent tasks - visualization opens automatically
💡 **Performance:** Pure stdlib means no dependencies to break or update

---

## Need Help?

- Installation details: [INSTALL.md](INSTALL.md)
- Auto-launch setup: [AUTOLAUNCH.md](AUTOLAUNCH.md)
- Run tests: `python -m pytest tests/ -v`

---

**Time from clone to running: ~60 seconds** ⚡

```bash
git clone https://github.com/Tranquil-Flow/hermes-neurovision.git && cd hermes-neurovision && pip install -e . && python3 install_helper.py && hermes-neurovision --gallery
```

That's all you need! 🚀
