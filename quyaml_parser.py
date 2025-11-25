import yaml
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter, ParameterExpression
import re
import numpy as np
import ast
import os
import json
import time
from typing import Any, Dict, Union, List

try:
    # Optional safe evaluator; used if available
    from asteval import Interpreter as _AEInterpreter  # type: ignore
except Exception:  # pragma: no cover
    _AEInterpreter = None

class QuYamlError(Exception):
    """Custom exception for QuYAML parsing errors."""
    pass

# Parser configuration for v0.4
# Default posture during transition: accept legacy (0.2/0.3) and missing version
# to keep existing content and tests working. Projects can call the setter below
# to disable legacy support and require explicit version: 0.4.
ALLOW_LEGACY_VERSIONS = True

def set_allow_legacy_versions(flag: bool) -> None:
    """Enable accepting legacy QuYAML versions (0.2/0.3) for migration."""
    global ALLOW_LEGACY_VERSIONS
    ALLOW_LEGACY_VERSIONS = bool(flag)


def _safe_eval_expression(expr: str, params: Dict[str, Any]) -> Union[float, ParameterExpression]:
    """Safely evaluate a small arithmetic expression used in parameterized gates.

    Supports both numeric evaluation and Qiskit Parameter objects (Native Parameterization).
    """
    # 1) Prepare expression for AST parsing by replacing $var with var
    # We use a regex to find $identifier and replace it with the identifier name
    # This assumes identifiers are valid Python names.
    
    # Map of available symbols (constants + params)
    symbols = {
        "pi": np.pi,
        "e": np.e,
    }
    symbols.update(params)

    def replace_var(match):
        name = match.group(1)
        if name not in params:
             # If it's not in params, we can't evaluate it.
             # But maybe it's a constant like pi?
             # If not, it's an error.
             pass
        return name

    # Replace $name with name. 
    # Note: This simple replacement might be risky if 'name' is a keyword or invalid,
    # but QuYAML vars are usually simple.
    try:
        # We only replace $var if var is in params to avoid accidental replacement of other things?
        # No, QuYAML syntax requires $ for variables.
        eval_expr = re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', replace_var, expr)
    except Exception as e:
        raise QuYamlError(f"Failed to parse variable syntax in '{expr}': {e}")

    # 2) Fallback: very small AST-based evaluator (no function calls)
    # Accept only modern AST nodes.
    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd,
        ast.Load, ast.Name, ast.Mod,
    )

    def _eval(node):
        if not isinstance(node, allowed_nodes):
            raise QuYamlError(f"Unsupported expression element in '{expr}' ({type(node).__name__}).")
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise QuYamlError(f"Non-numeric constant in '{expr}'.")
        if isinstance(node, ast.Name):
            if node.id in symbols:
                return symbols[node.id]
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
        raise QuYamlError(f"Unexpected node type {type(node).__name__} in '{expr}'.")

    try:
        tree = ast.parse(eval_expr, mode='eval')
        return _eval(tree.body)
    except SyntaxError:
        raise QuYamlError(f"Invalid expression syntax: '{expr}'")
    except Exception as e:
        if isinstance(e, QuYamlError): raise e
        raise QuYamlError(f"Evaluation failed for '{expr}': {e}")
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

def _enforce_limits(quyaml_string: str, max_bytes: int = 1_000_000, max_nesting: int = 50) -> None:
    """Guardrails: limit file size and approximate nesting depth."""
    if len(quyaml_string.encode('utf-8')) > max_bytes:
        raise QuYamlError("QuYAML document too large.")
    depth = 0
    for line in quyaml_string.splitlines():
        if not line.strip():
            continue
        leading = len(line) - len(line.lstrip(' '))
        level = leading // 2
        depth = max(depth, level)
        if depth > max_nesting:
            raise QuYamlError("QuYAML nesting too deep.")

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
        if re.search(r"(^|\s)<<\s*:\s*", line):
            raise QuYamlError("YAML merge keys (<<:) are not allowed in QuYAML for safety.")

