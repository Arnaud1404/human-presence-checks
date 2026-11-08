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


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_every_function_opens_with_a_one_line_summary(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))

    missing = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            continue
        if node.name.startswith("test_"):
            continue

        doc = ast.get_docstring(node)
        if doc is None:
            missing.append(f"{node.name}: no docstring")
            continue

        summary = doc.split("\n\n")[0]
        if "\n" in summary or not summary.endswith("."):
            missing.append(f"{node.name}: summary is not one sentence on one line")

    assert not missing, f"{missing} (AGENTS.md)"
