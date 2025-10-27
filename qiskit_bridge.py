from __future__ import annotations

from typing import Any, Dict, List, Tuple

from qiskit import QuantumCircuit


def simplify_circuit(qc: QuantumCircuit) -> List[Tuple[str, List[int], List[float]]]:
    """Return a simplified gate sequence: (name, qubit_indices, params_as_floats_or_str).
    Parameters are converted to float when possible; otherwise stringified.
    """
    seq: List[Tuple[str, List[int], List[float]]] = []
    for instr in qc.data:
        op = instr.operation
        name = op.name
        qubits = [qc.find_bit(q).index for q in instr.qubits]
        params: List[Any] = []
        for p in op.params:
            try:
                params.append(float(p))
            except Exception:
                params.append(str(p))
        seq.append((name, qubits, params))
    return seq


def qc_to_quyaml_dict(qc: QuantumCircuit) -> Dict[str, Any]:
    """Convert a QuantumCircuit to a minimal QuYAML v0.4 dictionary.

    Supported ops mapping:
      - h, x, cx, swap, barrier
      - reset
      - measure (structured form with q/c indices)
      - rx(angle), ry(angle)
      - cp(angle) -> cphase(angle)
    Unknown gates are stringified with their name and qubit indices (best-effort).
    """
    ops: List[Any] = []
    for instr in qc.data:
        op = instr.operation
        name = op.name
        qidx = [qc.find_bit(q).index for q in instr.qubits]
        if name in {"h", "x", "cx", "swap", "barrier"}:
            if name == "barrier":
                ops.append("barrier")
            elif name in {"cx", "swap"}:
                ops.append(f"{name} {qidx[0]} {qidx[1]}")
            else:
                ops.append(f"{name} {qidx[0]}")
        elif name == "reset":
            ops.append({"reset": {"q": int(qidx[0])}})
        elif name == "measure":
            # Expect one qubit and one clbit
            if instr.clbits:
                cidx = [qc.find_bit(c).index for c in instr.clbits][0]
                ops.append({"measure": {"q": int(qidx[0]), "c": int(cidx)}})
            else:
                # fallback to measure all
                ops.append("measure")
        elif name == "rx" and op.params:
            angle = op.params[0]
            try:
                angle = float(angle)
            except Exception:
                angle = str(angle)
            ops.append(f"rx({angle}) {qidx[0]}")
        elif name == "ry" and op.params:
            angle = op.params[0]
            try:
                angle = float(angle)
            except Exception:
                angle = str(angle)
            ops.append(f"ry({angle}) {qidx[0]}")
        elif name == "cp" and op.params:
            angle = op.params[0]
            try:
                angle = float(angle)
            except Exception:
                angle = str(angle)
            ops.append(f"cphase({angle}) {qidx[0]} {qidx[1]}")
        else:
            # Best-effort fallback
            ops.append(f"{name} {' '.join(str(i) for i in qidx)}")

    data: Dict[str, Any] = {
        "version": "0.4",
        "circuit": qc.name or "converted",
        "qubits": f"q[{qc.num_qubits}]",
    }
    if qc.num_clbits > 0:
        data["bits"] = f"c[{qc.num_clbits}]"
    data["ops"] = ops
    return data


def circuits_structurally_equal(qc1: QuantumCircuit, qc2: QuantumCircuit, *, atol: float = 1e-9) -> Tuple[bool, str]:
    """Compare two circuits by structure: qubits/cbits count and gate sequence.
    Returns (equal, message). Message explains first difference.
    """
    if qc1.num_qubits != qc2.num_qubits or qc1.num_clbits != qc2.num_clbits:
        return False, f"qubits/cbits mismatch: ({qc1.num_qubits},{qc1.num_clbits}) vs ({qc2.num_qubits},{qc2.num_clbits})"

    s1 = simplify_circuit(qc1)
    s2 = simplify_circuit(qc2)
    if len(s1) != len(s2):
        return False, f"op count mismatch: {len(s1)} vs {len(s2)}"
    for i, ((n1, q1, p1), (n2, q2, p2)) in enumerate(zip(s1, s2)):
        if n1 != n2 or q1 != q2:
            return False, f"op[{i}] name/qubits mismatch: {n1}{q1} vs {n2}{q2}"
        if len(p1) != len(p2):
            return False, f"op[{i}] param count mismatch: {len(p1)} vs {len(p2)}"
        for j, (a, b) in enumerate(zip(p1, p2)):
            try:
                if abs(float(a) - float(b)) > atol:
                    return False, f"op[{i}] param[{j}] mismatch: {a} vs {b}"
            except Exception:
                if str(a) != str(b):
                    return False, f"op[{i}] param[{j}] mismatch: {a} vs {b}"
    return True, "equal"


def diff_circuits(qc1: QuantumCircuit, qc2: QuantumCircuit, *, atol: float = 1e-9) -> Dict[str, Any]:
    """Produce a machine-friendly structural diff between two circuits.
    Returns a dict with keys: equal (bool), reason (str), and optionally details.
    """
    out: Dict[str, Any] = {"equal": True, "reason": "equal"}
    if qc1.num_qubits != qc2.num_qubits or qc1.num_clbits != qc2.num_clbits:
        out.update({
            "equal": False,
            "reason": "qubits/cbits mismatch",
            "left": {"qubits": qc1.num_qubits, "cbits": qc1.num_clbits},
            "right": {"qubits": qc2.num_qubits, "cbits": qc2.num_clbits},
        })
        return out

    s1 = simplify_circuit(qc1)
    s2 = simplify_circuit(qc2)
    if len(s1) != len(s2):
        out.update({
            "equal": False,
            "reason": "op count mismatch",
            "left_count": len(s1),
            "right_count": len(s2),
        })
        return out

    for i, ((n1, q1, p1), (n2, q2, p2)) in enumerate(zip(s1, s2)):
        if n1 != n2 or q1 != q2:
            out.update({
                "equal": False,
                "reason": "op mismatch",
                "index": i,
                "left": {"name": n1, "qubits": q1, "params": p1},
                "right": {"name": n2, "qubits": q2, "params": p2},
            })
            return out
        if len(p1) != len(p2):
            out.update({
                "equal": False,
                "reason": "param count mismatch",
                "index": i,
                "left_params": p1,
                "right_params": p2,
            })
            return out
        for j, (a, b) in enumerate(zip(p1, p2)):
            try:
                if abs(float(a) - float(b)) > atol:
                    out.update({
                        "equal": False,
                        "reason": "param mismatch",
                        "index": i,
                        "param_index": j,
                        "left_param": a,
                        "right_param": b,
                    })
                    return out
            except Exception:
                if str(a) != str(b):
                    out.update({
                        "equal": False,
                        "reason": "param mismatch",
                        "index": i,
                        "param_index": j,
                        "left_param": a,
                        "right_param": b,
                    })
                    return out
    return out
