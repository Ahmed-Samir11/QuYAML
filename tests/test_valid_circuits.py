import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from quyaml_parser import parse_quyaml_to_qiskit

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
    assert qc.data[0].operation.name == 'h'
    assert qc.data[1].operation.name == 'cx'

def test_parse_ghz_state():
    """Tests parsing a valid 3-qubit GHZ State circuit."""
    quyaml_string = """
    circuit: GHZState
    qreg: q[3]
    instructions:
      - h q[0]
      - cx q[0], q[1]
      - cx q[0], q[2]
    """
    qc = parse_quyaml_to_qiskit(quyaml_string)
    assert isinstance(qc, QuantumCircuit)
    assert qc.num_qubits == 3
    assert len(qc.data) == 3

# Metamorphic Test: Compare parsed circuit to a reference implementation
def test_bell_state_unitary_is_correct():
    """
    Metamorphic Test:
    Ensures the unitary matrix of the parsed QuYAML Bell State circuit
    is equivalent to a programmatically generated one.
    """
    quyaml_string = """
    circuit: BellState
    qreg: q[2]
    instructions:
      - h q[0]
      - cx q[0], q[1]
    """
    # 1. Create circuit from QuYAML
    parsed_qc = parse_quyaml_to_qiskit(quyaml_string)
    parsed_op = Operator(parsed_qc)

    # 2. Create reference circuit programmatically
    reference_qc = QuantumCircuit(2)
    reference_qc.h(0)
    reference_qc.cx(0, 1)
    reference_op = Operator(reference_qc)

    # 3. Assert they are equivalent
    assert parsed_op.equiv(reference_op)
