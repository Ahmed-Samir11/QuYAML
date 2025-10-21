"""
QuYAML vs Industry Standards Benchmark
======================================
Compares QuYAML against actual industry-standard formats:
- OpenQASM 2.0 (Qiskit's native format)
- Qiskit JSON serialization
- QuYAML

This shows the TRUE token efficiency gains.
"""

import time
import json
import numpy as np
from quyaml_parser import parse_quyaml_to_qiskit
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.qasm2 import dumps as qasm_dumps


def benchmark_token_count(text: str) -> int:
    """Estimate token count: 1 token ≈ 4 characters (OpenAI guideline)"""
    return len(text) // 4


def circuit_to_qiskit_json(qc: QuantumCircuit) -> str:
    """Convert Qiskit circuit to standard JSON format"""
    # Qiskit's native JSON-like representation
    circuit_dict = {
        "name": qc.name,
        "num_qubits": qc.num_qubits,
        "num_clbits": qc.num_clbits,
        "instructions": []
    }
    
    for instruction, qargs, cargs in qc.data:
        inst_dict = {
            "name": instruction.name,
            "qubits": [qc.find_bit(q).index for q in qargs],
            "params": [float(p) for p in instruction.params] if instruction.params else []
        }
        if cargs:
            inst_dict["clbits"] = [qc.find_bit(c).index for c in cargs]
        circuit_dict["instructions"].append(inst_dict)
    
    return json.dumps(circuit_dict)


# Test Circuits
TEST_CASES = [
    {
        "name": "Bell State",
        "quyaml": """circuit: BellState
qreg: q[2]
creg: c[2]
instructions:
  - h q[0]
  - cx q[0], q[1]
  - measure""",
        "reference_circuit": lambda: (
            qc := QuantumCircuit(2, 2, name="BellState"),
            qc.h(0),
            qc.cx(0, 1),
            qc.measure_all(),
            qc
        )[-1]
    },
    {
        "name": "GHZ State (3 qubits)",
        "quyaml": """circuit: GHZ
qreg: q[3]
creg: c[3]
instructions:
  - h q[0]
  - cx q[0], q[1]
  - cx q[0], q[2]
  - measure""",
        "reference_circuit": lambda: (
            qc := QuantumCircuit(3, 3, name="GHZ"),
            qc.h(0),
            qc.cx(0, 1),
            qc.cx(0, 2),
            qc.measure_all(),
            qc
        )[-1]
    },
    {
        "name": "Parameterized QAOA (2 qubits, p=1)",
        "quyaml": """circuit: QAOA
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
  - rx(2 * $beta) q[1]""",
        "reference_circuit": lambda: (
            qc := QuantumCircuit(2, name="QAOA"),
            qc.h(0),
            qc.h(1),
            qc.cx(0, 1),
            qc.ry(2 * 0.5, 1),
            qc.cx(0, 1),
            qc.rx(2 * 1.2, 0),
            qc.rx(2 * 1.2, 1),
            qc
        )[-1]
    },
    {
        "name": "QFT (3 qubits)",
        "quyaml": """circuit: QFT
qreg: q[3]
instructions:
  - h q[0]
  - cphase(pi/2) q[1], q[0]
  - h q[1]
  - cphase(pi/4) q[2], q[0]
  - cphase(pi/2) q[2], q[1]
  - h q[2]
  - swap q[0], q[2]""",
        "reference_circuit": lambda: (
            qc := QuantumCircuit(3, name="QFT"),
            qc.h(0),
            qc.cp(np.pi/2, 1, 0),
            qc.h(1),
            qc.cp(np.pi/4, 2, 0),
            qc.cp(np.pi/2, 2, 1),
            qc.h(2),
            qc.swap(0, 2),
            qc
        )[-1]
    },
    {
        "name": "VQE Ansatz (2 qubits)",
        "quyaml": """circuit: VQE
qreg: q[2]
parameters:
  theta0: 0.1
  theta1: 0.2
  theta2: 0.3
instructions:
  - ry($theta0) q[0]
  - ry($theta1) q[1]
  - cx q[0], q[1]
  - ry($theta2) q[1]
  - cx q[0], q[1]""",
        "reference_circuit": lambda: (
            qc := QuantumCircuit(2, name="VQE"),
            qc.ry(0.1, 0),
            qc.ry(0.2, 1),
            qc.cx(0, 1),
            qc.ry(0.3, 1),
            qc.cx(0, 1),
            qc
        )[-1]
    }
]


