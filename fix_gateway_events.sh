#!/bin/bash
# Find and fix the gateway to emit agent:start events for cronjobs

set -e

AGENT_DIR=~/.hermes/hermes-agent

echo "============================================================"
echo "  FIND AND FIX: Gateway Cronjob Event Emission"
echo "============================================================"
echo

# Step 1: Find the file that executes cronjobs
echo "[1] Finding cronjob execution code..."
cd "$AGENT_DIR"

echo "Searching for files that handle cronjob execution..."
grep -r "request_dump_cron" . --include="*.py" | head -5
echo

# Step 2: Find where hooks are instantiated
echo "[2] Finding hook manager code..."
grep -r "hook_manager\|HookManager" gateway/ cron/ --include="*.py" | head -10
echo

# Step 3: Show the cron directory structure
echo "[3] Cron directory structure..."
ls -la cron/
echo

# Step 4: Show gateway run.py (first 100 lines with line numbers)
echo "[4] Gateway run.py structure..."
head -100 gateway/run.py | grep -n "class\|def \|hook"
echo

echo "============================================================"
echo "  MANUAL INSPECTION NEEDED"
echo "============================================================"
echo
echo "Look for the function that:"
echo "  1. Starts executing a cronjob"
echo "  2. Has access to hook_manager or self.hooks"
echo "  3. Creates the session for the cronjob"
echo
echo "Then add AFTER session creation:"
echo '  self.hook_manager.emit("agent:start", {'
echo '      "session_id": session_id,'
echo '      "source": "cron",'
echo '      "job_id": job_id'
echo '  })'
echo
echo "Files to check:"
echo "  - gateway/run.py (likely has the hook_manager)"
echo "  - cron/scheduler.py (likely executes the jobs)"
echo
