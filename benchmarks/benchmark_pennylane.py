"""
Benchmark QuYAML vs Qiskit JSON on PennyLane-style challenging circuits.

- Circuits chosen to reflect complex PennyLane demos:
  * QAOA Max-Cut (p=3) on a 6-node ring
  * QFT (5 qubits)
  * Grover (4 qubits, oracle |1111>)
  * Phase Estimation (3 control + 1 target)

For each circuit we:
  - Count GPT-4 tokens for QuYAML string vs generated Qiskit JSON
  - Measure parse time: QuYAML (full parse) vs JSON (json.loads only)

Note: JSON 'parse time' measures JSON decode only, mirroring previous benchmarks.
"""
import json
import time
from typing import Dict
import os
import sys

# Ensure repository root is on path when running directly
_HERE = os.path.dirname(__file__)
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import tiktoken
from quyaml_parser import parse_quyaml_to_qiskit

encoder = tiktoken.encoding_for_model("gpt-4")


def count_tokens(text: str) -> int:
    return len(encoder.encode(text))


def measure_time(fn, text: str, iters: int = 100) -> float:
    times = []
    for _ in range(iters):
        t0 = time.perf_counter()
        fn(text)
        t1 = time.perf_counter()
        times.append(t1 - t0)
    return sum(times) / len(times) * 1000.0


def circuit_to_json_from_quyaml(quyaml_str: str) -> str:
    qc = parse_quyaml_to_qiskit(quyaml_str)
    data = {
        "circuit": qc.name,
        "qubits": qc.num_qubits,
        "cbits": qc.num_clbits,
        "gates": [],
    }
    for instr in qc.data:
        op = instr.operation
        qidx = [qc.find_bit(q).index for q in instr.qubits]
        params = []
        for p in op.params:
            try:
                params.append(float(p))
            except Exception:
                # fallback to string
                params.append(str(p))
        data["gates"].append({"name": op.name, "qubits": qidx, "params": params})
    return json.dumps(data, separators=(",", ":"))


TESTS: Dict[str, Dict[str, str]] = {
    "QAOA Max-Cut p=3 (ring-6)": {
        "quyaml": """
# p=3 QAOA for Max-Cut on 6-node ring (0-1-2-3-4-5-0)
circuit: qaoa_maxcut_p3
qubits: q[6]
params: {g1: 0.4, b1: 0.7, g2: 0.6, b2: 0.9, g3: 0.8, b3: 1.1}
ops:
  # init
  - h 0
  - h 1
  - h 2
  - h 3
  - h 4
  - h 5
  # layer 1 (cost)
  - cphase(2*$g1) 0 1
  - cphase(2*$g1) 1 2
  - cphase(2*$g1) 2 3
  - cphase(2*$g1) 3 4
  - cphase(2*$g1) 4 5
  - cphase(2*$g1) 5 0
  # layer 1 (mixer)
  - rx(2*$b1) 0
  - rx(2*$b1) 1
  - rx(2*$b1) 2
  - rx(2*$b1) 3
  - rx(2*$b1) 4
  - rx(2*$b1) 5
  # layer 2 (cost)
  - cphase(2*$g2) 0 1
  - cphase(2*$g2) 1 2
  - cphase(2*$g2) 2 3
  - cphase(2*$g2) 3 4
  - cphase(2*$g2) 4 5
  - cphase(2*$g2) 5 0
  # layer 2 (mixer)
  - rx(2*$b2) 0
  - rx(2*$b2) 1
  - rx(2*$b2) 2
  - rx(2*$b2) 3
  - rx(2*$b2) 4
  - rx(2*$b2) 5
  # layer 3 (cost)
  - cphase(2*$g3) 0 1
  - cphase(2*$g3) 1 2
  - cphase(2*$g3) 2 3
  - cphase(2*$g3) 3 4
  - cphase(2*$g3) 4 5
  - cphase(2*$g3) 5 0
  # layer 3 (mixer)
  - rx(2*$b3) 0
  - rx(2*$b3) 1
  - rx(2*$b3) 2
  - rx(2*$b3) 3
  - rx(2*$b3) 4
  - rx(2*$b3) 5
"""
    },
    "QFT (5 qubits)": {
        "quyaml": """
circuit: qft5
qubits: q[5]
ops:
  - h 0
  - cphase(pi/2) 1 0
  - cphase(pi/4) 2 0
  - cphase(pi/8) 3 0
  - cphase(pi/16) 4 0
  - h 1
  - cphase(pi/2) 2 1
  - cphase(pi/4) 3 1
  - cphase(pi/8) 4 1
  - h 2
  - cphase(pi/2) 3 2
  - cphase(pi/4) 4 2
  - h 3
  - cphase(pi/2) 4 3
  - h 4
  - swap 0 4
  - swap 1 3
"""
    },
    "Grover (4q oracle=1111)": {
        "quyaml": """
circuit: grover4
qubits: q[4]
ops:
  - h 0
  - h 1
  - h 2
  - h 3
  # oracle for |1111>
  - x 0
  - x 1
  - x 2
  - x 3
  - h 3
  - cx 2 3
  - cx 1 3
  - cx 0 3
  - h 3
  - x 0
  - x 1
  - x 2
  - x 3
  # diffuser
  - h 0
  - h 1
  - h 2
  - h 3
  - x 0
  - x 1
  - x 2
  - x 3
  - h 3
  - cx 2 3
  - cx 1 3
  - cx 0 3
  - h 3
  - x 0
  - x 1
  - x 2
  - x 3
  - h 0
  - h 1
  - h 2
  - h 3
"""
    },
    "Phase Estimation (3+1)": {
        "quyaml": """
circuit: qpe
qubits: q[4]
ops:
  - h 0
  - h 1
  - h 2
  - x 3
  - cx 0 3
  - cx 1 3
  - cx 2 3
  - h 0
  - cphase(-pi/2) 1 0
  - h 1
  - cphase(-pi/4) 2 0
  - cphase(-pi/2) 2 1
  - h 2
"""
    },
}


print("=" * 80)
print("PENNYLANE-STYLE BENCHMARK: QuYAML vs Qiskit JSON")
print("=" * 80)

rows = []
for name, data in TESTS.items():
    qy = data["quyaml"].strip()
    js = circuit_to_json_from_quyaml(qy)

    qy_tokens = count_tokens(qy)
    js_tokens = count_tokens(js)

    qy_ms = measure_time(parse_quyaml_to_qiskit, qy)
    js_ms = measure_time(json.loads, js)

    rows.append((name, qy_tokens, js_tokens, qy_ms, js_ms))

    print("\n--", name)
    print(f"  Tokens -> QuYAML: {qy_tokens:5d} | JSON: {js_tokens:5d} | delta: {((js_tokens-qy_tokens)/js_tokens*100):+.1f}% vs JSON")
    print(f"  Parse  -> QuYAML: {qy_ms:6.3f} ms | JSON-decode: {js_ms:6.3f} ms")

avg_qy = sum(r[1] for r in rows) / len(rows)
avg_js = sum(r[2] for r in rows) / len(rows)

print("\n" + "-" * 80)
print("AVERAGE TOKENS:")
print(f"  QuYAML: {avg_qy:.1f}")
print(f"  JSON  : {avg_js:.1f}")
print(f"  QuYAML vs JSON: {(avg_js-avg_qy)/avg_js*100:+.1f}% more efficient than JSON")
