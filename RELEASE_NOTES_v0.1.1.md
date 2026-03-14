# Hermes Neurovision v0.1.1 Release Notes

## 🎉 What's New

### Theme Export/Import System

Share custom themes as portable `.hvtheme` files!

**Export any theme:**
```bash
hermes-neurovision --export neural-sky --author "YourName"
```

**Import themes:**
```bash
# Preview first
hermes-neurovision --import mytheme.hvtheme --preview

# Then install
hermes-neurovision --import mytheme.hvtheme
```

**List imported themes:**
```bash
hermes-neurovision --list-themes
```

### Features

- **Theme Sharing**: Export themes as single JSON files
- **AI-Assisted Design**: Have Hermes Agent design custom themes for you
- **Community Themes**: Download and share themes with others
- **Two Theme Types**:
  - **Config-only**: Just parameter tweaks (safe, no code)
  - **Custom plugin**: Full Python customization (requires confirmation)
- **Version Safety**: Compatibility checking with graceful degradation
- **Security**: Warnings and confirmation for custom plugin code

### Package Rename

**BREAKING CHANGE**: Renamed from `hermes-vision` to `hermes-neurovision`

**Why?**
- More descriptive name
- Better reflects the "neuro" visualization concept
- Cleaner branding

**Migration required**: See [MIGRATION_v0.1.1.md](MIGRATION_v0.1.1.md)

Quick migration:
```bash
pip uninstall hermes-vision
pip install -e .
# Old: hermes-vision
# New: hermes-neurovision
```

## 🎨 Theme Examples

### Creating Themes with AI

Ask your Hermes Agent:
> "Create a sunset beach theme with orange and purple colors"

Agent will generate a `.hvtheme` file you can import!

### Sharing Themes

1. Customize a theme (parameters or code)
2. Export: `hermes-neurovision --export mytheme`
3. Share the `.hvtheme` file
4. Recipients import: `hermes-neurovision --import mytheme.hvtheme`

### Example Theme

**Peaceful Blue** - Config-only theme (safe):
```bash
# Download from community
curl -O https://example.com/peaceful-blue.hvtheme

# Preview
hermes-neurovision --import peaceful-blue.hvtheme --preview

# Import
hermes-neurovision --import peaceful-blue.hvtheme

# Use
hermes-neurovision --theme peaceful-blue
```

## 🔒 Security

Custom plugin themes contain Python code. Hermes Neurovision:
- ⚠️ Warns you before importing
- 📝 Shows code for review
- ✋ Requires confirmation
- 🚀 `--trust` flag available for trusted sources

## 📊 Technical Details

- **Format**: `.hvtheme` (JSON with optional base64-encoded Python)
- **Version**: Format v1.0, App v0.1.1
- **Backward Compat**: Includes both `hermes_neurovision_version` and `hermes_vision_version`
- **Forward Compat**: Graceful degradation for newer formats
- **Migration**: Auto-migrates pre-release formats

## 🛠️ Full Feature List

- 42 animated themes
- Live event visualization  
- Gallery mode (theme browser)
- Daemon mode (auto-switches)
- Log overlay
- Auto-launch with cron jobs
- **NEW**: Theme export/import
- **NEW**: Theme registry
- **NEW**: Version compatibility checking
- Pure stdlib (no dependencies)
- 63+ passing tests

## 📚 Documentation

- [README.md](README.md) - Main documentation
- [QUICKSTART.md](QUICKSTART.md) - 60-second setup
- [MIGRATION_v0.1.1.md](MIGRATION_v0.1.1.md) - Upgrade guide
- [VERSION_COMPATIBILITY.md](VERSION_COMPATIBILITY.md) - Version strategy
- [PLAN_v0.1.2.md](PLAN_v0.1.2.md) - Future plans (sliders!)
- [V0.1.1_IMPLEMENTATION_COMPLETE.md](V0.1.1_IMPLEMENTATION_COMPLETE.md) - Implementation details

## 🔮 Coming in v0.1.2

- Interactive sliders for theme customization
- Edit mode with keyboard controls
- Real-time parameter adjustment
- Save personal theme preferences

## 🌙 Credits

Built with Test-Driven Development by Hermes Agent  
Inspired by the Moonsong vision of beautiful, useful tools  
Created by Tranquil-Flow (tranquil_flow@protonmail.com)

**Philosophy**: Liberation through beauty and privacy  
**Technology**: Python · curses · TDD  

---

## Installation

```bash
git clone https://github.com/NousResearch/hermes-neurovision.git
cd hermes-neurovision
pip install -e .
hermes-neurovision --gallery
```

## Quick Reference

```
EXPORT/IMPORT:
  hermes-neurovision --export THEME
  hermes-neurovision --import file.hvtheme
  hermes-neurovision --import file.hvtheme --preview
  hermes-neurovision --list-themes

MODES:
  hermes-neurovision              → Live (default)
  hermes-neurovision --gallery    → Gallery (browse)
  hermes-neurovision --daemon     → Daemon (auto-switch)

KEYS:
  Gallery: n/p (browse), Enter (lock), s (select), q (quit)
  Live: l (toggle logs), q (quit)
```

---

**Enjoy sharing beautiful themes! 🌙✨**
