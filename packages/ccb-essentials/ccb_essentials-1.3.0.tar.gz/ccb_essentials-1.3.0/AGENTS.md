# AI Coding Instructions

## Project Overview

`ccb-essentials` is a small collection of thin, typed helpers around the Python standard library (argparse, filesystem, logging, signal, sqlite3, subprocess). Look for simple wrappers, explicit typing, and small utility classes rather than heavy frameworks.

## Architecture & Key Patterns

### Key directories/files

  - `ccb_essentials/` — implementation modules (see `filesystem.py`, `sqlite3.py`, `subprocess.py`, `logger.py`, `argparse.py`, `signal.py`).
  - `docs/` — human-facing usage examples and API notes (each module has a `.md` with concrete examples).
  - `tests/` — pytest test-suite to validate behavior.
  - `docs/dev.md` and `bin/lint.sh` — canonical development commands (uses uv).

### Dev workflow (exact commands)

  - Install & sync: `uv sync --extra dev`
  - Run tests: `uv run pytest` (or `pytest` if you use the environment directly)
  - Lint: `uv run bin/lint.sh` (see `bin/lint.sh` for exact linters used)
  - Build: `uv build`

### Style & conventions to preserve

  - Keep helpers small and explicit — functions typically wrap stdlib calls and return basic types (e.g. `Path`, `Optional[Path]`, `str`). Avoid introducing heavy abstractions.
  - Prefer `pathlib.Path` and explicit checks: many APIs accept `str|Path` and return `Path` (see `real_path`, `assert_real_dir`, `assert_real_file`).
  - Typing: package exposes `py.typed` so maintain type signatures and mypy-friendly code.
  - Doc-driven examples: usage examples in `docs/*.md` are the authoritative behavior examples — copy examples from there when writing tests or docs.

### Module-specific notes / gotchas

  - `ccb_essentials/filesystem.py`: `real_path(..., mkdir=True)` will create directories; `assert_real_*` functions raise standard file exceptions (`FileNotFoundError`, `NotADirectoryError`, `OSError`). Use these helpers to validate CLI inputs.
  - `ccb_essentials/sqlite3.py`: `Sqlite3` wraps `sqlite3.Connection`. Migrations are plain callables of signature `(conn, version) -> bool`; the library expects migrations list length to equal final schema version. Setting `application_id` is used to prevent accidentally opening the wrong DB file.
  - `ccb_essentials/subprocess.py`: `subprocess_command()` uses `shell=True` and returns `Optional[str]` (returns `None` on non-zero exit). When calling from higher-level code, handle `None` explicitly; to raise on stderr set `raise_std_error=True`.
  - `ccb_essentials/logger.py`: `StreamToLogger` is a file-like adapter to funnel `print()`/stdout into logging — used in examples to replace `sys.stdout`/`sys.stderr`.
  - `ccb_essentials/signal.py`: `DelayedKeyboardInterrupt` is a context manager to postpone `KeyboardInterrupt` signals during a critical section.

## Developer Workflow

### Testing and changes

  - When adding or changing behavior, add or update tests under `tests/` and mirror examples from `docs/` where appropriate.
  - Run `uv run pytest` locally. Tests are small and rely on the helpers' observable behavior rather than complex fixtures.

### What to look for when editing

  - Keep public function signatures stable; consumers may rely on return types (`Optional[Path]` vs raising). If you must change exception behavior, update docs and tests.
  - Preserve simple, explicit error types (don't wrap simple OSErrors in custom exceptions unless justified).

### Where to find examples to copy or test against

  - See `docs/filesystem.md`, `docs/sqlite3.md`, `docs/subprocess.md`, `docs/logger.md`, and `docs/signal.md` for canonical code snippets.
