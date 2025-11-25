"""
Benchmark QuYAML vs OpenQASM vs JSON using OPTIMIZED QuYAML syntax.
Uses tiktoken for exact GPT-4 tokenization.
"""

import tiktoken
import json
from qiskit import QuantumCircuit
from quyaml import parse_quyaml_to_qiskit

# Initialize GPT-4 tokenizer
encoder = tiktoken.encoding_for_model("gpt-4")

def count_tokens(text: str) -> int:
    """Count tokens using tiktoken (GPT-4 tokenizer)."""
    return len(encoder.encode(text))

# Test circuits using OPTIMIZED QuYAML syntax
test_circuits = {
    "Bell State": {
        "quyaml": """circuit: bell
qubits: q[2]
bits: c[2]
ops:
  - h 0
  - cx 0 1
  - measure""",
        "openqasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q -> c;""",
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
        "openqasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
h q[0];
cx q[0],q[1];
cx q[1],q[2];
measure q -> c;""",
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
        "openqasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
h q[1];
cp(1.0) q[0],q[1];
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
        "openqasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
h q[0];
cp(1.5708) q[1],q[0];
h q[1];
cp(0.7854) q[2],q[0];
cp(1.5708) q[2],q[1];
h q[2];
swap q[0],q[2];""",
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
        "openqasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
ry(0.5) q[0];
ry(1.2) q[1];
cx q[0],q[1];
ry(0.8) q[2];
cx q[1],q[2];
cx q[2],q[3];""",
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
        "openqasm": """OPENQASM 2.0;
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
        "openqasm": """OPENQASM 2.0;
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
        "openqasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
h q[1];
cx q[1],q[2];
cx q[0],q[1];
h q[0];
measure q -> c;""",
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
print("OPTIMIZED QuYAML vs OpenQASM vs JSON - Exact GPT-4 Tokenization")
print("=" * 80)
print()

results = []
for name, data in test_circuits.items():
    quyaml_str = data["quyaml"]
    openqasm_str = data["openqasm"]
    json_str = circuit_to_json(name)
    
    quyaml_tokens = count_tokens(quyaml_str)
    openqasm_tokens = count_tokens(openqasm_str)
    json_tokens = count_tokens(json_str)
    
    results.append({
        "name": name,
        "quyaml": quyaml_tokens,
        "openqasm": openqasm_tokens,
        "json": json_tokens,
        "description": data["description"]
    })
    
    print(f"{name}")
    print(f"  Description: {data['description']}")
    print(f"  OpenQASM:    {openqasm_tokens:4d} tokens")
    print(f"  JSON:        {json_tokens:4d} tokens")
    print(f"  QuYAML (OPT): {quyaml_tokens:4d} tokens")
    
    vs_openqasm = ((openqasm_tokens - quyaml_tokens) / openqasm_tokens) * 100
    vs_json = ((json_tokens - quyaml_tokens) / json_tokens) * 100
    
    print(f"  vs OpenQASM: {vs_openqasm:+.1f}% {'✓' if vs_openqasm > 0 else '✗'}")
    print(f"  vs JSON:     {vs_json:+.1f}% ✓")
    print()

# Calculate averages
avg_quyaml = sum(r["quyaml"] for r in results) / len(results)
avg_openqasm = sum(r["openqasm"] for r in results) / len(results)
avg_json = sum(r["json"] for r in results) / len(results)

print("=" * 80)
print("SUMMARY (Average across all circuits)")
print("=" * 80)
print(f"OpenQASM:         {avg_openqasm:.1f} tokens")
print(f"JSON:             {avg_json:.1f} tokens")
print(f"QuYAML (OPTIMIZED): {avg_quyaml:.1f} tokens")
print()

improvement_vs_openqasm = ((avg_openqasm - avg_quyaml) / avg_openqasm) * 100
improvement_vs_json = ((avg_json - avg_quyaml) / avg_json) * 100

print(f"QuYAML vs OpenQASM: {improvement_vs_openqasm:+.1f}%")
print(f"QuYAML vs JSON:     {improvement_vs_json:+.1f}%")
print()

if improvement_vs_openqasm > 0:
    print("🎉 SUCCESS! Optimized QuYAML beats OpenQASM!")
else:
    print(f"⚠️  Still behind OpenQASM by {abs(improvement_vs_openqasm):.1f}%")

# Cost analysis
print()
print("=" * 80)
print("COST ANALYSIS (GPT-4 API at $0.03/1K input tokens)")
print("=" * 80)
cost_quyaml = (avg_quyaml / 1000) * 0.03
cost_openqasm = (avg_openqasm / 1000) * 0.03
cost_json = (avg_json / 1000) * 0.03

print(f"Cost per circuit call:")
print(f"  OpenQASM: ${cost_openqasm:.6f}")
print(f"  QuYAML:   ${cost_quyaml:.6f}")
print(f"  JSON:     ${cost_json:.6f}")
print()

savings_vs_openqasm = (cost_openqasm - cost_quyaml) * 100000
savings_vs_json = (cost_json - cost_quyaml) * 100000

print(f"Savings per 100K API calls:")
print(f"  vs OpenQASM: ${savings_vs_openqasm:+.2f}")
print(f"  vs JSON:     ${savings_vs_json:+.2f}")
