# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Hatchling build hook that strips @test functions before packaging."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class InlineTestsHook(BuildHookInterface):
    """Strip @test functions during wheel/sdist builds.

    Hatchling's force_include reserves target paths, causing originals to be
    skipped. We copy stripped files to a temp dir and force_include from there.

    """

    PLUGIN_NAME = "inline_tests"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._temp_dirs: list[str] = []

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:  # noqa: ARG002
        """Strip @test functions from source before build."""
        if self.target_name not in ("wheel", "sdist"):
            return

        from .strip import strip_directory

        root = Path(self.root)
        sources = self.config.get("sources", ["src"])
        if isinstance(sources, str):
            sources = [sources]

        total_stripped = 0
        for source in sources:
            src_dir = root / source
            if not src_dir.exists():
                continue

            temp_dir = tempfile.mkdtemp(prefix=f"itest_strip_{source}_")
            self._temp_dirs.append(temp_dir)
            stripped_dst = Path(temp_dir)

            for _ in strip_directory(src_dir, stripped_dst):
                total_stripped += 1

            build_data.setdefault("force_include", {})
            for f in stripped_dst.rglob("*.py"):
                build_data["force_include"][str(f)] = str(f.relative_to(stripped_dst))

        if total_stripped:
            self.app.display_info(f"Stripped {total_stripped} files")

    def finalize(self, version: str, build_data: dict[str, Any], artifact_path: str) -> None:  # noqa: ARG002
        """Remove temp directories created during initialize."""
        for temp_dir in self._temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
