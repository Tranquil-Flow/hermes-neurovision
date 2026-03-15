"""Tests for Phase 5: Emergent Systems."""

import unittest.mock as mock

from hermes_neurovision.emergent import (
    CellularAutomaton, PhysarumSim, NeuralField,
    WaveField, BoidsFlock, ReactionDiffusion,
)


# ── CellularAutomaton ────────────────────────────────────────────────

def test_automaton_init():
    ca = CellularAutomaton(20, 10, rule='brians_brain', density=0.1)
    assert ca.w == 20
    assert ca.h == 10
    assert ca.rule == 'brians_brain'
    assert len(ca.grid) == 10
    assert len(ca.grid[0]) == 20


def test_automaton_step_no_crash():
    for rule in ('brians_brain', 'cyclic', 'rule110', 'game_of_life'):
        ca = CellularAutomaton(20, 10, rule=rule, density=0.1, update_interval=1)
        for _ in range(10):
            ca.step()


def test_automaton_inject():
    ca = CellularAutomaton(20, 10, rule='brians_brain', density=0.0)
    ca.inject(10, 5, radius=2)
    # Some cells should be alive
    alive = sum(1 for row in ca.grid for c in row if c == 1)
    assert alive > 0


def test_automaton_render_char():
    ca = CellularAutomaton(20, 10, rule='brians_brain', density=0.0)
    ca.grid[5][10] = 1  # on
    result = ca.render_char(10, 5)
    assert result is not None
    assert result[0] == '\u2593'
    assert result[1] == 'bright'


def test_automaton_render_off_returns_none():
    ca = CellularAutomaton(20, 10, density=0.0)
    assert ca.render_char(5, 5) is None


def test_automaton_brians_brain_cycle():
    """Brian's Brain: on -> dying -> off."""
    ca = CellularAutomaton(5, 5, rule='brians_brain', density=0.0, update_interval=1)
    ca.grid[2][2] = 1  # on
    ca.step()
    assert ca.grid[2][2] == 2  # dying
    ca.step()
    assert ca.grid[2][2] == 0  # off


# ── PhysarumSim ──────────────────────────────────────────────────────

def test_physarum_init():
    ps = PhysarumSim(40, 20, n_agents=50)
    assert ps.w == 40
    assert ps.h == 20
    assert len(ps.agents) == 50


def test_physarum_step_no_crash():
    ps = PhysarumSim(40, 20, n_agents=30)
    for _ in range(10):
        ps.step()


def test_physarum_add_food():
    ps = PhysarumSim(40, 20, n_agents=10)
    ps.add_food(20, 10, radius=2, amount=5.0)
    # Some trail cells should be non-zero
    has_food = any(ps.trails[y][x] > 0 for y in range(20) for x in range(40))
    assert has_food


def test_physarum_render_char():
    ps = PhysarumSim(20, 10, n_agents=0)
    ps.trails[5][10] = 4.0
    result = ps.render_char(10, 5)
    assert result is not None
    assert result[1] == 'bright'


def test_physarum_render_empty():
    ps = PhysarumSim(20, 10, n_agents=0)
    assert ps.render_char(5, 5) is None


# ── NeuralField ──────────────────────────────────────────────────────

def test_neural_field_init():
    nf = NeuralField(20, 10)
    assert nf.w == 20
    assert nf.h == 10
    assert all(nf.grid[y][x] == 0 for y in range(10) for x in range(20))


def test_neural_field_fire():
    nf = NeuralField(20, 10, fire_duration=3)
    nf.fire(10, 5, radius=1)
    assert nf.grid[5][10] == 3  # fire_duration


def test_neural_field_step_firing_decays():
    nf = NeuralField(20, 10, fire_duration=2, refractory=3)
    nf.grid[5][10] = 2  # firing
    nf.step()
    assert nf.grid[5][10] == 1  # still firing, lower
    nf.step()
    assert nf.grid[5][10] == -3  # now refractory


def test_neural_field_cascade():
    """Firing neurons trigger neighbors."""
    nf = NeuralField(10, 10, threshold=1, fire_duration=2)
    nf.grid[5][5] = 2  # fire center
    nf.step()
    # Neighbors should have been triggered
    neighbors_fired = sum(
        1 for dy in (-1, 0, 1) for dx in (-1, 0, 1)
        if (dx, dy) != (0, 0) and nf.grid[5+dy][5+dx] > 0
    )
    assert neighbors_fired > 0


def test_neural_field_render_char():
    nf = NeuralField(20, 10, fire_duration=2)
    nf.grid[5][10] = 2  # firing
    result = nf.render_char(10, 5)
    assert result is not None
    assert result[0] == '\u2588'
    assert result[1] == 'bright'


def test_neural_field_render_resting():
    nf = NeuralField(20, 10)
    assert nf.render_char(5, 5) is None


# ── WaveField ────────────────────────────────────────────────────────

def test_wave_field_init():
    wf = WaveField(20, 10)
    assert wf.w == 20
    assert wf.h == 10


def test_wave_field_drop():
    wf = WaveField(20, 10)
    wf.drop(10, 5, amplitude=3.0)
    assert wf.current[5][10] == 3.0


