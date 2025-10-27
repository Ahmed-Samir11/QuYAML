"""
QuYAML -> PennyLane utilities.

Provides a thin adapter that parses a QuYAML string into a Qiskit QuantumCircuit
(using the existing parser) and then converts it to a PennyLane quantum function
via qml.from_qiskit, if PennyLane and the PennyLane-Qiskit plugin are installed.

This keeps PennyLane as an optional dependency.
"""
from typing import Callable, Optional

from quyaml_parser import parse_quyaml_to_qiskit

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
