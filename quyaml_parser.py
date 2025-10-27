import yaml
from qiskit import QuantumCircuit
import re
import numpy as np
import ast
from typing import Any, Dict

try:
    # Optional safe evaluator; used if available
    from asteval import Interpreter as _AEInterpreter  # type: ignore
except Exception:  # pragma: no cover
    _AEInterpreter = None

class QuYamlError(Exception):
    """Custom exception for QuYAML parsing errors."""
    pass


def _safe_eval_expression(expr: str, params: Dict[str, Any]) -> float:
    """Safely evaluate a small arithmetic expression used in parameterized gates.

    Security notes:
    - Replaces `$name` occurrences with their numeric values from params.
    - Supports a tiny subset of arithmetic and constants (pi, e) by default.
    - If `asteval` is available, use it with a tightly constrained symbol table.
      Otherwise, fall back to a minimal AST walker that only permits
      numeric constants, +, -, *, /, ** and parentheses, and names {pi, e}.
    """
    # 1) Substitute parameters like $theta -> value
    eval_expr = expr
    for param_name, param_value in params.items():
        eval_expr = eval_expr.replace(f"${param_name}", str(param_value))

    # 2) If asteval is available, prefer it with a restricted symtable
    if _AEInterpreter is not None:
        sym = {
            # constants
            "pi": float(np.pi),
            "e": float(np.e),
            # common funcs (extend conservatively as needed)
            "sin": np.sin,
            "cos": np.cos,
            "tan": np.tan,
            "sqrt": np.sqrt,
            "exp": np.exp,
            "log": np.log,
            "abs": abs,
        }
        ae = _AEInterpreter(symtable=sym, minimal=True)
        out = ae(eval_expr)
        if len(ae.error) > 0:
            raise QuYamlError(f"Could not evaluate parameter expression '{expr}': {ae.error[0].get_error()}")
        try:
            return float(out)
        except Exception as e:
            raise QuYamlError(f"Parameter expression '{expr}' did not evaluate to a number: {e}")

    # 3) Fallback: very small AST-based evaluator (no function calls)
    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd,
        ast.Load, ast.Name, ast.Mod,
    )

    def _eval(node):
        if not isinstance(node, allowed_nodes):
            raise QuYamlError(f"Unsupported expression element in '{expr}' ({type(node).__name__}).")
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Num):  # Py<3.8
            return float(node.n)
        if isinstance(node, ast.Constant):  # Py3.8+
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise QuYamlError(f"Non-numeric constant in '{expr}'.")
        if isinstance(node, ast.Name):
            if node.id == 'pi':
                return float(np.pi)
            if node.id == 'e':
                return float(np.e)
            raise QuYamlError(f"Unknown symbol '{node.id}' in '{expr}'.")
        if isinstance(node, ast.UnaryOp):
            val = _eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +val
            if isinstance(node.op, ast.USub):
                return -val
            raise QuYamlError(f"Unsupported unary operator in '{expr}'.")
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow):
                return left ** right
            if isinstance(node.op, ast.Mod):
                return left % right
            raise QuYamlError(f"Unsupported binary operator in '{expr}'.")
        raise QuYamlError(f"Unsupported expression in '{expr}'.")

    try:
        tree = ast.parse(eval_expr, mode='eval')
        value = _eval(tree)
        return float(value)
    except QuYamlError:
        raise
    except Exception as e:  # pragma: no cover
        raise QuYamlError(f"Could not evaluate parameter expression '{expr}': {e}")

