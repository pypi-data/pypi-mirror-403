"""Test suite for CNOT gate."""

import pytest
import numpy as np

from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import CNOT_GATE, H_GATE, X_GATE


class TestCNOTGate:
    """Test CNOT gate."""
    
    def test_cnot_matrix(self):
        """Test CNOT gate matrix definition."""
        expected = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0]
        ], dtype=complex)
        np.testing.assert_array_almost_equal(CNOT_GATE.matrix, expected)
    
    def test_cnot_properties(self):
        """Test CNOT gate properties."""
        assert CNOT_GATE.name == "CNOT"
        assert CNOT_GATE.num_qubits == 2
        
        # CNOT is Hermitian and unitary
        np.testing.assert_array_almost_equal(
            CNOT_GATE.matrix.conj().T, CNOT_GATE.matrix
        )
        
        identity = np.eye(4, dtype=complex)
        np.testing.assert_array_almost_equal(
            CNOT_GATE.matrix.conj().T @ CNOT_GATE.matrix, identity
        )
    
    def test_cnot_action(self):
        """Test CNOT gate action on basis states."""
        sim = QuantumSimulator(2)
        
        # Test CNOT|00⟩ = |00⟩
        circuit = QuantumCircuit(2)
        circuit.add_gate(CNOT_GATE, [0, 1])
        circuit.execute(sim)
        
        expected = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
        
        # Test CNOT|01⟩ = |11⟩ (control=0 is 1, so flip target=1)
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        circuit.add_gate(X_GATE, [0])  # Prepare |01⟩
        circuit.add_gate(CNOT_GATE, [0, 1])
        circuit.execute(sim)
        
        expected = np.array([0.0, 0.0, 0.0, 1.0], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
    
    def test_bell_state_creation(self):
        """Test Bell state creation with CNOT."""
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        
        # Create Bell state: H⊗I then CNOT
        circuit.add_gate(H_GATE, [0])
        circuit.add_gate(CNOT_GATE, [0, 1])
        circuit.execute(sim)
        
        # Should be (|00⟩ + |11⟩)/√2
        expected = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / np.sqrt(2)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)