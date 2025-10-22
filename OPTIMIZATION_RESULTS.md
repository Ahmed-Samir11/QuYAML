# QuYAML Optimization Results

## Executive Summary

After implementing optimized QuYAML syntax (shorter field names, implicit qubit prefix, inline params), we achieved:

- **73.0% reduction vs JSON** (325.0 → 87.9 tokens)
- **3.5% behind OpenQASM** (84.9 vs 87.9 tokens)
- **Original QuYAML was 6.7% behind OpenQASM** (improved by 3.2 percentage points)

## Optimization Changes Implemented

### 1. Field Name Aliases
- `qreg` → `qubits` (saved 2 tokens per circuit)
- `creg` → `bits` (saved 2 tokens per circuit)
- `parameters` → `params` (saved 3 tokens per circuit)
- `instructions` → `ops` (saved 5 tokens per circuit)

### 2. Implicit Qubit Prefix
- Original: `h q[0]` → Optimized: `h 0`
- Saves 2-3 tokens per instruction
- Average circuit has 7+ instructions = 14-21 tokens saved

### 3. Inline Parameter Dictionary
- Original (multi-line):
  ```yaml
  parameters:
    gamma: 0.5
    beta: 1.2
  ```
- Optimized (single-line):
  ```yaml
  params: {gamma: 0.5, beta: 1.2}
  ```
- Saves 2-4 tokens per parameterized circuit

## Performance by Circuit Type

### Simple Circuits (Non-Parameterized)
QuYAML **WINS** against OpenQASM:

| Circuit | OpenQASM | QuYAML | Improvement |
|---------|----------|--------|-------------|
| Bell State | 46 | 37 | +19.6% ✓ |
| GHZ (3q) | 55 | 46 | +16.4% ✓ |
| Teleportation | 60 | 51 | +15.0% ✓ |
| QFT (3q) | 90 | 79 | +12.2% ✓ |

**Average: +15.8% better than OpenQASM**

### Parameterized Circuits
QuYAML **LOSES** to OpenQASM:

| Circuit | OpenQASM | QuYAML | Difference |
|---------|----------|--------|------------|
| QAOA (p=1) | 65 | 82 | -26.2% ✗ |
| VQE Ansatz | 78 | 95 | -21.8% ✗ |
| QAOA Max-Cut | 123 | 141 | -14.6% ✗ |
| Grover | 162 | 172 | -6.2% ✗ |

**Average: -17.2% worse than OpenQASM**

## Why Parameterized Circuits Lose

### Token Overhead Analysis

**QuYAML QAOA (p=1):**
```yaml
circuit: qaoa_p1          # 8 tokens
qubits: q[2]              # 7 tokens
params: {gamma: 0.5, ...} # 17 tokens (THE PROBLEM)
ops:                      # 2 tokens
  - h 0                   # 5 tokens
  - cphase(2*$gamma) 0 1  # 13 tokens (expression overhead)
```
**Total: 82 tokens**

**OpenQASM QAOA (p=1):**
```qasm
OPENQASM 2.0;             # 8 tokens
include "qelib1.inc";     # 7 tokens
qreg q[2];                # 6 tokens
h q[0];                   # 5 tokens
cp(1.0) q[0],q[1];        # 14 tokens (PRE-EVALUATED)
```
**Total: 65 tokens**

### The Trade-off

1. **QuYAML keeps parameters symbolic** (`$gamma`, `2*$beta`)
   - Better for readability and reusability
   - Worse for token efficiency (+~20 tokens per parameterized circuit)

2. **OpenQASM uses hardcoded values** (`cp(1.0)`, `rx(2.4)`)
   - Better for token efficiency
   - Worse for readability and reusability

3. **OpenQASM boilerplate is one-time cost**
   - 15 tokens for `OPENQASM 2.0; include "qelib1.inc";`
   - Amortized across all gates in the circuit

4. **QuYAML metadata grows with parameters**
   - Simple circuit: `qubits: q[2]` (7 tokens)
   - With params: `qubits: q[2] params: {gamma: 0.5, beta: 1.2}` (24 tokens)
   - Overhead grows linearly with parameter count

## Cost Impact (GPT-4 API)

At $0.03 per 1K input tokens:

- **Per circuit call:**
  - OpenQASM: $0.002546
  - QuYAML: $0.002636 (+$0.000090)
  - JSON: $0.009750

- **Per 100K API calls:**
  - QuYAML vs OpenQASM: -$9 (lose $9)
  - QuYAML vs JSON: +$711 (save $711)

## Recommendations

### Use QuYAML When:
1. **Simple, non-parameterized circuits** (15.8% better than OpenQASM)
2. **Human readability matters** (symbolic parameters, clean syntax)
3. **Compared to JSON** (73% reduction)
4. **Cost difference is negligible** ($9 per 100K calls = 0.009¢ per call)

### Use OpenQASM When:
1. **Heavily parameterized circuits** (17.2% better than QuYAML)
2. **Token efficiency is critical**
3. **Parameters can be pre-evaluated**
4. **High-volume production workloads** (millions of API calls)

### Use JSON When:
1. **Never for LLM input** (73-81% worse than QuYAML)
2. **Only for structured data storage**

## Future Optimization Ideas

If we wanted to beat OpenQASM on parameterized circuits, we could:

1. **Add pre-evaluated mode**: 
   ```yaml
   params: {gamma: 0.5, beta: 1.2}  # 17 tokens
   # vs
   # (no params line, use hardcoded values)  # 0 tokens
   ops:
     - cphase(1.0) 0 1  # 11 tokens vs cphase(2*$gamma) 0 1  # 13 tokens
   ```
   - Would save ~20 tokens per parameterized circuit
   - Loses symbolic parameters (defeats QuYAML's purpose)

2. **Ultra-compact mode**:
   ```yaml
   q: q[2]  # instead of qubits: q[2]
   p: {g: 0.5, b: 1.2}  # instead of params: {gamma: 0.5, beta: 1.2}
   o: [h 0, h 1, ...]  # inline array instead of list
   ```
   - Would save ~5-10 tokens
   - Hurts readability significantly

3. **Hybrid approach**: Detect when params are used, omit block if unused
   - Already implemented (optional params block)
   - Still loses to OpenQASM on parameterized circuits

## Conclusion

**We successfully optimized QuYAML from 6.7% worse to 3.5% worse overall.**

The 3.5% gap is architectural:
- QuYAML prioritizes **symbolic parameters and readability**
- OpenQASM prioritizes **pre-evaluated values and token efficiency**

Both are valid design choices. QuYAML is not strictly worse—it wins on simple circuits and readability, loses on parameterized circuits.

**Verdict: Ship it.** The 3.5% gap (avg 3 tokens per circuit, $0.000090 per call) is acceptable given QuYAML's readability advantages and 73% improvement over JSON.
