import pytest
from qiskit import QuantumCircuit
from quyaml_parser import parse_quyaml_job, parse_quyaml_to_qiskit, QuYamlJob

def test_job_manifest_parsing():
    yaml_str = """
    version: 0.4
    metadata:
      name: "Test Job"
      author: "Copilot"
    execution:
      backend: "ibmq_qasm_simulator"
      shots: 1024
    circuit:
      qubits: q[2]
      bits: c[2]
      ops:
        - h 0
        - cx 0 1
        - measure: {q: 0, c: 0}
        - measure: {q: 1, c: 1}
    post_processing:
      - type: "histogram"
    """
    
    job = parse_quyaml_job(yaml_str)
    assert isinstance(job, QuYamlJob)
    assert job.metadata['name'] == "Test Job"
    assert job.execution['shots'] == 1024
    assert isinstance(job.circuit, QuantumCircuit)
    assert job.circuit.num_qubits == 2
    assert job.circuit.num_clbits == 2
    assert len(job.post_processing) == 1

def test_legacy_parsing_via_job_parser():
    yaml_str = """
    version: 0.4
    qubits: q[2]
    bits: c[2]
    ops:
      - h 0
    """
    job = parse_quyaml_job(yaml_str)
    assert isinstance(job.circuit, QuantumCircuit)
    assert job.circuit.num_qubits == 2
    assert job.metadata == {}

def test_wrapper_compatibility():
    yaml_str = """
    version: 0.4
    metadata:
      name: "Wrapper Test"
    circuit:
      qubits: q[1]
      bits: c[1]
      ops:
        - x 0
    """
    qc = parse_quyaml_to_qiskit(yaml_str)
    assert isinstance(qc, QuantumCircuit)
    assert qc.num_qubits == 1
