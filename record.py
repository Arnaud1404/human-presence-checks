"""Record the real cursor every 10 ms on Windows, as a human baseline for bench.py."""

from __future__ import annotations

import argparse
import csv
import ctypes
import sys
import time
from pathlib import Path


class _Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def record(out: Path, seconds: float, step_ms: int = 10) -> int:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    point = _Point()
    out.parent.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter_ns()
    rows = 0
    with out.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["t_ms", "x", "y"])
        last_t = -1
        while (t := (time.perf_counter_ns() - start) // 1_000_000) <= seconds * 1000:
            if not user32.GetCursorPos(ctypes.byref(point)):
                raise ctypes.WinError(ctypes.get_last_error())
            if t > last_t:  # keep times strictly increasing if two reads share a millisecond
                writer.writerow([t, point.x, point.y])
                rows += 1
                last_t = t
            time.sleep(step_ms / 1000)
    return rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("traces/human.csv"))
    parser.add_argument(
        "--seconds", type=float, default=35.0, help="at least 30 for the idle check"
    )
    args = parser.parse_args(argv)
    if sys.platform != "win32":
        sys.exit("record.py reads the cursor through user32 and runs on Windows only")
    print(f"recording {args.seconds:.0f} s, use the mouse as usual")
    rows = record(args.out, args.seconds)
    print(f"{rows} samples written to {args.out}")


if __name__ == "__main__":
    main()
