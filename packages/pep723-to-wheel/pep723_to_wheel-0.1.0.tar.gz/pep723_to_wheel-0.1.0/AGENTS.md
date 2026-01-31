# Agent guide for pep723-to-wheel

## Repository overview
- `src/pep723_to_wheel/` contains the library and CLI implementation.
- `tests/` holds pytest coverage for core behavior.
- `pyproject.toml` defines dependencies, entry points, and tooling.

## Development setup
- Requires Python 3.12+ (see `pyproject.toml`).
- Environment management is with uv.
- Run Python and related CLI tools via `uv run` so they use the uv virtualenv.

## Common commands
- Run tests: `make test`
- Run type checks: `make typecheck`
- Run ruff checks: `make ruff`
- Run all checks: `make all-tests`

## Style and conventions
- TDD for all code development - write test, then run to verify it fails, then develop, then verify the test passes.
- All tasks should end by running `make all-tests` and verifying it passes.
- Prefer updating or adding pytest tests in `tests/` for behavior changes.
- For CLI changes, update both `src/pep723_to_wheel/cli.py` and any relevant tests.
- Target modern Python 3.12+ syntax, no need to be backwards compatible.

## Tips
- Use `pep723_to_wheel.core` for the main build/import logic.
- The CLI entry point is `pep723_to_wheel.cli:app`.
