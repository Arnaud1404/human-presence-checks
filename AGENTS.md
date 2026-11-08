# AGENTS.md

Instructions for coding agents working in this repository. Humans: see `README.md`.

## What the repo is

- `checks.py`: three published malware user-presence checks, replayed on a cursor trace. Each docstring names its source; do not change a threshold without a source.
- `trajectories.py`: seeded cursor traces from five candidate simulators, 10 ms sampling, integer screen positions.
- `bench.py`: pass-rate matrix over seeds, plus recorded traces given with `--trace`.
- `record.py`: Windows only, records the real cursor through user32 `GetCursorPos`.

## Commands

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check . && ruff format --check .
python bench.py --seeds 100
python record.py --out traces/human.csv   # Windows; traces/ is ignored by git
```

A change is done when the three commands above pass; `tests/test_readme.py` fails if the README table no longer matches `python bench.py --seeds 100`.

## Rules

- Python 3.12, standard library only at runtime.
- No malware samples, no code that evades a real sandbox: the repo measures simulators against published checks.
- README limits stay in sync with what the code models.
- Hard rule: no comprehensions or generator expressions, in source or tests. Not `[(int(r["t_ms"]), int(r["x"]), int(r["y"])) for r in csv.DictReader(f)]`, not `any(a == b for a, b in pairs)`: write an explicit `for` loop with named variables. `tests/test_style.py` enforces it; ruff's SIM110 is off because it asks for the opposite.
- A blank line separates each logical step inside a function: guard clauses, setup, each loop, the return. In tests, building the input is separated from the call and its asserts.
- Every function and class, test helpers included, opens with a one-line docstring: one sentence, third person, present tense, ending with a period (`"""Returns the cursor position at t_ms, as GetCursorPos would report it."""`), the style of `c-secure-build/src/vuln_shell.c.bak`. Detail and sources go in later paragraphs. `test_` functions are exempt: their names are the summary. `tests/test_style.py` enforces it.