def _reject_yaml_advanced(quyaml_string: str) -> None:
    """Reject dangerous/advanced YAML features: anchors (&), aliases (*), and custom tags (!).

    This is a conservative scan that ignores comments and looks for unescaped
    tokens in the content region of each line. If any are found, raise QuYamlError.
    """
    for raw in quyaml_string.splitlines():
        # strip comments
        line = raw.split('#', 1)[0]
        if not line.strip():
            continue
        # Look for anchors (&name), aliases (*name), or tags (!tag)
        if re.search(r"(^|\s)&[A-Za-z0-9_-]+", line):
            raise QuYamlError("YAML anchors (&name) are not allowed in QuYAML for safety.")
        if re.search(r"(^|\s)\*[A-Za-z0-9_-]+", line):
            raise QuYamlError("YAML aliases (*name) are not allowed in QuYAML for safety.")
        if re.search(r"(^|\s)!\S+", line):
            raise QuYamlError("YAML custom tags (!tag) are not allowed in QuYAML for safety.")

def _apply_instruction(qc: QuantumCircuit, inst_str: str, params: dict, line_num: int, cond=None):
    """Parses and applies a single QuYAML instruction string.
    
    Supports both original and optimized syntax:
    - Original: - h q[0]  or  - cx q[0], q[1]
    - Optimized: - h 0    or  - cx 0 1
    """
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
        """Parse qubit indices from either 'q[0]' or '0' format."""
        indices = []
        for s in target_strings:
            # Check if it's in q[n] format
            match = re.search(r'\[(\d+)\]', s)
            if match:
                idx = int(match.group(1))
            else:
                # Try to parse as plain integer (optimized format)
                try:
                    idx = int(s.replace(',', ''))
                except ValueError:
                    raise QuYamlError(f"Invalid qubit index '{s}' on line {line_num}. Use 'q[n]' or 'n' format.")
            
            if idx >= qc.num_qubits:
                raise QuYamlError(f"Qubit index {idx} out of bounds (circuit has {qc.num_qubits} qubits) on line {line_num}.")
            indices.append(idx)
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
            
            # Evaluate the parameter expression safely
            angle = _safe_eval_expression(param_expr, params)

            if gate_name == 'rx':
                ret = qc.rx(angle, q_indices[0])
            elif gate_name == 'ry':
                ret = qc.ry(angle, q_indices[0])
            elif gate_name == 'cphase':
                ret = qc.cp(angle, q_indices[0], q_indices[1])
            else:
                raise QuYamlError(f"Unknown parameterized gate '{gate_name}' on line {line_num}.")
            if cond is not None and 'ret' in locals() and ret is not None:
                creg, cval = cond
                try:
                    # Some Qiskit versions return InstructionSet without c_if; fallback to last op
                    if hasattr(ret, 'c_if'):
                        ret.c_if(creg, cval)
                    else:
                        last = qc.data[-1]
                        last.operation.c_if(creg, cval)
                except Exception as e:
                    raise QuYamlError(f"Failed to apply conditional to gate on line {line_num}: {e}")
        
        # Handle non-parameterized gates
        else:
            gate_name = gate_part
            ret = None
            if gate_name == 'h':
                ret = qc.h(q_indices[0])
            elif gate_name == 'x':
                ret = qc.x(q_indices[0])
            elif gate_name == 'cx':
                ret = qc.cx(q_indices[0], q_indices[1])
            elif gate_name == 'swap':
                ret = qc.swap(q_indices[0], q_indices[1])
            elif gate_name == 'barrier':
                qc.barrier()
            elif gate_name == 'measure':
                qc.measure_all()
            else:
                raise QuYamlError(f"Unknown gate '{gate_name}' on line {line_num}.")
            if cond is not None and ret is not None:
                creg, cval = cond
                try:
                    if hasattr(ret, 'c_if'):
                        ret.c_if(creg, cval)
                    else:
                        last = qc.data[-1]
                        last.operation.c_if(creg, cval)
                except Exception as e:
                    raise QuYamlError(f"Failed to apply conditional to gate on line {line_num}: {e}")

    except Exception as e:
        if isinstance(e, QuYamlError): raise e
        raise QuYamlError(f"Could not parse instruction '{inst_str}' on line {line_num}. Details: {e}")

