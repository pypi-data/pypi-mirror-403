# Quantum Entanglement

Entanglement is a uniquely quantum phenomenon where two or more qubits become correlated in such a way that the quantum state of each qubit cannot be described independently.

## Mathematical Definition

A multi-qubit state is **entangled** if it cannot be written as a tensor product of individual qubit states:

$$|\psi\rangle \neq |\psi_1\rangle \otimes |\psi_2\rangle \otimes \cdots \otimes |\psi_n\rangle$$

For entangled states, measuring one qubit instantly affects the state of all other entangled qubits, regardless of physical separation.

## Bell States

The four **Bell states** are maximally entangled two-qubit states:

### Bell State $|\Phi^+\rangle$

$$|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$$

**Properties**:

- Equal superposition of $|00\rangle$ and $|11\rangle$
- Measuring one qubit determines the other with 100% certainty
- If first qubit is 0, second qubit is definitely 0
- If first qubit is 1, second qubit is definitely 1

### Bell State $|\Phi^-\rangle$

$$|\Phi^-\rangle = \frac{1}{\sqrt{2}}(|00\rangle - |11\rangle)$$

Similar correlations but with opposite relative phase.

### Bell State $|\Psi^+\rangle$

$$|\Psi^+\rangle = \frac{1}{\sqrt{2}}(|01\rangle + |10\rangle)$$

**Properties**:

- If first qubit is 0, second qubit is definitely 1
- If first qubit is 1, second qubit is definitely 0
- Anti-correlated measurements

### Bell State $|\Psi^-\rangle$

$$|\Psi^-\rangle = \frac{1}{\sqrt{2}}(|01\rangle - |10\rangle)$$

Anti-correlated with opposite relative phase.

## Creating Entangled States

### Standard Bell State Preparation

To create $|\Phi^+\rangle$ from $|00\rangle$:

1. **Apply Hadamard** to first qubit: $H \otimes I |00\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |10\rangle)$
2. **Apply CNOT** with first qubit as control: $\text{CNOT} \cdot \frac{1}{\sqrt{2}}(|00\rangle + |10\rangle) = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$

### Circuit Representation

```
|0⟩ ──H────●──── |Φ⁺⟩
           │
|0⟩ ───────X────
```

## Entanglement Properties

### Non-Locality

Entangled qubits exhibit **non-local correlations**:

- Measuring one qubit instantly affects the other
- No classical communication can explain these correlations
- Violates Bell inequalities

### Monogamy

Quantum entanglement is **monogamous**:

- If qubit A is maximally entangled with qubit B, it cannot be entangled with qubit C
- Entanglement is a finite resource that must be shared

## Mathematical Tests for Entanglement

### Schmidt Decomposition

For a two-qubit state $|\psi\rangle$, perform Schmidt decomposition:

$$|\psi\rangle = \sum_i \lambda_i |u_i\rangle \otimes |v_i\rangle$$

The state is entangled if more than one Schmidt coefficient $\lambda_i$ is non-zero.

### Concurrence

For two qubits, concurrence $C$ measures entanglement:

$$C = \max(0, \sqrt{\lambda_1} - \sqrt{\lambda_2} - \sqrt{\lambda_3} - \sqrt{\lambda_4})$$

Where $\lambda_i$ are eigenvalues of $\rho(\sigma_y \otimes \sigma_y)\rho^*(\sigma_y \otimes \sigma_y)$.

- $C = 0$: Separable (no entanglement)
- $C = 1$: Maximally entangled

## Multi-Qubit Entanglement

### GHZ States

Three-qubit maximally entangled states:

$$|\text{GHZ}\rangle = \frac{1}{\sqrt{2}}(|000\rangle + |111\rangle)$$

### W States

Three-qubit symmetric entangled states:

$$|W\rangle = \frac{1}{\sqrt{3}}(|001\rangle + |010\rangle + |100\rangle)$$

## Entanglement in Quantum Algorithms

### Quantum Speedup

Entanglement is essential for:

- Quantum parallelism
- Exponential speedup in quantum algorithms
- Quantum error correction
- Quantum cryptography

### Quantum Teleportation

Entanglement enables quantum teleportation:

- Use entangled pair as quantum channel
- Transmit quantum state without physical transfer
- Requires classical communication

## Examples in the Simulator

### Creating a Bell State

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import H_GATE, CNOT_GATE

# Create Bell state |Φ⁺⟩
sim = QuantumSimulator(2)

circuit = QuantumCircuit(2)
circuit.add_gate(H_GATE, [0])      # Hadamard on first qubit
circuit.add_gate(CNOT_GATE, [0, 1]) # CNOT: control=0, target=1

circuit.execute(sim)
print(sim.get_state_vector())  # ≈ [0.707, 0, 0, 0.707]
```

This creates $|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$.

### Measuring Entangled Qubits

```python
# Measure the entangled qubits
result_0 = sim.measure(0)
result_1 = sim.measure(1)

print(f"Qubit 0: {result_0}, Qubit 1: {result_1}")
# Results will always be the same: (0,0) or (1,1)
```

### GHZ State Creation

```python
# Create 3-qubit GHZ state
sim = QuantumSimulator(3)

circuit = QuantumCircuit(3)
circuit.add_gate(H_GATE, [0])        # Superposition on first qubit
circuit.add_gate(CNOT_GATE, [0, 1])  # Entangle first two qubits
circuit.add_gate(CNOT_GATE, [0, 2])  # Entangle first and third qubits

circuit.execute(sim)
# Creates (|000⟩ + |111⟩)/√2
```

## Decoherence and Entanglement

Entanglement is extremely fragile:

- Environmental noise destroys entanglement
- Decoherence rates scale with system size  
- Quantum error correction protects entanglement

Entanglement is the key resource that enables quantum computing to outperform classical computing for certain problems.