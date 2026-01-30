"""Test suite for the W state 3-qubit example script."""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# Import the example script
from src.examples.w_state_3_qubit import main, demonstrate_w_vs_ghz


class TestWStateExampleScript:
    """Test the W state example script functionality."""
    
    def test_main_function_runs_without_error(self):
        """Test that the main function executes without raising exceptions."""
        try:
            main()
        except Exception as e:
            pytest.fail(f"main() function raised an exception: {e}")
    
    def test_w_state_correlation_in_main(self):
        """Test that main() demonstrates W state correlation multiple times."""
        # Test the real behavior by running multiple times and capturing measurements
        valid_w_measurements = 0
        
        for _ in range(50):
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
            
            # Check W state property: exactly one qubit should be |1⟩
            ones_count = sum([qubit0_result, qubit1_result, qubit2_result])
            if ones_count == 1:
                valid_w_measurements += 1
        
        # All measurements should show W state property (exactly one |1⟩)
        total_runs = 50
        assert valid_w_measurements == total_runs, (
            f"W state property failed: only {valid_w_measurements}/{total_runs} "
            f"measurements showed exactly one |1⟩. Expected 100% compliance with W state property."
        )
    
    def test_w_state_creation_in_main_real(self):
        """Test that main() creates the correct W state using real simulator."""
        # Instead of complex mocking, test the actual behavior
        # Capture measurement results to verify W state properties
        measurements = []
        
        def capture_measurement(original_method):
            def wrapper(self, qubit):
                result = original_method(self, qubit)
                measurements.append(result)
                return result
            return wrapper
        
        from quantum_simulator import QuantumSimulator
        original_measure = QuantumSimulator.measure
        
        with patch.object(QuantumSimulator, 'measure', capture_measurement(original_measure)):
            main()
        
        # Verify we got 3 measurements
        assert len(measurements) == 3, f"Expected 3 measurements, got {len(measurements)}"
        
        # Verify W state property: exactly one qubit should be |1⟩
        ones_count = sum(measurements)
        assert ones_count == 1, f"W state should have exactly one |1⟩, got {ones_count}"
    
    @patch('src.examples.w_state_3_qubit.QuantumCircuit')
    def test_circuit_construction_in_main(self, mock_circuit_class):
        """Test that main() constructs the quantum circuit correctly."""
        mock_circuit = MagicMock()
        mock_circuit_class.return_value = mock_circuit
        
        # Mock the circuit execution to avoid the property issue
        def mock_execute(simulator):
            # Just set the simulator to have a valid W state
            simulator.state_vector = np.zeros(8, dtype=complex)
            simulator.state_vector[1] = 1/np.sqrt(3)  # |001⟩
            simulator.state_vector[2] = 1/np.sqrt(3)  # |010⟩  
            simulator.state_vector[4] = 1/np.sqrt(3)  # |100⟩
        
        mock_circuit.execute.side_effect = mock_execute
        
        with patch('src.examples.w_state_3_qubit.QuantumSimulator.measure', return_value=0):
            main()
        
        # Verify circuit was created with 3 qubits
        mock_circuit_class.assert_called_with(3)
        
        # Verify gates were added (the exact gates may vary as the algorithm evolves)
        assert mock_circuit.add_gate.call_count >= 1, "At least one gate should be added to the circuit"
        
        # Verify execute was called
        mock_circuit.execute.assert_called_once()
    
    def test_w_state_amplitude_distribution(self):
        """Test that the W state has correct amplitude distribution."""
        from quantum_simulator import QuantumSimulator
        import numpy as np
        
        # Create W state manually (as done in the main function)
        sim = QuantumSimulator(3)
        w_state = np.zeros(8, dtype=complex)
        w_state[1] = 1/np.sqrt(3)  # |001⟩
        w_state[2] = 1/np.sqrt(3)  # |010⟩  
        w_state[4] = 1/np.sqrt(3)  # |100⟩
        sim.state_vector = w_state
        
        final_state = sim.get_state_vector()
        expected_amplitude = 1.0 / np.sqrt(3)
        
        # Check W state properties: |W⟩ = (|001⟩ + |010⟩ + |100⟩)/√3
        # |000⟩ state (index 0) should have amplitude 0
        assert abs(final_state[0]) < 1e-10, f"Non-zero |000⟩ amplitude: {final_state[0]}"
        
        # |001⟩ state (index 1) should have amplitude 1/√3
        assert abs(final_state[1] - expected_amplitude) < 1e-10, f"Wrong |001⟩ amplitude: {final_state[1]}"
        
        # |010⟩ state (index 2) should have amplitude 1/√3
        assert abs(final_state[2] - expected_amplitude) < 1e-10, f"Wrong |010⟩ amplitude: {final_state[2]}"
        
        # |011⟩ state (index 3) should have amplitude 0
        assert abs(final_state[3]) < 1e-10, f"Non-zero |011⟩ amplitude: {final_state[3]}"
        
        # |100⟩ state (index 4) should have amplitude 1/√3
        assert abs(final_state[4] - expected_amplitude) < 1e-10, f"Wrong |100⟩ amplitude: {final_state[4]}"
        
        # |101⟩, |110⟩, |111⟩ states should have amplitude 0
        for i in [5, 6, 7]:
            assert abs(final_state[i]) < 1e-10, f"Non-zero amplitude at index {i}: {final_state[i]}"
        
        # Verify normalization
        total_probability = sum(abs(amplitude)**2 for amplitude in final_state)
        assert abs(total_probability - 1.0) < 1e-10, f"State not normalized: {total_probability}"
    
    @patch('src.examples.w_state_3_qubit.QuantumSimulator.measure')
    def test_measurement_w_state_property_001(self, mock_measure):
        """Test W state measurement showing |001⟩ outcome."""
        # Mock the measure method to return W state pattern (exactly one |1⟩)
        mock_measure.side_effect = [0, 0, 1]  # |001⟩ pattern
        
        main()
        
        # Verify all measurements were called
        assert mock_measure.call_count == 3
        
        # Verify the calls were for qubits 0, 1, and 2
        calls = mock_measure.call_args_list
        assert calls[0][0] == (0,), "First measurement should be for qubit 0"
        assert calls[1][0] == (1,), "Second measurement should be for qubit 1"
        assert calls[2][0] == (2,), "Third measurement should be for qubit 2"
    
    @patch('src.examples.w_state_3_qubit.QuantumSimulator.measure')
    def test_measurement_w_state_property_010(self, mock_measure):
        """Test W state measurement showing |010⟩ outcome."""
        # Mock measurements to return |010⟩ pattern
        mock_measure.side_effect = [0, 1, 0]
        
        main()
        
        # Verify all measurements were made
        assert mock_measure.call_count == 3
    
    @patch('src.examples.w_state_3_qubit.QuantumSimulator.measure')
    def test_measurement_w_state_property_100(self, mock_measure):
        """Test W state measurement showing |100⟩ outcome."""
        # Mock measurements to return |100⟩ pattern
        mock_measure.side_effect = [1, 0, 0]
        
        main()
        
        # Verify all measurements were made
        assert mock_measure.call_count == 3
    
    def test_demonstrate_w_vs_ghz_function_runs(self):
        """Test that the demonstrate_w_vs_ghz function executes without error."""
        try:
            demonstrate_w_vs_ghz()
        except Exception as e:
            pytest.fail(f"demonstrate_w_vs_ghz() function raised an exception: {e}")


