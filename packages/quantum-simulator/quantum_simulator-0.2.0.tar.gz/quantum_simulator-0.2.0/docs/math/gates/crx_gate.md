# Controlled RX Gate (CRX)

The **Controlled RX gate** is a two-qubit gate that applies an RX rotation to a target qubit only when the control qubit is in the |1⟩ state. It performs conditional rotations around the X-axis of the Bloch sphere, making it essential for quantum algorithms requiring X-axis conditional control.

## Mathematical Definition

The CRX gate with rotation angle θ is defined by the 4×4 matrix:

$$\text{CRX}(\theta) = \begin{pmatrix}
1 & 0 & 0 & 0 \\
0 & 1 & 0 & 0 \\
0 & 0 & \cos(\theta/2) & -i\sin(\theta/2) \\
0 & 0 & -i\sin(\theta/2) & \cos(\theta/2)
\end{pmatrix}$$

This can be understood as:

$$\text{CRX}(\theta) = |0\rangle\langle 0| \otimes I + |1\rangle\langle 1| \otimes R_x(\theta)$$

## Action on Basis States

- $\text{CRX}(\theta)|00\rangle = |00\rangle$ (no change)
- $\text{CRX}(\theta)|01\rangle = |01\rangle$ (no change)
- $\text{CRX}(\theta)|10\rangle = \cos(\theta/2)|10\rangle - i\sin(\theta/2)|11\rangle$
- $\text{CRX}(\theta)|11\rangle = -i\sin(\theta/2)|10\rangle + \cos(\theta/2)|11\rangle$

## Quantum Circuit Representation

```
Control ──●──
          │
Target  ──RX(θ)──
```

The control qubit (●) determines whether the X-rotation is applied to the target qubit.

## Usage in Quantum Simulator

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import H_GATE, X_GATE, controlled_RX
import numpy as np

# Create a CRX gate with specific angle
theta = np.pi/3  # 60-degree rotation
crx_gate = controlled_RX(theta)

# Apply to qubits
sim = QuantumSimulator(2)
circuit = QuantumCircuit(2)

# Create superposition on control qubit
circuit.add_gate(H_GATE, [0])  # Control in (|0⟩ + |1⟩)/√2

# Apply controlled X-rotation
circuit.add_gate(crx_gate, [0, 1])

circuit.execute(sim)
print(f"State after H and CRX: {sim.get_state_vector()}")

# Test conditional behavior
def test_conditional_behavior():
    # Control = |0⟩: no rotation applied
    sim1 = QuantumSimulator(2)
    circuit1 = QuantumCircuit(2)
    circuit1.add_gate(H_GATE, [1])  # Target in superposition
    circuit1.add_gate(crx_gate, [0, 1])  # No effect since control = |0⟩
    circuit1.execute(sim1)
    print("Control |0⟩:", sim1.get_state_vector())
    
    # Control = |1⟩: rotation applied
    sim2 = QuantumSimulator(2)
    circuit2 = QuantumCircuit(2)
    circuit2.add_gate(X_GATE, [0])   # Control = |1⟩
    circuit2.add_gate(H_GATE, [1])   # Target in superposition
    circuit2.add_gate(crx_gate, [0, 1])  # Rotation applied
    circuit2.execute(sim2)
    print("Control |1⟩:", sim2.get_state_vector())

test_conditional_behavior()
```

## Special Angles and Cases

### Common Rotation Angles

```python
import numpy as np
from quantum_simulator.gates import controlled_RX

# π/2 rotation (quarter turn around X-axis)
crx_pi_2 = controlled_RX(np.pi/2)

# π rotation (half turn, equivalent to controlled X gate)
crx_pi = controlled_RX(np.pi)

# π/4 rotation (eighth turn)
crx_pi_4 = controlled_RX(np.pi/4)

# Custom angle
crx_custom = controlled_RX(2*np.pi/3)
```

### Relationship to Controlled-X (CNOT)

The CRX(π) gate is equivalent to a CNOT gate up to basis rotations:

```python
# CRX(π) applies X rotation when control is |1⟩
# This is similar to CNOT but with phase factors
crx_pi = controlled_RX(np.pi)

