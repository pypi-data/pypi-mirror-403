"""Test suite for the GHZ state 3-qubit example script."""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# Import the example script
from src.examples.greenberger_horne_zeilinger_3_qubit import main, demonstrate_ghz_properties


class TestGHZStateExampleScript:
    """Test the GHZ state example script functionality."""
    
    def test_main_function_runs_without_error(self):
        """Test that the main function executes without raising exceptions."""
        try:
            main()
        except Exception as e:
            pytest.fail(f"main() function raised an exception: {e}")
    
    def test_ghz_correlation_in_main(self):
        """Test that main() demonstrates GHZ correlation multiple times."""
        # Test the real behavior by running multiple times and capturing measurements
        correlation_results = []
        
        for _ in range(30):
            # Capture measurement results by patching the measure method
            measurements = []
            
            def capture_measurement(original_method):
                def wrapper(self, qubit):
                    result = original_method(self, qubit)
                    measurements.append(result)
                    return result
                return wrapper
            
            # Import here to avoid issues
            from quantum_simulator import QuantumSimulator
            original_measure = QuantumSimulator.measure
            
            with patch.object(QuantumSimulator, 'measure', capture_measurement(original_measure)):
                main()
            
            # Extract the three measurements
            assert len(measurements) == 3, f"Expected 3 measurements, got {len(measurements)}"
            qubit0_result = measurements[0]
            qubit1_result = measurements[1]
            qubit2_result = measurements[2]
            
            # Verify valid measurements
            assert qubit0_result in [0, 1], f"Invalid qubit 0 result: {qubit0_result}"
            assert qubit1_result in [0, 1], f"Invalid qubit 1 result: {qubit1_result}"
            assert qubit2_result in [0, 1], f"Invalid qubit 2 result: {qubit2_result}"
            
            # Check GHZ correlation (all qubits should have same value)
            correlation_results.append(
                qubit0_result == qubit1_result == qubit2_result
            )
        
        # All measurements should be correlated in GHZ state
        correlated_count = sum(correlation_results)
        total_runs = len(correlation_results)
        
        assert correlated_count == total_runs, (
            f"GHZ correlation failed: only {correlated_count}/{total_runs} "
            f"measurements were correlated. Expected 100% correlation in GHZ state."
        )
    
    @patch('src.examples.greenberger_horne_zeilinger_3_qubit.QuantumSimulator')
    def test_ghz_state_creation_in_main(self, mock_sim_class):
        """Test that main() creates the correct GHZ state."""
        mock_sim = MagicMock()
        mock_sim_class.return_value = mock_sim
        
        # Mock initial state
        mock_sim.get_state_vector.return_value = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        
        # Mock circuit execution to set final state to GHZ state
        def mock_execute(circuit):
            mock_sim.get_state_vector.return_value = np.array([
                1/np.sqrt(2), 0, 0, 0, 0, 0, 0, 1/np.sqrt(2)
            ])
        
        with patch('src.examples.greenberger_horne_zeilinger_3_qubit.QuantumCircuit.execute', side_effect=mock_execute):
            main()
        
        # Verify simulator was created with 3 qubits
        mock_sim_class.assert_called_once_with(3)
        
        # Verify get_state_vector was called (for displaying states)
        assert mock_sim.get_state_vector.call_count >= 1
        
        # Verify measure was called three times (once for each qubit)
        assert mock_sim.measure.call_count == 3
        mock_sim.measure.assert_any_call(0)
        mock_sim.measure.assert_any_call(1)
        mock_sim.measure.assert_any_call(2)
    
    @patch('src.examples.greenberger_horne_zeilinger_3_qubit.QuantumCircuit')
    def test_correct_gates_added_in_main(self, mock_circuit_class):
        """Test that main() adds the correct gates to create GHZ state."""
        mock_circuit = MagicMock()
        mock_circuit_class.return_value = mock_circuit
        
        main()
        
        # Verify circuit was created with 3 qubits
        mock_circuit_class.assert_called_once_with(3)
        
        # Verify correct gates were added
        assert mock_circuit.add_gate.call_count == 3
        
        # Check the gate calls
        calls = mock_circuit.add_gate.call_args_list
        
        # First call should be H gate on qubit 0
        first_call_args = calls[0][0]
        assert first_call_args[0].name == "H"  # H_GATE
        assert first_call_args[1] == [0]  # applied to qubit 0
        
        # Second call should be CNOT gate on qubits [0, 1]
        second_call_args = calls[1][0]
        assert second_call_args[0].name == "CNOT"  # CNOT_GATE
        assert second_call_args[1] == [0, 1]  # applied to qubits 0 and 1
        
        # Third call should be CNOT gate on qubits [0, 2]
        third_call_args = calls[2][0]
        assert third_call_args[0].name == "CNOT"  # CNOT_GATE
        assert third_call_args[1] == [0, 2]  # applied to qubits 0 and 2
        
        # Verify execute was called
        mock_circuit.execute.assert_called_once()
    
    @patch('src.examples.greenberger_horne_zeilinger_3_qubit.QuantumSimulator.measure')
    def test_measurement_correlation_with_mocked_results(self, mock_measure):
        """Test GHZ entanglement using mocked measurement results."""
        # Mock the measure method to return predictable results (all 0s)
        mock_measure.side_effect = [0, 0, 0]  # All qubits measure to 0
        
        main()
        
        # Verify all measurements were called
        assert mock_measure.call_count == 3
        
        # Verify the calls were for qubits 0, 1, and 2
        calls = mock_measure.call_args_list
        assert calls[0][0] == (0,), "First measurement should be for qubit 0"
        assert calls[1][0] == (1,), "Second measurement should be for qubit 1"
        assert calls[2][0] == (2,), "Third measurement should be for qubit 2"
    
    @patch('src.examples.greenberger_horne_zeilinger_3_qubit.QuantumSimulator.measure')
    def test_measurement_correlation_all_ones(self, mock_measure):
        """Test GHZ entanglement with all qubits measuring to 1."""
        # Mock all measurements to return 1
        mock_measure.side_effect = [1, 1, 1]
        
        main()
        
        # Verify all measurements were made
        assert mock_measure.call_count == 3
    
    def test_demonstrate_ghz_properties_function_runs(self):
        """Test that the demonstrate_ghz_properties function executes without error."""
        try:
            demonstrate_ghz_properties()
        except Exception as e:
            pytest.fail(f"demonstrate_ghz_properties() function raised an exception: {e}")


