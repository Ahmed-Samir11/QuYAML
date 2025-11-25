import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import tiktoken
except Exception:
    tiktoken = None  # optional

try:
    import jsonschema  # type: ignore
except Exception:
    jsonschema = None  # optional

# Ensure repository root on path when running via python -m
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from quyaml_parser import parse_quyaml_to_qiskit, QuYamlError
from qiskit_bridge import qc_to_quyaml_dict, circuits_structurally_equal, diff_circuits


def _read_text(path: str | None) -> str:
    if path and path != "-":
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        text = _read_text(args.input)
        qc = parse_quyaml_to_qiskit(text)
        if args.summary:
            print(f"OK: circuit '{qc.name}', qubits={qc.num_qubits}, cbits={qc.num_clbits}, ops={len(qc.data)}")
        else:
            print("OK")
        return 0
    except QuYamlError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


def _count_tokens(s: str) -> int | None:
    if tiktoken is None:
        return None
    enc = tiktoken.encoding_for_model("gpt-4")
    return len(enc.encode(s))


def cmd_count_tokens(args: argparse.Namespace) -> int:
    text = _read_text(args.input)
    report = {"QuYAML": _count_tokens(text)}

    if args.json or args.qasm3:
        # Build Qiskit circuit once
        try:
            qc = parse_quyaml_to_qiskit(text)
        except QuYamlError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2

        if args.json:
            data = {
                "circuit": qc.name,
                "qubits": qc.num_qubits,
                "cbits": qc.num_clbits,
                "gates": [],
            }
            for instr in qc.data:
                op = instr.operation
                qidx = [qc.find_bit(q).index for q in instr.qubits]
                params = []
                for p in op.params:
                    try:
                        params.append(float(p))
                    except Exception:
                        params.append(str(p))
                data["gates"].append({"name": op.name, "qubits": qidx, "params": params})
            js = json.dumps(data, separators=(",", ":"))
            report["JSON"] = _count_tokens(js)

        if args.qasm3:
            try:
                from qiskit import qasm3
                q3 = qasm3.dumps(qc)
                report["QASM3"] = _count_tokens(q3)
            except Exception as e:
                report["QASM3"] = None
                print(f"WARN: Failed to produce QASM3: {e}", file=sys.stderr)

    if tiktoken is None:
        print("WARN: tiktoken not installed; install to get token counts (pip install tiktoken)", file=sys.stderr)

    print(json.dumps(report, indent=2))
    return 0


def cmd_time_parse(args: argparse.Namespace) -> int:
    text = _read_text(args.input)

    # warmup
    try:
        parse_quyaml_to_qiskit(text)
    except QuYamlError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    iters = max(1, int(args.iters))
    t0 = time.perf_counter()
    for _ in range(iters):
        parse_quyaml_to_qiskit(text)
    t1 = time.perf_counter()
    ms = (t1 - t0) * 1000.0 / iters
    print(f"avg_parse_ms: {ms:.3f}")
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    """Lint a QuYAML file: JSON Schema validation when available, plus parse check."""
    text = _read_text(args.input)
    # JSON Schema validation (optional)
    schema_path = _ROOT / "docs" / "schema" / "quyaml.schema.json"
    schema_ok = False
    if jsonschema is not None and schema_path.exists():
        try:
            import yaml as _yaml
            data = _yaml.safe_load(text)
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.validate(data, schema)
            schema_ok = True
        except Exception as e:
            print(f"SCHEMA: FAIL - {e}", file=sys.stderr)
    else:
        if jsonschema is None:
            print("SCHEMA: SKIP - install jsonschema to enable schema checks", file=sys.stderr)
        else:
            print("SCHEMA: SKIP - schema file not found", file=sys.stderr)

    # Parse check
    try:
        parse_quyaml_to_qiskit(text)
        print("PARSE: OK")
    except QuYamlError as e:
        print(f"PARSE: FAIL - {e}", file=sys.stderr)
        return 2

    if schema_ok:
        print("SCHEMA: OK")
    return 0


