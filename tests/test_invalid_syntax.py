import pytest
from quyaml import parse_quyaml_to_qiskit, QuYamlError

def test_invalid_yaml_syntax():
    """Tests that malformed YAML raises an error."""
    quyaml_string = "qreg: q[2]\n instructions: - h q[0"
    with pytest.raises(QuYamlError, match="Invalid YAML syntax"):
        parse_quyaml_to_qiskit(quyaml_string)

def test_unknown_gate():
    """Tests that an unknown gate raises a custom error."""
    quyaml_string = "qreg: q[1]\ninstructions:\n  - my_gate q[0]"
    with pytest.raises(QuYamlError, match="Unknown gate 'my_gate'"):
        parse_quyaml_to_qiskit(quyaml_string)

def test_out_of_bounds_qubit():
    """Tests that a qubit index outside the register size raises an error."""
    quyaml_string = "qreg: q[2]\ninstructions:\n  - h q[5]"
    with pytest.raises(QuYamlError, match="out of bounds"):
        parse_quyaml_to_qiskit(quyaml_string)

def test_undefined_parameter():
    """Tests that using an undefined parameter raises an error."""
    quyaml_string = """
    qreg: q[1]
    parameters:
      theta: 1.57
    instructions:
      - rx($alpha) q[0]
    """
    with pytest.raises(QuYamlError, match="Parameter 'alpha' not defined"):
        parse_quyaml_to_qiskit(quyaml_string)
