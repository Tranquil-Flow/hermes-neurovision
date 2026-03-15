from hermes_neurovision.themes import build_theme_config, THEMES
from hermes_neurovision.scene import ThemeState, Particle, Packet


def test_theme_state_builds_scene():
    # Use a theme that still uses the traditional node-based graph rendering
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 100, 30, seed=42)
    assert len(state.nodes) > 0
    assert len(state.edges) > 0
    assert len(state.stars) > 0


def test_theme_state_step_advances_frame():
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 100, 30, seed=42)
    assert state.frame == 0
    state.step()
    assert state.frame == 1


def test_theme_state_resize():
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 100, 30, seed=42)
    old_nodes = len(state.nodes)
    state.resize(200, 60)
    assert state.width == 200
    assert state.height == 60


def test_particle_step_decrements_life():
    p = Particle(10.0, 10.0, 0.1, 0.1, 5.0, 5.0, "*")
    alive = p.step()
    assert alive is True
    assert p.life == 4.0


def test_particle_dies_when_life_zero():
    p = Particle(10.0, 10.0, 0.1, 0.1, 1.0, 5.0, "*")
    alive = p.step()
    assert alive is False


def test_packet_step_advances_progress():
    p = Packet((0, 1), 0.0, 0.1)
    p.step()
    assert p.progress > 0.0


def test_all_themes_simulate_without_error():
    for name in THEMES:
        config = build_theme_config(name)
        state = ThemeState(config, 80, 24, seed=42)
        for _ in range(20):
            state.step()


# Task 16: apply_trigger tests

class FakeTrigger:
    def __init__(self, effect, intensity=0.7, color_key="accent", target="random_node"):
        self.effect = effect
        self.intensity = intensity
        self.color_key = color_key
        self.target = target


def test_apply_trigger_packet():
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 100, 30, seed=42)
    before = len(state.packets)
    state.apply_trigger(FakeTrigger("packet", target="random_edge"))
    assert len(state.packets) > before


def test_apply_trigger_burst():
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 100, 30, seed=42)
    before = len(state.particles)
    state.apply_trigger(FakeTrigger("burst", intensity=0.8))
    assert len(state.particles) > before


def test_apply_trigger_pulse():
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 100, 30, seed=42)
    before = len(state.pulses)
    state.apply_trigger(FakeTrigger("pulse"))
    assert len(state.pulses) > before


def test_apply_trigger_wake():
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 100, 30, seed=42)
    state.apply_trigger(FakeTrigger("wake"))
    assert state._intensity_target == 1.0


def test_apply_trigger_cool_down():
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 100, 30, seed=42)
    state.apply_trigger(FakeTrigger("cool_down"))
    assert state._intensity_target == 0.3


def test_apply_trigger_spawn_node():
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 100, 30, seed=42)
    before = len(state.nodes)
    state.apply_trigger(FakeTrigger("spawn_node", target="new"))
    assert len(state.nodes) == before + 1


# Task 46: TuneSettings integration tests

def _tuned_state(show_packets=True, show_particles=True, show_pulses=True,
                 show_stars=True, show_flash=True, show_spawn_node=True,
                 burst_scale=1.0, packet_rate_mult=1.0, event_sensitivity=1.0):
    from hermes_neurovision.tune import TuneSettings
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 100, 30, seed=42)
    t = TuneSettings()
    t.show_packets = show_packets
    t.show_particles = show_particles
    t.show_pulses = show_pulses
    t.show_stars = show_stars
    t.show_flash = show_flash
    t.show_spawn_node = show_spawn_node
    t.burst_scale = burst_scale
    t.packet_rate_mult = packet_rate_mult
    t.event_sensitivity = event_sensitivity
    state.tune = t
    return state


def test_tune_toggle_packets_suppresses_passive_spawn():
    """With show_packets=False, no packets ever spawn during step()."""
    state = _tuned_state(show_packets=False)
    for _ in range(500):
        state.step()
    assert state.packets == []


def test_tune_toggle_packets_suppresses_event_trigger():
    """With show_packets=False, apply_trigger('packet') adds nothing."""
    state = _tuned_state(show_packets=False)
    state.apply_trigger(FakeTrigger("packet", target="random_edge"))
    assert state.packets == []


def test_tune_toggle_particles_suppresses_event_burst():
    """With show_particles=False, apply_trigger('burst') adds no particles."""
    state = _tuned_state(show_particles=False)
    state.apply_trigger(FakeTrigger("burst", intensity=1.0))
    assert state.particles == []


def test_tune_toggle_pulses_suppresses_passive_spawn():
    """With show_pulses=False, no pulses ever spawn during step()."""
    state = _tuned_state(show_pulses=False)
    for _ in range(500):
        state.step()
    assert state.pulses == []


def test_tune_toggle_pulses_suppresses_event_trigger():
    """With show_pulses=False, apply_trigger('pulse') adds nothing."""
    state = _tuned_state(show_pulses=False)
    state.apply_trigger(FakeTrigger("pulse"))
    assert state.pulses == []


def test_tune_toggle_flash_suppresses_event_trigger():
    """With show_flash=False, apply_trigger('flash') leaves flash_until at 0."""
    state = _tuned_state(show_flash=False)
    state.flash_until = 0.0
    state.apply_trigger(FakeTrigger("flash", intensity=1.0))
    assert state.flash_until == 0.0


