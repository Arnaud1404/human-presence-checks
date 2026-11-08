import math

import pytest

import bench
from bench import WINDOW_MS, evaluate, format_table, load_trace, simulate, window


@pytest.fixture(scope="module")
def rows():
    by_name = {}
    for row in simulate(seeds=20):
        by_name[row.name] = row
    return by_name


def write_csv(path, samples):
    lines = ["t_ms,x,y\n"]
    for t, x, y in samples:
        lines.append(f"{t},{x},{y}\n")
    path.write_text("".join(lines))
    return path


def trace_until(end_ms, x_at, y):
    """One sample every 10 ms from 0 to end_ms; x_at gives the x position at time t."""
    trace = []
    for t in range(0, end_ms + 1, 10):
        trace.append((t, x_at(t), y))
    return trace


def short_trace():
    """Ends 10 ms before the window does."""
    return trace_until(WINDOW_MS - 10, lambda t: 1, 1)


def test_idle_fails_every_check(rows):
    r = rows["idle"]
    assert (r.moved, r.recent, r.lumma) == (0, 0, 0)
    assert math.isinf(r.lumma_median_ms)


def test_set_cursor_pos_jumps_only_beat_the_position_check(rows):
    r = rows["jumps"]
    assert (r.moved, r.recent, r.lumma) == (20, 0, 0)


def test_random_jitter_beats_the_simple_checks_but_lumma_only_by_chance(rows):
    r = rows["random_walk"]
    assert (r.moved, r.recent) == (20, 20)
    assert 5 <= r.lumma <= 18
    assert r.lumma_median_ms > 5_000


def test_straight_lines_pass_lumma_after_one_poll(rows):
    r = rows["linear"]
    assert r.lumma == 20 and r.lumma_median_ms == 500


def test_human_like_passes_everything_after_one_poll(rows):
    r = rows["human_like"]
    assert (r.moved, r.recent, r.lumma, r.lumma_median_ms) == (20, 20, 20, 500)


def test_median_counts_runs_that_never_pass():
    still = trace_until(WINDOW_MS, lambda t: 5, 5)
    line = trace_until(WINDOW_MS, lambda t: t // 10, 5)
    r = evaluate("mixed", [still, still, line])
    assert r.lumma == 1 and math.isinf(r.lumma_median_ms)


def test_detonation_after_the_window_does_not_count():
    trace = trace_until(35_000, lambda t: 5 + max(0, t - 31_000) // 10, 5)
    r = evaluate("late", [trace])
    assert r.lumma == 0


def test_window_adds_a_sample_at_the_window_end():
    trace = [(0, 1, 1), (29_995, 2, 2), (30_007, 3, 3)]
    assert window(trace)[-1] == (WINDOW_MS, 2, 2)


@pytest.mark.parametrize("trace", [[], short_trace()])
def test_window_rejects_short_traces(trace):
    with pytest.raises(ValueError):
        window(trace)


def test_recorded_trace_roundtrip(tmp_path):
    path = write_csv(tmp_path / "t.csv", trace_until(WINDOW_MS, lambda t: t // 10, 5))
    trace = load_trace(path)
    assert trace[1] == (10, 1, 5)
    r = evaluate("recorded", [trace])
    assert (r.moved, r.recent, r.lumma) == (1, 1, 1)


def test_load_trace_rejects_unordered_times(tmp_path):
    path = write_csv(tmp_path / "t.csv", [(0, 1, 1), (0, 2, 2)])
    with pytest.raises(ValueError):
        load_trace(path)


def test_load_trace_rejects_a_short_recording(tmp_path):
    path = write_csv(tmp_path / "t.csv", short_trace())
    with pytest.raises(ValueError, match="30000 needed"):
        load_trace(path)


def test_bad_recording_fails_before_any_simulation(tmp_path, monkeypatch):
    path = write_csv(tmp_path / "t.csv", [])

    def no_simulation(seeds):
        raise AssertionError("simulate ran before the recorded trace was checked")

    monkeypatch.setattr(bench, "simulate", no_simulation)
    with pytest.raises(SystemExit):
        bench.main(["--trace", str(path)])


def test_table_lists_every_row(rows):
    table = format_table(list(rows.values()))
    assert table.count("\n") == len(rows) + 1
    assert "| idle | 20 | 0/20 | 0/20 | 0/20 | > 30 s |" in table
