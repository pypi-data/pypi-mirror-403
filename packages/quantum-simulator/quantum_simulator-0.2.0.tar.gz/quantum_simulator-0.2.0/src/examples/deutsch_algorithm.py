"""
Deutsch's Algorithm Example

This example demonstrates Deutsch's Algorithm, one of the first quantum algorithms
to show a speedup over classical computation. The algorithm determines whether
a black-box function f: {0,1} → {0,1} is constant (f(0)=f(1)) or balanced 
(f(0)≠f(1)) using only one function evaluation, while any classical algorithm
would need two evaluations.

What this example does:
1. Creates a 2-qubit quantum system (1 input qubit + 1 ancilla qubit)
2. Initializes the ancilla qubit to |1⟩ and applies Hadamard to both qubits
3. Applies the oracle function (either constant or balanced)
4. Applies Hadamard to the input qubit
5. Measures the input qubit: 0 = constant function, 1 = balanced function

The quantum advantage comes from quantum superposition allowing us to evaluate
the function on both inputs simultaneously through interference effects.
"""

from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import H_GATE, X_GATE, CNOT_GATE, Z_GATE
import numpy as np


def create_constant_zero_oracle() -> QuantumCircuit:
    """
    Create an oracle for the constant function f(x) = 0.
    This oracle does nothing (identity operation).
    
    Returns:
        QuantumCircuit: Oracle circuit for constant function f(x) = 0
    """
    circuit = QuantumCircuit(2)
    # Identity - do nothing
    return circuit


def create_constant_one_oracle() -> QuantumCircuit:
    """
    Create an oracle for the constant function f(x) = 1.
    This oracle flips the ancilla qubit regardless of input.
    
    Returns:
        QuantumCircuit: Oracle circuit for constant function f(x) = 1
    """
    circuit = QuantumCircuit(2)
    # Flip the ancilla qubit (qubit 1)
    circuit.add_gate(X_GATE, [1])
    return circuit


def create_balanced_identity_oracle() -> QuantumCircuit:
    """
    Create an oracle for the balanced function f(x) = x.
    This oracle copies the input to the ancilla qubit.
    
    Returns:
        QuantumCircuit: Oracle circuit for balanced function f(x) = x
    """
    circuit = QuantumCircuit(2)
    # CNOT with input qubit (0) as control, ancilla qubit (1) as target
    circuit.add_gate(CNOT_GATE, [0, 1])
    return circuit


def create_balanced_negation_oracle() -> QuantumCircuit:
    """
    Create an oracle for the balanced function f(x) = 1-x (NOT x).
    This oracle flips the ancilla qubit when input is 0.
    
    Returns:
        QuantumCircuit: Oracle circuit for balanced function f(x) = 1-x
    """
    circuit = QuantumCircuit(2)
    # First flip input, then CNOT, then flip input back
    circuit.add_gate(X_GATE, [0])      # Flip input qubit
    circuit.add_gate(CNOT_GATE, [0, 1])  # Conditional flip of ancilla
    circuit.add_gate(X_GATE, [0])      # Flip input qubit back
    return circuit


