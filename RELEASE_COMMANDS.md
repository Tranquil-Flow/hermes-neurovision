# Release Commands — Run from Mac

All commits and tags are ready in the local git repo.
Run these from your Mac terminal inside the hermes-neurovision directory.

## 1. Push commits + all tags

```bash
cd ~/Projects/hermes-neurovision
git push origin main
git push origin --tags
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

### v0.2.0 release (latest)

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

### Bug Fixes
- Python 3.14 crash: \`electric-storm\` bolt._age on plain list → \`[age, points]\` format
- \`dna-strand\` purple flashing boxes — glow_radius removed, palette fixed (MAGENTA → YELLOW)
- Gallery crash when new plugin files not auto-imported

### Documentation
- **PLUGIN_API.md** — complete agent API reference: all hooks, state fields, rainbow colour
  helpers, reactive system, worked examples including a strange attractor from scratch

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
