import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmarks" / "benchmark_pennylane.py"
OUT = ROOT / "benchmarks" / "_ci_pennylane_results.txt"
BASELINE = ROOT / "benchmarks" / "pennylane_baseline.json"

AVG_TOKENS_RE = re.compile(r"^\s*QuYAML:\s*([0-9.]+)\s*\n\s*JSON\s*:\s*([0-9.]+)\s*\n\s*QASM3\s*:\s*([0-9.]+)", re.MULTILINE)
AVG_PARSE_RE = re.compile(r"AVERAGE PARSE TIMES:\s*\n\s*QuYAML parse\s*:\s*([0-9.]+) ms\s*\n\s*JSON decode\s*:\s*([0-9.]+) ms\s*\n\s*QASM3 parse\s*:\s*([0-9.]+) ms", re.MULTILINE)


def run_benchmark() -> str:
    env = os.environ.copy()
    # Ensure repo root on PYTHONPATH
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    res = subprocess.run([sys.executable, str(BENCH)], capture_output=True, text=True, env=env)
    print(res.stdout)
    OUT.write_text(res.stdout, encoding="utf-8")
    if res.returncode != 0:
        print(res.stderr, file=sys.stderr)
        raise SystemExit(res.returncode)
    return res.stdout


def parse_averages(text: str):
    mt = AVG_TOKENS_RE.search(text)
    mp = AVG_PARSE_RE.search(text)
    if not mt or not mp:
        raise RuntimeError("Could not parse averages from benchmark output.")
    tokens = {
        "QuYAML": float(mt.group(1)),
        "JSON": float(mt.group(2)),
        "QASM3": float(mt.group(3)),
    }
    parse_ms = {
        "QuYAML": float(mp.group(1)),
        "JSON": float(mp.group(2)),
        "QASM3": float(mp.group(3)),
    }
    return tokens, parse_ms


def main():
    text = run_benchmark()
    tokens, parse_ms = parse_averages(text)

    if not BASELINE.exists():
        print("No baseline found; writing current results as baseline and exiting 0.")
        BASELINE.write_text(json.dumps({
            "avg_tokens": tokens,
            "avg_parse_ms": parse_ms,
            "tolerances": {"tokens_pct": 0.10, "parse_pct": 1.00},
        }, indent=2), encoding="utf-8")
        return

    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    tol_tokens = float(base.get("tolerances", {}).get("tokens_pct", 0.10))
    tol_parse = float(base.get("tolerances", {}).get("parse_pct", 1.00))

    # Token regression check: QuYAML avg tokens must not exceed baseline by > tol_tokens
    base_qy = float(base["avg_tokens"]["QuYAML"])  
    cur_qy = tokens["QuYAML"]
    token_limit = base_qy * (1.0 + tol_tokens)

    ok = True
    msgs = []

    if cur_qy > token_limit:
        ok = False
        msgs.append(f"Token regression: QuYAML avg tokens {cur_qy:.1f} > limit {token_limit:.1f} (baseline {base_qy:.1f}, tol {tol_tokens*100:.0f}%).")

    # Parse-time soft check: inform if QuYAML parse exceeds tolerance; do not fail by default
    base_qy_ms = float(base["avg_parse_ms"]["QuYAML"])  
    cur_qy_ms = parse_ms["QuYAML"]
    parse_limit = base_qy_ms * (1.0 + tol_parse)
    if cur_qy_ms > parse_limit:
        msgs.append(f"Note: QuYAML parse time increased to {cur_qy_ms:.3f} ms > {parse_limit:.3f} ms limit (baseline {base_qy_ms:.3f}, tol {tol_parse*100:.0f}%).")

    for m in msgs:
        print(m)

    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
