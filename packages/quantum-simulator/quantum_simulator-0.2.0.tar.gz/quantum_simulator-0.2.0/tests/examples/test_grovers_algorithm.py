"""Test suite for Grover's Algorithm example."""

import pytest
import numpy as np
import sys
import os

# Add src to path for importing examples
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from examples.grovers_algorithm_2_qubit import (
    oracle_mark_11, diffusion_operator, initialize_superposition, run_grovers_algorithm
)
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import H_GATE, CZ_GATE


class TestGroversAlgorithmComponents:
    """Test individual components of Grover's algorithm."""
    
    def test_initialize_superposition(self):
        """Test superposition initialization creates equal amplitudes."""
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        
        initialize_superposition(circuit, 2)
        circuit.execute(sim)
        
        state_vector = sim.get_state_vector()
        expected_amplitude = 1.0 / np.sqrt(4)  # 1/√4 for 2 qubits
        
        # All states should have equal amplitude
        for amplitude in state_vector:
            assert abs(amplitude) == pytest.approx(expected_amplitude, abs=1e-10)
    
    def test_oracle_marks_target_state(self):
        """Test oracle correctly marks the target state |11⟩."""
        # Test oracle on |11⟩ - should flip phase
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        
        # Prepare |11⟩ state
        circuit.add_gate(X_GATE, [0])
        circuit.add_gate(X_GATE, [1])
        circuit.execute(sim)
        
        # Apply oracle
        oracle_circuit = QuantumCircuit(2)
        oracle_mark_11(oracle_circuit)
        oracle_circuit.execute(sim)
        
        # Should have -1 amplitude for |11⟩
        expected = np.array([0.0, 0.0, 0.0, -1.0], dtype=complex)
        np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
    
    def test_oracle_preserves_other_states(self):
        """Test oracle doesn't affect states other than |11⟩."""
        test_states = [
            ([0, 0], [1.0, 0.0, 0.0, 0.0]),  # |00⟩
            ([1, 0], [0.0, 1.0, 0.0, 0.0]),  # |01⟩  
            ([0, 1], [0.0, 0.0, 1.0, 0.0])   # |10⟩
        ]
        
        for input_bits, expected_state in test_states:
            sim = QuantumSimulator(2)
            circuit = QuantumCircuit(2)
            
            # Prepare input state
            if input_bits[0]:
                circuit.add_gate(X_GATE, [0])
            if input_bits[1]:
                circuit.add_gate(X_GATE, [1])
            circuit.execute(sim)
            
            # Apply oracle
            oracle_circuit = QuantumCircuit(2)
            oracle_mark_11(oracle_circuit)
            oracle_circuit.execute(sim)
            
            # State should be unchanged (oracle only affects |11⟩)
            expected = np.array(expected_state, dtype=complex)
            np.testing.assert_array_almost_equal(sim.get_state_vector(), expected)
    
    def test_diffusion_operator_properties(self):
        """Test diffusion operator properties."""
        # Test on equal superposition
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        
        # Create superposition
        initialize_superposition(circuit, 2)
        circuit.execute(sim)
        
        initial_state = sim.get_state_vector().copy()
        
        # Apply diffusion operator
        diffusion_circuit = QuantumCircuit(2)
        diffusion_operator(diffusion_circuit)
        diffusion_circuit.execute(sim)
        
        final_state = sim.get_state_vector()
        
        # For uniform superposition, diffusion should return state with same probabilities
        # (may have global phase difference)
        initial_probs = np.abs(initial_state)**2
        final_probs = np.abs(final_state)**2
        np.testing.assert_array_almost_equal(final_probs, initial_probs, decimal=10)
    
    def test_oracle_is_unitary(self):
        """Test oracle preserves unitarity (probabilities sum to 1)."""
        # Test on random superposition
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        
        # Create arbitrary superposition
        circuit.add_gate(H_GATE, [0])
        circuit.add_gate(RY(np.pi/3), [1])  # Arbitrary rotation
        circuit.execute(sim)
        
        probs_before = np.abs(sim.get_state_vector())**2
        total_prob_before = np.sum(probs_before)
        
        # Apply oracle
        oracle_circuit = QuantumCircuit(2)
        oracle_mark_11(oracle_circuit)
        oracle_circuit.execute(sim)
        
        probs_after = np.abs(sim.get_state_vector())**2
        total_prob_after = np.sum(probs_after)
        
        # Probabilities should be preserved
        assert total_prob_before == pytest.approx(1.0)
        assert total_prob_after == pytest.approx(1.0)
        np.testing.assert_array_almost_equal(probs_before, probs_after)


