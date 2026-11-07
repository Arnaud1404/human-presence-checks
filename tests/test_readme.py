from pathlib import Path

from bench import format_table, simulate

README = Path(__file__).resolve().parent.parent / "README.md"


def test_readme_table_matches_the_bench():
    lines = README.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| simulator |"))
    end = next(i for i in range(start, len(lines)) if not lines[i].startswith("|"))
    assert "\n".join(lines[start:end]) == format_table(simulate(seeds=100))
