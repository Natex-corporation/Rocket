# Architecture

```text
OpenRocket airframe ─┐
measured mass/CG ────┼─> RocketPy 6-DOF + Monte Carlo ─> truth/sensor logs
weather/thrust ──────┘                                  │
                                                       v
NASA CEA/RocketCEA ─> engine performance         estimator replay
                                                       │
KiCad properties ───> BOM export                 phase/guidance inputs
                                                       │
                                                PX4 SITL/HITL target
```

The repository's core has no third-party runtime dependency. This makes unit tests fast and
lets a reviewer trace every equation. High-fidelity work is delegated to established tools.

The `dispersion` command provides a reproducible smoke-test uncertainty sweep. It should be used
to catch sensitivity and margin regressions in CI, then replaced or cross-checked with RocketPy's
full stochastic/Monte Carlo facilities for flight decisions.

## Coordinate and unit contract

- Configuration and CSV files use SI units, stated in every field name.
- The IMU schema uses body **forward-right-down (FRD)** axes.
- Altitude is metres above the launch point unless a field explicitly says MSL.
- The flight reference model is one-dimensional and upward-positive.
- Time is monotonic seconds. Logs must not contain duplicate timestamps.

## Repository map

- `src/rocket_workbench/engine.py`: ideal-nozzle check and RocketCEA adapter.
- `src/rocket_workbench/flight.py`: deterministic vertical flight/recovery model.
- `src/rocket_workbench/imu.py`: log schema, demonstrator filters, phase detector.
- `src/rocket_workbench/bom.py`: BOM format validator.
- `examples/`: configuration and non-certified sample thrust data.
- `tests/`: physics bounds and integration smoke tests.
- `bom/`: starter system BOM; future KiCad-derived exports belong here.

## Verification ladder

Every model change should pass, in order: unit tests, conservation/limit checks, comparison with
OpenRocket, comparison with RocketPy, logged ground test, SIL, PIL, HIL, and a written flight-
readiness review. Record tool versions, inputs, commit ID, and uncertainty assumptions with every
result used in a design decision.
