import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from quyaml import parse_quyaml_to_qiskit

def test_parse_bell_state():
    """Tests parsing a valid Bell State circuit."""
    quyaml_string = """
    circuit: BellState
    qreg: q[2]
    creg: c[2]
    instructions:
      - h q[0]
      - cx q[0], q[1]
    """
    qc = parse_quyaml_to_qiskit(quyaml_string)
    assert isinstance(qc, QuantumCircuit)
    assert qc.num_qubits == 2
    assert len(qc.data) == 2

def test_bell_state_unitary_is_correct():
    """
    Metamorphic Test: Compares the parsed QuYAML Bell State
    to a programmatically generated one.
    """
    quyaml_string = """
    circuit: BellState
    qreg: q[2]
    instructions:
      - h q[0]
      - cx q[0], q[1]
    """
    parsed_qc = parse_quyaml_to_qiskit(quyaml_string)
    parsed_op = Operator(parsed_qc)

    reference_qc = QuantumCircuit(2)
    reference_qc.h(0)
    reference_qc.cx(0, 1)
    reference_op = Operator(reference_qc)

    assert parsed_op.equiv(reference_op)
