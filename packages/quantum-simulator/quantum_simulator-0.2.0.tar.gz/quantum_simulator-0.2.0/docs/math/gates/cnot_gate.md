# CNOT Gate (Controlled-X)

The **CNOT gate** (Controlled-X or CX gate) is a fundamental two-qubit quantum gate that performs a **controlled bit-flip** operation. It's one of the most important gates in quantum computing, enabling entanglement creation and universal quantum computation.

## Matrix Representation

In the computational basis $\{|00\rangle, |01\rangle, |10\rangle, |11\rangle\}$:

$$\text{CNOT} = \begin{pmatrix}
1 & 0 & 0 & 0 \\
0 & 1 & 0 & 0 \\
0 & 0 & 0 & 1 \\
0 & 0 & 1 & 0
\end{pmatrix}$$

## Logical Operation

The CNOT gate applies an **X gate to the target qubit** when the control qubit is in state $|1\rangle$:

$$\text{CNOT}|c,t\rangle = |c, c \oplus t\rangle$$

Where $c$ is the control qubit, $t$ is the target qubit, and $\oplus$ denotes XOR (modulo-2 addition).

## Action on Basis States

$$\text{CNOT}|00\rangle = |00\rangle$$

$$\text{CNOT}|01\rangle = |01\rangle$$

$$\text{CNOT}|10\rangle = |11\rangle$$

$$\text{CNOT}|11\rangle = |10\rangle$$

### Summary

- **Control = 0**: Target qubit unchanged
- **Control = 1**: Target qubit flipped (X gate applied)

## Decomposition Form

The CNOT can be written as a **controlled unitary operation**:

$$\text{CNOT} = |0\rangle\langle 0| \otimes I + |1\rangle\langle 1| \otimes X$$

$$= \begin{pmatrix} I & 0 \\ 0 & X \end{pmatrix}$$

Where the control qubit determines which operation applies to the target.

## Circuit Symbol

```
Control ●─────
        │
Target  ⊕─────
```

The **filled circle** (●) represents the control qubit, and the **plus in circle** (⊕) represents the target qubit.

## Properties

### Involutory

$$\text{CNOT}^2 = I$$

CNOT is its own inverse: applying it twice returns to the original state.

### Hermitian

$$\text{CNOT}^\dagger = \text{CNOT}$$

### Asymmetric
Unlike controlled-Z gates, CNOT is **asymmetric** - swapping control and target gives a different gate (though related by Hadamards).

### Preserves Computational Basis
CNOT maps computational basis states to computational basis states (it's a **Clifford gate**).

## Entanglement Creation

CNOT is the **primary entangling gate** in quantum computing. When applied to separable states, it can create entangled states.

### Bell State Creation

Starting from $|00\rangle$:

$$|00\rangle \xrightarrow{H \otimes I} |+0\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |10\rangle)$$

$$|+0\rangle \xrightarrow{\text{CNOT}} \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle) = |\Phi^+\rangle$$

This creates the **Bell state** $|\Phi^+\rangle$, maximally entangled.

### General Entanglement

For input state $|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$ on control:

$$(\alpha|0\rangle + \beta|1\rangle) \otimes |0\rangle \xrightarrow{\text{CNOT}} \alpha|00\rangle + \beta|11\rangle$$

Creates entanglement whenever $\alpha, \beta \neq 0$.

## Universal Quantum Computing

CNOT + single-qubit gates form a **universal gate set**:

- Any quantum computation can be decomposed into CNOT and single-qubit rotations
- CNOT provides the necessary two-qubit interactions
- Single-qubit gates provide arbitrary single-qubit rotations

### Proof Sketch

1. Any unitary can be decomposed using **KAK decomposition**
2. Two-qubit unitaries require at most 3 CNOTs  
3. Single-qubit gates can generate any $SU(2)$ rotation

## Relationship to Classical XOR

In the computational basis, CNOT implements **classical XOR** logic:

| Control | Target | Output |
|---------|--------|--------|
| 0       | 0      | 0      |
| 0       | 1      | 1      |
| 1       | 0      | 1      |
| 1       | 1      | 0      |

But unlike classical XOR, CNOT preserves **quantum superposition** and **phase relationships**.

## Implementation Examples

### Basic CNOT Operation

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import CNOT_GATE, X_GATE

# CNOT with control=1, target=0
sim = QuantumSimulator(2)
circuit = QuantumCircuit(2)
circuit.add_gate(X_GATE, [0])      # Prepare |10⟩
circuit.add_gate(CNOT_GATE, [0, 1])  # Apply CNOT
circuit.execute(sim)

print(sim.get_state_vector())  # [0, 0, 0, 1] = |11⟩
```

### Bell State Creation

```python
from quantum_simulator.gates import H_GATE

# Create |Φ⁺⟩ Bell state
sim = QuantumSimulator(2)
circuit = QuantumCircuit(2)
circuit.add_gate(H_GATE, [0])     # H|0⟩ = |+⟩
circuit.add_gate(CNOT_GATE, [0, 1])  # Create entanglement
circuit.execute(sim)

print(sim.get_state_vector())  # [0.707, 0, 0, 0.707]
```

### Entanglement Distribution

```python
# Create 3-qubit GHZ state
sim = QuantumSimulator(3)
circuit = QuantumCircuit(3)
circuit.add_gate(H_GATE, [0])
circuit.add_gate(CNOT_GATE, [0, 1])
circuit.add_gate(CNOT_GATE, [0, 2])
circuit.execute(sim)