def parse_quyaml_to_qiskit(quyaml_string: str) -> QuantumCircuit:
    """
    Parses a QuYAML string with an extended specification into a Qiskit QuantumCircuit object.
    
    Supports both original and optimized field names:
    - Original: qreg, creg, parameters, instructions
    - Optimized: qubits, bits, params, ops
    """
    try:
        _reject_yaml_advanced(quyaml_string)
        data = yaml.safe_load(quyaml_string)
        if not isinstance(data, dict):
            raise QuYamlError("Top level of QuYAML must be a dictionary.")
    except yaml.YAMLError as e:
        raise QuYamlError(f"Invalid YAML syntax: {e}")

    # Version gate (optional for now; accept 0.2/0.3, reject others)
    version = data.get('version')
    if version is not None and str(version) not in {'0.2', '0.3'}:
        raise QuYamlError(f"Unsupported QuYAML version '{version}'. Supported versions: 0.2, 0.3.")

    circuit_name = data.get('circuit', 'my_circuit')
    
    # Support both 'parameters' and 'params' (optimized)
    params = data.get('params', data.get('parameters', {}))
    
    def get_reg_size(reg_str):
        if not reg_str or not isinstance(reg_str, str): return 0
        match = re.search(r'\[(\d+)\]', reg_str)
        return int(match.group(1)) if match else 0
    
    # Support both field names
    q_size = get_reg_size(data.get('qubits', data.get('qreg')))
    c_size = get_reg_size(data.get('bits', data.get('creg')))
    
    if q_size == 0:
        raise QuYamlError("QuYAML must define at least one quantum register (qreg/qubits).")
        
    qc = QuantumCircuit(q_size, c_size, name=circuit_name)

    # Support both 'instructions' and 'ops' (optimized)
    instructions = data.get('ops', data.get('instructions', []))
    if not isinstance(instructions, list):
        raise QuYamlError("'instructions'/'ops' must be a list.")

    def _parse_if_block(block: dict, start_line: int):
        cond_str = block.get('cond')
        then_ops = block.get('then', [])
        else_ops = block.get('else', [])
        if not isinstance(then_ops, list) or (else_ops is not None and not isinstance(else_ops, list)):
            raise QuYamlError(f"'if' block then/else must be lists (line {start_line}).")
        if qc.num_clbits == 0:
            raise QuYamlError("Conditional requires classical bits; define 'bits: c[n]' or 'creg'.")

        creg = qc.cregs[0] if qc.cregs else None
        if creg is None:
            raise QuYamlError("No classical register available for conditions.")

        # Supported conditions:
        # 1) Single bit: c[i] == 0/1
        # 2) Full-register equality: c == <int> (e.g., 3, 0b101, 0xA)
        then_val = None
        single_bit = False
        s = str(cond_str) if cond_str is not None else ''
        m_bit = re.match(r"^\s*c\[(\d+)\]\s*==\s*([01])\s*$", s)
        if m_bit:
            single_bit = True
            bit_idx = int(m_bit.group(1))
            bit_val = int(m_bit.group(2))
            if bit_idx >= qc.num_clbits:
                raise QuYamlError(f"Condition references c[{bit_idx}] but circuit has {qc.num_clbits} bits.")
            then_val = (1 << bit_idx) if bit_val == 1 else 0
        else:
            m_reg = re.match(r"^\s*c\s*==\s*(0b[01_]+|0x[0-9a-fA-F_]+|\d+)\s*$", s)
            if m_reg:
                lit = m_reg.group(1).replace('_', '')
                try:
                    then_val = int(lit, 0)
                except Exception:
                    raise QuYamlError(f"Invalid integer literal in condition on line {start_line}.")
                max_val = (1 << qc.num_clbits)
                if then_val < 0 or then_val >= max_val:
                    raise QuYamlError(f"Condition value {then_val} doesn't fit in {qc.num_clbits} classical bits.")
            else:
                raise QuYamlError(
                    f"Unsupported cond syntax in 'if' (line {start_line}). Use 'c[i] == 0/1' or 'c == <int>'."
                )

        # Build THEN (and optional ELSE) using dynamic-circuit blocks.
        # Prefer builder contexts when available; otherwise fall back to qc.if_else(true_body, false_body).
        try:
            if else_ops:
                if hasattr(qc, 'else_'):
                    with qc.if_test((creg, then_val)):
                        for j, sub in enumerate(then_ops):
                            if isinstance(sub, str):
                                _apply_instruction(qc, sub, params, line_num=start_line)
                            else:
                                raise QuYamlError("Nested structured ops inside 'then' are not yet supported.")
                    with qc.else_():
                        for j, sub in enumerate(else_ops):
                            if isinstance(sub, str):
                                _apply_instruction(qc, sub, params, line_num=start_line)
                            else:
                                raise QuYamlError("Nested structured ops inside 'else' are not yet supported.")
                else:
                    # Fallback: construct body circuits and use if_else API
                    from qiskit import QuantumCircuit as _QC
                    t_body = _QC(qc.num_qubits, qc.num_clbits)
                    f_body = _QC(qc.num_qubits, qc.num_clbits)
                    for sub in then_ops:
                        if isinstance(sub, str):
                            _apply_instruction(t_body, sub, params, line_num=start_line)
                        else:
                            raise QuYamlError("Nested structured ops inside 'then' are not yet supported.")
                    for sub in else_ops:
                        if isinstance(sub, str):
                            _apply_instruction(f_body, sub, params, line_num=start_line)
                        else:
                            raise QuYamlError("Nested structured ops inside 'else' are not yet supported.")
                    qc.if_else((creg, then_val), t_body, f_body, qc.qubits, qc.clbits)
            else:
                # Only THEN branch
                if hasattr(qc, 'if_test'):
                    with qc.if_test((creg, then_val)):
                        for j, sub in enumerate(then_ops):
                            if isinstance(sub, str):
                                _apply_instruction(qc, sub, params, line_num=start_line)
                            else:
                                raise QuYamlError("Nested structured ops inside 'then' are not yet supported.")
                else:
                    from qiskit import QuantumCircuit as _QC
                    t_body = _QC(qc.num_qubits, qc.num_clbits)
                    for sub in then_ops:
                        if isinstance(sub, str):
                            _apply_instruction(t_body, sub, params, line_num=start_line)
                        else:
                            raise QuYamlError("Nested structured ops inside 'then' are not yet supported.")
                    qc.if_else((creg, then_val), t_body, None, qc.qubits, qc.clbits)
        except Exception as e:
            raise QuYamlError(f"Failed to build conditional block: {e}")

    for i, inst in enumerate(instructions):
        # Support string instructions (existing) and structured dict ops for v0.3 features
        if isinstance(inst, str):
            _apply_instruction(qc, inst, params, line_num=i+1)
        elif isinstance(inst, dict):
            if 'measure' in inst:
                # Structured mid-circuit measure: {'measure': {'q': i, 'c': j}}
                spec = inst['measure']
                if not isinstance(spec, dict) or 'q' not in spec or 'c' not in spec:
                    raise QuYamlError(f"Invalid 'measure' spec on line {i+1}. Expected {{q: int, c: int}}.")
                if qc.num_clbits == 0:
                    raise QuYamlError("Structured measure requires classical bits; define 'bits: c[n]'.")
                q_i = int(spec['q'])
                c_i = int(spec['c'])
                if q_i >= qc.num_qubits or c_i >= qc.num_clbits:
                    raise QuYamlError(f"Measure indices out of bounds on line {i+1}.")
                try:
                    qc.measure(q_i, c_i)
                except Exception as e:
                    raise QuYamlError(f"Failed to apply measure on line {i+1}: {e}")
            elif 'if' in inst:
                block = inst['if']
                if not isinstance(block, dict):
                    raise QuYamlError(f"Invalid 'if' block on line {i+1}.")
                _parse_if_block(block, start_line=i+1)
            else:
                raise QuYamlError(f"Unknown structured op on line {i+1}. Supported: 'measure', 'if'.")
        else:
            raise QuYamlError(f"Instruction on line {i+1} must be string or object.")
        
    return qc
