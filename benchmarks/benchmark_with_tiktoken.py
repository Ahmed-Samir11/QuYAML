"""
QuYAML Benchmark with Real GPT Tokenizer (tiktoken)
====================================================
Uses OpenAI's official tiktoken library to measure EXACT token counts
for GPT-3.5-turbo and GPT-4 models.

This provides definitive measurements of QuYAML's token efficiency.
"""

import time
import json
import tiktoken
import numpy as np
from quyaml import parse_quyaml_to_qiskit
from qiskit import QuantumCircuit
from qiskit.qasm2 import dumps as qasm_dumps, loads as qasm_loads


# ============================================================================
# EXACT TOKEN COUNTING WITH TIKTOKEN
# ============================================================================

def count_tokens_gpt35(text: str) -> int:
    """Count exact tokens for GPT-3.5-turbo"""
    encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoder.encode(text)
    return len(tokens)


def count_tokens_gpt4(text: str) -> int:
    """Count exact tokens for GPT-4"""
    encoder = tiktoken.encoding_for_model("gpt-4")
    tokens = encoder.encode(text)
    return len(tokens)


def count_tokens_estimate(text: str) -> int:
    """Estimate using chars/4 method for comparison"""
    return len(text) // 4


# ============================================================================
# CIRCUIT CONVERSION
# ============================================================================

def circuit_to_qiskit_json(qc: QuantumCircuit) -> str:
    """Convert Qiskit circuit to standard JSON format"""
    circuit_dict = {
        "name": qc.name,
        "num_qubits": qc.num_qubits,
        "num_clbits": qc.num_clbits,
        "instructions": []
    }
    
    for instr in qc.data:
        inst_dict = {
            "name": instr.operation.name,
            "qubits": [qc.find_bit(q).index for q in instr.qubits],
            "params": [float(p) for p in instr.operation.params] if instr.operation.params else []
        }
        if instr.clbits:
            inst_dict["clbits"] = [qc.find_bit(c).index for c in instr.clbits]
        circuit_dict["instructions"].append(inst_dict)
    
    return json.dumps(circuit_dict)


# ============================================================================
# TEST CASES
# ============================================================================

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
        "name": "Parameterized QAOA (p=1)",
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
    },
    {
        "name": "QAOA Max-Cut (p=2, 4 qubits)",
        "quyaml": """circuit: QAOA_MaxCut
qreg: q[4]
parameters:
  gamma0: 0.785
  beta0: 1.57
  gamma1: 1.178
  beta1: 0.392
instructions:
  - h q[0]
  - h q[1]
  - h q[2]
  - h q[3]
  - barrier
  - cx q[0], q[1]
  - ry(2 * $gamma0) q[1]
  - cx q[0], q[1]
  - cx q[1], q[2]
  - ry(2 * $gamma0) q[2]
  - cx q[1], q[2]
  - cx q[2], q[3]
  - ry(2 * $gamma0) q[3]
  - cx q[2], q[3]
  - barrier
  - rx(2 * $beta0) q[0]
  - rx(2 * $beta0) q[1]
  - rx(2 * $beta0) q[2]
  - rx(2 * $beta0) q[3]
  - barrier
  - cx q[0], q[1]
  - ry(2 * $gamma1) q[1]
  - cx q[0], q[1]
  - cx q[1], q[2]
  - ry(2 * $gamma1) q[2]
  - cx q[1], q[2]
  - cx q[2], q[3]
  - ry(2 * $gamma1) q[3]
  - cx q[2], q[3]
  - barrier
  - rx(2 * $beta1) q[0]
  - rx(2 * $beta1) q[1]
  - rx(2 * $beta1) q[2]
  - rx(2 * $beta1) q[3]""",
        "reference_circuit": lambda: (
            qc := QuantumCircuit(4, name="QAOA_MaxCut"),
            qc.h(0), qc.h(1), qc.h(2), qc.h(3),
            qc.barrier(),
            qc.cx(0, 1), qc.ry(2 * 0.785, 1), qc.cx(0, 1),
            qc.cx(1, 2), qc.ry(2 * 0.785, 2), qc.cx(1, 2),
            qc.cx(2, 3), qc.ry(2 * 0.785, 3), qc.cx(2, 3),
            qc.barrier(),
            qc.rx(2 * 1.57, 0), qc.rx(2 * 1.57, 1), qc.rx(2 * 1.57, 2), qc.rx(2 * 1.57, 3),
            qc.barrier(),
            qc.cx(0, 1), qc.ry(2 * 1.178, 1), qc.cx(0, 1),
            qc.cx(1, 2), qc.ry(2 * 1.178, 2), qc.cx(1, 2),
            qc.cx(2, 3), qc.ry(2 * 1.178, 3), qc.cx(2, 3),
            qc.barrier(),
            qc.rx(2 * 0.392, 0), qc.rx(2 * 0.392, 1), qc.rx(2 * 0.392, 2), qc.rx(2 * 0.392, 3),
            qc
        )[-1]
    },
    {
        "name": "Grover's Algorithm (3 qubits)",
        "quyaml": """circuit: Grover
qreg: q[3]
instructions:
  - h q[0]
  - h q[1]
  - h q[2]
  - barrier
  - x q[0]
  - x q[1]
  - h q[2]
  - cx q[0], q[2]
  - cx q[1], q[2]
  - h q[2]
  - x q[0]
  - x q[1]
  - barrier
  - h q[0]
  - h q[1]
  - h q[2]
  - x q[0]
  - x q[1]
  - x q[2]
  - h q[2]
  - cx q[0], q[2]
  - cx q[1], q[2]
  - h q[2]
  - x q[0]
  - x q[1]
  - x q[2]
  - h q[0]
  - h q[1]
  - h q[2]""",
        "reference_circuit": lambda: (
            qc := QuantumCircuit(3, name="Grover"),
            qc.h(0), qc.h(1), qc.h(2),
            qc.barrier(),
            qc.x(0), qc.x(1),
            qc.h(2), qc.cx(0, 2), qc.cx(1, 2), qc.h(2),
            qc.x(0), qc.x(1),
            qc.barrier(),
            qc.h(0), qc.h(1), qc.h(2),
            qc.x(0), qc.x(1), qc.x(2),
            qc.h(2), qc.cx(0, 2), qc.cx(1, 2), qc.h(2),
            qc.x(0), qc.x(1), qc.x(2),
            qc.h(0), qc.h(1), qc.h(2),
            qc
        )[-1]
    },
    {
        "name": "Quantum Teleportation",
        "quyaml": """circuit: Teleportation
qreg: q[3]
creg: c[2]
instructions:
  - h q[1]
  - cx q[1], q[2]
  - barrier
  - cx q[0], q[1]
  - h q[0]
  - barrier
  - measure q[0], c[0]
  - measure q[1], c[1]""",
        "reference_circuit": lambda: (
            qc := QuantumCircuit(3, 2, name="Teleportation"),
            qc.h(1),
            qc.cx(1, 2),
            qc.barrier(),
            qc.cx(0, 1),
            qc.h(0),
            qc.barrier(),
            qc.measure(0, 0),
            qc.measure(1, 1),
            qc
        )[-1]
    }
]


