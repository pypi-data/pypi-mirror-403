# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0](https://github.com/beefy/quantum-simulator/releases/tag/v0.2.0) - 2026-01-25

### Added
- Deutsch's Algorithm example implementation
- Deutsch-Jozsa Algorithm example implementation  
- Quantum Approximate Optimization Algorithm (QAOA) example for Max-Cut problem
- RZZ two-qubit rotation gate for QAOA cost Hamiltonians
- Phase gate for single-qubit phase operations
- Comprehensive test coverage for all new algorithm examples
- execute_circuit function for enhanced quantum circuit execution capabilities

## [0.1.7](https://github.com/beefy/quantum-simulator/releases/tag/v0.1.7) - 2026-01-18

### Added
- RX gate
- CRX gate
- CRZ gate
- CZ gate
- Toffoli gate
- Grover's algorithm example
- Additional testing

## [0.1.6](https://github.com/beefy/quantum-simulator/releases/tag/v0.1.6) - 2026-01-09

### Added
- RY gate
- RZ gate
- CRY gate
- W state 3 qubit example
- GHZ 3 qubit example

## [0.1.5](https://github.com/beefy/quantum-simulator/releases/tag/v0.1.5) - 2026-01-01

### Added
- Documentation fixes

## [0.1.4](https://github.com/beefy/quantum-simulator/releases/tag/v0.1.4) - 2025-12-16

### Added
- Fix broken links in documentation
- Added initial math overview documentation

## [0.1.3](https://github.com/beefy/quantum-simulator/releases/tag/v0.1.3) - 2025-12-16

### Added
- Fix documentation references

## [0.1.2](https://github.com/beefy/quantum-simulator/releases/tag/v0.1.2) - 2025-12-16

### Added
- Fix documentation
- Fix docs github action

## [0.1.1](https://github.com/beefy/quantum-simulator/releases/tag/v0.1.1) - 2025-12-16

### Added
- Fix dimension mismatch bug
- Fix CNOT bug
- Fix documentation
- Add CONTRIBUTING.md
- Fix tests
- Fix linting

## [0.1.0](https://github.com/beefy/quantum-simulator/releases/tag/v0.1.0) - 2025-12-16

### Added
- Initial release
- Initial project structure
- Basic quantum simulation functionality
- Documentation with MkDocs
- CI/CD with GitHub Actions
- `QuantumSimulator` class for quantum state simulation
- Basic quantum gates (X, Y, Z, H, CNOT)
- `QuantumCircuit` class for building quantum circuits
- Quantum measurement functionality
- Comprehensive documentation
- Unit tests and type checking
- PyPI packaging configuration
- GitHub Actions for automated testing and publishing

### Features
- Support for multi-qubit quantum systems
- State vector representation of quantum states
- Gate application and circuit execution
- Measurement with state collapse
- Modern Python packaging with `pyproject.toml`
- MkDocs documentation with Material theme
- Automated PyPI publishing on releases
- Automated documentation deployment to GitHub Pages
