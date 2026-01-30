# Toffoli Gate (CCX/CCNOT)

The **Toffoli gate** (also known as CCX or CCNOT) is a three-qubit quantum gate that performs a controlled-controlled-X operation. It applies an X gate to the target qubit only when both control qubits are in the |1⟩ state. The Toffoli gate is fundamental for quantum computing, enabling universal quantum computation and playing a crucial role in algorithms like Grover's search.

## Mathematical Definition

The Toffoli gate is defined by the 8×8 matrix:

$$\text{Toffoli} = \text{CCX} = \begin{pmatrix}
1 & 0 & 0 & 0 & 0 & 0 & 0 & 0 \\
0 & 1 & 0 & 0 & 0 & 0 & 0 & 0 \\
0 & 0 & 1 & 0 & 0 & 0 & 0 & 0 \\
0 & 0 & 0 & 1 & 0 & 0 & 0 & 0 \\
0 & 0 & 0 & 0 & 1 & 0 & 0 & 0 \\
0 & 0 & 0 & 0 & 0 & 1 & 0 & 0 \\
0 & 0 & 0 & 0 & 0 & 0 & 0 & 1 \\
0 & 0 & 0 & 0 & 0 & 0 & 1 & 0
\end{pmatrix}$$

This can be understood as:

$$\text{Toffoli} = |00\rangle\langle 00| \otimes I + |01\rangle\langle 01| \otimes I + |10\rangle\langle 10| \otimes I + |11\rangle\langle 11| \otimes X$$

## Action on Basis States

- $\text{Toffoli}|000\rangle = |000\rangle$ (no change)
- $\text{Toffoli}|001\rangle = |001\rangle$ (no change)
- $\text{Toffoli}|010\rangle = |010\rangle$ (no change)
- $\text{Toffoli}|011\rangle = |011\rangle$ (no change)
- $\text{Toffoli}|100\rangle = |100\rangle$ (no change)
- $\text{Toffoli}|101\rangle = |101\rangle$ (no change)
- $\text{Toffoli}|110\rangle = |111\rangle$ (X applied to target)
- $\text{Toffoli}|111\rangle = |110\rangle$ (X applied to target)

## Quantum Circuit Representation

```
Control1 ──●──
           │
Control2 ──●──
           │
Target   ──⊕──
```

The target qubit is flipped (⊕) only when both control qubits (●) are in state |1⟩.

## Usage in Quantum Simulator

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import H_GATE, X_GATE, TOFFOLI_GATE, CCX_GATE
import numpy as np

# Basic Toffoli gate application
sim = QuantumSimulator(3)
circuit = QuantumCircuit(3)

# Prepare |110⟩ state to see the flip
circuit.add_gate(X_GATE, [0])  # Control1 = |1⟩
circuit.add_gate(X_GATE, [1])  # Control2 = |1⟩
# Target starts as |0⟩

circuit.add_gate(TOFFOLI_GATE, [0, 1, 2])  # Apply Toffoli

circuit.execute(sim)
print(f"Toffoli|110⟩ = {sim.get_state_vector()}")  # Should show |111⟩

# Using the CCX alias
circuit2 = QuantumCircuit(3)
circuit2.add_gate(X_GATE, [0])
circuit2.add_gate(X_GATE, [1])
circuit2.add_gate(CCX_GATE, [0, 1, 2])  # Same as TOFFOLI_GATE

# Demonstrate conditional logic
def conditional_not_demo():
    """Demonstrate conditional NOT logic with Toffoli."""
    sim = QuantumSimulator(3)
    
    # Test all control combinations
    test_cases = [
        ([0, 0, 0], "000"),
        ([0, 0, 1], "001"), 
        ([0, 1, 0], "010"),
        ([0, 1, 1], "011"),
        ([1, 0, 0], "100"),
        ([1, 0, 1], "101"),
        ([1, 1, 0], "110"),  # Only this should flip target
        ([1, 1, 1], "111")   # This should flip target back
    ]
    
    for controls_target, state_name in test_cases:
        sim.reset()
        circuit = QuantumCircuit(3)
        
        # Prepare initial state
        for i, bit in enumerate(controls_target):
            if bit == 1:
                circuit.add_gate(X_GATE, [i])
        
        # Apply Toffoli
        circuit.add_gate(TOFFOLI_GATE, [0, 1, 2])
        circuit.execute(sim)
        
        result_state = sim.get_state_vector()
        print(f"|{state_name}⟩ → {result_state}")

