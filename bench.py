"""Pass rates of each simulator against each check, over many seeds or recorded traces."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

from checks import Sample, cursor_moved, lumma_detonation, position, recent_input
from trajectories import SIMULATORS, generate

WINDOW_MS = 30_000


@dataclass(frozen=True)
class Row:
    name: str
    runs: int
    moved: int
    recent: int
    lumma: int
    # Over all runs, a run that never passes counting as longer than the window.
    lumma_median_ms: float


def window(trace: list[Sample], length_ms: int = WINDOW_MS) -> list[Sample]:
    """The first length_ms of a trace, ending with a sample exactly at the window end."""
    if not trace:
        raise ValueError("empty trace")
    end = trace[0][0] + length_ms
    if trace[-1][0] < end:
        raise ValueError(f"trace lasts {trace[-1][0] - trace[0][0]} ms, {length_ms} needed")
    cut = [s for s in trace if s[0] <= end]
    if cut[-1][0] < end:
        cut.append((end, *position(trace, end)))
    return cut


def evaluate(name: str, traces: list[list[Sample]], moves_are_input: bool = True) -> Row:
    traces = [window(t) for t in traces]
    waits = [lumma_detonation(t) for t in traces]
    return Row(
        name=name,
        runs=len(traces),
        moved=sum(cursor_moved(t) for t in traces),
        recent=sum(recent_input(t, moves_are_input=moves_are_input) for t in traces),
        lumma=sum(w is not None for w in waits),
        lumma_median_ms=statistics.median(math.inf if w is None else w for w in waits),
    )


def simulate(seeds: int) -> list[Row]:
    return [
        evaluate(
            name,
            [generate(name, seed, WINDOW_MS) for seed in range(seeds)],
            moves_are_input=sim.moves_are_input,
        )
        for name, sim in SIMULATORS.items()
    ]


def load_trace(path: Path) -> list[Sample]:
    """CSV with a t_ms,x,y header as record.py writes it, checked to cover the window."""
    with path.open(newline="") as f:
        trace = [(int(r["t_ms"]), int(r["x"]), int(r["y"])) for r in csv.DictReader(f)]
    if any(b[0] <= a[0] for a, b in pairwise(trace)):
        raise ValueError(f"{path}: times are not strictly increasing")
    try:
        window(trace)
    except ValueError as e:
        raise ValueError(f"{path}: {e}") from None
    return trace


def format_table(rows: list[Row]) -> str:
    lines = [
        "| simulator | runs | cursor moved in 2 s | input in last 6 s at 30 s "
        "| LummaC2 passed in 30 s | LummaC2 median wait |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        wait = "> 30 s" if math.isinf(r.lumma_median_ms) else f"{r.lumma_median_ms / 1000:.1f} s"
        lines.append(
            f"| {r.name} | {r.runs} | {r.moved}/{r.runs} | {r.recent}/{r.runs} "
            f"| {r.lumma}/{r.runs} | {wait} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=100, help="traces per simulator")
    parser.add_argument(
        "--trace",
        type=Path,
        action="append",
        default=[],
        help="recorded CSV to evaluate as well (repeatable)",
    )
    args = parser.parse_args(argv)
    try:
        recorded = [(p, load_trace(p)) for p in args.trace]
    except (OSError, ValueError, KeyError) as e:
        parser.error(str(e))
    rows = simulate(args.seeds)
    rows += [evaluate(f"recorded: {p.name}", [t]) for p, t in recorded]
    print(format_table(rows))


if __name__ == "__main__":
    main()
