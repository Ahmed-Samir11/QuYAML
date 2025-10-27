import sys
sys.path.insert(0, r'F:/repos/QuYAML')
from quyaml_pennylane import parse_quyaml_to_pennylane
import pennylane as qml

qy = '''
circuit: bell
qubits: q[2]
ops:
  - h 0
  - cx 0 1
'''

fn = parse_quyaml_to_pennylane(qy)

n = 2
dev = qml.device('default.qubit', wires=n)

def qf():
    fn(wires=range(n))
    return qml.probs(wires=range(n))

circuit = qml.QNode(qf, dev)
print('Probs:', circuit())
