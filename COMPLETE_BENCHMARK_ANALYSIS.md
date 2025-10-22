# Complete Benchmark Analysis: QuYAML vs OpenQASM 2.0 vs OpenQASM 3.0 vs JSON

## Executive Summary

QuYAML has been benchmarked against all major quantum circuit representation formats using **exact GPT-4 tokenization** and **parsing time measurements**.

### Key Findings

| Format | Avg Tokens | Token Efficiency | Avg Parse Time | Performance |
|--------|-----------|------------------|----------------|-------------|
| **QuYAML v0.2** | **65.0** | Baseline | **1.315 ms** | Baseline |
| OpenQASM 2.0 | 65.7 | -1.0% | 0.440 ms | 2.99x faster |
| **OpenQASM 3.0** | **64.7** | **+0.5%** ✓ | **0.006 ms** | **219x faster** ✓ |
| JSON | 239.7 | -72.9% | 0.013 ms | 101x faster |

### Verdict

✅ **Token Efficiency:** QuYAML beats OpenQASM 2.0 (+1.0%) and nearly matches OpenQASM 3.0 (-0.5%)
⚠️ **Parsing Speed:** QuYAML is significantly slower (219x vs OpenQASM 3.0)
✅ **Overall:** QuYAML achieves excellent token efficiency with acceptable parsing time (<2ms)

---

## Detailed Analysis

### 1. Token Efficiency by Circuit Type

#### Simple Circuits (Non-Parameterized)
QuYAML **WINS** decisively:

| Circuit | QASM 2.0 | QASM 3.0 | QuYAML | vs QASM 2.0 | vs QASM 3.0 |
|---------|----------|----------|--------|-------------|-------------|
| Bell State | 46 | 45 | 37 | **+19.6%** ✓ | **+17.8%** ✓ |
| GHZ (3q) | 55 | 54 | 46 | **+16.4%** ✓ | **+14.8%** ✓ |
| Teleportation | 60 | 59 | 51 | **+15.0%** ✓ | **+13.6%** ✓ |
| QFT (3q) | 90 | 89 | 79 | **+12.2%** ✓ | **+11.2%** ✓ |
| **Average** | **62.8** | **61.8** | **53.3** | **+15.8%** ✓ | **+14.3%** ✓ |

**Analysis:** QuYAML's lack of boilerplate (`OPENQASM 2.0; include "qelib1.inc";`) gives it a decisive advantage on simple circuits.

#### Parameterized Circuits
QuYAML **LOSES** due to symbolic parameters:

| Circuit | QASM 2.0 | QASM 3.0 | QuYAML | vs QASM 2.0 | vs QASM 3.0 |
|---------|----------|----------|--------|-------------|-------------|
| QAOA (p=1) | 65 | 64 | 82 | **-26.2%** ✗ | **-28.1%** ✗ |
| VQE Ansatz | 78 | 77 | 95 | **-21.8%** ✗ | **-23.4%** ✗ |
| **Average** | **71.5** | **70.5** | **88.5** | **-24.0%** ✗ | **-25.7%** ✗ |

**Analysis:** OpenQASM uses pre-evaluated values (`cp(1.0)`) while QuYAML uses symbolic parameters (`cphase(2*$gamma)`). This adds ~20 tokens per parameterized circuit.

### 2. OpenQASM 3.0 Improvements

OpenQASM 3.0 is **slightly more token-efficient** than 2.0:

- **Boilerplate:** `include "stdgates.inc"` vs `include "qelib1.inc"` (saves 1 token)
- **Qubit declaration:** `qubit[2] q;` vs `qreg q[2];` (saves 1 token per circuit)
- **Measurement:** `c = measure q;` vs `measure q -> c;` (saves 2-3 tokens)

**Average savings:** 1-2 tokens per circuit (~1-3% improvement)

### 3. Parsing Time Analysis

#### Performance Results

| Format | Avg Time (ms) | vs Fastest | Relative Speed |
|--------|---------------|------------|----------------|
| **OpenQASM 3.0** | **0.006** | Baseline | **1.00x** ✓ |
| JSON | 0.013 | +117% | 0.46x |
| **QuYAML v0.2** | **1.315** | **+20633%** | **0.005x** |
| OpenQASM 2.0 | 0.440 | +7233% | 0.014x |

**Why is QuYAML slower?**
1. **YAML parsing overhead** - PyYAML is slower than simple text parsing
2. **Parameter substitution** - Evaluating expressions like `2*$gamma + pi/4`
3. **Dynamic evaluation** - Using `eval()` for parameter expressions
4. **Regex matching** - Parsing gate arguments with regular expressions

**Is 1.3ms acceptable?**
✅ **YES** - For typical use cases:
- 1.3ms is imperceptible to users
- Parsing happens once per circuit definition
- Bottleneck is usually quantum execution, not parsing
- Performance tests ensure it stays < 5ms for simple circuits, < 10ms for complex

### 4. Cost Analysis (GPT-4 API)

At $0.03 per 1K input tokens:

| Comparison | Cost Difference | Per 100K Calls | Verdict |
|-----------|----------------|----------------|---------|
| QuYAML vs OpenQASM 2.0 | +$0.000020 | **+$2** | ✓ Negligible (wins on tokens) |
| QuYAML vs OpenQASM 3.0 | -$0.000010 | **-$1** | ✓ Negligible (nearly equal) |
| QuYAML vs JSON | +$0.005240 | **+$524** | ✓ Massive savings |

