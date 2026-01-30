# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Strip @test-decorated functions from Python source files."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

from . import test


if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = ["strip_directory", "strip_file", "strip_source"]

# Decorator names that mark test functions
TEST_DECORATORS = frozenset({"test", "it"})


def _is_inline_tests_import(node: ast.stmt) -> bool:
    """Check if a statement is an inline_tests import to remove.

    Removes:
      - `from inline_tests import test`
      - `from inline_tests import test, it`
      - `import inline_tests`

    Preserves:
      - `from inline_tests import strip` (non-decorator imports)
      - `from inline_tests import test, strip` -> `from inline_tests import strip`

    """
    if isinstance(node, ast.Import):
        return any(alias.name == "inline_tests" for alias in node.names)

    if isinstance(node, ast.ImportFrom):
        module = node.module or ""
        if not (module == "inline_tests" or module.startswith("inline_tests.")):
            return False
        return all(alias.name in TEST_DECORATORS for alias in node.names)

    return False


def _clean_mixed_import(node: ast.ImportFrom) -> ast.ImportFrom | None:
    """Remove test/it from a mixed import, return None if nothing left."""
    remaining = [alias for alias in node.names if alias.name not in TEST_DECORATORS]
    if not remaining:
        return None
    node.names = remaining
    return node


def _is_test_decorator(node: ast.expr) -> bool:
    """Check if a decorator node is @test or @it (with or without call)."""
    if isinstance(node, ast.Name):
        return node.id in TEST_DECORATORS
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id in TEST_DECORATORS
    return False


def _has_test_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> bool:
    """Check if a function/class has @test or @it decorator."""
    return any(_is_test_decorator(d) for d in node.decorator_list)


class TestStripper(ast.NodeTransformer):
    """AST transformer that removes @test-decorated functions, classes, and imports."""

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Process module body, stripping tests and inline_tests imports."""
        new_body = []
        for stmt in node.body:
            if _is_inline_tests_import(stmt):
                continue

            if isinstance(stmt, ast.ImportFrom):
                module = stmt.module or ""
                if module == "inline_tests" or module.startswith("inline_tests."):
                    cleaned = _clean_mixed_import(stmt)
                    if cleaned:
                        new_body.append(cleaned)
                    continue

            result = self.visit(stmt)
            if result is not None:
                new_body.append(result)

        node.body = new_body
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef | None:
        if _has_test_decorator(node):
            return None
        self.generic_visit(node)
        node.body = [s for s in node.body if not _is_inline_tests_import(s)]
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef | None:
        if _has_test_decorator(node):
            return None
        self.generic_visit(node)
        node.body = [s for s in node.body if not _is_inline_tests_import(s)]
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef | None:
        if _has_test_decorator(node):
            return None
        node.body = [
            child
            for child in node.body
            if not (isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and _has_test_decorator(child))
        ]
        node.body = [s for s in node.body if not _is_inline_tests_import(s)]
        return node


def strip_source(source: str) -> str:
    """Remove @test-decorated functions from Python source code.

    Args:
        source: Python source code as a string.

    Returns:
        Source code with test functions removed.
    """
    tree = ast.parse(source)
    stripper = TestStripper()
    stripped = stripper.visit(tree)
    ast.fix_missing_locations(stripped)
    return ast.unparse(stripped)


def strip_file(src: Path, dst: Path) -> None:
    """Strip tests from a Python file and write to destination.

    Args:
        src: Source file path.
        dst: Destination file path.
    """
    source = src.read_text(encoding="utf-8")
    stripped = strip_source(source)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(stripped, encoding="utf-8")


def strip_directory(src: Path, dst: Path) -> Iterator[Path]:
    """Strip tests from all Python files in a directory.

    Args:
        src: Source directory.
        dst: Destination directory.

    Yields:
        Paths of stripped files.
    """
    for py_file in src.rglob("*.py"):
        rel = py_file.relative_to(src)
        out = dst / rel
        strip_file(py_file, out)
        yield out


# --- Self-hosted tests (stripped from published package) ---


@test
def strips_simple_test_function():
    """@test function is removed."""
    source = """
def keep_me():
    pass

@test
def remove_me():
    pass

def also_keep():
    return 1
"""
    result = strip_source(source)
    assert "keep_me" in result
    assert "also_keep" in result
    assert "remove_me" not in result


@test
def strips_test_with_reason():
    """@test(reason=...) function is removed."""
    source = """
@test(reason="regression")
def remove_me():
    pass

def keep_me():
    pass
"""
    result = strip_source(source)
    assert "keep_me" in result
    assert "remove_me" not in result


@test
def strips_it_alias():
    """@it function is removed."""
    source = """
@it
def should_be_removed():
    pass

def keep():
    pass
"""
    result = strip_source(source)
    assert "keep" in result
    assert "should_be_removed" not in result


@test
def strips_async_test():
    """Async @test function is removed."""
    source = """
@test
async def async_test():
    pass

async def async_keep():
    pass
"""
    result = strip_source(source)
    assert "async_keep" in result
    assert "async_test" not in result


@test
def strips_test_class():
    """@test class is removed entirely."""
    source = """
@test
class TestSuite:
    def test_one(self):
        pass

class KeepMe:
    pass
"""
    result = strip_source(source)
    assert "KeepMe" in result
    assert "TestSuite" not in result


@test
def strips_test_methods_from_non_test_class():
    """@test methods inside non-test classes are removed."""
    source = """
class MyClass:
    def regular_method(self):
        pass

    @test
    def test_method(self):
        pass

    def another_regular(self):
        pass
"""
    result = strip_source(source)
    assert "MyClass" in result
    assert "regular_method" in result
    assert "another_regular" in result
    assert "test_method" not in result


@test
def strips_inline_tests_import():
    """inline_tests imports are stripped."""
    source = """
from inline_tests import test
import os

@test
def remove_me():
    pass

def keep():
    return os.getcwd()
"""
    result = strip_source(source)
    assert "import os" in result
    assert "keep" in result
    assert "remove_me" not in result
    assert "inline_tests" not in result


@test
def preserves_non_decorator_imports():
    """Non-decorator inline_tests imports are preserved."""
    source = """
from inline_tests.strip import strip_source

def use_strip():
    return strip_source("code")
"""
    result = strip_source(source)
    assert "strip_source" in result
    assert "use_strip" in result


@test
def cleans_mixed_imports():
    """Mixed imports keep non-decorator parts."""
    source = """
from inline_tests import test, it
from inline_tests.strip import strip_source

def keep():
    pass
"""
    result = strip_source(source)
    assert "strip_source" in result
    assert "keep" in result
    assert "from inline_tests import test" not in result


@test
def preserves_other_decorators():
    """Non-test decorators are preserved."""
    source = """
@property
def my_prop(self):
    pass

@staticmethod
def my_static():
    pass

@test
def remove_me():
    pass
"""
    result = strip_source(source)
    assert "my_prop" in result
    assert "my_static" in result
    assert "remove_me" not in result


@test
def handles_empty_result():
    """File with only tests produces minimal valid Python."""
    source = """
@test
def only_test():
    pass
"""
    result = strip_source(source)
    # Should be empty or whitespace, but valid Python
    ast.parse(result)  # Should not raise
