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
import random
import math

# Ensure repository root is on path when running directly
_HERE = os.path.dirname(__file__)
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import tiktoken
from qiskit import qasm3
from quyaml_parser import parse_quyaml_to_qiskit
from qiskit import QuantumCircuit

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


def circuit_to_qasm3_from_quyaml(quyaml_str: str) -> str:
    """Generate an OpenQASM 3.0 string for the given QuYAML by first
    converting to a Qiskit circuit and then dumping to QASM3.
    """
    qc = parse_quyaml_to_qiskit(quyaml_str)
    return qasm3.dumps(qc)


def json_to_qiskit(json_str: str) -> QuantumCircuit:
    """Decode our compact JSON representation and rebuild a Qiskit circuit.

    Note: This aims to be a fairer comparison by including the reconstruction
    step (string -> dict -> QuantumCircuit), not just JSON decode time.
    """
    data = json.loads(json_str)
    nq = int(data.get("qubits", 0) or 0)
    nc = int(data.get("cbits", 0) or 0)
    qc = QuantumCircuit(nq, nc)

    for gate in data.get("gates", []):
        name = gate.get("name")
        q = gate.get("qubits", [])
        p = gate.get("params", [])
        if name == "h":
            qc.h(q[0])
        elif name == "x":
            qc.x(q[0])
        elif name == "cx":
            qc.cx(q[0], q[1])
        elif name == "swap":
            qc.swap(q[0], q[1])
        elif name == "barrier":
            qc.barrier()
        elif name in ("cp", "cphase"):
            qc.cp(float(p[0]), q[0], q[1])
        elif name == "rx":
            qc.rx(float(p[0]), q[0])
        elif name == "ry":
            qc.ry(float(p[0]), q[0])
        elif name == "measure":
            # Only handle simple measure if classical bits exist
            if qc.num_clbits > 0 and len(q) == 1:
                qc.measure(q[0], 0)
        # else: ignore unknowns silently for fairness
    return qc

def qaoa_maxcut_ring_quyaml(p: int, n: int = 6) -> str:
    edges = [(i, (i + 1) % n) for i in range(n)]
    params = []
    for layer in range(1, p + 1):
        params.append((f"g{layer}", round(0.2 + 0.2 * layer, 3)))
        params.append((f"b{layer}", round(0.5 + 0.2 * layer, 3)))
    params_str = ", ".join(f"{k}: {v}" for k, v in params)

    lines = [
        f"circuit: qaoa_maxcut_p{p}",
        f"qubits: q[{n}]",
        f"params: {{{params_str}}}",
        "ops:",
    ]
    for i in range(n):
        lines.append(f"  - h {i}")
    for layer in range(1, p + 1):
        for u, v in edges:
            lines.append(f"  - cphase(2*$g{layer}) {u} {v}")
        for i in range(n):
            lines.append(f"  - rx(2*$b{layer}) {i}")
    return "\n".join(lines)


def random_entangling_layers_quyaml(n: int = 6, depth: int = 4, seed: int = 7) -> str:
    rnd = random.Random(seed)
    lines = [f"circuit: random_layers_{n}_{depth}", f"qubits: q[{n}]", "ops:"]
    for _ in range(depth):
        for i in range(n):
            a = round(rnd.random() * math.pi, 3)
            b = round(rnd.random() * math.pi, 3)
            lines.append(f"  - rx({a}) {i}")
            lines.append(f"  - ry({b}) {i}")
        for i in range(n):
            j = (i + 1) % n
            lines.append(f"  - cx {i} {j}")
    return "\n".join(lines)


