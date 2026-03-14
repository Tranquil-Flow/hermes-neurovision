# 🌌 Hermes Neurovisualizer v0.1.0 - "The Visualization Expansion"

**Release Date:** March 14, 2026  
**Type:** Major Feature Release  
**Status:** Production Ready  

---

## 🎉 What's New

### Massive Theme Expansion
- **42 animated themes** (expanded from 10) across 8 categories
- **Plugin architecture** for extensible theme system
- Each theme is now a dedicated plugin class with full customization

### Visual Enhancements

Eight themes received major upgrades:

#### 1. **Black Hole** ⭐ (Now #1)
- Moved to first position in gallery
- Default showcase theme

#### 2. **Beach Lighthouse** 🌊
- Animated waves covering bottom 30% of screen
- Lighthouse beam always renders on top
- Shoreline marker for visual depth

#### 3. **Aurora Borealis** ⭐
- Complete redesign with constellation patterns
- Big Dipper, Orion, Cassiopeia, and Triangle shapes
- Gentle pulsing and shimmering stars

#### 4. **Binary Rain** ☁️
- Dense 5-row animated cloud layer at top
- Three density levels (dense, medium, light)
- Shifting pattern creates dynamic coverage

#### 5. **Clockwork** ⏰
- Giant pendulum swinging across entire screen
- -45° to +45° swing range
- Dynamic line drawing with anchor, rod, and bob

#### 6. **Maze Runner** 🌀
- Complete redesign as "Shifting Dimensional Maze"
- Three layers of reality (front, middle, deep)
- Reality tears and phasing portals
- Dimensional sparks ejecting in all directions

#### 7. **Campfire** 🔥
- Upgraded to large bonfire visualization
- 10-line tall ASCII art
- Enhanced flame colors and visibility

#### 8. **Circuit Board** 🔌
- Components spread across entire screen
- Electrical signals flickering everywhere
- Dense grid covering full viewport

### Technical Improvements

- **Bounds checking** prevents IndexError crashes during theme transitions
- **Stars/particles spawn everywhere** on industrial themes (factory-floor, pipe-hell, clockwork, circuit-board) - not just at top
- **Display name** updated to "Hermes Neurovisualizer"
- **Version number** displayed in footer (v0.1.0)
- **Nebula nursery** particle speeds reduced 5-6x for better aesthetics

### Bug Fixes

- Fixed IndexError when node indices go out of range
- Fixed lighthouse beam rendering order (now always on top)
- Fixed particle spawn locations for industrial themes

---

## 📦 Full Theme List

### Originals (7)
1. black-hole ⭐
2. neural-sky
3. storm-core
4. moonwire
5. rootsong
6. stormglass
7. spiral-galaxy

### Nature (5)
- deep-abyss
- storm-sea
- dark-forest
- mountain-stars
- beach-lighthouse ⭐

### Cosmic (4)
- aurora-borealis ⭐
- nebula-nursery
- binary-rain ⭐
- wormhole

### Industrial (4)
- liquid-metal
- factory-floor ⭐
- pipe-hell ⭐
- oil-slick

### Whimsical (5)
- campfire ⭐
- aquarium
- circuit-board ⭐
- lava-lamp
- firefly-field

### Hostile (2)
- noxious-fumes
- maze-runner ⭐

### Exotic (5)
- neon-rain
- volcanic
- crystal-cave
- spider-web
- snow-globe

### Mechanical/Retro (5)
- clockwork ⭐
- coral-reef
- ant-colony
- satellite-orbit
- starfall

### Cosmic Advanced (5)
- quasar
- supernova
- sol
- terra
- binary-star

⭐ = Enhanced in v0.1.0

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/NousResearch/hermes-neurovision.git
cd hermes-neurovision

# Checkout v0.1.0
git checkout v0.1.0

# Install
pip install -e .

# Run setup
python3 install_helper.py

# Start visualizing
hermes-neurovision --gallery
```

---

## 🎮 Quick Start

```bash
# Gallery mode - browse all 42 themes
hermes-neurovision --gallery

# Live mode - react to agent events
hermes-neurovision

# With log overlay
hermes-neurovision --logs

# Daemon mode (auto-switching)
hermes-neurovision --daemon --logs

# Specific theme
hermes-neurovision --theme black-hole
```

---

## 📋 Requirements

- Python 3.10+
- No external dependencies (pure stdlib)
- Terminal with 256 color support
- Minimum size: 80x24

---

## ✅ Testing

- **63 tests** - All passing
- **Manual validation** - All 42 themes load successfully
- **Smoke tests** - Gallery and live modes functional

---

## 🔗 Resources

- **Repository:** https://github.com/NousResearch/hermes-neurovision
- **Documentation:** [README.md](README.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Release Guide:** [RELEASE.md](RELEASE.md)
- **License:** [LICENSE](LICENSE) (MIT)

---

## 🙏 Acknowledgments

Built with Test-Driven Development by Hermes Agent for the Moonsong vision of beautiful, privacy-respecting tools.

**Technology Stack:**
- Python stdlib (curses, sqlite3, json)
- Zero external dependencies
- Plugin-based architecture

**Philosophy:**
- Liberation through beauty
- Privacy by design
- Extensibility first

---

## 🐛 Known Issues

None at release time.

---

## 🔮 Future Roadmap

Potential features for v0.2.0:
- Theme creation tutorial/guide
- Custom color palette support
- Performance metrics overlay
- Recording/playback mode
- Additional cosmic phenomena themes
- User-configurable particle systems
- Theme editor CLI

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check documentation in [README.md](README.md)
- Review [CHANGELOG.md](CHANGELOG.md) for migration notes

---

**Enjoy watching your AI think! 🧠✨**
