import pytest
from quyaml import parse_quyaml_to_qiskit, QuYamlError


def test_reject_yaml_anchors_aliases_tags():
    # Anchors & aliases
    bad = """
    circuit: test
    qreg: &q q[2]
    creg: c[2]
    instructions:
      - h q[0]
      - cx q[0], q[1]
    use: *q
    """
    with pytest.raises(QuYamlError):
        parse_quyaml_to_qiskit(bad)

    # Custom tags
    bad_tag = """
    circuit: test
    !custom_tag qubits: q[2]
    ops: [h 0]
    """
    with pytest.raises(QuYamlError):
        parse_quyaml_to_qiskit(bad_tag)
