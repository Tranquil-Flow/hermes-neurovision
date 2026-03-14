# Auto-Launch Feature

Automatically open hermes-neurovision in a new terminal when a cron job starts a Hermes session.

## How It Works

1. **Cron triggers** an agent:start event
2. **Gateway hook** detects it's from cron
3. **Launcher** spawns hermes-neurovision in a new terminal
4. **Visualization** starts with `--auto-exit --logs`
5. **Auto-closes** after 30 seconds of inactivity

## Setup

### 1. Enable Auto-Launch

Create config file:
```bash
mkdir -p ~/.hermes/neurovision
cat > ~/.hermes/neurovision/config.json << 'EOF'
{
  "auto_launch": true
}
EOF
```

### 2. Verify Gateway Hook is Installed

```bash
# Should exist from earlier installation
ls -la ~/.hermes/hooks/hermes-neurovision/
# Should show: handler.py and HOOK.yaml
```

If missing, reinstall:
```bash
cd ~/Projects/hermes-neurovision
mkdir -p ~/.hermes/hooks/hermes-neurovision
cp hermes_neurovision/sources/hook_handler.py ~/.hermes/hooks/hermes-neurovision/handler.py
cp hermes_neurovision/sources/HOOK.yaml ~/.hermes/hooks/hermes-neurovision/HOOK.yaml
```

## Testing

### Test 1: Platform Detection

```bash
cd ~/Projects/hermes-neurovision
python3 hermes_neurovision/launcher.py
```

Expected output:
```
Platform: macos (or linux)
Terminal: iterm2 (or terminal, tmux, etc.)
Already running: False
```

### Test 2: Manual Launch

```bash
python3 hermes_neurovision/launcher.py --test-launch
```

This should:
- Open a new terminal window/tab
- Start hermes-neurovision with `--auto-exit --logs`
- Exit with code 0 if successful

### Test 3: Duplicate Prevention

1. Run `hermes-neurovision` in one terminal
2. In another terminal:
```bash
python3 hermes_neurovision/launcher.py --test-launch
```

Should print "Launch failed" (duplicate prevented)

### Test 4: End-to-End with Cron

1. **Enable auto-launch** (see Setup above)

2. **Create a test cron job** that triggers agent:start:

```bash
# Add to ~/.hermes/cron/ if you have cron jobs set up
# Or manually write an event:
echo '{
  "timestamp": '$(date +%s.%N)',
  "event_type": "agent:start",
  "context": {
    "source": "cron",
    "session_id": "test_auto_launch"
  }
}' >> ~/.hermes/neurovision/events.jsonl
```

3. **Trigger the hook manually**:

```bash
cd ~/.hermes/hooks/hermes-neurovision
python3 handler.py
```

Or if gateway is running, it will handle automatically.

4. **Verify**:
- A new terminal should open automatically
- hermes-neurovision should be running with logs
- After 30s of no events, it should auto-exit

## Supported Terminals

**macOS:**
- ✅ iTerm2 (preferred)
- ✅ Terminal.app (fallback)
- ✅ tmux (if running in tmux)

**Linux:**
- ✅ tmux (if running in tmux)
- ✅ gnome-terminal
- ✅ konsole
- ✅ xterm
- ✅ xfce4-terminal

## Configuration Options

`~/.hermes/neurovision/config.json`:

```json
{
  "auto_launch": true,
  "preferred_terminal": "iterm2",
  "launch_command": "hermes-neurovision --daemon --logs"
}
```

**Options:**
- `auto_launch` (bool): Enable/disable auto-launch (default: false)
- `preferred_terminal` (string): Force specific terminal (default: auto-detect)
- `launch_command` (string): Custom command to run (default: "hermes-neurovision --auto-exit --logs")

## Troubleshooting

**Auto-launch not working:**
1. Check config: `cat ~/.hermes/neurovision/config.json`
2. Verify hook installed: `ls ~/.hermes/hooks/hermes-neurovision/`
3. Test launcher: `python3 hermes_neurovision/launcher.py --test-launch`
4. Check gateway logs for errors

**Multiple windows opening:**
- Launcher checks if hermes-neurovision is already running
- If duplicate opens, check `ps aux | grep hermes-neurovision` for stale processes

**Wrong terminal opening:**
- Set `preferred_terminal` in config.json
- Or file an issue with your terminal name

**Nothing happens:**
- Auto-launch is **opt-in** - must enable in config
- Only triggers on `agent:start` from cron/automated sources
- Won't trigger for manual/interactive sessions

## Security Note

Auto-launch is:
- **Opt-in** (disabled by default)
- **Fail-safe** (never crashes gateway)
- **Duplicate-aware** (won't spawn multiple instances)
- **Source-restricted** (only cron/automated triggers)

The launcher runs in a detached subprocess and can't interfere with the main Hermes process.
