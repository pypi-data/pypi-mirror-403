# X Gate (Pauli-X)

The X gate, also known as the **Pauli-X gate** or **NOT gate**, is a fundamental single-qubit quantum gate that performs a bit-flip operation.

## Matrix Representation

$$X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}$$

## Action on Basis States

The X gate flips computational basis states:

$$X|0\rangle = |1\rangle$$

$$X|1\rangle = |0\rangle$$

## General Action

For an arbitrary qubit state $|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$:

$$X|\psi\rangle = X(\alpha|0\rangle + \beta|1\rangle) = \alpha|1\rangle + \beta|0\rangle$$

The amplitudes are **swapped** between the $|0\rangle$ and $|1\rangle$ components.

## Bloch Sphere Representation

The X gate corresponds to a **180° rotation around the X-axis** of the Bloch sphere.

- Maps north pole ($|0\rangle$) to south pole ($|1\rangle$)
- Maps south pole ($|1\rangle$) to north pole ($|0\rangle$)
- Maps points on the X-axis to themselves
- Inverts points on the Y and Z axes

## Properties

### Involutory
$$X^2 = I$$

The X gate is its own inverse - applying it twice returns to the original state.

### Hermitian
$$X^\dagger = X$$

The X gate is Hermitian, making it both unitary and self-adjoint.

### Eigenvalues and Eigenvectors

**Eigenvalues**: $\lambda_1 = +1$, $\lambda_2 = -1$

**Eigenvectors**:

$$|+\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle), \quad X|+\rangle = +|+\rangle$$

$$|-\rangle = \frac{1}{\sqrt{2}}(|0\rangle - |1\rangle), \quad X|-\rangle = -|-\rangle$$

## Pauli Group

The X gate belongs to the **Pauli group** along with Y, Z, and I:

$$\{I, X, Y, Z\}$$

### Commutation Relations

$$XY = iZ, \quad YZ = iX, \quad ZX = iY$$

$$[X,Y] = XY - YX = 2iZ$$

### Anti-commutation

$$\{X,Y\} = XY + YX = 0$$

$$\{X,Z\} = XZ + ZX = 0$$

## Circuit Symbol

```
|ψ⟩ ──X── X|ψ⟩
```

Or with the traditional NOT gate symbol:
```
|ψ⟩ ──⊕── X|ψ⟩
```

## Applications

### Classical NOT Operation

For computational basis states, X gate performs classical NOT:

- $|0\rangle \rightarrow |1\rangle$ (0 → 1)
- $|1\rangle \rightarrow |0\rangle$ (1 → 0)

### State Preparation

Prepare $|1\rangle$ state from initialized $|0\rangle$:

$$X|0\rangle = |1\rangle$$

### Conditional Operations

X gate is used as the target in controlled operations like CNOT.

## Implementation Examples

### Using the Simulator

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import X_GATE

# Apply X gate to |0⟩
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(X_GATE, [0])
circuit.execute(sim)

print(sim.get_state_vector())  # [0, 1] = |1⟩
```

### Multiple X Gates

```python
# Apply X gate twice (should return to original state)
circuit = QuantumCircuit(1)
circuit.add_gate(X_GATE, [0])  # |0⟩ → |1⟩
circuit.add_gate(X_GATE, [0])  # |1⟩ → |0⟩
circuit.execute(sim)

print(sim.get_state_vector())  # [1, 0] = |0⟩
```

### X Gate on Superposition

```python
from quantum_simulator.gates import H_GATE

# Create superposition then apply X
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(H_GATE, [0])  # |0⟩ → |+⟩
circuit.add_gate(X_GATE, [0])  # |+⟩ → |+⟩ (eigenstate)
circuit.execute(sim)

print(sim.get_state_vector())  # ≈ [0.707, 0.707] = |+⟩
```

## Related Gates

### Controlled-X (CNOT)

The X gate serves as the target in the controlled-X (CNOT) gate:

$$\text{CNOT} = |0\rangle\langle 0| \otimes I + |1\rangle\langle 1| \otimes X$$

### Rotation Relationship

The X gate can be expressed as a rotation:

$$X = e^{-i\pi\sigma_x/2} = \cos(\pi/2)I - i\sin(\pi/2)\sigma_x$$

Where $\sigma_x = X$ is the Pauli-X operator.

### Relationship to Hadamard

$$HXH = Z$$

The X gate conjugated by Hadamard gates becomes a Z gate.

## Physical Implementations

In physical quantum systems, the X gate can be implemented by:

- **Microwave pulses** in superconducting qubits
- **Laser pulses** in trapped ions  
- **Magnetic field pulses** in NMR systems
- **Optical pulses** in photonic systems

The exact implementation depends on the physical platform and how qubits are encoded.