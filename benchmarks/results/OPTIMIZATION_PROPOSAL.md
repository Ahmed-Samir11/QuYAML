# QuYAML Optimization Proposal

## Analysis: Why OpenQASM Wins

Looking at where QuYAML loses (parameterized circuits):

### Current QuYAML (109 tokens for QAOA):
```yaml
circuit: QAOA
qreg: q[2]
parameters:
  gamma: 0.5
  beta: 1.2
instructions:
  - h q[0]
  - h q[1]
  - cx q[0], q[1]
  - ry(2 * $gamma) q[1]
  - cx q[0], q[1]
  - rx(2 * $beta) q[0]
  - rx(2 * $beta) q[1]
```

### OpenQASM (79 tokens):
```
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
h q[1];
cx q[0],q[1];
ry(1.0) q[1];
cx q[0],q[1];
rx(2.4) q[0];
rx(2.4) q[1];
```

## Token Waste Analysis

1. **"parameters:" keyword** = 2 tokens (but necessary for flexibility)
2. **Parameter declarations** = ~8 tokens (gamma: 0.5, beta: 1.2)
3. **"instructions:" keyword** = 2 tokens
4. **List dashes "- "** = 1 token each × 7 = 7 tokens
5. **Parameter expressions** = "$gamma" vs "0.5" (similar)

**Total overhead: ~19 tokens just for structure**

## Optimization Strategy

### Keep What's Good:
✅ YAML structure (readable)
✅ Parameter block (flexible)
✅ Semantic grouping
✅ No semicolons

### Optimize:
1. **Make keywords optional when clear from context**
2. **Shorten register syntax**
3. **Remove unnecessary list markers for single-line instructions**
4. **Inline simple parameters**

## Proposed Optimizations

### Optimization 1: Optional Keywords
```yaml
# Before (current):
circuit: QAOA
qreg: q[2]
parameters:
  gamma: 0.5
  beta: 1.2
instructions:
  - h q[0]

# After (optimized):
QAOA                    # circuit name on first line (implicit)
q[2]                    # qreg implicit
params: {gamma: 0.5, beta: 1.2}   # inline params
h q[0]                  # no dash, no "instructions:" needed
```

❌ **REJECTED**: Too cryptic, loses YAML structure benefits

### Optimization 2: Shorter Keywords
```yaml
# Before:
circuit: QAOA
qreg: q[2]
parameters:
  gamma: 0.5
instructions:
  - h q[0]

# After:
c: QAOA                 # circuit
q: q[2]                # qubits
p:                     # params
  gamma: 0.5
i:                     # instructions
  - h q[0]
```

❌ **REJECTED**: Loses readability, confusing single-letter keys

### Optimization 3: Smart Defaults (RECOMMENDED)
```yaml
# Before (43 tokens for Bell State):
circuit: BellState
qreg: q[2]
creg: c[2]
instructions:
  - h q[0]
  - cx q[0], q[1]
  - measure

# After (estimated 35 tokens):
circuit: BellState
qubits: 2              # Shorter, implies q[0] and q[1]
bits: 2                # Shorter than creg: c[2]
ops:                   # Shorter than instructions
  - h 0                # Implicit q[] prefix
  - cx 0 1             # No commas needed
  - measure            # Implicit "all qubits"
```

Token savings: ~8 tokens (18% reduction for simple circuits)

### Optimization 4: Hybrid Approach (BEST)
```yaml
# For simple circuits (no parameters):
circuit: BellState
qubits: 2
bits: 2
ops:
  - h 0
  - cx 0 1
  - measure

# For parameterized circuits:
circuit: QAOA
qubits: 2
params: {gamma: 0.5, beta: 1.2}  # Inline for brevity
ops:
  - h 0
  - h 1
  - cx 0 1
  - ry(2*$gamma) 1     # No spaces in expressions
  - cx 0 1
  - rx(2*$beta) 0
  - rx(2*$beta) 1
```

Estimated savings:
- Bell State: 43 → ~32 tokens (-25%)
- QAOA: 109 → ~85 tokens (-22%)
- New average: ~115 tokens vs 134 OpenQASM (**14% better!**)

## Proposed Changes to QuYAML v0.2

### Backward Compatible Optimizations:

1. **Support shorter field names** (aliases):
   - `qubits` or `qreg` (both work)
   - `bits` or `creg` (both work)
   - `ops` or `instructions` (both work)
   - `params` or `parameters` (both work)

2. **Implicit qubit prefix**:
   - `h 0` means `h q[0]`
   - `cx 0 1` means `cx q[0], q[1]`
   - Original syntax still works

3. **Inline parameters**:
   - `params: {gamma: 0.5, beta: 1.2}` (one line)
   - Original multi-line format still works

4. **Space tolerance**:
   - `ry(2*$gamma)` same as `ry(2 * $gamma)`
   - Fewer spaces = fewer tokens

5. **Implicit measure**:
   - `measure` means measure all to all (if possible)
   - Explicit `measure 0 0` still works

### Implementation Priority:

**Phase 1** (immediate):
- Support `qubits/bits/ops/params` aliases
- Implicit `q[]` prefix parsing
- Inline params dict parsing

**Phase 2** (next):
- Whitespace compression in expressions
- Smart defaults for measure

**Phase 3** (future):
- Auto-detect circuit name from context
- Range syntax: `h [0-2]` for `h 0; h 1; h 2`

## Expected Results

After optimizations:

| Circuit | Current | Optimized | OpenQASM | Winner |
|---------|---------|-----------|----------|--------|
| Bell | 43 | 32 | 77 | **QuYAML** ✅ |
| GHZ | 54 | 40 | 100 | **QuYAML** ✅ |
| QAOA | 109 | 85 | 79 | OpenQASM (but close!) |
| QFT | 95 | 75 | 84 | **QuYAML** ✅ |
| VQE | 99 | 78 | 69 | OpenQASM (but close!) |
| **Average** | 143.1 | **~110** | 134.1 | **QuYAML** ✅ |

**Estimated 18% improvement** → QuYAML beats OpenQASM by ~18%!

## Maintains Readability

✅ Still valid YAML
✅ Clear field names (even if shorter)
✅ Structured format
✅ Parameter flexibility
✅ More concise without being cryptic

```yaml
# Optimized QuYAML - Clear AND Compact
circuit: QAOA_MaxCut
qubits: 4
params: {gamma: 0.785, beta: 1.57}
ops:
  - h 0
  - h 1
  - h 2
  - h 3
  - cx 0 1
  - ry(2*$gamma) 1
  - cx 0 1
```

vs OpenQASM:
```
OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
h q[0];
h q[1];
h q[2];
h q[3];
cx q[0],q[1];
ry(1.57) q[1];
cx q[0],q[1];
```

Still clearly more readable with better parameter handling!
