"""
QuYAML Benchmark Script
=======================
Empirically compares JSON, YAML, and QuYAML formats for defining quantum circuits.
Benchmarks: Token efficiency and parsing/conversion time.
"""

import time
import json
import yaml
import numpy as np
from quyaml_parser import parse_quyaml_to_qiskit
from qiskit import QuantumCircuit


# Test Data: Quantum Circuits in Multiple Formats
TEST_CIRCUITS = [
    {
        "name": "2-Qubit Simple Feature Map",
        "json_str": """{"circuit": "SimpleFeatureMap", "qreg": "q[2]", "parameters": {"x0": 0.5, "x1": 1.2}, "instructions": ["h q[0]", "h q[1]", "barrier", "rx(2 * $x0) q[0]", "rx(2 * $x1) q[1]", "barrier", "cx q[0], q[1]", "ry(2 * $x0 * $x1) q[1]", "cx q[0], q[1]"]}""",
        "yaml_str": """circuit: SimpleFeatureMap\nqreg: q[2]\nparameters:\n  x0: 0.5\n  x1: 1.2\ninstructions:\n  - h q[0]\n  - h q[1]\n  - barrier\n  - rx(2 * $x0) q[0]\n  - rx(2 * $x1) q[1]\n  - barrier\n  - cx q[0], q[1]\n  - ry(2 * $x0 * $x1) q[1]\n  - cx q[0], q[1]""",
        "quyaml_str": """
circuit: SimpleFeatureMap
qreg: q[2]
parameters:
  x0: 0.5
  x1: 1.2
instructions:
  - h q[0]
  - h q[1]
  - barrier
  - rx(2 * $x0) q[0]
  - rx(2 * $x1) q[1]
  - barrier
  - cx q[0], q[1]
  - ry(2 * $x0 * $x1) q[1]
  - cx q[0], q[1]
"""
    },
    {
        "name": "2-Qubit QAOA Ansatz (p=1)",
        "json_str": """{"circuit": "QAOA_Ansatz_p1", "qreg": "q[2]", "parameters": {"gamma": 0.5, "beta": 1.2}, "instructions": ["h q[0]", "h q[1]", "barrier", "cx q[0], q[1]", "ry(2 * $gamma) q[1]", "cx q[0], q[1]", "barrier", "rx(2 * $beta) q[0]", "rx(2 * $beta) q[1]"]}""",
        "yaml_str": """circuit: QAOA_Ansatz_p1\nqreg: q[2]\nparameters:\n  gamma: 0.5\n  beta: 1.2\ninstructions:\n  - h q[0]\n  - h q[1]\n  - barrier\n  - cx q[0], q[1]\n  - ry(2 * $gamma) q[1]\n  - cx q[0], q[1]\n  - barrier\n  - rx(2 * $beta) q[0]\n  - rx(2 * $beta) q[1]""",
        "quyaml_str": """
circuit: QAOA_Ansatz_p1
qreg: q[2]
parameters:
  gamma: 0.5
  beta: 1.2
instructions:
  - h q[0]
  - h q[1]
  - barrier
  - cx q[0], q[1]
  - ry(2 * $gamma) q[1]
  - cx q[0], q[1]
  - barrier
  - rx(2 * $beta) q[0]
  - rx(2 * $beta) q[1]
"""
    },
    {
        "name": "3-Qubit QFT",
        "json_str": """{"circuit": "QFT_3_Qubit", "qreg": "q[3]", "instructions": ["h q[0]", "cphase(pi/2) q[1], q[0]", "h q[1]", "cphase(pi/4) q[2], q[0]", "cphase(pi/2) q[2], q[1]", "h q[2]", "barrier", "swap q[0], q[2]"]}""",
        "yaml_str": """circuit: QFT_3_Qubit\nqreg: q[3]\ninstructions:\n  - h q[0]\n  - cphase(pi/2) q[1], q[0]\n  - h q[1]\n  - cphase(pi/4) q[2], q[0]\n  - cphase(pi/2) q[2], q[1]\n  - h q[2]\n  - barrier\n  - swap q[0], q[2]""",
        "quyaml_str": """
circuit: QFT_3_Qubit
qreg: q[3]
instructions:
  - h q[0]
  - cphase(pi/2) q[1], q[0]
  - h q[1]
  - cphase(pi/4) q[2], q[0]
  - cphase(pi/2) q[2], q[1]
  - h q[2]
  - barrier
  - swap q[0], q[2]
"""
    },
    {
        "name": "3-Qubit QAOA Max-Cut (p=2)",
        "json_str": """{"circuit": "QAOA_MaxCut_p2", "qreg": "q[3]", "parameters": {"gamma0": 0.785, "beta0": 1.57, "gamma1": 1.178, "beta1": 0.392}, "instructions": ["h q[0]", "h q[1]", "h q[2]", "barrier", "cx q[0], q[1]", "ry(2 * $gamma0) q[1]", "cx q[0], q[1]", "cx q[0], q[2]", "ry(2 * $gamma0) q[2]", "cx q[0], q[2]", "cx q[1], q[2]", "ry(2 * $gamma0) q[2]", "cx q[1], q[2]", "barrier", "rx(2 * $beta0) q[0]", "rx(2 * $beta0) q[1]", "rx(2 * $beta0) q[2]", "barrier", "cx q[0], q[1]", "ry(2 * $gamma1) q[1]", "cx q[0], q[1]", "cx q[0], q[2]", "ry(2 * $gamma1) q[2]", "cx q[0], q[2]", "cx q[1], q[2]", "ry(2 * $gamma1) q[2]", "cx q[1], q[2]", "barrier", "rx(2 * $beta1) q[0]", "rx(2 * $beta1) q[1]", "rx(2 * $beta1) q[2]"]}""",
        "yaml_str": """circuit: QAOA_MaxCut_p2\nqreg: q[3]\nparameters:\n  gamma0: 0.785\n  beta0: 1.57\n  gamma1: 1.178\n  beta1: 0.392\ninstructions:\n  - h q[0]\n  - h q[1]\n  - h q[2]\n  - barrier\n  - cx q[0], q[1]\n  - ry(2 * $gamma0) q[1]\n  - cx q[0], q[1]\n  - cx q[0], q[2]\n  - ry(2 * $gamma0) q[2]\n  - cx q[0], q[2]\n  - cx q[1], q[2]\n  - ry(2 * $gamma0) q[2]\n  - cx q[1], q[2]\n  - barrier\n  - rx(2 * $beta0) q[0]\n  - rx(2 * $beta0) q[1]\n  - rx(2 * $beta0) q[2]\n  - barrier\n  - cx q[0], q[1]\n  - ry(2 * $gamma1) q[1]\n  - cx q[0], q[1]\n  - cx q[0], q[2]\n  - ry(2 * $gamma1) q[2]\n  - cx q[0], q[2]\n  - cx q[1], q[2]\n  - ry(2 * $gamma1) q[2]\n  - cx q[1], q[2]\n  - barrier\n  - rx(2 * $beta1) q[0]\n  - rx(2 * $beta1) q[1]\n  - rx(2 * $beta1) q[2]""",
        "quyaml_str": """
circuit: QAOA_MaxCut_p2
qreg: q[3]
parameters:
  gamma0: 0.785
  beta0: 1.57
  gamma1: 1.178
  beta1: 0.392
instructions:
  - h q[0]
  - h q[1]
  - h q[2]
  - barrier
  - cx q[0], q[1]
  - ry(2 * $gamma0) q[1]
  - cx q[0], q[1]
  - cx q[0], q[2]
  - ry(2 * $gamma0) q[2]
  - cx q[0], q[2]
  - cx q[1], q[2]
  - ry(2 * $gamma0) q[2]
  - cx q[1], q[2]
  - barrier
  - rx(2 * $beta0) q[0]
  - rx(2 * $beta0) q[1]
  - rx(2 * $beta0) q[2]
  - barrier
  - cx q[0], q[1]
  - ry(2 * $gamma1) q[1]
  - cx q[0], q[1]
  - cx q[0], q[2]
  - ry(2 * $gamma1) q[2]
  - cx q[0], q[2]
  - cx q[1], q[2]
  - ry(2 * $gamma1) q[2]
  - cx q[1], q[2]
  - barrier
  - rx(2 * $beta1) q[0]
  - rx(2 * $beta1) q[1]
  - rx(2 * $beta1) q[2]
"""
    }
]


