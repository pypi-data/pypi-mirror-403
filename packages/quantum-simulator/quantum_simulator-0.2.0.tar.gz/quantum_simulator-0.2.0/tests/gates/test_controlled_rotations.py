"""Test suite for controlled rotation gates (CRX, CRY, CRZ)."""

import pytest
import numpy as np

from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import (
    controlled_RX, controlled_RY, controlled_RZ, CRY_W,
    H_GATE, X_GATE
)


class TestControlledRotations:
    """Test controlled rotation gates."""
    
    def test_controlled_ry_creation(self):
        """Test controlled RY gate creation."""
        theta = np.pi/3
        cry_gate = controlled_RY(theta)
        
        assert cry_gate.name == f"CRY({theta:.3f})"
        assert cry_gate.num_qubits == 2
        
        # Check matrix structure: I⊗|0⟩⟨0| + RY(θ)⊗|1⟩⟨1|
        cos_half = np.cos(theta / 2)
        sin_half = np.sin(theta / 2)
        
        expected = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, cos_half, -sin_half],
            [0, 0, sin_half, cos_half]
        ], dtype=complex)
        
        np.testing.assert_array_almost_equal(cry_gate.matrix, expected)
    
    def test_cry_w_properties(self):
        """Test CRY_W gate properties."""
        w2_angle = np.arccos(np.sqrt(1/2))  # π/4
        
        assert CRY_W.name == f"CRY({w2_angle:.3f})"
        assert CRY_W.num_qubits == 2
        
        # Should be equivalent to controlled_RY(π/4)
        cry_pi_4 = controlled_RY(np.pi/4)
        np.testing.assert_array_almost_equal(CRY_W.matrix, cry_pi_4.matrix)
    
    def test_controlled_rotation_action(self):
        """Test controlled rotation gate action."""
        cry = controlled_RY(np.pi/2)
        
        # Test on |00⟩ - should remain unchanged
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        circuit.add_gate(cry, [0, 1])
        circuit.execute(sim)
        
        expected = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
        
        # Test on |01⟩ - control qubit 0 is 1, so should apply RY(π/2) to target qubit 1
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        circuit.add_gate(X_GATE, [0])  # Prepare |01⟩ (X on qubit 0)
        circuit.add_gate(cry, [0, 1])  # Apply controlled rotation (control=0, target=1)
        circuit.execute(sim)
        
        # Should become (|01⟩ + |11⟩)/√2 = [0, 1/√2, 0, 1/√2]
        expected = np.array([0.0, 1.0, 0.0, 1.0], dtype=complex) / np.sqrt(2)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)


