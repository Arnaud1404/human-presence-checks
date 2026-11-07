from itertools import pairwise

import pytest

from trajectories import HEIGHT, SIMULATORS, STEP_MS, WIDTH, generate


@pytest.mark.parametrize("name", SIMULATORS)
def test_trace_shape(name):
    trace = generate(name, seed=1, duration_ms=5_000)
    assert [t for t, _, _ in trace] == list(range(0, 5_001, STEP_MS))
    assert all(0 <= x < WIDTH and 0 <= y < HEIGHT for _, x, y in trace)


@pytest.mark.parametrize("name", SIMULATORS)
def test_same_seed_same_trace(name):
    assert generate(name, seed=7, duration_ms=3_000) == generate(name, seed=7, duration_ms=3_000)
    assert generate(name, seed=7, duration_ms=3_000) != generate(name, seed=8, duration_ms=3_000)


def test_idle_never_moves():
    assert len({(x, y) for _, x, y in generate("idle", seed=3)}) == 1


def test_jumps_hold_each_point_for_a_second():
    trace = generate("jumps", seed=3, duration_ms=3_000)
    changes = [t for (t, *a), (_, *b) in pairwise(trace) if a != b]
    assert all(t % 1_000 == 990 for t in changes)
