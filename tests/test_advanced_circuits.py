import pytest
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes
from quyaml_parser import parse_quyaml_to_qiskit

def test_qml_zzfeaturemap():
    """
    Metamorphic Test for QML:
    Parses a QuYAML definition of a simple feature map and verifies its
    unitary matches a manually constructed reference circuit.
    """
    quyaml_string = """
    circuit: SimpleFeatureMap
    metadata:
      type: QML Feature Map
      description: A 2-qubit feature map with parameterized rotations
    qreg: q[2]
    parameters:
      x0: 0.5
      x1: 1.2
    instructions:
      - h q[0]
      - h q[1]
      - barrier
      - rx(2 * $x0) q[0]
      - rx(2 * $x1) q[1]
      - barrier
      - cx q[0], q[1]
      - ry(2 * $x0 * $x1) q[1]
      - cx q[0], q[1]
    """
    # 1. Create from QuYAML
    parsed_qc = parse_quyaml_to_qiskit(quyaml_string)
    
    # 2. Create reference circuit programmatically
    x0, x1 = 0.5, 1.2
    reference_qc = QuantumCircuit(2)
    reference_qc.h([0, 1])
    reference_qc.barrier()
    reference_qc.rx(2 * x0, 0)
    reference_qc.rx(2 * x1, 1)
    reference_qc.barrier()
    reference_qc.cx(0, 1)
    reference_qc.ry(2 * x0 * x1, 1)
    reference_qc.cx(0, 1)

    # 3. Compare their unitaries
    assert Operator(parsed_qc).equiv(Operator(reference_qc))

def test_optimization_qaoa_ansatz():
    """
    Metamorphic Test for Quantum Optimization:
    Parses a simple QAOA ansatz (p=1) and verifies its unitary.
    """
    quyaml_string = """
    circuit: QAOA_Ansatz_p1
    metadata:
      type: QAOA Ansatz
      description: A simple 2-qubit QAOA ansatz with p=1.
    qreg: q[2]
    parameters:
      gamma: 0.5
      beta: 1.2
    instructions:
      # Initial state preparation
      - h q[0]
      - h q[1]
      - barrier
      # Cost Hamiltonian Layer
      - cx q[0], q[1]
      - ry(2 * $gamma) q[1]
      - cx q[0], q[1]
      - barrier
      # Mixer Hamiltonian Layer
      - rx(2 * $beta) q[0]
      - rx(2 * $beta) q[1]
    """
    # 1. Create from QuYAML
    parsed_qc = parse_quyaml_to_qiskit(quyaml_string)

    # 2. Create reference from Qiskit library (or manually)
    gamma, beta = 0.5, 1.2
    reference_qc = QuantumCircuit(2)
    reference_qc.h([0, 1])
    reference_qc.barrier()
    reference_qc.cx(0, 1)
    reference_qc.ry(2 * gamma, 1)
    reference_qc.cx(0, 1)
    reference_qc.barrier()
    reference_qc.rx(2 * beta, 0)
    reference_qc.rx(2 * beta, 1)

    # 3. Compare their unitaries
    assert Operator(parsed_qc).equiv(Operator(reference_qc))
