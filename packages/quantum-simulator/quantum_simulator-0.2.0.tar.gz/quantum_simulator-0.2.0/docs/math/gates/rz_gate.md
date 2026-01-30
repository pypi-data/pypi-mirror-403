# RZ Gate (Z-Rotation)

The **RZ gate** performs a rotation around the Z-axis of the Bloch sphere. It applies a phase shift to the |1⟩ component while leaving the |0⟩ component unchanged, making it essential for phase manipulation in quantum algorithms.

## Mathematical Definition

The RZ gate with rotation angle θ is defined by the matrix:

$$R_z(\theta) = \begin{pmatrix}
e^{-i\theta/2} & 0 \\
0 & e^{i\theta/2}
\end{pmatrix}$$

Alternatively, up to a global phase, it can be written as:

$$R_z(\theta) = \begin{pmatrix}
1 & 0 \\
0 & e^{i\theta}
\end{pmatrix}$$

## Action on Basis States

- $R_z(\theta)|0\rangle = e^{-i\theta/2}|0\rangle$
- $R_z(\theta)|1\rangle = e^{i\theta/2}|1\rangle$

For a general state $\alpha|0\rangle + \beta|1\rangle$:

$$R_z(\theta)(\alpha|0\rangle + \beta|1\rangle) = \alpha e^{-i\theta/2}|0\rangle + \beta e^{i\theta/2}|1\rangle$$

## Geometric Interpretation

The RZ gate rotates the qubit state vector around the Z-axis of the Bloch sphere by angle θ:

- **θ = 0**: Identity operation
- **θ = π/2**: S gate (phase gate)
- **θ = π**: Z gate (phase flip)
- **θ = π/4**: T gate (π/8 gate)

## Usage in Quantum Simulator

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import RZ, H_GATE
import numpy as np

# Create RZ gate with specific angle
theta = np.pi/4  # π/4 rotation (T gate)
rz_gate = RZ(theta)

# Apply to superposition state to see phase effect
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)

# Create superposition first
circuit.add_gate(H_GATE, [0])  # |+⟩ = (|0⟩ + |1⟩)/√2

# Apply phase rotation
circuit.add_gate(rz_gate, [0])  # Adds phase to |1⟩ component

circuit.execute(sim)
print(f"State after H then RZ(π/4): {sim.get_state_vector()}")
```

## Special Cases

### Common Phase Gates

```python
from quantum_simulator.gates import RZ
import numpy as np

# S gate (Phase gate): RZ(π/2)
s_gate = RZ(np.pi/2)

# T gate (π/8 gate): RZ(π/4)  
t_gate = RZ(np.pi/4)

# Z gate (Phase flip): RZ(π)
z_gate = RZ(np.pi)

# Custom phase rotation
custom_phase = RZ(np.pi/6)  # 30-degree phase rotation
```

## Common Applications

1. **Phase Manipulation**: Adding relative phases between |0⟩ and |1⟩
2. **Quantum Fourier Transform**: Essential for QFT implementations
3. **Quantum Phase Estimation**: Phase kickback and controlled rotations
4. **Variational Algorithms**: Parameter optimization in quantum circuits
5. **Error Correction**: Phase error correction protocols
6. **Quantum Chemistry**: Molecular simulation and phase evolution

## Properties

- **Diagonal**: Only affects phases, not populations
- **Unitary**: $R_z(\theta)^\dagger R_z(\theta) = I$
- **Commutative**: $R_z(\theta_1) R_z(\theta_2) = R_z(\theta_1 + \theta_2)$
- **Inverse**: $R_z(\theta)^{-1} = R_z(-\theta)$
- **Global Phase**: Often written with global phase $e^{i\theta/2}$ factored out

## Controlled RZ Gates

The RZ gate is commonly used in controlled operations:

```python
# Controlled-RZ gates are used in QFT and other algorithms
# CRZ applies RZ to target only when control is |1⟩

# In quantum algorithms, controlled phases are crucial:
# |00⟩ → |00⟩
# |01⟩ → |01⟩  
# |10⟩ → |10⟩
# |11⟩ → e^{iθ}|11⟩
```

## Relationship to Other Gates

- **Z Gate**: $Z = R_z(\pi)$
- **S Gate**: $S = R_z(\pi/2)$
- **T Gate**: $T = R_z(\pi/4)$
- **Phase Gate**: $P(\phi) = R_z(\phi)$ (up to global phase)

## Circuit Symbol

```
|ψ⟩ ──RZ(θ)── |ψ'⟩
```

Or for specific cases:
```
|ψ⟩ ──S── |ψ'⟩    (θ = π/2)
|ψ⟩ ──T── |ψ'⟩    (θ = π/4)  
|ψ⟩ ──Z── |ψ'⟩    (θ = π)
```

The RZ gate is fundamental for phase control and appears in virtually all quantum algorithms requiring precise phase manipulation, making it one of the most important single-qubit gates in quantum computing.