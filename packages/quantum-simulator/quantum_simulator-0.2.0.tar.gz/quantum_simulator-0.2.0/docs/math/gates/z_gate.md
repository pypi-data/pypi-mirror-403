# Z Gate (Pauli-Z)

The Z gate, also known as the **Pauli-Z gate** or **phase-flip gate**, is a fundamental single-qubit quantum gate that introduces a phase flip to the $|1\rangle$ state while leaving $|0\rangle$ unchanged.

## Matrix Representation

$$Z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}$$

## Action on Basis States

The Z gate applies a phase flip to the $|1\rangle$ state:

$$Z|0\rangle = |0\rangle$$

$$Z|1\rangle = -|1\rangle$$

## General Action

For an arbitrary qubit state $|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$:

$$Z|\psi\rangle = Z(\alpha|0\rangle + \beta|1\rangle) = \alpha|0\rangle + \beta(-|1\rangle)$$

$$= \alpha|0\rangle - \beta|1\rangle$$

The Z gate **flips the phase** of the $|1\rangle$ component while preserving amplitudes' magnitudes.

## Bloch Sphere Representation

The Z gate corresponds to a **180° rotation around the Z-axis** of the Bloch sphere.

- North pole ($|0\rangle$) maps to itself
- South pole ($|1\rangle$) maps to itself  
- Points on the Z-axis are unchanged
- Points on the XY-plane are inverted through the Z-axis

## Properties

### Involutory

$$Z^2 = I$$

The Z gate is its own inverse.

### Hermitian

$$Z^\dagger = Z$$

The Z gate is Hermitian.

### Eigenvalues and Eigenvectors

**Eigenvalues**: $\lambda_1 = +1$, $\lambda_2 = -1$

**Eigenvectors**:

$$|0\rangle, \quad Z|0\rangle = +|0\rangle$$

$$|1\rangle, \quad Z|1\rangle = -|1\rangle$$

The computational basis states are eigenstates of Z.

## Pauli Group Relations

The Z gate completes the Pauli group with:

$$ZX = iY, \quad XY = iZ, \quad YZ = iX$$

### Anti-commutation

$$\{Z,X\} = ZX + XZ = 0$$

$$\{Z,Y\} = ZY + YZ = 0$$

### Commutation with Z-basis

$$[Z, |0\rangle\langle 0|] = 0$$

$$[Z, |1\rangle\langle 1|] = 0$$

Z commutes with computational basis projectors.

## Circuit Symbol

```
|ψ⟩ ──Z── Z|ψ⟩
```

## Phase Gate Family

The Z gate belongs to the family of **phase gates**:

$$P(\phi) = \begin{pmatrix} 1 & 0 \\ 0 & e^{i\phi} \end{pmatrix}$$

Where $Z = P(\pi)$ with $\phi = \pi$.

### Related Phase Gates

- **S gate**: $S = P(\pi/2) = \sqrt{Z}$
- **T gate**: $T = P(\pi/4) = \sqrt{S}$
- **Identity**: $I = P(0)$

## Measurement and Observables

### Z-measurement

The Z gate corresponds to measurement in the computational basis:

- Eigenvalue +1: measure $|0\rangle$
- Eigenvalue -1: measure $|1\rangle$

### Expectation Value

For state $|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$:

$$\langle Z \rangle = \langle\psi|Z|\psi\rangle = |\alpha|^2 - |\beta|^2$$

This gives the **population difference** between $|0\rangle$ and $|1\rangle$.

## Applications

### Phase Flip

Z gate implements a **conditional phase flip**:

- No effect on $|0\rangle$ states
- Flips sign of $|1\rangle$ states

### Quantum Interference

Creates interference patterns in superposition:

$$Z(|0\rangle + |1\rangle) = |0\rangle - |1\rangle$$

### Error Syndrome

Used in quantum error correction to detect phase flip errors.

## Implementation Examples

### Using the Simulator

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import Z_GATE

# Apply Z gate to |0⟩ (no change)
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(Z_GATE, [0])
circuit.execute(sim)

print(sim.get_state_vector())  # [1, 0] = |0⟩
```

### Z Gate on |1⟩

```python
from quantum_simulator.gates import X_GATE

# Apply Z to |1⟩ state
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(X_GATE, [0])  # Prepare |1⟩
circuit.add_gate(Z_GATE, [0])  # Apply Z
circuit.execute(sim)

print(sim.get_state_vector())  # [0, -1] = -|1⟩
```

### Z on Superposition

```python
from quantum_simulator.gates import H_GATE

# Apply Z to |+⟩ state
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(H_GATE, [0])  # Create |+⟩
circuit.add_gate(Z_GATE, [0])  # Apply Z
circuit.execute(sim)

# Result: Z|+⟩ = |-⟩
print(sim.get_state_vector())  # ≈ [0.707, -0.707]
```

## Controlled-Z Operations

### Controlled-Z Gate

The **controlled-Z** (CZ) gate applies Z to the target when control is $|1\rangle$:

$$CZ = |0\rangle\langle 0| \otimes I + |1\rangle\langle 1| \otimes Z$$

$$CZ = \begin{pmatrix} 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 \\ 0 & 0 & 1 & 0 \\ 0 & 0 & 0 & -1 \end{pmatrix}$$

### Symmetry

Unlike CNOT, controlled-Z is **symmetric**:

$$CZ_{12} = CZ_{21}$$

Both qubits can be considered as control or target.

## Relationship to Other Gates

### Basis Transformation

$$HZH = X$$

The Z gate becomes an X gate under Hadamard conjugation.

### Rotation Equivalence

$$Z = R_z(\pi) = e^{-i\pi\sigma_z/2}$$

The Z gate is a π rotation around the Z-axis.

### Sequential Operations

$$XZ = -iY, \quad ZY = iX$$

## Physical Implementations

Z gates are often the **easiest to implement** in quantum hardware:

- **Frequency shifts** in superconducting qubits
- **Stark shifts** in trapped ions
- **Optical phase shifts** in photonic systems
- **Chemical shifts** in NMR

Many implementations achieve Z gates through **virtual Z gates** - software phase tracking without physical operations.

## Virtual Z Gates

In many quantum processors, Z gates are implemented as **virtual gates**:

- No physical operation required
- Phase tracking in software
- Applied during subsequent physical gates
- Reduces gate time and errors

This makes Z gates effectively "free" in terms of decoherence and error rates.

## Error Models

Common Z gate errors:

- **Over-rotation**: $e^{-i(\pi+\epsilon)\sigma_z/2}$
- **Under-rotation**: $e^{-i(\pi-\epsilon)\sigma_z/2}$
- **Dephasing**: Loss of phase coherence

These can be characterized through **process tomography** and corrected through calibration.