def benchmark_token_count(text_data: str) -> int:
    """
    Estimate token count for the given text.
    Uses a simple heuristic: 1 token ≈ 4 characters.
    
    Args:
        text_data: String representation of the circuit
        
    Returns:
        Estimated token count
    """
    return len(text_data) // 4


def benchmark_parsing_time(format_type: str, text_data: str, iterations: int = 100) -> float:
    """
    Measure the average time to parse text and convert to Qiskit circuit.
    
    Args:
        format_type: One of 'json', 'yaml', or 'quyaml'
        text_data: String representation of the circuit
        iterations: Number of iterations for averaging
        
    Returns:
        Average parsing time in milliseconds
    """
    total_time = 0.0
    
    for _ in range(iterations):
        start = time.perf_counter()
        
        if format_type == 'json':
            # Parse JSON and convert to circuit
            data = json.loads(text_data)
            # Simple conversion to YAML format for our parser
            yaml_str = yaml.dump(data)
            qc = parse_quyaml_to_qiskit(yaml_str)
            
        elif format_type == 'yaml':
            # Parse YAML directly
            qc = parse_quyaml_to_qiskit(text_data)
            
        elif format_type == 'quyaml':
            # Parse QuYAML directly
            qc = parse_quyaml_to_qiskit(text_data)
            
        else:
            raise ValueError(f"Unknown format type: {format_type}")
        
        end = time.perf_counter()
        total_time += (end - start)
    
    # Return average time in milliseconds
    return (total_time / iterations) * 1000


