# Controlled RZ Gate (CRZ)

The **Controlled RZ gate** is a two-qubit gate that applies an RZ rotation to a target qubit only when the control qubit is in the |1⟩ state. It performs conditional phase rotations around the Z-axis of the Bloch sphere, making it fundamental for quantum phase manipulation and quantum algorithms requiring conditional phase control.

## Mathematical Definition

The CRZ gate with rotation angle θ is defined by the 4×4 matrix:

$$\text{CRZ}(\theta) = \begin{pmatrix}
1 & 0 & 0 & 0 \\
0 & 1 & 0 & 0 \\
0 & 0 & e^{-i\theta/2} & 0 \\
0 & 0 & 0 & e^{i\theta/2}
\end{pmatrix}$$

This can be understood as:

$$\text{CRZ}(\theta) = |0\rangle\langle 0| \otimes I + |1\rangle\langle 1| \otimes R_z(\theta)$$

## Action on Basis States

- $\text{CRZ}(\theta)|00\rangle = |00\rangle$ (no change)
- $\text{CRZ}(\theta)|01\rangle = |01\rangle$ (no change)  
- $\text{CRZ}(\theta)|10\rangle = e^{-i\theta/2}|10\rangle$ (phase shift)
- $\text{CRZ}(\theta)|11\rangle = e^{i\theta/2}|11\rangle$ (opposite phase shift)

## Quantum Circuit Representation

```
Control ──●──
          │
Target  ──RZ(θ)──
```

The control qubit (●) determines whether the Z-rotation (phase shift) is applied to the target qubit.

## Usage in Quantum Simulator

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import H_GATE, X_GATE, controlled_RZ
import numpy as np

# Create a CRZ gate with specific angle
theta = np.pi/4  # 45-degree phase rotation
crz_gate = controlled_RZ(theta)

# Apply to qubits in superposition to see phase effects
sim = QuantumSimulator(2)
circuit = QuantumCircuit(2)

# Create superposition on both qubits
circuit.add_gate(H_GATE, [0])  # Control in (|0⟩ + |1⟩)/√2
circuit.add_gate(H_GATE, [1])  # Target in (|0⟩ + |1⟩)/√2

# Apply controlled Z-rotation
circuit.add_gate(crz_gate, [0, 1])

circuit.execute(sim)
print(f"State after H⊗H and CRZ: {sim.get_state_vector()}")

# Demonstrate phase effect visibility
def demonstrate_phase_effects():
    """Show how CRZ affects quantum interference."""
    sim = QuantumSimulator(2)
    circuit = QuantumCircuit(2)
    
    # Prepare Bell-like state
    circuit.add_gate(H_GATE, [0])
    circuit.add_gate(H_GATE, [1])
    
    # Apply phase rotation
    crz_pi = controlled_RZ(np.pi)  # π phase shift
    circuit.add_gate(crz_pi, [0, 1])
    
    # Measure interference by rotating back
    circuit.add_gate(H_GATE, [0])
    circuit.add_gate(H_GATE, [1])
    
    circuit.execute(sim)
    print("After phase rotation and interference:", sim.get_state_vector())

demonstrate_phase_effects()
```

## Special Angles and Applications

### Common Phase Rotations

```python
import numpy as np
from quantum_simulator.gates import controlled_RZ

# π/2 phase shift (S gate when control is |1⟩)
crz_s = controlled_RZ(np.pi/2)

# π phase shift (Z gate when control is |1⟩) 
crz_z = controlled_RZ(np.pi)

# π/4 phase shift (T gate when control is |1⟩)
crz_t = controlled_RZ(np.pi/4)

# Custom phase
crz_custom = controlled_RZ(np.pi/6)
```

### Quantum Fourier Transform

The CRZ gate is essential for the Quantum Fourier Transform (QFT):

```python
def qft_crz_demo(n_qubits=3):
    """Demonstrate CRZ usage in QFT-like circuits."""
    sim = QuantumSimulator(n_qubits)
    circuit = QuantumCircuit(n_qubits)
    
    # QFT uses controlled rotations with decreasing angles
    angles = [np.pi/2, np.pi/4, np.pi/8]  # 2π/2^k
    
    for i in range(n_qubits):
        circuit.add_gate(H_GATE, [i])
        
        # Apply controlled rotations
        for j in range(i+1, n_qubits):
            if j-i-1 < len(angles):
                crz = controlled_RZ(angles[j-i-1])
                circuit.add_gate(crz, [j, i])
    
    return sim, circuit

# Usage in QFT
sim, circuit = qft_crz_demo()
```

## Quantum Phase Estimation

CRZ gates are fundamental in quantum phase estimation algorithms:

```python
def phase_estimation_crz():
    """Use CRZ in phase estimation circuit."""
    sim = QuantumSimulator(3)
    circuit = QuantumCircuit(3)
    
    # Prepare eigenstate on target qubit
    circuit.add_gate(X_GATE, [2])  # |1⟩ eigenstate
    
    # Create superposition on control qubits
    circuit.add_gate(H_GATE, [0])
    circuit.add_gate(H_GATE, [1])
    
    # Apply controlled unitaries with different powers
    # U^1, U^2 where U adds phase θ to |1⟩
    phase = np.pi/3
    circuit.add_gate(controlled_RZ(phase), [1, 2])      # U^1
    circuit.add_gate(controlled_RZ(2*phase), [0, 2])    # U^2
    
    # Inverse QFT would follow here
    return sim, circuit
