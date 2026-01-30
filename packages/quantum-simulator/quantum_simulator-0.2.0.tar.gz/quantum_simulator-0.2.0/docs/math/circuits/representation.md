# Circuit Representation

Quantum circuits provide a **visual and mathematical representation** of quantum computations. They offer an intuitive way to design, analyze, and implement quantum algorithms using standardized notation and conventions.

## Basic Circuit Elements

### Quantum Wires
Horizontal lines represent **quantum wires** carrying qubits:

```
|ψ₁⟩ ─────────────
|ψ₂⟩ ─────────────  
|ψ₃⟩ ─────────────
```

- Time flows from **left to right**
- Each wire carries one qubit
- Initial states written on the left
- Final states (if shown) on the right

### Single-Qubit Gates
Represented as boxes or symbols on wires:

```
|ψ⟩ ──[U]── U|ψ⟩
|ψ⟩ ──H──── H|ψ⟩  
|ψ⟩ ──X──── X|ψ⟩
```

Common single-qubit gate symbols:

- **H**: Hadamard gate
- **X**, **Y**, **Z**: Pauli gates
- **S**: Phase gate (√Z)
- **T**: π/8 gate (√S)
- **[R_x(θ)]**: Parameterized rotations

### Multi-Qubit Gates
Connected across multiple wires:

#### Controlled Gates
```
Control ●─────
        │
Target  ⊕─────
```

- **●**: Control qubit (filled circle)
- **⊕**: Target qubit (plus in circle)
- **│**: Control connection

#### General Two-Qubit Gates
```
|ψ₁⟩ ──┌───────┐──
       │   U   │
|ψ₂⟩ ──└───────┘──
```

### Measurement
Represented by meter symbols:

```
|ψ⟩ ─────■─── classical bit
         │
      ┌─────┐
      │  M  │
      └─────┘
```

- **■**: Measurement operation
- **Double lines**: Classical information
- **M**: Measurement symbol in box

## Circuit Composition Rules

### Sequential Operations
Gates applied **left to right** in time order:

```
|ψ⟩ ──H────X────Z── |final⟩
```

Represents: $Z \cdot X \cdot H |\psi\rangle$ (note reverse order in math)

### Parallel Operations  
Gates on different qubits can be applied **simultaneously**:

```
|ψ₁⟩ ──H────────
|ψ₂⟩ ──────X────
|ψ₃⟩ ──Z────────
```

Represents: $(H \otimes X \otimes Z)|\psi_1\psi_2\psi_3\rangle$

### Gate Timing
Vertical alignment indicates **simultaneous application**:

```
|ψ₁⟩ ──H────●──  ← Time 1    Time 2
|ψ₂⟩ ──X────⊕──
```

## Standard Gate Notation

### Pauli Gates
```
X Gate:  ──X──   or   ──⊕──
Y Gate:  ──Y──
Z Gate:  ──Z──
```

### Rotation Gates
```
R_x(θ): ──[Rx(θ)]──
R_y(θ): ──[Ry(θ)]──  
R_z(θ): ──[Rz(θ)]──
```

### Phase Gates
```
S Gate:  ──S──   (π/2 phase)
T Gate:  ──T──   (π/4 phase)
P(φ):    ──[P(φ)]──
```

### Controlled Variants
```
CNOT:    ●────
         │
         ⊕────

CZ:      ●────
         │  
         ●────

C-U:     ●────
         │
         [U]──
```

## Multi-Control Gates

### Toffoli (CCNOT)
```
●────
│
●────
│  
⊕────
```

### Multi-Control Unitary
```
●────
│
●────
│
●────
│
[U]──
```

### Alternative Control Symbols

- **●**: Control on |1⟩ state
- **○**: Control on |0⟩ state (open circle)

## Circuit Depth and Width

### Circuit Width
**Number of qubits** in the circuit:

```
|q₀⟩ ──H────●──    ← Width = 3 qubits
|q₁⟩ ──────⊕────
|q₂⟩ ──X─────────
```

### Circuit Depth  
**Number of time steps** (sequential gate layers):

```
|q₀⟩ ──H────●────Z──  ← Depth = 3 layers
|q₁⟩ ──────⊕─────────
```

Layer 1: H gate

Layer 2: CNOT gate  

Layer 3: Z gate

### Parallelization
Gates on **disjoint qubits** can be parallelized:

```
Before:  |q₀⟩ ──H────X──    Depth = 2
         |q₁⟩ ──────Y──

After:   |q₀⟩ ──H────X──    Depth = 2 (no change)
         |q₁⟩ ──Y─────────   (Y moved to parallel with H)
```

## Quantum Circuit Model

### Mathematical Representation
A quantum circuit implements a **unitary transformation**:

$$U_{\text{circuit}} = U_L \cdot U_{L-1} \cdot \ldots \cdot U_2 \cdot U_1$$