conditional_not_demo()
```

## Key Properties

### Universality for Classical Computation
The Toffoli gate is **universal for classical computation**:
- Can implement any classical Boolean function
- Preserves classical information (reversible)
- Foundation for quantum versions of classical algorithms

### Reversibility
The Toffoli gate is **self-inverse**:

$$\text{Toffoli}^2 = I$$

Applying Toffoli twice returns to the original state.

### Quantum Universality
Combined with single-qubit gates, Toffoli enables **universal quantum computation**.

## Applications in Quantum Algorithms

### Grover's Algorithm - Oracle Implementation

Toffoli gates are essential for implementing oracle functions in Grover's algorithm:

```python
def grover_oracle_3qubit(marked_state="111"):
    """
    Implement a Grover oracle that marks a specific 3-qubit state.
    
    Args:
        marked_state: String like "111" representing the marked state
    """
    circuit = QuantumCircuit(4)  # 3 data qubits + 1 ancilla
    
    # Convert marked_state to list of bits
    marked_bits = [int(bit) for bit in marked_state]
    
    # Flip qubits that should be 0 in the marked state
    for i, bit in enumerate(marked_bits):
        if bit == 0:
            circuit.add_gate(X_GATE, [i])
    
    # Multi-controlled NOT on ancilla (marks the state)
    # For 3-qubit case, we need a 4-qubit Toffoli (can be decomposed)
    circuit.add_gate(TOFFOLI_GATE, [0, 1, 3])  # First part of 4-qubit Toffoli
    circuit.add_gate(TOFFOLI_GATE, [2, 3, 3])  # Complete the marking
    
    # Unflip the qubits we flipped earlier
    for i, bit in enumerate(marked_bits):
        if bit == 0:
            circuit.add_gate(X_GATE, [i])
    
    return circuit

# Usage in complete Grover's algorithm
def grovers_algorithm_3qubit(marked_state="111", iterations=1):
    """Complete 3-qubit Grover's algorithm."""
    sim = QuantumSimulator(4)  # 3 data + 1 ancilla
    circuit = QuantumCircuit(4)
    
    # Initialize ancilla in |1⟩ for phase kickback
    circuit.add_gate(X_GATE, [3])
    circuit.add_gate(H_GATE, [3])
    
    # Initialize data qubits in uniform superposition
    for i in range(3):
        circuit.add_gate(H_GATE, [i])
    
    for _ in range(iterations):
        # Oracle
        oracle = grover_oracle_3qubit(marked_state)
        for gate, qubits in oracle.gates:
            circuit.add_gate(gate, qubits)
        
        # Diffusion operator
        diffusion = grover_diffusion_3qubit()
        for gate, qubits in diffusion.gates:
            circuit.add_gate(gate, qubits)
    
    return sim, circuit
```

### Diffusion Operator for Grover's Algorithm

```python
def grover_diffusion_3qubit():
    """Implement 3-qubit Grover diffusion operator using Toffoli."""
    circuit = QuantumCircuit(3)
    
    # Step 1: H† on all qubits
    for i in range(3):
        circuit.add_gate(H_GATE, [i])
    
    # Step 2: X on all qubits (prepare for phase flip about |000⟩)
    for i in range(3):
        circuit.add_gate(X_GATE, [i])
    
    # Step 3: Multi-controlled Z (can use Toffoli + single Z)
    # |111⟩ → -|111⟩ after X gates means original |000⟩ → -|000⟩
    circuit.add_gate(H_GATE, [2])      # Convert last qubit for CNOT→CZ
    circuit.add_gate(TOFFOLI_GATE, [0, 1, 2])  # CCX
    circuit.add_gate(H_GATE, [2])      # Convert back
    
    # Step 4: Undo X gates
    for i in range(3):
        circuit.add_gate(X_GATE, [i])
    
    # Step 5: H on all qubits
    for i in range(3):
        circuit.add_gate(H_GATE, [i])
    
    return circuit
