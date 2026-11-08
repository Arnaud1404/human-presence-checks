from itertools import pairwise

import pytest

from trajectories import HEIGHT, SIMULATORS, STEP_MS, WIDTH, generate


@pytest.mark.parametrize("name", SIMULATORS)
def test_trace_shape(name):
    trace = generate(name, seed=1, duration_ms=5_000)
    times = []
    for t, x, y in trace:
        times.append(t)
        assert 0 <= x < WIDTH and 0 <= y < HEIGHT
    assert times == list(range(0, 5_001, STEP_MS))


@pytest.mark.parametrize("name", SIMULATORS)
def test_same_seed_same_trace(name):
    assert generate(name, seed=7, duration_ms=3_000) == generate(name, seed=7, duration_ms=3_000)
    assert generate(name, seed=7, duration_ms=3_000) != generate(name, seed=8, duration_ms=3_000)


def test_idle_never_moves():
    positions = set()
    for _, x, y in generate("idle", seed=3):
        positions.add((x, y))
    assert len(positions) == 1


def test_jumps_hold_each_point_for_a_second():
    trace = generate("jumps", seed=3, duration_ms=3_000)
    changes = 0
    for (t, *before), (_, *after) in pairwise(trace):
        if before != after:
            changes += 1
            assert t % 1_000 == 990
    assert changes > 0
