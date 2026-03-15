# Release Commands — Run from Mac

All commits and tags are ready in the local git repo.
Run these from your Mac terminal inside the hermes-neurovision directory.

## 1. Push commits + all tags

```bash
cd ~/Projects/hermes-neurovision
git push origin main
git push origin --tags --force   # force needed: v0.2.0 tag was moved to HEAD
```

## 2. Create GitHub releases

### v0.1.2 release (retroactive — at the correct commit)

```bash
gh release create v0.1.2 \
  --title "v0.1.2 — AI-Driven Live Mode + Docker Visibility" \
  --notes "## Changes since v0.1.1

- Live mode uses AI event injection by default (quiet unless agent active)
- \`--animated\` flag restores passive ambient animations in live mode
- Docker container visibility improvements (events propagate across container boundary)
- Theme persistence: last-used theme remembered between sessions

**Commit:** 225413bf1b1f67942f0851860badb44f19f61841" \
  --target 225413bf1b1f67942f0851860badb44f19f61841
```

### v0.2.0 release (latest — tag is now at HEAD)

```bash
gh release create v0.2.0 \
  --title "v0.2.0 — 85 Themes, Strange Attractors, Spectacular Screens, Full Engine Overhaul" \
  --latest \
  --notes "## v0.2.0 — Major Release 🚀

### 85 Themes (was 42)

#### Strange Attractors — NEW
Real ODE systems rendered as density fields. Every pixel rainbow-hued.
\`lorenz-butterfly\` \`rossler-ribbon\` \`halvorsen-star\` \`aizawa-torus\` \`thomas-labyrinth\`

#### Spectacular — NEW
Maximum colour, maximum geometry. Every pixel individually coloured.
\`plasma-rainbow\` \`hypnotic-tunnel\` \`fractal-zoom\` \`particle-vortex\` \`chladni-sand\`

#### Engine Showcase (v0.2.0 new features)
\`dna-helix\` \`pendulum-waves\` \`kaleidoscope\` \`electric-storm\` \`coral-growth\`
\`dna-strand\` \`pendulum-array\` \`mandala-scope\` \`ghost-echo\` \`magnetic-field\`
\`mycelium-network\` \`swarm-mind\` \`neural-cascade\` \`tide-pool\` \`turing-garden\`
\`plasma-grid\` \`deep-signal\`

### New Engine Features
- **Post-processing pipeline**: warp, symmetry, glow, void, echo, force-field, decay
- **Reactive Element System**: SPARK, BLOOM, RIPPLE, WAVE, SHATTER, VOID, PULSE_BURST, STREAK
- **Emergent Systems**: reaction-diffusion, cellular automaton, physarum, wave field, neural field, boids
- **Tuner Overlay**: press \`t\` — real-time sliders for every visual parameter
- **Debug Panel**: press \`d\` — live event/trigger diagnostics
- **Performance Mode**: press \`P\` — halves render resolution for slow terminals
- **Mute** (\`M\`) and **Fullscreen** (\`F\`) toggles
- **Boot sequence**: animated startup with blinking label
- **Transparent background renderer**: remove forced black fill for bg-mode layering
- **Soundtrack assets**: lyrics, tags, generation scripts for 3 companion tracks

### Background Mode (--bg) — EXPERIMENTAL
Run neurovision silently behind a transparent terminal emulator.
Works on iTerm2, Kitty, Alacritty, WezTerm. Terminal.app requires manual opacity.

\`\`\`bash
hermes-neurovision --bg start           # gallery rotation behind terminal
hermes-neurovision --bg start --bg-theme lorenz-butterfly
hermes-neurovision --bg status
hermes-neurovision --bg stop
\`\`\`

> Note: bg mode is additive — does not affect live/gallery/daemon modes.

### Bug Fixes
- Python 3.14 crash: \`electric-storm\` bolt._age on plain list → \`[age, points]\` format
- \`dna-strand\` purple flashing boxes — glow_radius removed, palette fixed
- Gallery crash when new plugin files not auto-imported
- Attractors NaN crash — guard divergence, conservative dt, _reset_trajectory()
- Rossler/Thomas tumbling 3D camera, fractal-zoom continuous zoom
- Beach-lighthouse layout fix + quasar stellar rework
- bg dispatch bug: handle_bg_command read wrong attr (bg_action vs bg)
- --bg-theme now correctly disables gallery override

### Documentation
- **PLUGIN_API.md** — complete agent API reference: all hooks, state fields, rainbow colour
  helpers, reactive system, worked examples including a strange attractor from scratch
- **RELEASE_COMMANDS.md** — this file

### Install / Upgrade
\`\`\`bash
git pull
pip install -e .
\`\`\`"
```

## 3. Verify

```bash
gh release list
gh release view v0.1.2
gh release view v0.2.0
```

---

## Known Issues / Post-v0.2.0 TODO

- **bg mode on Terminal.app**: osascript backgroundAlpha requires macOS Automation
  permission (Privacy & Security > Automation). Unresolved — stashed for v0.2.1 polish.
- **bg mode text fade**: Per-line ANSI fade-up effect not yet implemented. Planned as
  a separate TUI wrapper mode. High complexity — requires owning the full render loop.
- **bg mode fullscreen/side-by-side**: window_mode config key exists but placement
  logic not implemented beyond spawning the process detached.
