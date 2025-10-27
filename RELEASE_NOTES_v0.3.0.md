# QuYAML v0.3.0

QuYAML v0.3.0 focuses on experimental control flow (v0.3 syntax), YAML safety, fairer benchmarks, and a tiny CLI.

## Highlights

- v0.3 features: mid-circuit measurement and classical if/else
  - Structured mid-circuit measure: `{ measure: { q: <int>, c: <int> } }`
  - Classical control with if/else blocks:
    - Single-bit conditions: `c[i] == 0|1`
    - Full-register equality: `c == <int>` (supports decimal, 0b, 0x)
  - Implements dynamic-circuit control using `if_test`/`else_` or `qc.if_else(...)` fallback.

- YAML restrictions and safety
  - Forbid anchors (&), aliases (*), and custom tags (!)
  - Pre-parse scanner rejects advanced YAML features before loading

- Benchmarks updated; JSON rebuild timing added
  - New case: Conditional full-register equality (2q)
    - Tokens: QuYAML 131, JSON 442, QASM3 90
    - Parse times (ms): QuYAML 3.545, JSON decode 0.013, JSON rebuild 0.168, QASM3 parse 8.464
  - Averages across all tests:
    - Tokens: QuYAML 424.6, JSON 633.8, QASM3 372.9
    - Parse times (ms): QuYAML 6.269, JSON decode 0.051, JSON rebuild 0.672, QASM3 21.475
  - Regression checker in CI now gates on JSON rebuild parse time as well

- CLI utilities
  - Validate, count tokens, and time parsing
  - Examples (PowerShell):
    - Validate and summarize:
      `F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/quyaml_cli.py validate examples/bell.quyaml --summary`
    - Count tokens (stdin):
      `Get-Content examples/bell.quyaml | F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/quyaml_cli.py count-tokens -`
    - Count tokens including JSON and QASM3:
      `F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/quyaml_cli.py count-tokens examples/bell.quyaml --json --qasm3`
    - Time parse:
      `F:/repos/QuYAML/quyaml/Scripts/python.exe scripts/quyaml_cli.py time-parse examples/bell.quyaml -n 200`

- Deprecation cleanup
  - Removed usage of deprecated `ast.Num` in the safe expression evaluator; no deprecation warnings on Python 3.12+, compatible with current versions (uses `ast.Constant` for numeric literals).

## Notes

- v0.3 features are marked experimental and may evolve.
- YAML safety checks are conservative by design.
- The repository includes tests and CI to validate functionality and benchmark regression checks.
