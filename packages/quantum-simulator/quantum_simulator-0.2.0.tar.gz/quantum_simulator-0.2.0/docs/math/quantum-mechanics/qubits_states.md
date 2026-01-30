# Qubits and Quantum States

This page introduces the mathematical foundation of qubits and quantum states as implemented in the Quantum Simulator.

## What is a Qubit?

A **qubit** (quantum bit) is the fundamental unit of quantum information. Unlike classical bits that can only be 0 or 1, qubits can exist in a **superposition** of both states simultaneously.

### Mathematical Representation

A qubit state $|\psi\rangle$ is represented as a linear combination of the computational basis states:

$$|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$$

Where:

- $\alpha, \beta \in \mathbb{C}$ are complex probability amplitudes
- $|0\rangle, |1\rangle$ are the computational basis states
- The normalization condition requires: $|\alpha|^2 + |\beta|^2 = 1$

### Computational Basis States

The two computational basis states are:

$$|0\rangle = \begin{pmatrix} 1 \\ 0 \end{pmatrix}, \quad |1\rangle = \begin{pmatrix} 0 \\ 1 \end{pmatrix}$$

Any qubit state can be written in vector form:

$$|\psi\rangle = \begin{pmatrix} \alpha \\ \beta \end{pmatrix}$$

## Bloch Sphere Representation

Any single qubit state can be represented on the **Bloch sphere** using angles $\theta$ and $\phi$:

$$|\psi\rangle = \cos\frac{\theta}{2}|0\rangle + e^{i\phi}\sin\frac{\theta}{2}|1\rangle$$

Where:

- $\theta \in [0, \pi]$ is the polar angle
- $\phi \in [0, 2\pi)$ is the azimuthal angle

### Important Points on the Bloch Sphere

- **North pole**: $|0\rangle$ (computational basis state)
- **South pole**: $|1\rangle$ (computational basis state)  
- **Equator**: Superposition states like $|+\rangle, |-\rangle$

## Multi-Qubit Systems

For $n$ qubits, the state space has dimension $2^n$. The state vector has $2^n$ complex amplitudes.

### Two-Qubit System

A general two-qubit state is:

$$|\psi\rangle = \alpha_{00}|00\rangle + \alpha_{01}|01\rangle + \alpha_{10}|10\rangle + \alpha_{11}|11\rangle$$

In vector form:

$$|\psi\rangle = \begin{pmatrix} \alpha_{00} \\ \alpha_{01} \\ \alpha_{10} \\ \alpha_{11} \end{pmatrix}$$

### Computational Basis for Two Qubits

$$|00\rangle = \begin{pmatrix} 1 \\ 0 \\ 0 \\ 0 \end{pmatrix}, |01\rangle = \begin{pmatrix} 0 \\ 1 \\ 0 \\ 0 \end{pmatrix}, |10\rangle = \begin{pmatrix} 0 \\ 0 \\ 1 \\ 0 \end{pmatrix}, |11\rangle = \begin{pmatrix} 0 \\ 0 \\ 0 \\ 1 \end{pmatrix}$$

## State Properties

### Normalization

All quantum states must be normalized:

$$\langle\psi|\psi\rangle = \sum_i |\alpha_i|^2 = 1$$

### Orthogonality

Computational basis states are orthonormal:

$$\langle i|j\rangle = \delta_{ij}$$

Where $\delta_{ij}$ is the Kronecker delta.

## Examples in the Simulator

### Creating a Qubit in |0⟩ State

```python
from quantum_simulator import QuantumSimulator

# Create single qubit in |0⟩ state
sim = QuantumSimulator(1)
print(sim.get_state_vector())  # [1.0, 0.0]
```

### Two-Qubit System in |00⟩ State

```python
# Create two qubits in |00⟩ state  
sim = QuantumSimulator(2)
print(sim.get_state_vector())  # [1.0, 0.0, 0.0, 0.0]
```

The simulator stores quantum states as complex numpy arrays, where each element represents the probability amplitude for the corresponding computational basis state.