Where $U_i$ are the gates applied at each time step.

### State Evolution
Initial state evolves through the circuit:

$$|\psi_{\text{final}}\rangle = U_{\text{circuit}}|\psi_{\text{initial}}\rangle$$

### Tensor Product Structure
For parallel gates:

$$U_{\text{parallel}} = U_1 \otimes U_2 \otimes \ldots \otimes U_n$$

## Classical Control

### Conditional Gates
Gates controlled by **classical measurement results**:

```
|ψ₁⟩ ──────■───c[0]──X──  ← Controlled by c[0]
           │               
|ψ₂⟩ ──H───M─────────────
```

### Feedforward
Using measurement results to control later gates:

```
|ψ⟩ ──H──■─────c──X──  if c==1
         │       ║     
      ┌─────┐    ║
      │  M  │════╝
      └─────┘
```

## Circuit Compilation

### Gate Decomposition
Complex gates decomposed into **elementary gates**:

```
Original:  ──[Toffoli]──

Compiled:  ──H──●──T†─●─T──●──T†─●─T──H──
              │     │    │     │
           ──T──⊕──T†─●─T──⊕──T†────────  
              │     │       │
           ─────────⊕───────⊕──────────
```

### Optimization Goals
- **Minimize depth**: Reduce execution time
- **Minimize gate count**: Reduce error accumulation  
- **Hardware constraints**: Respect connectivity topology
- **Native gates**: Use hardware-supported operations

## Error Correction Integration

### Logical Qubits
Physical qubits grouped into **error-corrected logical qubits**:

```
Logical |0⟩_L: ───[───]───  ← Multiple physical qubits
               ───[───]───
               ───[───]───
```

### Fault-Tolerant Gates
Gates implemented **transversally** across code blocks:

```
|ψ⟩_L ───[T⊗T⊗T]───  ← Bitwise T gate
      ───[T⊗T⊗T]───
      ───[T⊗T⊗T]───
```

## Visualization Examples

### Bell State Circuit
```
|0⟩ ──H────●──  |Φ⁺⟩
|0⟩ ───────⊕──
```

Mathematical: $|\Phi^+\rangle = \text{CNOT} \cdot (H \otimes I)|00\rangle$

### Teleportation Circuit  
```
|ψ⟩ ──────●──H──■──
          │     │  
|0⟩ ──H───⊕─────■──
          │     │
|0⟩ ──────⊕─────X──  |ψ⟩
```

### QFT Circuit (3 qubits)
```
|x₀⟩ ──H──●────────●────────H──
          │        │
|x₁⟩ ─────S─●─────H──S──H─────
              │     │
|x₂⟩ ─────────T──H──────────────
```

## Circuit Simulation

### State Vector Evolution
Track **full quantum state** through circuit:

```python
# Initialize |000⟩
state = [1, 0, 0, 0, 0, 0, 0, 0]

# Apply H⊗I⊗I  
state = apply_gate(H_gate, state, qubit=0)

# Apply CNOT₀₁
state = apply_gate(CNOT_gate, state, qubits=[0,1])
```

### Quantum Circuit Simulators
- **State vector simulators**: Track full quantum state
- **Stabilizer simulators**: Efficient for Clifford circuits  
- **Tensor network simulators**: Handle large, low-entanglement circuits
- **Quantum hardware simulators**: Model noise and decoherence

## Advanced Circuit Features

### Parametric Circuits
Gates with **tunable parameters**:

```
|ψ⟩ ──[Rx(θ₁)]────●────[Ry(θ₂)]──
                  │
|0⟩ ──[Rx(θ₃)]────⊕────[Rz(θ₄)]──
```

Used in **variational quantum algorithms** and **quantum machine learning**.

### Ancilla Qubits
**Helper qubits** for complex operations:

```
|ψ⟩ ──────●─────────────
          │
|0⟩ ──H───⊕───H──■──  ← Ancilla
                 │
Classical ───────c──
```

### Reset Operations
Mid-circuit qubit **initialization**:

```
|ψ⟩ ──■─────|0⟩────H──  ← Reset to |0⟩
      │
   ┌─────┐
   │  M  │
   └─────┘
```

## Software Tools

### Circuit Description Languages
- **QASM**: Quantum assembly language
- **Cirq**: Google's quantum framework  
- **Qiskit**: IBM's quantum toolkit
- **PennyLane**: Quantum ML framework

### Example QASM
```qasm
OPENQASM 2.0;
include "qelib1.inc";

qreg q[2];
creg c[2];

h q[0];
cx q[0],q[1];
measure q -> c;
```

### Circuit Visualization Tools
- **Circuit diagrams**: ASCII or graphical representation
- **Interactive visualizers**: Web-based circuit editors
- **Animation tools**: Show state evolution through circuit

The quantum circuit model provides the foundation for **quantum algorithm design**, **hardware implementation**, and **quantum software development**.