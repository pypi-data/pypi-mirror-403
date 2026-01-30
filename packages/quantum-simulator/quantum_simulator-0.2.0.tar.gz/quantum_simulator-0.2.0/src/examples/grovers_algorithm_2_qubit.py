"""
Grover's Algorithm - 2-Qubit Search Example

This example demonstrates Grover's quantum search algorithm, which can search
an unsorted database quadratically faster than classical algorithms.
For N items, classical search takes O(N) time, while Grover's algorithm takes O(√N).

What this example does:
1. Creates a 2-qubit quantum system (4 possible states: |00⟩, |01⟩, |10⟩, |11⟩)
2. Initializes all states in equal superposition using Hadamard gates
3. Applies the oracle function to mark the target item (let's mark |11⟩)
4. Applies the diffusion operator (amplitude amplification)
5. Measures the result to find the marked item with high probability

The Oracle:
- Marks the target state |11⟩ by flipping its phase
- Uses controlled-Z gates to implement the phase oracle
- For 2-qubits marking |11⟩: CZ(qubit0, qubit1) flips phase of |11⟩

The Diffusion Operator:
- Reflects amplitudes around their average
- Implemented as: H⊗H → X⊗X → CZ → X⊗X → H⊗H
- This amplifies the marked state and reduces unmarked states

Expected Output:
- Initial superposition: equal amplitudes for all 4 states
- After 1 Grover iteration: |11⟩ has ~100% probability for 2-qubit case
- Measurement: Should find the marked item |11⟩ with high probability

For 2 qubits, exactly 1 iteration gives optimal results.
For N items, optimal iterations ≈ π/4 × √N.
"""

import numpy as np
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import H_GATE, X_GATE, Z_GATE, CZ_GATE


def oracle_mark_11(circuit: QuantumCircuit) -> None:
    """
    Oracle function that marks the state |11⟩ by flipping its phase.
    
    This oracle uses a controlled-Z gate which flips the phase of |11⟩
    while leaving other states unchanged.
    
    Args:
        circuit: The quantum circuit to add the oracle to
    """
    # CZ gate flips phase of |11⟩: |11⟩ → -|11⟩
    circuit.add_gate(CZ_GATE, [0, 1])


def diffusion_operator(circuit: QuantumCircuit) -> None:
    """
    Grover diffusion operator (amplitude amplification about average).
    
    The diffusion operator reflects all amplitudes around their average.
    It's implemented as the inversion about average transformation:
    2|s⟩⟨s| - I, where |s⟩ is the uniform superposition state.
    
    For 2 qubits: H⊗H → X⊗X → CZ → X⊗X → H⊗H
    
    Args:
        circuit: The quantum circuit to add the diffusion operator to
    """
    # Step 1: Transform back to computational basis
    circuit.add_gate(H_GATE, [0])
    circuit.add_gate(H_GATE, [1])
    
    # Step 2: Flip all qubits (X gates)
    circuit.add_gate(X_GATE, [0])
    circuit.add_gate(X_GATE, [1])
    
    # Step 3: Apply controlled-Z to flip phase of |11⟩ (now |00⟩ after X gates)
    circuit.add_gate(CZ_GATE, [0, 1])
    
    # Step 4: Flip all qubits back (X gates)
    circuit.add_gate(X_GATE, [0])
    circuit.add_gate(X_GATE, [1])
    
    # Step 5: Transform back to superposition basis
    circuit.add_gate(H_GATE, [0])
    circuit.add_gate(H_GATE, [1])


def initialize_superposition(circuit: QuantumCircuit, num_qubits: int) -> None:
    """
    Initialize all qubits in equal superposition.
    
    Applies Hadamard gates to all qubits to create the uniform superposition:
    |s⟩ = (1/√N) Σ|x⟩ for all possible states x
    
    Args:
        circuit: The quantum circuit to add initialization to
        num_qubits: Number of qubits in the system
    """
    for qubit in range(num_qubits):
        circuit.add_gate(H_GATE, [qubit])


