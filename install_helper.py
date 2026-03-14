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
    
    # Try with --user and --break-system-packages for macOS
    install_args = [sys.executable, "-m", "pip", "install", "-e", ".", "--user", "--break-system-packages"]
    
    try:
        result = subprocess.run(install_args, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Package installed")
        else:
            # Try without --break-system-packages if that flag doesn't work
            print("⚠️  Trying alternate install method...")
            install_args = [sys.executable, "-m", "pip", "install", "-e", ".", "--user"]
            result = subprocess.run(install_args, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Package installed")
            else:
                print(f"❌ Installation failed: {result.stderr}")
                sys.exit(1)
    except Exception as e:
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
    
    # Step 5: Test installation and provide PATH fix
    current += 1
    print_step(current, total_steps, "Testing installation...")
    
    # Detect where the script was installed
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    user_bin = os.path.expanduser(f"~/Library/Python/{python_version}/bin")
    
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
            raise FileNotFoundError("Not in PATH")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  Command 'hermes-neurovision' not in PATH")
        print(f"\\n   The command is installed in: {user_bin}")
        print(f"\\n   🔧 FIX: Add to your PATH by running:")
        print(f"\\n   echo 'export PATH=\\\"{user_bin}:$PATH\\\"' >> ~/.zshrc")
        print(f"   source ~/.zshrc")
        print(f"\\n   OR use directly:")
        print(f"   python3 -m hermes_neurovision --gallery")
    
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
