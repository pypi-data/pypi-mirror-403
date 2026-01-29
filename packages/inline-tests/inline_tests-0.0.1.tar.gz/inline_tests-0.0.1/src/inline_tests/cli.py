# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""CLI entry point: `itest` wraps pytest with --inline-tests."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

from . import test


def _run_strip(args: list[str]) -> int:
    """Run the strip command."""
    from .strip import strip_directory, strip_file

    if len(args) < 2:
        print("Usage: itest strip <src> -o <dst>", file=sys.stderr)
        return 2

    src = Path(args[0])
    if args[1] != "-o" or len(args) < 3:
        print("Usage: itest strip <src> -o <dst>", file=sys.stderr)
        return 2

    dst = Path(args[2])

    if not src.exists():
        print(f"Source not found: {src}", file=sys.stderr)
        return 1

    if src.is_file():
        strip_file(src, dst)
        print(f"Stripped: {src} -> {dst}")
    else:
        for path in strip_directory(src, dst):
            print(f"Stripped: {path}")

    return 0


def main() -> int:
    """Run pytest with --inline-tests, or subcommands like 'strip'."""
    if len(sys.argv) > 1 and sys.argv[1] == "strip":
        return _run_strip(sys.argv[2:])

    return pytest.main(["--inline-tests", *sys.argv[1:]])


if __name__ == "__main__":
    sys.exit(main())


# --- Self-hosted tests ---


@test
def cli_invokes_pytest():
    """itest --help shows pytest help."""
    result = subprocess.run([sys.executable, "-m", "inline_tests.cli", "--help"], capture_output=True, text=True)
    assert result.returncode == 0


@test
def cli_forwards_args():
    """itest --version shows pytest version."""
    result = subprocess.run([sys.executable, "-m", "inline_tests.cli", "--version"], capture_output=True, text=True)
    assert "pytest" in result.stdout


@test
def cli_strip_shows_usage():
    """itest strip without args shows usage."""
    result = subprocess.run([sys.executable, "-m", "inline_tests.cli", "strip"], capture_output=True, text=True)
    assert result.returncode == 2
    assert "Usage" in result.stderr


@test
def cli_strip_file(tmp_path: Path) -> None:
    """itest strip works on a single file."""
    src = tmp_path / "src.py"
    dst = tmp_path / "dst.py"
    src.write_text("@test\ndef remove(): pass\ndef keep(): pass")

    result = subprocess.run(
        [sys.executable, "-m", "inline_tests.cli", "strip", str(src), "-o", str(dst)], capture_output=True, text=True
    )
    assert result.returncode == 0
    content = dst.read_text()
    assert "keep" in content
    assert "remove" not in content
