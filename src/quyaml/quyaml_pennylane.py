"""
QuYAML -> PennyLane utilities.

Provides a thin adapter that parses a QuYAML string into a Qiskit QuantumCircuit
(using the existing parser) and then converts it to a PennyLane quantum function
via qml.from_qiskit, if PennyLane and the PennyLane-Qiskit plugin are installed.

This keeps PennyLane as an optional dependency.
"""
from typing import Callable, Optional

from .quyaml_parser import parse_quyaml_to_qiskit

try:
    import pennylane as qml
except Exception as _e:  # pragma: no cover
    qml = None
    _import_err = _e
else:
    _import_err = None


def parse_quyaml_to_pennylane(quyaml_string: str, measurements=None) -> Callable:
    """
    Convert a QuYAML string into a PennyLane template (quantum function).

    Args:
        quyaml_string: The QuYAML circuit definition.
        measurements: Optional PennyLane measurements to pass through to qml.from_qiskit.

    Returns:
        A PennyLane quantum function (callable) suitable for use inside a QNode.

    Raises:
        RuntimeError: If PennyLane is not installed or the PennyLane-Qiskit plugin is missing.
        Exception: Any exception thrown by the underlying QuYAML or conversion layers.
    """
    if qml is None:
        raise RuntimeError(
            "PennyLane is not available. Please install it first: pip install pennylane pennylane-qiskit\n"
            f"Original import error: {_import_err}"
        )

    qc = parse_quyaml_to_qiskit(quyaml_string)
    # Convert to a PennyLane template using official interop
    return qml.from_qiskit(qc, measurements)


def _run_cli():  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="Convert .quyaml to a PennyLane template and optionally run it.")
    parser.add_argument("input", help="Path to .quyaml file")
    parser.add_argument("--wires", type=int, default=None, help="Number of wires to allocate (defaults to circuit qubits)")
    parser.add_argument("--measure", action="store_true", help="Run a simple QNode with expval(Z(0)) and print the result")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    qc = parse_quyaml_to_qiskit(text)
    tmpl = qml.from_qiskit(qc)
    n = args.wires or qc.num_qubits

    print(f"Converted {args.input} -> PennyLane template (wires inferred: {n})")

    if args.measure:
        dev = qml.device("default.qubit", wires=n)

        @qml.qnode(dev)
        def pl_circuit():
            tmpl(wires=list(range(n)))
            return qml.expval(qml.Z(0))

        print("Result expval(Z(0)):", pl_circuit())


if __name__ == "__main__":  # pragma: no cover
    if qml is None:
        raise RuntimeError(
            "PennyLane is not available. Please install: pip install pennylane pennylane-qiskit"
        )
    _run_cli()
