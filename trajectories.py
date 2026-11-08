"""Cursor traces produced by candidate user simulators, sampled every 10 ms."""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from checks import Sample

WIDTH, HEIGHT = 1920, 1080
STEP_MS = 10

FloatPoint = tuple[float, float]


def _random_point(rng: random.Random) -> FloatPoint:
    return rng.uniform(0, WIDTH - 1), rng.uniform(0, HEIGHT - 1)


def _idle(rng: random.Random) -> Iterator[FloatPoint]:
    p = _random_point(rng)
    while True:
        yield p


def _jumps(rng: random.Random, period_ms: int = 1000) -> Iterator[FloatPoint]:
    """Teleports to a random point once per period with SetCursorPos, like an auto-clicker."""
    while True:
        p = _random_point(rng)
        for _ in range(period_ms // STEP_MS):
            yield p


def _random_walk(rng: random.Random, step_px: int = 3) -> Iterator[FloatPoint]:
    """Irregular jitter: each axis moves by a random step every 10 ms."""
    x, y = _random_point(rng)
    while True:
        yield x, y
        x = min(max(x + rng.randint(-step_px, step_px), 0), WIDTH - 1)
        y = min(max(y + rng.randint(-step_px, step_px), 0), HEIGHT - 1)


def _linear(rng: random.Random, speed_px_s: float = 800.0) -> Iterator[FloatPoint]:
    """Straight lines at constant speed between random targets, no pause."""
    x, y = _random_point(rng)
    while True:
        tx, ty = _random_point(rng)
        n = max(1, round(math.dist((x, y), (tx, ty)) / speed_px_s * 1000 / STEP_MS))

        for k in range(1, n + 1):
            yield x + (tx - x) * k / n, y + (ty - y) * k / n

        x, y = tx, ty


def _bezier(s: float, a: float, b: float, c: float, d: float) -> float:
    """One coordinate of the cubic Bezier with control values a, b, c, d at parameter s."""
    return (1 - s) ** 3 * a + 3 * (1 - s) ** 2 * s * b + 3 * (1 - s) * s**2 * c + s**3 * d


def _human_like(rng: random.Random) -> Iterator[FloatPoint]:
    """Curved moves that speed up then slow down, separated by short pauses.

    Each move is a cubic Bezier whose control points sit off the straight line, so the
    path bends; the smoothstep timing gives the ease-in and ease-out of a hand.
    """
    p0 = _random_point(rng)
    while True:
        p3 = _random_point(rng)
        dist = max(math.dist(p0, p3), 1.0)
        nx, ny = (p0[1] - p3[1]) / dist, (p3[0] - p0[0]) / dist
        bend = rng.uniform(-0.3, 0.3) * dist

        dx, dy = p3[0] - p0[0], p3[1] - p0[1]
        third, two_thirds = 1 / 3, 2 / 3
        p1 = (p0[0] + third * dx + nx * bend, p0[1] + third * dy + ny * bend)
        p2 = (p0[0] + two_thirds * dx + nx * bend, p0[1] + two_thirds * dy + ny * bend)

        n = round((300 + 0.4 * dist) / STEP_MS)
        for k in range(1, n + 1):
            u = k / n
            s = u * u * (3 - 2 * u)
            yield (
                _bezier(s, p0[0], p1[0], p2[0], p3[0]),
                _bezier(s, p0[1], p1[1], p2[1], p3[1]),
            )

        for _ in range(rng.randint(100, 1500) // STEP_MS):
            yield p3

        p0 = p3


@dataclass(frozen=True)
class Simulator:
    moves: Callable[[random.Random], Iterator[FloatPoint]]
    # False when the simulator calls SetCursorPos, which moves the cursor without updating
    # GetLastInputInfo; True for SendInput or input injected from outside the guest.
    moves_are_input: bool


SIMULATORS: dict[str, Simulator] = {
    "idle": Simulator(_idle, moves_are_input=True),
    "jumps": Simulator(_jumps, moves_are_input=False),
    "random_walk": Simulator(_random_walk, moves_are_input=True),
    "linear": Simulator(_linear, moves_are_input=True),
    "human_like": Simulator(_human_like, moves_are_input=True),
}


def generate(name: str, seed: int, duration_ms: int = 30_000) -> list[Sample]:
    """Integer screen positions, clamped to the screen, as GetCursorPos reports them."""
    points = SIMULATORS[name].moves(random.Random(seed))

    trace = []
    for t, (x, y) in zip(range(0, duration_ms + 1, STEP_MS), points, strict=False):
        trace.append((t, min(max(round(x), 0), WIDTH - 1), min(max(round(y), 0), HEIGHT - 1)))

    return trace
