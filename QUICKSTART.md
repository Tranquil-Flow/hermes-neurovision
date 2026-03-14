# ⚡ Hermes Neurovision - 60 Second Setup

## For First-Time Users

```bash
# 1. Install (choose one method)

# Method A - Automated (recommended)
cd ~/Projects/hermes-neurovision
python3 setup.py

# Method B - Manual  
pip install -e .
mkdir -p ~/.hermes/hooks/hermes-neurovision
cp hermes_neurovision/sources/hook_handler.py ~/.hermes/hooks/hermes-neurovision/handler.py
cp hermes_neurovision/sources/HOOK.yaml ~/.hermes/hooks/hermes-neurovision/HOOK.yaml

# 2. Run it!
hermes-neurovision --gallery

# 3. Browse themes with 'n' key
# 4. Lock your favorite with 'Enter'
# 5. Press 's' to select for live mode
```

That's it! 🎉

---

## Gallery Mode Workflow

```bash
hermes-neurovision --gallery
```

1. **Browse**: Press `n` or `p` to cycle through 10 themes
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

# Export a theme (NEW in v0.1.1)
hermes-neurovision --export neural-sky --author "YourName"

# Import a theme (NEW in v0.1.1)
hermes-neurovision --import mytheme.hvtheme

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
- Beautiful generative animation
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

- Read full docs: [COMPLETE.md](COMPLETE.md)
- Installation issues: [INSTALL.md](INSTALL.md)
- Auto-launch setup: [AUTOLAUNCH.md](AUTOLAUNCH.md)
- Check tests: `python -m pytest tests/ -v`

---

**Time from clone to running: ~60 seconds** ⚡

```bash
cd ~/Projects/hermes-neurovision && python3 setup.py && hermes-neurovision --gallery
```

That's all you need! 🚀
