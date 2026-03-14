#!/usr/bin/env python3
"""One-command setup script for Hermes Vision."""

import os
import shutil
import subprocess
import sys


def print_step(step: int, total: int, message: str):
    """Print a formatted step."""
    print(f"\n[{step}/{total}] {message}")


def main():
    print("=" * 60)
    print("  Hermes Vision - Automated Setup")
    print("=" * 60)
    
    total_steps = 5
    current = 0
    
    # Step 1: Check Python version
    current += 1
    print_step(current, total_steps, "Checking Python version...")
    if sys.version_info < (3, 10):
        print("❌ ERROR: Python 3.10+ required")
        print(f"   You have: Python {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Step 2: Install package
    current += 1
    print_step(current, total_steps, "Installing hermes-neurovision package...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            check=True,
            capture_output=True
        )
        print("✅ Package installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        sys.exit(1)
    
    # Step 3: Install gateway hook
    current += 1
    print_step(current, total_steps, "Installing gateway hook...")
    hook_dir = os.path.expanduser("~/.hermes/hooks/hermes-neurovision")
    os.makedirs(hook_dir, exist_ok=True)
    
    handler_src = "hermes_neurovision/sources/hook_handler.py"
    hook_yaml_src = "hermes_neurovision/sources/HOOK.yaml"
    
    shutil.copy(handler_src, os.path.join(hook_dir, "handler.py"))
    shutil.copy(hook_yaml_src, os.path.join(hook_dir, "HOOK.yaml"))
    print(f"✅ Hook installed to {hook_dir}")
    
    # Step 4: Create config directory
    current += 1
    print_step(current, total_steps, "Setting up configuration...")
    config_dir = os.path.expanduser("~/.hermes/neurovision")
    os.makedirs(config_dir, exist_ok=True)
    print(f"✅ Config directory: {config_dir}")
    
    # Step 5: Test installation
    current += 1
    print_step(current, total_steps, "Testing installation...")
    try:
        result = subprocess.run(
            ["hermes-neurovision", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ CLI command works")
        else:
            print("⚠️  CLI may need PATH adjustment")
            print(f"   Try: export PATH=\"$HOME/.local/bin:$PATH\"")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  Command 'hermes-neurovision' not found in PATH")
        print(f"   You may need to add to PATH or use: python3 -m hermes_neurovision.cli")
    
    # Done!
    print("\n" + "=" * 60)
    print("  ✅ Setup Complete!")
    print("=" * 60)
    
    print("\n📚 Quick Start:\n")
    print("  # Live mode (reacts to agent events)")
    print("  hermes-neurovision")
    print()
    print("  # Gallery mode (browse themes)")
    print("  hermes-neurovision --gallery")
    print()
    print("  # Daemon mode (gallery when idle)")
    print("  hermes-neurovision --daemon --logs")
    
    print("\n🤖 Enable Auto-Launch (optional):\n")
    print("  echo '{\"auto_launch\": true}' > ~/.hermes/neurovision/config.json")
    print("  python3 hermes_neurovision/launcher.py --test-launch")
    
    print("\n📖 Documentation:\n")
    print("  README.md     - This file")
    print("  INSTALL.md    - Detailed installation")
    print("  AUTOLAUNCH.md - Auto-launch setup")
    print("  COMPLETE.md   - Full feature reference")
    
    print("\n🎨 Keyboard Controls:\n")
    print("  Gallery: n/p (next/prev), Enter (lock), s (select)")
    print("  Live:    l (logs), q (quit)")
    
    print("\n" + "=" * 60)
    print("  Enjoy your neural network visualization! 🌌")
    print("=" * 60)


if __name__ == "__main__":
    main()
