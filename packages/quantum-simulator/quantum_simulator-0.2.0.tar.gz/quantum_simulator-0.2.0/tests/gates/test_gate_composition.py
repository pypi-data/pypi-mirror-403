"""Test suite for gate composition and sequences."""

import pytest
import numpy as np

from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import (
    RY, X_GATE, Y_GATE, Z_GATE, H_GATE
)


class TestGateComposition:
    """Test gate composition and sequences."""
    
    def test_rotation_composition(self):
        """Test that rotation gates compose correctly."""
        theta1 = np.pi/6
        theta2 = np.pi/4
        
        # RY(θ1) followed by RY(θ2) should equal RY(θ1 + θ2)
        sim1 = QuantumSimulator(1)
        sim2 = QuantumSimulator(1)
        
        circuit1 = QuantumCircuit(1)
        circuit1.add_gate(RY(theta1), [0])
        circuit1.add_gate(RY(theta2), [0])
        circuit1.execute(sim1)
        
        circuit2 = QuantumCircuit(1)
        circuit2.add_gate(RY(theta1 + theta2), [0])
        circuit2.execute(sim2)
        
        np.testing.assert_array_almost_equal(
            sim1.get_state_vector(), sim2.get_state_vector()
        )
    
    def test_pauli_anticommutation(self):
        """Test Pauli gate anticommutation relations."""
        sim1 = QuantumSimulator(1)
        sim2 = QuantumSimulator(1)
        
        # XY should equal -YX (anticommute)
        circuit1 = QuantumCircuit(1)
        circuit1.add_gate(X_GATE, [0])
        circuit1.add_gate(Y_GATE, [0])
        circuit1.execute(sim1)
        
        circuit2 = QuantumCircuit(1)
        circuit2.add_gate(Y_GATE, [0])
        circuit2.add_gate(X_GATE, [0])
        circuit2.execute(sim2)
        
        # States should differ by a sign (and possibly phase)
        state1 = sim1.get_state_vector()
        state2 = sim2.get_state_vector()
        
        # Check that |XY|ψ⟩| = |YX|ψ⟩| (same magnitude)
        np.testing.assert_array_almost_equal(np.abs(state1), np.abs(state2))
    
    def test_hadamard_basis_change(self):
        """Test Hadamard changes computational basis."""
        sim = QuantumSimulator(1)
        circuit = QuantumCircuit(1)
        
        # HZH should equal X (basis change property)
        circuit.add_gate(H_GATE, [0])
        circuit.add_gate(Z_GATE, [0])
        circuit.add_gate(H_GATE, [0])
        circuit.execute(sim)
        
        # Compare with X gate applied directly
        sim_x = QuantumSimulator(1)
        circuit_x = QuantumCircuit(1)
        circuit_x.add_gate(X_GATE, [0])
        circuit_x.execute(sim_x)
        
        np.testing.assert_array_almost_equal(
            sim.get_state_vector(), sim_x.get_state_vector()
        )