def _parse_condition_string(cond_str: str, qc: QuantumCircuit):
    """Parse condition string into boolean AST supporting atoms and &&/||.
    Atoms: c[i] == 0|1, c == <int>. No parentheses support.
    Returns nested tuples: ('atom', ('reg', value)) or ('and'|'or', left, right).
    """
    s = cond_str.strip()
    if not s:
        raise QuYamlError("Empty condition string.")

    def parse_atom(token: str):
        m_bit = re.fullmatch(r"c\[(\d+)\]\s*==\s*([01])", token.strip())
        if m_bit:
            bit_idx = int(m_bit.group(1))
            bit_val = int(m_bit.group(2))
            if bit_idx >= qc.num_clbits:
                raise QuYamlError(f"Condition references c[{bit_idx}] but circuit has {qc.num_clbits} bits.")
            then_val = (1 << bit_idx) if bit_val == 1 else 0
            return ("atom", ("reg", then_val))
        m_reg = re.fullmatch(r"c\s*==\s*(0b[01_]+|0x[0-9a-fA-F_]+|\d+)", token.strip())
        if m_reg:
            lit = m_reg.group(1).replace('_', '')
            try:
                then_val = int(lit, 0)
            except Exception:
                raise QuYamlError("Invalid integer literal in condition.")
            max_val = (1 << qc.num_clbits)
            if then_val < 0 or then_val >= max_val:
                raise QuYamlError(f"Condition value {then_val} doesn't fit in {qc.num_clbits} classical bits.")
            return ("atom", ("reg", then_val))
        raise QuYamlError("Unsupported condition atom. Use 'c[i] == 0/1' or 'c == <int>'.")

    # Split by || then &&; left-associative
    or_parts = [p for p in re.split(r"\|\|", s) if p.strip()]
    def parse_and(expr: str):
        and_parts = [p for p in re.split(r"&&", expr) if p.strip()]
        node = parse_atom(and_parts[0])
        for part in and_parts[1:]:
            node = ("and", node, parse_atom(part))
        return node
    node = parse_and(or_parts[0])
    for part in or_parts[1:]:
        node = ("or", node, parse_and(part))
    return node

