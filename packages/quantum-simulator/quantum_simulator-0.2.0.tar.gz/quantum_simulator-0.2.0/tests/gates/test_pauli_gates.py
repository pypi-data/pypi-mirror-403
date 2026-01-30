"""Test suite for Pauli gates (X, Y, Z)."""

import pytest
import numpy as np

from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import X_GATE, Y_GATE, Z_GATE


class TestPauliGates:
    """Test Pauli gates (X, Y, Z)."""
    
    def test_x_gate_matrix(self):
        """Test X gate matrix definition."""
        expected = np.array([[0, 1], [1, 0]], dtype=complex)
        np.testing.assert_array_almost_equal(X_GATE.matrix, expected)
    
    def test_x_gate_properties(self):
        """Test X gate properties."""
        assert X_GATE.name == "X"
        assert X_GATE.num_qubits == 1
        
        # X gate is Hermitian: X† = X
        np.testing.assert_array_almost_equal(
            X_GATE.matrix.conj().T, X_GATE.matrix
        )
        
        # X gate is unitary: X†X = I
        identity = np.eye(2, dtype=complex)
        np.testing.assert_array_almost_equal(
            X_GATE.matrix.conj().T @ X_GATE.matrix, identity
        )
    
    def test_x_gate_action(self):
        """Test X gate action on basis states."""
        sim = QuantumSimulator(1)
        
        # Test X|0⟩ = |1⟩
        sim.reset()
        circuit = QuantumCircuit(1)
        circuit.add_gate(X_GATE, [0])
        circuit.execute(sim)
        
        expected = np.array([0.0, 1.0], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
        
        # Test X|1⟩ = |0⟩ (apply X twice, starting fresh)
        sim.reset()
        circuit = QuantumCircuit(1)
        circuit.add_gate(X_GATE, [0])  # First X: |0⟩ → |1⟩
        circuit.add_gate(X_GATE, [0])  # Second X: |1⟩ → |0⟩
        circuit.execute(sim)
        
        expected = np.array([1.0, 0.0], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
    
    def test_y_gate_matrix(self):
        """Test Y gate matrix definition."""
        expected = np.array([[0, -1j], [1j, 0]], dtype=complex)
        np.testing.assert_array_almost_equal(Y_GATE.matrix, expected)
    
    def test_y_gate_properties(self):
        """Test Y gate properties."""
        assert Y_GATE.name == "Y"
        assert Y_GATE.num_qubits == 1
        
        # Y gate is Hermitian: Y† = Y
        np.testing.assert_array_almost_equal(
            Y_GATE.matrix.conj().T, Y_GATE.matrix
        )
        
        # Y gate is unitary
        identity = np.eye(2, dtype=complex)
        np.testing.assert_array_almost_equal(
            Y_GATE.matrix.conj().T @ Y_GATE.matrix, identity
        )
    
    def test_y_gate_action(self):
        """Test Y gate action on basis states."""
        sim = QuantumSimulator(1)
        
        # Test Y|0⟩ = i|1⟩
        circuit = QuantumCircuit(1)
        circuit.add_gate(Y_GATE, [0])
        circuit.execute(sim)
        
        expected = np.array([0.0, 1j], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
    
    def test_z_gate_matrix(self):
        """Test Z gate matrix definition."""
        expected = np.array([[1, 0], [0, -1]], dtype=complex)
        np.testing.assert_array_almost_equal(Z_GATE.matrix, expected)
    
    def test_z_gate_properties(self):
        """Test Z gate properties."""
        assert Z_GATE.name == "Z"
        assert Z_GATE.num_qubits == 1
        
        # Z gate is Hermitian and unitary
        np.testing.assert_array_almost_equal(
            Z_GATE.matrix.conj().T, Z_GATE.matrix
        )
        
        identity = np.eye(2, dtype=complex)
        np.testing.assert_array_almost_equal(
            Z_GATE.matrix.conj().T @ Z_GATE.matrix, identity
        )
    
    def test_z_gate_action(self):
        """Test Z gate action on basis states."""
        sim = QuantumSimulator(1)
        
        # Test Z|0⟩ = |0⟩
        circuit = QuantumCircuit(1)
        circuit.add_gate(Z_GATE, [0])
        circuit.execute(sim)
        
        expected = np.array([1.0, 0.0], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
        
        # Test Z|1⟩ = -|1⟩
        sim = QuantumSimulator(1)
        circuit = QuantumCircuit(1)
        circuit.add_gate(X_GATE, [0])  # Prepare |1⟩
        circuit.add_gate(Z_GATE, [0])  # Apply Z
        circuit.execute(sim)
        
        expected = np.array([0.0, -1.0], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)