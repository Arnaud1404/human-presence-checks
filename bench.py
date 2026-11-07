"""Pass rates of each simulator against each check, over many seeds or one recorded trace."""

from __future__ import annotations

import argparse
import csv
import statistics
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

from checks import Sample, cursor_moved, lumma_detonation, recent_input
from trajectories import GENERATORS, generate


@dataclass(frozen=True)
class Row:
    name: str
    runs: int
    moved: int
    recent: int
    lumma: int
    lumma_median_ms: float | None


def evaluate(name: str, traces: list[list[Sample]]) -> Row:
    detonations = [d for t in traces if (d := lumma_detonation(t)) is not None]
    return Row(
        name=name,
        runs=len(traces),
        moved=sum(cursor_moved(t) for t in traces),
        recent=sum(recent_input(t) for t in traces),
        lumma=len(detonations),
        lumma_median_ms=statistics.median(detonations) if detonations else None,
    )


def simulate(seeds: int, duration_ms: int = 30_000) -> list[Row]:
    return [
        evaluate(name, [generate(name, seed, duration_ms) for seed in range(seeds)])
        for name in GENERATORS
    ]


def load_trace(path: Path) -> list[Sample]:
    """CSV with a t_ms,x,y header, times strictly increasing, as record.py writes it."""
    with path.open(newline="") as f:
        trace = [(int(r["t_ms"]), int(r["x"]), int(r["y"])) for r in csv.DictReader(f)]
    if any(b[0] <= a[0] for a, b in pairwise(trace)):
        raise ValueError(f"{path}: times are not strictly increasing")
    return trace


def format_table(rows: list[Row]) -> str:
    lines = [
        "| simulator | runs | cursor moved in 2 s | input in last 6 s at 30 s "
        "| LummaC2 passed in 30 s | LummaC2 median wait |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        wait = "never" if r.lumma_median_ms is None else f"{r.lumma_median_ms / 1000:.1f} s"
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
    rows = simulate(args.seeds)
    rows += [evaluate(f"recorded: {p.name}", [load_trace(p)]) for p in args.trace]
    print(format_table(rows))


if __name__ == "__main__":
    main()
