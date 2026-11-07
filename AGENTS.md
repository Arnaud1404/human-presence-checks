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

A change is done when the three commands above pass and the README table matches `python bench.py --seeds 100`.

## Rules

- Python 3.12, standard library only at runtime.
- No malware samples, no code that evades a real sandbox: the repo measures simulators against published checks.
- README limits stay in sync with what the code models.
