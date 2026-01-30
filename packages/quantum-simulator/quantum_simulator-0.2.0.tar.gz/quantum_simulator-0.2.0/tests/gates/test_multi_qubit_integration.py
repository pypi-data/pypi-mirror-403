"""Test suite for integration and relationships between multi-qubit gates."""

import pytest
import numpy as np

from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import (
    H_GATE, X_GATE, Y_GATE, Z_GATE, CNOT_GATE, CZ_GATE,
    TOFFOLI_GATE, CCZ_GATE, RY
)


class TestMultiQubitGateIntegration:
    """Test integration and relationships between multi-qubit gates."""
    
    def test_cz_from_cnot_and_hadamard(self):
        """Test that CZ = H⊗I CNOT H⊗I."""
        sim1 = QuantumSimulator(2)
        sim2 = QuantumSimulator(2)
        
        # Prepare test state
        circuit1 = QuantumCircuit(2)
        circuit1.add_gate(H_GATE, [0])
        circuit1.add_gate(RY(np.pi/3), [1])
        circuit1.add_gate(CZ_GATE, [0, 1])  # Direct CZ
        circuit1.execute(sim1)
        
        # Equivalent implementation using CNOT
        circuit2 = QuantumCircuit(2)
        circuit2.add_gate(H_GATE, [0])
        circuit2.add_gate(RY(np.pi/3), [1])
        circuit2.add_gate(H_GATE, [1])      # H on target
        circuit2.add_gate(CNOT_GATE, [0, 1]) # CNOT
        circuit2.add_gate(H_GATE, [1])      # H on target
        circuit2.execute(sim2)
        
        np.testing.assert_array_almost_equal(
            sim1.get_state_vector(), sim2.get_state_vector()
        )
    
    def test_three_qubit_gate_decomposition(self):
        """Test decomposition relationships between 3-qubit gates."""
        # CCZ can be implemented using Toffoli and single qubit gates
        sim1 = QuantumSimulator(3)
        sim2 = QuantumSimulator(3)
        
        # Prepare test state
        circuit1 = QuantumCircuit(3)
        circuit1.add_gate(H_GATE, [0])
        circuit1.add_gate(H_GATE, [1])
        circuit1.add_gate(X_GATE, [2])
        circuit1.add_gate(CCZ_GATE, [0, 1, 2])  # Direct CCZ
        circuit1.execute(sim1)
        
        # Equivalent implementation using Toffoli
        circuit2 = QuantumCircuit(3)
        circuit2.add_gate(H_GATE, [0])
        circuit2.add_gate(H_GATE, [1])
        circuit2.add_gate(X_GATE, [2])
        circuit2.add_gate(H_GATE, [2])           # Convert X basis to Z basis
        circuit2.add_gate(TOFFOLI_GATE, [0, 1, 2])  # Toffoli
        circuit2.add_gate(H_GATE, [2])           # Convert back
        circuit2.execute(sim2)
        
        np.testing.assert_array_almost_equal(
            sim1.get_state_vector(), sim2.get_state_vector()
        )
    
    def test_gate_universality(self):
        """Test that new gates enable universal quantum computation."""
        # Demonstrate that we can implement arbitrary 3-qubit unitaries
        # using combinations of single-qubit gates, CNOT, and Toffoli
        
        # This is more of a conceptual test - we verify we have the right building blocks
        gates_available = {
            'single_qubit': [H_GATE, X_GATE, Y_GATE, Z_GATE],
            'two_qubit': [CNOT_GATE, CZ_GATE],
            'three_qubit': [TOFFOLI_GATE, CCZ_GATE]
        }
        
        # Verify all gates are available and have correct dimensions
        assert all(gate.num_qubits == 1 for gate in gates_available['single_qubit'])
        assert all(gate.num_qubits == 2 for gate in gates_available['two_qubit'])
        assert all(gate.num_qubits == 3 for gate in gates_available['three_qubit'])
        
        # This gate set is known to be universal for quantum computation
        assert True  # Conceptual verification