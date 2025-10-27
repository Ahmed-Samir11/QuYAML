import pytest
from qiskit import QuantumCircuit

from quyaml_parser import parse_quyaml_to_qiskit, QuYamlError


def test_reset_string_and_structured():
    yml = """
    version: 0.4
    qubits: q[2]
    bits: c[1]
    ops:
      - h 0
      - reset 0
      - {reset: {q: 1}}
      - measure
    """
    qc = parse_quyaml_to_qiskit(yml)
    assert isinstance(qc, QuantumCircuit)
    names = [inst.operation.name for inst in qc.data]
    # Two resets should be present, plus measure
    assert names.count('reset') >= 2
    assert any(n == 'measure' for n in names)


def test_if_composite_condition_and():
    yml = """
    version: 0.4
    qubits: q[2]
    bits: c[2]
    ops:
      - {measure: {q: 0, c: 0}}
      - {measure: {q: 1, c: 1}}
      - if:
          cond: "c[0] == 1 && c[1] == 1"
          then:
            - x 0
          else:
            - h 0
    """
    qc = parse_quyaml_to_qiskit(yml)
    names = [inst.operation.name for inst in qc.data]
    assert any(name == 'if_else' for name in names)


def test_if_composite_condition_or():
    yml = """
    version: 0.4
    qubits: q[2]
    bits: c[2]
    ops:
      - {measure: {q: 0, c: 0}}
      - if:
          cond: "c[0] == 1 || c == 0b10"
          then:
            - x 1
          else:
            - h 1
    """
    qc = parse_quyaml_to_qiskit(yml)
    names = [inst.operation.name for inst in qc.data]
    assert any(name == 'if_else' for name in names)


def test_while_loop_atom_condition():
    yml = """
    version: 0.4
    qubits: q[2]
    bits: c[1]
    ops:
      - {measure: {q: 0, c: 0}}
      - while:
          cond: "c == 0b0"
          body:
            - x 0
            - {measure: {q: 0, c: 0}}
          max_iter: 2
    """
    qc = parse_quyaml_to_qiskit(yml)
    names = [inst.operation.name for inst in qc.data]
    # Either a while_loop op exists (newer Qiskit) or conditional unrolled via if_else
    assert any(n in ('while_loop', 'if_else') for n in names)


def test_for_loop_range():
    yml = """
    version: 0.4
    qubits: q[1]
    ops:
      - for:
          range: [0, 3]
          body:
            - h 0
    """
    qc = parse_quyaml_to_qiskit(yml)
    names = [inst.operation.name for inst in qc.data]
    # Either a for_loop op exists, or 3 h gates were unrolled
    if any(n == 'for_loop' for n in names):
        assert True
    else:
        assert names.count('h') >= 3


def test_condition_bit_out_of_range():
    yml = """
    version: 0.4
    qubits: q[1]
    bits: c[1]
    ops:
      - if:
          cond: "c[1] == 1"
          then: [x 0]
    """
    with pytest.raises(QuYamlError, match="Condition references c\[1\]"):
        parse_quyaml_to_qiskit(yml)


def test_condition_value_too_large():
    yml = """
    version: 0.4
    qubits: q[1]
    bits: c[1]
    ops:
      - if:
          cond: "c == 0b10"
          then: [x 0]
    """
    with pytest.raises(QuYamlError, match="doesn't fit in 1 classical bits"):
        parse_quyaml_to_qiskit(yml)