# Result: (|000⟩ + |111⟩)/√2
print(sim.get_state_vector())  # [0.707, 0, 0, 0, 0, 0, 0, 0.707]
```

## Bell States Generation

All four **Bell states** can be created using CNOT:

### |Φ⁺⟩ = (|00⟩ + |11⟩)/√2
```
|0⟩ ──H────●── |Φ⁺⟩
|0⟩ ───────⊕──
```

### |Φ⁻⟩ = (|00⟩ - |11⟩)/√2  
```
|0⟩ ──H────●── |Φ⁻⟩
|0⟩ ──Z────⊕──
```

### |Ψ⁺⟩ = (|01⟩ + |10⟩)/√2
```
|0⟩ ──H────●── |Ψ⁺⟩  
|0⟩ ──X────⊕──
```

### |Ψ⁻⟩ = (|01⟩ - |10⟩)/√2
```
|0⟩ ──H────●── |Ψ⁻⟩
|0⟩ ──XZ───⊕──
```

## Quantum Algorithms

### Quantum Teleportation

CNOT gates perform **Bell measurements** in teleportation protocol:

```
|ψ⟩ ────●──H── M
        │
|0⟩ ──H─⊕──── M
        │
|0⟩ ────⊕──── |ψ⟩
```

### Superdense Coding

Enables transmission of 2 classical bits using 1 qubit + shared entanglement.

### Error Correction

CNOT gates implement **stabilizer measurements** in quantum error correction codes.

## Gate Decompositions

### CNOT from Other Gates

CNOT can be constructed from **controlled-Z** and Hadamard:

$$\text{CNOT} = (I \otimes H) \cdot \text{CZ} \cdot (I \otimes H)$$

### CNOT from Rotation Gates

Using **two-qubit rotation gates**:

$$\text{CNOT} = e^{-i\pi/4(I \otimes I)} e^{i\pi/4(Z \otimes I)} e^{i\pi/4(I \otimes X)} e^{i\pi/4(Z \otimes X)}$$

### Toffoli from CNOT

The **Toffoli gate** (CCNOT) requires multiple CNOTs:

```
●──●────────●─── ●
   │        │   │
●──⊕──T†─●─T†─⊕─T†─●─T†─
          │       │
○─────────⊕───────⊕─────
```

## Physical Implementations

### Superconducting Qubits
- **Cross-resonance** interactions
- **iSWAP + single-qubit rotations**
- **Flux-tunable couplers**
- Typical gate times: 100-500 ns

### Trapped Ions
- **Mølmer-Sørensen gates** + decomposition
- **Geometric phase gates**  
- **Laser-induced entangling interactions**
- Gate times: 10-100 μs

### Photonic Systems
- **Linear optical CNOT** (probabilistic)
- **Kerr nonlinearity** (deterministic)
- **Measurement-induced** (with ancillas)

### NMR
- **J-coupling** evolution
- **Composite pulse sequences**
- **Liquid-state** implementations

## Error Models

Common CNOT errors include:

### Coherent Errors
- **Over/under-rotation**: $(1+\epsilon)$ CNOT
- **Cross-talk**: unintended interactions with other qubits
- **Residual ZZ coupling**: unwanted always-on interactions

### Incoherent Errors  
- **Depolarizing**: random Pauli errors
- **Decoherence**: T₁ and T₂ effects during gate time
- **Leakage**: transitions outside computational subspace

### Correlated Errors
CNOT errors often affect **both qubits simultaneously**, requiring **correlated error models**.

## Gate Time Optimization

CNOT gates typically have **longer gate times** than single-qubit gates, making them bottlenecks:

### Circuit Optimization
- **Minimize CNOT count** in circuit compilation
- **Parallelize** independent CNOTs
- **Route** efficiently on constrained topologies

### Hardware Improvements  
- **Faster gate implementations**
- **Reduced crosstalk**
- **Higher fidelity** operations

## Equivalences and Identities

### Commutation Relations

$$[\text{CNOT}_{12}, I \otimes Z] = 0$$

$$[\text{CNOT}_{12}, Z \otimes I] = 0$$

CNOT commutes with Z operations on either qubit.

### Conjugation Relations  
$$(H \otimes H) \text{CNOT}_{12} (H \otimes H) = \text{CNOT}_{21}$$

Hadamards swap control and target roles.

### Pauli Propagation

$$\text{CNOT} (X \otimes I) \text{CNOT}^\dagger = X \otimes X$$

$$\text{CNOT} (I \otimes X) \text{CNOT}^\dagger = I \otimes X$$

$$\text{CNOT} (Z \otimes I) \text{CNOT}^\dagger = Z \otimes I$$

$$\text{CNOT} (I \otimes Z) \text{CNOT}^\dagger = Z \otimes Z$$

## Advanced Applications

### Quantum Phase Estimation
CNOT gates implement **controlled unitaries** $C-U^{2^j}$ for phase extraction.

### Variational Quantum Eigensolver
Two-qubit **ansatz circuits** built from CNOT + parameterized rotations.

### Quantum Machine Learning
**Feature maps** and **variational circuits** rely heavily on CNOT entangling gates.

### Quantum Simulation
**Trotter decomposition** of Hamiltonian evolution often requires many CNOT gates for fermion-to-qubit mappings.