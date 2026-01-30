# Circuit Examples

This section demonstrates practical quantum circuit constructions for common quantum algorithms and operations. Each exam### W States

**W states** have equal superposition with exactly one qubit in |1⟩:

#### 3-Qubit W State
$$|W_3\rangle = \frac{1}{\sqrt{3}}(|001\rangle + |010\rangle + |100\rangle)$$

**Circuit (one construction):**
```
|0⟩ ──[R_y(θ₁)]────●────────────
|0⟩ ─────────────[C-R_y(θ₂)]──●──
|0⟩ ──────────────────────────⊕──
```

Where $\theta_1 = 2\arccos(\sqrt{2/3})$ and $\theta_2 = 2\arccos(\sqrt{1/2})$.

**Implementation:**
```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import RY_W1, CRY_W, CNOT_GATE
import numpy as np

# Create 3-qubit W state
sim = QuantumSimulator(3)
circuit = QuantumCircuit(3)

# Apply rotation gates to create W state
circuit.add_gate(RY_W1, [0])           # R_y(θ₁) on qubit 0
circuit.add_gate(CRY_W, [0, 1])        # Controlled R_y(θ₂) on qubits 0→1
circuit.add_gate(CNOT_GATE, [1, 2])    # CNOT: 1→2
circuit.add_gate(CNOT_GATE, [0, 2])    # CNOT: 0→2

circuit.execute(sim)
print(sim.get_state_vector())  # [0, 0.577, 0.577, 0, 0.577, 0, 0, 0]

# Alternatively, create W state directly
w_state = np.zeros(8, dtype=complex)
w_state[1] = 1/np.sqrt(3)  # |001⟩
w_state[2] = 1/np.sqrt(3)  # |010⟩  
w_state[4] = 1/np.sqrt(3)  # |100⟩
sim.state_vector = w_state
```

**Properties:**

- Each qubit has equal 1/3 probability of being measured as |1⟩
- Exactly one qubit will be |1⟩ in any measurement
- More robust to particle loss than GHZ states
- Demonstrates symmetric multipartite entanglementrcuit diagrams, mathematical descriptions, and implementation code using our quantum simulator.

## Basic Quantum States

### Computational Basis States

The simplest circuits prepare **computational basis states** |0⟩ and |1⟩:

#### Preparing |0⟩
```
|0⟩ ────────  |0⟩  (Identity circuit)
```

#### Preparing |1⟩  
```
|0⟩ ──X──  |1⟩
```

**Implementation:**
```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import X_GATE

# Prepare |1⟩ state
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(X_GATE, [0])
circuit.execute(sim)

print(sim.get_state_vector())  # [0, 1] = |1⟩
```

### Superposition States

#### Plus State |+⟩
```
|0⟩ ──H──  |+⟩ = (|0⟩ + |1⟩)/√2
```

#### Minus State |-⟩
```
|0⟩ ──X──H──  |-⟩ = (|0⟩ - |1⟩)/√2
```

**Implementation:**
```python
from quantum_simulator.gates import H_GATE

# Prepare |+⟩ state
sim = QuantumSimulator(1)
circuit = QuantumCircuit(1)
circuit.add_gate(H_GATE, [0])
circuit.execute(sim)

print(sim.get_state_vector())  # [0.707, 0.707] ≈ |+⟩
```

### Y-basis States
```
|0⟩ ──H──S──  |+i⟩ = (|0⟩ + i|1⟩)/√2
|0⟩ ──X──H──S──  |-i⟩ = (|0⟩ - i|1⟩)/√2
```

## Entangled States

### Bell States

The four **maximally entangled two-qubit states**:

#### |Φ⁺⟩ = (|00⟩ + |11⟩)/√2
```
|0⟩ ──H────●──  |Φ⁺⟩
|0⟩ ───────⊕──
```

#### |Φ⁻⟩ = (|00⟩ - |11⟩)/√2
```
|0⟩ ──H────●──  |Φ⁻⟩
|0⟩ ──Z────⊕──
```

#### |Ψ⁺⟩ = (|01⟩ + |10⟩)/√2
```
|0⟩ ──H────●──  |Ψ⁺⟩
|0⟩ ──X────⊕──
```

#### |Ψ⁻⟩ = (|01⟩ - |10⟩)/√2
```
|0⟩ ──H────●──  |Ψ⁻⟩
|0⟩ ──XZ───⊕──
```

**Implementation (|Φ⁺⟩):**
```python
from quantum_simulator.gates import CNOT_GATE

# Create Bell state |Φ⁺⟩
sim = QuantumSimulator(2)
circuit = QuantumCircuit(2)
circuit.add_gate(H_GATE, [0])      # Create superposition
circuit.add_gate(CNOT_GATE, [0, 1])  # Create entanglement
circuit.execute(sim)

print(sim.get_state_vector())  # [0.707, 0, 0, 0.707]
```

### GHZ States

**Greenberger-Horne-Zeilinger** states for 3+ qubits:

#### 3-Qubit GHZ
```
|0⟩ ──H────●────●──  |GHZ₃⟩ = (|000⟩ + |111⟩)/√2
|0⟩ ───────⊕────│──
|0⟩ ────────────⊕──
```

