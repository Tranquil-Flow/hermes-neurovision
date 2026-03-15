"""Generated theme plugin screens for hermes-neurovision."""
import math
import random
import curses

from hermes_neurovision.plugin import ThemePlugin, ReactiveElement, Reaction
from hermes_neurovision.theme_plugins import register


class QuantumFoamPlugin(ThemePlugin):
    """Planck-scale spacetime foam — virtual particle pairs, wormholes, quantum interference."""

    name = "quantum-foam"

    def __init__(self):
        self._w = self._h = 0
        self._pairs = []          # list of [x1, y1, x2, y2, age, max_age]
        self._rng = random.Random(42)
        self._collapse_frame = -999   # frame when wavefunction collapsed
        self._decay_bubble = None     # (cx, cy, radius, max_radius) vacuum decay
        self._coherence_frame = -999  # frame when quantum coherence triggered
        self._wormholes = []          # [(cx, cy, radius, angle_offset, life)]

    def build_nodes(self, w, h, cx, cy, count, rng):
        return []

    def automaton_config(self):
        return {"rule": "brians_brain", "density": 0.06, "update_interval": 2}

    def emergent_layer(self):
        return "background"

    def glow_radius(self):
        return 2

    def react(self, event_kind: str, data) -> "Reaction | None":
        if event_kind == "agent_start":
            return Reaction(element=ReactiveElement.PULSE, intensity=1.0,
                            origin=(0.5, 0.5), color_key="bright", duration=3.0)
        if event_kind in ("llm_start", "llm_chunk"):
            return Reaction(element=ReactiveElement.STREAM, intensity=0.6,
                            origin=(0.0, self._rng.random()), color_key="accent", duration=0.9)
        if event_kind in ("llm_end",):
            return Reaction(element=ReactiveElement.WAVE, intensity=0.5,
                            origin=(0.5, 0.5), color_key="soft", duration=1.5)
        if event_kind in ("tool_call", "mcp_tool_call"):
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.8,
                            origin=(self._rng.random(), self._rng.random()),
                            color_key="accent", duration=2.0)
        if event_kind == "tool_error":
            return Reaction(element=ReactiveElement.SHATTER, intensity=0.85,
                            origin=(0.5, 0.5), color_key="warning", duration=2.5)
        if event_kind in ("error", "crash"):
            return Reaction(element=ReactiveElement.SHATTER, intensity=1.0,
                            origin=(0.5, 0.5), color_key="warning", duration=3.0)
        if event_kind in ("memory_save", "checkpoint_created"):
            return Reaction(element=ReactiveElement.BLOOM, intensity=1.0,
                            origin=(0.5, 0.5), color_key="bright", duration=3.0)
        if event_kind == "skill_create":
            return Reaction(element=ReactiveElement.BLOOM, intensity=0.9,
                            origin=(self._rng.random(), self._rng.random()),
                            color_key="accent", duration=2.5)
        if event_kind == "approval_request":
            return Reaction(element=ReactiveElement.SPARK, intensity=1.0,
                            origin=(0.5, 0.5), color_key="warning", duration=2.0)
        if event_kind == "dangerous_cmd":
            return Reaction(element=ReactiveElement.SPARK, intensity=1.0,
                            origin=(self._rng.random(), self._rng.random()),
                            color_key="warning", duration=2.0)
        if event_kind == "git_commit":
            return Reaction(element=ReactiveElement.TRAIL, intensity=0.7,
                            origin=(0.0, 0.5), color_key="soft", duration=2.0)
        if event_kind == "cron_tick":
            return Reaction(element=ReactiveElement.ORBIT, intensity=0.5,
                            origin=(0.5, 0.5), color_key="soft", duration=2.5)
        if event_kind == "subagent_started":
            return Reaction(element=ReactiveElement.RIPPLE, intensity=0.8,
                            origin=(self._rng.random(), self._rng.random()),
                            color_key="accent", duration=2.0)
        if event_kind == "mcp_connected":
            return Reaction(element=ReactiveElement.CONSTELLATION, intensity=0.9,
                            origin=(0.5, 0.5), color_key="bright", duration=3.0)
        if event_kind == "mcp_disconnected":
            return Reaction(element=ReactiveElement.SHATTER, intensity=0.6,
                            origin=(0.5, 0.5), color_key="soft", duration=1.5)
        if event_kind in ("compression_started", "compression_ended"):
            return Reaction(element=ReactiveElement.WAVE, intensity=0.7,
                            origin=(0.5, 0.0), color_key="accent", duration=2.0)
        return None

    def draw_extras(self, stdscr, state, color_pairs):
        import curses
        import math
        import random

        w, h = state.width, state.height
        f = state.frame
        intensity = state.intensity_multiplier

        # Resize guard
        if (w, h) != (self._w, self._h):
            self._w, self._h = w, h
            self._pairs = []
            self._wormholes = []

        bright_attr = curses.color_pair(color_pairs["bright"]) | curses.A_BOLD
        accent_attr = curses.color_pair(color_pairs["accent"])
        soft_attr   = curses.color_pair(color_pairs["soft"])
        base_dim    = curses.color_pair(color_pairs["base"]) | curses.A_DIM
        warn_attr   = curses.color_pair(color_pairs["warning"]) | curses.A_BOLD

        cx, cy = w / 2.0, h / 2.0
        t = f * 0.025

        # ── Quantum interference background ──────────────────────────────────
        # Multiple superimposed sine waves create quantum probability density
        wave_chars = " ·:;+=*#"
        n_wc = len(wave_chars) - 1

        for y in range(1, h - 1):
            for x in range(0, w - 1):
                dx, dy = (x - cx) / (w * 0.4), (y - cy) / (h * 0.4)
                # Four interfering quantum waves
                r1 = math.sqrt((dx + 0.3) ** 2 * 2 + (dy + 0.2) ** 2)
                r2 = math.sqrt((dx - 0.3) ** 2 * 2 + (dy - 0.2) ** 2)
                r3 = math.sqrt(dx ** 2 * 2 + dy ** 2)
                w1 = math.sin(r1 * 14.0 - t * 2.1)
                w2 = math.sin(r2 * 11.0 + t * 1.7)
                w3 = math.sin(r3 * 8.0 - t * 1.3)
                w4 = math.sin(dx * 6.0 + t) * math.sin(dy * 6.0 - t * 0.8)
                # Quantum probability amplitude (superposition)
                psi = (w1 + w2 + w3 * 0.7 + w4 * 0.5) / 4.0
                prob = (psi + 1.0) / 2.0   # 0..1
                prob = max(0.0, min(1.0, prob * (0.4 + 0.3 * intensity)))

                ch = wave_chars[int(prob * n_wc)]
                if prob > 0.7:
                    attr = accent_attr
                elif prob > 0.45:
                    attr = soft_attr
                else:
                    attr = base_dim
                try:
                    stdscr.addstr(y, x, ch, attr)
                except curses.error:
                    pass

        # ── Wormhole portals ──────────────────────────────────────────────────
        # Spawn wormholes occasionally
        spawn_chance = 0.004 + 0.003 * intensity
        if self._rng.random() < spawn_chance and len(self._wormholes) < 3:
            margin_x, margin_y = int(w * 0.15), int(h * 0.15)
            wcx = self._rng.randint(margin_x, w - margin_x)
            wcy = self._rng.randint(margin_y, h - margin_y)
            max_r = self._rng.randint(4, max(5, min(h // 4, 10)))
            self._wormholes.append([wcx, wcy, 0.0, max_r, self._rng.uniform(0, math.pi * 2), 0])

        # Draw and evolve wormholes
        alive_wormholes = []
        for wh in self._wormholes:
            wcx, wcy, radius, max_r, angle_off, age = wh
            age += 1
            # Grow then shrink lifecycle
            if radius < max_r and age < 60:
                radius += 0.4
            elif age >= 60:
                radius -= 0.5
            if radius > 0:
                # Draw swirling rings
                num_rings = max(1, int(radius))
                for ring in range(num_rings):
                    r_ring = (ring + 1) * (radius / num_rings)
                    rx = r_ring * 2.2  # aspect correction
                    ry = r_ring
                    steps = max(12, int(r_ring * 8))
                    for s in range(steps):
                        angle = (2 * math.pi * s / steps) + angle_off + age * 0.04
                        px = int(wcx + rx * math.cos(angle))
                        py = int(wcy + ry * math.sin(angle))
                        if 1 <= py < h - 1 and 0 <= px < w - 1:
                            spiral_ch = "◎○●◉"[ring % 4] if ring < 4 else "·"
                            attr = bright_attr if ring == 0 else (accent_attr if ring == 1 else soft_attr)
                            try:
                                stdscr.addstr(py, px, spiral_ch, attr)
                            except curses.error:
                                pass
                # Center singularity
                if 1 <= wcy < h - 1 and 0 <= wcx < w - 1:
                    try:
                        stdscr.addstr(wcy, wcx, "\u2746" if age % 10 < 5 else "\u2747", bright_attr)
                    except curses.error:
                        pass
                alive_wormholes.append([wcx, wcy, radius, max_r, angle_off, age])
        self._wormholes = alive_wormholes

        # ── Entanglement pairs ────────────────────────────────────────────────
        # Spawn new entangled particle pairs
        pair_budget = int(6 + 8 * intensity)
        while len(self._pairs) < pair_budget:
            # Two random positions, connected by quantum entanglement
            x1 = self._rng.randint(2, w - 3)
            y1 = self._rng.randint(2, h - 3)
            # Partner appears somewhere "symmetric-ish" (not exact mirror, quantum uncertainty)
            x2 = self._rng.randint(2, w - 3)
            y2 = self._rng.randint(2, h - 3)
            max_age = self._rng.randint(20, 80)
            self._pairs.append([x1, y1, x2, y2, 0, max_age])

        alive_pairs = []
        for pair in self._pairs:
            x1, y1, x2, y2, age, max_age = pair
            age += 1
            if age < max_age:
                # Draw entanglement line (ghostly dashes)
                steps = max(1, int(math.sqrt(((x2 - x1) / 2.0) ** 2 + (y2 - y1) ** 2) / 2))
                for s in range(steps + 1):
                    t_frac = s / max(1, steps)
                    lx = int(x1 + (x2 - x1) * t_frac)
                    ly = int(y1 + (y2 - y1) * t_frac)
                    if 1 <= ly < h - 1 and 0 <= lx < w - 1:
                        if (s + f) % 3 == 0:   # dashed, animated
                            line_ch = "~" if (f // 4 + s) % 2 == 0 else "\u2248"
                            try:
                                stdscr.addstr(ly, lx, line_ch, soft_attr)
                            except curses.error:
                                pass

                # Draw the particles themselves — they flash in sync (entangled)
                flash = (f // 3 + age) % 2 == 0
                particle_ch = "\u25c6" if flash else "\u25c7"
                for px, py in [(x1, y1), (x2, y2)]:
                    if 1 <= py < h - 1 and 0 <= px < w - 1:
                        try:
                            stdscr.addstr(py, px, particle_ch,
                                          bright_attr if flash else accent_attr)
                        except curses.error:
                            pass
                alive_pairs.append([x1, y1, x2, y2, age, max_age])
        self._pairs = alive_pairs

        # ── Vacuum decay bubble ───────────────────────────────────────────────
        if self._decay_bubble is not None:
            bcx, bcy, brad, bmax = self._decay_bubble
            brad += 1.5
            # Draw expanding bubble wall
            rx = brad * 2.2
            ry = brad
            steps = max(24, int(brad * 12))
            for s in range(steps):
                angle = 2 * math.pi * s / steps
                bx = int(bcx + rx * math.cos(angle))
                by = int(bcy + ry * math.sin(angle))
                if 1 <= by < h - 1 and 0 <= bx < w - 1:
                    try:
                        stdscr.addstr(by, bx, "\u2593", warn_attr)
                    except curses.error:
                        pass
            # Interior — show consumed spacetime
            for dy in range(-int(ry), int(ry) + 1):
                for dx in range(-int(rx), int(rx) + 1):
                    if rx > 0 and ry > 0 and (dx / rx) ** 2 + (dy / ry) ** 2 < 0.7:
                        ix, iy = int(bcx + dx), int(bcy + dy)
                        if 1 <= iy < h - 1 and 0 <= ix < w - 1:
                            if self._rng.random() < 0.3:
                                try:
                                    stdscr.addstr(iy, ix, "\u2591", warn_attr)
                                except curses.error:
                                    pass
            if brad >= bmax:
                self._decay_bubble = None
            else:
                self._decay_bubble = (bcx, bcy, brad, bmax)

        # ── Heisenberg uncertainty sparks ─────────────────────────────────────
        # Random position-momentum uncertainty flashes
        spark_count = int(3 + 5 * intensity)
        for _ in range(spark_count):
            sx = self._rng.randint(1, w - 2)
            sy = self._rng.randint(1, h - 2)
            spark_ch = self._rng.choice(["·", ":", "+", "\u2746", "*", "\u2295", "\u2297"])
            s_attr = self._rng.choice([bright_attr, accent_attr, soft_attr])
            try:
                stdscr.addstr(sy, sx, spark_ch, s_attr)
            except curses.error:
                pass


register(QuantumFoamPlugin())