def deutsch_algorithm(oracle: QuantumCircuit, oracle_name: str) -> bool:
    """
    Execute Deutsch's Algorithm with the given oracle.
    
    Args:
        oracle: The oracle circuit implementing the black-box function
        oracle_name: Name of the oracle for display purposes
        
    Returns:
        bool: True if function is constant, False if balanced
    """
    print(f"\nTesting Deutsch's Algorithm with {oracle_name}")
    print("-" * 50)
    
    # Step 1: Initialize 2-qubit system
    sim = QuantumSimulator(2)
    print(f"Initial state |00⟩: {sim.get_state_vector()}")
    
    # Step 2: Prepare ancilla qubit in |1⟩ state
    circuit = QuantumCircuit(2)
    circuit.add_gate(X_GATE, [1])  # Flip ancilla to |1⟩
    sim.execute_circuit(circuit)
    print(f"After X on ancilla: {sim.get_state_vector()}")
    
    # Step 3: Apply Hadamard gates to both qubits
    circuit = QuantumCircuit(2)
    circuit.add_gate(H_GATE, [0])  # Hadamard on input qubit
    circuit.add_gate(H_GATE, [1])  # Hadamard on ancilla qubit
    sim.execute_circuit(circuit)
    print(f"After Hadamard gates: {sim.get_state_vector()}")
    
    # Step 4: Apply the oracle
    sim.execute_circuit(oracle)
    print(f"After oracle: {sim.get_state_vector()}")
    
    # Step 5: Apply Hadamard to input qubit
    circuit = QuantumCircuit(2)
    circuit.add_gate(H_GATE, [0])
    sim.execute_circuit(circuit)
    print(f"After final Hadamard: {sim.get_state_vector()}")
    
    # Step 6: Measure input qubit (qubit 0)
    measurement_results = []
    for i in range(10):  # Take multiple measurements to verify
        sim_copy = QuantumSimulator(2)
        # Re-execute the entire algorithm
        circuit = QuantumCircuit(2)
        circuit.add_gate(X_GATE, [1])
        circuit.add_gate(H_GATE, [0])
        circuit.add_gate(H_GATE, [1])
        sim_copy.execute_circuit(circuit)
        sim_copy.execute_circuit(oracle)
        circuit = QuantumCircuit(2)
        circuit.add_gate(H_GATE, [0])
        sim_copy.execute_circuit(circuit)
        
        result = sim_copy.measure(0)
        measurement_results.append(result)
    
    result = measurement_results[0]  # All should be the same for this algorithm
    print(f"Measurement results: {measurement_results}")
    print(f"Input qubit measurement: {result}")
    
    # Interpret result
    is_constant = (result == 0)
    function_type = "CONSTANT" if is_constant else "BALANCED"
    print(f"Algorithm result: Function is {function_type}")
    
    return is_constant


def main() -> None:
    """
    Demonstrate Deutsch's Algorithm with different oracle functions.
    
    This function tests the algorithm with four different oracle implementations:
    two constant functions (f(x)=0 and f(x)=1) and two balanced functions 
    (f(x)=x and f(x)=1-x).
    """
    print("Deutsch's Algorithm Demonstration")
    print("=" * 40)
    print("This algorithm determines if a boolean function is constant or balanced")
    print("using only ONE quantum function evaluation (vs. 2 classical evaluations).")
    
    # Test with constant function f(x) = 0
    oracle_0 = create_constant_zero_oracle()
    result_0 = deutsch_algorithm(oracle_0, "Constant f(x) = 0")
    
    # Test with constant function f(x) = 1  
    oracle_1 = create_constant_one_oracle()
    result_1 = deutsch_algorithm(oracle_1, "Constant f(x) = 1")
    
    # Test with balanced function f(x) = x
    oracle_id = create_balanced_identity_oracle()
    result_id = deutsch_algorithm(oracle_id, "Balanced f(x) = x")
    
    # Test with balanced function f(x) = 1-x
    oracle_not = create_balanced_negation_oracle()
    result_not = deutsch_algorithm(oracle_not, "Balanced f(x) = 1-x")
    
    # Summary
    print(f"\n" + "=" * 40)
    print("SUMMARY OF RESULTS:")
    print(f"Constant f(x)=0: {'✓ CORRECT' if result_0 else '✗ WRONG'}")
    print(f"Constant f(x)=1: {'✓ CORRECT' if result_1 else '✗ WRONG'}")
    print(f"Balanced f(x)=x: {'✓ CORRECT' if not result_id else '✗ WRONG'}")
    print(f"Balanced f(x)=1-x: {'✓ CORRECT' if not result_not else '✗ WRONG'}")
    
    print(f"\nQuantum Advantage: Determined function type with 1 evaluation")
    print("(Classical algorithm would need 2 evaluations)")


if __name__ == "__main__":
    main()