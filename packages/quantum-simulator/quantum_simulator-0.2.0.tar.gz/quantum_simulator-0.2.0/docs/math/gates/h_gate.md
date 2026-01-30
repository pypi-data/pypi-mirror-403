# Hadamard Gate

The **Hadamard gate** (H gate) is one of the most important quantum gates, creating **superposition states** from computational basis states. It maps the computational basis $\{|0\rangle, |1\rangle\}$ to the Hadamard basis $\{|+\rangle, |-\rangle\}$.

## Matrix Representation

$$H = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$$

## Action on Basis States

The Hadamard gate creates equal superposition states:

$$H|0\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle) = |+\rangle$$

$$H|1\rangle = \frac{1}{\sqrt{2}}(|0\rangle - |1\rangle) = |-\rangle$$

## General Action

For an arbitrary qubit state $|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$:

$$H|\psi\rangle = H(\alpha|0\rangle + \beta|1\rangle)$$

$$= \alpha H|0\rangle + \beta H|1\rangle$$

$$= \frac{\alpha}{\sqrt{2}}(|0\rangle + |1\rangle) + \frac{\beta}{\sqrt{2}}(|0\rangle - |1\rangle)$$

$$= \frac{\alpha + \beta}{\sqrt{2}}|0\rangle + \frac{\alpha - \beta}{\sqrt{2}}|1\rangle$$

## Hadamard Basis

The Hadamard gate transforms between computational and Hadamard bases:

### Computational to Hadamard

$$|0\rangle \rightarrow |+\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle)$$

$$|1\rangle \rightarrow |-\rangle = \frac{1}{\sqrt{2}}(|0\rangle - |1\rangle)$$

### Hadamard to Computational

$$|+\rangle \rightarrow |0\rangle$$

$$|-\rangle \rightarrow |1\rangle$$

## Bloch Sphere Representation

The Hadamard gate corresponds to a **π rotation around the (X+Z)/√2 axis** of the Bloch sphere.

Geometrically, it's equivalent to:

1. π rotation around X-axis
2. Followed by π/2 rotation around Y-axis

Or alternatively:

$$H = \frac{1}{\sqrt{2}}(X + Z)$$

## Properties

### Involutory

$$H^2 = I$$

The Hadamard gate is its own inverse: applying H twice returns to the original state.

### Hermitian

$$H^\dagger = H$$

The Hadamard gate is Hermitian (self-adjoint).

### Unitary

$$H^\dagger H = H^2 = I$$

### Eigenvalues and Eigenvectors

**Eigenvalues**: $\lambda_1 = +1$, $\lambda_2 = -1$

**Eigenvectors**:

$$|+\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle), \quad H|+\rangle = +|+\rangle$$

$$|-\rangle = \frac{1}{\sqrt{2}}(|0\rangle - |1\rangle), \quad H|-\rangle = -|-\rangle$$

The $\{|+\rangle, |-\rangle\}$ states are eigenstates of H.

## Circuit Symbol

```
|ψ⟩ ──H── H|ψ⟩
```

## Pauli Group Relations

The Hadamard gate **conjugates** Pauli operators:

$$HXH = Z$$

$$HYH = -Y$$  

$$HZH = X$$

This property makes H crucial for **basis transformations** between X and Z measurements.

## Multi-Qubit Hadamard

For n qubits, applying H to each qubit creates **uniform superposition**:

$$H^{\otimes n}|0\rangle^{\otimes n} = \frac{1}{\sqrt{2^n}}\sum_{x=0}^{2^n-1}|x\rangle$$

This creates an **equal amplitude superposition** over all $2^n$ computational basis states.

### Two-Qubit Example

$$H \otimes H |00\rangle = \frac{1}{2}(|00\rangle + |01\rangle + |10\rangle + |11\rangle)$$

## Walsh-Hadamard Transform

The n-qubit Hadamard operation implements the **Walsh-Hadamard transform**:

$$H^{\otimes n}|x\rangle = \frac{1}{\sqrt{2^n}}\sum_{z=0}^{2^n-1}(-1)^{x \cdot z}|z\rangle$$

Where $x \cdot z = \sum_i x_i z_i$ is the bitwise dot product.

## Measurement and Observables

### X-basis Measurement

Since H diagonalizes the X operator:

$$H|+\rangle = |0\rangle, \quad H|-\rangle = |1\rangle$$

Measuring after H gives **X-basis measurement**:

- Result 0: state was $|+\rangle$
- Result 1: state was $|-\rangle$

### Expectation Value

For state $|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$:

$$\langle H \rangle = \langle\psi|H|\psi\rangle = \frac{2\text{Re}(\alpha^*\beta)}{\sqrt{2}}$$

This measures the **coherence** between computational basis states.

## Applications

### Superposition Creation

