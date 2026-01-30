"""
3-Qubit Greenberger-Horne-Zeilinger (GHZ) State Creation Example

This example demonstrates how to create a 3-qubit GHZ state, which is a maximally
entangled quantum state involving three qubits. The GHZ state is a generalization
of the 2-qubit Bell state and exhibits remarkable quantum correlations.

What this example does:
1. Creates a 3-qubit quantum simulator initialized to |000⟩ state
2. Applies a Hadamard gate to the first qubit, creating superposition: (|000⟩ + |100⟩)/√2
3. Applies CNOT gates to entangle all three qubits:
   - CNOT(0→1): Creates (|000⟩ + |110⟩)/√2
   - CNOT(0→2): Creates the final GHZ state |GHZ⟩ = (|000⟩ + |111⟩)/√2
4. Measures all three qubits to demonstrate the unique GHZ correlations

Expected Output:
- Initial state: [1+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j] (representing |000⟩)
- After circuit execution: [0.707+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0+0j, 0.707+0j] (GHZ state)
- Measurement results: All qubits will have the same value (all 0 or all 1)

The GHZ state demonstrates:
- Tripartite entanglement: All three qubits are entangled together
- Non-local correlations: No pair of qubits alone shows maximum correlation
- Violation of local realism: Stronger than Bell inequalities
- Collective measurement effects: The correlations only appear when all qubits are measured

This is a fundamental example in quantum information theory, showing how quantum
entanglement can extend beyond pairs to multiple particles simultaneously.
"""

from quantum_simulator import QuantumSimulator, QuantumCircuit, QuantumGate
from quantum_simulator.gates import H_GATE, X_GATE, CNOT_GATE


def main() -> None:
    """
    Demonstrate GHZ state creation using quantum gates.
    
    This function creates a maximally entangled 3-qubit GHZ state by applying
    a Hadamard gate followed by two CNOT gates, then measures all three qubits.
    """
    print("3-Qubit GHZ State Example")
    print("=" * 30)
    
    # Step 1: Initialize a 3-qubit quantum simulator
    # The simulator starts in the |000⟩ state: [1, 0, 0, 0, 0, 0, 0, 0]
    # This represents all three qubits in the |0⟩ state
    sim = QuantumSimulator(3)
    print(f"Initial state: {sim.get_state_vector()}")
    
    # Step 2: Create a quantum circuit for 3 qubits
    # A circuit is a sequence of quantum gates applied to qubits
    circuit = QuantumCircuit(3)
    
    # Step 3: Add Hadamard gate to qubit 0 (control qubit)
    # H|0⟩ = (|0⟩ + |1⟩)/√2, creating superposition on first qubit
    # This transforms |000⟩ → (|000⟩ + |100⟩)/√2
    circuit.add_gate(H_GATE, [0])  # Hadamard gate on qubit 0
    
    # Step 4: Add first CNOT gate with qubit 0 as control, qubit 1 as target
    # CNOT flips the target qubit if the control qubit is |1⟩
    # This transforms (|000⟩ + |100⟩)/√2 → (|000⟩ + |110⟩)/√2
    circuit.add_gate(CNOT_GATE, [0, 1])  # CNOT gate: control=0, target=1
    
    # Step 5: Add second CNOT gate with qubit 0 as control, qubit 2 as target
    # This creates the final GHZ state by entangling the third qubit
    # This transforms (|000⟩ + |110⟩)/√2 → (|000⟩ + |111⟩)/√2
    # The result is the GHZ state |GHZ⟩, where all three qubits are maximally entangled
    circuit.add_gate(CNOT_GATE, [0, 2])  # CNOT gate: control=0, target=2
    
    print(f"\nCircuit:\n{circuit}")
    
    # Step 6: Execute the complete circuit on the simulator
    # This applies all gates in sequence to transform the quantum state
    circuit.execute(sim)
    print(f"Final state (GHZ): {sim.get_state_vector()}")
    
    # Step 7: Measure all three qubits
    # Measurement collapses the quantum superposition to classical bits
    # Due to GHZ entanglement, all qubits will always have the same measurement result
    # The probability of getting (0,0,0) or (1,1,1) is 50% each
    # The probability of getting any mixed result like (0,1,0) is 0% due to entanglement
    result0 = sim.measure(0)
    result1 = sim.measure(1)
    result2 = sim.measure(2)
    print(f"Measurement results: qubit 0 = {result0}, qubit 1 = {result1}, qubit 2 = {result2}")
    
    # Analyze the measurement pattern
    if result0 == result1 == result2:
        print(f"✓ Perfect GHZ correlation: All qubits measured to {result0}")
        if result0 == 0:
            print("  Collapsed to |000⟩ state")
        else:
            print("  Collapsed to |111⟩ state")
    else:
        print(f"✗ Unexpected result - GHZ state should show perfect correlation!")
    
    # Note: Run this example multiple times to see the random measurement outcomes
    # You'll observe that all three qubits always match (all 0 or all 1)
    # This demonstrates the unique tripartite entanglement of the GHZ state


def demonstrate_ghz_properties() -> None:
    """
    Demonstrate the unique properties of GHZ states through multiple measurements.
    
    This function runs the GHZ state preparation multiple times to show:
    1. Perfect three-way correlation
    2. Statistical distribution of outcomes
    3. Absence of partial correlations
    """
    print("\n" + "=" * 50)
    print("GHZ State Properties Demonstration")
    print("=" * 50)
    
    num_trials = 20
    outcomes_000 = 0
    outcomes_111 = 0
    total_correlations = 0
    
    print(f"Running {num_trials} trials to demonstrate GHZ properties...\n")
    
    for trial in range(num_trials):
        # Create fresh simulator and GHZ state for each trial
        sim = QuantumSimulator(3)
        circuit = QuantumCircuit(3)
        
        # Create GHZ state
        circuit.add_gate(H_GATE, [0])
        circuit.add_gate(CNOT_GATE, [0, 1])
        circuit.add_gate(CNOT_GATE, [0, 2])
        circuit.execute(sim)
        
        # Measure all qubits
        results = [sim.measure(i) for i in range(3)]
        
        print(f"Trial {trial+1:2d}: ({results[0]}, {results[1]}, {results[2]})", end="")
        
        # Check for perfect correlation
        if results[0] == results[1] == results[2]:
            total_correlations += 1
            if results[0] == 0:
                outcomes_000 += 1
                print(" → |000⟩")
            else:
                outcomes_111 += 1
                print(" → |111⟩")
        else:
            print(" → Invalid! (Should not happen in GHZ state)")
    
    # Statistical analysis
    print(f"\nStatistical Results:")
    print(f"Perfect correlations: {total_correlations}/{num_trials} ({100*total_correlations/num_trials:.1f}%)")
    print(f"|000⟩ outcomes: {outcomes_000} ({100*outcomes_000/num_trials:.1f}%)")
    print(f"|111⟩ outcomes: {outcomes_111} ({100*outcomes_111/num_trials:.1f}%)")
    
    if total_correlations == num_trials:
        print("✓ Perfect GHZ entanglement demonstrated!")
    else:
        print("✗ Unexpected behavior detected!")


if __name__ == "__main__":
    main()
    demonstrate_ghz_properties()
