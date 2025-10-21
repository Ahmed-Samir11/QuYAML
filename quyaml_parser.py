import yaml
from qiskit import QuantumCircuit
import re
import numpy as np

class QuYamlError(Exception):
    """Custom exception for QuYAML parsing errors."""
    pass

def _apply_instruction(qc: QuantumCircuit, inst_str: str, params: dict, line_num: int):
    """Parses and applies a single QuYAML instruction string."""
    if not isinstance(inst_str, str):
        raise QuYamlError(f"Instruction on line {line_num} is not a string.")

    # Extract gate name and parameter expression if present
    # Use a more robust regex to handle nested parentheses
    first_paren = inst_str.find('(')
    if first_paren != -1:
        gate_part = inst_str[:first_paren].strip().lower()
        # Find matching closing parenthesis
        paren_count = 0
        closing_paren = -1
        for i in range(first_paren, len(inst_str)):
            if inst_str[i] == '(':
                paren_count += 1
            elif inst_str[i] == ')':
                paren_count -= 1
                if paren_count == 0:
                    closing_paren = i
                    break
        
        if closing_paren == -1:
            raise QuYamlError(f"Unmatched parentheses in instruction on line {line_num}.")
        
        param_expr = inst_str[first_paren+1:closing_paren]
        rest = inst_str[closing_paren+1:].strip()
        parts = [gate_part] + rest.split()
    else:
        parts = inst_str.split()
        gate_part = parts[0].lower()
        param_expr = None
    
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
        
        # Handle parameterized gates
        if param_expr:
            gate_name = gate_part
            
            # Check for undefined parameters first
            param_names = re.findall(r'\$(\w+)', param_expr)
            for pname in param_names:
                if pname not in params:
                    raise QuYamlError(f"Parameter '{pname}' not defined in parameters block.")
            
            # Evaluate the parameter expression
            # Replace parameters with their values
            eval_expr = param_expr
            for param_name, param_value in params.items():
                eval_expr = eval_expr.replace(f'${param_name}', str(param_value))
            
            # Replace pi with np.pi
            eval_expr = eval_expr.replace('pi', 'np.pi')
            
            # Evaluate the expression
            try:
                angle = eval(eval_expr, {"__builtins__": None}, {"np": np})
            except Exception as e:
                raise QuYamlError(f"Could not evaluate parameter expression '{param_expr}': {e}")

            if gate_name == 'rx':
                qc.rx(angle, q_indices[0])
            elif gate_name == 'ry':
                qc.ry(angle, q_indices[0])
            elif gate_name == 'cphase':
                qc.cp(angle, q_indices[0], q_indices[1])
            else:
                raise QuYamlError(f"Unknown parameterized gate '{gate_name}' on line {line_num}.")
        
        # Handle non-parameterized gates
        else:
            gate_name = gate_part
            if gate_name == 'h':
                qc.h(q_indices[0])
            elif gate_name == 'x':
                qc.x(q_indices[0])
            elif gate_name == 'cx':
                qc.cx(q_indices[0], q_indices[1])
            elif gate_name == 'swap':
                qc.swap(q_indices[0], q_indices[1])
            elif gate_name == 'barrier':
                qc.barrier()
            elif gate_name == 'measure':
                qc.measure_all()
            else:
                raise QuYamlError(f"Unknown gate '{gate_name}' on line {line_num}.")

    except Exception as e:
        if isinstance(e, QuYamlError): raise e
        raise QuYamlError(f"Could not parse instruction '{inst_str}' on line {line_num}. Details: {e}")

def parse_quyaml_to_qiskit(quyaml_string: str) -> QuantumCircuit:
    """
    Parses a QuYAML string with an extended specification into a Qiskit QuantumCircuit object.
    """
    try:
        data = yaml.safe_load(quyaml_string)
        if not isinstance(data, dict):
            raise QuYamlError("Top level of QuYAML must be a dictionary.")
    except yaml.YAMLError as e:
        raise QuYamlError(f"Invalid YAML syntax: {e}")

    circuit_name = data.get('circuit', 'my_circuit')
    params = data.get('parameters', {})
    
    def get_reg_size(reg_str):
        if not reg_str or not isinstance(reg_str, str): return 0
        match = re.search(r'\[(\d+)\]', reg_str)
        return int(match.group(1)) if match else 0
        
    q_size = get_reg_size(data.get('qreg'))
    c_size = get_reg_size(data.get('creg'))
    
    if q_size == 0:
        raise QuYamlError("QuYAML must define at least one quantum register (qreg).")
        
    qc = QuantumCircuit(q_size, c_size, name=circuit_name)

    instructions = data.get('instructions', [])
    if not isinstance(instructions, list):
        raise QuYamlError("'instructions' must be a list.")
        
    for i, inst_str in enumerate(instructions):
        _apply_instruction(qc, inst_str, params, line_num=i+1)
        
    return qc
