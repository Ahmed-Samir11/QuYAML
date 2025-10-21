# QuYAML

A robust, production-ready parser for converting QuYAML (Quantum YAML) syntax into Qiskit QuantumCircuit objects.

## Overview

QuYAML provides a simple, human-readable YAML-based syntax for defining quantum circuits. This parser translates QuYAML files into executable Qiskit circuits, making quantum circuit definition more accessible and maintainable.

## Features

- 🔄 **Clean YAML Syntax**: Define quantum circuits using intuitive YAML structure
- 🎯 **Qiskit Integration**: Seamless conversion to Qiskit QuantumCircuit objects
- 🧪 **Comprehensive Testing**: Unit tests, failure case tests, and property-based tests using Hypothesis
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
qreg: q[num_qubits]
creg: c[num_classical_bits]  # Optional
instructions:
  - gate_name qubit_targets
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

## Supported Gates

- **Single-qubit gates**: `h` (Hadamard), `x` (Pauli-X)
- **Two-qubit gates**: `cx` (CNOT), `swap`
- **Parametric gates**: `cphase(angle)` - Controlled phase gate
- **Measurement**: `measure` (measures all qubits)

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

The project includes three types of tests:

1. **Unit Tests** (`tests/test_valid_circuits.py`): Tests for valid circuit parsing
2. **Failure Tests** (`tests/test_invalid_syntax.py`): Tests for error handling
3. **Property-Based Tests** (`tests/test_property_based.py`): Advanced tests using Hypothesis

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
│       └── ci.yml              # GitHub Actions CI/CD
├── tests/
│   ├── test_valid_circuits.py  # Unit tests
│   ├── test_invalid_syntax.py  # Failure case tests
│   └── test_property_based.py  # Hypothesis property tests
├── quyaml_parser.py            # Main parser implementation
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## Dependencies

- `pyyaml`: YAML parsing
- `qiskit`: Quantum circuit framework
- `numpy`: Numerical operations
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
