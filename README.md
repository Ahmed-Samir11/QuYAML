# QuYAML: A Human-Readable Standard for Quantum Circuits

**QuYAML is a token-efficient, human-readable data format for defining quantum circuits, designed for the age of AI-driven quantum development.**

[![Tests](https://img.shields.io/badge/tests-14%20passed-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

This repository contains the official Python parser for the **QuYAML v0.2** specification. It provides a robust, well-tested tool to convert `.quyaml` files or strings into executable Qiskit `QuantumCircuit` objects.

## Why QuYAML?

As we increasingly use Large Language Models (LLMs) to assist in quantum development, the verbosity of standard formats like JSON becomes a bottleneck. QuYAML solves this by being:

- **Token-Efficient**: Achieves **73% fewer tokens** compared to standard Qiskit JSON (measured with exact GPT-4 tokenization)
- **Human-Readable**: Clean, minimal syntax makes it easy for researchers to write, read, and share circuit designs
- **Structured & Extensible**: Built on YAML, it's easy to extend with new features like metadata and parameters
- **Production-Ready**: Comprehensive test suite with metamorphic testing ensures mathematical correctness

## Performance Comparison

Using exact GPT-4 tokenization across 8 diverse quantum circuits:

| Format | Avg Tokens | vs QuYAML | Cost per 100K calls |
|--------|-----------|-----------|---------------------|
| **QuYAML (Optimized)** | **87.9** | baseline | **$263.64** |
| OpenQASM 2.0 | 84.9 | +3.5% | $254.64 (-$9) |
| JSON (Qiskit) | 325.0 | -73.0% | $975.00 (+$711) |

**Key Findings:**
- ✅ **73% more efficient than JSON** - Save $711 per 100K API calls
- ⚠️ **3.5% behind OpenQASM overall** - Trade-off for readability and symbolic parameters
- ✨ **Wins on simple circuits** - 15.8% better than OpenQASM for non-parameterized circuits
- 📊 **Loses on parameterized circuits** - 17.2% worse than OpenQASM (pre-evaluated values win)

See [`benchmarks/README.md`](benchmarks/README.md) for detailed analysis.

## QuYAML v0.2 Specification

QuYAML supports both **original** and **optimized** syntax (fully backward compatible):

### Optimized Syntax (Recommended for LLMs)
```yaml
# Bell State - Maximum token efficiency
circuit: bell
qubits: q[2]
bits: c[2]
ops:
  - h 0
  - cx 0 1
  - measure
```

## Installation

### Quick Start

```bash
# Clone the repository
git clone https://github.com/Ahmed-Samir11/QuYAML.git
cd QuYAML

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

```bash
pip install pyyaml qiskit numpy
```

## Usage

```python
from quyaml_parser import parse_quyaml_to_qiskit

quyaml_string = """
circuit: MyFirstCircuit
qreg: q[1]
instructions:
  - h q[0]
"""

try:
    quantum_circuit = parse_quyaml_to_qiskit(quyaml_string)
    print("Successfully parsed circuit:")
    print(quantum_circuit)
    # Use with Qiskit
    quantum_circuit.draw('mpl')
except Exception as e:
    print(f"Error: {e}")
```

### Advanced Example: Parameterized QAOA Circuit

```python
from quyaml_parser import parse_quyaml_to_qiskit

### Original Syntax (Human-Readable)
```yaml
# Bell State - Explicit and descriptive
circuit: BellState
metadata:
  description: Creates an entangled Bell pair
qreg: q[2]
creg: c[2]
instructions:
  - h q[0]
  - cx q[0], q[1]
  - measure
```

### Parameterized Circuits
```yaml
# QAOA Ansatz - Supports symbolic parameters
circuit: qaoa_p1
qubits: q[2]
params: {gamma: 0.5, beta: 1.2}
ops:
  - h 0
  - h 1
  - cphase(2*$gamma) 0 1
  - rx(2*$beta) 0
  - rx(2*$beta) 1
```

## Installation

### Quick Start

```bash
# Clone the repository
git clone https://github.com/Ahmed-Samir11/QuYAML.git
cd QuYAML

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

```bash
pip install pyyaml qiskit numpy
```

## Usage

### Basic Example
```python
from quyaml_parser import parse_quyaml_to_qiskit

# Optimized syntax for token efficiency
quyaml_string = """
circuit: bell
qubits: q[2]
ops:
  - h 0
  - cx 0 1
"""

try:
    quantum_circuit = parse_quyaml_to_qiskit(quyaml_string)
    print("Successfully parsed circuit:")
    print(quantum_circuit)
    # Use with Qiskit
    quantum_circuit.draw('mpl')
except Exception as e:
    print(f"Error: {e}")
```

### Advanced Example: Parameterized QAOA Circuit

```python
from quyaml_parser import parse_quyaml_to_qiskit

quyaml_string = """
circuit: QAOA_Ansatz
qubits: q[2]
params: {gamma: 0.5, beta: 1.2}
ops:
  - h 0
  - h 1
  - barrier
  - cx 0 1
  - ry(2*$gamma) 1
  - cx 0 1
  - barrier
  - rx(2*$beta) 0
  - rx(2*$beta) 1
"""

qc = parse_quyaml_to_qiskit(quyaml_string)
print(qc)
```

## Testing & Verification

To verify the parser's correctness, install the test dependencies and run pytest:

```bash
pip install -r requirements.txt
pytest
```

The project includes comprehensive test coverage with **14 tests, 100% passing**:

1. **Unit Tests** (`tests/test_valid_circuits.py`): Basic circuit parsing with metamorphic testing
2. **Advanced Circuit Tests** (`tests/test_advanced_circuits.py`): QML feature maps and QAOA ansatz circuits
3. **Advanced Algorithm Tests** (`tests/test_advanced_algorithms.py`): QFT, QAOA Max-Cut, Toffoli decomposition, VQE, Quantum Teleportation
4. **Failure Tests** (`tests/test_invalid_syntax.py`): Error handling and edge cases
5. **Property-Based Tests** (`tests/test_property_based.py`): Hypothesis-based generative testing

### Metamorphic Testing

The test suite includes **metamorphic tests** that prove the parser produces circuits mathematically identical to those created by Qiskit. These tests compare unitary matrices using `Operator.equiv()`, ensuring correctness for complex algorithms like:
- Quantum Fourier Transform (QFT)
- QAOA optimization ansätze
- Variational Quantum Eigensolver (VQE) circuits
- Quantum Teleportation protocol

Run tests with verbose output:
```bash
pytest -v
```

## Benchmarks

### Running Benchmarks

```bash
# Recommended: Optimized syntax with exact GPT-4 tokenization
python benchmarks/benchmark_optimized.py

# Original syntax baseline
python benchmarks/benchmark_with_tiktoken.py

# Test syntax compatibility
python benchmarks/test_optimized_syntax.py
```

### Results Summary

Using exact GPT-4 tokenization (`tiktoken`) across 8 diverse circuits:

| Circuit Type | OpenQASM | QuYAML | Improvement |
|-------------|----------|--------|-------------|
| **Simple Circuits** | 62.8 | 53.5 | **+15.8%** ✓ |
| Bell State | 46 | 37 | +19.6% |
| GHZ (3 qubits) | 55 | 46 | +16.4% |
| Teleportation | 60 | 51 | +15.0% |
| QFT (3 qubits) | 90 | 79 | +12.2% |
| **Parameterized** | 107.0 | 125.3 | **-17.2%** ✗ |
| QAOA (p=1) | 65 | 82 | -26.2% |
| VQE Ansatz | 78 | 95 | -21.8% |
| **Overall Average** | **84.9** | **87.9** | **-3.5%** |

**Compared to JSON:**
- QuYAML: 87.9 tokens (average)
- JSON: 325.0 tokens (average)
- **Reduction: 73.0%** ✓

**Cost Impact** (GPT-4 API @ $0.03/1K tokens):
- QuYAML vs OpenQASM: -$9 per 100K calls (negligible)
- QuYAML vs JSON: +$711 per 100K calls (significant savings)

See [`benchmarks/README.md`](benchmarks/README.md) and [`OPTIMIZATION_RESULTS.md`](OPTIMIZATION_RESULTS.md) for detailed analysis.

## QuYAML v0.2 Language Reference

### Field Names (Aliases Supported)

Both original and optimized syntax work identically:

| Feature | Original | Optimized |
|---------|----------|-----------|
| Quantum register | `qreg: q[n]` | `qubits: q[n]` |
| Classical register | `creg: c[n]` | `bits: c[n]` |
| Parameters | `parameters:` | `params:` |
| Instructions | `instructions:` | `ops:` |
| Qubit index | `q[0]` | `0` (implicit) |

### Required Fields

```yaml
circuit: CircuitName         # Circuit identifier
qubits: q[n]                 # Quantum register (n qubits) [or qreg]
ops:                         # List of operations [or instructions]
  - gate_name args
```

### Optional Fields

```yaml
bits: c[n]                   # Classical register (n bits) [or creg]
params:                      # Symbolic parameters [or parameters]
  theta: 0.5
  gamma: 1.2
metadata:                    # Circuit metadata (optional, ignored by parser)
  description: "Circuit description"
  author: "Your Name"
```

### Supported Gates

| Gate | Original Syntax | Optimized Syntax | Description |
|------|----------------|------------------|-------------|
| Hadamard | `h q[0]` | `h 0` | Single-qubit Hadamard |
| Pauli-X | `x q[0]` | `x 0` | Bit flip gate |
| CNOT | `cx q[0], q[1]` | `cx 0 1` | Controlled-NOT |
| SWAP | `swap q[0], q[1]` | `swap 0 1` | Swap two qubits |
| RX | `rx(theta) q[0]` | `rx(theta) 0` | X-axis rotation |
| RY | `ry(theta) q[0]` | `ry(theta) 0` | Y-axis rotation |
| Controlled-Phase | `cphase(theta) q[0], q[1]` | `cphase(theta) 0 1` | Controlled phase gate |
| Barrier | `barrier` | `barrier` | Prevent optimization across barrier |
| Measure | `measure` | `measure` | Measure all qubits |

### Parameter Substitution

Use `$variable` to reference parameters, and expressions are evaluated with NumPy:

```yaml
params: {theta: 0.5, gamma: 1.2}
ops:
  - rx(2*$theta) 0
  - ry($gamma+pi/4) 1
  - cphase(2*(pi-$theta)) 0 1
```

**Supported constants**: `pi`, `e` (from NumPy)  
**Supported operators**: `+`, `-`, `*`, `/`, `**` (exponentiation)  
**Supported functions**: All NumPy functions (e.g., `sin`, `cos`, `sqrt`)

## When to Use QuYAML

### ✅ Use QuYAML When:
- Defining simple, non-parameterized circuits (15.8% better than OpenQASM)
- Human readability and symbolic parameters matter
- Replacing JSON for LLM interactions (73% token reduction)
- Cost difference is negligible ($0.000090 per circuit call)
- Working with quantum AI/ML applications

### ⚠️ Consider OpenQASM When:
- Heavily parameterized circuits with pre-evaluated values
- Token efficiency is absolutely critical
- High-volume production workloads (millions of API calls)
- Legacy integration with OpenQASM ecosystem

### ❌ Never Use JSON:
- For LLM input (73-81% worse than QuYAML)
- Use only for structured data storage

## Roadmap

QuYAML is under active development. Future versions will include:

- **v0.3**: Support for custom gates, multi-qubit gates (Toffoli, Fredkin), and improved error messages
- **v0.4**: Circuit composition and subcircuit definitions
- **v1.0**: Full specification with standardized metadata, versioning, and extended gate library

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Add tests for your changes
4. Ensure all tests pass (`pytest`)
5. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
6. Push to the branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use QuYAML in your research, please cite:

```bibtex
@software{quyaml2025,
  author = {Ahmed Samir},
  title = {QuYAML: A Token-Efficient Standard for Quantum Circuits},
  year = {2025},
  url = {https://github.com/Ahmed-Samir11/QuYAML},
  version = {0.1.1}
}
```

## Contact

**Ahmed Samir**  
GitHub: [@Ahmed-Samir11](https://github.com/Ahmed-Samir11)  
Project Link: [https://github.com/Ahmed-Samir11/QuYAML](https://github.com/Ahmed-Samir11/QuYAML)

---

**Built for the age of AI-driven quantum development.** 🚀
