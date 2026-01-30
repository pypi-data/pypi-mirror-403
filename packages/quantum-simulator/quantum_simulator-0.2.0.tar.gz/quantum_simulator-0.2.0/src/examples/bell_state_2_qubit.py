
"""
2-Qubit Bell State Creation Example

This example demonstrates how to create a quantum Bell state (maximally entangled state)
using the quantum simulator. The example creates an entangled 2-qubit system where
measuring one qubit instantly determines the state of the other qubit.

What this example does:
1. Creates a 2-qubit quantum simulator initialized to |00⟩ state
2. Applies a Hadamard gate to the first qubit, creating superposition: (|00⟩ + |10⟩)/√2
3. Applies a CNOT gate with qubit 0 as control and qubit 1 as target
4. Results in the Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2
5. Measures both qubits to demonstrate entanglement

Expected Output:
- Initial state: [1+0j, 0+0j, 0+0j, 0+0j] (representing |00⟩)
- After circuit execution: [0.707+0j, 0+0j, 0+0j, 0.707+0j] (representing Bell state)
- Measurement results: Both qubits will always have the same value (both 0 or both 1)

This demonstrates quantum entanglement - a fundamental quantum mechanical phenomenon
where particles become correlated such that the quantum state of each particle
cannot be described independently.
"""

from quantum_simulator import QuantumSimulator, QuantumCircuit, QuantumGate
from quantum_simulator.gates import H_GATE, X_GATE, CNOT_GATE


def main() -> None:
    """
    Demonstrate Bell state creation using quantum gates.
    
    This function creates a maximally entangled 2-qubit Bell state by applying
    a Hadamard gate followed by a CNOT gate, then measures the result.
    """
    print("Quantum Simulator Example")
    print("=" * 30)
    
    # Step 1: Initialize a 2-qubit quantum simulator
    # The simulator starts in the |00⟩ state: [1, 0, 0, 0]
    # This represents both qubits in the |0⟩ state
    sim = QuantumSimulator(2)
    print(f"Initial state: {sim.get_state_vector()}")
    
    # Step 2: Create a quantum circuit for 2 qubits
    # A circuit is a sequence of quantum gates applied to qubits
    circuit = QuantumCircuit(2)
    
    # Step 3: Add Hadamard gate to qubit 0
    # H|0⟩ = (|0⟩ + |1⟩)/√2, creating superposition on first qubit
    # This transforms |00⟩ → (|00⟩ + |10⟩)/√2
    circuit.add_gate(H_GATE, [0])  # Hadamard gate on qubit 0
    
    # Step 4: Add CNOT gate with qubit 0 as control, qubit 1 as target
    # CNOT flips the target qubit if the control qubit is |1⟩
    # This transforms (|00⟩ + |10⟩)/√2 → (|00⟩ + |11⟩)/√2
    # The result is the Bell state |Φ+⟩, where both qubits are maximally entangled
    circuit.add_gate(CNOT_GATE, [0, 1])  # CNOT gate with control=0, target=1
    
    print(f"\nCircuit:\n{circuit}")
    
    # Step 5: Execute the complete circuit on the simulator
    # This applies all gates in sequence to transform the quantum state
    circuit.execute(sim)
    print(f"Final state: {sim.get_state_vector()}")
    
    # Step 6: Measure both qubits
    # Measurement collapses the quantum superposition to classical bits
    # Due to entanglement, both qubits will always have the same measurement result
    # The probability of getting (0,0) or (1,1) is 50% each
    # The probability of getting (0,1) or (1,0) is 0% due to entanglement
    result0 = sim.measure(0)
    result1 = sim.measure(1)
    print(f"Measurement results: qubit 0 = {result0}, qubit 1 = {result1}")
    
    # Note: Run this example multiple times to see the random measurement outcomes
    # You'll observe that both qubits always match (both 0 or both 1)


if __name__ == "__main__":
    main()
