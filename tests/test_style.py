import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SOURCES = sorted([*ROOT.glob("*.py"), *ROOT.glob("tests/*.py")])
COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_no_comprehensions(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))

    lines = []
    for node in ast.walk(tree):
        if isinstance(node, COMPREHENSIONS):
            lines.append(node.lineno)

    assert not lines, f"comprehension on lines {sorted(lines)}: write a for loop (AGENTS.md)"
