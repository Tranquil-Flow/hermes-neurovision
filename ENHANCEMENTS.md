# Hermes Neurovision - Enhancement Plan

## Phase 1: UX Improvements (Immediate)

### 1.1 Gallery → Live Theme Selection
**Goal:** Let users browse gallery and press 's' to select current theme for live mode

**Implementation:**
- Add `s` key handler in GalleryApp
- Store selected theme, exit gallery
- Launch LiveApp with selected theme
- Add visual indicator showing "Press 's' to select this theme for live mode"

### 1.2 Gallery Lock Mode
**Goal:** Stay on current theme, keep animating (not paused)

**Implementation:**
- Add `locked` flag to GalleryApp
- Press `enter` to lock (stop auto-rotation, keep animating)
- Press `enter` again to unlock
- Visual indicator: "LOCKED" in corner

### 1.3 Black Hole Center Spinning
**Goal:** Make the central singularity visibly rotate

**Implementation:**
- Modify black_hole_mode in scene.py
- Add central node rotation animation
- Inner ring of nodes should spin fastest
- Outer accretion disk spins slower

### 1.4 Spiral Galaxy Distinct Arms
**Goal:** Make spiral arms more visible/distinct

**Implementation:**
- Increase arm separation in _build_nodes
- Add more pronounced twist
- Maybe vary node density by arm quadrant
- Consider adding arm-specific colors/brightness

## Phase 2: Post-MVP Features

### 2.1 Daemon Mode
**Implementation:**
- Create DaemonApp class
- Start in gallery mode
- Poll for events every 1s
- On first event: switch to live mode with visual transition
- After 30s idle: fade back to gallery
- Preserve selected theme across transitions

### 2.2 Trajectory Logs Monitoring
**Implementation:**
- Create sources/trajectories.py
- Poll ~/.hermes/logs/trajectory_samples.jsonl
- Poll ~/.hermes/logs/failed_trajectories.jsonl
- Map to events: trajectory_logged, trajectory_failed
- Add to bridge mapping

### 2.3 Session Duration Visualization
**Implementation:**
- Track session start_time in state_db source
- Emit periodic session_duration events (every 5min?)
- Map to visual: growing intensity or expanding pulse
- Show in log overlay: "Session: 23m"

### 2.4 Tool Usage Pattern Detection
**Implementation:**
- Track tool call frequency in state_db source
- Detect patterns: tool_burst (5+ in 10s), tool_chain (same tool 3x)
- Emit pattern events
- Map to visuals: cascade effect for burst,連鎖 for chain

### 2.5 Auto-launch on Agent:Start
**Implementation:**
- Modify hook_handler.py
- On agent:start event, spawn hermes-neurovision in background
- Detect platform (tmux/terminal/iTerm)
- Launch with --auto-exit (closes after 30s idle)
- Complex: needs to check if already running

## Implementation Order

**Today (Phase 1):**
1. Gallery lock mode (easiest)
2. Theme selection workflow
3. Black hole spinning
4. Spiral galaxy arms

**Next Session (Phase 2):**
5. Daemon mode
6. Trajectory monitoring
7. Session duration
8. Tool patterns
9. Auto-launch (if time)
