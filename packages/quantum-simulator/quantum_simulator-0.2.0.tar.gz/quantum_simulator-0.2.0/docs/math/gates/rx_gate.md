# RX Gate (X-Rotation)

The **RX gate** performs a rotation around the X-axis of the Bloch sphere. It's one of the fundamental single-qubit rotation gates that, together with RY and RZ, forms a complete set for arbitrary single-qubit rotations.

## Mathematical Definition

The RX gate with rotation angle θ is defined by the matrix:

$$R_x(\theta) = \begin{pmatrix}
\cos(\theta/2) & -i\sin(\theta/2) \\
-i\sin(\theta/2) & \cos(\theta/2)
\end{pmatrix}$$

## Action on Basis States

- $R_x(\theta)|0\rangle = \cos(\theta/2)|0\rangle - i\sin(\theta/2)|1\rangle$
- $R_x(\theta)|1\rangle = -i\sin(\theta/2)|0\rangle + \cos(\theta/2)|1\rangle$

## Geometric Interpretation

The RX gate rotates the qubit state vector around the X-axis of the Bloch sphere by angle θ:

- **θ = 0**: Identity operation (no rotation)
- **θ = π/2**: Rotates around X-axis by 90°, equivalent to $\frac{1}{\sqrt{2}}(X + I)$
- **θ = π**: Equivalent to X gate (bit flip)
- **θ = 2π**: Full rotation, returns to original state (up to global phase)

## Usage in Quantum Simulator

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import RX
import numpy as np

# Create RX gate with specific angle
theta = np.pi/3  # 60-degree rotation
rx_gate = RX(theta)

# Apply to qubit
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(rx_gate, [0])
circuit.execute(sim)

print(f"State after RX(π/3): {sim.get_state_vector()}")
```

## Relationship to Pauli-X Gate

The RX gate generalizes the Pauli-X gate:

```python
from quantum_simulator.gates import RX, X_GATE
import numpy as np

# X gate is RX(π)
x_equivalent = RX(np.pi)

# These should produce the same results (up to global phase)
sim1 = QuantumSimulator(1)
sim2 = QuantumSimulator(1)

circuit1 = QuantumCircuit(1)
circuit1.add_gate(X_GATE, [0])
circuit1.execute(sim1)

circuit2 = QuantumCircuit(1)
circuit2.add_gate(x_equivalent, [0])
circuit2.execute(sim2)
```

## Common Applications

1. **Arbitrary State Preparation**: Combined with RY and RZ for universal single-qubit control
2. **Quantum Algorithms**: Rotation sequences in optimization algorithms
3. **Error Correction**: Correcting bit-flip errors with controlled rotations
4. **Quantum Machine Learning**: Parameterized circuits and feature maps
5. **Adiabatic Evolution**: Smooth state transitions in quantum annealing

## Properties

- **Unitary**: $R_x(\theta)^\dagger R_x(\theta) = I$
- **Hermitian**: $R_x(\theta)^\dagger = R_x(-\theta)$
- **Periodic**: $R_x(\theta + 2\pi) = R_x(\theta)$ (up to global phase)
- **Composition**: $R_x(\theta_1)R_x(\theta_2) = R_x(\theta_1 + \theta_2)$

## Universal Single-Qubit Rotations

Any single-qubit unitary can be decomposed using RX, RY, and RZ gates:

$$U = e^{i\alpha} R_z(\gamma) R_y(\beta) R_z(\delta)$$

or alternatively:

$$U = e^{i\alpha} R_z(\gamma) R_x(\beta) R_z(\delta)$$

```python
# Example: Arbitrary single-qubit rotation
from quantum_simulator.gates import RX, RY, RZ
import numpy as np

def arbitrary_rotation(alpha, beta, gamma):
    """Create circuit for arbitrary single-qubit rotation."""
    circuit = QuantumCircuit(1)
    circuit.add_gate(RZ(gamma), [0])
    circuit.add_gate(RY(beta), [0])
    circuit.add_gate(RZ(alpha), [0])
    return circuit
```

## Bloch Sphere Visualization

On the Bloch sphere, RX rotations:
- Keep states on the YZ plane fixed on their meridians
- Rotate the +Z axis toward +Y axis for positive θ
- Are particularly useful for creating and manipulating states in the XY plane

## Special Angles

- **RX(π/2)**: Creates superposition when applied to |0⟩: $(|0\rangle - i|1\rangle)/\sqrt{2}$
- **RX(π)**: Bit flip operation (equivalent to X gate)
- **RX(π/4)**: Common in quantum algorithms, creates $(|0\rangle - i|1\rangle/\sqrt{2})/\sqrt{2}$

## Circuit Symbol

```
|ψ⟩ ──RX(θ)── |ψ'⟩
```

The RX gate completes the set of fundamental rotation gates and is essential for achieving universal quantum computation when combined with RY and RZ gates.