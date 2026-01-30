# Phase Gate (Single-Qubit Phase Shift)

The **Phase gate** (also known as the **P gate** or **phase shift gate**) is a fundamental single-qubit gate that applies a **phase rotation** to the $|1\rangle$ state while leaving the $|0\rangle$ state unchanged. It's essential for creating quantum interference effects and controlling relative phases.

## Mathematical Definition

The Phase gate with phase angle φ is defined by the matrix:

$$P(\phi) = \begin{pmatrix}
1 & 0 \\
0 & e^{i\phi}
\end{pmatrix}$$

## Action on Basis States

- $P(\phi)|0\rangle = |0\rangle$ (unchanged)
- $P(\phi)|1\rangle = e^{i\phi}|1\rangle$ (acquires phase $e^{i\phi}$)

## Action on Superposition States

For a general single-qubit state $|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$:

$$P(\phi)|\psi\rangle = \alpha|0\rangle + \beta e^{i\phi}|1\rangle$$

The **measurement probabilities** remain unchanged, but the **relative phase** between $|0\rangle$ and $|1\rangle$ is modified by φ.

## Geometric Interpretation

On the **Bloch sphere**, the Phase gate corresponds to a rotation around the **Z-axis** by angle φ:

- The **north pole** ($|0\rangle$) remains fixed
- The **south pole** ($|1\rangle$) acquires phase $e^{i\phi}$
- Points on the **equator** (superposition states) rotate around the Z-axis

## Usage in Quantum Simulator

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import phase_gate, H_GATE
import numpy as np

# Create phase gate with specific angle
phi = np.pi/4
p_gate = phase_gate(phi)

# Apply to superposition state
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(H_GATE, [0])     # Create superposition
circuit.add_gate(p_gate, [0])     # Apply phase shift

sim.execute_circuit(circuit)
print(f"State after Phase(π/4): {sim.get_state_vector()}")
```

## Special Cases and Named Gates

### Common Phase Gates

- **φ = 0**: Identity gate $I$
- **φ = π/4**: T gate (π/8 gate)
- **φ = π/2**: S gate (phase gate)
- **φ = π**: Z gate (Pauli-Z)
- **φ = 2π**: Identity (full rotation)

### S Gate (φ = π/2)
$$S = P(\pi/2) = \begin{pmatrix} 1 & 0 \\ 0 & i \end{pmatrix}$$

### T Gate (φ = π/4)
$$T = P(\pi/4) = \begin{pmatrix} 1 & 0 \\ 0 & e^{i\pi/4} \end{pmatrix} = \begin{pmatrix} 1 & 0 \\ 0 & \frac{1+i}{\sqrt{2}} \end{pmatrix}$$

## Key Properties

### Unitarity
Phase gates are **unitary**: $P(\phi)^\dagger P(\phi) = I$

### Commutativity
Phase gates **commute** with each other and with Z gate:

$$P(\phi_1) P(\phi_2) = P(\phi_2) P(\phi_1) = P(\phi_1 + \phi_2)$$

### Inverse
$$P(\phi)^{-1} = P(-\phi) = P(\phi)^\dagger$$

### Diagonal Property
Phase gates are **diagonal** in the computational basis, making them easy to implement and analyze.

## Physical Significance

### Quantum Interference
Phase gates create the **relative phases** necessary for quantum interference effects in algorithms like:

- **Quantum Fourier Transform (QFT)**
- **Grover's Algorithm** 
- **Phase Estimation**
- **Variational Quantum Algorithms**

### No Effect on Measurement
Phase gates **don't change measurement probabilities** when measuring in the computational basis, but they're crucial for:

- **Interference patterns** in superposition
- **Entanglement creation** when combined with other gates
- **Quantum algorithm implementation**

## Relationship to Other Gates

### Connection to Z-Rotation
The Phase gate is equivalent to a **Z-rotation**:

$$P(\phi) = R_Z(\phi) = e^{-i\phi/2} \begin{pmatrix} e^{i\phi/2} & 0 \\ 0 & e^{-i\phi/2} \end{pmatrix}$$

(up to a global phase factor $e^{-i\phi/2}$)

### Pauli-Z Relationship
$$Z = P(\pi) = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}$$

### X-Gate Conjugation
$$X \cdot P(\phi) \cdot X = P(-\phi)^*$$

This swaps which basis state gets the phase.

## Circuit Representation

In quantum circuit diagrams, phase gates are represented as:

```
q: ──P(φ)──
```

Or for specific cases:
```
q: ──S──    (for φ = π/2)
q: ──T──    (for φ = π/4) 
q: ──Z──    (for φ = π)
```

## Applications

### 1. Quantum Fourier Transform
Phase gates implement the **controlled phase rotations**:
```python
# QFT uses phase gates of the form P(2π/2^k)
for k in range(1, n+1):
    phase_k = phase_gate(2*np.pi / (2**k))
    circuit.add_gate(phase_k, [target_qubit])
```

### 2. Quantum Phase Estimation
Accumulates phases through **controlled-phase operations**.

### 3. Variational Quantum Circuits
Phase gates provide **continuous parameterization** for optimization:
```python
def parameterized_layer(theta):
    circuit = QuantumCircuit(n_qubits)
    for i in range(n_qubits):
        circuit.add_gate(phase_gate(theta[i]), [i])
    return circuit
```

### 4. Quantum Error Correction
Phase gates help implement **stabilizer codes** and **error syndromes**.

## Example: Creating Quantum Interference

```python
# Demonstrate phase-dependent interference
sim = QuantumSimulator(1)

# Create superposition
circuit = QuantumCircuit(1)
circuit.add_gate(H_GATE, [0])
circuit.add_gate(phase_gate(np.pi), [0])  # Apply π phase
circuit.add_gate(H_GATE, [0])  # Second Hadamard

sim.execute_circuit(circuit)
# Result: |1⟩ (destructive interference for |0⟩)
```

The phase gate is fundamental to quantum computing, enabling the **phase relationships** that make quantum algorithms more powerful than their classical counterparts.