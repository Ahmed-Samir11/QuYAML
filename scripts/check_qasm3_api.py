from qiskit import qasm3
print('has_dumps', hasattr(qasm3, 'dumps'))
print('has_loads', hasattr(qasm3, 'loads'))
print('exports', [m for m in dir(qasm3) if not m.startswith('_')])
