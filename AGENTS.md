# Repository Guidelines

## Project Structure & Module Organization
- `src/parlant/`: Core server, SDK, adapters, and module packages; respect existing subpackage boundaries when adding features.
- `tests/`: Pytest suites split by domain (`api`, `adapters`, `core`, `sdk`, `e2e`); BDD `.feature` files in `tests/core/.../features` live beside their step implementations.
- `examples/`: Runnable docs samples; keep dependencies light and import via the installed package.
- `docs/`: Customer-facing guides and media (`demo.gif`, logos); update whenever user-visible behavior shifts.
- `scripts/`: CI utilities (`lint.py`, `publish.py`, etc.); extend these before introducing new tooling entrypoints.

## Build, Test, and Development Commands
- `poetry install --with dev`: Install runtime and dev dependencies.
- `poetry run ruff check src tests` / `poetry run ruff format .`: Enforce linting and formatting.
- `poetry run mypy src tests`: Apply strict typing per `mypy.ini`.
- `poetry run pytest`: Run the deterministic suite.
- `poetry run pytest tests/core/stable --maxfail=1`: Exercise stable BDD journeys; coordinate additional plans through `pytest_stochastics.json`.
- `poetry run scripts/lint.py`: Combined lint gate mirroring CI.

## Coding Style & Naming Conventions
- Ruff defaults apply: 4-space indentation, 100-character lines, double-quoted strings, Black-compatible formatting.
- Packages stay snake_case, classes PascalCase, constants UPPER_SNAKE_CASE.
- Provide explicit type hints and reuse shared dataclasses or TypedDicts for structured payloads.
- Keep async flows non-blocking—prefer provided adapters and avoid bare `open()` inside async functions.

## Testing Guidelines
- Mirror source file names (e.g., `src/parlant/core/journeys.py` → `tests/core/test_journeys.py`) and colocate fixtures in the relevant `conftest.py`.
- Parametrize scenarios instead of duplicating fixtures; lean on `tests/test_utilities.py` and `tests/tool_utilities.py`.
- House BDD coverage under `tests/core` and align expectations with the policies recorded in `pytest_stochastics.json`.
- Note the commands executed (including BDD runs) in the PR description.

## Commit & Pull Request Guidelines
- Use imperative commit subjects (`Add relationship handling in JourneyModule`) and append a DCO `Signed-off-by` trailer (see `CONTRIBUTING.md`).
- Keep commits focused; squash fixups before requesting review.
- Pull requests must explain scope, link tracking issues, list executed tests, and attach logs or screenshots when altering APIs or demos.
- Request review only after local checks and relevant CI workflows pass; track follow-up work in linked issues rather than TODO comments.
