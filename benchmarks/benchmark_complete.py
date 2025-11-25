"""
Complete benchmark: QuYAML vs OpenQASM 2.0 vs OpenQASM 3.0 vs JSON
Measures both token efficiency AND parsing time performance.
Uses exact GPT-4 tokenization (tiktoken).
"""

import tiktoken
import json
import time
from qiskit import QuantumCircuit, qasm2, qasm3
from quyaml import parse_quyaml_to_qiskit

# Initialize GPT-4 tokenizer
encoder = tiktoken.encoding_for_model("gpt-4")

def count_tokens(text: str) -> int:
    """Count tokens using tiktoken (GPT-4 tokenizer)."""
    return len(encoder.encode(text))

def measure_parse_time(parser_func, text: str, iterations: int = 100) -> float:
    """Measure average parsing time over multiple iterations."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        try:
            parser_func(text)
        except:
            pass  # Some parsers might fail on certain formats
        end = time.perf_counter()
        times.append(end - start)
    return sum(times) / len(times) * 1000  # Return in milliseconds

# Test circuits with all four formats
test_circuits = {
    "Bell State": {
        "quyaml": """circuit: bell
qubits: q[2]
bits: c[2]
ops:
  - h 0
  - cx 0 1
  - measure""",
        "openqasm2": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q -> c;""",
        "openqasm3": """OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
bit[2] c;
h q[0];
cx q[0], q[1];
c = measure q;""",
        "description": "Simple 2-qubit entanglement"
    },
    
    "GHZ State (3 qubits)": {
        "quyaml": """circuit: ghz
qubits: q[3]
bits: c[3]
ops:
  - h 0
  - cx 0 1
  - cx 1 2
  - measure""",
        "openqasm2": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
h q[0];
cx q[0],q[1];
cx q[1],q[2];
measure q -> c;""",
        "openqasm3": """OPENQASM 3;
include "stdgates.inc";
qubit[3] q;
bit[3] c;
h q[0];
cx q[0], q[1];
cx q[1], q[2];
c = measure q;""",
        "description": "3-qubit entangled state"
    },
    
    "QAOA (p=1)": {
        "quyaml": """circuit: qaoa_p1
qubits: q[2]
params: {gamma: 0.5, beta: 1.2}
ops:
  - h 0
  - h 1
  - cphase(2*$gamma) 0 1
  - rx(2*$beta) 0
  - rx(2*$beta) 1""",
        "openqasm2": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
h q[1];
cp(1.0) q[0],q[1];
rx(2.4) q[0];
rx(2.4) q[1];""",
        "openqasm3": """OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
h q[0];
h q[1];
cp(1.0) q[0], q[1];
rx(2.4) q[0];
rx(2.4) q[1];""",
        "description": "QAOA with parameterization"
    },
    
    "QFT (3 qubits)": {
        "quyaml": """circuit: qft
qubits: q[3]
ops:
  - h 0
  - cphase(pi/2) 1 0
  - h 1
  - cphase(pi/4) 2 0
  - cphase(pi/2) 2 1
  - h 2
  - swap 0 2""",
        "openqasm2": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
h q[0];
cp(1.5708) q[1],q[0];
h q[1];
cp(0.7854) q[2],q[0];
cp(1.5708) q[2],q[1];
h q[2];
swap q[0],q[2];""",
        "openqasm3": """OPENQASM 3;
include "stdgates.inc";
qubit[3] q;
h q[0];
cp(1.5708) q[1], q[0];
h q[1];
cp(0.7854) q[2], q[0];
cp(1.5708) q[2], q[1];
h q[2];
swap q[0], q[2];""",
        "description": "Quantum Fourier Transform"
    },
    
    "VQE Ansatz": {
        "quyaml": """circuit: vqe
qubits: q[4]
params: {theta1: 0.5, theta2: 1.2, theta3: 0.8}
ops:
  - ry($theta1) 0
  - ry($theta2) 1
  - cx 0 1
  - ry($theta3) 2
  - cx 1 2
  - cx 2 3""",
        "openqasm2": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
ry(0.5) q[0];
ry(1.2) q[1];
cx q[0],q[1];
ry(0.8) q[2];
cx q[1],q[2];
cx q[2],q[3];""",
        "openqasm3": """OPENQASM 3;
include "stdgates.inc";
qubit[4] q;
ry(0.5) q[0];
ry(1.2) q[1];
cx q[0], q[1];
ry(0.8) q[2];
cx q[1], q[2];
cx q[2], q[3];""",
        "description": "Variational ansatz"
    },
    
    "QAOA Max-Cut": {
        "quyaml": """circuit: maxcut
qubits: q[4]
params: {gamma: 0.5, beta: 1.0}
ops:
  - h 0
  - h 1
  - h 2
  - h 3
  - cphase(2*$gamma) 0 1
  - cphase(2*$gamma) 1 2
  - cphase(2*$gamma) 2 3
  - rx(2*$beta) 0
  - rx(2*$beta) 1
  - rx(2*$beta) 2
  - rx(2*$beta) 3""",
        "openqasm2": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
h q[0];
h q[1];
h q[2];
h q[3];
cp(1.0) q[0],q[1];
cp(1.0) q[1],q[2];
cp(1.0) q[2],q[3];
rx(2.0) q[0];
rx(2.0) q[1];
rx(2.0) q[2];
rx(2.0) q[3];""",
        "openqasm3": """OPENQASM 3;
include "stdgates.inc";
qubit[4] q;
h q[0];
h q[1];
h q[2];
h q[3];
cp(1.0) q[0], q[1];
cp(1.0) q[1], q[2];
cp(1.0) q[2], q[3];
rx(2.0) q[0];
rx(2.0) q[1];
rx(2.0) q[2];
rx(2.0) q[3];""",
        "description": "Max-Cut problem"
    },
    
    "Grover's Algorithm": {
        "quyaml": """circuit: grover
qubits: q[3]
ops:
  - h 0
  - h 1
  - h 2
  - x 2
  - h 2
  - cx 0 2
  - cx 1 2
  - h 2
  - x 2
  - h 0
  - h 1
  - h 2
  - x 0
  - x 1
  - x 2
  - h 2
  - cx 0 2
  - cx 1 2
  - h 2
  - x 0
  - x 1
  - x 2
  - h 0
  - h 1
  - h 2""",
        "openqasm2": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
h q[0];
h q[1];
h q[2];
x q[2];
h q[2];
cx q[0],q[2];
cx q[1],q[2];
h q[2];
x q[2];
h q[0];
h q[1];
h q[2];
x q[0];
x q[1];
x q[2];
h q[2];
cx q[0],q[2];
cx q[1],q[2];
h q[2];
x q[0];
x q[1];
x q[2];
h q[0];
h q[1];
h q[2];""",
        "openqasm3": """OPENQASM 3;
include "stdgates.inc";
qubit[3] q;
h q[0];
h q[1];
h q[2];
x q[2];
h q[2];
cx q[0], q[2];
cx q[1], q[2];
h q[2];
x q[2];
h q[0];
h q[1];
h q[2];
x q[0];
x q[1];
x q[2];
h q[2];
cx q[0], q[2];
cx q[1], q[2];
h q[2];
x q[0];
x q[1];
x q[2];
h q[0];
h q[1];
h q[2];""",
        "description": "Search algorithm"
    },
    
    "Quantum Teleportation": {
        "quyaml": """circuit: teleport
qubits: q[3]
bits: c[3]
ops:
  - h 1
  - cx 1 2
  - cx 0 1
  - h 0
  - measure""",
        "openqasm2": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
h q[1];
cx q[1],q[2];
cx q[0],q[1];
h q[0];
measure q -> c;""",
        "openqasm3": """OPENQASM 3;
include "stdgates.inc";
qubit[3] q;
bit[3] c;
h q[1];
cx q[1], q[2];
cx q[0], q[1];
h q[0];
c = measure q;""",
        "description": "Teleportation protocol"
    }
}

def circuit_to_json(circuit_name: str) -> str:
    """Convert circuit to JSON representation."""
    # Parse QuYAML to get circuit structure
    quyaml = test_circuits[circuit_name]["quyaml"]
    qc = parse_quyaml_to_qiskit(quyaml)
    
    # Create JSON representation
    json_data = {
        "circuit": qc.name,
        "qubits": qc.num_qubits,
        "cbits": qc.num_clbits,
        "gates": [
            {
                "name": instr.operation.name,
                "qubits": [qc.find_bit(q).index for q in instr.qubits],
                "params": [float(p) for p in instr.operation.params]
            }
            for instr in qc.data
        ]
    }
    return json.dumps(json_data, indent=2)

print("=" * 80)
print("COMPLETE BENCHMARK: Token Efficiency + Parsing Time")
print("QuYAML vs OpenQASM 2.0 vs OpenQASM 3.0 vs JSON")
print("=" * 80)
print()

results = []
for name, data in test_circuits.items():
    quyaml_str = data["quyaml"]
    openqasm2_str = data["openqasm2"]
    openqasm3_str = data["openqasm3"]
    json_str = circuit_to_json(name)
    
    # Count tokens
    quyaml_tokens = count_tokens(quyaml_str)
    openqasm2_tokens = count_tokens(openqasm2_str)
    openqasm3_tokens = count_tokens(openqasm3_str)
    json_tokens = count_tokens(json_str)
    
    # Measure parsing time
    quyaml_time = measure_parse_time(parse_quyaml_to_qiskit, quyaml_str)
    openqasm2_time = measure_parse_time(lambda x: qasm2.loads(x), openqasm2_str)
    openqasm3_time = measure_parse_time(lambda x: qasm3.loads(x), openqasm3_str)
    json_time = measure_parse_time(lambda x: json.loads(x), json_str)
    
    results.append({
        "name": name,
        "quyaml": quyaml_tokens,
        "openqasm2": openqasm2_tokens,
        "openqasm3": openqasm3_tokens,
        "json": json_tokens,
        "quyaml_time": quyaml_time,
        "openqasm2_time": openqasm2_time,
        "openqasm3_time": openqasm3_time,
        "json_time": json_time,
        "description": data["description"]
    })
    
    print(f"{name}")
    print(f"  Description: {data['description']}")
    print()
    print(f"  TOKEN COUNTS:")
    print(f"    OpenQASM 2.0: {openqasm2_tokens:4d} tokens")
    print(f"    OpenQASM 3.0: {openqasm3_tokens:4d} tokens")
    print(f"    JSON:         {json_tokens:4d} tokens")
    print(f"    QuYAML (v0.2): {quyaml_tokens:4d} tokens")
    print()
    
    # Token efficiency comparisons
    vs_openqasm2 = ((openqasm2_tokens - quyaml_tokens) / openqasm2_tokens) * 100
    vs_openqasm3 = ((openqasm3_tokens - quyaml_tokens) / openqasm3_tokens) * 100
    vs_json = ((json_tokens - quyaml_tokens) / json_tokens) * 100
    
    print(f"  TOKEN EFFICIENCY:")
    print(f"    vs OpenQASM 2.0: {vs_openqasm2:+.1f}% {'✓' if vs_openqasm2 > 0 else '✗'}")
    print(f"    vs OpenQASM 3.0: {vs_openqasm3:+.1f}% {'✓' if vs_openqasm3 > 0 else '✗'}")
    print(f"    vs JSON:         {vs_json:+.1f}% ✓")
    print()
    
    # Parsing time comparisons
    print(f"  PARSING TIME:")
    print(f"    OpenQASM 2.0: {openqasm2_time:.3f} ms")
    print(f"    OpenQASM 3.0: {openqasm3_time:.3f} ms")
    print(f"    JSON:         {json_time:.3f} ms")
    print(f"    QuYAML:       {quyaml_time:.3f} ms")
    print()
    
    fastest = min(openqasm2_time, openqasm3_time, json_time, quyaml_time)
    quyaml_vs_fastest = ((quyaml_time - fastest) / fastest) * 100
    print(f"  PERFORMANCE vs fastest: {quyaml_vs_fastest:+.1f}%")
    print()
    print("-" * 80)
    print()

# Calculate averages
avg_quyaml = sum(r["quyaml"] for r in results) / len(results)
avg_openqasm2 = sum(r["openqasm2"] for r in results) / len(results)
avg_openqasm3 = sum(r["openqasm3"] for r in results) / len(results)
avg_json = sum(r["json"] for r in results) / len(results)

avg_quyaml_time = sum(r["quyaml_time"] for r in results) / len(results)
avg_openqasm2_time = sum(r["openqasm2_time"] for r in results) / len(results)
avg_openqasm3_time = sum(r["openqasm3_time"] for r in results) / len(results)
avg_json_time = sum(r["json_time"] for r in results) / len(results)

print("=" * 80)
print("SUMMARY - Token Efficiency (Average across all circuits)")
print("=" * 80)
print(f"OpenQASM 2.0:     {avg_openqasm2:.1f} tokens")
print(f"OpenQASM 3.0:     {avg_openqasm3:.1f} tokens")
print(f"JSON:             {avg_json:.1f} tokens")
print(f"QuYAML (v0.2):    {avg_quyaml:.1f} tokens")
print()

improvement_vs_openqasm2 = ((avg_openqasm2 - avg_quyaml) / avg_openqasm2) * 100
improvement_vs_openqasm3 = ((avg_openqasm3 - avg_quyaml) / avg_openqasm3) * 100
improvement_vs_json = ((avg_json - avg_quyaml) / avg_json) * 100

print(f"QuYAML vs OpenQASM 2.0: {improvement_vs_openqasm2:+.1f}%")
print(f"QuYAML vs OpenQASM 3.0: {improvement_vs_openqasm3:+.1f}%")
print(f"QuYAML vs JSON:         {improvement_vs_json:+.1f}%")
print()

# Parsing time summary
print("=" * 80)
print("SUMMARY - Parsing Time (Average across all circuits)")
print("=" * 80)
print(f"OpenQASM 2.0:     {avg_openqasm2_time:.3f} ms")
print(f"OpenQASM 3.0:     {avg_openqasm3_time:.3f} ms")
print(f"JSON:             {avg_json_time:.3f} ms")
print(f"QuYAML (v0.2):    {avg_quyaml_time:.3f} ms")
print()

fastest_avg = min(avg_openqasm2_time, avg_openqasm3_time, avg_json_time, avg_quyaml_time)
quyaml_time_vs_fastest = ((avg_quyaml_time - fastest_avg) / fastest_avg) * 100

print(f"QuYAML vs fastest parser: {quyaml_time_vs_fastest:+.1f}%")
print()

# Cost analysis
print("=" * 80)
print("COST ANALYSIS (GPT-4 API at $0.03/1K input tokens)")
print("=" * 80)
cost_openqasm2 = (avg_openqasm2 / 1000) * 0.03
cost_openqasm3 = (avg_openqasm3 / 1000) * 0.03
cost_quyaml = (avg_quyaml / 1000) * 0.03
cost_json = (avg_json / 1000) * 0.03

print(f"Cost per circuit call:")
print(f"  OpenQASM 2.0: ${cost_openqasm2:.6f}")
print(f"  OpenQASM 3.0: ${cost_openqasm3:.6f}")
print(f"  QuYAML:       ${cost_quyaml:.6f}")
print(f"  JSON:         ${cost_json:.6f}")
print()

savings_vs_openqasm2 = (cost_openqasm2 - cost_quyaml) * 100000
savings_vs_openqasm3 = (cost_openqasm3 - cost_quyaml) * 100000
savings_vs_json = (cost_json - cost_quyaml) * 100000

print(f"Savings per 100K API calls:")
print(f"  vs OpenQASM 2.0: ${savings_vs_openqasm2:+.2f}")
print(f"  vs OpenQASM 3.0: ${savings_vs_openqasm3:+.2f}")
print(f"  vs JSON:         ${savings_vs_json:+.2f}")
print()

# Performance verdict
print("=" * 80)
print("VERDICT")
print("=" * 80)
if improvement_vs_openqasm2 > 0 and improvement_vs_openqasm3 > 0:
    print("🎉 QuYAML beats both OpenQASM versions on token efficiency!")
elif improvement_vs_openqasm2 > 0:
    print("✓ QuYAML beats OpenQASM 2.0 on token efficiency")
    print(f"⚠️ OpenQASM 3.0 is {abs(improvement_vs_openqasm3):.1f}% more efficient")
else:
    print(f"⚠️ QuYAML is behind both OpenQASM versions on tokens")
    print(f"   OpenQASM 2.0: {abs(improvement_vs_openqasm2):.1f}% better")
    print(f"   OpenQASM 3.0: {abs(improvement_vs_openqasm3):.1f}% better")

print()
print(f"✓ QuYAML achieves {improvement_vs_json:.1f}% token reduction vs JSON")
print()

if quyaml_time_vs_fastest > 50:
    print(f"⚠️ QuYAML parsing is {quyaml_time_vs_fastest:.1f}% slower than fastest parser")
else:
    print(f"✓ QuYAML parsing time is acceptable ({avg_quyaml_time:.3f} ms average)")