def run_grovers_algorithm(target_state: str = "11") -> None:
    """
    Execute Grover's algorithm to search for a marked item.
    
    Args:
        target_state: Binary string representing the target state (default: "11")
    """
    print("Grover's Algorithm - 2-Qubit Search")
    print("=" * 40)
    print(f"Searching for target state: |{target_state}⟩")
    print()
    
    # Step 1: Initialize 2-qubit quantum simulator
    num_qubits = 2
    sim = QuantumSimulator(num_qubits)
    print(f"Initial state |00⟩: {sim.get_state_vector()}")
    
    # Step 2: Create quantum circuit and initialize superposition
    circuit = QuantumCircuit(num_qubits)
    initialize_superposition(circuit, num_qubits)
    circuit.execute(sim)
    
    print(f"After initialization (equal superposition):")
    state_vector = sim.get_state_vector()
    print(f"  State vector: {state_vector}")
    print(f"  |00⟩: {abs(state_vector[0])**2:.3f}")
    print(f"  |01⟩: {abs(state_vector[1])**2:.3f}")  
    print(f"  |10⟩: {abs(state_vector[2])**2:.3f}")
    print(f"  |11⟩: {abs(state_vector[3])**2:.3f}")
    print()
    
    # Step 3: Apply Grover iteration (oracle + diffusion)
    # For 2 qubits (4 items), optimal iterations = π/4 × √4 ≈ 1.57 ≈ 1
    print("Applying Grover iteration...")
    
    # Create new circuit for the iteration
    grover_circuit = QuantumCircuit(num_qubits)
    
    # Apply oracle (marks target state |11⟩)
    oracle_mark_11(grover_circuit)
    
    # Apply diffusion operator (amplitude amplification)
    diffusion_operator(grover_circuit)
    
    # Execute the Grover iteration
    grover_circuit.execute(sim)
    
    # Step 4: Analyze results
    print("After 1 Grover iteration:")
    final_state = sim.get_state_vector()
    print(f"  State vector: {final_state}")
    
    # Calculate probabilities
    probabilities = np.abs(final_state)**2
    print(f"  Probabilities:")
    print(f"    |00⟩: {probabilities[0]:.3f}")
    print(f"    |01⟩: {probabilities[1]:.3f}")
    print(f"    |10⟩: {probabilities[2]:.3f}")
    print(f"    |11⟩: {probabilities[3]:.3f}")
    
    # Find the most probable state
    max_prob_index = np.argmax(probabilities)
    max_probability = probabilities[max_prob_index]
    
    # Convert index to binary string
    found_state = format(max_prob_index, f'0{num_qubits}b')
    
    print(f"\nSearch Result:")
    print(f"  Most probable state: |{found_state}⟩")
    print(f"  Probability: {max_probability:.3f}")
    
    if found_state == target_state:
        print(f"  ✅ SUCCESS! Found target state |{target_state}⟩")
    else:
        print(f"  ❌ Target |{target_state}⟩ not found")
    
    # Step 5: Simulate multiple measurements
    print(f"\nSimulating 100 measurements:")
    measurements = {f"|{format(i, f'0{num_qubits}b')}⟩": 0 for i in range(2**num_qubits)}
    
    for _ in range(100):
        # Simple measurement simulation based on probabilities
        rand = np.random.random()
        cumulative_prob = 0
        for i, prob in enumerate(probabilities):
            cumulative_prob += prob
            if rand <= cumulative_prob:
                state_str = f"|{format(i, f'0{num_qubits}b')}⟩"
                measurements[state_str] += 1
                break
    
    for state, count in measurements.items():
        if count > 0:
            print(f"  {state}: {count} times ({count}%)")


def main() -> None:
    """
    Main function demonstrating Grover's algorithm.
    """
    try:
        run_grovers_algorithm("11")
        
        print("\n" + "="*50)
        print("Grover's Algorithm Analysis:")
        print(f"• Classical search: Would need 2-4 queries on average")
        print(f"• Grover's algorithm: Finds answer in 1 iteration")
        print(f"• Speedup: Quadratic improvement (O(√N) vs O(N))")
        print(f"• For larger databases, the advantage becomes more significant")
        
    except Exception as e:
        print(f"Error running Grover's algorithm: {e}")


if __name__ == "__main__":
    main()