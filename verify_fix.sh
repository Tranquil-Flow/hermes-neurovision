#!/bin/bash
# Quick verification script for the hermes-neurovision auto-launch fix

echo "════════════════════════════════════════════════════════════"
echo "  Hermes Vision Auto-Launch Verification"
echo "════════════════════════════════════════════════════════════"
echo

# Check if package is installed
echo "[1/5] Checking package installation..."
if command -v hermes-neurovision &> /dev/null; then
    echo "✅ hermes-neurovision command found"
    hermes-neurovision --help | head -3
else
    echo "❌ hermes-neurovision not installed"
    echo "    Run: cd ~/Projects/hermes-neurovision && python3 install_helper.py"
    exit 1
fi
echo

# Check hook installation
echo "[2/5] Checking hook installation..."
if [ -f ~/.hermes/hooks/hermes-neurovision/handler.py ]; then
    echo "✅ Hook handler installed"
    echo "    Path: ~/.hermes/hooks/hermes-neurovision/handler.py"
else
    echo "❌ Hook handler not installed"
    echo "    Run: cd ~/Projects/hermes-neurovision && python3 install_helper.py"
    exit 1
fi
echo

# Check config
echo "[3/5] Checking config..."
if [ -f ~/.hermes/vision/config.json ]; then
    echo "✅ Config found"
    cat ~/.hermes/vision/config.json
else
    echo "⚠️  Config not found (auto-launch disabled)"
    echo "    To enable: echo '{\"auto_launch\": true}' > ~/.hermes/vision/config.json"
fi
echo

# Test hook handler
echo "[4/5] Testing hook handler..."
python3 -c "
import sys, os, json
sys.path.insert(0, os.path.expanduser('~/.hermes/hooks/hermes-neurovision'))
import handler

handler.handle('agent:start', {'source': 'cron', 'session_id': 'verify-test'})
print('✅ Handler executed successfully')

events_path = os.path.expanduser('~/.hermes/vision/events.jsonl')
if os.path.exists(events_path):
    with open(events_path, 'r') as f:
        count = len(f.readlines())
    print(f'✅ Events file has {count} events')
"
echo

# Check terminal detection
echo "[5/5] Checking terminal detection..."
python3 -c "
from hermes_neurovision.launcher import detect_platform, detect_terminal
platform = detect_platform()
terminal = detect_terminal()
print(f'Platform: {platform}')
print(f'Terminal: {terminal}')
if terminal:
    print('✅ Terminal detected - auto-launch will work')
else:
    print('⚠️  No terminal detected - auto-launch will fail gracefully')
"
echo

echo "════════════════════════════════════════════════════════════"
echo "  ✅ Verification Complete"
echo "════════════════════════════════════════════════════════════"
echo
echo "To test auto-launch with a real cronjob:"
echo "  hermes cron add --schedule \"1m\" --prompt \"Test vision auto-launch\""
echo
echo "Expected behavior:"
echo "  - Event written to ~/.hermes/vision/events.jsonl"
echo "  - New terminal window opens (if terminal detected)"
echo "  - hermes-neurovision runs for ~30 seconds then exits"
