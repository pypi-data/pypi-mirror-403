# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Pytest plugin for collecting @test-decorated inline tests."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from ._types import DECORATOR_NAMES, MARKER


if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = ["pytest_addoption", "pytest_collect_file", "pytest_collection_modifyitems", "pytest_pycollect_makeitem"]


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--inline-tests", action="store_true", help="Collect @test-decorated inline tests.")


def pytest_collect_file(file_path: Path, parent: pytest.Collector) -> pytest.Module | None:
    if not parent.config.getoption("--inline-tests"):
        return None
    if file_path.suffix != ".py" or file_path.name.startswith("test_") or file_path.name.endswith("_test.py"):
        return None
    try:
        src = file_path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not any(f"@{name}" in src for name in DECORATOR_NAMES):
        return None
    try:
        tree = ast.parse(src, filename=str(file_path))
    except SyntaxError:
        return None
    if not _has_test_decorator(tree):
        return None
    return InlineModule.from_parent(parent, path=file_path)


@pytest.hookimpl(tryfirst=True)
def pytest_pycollect_makeitem(
    collector: pytest.Module | pytest.Class, name: str, obj: object
) -> list[pytest.Item] | None:
    """Create test items for @test-decorated functions."""
    if not isinstance(collector, InlineModule | InlineClass):
        return None
    if not callable(obj) or isinstance(obj, type):
        return None
    if not getattr(obj, MARKER, False):
        return None
    # Create Function items via _genfunctions (handles parametrize, fixtures, etc.)
    return list(collector._genfunctions(name, obj))


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Remove duplicate items from default Module for files we handle with InlineModule."""
    if not config.getoption("--inline-tests"):
        return

    inline_files: set[Path] = set()
    for item in items:
        parent = item.parent
        while parent is not None:
            if isinstance(parent, InlineModule):
                inline_files.add(item.path)
                break
            parent = getattr(parent, "parent", None)

    items[:] = [item for item in items if _is_inline_item(item) or item.path not in inline_files]


def _is_inline_item(item: pytest.Item) -> bool:
    """Check if item comes from our InlineModule/InlineClass collectors."""
    parent = item.parent
    while parent is not None:
        if isinstance(parent, InlineModule | InlineClass):
            return True
        parent = getattr(parent, "parent", None)
    return False


def _has_test_decorator(tree: ast.AST) -> bool:
    """AST check for @test or @it decorators on functions/classes."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            for dec in node.decorator_list:
                name = dec.func.id if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) else None
                name = name or (dec.id if isinstance(dec, ast.Name) else None)
                if name in DECORATOR_NAMES:
                    return True
    return False


class InlineModule(pytest.Module):
    """Collector for @test/@it decorated items in non-test files."""

    def collect(self) -> Iterator[pytest.Function | pytest.Class]:
        """Collect @test-decorated functions and classes."""
        mod = self._getobj()
        for name, obj in vars(mod).items():
            if getattr(obj, "__module__", None) != mod.__name__:
                continue
            if callable(obj) and not isinstance(obj, type) and getattr(obj, MARKER, False):
                # Route through hook chain so pytest-asyncio can convert async functions
                res = self.ihook.pytest_pycollect_makeitem(collector=self, name=name, obj=obj)
                if res is not None:
                    yield from res if isinstance(res, list) else [res]
            elif isinstance(obj, type) and _class_has_test_methods(obj):
                yield InlineClass.from_parent(self, name=name, callobj=obj)


def _class_has_test_methods(cls: type) -> bool:
    """Check if class has any methods with MARKER."""
    return any(getattr(m, MARKER, False) for m in vars(cls).values() if callable(m))


class InlineClass(pytest.Class):
    """Collector for @test-decorated classes."""

    def __init__(self, name: str, parent: pytest.Collector, callobj: type, **kw: Any) -> None:
        super().__init__(name, parent, **kw)
        self._callobj = callobj

    def _getobj(self) -> type:
        return self._callobj

    def collect(self) -> Iterator[pytest.Function]:
        for name, method in vars(self._callobj).items():
            if getattr(method, MARKER, False):
                # Route through hook chain so pytest-asyncio can convert async methods
                res = self.ihook.pytest_pycollect_makeitem(collector=self, name=name, obj=method)
                if res is not None:
                    yield from res if isinstance(res, list) else [res]
