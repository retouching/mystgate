import ast
import tokenize
from pathlib import Path
from typing import Final

from tests.constants import ROOT

SOURCE_DIRS: Final[tuple[Path, ...]] = (ROOT / "mystgate", ROOT / "tests")
ALLOWED_COMMENT_PREFIXES: Final[tuple[str, ...]] = ("# noqa:", "# type: ignore[")


class TestLayout:
    @staticmethod
    def python_files() -> list[Path]:
        """Return all Python source files under package and tests."""
        files: list[Path] = []
        for folder in SOURCE_DIRS:
            files.extend(sorted(folder.rglob("*.py")))
        return files

    @staticmethod
    def is_dunder(name: str) -> bool:
        """Check whether an identifier is a Python dunder name."""
        return len(name) > 4 and name.startswith("__") and name.endswith("__")

    def test_no_comments_except_pragmas(self) -> None:
        """Verify no Python file contains comments outside noqa or type ignore."""
        violations: list[str] = []
        for path in self.python_files():
            with path.open("rb") as handle:
                for token in tokenize.tokenize(handle.readline):
                    if token.type != tokenize.COMMENT:
                        continue
                    if not token.string.startswith(ALLOWED_COMMENT_PREFIXES):
                        violations.append(f"{path.relative_to(ROOT)}:{token.start[0]}: {token.string}")
        assert not violations, "\n".join(violations)

    def test_no_protocol_declarations(self) -> None:
        """Verify no Protocol class is declared anywhere in the repository."""
        violations: list[str] = []
        for path in self.python_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "Protocol":
                        violations.append(f"{path.relative_to(ROOT)}:{node.lineno}: {node.name}")
                    if isinstance(base, ast.Attribute) and base.attr == "Protocol":
                        violations.append(f"{path.relative_to(ROOT)}:{node.lineno}: {node.name}")
        assert not violations, "\n".join(violations)

    def test_no_leading_underscore_names(self) -> None:
        """Verify no module, class, function, or parameter starts with an underscore."""
        violations: list[str] = []
        for path in self.python_files():
            stem = path.stem
            if stem.startswith("_") and not self.is_dunder(stem):
                violations.append(f"{path.relative_to(ROOT)}: module name {stem}")
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if (
                    isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name.startswith("_")
                    and not self.is_dunder(node.name)
                ):
                    violations.append(f"{path.relative_to(ROOT)}:{node.lineno}: {node.name}")
                if isinstance(node, ast.arg) and node.arg.startswith("_") and node.arg != "_":
                    violations.append(f"{path.relative_to(ROOT)}:{node.lineno}: arg {node.arg}")
        assert not violations, "\n".join(violations)

    def test_docstrings_only_on_functions_and_methods(self) -> None:
        """Verify every function and method has a docstring while modules and classes do not."""
        violations: list[str] = []
        for path in self.python_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            if ast.get_docstring(tree) is not None:
                violations.append(f"{path.relative_to(ROOT)}:1: module docstring forbidden")
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and ast.get_docstring(node) is not None:
                    violations.append(
                        f"{path.relative_to(ROOT)}:{node.lineno}: class docstring forbidden on {node.name}"
                    )
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and ast.get_docstring(node) is None:
                    violations.append(f"{path.relative_to(ROOT)}:{node.lineno}: missing docstring on {node.name}")
        assert not violations, "\n".join(violations)

    def test_all_tests_live_inside_classes(self) -> None:
        """Verify every test function under tests/ is a method of a Test* class."""
        violations: list[str] = []
        for path in sorted((ROOT / "tests").rglob("test_*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                    violations.append(f"{path.relative_to(ROOT)}:{node.lineno}: top-level {node.name}")
        assert not violations, "\n".join(violations)
