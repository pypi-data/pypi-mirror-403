# CZ Gate (Controlled-Z)

The **CZ gate** (Controlled-Z or Controlled Phase Flip) is a fundamental two-qubit quantum gate that applies a phase flip to the target qubit only when the control qubit is in the |1⟩ state. It's essential for quantum algorithms, particularly Grover's algorithm and quantum error correction.

## Mathematical Definition

The CZ gate is defined by the 4×4 matrix:

$$\text{CZ} = \begin{pmatrix}
1 & 0 & 0 & 0 \\
0 & 1 & 0 & 0 \\
0 & 0 & 1 & 0 \\
0 & 0 & 0 & -1
\end{pmatrix}$$

This can be understood as:

$$\text{CZ} = |0\rangle\langle 0| \otimes I + |1\rangle\langle 1| \otimes Z$$

## Action on Basis States

- $\text{CZ}|00\rangle = |00\rangle$ (no change)
- $\text{CZ}|01\rangle = |01\rangle$ (no change)
- $\text{CZ}|10\rangle = |10\rangle$ (no change)
- $\text{CZ}|11\rangle = -|11\rangle$ (phase flip)

## Quantum Circuit Representation

```
Control ──●──
          │
Target  ──●──
```

Both qubits have the same symbol (●) because the CZ gate is **symmetric** - swapping control and target gives the same result.

## Usage in Quantum Simulator

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import H_GATE, X_GATE, CZ_GATE
import numpy as np

# Basic CZ gate application
sim = QuantumSimulator(2)
circuit = QuantumCircuit(2)

# Prepare |11⟩ state to see phase flip
circuit.add_gate(X_GATE, [0])  # |01⟩
circuit.add_gate(X_GATE, [1])  # |11⟩
circuit.add_gate(CZ_GATE, [0, 1])  # Apply CZ

circuit.execute(sim)
print(f"CZ|11⟩ = {sim.get_state_vector()}")  # Should show phase flip

# Demonstrate phase effect with superposition
def demonstrate_cz_phase():
    """Show CZ phase effect using quantum interference."""
    sim = QuantumSimulator(2)
    circuit = QuantumCircuit(2)
    
    # Create Bell-like superposition
    circuit.add_gate(H_GATE, [0])  # (|0⟩ + |1⟩)/√2
    circuit.add_gate(H_GATE, [1])  # Equal superposition on both qubits
    
    # Apply CZ - only affects |11⟩ component
    circuit.add_gate(CZ_GATE, [0, 1])
    
    # Rotate back to see interference
    circuit.add_gate(H_GATE, [0])
    circuit.add_gate(H_GATE, [1])
    
    circuit.execute(sim)
    print(f"After CZ interference: {sim.get_state_vector()}")

demonstrate_cz_phase()
```

## Key Properties

### Symmetry
The CZ gate is **symmetric** under qubit exchange:

$$\text{CZ}_{ij} = \text{CZ}_{ji}$$

This means CZ(control=0, target=1) = CZ(control=1, target=0).

### Self-Inverse
The CZ gate is **self-inverse**:

$$\text{CZ}^2 = I$$

Applying CZ twice returns to the original state.

### Diagonal Matrix
CZ is a **diagonal gate** - it only affects phases, not probability amplitudes:

- Preserves computational basis state populations
- Only changes relative phases between states

## Relationship to Other Gates

### Controlled-Z via CRZ
CZ is equivalent to CRZ(π):
```python
from quantum_simulator.gates import controlled_RZ
import numpy as np

cz_equivalent = controlled_RZ(np.pi)
# This is equivalent to CZ_GATE (up to global phase)
```

### CZ from CNOT and Hadamard
CZ can be constructed from CNOT:
```
──H──●──H── = ──●──
     │         │
──H──⊕──H──   ──●──
```

```python
def cz_from_cnot():
    """Construct CZ using CNOT and Hadamard gates."""
    sim = QuantumSimulator(2)
    circuit = QuantumCircuit(2)
    
    # Prepare test state |11⟩
    circuit.add_gate(X_GATE, [0])
    circuit.add_gate(X_GATE, [1])
    
    # CZ implementation using CNOT
    circuit.add_gate(H_GATE, [1])     # H on target
    circuit.add_gate(CNOT_GATE, [0, 1])  # CNOT
    circuit.add_gate(H_GATE, [1])     # H on target
    
    circuit.execute(sim)
    return sim.get_state_vector()
