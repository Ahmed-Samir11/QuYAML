import re
import pytest
from qiskit import QuantumCircuit

from quyaml import parse_quyaml_to_qiskit, QuYamlError


def test_mid_circuit_measure_basic():
    yml = """
    version: 0.3
    qubits: q[2]
    bits: c[2]
    ops:
      - h 0
      - {measure: {q: 0, c: 0}}
      - x 1
    """
    qc = parse_quyaml_to_qiskit(yml)
    assert isinstance(qc, QuantumCircuit)
    # Should have at least one measure in data
    assert any(getattr(inst.operation, 'name', '') == 'measure' for inst in qc.data)
    # h on qubit 0, then structured measure, then x on 1
    names = [inst.operation.name for inst in qc.data]
    assert 'h' in names and 'x' in names and 'measure' in names


def test_if_then_else_single_bit_condition():
    yml = """
    version: 0.3
    qubits: q[2]
    bits: c[2]
    ops:
      - {measure: {q: 0, c: 0}}
      - if:
          cond: "c[0] == 1"
          then:
            - x 1
          else:
            - h 1
    """
    qc = parse_quyaml_to_qiskit(yml)
    # Expect a control-flow op (if_else) to be present
    names = [inst.operation.name for inst in qc.data]
    assert any(name == 'if_else' for name in names)


def test_if_requires_classical_bits():
    yml = """
    version: 0.3
    qubits: q[1]
    ops:
      - if:
          cond: "c[0] == 1"
          then: [x 0]
    """
    with pytest.raises(QuYamlError):
        parse_quyaml_to_qiskit(yml)


def test_full_register_equality_condition():
    yml = """
    version: 0.3
    qubits: q[2]
    bits: c[2]
    ops:
      - {measure: {q: 0, c: 0}}
      - {measure: {q: 1, c: 1}}
      - if:
          cond: "c == 0b11"
          then:
            - x 0
          else:
            - h 0
    """
    qc = parse_quyaml_to_qiskit(yml)
    names = [inst.operation.name for inst in qc.data]
    assert any(name == 'if_else' for name in names)
