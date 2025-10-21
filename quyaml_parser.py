import yaml
from qiskit import QuantumCircuit
import re
import numpy as np

class QuYamlError(Exception):
    """Custom exception for QuYAML parsing errors."""
    pass

def parse_quyaml_to_qiskit(quyaml_string: str) -> QuantumCircuit:
    """
    Parses a QuYAML string into a Qiskit QuantumCircuit object.
    Raises QuYamlError for parsing or conversion failures.
    """
    try:
        data = yaml.safe_load(quyaml_string)
        if not isinstance(data, dict):
            raise QuYamlError("Top level of QuYAML must be a dictionary.")
    except yaml.YAMLError as e:
        raise QuYamlError(f"Invalid YAML syntax: {e}")

    circuit_name = data.get('circuit', 'my_circuit')
    
    def get_reg_size(reg_str):
        if not reg_str or not isinstance(reg_str, str): return 0
        match = re.search(r'\[(\d+)\]', reg_str)
        return int(match.group(1)) if match else 0
        
    q_size = get_reg_size(data.get('qreg'))
    c_size = get_reg_size(data.get('creg'))
    
    if q_size == 0:
        raise QuYamlError("QuYAML must define at least one quantum register (e.g., qreg: q[1])")
        
    qc = QuantumCircuit(q_size, c_size, name=circuit_name)

    instructions = data.get('instructions', [])
    if not isinstance(instructions, list):
        raise QuYamlError("'instructions' must be a list.")
        
    for i, inst_str in enumerate(instructions):
        apply_instruction(qc, inst_str, line_num=i+1)
        
    return qc

def apply_instruction(qc: QuantumCircuit, inst_str: str, line_num: int):
    """
    Parses a single QuYAML instruction string and applies it to the circuit.
    """
    if not isinstance(inst_str, str):
        raise QuYamlError(f"Instruction on line {line_num} is not a string.")

    parts = inst_str.split()
    gate = parts[0].lower()
    
    def get_indices(target_strings):
        indices = []
        for s in target_strings:
            match = re.search(r'\[(\d+)\]', s)
            if match and int(match.group(1)) < qc.num_qubits:
                indices.append(int(match.group(1)))
            else:
                raise QuYamlError(f"Invalid or out-of-bounds qubit index in '{s}' on line {line_num}.")
        return indices

    targets = [p.replace(',', '') for p in parts[1:]]
    
    try:
        q_indices = get_indices(targets)
        if gate == 'h':
            if len(q_indices) != 1: raise QuYamlError("H gate requires 1 qubit.")
            qc.h(q_indices[0])
        elif gate == 'x':
            if len(q_indices) != 1: raise QuYamlError("X gate requires 1 qubit.")
            qc.x(q_indices[0])
        elif gate == 'cx':
            if len(q_indices) != 2: raise QuYamlError("CX gate requires 2 qubits.")
            qc.cx(q_indices[0], q_indices[1])
        elif gate == 'swap':
            if len(q_indices) != 2: raise QuYamlError("SWAP gate requires 2 qubits.")
            qc.swap(q_indices[0], q_indices[1])
        elif gate.startswith('cphase'):
            if len(q_indices) != 2: raise QuYamlError("cphase gate requires 2 qubits.")
            angle_str = re.search(r'\((.*?)\)', gate).group(1)
            angle_map = {'pi/2': np.pi / 2, 'pi/4': np.pi / 4, 'pi': np.pi}
            angle = angle_map.get(angle_str, float(angle_str))
            qc.cp(angle, q_indices[0], q_indices[1])
        elif gate == 'measure':
            qc.measure_all()
        else:
            raise QuYamlError(f"Unknown gate '{gate}' on line {line_num}.")
    except Exception as e:
        if isinstance(e, QuYamlError): raise e
        raise QuYamlError(f"Could not parse instruction '{inst_str}' on line {line_num}. Details: {e}")
