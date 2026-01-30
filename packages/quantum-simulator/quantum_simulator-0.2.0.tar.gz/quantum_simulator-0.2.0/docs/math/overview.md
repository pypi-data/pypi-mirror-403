# Math Overview

This section provides mathematical foundations for understanding quantum computing concepts implemented in the Quantum Simulator library.

## Mathematical Notation

Quantum computing relies heavily on linear algebra and complex numbers. This documentation uses standard mathematical notation to describe quantum states, operations, and measurements.

### Key Mathematical Concepts

- **Complex Numbers**: Quantum amplitudes are complex numbers
- **Vector Spaces**: Quantum states live in complex vector spaces
- **Linear Operators**: Quantum gates are unitary linear operators
- **Probability**: Measurement outcomes follow quantum probability rules

### Notation Standards

- States are denoted using Dirac notation: $|0\rangle$, $|1\rangle$, $|\psi\rangle$
- Operators use capital letters: $X$, $Y$, $Z$, $H$, $U$
- Inner products: $\langle\phi|\psi\rangle$
- Tensor products: $\otimes$
- Matrix elements: $\langle i|U|j\rangle$

## Topics Covered

1. **[Quantum Mechanics](quantum-mechanics/qubits_states.md)** - Fundamental quantum concepts
2. **[Gates](../math/gates/x_gate.md)** - Mathematical description of quantum gates
3. **[Circuits](circuits/representation.md)** - Circuit composition and execution

## Prerequisites

- Basic linear algebra (vectors, matrices, eigenvalues)
- Complex numbers
- Basic probability theory

## Further Reading

For deeper mathematical foundations, consult:

- Nielsen & Chuang: "Quantum Computation and Quantum Information"
- Preskill: "Quantum Computing: An Introduction" (Caltech lecture notes)
- Watrous: "The Theory of Quantum Information"