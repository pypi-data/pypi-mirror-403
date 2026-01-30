"""Test suite for RZZ gate (two-qubit rotation around Z⊗Z)."""

import pytest
import numpy as np

from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import RZZ, H_GATE, Z_GATE


class TestRZZGate:
    """Test RZZ gate (two-qubit rotation around Z⊗Z)."""
    
    def test_rzz_gate_creation(self):
        """Test RZZ gate creation and properties."""
        theta = np.pi/4
        rzz_gate = RZZ(theta)
        
        assert rzz_gate.name == f"RZZ({theta:.3f})"
        assert rzz_gate.num_qubits == 2
        
        # Check matrix elements
        exp_neg = np.exp(-1j * theta / 2)
        exp_pos = np.exp(1j * theta / 2)
        expected = np.array([
            [exp_neg, 0, 0, 0],         # |00⟩ → e^(-iθ/2)|00⟩
            [0, exp_pos, 0, 0],         # |01⟩ → e^(iθ/2)|01⟩  
            [0, 0, exp_pos, 0],         # |10⟩ → e^(iθ/2)|10⟩
            [0, 0, 0, exp_neg]          # |11⟩ → e^(-iθ/2)|11⟩
        ], dtype=complex)
        
        np.testing.assert_array_almost_equal(rzz_gate.matrix, expected)
    
    def test_rzz_special_cases(self):
        """Test RZZ gate special cases."""
        # RZZ(0) should be identity
        rzz_zero = RZZ(0)
        identity = np.eye(4, dtype=complex)
        np.testing.assert_array_almost_equal(rzz_zero.matrix, identity)
        
        # RZZ(2π) should be identity (up to global phase)
        rzz_2pi = RZZ(2 * np.pi)
        # The matrix should be -I (global phase of -1)
        expected = -identity
        np.testing.assert_array_almost_equal(rzz_2pi.matrix, expected)
    
    def test_rzz_properties(self):
        """Test RZZ gate mathematical properties."""
        theta = np.pi/3
        rzz_gate = RZZ(theta)
        
        # RZZ should be unitary
        identity = np.eye(4, dtype=complex)
        np.testing.assert_array_almost_equal(
            rzz_gate.matrix.conj().T @ rzz_gate.matrix, identity
        )
        
        # RZZ should be self-inverse when theta = π
        rzz_pi = RZZ(np.pi)
        product = rzz_pi.matrix @ rzz_pi.matrix
        # This gives a global phase of -1, so we expect -I
        expected = -identity
        np.testing.assert_array_almost_equal(product, expected)
    
    def test_rzz_action_on_basis_states(self):
        """Test RZZ gate action on computational basis states."""
        theta = np.pi/4
        rzz_gate = RZZ(theta)
        
        # Test on |00⟩ state
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        circuit.add_gate(rzz_gate, [0, 1])
        circuit.execute(sim)
        
        exp_neg = np.exp(-1j * theta / 2)
        expected = np.array([exp_neg, 0, 0, 0], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
        
        # Test on |11⟩ state
        sim.reset()
        prep_circuit = QuantumCircuit(2)
        prep_circuit.add_gate(Z_GATE, [0])  # This doesn't create |11⟩, let me fix
        # Actually let me use a different approach
        sim.state_vector = np.array([0, 0, 0, 1], dtype=complex)  # |11⟩
        
        circuit = QuantumCircuit(2)  
        circuit.add_gate(rzz_gate, [0, 1])
        circuit.execute(sim)
        
        expected = np.array([0, 0, 0, exp_neg], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
    
    def test_rzz_on_superposition_states(self):
        """Test RZZ gate on superposition states."""
        theta = np.pi/6
        rzz_gate = RZZ(theta)
        
        # Create superposition state (|00⟩ + |11⟩)/√2
        sim = QuantumSimulator(2)
        sim.state_vector = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)], dtype=complex)
        
        circuit = QuantumCircuit(2)
        circuit.add_gate(rzz_gate, [0, 1])
        circuit.execute(sim)
        
        exp_neg = np.exp(-1j * theta / 2)
        expected = np.array([exp_neg/np.sqrt(2), 0, 0, exp_neg/np.sqrt(2)], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
    
    def test_rzz_commutation_properties(self):
        """Test RZZ gate commutation properties."""
        theta1 = np.pi/4
        theta2 = np.pi/3
        
        rzz1 = RZZ(theta1)
        rzz2 = RZZ(theta2)
        
        # RZZ gates should commute with each other
        product1 = rzz1.matrix @ rzz2.matrix
        product2 = rzz2.matrix @ rzz1.matrix
        np.testing.assert_array_almost_equal(product1, product2)
        
        # RZZ should equal RZZ(theta1 + theta2) up to global phase
        rzz_sum = RZZ(theta1 + theta2)
        # Remove global phase difference for comparison
        product1_normalized = product1 / product1[0, 0]
        rzz_sum_normalized = rzz_sum.matrix / rzz_sum.matrix[0, 0]
        np.testing.assert_array_almost_equal(product1_normalized, rzz_sum_normalized)
    
    def test_rzz_inverse(self):
        """Test RZZ gate inverse."""
        theta = np.pi/5
        rzz_gate = RZZ(theta)
        rzz_inv = RZZ(-theta)
        
        # RZZ(θ) @ RZZ(-θ) should be identity
        identity = np.eye(4, dtype=complex)
        product = rzz_gate.matrix @ rzz_inv.matrix
        np.testing.assert_array_almost_equal(product, identity)
    
    def test_rzz_with_different_qubit_ordering(self):
        """Test RZZ gate with different qubit orderings."""
        theta = np.pi/7
        rzz_gate = RZZ(theta)
        
        # Test applying RZZ to qubits [0, 1]
        sim1 = QuantumSimulator(2)
        sim1.state_vector = np.array([1/2, 1/2, 1/2, 1/2], dtype=complex)
        
        circuit1 = QuantumCircuit(2)
        circuit1.add_gate(rzz_gate, [0, 1])
        circuit1.execute(sim1)
        
        # Test applying RZZ to qubits [1, 0] - should give same result for this gate
        sim2 = QuantumSimulator(2)
        sim2.state_vector = np.array([1/2, 1/2, 1/2, 1/2], dtype=complex)
        
        circuit2 = QuantumCircuit(2)
        circuit2.add_gate(rzz_gate, [1, 0])
        circuit2.execute(sim2)
        
        # Results should be the same since RZZ is symmetric
        np.testing.assert_array_almost_equal(sim1.get_state_vector(), sim2.get_state_vector())


if __name__ == "__main__":
    pytest.main([__file__])