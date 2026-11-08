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
    """Reads until the first read at or past `seconds`, so the trace covers the whole span."""
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    point = _Point()
    out.parent.mkdir(parents=True, exist_ok=True)

    start = time.perf_counter_ns()
    deadline = start
    rows = 0

    with out.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["t_ms", "x", "y"])

        last_t = -1
        while True:
            t = (time.perf_counter_ns() - start) // 1_000_000
            if not user32.GetCursorPos(ctypes.byref(point)):
                raise ctypes.WinError(ctypes.get_last_error())

            if t > last_t:  # keep times strictly increasing if two reads share a millisecond
                writer.writerow([t, point.x, point.y])
                rows += 1
                last_t = t

            if t >= seconds * 1000:
                return rows

            # Sleep to the next tick of a fixed grid, so loop overhead does not accumulate.
            deadline += step_ms * 1_000_000
            delay = deadline - time.perf_counter_ns()
            if delay > 0:
                time.sleep(delay / 1e9)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("traces/human.csv"))
    parser.add_argument(
        "--seconds", type=float, default=35.0, help="at least 30, the window bench.py scores"
    )
    parser.add_argument(
        "--countdown", type=int, default=5, help="seconds to get ready before recording starts"
    )

    args = parser.parse_args(argv)

    if args.seconds < 30:
        parser.error("--seconds must be at least 30: the idle check reads the cursor at 30 s")
    if args.countdown < 0:
        parser.error("--countdown must not be negative")

    if sys.platform != "win32":
        sys.exit("record.py reads the cursor through user32 and runs on Windows only")

    # Without a countdown, reading these lines takes the first seconds of the trace, and the
    # 2 s cursor check then fails for a reason that has nothing to do with the user.
    print(
        f"Browse or click around as you normally would for {args.seconds:.0f} s, starting at GO.",
        flush=True,
    )
    for left in range(args.countdown, 0, -1):
        print(f"{left}...", flush=True)
        time.sleep(1)
    print("GO", flush=True)

    rows = record(args.out, args.seconds)
    print(f"{rows} samples written to {args.out}")


if __name__ == "__main__":
    main()
