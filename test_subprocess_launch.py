#!/usr/bin/env python3
"""Test if subprocess launching works."""

import subprocess
import time

print("Testing subprocess launch of hermes-neurovision auto_launch...")
print()

# Test 1: Direct call (this works for you)
print("[1] Direct call (should open terminal):")
from hermes_neurovision.launcher import auto_launch
result = auto_launch('hermes-neurovision --daemon --auto-exit --logs')
print(f"  Result: {result}")
time.sleep(2)

# Test 2: Via subprocess with output captured
print("\n[2] Via subprocess with output captured:")
proc = subprocess.Popen(
    [
        "python3", "-c",
        "from hermes_neurovision.launcher import auto_launch; "
        "result = auto_launch('hermes-neurovision --daemon --auto-exit --logs'); "
        "print(f'Launch result: {result}')"
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    start_new_session=True,
)

# Wait a bit for it to execute
time.sleep(2)
stdout, stderr = proc.communicate(timeout=3)

print(f"  Stdout: {stdout.decode()}")
print(f"  Stderr: {stderr.decode()}")
print(f"  Exit code: {proc.returncode}")

print("\n[3] Check if hermes-neurovision is running:")
ps_result = subprocess.run(
    ["ps", "aux"],
    capture_output=True,
    text=True
)
count = sum(1 for line in ps_result.stdout.split('\n') if 'hermes-neurovision' in line and 'grep' not in line)
print(f"  Found {count} hermes-neurovision processes")

print("\nDid two terminal windows open?")