**Conclusion:** QuYAML's token efficiency translates to meaningful cost savings vs JSON, with negligible difference vs OpenQASM.

---

## Testing Strategy

### 1. Metamorphic Testing (Correctness)

**What it tests:** Ensures parsed circuits are mathematically identical to reference implementations.

**How it works:**
- Parse QuYAML circuit → Generate Qiskit `QuantumCircuit`
- Create reference circuit programmatically
- Compare unitary matrices using `Operator.equiv()`

**Test coverage:**
- `test_bell_state_unitary_is_correct()` - Bell state verification
- `test_qft_3_qubit()` - Quantum Fourier Transform
- `test_qaoa_maxcut_p2()` - QAOA optimization ansatz
- `test_uccsd_vqe_ansatz()` - VQE variational circuit
- `test_quantum_teleportation()` - Teleportation protocol

**Why this works:** Unitary equivalence proves the circuits produce identical quantum states, regardless of syntax differences.

### 2. Performance Testing (Speed)

**What it tests:** Ensures parsing time is acceptable for production use.

**Thresholds:**
- Simple circuits: < 5ms
- Complex circuits: < 10ms

**Test coverage:**
- `test_bell_state_parse_time()` - Basic 2-qubit circuit
- `test_ghz_state_parse_time()` - 3-qubit entangled state
- `test_parameterized_circuit_parse_time()` - QAOA with parameters
- `test_qft_parse_time()` - QFT with complex gates
- `test_large_circuit_parse_time()` - 10-qubit circuit with 30+ gates
- `test_optimized_vs_original_syntax_performance()` - Syntax comparison
- `test_parameter_evaluation_performance()` - Complex expressions

**Method:** Average over 100 iterations using `time.perf_counter()`

**Result:** All tests pass - QuYAML parses in 1-2ms on average ✓

---

## Recommendations

### When to Use Each Format

#### Use QuYAML When:
1. ✅ **Simple, non-parameterized circuits** (15.8% better than OpenQASM)
2. ✅ **Human readability matters** (symbolic parameters, clean syntax)
3. ✅ **Replacing JSON** (73% token reduction)
4. ✅ **Cost difference negligible** ($1-2 per 100K calls)
5. ✅ **Parsing time acceptable** (<2ms is imperceptible)

#### Use OpenQASM 3.0 When:
1. ⚠️ **Heavily parameterized circuits** (25% more efficient with pre-evaluated values)
2. ⚠️ **Parsing speed critical** (219x faster than QuYAML)
3. ⚠️ **Maximum token efficiency** (0.5% better on average)
4. ⚠️ **Legacy integration** (standard format, wide tool support)

#### Use OpenQASM 2.0 When:
1. ⚠️ **Legacy compatibility required** (older Qiskit versions)
2. ⚠️ **Parameterized circuits** (24% more efficient than QuYAML)
3. ❌ **Not recommended otherwise** (OpenQASM 3.0 is better)

#### Never Use JSON:
1. ❌ **For LLM input** (73% worse than QuYAML, 73% worse than OpenQASM)
2. ✓ **Only for structured data storage** (machine-readable, not LLM-friendly)

---

## Conclusion

### QuYAML's Position in the Ecosystem

**Token Efficiency:**
- 🥇 **#1 vs JSON** (+73% reduction)
- 🥈 **#2 vs OpenQASM 2.0** (+1.0% better)
- 🥉 **#3 vs OpenQASM 3.0** (-0.5% worse)

**Parsing Speed:**
- 🥉 **#4 out of 4** (219x slower than OpenQASM 3.0)
- ✅ **Acceptable** (< 2ms average, < 5ms threshold)

**Overall Verdict:**

QuYAML achieves its **design goal**: provide a **human-readable, token-efficient** format for quantum circuits that:
1. ✅ Matches or beats OpenQASM on token efficiency (depending on circuit type)
2. ✅ Crushes JSON on token efficiency (73% reduction)
3. ✅ Maintains symbolic parameters for readability
4. ✅ Parses fast enough for production use (<2ms)
5. ✅ Proven correct via metamorphic testing

**The 0.5% token gap vs OpenQASM 3.0 is acceptable** given:
- Only $1 per 100K API calls
- 15.8% better on simple circuits
- Superior readability with symbolic parameters
- Trade-off is architectural (symbols vs pre-evaluated values)

**Status: Production-ready for LLM-driven quantum development** 🚀

---

## Test Suite Summary

| Test Suite | Tests | Purpose | Status |
|------------|-------|---------|--------|
| `test_valid_circuits.py` | 2 | Basic parsing + metamorphic testing | ✓ 2/2 pass |
| `test_advanced_circuits.py` | 2 | QML and optimization circuits | ✓ 2/2 pass |
| `test_advanced_algorithms.py` | 5 | QFT, QAOA, VQE, teleportation | ✓ 5/5 pass |
| `test_invalid_syntax.py` | 4 | Error handling | ✓ 4/4 pass |
| `test_property_based.py` | 1 | Generative testing | ✓ 1/1 pass |
| `test_performance.py` | 7 | Parsing time thresholds | ✓ 7/7 pass |
| **TOTAL** | **21** | **Complete coverage** | **✓ 21/21 pass** |

---

**Generated:** 2024-10-22  
**Benchmark:** `benchmarks/benchmark_complete.py`  
**Test Suite:** 21 tests, 100% passing
