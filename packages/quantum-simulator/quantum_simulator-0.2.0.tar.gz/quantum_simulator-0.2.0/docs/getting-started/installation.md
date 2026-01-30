# Installation

## Requirements

- Python 3.8 or higher
- NumPy 1.20.0 or higher

## Install from PyPI

```bash
pip install quantum-simulator
```

## Install from Source

### Clone the Repository

```bash
git clone https://github.com/beefy/quantum-simulator.git
cd quantum-simulator
```

### Install in Development Mode

For development work:

```bash
pip install -e .[dev,docs]
```

This installs the package in editable mode with all development dependencies.

### Install for Production

For production use:

```bash
pip install -e .
```

## Verify Installation

Test that the installation was successful:

```python
import quantum_simulator
print(quantum_simulator.__version__)

# Test basic functionality
from quantum_simulator import QuantumSimulator
sim = QuantumSimulator(1)
print("Installation successful!")
```

## Dependencies

### Core Dependencies

- **NumPy**: Used for mathematical operations and state vector calculations

### Optional Dependencies

#### Development Dependencies

Install with `pip install quantum-simulator[dev]`:

- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks for code quality

#### Documentation Dependencies

Install with `pip install quantum-simulator[docs]`:

- **mkdocs**: Documentation generator
- **mkdocs-material**: Material theme for MkDocs
- **mkdocstrings**: API documentation from docstrings
- **mkdocs-autorefs**: Cross-reference support

## Troubleshooting

### Common Issues

#### ImportError: No module named 'quantum_simulator'

Make sure you've installed the package:

```bash
pip install quantum-simulator
```

#### NumPy compatibility issues

Update NumPy to a compatible version:

```bash
pip install "numpy>=1.20.0"
```

#### Permission errors during installation

Use the `--user` flag:

```bash
pip install --user quantum-simulator
```

Or use a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install quantum-simulator
```