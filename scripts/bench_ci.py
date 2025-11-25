import argparse
import json
import time
from pathlib import Path
import sys

# Ensure repository root is on path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from quyaml import parse_quyaml_to_qiskit, QuYamlError

try:
    import tiktoken  # type: ignore
except Exception:  # pragma: no cover
    tiktoken = None


def measure_parse_ms(text: str, iters: int) -> float:
    # Warm-up
    parse_quyaml_to_qiskit(text)
    t0 = time.perf_counter()
    for _ in range(iters):
        parse_quyaml_to_qiskit(text)
    t1 = time.perf_counter()
    return (t1 - t0) * 1000.0 / max(1, iters)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="CI parse-time gate for QuYAML")
    p.add_argument("inputs", nargs="+", help="Input QuYAML files")
    p.add_argument("--iters", type=int, default=200, help="Iterations per file (default: 200)")
    p.add_argument("--max-ms", type=float, default=80.0, help="Max allowed average parse ms (default: 80.0 ms)")
    p.add_argument("--max-tokens", type=int, default=None, help="Max allowed QuYAML token count (requires tiktoken)")
    p.add_argument("--json", action="store_true", help="Emit JSON report")
    args = p.parse_args(argv)

    results = []
    failed = False
    for path in args.inputs:
        s = Path(path).read_text(encoding="utf-8")
        try:
            ms = measure_parse_ms(s, args.iters)
            ok = ms <= args.max_ms
            entry = {"file": path, "avg_ms": ms, "iters": args.iters, "ok": ok, "max_ms": args.max_ms}
            # Optional token gating
            if args.max_tokens is not None:
                if tiktoken is None:
                    entry.update({"tokens": None, "token_ok": False, "token_error": "tiktoken not installed"})
                    failed = True
                else:
                    enc = tiktoken.encoding_for_model("gpt-4")
                    tok = len(enc.encode(s))
                    entry.update({"tokens": tok, "token_max": args.max_tokens, "token_ok": tok <= args.max_tokens})
                    if not entry["token_ok"]:
                        failed = True
            results.append(entry)
            if not ok:
                failed = True
        except QuYamlError as e:
            results.append({"file": path, "error": str(e), "ok": False})
            failed = True

    if args.json:
        print(json.dumps({"results": results}, indent=2))
    else:
        for r in results:
            if r.get("error"):
                print(f"FAIL: {r['file']} - {r['error']}")
            else:
                line = f"{r['file']}: avg_ms={r['avg_ms']:.3f} iters={r['iters']} (limit {r['max_ms']} ms) => {'OK' if r['ok'] else 'FAIL'}"
                if "tokens" in r or "token_error" in r:
                    if r.get("token_error"):
                        line += f" | TOKENS: ERROR ({r['token_error']})"
                    else:
                        line += f" | tokens={r['tokens']} (limit {r['token_max']}) => {'OK' if r['token_ok'] else 'FAIL'}"
                print(line)

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
