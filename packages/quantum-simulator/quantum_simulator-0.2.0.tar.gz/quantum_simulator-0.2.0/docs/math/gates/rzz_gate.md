# RZZ Gate (Two-Qubit Z⊗Z Rotation)

The **RZZ gate** is a two-qubit rotation gate that performs a rotation around the Z⊗Z axis in the two-qubit Hilbert space. It's particularly important in **Quantum Approximate Optimization Algorithm (QAOA)** where it's used to implement cost Hamiltonians for optimization problems.

## Mathematical Definition

The RZZ gate with rotation angle θ is defined by the matrix:

$$R_{ZZ}(\theta) = \exp\left(-i\frac{\theta}{2} Z \otimes Z\right) = \begin{pmatrix}
e^{-i\theta/2} & 0 & 0 & 0 \\
0 & e^{i\theta/2} & 0 & 0 \\
0 & 0 & e^{i\theta/2} & 0 \\
0 & 0 & 0 & e^{-i\theta/2}
\end{pmatrix}$$

## Action on Basis States

The RZZ gate applies different phases depending on the parity of the two-qubit state:

- $R_{ZZ}(\theta)|00\rangle = e^{-i\theta/2}|00\rangle$
- $R_{ZZ}(\theta)|01\rangle = e^{i\theta/2}|01\rangle$
- $R_{ZZ}(\theta)|10\rangle = e^{i\theta/2}|10\rangle$
- $R_{ZZ}(\theta)|11\rangle = e^{-i\theta/2}|11\rangle$

## Geometric Interpretation

The RZZ gate creates **correlated phase rotations** between the two qubits:

- **States with even parity** ($|00\rangle$, $|11\rangle$): acquire phase $e^{-i\theta/2}$
- **States with odd parity** ($|01\rangle$, $|10\rangle$): acquire phase $e^{i\theta/2}$

## Physical Significance

### In QAOA
RZZ gates implement the **cost Hamiltonian** for many optimization problems:

$$H_C = \sum_{(i,j) \in E} \frac{1 - Z_i Z_j}{2}$$

Where $(i,j)$ represents edges in a graph, such as in the **Max-Cut problem**.

### In Quantum Chemistry
RZZ rotations appear in **variational quantum eigensolvers** for molecular Hamiltonians with two-body interaction terms.

## Usage in Quantum Simulator

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import RZZ, H_GATE
import numpy as np

# Create RZZ gate with specific angle
theta = np.pi/4
rzz_gate = RZZ(theta)

# Apply to Bell state
sim = QuantumSimulator(2)
circuit = QuantumCircuit(2)
circuit.add_gate(H_GATE, [0])      # Create superposition
circuit.add_gate(rzz_gate, [0, 1])  # Apply RZZ rotation

sim.execute_circuit(circuit)
print(f"State after RZZ(π/4): {sim.get_state_vector()}")
```

## Key Properties

### Unitarity
RZZ is a **unitary gate**: $R_{ZZ}(\theta)^\dagger R_{ZZ}(\theta) = I$

### Commutativity
RZZ gates with different angles **commute**:

$$R_{ZZ}(\theta_1) R_{ZZ}(\theta_2) = R_{ZZ}(\theta_2) R_{ZZ}(\theta_1) = R_{ZZ}(\theta_1 + \theta_2)$$

### Inverse
$$R_{ZZ}(\theta)^{-1} = R_{ZZ}(-\theta)$$

### Self-Inverse Property

$$R_{ZZ}(\pi) \cdot R_{ZZ}(\pi) = -I$$

(up to global phase)

## Special Cases

- **θ = 0**: Identity operation
- **θ = π**: Creates a **controlled-phase flip** on both qubits
- **θ = π/2**: Quarter rotation, commonly used in QAOA circuits

## Relationship to Other Gates

### Connection to CZ Gate
The RZZ gate is related to the **controlled-Z (CZ) gate**:

$$\text{CZ} = \text{diag}(1, 1, 1, -1)$$

While CZ applies a phase only to $|11\rangle$, RZZ applies **correlated phases** to all computational basis states.

### Pauli Operator Decomposition
$$R_{ZZ}(\theta) = \cos(\theta/2) I \otimes I - i\sin(\theta/2) Z \otimes Z$$

## Applications

1. **QAOA Optimization**: Cost Hamiltonian implementation
2. **Quantum Chemistry**: Two-body interaction terms
3. **Quantum Machine Learning**: Parameterized quantum circuits
4. **Entanglement Generation**: Creating phase-entangled states

## Circuit Representation

In quantum circuit diagrams, RZZ is often represented as:

```
q0: ──●──RZZ(θ)──●──
      │          │
q1: ──●──────────●──
```

Or more compactly:
```
q0: ──RZZ(θ)──
      │
q1: ──RZZ(θ)──
```

## Example: QAOA Cost Hamiltonian

For a Max-Cut problem on a graph with edges, each edge contributes an RZZ term:

```python
def create_cost_hamiltonian(edges, gamma):
    circuit = QuantumCircuit(n_qubits)
    for i, j in edges:
        rzz_gate = RZZ(-gamma)  # Negative for Max-Cut
        circuit.add_gate(rzz_gate, [i, j])
    return circuit
```

This creates quantum interference patterns that preferentially amplify good cuts in the optimization landscape.