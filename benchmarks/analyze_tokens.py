"""Analyze where tokens are being spent in parameterized circuits."""

import tiktoken

encoder = tiktoken.encoding_for_model("gpt-4")

# QAOA circuit - where we lose the most
quyaml_qaoa = """circuit: qaoa_p1
qubits: q[2]
params: {gamma: 0.5, beta: 1.2}
ops:
  - h 0
  - h 1
  - cphase(2*$gamma) 0 1
  - rx(2*$beta) 0
  - rx(2*$beta) 1"""

openqasm_qaoa = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
h q[1];
cp(1.0) q[0],q[1];
rx(2.4) q[0];
rx(2.4) q[1];"""

print("Token-by-token analysis:")
print("=" * 60)
print()

# Break down QuYAML
quyaml_lines = quyaml_qaoa.strip().split('\n')
total_quyaml = 0
for line in quyaml_lines:
    tokens = len(encoder.encode(line))
    total_quyaml += tokens
    print(f"QuYAML: {tokens:2d} tokens | {line}")

print()
print(f"Total QuYAML: {total_quyaml} tokens")
print()

# Break down OpenQASM
openqasm_lines = openqasm_qaoa.strip().split('\n')
total_openqasm = 0
for line in openqasm_lines:
    tokens = len(encoder.encode(line))
    total_openqasm += tokens
    print(f"OpenQASM: {tokens:2d} tokens | {line}")

print()
print(f"Total OpenQASM: {total_openqasm} tokens")
print()

print("=" * 60)
print("KEY FINDINGS:")
print("=" * 60)

# Test without metadata
quyaml_minimal = """qubits: q[2]
params: {gamma: 0.5, beta: 1.2}
ops:
  - h 0
  - h 1
  - cphase(2*$gamma) 0 1
  - rx(2*$beta) 0
  - rx(2*$beta) 1"""

openqasm_minimal = """qreg q[2];
h q[0];
h q[1];
cp(1.0) q[0],q[1];
rx(2.4) q[0];
rx(2.4) q[1];"""

quyaml_min_tokens = len(encoder.encode(quyaml_minimal))
openqasm_min_tokens = len(encoder.encode(openqasm_minimal))

print(f"Without 'circuit:' line:")
print(f"  QuYAML:   {quyaml_min_tokens} tokens")
print(f"  OpenQASM: {openqasm_min_tokens} tokens")
print()

# Test even more compact
quyaml_ultra = """q: q[2]
p: {g: 0.5, b: 1.2}
o:
  - h 0
  - h 1
  - cphase(2*$g) 0 1
  - rx(2*$b) 0
  - rx(2*$b) 1"""

ultra_tokens = len(encoder.encode(quyaml_ultra))
print(f"Ultra-compact (single-letter keys):")
print(f"  QuYAML:   {ultra_tokens} tokens")
print()

# The issue: params line
params_original = "params: {gamma: 0.5, beta: 1.2}"
params_tokens = len(encoder.encode(params_original))
print(f"'params:' line alone: {params_tokens} tokens")
print()

# Compare to OpenQASM's boilerplate
openqasm_boilerplate = """OPENQASM 2.0;
include "qelib1.inc";"""
boilerplate_tokens = len(encoder.encode(openqasm_boilerplate))
print(f"OpenQASM boilerplate: {boilerplate_tokens} tokens")
print()

print("=" * 60)
print("CONCLUSION:")
print("=" * 60)
print("QuYAML's parameter block adds ~14 tokens per circuit.")
print("OpenQASM's boilerplate adds ~11 tokens but is one-time overhead.")
print("For parameterized circuits, OpenQASM wins by pre-evaluating expressions.")
print("For non-parameterized circuits, QuYAML wins by avoiding boilerplate.")
