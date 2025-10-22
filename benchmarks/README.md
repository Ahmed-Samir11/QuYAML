# QuYAML Benchmarks

This directory contains all benchmark scripts and results for comparing QuYAML against OpenQASM and JSON.

## Main Benchmarks

### 🎯 `benchmark_optimized.py` (RECOMMENDED)
The primary benchmark using **optimized QuYAML syntax** with exact GPT-4 tokenization (tiktoken).

**Features:**
- 8 diverse quantum circuits (Bell, GHZ, QAOA, QFT, VQE, Max-Cut, Grover, Teleportation)
- Exact GPT-4 token counting using `tiktoken`
- Compares: Optimized QuYAML vs OpenQASM vs JSON
- Includes cost analysis ($0.03/1K tokens)

**Results Summary:**
- QuYAML: 87.9 tokens (average)
- OpenQASM: 84.9 tokens (-3.5%)
- JSON: 325.0 tokens (+73.0% reduction)

**Run:**
```bash
python benchmarks/benchmark_optimized.py
```

### 📊 `benchmark_with_tiktoken.py`
Original benchmark using **non-optimized QuYAML syntax** (baseline comparison).

**Results Summary:**
- QuYAML (original): 143.1 tokens (average)
- OpenQASM: 134.1 tokens (-6.7%)
- JSON: 293.6 tokens (+51.3% reduction)

**Shows:** Optimization improved QuYAML from 6.7% worse to 3.5% worse vs OpenQASM.

**Run:**
```bash
python benchmarks/benchmark_with_tiktoken.py
```

## Supporting Files

### `test_optimized_syntax.py`
Tests backward compatibility of optimized syntax. Verifies both old and new formats work correctly.

**Tests:**
- Original syntax: `qreg`, `creg`, `parameters`, `instructions`, `q[0]`
- Optimized syntax: `qubits`, `bits`, `params`, `ops`, `0`

### `analyze_tokens.py`
Detailed token-by-token analysis of QAOA circuit to understand where tokens are spent.

**Key Findings:**
- OpenQASM boilerplate: 15 tokens (one-time overhead)
- QuYAML params block: 17 tokens (per parameterized circuit)
- Parameterized circuits favor OpenQASM (pre-evaluated values)
- Simple circuits favor QuYAML (no boilerplate)

## Archived Benchmarks

### `archived_comprehensive.py`
Multi-method token counting (chars/4, word-based, GPT-style, information density).

**Status:** Archived - superseded by tiktoken-based benchmarks.

**Why Archived:** chars/4 method proven inaccurate (40-58% underestimation).

### `archived_vs_standards.py`
Original comparison using chars/4 estimation.

**Status:** Archived - inaccurate token counting.

**Historical Value:** Shows 61.2% improvement vs JSON (overestimated due to chars/4 error).

## Results Directory

All benchmark outputs saved to `results/`:
- `benchmark_tiktoken_results.txt` - Original syntax results
- `benchmark_comprehensive_results.txt` - Multi-method results (archived)
- `benchmark_results.txt` - chars/4 results (archived)

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install tiktoken qiskit pyyaml
   ```

2. **Run main benchmark:**
   ```bash
   python benchmarks/benchmark_optimized.py
   ```

3. **Test syntax compatibility:**
   ```bash
   python benchmarks/test_optimized_syntax.py
   ```

## Token Counting Methods Comparison

| Method | Accuracy | Use Case |
|--------|----------|----------|
| **tiktoken** | ✅ Exact | Production (GPT-4 tokenizer) |
| GPT-style | ⚠️ Approximate | Quick estimation |
| chars/4 | ❌ Inaccurate | **Not recommended** |
| Word-based | ❌ Inaccurate | **Not recommended** |

## Performance Summary

### Simple Circuits (Non-Parameterized)
QuYAML **beats** OpenQASM by **+15.8%** on average:
- Bell State: +19.6%
- GHZ (3q): +16.4%
- Teleportation: +15.0%
- QFT (3q): +12.2%

### Parameterized Circuits
QuYAML **loses** to OpenQASM by **-17.2%** on average:
- QAOA (p=1): -26.2%
- VQE Ansatz: -21.8%
- QAOA Max-Cut: -14.6%
- Grover: -6.2%

### Overall Average
- QuYAML: 87.9 tokens
- OpenQASM: 84.9 tokens (**-3.5%**)
- JSON: 325.0 tokens (**+73.0%** reduction)

## Cost Analysis

At GPT-4 pricing ($0.03/1K input tokens):

**Per circuit call:**
- OpenQASM: $0.002546
- QuYAML: $0.002636 (+$0.000090)
- JSON: $0.009750

**Per 100K API calls:**
- QuYAML vs OpenQASM: -$9 (lose $9)
- QuYAML vs JSON: +$711 (save $711)

## Recommendations

- **Use QuYAML:** Simple circuits, readability matters, compared to JSON
- **Use OpenQASM:** Heavily parameterized circuits, token efficiency critical
- **Never use JSON:** For LLM input (73% worse than QuYAML)

See `../OPTIMIZATION_RESULTS.md` for detailed analysis.