def cmd_format(args: argparse.Namespace) -> int:
    """Format QuYAML into a canonical top-level key order and YAML style."""
    text = _read_text(args.input)
    try:
        import yaml as _yaml
        data = _yaml.safe_load(text)
        if not isinstance(data, dict):
            print("ERROR: Top-level must be a mapping", file=sys.stderr)
            return 2
        # Ensure version exists; default to '0.4' if missing
        version = data.get('version', '0.4')
        # Reorder top-level keys
        ordered = {
            'version': version,
            'circuit': data.get('circuit', 'my_circuit'),
            'qubits': data.get('qubits', data.get('qreg')),
            'bits': data.get('bits', data.get('creg')),
            'params': data.get('params', data.get('parameters')),
            'ops': data.get('ops', data.get('instructions', [])),
        }
        # Remove None keys
        ordered = {k: v for k, v in ordered.items() if v is not None}
        # Dump
        out = _yaml.safe_dump(ordered, sort_keys=False)
        if args.write and args.input and args.input != '-':
            Path(args.input).write_text(out, encoding='utf-8')
        else:
            sys.stdout.write(out)
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


def cmd_convert(args: argparse.Namespace) -> int:
    """Convert between QuYAML and QASM3.

    Modes:
      - --to qasm3: parse QuYAML input, output QASM3 text
      - --from qasm3: read QASM3 input, output QuYAML text
    """
    mode_to = (args.to or '').lower()
    mode_from = (args.from_ or '').lower()
    if (mode_to == 'qasm3') == (mode_from == 'qasm3'):
        print("ERROR: specify exactly one of '--to qasm3' or '--from qasm3'", file=sys.stderr)
        return 2
    try:
        if mode_to == 'qasm3':
            text = _read_text(args.input)
            qc = parse_quyaml_to_qiskit(text)
            from qiskit import qasm3
            out = qasm3.dumps(qc)
            if args.output and args.output != '-':
                Path(args.output).write_text(out, encoding='utf-8')
            else:
                sys.stdout.write(out)
            return 0
        else:
            # from qasm3 to QuYAML
            text = _read_text(args.input)
            from qiskit import qasm3
            qc = qasm3.loads(text)
            data = qc_to_quyaml_dict(qc)
            import yaml as _yaml
            out = _yaml.safe_dump(data, sort_keys=False)
            if args.output and args.output != '-':
                Path(args.output).write_text(out, encoding='utf-8')
            else:
                sys.stdout.write(out)
            return 0
    except QuYamlError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


