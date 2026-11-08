from pathlib import Path

from bench import format_table, simulate

README = Path(__file__).resolve().parent.parent / "README.md"


def test_readme_table_matches_the_bench():
    lines = README.read_text(encoding="utf-8").splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("| simulator |"):
            start = i
            break
    assert start is not None, "README has no bench table"
    end = start
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    assert "\n".join(lines[start:end]) == format_table(simulate(seeds=100))
