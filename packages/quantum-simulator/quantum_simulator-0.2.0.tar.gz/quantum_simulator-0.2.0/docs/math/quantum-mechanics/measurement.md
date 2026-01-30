# Quantum Measurement

Quantum measurement is the process by which quantum states are observed, causing the probabilistic collapse of superposition states into definite classical outcomes.

## Mathematical Framework

### Born Rule

The probability of measuring state $|i\rangle$ from quantum state $|\psi\rangle$ is given by the **Born rule**:

$$P(|i\rangle) = |\langle i|\psi\rangle|^2$$

For a general state $|\psi\rangle = \sum_i \alpha_i |i\rangle$:

$$P(|i\rangle) = |\alpha_i|^2$$

### Normalization

Probabilities must sum to 1:

$$\sum_i P(|i\rangle) = \sum_i |\alpha_i|^2 = 1$$

This is ensured by the normalization condition on quantum states.

## Measurement Operators

### Projective Measurement

A **projective measurement** is described by projection operators $P_i$:

$$P_i = |i\rangle\langle i|$$

**Properties**:

- $P_i^2 = P_i$ (idempotent)
- $P_i P_j = 0$ for $i \neq j$ (orthogonal)
- $\sum_i P_i = I$ (completeness)

### General Measurements (POVM)

**Positive Operator-Valued Measures** generalize projective measurements:

$$\sum_i E_i = I, \quad E_i \geq 0$$

Where $E_i$ are positive operators (not necessarily projections).

## State Collapse

### Post-Measurement State

If measurement outcome $i$ is observed, the state collapses to:

$$|\psi\rangle \rightarrow \frac{P_i|\psi\rangle}{\sqrt{\langle\psi|P_i|\psi\rangle}}$$

For computational basis measurement:

$$|\psi\rangle = \alpha|0\rangle + \beta|1\rangle \xrightarrow{\text{measure}} \begin{cases} |0\rangle & \text{probability } |\alpha|^2 \\ |1\rangle & \text{probability } |\beta|^2 \end{cases}$$

### Irreversibility

Quantum measurement is **irreversible**:

- Information about the original superposition is lost
- Cannot reconstruct $|\psi\rangle$ from measurement outcome
- Multiple measurements on identical states give statistics

## Types of Measurements

### Computational Basis Measurement

**Standard measurement** in the $\{|0\rangle, |1\rangle\}$ basis:

$$M_0 = |0\rangle\langle 0| = \begin{pmatrix} 1 & 0 \\ 0 & 0 \end{pmatrix}$$

$$M_1 = |1\rangle\langle 1| = \begin{pmatrix} 0 & 0 \\ 0 & 1 \end{pmatrix}$$

### Pauli Measurements

**X-basis measurement** in the $\{|+\rangle, |-\rangle\}$ basis:

$$|+\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle), \quad |-\rangle = \frac{1}{\sqrt{2}}(|0\rangle - |1\rangle)$$

**Y-basis measurement** in the $\{|+i\rangle, |-i\rangle\}$ basis:

$$|+i\rangle = \frac{1}{\sqrt{2}}(|0\rangle + i|1\rangle), \quad |-i\rangle = \frac{1}{\sqrt{2}}(|0\rangle - i|1\rangle)$$

## Multi-Qubit Measurements

### Joint Measurement

Measuring all qubits simultaneously in computational basis:

For $|\psi\rangle = \sum_{i_1,i_2,\ldots,i_n} \alpha_{i_1 i_2 \cdots i_n} |i_1 i_2 \cdots i_n\rangle$

$$P(|i_1 i_2 \cdots i_n\rangle) = |\alpha_{i_1 i_2 \cdots i_n}|^2$$

### Partial Measurement

Measuring only a subset of qubits causes **partial collapse**.

For two qubits $|\psi\rangle = \sum_{ij} \alpha_{ij}|ij\rangle$, measuring first qubit:

$$P(0) = \sum_j |\alpha_{0j}|^2, \quad P(1) = \sum_j |\alpha_{1j}|^2$$

**Post-measurement state** (if outcome 0):

$$|\psi'\rangle = \frac{1}{\sqrt{P(0)}} \sum_j \alpha_{0j}|0j\rangle$$

## Expectation Values

### Observable Measurement

For Hermitian operator $A$ representing an observable:

$$\langle A \rangle = \langle\psi|A|\psi\rangle$$

This gives the **expected value** of measuring observable $A$.

### Variance

The uncertainty in measurement is:

$$(\Delta A)^2 = \langle A^2 \rangle - \langle A \rangle^2$$

## Examples with Bell States

### Measuring Bell State $|\Phi^+\rangle$

For $|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$:

**Joint measurement probabilities**:

- $P(00) = \frac{1}{2}$
- $P(01) = 0$ 
- $P(10) = 0$
- $P(11) = \frac{1}{2}$

**Individual qubit probabilities**:

- $P(\text{qubit 0} = 0) = \frac{1}{2}$
- $P(\text{qubit 0} = 1) = \frac{1}{2}$
- $P(\text{qubit 1} = 0) = \frac{1}{2}$
- $P(\text{qubit 1} = 1) = \frac{1}{2}$

**Correlations**: If qubit 0 is measured as 0, qubit 1 is guaranteed to be 0.

## Implementation in the Simulator

### Single Qubit Measurement

```python
from quantum_simulator import QuantumSimulator
from quantum_simulator.gates import H_GATE

# Create superposition
sim = QuantumSimulator(1)
H_GATE.apply(sim.state_vector, [0])

# Measure multiple times to see statistics
results = []
for _ in range(1000):
    sim_copy = QuantumSimulator(1)
    sim_copy.state_vector = sim.state_vector.copy()
    result = sim_copy.measure(0)
    results.append(result)

print(f"Fraction of 0s: {results.count(0)/1000}")  # ≈ 0.5
print(f"Fraction of 1s: {results.count(1)/1000}")  # ≈ 0.5
```

### Bell State Measurement

```python
from quantum_simulator.gates import CNOT_GATE

# Create Bell state
sim = QuantumSimulator(2)
H_GATE.apply(sim.state_vector, [0])
CNOT_GATE.apply(sim.state_vector, [0, 1])

# Measure both qubits
result_0 = sim.measure(0)  
result_1 = sim.measure(1)

print(f"Results: ({result_0}, {result_1})")  # Will be (0,0) or (1,1)
```

## Quantum Non-Demolition Measurements

**Special measurements** that can be repeated without disturbing the state:

- Measure eigenstate of the measurement operator
- Subsequent measurements give same result
- Used in quantum error correction

## Deferred Measurement

In quantum circuits, measurements can be **deferred** to the end:

- Replace mid-circuit measurements with conditional operations
- Equivalent to measuring at the end
- Useful for theoretical analysis

Measurement is the bridge between the quantum and classical worlds, converting quantum superposition into definite classical information.