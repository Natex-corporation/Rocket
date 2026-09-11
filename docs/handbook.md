# Student Rocket Workbench — team handbook

This repository is a small, reviewable engineering workbench for a student rocket team. It joins
propulsion estimates, a transparent reference flight model, sensor-log replay, advisory guidance,
dispersion checks, CAD/aerodynamic imports, and an avionics bill of materials.

It is not a flight computer, motor-design package, or flight authorization system. Use it to make
assumptions visible and results reproducible; use established tools and qualified review for
flight decisions.

## Repository map

```text
src/rocket_workbench/       Python package and CLI
examples/                   versioned configurations and sample thrust curve
results/                    generated CSV/JSON artifacts
bom/                        reference avionics BOM
integrations/               optional RocketPy adapter
docs/                       architecture, safety, toolchain, and this handbook
tests/                      unit and integration tests
```

## Installation

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest
```

Optional integrations are listed in `pyproject.toml`:

```powershell
.\.venv\Scripts\python -m pip install -e ".[simulation]"  # RocketPy
.\.venv\Scripts\python -m pip install -e ".[engine]"      # RocketCEA
.\.venv\Scripts\python -m pip install -e ".[analysis]"    # NumPy/Matplotlib
```

Record Python/tool versions, git commit, and input checksums in every report. Do not mix results
from different tool versions without documenting the change.

## First run

```powershell
$env:PYTHONPATH = "src"
python -m rocket_workbench --help
python -m rocket_workbench flight examples\flight_reference.toml --output results\flight.csv
python -m rocket_workbench engine examples\engine_lox_methane.toml
python -m rocket_workbench imu-demo examples\flight_reference.toml --log results\imu.csv --output results\estimate.csv
python -m rocket_workbench guidance results\estimate.csv --target-apogee-m 2000 --output results\advisory.csv
python -m rocket_workbench dispersion examples\flight_reference.toml --cases 100 --seed 7 --output results\dispersion.csv
python -m rocket_workbench bom-check bom\reference_bom.csv
```

The reference fixture is approximately: apogee 1,989 m AGL, maximum velocity 229 m/s, rail-exit
velocity 34.5 m/s, and total flight time 166 s. These are regression anchors, not a real-vehicle
prediction.

## Command reference

| Command | Input | Purpose |
|---|---|---|
| `engine CONFIG` | engine TOML | Ideal-nozzle or RocketCEA performance JSON |
| `flight CONFIG` | flight TOML | Deterministic vertical-flight CSV and summary |
| `imu-replay LOG` | IMU/barometer CSV | Estimate altitude, velocity, attitude, and phase |
| `imu-demo CONFIG` | flight TOML | Generate synthetic sensors and replay them |
| `guidance ESTIMATE` | estimator CSV | Non-actuating apogee/recovery advisory |
| `dispersion CONFIG` | flight TOML | Seeded mass/drag/thrust uncertainty sweep |
| `bom-check CSV` | BOM CSV | Validate schema, MPNs, quantities, and placeholders |
| `cad-info MESH` | STL/OBJ | Read-only geometry metadata |
| `openrocket-info FILE` | `.ork` | Read-only OpenRocket metadata |
| `mass-info CSV` | mass-property CSV | Validate mass, CG, and inertia |
| `aero-info CSV` | aero-polar CSV | Validate coefficients and units |

Use `python -m rocket_workbench COMMAND --help` for exact options. Commands write only the output
path requested; they do not upload data or alter hardware.

## Data contracts

### Flight configuration

The sample `examples/flight_reference.toml` defines dry/propellant mass, diameter, drag
coefficient, launch altitude, rail length, timestep, duration, parachute `CdA`, deployment delay,
and a thrust-curve path. Paths are relative to the TOML file. SI units are mandatory.

The built-in model is one-dimensional, upward-positive, and intended for transparent cross-checks.
It does not model 6-DOF attitude, fin flutter, rail bending, detailed motor thermochemistry, or
structural failure.

### IMU CSV

Required header:

```text
time_s,ax_m_s2,ay_m_s2,az_m_s2,gx_rad_s,gy_rad_s,gz_rad_s,baro_altitude_m
```

Axes are body **forward-right-down (FRD)**. Accelerometers contain specific force; a stationary
upright sensor is approximately `az = -9.80665 m/s²`. Timestamps must be finite, monotonic, and
non-duplicated. Calibrate bias, scale, alignment, timing, temperature response, saturation, and
vibration on the assembled electronics.

### BOM CSV

Required columns are `category,item,quantity,manufacturer,mpn,status,validated_utc,datasheet_url,
notes`. `REFERENCE` means a starting point, not procurement approval. Replace `PLACEHOLDER` rows
with exact MPNs, availability, temperature grade, interfaces, and approved datasheets.

## Recommended team workflow

1. Freeze mass, CG, inertia, thrust curve, atmosphere, launch rail, recovery assumptions, and
   coordinate conventions.
2. Check the airframe in OpenRocket: stability, rail departure, motor, recovery, and wind cases.
3. Cross-check in RocketPy with weather, 6-DOF effects, and Monte Carlo dispersion.
4. Compare propulsion against RocketCEA/NASA CEA and independently review feed, thermal,
   injector, pressure, and structural margins.
5. Generate and replay sensors; compare truth, estimator, phase timing, innovations, dropouts,
   saturation, and resets.
6. Run the advisory layer as a review record only; it cannot command recovery hardware.
7. Use KiCad as the schematic/PCB source of truth; run ERC/DRC, BOM checks, power, EMC, and
   vibration reviews.
8. Progress bench → inert captive test → SIL → PIL → HIL → range-authorized readiness review.

## Evidence checklist

For each accepted result, record the git commit, working-tree state, tool versions, exact inputs and
checksums, coordinate frame, units, atmosphere, mass/CG/inertia source, thrust-curve source,
aerodynamic assumptions, sensor calibration, expected limits, result, and independent reviewer.

Every model change should pass unit tests, limit/conservation checks, independent OpenRocket or
RocketPy comparison, logged ground-test replay, SIL/PIL/HIL checks, and a written readiness review.
A nominal trajectory alone is never sufficient evidence.

## Safety boundary

Motors, pressure systems, energetic recovery devices, high-current batteries, transmitters, and
active control surfaces require competent review and may be regulated. Follow university safety
procedures, range rules, and applicable law. Use independent recovery electronics and physical
safing/inhibits. Keep experimental software out of the sole life-safety path until it has passed an
approved verification campaign.

The guidance command is advisory-only. Its labels (`MONITOR_ONLY`, `UNDER_TARGET_MONITOR_ONLY`,
`RECOVERY_SYSTEM_REQUIRED`, `SAFE_AND_LOG`) are analysis records, never actuator commands. Do not
connect this workbench directly to pyrotechnics, control surfaces, or recovery circuits.

## Related documents

- [Architecture](architecture.md) — data flow, units, coordinate contract, verification ladder
- [Established toolchain](toolchain.md) — external tools and integration boundaries
- [IMU and guidance](imu-and-guidance.md) — estimator scope and production direction
- [Safety and review boundary](safety.md) — review and flight-readiness constraints
- [CAD and toolchain](cad-and-toolchain.md) — geometry and analysis handoffs
- [PX4 bring-up](px4-bringup.md) — estimator/SITL/HIL direction