def test_wave_field_step_propagates():
    wf = WaveField(20, 10, speed=0.5, damping=0.99)
    wf.drop(10, 5, amplitude=5.0)
    wf.step()
    # Energy should spread to neighbors
    assert wf.current[5][10] != 5.0  # changed
    # Cardinal neighbors should have non-zero (5-point stencil)
    has_neighbor = any(
        abs(wf.current[5+dy][10+dx]) > 0.01
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))
        if 0 < 5+dy < 9 and 0 < 10+dx < 19
    )
    assert has_neighbor


def test_wave_field_render_char():
    wf = WaveField(20, 10)
    wf.current[5][10] = 2.0
    result = wf.render_char(10, 5)
    assert result is not None
    assert result[1] == 'bright'


def test_wave_field_render_calm():
    wf = WaveField(20, 10)
    assert wf.render_char(5, 5) is None


# ── BoidsFlock ───────────────────────────────────────────────────────

def test_boids_init():
    bf = BoidsFlock(40, 20, n_boids=20)
    assert bf.w == 40
    assert bf.h == 20
    assert len(bf.boids) == 20


def test_boids_step_no_crash():
    bf = BoidsFlock(40, 20, n_boids=20)
    for _ in range(20):
        bf.step()


def test_boids_add_attractor():
    bf = BoidsFlock(40, 20, n_boids=5)
    bf.add_attractor(20.0, 10.0, ttl=30)
    assert len(bf._attractors) == 1


def test_boids_attractor_decays():
    bf = BoidsFlock(40, 20, n_boids=5)
    bf.add_attractor(20.0, 10.0, ttl=2)
    bf.step()
    assert len(bf._attractors) == 1
    bf.step()
    assert len(bf._attractors) == 0  # expired


def test_boids_render_boids():
    bf = BoidsFlock(40, 20, n_boids=5)
    result = bf.render_boids()
    assert len(result) == 5
    for x, y, ch, color_key in result:
        assert isinstance(ch, str)
        assert len(ch) == 1
        assert color_key == 'accent'


def test_boids_stay_in_bounds():
    bf = BoidsFlock(40, 20, n_boids=10)
    for _ in range(50):
        bf.step()
    for boid in bf.boids:
        assert 0 <= boid[0] < 40
        assert 0 <= boid[1] < 20


# ── ReactionDiffusion ────────────────────────────────────────────────

def test_rd_init():
    rd = ReactionDiffusion(80, 40)
    assert rd.display_w == 80
    assert rd.display_h == 40
    assert rd.w == 40  # half-res
    assert rd.h == 20


def test_rd_step_no_crash():
    rd = ReactionDiffusion(40, 20, update_interval=1)
    for _ in range(10):
        rd.step()


def test_rd_add_chemical():
    rd = ReactionDiffusion(40, 20)
    rd.add_chemical(20, 10, radius=2)
    # Some v cells should be elevated
    has_chem = any(rd.v[y][x] > 0.05 for y in range(rd.h) for x in range(rd.w))
    assert has_chem


def test_rd_render_char():
    rd = ReactionDiffusion(40, 20)
    # Set high v value at internal coords
    rd.v[5][10] = 0.5
    # Display coords are 2x internal
    result = rd.render_char(20, 10)
    assert result is not None
    assert result[1] == 'bright'


def test_rd_render_empty():
    rd = ReactionDiffusion(40, 20)
    rd.v[5][10] = 0.0
    assert rd.render_char(20, 10) is None


# ── Integration: ThemeState fields ───────────────────────────────────

def test_theme_state_has_emergent_fields():
    from hermes_neurovision.scene import ThemeState
    from hermes_neurovision.themes import build_theme_config
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 80, 24, seed=42)
    # All should be None by default (plugin returns None for all configs)
    assert state.automaton is None
    assert state.physarum is None
    assert state.neural_field is None
    assert state.wave_field is None
    assert state.boids is None
    assert state.reaction_diffusion is None


def test_theme_state_init_emergent_with_config():
    """When plugin returns config, emergent systems are initialized."""
    from hermes_neurovision.scene import ThemeState
    from hermes_neurovision.themes import build_theme_config
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 80, 24, seed=42)
    # Override plugin to return a config
    state.plugin.automaton_config = lambda: {'rule': 'brians_brain', 'density': 0.05}
    state._init_emergent()
    assert state.automaton is not None
    assert isinstance(state.automaton, CellularAutomaton)


def test_theme_state_resize_reinits_emergent():
    from hermes_neurovision.scene import ThemeState
    from hermes_neurovision.themes import build_theme_config
    config = build_theme_config("electric-mycelium")
    state = ThemeState(config, 80, 24, seed=42)
    state.plugin.wave_config = lambda: {'speed': 0.3}
    state._init_emergent()
    assert state.wave_field is not None
    state.resize(100, 30)
    # After resize, should be re-initialized with new dimensions
    if state.wave_field is not None:
        assert state.wave_field.w == 100


# ── Renderer integration ─────────────────────────────────────────────

def test_renderer_has_draw_emergent():
    from hermes_neurovision.renderer import Renderer
    mock_stdscr = mock.MagicMock()
    mock_stdscr.getmaxyx.return_value = (30, 100)
    with mock.patch("curses.has_colors", return_value=False):
        renderer = Renderer(mock_stdscr)
    assert hasattr(renderer, '_draw_emergent')
