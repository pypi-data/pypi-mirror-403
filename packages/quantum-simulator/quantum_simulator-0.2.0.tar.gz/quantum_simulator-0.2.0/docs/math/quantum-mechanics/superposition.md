# Quantum Superposition

Superposition is one of the fundamental principles of quantum mechanics that allows qubits to exist in multiple states simultaneously until measured.

## Mathematical Definition

A qubit is in **superposition** when it exists in a linear combination of basis states:

$$|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$$

Where $\alpha$ and $\beta$ are non-zero complex amplitudes satisfying $|\alpha|^2 + |\beta|^2 = 1$.

## Key Properties

### Probability Interpretation

When measured, the qubit will be found in state:
- $|0\rangle$ with probability $|\alpha|^2$
- $|1\rangle$ with probability $|\beta|^2$

The measurement is **probabilistic** and **irreversible**.

### Equal Superposition

The most common superposition states are:

$$|+\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle)$$

$$|-\rangle = \frac{1}{\sqrt{2}}(|0\rangle - |1\rangle)$$

These states have equal probability ($\frac{1}{2}$) of measuring 0 or 1.

## Creating Superposition

### Using the Hadamard Gate

The Hadamard gate creates equal superposition from computational basis states:

$$H|0\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle) = |+\rangle$$

$$H|1\rangle = \frac{1}{\sqrt{2}}(|0\rangle - |1\rangle) = |-\rangle$$

### Matrix Representation

$$H = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$$

## Phase Relationships

Superposition states can have different **relative phases**:

$$|\psi\rangle = \frac{1}{\sqrt{2}}(|0\rangle + e^{i\phi}|1\rangle)$$

Where $\phi$ is the relative phase between the $|0\rangle$ and $|1\rangle$ components.

### Important Phase Examples

- $\phi = 0$: $|+\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle)$
- $\phi = \pi$: $|-\rangle = \frac{1}{\sqrt{2}}(|0\rangle - |1\rangle)$  
- $\phi = \pi/2$: $|+i\rangle = \frac{1}{\sqrt{2}}(|0\rangle + i|1\rangle)$
- $\phi = 3\pi/2$: $|-i\rangle = \frac{1}{\sqrt{2}}(|0\rangle - i|1\rangle)$

## Multi-Qubit Superposition

For multiple qubits, superposition becomes more complex. Each qubit can be in superposition independently, or the system can be in a **global** superposition.

### Independent Superposition

Two qubits each in $|+\rangle$ state:

$$|\psi\rangle = |+\rangle \otimes |+\rangle = \frac{1}{2}(|00\rangle + |01\rangle + |10\rangle + |11\rangle)$$

### Global Superposition

The system is in superposition over all computational basis states:

$$|\psi\rangle = \frac{1}{2}(|00\rangle + |01\rangle + |10\rangle + |11\rangle)$$

This gives equal probability ($\frac{1}{4}$) for each measurement outcome.

## Visualization on the Bloch Sphere

Superposition states lie on the surface of the Bloch sphere:

- $|+\rangle$: Point on the positive x-axis
- $|-\rangle$: Point on the negative x-axis
- $|+i\rangle$: Point on the positive y-axis
- $|-i\rangle$: Point on the negative y-axis

## Decoherence and Measurement

### Measurement Collapse

When a superposition state is measured, it **collapses** to one of the basis states:

$$|\psi\rangle = \alpha|0\rangle + \beta|1\rangle \xrightarrow{\text{measure}} \begin{cases} |0\rangle & \text{with probability } |\alpha|^2 \\ |1\rangle & \text{with probability } |\beta|^2 \end{cases}$$

### Decoherence

In real quantum systems, superposition is fragile and can be destroyed by interaction with the environment, leading to **decoherence**.

## Examples in the Simulator

### Creating Superposition with Hadamard

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import H_GATE

# Create single qubit
sim = QuantumSimulator(1)

# Apply Hadamard to create |+⟩ state
circuit = QuantumCircuit(1)
circuit.add_gate(H_GATE, [0])
circuit.execute(sim)

print(sim.get_state_vector())  # ≈ [0.707, 0.707]
```

### Two-Qubit Superposition

```python
# Create two qubits in superposition
sim = QuantumSimulator(2)

circuit = QuantumCircuit(2)
circuit.add_gate(H_GATE, [0])  # First qubit in superposition
circuit.add_gate(H_GATE, [1])  # Second qubit in superposition
circuit.execute(sim)

print(sim.get_state_vector())  # ≈ [0.5, 0.5, 0.5, 0.5]
```

This creates the state $\frac{1}{2}(|00\rangle + |01\rangle + |10\rangle + |11\rangle)$.

## Quantum Interference

Superposition enables **quantum interference**, where probability amplitudes can add constructively or destructively, leading to quantum speedup in algorithms.