def test_tune_toggle_spawn_node_suppresses_event_trigger():
    """With show_spawn_node=False, apply_trigger('spawn_node') adds no node."""
    state = _tuned_state(show_spawn_node=False)
    before = len(state.nodes)
    state.apply_trigger(FakeTrigger("spawn_node", target="new"))
    assert len(state.nodes) == before


def test_tune_toggle_stars_suppresses_movement():
    """With show_stars=False, calling _step_stars() leaves star positions unchanged."""
    state = _tuned_state(show_stars=False)
    # Force all stars to a known x=50 so drift would move them if not gated
    for star in state.stars:
        star[0] = 50.0
    positions_before = [star[0] for star in state.stars]
    state._step_stars()
    positions_after = [star[0] for star in state.stars]
    assert positions_before == positions_after


def test_tune_slider_burst_scale_multiplies_particle_count():
    """burst_scale=2.0 produces more particles than burst_scale=1.0."""
    state_normal = _tuned_state(burst_scale=1.0)
    state_normal.apply_trigger(FakeTrigger("burst", intensity=1.0))
    count_normal = len(state_normal.particles)

    state_scaled = _tuned_state(burst_scale=2.0)
    state_scaled.apply_trigger(FakeTrigger("burst", intensity=1.0))
    count_scaled = len(state_scaled.particles)

    assert count_scaled > count_normal


def test_tune_slider_event_sensitivity_scales_burst_intensity():
    """event_sensitivity=0.0 produces fewer particles than sensitivity=1.0."""
    state_full = _tuned_state(event_sensitivity=1.0)
    state_full.apply_trigger(FakeTrigger("burst", intensity=1.0))
    count_full = len(state_full.particles)

    state_zero = _tuned_state(event_sensitivity=0.0)
    state_zero.apply_trigger(FakeTrigger("burst", intensity=1.0))
    count_zero = len(state_zero.particles)

    assert count_zero < count_full


def test_tune_slider_packet_rate_mult_zero_suppresses_passive_spawn():
    """packet_rate_mult=0.0 means no passive packets spawn over many steps."""
    state = _tuned_state(packet_rate_mult=0.0)
    for _ in range(500):
        state.step()
    assert state.packets == []


def test_tune_none_means_no_gating():
    """When state.tune is None, all normal behaviour is preserved."""
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 100, 30, seed=42)
    assert state.tune is None
    # Triggers work normally
    state.apply_trigger(FakeTrigger("burst", intensity=1.0))
    assert len(state.particles) > 0
    state.apply_trigger(FakeTrigger("packet", target="random_edge"))
    assert len(state.packets) > 0


# ── Node placement quality ────────────────────────────────────────────────────

def _node_spread(theme_name, w=120, h=30, seed=42):
    """Return (x_fraction, y_fraction) of usable terminal covered by nodes."""
    config = build_theme_config(theme_name)
    state = ThemeState(config, w, h, seed=seed)
    if not state.nodes:
        return None, None
    xs = [n[0] for n in state.nodes]
    ys = [n[1] for n in state.nodes]
    usable_w = w - 8
    usable_h = h - 6
    return (max(xs) - min(xs)) / usable_w, (max(ys) - min(ys)) / usable_h


def test_default_cluster_logic_spreads_across_width():
    """stellar-weave uses the default cluster logic — must cover ≥50% of usable width."""
    xf, _ = _node_spread("stellar-weave")
    assert xf is not None and xf >= 0.50, (
        f"stellar-weave default cluster logic only covers {xf:.0%} of width"
    )


def test_default_cluster_logic_spreads_across_height():
    """stellar-weave uses the default cluster logic — must cover ≥35% of usable height."""
    _, yf = _node_spread("stellar-weave")
    assert yf is not None and yf >= 0.35, (
        f"stellar-weave default cluster logic only covers {yf:.0%} of height"
    )


def test_default_cluster_logic_consistent_across_seeds():
    """Default cluster logic must not collapse to <30% height for common seeds."""
    for seed in (42, 7, 99, 13, 17, 31):
        _, yf = _node_spread("stellar-weave", seed=seed)
        if yf is None:
            continue
        assert yf >= 0.30, f"stellar-weave seed={seed}: only {yf:.0%} y coverage"


def test_edge_building_uses_aspect_ratio_correction():
    """Aspect ratio correction must produce more diagonal than vertical edges
    on a wide terminal (120x30) where chars are ~2:1 tall:wide in pixels."""
    config = build_theme_config("aurora-borealis")
    state = ThemeState(config, 120, 30, seed=42)
    if not state.edges or not state.nodes:
        return

    vert = diag = 0
    for ia, ib in state.edges:
        if ia >= len(state.nodes) or ib >= len(state.nodes):
            continue
        dx = abs(state.nodes[ib][0] - state.nodes[ia][0])
        dy = abs(state.nodes[ib][1] - state.nodes[ia][1])
        if dx < dy * 0.45:
            vert += 1
        elif dy < dx * 0.35:
            pass  # horizontal
        else:
            diag += 1

    total = vert + diag
    if total > 0:
        # After aspect ratio correction, vertical-only edges should be rare
        assert vert / total <= 0.40, (
            f"Too many vertical edges: {vert}/{total} ({vert/total:.0%}) — "
            f"aspect ratio correction may not be working"
        )
