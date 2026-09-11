# Contributing

This project is a student-team engineering workbench. Keep changes reviewable, reproducible, and
explicit about their validity limits.

## Before opening a change

```powershell
$env:PYTHONPATH = "src"
python -m ruff check .
python -m ruff format --check .
python -m pytest -q --basetemp=test-run-temp
python -m compileall -q src tests integrations
```

If the local environment cannot execute the checked-in virtual environment, use a fresh Python
environment and install `-e ".[dev]"`. Do not commit `.venv`, generated `results/`, caches, or
temporary dispersion files.

## Modeling changes

- State units and coordinate frames in field names or docstrings.
- Add a regression test for every corrected bug or newly supported input.
- Keep nominal examples fictional unless their source and revision are documented.
- Compare high-fidelity changes against RocketPy/OpenRocket where applicable.
- Never imply that the built-in point-mass, estimator, or advisory code is flight-qualified.

## Hardware and BOM changes

Use the KiCad schematic as the source of truth once a board exists. Record manufacturer, exact MPN,
package, datasheet, revision/date, and any acceptable alternates. Separate references from parts
that still need requirements, regulatory review, stock checks, or team approval.

## Review minimum

Every flight-relevant change needs one independent technical reviewer and a short note describing
changed assumptions, verification evidence, and remaining uncertainty. Hardware activation paths
also need a safety reviewer; analysis-only changes do not grant permission to operate hardware.
