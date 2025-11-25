import os
import json
import argparse
from pathlib import Path
from qiskit import QuantumCircuit
import yaml
# Import qc_to_quyaml_dict from qiskit_bridge. 
# Assuming qiskit_bridge.py is in the same directory or python path.
import sys
sys.path.append(str(Path(__file__).resolve().parents[1])) # Add repo root to path
from quyaml import qc_to_quyaml_dict

def convert_qasm_to_quyaml(qasm_str: str) -> str:
    try:
        qc = QuantumCircuit.from_qasm_str(qasm_str)
        data = qc_to_quyaml_dict(qc)
        return yaml.dump(data, sort_keys=False)
    except Exception as e:
        print(f"Failed to convert QASM: {e}")
        return None

def generate_dataset(input_dir: str, output_file: str):
    dataset = []
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Input directory {input_dir} does not exist.")
        return

    # Process QASM files
    for file in input_path.glob("**/*.qasm"):
        try:
            qasm_content = file.read_text(encoding='utf-8')
            quyaml_content = convert_qasm_to_quyaml(qasm_content)
            
            if quyaml_content:
                entry = {
                    "instruction": "Convert the following OpenQASM code to QuYAML.",
                    "input": qasm_content,
                    "output": quyaml_content
                }
                dataset.append(entry)
                
                # Reverse direction
                entry_rev = {
                    "instruction": "Convert the following QuYAML code to OpenQASM.",
                    "input": quyaml_content,
                    "output": qasm_content
                }
                dataset.append(entry_rev)
        except Exception as e:
            print(f"Error processing {file}: {e}")

    # Save to JSONL
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in dataset:
            f.write(json.dumps(entry) + "\n")
    
    print(f"Generated {len(dataset)} examples in {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate LLM fine-tuning dataset")
    parser.add_argument("input_dir", help="Directory containing QASM files")
    parser.add_argument("output_file", help="Output JSONL file")
    args = parser.parse_args()
    generate_dataset(args.input_dir, args.output_file)