Primary use: creating **quantum superposition** from classical states:

$$H|0\rangle = |+\rangle \quad \text{(equal superposition)}$$

### Interference

Enables **quantum interference** by creating coherent superpositions that can interfere constructively or destructively.

### Basis Rotation

Rotates measurement basis from Z to X:

- Z-measurement after H gives X-measurement
- X-measurement after H gives Z-measurement

### Quantum Fourier Transform

Hadamard is the **1-qubit QFT**:

$$\text{QFT}_1 = H$$

And forms the foundation of multi-qubit QFT circuits.

## Implementation Examples

### Basic Superposition

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import H_GATE

# Create |+⟩ state
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(H_GATE, [0])
circuit.execute(sim)

print(sim.get_state_vector())  # ≈ [0.707, 0.707] = |+⟩
```

### Basis Transformation

```python
from quantum_simulator.gates import X_GATE

# X-measurement via H
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(H_GATE, [0])  # Create |+⟩
circuit.add_gate(H_GATE, [0])  # Transform back
circuit.execute(sim)

print(sim.get_state_vector())  # [1, 0] = |0⟩
```

### Bell State Preparation

```python
from quantum_simulator.gates import CNOT_GATE

# Create Bell state |Φ⁺⟩
sim = QuantumSimulator(2)
circuit = QuantumCircuit(2)
circuit.add_gate(H_GATE, [0])     # H⊗I|00⟩ = |+0⟩
circuit.add_gate(CNOT_GATE, [0, 1])  # CNOT|+0⟩ = |Φ⁺⟩
circuit.execute(sim)

# Result: |Φ⁺⟩ = (|00⟩ + |11⟩)/√2
print(sim.get_state_vector())  # [0.707, 0, 0, 0.707]
```

### Uniform Superposition

```python
# Create 3-qubit uniform superposition
sim = QuantumSimulator(3)
circuit = QuantumCircuit(3)
for i in range(3):
    circuit.add_gate(H_GATE, [i])
circuit.execute(sim)

# Result: equal amplitudes over all 8 basis states
print(sim.get_state_vector())  # All components ≈ 0.354
```

## Quantum Algorithms

### Deutsch-Jozsa Algorithm

Hadamard gates create initial superposition and final interference:

```
|0⟩ ──H── [ f ] ──H── measurement
|1⟩ ──H── [ f ] ────── (ancilla)
```

### Grover's Algorithm

Hadamard creates uniform superposition as starting state:

$$H^{\otimes n}|0\rangle^{\otimes n} = |\text{uniform}\rangle$$

### Simon's Algorithm

Uses Hadamard for creating superposition and extracting period information.

## Parameterized Hadamard

The Hadamard can be generalized to **parameterized Hadamard gates**:

$$H(\theta, \phi) = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & e^{-i\phi} \\ e^{i\theta} & -e^{i(\theta+\phi)} \end{pmatrix}$$

With standard Hadamard: $H = H(0, 0)$.

## Physical Implementations

Common physical realizations:

### Superconducting Qubits

- **Microwave pulses** at specific frequencies
- **Rabi oscillations** for π/2 + π rotations
- Typical gate times: 10-50 ns

### Trapped Ions

- **Laser pulses** for state manipulation
- **Raman transitions** between internal states
- Gate times: μs range

### Photonic Systems

- **Beam splitters** (50/50 splitting)
- **Wave plates** for polarization rotation
- Near-instantaneous operations

### NMR

- **RF pulses** at Larmor frequency
- **Composite pulse sequences**
- Gate times: ms range

## Gate Decomposition

### Rotation Decomposition

$$H = R_y(\pi/2) R_z(\pi) R_y(\pi/2)$$

$$H = e^{-i\pi Y/4} e^{-i\pi Z/2} e^{-i\pi Y/4}$$

### Euler Angles

$$H = R_z(\phi) R_y(\theta) R_z(\lambda)$$

With specific angle choices giving the Hadamard transformation.

## Error Models

Common Hadamard gate errors:

### Amplitude Errors
$$H_{\text{error}} = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1+\epsilon \\ 1+\delta & -1 \end{pmatrix}$$

### Phase Errors
$$H_{\text{phase}} = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & e^{i\phi} \\ 1 & -e^{i\psi} \end{pmatrix}$$

### Coherent Errors
Systematic over/under-rotation from calibration errors.

These errors can be characterized through **randomized benchmarking** and **process tomography**.

## Advanced Properties

### Clifford Group

Hadamard is a generator of the **Clifford group** along with S and CNOT gates.

### Stabilizer Formalism

H transforms **stabilizer generators**:

- X-stabilizers → Z-stabilizers  
- Z-stabilizers → X-stabilizers

### Resource Theory

In **magic state theory**, Hadamard gates are **free operations** when combined with stabilizer states and measurements.