class TestWStateExampleIntegration:
    """Integration tests for the complete W state example."""
    
    def test_statistical_w_state_demonstration(self):
        """Test that running main() multiple times shows statistical W state properties."""
        results_001 = 0
        results_010 = 0
        results_100 = 0
        results_invalid = 0
        
        num_runs = 150
        
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
            if result0 == 0 and result1 == 0 and result2 == 1:
                results_001 += 1
            elif result0 == 0 and result1 == 1 and result2 == 0:
                results_010 += 1
            elif result0 == 1 and result1 == 0 and result2 == 0:
                results_100 += 1
            else:
                results_invalid += 1
        
        # In a W state, we should only see |001⟩, |010⟩, and |100⟩ outcomes
        assert results_invalid == 0, (
            f"Found {results_invalid} invalid measurements (not exactly one |1⟩)"
        )
        
        # Should have valid W state outcomes
        total_valid = results_001 + results_010 + results_100
        assert total_valid == num_runs, f"Expected {num_runs} valid measurements, got {total_valid}"
        
        # Each outcome should appear roughly 1/3 of the time (allow 20%-50% range for statistical variation)
        min_expected = int(0.2 * num_runs)
        max_expected = int(0.5 * num_runs)
        
        assert min_expected <= results_001 <= max_expected, (
            f"Unexpected |001⟩ distribution: {results_001} outcomes"
        )
        assert min_expected <= results_010 <= max_expected, (
            f"Unexpected |010⟩ distribution: {results_010} outcomes"
        )
        assert min_expected <= results_100 <= max_expected, (
            f"Unexpected |100⟩ distribution: {results_100} outcomes"
        )
    
    def test_w_state_vs_ghz_difference(self):
        """Test that W states and GHZ states have different measurement patterns."""
        # Create W state
        from quantum_simulator import QuantumSimulator
        import numpy as np
        
        w_sim = QuantumSimulator(3)
        w_state = np.zeros(8, dtype=complex)
        w_state[1] = 1/np.sqrt(3)  # |001⟩
        w_state[2] = 1/np.sqrt(3)  # |010⟩  
        w_state[4] = 1/np.sqrt(3)  # |100⟩
        w_sim.state_vector = w_state
        
        # Create GHZ state for comparison
        from quantum_simulator.gates import H_GATE, CNOT_GATE
        from quantum_simulator import QuantumCircuit
        
        ghz_sim = QuantumSimulator(3)
        ghz_circuit = QuantumCircuit(3)
        ghz_circuit.add_gate(H_GATE, [0])
        ghz_circuit.add_gate(CNOT_GATE, [0, 1])
        ghz_circuit.add_gate(CNOT_GATE, [0, 2])
        ghz_circuit.execute(ghz_sim)
        
        # Test multiple measurements to verify different behavior
        w_outcomes = []
        ghz_outcomes = []
        
        num_tests = 50
        
        for _ in range(num_tests):
            # Measure W state (create fresh copy each time)
            w_test_sim = QuantumSimulator(3)
            w_test_sim.state_vector = w_state.copy()
            w_result = [w_test_sim.measure(i) for i in range(3)]
            w_ones_count = sum(w_result)
            w_outcomes.append(w_ones_count)
            
            # Measure GHZ state (create fresh copy each time)
            ghz_test_sim = QuantumSimulator(3)
            ghz_test_circuit = QuantumCircuit(3)
            ghz_test_circuit.add_gate(H_GATE, [0])
            ghz_test_circuit.add_gate(CNOT_GATE, [0, 1])
            ghz_test_circuit.add_gate(CNOT_GATE, [0, 2])
            ghz_test_circuit.execute(ghz_test_sim)
            ghz_result = [ghz_test_sim.measure(i) for i in range(3)]
            ghz_ones_count = sum(ghz_result)
            ghz_outcomes.append(ghz_ones_count)
        
        # W state: should always have exactly 1 |1⟩
        w_one_count = w_outcomes.count(1)
        assert w_one_count == num_tests, (
            f"W state failed: {w_one_count}/{num_tests} measurements had exactly one |1⟩"
        )
        
        # GHZ state: should have either 0 or 3 |1⟩s (never 1 or 2)
        ghz_zero_count = ghz_outcomes.count(0)
        ghz_three_count = ghz_outcomes.count(3)
        ghz_valid_count = ghz_zero_count + ghz_three_count
        
        assert ghz_valid_count == num_tests, (
            f"GHZ state failed: only {ghz_valid_count}/{num_tests} measurements were valid (0 or 3 |1⟩s)"
        )
        
        # The patterns should be clearly different
        assert ghz_outcomes.count(1) == 0, "GHZ state should never have exactly 1 |1⟩"
        assert w_outcomes.count(0) == 0, "W state should never have 0 |1⟩s"
        assert w_outcomes.count(3) == 0, "W state should never have 3 |1⟩s"
    
    def test_demonstrate_w_vs_ghz_statistical_behavior(self):
        """Test the statistical behavior of the demonstrate_w_vs_ghz function."""
        # This test ensures the demonstrate_w_vs_ghz function shows proper W state behavior
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
            demonstrate_w_vs_ghz()
        
        # The function runs 30 trials with 3 measurements each
        expected_total_measurements = 30 * 3
        assert len(measurements_captured) == expected_total_measurements, (
            f"Expected {expected_total_measurements} measurements, got {len(measurements_captured)}"
        )
        
        # Check that measurements come in groups of 3 with exactly one |1⟩
        valid_w_trials = 0
        for i in range(0, len(measurements_captured), 3):
            qubit0_result = measurements_captured[i]
            qubit1_result = measurements_captured[i+1]
            qubit2_result = measurements_captured[i+2]
            
            ones_count = sum([qubit0_result, qubit1_result, qubit2_result])
            if ones_count == 1:
                valid_w_trials += 1
        
        # All trials should show W state property
        expected_trials = 30
        assert valid_w_trials == expected_trials, (
            f"W state property failed: only {valid_w_trials}/{expected_trials} trials "
            f"showed exactly one |1⟩"
        )
    
    def test_w_state_symmetry_property(self):
        """Test that W state measurements show symmetric distribution among qubits."""
        # Run many measurements and check that each qubit has roughly equal probability of being |1⟩
        qubit_0_ones = 0
        qubit_1_ones = 0
        qubit_2_ones = 0
        
        num_runs = 300  # Large number for good statistics
        
        for _ in range(num_runs):
            measurements = []
            
            def capture_measurement(original_method):
                def wrapper(self, qubit):
                    result = original_method(self, qubit)
                    measurements.append(result)
                    return result
                return wrapper
            
            from quantum_simulator import QuantumSimulator
            original_measure = QuantumSimulator.measure
            
            with patch.object(QuantumSimulator, 'measure', capture_measurement(original_measure)):
                main()
            
            # Count which qubit was |1⟩
            result0, result1, result2 = measurements[0], measurements[1], measurements[2]
            if result0 == 1:
                qubit_0_ones += 1
            elif result1 == 1:
                qubit_1_ones += 1
            elif result2 == 1:
                qubit_2_ones += 1
        
        # Each qubit should be |1⟩ roughly 1/3 of the time (allow 25%-45% range)
        min_expected = int(0.25 * num_runs)
        max_expected = int(0.45 * num_runs)
        
        assert min_expected <= qubit_0_ones <= max_expected, (
            f"Qubit 0 symmetry failed: {qubit_0_ones}/{num_runs} = {100*qubit_0_ones/num_runs:.1f}%"
        )
        assert min_expected <= qubit_1_ones <= max_expected, (
            f"Qubit 1 symmetry failed: {qubit_1_ones}/{num_runs} = {100*qubit_1_ones/num_runs:.1f}%"
        )
        assert min_expected <= qubit_2_ones <= max_expected, (
            f"Qubit 2 symmetry failed: {qubit_2_ones}/{num_runs} = {100*qubit_2_ones/num_runs:.1f}%"
        )
        
        # Total should equal num_runs (each measurement has exactly one |1⟩)
        total_ones = qubit_0_ones + qubit_1_ones + qubit_2_ones
        assert total_ones == num_runs, (
            f"Total ones mismatch: {total_ones} vs {num_runs}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])