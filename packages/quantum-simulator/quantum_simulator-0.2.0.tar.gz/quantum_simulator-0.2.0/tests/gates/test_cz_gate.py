"""Test suite for Controlled-Z gate."""

import pytest
import numpy as np

from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import CZ_GATE, H_GATE, X_GATE


class TestControlledZ:
    """Test Controlled-Z gate."""
    
    def test_cz_matrix(self):
        """Test CZ gate matrix definition."""
        expected = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, -1]
        ], dtype=complex)
        np.testing.assert_array_almost_equal(CZ_GATE.matrix, expected)
    
    def test_cz_properties(self):
        """Test CZ gate properties."""
        assert CZ_GATE.name == "CZ"
        assert CZ_GATE.num_qubits == 2
        
        # CZ is Hermitian and unitary
        np.testing.assert_array_almost_equal(
            CZ_GATE.matrix.conj().T, CZ_GATE.matrix
        )
        
        # CZ is self-inverse (CZ² = I)
        identity = np.eye(4, dtype=complex)
        np.testing.assert_array_almost_equal(
            CZ_GATE.matrix @ CZ_GATE.matrix, identity
        )
    
    def test_cz_symmetry(self):
        """Test CZ gate symmetry (CZ(0,1) = CZ(1,0))."""
        sim1 = QuantumSimulator(2)
        sim2 = QuantumSimulator(2)
        
        # Prepare identical test states
        circuit1 = QuantumCircuit(2)
        circuit1.add_gate(H_GATE, [0])
        circuit1.add_gate(H_GATE, [1])
        circuit1.add_gate(CZ_GATE, [0, 1])  # CZ(control=0, target=1)
        circuit1.execute(sim1)
        
        circuit2 = QuantumCircuit(2)
        circuit2.add_gate(H_GATE, [0])
        circuit2.add_gate(H_GATE, [1])
        circuit2.add_gate(CZ_GATE, [1, 0])  # CZ(control=1, target=0)
        circuit2.execute(sim2)
        
        # Results should be identical due to symmetry
        np.testing.assert_array_almost_equal(
            sim1.get_state_vector(), sim2.get_state_vector()
        )
    
    def test_cz_action_on_basis_states(self):
        """Test CZ gate action on computational basis states."""
        # Test CZ|00⟩ = |00⟩
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        circuit.add_gate(CZ_GATE, [0, 1])
        circuit.execute(sim)
        
        expected = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
        
        # Test CZ|11⟩ = -|11⟩ (phase flip)
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        circuit.add_gate(X_GATE, [0])  # Prepare |11⟩
        circuit.add_gate(X_GATE, [1])
        circuit.add_gate(CZ_GATE, [0, 1])
        circuit.execute(sim)
        
        expected = np.array([0.0, 0.0, 0.0, -1.0], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
    
    def test_cz_preserves_populations(self):
        """Test that CZ preserves computational basis populations."""
        # Start with equal superposition
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        circuit.add_gate(H_GATE, [0])
        circuit.add_gate(H_GATE, [1])
        
        # Get probabilities before CZ
        circuit.execute(sim)
        probs_before = np.abs(sim.get_state_vector())**2
        
        # Apply CZ and check probabilities after
        sim.reset()
        circuit.add_gate(CZ_GATE, [0, 1])
        circuit.execute(sim)
        probs_after = np.abs(sim.get_state_vector())**2
        
        # Probabilities should be preserved (only phases change)
        np.testing.assert_array_almost_equal(probs_before, probs_after)