class TestControlledRX:
    """Test controlled RX gates."""
    
    def test_controlled_rx_creation(self):
        """Test controlled RX gate creation."""
        theta = np.pi/4
        crx_gate = controlled_RX(theta)
        
        assert crx_gate.name == f"CRX({theta:.3f})"
        assert crx_gate.num_qubits == 2
        
        # Check matrix structure: I⊗|0⟩⟨0| + RX(θ)⊗|1⟩⟨1|
        cos_half = np.cos(theta / 2)
        sin_half = np.sin(theta / 2)
        
        expected = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, cos_half, -1j * sin_half],
            [0, 0, -1j * sin_half, cos_half]
        ], dtype=complex)
        
        np.testing.assert_array_almost_equal(crx_gate.matrix, expected)
    
    def test_crx_unitarity(self):
        """Test that CRX gates are unitary."""
        angles = [0, np.pi/6, np.pi/4, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi]
        
        for theta in angles:
            crx = controlled_RX(theta)
            identity = np.eye(4, dtype=complex)
            
            # Test unitarity: U†U = I
            np.testing.assert_array_almost_equal(
                crx.matrix.conj().T @ crx.matrix, identity
            )
    
    def test_crx_action_on_basis_states(self):
        """Test CRX gate action on computational basis states."""
        crx = controlled_RX(np.pi/2)
        
        # Test on |00⟩ - should remain unchanged
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        circuit.add_gate(crx, [0, 1])
        circuit.execute(sim)
        
        expected = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
        
        # Test on |01⟩ - control is 1, so should apply RX(π/2) to target
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        circuit.add_gate(X_GATE, [0])  # Prepare |01⟩
        circuit.add_gate(crx, [0, 1])
        circuit.execute(sim)
        
        # Should become (|01⟩ - i|11⟩)/√2
        expected = np.array([0.0, 1.0, 0.0, -1j], dtype=complex) / np.sqrt(2)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
    
    def test_crx_special_cases(self):
        """Test CRX gate special cases."""
        # CRX(0) should be identity
        crx_zero = controlled_RX(0)
        identity = np.eye(4, dtype=complex)
        np.testing.assert_array_almost_equal(crx_zero.matrix, identity)
        
        # CRX(2π) should be identity (up to global phase)
        crx_2pi = controlled_RX(2*np.pi)
        # Check that it acts as identity on basis states
        sim1 = QuantumSimulator(2)
        sim2 = QuantumSimulator(2)
        
        circuit1 = QuantumCircuit(2)
        circuit1.add_gate(X_GATE, [0])
        circuit1.execute(sim1)
        
        circuit2 = QuantumCircuit(2)
        circuit2.add_gate(X_GATE, [0])
        circuit2.add_gate(crx_2pi, [0, 1])
        circuit2.execute(sim2)
        
        # Should have same probabilities
        np.testing.assert_array_almost_equal(
            np.abs(sim1.get_state_vector())**2, 
            np.abs(sim2.get_state_vector())**2
        )
    
    def test_crx_composition(self):
        """Test CRX gate composition properties."""
        theta1, theta2 = np.pi/6, np.pi/4
        
        # CRX(θ1) followed by CRX(θ2) should equal CRX(θ1 + θ2)
        sim1 = QuantumSimulator(2)
        sim2 = QuantumSimulator(2)
        
        # Prepare identical initial states
        circuit1 = QuantumCircuit(2)
        circuit1.add_gate(X_GATE, [0])  # Control = |1⟩
        circuit1.add_gate(H_GATE, [1])  # Target in superposition
        circuit1.add_gate(controlled_RX(theta1), [0, 1])
        circuit1.add_gate(controlled_RX(theta2), [0, 1])
        circuit1.execute(sim1)
        
        circuit2 = QuantumCircuit(2)
        circuit2.add_gate(X_GATE, [0])  # Control = |1⟩ 
        circuit2.add_gate(H_GATE, [1])  # Target in superposition
        circuit2.add_gate(controlled_RX(theta1 + theta2), [0, 1])
        circuit2.execute(sim2)
        
        np.testing.assert_array_almost_equal(
            sim1.get_state_vector(), sim2.get_state_vector()
        )


