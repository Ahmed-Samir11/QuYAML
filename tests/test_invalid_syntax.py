import pytest
from quyaml_parser import parse_quyaml_to_qiskit, QuYamlError

def test_invalid_yaml_syntax():
    """Tests that malformed YAML raises an error."""
    quyaml_string = "qreg: q[2]\n instructions: - h q[0" # Missing closing bracket
    with pytest.raises(QuYamlError, match="Invalid YAML syntax"):
        parse_quyaml_to_qiskit(quyaml_string)

def test_unknown_gate():
    """Tests that an unknown gate raises a custom error."""
    quyaml_string = """
    qreg: q[1]
    instructions:
      - my_custom_gate q[0]
    """
    with pytest.raises(QuYamlError, match="Unknown gate 'my_custom_gate'"):
        parse_quyaml_to_qiskit(quyaml_string)

def test_wrong_argument_count():
    """Tests that the wrong number of arguments for a gate raises an error."""
    quyaml_string = """
    qreg: q[2]
    instructions:
      - h q[0], q[1]
    """
    with pytest.raises(QuYamlError, match="H gate requires 1 qubit"):
        parse_quyaml_to_qiskit(quyaml_string)

def test_out_of_bounds_qubit():
    """Tests that a qubit index outside the register size raises an error."""
    quyaml_string = """
    qreg: q[2]
    instructions:
      - h q[5]
    """
    with pytest.raises(QuYamlError, match="Invalid or out-of-bounds qubit index"):
        parse_quyaml_to_qiskit(quyaml_string)

def test_no_qreg_defined():
    """Tests that a missing qreg definition raises an error."""
    quyaml_string = "circuit: NoQReg"
    with pytest.raises(QuYamlError, match="must define at least one quantum register"):
        parse_quyaml_to_qiskit(quyaml_string)