#### 4-Qubit GHZ  
```
|0⟩ ──H────●────●────●──  |GHZ₄⟩ = (|0000⟩ + |1111⟩)/√2
|0⟩ ───────⊕────│────│──
|0⟩ ────────────⊕────│──
|0⟩ ─────────────────⊕──
```

**Implementation:**
```python
# Create 3-qubit GHZ state
sim = QuantumSimulator(3)
circuit = QuantumCircuit(3)
circuit.add_gate(H_GATE, [0])
circuit.add_gate(CNOT_GATE, [0, 1])
circuit.add_gate(CNOT_GATE, [0, 2])
circuit.execute(sim)

print(sim.get_state_vector())  # [0.707, 0, 0, 0, 0, 0, 0, 0.707]
```

### W States

**W states** have equal superposition with exactly one qubit in |1⟩:

#### 3-Qubit W State
$$|W_3\rangle = \frac{1}{\sqrt{3}}(|001\rangle + |010\rangle + |100\rangle)$$

**Circuit (one construction):**
```
|0⟩ ──[R_y(θ₁)]────●────────────
|0⟩ ─────────────[C-R_y(θ₂)]──●──
|0⟩ ──────────────────────────⊕──
```

Where $\theta_1 = 2\arccos(\sqrt{2/3})$ and $\theta_2 = 2\arccos(\sqrt{1/2})$.

## Quantum Algorithms

### Deutsch's Algorithm

Determines if function $f:\{0,1\} \to \{0,1\}$ is **constant** or **balanced**:

```
|0⟩ ──H──────[U_f]──H──■──
|1⟩ ──H──────[U_f]─────────
```

Where $U_f|x,y\rangle = |x, y \oplus f(x)\rangle$.

**Result**: Measure 0 → constant, Measure 1 → balanced

### Deutsch-Jozsa Algorithm

Generalization to $n$-bit functions:

```
|0⟩^⊗n ──H^⊗n──[U_f]──H^⊗n──■──
|1⟩    ──H─────[U_f]────────────
```

**Implementation (2-bit example):**
```python
# Example: f(x) = x₁ ⊕ x₂ (balanced function)
def deutsch_jozsa_circuit():
    sim = QuantumSimulator(3)  # 2 input + 1 ancilla
    circuit = QuantumCircuit(3)
    
    # Initialize ancilla to |1⟩
    circuit.add_gate(X_GATE, [2])
    
    # Apply Hadamard to all qubits
    for i in range(3):
        circuit.add_gate(H_GATE, [i])
    
    # Oracle: f(x) = x₁ ⊕ x₂
    circuit.add_gate(CNOT_GATE, [0, 2])  # x₀ → ancilla
    circuit.add_gate(CNOT_GATE, [1, 2])  # x₁ → ancilla
    
    # Final Hadamard on input qubits
    circuit.add_gate(H_GATE, [0])
    circuit.add_gate(H_GATE, [1])
    
    circuit.execute(sim)
    return sim
```

### Grover's Algorithm

**Quantum search** for marked items in unsorted database:

#### Single Iteration (2-qubit example)
```
|0⟩ ──H──[Oracle]──H──Z──H──■──
|0⟩ ──H──[Oracle]──H──Z──H──■──
```

Where **Oracle** marks target state with phase flip.

#### Amplitude Amplification
```
|ψ⟩ ──[Oracle]──[Diffuser]──[Oracle]──[Diffuser]── ... ──■──
```

**Diffuser**: $2|\psi\rangle\langle\psi| - I$ operation.

### Simon's Algorithm

Finds **hidden period** of function $f:\{0,1\}^n \to \{0,1\}^n$:

```
|0⟩^⊗n ──H^⊗n──[U_f]──H^⊗n──■──
|0⟩^⊗n ───────[U_f]─────────────
```

Requires multiple runs to determine period **s** where $f(x) = f(x \oplus s)$.

## Quantum Simulation

### Ising Model Evolution

Time evolution under **Ising Hamiltonian**: $H = \sum J_{ij}\sigma_i^z\sigma_j^z + \sum h_i\sigma_i^x$

#### Trotter Decomposition
```
|ψ⟩ ──[R_x(h₀t/n)]──●──[R_x(h₁t/n)]──●── ... ──■──
                     │                  │
                  [R_z(J₀₁t/n)]    [R_z(J₁₂t/n)]
```

### Variational Quantum Eigensolver (VQE)

**Parameterized circuits** for finding ground states:

#### Hardware-Efficient Ansatz
```
|0⟩ ──[R_y(θ₁)]──●────[R_y(θ₅)]──●── ...
|0⟩ ──[R_y(θ₂)]──⊕──●──[R_y(θ₆)]──⊕── ...  
|0⟩ ──[R_y(θ₃)]─────⊕──[R_y(θ₇)]───── ...
|0⟩ ──[R_y(θ₄)]────────[R_y(θ₈)]───── ...
```

### Quantum Approximate Optimization Algorithm (QAOA)

For **combinatorial optimization**:

#### Single QAOA Layer
```
|+⟩^⊗n ──[e^{-iγC}]──[e^{-iβB}]──■──
```

