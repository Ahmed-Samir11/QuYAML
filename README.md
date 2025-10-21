# QuYAML

A robust, production-ready parser for converting QuYAML (Quantum YAML) syntax into Qiskit QuantumCircuit objects.

## Overview

QuYAML provides a simple, human-readable YAML-based syntax for defining quantum circuits. This parser translates QuYAML files into executable Qiskit circuits, making quantum circuit definition more accessible and maintainable.

## Features

- 🔄 **Clean YAML Syntax**: Define quantum circuits using intuitive YAML structure
- 🎯 **Qiskit Integration**: Seamless conversion to Qiskit QuantumCircuit objects
- 🔢 **Parameterized Gates**: Support for gates with arithmetic expressions and variable substitution
- � **QML Ready**: Build quantum machine learning feature maps with parameterized rotations
- 🎲 **Optimization Support**: Create QAOA and other variational quantum algorithm circuits
- �🧪 **Comprehensive Testing**: Unit tests, metamorphic tests, and property-based tests using Hypothesis
- 🚀 **CI/CD Ready**: GitHub Actions workflow for automated testing
- ⚡ **Error Handling**: Custom `QuYamlError` exceptions with clear error messages

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Ahmed-Samir11/QuYAML.git
cd QuYAML
```

2. Create and activate a virtual environment:
```bash
python -m venv quyaml
# Windows
quyaml\Scripts\activate
# Linux/Mac
source quyaml/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## QuYAML Syntax

### Basic Structure

```yaml
circuit: CircuitName
metadata:  # Optional
  type: Circuit Type
  description: Circuit description
qreg: q[num_qubits]
creg: c[num_classical_bits]  # Optional
parameters:  # Optional - for parameterized circuits
  param_name: value
instructions:
  - gate_name qubit_targets
  - gate_name(expression) qubit_targets  # Parameterized gates
```

### Example: Bell State

```yaml
circuit: BellState
qreg: q[2]
creg: c[2]
instructions:
  - h q[0]
  - cx q[0], q[1]
```

### Example: GHZ State

```yaml
circuit: GHZState
qreg: q[3]
instructions:
  - h q[0]
  - cx q[0], q[1]
  - cx q[0], q[2]
```

### Example: Parameterized QML Feature Map

```yaml
circuit: SimpleFeatureMap
metadata:
  type: QML Feature Map
  description: A 2-qubit feature map with parameterized rotations
qreg: q[2]
parameters:
  x0: 0.5
  x1: 1.2
instructions:
  - h q[0]
  - h q[1]
  - barrier
  - rx(2 * $x0) q[0]
  - rx(2 * $x1) q[1]
  - barrier
  - cx q[0], q[1]
  - ry(2 * $x0 * $x1) q[1]
  - cx q[0], q[1]
```

### Example: QAOA Optimization Ansatz

```yaml
circuit: QAOA_Ansatz_p1
metadata:
  type: QAOA Ansatz
  description: A simple 2-qubit QAOA ansatz with p=1
qreg: q[2]
parameters:
  gamma: 0.5
  beta: 1.2
instructions:
  # Initial state preparation
  - h q[0]
  - h q[1]
  - barrier
  # Cost Hamiltonian Layer
  - cx q[0], q[1]
  - ry(2 * $gamma) q[1]
  - cx q[0], q[1]
  - barrier
  # Mixer Hamiltonian Layer
  - rx(2 * $beta) q[0]
  - rx(2 * $beta) q[1]
```

## Supported Gates

- **Single-qubit gates**: `h` (Hadamard), `x` (Pauli-X)
- **Two-qubit gates**: `cx` (CNOT), `swap`
- **Parameterized single-qubit gates**: `rx(angle)`, `ry(angle)` - Rotation gates
- **Parameterized two-qubit gates**: `cphase(angle)` - Controlled phase gate
- **Utility**: `barrier` (visual separator), `measure` (measures all qubits)

### Parameter Expressions

Parameters can use arithmetic expressions with:
- **Variables**: Use `$variable_name` to reference parameters
- **Constants**: `pi`, `np.pi`
- **Operators**: `+`, `-`, `*`, `/`, `**` (power)
- **Functions**: Any NumPy functions available via `np.*`
- **Examples**: 
  - `rx($theta) q[0]` - Simple parameter
  - `ry(2 * $gamma) q[1]` - Arithmetic expression
  - `cphase(2 * (pi - $x0) * (pi - $x1)) q[0], q[1]` - Complex expression

## Usage

```python
from quyaml_parser import parse_quyaml_to_qiskit

quyaml_string = """
circuit: BellState
qreg: q[2]
instructions:
  - h q[0]
  - cx q[0], q[1]
"""

# Parse QuYAML to Qiskit circuit
qc = parse_quyaml_to_qiskit(quyaml_string)

# Use the circuit with Qiskit
print(qc)
qc.draw('mpl')
```

## Testing

The project includes comprehensive test coverage:

1. **Unit Tests** (`tests/test_valid_circuits.py`): Tests for valid circuit parsing with metamorphic testing
2. **Advanced Circuit Tests** (`tests/test_advanced_circuits.py`): QML feature maps and QAOA ansatz circuits
3. **Failure Tests** (`tests/test_invalid_syntax.py`): Error handling and edge cases
4. **Property-Based Tests** (`tests/test_property_based.py`): Hypothesis-based generative testing

Run all tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/test_valid_circuits.py
```

## Error Handling

The parser raises `QuYamlError` exceptions for:
- Invalid YAML syntax
- Missing quantum register definition
- Unknown gate names
- Incorrect gate arguments
- Out-of-bounds qubit indices
- Undefined parameters in expressions
- Invalid parameter expressions

## CI/CD

The repository includes a GitHub Actions workflow that:
- Runs on Python 3.10 and 3.11
- Executes all tests automatically on push/pull request
- Ensures code quality and reliability

## Project Structure

```
QuYAML/
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI/CD
├── tests/
│   ├── test_valid_circuits.py     # Basic circuit unit tests
│   ├── test_advanced_circuits.py  # QML & optimization tests
│   ├── test_invalid_syntax.py     # Error handling tests
│   └── test_property_based.py     # Hypothesis property tests
├── quyaml_parser.py               # Main parser implementation
├── requirements.txt               # Python dependencies
├── pytest.ini                     # Pytest configuration
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

## Dependencies

- `pyyaml`: YAML parsing
- `qiskit`: Quantum circuit framework
- `qiskit-machine-learning`: QML algorithms and feature maps
- `qiskit-optimization`: Quantum optimization algorithms (QAOA, VQE)
- `qiskit-aer`: High-performance quantum circuit simulation
- `numpy`: Numerical operations and parameter evaluation
- `pytest`: Testing framework
- `hypothesis`: Property-based testing

## Contributing

Contributions are welcome! Please ensure all tests pass before submitting a pull request.

## License

This project is open source and available for educational and research purposes.

## Author

Ahmed Samir

## Acknowledgments

Built with Qiskit and tested with Hypothesis for robust quantum circuit parsing.
