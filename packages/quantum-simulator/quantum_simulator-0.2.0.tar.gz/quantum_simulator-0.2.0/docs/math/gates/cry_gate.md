# Controlled RY Gate (CRY)

The **Controlled RY gate** is a two-qubit gate that applies an RY rotation to a target qubit only when the control qubit is in the |1⟩ state. It's essential for creating complex entangled states and implementing conditional quantum operations.

## Mathematical Definition

The CRY gate with rotation angle θ is defined by the 4×4 matrix:

$$\text{CRY}(\theta) = \begin{pmatrix}
1 & 0 & 0 & 0 \\
0 & 1 & 0 & 0 \\
0 & 0 & \cos(\theta/2) & -\sin(\theta/2) \\
0 & 0 & \sin(\theta/2) & \cos(\theta/2)
\end{pmatrix}$$

This can be understood as:

$$\text{CRY}(\theta) = |0\rangle\langle 0| \otimes I + |1\rangle\langle 1| \otimes R_y(\theta)$$

## Action on Basis States

- $\text{CRY}(\theta)|00\rangle = |00\rangle$ (no change)
- $\text{CRY}(\theta)|01\rangle = |01\rangle$ (no change)
- $\text{CRY}(\theta)|10\rangle = \cos(\theta/2)|10\rangle + \sin(\theta/2)|11\rangle$
- $\text{CRY}(\theta)|11\rangle = -\sin(\theta/2)|10\rangle + \cos(\theta/2)|11\rangle$

## Quantum Circuit Representation

```
Control ──●──
          │
Target  ──RY(θ)──
```

The control qubit (●) determines whether the rotation is applied to the target qubit.

## Usage in Quantum Simulator

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import H_GATE, CRY_W, controlled_RY
import numpy as np

# Using pre-defined CRY gate for W states
sim = QuantumSimulator(2)
circuit = QuantumCircuit(2)

# Create superposition on control qubit
circuit.add_gate(H_GATE, [0])  # Control in (|0⟩ + |1⟩)/√2

# Apply controlled rotation
circuit.add_gate(CRY_W, [0, 1])  # CRY with θ = π/4

circuit.execute(sim)
print(f"State after H and CRY: {sim.get_state_vector()}")

# Creating custom CRY gates
custom_angle = np.pi/6
custom_cry = controlled_RY(custom_angle)

circuit2 = QuantumCircuit(2)
circuit2.add_gate(H_GATE, [0])
circuit2.add_gate(custom_cry, [0, 1])
circuit2.execute(sim)
```

## W State Construction

The CRY gate is crucial for creating 3-qubit W states:

```python
from quantum_simulator.gates import RY_W1, CRY_W, CNOT_GATE

# Complete W state circuit
sim = QuantumSimulator(3)
circuit = QuantumCircuit(3)

# Step 1: RY rotation on qubit 0
circuit.add_gate(RY_W1, [0])  # θ = arccos(√(2/3))

# Step 2: Controlled RY on qubits 0→1  
circuit.add_gate(CRY_W, [0, 1])  # θ = π/4

# Step 3: CNOT gates to complete W state
circuit.add_gate(CNOT_GATE, [1, 2])
circuit.add_gate(CNOT_GATE, [0, 2])

circuit.execute(sim)
# Results in |W⟩ = (|001⟩ + |010⟩ + |100⟩)/√3
```

## Conditional Logic

The CRY gate implements quantum conditional logic:

```python
# If control qubit is |0⟩: target unchanged
# If control qubit is |1⟩: target rotated by θ

# This allows for quantum branching and conditional operations
def conditional_rotation_demo():
    sim = QuantumSimulator(2)
    
    # Test with control = |0⟩
    circuit1 = QuantumCircuit(2)
    # Control stays |0⟩, target in superposition
    circuit1.add_gate(H_GATE, [1])  # Target = (|0⟩ + |1⟩)/√2
    circuit1.add_gate(CRY_W, [0, 1])  # No rotation applied
    circuit1.execute(sim)
    print("Control |0⟩:", sim.get_state_vector())
    
    # Test with control = |1⟩  
    sim.reset()
    circuit2 = QuantumCircuit(2)
    circuit2.add_gate(X_GATE, [0])   # Control = |1⟩
    circuit2.add_gate(H_GATE, [1])   # Target = (|0⟩ + |1⟩)/√2
    circuit2.add_gate(CRY_W, [0, 1])  # Rotation applied
    circuit2.execute(sim)
    print("Control |1⟩:", sim.get_state_vector())
```

## Applications

1. **W State Creation**: Essential component for symmetric entangled states
2. **Quantum Algorithms**: Conditional operations in quantum search and optimization
3. **Variational Circuits**: Parameterized entangling operations
4. **Quantum Machine Learning**: Feature-dependent rotations
5. **Error Correction**: Conditional syndrome corrections
6. **Quantum Control**: Implementing quantum if-then logic

## Properties

- **Unitary**: $\text{CRY}(\theta)^\dagger \text{CRY}(\theta) = I$
- **Controlled Unitary**: Generalizes single-qubit RY to controlled operation
- **Reversible**: $\text{CRY}(\theta)^{-1} = \text{CRY}(-\theta)$
- **Commutes with Control Operations**: Commutes with operations only on control qubit

## Decomposition

CRY can be decomposed using CNOT and single-qubit rotations:

```
Control ──────●─────●──
              │     │
Target  ──RY(θ/2)──⊕──RY(-θ/2)──⊕──RY(θ/2)──
```

## Special Cases

### Pre-defined for W States

```python
from quantum_simulator.gates import CRY_W

# CRY_W uses θ = π/4 = arccos(√(1/2))
# Specifically designed for W state construction
# Creates perfect 1/√2 amplitude distribution
```

## Relationship to Other Gates

- **CNOT**: $\text{CNOT} = \text{CRY}(\pi)$ (up to basis rotation)
- **Controlled-Z**: Related through basis transformations
- **CRX, CRZ**: Other controlled rotations around different axes

## Circuit Symbol Variations

```
Control ──●──     or     ──●──
          │              │
Target  ──RY(θ)──      ──○──RY(θ)
```

The CRY gate bridges single-qubit rotations and multi-qubit entanglement, making it indispensable for creating complex quantum states and implementing sophisticated quantum algorithms.