```

## Applications

1. **Quantum Fourier Transform**: Core component for frequency domain operations
2. **Phase Estimation**: Measuring unknown phases in quantum systems  
3. **Variational Algorithms**: Parameterized phase gates in optimization
4. **Quantum Chemistry**: Molecular phase evolution simulation
5. **Quantum Error Correction**: Phase error syndrome detection
6. **Quantum Machine Learning**: Phase-based feature encoding
7. **Quantum Cryptography**: Phase-dependent security protocols

## Geometric Interpretation

On the Bloch sphere, the CRZ gate:
- Leaves the target qubit unchanged when control is |0⟩
- Rotates the target qubit around the Z-axis when control is |1⟩
- Only affects relative phases, not probability amplitudes
- Creates phase-based entanglement between qubits

## Properties

- **Diagonal**: Only modifies phases, preserves probability distributions
- **Unitary**: $\text{CRZ}(\theta)^\dagger \text{CRZ}(\theta) = I$
- **Controlled Unitary**: Generalizes single-qubit RZ to controlled operation
- **Reversible**: $\text{CRZ}(\theta)^{-1} = \text{CRZ}(-\theta)$
- **Commutative**: $\text{CRZ}(\theta_1)\text{CRZ}(\theta_2) = \text{CRZ}(\theta_1 + \theta_2)$
- **Phase-only**: Preserves computational basis state populations

## Relationship to Controlled-Phase Gates

The CRZ gate is closely related to the controlled-phase (CPHASE) gate:

```python
# CRZ with global phase removed
def controlled_phase(phi):
    """Controlled phase gate equivalent to CRZ up to global phase."""
    return controlled_RZ(phi)

# Common controlled phase gates
cphase_s = controlled_RZ(np.pi/2)  # Controlled-S
cphase_t = controlled_RZ(np.pi/4)  # Controlled-T  
cphase_z = controlled_RZ(np.pi)    # Controlled-Z
```

## Decomposition

CRZ can be implemented using simpler gates:

### Using CNOT and RZ gates:
```
Control ──●─────●──
          │     │  
Target  ──⊕──RZ(θ/2)──⊕──RZ(-θ/2)──
```

### Alternative decomposition:
```
Control ──RZ(θ/2)──●──RZ(-θ/2)──
                   │
Target  ──RZ(θ/2)──⊕──RZ(θ/2)──
```

## Advanced Usage Patterns

### Phase Kickback

CRZ demonstrates quantum phase kickback when the target is an eigenstate:

```python
def phase_kickback_demo():
    """Demonstrate phase kickback with CRZ."""
    sim = QuantumSimulator(2)
    circuit = QuantumCircuit(2)
    
    # Control in superposition
    circuit.add_gate(H_GATE, [0])
    
    # Target as Z-eigenstate |1⟩ 
    circuit.add_gate(X_GATE, [1])
    
    # Phase kicks back to control qubit
    crz = controlled_RZ(np.pi/3)
    circuit.add_gate(crz, [0, 1])
    
    # Observe phase on control via interference
    circuit.add_gate(H_GATE, [0])
    
    circuit.execute(sim)
    return sim.get_state_vector()
```

### Multi-Controlled Z Rotations

CRZ can be extended to multi-controlled operations:

```python
def multi_controlled_z_rotation():
    """Build multi-controlled Z rotations using CRZ."""
    # Implementation would use additional ancilla qubits
    # and decompose into multiple CRZ gates
    pass
```

## Relationship to Other Gates

- **Controlled-Z**: $\text{CZ} = \text{CRZ}(\pi)$ (up to global phase)
- **CRX, CRY**: Other controlled rotations around different axes  
- **CNOT**: Related through basis transformations: $\text{CNOT} = H_1 \cdot \text{CZ} \cdot H_1$
- **Toffoli**: Can be built using multiple CRZ gates with ancillas

## Circuit Symbol Variations

```
Control ──●──     or     ──●──     or    ──●──
          │              │              │
Target  ──RZ(θ)──      ──○──RZ(θ)    ──Rφ(θ)──
```

## Quantum Algorithm Integration

### Shor's Algorithm
```python
# CRZ gates provide the controlled modular exponentiation
# in Shor's factoring algorithm through QFT
```

### Grover's Algorithm  
```python
# CRZ gates can implement the oracle and diffusion operator
# phase shifts in Grover's search algorithm
```

The CRZ gate is essential for quantum phase manipulation, providing precise control over relative phases in multi-qubit systems. Its diagonal nature makes it particularly valuable for algorithms requiring phase relationships while preserving computational basis populations.