def run_benchmark():
    """Run comprehensive benchmark comparing QuYAML vs industry standards"""
    
    print("=" * 80)
    print("QuYAML vs Industry Standards Benchmark")
    print("=" * 80)
    print()
    print("Comparing QuYAML against:")
    print("  1. OpenQASM 2.0 (Qiskit's native format)")
    print("  2. Qiskit JSON serialization")
    print("  3. QuYAML")
    print()
    print("=" * 80)
    print()
    
    results = []
    
    for test in TEST_CASES:
        print(f"Testing: {test['name']}...")
        
        # Get QuYAML representation
        quyaml_str = test['quyaml']
        quyaml_tokens = benchmark_token_count(quyaml_str)
        
        # Create reference Qiskit circuit
        ref_circuit = test['reference_circuit']()
        
        # Get OpenQASM representation
        try:
            qasm_str = qasm_dumps(ref_circuit)
            qasm_tokens = benchmark_token_count(qasm_str)
        except Exception as e:
            # Fallback for circuits with parameters
            qasm_str = ref_circuit.qasm()
            qasm_tokens = benchmark_token_count(qasm_str)
        
        # Get JSON representation
        json_str = circuit_to_qiskit_json(ref_circuit)
        json_tokens = benchmark_token_count(json_str)
        
        results.append({
            'name': test['name'],
            'qasm': qasm_str,
            'qasm_tokens': qasm_tokens,
            'json': json_str,
            'json_tokens': json_tokens,
            'quyaml': quyaml_str,
            'quyaml_tokens': quyaml_tokens
        })
        
        print(f"  OpenQASM: {qasm_tokens} tokens ({len(qasm_str)} chars)")
        print(f"  JSON:     {json_tokens} tokens ({len(json_str)} chars)")
        print(f"  QuYAML:   {quyaml_tokens} tokens ({len(quyaml_str)} chars)")
        print()
    
    # Calculate averages
    avg_qasm = sum(r['qasm_tokens'] for r in results) / len(results)
    avg_json = sum(r['json_tokens'] for r in results) / len(results)
    avg_quyaml = sum(r['quyaml_tokens'] for r in results) / len(results)
    
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()
    print(f"OpenQASM 2.0 - Average Token Count: {avg_qasm:.1f}")
    print(f"Qiskit JSON  - Average Token Count: {avg_json:.1f}")
    print(f"QuYAML       - Average Token Count: {avg_quyaml:.1f}")
    print()
    
    # Calculate improvements
    improvement_vs_qasm = ((avg_qasm - avg_quyaml) / avg_qasm) * 100
    improvement_vs_json = ((avg_json - avg_quyaml) / avg_json) * 100
    
    print("=" * 80)
    print("QuYAML TOKEN EFFICIENCY GAINS")
    print("=" * 80)
    print()
    print(f"vs OpenQASM 2.0: {improvement_vs_qasm:+.1f}% (QuYAML uses {improvement_vs_qasm:.1f}% fewer tokens)")
    print(f"vs Qiskit JSON:  {improvement_vs_json:+.1f}% (QuYAML uses {improvement_vs_json:.1f}% fewer tokens)")
    print()
    
    # Detailed comparison table
    print("=" * 80)
    print("DETAILED COMPARISON TABLE")
    print("=" * 80)
    print()
    print(f"{'Circuit':<30} | {'QASM':<8} | {'JSON':<8} | {'QuYAML':<8} | QASM->QuYAML | JSON->QuYAML")
    print("-" * 80)
    
    for r in results:
        qasm_improvement = ((r['qasm_tokens'] - r['quyaml_tokens']) / r['qasm_tokens']) * 100
        json_improvement = ((r['json_tokens'] - r['quyaml_tokens']) / r['json_tokens']) * 100
        
        print(f"{r['name']:<30} | {r['qasm_tokens']:>6}   | {r['json_tokens']:>6}   | "
              f"{r['quyaml_tokens']:>6}   | {qasm_improvement:>10.1f}% | {json_improvement:>10.1f}%")
    
    print()
    print("=" * 80)
    print()
    
    # Show actual examples
    print("EXAMPLE: Bell State Circuit")
    print("=" * 80)
    print()
    bell = results[0]
    print("OpenQASM 2.0:")
    print("-" * 40)
    print(bell['qasm'])
    print()
    print("Qiskit JSON:")
    print("-" * 40)
    print(bell['json'])
    print()
    print("QuYAML:")
    print("-" * 40)
    print(bell['quyaml'])
    print()
    print("=" * 80)
    print()
    print(f"CONCLUSION: QuYAML achieves {improvement_vs_qasm:.1f}% token reduction vs OpenQASM")
    print(f"            and {improvement_vs_json:.1f}% token reduction vs JSON!")
    print()
    print("This makes QuYAML ideal for LLM-driven quantum development,")
    print("reducing API costs and fitting more context into prompts.")
    print("=" * 80)


if __name__ == "__main__":
    run_benchmark()
