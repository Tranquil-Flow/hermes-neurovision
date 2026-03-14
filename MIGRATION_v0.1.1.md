# Migration Guide: Hermes Vision → Hermes Neurovision

## What Changed in v0.1.1?

The project has been renamed from **hermes-vision** to **hermes-neurovision** for better clarity and descriptiveness.

## Why the Rename?

- More descriptive: "neurovision" better captures the neural network visualization concept
- Distinguishes from generic "vision" (which could mean computer vision)
- Aligns with the "Neurovisualizer" branding already in docs
- Clean slate for the official release

## What You Need to Do

### If You Have v0.1.0 Installed

```bash
# 1. Uninstall old package
pip uninstall hermes-vision

# 2. Reinstall with new name
cd ~/Projects/hermes-vision  # (directory name can stay)
pip install -e .

# 3. Update your workflow
# Old command: hermes-vision
# New command: hermes-neurovision
```

### Config Path Changes

Your config files will automatically migrate:

**Old paths**:
- `~/.hermes/vision/config.json`
- `~/.hermes/vision/events.jsonl`
- `~/.hermes/vision/themes/`

**New paths**:
- `~/.hermes/neurovision/config.json`
- `~/.hermes/neurovision/events.jsonl`
- `~/.hermes/neurovision/themes/`

**Migration**: Just copy your old config if you have customizations:
```bash
cp ~/.hermes/vision/config.json ~/.hermes/neurovision/config.json
```

### Hook Path Changes

**Old**: `~/.hermes/hooks/hermes-vision/`  
**New**: `~/.hermes/hooks/hermes-neurovision/`

**Reinstall hook**:
```bash
cd ~/Projects/hermes-vision
python3 install_helper.py
```

Or manually:
```bash
mkdir -p ~/.hermes/hooks/hermes-neurovision
cp hermes_neurovision/sources/hook_handler.py ~/.hermes/hooks/hermes-neurovision/handler.py
cp hermes_neurovision/sources/HOOK.yaml ~/.hermes/hooks/hermes-neurovision/HOOK.yaml
```

### .hvtheme Files

**Good news**: .hvtheme files exported from v0.1.0 (as hermes-vision) will still work!

The new version includes both field names for backward compatibility:
```json
{
  "metadata": {
    "hermes_neurovision_version": "0.1.1",
    "hermes_vision_version": "0.1.1"
  }
}
```

Old themes will import with a gentle migration message.

## Quick Reference

### Before (v0.1.0)
```bash
pip install -e .
hermes-vision --gallery
hermes-vision --theme neural-sky
~/.hermes/vision/config.json
~/.hermes/hooks/hermes-vision/
```

### After (v0.1.1)
```bash
pip install -e .
hermes-neurovision --gallery
hermes-neurovision --theme neural-sky
~/.hermes/neurovision/config.json
~/.hermes/hooks/hermes-neurovision/
```

## Breaking Changes Summary

| Item | Old | New |
|------|-----|-----|
| Package name | `hermes-vision` | `hermes-neurovision` |
| CLI command | `hermes-vision` | `hermes-neurovision` |
| Python package | `hermes_vision` | `hermes_neurovision` |
| Config directory | `~/.hermes/vision/` | `~/.hermes/neurovision/` |
| Hook directory | `~/.hermes/hooks/hermes-vision/` | `~/.hermes/hooks/hermes-neurovision/` |

## What Stays the Same

- All 42 themes
- Theme names (neural-sky, black-hole, etc.)
- All functionality
- .hvtheme file format
- Command-line flags
- Keyboard controls
- Visual effects

## Compatibility

- ✅ Old .hvtheme files work with new version
- ✅ New .hvtheme files include backward compatible metadata
- ⚠️ Old configs need manual copy to new path (if customized)
- ⚠️ Hooks need reinstall

## Support

If you run into issues:
1. Check you uninstalled the old package: `pip list | grep hermes`
2. Verify new package installed: `which hermes-neurovision`
3. Reinstall hooks: `python3 install_helper.py`
4. Test with: `hermes-neurovision --gallery --seconds 2`

## GitHub Repository

The repository will be renamed on GitHub from:
- `NousResearch/hermes-vision` → `NousResearch/hermes-neurovision`

GitHub automatically redirects old URLs, so existing clones will continue to work.

## Timeline

- v0.1.0: Released as "hermes-vision"
- v0.1.1: Renamed to "hermes-neurovision"
- Future: All releases as "hermes-neurovision"

The rename happens once, now, for a clean foundation going forward.
