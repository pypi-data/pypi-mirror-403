# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Type definitions for inline-tests."""

from __future__ import annotations

from enum import Enum
from typing import Final


class DecoratorName(str, Enum):
    """Supported decorator names for inline tests."""

    TEST = "test"
    IT = "it"

    def __str__(self) -> str:
        return self.value


MARKER: Final[str] = "__inline_test__"
"""Attribute name set on decorated test functions/classes."""

DECORATOR_NAMES: Final[frozenset[str]] = frozenset(d.value for d in DecoratorName)
"""Set of all valid decorator name strings for fast lookup."""