```

## Applications in Quantum Algorithms

### Grover's Algorithm
CZ gates are essential for implementing Grover's diffusion operator:

```python
def grover_diffusion_2q():
    """Implement 2-qubit Grover diffusion operator."""
    circuit = QuantumCircuit(2)
    
    # Step 1: Apply H to all qubits
    circuit.add_gate(H_GATE, [0])
    circuit.add_gate(H_GATE, [1])
    
    # Step 2: Apply X to all qubits
    circuit.add_gate(X_GATE, [0])
    circuit.add_gate(X_GATE, [1])
    
    # Step 3: Apply CZ (controlled phase flip)
    circuit.add_gate(CZ_GATE, [0, 1])
    
    # Step 4: Apply X to all qubits (undo step 2)
    circuit.add_gate(X_GATE, [0])
    circuit.add_gate(X_GATE, [1])
    
    # Step 5: Apply H to all qubits (undo step 1)
    circuit.add_gate(H_GATE, [0])
    circuit.add_gate(H_GATE, [1])
    
    return circuit
```

### Quantum Error Correction
CZ gates are used in stabilizer codes for phase error detection:

```python
def phase_error_syndrome():
    """Detect phase errors using CZ gates."""
    # Implementation would use CZ for syndrome extraction
    pass
```

### Bell State Preparation
Different Bell states using CZ:

```python
def bell_states_with_cz():
    """Create Bell states using CZ instead of CNOT."""
    # |Φ⁺⟩ = (|00⟩ + |11⟩)/√2
    circuit1 = QuantumCircuit(2)
    circuit1.add_gate(H_GATE, [0])
    circuit1.add_gate(H_GATE, [1])
    circuit1.add_gate(CZ_GATE, [0, 1])
    circuit1.add_gate(H_GATE, [1])
    
    return circuit1
```

## Properties and Identities

### Commutation Relations
CZ commutes with Z operations on either qubit:

$$[\text{CZ}, Z \otimes I] = 0$$

$$[\text{CZ}, I \otimes Z] = 0$$

### Conjugation by Hadamard

$$(H \otimes H) \text{CZ} (H \otimes H) = \text{CNOT}$$

This shows the deep relationship between CZ and CNOT gates.

### Phase Kickback
When the target is in a Z-eigenstate, the phase kicks back to the control:

```python
def demonstrate_phase_kickback():
    """Show phase kickback with CZ gate."""
    sim = QuantumSimulator(2)
    circuit = QuantumCircuit(2)
    
    # Control in superposition
    circuit.add_gate(H_GATE, [0])  # (|0⟩ + |1⟩)/√2
    
    # Target in |1⟩ (Z eigenstate with eigenvalue -1)
    circuit.add_gate(X_GATE, [1])
    
    # Apply CZ - phase kicks back to control
    circuit.add_gate(CZ_GATE, [0, 1])
    
    # Observe kickback via interference
    circuit.add_gate(H_GATE, [0])
    
    circuit.execute(sim)
    return sim.get_state_vector()
```

## Implementation Advantages

### Efficiency
- **Diagonal structure** makes CZ gates often easier to implement physically
- **Symmetric nature** simplifies circuit design
- **Phase-only operations** preserve state magnitudes

### Universality
- CZ + single-qubit gates form a **universal gate set**
- Can implement any quantum algorithm
- Natural for many quantum error correction protocols

## Circuit Symbol Variations

```
Standard:    ──●──    or    ──●──    or    Control ──●──
             │             │              Target  ──●──

Alternative: ──CZ──         ──Z──
             ──CZ──         ──●──
```

## Physical Implementation

CZ gates are often **native operations** in many quantum computing platforms:

- **Superconducting qubits**: Natural interaction via tunable coupling
- **Trapped ions**: Implemented via Mølmer-Sørensen gates
- **Photonic systems**: Via linear optical elements

The CZ gate's diagonal nature and symmetry make it fundamental for quantum computing, providing clean phase relationships essential for quantum interference and algorithm implementation.