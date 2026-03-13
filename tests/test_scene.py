from hermes_vision.themes import build_theme_config, THEMES
from hermes_vision.scene import ThemeState, Particle, Packet


def test_theme_state_builds_scene():
    config = build_theme_config("neural-sky")
    state = ThemeState(config, 100, 30, seed=42)
    assert len(state.nodes) > 0
    assert len(state.edges) > 0
    assert len(state.stars) > 0


def test_theme_state_step_advances_frame():
    config = build_theme_config("neural-sky")
    state = ThemeState(config, 100, 30, seed=42)
    assert state.frame == 0
    state.step()
    assert state.frame == 1


def test_theme_state_resize():
    config = build_theme_config("neural-sky")
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
