# Hermes Vision - Final Release

## 🎉 ALL FEATURES COMPLETE

**Version:** 0.2.0  
**Status:** Production Ready  
**Tests:** 63 passing ✅

---

## What's Included

### Core Features (MVP)
✅ 10 animated themes (neural-sky to black-hole)  
✅ Gallery mode (rotate through themes)  
✅ Live mode (react to agent events)  
✅ 34 event types mapped to 8 visual effects  
✅ 7 data sources monitored  
✅ Log overlay with color coding  
✅ Pure stdlib (zero external dependencies)

### Phase 1: UX Improvements
✅ Gallery lock mode (Enter key - stays animated)  
✅ Theme selection workflow ('s' key → live mode)  
✅ Black hole spinning animation  
✅ Spiral galaxy 3-arm structure  
✅ Status indicators and hints  

### Phase 2: Post-MVP Features  
✅ Daemon mode (gallery when idle, live on events)  
✅ Trajectory monitoring (success/failure logs)  
✅ Session duration visualization (updates every 5min)  
✅ Tool usage pattern detection (bursts & chains)  

### Phase 3: Auto-Launch
✅ Platform detection (macOS/Linux)  
✅ Terminal detection (iTerm2, Terminal, tmux, etc)  
✅ Duplicate prevention  
✅ Opt-in configuration  
✅ Fail-safe (never crashes gateway)

---

## Installation

```bash
cd ~/Projects/hermes-vision
pip install -e .

# Install gateway hook
mkdir -p ~/.hermes/hooks/hermes-vision
cp hermes_vision/sources/hook_handler.py ~/.hermes/hooks/hermes-vision/handler.py
cp hermes_vision/sources/HOOK.yaml ~/.hermes/hooks/hermes-vision/HOOK.yaml

# Enable auto-launch (optional)
mkdir -p ~/.hermes/vision
echo '{"auto_launch": true}' > ~/.hermes/vision/config.json
```

---

## Usage

### Basic Commands

```bash
# Default mode (live visualization)
hermes-vision

# Gallery mode (browse themes)
hermes-vision --gallery

# Daemon mode (best of both worlds)
hermes-vision --daemon

# With log overlay
hermes-vision --logs

# Specific theme
hermes-vision --theme black-hole

# Auto-exit after idle
hermes-vision --auto-exit
```

### Keyboard Controls

**Gallery Mode:**
- `n` / Right Arrow - Next theme
- `p` / Left Arrow - Previous theme
- `Enter` - Lock current theme (stays animated)
- `s` - Select theme for live mode
- `Space` - Pause/Resume
- `q` - Quit

**Live Mode:**
- `l` - Toggle log overlay
- `q` - Quit

**Daemon Mode:**
- `l` - Toggle log overlay (works in both modes)
- `q` - Quit

---

## Event Sources

1. **Custom Events** - Gateway hook → `~/.hermes/vision/events.jsonl`
2. **State Database** - SQLite → `~/.hermes/state.db`
3. **Memories** - Filesystem → `~/.hermes/memories/`
4. **Cron Jobs** - Status → `~/.hermes/cron/`
5. **Aegis** - Audit trail → `~/.hermes-aegis/audit.jsonl` (optional)
6. **Trajectories** - Logs → `~/.hermes/logs/*.jsonl`
7. **Patterns** - Derived from state.db (bursts, chains, duration)

---

## Event Types (34)

**Agent Lifecycle:**
- agent_start, agent_end, agent_step
- session_start, session_reset, session_duration
- active_session, model_switch

**Tool Usage:**
- tool_call, tool_complete, command_executed
- tool_burst (5+ in 10s), tool_chain (3+ same tool)

**Memory:**
- memory_created, memory_accessed, memory_count_changed

**Cron:**
- cron_executing, cron_completed, cron_failed

**Security (Aegis):**
- threat_blocked, secret_redacted, secret_detected, rate_anomaly

**Data:**
- token_update, message_added

**Trajectories:**
- trajectory_logged, trajectory_failed

**Custom:**
- task_completed, skill_activated, error
- file_written, web_search, image_generated

---

## Visual Effects (8)

1. **packet** - Glyph travels along edge
2. **pulse** - Expanding ring from node
3. **burst** - Particle explosion
4. **flash** - All edges briefly change color
5. **spawn_node** - New node with connections
6. **wake** - Global intensity surge
7. **cool_down** - Global intensity fade
8. **dim** - Temporary intensity reduction

---

## Themes (10)

1. **neural-sky** - Classic cyan/blue network
2. **electric-mycelium** - Green organic growth
3. **cathedral-circuit** - Architectural blue
4. **storm-core** - Chaotic blue/cyan storms
5. **hybrid** - Multi-color dynamic
6. **moonwire** - Silver/white minimal
7. **rootsong** - Earth-tone organic
8. **stormglass** - Aqua crystalline
9. **spiral-galaxy** - 3-arm cosmic spiral (enhanced)
10. **black-hole** - Rotating singularity (enhanced)

---

## Auto-Launch Setup

See [AUTOLAUNCH.md](AUTOLAUNCH.md) for detailed testing guide.

**Quick setup:**
```bash
# Enable auto-launch
echo '{"auto_launch": true}' > ~/.hermes/vision/config.json

# Test it
python3 hermes_vision/launcher.py --test-launch
```

Platform support:
- ✅ macOS (iTerm2, Terminal.app)
- ✅ Linux (gnome-terminal, konsole, xterm)
- ✅ tmux (any platform)

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Test specific feature
python -m pytest tests/test_launcher.py -v

# Headless smoke test
echo "" | hermes-vision --gallery --seconds 1
```

**Current test coverage:** 63 tests, 100% passing ✅

---

## Project Statistics

- **Commits:** 30+
- **Python files:** 19
- **Lines of code:** 2,100+
- **Test files:** 8
- **Tests:** 63
- **Event types:** 34
- **Visual effects:** 8
- **Themes:** 10
- **Data sources:** 7

---

## Known Issues

1. **Black hole visual** - User reported it looks "a bit off" in gallery mode
   - Inner rings spin correctly
   - May need adjustment to node positioning

---

## Future Enhancements (Optional)

- Interactive node inspection (click to see event details)
- Theme editor/customization UI
- Recording mode (save animation as video/gif)
- More themes (community submissions)
- Custom color palettes
- Sound effects (optional audio feedback)

---

## Documentation

- [INSTALL.md](INSTALL.md) - Installation guide
- [AUTOLAUNCH.md](AUTOLAUNCH.md) - Auto-launch testing
- [PHASE1_UX_COMPLETE.md](PHASE1_UX_COMPLETE.md) - Phase 1 details
- [PHASE2_COMPLETE.md](PHASE2_COMPLETE.md) - Phase 2 details
- [ENHANCEMENTS.md](ENHANCEMENTS.md) - Enhancement roadmap

---

## Credits

Built with:
- Python 3.10+ (stdlib only)
- curses (terminal UI)
- Test-Driven Development (TDD)
- Moonsong's vision ✨

**Thank you for using Hermes Vision!** 🌙

---

_For support, issues, or contributions, see the project repository._
