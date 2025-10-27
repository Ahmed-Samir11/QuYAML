# QuYAML Migration Guide: 0.3 → 0.4

This guide helps you upgrade QuYAML circuits and tooling from v0.3 to v0.4.

v0.4 is the default parsing target. For compatibility, the parser can still accept legacy v0.2/v0.3 when legacy mode is enabled, but new files should set `version: 0.4` and adopt the structured control-flow constructs.

## What changed in v0.4

- Structured control flow with safer, clearer syntax:
  - `if` blocks with `cond`, `then`, optional `elif`, and optional `else`
  - `while` blocks with `cond`, `body`, and optional `max_iter`
  - `for` blocks with `range: [start, stop]` and `body`
- Composite conditions in `cond` using `&&` and `||` in addition to `==` on bits, e.g., `"c[0] == 1 && c[1] == 0"`.
- Reset supports both string and structured forms: `reset 0` or `{reset: {q: 0}}`.
- YAML safety tightened: anchors, aliases, custom tags, and merge keys are rejected. Limits on input size and nesting are enforced.
- JSON Schema published at `docs/schema/quyaml.schema.json` and a canonical formatter is provided via the CLI.
- New CLI commands: `lint`, `format`, `convert` (QuYAML↔QASM3), `diff` (human/JSON), `compile` (compact JSON).

## Minimal upgrades for existing files

1. Add a version header:
   ```yaml
   version: 0.4
   ```
2. Replace v0.3-style if-then with the structured block form:
   
   v0.3 example:
   ```yaml
   version: 0.3
   qubits: q[2]
   bits: c[2]
   ops:
     - h 0
     - {measure: {q: 0, c: 0}}
     - if:
         cond: "c[0] == 1"
         then:
           - x 1
   ```
   
   v0.4 equivalent (supports elif/else and composites):
   ```yaml
   version: 0.4
   qubits: q[2]
   bits: c[2]
   ops:
     - h 0
     - {measure: {q: 0, c: 0}}
     - if:
         cond: "c[0] == 1"
         then:
           - x 1
   ```

3. Prefer structured reset/measure when targeting specific bits/qubits:
   - `reset 0` or `{reset: {q: 0}}`
   - `{measure: {q: 0, c: 0}}` for mid-circuit measurement

## Cond expression notes

- Allowed primitives: `c[i] == 0` or `c[i] == 1` and `c == 0/1` for full-register equality when supported.
- Combine with `&&` and `||` for composites, e.g. `"c[0]==1 && (c[1]==0 || c[2]==1)"`.
- Internally, the parser lowers these to Qiskit dynamic-circuit builders; if-else and loop blocks are created with context managers for best compatibility.

## YAML safety and limits

- Not allowed: `&anchor`, `*alias`, `!custom`, and `<<:` merge keys.
- Large inputs or too-deep nesting will be rejected with a clear error.
- Safe loading is enforced; CSafeLoader is used when available.

## CLI updates

Install optional helpers for the best experience:

```powershell
pip install tiktoken jsonschema
```

Common tasks:

```powershell
# Lint (schema + parse)
python scripts/quyaml_cli.py lint path/to/file.quyaml

# Format in place
python scripts/quyaml_cli.py format path/to/file.quyaml -w

# Convert to/from QASM3
python scripts/quyaml_cli.py convert path/to/file.quyaml --to qasm3 -o -
python scripts/quyaml_cli.py convert --from qasm3 - < path/to/file.qasm3 > out.quyaml

# Diff two circuits
python scripts/quyaml_cli.py diff a.quyaml b.quyaml --json
```

## Parser behavior

- Default target is v0.4. When legacy mode is allowed, missing versions are treated as legacy (v0.3), and explicit `version: 0.2/0.3` are accepted.
- To enforce v0.4 only, disable legacy mode in your application (see `quyaml_parser.py`).

## Troubleshooting

- If a file fails schema validation, run the formatter to normalize key order and check for typos.
- If conditions produce unexpected behavior, simplify to single-bit equality expressions and reintroduce composites incrementally.
- For dynamic circuits, ensure you declared `bits: c[n]` and used structured measure forms when mapping qubits to bits.

## References

- Schema: `docs/schema/quyaml.schema.json`
- Parser: `quyaml_parser.py`
- CLI: `scripts/quyaml_cli.py`
- QASM3 bridge and diffs: `qiskit_bridge.py`
