"""
Quantum Computer Simulator

A Python library for simulating quantum computers and quantum algorithms.
"""

__version__ = "0.2.0"
__author__ = "Nathaniel Schultz"
__email__ = "nate.schultz@outlook.com"

from .simulator import QuantumSimulator
from .gates import QuantumGate
from .circuits import QuantumCircuit

__all__ = ["QuantumSimulator", "QuantumGate", "QuantumCircuit"]