"""Emergent simulation systems for hermes-neurovision."""
from hermes_neurovision.emergent.automaton import CellularAutomaton
from hermes_neurovision.emergent.physarum import PhysarumSim
from hermes_neurovision.emergent.neural_field import NeuralField
from hermes_neurovision.emergent.wave_field import WaveField
from hermes_neurovision.emergent.boids import BoidsFlock
from hermes_neurovision.emergent.reaction_diffusion import ReactionDiffusion

__all__ = [
    'CellularAutomaton', 'PhysarumSim', 'NeuralField',
    'WaveField', 'BoidsFlock', 'ReactionDiffusion',
]
