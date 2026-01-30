"""Test suite for the Bell state 2-qubit example script."""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# Import the example script
from src.examples.bell_state_2_qubit import main


class TestBellStateExampleScript:
    """Test the Bell state example script functionality."""
    
    def test_main_function_runs_without_error(self):
        """Test that the main function executes without raising exceptions."""
        try:
            main()
        except Exception as e:
            pytest.fail(f"main() function raised an exception: {e}")
    
    def test_entanglement_correlation_in_main(self):
        """Test that main() demonstrates entanglement correlation multiple times."""
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
            
            # Extract the two measurements
            assert len(measurements) == 2, f"Expected 2 measurements, got {len(measurements)}"
            qubit0_result = measurements[0]
            qubit1_result = measurements[1]
            
            # Verify valid measurements
            assert qubit0_result in [0, 1], f"Invalid qubit 0 result: {qubit0_result}"
            assert qubit1_result in [0, 1], f"Invalid qubit 1 result: {qubit1_result}"
            
            # Check correlation (should always match in Bell state)
            correlation_results.append(qubit0_result == qubit1_result)
        
        # All measurements should be correlated in Bell state
        correlated_count = sum(correlation_results)
        total_runs = len(correlation_results)
        
        assert correlated_count == total_runs, (
            f"Entanglement correlation failed: only {correlated_count}/{total_runs} "
            f"measurements were correlated. Expected 100% correlation in Bell state."
        )
    
    @patch('src.examples.bell_state_2_qubit.QuantumSimulator')
    def test_bell_state_creation_in_main(self, mock_sim_class):
        """Test that main() creates the correct Bell state."""
        mock_sim = MagicMock()
        mock_sim_class.return_value = mock_sim
        
        # Mock initial state
        mock_sim.get_state_vector.return_value = np.array([1.0, 0.0, 0.0, 0.0])
        
        # Mock circuit execution to set final state to Bell state
        def mock_execute(circuit):
            mock_sim.get_state_vector.return_value = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)])
        
        with patch('src.examples.bell_state_2_qubit.QuantumCircuit.execute', side_effect=mock_execute):
            main()
        
        # Verify simulator was created with 2 qubits
        mock_sim_class.assert_called_once_with(2)
        
        # Verify get_state_vector was called (for displaying states)
        assert mock_sim.get_state_vector.call_count >= 1
        
        # Verify measure was called twice (once for each qubit)
        assert mock_sim.measure.call_count == 2
        mock_sim.measure.assert_any_call(0)
        mock_sim.measure.assert_any_call(1)
    
    @patch('src.examples.bell_state_2_qubit.QuantumCircuit')
    def test_correct_gates_added_in_main(self, mock_circuit_class):
        """Test that main() adds the correct gates to create Bell state."""
        mock_circuit = MagicMock()
        mock_circuit_class.return_value = mock_circuit
        
        main()
        
        # Verify circuit was created with 2 qubits
        mock_circuit_class.assert_called_once_with(2)
        
        # Verify correct gates were added
        assert mock_circuit.add_gate.call_count == 2
        
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
        
        # Verify execute was called
        mock_circuit.execute.assert_called_once()
    
    @patch('src.examples.bell_state_2_qubit.QuantumSimulator.measure')
    def test_measurement_correlation_with_mocked_results(self, mock_measure):
        """Test entanglement using mocked measurement results."""
        # Mock the measure method to return predictable results
        mock_measure.side_effect = [0, 0]  # Both qubits measure to 0
        
        main()
        
        # Verify both measurements were called
        assert mock_measure.call_count == 2
        
        # Verify the calls were for qubits 0 and 1
        calls = mock_measure.call_args_list
        assert calls[0][0] == (0,), "First measurement should be for qubit 0"
        assert calls[1][0] == (1,), "Second measurement should be for qubit 1"
    
    @patch('src.examples.bell_state_2_qubit.QuantumSimulator.measure')
    def test_measurement_correlation_both_ones(self, mock_measure):
        """Test entanglement with both qubits measuring to 1."""
        # Mock both measurements to return 1
        mock_measure.side_effect = [1, 1]
        
        main()
        
        # Verify both measurements were made
        assert mock_measure.call_count == 2


class TestBellStateExampleIntegration:
    """Integration tests for the complete Bell state example."""
    
    def test_statistical_entanglement_demonstration(self):
        """Test that running main() multiple times shows statistical entanglement."""
        results_00 = 0
        results_11 = 0
        results_01 = 0
        results_10 = 0
        
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
            
            # Extract the two measurement results
            assert len(measurements) == 2, f"Expected 2 measurements, got {len(measurements)}"
            result0, result1 = measurements[0], measurements[1]
            
            # Count outcomes
            if result0 == 0 and result1 == 0:
                results_00 += 1
            elif result0 == 1 and result1 == 1:
                results_11 += 1
            elif result0 == 0 and result1 == 1:
                results_01 += 1
            elif result0 == 1 and result1 == 0:
                results_10 += 1
        
        # In a Bell state, we should only see |00⟩ and |11⟩ outcomes
        assert results_01 == 0, f"Found {results_01} invalid |01⟩ measurements"
        assert results_10 == 0, f"Found {results_10} invalid |10⟩ measurements"
        
        # Should have roughly equal distribution of |00⟩ and |11⟩
        total_valid = results_00 + results_11
        assert total_valid == num_runs, f"Expected {num_runs} valid measurements, got {total_valid}"
        
        # Allow some statistical variation (30-70% range)
        min_expected = int(0.3 * num_runs)
        max_expected = int(0.7 * num_runs)
        
        assert min_expected <= results_00 <= max_expected, (
            f"Unexpected distribution: {results_00} |00⟩ vs {results_11} |11⟩ outcomes"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])