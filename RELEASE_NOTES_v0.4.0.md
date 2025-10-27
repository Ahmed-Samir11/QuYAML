# QuYAML v0.4.0 Release Notes

Date: 2025-10-27

## Highlights
- Structured control flow: `if`/`elif`/`else`, `while`, and `for` blocks with schema validation.
- Composite conditions: `&&` and `||` supported in `cond` expressions, safely lowered to Qiskit dynamic-circuit builders.
- YAML safety: anchors, aliases, custom tags, and merge keys are rejected; safe loader and guardrails on input size/nesting.
- QASM3 interop: CLI `convert` (to/from QASM3) and round-trip tests via `qiskit_qasm3_import`.
- CLI suite: `validate`, `lint`, `format`, `convert`, `diff` (human/JSON), `compile` (compact JSON), `count-tokens`, `time-parse`.
- CI gates: parse-time checks and token-count budgets, including higher budgets for dynamic circuits.

## Breaking/Behavioral Changes
- Default spec version is now v0.4. Legacy v0.2/v0.3 inputs are accepted only when legacy mode is enabled.
- Expression evaluation runs in a minimal, safe evaluator (constants: `pi`, `e`; basic operators; limited functions).

## Migration
- See `docs/MIGRATION_0.3_to_0.4.md` for steps to update older files and notes on `cond` expressions.

## Install
```bash
pip install -r requirements.txt
# Optional for QASM3 round-trips
pip install qiskit_qasm3_import
```

## Thanks
Thanks to contributors and reviewers for feedback on control flow, safety guardrails, and interop.
