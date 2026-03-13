#!/bin/bash
# Ultimate test to verify gateway -> hook -> auto-launch pipeline

echo "==================================================================="
echo "  ULTIMATE HERMES-VISION AUTO-LAUNCH TEST"
echo "==================================================================="
echo

# Step 1: Update handler with latest version
echo "[1] Updating handler with debug logging..."
cd ~/Projects/hermes-vision
git pull origin main 2>/dev/null || echo "  (git pull skipped)"
cp hermes_vision/sources/hook_handler.py ~/.hermes/hooks/hermes-vision/handler.py
echo "  ✅ Handler updated"
echo

# Step 2: Clear old logs
echo "[2] Clearing old logs for clean test..."
rm -f ~/.hermes/vision/launch_attempts.log
rm -f ~/.hermes/vision/handler_debug.log
echo "  ✅ Logs cleared"
echo

# Step 3: Verify config
echo "[3] Checking config..."
cat ~/.hermes/vision/config.json
echo

# Step 4: Manual trigger test
echo "[4] Manual trigger test (should open terminal)..."
pkill -f hermes-vision 2>/dev/null
sleep 1

python3 -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.hermes/hooks/hermes-vision'))
import handler
print('Calling handler.handle() manually...')
handler.handle('agent:start', {'source': 'cron', 'session_id': 'manual-ultimate-test'})
print('Done - check if terminal opened!')
"

sleep 3

echo
echo "[5] Checking launch attempt log..."
if [ -f ~/.hermes/vision/launch_attempts.log ]; then
    cat ~/.hermes/vision/launch_attempts.log
else
    echo "  ⚠️  No launch_attempts.log - handler may not be running _try_auto_launch()"
fi

echo
echo "[6] Did a terminal window open?"
echo "  Check now - you should see a new Terminal.app window with hermes-vision"
echo
echo "[7] Gateway logs (last 20 lines)..."
tail -20 ~/.hermes/logs/gateway.log 2>/dev/null | grep -E "(hook|agent:start|cron)" || echo "  No relevant gateway logs"
echo

echo "==================================================================="
echo "  Next: Wait for the scheduled cronjob at 08:53:54 to test real flow"
echo "==================================================================="
