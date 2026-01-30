# Python Playwright Framework

A minimal, clean Python test automation framework built with **pytest** and **Playwright**, focused on:
- deterministic local execution
- fast feedback
- enforced code quality via pre-commit hooks

This repository is intentionally kept simple as a foundation for further expansion.

---

## Requirements

- Python 3.10+ (tested locally with a virtual environment)
- Git
- Node.js (required by Playwright)

---

## Project Structure
```
├── tests/
│ ├── conftest.py # pytest + Playwright fixtures and failure artifacts
│ └── test_smoke.py # example smoke test
├── artifacts/
│ ├── screenshots/ # screenshots captured on test failure
│ └── traces/ # Playwright traces (optional)
├── reports/ # test reports (if enabled)
├── .pre-commit-config.yaml
├── pyproject.toml
└── README.md
```
## Setup

### 1) Create and activate virtual environment
```
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate         # Windows PowerShell
```

### 2) Install dependencies
```
pip install -r requirements.txt
```
Install Playwright browsers:
```
python -m playwright install
```

## Running Tests

### Run all tests:

```
pytest
```
### Run a specific test:

```
pytest tests/test_smoke.py
```

### Run in headed mode:

```
pytest --headed
```

### Select browser:

```
pytest --browser chromium
pytest --browser firefox
pytest --browser webkit
```

### Slow down actions (milliseconds):

```
pytest --slowmo 200
```
## Parallel Execution (pytest-xdist)

This project supports running tests in parallel using **pytest-xdist**.

### Install

```
 pip install pytest-xdist 
 ```

### Run tests in parallel

Run with an automatic number of workers:

```
pytest -n auto
 ```


Run with a fixed number of workers (example: 4):

```
 pytest -n 4
  ```

## Artifacts on Failure

On test failure, the framework automatically captures:

### Screenshot (PNG)

Playwright trace (ZIP, optional)

Artifacts are stored under:
```
artifacts/
├── screenshots/
└── traces/
```

### Enable tracing (optional)
```
PW_TRACE=true pytest
```

Traces are saved only when a test fails.

## Pre-commit

This project uses pre-commit to enforce code quality checks before each commit.

### Checks included

Ruff – fast Python linting with auto-fixes

Ruff Format – consistent code formatting

Mypy – static type checking (ignores missing third-party stubs)

### One-time setup
```
pip install pre-commit
pre-commit install

```
### First run (recommended)
```
pre-commit run --all-files
```


After setup, hooks run automatically on every git commit.
If a hook modifies files or fails, re-stage the changes and commit again.

## Notes

- All paths are resolved relative to the repository root

- Artifacts are created only for failed tests

- The framework is intentionally minimal and designed to evolve incrementally