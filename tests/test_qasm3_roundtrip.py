import yaml
from qiskit import qasm3

from quyaml_parser import parse_quyaml_to_qiskit
from qiskit_bridge import qc_to_quyaml_dict, circuits_structurally_equal


def test_roundtrip_quyaml_to_qasm3_and_back_simple():
    yml = """
    version: 0.4
    circuit: rt_simple
    qubits: q[2]
    ops:
      - h 0
      - cx 0 1
    """
    qc1 = parse_quyaml_to_qiskit(yml)
    q3 = qasm3.dumps(qc1)
    qc2 = qasm3.loads(q3)
    ok, msg = circuits_structurally_equal(qc1, qc2)
    assert ok, msg


def test_roundtrip_qasm3_to_quyaml_and_back_simple():
    q3 = """OPENQASM 3.0;
include \"stdgates.inc\";
qubit[2] q;
h q[0];
cx q[0], q[1];
"""
    qc1 = qasm3.loads(q3)
    data = qc_to_quyaml_dict(qc1)
    yml = yaml.safe_dump(data, sort_keys=False)
    qc2 = parse_quyaml_to_qiskit(yml)
    ok, msg = circuits_structurally_equal(qc1, qc2)
    assert ok, msg


def test_roundtrip_with_parameters_rx_ry():
    yml = """
    version: 0.4
    circuit: rt_params
    qubits: q[2]
    ops:
      - rx(1.57079632679) 0
      - ry(0.25) 1
    """
    qc1 = parse_quyaml_to_qiskit(yml)
    q3 = qasm3.dumps(qc1)
    qc2 = qasm3.loads(q3)
    ok, msg = circuits_structurally_equal(qc1, qc2, atol=1e-9)
    assert ok, msg
