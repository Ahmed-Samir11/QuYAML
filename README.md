# QuYAML v0.4: A Human-Readable Standard for Quantum Circuits

QuYAML is a token-efficient, human-readable data format for defining quantum circuits, designed for the age of AI-driven quantum development.

[![Tests](https://img.shields.io/badge/tests-21%20passed-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()
[![Release](https://img.shields.io/github/v/release/Ahmed-Samir11/QuYAML)](https://github.com/Ahmed-Samir11/QuYAML/releases/latest)
[![QASM3 Import](https://img.shields.io/badge/qasm3%20import-enabled-brightgreen)](https://pypi.org/project/qiskit-qasm3-import/)
[![Benchmarks](https://github.com/Ahmed-Samir11/QuYAML/actions/workflows/benchmark.yml/badge.svg)](https://github.com/Ahmed-Samir11/QuYAML/actions/workflows/benchmark.yml)

This repository contains the official Python tooling for the QuYAML format. The parser now targets the **v0.4** specification by default, with a legacy opt-in for v0.2/0.3. It converts `.quyaml` files or strings into executable Qiskit `QuantumCircuit` objects and provides a CLI for validation, conversion, diffs, and benchmarking.

Highlights in v0.4:
- Structured control flow: if/elif/else, while, and for blocks
- Composite conditions with `&&` and `||` (lowered to Qiskit dynamic-circuit builders)
- Safer YAML surface: rejects anchors, aliases, custom tags, and merge keys
- Strict schema and canonical formatter; JSON Schema shipped in `docs/schema/quyaml.schema.json`
- CLI: validate, lint, format, convert (QuYAML↔QASM3), diff (human/JSON), compile (compact JSON)
- CI-friendly parse-time gates and token-count gates

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
| OpenQASM 2.0 | 84.9 | **-3.5% better** ✅ | $254.64 (-$9) |
| OpenQASM 3.0 | 83.9 | **-4.8% better** ✅ | $251.64 (-$12) |
| **QuYAML (Optimized)** | **87.9** | baseline | **$263.64** |
| JSON (Qiskit) | 325.0 | **+72.9% worse** ❌ | $975.00 (+$711) |

**Key Findings:**
- ✅ **73% more efficient than JSON** - Save $711 per 100K API calls vs JSON
- ⚠️ **3.5% behind OpenQASM 2.0** - Costs $9 more per 100K calls
- ⚠️ **4.8% behind OpenQASM 3.0** - Costs $12 more per 100K calls
- ✨ **Wins on simple circuits** - 15.8% better than OpenQASM for non-parameterized circuits (Bell, GHZ, QFT, Teleportation)
- 📊 **Loses on parameterized circuits** - 17.2% worse than OpenQASM for circuits with symbolic parameters (QAOA, VQE, Max-Cut, Grover)

**Trade-off:** QuYAML prioritizes human readability with symbolic parameters (`$gamma`, `2*$beta`) over maximum token efficiency. OpenQASM's pre-evaluated numeric values (`1.0`, `2.4`) are more token-efficient but less readable for humans and LLMs working with parameterized circuits.

See [`benchmarks/README.md`](benchmarks/README.md) for detailed per-circuit analysis.

## QuYAML v0.4 at a glance

QuYAML supports both **original** and **optimized** syntax (fully backward compatible):

### Optimized Syntax (Recommended for LLMs)
```yaml
# Bell state – minimal and token-efficient
version: 0.4
circuit: bell
qubits: q[2]
bits: c[2]
ops:
  - h 0
  - cx 0 1
  - measure
```

### Original Syntax (Human-Readable)
```yaml
# Bell state – explicit and descriptive
version: 0.4
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

### Parameterized circuits
```yaml
version: 0.4
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

### Control flow (new in v0.4)

Conditional blocks with composite conditions:

```yaml
version: 0.4
qubits: q[2]
bits: c[2]
ops:
  - h 0
  - {measure: {q: 0, c: 0}}
  - if:
      cond: "c[0] == 1 && c[1] == 0"   # && and || supported
      then:
        - x 1
      else:
        - h 1
```

While and for-loops:

```yaml
version: 0.4
qubits: q[1]
bits: c[1]
ops:
  - reset 0         # string form
  - while:
      cond: "c[0] == 0"
      body:
        - h 0
        - {measure: {q: 0, c: 0}}
  - for:
      range: [0, 3]  # start, stop (exclusive)
      body:
        - rx(pi/4) 0
```

Reset and measure forms:

- `reset 0` or `{reset: {q: 0}}`
- `measure` (all qubits) or `{measure: {q: 0, c: 0}}` for mid-circuit bit-targeted measurement

## Installation

```bash
# Clone the repository
git clone https://github.com/Ahmed-Samir11/QuYAML.git
cd QuYAML

# Install dependencies
pip install -r requirements.txt
```

Dependencies: `pyyaml`, `qiskit`, `numpy` (plus optional: `tiktoken`, `jsonschema`)

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

quantum_circuit = parse_quyaml_to_qiskit(quyaml_string)
print(quantum_circuit)
quantum_circuit.draw('mpl')
```

### Advanced example: Parameterized QAOA circuit

```python
from quyaml_parser import parse_quyaml_to_qiskit

quyaml_string = """
version: 0.4
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

## PennyLane compatibility

QuYAML circuits can be used directly with PennyLane via an optional helper:

```python
import pennylane as qml
from quyaml_pennylane import parse_quyaml_to_pennylane

quyaml_string = """
circuit: bell
qubits: q[2]
ops:
  - h 0
  - cx 0 1
"""

my_template = parse_quyaml_to_pennylane(quyaml_string)  # returns a PennyLane quantum function

dev = qml.device("default.qubit", wires=2)

@qml.qnode(dev)
def pl_circuit():
    my_template(wires=[0, 1])
    return qml.expval(qml.Z(0))

print(pl_circuit())
```

Notes:
- Requires installing optional dependencies: `pip install pennylane pennylane-qiskit`
- Under the hood, QuYAML -> Qiskit QuantumCircuit -> PennyLane via `qml.from_qiskit()`
```

## Testing & verification

To verify the parser's correctness, install the test dependencies and run pytest:

```bash
pip install -r requirements.txt
pytest
```

The project includes comprehensive tests for v0.4 features and QASM3 round-trips.

### Dev setup notes

- QASM3 round-trip tests require the optional OpenQASM 3 loader: `pip install qiskit_qasm3_import`.
- We pin Qiskit to the 2.x line for compatibility with dynamic circuits and optional integrations: `qiskit>=2.0,<2.2` (see `requirements.txt`).
- If you use PennyLane’s qiskit plugin, ensure versions are compatible with the Qiskit pin.

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

### Additional Docs

- Expert evaluation and roadmap: [`docs/EVALUATION_v0.2.md`](docs/EVALUATION_v0.2.md)

### PennyLane-style Benchmarks (QuYAML vs JSON vs OpenQASM 3)

We also evaluated a set of harder, PennyLane-style circuits (QAOA Max-Cut, QFT, Grover, Phase Estimation, random entangling layers, and a shallow quantum-volume-like circuit), using exact GPT-4 tokenization and measuring parse times:

- Tokens are counted for the QuYAML source, a compact Qiskit JSON representation, and OpenQASM 3 generated from the same circuit.
- Parse times measure: QuYAML parse (QuYAML → Qiskit), JSON decode only, and QASM3 parse via Qiskit’s `qasm3.loads`.

Update (includes v0.3 control-flow case and JSON→Qiskit rebuild timing):

- New case: Conditional full-register equality (2q)
  - Tokens: QuYAML 131, JSON 442, QASM3 90
  - Parse times (ms): QuYAML 3.545, JSON decode 0.013, JSON rebuild 0.168, QASM3 parse 8.464

Refreshed averages across all tests:

- Tokens: QuYAML 424.6, JSON 633.8, QASM3 372.9
- QuYAML vs JSON: +33.0% fewer tokens than JSON
- QuYAML vs QASM3: −13.9% more tokens than QASM3 (QASM3 wins on average)
- Parse times (ms): QuYAML 6.269, JSON decode 0.051, JSON rebuild 0.672, QASM3 parse 21.475

Per-circuit token counts and deltas:

| Circuit | QuYAML | JSON | QASM3 | QuYAML vs JSON | QuYAML vs QASM3 |
|---|---:|---:|---:|---:|---:|
| QAOA Max-Cut p=3 (ring-6) | 678 | 715 | 484 | +5.2% | -40.1% |
| QFT (5 qubits) | 191 | 346 | 195 | +44.8% | +2.1% |
| Grover (4q, oracle=1111) | 268 | 527 | 236 | +49.1% | -13.6% |
| Phase Estimation (3+1) | 122 | 225 | 126 | +45.8% | +3.2% |
| QAOA Max-Cut p=5 (ring-6) | 948 | 1123 | 772 | +15.6% | -22.8% |
| Random entangling (n=6, d=4) | 738 | 1152 | 718 | +35.9% | -2.8% |
| Quantum-volume-like (n=6, layers=2) | 321 | 540 | 362 | +40.6% | +11.3% |

Per-circuit parse times (milliseconds):

| Circuit | QuYAML parse | JSON decode | QASM3 parse |
|---|---:|---:|---:|
| QAOA Max-Cut p=3 (ring-6) | 7.409 | 0.068 | 30.593 |
| QFT (5 qubits) | 3.061 | 0.040 | 13.344 |
| Grover (4q, oracle=1111) | 3.443 | 0.035 | 20.074 |
| Phase Estimation (3+1) | 1.737 | 0.018 | 8.313 |
| QAOA Max-Cut p=5 (ring-6) | 11.093 | 0.076 | 36.120 |
| Random entangling (n=6, d=4) | 7.730 | 0.083 | 45.472 |
| Quantum-volume-like (n=6, layers=2) | 4.352 | 0.037 | 21.815 |

Reproduce locally:

```powershell
# Activate venv (Windows PowerShell)
& F:/repos/QuYAML/quyaml/Scripts/Activate.ps1

# Run the PennyLane-style benchmark
F:/repos/QuYAML/quyaml/Scripts/python.exe benchmarks/benchmark_pennylane.py
```

The latest run output is saved to `benchmarks/_last_pennylane_results.txt`.

## CLI utilities

The CLI supports validate, lint, format, convert (QuYAML↔QASM3), diff, compile (compact JSON), count-tokens, and time-parse. Use a file path or `-` for stdin.

```powershell
# Validate and print a summary
F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/quyaml_cli.py validate examples/bell.quyaml --summary

# Lint with JSON Schema (if jsonschema installed) and parse check
F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/quyaml_cli.py lint examples/bell.quyaml

# Format to canonical key order and style (in-place)
F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/quyaml_cli.py format examples/bell.quyaml -w

# Convert QuYAML -> QASM3
F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/quyaml_cli.py convert examples/bell.quyaml --to qasm3 -o -

# Convert QASM3 -> QuYAML
Get-Content examples/bell.qasm | F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/quyaml_cli.py convert --from qasm3 - > bell.quyaml

# Structural diff (human)
F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/quyaml_cli.py diff a.quyaml b.quyaml

# Structural diff (JSON)
F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/quyaml_cli.py diff a.quyaml b.quyaml --json

# Compile to compact JSON (for benchmarking/token counting)
F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/quyaml_cli.py compile examples/bell.quyaml -o -

# Count tokens across QuYAML/JSON/QASM3 (requires tiktoken)
F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/quyaml_cli.py count-tokens examples/bell.quyaml --json --qasm3

# Measure average parse time (ms) over N iterations
F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/quyaml_cli.py time-parse examples/bell.quyaml -n 200
```

## CI and performance gates

We ship a CI-friendly benchmark harness `scripts/bench_ci.py` to keep parse-time regressions and token budgets under control.

Examples:

```powershell
# Parse-time gates for small, static samples
F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/bench_ci.py --iters 300 --max-ms 100 benchmarks/samples/ghz.quyaml benchmarks/samples/qft3.quyaml benchmarks/samples/control_flow.quyaml

# Parse-time gates for dynamic circuits (looser threshold)
F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/bench_ci.py --iters 300 --max-ms 200 benchmarks/samples/teleportation.quyaml benchmarks/samples/ipea.quyaml benchmarks/samples/rus.quyaml

# Token-count gates for static samples (500 tokens)
F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/bench_ci.py --max-tokens 500 benchmarks/samples/ghz.quyaml benchmarks/samples/qft3.quyaml benchmarks/samples/control_flow.quyaml

# Token-count gates for dynamic circuits (higher threshold e.g. 1000)
F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/bench_ci.py --max-tokens 1000 benchmarks/samples/teleportation.quyaml benchmarks/samples/ipea.quyaml benchmarks/samples/rus.quyaml
```

Our GitHub Actions workflow `.github/workflows/ci.yml` runs a matrix across Windows and Ubuntu with Python 3.11/3.12, executes unit tests, and enforces the gates above. Adjust thresholds per your project needs.

## YAML safety and restrictions (enforced)

To keep parsing safe and predictable for both humans and LLMs, the parser enforces a restricted YAML subset and resource guardrails:

- Not allowed: YAML anchors (&name), aliases (*name), custom tags (!tag), and merge keys (<<:)
- Size limits: sane ceilings on input length and nesting depth
- Safe loader: prefers CSafeLoader when available, otherwise safe_load

Violations fail parsing with a clear error. See the JSON Schema in `docs/schema/quyaml.schema.json` for structural validation.

### YAML safety and restrictions

To keep parsing safe and predictable for both humans and LLMs, the parser enforces a restricted YAML subset:

- Allowed: plain mappings/sequences/scalars used by the QuYAML fields
- Not allowed: YAML anchors (&name) and aliases (*name)
- Not allowed: YAML custom tags (!tag)

If any of these are present, parsing will fail with a clear error. We also use `yaml.safe_load` under the hood.

Editor tip: VS Code users get schema validation and completion by opening this repo; it includes `.vscode/settings.json` mapping the QuYAML schema (`docs/schema/quyaml.schema.json`) to `*.quyaml` files.

## QuYAML language reference (selected)

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

### Parameter substitution

Use `$variable` to reference parameters, and expressions are evaluated with NumPy:

```yaml
params: {theta: 0.5, gamma: 1.2}
ops:
  - rx(2*$theta) 0
  - ry($gamma+pi/4) 1
  - cphase(2*(pi-$theta)) 0 1
```

Supported constants: `pi`, `e`

Operators: `+`, `-`, `*`, `/`, `**`, `%`

Functions: a minimal safe subset sufficient for common arithmetic; expression evaluation is sandboxed.

For full details, browse the parser source in `quyaml_parser.py`.

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

## Migration

Coming from v0.2 or v0.3? See the migration guide: [docs/MIGRATION_0.3_to_0.4.md](docs/MIGRATION_0.3_to_0.4.md)

## Citation

If you use QuYAML in your research, please cite:

```bibtex
@software{quyaml2025,
  author = {Ahmed Samir},
  title = {QuYAML: A Token-Efficient Standard for Quantum Circuits},
  year = {2025},
  url = {https://github.com/Ahmed-Samir11/QuYAML},
  version = {0.4.0}
}
```

## Contact

**Ahmed Samir**  
GitHub: [@Ahmed-Samir11](https://github.com/Ahmed-Samir11)  
Project Link: [https://github.com/Ahmed-Samir11/QuYAML](https://github.com/Ahmed-Samir11/QuYAML)

---

**Built for the age of AI-driven quantum development.** 🚀
