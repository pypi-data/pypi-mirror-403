"""Test suite for phase gate (single-qubit phase shift)."""

import pytest
import numpy as np

from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import phase_gate, H_GATE, X_GATE, Z_GATE


class TestPhaseGate:
    """Test phase gate (single-qubit phase shift)."""
    
    def test_phase_gate_creation(self):
        """Test phase gate creation and properties."""
        phi = np.pi/4
        p_gate = phase_gate(phi)
        
        assert p_gate.name == f"Phase({phi:.3f})"
        assert p_gate.num_qubits == 1
        
        # Check matrix elements
        expected = np.array([
            [1, 0],
            [0, np.exp(1j * phi)]
        ], dtype=complex)
        
        np.testing.assert_array_almost_equal(p_gate.matrix, expected)
    
    def test_phase_special_cases(self):
        """Test phase gate special cases."""
        # Phase(0) should be identity
        p_zero = phase_gate(0)
        identity = np.eye(2, dtype=complex)
        np.testing.assert_array_almost_equal(p_zero.matrix, identity)
        
        # Phase(π) should be equivalent to Z gate
        p_pi = phase_gate(np.pi)
        np.testing.assert_array_almost_equal(p_pi.matrix, Z_GATE.matrix)
        
        # Phase(π/2) should be the S gate
        p_pi_2 = phase_gate(np.pi/2)
        s_gate = np.array([[1, 0], [0, 1j]], dtype=complex)
        np.testing.assert_array_almost_equal(p_pi_2.matrix, s_gate)
        
        # Phase(π/4) should be the T gate
        p_pi_4 = phase_gate(np.pi/4)
        t_gate = np.array([[1, 0], [0, np.exp(1j * np.pi/4)]], dtype=complex)
        np.testing.assert_array_almost_equal(p_pi_4.matrix, t_gate)
    
    def test_phase_properties(self):
        """Test phase gate mathematical properties."""
        phi = np.pi/3
        p_gate = phase_gate(phi)
        
        # Phase gate should be unitary
        identity = np.eye(2, dtype=complex)
        np.testing.assert_array_almost_equal(
            p_gate.matrix.conj().T @ p_gate.matrix, identity
        )
        
        # Phase gate should be diagonal
        assert np.allclose(p_gate.matrix[0, 1], 0)
        assert np.allclose(p_gate.matrix[1, 0], 0)
        
        # Diagonal elements should be [1, e^(iφ)]
        assert np.allclose(p_gate.matrix[0, 0], 1)
        assert np.allclose(p_gate.matrix[1, 1], np.exp(1j * phi))
    
    def test_phase_action_on_basis_states(self):
        """Test phase gate action on computational basis states."""
        phi = np.pi/5
        p_gate = phase_gate(phi)
        
        # Test on |0⟩ state (should be unchanged)
        sim = QuantumSimulator(1)
        circuit = QuantumCircuit(1)
        circuit.add_gate(p_gate, [0])
        circuit.execute(sim)
        
        expected = np.array([1, 0], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
        
        # Test on |1⟩ state (should acquire phase)
        sim.reset()
        sim.state_vector = np.array([0, 1], dtype=complex)  # |1⟩
        
        circuit = QuantumCircuit(1)
        circuit.add_gate(p_gate, [0])
        circuit.execute(sim)
        
        expected = np.array([0, np.exp(1j * phi)], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
    
    def test_phase_on_superposition_state(self):
        """Test phase gate on superposition state."""
        phi = np.pi/6
        p_gate = phase_gate(phi)
        
        # Create superposition state (|0⟩ + |1⟩)/√2
        sim = QuantumSimulator(1)
        circuit = QuantumCircuit(1)
        circuit.add_gate(H_GATE, [0])  # Creates (|0⟩ + |1⟩)/√2
        circuit.execute(sim)
        
        # Apply phase gate
        circuit = QuantumCircuit(1)
        circuit.add_gate(p_gate, [0])
        circuit.execute(sim)
        
        # Expected: (|0⟩ + e^(iφ)|1⟩)/√2
        expected = np.array([1/np.sqrt(2), np.exp(1j * phi)/np.sqrt(2)], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
    
    def test_phase_commutation_properties(self):
        """Test phase gate commutation properties."""
        phi1 = np.pi/4
        phi2 = np.pi/3
        
        p1 = phase_gate(phi1)
        p2 = phase_gate(phi2)
        
        # Phase gates should commute with each other
        product1 = p1.matrix @ p2.matrix
        product2 = p2.matrix @ p1.matrix
        np.testing.assert_array_almost_equal(product1, product2)
        
        # Phase(φ1) @ Phase(φ2) should equal Phase(φ1 + φ2)
        p_sum = phase_gate(phi1 + phi2)
        np.testing.assert_array_almost_equal(product1, p_sum.matrix)
        
        # Phase should commute with Z gate
        z_p_product = Z_GATE.matrix @ p1.matrix
        p_z_product = p1.matrix @ Z_GATE.matrix
        np.testing.assert_array_almost_equal(z_p_product, p_z_product)
    
    def test_phase_inverse(self):
        """Test phase gate inverse."""
        phi = np.pi/7
        p_gate = phase_gate(phi)
        p_inv = phase_gate(-phi)
        
        # Phase(φ) @ Phase(-φ) should be identity
        identity = np.eye(2, dtype=complex)
        product = p_gate.matrix @ p_inv.matrix
        np.testing.assert_array_almost_equal(product, identity)
    
    def test_phase_powers(self):
        """Test powers of phase gate."""
        phi = np.pi/8
        p_gate = phase_gate(phi)
        
        # Phase(φ)^2 should equal Phase(2φ)
        p_squared = p_gate.matrix @ p_gate.matrix
        p_2phi = phase_gate(2 * phi)
        np.testing.assert_array_almost_equal(p_squared, p_2phi.matrix)
        
        # Phase(π/4)^8 should be identity (2π rotation)
        p_pi_8 = phase_gate(np.pi/4)
        result = np.eye(2, dtype=complex)
        for _ in range(8):
            result = result @ p_pi_8.matrix
        identity = np.eye(2, dtype=complex)
        np.testing.assert_array_almost_equal(result, identity)
    
    def test_phase_with_x_gate(self):
        """Test phase gate interaction with X gate."""
        phi = np.pi/3
        p_gate = phase_gate(phi)
        
        # Test X @ Phase @ X transforms the phase gate
        # This should swap where the phase is applied (from |1⟩ to |0⟩)
        product = X_GATE.matrix @ p_gate.matrix @ X_GATE.matrix
        # The result should be [[e^(iφ), 0], [0, 1]]
        expected = np.array([
            [np.exp(1j * phi), 0],
            [0, 1]
        ], dtype=complex)
        np.testing.assert_array_almost_equal(product, expected)
    
    def test_phase_measurement_invariance(self):
        """Test that phase doesn't affect measurement probabilities."""
        phi = np.pi/2
        p_gate = phase_gate(phi)
        
        # Create superposition state
        sim1 = QuantumSimulator(1)
        circuit = QuantumCircuit(1)
        circuit.add_gate(H_GATE, [0])
        circuit.execute(sim1)
        
        # Apply phase and measure probabilities should be same
        sim2 = QuantumSimulator(1)
        circuit = QuantumCircuit(1)
        circuit.add_gate(H_GATE, [0])
        circuit.add_gate(p_gate, [0])
        circuit.execute(sim2)
        
        # Measurement probabilities should be identical
        probs1 = np.abs(sim1.get_state_vector()) ** 2
        probs2 = np.abs(sim2.get_state_vector()) ** 2
        np.testing.assert_array_almost_equal(probs1, probs2)


if __name__ == "__main__":
    pytest.main([__file__])