"""Test suite for Toffoli (CCX) gate."""

import pytest
import numpy as np

from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import TOFFOLI_GATE, CCX_GATE, X_GATE


class TestToffoliGate:
    """Test Toffoli (CCX) gate."""
    
    def test_toffoli_matrix(self):
        """Test Toffoli gate matrix definition."""
        expected = np.array([
            [1, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 0, 1, 0]
        ], dtype=complex)
        np.testing.assert_array_almost_equal(TOFFOLI_GATE.matrix, expected)
    
    def test_toffoli_properties(self):
        """Test Toffoli gate properties."""
        assert TOFFOLI_GATE.name == "Toffoli"
        assert TOFFOLI_GATE.num_qubits == 3
        
        # Toffoli is Hermitian and unitary
        np.testing.assert_array_almost_equal(
            TOFFOLI_GATE.matrix.conj().T, TOFFOLI_GATE.matrix
        )
        
        # Toffoli is self-inverse
        identity = np.eye(8, dtype=complex)
        np.testing.assert_array_almost_equal(
            TOFFOLI_GATE.matrix @ TOFFOLI_GATE.matrix, identity
        )
    
    def test_ccx_alias(self):
        """Test that CCX_GATE is an alias for TOFFOLI_GATE."""
        assert CCX_GATE is TOFFOLI_GATE
        assert CCX_GATE.name == "Toffoli"
        np.testing.assert_array_almost_equal(CCX_GATE.matrix, TOFFOLI_GATE.matrix)
    
    def test_toffoli_action_on_basis_states(self):
        """Test Toffoli gate action on all computational basis states."""
        # Note: simulator uses |q2 q1 q0⟩ notation where q0 is LSB
        # Toffoli([0,1,2]) means controls on qubits 0,1 and target on qubit 2
        test_cases = [
            ([0, 0, 0], [1, 0, 0, 0, 0, 0, 0, 0]),  # |000⟩ → |000⟩ (no controls active)
            ([1, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0]),  # |001⟩ → |001⟩ (only one control active)
            ([0, 1, 0], [0, 0, 1, 0, 0, 0, 0, 0]),  # |010⟩ → |010⟩ (only one control active)
            ([1, 1, 0], [0, 0, 0, 0, 0, 0, 0, 1]),  # |011⟩ → |111⟩ (both controls active, flip target 0→1)
            ([0, 0, 1], [0, 0, 0, 0, 1, 0, 0, 0]),  # |100⟩ → |100⟩ (no controls active)
            ([1, 0, 1], [0, 0, 0, 0, 0, 1, 0, 0]),  # |101⟩ → |101⟩ (only one control active)
            ([0, 1, 1], [0, 0, 0, 0, 0, 0, 1, 0]),  # |110⟩ → |110⟩ (only one control active)
            ([1, 1, 1], [0, 0, 0, 1, 0, 0, 0, 0])   # |111⟩ → |011⟩ (both controls active, flip target 1→0)
        ]
        
        for input_state, expected_output in test_cases:
            sim = QuantumSimulator(3)
            circuit = QuantumCircuit(3)
            
            # Prepare input state
            for i, bit in enumerate(input_state):
                if bit == 1:
                    circuit.add_gate(X_GATE, [i])
            
            # Apply Toffoli
            circuit.add_gate(TOFFOLI_GATE, [0, 1, 2])
            circuit.execute(sim)
            
            expected = np.array(expected_output, dtype=complex)
            np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
    
    def test_toffoli_conditional_logic(self):
        """Test Toffoli implements conditional AND logic."""
        # Test that target is flipped only when both controls are |1⟩
        sim = QuantumSimulator(3)

        # Case 1: Both controls |1⟩, target |0⟩ → should flip to |1⟩
        circuit = QuantumCircuit(3)
        circuit.add_gate(X_GATE, [0])  # Control1 = |1⟩
        circuit.add_gate(X_GATE, [1])  # Control2 = |1⟩
        # Target = |0⟩ (default)
        circuit.add_gate(TOFFOLI_GATE, [0, 1, 2])
        circuit.execute(sim)

        # Should be in |111⟩
        assert sim.get_state_vector()[7] == pytest.approx(1.0)

        # Case 2: Apply Toffoli again → should flip back to |011⟩
        circuit = QuantumCircuit(3)  # Create new circuit
        circuit.add_gate(TOFFOLI_GATE, [0, 1, 2])
        circuit.execute(sim)

        # Should be back in |011⟩ (controls still |1⟩, target flipped from |1⟩ to |0⟩)
        assert sim.get_state_vector()[3] == pytest.approx(1.0)