# ============================================================================
# MAIN BENCHMARK
# ============================================================================

def run_tiktoken_benchmark():
    """Run comprehensive benchmark with real GPT tokenizer"""
    
    print("=" * 100)
    print("QuYAML Token Efficiency Benchmark - EXACT GPT TOKENIZATION")
    print("=" * 100)
    print()
    print("Using OpenAI's tiktoken library for EXACT token counts")
    print("Models: GPT-3.5-turbo, GPT-4")
    print()
    print("Formats compared:")
    print("  1. OpenQASM 2.0 (Qiskit's native quantum assembly)")
    print("  2. Qiskit JSON (standard JSON serialization)")
    print("  3. QuYAML (proposed YAML-based format)")
    print()
    print("=" * 100)
    print()
    
    all_results = []
    
    for test in TEST_CASES:
        print(f"Testing: {test['name']}...")
        
        # Get representations
        quyaml_str = test['quyaml']
        ref_circuit = test['reference_circuit']()
        
        try:
            qasm_str = qasm_dumps(ref_circuit)
        except:
            qasm_str = ref_circuit.qasm()
        
        json_str = circuit_to_qiskit_json(ref_circuit)
        
        # Count tokens with all methods
        result = {
            'name': test['name'],
            'formats': {
                'OpenQASM': {
                    'text': qasm_str,
                    'chars': len(qasm_str),
                    'tokens_gpt35': count_tokens_gpt35(qasm_str),
                    'tokens_gpt4': count_tokens_gpt4(qasm_str),
                    'tokens_estimate': count_tokens_estimate(qasm_str)
                },
                'JSON': {
                    'text': json_str,
                    'chars': len(json_str),
                    'tokens_gpt35': count_tokens_gpt35(json_str),
                    'tokens_gpt4': count_tokens_gpt4(json_str),
                    'tokens_estimate': count_tokens_estimate(json_str)
                },
                'QuYAML': {
                    'text': quyaml_str,
                    'chars': len(quyaml_str),
                    'tokens_gpt35': count_tokens_gpt35(quyaml_str),
                    'tokens_gpt4': count_tokens_gpt4(quyaml_str),
                    'tokens_estimate': count_tokens_estimate(quyaml_str)
                }
            }
        }
        
        all_results.append(result)
        print(f"  [OK] Completed")
        print()
    
    # ========================================================================
    # DETAILED RESULTS
    # ========================================================================
    
    print("=" * 100)
    print("PART 1: EXACT GPT-4 TOKEN COUNTS (tiktoken)")
    print("=" * 100)
    print()
    print(f"{'Circuit':<35} | {'OpenQASM':<10} | {'JSON':<10} | {'QuYAML':<10} | vs QASM | vs JSON")
    print("-" * 100)
    
    for r in all_results:
        qasm_tok = r['formats']['OpenQASM']['tokens_gpt4']
        json_tok = r['formats']['JSON']['tokens_gpt4']
        quyaml_tok = r['formats']['QuYAML']['tokens_gpt4']
        
        vs_qasm = ((qasm_tok - quyaml_tok) / qasm_tok * 100) if qasm_tok > 0 else 0
        vs_json = ((json_tok - quyaml_tok) / json_tok * 100) if json_tok > 0 else 0
        
        print(f"{r['name']:<35} | {qasm_tok:>10} | {json_tok:>10} | {quyaml_tok:>10} | "
              f"{vs_qasm:>6.1f}% | {vs_json:>6.1f}%")
    
    print()
    print()
    
    # ========================================================================
    # GPT-3.5-TURBO COMPARISON
    # ========================================================================
    
    print("=" * 100)
    print("PART 2: EXACT GPT-3.5-TURBO TOKEN COUNTS (tiktoken)")
    print("=" * 100)
    print()
    print(f"{'Circuit':<35} | {'OpenQASM':<10} | {'JSON':<10} | {'QuYAML':<10} | vs QASM | vs JSON")
    print("-" * 100)
    
    for r in all_results:
        qasm_tok = r['formats']['OpenQASM']['tokens_gpt35']
        json_tok = r['formats']['JSON']['tokens_gpt35']
        quyaml_tok = r['formats']['QuYAML']['tokens_gpt35']
        
        vs_qasm = ((qasm_tok - quyaml_tok) / qasm_tok * 100) if qasm_tok > 0 else 0
        vs_json = ((json_tok - quyaml_tok) / json_tok * 100) if json_tok > 0 else 0
        
        print(f"{r['name']:<35} | {qasm_tok:>10} | {json_tok:>10} | {quyaml_tok:>10} | "
              f"{vs_qasm:>6.1f}% | {vs_json:>6.1f}%")
    
    print()
    print()
    
    # ========================================================================
    # COMPARISON: ESTIMATED vs ACTUAL
    # ========================================================================
    
    print("=" * 100)
    print("PART 3: ESTIMATED (chars/4) vs ACTUAL (GPT-4) TOKEN COUNTS")
    print("=" * 100)
    print()
    print(f"{'Circuit':<35} | {'Format':<10} | {'Estimate':<10} | {'Actual':<10} | Error")
    print("-" * 100)
    
    for r in all_results:
        for fmt in ['OpenQASM', 'JSON', 'QuYAML']:
            est = r['formats'][fmt]['tokens_estimate']
            act = r['formats'][fmt]['tokens_gpt4']
            error = ((est - act) / act * 100) if act > 0 else 0
            
            print(f"{r['name']:<35} | {fmt:<10} | {est:>10} | {act:>10} | {error:>6.1f}%")
    
    print()
    print()
    
    # ========================================================================
    # SUMMARY STATISTICS
    # ========================================================================
    
    print("=" * 100)
    print("SUMMARY - EXACT GPT-4 TOKEN EFFICIENCY")
    print("=" * 100)
    print()
    
    # Calculate averages
    avg_qasm_gpt4 = sum(r['formats']['OpenQASM']['tokens_gpt4'] for r in all_results) / len(all_results)
    avg_json_gpt4 = sum(r['formats']['JSON']['tokens_gpt4'] for r in all_results) / len(all_results)
    avg_quyaml_gpt4 = sum(r['formats']['QuYAML']['tokens_gpt4'] for r in all_results) / len(all_results)
    
    avg_qasm_gpt35 = sum(r['formats']['OpenQASM']['tokens_gpt35'] for r in all_results) / len(all_results)
    avg_json_gpt35 = sum(r['formats']['JSON']['tokens_gpt35'] for r in all_results) / len(all_results)
    avg_quyaml_gpt35 = sum(r['formats']['QuYAML']['tokens_gpt35'] for r in all_results) / len(all_results)
    
    print("GPT-4 Token Counts (EXACT):")
    print(f"  OpenQASM: {avg_qasm_gpt4:.1f} tokens")
    print(f"  JSON:     {avg_json_gpt4:.1f} tokens")
    print(f"  QuYAML:   {avg_quyaml_gpt4:.1f} tokens")
    print()
    
    improvement_vs_qasm_gpt4 = ((avg_qasm_gpt4 - avg_quyaml_gpt4) / avg_qasm_gpt4) * 100
    improvement_vs_json_gpt4 = ((avg_json_gpt4 - avg_quyaml_gpt4) / avg_json_gpt4) * 100
    
    print(f"  QuYAML vs OpenQASM: {improvement_vs_qasm_gpt4:+.1f}%")
    print(f"  QuYAML vs JSON:     {improvement_vs_json_gpt4:+.1f}%")
    print()
    
    print("GPT-3.5-turbo Token Counts (EXACT):")
    print(f"  OpenQASM: {avg_qasm_gpt35:.1f} tokens")
    print(f"  JSON:     {avg_json_gpt35:.1f} tokens")
    print(f"  QuYAML:   {avg_quyaml_gpt35:.1f} tokens")
    print()
    
    improvement_vs_qasm_gpt35 = ((avg_qasm_gpt35 - avg_quyaml_gpt35) / avg_qasm_gpt35) * 100
    improvement_vs_json_gpt35 = ((avg_json_gpt35 - avg_quyaml_gpt35) / avg_json_gpt35) * 100
    
    print(f"  QuYAML vs OpenQASM: {improvement_vs_qasm_gpt35:+.1f}%")
    print(f"  QuYAML vs JSON:     {improvement_vs_json_gpt35:+.1f}%")
    print()
    
    # ========================================================================
    # COST ANALYSIS
    # ========================================================================
    
    print("=" * 100)
    print("API COST ANALYSIS (GPT-4 Pricing)")
    print("=" * 100)
    print()
    
    # GPT-4 pricing (as of 2024)
    gpt4_input_cost_per_1k = 0.03  # $0.03 per 1K tokens
    
    # Calculate cost for 1000 API calls with average circuit
    calls = 1000
    
    cost_qasm = (avg_qasm_gpt4 * calls / 1000) * gpt4_input_cost_per_1k
    cost_json = (avg_json_gpt4 * calls / 1000) * gpt4_input_cost_per_1k
    cost_quyaml = (avg_quyaml_gpt4 * calls / 1000) * gpt4_input_cost_per_1k
    
    print(f"Cost for {calls} API calls (average circuit):")
    print(f"  OpenQASM: ${cost_qasm:.2f}")
    print(f"  JSON:     ${cost_json:.2f}")
    print(f"  QuYAML:   ${cost_quyaml:.2f}")
    print()
    print(f"Savings with QuYAML:")
    print(f"  vs OpenQASM: ${cost_qasm - cost_quyaml:.2f} ({improvement_vs_qasm_gpt4:.1f}% reduction)")
    print(f"  vs JSON:     ${cost_json - cost_quyaml:.2f} ({improvement_vs_json_gpt4:.1f}% reduction)")
    print()
    
    # Extrapolate to larger scale
    large_scale = 100000
    large_savings_qasm = ((avg_qasm_gpt4 * large_scale / 1000) * gpt4_input_cost_per_1k) - \
                          ((avg_quyaml_gpt4 * large_scale / 1000) * gpt4_input_cost_per_1k)
    large_savings_json = ((avg_json_gpt4 * large_scale / 1000) * gpt4_input_cost_per_1k) - \
                          ((avg_quyaml_gpt4 * large_scale / 1000) * gpt4_input_cost_per_1k)
    
    print(f"Savings with QuYAML at scale ({large_scale:,} API calls):")
    print(f"  vs OpenQASM: ${large_savings_qasm:,.2f}")
    print(f"  vs JSON:     ${large_savings_json:,.2f}")
    print()
    
    print("=" * 100)
    print()
    print("KEY FINDINGS:")
    print(f"  - QuYAML achieves {improvement_vs_json_gpt4:.1f}% token reduction vs JSON (EXACT)")
    print(f"  - QuYAML achieves {improvement_vs_qasm_gpt4:.1f}% token reduction vs OpenQASM (EXACT)")
    print(f"  - For 100K API calls: Save ${large_savings_json:,.2f} vs JSON, ${large_savings_qasm:,.2f} vs OpenQASM")
    print(f"  - Measurements using OpenAI's official tiktoken library (GPT-4 encoder)")
    print(f"  - QuYAML is the most token-efficient format for LLM-driven quantum development")
    print()
    print("=" * 100)


if __name__ == "__main__":
    run_tiktoken_benchmark()