def _emit_conditional(qc: QuantumCircuit, cond_ast, then_ops, else_ops, params, start_line: int):
    """Lower boolean AST to nested if/else using equality on full register.
    This supports atoms and limited &&/|| composition via nesting.
    """
    creg = qc.cregs[0] if qc.cregs else None
    if creg is None:
        raise QuYamlError("Conditional requires classical bits; define 'bits: c[n]'.")

    def apply_ops(op_list):
        for sub in op_list:
            if isinstance(sub, str):
                _apply_instruction(qc, sub, params, line_num=start_line)
            elif isinstance(sub, dict):
                if 'measure' in sub:
                    spec = sub['measure']
                    qc.measure(int(spec['q']), int(spec['c']))
                elif 'reset' in sub:
                    qc.reset(int(sub['reset']['q']))
                else:
                    raise QuYamlError("Nested structured op not supported here (only measure/reset).")
            else:
                raise QuYamlError("Invalid op in conditional body.")

    kind = cond_ast[0]
    if kind == 'atom':
        _, (rk, val) = cond_ast
        if rk != 'reg':
            raise QuYamlError("Unsupported condition kind.")
        if else_ops:
            if hasattr(qc, 'if_test') and hasattr(qc, 'else_'):
                with qc.if_test((creg, val)):
                    apply_ops(then_ops)
                with qc.else_():
                    apply_ops(else_ops)
            else:
                from qiskit import QuantumCircuit as _QC
                t_body = _QC(qc.num_qubits, qc.num_clbits)
                f_body = _QC(qc.num_qubits, qc.num_clbits)
                _orig = qc
                qc = t_body; apply_ops(then_ops)
                qc = f_body; apply_ops(else_ops)
                qc = _orig
                qc.if_else((creg, val), t_body, f_body, qc.qubits, qc.clbits)
        else:
            if hasattr(qc, 'if_test'):
                with qc.if_test((creg, val)):
                    apply_ops(then_ops)
            else:
                from qiskit import QuantumCircuit as _QC
                t_body = _QC(qc.num_qubits, qc.num_clbits)
                _orig = qc
                qc = t_body; apply_ops(then_ops)
                qc = _orig
                qc.if_else((creg, val), t_body, None, qc.qubits, qc.clbits)
    elif kind == 'and':
        _, left, right = cond_ast
        # if left then (right ? then_ops : else_ops) else else_ops
        def first_atom(n):
            return first_atom(n[1]) if n[0] in ('and','or') else n
        leaf = first_atom(left)
        _, (rk, val) = leaf
        if hasattr(qc, 'if_test') and hasattr(qc, 'else_'):
            with qc.if_test((creg, val)):
                _emit_conditional(qc, right, then_ops, else_ops, params, start_line)
            if else_ops:
                with qc.else_():
                    apply_ops(else_ops)
        elif hasattr(qc, 'if_test'):
            # Fallback without else_ using manual bodies
            from qiskit import QuantumCircuit as _QC
            t_body = _QC(qc.num_qubits, qc.num_clbits)
            f_body = _QC(qc.num_qubits, qc.num_clbits)
            _orig = qc
            qc = t_body; _emit_conditional(qc, right, then_ops, else_ops, params, start_line)
            qc = f_body; apply_ops(else_ops)
            qc = _orig
            qc.if_else((creg, val), t_body, f_body, qc.qubits, qc.clbits)
        else:
            # No builders: lower to if_else with constructed bodies
            from qiskit import QuantumCircuit as _QC
            t_body = _QC(qc.num_qubits, qc.num_clbits)
            f_body = _QC(qc.num_qubits, qc.num_clbits)
            _orig = qc
            qc = t_body; _emit_conditional(qc, right, then_ops, else_ops, params, start_line)
            qc = f_body; apply_ops(else_ops)
            qc = _orig
            qc.if_else((creg, val), t_body, f_body, qc.qubits, qc.clbits)
    elif kind == 'or':
        _, left, right = cond_ast
        # if left then then_ops else (if right then then_ops else else_ops)
        def first_atom(n):
            return first_atom(n[1]) if n[0] in ('and','or') else n
        leaf = first_atom(left)
        _, (rk, val) = leaf
        if hasattr(qc, 'if_test') and hasattr(qc, 'else_'):
            with qc.if_test((creg, val)):
                apply_ops(then_ops)
            with qc.else_():
                _emit_conditional(qc, right, then_ops, else_ops, params, start_line)
        else:
            # Build bodies manually and use if_else
            from qiskit import QuantumCircuit as _QC
            t_body = _QC(qc.num_qubits, qc.num_clbits)
            f_body = _QC(qc.num_qubits, qc.num_clbits)
            _orig = qc
            qc = t_body; apply_ops(then_ops)
            qc = f_body; _emit_conditional(qc, right, then_ops, else_ops, params, start_line)
            qc = _orig
            qc.if_else((creg, val), t_body, f_body, qc.qubits, qc.clbits)
    else:
        raise QuYamlError("Unsupported condition tree.")

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
            elif gate_name == 'z':
                ret = qc.z(q_indices[0])
            elif gate_name == 'cx':
                ret = qc.cx(q_indices[0], q_indices[1])
            elif gate_name == 'swap':
                ret = qc.swap(q_indices[0], q_indices[1])
            elif gate_name == 'barrier':
                qc.barrier()
            elif gate_name == 'measure':
                qc.measure_all()
            elif gate_name == 'reset':
                ret = qc.reset(q_indices[0])
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
    Parses a QuYAML string into a Qiskit QuantumCircuit object.
    Wrapper around parse_quyaml_job for backward compatibility.
    """
    job = parse_quyaml_job(quyaml_string)
    return job.circuit

class QuYamlResult:
    """
    Represents the result of a QuYAML job execution, ensuring data provenance.
    """
    def __init__(self, job_id: str, backend_name: str, results: Any, metadata: Dict[str, Any] = None):
        self.job_id = job_id
        self.backend_name = backend_name
        self.results = results
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.quyaml_version = '0.4'

    def save(self, filepath: str):
        """Saves the result and metadata to a JSON file."""
        data = {
            "job_id": self.job_id,
            "backend": self.backend_name,
            "timestamp": self.timestamp,
            "quyaml_version": self.quyaml_version,
            "results": str(self.results), # Convert to string if not serializable
            "metadata": self.metadata
        }
        # Try to serialize results properly if it's a dict/list
        try:
            json.dumps(self.results)
            data["results"] = self.results
        except (TypeError, OverflowError):
            pass # Keep as string

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[QuYAML] Result saved to {filepath}")

class QuYamlJob:
    """
    Represents a parsed QuYAML Job, containing the circuit and execution metadata.
    """
    def __init__(self, circuit: QuantumCircuit, metadata: Dict[str, Any] = None, 
                 execution: Dict[str, Any] = None, post_processing: list = None):
        self.circuit = circuit
        self.metadata = metadata or {}
        self.execution = execution or {}
        self.post_processing = post_processing or []

    def execute(self, log_dir: str = "./runs") -> QuYamlResult:
        """
        Executes the job on the resolved backend.
        Handles parameter sweeps and returns a provenance-aware result object.
        Automatically saves the result to log_dir (Opt-Out Provenance).
        """
        backend = self.resolve_backend()
        shots = self.execution.get('shots', 1024)
        
        # Handle Parameter Sweeps
        sweep_config = self.execution.get('parameter_sweep', {})
        circuits_to_run = []
        
        if sweep_config:
            # Native Parameterization Support
            # If the circuit has parameters, we use assign_parameters to generate the batch.
            if self.circuit.parameters:
                # Flatten the sweep: currently supports only one parameter sweep or simple product
                # For MVP: take the first parameter found
                param_name = list(sweep_config.keys())[0]
                values = sweep_config[param_name]
                
                # Find the parameter object in the circuit
                # We need to match the name.
                target_param = None
                for p in self.circuit.parameters:
                    if p.name == param_name:
                        target_param = p
                        break
                
                if target_param:
                    print(f"[QuYAML] Generating {len(values)} circuits for sweep over '{param_name}'...")
                    # Efficiently bind parameters
                    for val in values:
                        bound_qc = self.circuit.assign_parameters({target_param: val})
                        circuits_to_run.append(bound_qc)
                else:
                    print(f"WARNING: Parameter '{param_name}' defined in sweep but not found in circuit parameters. Running base circuit repeatedly.")
                    circuits_to_run = [self.circuit] * len(values)
            else:
                # Fallback if parser didn't produce parameters (should not happen with new parser logic)
                print("WARNING: Circuit has no parameters. Running base circuit repeatedly.")
                pass

        # Default single execution
        if not circuits_to_run:
            circuits_to_run = [self.circuit]

        try:
            # Use run() for now. 
            # Note: Qiskit 2.x primitives (Sampler) are preferred but backend.run is still common for direct access.
            job = backend.run(circuits_to_run, shots=shots)
            result = job.result()
            
            # Create Provenance Record
            q_result = QuYamlResult(
                job_id=job.job_id(),
                backend_name=backend.name,
                results=result.get_counts(),
                metadata={
                    "shots": shots,
                    "sweep": sweep_config,
                    "executed_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
            
            # Auto-Save (Opt-Out Provenance)
            os.makedirs(log_dir, exist_ok=True)
            filename = f"quyaml_job_{job.job_id()}.json"
            filepath = os.path.join(log_dir, filename)
            q_result.save(filepath)
            
            return q_result
            
        except Exception as e:
            raise QuYamlError(f"Execution failed: {e}")

    def resolve_backend(self):
        """
        Resolves the backend for execution using a Zero-Trust approach.
        
        Security Policy:
        - Credentials are NEVER read from the QuYAML file.
        - Credentials must be present in environment variables (IBMQ_TOKEN)
          or in the local ~/.qiskit/qiskit-ibm.json config file.
        
        Returns:
            The Qiskit backend object.
        """
        # Check if credentials are explicitly provided in the file (and warn/ignore)
        if 'token' in self.execution or 'url' in self.execution:
            print("WARNING: Credentials found in QuYAML file. They will be IGNORED per Zero-Trust policy.")
        
        # Try to load QiskitRuntimeService
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
        except ImportError:
            raise QuYamlError("qiskit-ibm-runtime is required for backend resolution.")

        # Initialize service using env vars or local config (Zero-Trust)
        # QiskitRuntimeService automatically looks for IBMQ_TOKEN or local config if no args provided.
        try:
            service = QiskitRuntimeService()
        except Exception as e:
            # Fallback: check for explicit env var if Qiskit didn't pick it up automatically
            token = os.getenv('IBMQ_TOKEN')
            if token:
                service = QiskitRuntimeService(channel='ibm_quantum', token=token)
            else:
                raise QuYamlError(f"Failed to initialize QiskitRuntimeService: {e}. Ensure IBMQ_TOKEN is set or ~/.qiskit/qiskit-ibm.json exists.")

        backend_spec = self.execution.get('backend')
        if not backend_spec:
            raise QuYamlError("No backend specified in execution options.")

        if isinstance(backend_spec, str):
            # Direct backend name
            return service.backend(backend_spec)
        
        elif isinstance(backend_spec, dict):
            # Filter strategy
            min_qubits = backend_spec.get('min_qubits', 1)
            simulator = backend_spec.get('simulator', False)
            strategy = backend_spec.get('strategy', 'least_busy')
            
            filters = lambda b: (
                b.configuration().n_qubits >= min_qubits and
                b.configuration().simulator == simulator and
                b.status().operational
            )
            
            backends = service.backends(filters=filters)
            
            if not backends:
                raise QuYamlError(f"No backend found matching criteria: {backend_spec}")
            
            if strategy == 'least_busy':
                # Find least busy backend
                # Note: This is a simplified implementation. Real least_busy logic might differ.
                selected = min(backends, key=lambda b: b.status().pending_jobs)
            else:
                # Default to first available
                selected = backends[0]
            
            # Result Metadata Logging (Safety)
            print(f"[QuYAML] Dynamic Backend Selection: Strategy='{strategy}' -> Selected='{selected.name}'")
            return selected
        else:
            raise QuYamlError("Invalid backend specification. Must be string or dict.")

def parse_quyaml_job(quyaml_string: str) -> QuYamlJob:
    """
    Parses a QuYAML string into a QuYamlJob object.
    Handles both simple circuit files and Job Manifests.
    """
    try:
        _enforce_limits(quyaml_string)
        _reject_yaml_advanced(quyaml_string)
        try:
            data = yaml.load(quyaml_string, Loader=yaml.CSafeLoader)  # type: ignore[attr-defined]
        except Exception:
            data = yaml.safe_load(quyaml_string)
        if not isinstance(data, dict):
            raise QuYamlError("Top level of QuYAML must be a dictionary.")
    except yaml.YAMLError as e:
        raise QuYamlError(f"Invalid YAML syntax: {e}")

    # Version check
    version = data.get('version')
    if version is None:
        if ALLOW_LEGACY_VERSIONS:
            v = '0.3'
        else:
            raise QuYamlError("Missing required 'version' field (expected '0.4').")
    else:
        v = str(version)
    if v != '0.4':
        if not (ALLOW_LEGACY_VERSIONS and v in {'0.2', '0.3'}):
            extra = ", 0.2, 0.3 (legacy)" if ALLOW_LEGACY_VERSIONS else ""
            raise QuYamlError(f"Unsupported QuYAML version '{version}'. Supported: 0.4{extra}.")

    # Extract metadata and execution options
    metadata = data.get('metadata', {})
    execution = data.get('execution', {})
    post_processing = data.get('post_processing', [])

    # Determine where the circuit is defined
    if 'circuit' in data and isinstance(data['circuit'], dict):
        # Job Manifest mode
        circuit_data = data['circuit']
        # Inherit circuit name from metadata if not present in circuit block
        if 'name' in metadata and 'circuit' not in circuit_data:
             # Note: 'circuit' key in circuit_data is the name of the circuit in legacy parser
             pass 
    else:
        # Legacy/Simple mode: root is the circuit data
        circuit_data = data

    # Identify symbolic parameters from sweep config
    symbolic_params = []
    sweep_config = execution.get('parameter_sweep', {})
    if sweep_config:
        symbolic_params = list(sweep_config.keys())

    # Parse the circuit
    qc = _parse_circuit_data(circuit_data, symbolic_params=symbolic_params)
    
    return QuYamlJob(qc, metadata, execution, post_processing)

def _parse_circuit_data(data: Dict[str, Any], symbolic_params: List[str] = None) -> QuantumCircuit:
    """
    Internal helper to parse circuit data (qubits, ops, etc.) into a QuantumCircuit.
    Refactored from parse_quyaml_to_qiskit.
    """
    circuit_name = data.get('circuit', 'my_circuit')
    
    # Support both 'parameters' and 'params' (optimized)
    params = data.get('params', data.get('parameters', {}))
    
    # Inject symbolic parameters if requested
    if symbolic_params:
        for name in symbolic_params:
            # Create Qiskit Parameter object
            # If the param is already in 'params', we overwrite it with the symbolic version
            # This allows the parser to use the Parameter object in gates
            params[name] = Parameter(name)

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

    for i, inst in enumerate(instructions):
        line_num = i + 1
        if isinstance(inst, str):
            _apply_instruction(qc, inst, params, line_num)
        elif isinstance(inst, dict):
            # Structured op
            if 'if' in inst:
                _parse_if_block_internal(qc, inst['if'], params, line_num)
            elif 'while' in inst:
                wb = inst['while']
                if not isinstance(wb, dict):
                    raise QuYamlError(f"Invalid 'while' block on line {line_num}.")
                cond_ast = _parse_condition_string(str(wb.get('cond','')), qc)
                body = wb.get('body', [])
                max_iter = int(wb.get('max_iter', 1024))
                if hasattr(qc, 'while_loop') and cond_ast[0] == 'atom':
                    _, (rk, val) = cond_ast
                    try:
                        with qc.while_loop((qc.cregs[0], val)):
                            for sub in body:
                                if isinstance(sub, str):
                                    _apply_instruction(qc, sub, params, line_num=line_num)
                                elif isinstance(sub, dict):
                                    if 'measure' in sub:
                                        spec = sub['measure']
                                        qc.measure(int(spec['q']), int(spec['c']))
                                    elif 'reset' in sub:
                                        qc.reset(int(sub['reset']['q']))
                                    else:
                                        raise QuYamlError("Unsupported structured op in while body.")
                                else:
                                    raise QuYamlError("Invalid op in while body.")
                    except Exception as e:
                        raise QuYamlError(f"Failed to build while_loop: {e}")
                else:
                    for _ in range(max_iter):
                        _emit_conditional(qc, cond_ast, body, [], params, start_line=line_num)
            elif 'for' in inst:
                fb = inst['for']
                if not isinstance(fb, dict):
                    raise QuYamlError(f"Invalid 'for' block on line {line_num}.")
                r = fb.get('range')
                if not (isinstance(r, list) and len(r) == 2):
                    raise QuYamlError("'for' requires range: [start, end]")
                start, end = int(r[0]), int(r[1])
                body = fb.get('body', [])
                count = max(0, end - start)
                if hasattr(qc, 'for_loop'):
                    try:
                        with qc.for_loop(range(start, end)):
                            for sub in body:
                                if isinstance(sub, str):
                                    _apply_instruction(qc, sub, params, line_num=line_num)
                                elif isinstance(sub, dict):
                                    if 'measure' in sub:
                                        spec = sub['measure']
                                        qc.measure(int(spec['q']), int(spec['c']))
                                    elif 'reset' in sub:
                                        qc.reset(int(sub['reset']['q']))
                                    else:
                                        raise QuYamlError("Unsupported structured op in for body.")
                                else:
                                    raise QuYamlError("Invalid op in for body.")
                    except Exception as e:
                        raise QuYamlError(f"Failed to build for_loop: {e}")
                else:
                    for _ in range(count):
                        for sub in body:
                            if isinstance(sub, str):
                                _apply_instruction(qc, sub, params, line_num=line_num)
                            elif isinstance(sub, dict):
                                if 'measure' in sub:
                                    spec = sub['measure']
                                    qc.measure(int(spec['q']), int(spec['c']))
                                elif 'reset' in sub:
                                    qc.reset(int(sub['reset']['q']))
                                else:
                                    raise QuYamlError("Unsupported structured op in for body.")
                            else:
                                raise QuYamlError("Invalid op in for body.")
            else:
                # Try other structured ops like measure/reset if they were allowed as dicts
                if 'measure' in inst:
                    spec = inst['measure']
                    qc.measure(int(spec['q']), int(spec['c']))
                elif 'reset' in inst:
                    qc.reset(int(inst['reset']['q']))
                else:
                    raise QuYamlError(f"Unknown structured op on line {line_num}. Supported: 'measure', 'if', 'while', 'for'.")
        else:
            raise QuYamlError(f"Instruction on line {line_num} must be string or object.")

    return qc

def _parse_if_block_internal(qc, block, params, start_line):
    """
    Helper to parse 'if' blocks, extracted from parse_quyaml_to_qiskit.
    """
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

    # Parse condition string
    try:
        cond_ast = _parse_condition_string(str(cond_str), qc)
        _emit_conditional(qc, cond_ast, then_ops, else_ops, params, start_line)
    except QuYamlError as e:
        raise QuYamlError(f"Error in 'if' block on line {start_line}: {e}")
