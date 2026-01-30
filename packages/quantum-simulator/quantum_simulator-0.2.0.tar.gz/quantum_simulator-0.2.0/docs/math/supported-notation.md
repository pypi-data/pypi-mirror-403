# Supported Mathematical Notation

This page documents the LaTeX mathematical notation supported in our documentation and provides examples of quantum computing mathematical expressions.

## Dirac Notation

**Ket vectors** (quantum states):

$$|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$$

**Bra vectors** (complex conjugate transpose):

$$\langle\psi| = \alpha^*\langle 0| + \beta^*\langle 1|$$

**Inner products** (probability amplitudes):

$$\langle\phi|\psi\rangle = \sum_i \phi_i^* \psi_i$$

**Outer products** (projection operators):

$$|\psi\rangle\langle\phi| = \begin{pmatrix} \psi_0 \phi_0^* & \psi_0 \phi_1^* \\ \psi_1 \phi_0^* & \psi_1 \phi_1^* \end{pmatrix}$$

## Common Quantum States

**Computational basis states**:

$$|0\rangle = \begin{pmatrix} 1 \\ 0 \end{pmatrix}, \quad |1\rangle = \begin{pmatrix} 0 \\ 1 \end{pmatrix}$$

**Superposition states**:

$$|+\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle) = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 \\ 1 \end{pmatrix}$$

$$|-\rangle = \frac{1}{\sqrt{2}}(|0\rangle - |1\rangle) = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 \\ -1 \end{pmatrix}$$

## Multi-Qubit Notation

**Tensor product**:

$$|00\rangle = |0\rangle \otimes |0\rangle = \begin{pmatrix} 1 \\ 0 \\ 0 \\ 0 \end{pmatrix}$$

**Bell states** (maximally entangled):

$$|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$$

$$|\Phi^-\rangle = \frac{1}{\sqrt{2}}(|00\rangle - |11\rangle)$$

$$|\Psi^+\rangle = \frac{1}{\sqrt{2}}(|01\rangle + |10\rangle)$$

$$|\Psi^-\rangle = \frac{1}{\sqrt{2}}(|01\rangle - |10\rangle)$$

## Operators and Matrices

**Pauli matrices**:

$$\sigma_x = X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}$$

$$\sigma_y = Y = \begin{pmatrix} 0 & -i \\ i & 0 \end{pmatrix}$$

$$\sigma_z = Z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}$$

**Hadamard gate**:

$$H = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$$

**CNOT gate** (controlled-X):

$$\text{CNOT} = \begin{pmatrix} 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 \\ 0 & 0 & 0 & 1 \\ 0 & 0 & 1 & 0 \end{pmatrix}$$

## Probability and Measurement

**Born rule** (measurement probability):

$$P(|i\rangle) = |\langle i|\psi\rangle|^2$$

**Normalization condition**:

$$\langle\psi|\psi\rangle = \sum_i |\alpha_i|^2 = 1$$

**Expectation value** of observable $A$:

$$\langle A \rangle = \langle\psi|A|\psi\rangle$$

## Evolution and Dynamics

**Unitary evolution**:

$$|\psi(t)\rangle = U(t)|\psi(0)\rangle$$

**Schrödinger equation**:

$$i\hbar\frac{d}{dt}|\psi\rangle = H|\psi\rangle$$

**Time evolution operator**:

$$U(t) = e^{-iHt/\hbar}$$

## Rendering Notes

- All equations are rendered using MathJax
- Complex expressions may take a moment to load