class TestGHZStateExampleIntegration:
    """Integration tests for the complete GHZ state example."""
    
    def test_statistical_ghz_entanglement_demonstration(self):
        """Test that running main() multiple times shows statistical GHZ entanglement."""
        results_000 = 0
        results_111 = 0
        results_invalid = 0
        
        num_runs = 100
        
        for _ in range(num_runs):
            # Capture measurement results by patching
            measurements = []
            
            def capture_measurement(original_method):
                def wrapper(self, qubit):
                    result = original_method(self, qubit)
                    measurements.append(result)
                    return result
                return wrapper
            
            # Patch the measure method to capture results
            from quantum_simulator import QuantumSimulator
            original_measure = QuantumSimulator.measure
            
            with patch.object(QuantumSimulator, 'measure', capture_measurement(original_measure)):
                main()
            
            # Extract the three measurement results
            assert len(measurements) == 3, f"Expected 3 measurements, got {len(measurements)}"
            result0, result1, result2 = measurements[0], measurements[1], measurements[2]
            
            # Count outcomes
            if result0 == 0 and result1 == 0 and result2 == 0:
                results_000 += 1
            elif result0 == 1 and result1 == 1 and result2 == 1:
                results_111 += 1
            else:
                results_invalid += 1
        
        # In a GHZ state, we should only see |000⟩ and |111⟩ outcomes
        assert results_invalid == 0, f"Found {results_invalid} invalid measurements (not all same)"
        
        # Should have roughly equal distribution of |000⟩ and |111⟩
        total_valid = results_000 + results_111
        assert total_valid == num_runs, f"Expected {num_runs} valid measurements, got {total_valid}"
        
        # Allow some statistical variation (30-70% range)
        min_expected = int(0.3 * num_runs)
        max_expected = int(0.7 * num_runs)
        
        assert min_expected <= results_000 <= max_expected, (
            f"Unexpected distribution: {results_000} |000⟩ vs {results_111} |111⟩ outcomes"
        )
    
    def test_ghz_state_vector_properties(self):
        """Test that the GHZ state has the correct mathematical properties."""
        from quantum_simulator import QuantumSimulator, QuantumCircuit
        from quantum_simulator.gates import H_GATE, CNOT_GATE
        
        # Create GHZ state
        sim = QuantumSimulator(3)
        circuit = QuantumCircuit(3)
        
        # Apply GHZ circuit
        circuit.add_gate(H_GATE, [0])
        circuit.add_gate(CNOT_GATE, [0, 1])
        circuit.add_gate(CNOT_GATE, [0, 2])
        circuit.execute(sim)
        
        state_vector = sim.get_state_vector()
        
        # Check GHZ state properties: |GHZ⟩ = (|000⟩ + |111⟩)/√2
        expected_amplitude = 1.0 / np.sqrt(2)
        
        # |000⟩ state (index 0) should have amplitude 1/√2
        assert abs(state_vector[0] - expected_amplitude) < 1e-10, f"Wrong |000⟩ amplitude: {state_vector[0]}"
        
        # |111⟩ state (index 7) should have amplitude 1/√2
        assert abs(state_vector[7] - expected_amplitude) < 1e-10, f"Wrong |111⟩ amplitude: {state_vector[7]}"
        
        # All other amplitudes should be 0
        for i in [1, 2, 3, 4, 5, 6]:
            assert abs(state_vector[i]) < 1e-10, f"Non-zero amplitude at index {i}: {state_vector[i]}"
        
        # Verify normalization
        total_probability = sum(abs(amplitude)**2 for amplitude in state_vector)
        assert abs(total_probability - 1.0) < 1e-10, f"State not normalized: {total_probability}"
    
    def test_demonstrate_ghz_properties_statistical_behavior(self):
        """Test the statistical behavior of the demonstrate_ghz_properties function."""
        # This test ensures the demonstrate_ghz_properties function shows proper correlations
        # We'll capture the measurements made within the function
        
        measurements_captured = []
        
        def capture_measurement(original_method):
            def wrapper(self, qubit):
                result = original_method(self, qubit)
                measurements_captured.append(result)
                return result
            return wrapper
        
        from quantum_simulator import QuantumSimulator
        original_measure = QuantumSimulator.measure
        
        with patch.object(QuantumSimulator, 'measure', capture_measurement(original_measure)):
            demonstrate_ghz_properties()
        
        # The function runs 20 trials with 3 measurements each
        expected_total_measurements = 20 * 3
        assert len(measurements_captured) == expected_total_measurements, (
            f"Expected {expected_total_measurements} measurements, got {len(measurements_captured)}"
        )
        
        # Check that measurements come in groups of 3 with perfect correlation
        for i in range(0, len(measurements_captured), 3):
            qubit0_result = measurements_captured[i]
            qubit1_result = measurements_captured[i+1]
            qubit2_result = measurements_captured[i+2]
            
            # All three qubits should have the same measurement result
            assert qubit0_result == qubit1_result == qubit2_result, (
                f"GHZ correlation failed at trial {i//3 + 1}: "
                f"({qubit0_result}, {qubit1_result}, {qubit2_result})"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])