# Student Rocket Workbench

A reproducible starting point for a student rocketry team. It joins four workflows:

- engine performance sanity checks, with an optional RocketCEA/NASA CEA backend;
- a fast, transparent vertical point-mass flight model for tests and parameter sweeps;
- IMU/barometer log replay with attitude, altitude/velocity, and flight-phase estimates;
- non-actuating apogee/recovery advisories from estimator logs;
- seeded Monte Carlo dispersion over mass, drag, and thrust scale;
- read-only STL/OBJ CAD inspection with optional `trimesh` geometry metrics;
- read-only OpenRocket `.ork` metadata import;
- RASP `.eng` thrust-curve import for common motor libraries;
- CAD/FEA mass-property CSV import for mass, CG, and inertia checks;
- CFD/RASAero/ANSYS-style aerodynamic polar CSV validation;
- a machine-checked avionics BOM that clearly separates references from placeholders.

The built-in physics is deliberately small and reviewable. **Use RocketPy or OpenRocket for
6-DOF/stability work and RocketCEA/NASA CEA for propulsion decisions.** The internal models are
cross-checks and CI fixtures, not certification evidence.

## Team handbook

See [docs/handbook.md](docs/handbook.md) for the full team handoff: installation, commands,
configuration and CSV contracts, recommended workflow, verification evidence, integrations, and
safety boundaries.

## Quick start (Windows PowerShell)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\rocket-workbench engine examples\engine_lox_methane.toml
.\.venv\Scripts\rocket-workbench flight examples\flight_reference.toml
.\.venv\Scripts\rocket-workbench imu-demo examples\flight_reference.toml
.\.venv\Scripts\rocket-workbench bom-check bom\reference_bom.csv
.\.venv\Scripts\python -m pytest
```

Optional established tools:

```powershell
# 6-DOF trajectory and Monte Carlo analysis
.\.venv\Scripts\python -m pip install -e ".[simulation]"
.\.venv\Scripts\python integrations\rocketpy_reference.py

# NASA CEA wrapper (Fortran compiler/build support may be required on some systems)
.\.venv\Scripts\python -m pip install -e ".[engine]"
.\.venv\Scripts\rocket-workbench engine examples\engine_lox_methane.toml --backend rocketcea
```

Python 3.13 is recommended for the widest binary-wheel compatibility. The package itself also
runs on the Python 3.14 interpreter currently installed in this workspace.

## Commands

| Command | Purpose | Output |
|---|---|---|
| `engine CONFIG` | Ideal-nozzle check or RocketCEA calculation | JSON summary |
| `flight CONFIG` | Reference ascent/coast/recovery simulation | `results/flight.csv` |
| `imu-replay LOG` | Replay a team log in the documented CSV schema | `results/estimate.csv` |
| `imu-demo CONFIG` | End-to-end synthetic sensor/estimator exercise | both CSV files |
| `guidance ESTIMATE` | Advisory-only apogee and recovery analysis | `results/advisory.csv` |
| `dispersion CONFIG` | Seeded uncertainty analysis | `results/dispersion.csv` |
| `bom-check CSV` | Check BOM fields, quantities, and MPN presence | JSON report |
| `cad-info MESH` | Inspect STL/OBJ geometry and normalize units | JSON metadata |
| `openrocket-info FILE` | Inspect OpenRocket project metadata | JSON metadata |
| `mass-info CSV` | Validate CAD/FEA mass-property export | JSON properties |
| `aero-info CSV` | Validate aerodynamic polar export | JSON summary |

## Recommended team workflow

1. Design the airframe and check static/dynamic stability in **OpenRocket**.
2. Recreate the measured mass, thrust curve, drag, weather, and recovery in **RocketPy**; run
   Monte Carlo dispersion, not only a nominal flight.
3. Cross-check propulsion with **RocketCEA/NASA CEA** and a separate feed/thermal/structural
   analysis owned by qualified team members.
4. Replay simulated sensor data through this estimator interface, then replace it with **PX4
   EKF2** or another independently reviewed estimator for hardware tests.
5. Progress software-in-the-loop, processor-in-the-loop, hardware-in-the-loop, captive tests,
   and only then a flight-readiness review.

The `guidance` command is deliberately non-actuating. It is useful for analysis and
SIL/HIL comparisons; it cannot arm or trigger recovery hardware.

Dispersion results are percentile summaries, not a substitute for a full RocketPy/OpenRocket
Monte Carlo campaign. The built-in sweep is intentionally transparent and defaults to dry mass
(3%), drag coefficient (8%), and thrust scale (5%) variation. Override those widths with
`--mass-sigma`, `--drag-sigma`, and `--thrust-sigma` when the team's measured uncertainty budget
is available.
Use `--summary-output results\dispersion-summary.json` to save the seed, case count, uncertainty
widths, percentile results, and model label alongside the per-case CSV.

See [docs/architecture.md](docs/architecture.md), [docs/toolchain.md](docs/toolchain.md),
[docs/imu-and-guidance.md](docs/imu-and-guidance.md), [docs/px4-bringup.md](docs/px4-bringup.md),
and [docs/safety.md](docs/safety.md).

Team contribution and verification conventions are in [CONTRIBUTING.md](CONTRIBUTING.md). Every
push and pull request runs the test/lint/format matrix in `.github/workflows/ci.yml`.

`integrations/rocketpy_reference.py` is a runnable 6-DOF wiring example. Its geometry and inertias
are explicitly fictional; replace every one with measured project data.

CAD exports can be inspected with:

```powershell
$env:PYTHONPATH = "src"
python -m rocket_workbench cad-info models\airframe.stl --units mm
# Optional volume/watertight analysis:
python -m pip install -e ".[cad]"
```

OpenRocket projects can be inspected with:

```powershell
python -m rocket_workbench openrocket-info designs\vehicle.ork
```

CAD/FEA mass properties can be checked with:

```powershell
python -m rocket_workbench mass-info exports\mass-properties.csv
```

Aerodynamic data exported from CFD or RASAero-style workflows can be checked with:

```powershell
python -m rocket_workbench aero-info exports\polar.csv
```

Use CAD tools for geometry and mass-property preparation, OpenRocket for early stability design,
RocketPy for 6-DOF flight, OpenFOAM/SU2/ANSYS Fluent for CFD, and CalculiX/Ansys/Abaqus for
structural work. CAD mesh metadata is not a substitute for CFD, structural analysis, or a measured
mass/CG audit.

## BOM status

`bom/reference_bom.csv` is a **system-level starter list**, not a purchase order. Rows marked
`REFERENCE` have a concrete reference part; `PLACEHOLDER` rows require measured requirements,
team review, current stock/pricing checks, and often a country-specific radio or safety decision.
When a custom KiCad board exists, put Manufacturer/MPN/distributor properties in the schematic
and export the BOM from there; the schematic should then become the source of truth.

Reference MPNs and manufacturer evidence were checked on 2026-07-12. DigiKey API credentials
were not available, so distributor stock, regional price, and DigiKey order numbers remain
unvalidated and must be refreshed immediately before procurement.
