"""Test suite for Hadamard gate."""

import pytest
import numpy as np

from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import H_GATE, X_GATE


class TestHadamardGate:
    """Test Hadamard gate."""
    
    def test_hadamard_matrix(self):
        """Test Hadamard gate matrix definition."""
        expected = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        np.testing.assert_array_almost_equal(H_GATE.matrix, expected)
    
    def test_hadamard_properties(self):
        """Test Hadamard gate properties."""
        assert H_GATE.name == "H"
        assert H_GATE.num_qubits == 1
        
        # Hadamard is Hermitian and unitary
        np.testing.assert_array_almost_equal(
            H_GATE.matrix.conj().T, H_GATE.matrix
        )
        
        # H² = I (Hadamard is its own inverse)
        identity = np.eye(2, dtype=complex)
        np.testing.assert_array_almost_equal(
            H_GATE.matrix @ H_GATE.matrix, identity
        )
    
    def test_hadamard_superposition(self):
        """Test Hadamard creates superposition."""
        sim = QuantumSimulator(1)
        
        # Test H|0⟩ = (|0⟩ + |1⟩)/√2
        circuit = QuantumCircuit(1)
        circuit.add_gate(H_GATE, [0])
        circuit.execute(sim)
        
        expected = np.array([1.0, 1.0], dtype=complex) / np.sqrt(2)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
        
        # Test H|1⟩ = (|0⟩ - |1⟩)/√2
        sim = QuantumSimulator(1)
        circuit = QuantumCircuit(1)
        circuit.add_gate(X_GATE, [0])  # Prepare |1⟩
        circuit.add_gate(H_GATE, [0])  # Apply H
        circuit.execute(sim)
        
        expected = np.array([1.0, -1.0], dtype=complex) / np.sqrt(2)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)