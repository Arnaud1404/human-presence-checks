import pytest

from bench import evaluate, format_table, load_trace, simulate


@pytest.fixture(scope="module")
def rows():
    return {r.name: r for r in simulate(seeds=20)}


def test_idle_fails_every_check(rows):
    r = rows["idle"]
    assert (r.moved, r.recent, r.lumma) == (0, 0, 0)


def test_set_cursor_pos_jumps_only_beat_the_position_check(rows):
    r = rows["jumps"]
    assert (r.moved, r.recent, r.lumma) == (20, 0, 0)


def test_random_jitter_only_passes_lumma_by_chance(rows):
    r = rows["random_walk"]
    assert r.lumma_median_ms is not None and r.lumma_median_ms > 2_000


def test_straight_lines_pass_lumma_at_once(rows):
    r = rows["linear"]
    assert r.lumma == 20 and r.lumma_median_ms == 200


def test_human_like_passes_everything_at_once(rows):
    r = rows["human_like"]
    assert (r.moved, r.recent, r.lumma, r.lumma_median_ms) == (20, 20, 20, 200)


def test_recorded_trace_roundtrip(tmp_path):
    path = tmp_path / "t.csv"
    path.write_text("t_ms,x,y\n" + "".join(f"{t},{t // 10},5\n" for t in range(0, 30_001, 10)))
    trace = load_trace(path)
    assert trace[1] == (10, 1, 5)
    r = evaluate("recorded", [trace])
    assert (r.moved, r.recent, r.lumma) == (1, 1, 1)


def test_load_trace_rejects_unordered_times(tmp_path):
    path = tmp_path / "t.csv"
    path.write_text("t_ms,x,y\n0,1,1\n0,2,2\n")
    with pytest.raises(ValueError):
        load_trace(path)


def test_table_lists_every_row(rows):
    table = format_table(list(rows.values()))
    assert table.count("\n") == len(rows) + 1
    assert "| idle | 20 | 0/20 | 0/20 | 0/20 | never |" in table
