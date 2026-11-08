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

    cut = []
    for sample in trace:
        if sample[0] <= end:
            cut.append(sample)

    if cut[-1][0] < end:
        cut.append((end, *position(trace, end)))

    return cut


def evaluate(name: str, traces: list[list[Sample]], moves_are_input: bool = True) -> Row:
    moved = recent = lumma = 0
    waits = []

    for trace in traces:
        trace = window(trace)

        if cursor_moved(trace):
            moved += 1
        if recent_input(trace, moves_are_input=moves_are_input):
            recent += 1

        wait = lumma_detonation(trace)
        if wait is None:
            waits.append(math.inf)
        else:
            lumma += 1
            waits.append(wait)

    return Row(
        name=name,
        runs=len(traces),
        moved=moved,
        recent=recent,
        lumma=lumma,
        lumma_median_ms=statistics.median(waits),
    )


def simulate(seeds: int) -> list[Row]:
    rows = []
    for name, sim in SIMULATORS.items():
        traces = []
        for seed in range(seeds):
            traces.append(generate(name, seed, WINDOW_MS))

        rows.append(evaluate(name, traces, moves_are_input=sim.moves_are_input))

    return rows


def load_trace(path: Path) -> list[Sample]:
    """CSV with a t_ms,x,y header as record.py writes it, checked to cover the window."""
    trace = []
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            trace.append((int(row["t_ms"]), int(row["x"]), int(row["y"])))

    for a, b in pairwise(trace):
        if b[0] <= a[0]:
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

    recorded = []
    try:
        for path in args.trace:
            recorded.append((path, load_trace(path)))
    except (OSError, ValueError, KeyError) as e:
        parser.error(str(e))

    rows = simulate(args.seeds)
    for path, trace in recorded:
        rows.append(evaluate(f"recorded: {path.name}", [trace]))

    print(format_table(rows))


if __name__ == "__main__":
    main()
