"""Test suite for rotation gates (RX, RY, RZ)."""

import pytest
import numpy as np

from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import RX, RY, RZ, X_GATE, Z_GATE


class TestRotationGates:
    """Test rotation gates (RX, RY, RZ)."""
    
    def test_rx_gate_creation(self):
        """Test RX gate creation and properties."""
        theta = np.pi/4
        rx_gate = RX(theta)
        
        assert rx_gate.name == f"RX({theta:.3f})"
        assert rx_gate.num_qubits == 1
        
        # Check matrix elements
        cos_half = np.cos(theta / 2)
        sin_half = np.sin(theta / 2)
        expected = np.array([
            [cos_half, -1j * sin_half],
            [-1j * sin_half, cos_half]
        ], dtype=complex)
        
        np.testing.assert_array_almost_equal(rx_gate.matrix, expected)
    
    def test_rx_special_cases(self):
        """Test RX gate special cases."""
        # RX(0) should be identity
        rx_zero = RX(0)
        identity = np.eye(2, dtype=complex)
        np.testing.assert_array_almost_equal(rx_zero.matrix, identity)
        
        # RX(π) should be equivalent to X gate (up to global phase)
        rx_pi = RX(np.pi)
        # Remove global phase factor for comparison
        rx_normalized = rx_pi.matrix / rx_pi.matrix[0, 1]
        x_normalized = X_GATE.matrix / X_GATE.matrix[0, 1]
        np.testing.assert_array_almost_equal(rx_normalized, x_normalized)
    
    def test_ry_gate_creation(self):
        """Test RY gate creation and properties."""
        theta = np.pi/3
        ry_gate = RY(theta)
        
        assert ry_gate.name == f"RY({theta:.3f})"
        assert ry_gate.num_qubits == 1
        
        # Check matrix elements
        cos_half = np.cos(theta / 2)
        sin_half = np.sin(theta / 2)
        expected = np.array([
            [cos_half, -sin_half],
            [sin_half, cos_half]
        ], dtype=complex)
        
        np.testing.assert_array_almost_equal(ry_gate.matrix, expected)
    
    def test_ry_special_cases(self):
        """Test RY gate special cases."""
        # RY(0) should be identity
        ry_zero = RY(0)
        identity = np.eye(2, dtype=complex)
        np.testing.assert_array_almost_equal(ry_zero.matrix, identity)
        
        # RY(π/2) creates equal superposition
        ry_half_pi = RY(np.pi/2)
        sim = QuantumSimulator(1)
        circuit = QuantumCircuit(1)
        circuit.add_gate(ry_half_pi, [0])
        circuit.execute(sim)
        
        expected = np.array([1.0, 1.0], dtype=complex) / np.sqrt(2)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
    
    def test_rz_gate_creation(self):
        """Test RZ gate creation and properties."""
        theta = np.pi/6
        rz_gate = RZ(theta)
        
        assert rz_gate.name == f"RZ({theta:.3f})"
        assert rz_gate.num_qubits == 1
        
        # Check matrix elements
        exp_neg = np.exp(-1j * theta / 2)
        exp_pos = np.exp(1j * theta / 2)
        expected = np.array([
            [exp_neg, 0],
            [0, exp_pos]
        ], dtype=complex)
        
        np.testing.assert_array_almost_equal(rz_gate.matrix, expected)
    
    def test_rz_special_cases(self):
        """Test RZ gate special cases."""
        # RZ(0) should be identity
        rz_zero = RZ(0)
        identity = np.eye(2, dtype=complex)
        np.testing.assert_array_almost_equal(rz_zero.matrix, identity)
        
        # RZ(π) should be equivalent to Z gate (up to global phase)
        rz_pi = RZ(np.pi)
        # The RZ(π) matrix has extra phase factors compared to Z
        # Check that it gives the same action on basis states
        sim1 = QuantumSimulator(1)
        sim2 = QuantumSimulator(1)
        
        circuit1 = QuantumCircuit(1)
        circuit1.add_gate(Z_GATE, [0])
        circuit1.execute(sim1)
        
        circuit2 = QuantumCircuit(1)
        circuit2.add_gate(rz_pi, [0])
        circuit2.execute(sim2)
        
        # Both should leave |0⟩ unchanged (up to global phase)
        assert abs(sim1.get_state_vector()[0]) == pytest.approx(abs(sim2.get_state_vector()[0]))
    
    def test_rotation_unitarity(self):
        """Test that rotation gates are unitary."""
        angles = [0, np.pi/6, np.pi/4, np.pi/3, np.pi/2, np.pi, 2*np.pi]
        
        for theta in angles:
            rx = RX(theta)
            ry = RY(theta)
            rz = RZ(theta)
            
            identity = np.eye(2, dtype=complex)
            
            # Test unitarity: U†U = I
            np.testing.assert_array_almost_equal(
                rx.matrix.conj().T @ rx.matrix, identity
            )
            np.testing.assert_array_almost_equal(
                ry.matrix.conj().T @ ry.matrix, identity
            )
            np.testing.assert_array_almost_equal(
                rz.matrix.conj().T @ rz.matrix, identity
            )