def shallow_quantum_volume_like_quyaml(n: int = 6, layers: int = 2, seed: int = 11) -> str:
    rnd = random.Random(seed)
    lines = [f"circuit: qv_like_{n}_{layers}", f"qubits: q[{n}]", "ops:"]
    for _ in range(layers):
        perm = list(range(n))
        rnd.shuffle(perm)
        for k in range(0, n - 1, 2):
            a, b = perm[k], perm[k + 1]
            r1 = round(rnd.random() * math.pi, 3)
            r2 = round(rnd.random() * math.pi, 3)
            r3 = round(rnd.random() * math.pi, 3)
            lines.append(f"  - cx {a} {b}")
            lines.append(f"  - ry({r1}) {a}")
            lines.append(f"  - rx({r2}) {b}")
            lines.append(f"  - cx {a} {b}")
            lines.append(f"  - ry({r3}) {a}")
        lines.append("  - barrier")
    return "\n".join(lines)


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
    "QAOA Max-Cut p=5 (ring-6)": {
        "quyaml": qaoa_maxcut_ring_quyaml(p=5, n=6),
    },
    "Random entangling layers (n=6, d=4)": {
        "quyaml": random_entangling_layers_quyaml(n=6, depth=4, seed=7),
    },
    "Quantum-volume-like (n=6, layers=2)": {
        "quyaml": shallow_quantum_volume_like_quyaml(n=6, layers=2, seed=11),
    },
}


print("=" * 80)
print("PENNYLANE-STYLE BENCHMARK: QuYAML vs Qiskit JSON")
print("=" * 80)

rows = []
unsupported = 0
for name, data in TESTS.items():
    qy_val = data.get("quyaml")
    if qy_val is None:
        print("\n--", name)
        print("  QuYAML: UNSUPPORTED (requires mid-circuit measure/control-flow)")
        unsupported += 1
        continue
    qy = qy_val.strip()
    js = circuit_to_json_from_quyaml(qy)
    q3 = circuit_to_qasm3_from_quyaml(qy)

    qy_tokens = count_tokens(qy)
    js_tokens = count_tokens(js)
    q3_tokens = count_tokens(q3)

    qy_ms = measure_time(parse_quyaml_to_qiskit, qy)
    js_ms = measure_time(json.loads, js)
    js_rebuild_ms = measure_time(json_to_qiskit, js)
    q3_ms = measure_time(lambda s: qasm3.loads(s), q3)

    rows.append((name, qy_tokens, js_tokens, q3_tokens, qy_ms, js_ms, js_rebuild_ms, q3_ms))

    print("\n--", name)
    print(
        f"  Tokens -> QuYAML: {qy_tokens:5d} | JSON: {js_tokens:5d} | QASM3: {q3_tokens:5d} | "
        f"QuYAML vs JSON: {((js_tokens-qy_tokens)/js_tokens*100):+.1f}% | QuYAML vs QASM3: {((q3_tokens-qy_tokens)/q3_tokens*100):+.1f}%"
    )
    print(
        f"  Parse  -> QuYAML: {qy_ms:6.3f} ms | JSON-decode: {js_ms:6.3f} ms | "
        f"JSON-rebuild: {js_rebuild_ms:6.3f} ms | QASM3-parse: {q3_ms:6.3f} ms"
    )

avg_qy = sum(r[1] for r in rows) / len(rows)
avg_js = sum(r[2] for r in rows) / len(rows)
avg_q3 = sum(r[3] for r in rows) / len(rows)
avg_qy_ms = sum(r[4] for r in rows) / len(rows)
avg_js_ms = sum(r[5] for r in rows) / len(rows)
avg_js_rebuild_ms = sum(r[6] for r in rows) / len(rows)
avg_q3_ms = sum(r[7] for r in rows) / len(rows)

print("\n" + "-" * 80)
print("AVERAGE TOKENS (across supported tests):")
print(f"  QuYAML: {avg_qy:.1f}")
print(f"  JSON  : {avg_js:.1f}")
print(f"  QASM3 : {avg_q3:.1f}")
print(f"  QuYAML vs JSON: {(avg_js-avg_qy)/avg_js*100:+.1f}% more efficient than JSON")
print(f"  QuYAML vs QASM3: {(avg_q3-avg_qy)/avg_q3*100:+.1f}% more efficient than QASM3")
print("\nAVERAGE PARSE TIMES:")
print(f"  QuYAML parse   : {avg_qy_ms:.3f} ms")
print(f"  JSON decode    : {avg_js_ms:.3f} ms")
print(f"  JSON rebuild   : {avg_js_rebuild_ms:.3f} ms")
print(f"  QASM3 parse    : {avg_q3_ms:.3f} ms")
if unsupported:
    print(f"\nNote: {unsupported} test(s) omitted due to unsupported mid-circuit control in QuYAML v0.2.")