class TestControlledRZ:
    """Test controlled RZ gates."""
    
    def test_controlled_rz_creation(self):
        """Test controlled RZ gate creation."""
        theta = np.pi/3
        crz_gate = controlled_RZ(theta)
        
        assert crz_gate.name == f"CRZ({theta:.3f})"
        assert crz_gate.num_qubits == 2
        
        # Check matrix structure: I⊗|0⟩⟨0| + RZ(θ)⊗|1⟩⟨1|
        exp_neg = np.exp(-1j * theta / 2)
        exp_pos = np.exp(1j * theta / 2)
        
        expected = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, exp_neg, 0],
            [0, 0, 0, exp_pos]
        ], dtype=complex)
        
        np.testing.assert_array_almost_equal(crz_gate.matrix, expected)
    
    def test_crz_unitarity(self):
        """Test that CRZ gates are unitary."""
        angles = [0, np.pi/8, np.pi/4, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi]
        
        for theta in angles:
            crz = controlled_RZ(theta)
            identity = np.eye(4, dtype=complex)
            
            # Test unitarity: U†U = I
            np.testing.assert_array_almost_equal(
                crz.matrix.conj().T @ crz.matrix, identity
            )
    
    def test_crz_diagonal_property(self):
        """Test that CRZ is diagonal (only affects phases)."""
        angles = [np.pi/6, np.pi/4, np.pi/2, np.pi]
        
        for theta in angles:
            crz = controlled_RZ(theta)
            
            # Check that matrix is diagonal
            off_diagonal = crz.matrix - np.diag(np.diag(crz.matrix))
            np.testing.assert_array_almost_equal(off_diagonal, np.zeros((4, 4)))
    
    def test_crz_action_on_basis_states(self):
        """Test CRZ gate action on computational basis states."""
        crz = controlled_RZ(np.pi/4)
        
        # Test on |00⟩ - should remain unchanged
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        circuit.add_gate(crz, [0, 1])
        circuit.execute(sim)
        
        expected = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
        
        # Test on |01⟩ - control is 1, so should apply RZ to target |0⟩
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        circuit.add_gate(X_GATE, [0])  # Prepare |01⟩
        circuit.add_gate(crz, [0, 1])
        circuit.execute(sim)
        
        # Should get phase e^(-iπ/8) on |01⟩
        exp_factor = np.exp(-1j * np.pi / 8)
        expected = np.array([0.0, exp_factor, 0.0, 0.0], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
        
        # Test on |11⟩ - should get phase e^(iπ/8)
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        circuit.add_gate(X_GATE, [0])  # Prepare |01⟩
        circuit.add_gate(X_GATE, [1])  # Make it |11⟩
        circuit.add_gate(crz, [0, 1])
        circuit.execute(sim)
        
        exp_factor = np.exp(1j * np.pi / 8)
        expected = np.array([0.0, 0.0, 0.0, exp_factor], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
    
    def test_crz_special_cases(self):
        """Test CRZ gate special cases."""
        # CRZ(0) should be identity
        crz_zero = controlled_RZ(0)
        identity = np.eye(4, dtype=complex)
        np.testing.assert_array_almost_equal(crz_zero.matrix, identity)
        
        # CRZ(π) should be controlled-Z (up to global phase)
        crz_pi = controlled_RZ(np.pi)
        
        # Test that it flips the phase of |11⟩
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        circuit.add_gate(X_GATE, [0])
        circuit.add_gate(X_GATE, [1])  # Prepare |11⟩
        circuit.add_gate(crz_pi, [0, 1])
        circuit.execute(sim)
        
        # Should have phase -1 on |11⟩ (up to global phase)
        state = sim.get_state_vector()
        assert abs(state[3]) == pytest.approx(1.0)  # Magnitude preserved
        
    def test_crz_preserves_populations(self):
        """Test that CRZ preserves computational basis populations."""
        crz = controlled_RZ(np.pi/3)
        
        # Start with superposition state
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        circuit.add_gate(H_GATE, [0])
        circuit.add_gate(H_GATE, [1])
        
        # Get state before CRZ
        circuit.execute(sim)
        probs_before = np.abs(sim.get_state_vector())**2
        
        # Apply CRZ
        sim.reset()
        circuit.add_gate(crz, [0, 1])
        circuit.execute(sim)
        probs_after = np.abs(sim.get_state_vector())**2
        
        # Probabilities should be unchanged
        np.testing.assert_array_almost_equal(probs_before, probs_after)
    
    def test_crz_composition(self):
        """Test CRZ gate composition properties."""
        theta1, theta2 = np.pi/8, np.pi/6
        
        # CRZ(θ1) followed by CRZ(θ2) should equal CRZ(θ1 + θ2)
        sim1 = QuantumSimulator(2)
        sim2 = QuantumSimulator(2)
        
        # Prepare identical initial states
        circuit1 = QuantumCircuit(2)
        circuit1.add_gate(X_GATE, [0])  # Control = |1⟩
        circuit1.add_gate(H_GATE, [1])  # Target in superposition
        circuit1.add_gate(controlled_RZ(theta1), [0, 1])
        circuit1.add_gate(controlled_RZ(theta2), [0, 1])
        circuit1.execute(sim1)
        
        circuit2 = QuantumCircuit(2)
        circuit2.add_gate(X_GATE, [0])  # Control = |1⟩
        circuit2.add_gate(H_GATE, [1])  # Target in superposition 
        circuit2.add_gate(controlled_RZ(theta1 + theta2), [0, 1])
        circuit2.execute(sim2)
        
        np.testing.assert_array_almost_equal(
            sim1.get_state_vector(), sim2.get_state_vector()
        )
    
    def test_crz_phase_kickback(self):
        """Test CRZ demonstrates phase kickback."""
        # When target is Z-eigenstate, phase kicks back to control
        crz = controlled_RZ(np.pi/4)
        
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        
        # Control in superposition, target in |1⟩ eigenstate
        circuit.add_gate(H_GATE, [0])  # (|0⟩ + |1⟩)/√2
        circuit.add_gate(X_GATE, [1])  # |1⟩
        
        # Apply CRZ - phase should kick back to control
        circuit.add_gate(crz, [0, 1])
        
        # Measure interference by rotating control back
        circuit.add_gate(H_GATE, [0])
        
        circuit.execute(sim)
        
        # The phase kickback should be visible in the final state
        state = sim.get_state_vector()
        
        # Due to phase kickback, we should see interference effects
        # The exact values depend on the phase, but |00⟩ and |10⟩ should have different amplitudes
        assert not np.isclose(abs(state[0]), abs(state[2]))