"""Test suite for CCZ (Controlled-Controlled-Z) gate."""

import pytest
import numpy as np

from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import CCZ_GATE, H_GATE, X_GATE


class TestCCZGate:
    """Test CCZ (Controlled-Controlled-Z) gate."""
    
    def test_ccz_matrix(self):
        """Test CCZ gate matrix definition."""
        expected = np.array([
            [1, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, -1]
        ], dtype=complex)
        np.testing.assert_array_almost_equal(CCZ_GATE.matrix, expected)
    
    def test_ccz_properties(self):
        """Test CCZ gate properties."""
        assert CCZ_GATE.name == "CCZ"
        assert CCZ_GATE.num_qubits == 3
        
        # CCZ is diagonal (phase-only)
        diagonal_matrix = np.diag(np.diag(CCZ_GATE.matrix))
        np.testing.assert_array_almost_equal(CCZ_GATE.matrix, diagonal_matrix)
        
        # CCZ is Hermitian and unitary
        np.testing.assert_array_almost_equal(
            CCZ_GATE.matrix.conj().T, CCZ_GATE.matrix
        )
        
        # CCZ is self-inverse
        identity = np.eye(8, dtype=complex)
        np.testing.assert_array_almost_equal(
            CCZ_GATE.matrix @ CCZ_GATE.matrix, identity
        )
    
    def test_ccz_action_on_basis_states(self):
        """Test CCZ gate action - only |111⟩ gets phase flip."""
        # Test all basis states except |111⟩ remain unchanged
        for i in range(7):  # 0 to 6 (excluding 7 which is |111⟩)
            sim = QuantumSimulator(3)
            circuit = QuantumCircuit(3)
            
            # Prepare state |i⟩
            if i & 1: circuit.add_gate(X_GATE, [0])
            if i & 2: circuit.add_gate(X_GATE, [1]) 
            if i & 4: circuit.add_gate(X_GATE, [2])
            
            # Apply CCZ
            circuit.add_gate(CCZ_GATE, [0, 1, 2])
            circuit.execute(sim)
            
            # State should be unchanged
            expected = np.zeros(8, dtype=complex)
            expected[i] = 1.0
            np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
        
        # Test |111⟩ gets phase flip
        sim = QuantumSimulator(3)
        circuit = QuantumCircuit(3)
        circuit.add_gate(X_GATE, [0])  # Prepare |111⟩
        circuit.add_gate(X_GATE, [1])
        circuit.add_gate(X_GATE, [2])
        circuit.add_gate(CCZ_GATE, [0, 1, 2])
        circuit.execute(sim)
        
        expected = np.zeros(8, dtype=complex)
        expected[7] = -1.0  # Phase flip
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
    
    def test_ccz_preserves_populations(self):
        """Test that CCZ preserves all computational basis populations."""
        # Create random superposition state
        sim = QuantumSimulator(3)
        circuit = QuantumCircuit(3)
        
        # Create superposition on all qubits
        circuit.add_gate(H_GATE, [0])
        circuit.add_gate(H_GATE, [1])
        circuit.add_gate(H_GATE, [2])
        
        # Get probabilities before CCZ
        circuit.execute(sim)
        probs_before = np.abs(sim.get_state_vector())**2
        
        # Apply CCZ
        sim.reset()
        circuit.add_gate(CCZ_GATE, [0, 1, 2])
        circuit.execute(sim)
        probs_after = np.abs(sim.get_state_vector())**2
        
        # All probabilities should be preserved (only phases change)
        np.testing.assert_array_almost_equal(probs_before, probs_after)