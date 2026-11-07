"""User-presence checks published for Windows malware, replayed on a cursor trace.

A trace is a list of (t_ms, x, y) samples at increasing times. The cursor position
at time t is the last sample at or before t, which is what GetCursorPos would return.
Only cursor moves count as input: keyboard activity is not modelled.
"""

from __future__ import annotations

import math
from bisect import bisect_right
from collections.abc import Sequence
from itertools import pairwise

Sample = tuple[int, int, int]
Trace = Sequence[Sample]
Point = tuple[int, int]


def _index(trace: Trace, t_ms: int) -> int:
    if not trace or t_ms < trace[0][0] or t_ms > trace[-1][0]:
        raise ValueError(f"t={t_ms} ms is outside the trace")
    return bisect_right(trace, t_ms, key=lambda s: s[0]) - 1


def position(trace: Trace, t_ms: int) -> Point:
    _, x, y = trace[_index(trace, t_ms)]
    return x, y


def last_input(trace: Trace, t_ms: int) -> int:
    """Time of the last cursor move at or before t_ms; the trace start if it never moved."""
    i = _index(trace, t_ms)
    while i > 0 and trace[i][1:] == trace[i - 1][1:]:
        i -= 1
    return trace[i][0]


def cursor_moved(trace: Trace, wait_ms: int = 2000) -> bool:
    """GetCursorPos, Sleep(2000), GetCursorPos: no change means no user.

    Check Point Evasions, "Human-like behavior", 2.1 (the pafish check).
    """
    t0 = trace[0][0]
    return position(trace, t0) != position(trace, t0 + wait_ms)


def recent_input(
    trace: Trace, sleep_ms: int = 30_000, max_idle_ms: int = 6_000, moves_are_input: bool = True
) -> bool:
    """Sleep(30000), then GetTickCount() - LASTINPUTINFO.dwTime above 6000 ms means no user.

    Check Point Evasions, "Human-like behavior", 2.5. Cursor moves made with SetCursorPos do
    not update LASTINPUTINFO (moves_are_input=False); SendInput moves do.
    """
    now = trace[0][0] + sleep_ms
    last = last_input(trace, now) if moves_are_input else trace[0][0]
    return now - last <= max_idle_ms


def angle(u: Point, v: Point) -> float:
    """Angle in degrees between two non-zero vectors."""
    cos = (u[0] * v[0] + u[1] * v[1]) / (math.hypot(*u) * math.hypot(*v))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def looks_human(points: Sequence[Point], max_angle: float = 45.0) -> bool:
    """LummaC2 test on one set of reads: all consecutive reads differ, every turn < 45 degrees."""
    if any(a == b for a, b in pairwise(points)):
        return False
    vectors = [(b[0] - a[0], b[1] - a[1]) for a, b in pairwise(points)]
    return all(angle(u, v) < max_angle for u, v in pairwise(vectors))


def lumma_detonation(
    trace: Trace, interval_ms: int = 50, reads: int = 5, poll_ms: int = 300
) -> int | None:
    """Wait, from the trace start, until LummaC2 v4.0 would act; None if not within the trace.

    Outpost24 analysis (November 2023), as reported by The Hacker News and Picus: read the
    cursor, Sleep(300) and read again until it has moved; then take 5 reads 50 ms apart that
    must pass looks_human, otherwise start over from the 300 ms wait.
    """
    t0 = t = trace[0][0]
    span = interval_ms * (reads - 1)
    while t + poll_ms + span <= trace[-1][0]:
        previous = position(trace, t)
        t += poll_ms
        if position(trace, t) == previous:
            continue
        points = [position(trace, t + k * interval_ms) for k in range(reads)]
        if looks_human(points):
            return t + span - t0
        t += span
    return None
