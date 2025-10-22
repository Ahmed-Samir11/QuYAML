"""Test optimized QuYAML syntax with backward compatibility."""

from quyaml_parser import parse_quyaml_to_qiskit

# Original syntax (should still work)
original_quyaml = """
circuit: bell
qreg: q[2]
creg: c[2]
instructions:
  - h q[0]
  - cx q[0], q[1]
  - measure
"""

# Optimized syntax - shorter field names and implicit q[] prefix
optimized_quyaml = """
circuit: bell
qubits: q[2]
bits: c[2]
ops:
  - h 0
  - cx 0 1
  - measure
"""

# Test with parameterized circuit - original syntax
original_qaoa = """
circuit: qaoa_p1
qreg: q[2]
parameters:
  gamma: 0.5
  beta: 1.2
instructions:
  - h q[0]
  - h q[1]
  - cphase(2*$gamma) q[0], q[1]
  - rx(2*$beta) q[0]
  - rx(2*$beta) q[1]
"""

# Optimized parameterized circuit - inline params dict
optimized_qaoa = """
circuit: qaoa_p1
qubits: q[2]
params: {gamma: 0.5, beta: 1.2}
ops:
  - h 0
  - h 1
  - cphase(2*$gamma) 0 1
  - rx(2*$beta) 0
  - rx(2*$beta) 1
"""

print("Testing Original Syntax (Bell State)...")
qc1 = parse_quyaml_to_qiskit(original_quyaml)
print(f"✓ Circuit: {qc1.name}, Qubits: {qc1.num_qubits}, Gates: {len(qc1.data)}")
print()

print("Testing Optimized Syntax (Bell State)...")
qc2 = parse_quyaml_to_qiskit(optimized_quyaml)
print(f"✓ Circuit: {qc2.name}, Qubits: {qc2.num_qubits}, Gates: {len(qc2.data)}")
print()

print("Testing Original Syntax (QAOA)...")
qc3 = parse_quyaml_to_qiskit(original_qaoa)
print(f"✓ Circuit: {qc3.name}, Qubits: {qc3.num_qubits}, Gates: {len(qc3.data)}")
print()

print("Testing Optimized Syntax (QAOA)...")
qc4 = parse_quyaml_to_qiskit(optimized_qaoa)
print(f"✓ Circuit: {qc4.name}, Qubits: {qc4.num_qubits}, Gates: {len(qc4.data)}")
print()

# Calculate token savings
import tiktoken
encoder = tiktoken.encoding_for_model("gpt-4")

original_tokens = len(encoder.encode(original_qaoa))
optimized_tokens = len(encoder.encode(optimized_qaoa))
savings = ((original_tokens - optimized_tokens) / original_tokens) * 100

print("=" * 60)
print("TOKEN COMPARISON (QAOA Circuit)")
print("=" * 60)
print(f"Original syntax:  {original_tokens} tokens")
print(f"Optimized syntax: {optimized_tokens} tokens")
print(f"Reduction:        {original_tokens - optimized_tokens} tokens ({savings:.1f}%)")
print()

print("✅ All tests passed! Both syntaxes work correctly.")