def cmd_diff(args: argparse.Namespace) -> int:
    """Diff two QuYAML files structurally via parsed QuantumCircuits.
    Outputs human-readable text by default, or JSON with --json.
    """
    text_a = _read_text(args.a)
    text_b = _read_text(args.b)
    try:
        qc_a = parse_quyaml_to_qiskit(text_a)
        qc_b = parse_quyaml_to_qiskit(text_b)
    except QuYamlError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    d = diff_circuits(qc_a, qc_b)
    if args.json:
        print(json.dumps(d, indent=2))
    else:
        if d.get("equal"):
            print("EQUAL")
        else:
            reason = d.get("reason", "diff")
            idx = d.get("index")
            if reason == "op mismatch" and idx is not None:
                la = d.get("left", {})
                rb = d.get("right", {})
                print(f"DIFF: op[{idx}] {la.get('name')}{la.get('qubits')} vs {rb.get('name')}{rb.get('qubits')}")
            elif reason == "param mismatch" and idx is not None:
                pj = d.get("param_index")
                print(f"DIFF: op[{idx}] param[{pj}] {d.get('left_param')} vs {d.get('right_param')}")
            else:
                print(f"DIFF: {reason}")
    return 0 if d.get("equal") else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="quyaml", description="QuYAML CLI utilities")
    sub = p.add_subparsers(dest="cmd", required=True)

    # validate
    v = sub.add_parser("validate", help="Validate a QuYAML file/string")
    v.add_argument("input", nargs="?", help="Path to file or '-' for stdin")
    v.add_argument("--summary", action="store_true", help="Print circuit summary on success")
    v.set_defaults(func=cmd_validate)

    # count-tokens
    ct = sub.add_parser("count-tokens", help="Count GPT-4 tokens in QuYAML; optional JSON/QASM3")
    ct.add_argument("input", nargs="?", help="Path to file or '-' for stdin")
    ct.add_argument("--json", action="store_true", help="Also count tokens in compact JSON dump")
    ct.add_argument("--qasm3", action="store_true", help="Also count tokens in QASM3 dump")
    ct.set_defaults(func=cmd_count_tokens)

    # time-parse
    tp = sub.add_parser("time-parse", help="Measure average parse time (ms)")
    tp.add_argument("input", nargs="?", help="Path to file or '-' for stdin")
    tp.add_argument("-n", "--iters", default=100, help="Iterations (default: 100)")
    tp.set_defaults(func=cmd_time_parse)

    # lint
    ln = sub.add_parser("lint", help="Lint a QuYAML file using schema and parser")
    ln.add_argument("input", nargs="?", help="Path to file or '-' for stdin")
    ln.set_defaults(func=cmd_lint)

    # format
    fm = sub.add_parser("format", help="Format QuYAML to a canonical style")
    fm.add_argument("input", nargs="?", help="Path to file or '-' for stdin")
    fm.add_argument("-w", "--write", action="store_true", help="Write changes back to the input file")
    fm.set_defaults(func=cmd_format)

    # convert
    cv = sub.add_parser("convert", help="Convert between QuYAML and QASM3")
    cv.add_argument("input", nargs="?", help="Path to file or '-' for stdin")
    cv.add_argument("-o", "--output", help="Output path or '-' for stdout")
    cv.add_argument("--to", choices=["qasm3"], help="Convert to format")
    cv.add_argument("--from", dest="from_", choices=["qasm3"], help="Convert from format")
    cv.set_defaults(func=cmd_convert)

    # diff
    df = sub.add_parser("diff", help="Structural diff of two QuYAML files")
    df.add_argument("a", help="Left QuYAML file or '-' for stdin")
    df.add_argument("b", help="Right QuYAML file")
    df.add_argument("--json", action="store_true", help="Emit JSON diff for machine consumption")
    df.set_defaults(func=cmd_diff)

    # compile
    cp = sub.add_parser("compile", help="Compile QuYAML to compact JSON for benchmarking")
    cp.add_argument("input", nargs="?", help="Path to file or '-' for stdin")
    cp.add_argument("-o", "--output", help="Output path or '-' for stdout")
    cp.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    cp.set_defaults(func=cmd_compile)

    # visualize
    vz = sub.add_parser("visualize", help="Visualize a QuYAML circuit and save to image")
    vz.add_argument("input", nargs="?", help="Path to file or '-' for stdin")
    vz.add_argument("-o", "--output", help="Output image file (e.g., circuit.png)")
    vz.set_defaults(func=cmd_visualize)

    args = p.parse_args(argv)
    return args.func(args)


def cmd_compile(args: argparse.Namespace) -> int:
    """Compile QuYAML to a compact JSON representation for benchmarking."""
    text = _read_text(args.input)
    try:
        qc = parse_quyaml_to_qiskit(text)
    except QuYamlError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    data = {
        "circuit": qc.name,
        "qubits": qc.num_qubits,
        "cbits": qc.num_clbits,
        "gates": [],
    }
    for instr in qc.data:
        op = instr.operation
        qidx = [qc.find_bit(q).index for q in instr.qubits]
        params = []
        for p in op.params:
            try:
                params.append(float(p))
            except Exception:
                params.append(str(p))
        data["gates"].append({"name": op.name, "qubits": qidx, "params": params})
    if args.output and args.output != '-':
        Path(args.output).write_text(json.dumps(data, separators=(",", ":")) if not args.pretty else json.dumps(data, indent=2), encoding='utf-8')
    else:
        if args.pretty:
            print(json.dumps(data, indent=2))
        else:
            print(json.dumps(data, separators=(",", ":")))
    return 0


def cmd_visualize(args: argparse.Namespace) -> int:
    """Visualize a QuYAML circuit and save to image."""
    text = _read_text(args.input)
    try:
        qc = parse_quyaml_to_qiskit(text)
    except QuYamlError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    try:
        # Use qiskit's draw method
        filename = args.output
        if not filename:
            print("ERROR: --output is required for visualization.", file=sys.stderr)
            return 1
        
        # 'mpl' is the matplotlib drawer which supports png, svg, etc.
        qc.draw(output='mpl', filename=filename)
        print(f"Saved visualization to {filename}")
        return 0
    except ImportError as e:
        print(f"ERROR: Visualization dependencies missing. Please run 'pip install quyaml[viz]'. Details: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Failed to visualize: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
