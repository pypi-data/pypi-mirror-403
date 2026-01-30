# Quantum Simulator

[![Tests](https://github.com/beefy/quantum-simulator/actions/workflows/tests.yml/badge.svg)](https://github.com/beefy/quantum-simulator/actions/workflows/tests.yml)
[![PyPI version](https://badge.fury.io/py/quantum-simulator.svg)](https://badge.fury.io/py/quantum-simulator)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://beefy.github.io/quantum-simulator/)
[![Python versions](https://img.shields.io/pypi/pyversions/quantum-simulator)](https://pypi.org/project/quantum-simulator/)
[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](http://unlicense.org/)

A Python library for simulating quantum computers and quantum algorithms. This package provides an easy-to-use interface for quantum state simulation, gate operations, and circuit execution.

## Features

- 🔬 **Quantum State Simulation**: Accurate simulation of quantum states using state vectors
- 🚪 **Quantum Gates**: Implementation of common single and multi-qubit gates (X, Y, Z, H, CNOT)
- 🔗 **Quantum Circuits**: Build and execute complex quantum circuits
- 📊 **Measurement**: Simulate quantum measurements with proper state collapse

## Quick Start

### Installation

```bash
pip install quantum-simulator
```

### Basic Example

```python
from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import H_GATE, CNOT_GATE

# Create a 2-qubit quantum simulator
sim = QuantumSimulator(2)

# Build a Bell state circuit
circuit = QuantumCircuit(2)
circuit.add_gate(H_GATE, [0])        # Hadamard on qubit 0
circuit.add_gate(CNOT_GATE, [0, 1])  # CNOT with control=0, target=1

# Execute the circuit
circuit.execute(sim)

# Measure the qubits
result0 = sim.measure(0)
result1 = sim.measure(1)
print(f"Measurement: {result0}, {result1}")
```

## Documentation

Full documentation is available at **[beefy.github.io/quantum-simulator](https://beefy.github.io/quantum-simulator/)**

- [Installation Guide](https://beefy.github.io/quantum-simulator/getting-started/installation/)
- [Quick Start](https://beefy.github.io/quantum-simulator/getting-started/quickstart/)

## Development

### Setting Up Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/beefy/quantum-simulator.git
   cd quantum-simulator
   ```

2. **Install in development mode**:
   ```bash
   pip install -e .[dev,docs]
   ```

3. **Run tests**:
   ```bash
   pytest --cov=quantum_simulator --cov-report=xml --cov-report=term
   ```

4. **Run lint checks**:
   ```bash
   flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
   mypy src/
   ```

4. **Build documentation**:
   ```bash
   mkdocs serve
   ```
