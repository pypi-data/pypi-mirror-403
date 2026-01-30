# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Hatchling plugin registration."""

from __future__ import annotations

from hatchling.plugin import hookimpl

from .hatch import InlineTestsHook


@hookimpl
def hatch_register_build_hook() -> type[InlineTestsHook]:
    """Register the inline_tests build hook."""
    return InlineTestsHook
