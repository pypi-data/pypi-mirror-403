# inline-tests

<div align="center">
  <strong>"Just itest it."</strong>
  <br>
  <strong>"Does it pass the (eye) itest?"</strong> 👁️
</div>

<br />

<div align="center">
  <img src="https://raw.githubusercontent.com/dedalus-labs/inline-tests-python/main/assets/logo.svg" alt="inline-tests" width="100">
</div>

<br />

<div align="center">

[![PyPI](https://img.shields.io/pypi/v/inline-tests)](https://pypi.org/project/inline-tests/)
[![Python](https://img.shields.io/pypi/pyversions/inline-tests)](https://pypi.org/project/inline-tests/)
[![License](https://img.shields.io/pypi/l/inline-tests)](https://github.com/dedalus-labs/inline-tests-python/blob/main/LICENSE)
[![CI](https://github.com/dedalus-labs/inline-tests-python/actions/workflows/ci.yml/badge.svg)](https://github.com/dedalus-labs/inline-tests-python/actions/workflows/ci.yml)

</div>

---

## The Problem

Tests live in one place. Code lives in another. You change a function and forget to update its test. Or you write the test later. Or never.

The test file mirrors the source file. `src/auth/login.py` becomes `tests/auth/test_login.py`. Two parallel hierarchies drifting apart.

Rust solved this years ago. Tests live next to the code they test. You see them together. You change them together. They can't drift because they're in the same file.

Python never had this. Until now.

## The Solution

```python
# auth/login.py
from inline_tests import test

def authenticate(user, password):
    if not user or not password:
        return None
    return verify_credentials(user, password)

@test
def rejects_empty_credentials():
    assert authenticate("", "pass") is None
    assert authenticate("user", "") is None

@test
def accepts_valid_credentials():
    result = authenticate("admin", "secret")
    assert result is not None
```

```bash
itest
```

## Install

```bash
uv tool install inline-tests
```

This gives you `itest` everywhere. For one-off use: `uvx inline-tests`.

<details>
<summary><em>Other install methods</em></summary>

```bash
# As a project dependency
uv add inline-tests --group dev
pip install inline-tests

# With extras
uv tool install inline-tests[full]        # everything
uv tool install inline-tests[essentials]  # async, mock, coverage
```

</details>

## Why This Works

**Tests can't go stale.** When you change the function, the test is right there. You can't miss it.

**Testing becomes part of writing code.** Not a separate phase. Not something you do after. You think about behavior while you're defining it.

**You see the relationship.** Test and implementation side by side. You notice when tests check implementation details instead of behavior. You notice missing edge cases.

**No ceremony.** No mirroring directory structures. No hunting for the right test file. No context switching. Just `@test` and you're done.

## Features

Everything pytest offers, because this *is* pytest.

```python
from inline_tests import test, it

# BDD style
@it
def should_handle_empty_input():
    assert process("") == []

# Async
@test
async def fetches_data():
    result = await fetch("https://api.example.com")
    assert result.status == 200

# Fixtures
@test
def writes_to_disk(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello")
    assert f.read_text() == "hello"

# Parametrize
@test
@pytest.mark.parametrize("x,expected", [(1, 1), (2, 4), (3, 9)])
def squares_correctly(x, expected):
    assert x * x == expected

# Test classes (no decorator needed on class)
class ValidationSuite:
    @test
    def rejects_negative(self):
        assert validate(-1) is False
```

## Extras

| Extra        | What you get                          |
|:-------------|:--------------------------------------|
| `async`      | pytest-asyncio, anyio, pyleak         |
| `mock`       | pytest-mock                           |
| `cov`        | pytest-cov                            |
| `parallel`   | pytest-xdist                          |
| `bench`      | pytest-benchmark                      |
| `property`   | hypothesis                            |
| `http`       | pytest-httpx                          |
| `data`       | faker                                 |
| `essentials` | async + mock + cov                    |
| `full`       | all of the above                      |

## How It Works

The `@test` decorator marks functions with a hidden attribute. When you run `itest`, the plugin scans Python files for this marker using AST parsing. No imports happen until a file actually contains tests. Then pytest collects and runs them normally.

Standard `test_*.py` files work as usual. This is additive.

## Production

**Just ship it.** The `@test` decorator is a no-op at runtime. Tests never execute unless you run `itest`.

**Or strip tests** for minimal deployments:

```bash
itest strip src/ -o dist/
uv build dist/
```

Removes `@test` functions via AST. Original files untouched.

## Development

```bash
git clone https://github.com/dedalus-labs/inline-tests-python
cd inline-tests
uv sync
uv run pytest
```

Built on a modern Python stack. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT

## Links

- [Documentation](https://oss.dedaluslabs.ai/inline-tests-python)
- [Dedalus Labs](https://dedaluslabs.ai)
- [Discord](https://discord.com/invite/RuDhZKnq5R)

---

<div align="center">
  <sub>Dedalus Labs © 2026.</sub>
</div>

---
