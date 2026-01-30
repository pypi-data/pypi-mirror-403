# Y Gate (Pauli-Y)

The Y gate, also known as the **Pauli-Y gate**, is a fundamental single-qubit quantum gate that performs a combined bit-flip and phase-flip operation.

## Matrix Representation

$$Y = \begin{pmatrix} 0 & -i \\ i & 0 \end{pmatrix}$$

## Action on Basis States

The Y gate transforms computational basis states with a phase factor:

$$Y|0\rangle = i|1\rangle$$

$$Y|1\rangle = -i|0\rangle$$

## General Action

For an arbitrary qubit state $|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$:

$$Y|\psi\rangle = Y(\alpha|0\rangle + \beta|1\rangle) = \alpha \cdot i|1\rangle + \beta \cdot (-i)|0\rangle$$

$$= -i\beta|0\rangle + i\alpha|1\rangle$$

The Y gate both **swaps amplitudes** (like X) and **introduces phase factors**.

## Bloch Sphere Representation

The Y gate corresponds to a **180° rotation around the Y-axis** of the Bloch sphere.

- Maps north pole ($|0\rangle$) to south pole ($|1\rangle$) with phase $i$
- Maps south pole ($|1\rangle$) to north pole ($|0\rangle$) with phase $-i$
- Maps points on the Y-axis to themselves
- Inverts and phase-shifts points on the X and Z axes

## Properties

### Involutory

$$Y^2 = -I$$

Applying Y twice gives negative identity (global phase of -1).

### Hermitian

$$Y^\dagger = Y$$

The Y gate is Hermitian.

### Eigenvalues and Eigenvectors

**Eigenvalues**: $\lambda_1 = +1$, $\lambda_2 = -1$

**Eigenvectors**:

$$|+i\rangle = \frac{1}{\sqrt{2}}(|0\rangle + i|1\rangle), \quad Y|+i\rangle = +|+i\rangle$$

$$|-i\rangle = \frac{1}{\sqrt{2}}(|0\rangle - i|1\rangle), \quad Y|-i\rangle = -|-i\rangle$$

## Pauli Group Relations

The Y gate is part of the Pauli group with commutation relations:

$$YZ = iX, \quad ZX = iY, \quad XY = iZ$$

### Anti-commutation

$$\{Y,X\} = YX + XY = 0$$

$$\{Y,Z\} = YZ + ZY = 0$$

## Circuit Symbol

```
|ψ⟩ ──Y── Y|ψ⟩
```

## Decomposition

The Y gate can be decomposed using other gates:

$$Y = iXZ = -iZX$$

Or using rotations:
$$Y = e^{-i\pi\sigma_y/2}$$

## Applications

### Combined Operations

Y gate performs both:

1. **Bit flip**: $|0\rangle \leftrightarrow |1\rangle$ 
2. **Phase modification**: Introduces $\pm i$ factors

### Quantum Algorithms

- Used in quantum error correction
- Component of arbitrary single-qubit rotations
- Basis transformations between X and Z eigenstates

### State Preparation

Prepare specific superposition states:

$$Y|0\rangle = i|1\rangle$$

$$Y|+\rangle = |-i\rangle$$

## Measurement Basis

The Y gate eigenstates form the **Y-measurement basis**:

$$|+i\rangle = \frac{1}{\sqrt{2}}(|0\rangle + i|1\rangle)$$

$$|-i\rangle = \frac{1}{\sqrt{2}}(|0\rangle - i|1\rangle)$$

Measuring in this basis projects onto Y eigenstates.

## Implementation Examples

### Using the Simulator

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import Y_GATE

# Apply Y gate to |0⟩
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(Y_GATE, [0])
circuit.execute(sim)

print(sim.get_state_vector())  # [0, i] = i|1⟩
```

### Y Gate on |1⟩

```python
from quantum_simulator.gates import X_GATE

# Apply Y to |1⟩ state
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(X_GATE, [0])  # Prepare |1⟩
circuit.add_gate(Y_GATE, [0])  # Apply Y
circuit.execute(sim)

print(sim.get_state_vector())  # [-i, 0] = -i|0⟩
```

### Y on Superposition

```python
from quantum_simulator.gates import H_GATE

# Apply Y to |+⟩ state
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(H_GATE, [0])  # Create |+⟩
circuit.add_gate(Y_GATE, [0])  # Apply Y
circuit.execute(sim)

# Result: Y|+⟩ = |-i⟩
print(sim.get_state_vector())  # ≈ [0.707, -0.707i]
```

## Relationship to Other Gates

### Conjugation Relations

$$HYH = -Y$$

$$XYX = -Y$$

$$ZYZ = -Y$$

### Rotation Equivalence

The Y gate is equivalent to a π rotation around the Y-axis:

$$Y = R_y(\pi) = e^{-i\pi\sigma_y/2}$$

### Sequential Applications

$$XY = iZ, \quad YZ = iX, \quad ZY = -iX$$

## Physical Implementations

In quantum hardware:

- **Phase and amplitude control** in superconducting qubits
- **Combined pulse sequences** in trapped ions
- **Polarization rotations** in photonic systems
- **Composite pulses** in NMR systems

The Y gate often requires more complex control than X or Z gates due to its phase requirements.

## Error Analysis

The Y gate can introduce errors through:

- **Amplitude errors**: Incorrect rotation angle
- **Phase errors**: Wrong phase accumulation  
- **Decoherence**: Loss of quantum coherence during gate operation

These errors can be mitigated through:

- Calibrated pulse sequences
- Dynamical decoupling
- Quantum error correction