class TestGroversAlgorithm:
    """Test the complete Grover's algorithm."""
    
    def test_grovers_finds_target_state(self):
        """Test that Grover's algorithm amplifies the target state."""
        sim = QuantumSimulator(2)
        
        # Initialize superposition
        circuit = QuantumCircuit(2)
        initialize_superposition(circuit, 2)
        circuit.execute(sim)
        
        # Apply one Grover iteration
        grover_circuit = QuantumCircuit(2)
        oracle_mark_11(grover_circuit)
        diffusion_operator(grover_circuit)
        grover_circuit.execute(sim)
        
        # Check final state
        final_state = sim.get_state_vector()
        probabilities = np.abs(final_state)**2
        
        # |11⟩ should have highest probability
        target_prob = probabilities[3]  # |11⟩ is at index 3
        
        # For 2-qubit Grover's with 1 iteration, |11⟩ should have ~100% probability
        assert target_prob > 0.9, f"Target probability {target_prob} should be > 0.9"
        
        # Other states should have much lower probability
        for i, prob in enumerate(probabilities[:3]):  # |00⟩, |01⟩, |10⟩
            assert prob < 0.1, f"Non-target state {i} has probability {prob} > 0.1"
    
    def test_grovers_probability_conservation(self):
        """Test that Grover's algorithm conserves total probability."""
        sim = QuantumSimulator(2)
        
        # Initialize and run one Grover iteration
        circuit = QuantumCircuit(2)
        initialize_superposition(circuit, 2)
        circuit.execute(sim)
        
        grover_circuit = QuantumCircuit(2)
        oracle_mark_11(grover_circuit)
        diffusion_operator(grover_circuit)
        grover_circuit.execute(sim)
        
        # Check probability conservation
        probabilities = np.abs(sim.get_state_vector())**2
        total_probability = np.sum(probabilities)
        
        assert total_probability == pytest.approx(1.0, abs=1e-10)
    
    def test_grovers_optimal_iterations(self):
        """Test that one iteration is optimal for 2-qubit case."""
        # For 4 items (2 qubits), optimal iterations ≈ π/4 × √4 ≈ 1.57 ≈ 1
        
        sim1 = QuantumSimulator(2)
        sim2 = QuantumSimulator(2)
        
        # Test 1 iteration
        circuit1 = QuantumCircuit(2)
        initialize_superposition(circuit1, 2)
        circuit1.execute(sim1)
        
        grover1 = QuantumCircuit(2)
        oracle_mark_11(grover1)
        diffusion_operator(grover1)
        grover1.execute(sim1)
        
        prob_1_iter = np.abs(sim1.get_state_vector()[3])**2
        
        # Test 2 iterations
        circuit2 = QuantumCircuit(2)
        initialize_superposition(circuit2, 2)
        circuit2.execute(sim2)
        
        # First iteration
        grover2a = QuantumCircuit(2)
        oracle_mark_11(grover2a)
        diffusion_operator(grover2a)
        grover2a.execute(sim2)
        
        # Second iteration
        grover2b = QuantumCircuit(2)
        oracle_mark_11(grover2b)
        diffusion_operator(grover2b)
        grover2b.execute(sim2)
        
        prob_2_iter = np.abs(sim2.get_state_vector()[3])**2
        
        # 1 iteration should give better results than 2 iterations
        assert prob_1_iter > prob_2_iter, f"1 iter: {prob_1_iter}, 2 iter: {prob_2_iter}"
        assert prob_1_iter > 0.9, f"1 iteration should give >90% success"
    
    def test_grovers_algorithm_execution(self):
        """Test that run_grovers_algorithm executes without errors."""
        # This is more of an integration test
        try:
            # Capture stdout to avoid cluttering test output
            import io
            from contextlib import redirect_stdout
            
            with io.StringIO() as buf:
                with redirect_stdout(buf):
                    run_grovers_algorithm("11")
                
                output = buf.getvalue()
            
            # Check that some expected strings appear in output
            assert "Grover's Algorithm" in output
            assert "SUCCESS" in output or "Found target state" in output
            
        except Exception as e:
            pytest.fail(f"run_grovers_algorithm raised an exception: {e}")


class TestGroversAlgorithmEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_diffusion_operator_on_computational_basis(self):
        """Test diffusion operator on computational basis states."""
        # Test on each computational basis state
        for i in range(4):
            sim = QuantumSimulator(2)
            circuit = QuantumCircuit(2)
            
            # Prepare basis state |i⟩
            if i & 1:
                circuit.add_gate(X_GATE, [0])
            if i & 2:
                circuit.add_gate(X_GATE, [1])
            circuit.execute(sim)
            
            # Apply diffusion operator
            diffusion_circuit = QuantumCircuit(2)
            diffusion_operator(diffusion_circuit)
            diffusion_circuit.execute(sim)
            
            # Result should be valid quantum state
            final_state = sim.get_state_vector()
            total_prob = np.sum(np.abs(final_state)**2)
            assert total_prob == pytest.approx(1.0)
    
    def test_multiple_oracle_applications(self):
        """Test applying oracle multiple times (should return to original)."""
        sim = QuantumSimulator(2)
        circuit = QuantumCircuit(2)
        
        # Create superposition
        initialize_superposition(circuit, 2)
        circuit.execute(sim)
        
        initial_state = sim.get_state_vector().copy()
        
        # Apply oracle twice (should return to original due to phase²= identity)
        oracle_circuit = QuantumCircuit(2)
        oracle_mark_11(oracle_circuit)
        oracle_mark_11(oracle_circuit)  # Apply twice
        oracle_circuit.execute(sim)
        
        final_state = sim.get_state_vector()
        
        # Should be back to original state
        np.testing.assert_array_almost_equal(final_state, initial_state, decimal=10)


# Import required for some tests
from quantum_simulator.gates import X_GATE, RY


if __name__ == "__main__":
    pytest.main([__file__])