def main():
    """Main execution function to run benchmarks and generate report."""
    
    print("=" * 80)
    print("QuYAML Benchmark Report")
    print("=" * 80)
    print("\nComparing JSON, YAML, and QuYAML formats for quantum circuit definition")
    print(f"Testing {len(TEST_CIRCUITS)} circuits with 100 iterations each\n")
    
    results = []
    
    # Run benchmarks for each circuit
    for circuit in TEST_CIRCUITS:
        name = circuit['name']
        print(f"Benchmarking: {name}...")
        
        # Benchmark JSON
        json_tokens = benchmark_token_count(circuit['json_str'])
        json_time = benchmark_parsing_time('json', circuit['json_str'])
        results.append({
            'circuit': name,
            'format': 'JSON',
            'tokens': json_tokens,
            'time': json_time
        })
        
        # Benchmark YAML (compact)
        yaml_tokens = benchmark_token_count(circuit['yaml_str'])
        yaml_time = benchmark_parsing_time('yaml', circuit['yaml_str'])
        results.append({
            'circuit': name,
            'format': 'YAML',
            'tokens': yaml_tokens,
            'time': yaml_time
        })
        
        # Benchmark QuYAML
        quyaml_tokens = benchmark_token_count(circuit['quyaml_str'])
        quyaml_time = benchmark_parsing_time('quyaml', circuit['quyaml_str'])
        results.append({
            'circuit': name,
            'format': 'QuYAML',
            'tokens': quyaml_tokens,
            'time': quyaml_time
        })
    
    # Print results table
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS")
    print("=" * 80)
    print()
    print("| Circuit                        | Format  | Token Count | Avg. Parse Time (ms) |")
    print("|--------------------------------|---------|-------------|----------------------|")
    
    for result in results:
        circuit = result['circuit']
        format_type = result['format']
        tokens = result['tokens']
        time_ms = result['time']
        
        print(f"| {circuit:30} | {format_type:7} | {tokens:11} | {time_ms:20.4f} |")
    
    # Calculate and print summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()
    
    # Group by format
    formats = ['JSON', 'YAML', 'QuYAML']
    for fmt in formats:
        fmt_results = [r for r in results if r['format'] == fmt]
        avg_tokens = sum(r['tokens'] for r in fmt_results) / len(fmt_results)
        avg_time = sum(r['time'] for r in fmt_results) / len(fmt_results)
        
        print(f"{fmt:7} - Avg Token Count: {avg_tokens:8.1f} | Avg Parse Time: {avg_time:8.4f} ms")
    
    # Calculate improvements
    print("\n" + "=" * 80)
    print("QuYAML IMPROVEMENTS vs JSON")
    print("=" * 80)
    
    json_results = [r for r in results if r['format'] == 'JSON']
    quyaml_results = [r for r in results if r['format'] == 'QuYAML']
    
    json_avg_tokens = sum(r['tokens'] for r in json_results) / len(json_results)
    quyaml_avg_tokens = sum(r['tokens'] for r in quyaml_results) / len(quyaml_results)
    
    json_avg_time = sum(r['time'] for r in json_results) / len(json_results)
    quyaml_avg_time = sum(r['time'] for r in quyaml_results) / len(quyaml_results)
    
    token_improvement = ((json_avg_tokens - quyaml_avg_tokens) / json_avg_tokens) * 100
    time_improvement = ((json_avg_time - quyaml_avg_time) / json_avg_time) * 100
    
    print(f"\nToken Efficiency: {token_improvement:+.1f}% (fewer tokens is better)")
    print(f"Parse Speed:      {time_improvement:+.1f}% (negative means QuYAML is faster)")
    
    print("\n" + "=" * 80)
    print("QuYAML IMPROVEMENTS vs YAML")
    print("=" * 80)
    
    yaml_results = [r for r in results if r['format'] == 'YAML']
    
    yaml_avg_tokens = sum(r['tokens'] for r in yaml_results) / len(yaml_results)
    yaml_avg_time = sum(r['time'] for r in yaml_results) / len(yaml_results)
    
    token_improvement_yaml = ((yaml_avg_tokens - quyaml_avg_tokens) / yaml_avg_tokens) * 100
    time_improvement_yaml = ((yaml_avg_time - quyaml_avg_time) / yaml_avg_time) * 100
    
    print(f"\nToken Efficiency: {token_improvement_yaml:+.1f}% (fewer tokens is better)")
    print(f"Parse Speed:      {time_improvement_yaml:+.1f}% (negative means QuYAML is faster)")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("\nQuYAML provides:")
    print(f"  • {abs(token_improvement):.1f}% {'better' if token_improvement > 0 else 'worse'} token efficiency vs JSON")
    print(f"  • {abs(token_improvement_yaml):.1f}% {'better' if token_improvement_yaml > 0 else 'worse'} token efficiency vs YAML")
    print(f"  • {'Faster' if time_improvement > 0 else 'Slower'} parsing by {abs(time_improvement):.2f}% vs JSON")
    print(f"  • {'Faster' if time_improvement_yaml > 0 else 'Slower'} parsing by {abs(time_improvement_yaml):.2f}% vs YAML")
    print("  • Human-readable syntax optimized for quantum circuits")
    print("  • Native support for quantum-specific constructs (parameters, barriers, etc.)")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
