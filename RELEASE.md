# Release Guide for Hermes Vision v0.1.0

## What's New in v0.1.0

### Major Enhancements
- **42 Themes** - Expanded from 10 to 42 animated themes across 8 categories
- **Plugin Architecture** - Extensible theme system with dedicated plugin classes
- **Visual Improvements** - 8 themes significantly enhanced with new effects
- **Bug Fixes** - IndexError crashes resolved with proper bounds checking

### Theme Highlights
- 🌊 **Beach Lighthouse** - Waves covering bottom 30% with beam always on top
- ⭐ **Aurora Borealis** - Constellation patterns (Big Dipper, Orion, Cassiopeia)
- ☁️ **Binary Rain** - Dense 5-row animated cloud layer at top
- ⏰ **Clockwork** - Giant pendulum swinging across entire screen
- 🌌 **Maze Runner** - Complete redesign as "Shifting Dimensional Maze"
- 🔥 **Campfire** - Large bonfire with visible flames
- 💫 **Nebula Nursery** - Slow-drifting stellar wind particles
- 🔌 **Circuit Board** - Components spread across entire screen

### Technical Improvements
- Proper bounds checking prevents crashes during theme transitions
- Stars/particles now spawn everywhere (not just at top) for industrial themes
- Display name updated to "Hermes Neurovisualizer"
- Version number displayed in footer

## Pre-Release Checklist

- [x] All tests passing (63/63)
- [x] Version updated to 0.1.0 in pyproject.toml
- [x] CHANGELOG.md created
- [x] LICENSE file added (MIT)
- [x] README.md updated with accurate theme count and features
- [x] .gitignore properly configured for Python
- [x] All new files added to git

## Installation Testing

```bash
# Clean install test
pip uninstall hermes-vision -y
cd /path/to/hermes-vision
pip install -e .

# Verify version
python3 -c "from hermes_vision.themes import THEMES; print(len(THEMES))"
# Should output: 42

# Test gallery mode
hermes-vision --gallery --seconds 10

# Test live mode
hermes-vision --seconds 5
```

## Release Steps

1. **Final commit**
   ```bash
   git add .
   git commit -m "Release v0.1.0 - 42 themes, plugin architecture, visual enhancements"
   ```

2. **Create tag**
   ```bash
   git tag -a v0.1.0 -m "v0.1.0 - First major release with 42 themes"
   ```

3. **Push to GitHub**
   ```bash
   git push origin main
   git push origin v0.1.0
   ```

4. **Create GitHub Release**
   - Go to: https://github.com/NousResearch/hermes-vision/releases/new
   - Tag: v0.1.0
   - Title: "Hermes Vision v0.1.0 - The Visualization Expansion"
   - Description: Copy from CHANGELOG.md

5. **Verify Installation**
   ```bash
   pip install git+https://github.com/NousResearch/hermes-vision.git@v0.1.0
   hermes-vision --gallery
   ```

## Post-Release

- [ ] Update documentation site (if exists)
- [ ] Announce on relevant channels
- [ ] Monitor for bug reports
- [ ] Plan v0.2.0 features

## Known Issues

None at release time. All 63 tests passing.

## Future Roadmap (v0.2.0)

Potential features for next release:
- Theme creation tutorial
- Custom color palette support
- Performance metrics overlay
- Recording/playback mode
- Additional cosmic themes
- User-configurable particle systems
