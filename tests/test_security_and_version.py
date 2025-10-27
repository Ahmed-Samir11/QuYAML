import pytest
from quyaml_parser import parse_quyaml_to_qiskit, QuYamlError


def test_safe_param_eval_basic_pi():
    text = """
    circuit: t1
    qubits: q[1]
    ops:
      - rx(pi/2) 0
    """
    qc = parse_quyaml_to_qiskit(text)
    # should parse without exception
    assert qc.num_qubits == 1


def test_safe_param_eval_with_params():
    text = """
    circuit: t2
    qubits: q[1]
    params: {theta: 0.5}
    ops:
      - ry(2*$theta + pi/2) 0
    """
    qc = parse_quyaml_to_qiskit(text)
    assert qc.num_qubits == 1


def test_version_gate_accepts_known():
    for ver in ("0.2", "0.3"):
        text = f"""
        version: {ver}
        circuit: v_ok
        qubits: q[1]
        ops:
          - h 0
        """
        qc = parse_quyaml_to_qiskit(text)
        assert qc.num_qubits == 1


def test_version_gate_rejects_unknown():
    text = """
    version: 9.9
    circuit: bad
    qubits: q[1]
    ops:
      - h 0
    """
    with pytest.raises(QuYamlError, match="Unsupported QuYAML version"):
        parse_quyaml_to_qiskit(text)