```

### Quantum Arithmetic

Toffoli gates are building blocks for quantum arithmetic operations:

```python
def quantum_full_adder():
    """Implement quantum full adder using Toffoli gates."""
    # Inputs: a (qubit 0), b (qubit 1), carry_in (qubit 2)
    # Outputs: sum (qubit 3), carry_out (qubit 4)
    circuit = QuantumCircuit(5)
    
    # Sum = a ⊕ b ⊕ carry_in (can be implemented with CNOTs)
    circuit.add_gate(CNOT_GATE, [0, 3])  # a → sum
    circuit.add_gate(CNOT_GATE, [1, 3])  # b → sum  
    circuit.add_gate(CNOT_GATE, [2, 3])  # carry_in → sum
    
    # Carry_out = ab + carry_in(a ⊕ b)
    circuit.add_gate(TOFFOLI_GATE, [0, 1, 4])    # ab → carry_out
    circuit.add_gate(TOFFOLI_GATE, [2, 3, 4])    # carry_in·(a⊕b) → carry_out
    
    return circuit
```

## Decomposition into Elementary Gates

The Toffoli gate can be decomposed into CNOT gates and single-qubit rotations:

```python
def toffoli_decomposition():
    """Decompose Toffoli gate into elementary gates."""
    circuit = QuantumCircuit(3)
    
    # Standard decomposition (requires 6 CNOTs)
    circuit.add_gate(H_GATE, [2])
    circuit.add_gate(CNOT_GATE, [1, 2])
    circuit.add_gate(RZ(-np.pi/4), [2])
    circuit.add_gate(CNOT_GATE, [0, 2])
    circuit.add_gate(RZ(np.pi/4), [2])
    circuit.add_gate(CNOT_GATE, [1, 2])
    circuit.add_gate(RZ(-np.pi/4), [2])
    circuit.add_gate(CNOT_GATE, [0, 2])
    circuit.add_gate(RZ(np.pi/4), [1])
    circuit.add_gate(RZ(np.pi/4), [2])
    circuit.add_gate(H_GATE, [2])
    circuit.add_gate(CNOT_GATE, [0, 1])
    circuit.add_gate(RZ(np.pi/4), [0])
    circuit.add_gate(RZ(-np.pi/4), [1])
    circuit.add_gate(CNOT_GATE, [0, 1])
    
    return circuit
```

## Relationship to Other Gates

### Classical AND Gate
When the target qubit starts in |0⟩, Toffoli implements classical AND:

$$\text{Toffoli}|c_1, c_2, 0\rangle = |c_1, c_2, c_1 \land c_2\rangle$$

### Fredkin Gate Relationship
Toffoli and Fredkin gates are related through basis transformations and both are universal for classical computation.

### Multi-Controlled Extensions
Toffoli can be extended to more controls (C³X, C⁴X, etc.) using ancilla qubits and gate decompositions.

## Properties and Identities

### Conservation Laws
- **Hamming weight**: Number of |1⟩s changes by at most 1
- **Reversibility**: All information is preserved
- **Deterministic**: No probabilistic outcomes

### Commutation Relations
Toffoli gates commute when they act on disjoint sets of qubits:

$$[\text{Toffoli}_{abc}, \text{Toffoli}_{def}] = 0 \text{ if } \{a,b,c\} \cap \{d,e,f\} = \emptyset$$

## Physical Implementation Challenges

### Gate Fidelity
Toffoli gates are typically **more error-prone** than two-qubit gates due to:

- Longer gate sequences in decomposition
- More opportunities for decoherence
- Higher control complexity

### Optimization Strategies
- **Native three-qubit operations** where available
- **Optimized decompositions** to minimize gate count
- **Parallelization** of independent operations

## Circuit Symbol Variations

```
Standard:     ──●──
              │
              ──●──
              │
              ──⊕──

Alternative:  ──●──    or    ──CCX──
              ──●──          ──CCX──
              ──X──          ──CCX──

With labels: Control1 ──●──
             Control2 ──●──
             Target   ──⊕──
```

The Toffoli gate bridges classical and quantum computation, enabling implementation of any classical Boolean function while maintaining quantum coherence. Its role in Grover's algorithm and quantum arithmetic makes it indispensable for practical quantum computing applications.