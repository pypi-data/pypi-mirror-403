"""Test suite for special gates used in W state construction."""

import pytest
import numpy as np

from quantum_simulator.gates import RY_W1, RY_W2, RY


class TestWStateGates:
    """Test special gates for W state construction."""
    
    def test_ry_w1_properties(self):
        """Test RY_W1 gate properties."""
        expected_angle = np.arccos(np.sqrt(2/3))
        assert RY_W1.name == f"RY({expected_angle:.3f})"
        assert RY_W1.num_qubits == 1
        
        # Check matrix matches expected angle
        cos_half = np.cos(expected_angle / 2)
        sin_half = np.sin(expected_angle / 2)
        expected_matrix = np.array([
            [cos_half, -sin_half],
            [sin_half, cos_half]
        ], dtype=complex)
        
        np.testing.assert_array_almost_equal(RY_W1.matrix, expected_matrix)
    
    def test_ry_w2_properties(self):
        """Test RY_W2 gate properties."""
        expected_angle = np.arccos(np.sqrt(1/2))  # π/4
        assert RY_W2.name == f"RY({expected_angle:.3f})"
        assert RY_W2.num_qubits == 1
        
        # Should be equivalent to RY(π/4)
        ry_pi_4 = RY(np.pi/4)
        np.testing.assert_array_almost_equal(RY_W2.matrix, ry_pi_4.matrix)
    
    def test_w_state_angles_values(self):
        """Test that W state angles have correct numerical values."""
        # RY_W1 angle should be arccos(√(2/3)) ≈ 0.6155 radians
        w1_angle = np.arccos(np.sqrt(2/3))
        assert w1_angle == pytest.approx(0.6155, abs=1e-4)
        
        # RY_W2 angle should be π/4 ≈ 0.7854 radians
        w2_angle = np.arccos(np.sqrt(1/2))
        assert w2_angle == pytest.approx(np.pi/4, abs=1e-10)