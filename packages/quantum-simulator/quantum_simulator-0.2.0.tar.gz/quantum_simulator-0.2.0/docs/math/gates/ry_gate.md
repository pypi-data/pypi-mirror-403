# RY Gate (Y-Rotation)

The **RY gate** performs a rotation around the Y-axis of the Bloch sphere. It's one of the fundamental single-qubit rotation gates and is essential for creating arbitrary quantum states and implementing quantum algorithms.

## Mathematical Definition

The RY gate with rotation angle θ is defined by the matrix:

$$R_y(\theta) = \begin{pmatrix}
\cos(\theta/2) & -\sin(\theta/2) \\
\sin(\theta/2) & \cos(\theta/2)
\end{pmatrix}$$

## Action on Basis States

- $R_y(\theta)|0\rangle = \cos(\theta/2)|0\rangle + \sin(\theta/2)|1\rangle$
- $R_y(\theta)|1\rangle = -\sin(\theta/2)|0\rangle + \cos(\theta/2)|1\rangle$

## Geometric Interpretation

The RY gate rotates the qubit state vector around the Y-axis of the Bloch sphere by angle θ:

- **θ = 0**: Identity operation (no rotation)
- **θ = π/2**: Rotates |0⟩ to (|0⟩ + |1⟩)/√2 (plus state)
- **θ = π**: Equivalent to X gate (bit flip)
- **θ = 3π/2**: Rotates |0⟩ to (|0⟩ - |1⟩)/√2 (minus state)

## Usage in Quantum Simulator

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import RY
import numpy as np

# Create RY gate with specific angle
theta = np.pi/4  # 45-degree rotation
ry_gate = RY(theta)

# Apply to qubit
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(ry_gate, [0])
circuit.execute(sim)

print(f"State after RY(π/4): {sim.get_state_vector()}")
```

## Special Cases

### Pre-defined RY Gates for W States

The simulator includes pre-computed RY gates for W state construction:

```python
from quantum_simulator.gates import RY_W1, RY_W2

# RY_W1: θ = arccos(√(2/3)) ≈ 0.955 radians
# RY_W2: θ = arccos(√(1/2)) = π/4 radians

sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(RY_W1, [0])  # For W state construction
circuit.execute(sim)
```

## Common Applications

1. **State Preparation**: Creating arbitrary superposition states
2. **Variational Circuits**: Parameterized gates in VQE and QAOA
3. **W State Construction**: Essential for symmetric entangled states
4. **Quantum Machine Learning**: Feature encoding and variational layers
5. **Quantum Control**: Fine-tuning qubit rotations

## Properties

- **Unitary**: $R_y(\theta)^\dagger R_y(\theta) = I$
- **Hermitian**: $R_y(\pi/2)^\dagger = R_y(-\pi/2)$
- **Periodic**: $R_y(\theta + 2\pi) = R_y(\theta)$
- **Commutes with Z rotations**: $[R_y(\theta), R_z(\phi)] = 0$

## Relationship to Other Gates

- **Hadamard**: $H = R_y(\pi/2) \cdot R_z(\pi)$
- **X Gate**: $X = R_y(\pi)$
- **Y Gate**: $Y = i \cdot R_y(\pi)$

## Circuit Symbol

```
|ψ⟩ ──RY(θ)── |ψ'⟩
```

The RY gate is fundamental for quantum state manipulation and appears in most quantum algorithms requiring continuous parameter control.