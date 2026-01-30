# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Inline tests for Python — colocate tests with implementation, Rust-style."""

from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import version
from typing import TypeVar, overload

from ._types import MARKER


__all__ = ["MARKER", "__version__", "it", "test"]
__version__ = version("inline-tests")

T = TypeVar("T")


@overload
def test(obj: T) -> T: ...
@overload
def test(*, reason: str | None = ...) -> Callable[[T], T]: ...


def test(obj: T | None = None, *, reason: str | None = None) -> T | Callable[[T], T]:
    """Mark a function or class as an inline test."""

    def mark(target: T) -> T:
        setattr(target, MARKER, reason or True)
        return target

    return mark(obj) if obj is not None else mark


it = test


# --- Self-hosted tests ---


@test
def decorator_sets_marker():
    """Bare @test sets MARKER to True."""

    @test
    def f():
        pass

    assert getattr(f, MARKER) is True


@test
def decorator_stores_reason():
    """@test(reason=...) stores the string."""

    @test(reason="regression")
    def f():
        pass

    assert getattr(f, MARKER) == "regression"


@test
def decorator_preserves_identity():
    """Decorated function is the same object."""

    def f():
        return 42

    assert test(f) is f


@test
def it_aliases_test():
    """@it is @test."""
    assert it is test


@test
class ClassDecoration:
    """@test on classes."""

    @test
    def class_gets_marker(self):
        """Class receives MARKER attribute."""
        assert getattr(ClassDecoration, MARKER) is True