Where **C** encodes the cost function and **B** is the mixing Hamiltonian.

## Quantum Information Protocols

### Teleportation

**Quantum state transfer** using entanglement and classical communication:

```
|ψ⟩ ──────●──H──■─c₀──
          │     │
|0⟩ ──H───⊕─────■─c₁──
          │
|0⟩ ──────⊕───X^c₁─Z^c₀─ |ψ⟩
```

**Implementation:**
```python
def teleportation_circuit():
    sim = QuantumSimulator(3)
    circuit = QuantumCircuit(3)
    
    # Prepare state to teleport (example: |+⟩)
    circuit.add_gate(H_GATE, [0])
    
    # Create Bell pair between qubits 1 and 2
    circuit.add_gate(H_GATE, [1])
    circuit.add_gate(CNOT_GATE, [1, 2])
    
    # Bell measurement on qubits 0 and 1
    circuit.add_gate(CNOT_GATE, [0, 1])
    circuit.add_gate(H_GATE, [0])
    
    # Measure qubits 0 and 1 (simulated here)
    # In real implementation, apply corrections based on results
    
    circuit.execute(sim)
    return sim
```

### Superdense Coding

Transmit **2 classical bits** using 1 qubit + shared entanglement:

```
         ┌─ Encoding ─┐
|0⟩ ──H──●─[I/X/Z/Y]──■─c₀──  (2 bits: c₀c₁)
|0⟩ ─────⊕────────────⊕─c₁──
```

Encoding rules:
- 00 → I (identity)
- 01 → X  
- 10 → Z
- 11 → Y

### Quantum Error Correction

#### 3-Qubit Bit-Flip Code
```
|ψ⟩ ──●────●───...error channel...──●────●──■──
|0⟩ ──⊕────│─────────────────────────⊕────│──■──
|0⟩ ───────⊕─────────────────────────────⊕──■──
```

Encodes 1 logical qubit in 3 physical qubits, corrects single bit-flip errors.

## Quantum Fourier Transform

### 3-Qubit QFT
```
|x₀⟩ ──H──●──────●────────SWAP──
          │      │         │
|x₁⟩ ─────S─●────│──H──S───│────
              │  │     │   │
|x₂⟩ ─────────T──H─────────T─────
```

Where gates implement controlled rotations:
- S = controlled-$R_z(\pi/2)$
- T = controlled-$R_z(\pi/4)$

**Mathematical representation:**
$$\text{QFT}|x\rangle = \frac{1}{\sqrt{2^n}}\sum_{y=0}^{2^n-1}e^{2\pi i xy/2^n}|y\rangle$$

### Inverse QFT
Apply **reverse order** of QFT with **conjugated rotations**:

```
SWAP──●────────●──H──|y₀⟩
  │   │        │
──│───S†─●─────S──────|y₁⟩  
  │      │     │
──T†─────T†────H──────|y₂⟩
```

## Quantum Walk Algorithms

### Discrete Quantum Walk

**Quantum analog** of classical random walk:

```
|coin⟩ ──H──●─────●──H──●── ...
            │     │     │
|pos⟩ ─────[S+]─[S-]──[S+]─ ...
```

Where S± are **conditional shift operators** based on coin state.

### Continuous Quantum Walk

Implemented via **Hamiltonian simulation** on graphs:

```
|ψ⟩ ──[e^{-iHt}]──■──
```

Where **H** is the graph adjacency matrix.

## Parameterized Quantum Circuits

### Quantum Machine Learning

#### Data Encoding
```
|0⟩^⊗n ──[R_x(x₁)]──[R_y(x₂)]── ... ──[Feature Map]──
```

#### Variational Layer
```
──[R_y(θ₁)]──●────[R_y(θ₄)]──●── ...
──[R_y(θ₂)]──⊕──●──[R_y(θ₅)]──⊕── ...
──[R_y(θ₃)]─────⊕──[R_y(θ₆)]───── ...
```

### Quantum Neural Networks

**Quantum version** of neural network layers:

```
|x⟩ ──[Encoder]──[Layer 1]──[Layer 2]── ... ──[Measurement]── y
```

Each layer contains **parameterized gates** optimized via **gradient descent**.

## Advanced Circuit Techniques

### Gate Synthesis

Decomposing arbitrary unitaries into elementary gates:

#### Arbitrary Single-Qubit Unitary
```
|ψ⟩ ──[R_z(α)]──[R_y(β)]──[R_z(γ)]──
```

Any single-qubit unitary can be decomposed as $R_z(\alpha)R_y(\beta)R_z(\gamma)$.

#### Two-Qubit Unitary Decomposition
Uses **KAK decomposition** with at most 3 CNOTs:

```
──●──[R_y(θ₁)]──●──[R_y(θ₃)]──●──[R_z(φ₁)]──
  │              │              │
──⊕──[R_y(θ₂)]──⊕──[R_y(θ₄)]──⊕──[R_z(φ₂)]──
```

These examples demonstrate the **versatility** and **power** of quantum circuits for implementing quantum algorithms, simulating quantum systems, and solving computational problems with quantum advantage.