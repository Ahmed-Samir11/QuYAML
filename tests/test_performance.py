"""
Performance tests for QuYAML parser.
Measures parsing time to ensure acceptable performance.
"""

import pytest
import time
from quyaml_parser import parse_quyaml_to_qiskit

# Performance thresholds (in milliseconds)
SIMPLE_CIRCUIT_MAX_TIME = 5.0  # Simple circuits should parse in < 5ms
COMPLEX_CIRCUIT_MAX_TIME = 10.0  # Complex circuits should parse in < 10ms


def measure_parse_time(quyaml_string: str, iterations: int = 100) -> float:
    """Measure average parsing time over multiple iterations."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        parse_quyaml_to_qiskit(quyaml_string)
        end = time.perf_counter()
        times.append(end - start)
    return sum(times) / len(times) * 1000  # Return in milliseconds


def test_bell_state_parse_time():
    """Test that Bell state circuit parses in acceptable time."""
    quyaml_string = """
    circuit: bell
    qubits: q[2]
    ops:
      - h 0
      - cx 0 1
    """
    avg_time = measure_parse_time(quyaml_string)
    assert avg_time < SIMPLE_CIRCUIT_MAX_TIME, \
        f"Bell state parsing too slow: {avg_time:.2f}ms (max: {SIMPLE_CIRCUIT_MAX_TIME}ms)"


def test_ghz_state_parse_time():
    """Test that GHZ state circuit parses in acceptable time."""
    quyaml_string = """
    circuit: ghz
    qubits: q[3]
    ops:
      - h 0
      - cx 0 1
      - cx 1 2
    """
    avg_time = measure_parse_time(quyaml_string)
    assert avg_time < SIMPLE_CIRCUIT_MAX_TIME, \
        f"GHZ state parsing too slow: {avg_time:.2f}ms (max: {SIMPLE_CIRCUIT_MAX_TIME}ms)"


def test_parameterized_circuit_parse_time():
    """Test that parameterized circuits parse in acceptable time."""
    quyaml_string = """
    circuit: qaoa
    qubits: q[2]
    params: {gamma: 0.5, beta: 1.2}
    ops:
      - h 0
      - h 1
      - cphase(2*$gamma) 0 1
      - rx(2*$beta) 0
      - rx(2*$beta) 1
    """
    avg_time = measure_parse_time(quyaml_string)
    assert avg_time < SIMPLE_CIRCUIT_MAX_TIME, \
        f"QAOA parsing too slow: {avg_time:.2f}ms (max: {SIMPLE_CIRCUIT_MAX_TIME}ms)"


def test_qft_parse_time():
    """Test that QFT circuit parses in acceptable time."""
    quyaml_string = """
    circuit: qft
    qubits: q[3]
    ops:
      - h 0
      - cphase(pi/2) 1 0
      - h 1
      - cphase(pi/4) 2 0
      - cphase(pi/2) 2 1
      - h 2
      - swap 0 2
    """
    avg_time = measure_parse_time(quyaml_string)
    assert avg_time < SIMPLE_CIRCUIT_MAX_TIME, \
        f"QFT parsing too slow: {avg_time:.2f}ms (max: {SIMPLE_CIRCUIT_MAX_TIME}ms)"


def test_large_circuit_parse_time():
    """Test that larger circuits parse in acceptable time."""
    # 10-qubit circuit with many gates
    quyaml_string = """
    circuit: large_circuit
    qubits: q[10]
    ops:
      - h 0
      - h 1
      - h 2
      - h 3
      - h 4
      - h 5
      - h 6
      - h 7
      - h 8
      - h 9
      - cx 0 1
      - cx 1 2
      - cx 2 3
      - cx 3 4
      - cx 4 5
      - cx 5 6
      - cx 6 7
      - cx 7 8
      - cx 8 9
      - barrier
      - h 0
      - h 1
      - h 2
      - h 3
      - h 4
      - h 5
      - h 6
      - h 7
      - h 8
      - h 9
    """
    avg_time = measure_parse_time(quyaml_string, iterations=50)  # Fewer iterations for large circuit
    assert avg_time < COMPLEX_CIRCUIT_MAX_TIME, \
        f"Large circuit parsing too slow: {avg_time:.2f}ms (max: {COMPLEX_CIRCUIT_MAX_TIME}ms)"


def test_optimized_vs_original_syntax_performance():
    """Test that optimized syntax doesn't significantly impact parse time."""
    original_syntax = """
    circuit: test
    qreg: q[2]
    instructions:
      - h q[0]
      - cx q[0], q[1]
    """
    
    optimized_syntax = """
    circuit: test
    qubits: q[2]
    ops:
      - h 0
      - cx 0 1
    """
    
    original_time = measure_parse_time(original_syntax)
    optimized_time = measure_parse_time(optimized_syntax)

    # Optimized should be within 60% of original (not significantly slower)
    time_difference = abs(optimized_time - original_time) / original_time * 100
    assert time_difference < 60, \
        f"Optimized syntax significantly different performance: {time_difference:.1f}% difference"


def test_parameter_evaluation_performance():
    """Test that parameter evaluation doesn't cause excessive overhead."""
    # Circuit with complex parameter expressions
    quyaml_string = """
    circuit: complex_params
    qubits: q[4]
    params: {a: 0.5, b: 1.2, c: 0.8}
    ops:
      - ry(2*$a + $b) 0
      - rx($b * pi / 4) 1
      - cphase($a + $b * $c) 0 1
      - ry($a * pi) 2
      - rx($b * 2) 3
    """
    avg_time = measure_parse_time(quyaml_string)
    assert avg_time < COMPLEX_CIRCUIT_MAX_TIME, \
        f"Complex parameter evaluation too slow: {avg_time:.2f}ms (max: {COMPLEX_CIRCUIT_MAX_TIME}ms)"


if __name__ == "__main__":
    # Run performance tests and print results
    print("=" * 60)
    print("QuYAML Parser Performance Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("Bell State", test_bell_state_parse_time),
        ("GHZ State", test_ghz_state_parse_time),
        ("Parameterized QAOA", test_parameterized_circuit_parse_time),
        ("QFT", test_qft_parse_time),
        ("Large Circuit (10 qubits)", test_large_circuit_parse_time),
        ("Optimized vs Original", test_optimized_vs_original_syntax_performance),
        ("Complex Parameters", test_parameter_evaluation_performance),
    ]
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}: PASS")
        except AssertionError as e:
            print(f"✗ {name}: FAIL - {e}")
        except Exception as e:
            print(f"✗ {name}: ERROR - {e}")
    
    print()
    print("=" * 60)
    print("Performance Summary")
    print("=" * 60)
    print(f"Simple circuit threshold: < {SIMPLE_CIRCUIT_MAX_TIME}ms")
    print(f"Complex circuit threshold: < {COMPLEX_CIRCUIT_MAX_TIME}ms")
