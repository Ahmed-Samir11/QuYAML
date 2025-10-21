from hypothesis import given, strategies as st
from quyaml_parser import parse_quyaml_to_qiskit
from qiskit import QuantumCircuit

@st.composite
def st_quyaml_instructions(draw, max_qubits=4):
    """A Hypothesis strategy to generate a list of valid QuYAML instructions."""
    num_qubits = draw(st.integers(min_value=1, max_value=max_qubits))
    st_qubit_index = st.integers(min_value=0, max_value=num_qubits - 1).map(lambda i: f"q[{i}]")
    st_gate_name = st.sampled_from(["h", "x", "cx", "swap"])
    instructions = []
    num_instructions = draw(st.integers(min_value=1, max_value=10))
    for _ in range(num_instructions):
        gate = draw(st_gate_name)
        if gate in ["h", "x"]:
            instructions.append(f"{gate} {draw(st_qubit_index)}")
        elif gate in ["cx", "swap"]:
            q1, q2 = draw(st.lists(st_qubit_index, min_size=2, max_size=2, unique=True))
            instructions.append(f"{gate} {q1}, {q2}")
    quyaml_list = [f"qreg: q[{num_qubits}]", "instructions:"]
    quyaml_list.extend([f"  - {inst}" for inst in instructions])
    return "\n".join(quyaml_list)

@given(quyaml_string=st_quyaml_instructions())
def test_parser_handles_valid_generated_circuits(quyaml_string):
    """
    Property-Based Test: Asserts that the parser can process any valid,
    randomly generated QuYAML string without crashing.
    """
    qc = parse_quyaml_to_qiskit(quyaml_string)
    assert isinstance(qc, QuantumCircuit)
