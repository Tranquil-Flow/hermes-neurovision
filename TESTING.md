# Testing Hermes Neurovision Auto-Launch

## Quick Test (Hook Handler Only)

Test that the hook handler correctly processes events:

```bash
python3 /tmp/test_vision_hook.py
```

Expected: Events written to `~/.hermes/neurovision/events.jsonl`, auto-launch gracefully fails in headless environments.

## Full Integration Test (With Terminal)

On a system with a graphical terminal (macOS, Linux desktop):

1. Install:
```bash
cd ~/Projects/hermes-neurovision
python3 install_helper.py
```

2. Enable auto-launch:
```bash
echo '{"auto_launch": true}' > ~/.hermes/neurovision/config.json
```

3. Test with a cronjob:
```bash
hermes cron add --schedule "1m" --prompt "Test vision auto-launch: write timestamp to /tmp/vision-test.log with the current time"
```

4. Verify:
- Check `~/.hermes/neurovision/events.jsonl` for agent:start event
- A new terminal window should open with hermes-neurovision running
- Process should exit after 30 seconds (--auto-exit flag)

## Verifying Hook Installation

```bash
ls -la ~/.hermes/hooks/hermes-neurovision/
cat ~/.hermes/hooks/hermes-neurovision/HOOK.yaml
```

Should show:
- handler.py (the hook handler)
- HOOK.yaml (event subscriptions)

## Manual Hook Test

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.hermes/hooks/hermes-neurovision"))
import handler

handler.handle("agent:start", {"source": "cron", "session_id": "manual-test"})
print("Check ~/.hermes/neurovision/events.jsonl")
```

## Environment Requirements

- **Desktop/GUI environment:** macOS with Terminal.app/iTerm2, or Linux with gnome-terminal/konsole/xterm
- **OR tmux/screen:** For headless servers (set TERM appropriately)
- **NOT compatible:** Pure headless containers without pseudo-terminal support

## Debugging

If auto-launch fails, check:

1. Config exists and is valid JSON:
```bash
cat ~/.hermes/neurovision/config.json
```

2. Terminal detection works:
```bash
python3 -c "from hermes_neurovision.launcher import detect_terminal; print(detect_terminal())"
```

3. Process check works:
```bash
python3 -c "from hermes_neurovision.launcher import is_already_running; print(is_already_running())"
```

4. Custom launch command (for testing in special environments):
```bash
echo '{"auto_launch": true, "launch_command": "hermes-neurovision --gallery --seconds 10"}' > ~/.hermes/neurovision/config.json
```
