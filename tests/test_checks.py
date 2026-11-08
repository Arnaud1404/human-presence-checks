import pytest

from checks import (
    angle,
    cursor_moved,
    last_input,
    looks_human,
    lumma_detonation,
    position,
    recent_input,
)


def still(duration_ms, x=100, y=100):
    trace = []
    for t in range(0, duration_ms + 1, 10):
        trace.append((t, x, y))
    return trace


def moving_until(stop_ms, duration_ms):
    """Moves 1 px right every 10 ms until stop_ms, then stays put."""
    trace = []
    for t in range(0, duration_ms + 1, 10):
        trace.append((t, 100 + min(t, stop_ms) // 10, 100))
    return trace


def test_position_is_last_sample_at_or_before_t():
    trace = [(0, 1, 1), (10, 2, 2), (20, 3, 3)]
    assert position(trace, 0) == (1, 1)
    assert position(trace, 15) == (2, 2)
    assert position(trace, 20) == (3, 3)


def test_position_outside_trace_raises():
    with pytest.raises(ValueError):
        position([(0, 1, 1), (10, 2, 2)], 11)


def test_last_input_skips_unchanged_samples():
    assert last_input(moving_until(500, 2000), 2000) == 500
    assert last_input(still(2000), 2000) == 0


def test_cursor_moved():
    assert not cursor_moved(still(2000))
    assert cursor_moved(moving_until(1500, 2000))


def test_recent_input_threshold():
    assert recent_input(moving_until(25_000, 30_000))
    assert recent_input(moving_until(24_000, 30_000))
    assert not recent_input(moving_until(23_990, 30_000))
    assert not recent_input(still(30_000))


def test_recent_input_ignores_moves_that_are_not_input():
    assert not recent_input(moving_until(29_000, 30_000), moves_are_input=False)


def test_recent_input_needs_a_30_s_trace():
    with pytest.raises(ValueError):
        recent_input(still(10_000))


def test_angle():
    assert angle((1, 0), (2, 0)) == pytest.approx(0.0)
    assert angle((1, 0), (0, 1)) == pytest.approx(90.0)
    assert angle((1, 0), (-1, 0)) == pytest.approx(180.0)


def test_looks_human():
    assert looks_human([(0, 0), (10, 0), (20, 2), (30, 6), (40, 12)])
    assert not looks_human([(0, 0), (10, 0), (10, 0), (20, 0), (30, 0)])  # repeated read
    assert not looks_human([(0, 0), (10, 0), (10, 10), (20, 10), (20, 20)])  # 90 degree turns


def test_lumma_detonates_after_one_poll_for_a_straight_line():
    assert lumma_detonation(moving_until(10_000, 10_000)) == 500


def test_lumma_wait_is_measured_from_the_trace_start():
    shifted = []
    for t, x, y in moving_until(10_000, 10_000):
        shifted.append((t + 1_000, x, y))
    assert lumma_detonation(shifted) == 500


def test_lumma_never_detonates_on_zigzag():
    zigzag = []
    for t in range(0, 5_001, 10):
        step = t // 50
        zigzag.append((t, step * 10, (step % 2) * 10))
    assert lumma_detonation(zigzag) is None


def test_lumma_retries_until_the_cursor_moves():
    trace = []
    for t in range(0, 5_001, 10):
        trace.append((t, 100 + max(0, t - 1_000) // 10, 100))
    detonation = lumma_detonation(trace)
    assert detonation is not None and detonation > 1_000
