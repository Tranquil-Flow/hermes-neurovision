# Hermes Neurovision v0.1.2 Plan

## Overview

v0.1.2 focuses on interactive parameter adjustment via sliders/keyboard controls in the CLI.

## Core Feature: Interactive Theme Editor

### User Experience

```bash
# Run any theme
hermes-neurovision --theme neural-sky

# Press 'e' to enter Edit Mode
# → Shows parameter overlay with current values
# → Arrow keys (↑/↓) select parameter
# → -/+ keys adjust value
# → Changes apply in real-time
# → Press 's' to save, 'q' to cancel
```

### Parameters Available for Editing

All ThemeConfig numeric parameters:
- `background_density` (0.01-0.05)
- `star_drift` (0.0-0.2)
- `node_jitter` (0.0-0.6)
- `packet_rate` (0.1-0.5)
- `packet_speed_min` (0.02-0.10)
- `packet_speed_max` (0.03-0.12)
- `pulse_rate` (0.05-0.15)
- `edge_bias` (0.3-0.8)
- `cluster_count` (2-5)

### UI Design

```
╔═ THEME EDITOR ═════════════════════════════╗
║                                             ║
║  Background Density  [████████░░░░] 0.030  ║
║  Star Drift          [██████░░░░░░] 0.100  ║
║▶ Node Jitter         [████████████] 0.400  ║
║  Packet Rate         [██████████░░] 0.320  ║
║  Packet Speed Min    [████░░░░░░░░] 0.040  ║
║  Packet Speed Max    [████████░░░░] 0.080  ║
║  Pulse Rate          [██████░░░░░░] 0.100  ║
║  Edge Bias           [██████████░░] 0.500  ║
║  Cluster Count       [██░░░░░░░░░░] 3      ║
║                                             ║
║  ↑/↓: Select  -/+: Adjust  s: Save  q: Cancel
╚═════════════════════════════════════════════╝
```

### Implementation Components

1. **EditModeOverlay class** (`hermes_neurovision/edit_mode.py`)
   - Render parameter list with sliders
   - Handle keyboard input
   - Trigger scene updates

2. **Scene Rebuild Hooks** (`hermes_neurovision/scene.py`)
   - `ThemeState.update_param(param, value)` method
   - Partial rebuild (only affected elements)
   - Preserve animation state

3. **Config Persistence** (`~/.hermes/neurovision/theme_overrides.json`)
   - Save user adjustments per theme
   - Load on theme startup
   - Merge with base config

4. **CLI Integration** (`hermes_neurovision/app.py`)
   - 'e' key toggles edit mode
   - Edit mode overlay on top of live visualization
   - Real-time preview of changes

### Config Override System

```json
// ~/.hermes/neurovision/theme_overrides.json
{
  "neural-sky": {
    "background_density": 0.035,
    "star_drift": 0.12,
    "node_jitter": 0.45,
    "packet_rate": 0.40
  },
  "black-hole": {
    "background_density": 0.042,
    "packet_speed": [0.03, 0.06]
  }
}
```

### Performance Considerations

- **Throttle updates**: Max 10fps during adjustment
- **Partial rebuild**: Only regenerate affected elements
  - `background_density` → rebuild stars only
  - `cluster_count` → rebuild nodes and edges
  - `packet_rate` → no rebuild, just update config
- **Preserve state**: Don't reset frame counter or intensity

### User Workflow

1. User runs theme: `hermes-neurovision --theme neural-sky`
2. Presses `e` → Edit mode appears
3. Uses arrow keys to select "Node Jitter"
4. Presses `+` repeatedly → sees nodes shake more
5. Adjusts other parameters
6. Presses `s` → Saves overrides
7. Next time theme loads, custom values apply automatically

### Export Integration

Once user has customized a theme with sliders, they can export it:

```bash
# Customize theme with sliders
hermes-neurovision --theme neural-sky
# [press 'e', adjust parameters, save]

# Export customized version
hermes-neurovision --export neural-sky --output my-neural.hvtheme
# → .hvtheme includes user's custom parameter values
```

## Secondary Features

### Advanced Parameter Controls

- **Reset to defaults**: `r` key in edit mode
- **Presets**: Save/load named parameter sets
- **Copy parameters**: Copy from another theme

### Plugin Parameter Exposure

Allow plugins to register custom tunable parameters:

```python
class MyThemePlugin(ThemePlugin):
    def get_editable_params(self):
        return {
            "wave_speed": (0.1, 2.0, 0.5),  # (min, max, default)
            "splash_intensity": (0.0, 1.0, 0.7)
        }
```

### Palette Editor (Stretch Goal)

Interactive color selection:
- `c` key in edit mode → color palette editor
- Select which palette slot (base, soft, bright, accent)
- Choose new color from available curses colors
- Preview changes live

## Implementation Timeline

- **Edit mode overlay**: 3-4 hours
- **Scene update hooks**: 2-3 hours
- **Config persistence**: 1-2 hours
- **Testing & polish**: 2-3 hours

**Total**: ~8-12 hours

## Success Criteria

- [ ] Can enter edit mode from any running theme
- [ ] All parameters adjustable with keyboard
- [ ] Changes visible in real-time
- [ ] Adjustments persist across sessions
- [ ] Can export customized themes
- [ ] Performance remains smooth (30+ FPS)
- [ ] No crashes or glitches during editing

## Future Ideas (v0.1.3+)

- Web-based editor with mouse controls
- Color picker with more options
- Animation speed global control
- Theme remix/blend functionality
- Community preset repository