# For comparison with CNOT behavior
from quantum_simulator.gates import CNOT_GATE
```

## Applications

1. **Quantum Error Correction**: Conditional bit-flip corrections
2. **Variational Quantum Algorithms**: Parameterized entangling operations
3. **Quantum Machine Learning**: Feature-dependent X-rotations
4. **Quantum Control**: Implementing conditional bit operations
5. **State Preparation**: Creating complex entangled states
6. **Quantum Simulation**: Modeling conditional interactions

## Geometric Interpretation

On the Bloch sphere, the CRX gate:
- Leaves the target qubit unchanged when control is |0⟩
- Rotates the target qubit around the X-axis when control is |1⟩
- Creates entanglement between control and target qubits
- Particularly useful for creating states in the YZ plane of the target

## Properties

- **Unitary**: $\text{CRX}(\theta)^\dagger \text{CRX}(\theta) = I$
- **Controlled Unitary**: Generalizes single-qubit RX to controlled operation
- **Reversible**: $\text{CRX}(\theta)^{-1} = \text{CRX}(-\theta)$
- **Hermitian for θ = π**: $\text{CRX}(\pi)^\dagger = \text{CRX}(\pi)$
- **Commutes with Z operations on control**: Compatible with control qubit Z-basis operations

## Decomposition

CRX can be decomposed using CNOT and single-qubit rotations:

```
Control ──────────●─────●──────────
                  │     │
Target  ──RY(-π/2)──⊕──RY(π/2)──RZ(θ)──⊕──RZ(-θ)──
```

Alternatively, using Hadamard gates to change basis:

```
Control ──────●─────
              │
Target  ──H──RZ(θ)──H──
```

## Quantum Algorithm Applications

### Conditional State Preparation

```python
def conditional_state_prep(angle1, angle2):
    """Create states based on control qubit value."""
    sim = QuantumSimulator(2)
    circuit = QuantumCircuit(2)
    
    # Create superposition on control
    circuit.add_gate(H_GATE, [0])
    
    # Different X-rotations based on control
    circuit.add_gate(controlled_RX(angle1), [0, 1])
    
    return sim, circuit

# Usage in quantum algorithms
sim, circuit = conditional_state_prep(np.pi/3, np.pi/6)
circuit.execute(sim)
```

### Quantum Feature Maps

```python
def feature_map_crx(features):
    """Encode classical features using CRX gates."""
    n_qubits = len(features)
    sim = QuantumSimulator(n_qubits)
    circuit = QuantumCircuit(n_qubits)
    
    # Initialize superposition
    for i in range(n_qubits):
        circuit.add_gate(H_GATE, [i])
    
    # Apply feature-dependent rotations
    for i in range(n_qubits-1):
        crx = controlled_RX(features[i] * np.pi)
        circuit.add_gate(crx, [i, i+1])
    
    return sim, circuit
```

## Relationship to Other Gates

- **CNOT**: $\text{CNOT} \approx H_1 \cdot \text{CRX}(\pi) \cdot H_1$ (up to phases)
- **CRY, CRZ**: Other controlled rotations around different axes
- **Controlled-Phase**: Related through basis transformations
- **Toffoli**: CRX can be part of multi-controlled constructions

## Circuit Symbol Variations

```
Control ──●──     or     ──●──
          │              │
Target  ──RX(θ)──      ──○──RX(θ)
```

## Phase Considerations

Unlike CRY and CRZ, the CRX gate introduces complex phase factors (involving i) in its matrix elements. This makes it particularly useful for:

- Creating states with specific phase relationships
- Implementing quantum interferometry protocols  
- Building quantum circuits sensitive to X-axis rotations

The CRX gate provides essential X-axis conditional control, completing the set of controlled rotation gates and enabling comprehensive quantum state manipulation across all Bloch sphere axes.