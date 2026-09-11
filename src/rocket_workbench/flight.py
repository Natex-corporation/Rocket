from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from math import exp, isfinite, pi
from pathlib import Path

from .config import FlightConfig

G0 = 9.80665


@dataclass(frozen=True)
class FlightSample:
    time_s: float
    altitude_m: float
    velocity_m_s: float
    acceleration_m_s2: float
    mass_kg: float
    thrust_n: float
    phase: str


@dataclass(frozen=True)
class FlightSummary:
    apogee_m_agl: float
    max_velocity_m_s: float
    max_acceleration_m_s2: float
    rail_exit_velocity_m_s: float | None
    burnout_time_s: float
    flight_time_s: float

    def as_dict(self) -> dict[str, float | None]:
        return asdict(self)


def load_thrust_curve(path: Path) -> list[tuple[float, float]]:
    rows: list[tuple[float, float]] = []
    if path.suffix.lower() == ".eng":
        return _load_rasp_eng(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(line for line in handle if not line.lstrip().startswith("#"))
        required = {"time_s", "thrust_n"}
        missing = required.difference(reader.fieldnames or ())
        if missing:
            raise ValueError(f"thrust curve missing columns: {', '.join(sorted(missing))}")
        for number, row in enumerate(reader, 2):
            try:
                time_s = float(row["time_s"])
                thrust_n = float(row["thrust_n"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid thrust curve values on row {number}") from exc
            if not isfinite(time_s) or not isfinite(thrust_n):
                raise ValueError(f"thrust curve contains a non-finite value on row {number}")
            if time_s < 0 or thrust_n < 0:
                raise ValueError("thrust curve time and thrust must be non-negative")
            rows.append((time_s, thrust_n))
    if len(rows) < 2 or rows[0][0] != 0 or any(b[0] <= a[0] for a, b in zip(rows, rows[1:])):
        raise ValueError("thrust curve needs increasing time_s values and must start at zero")
    return rows


def _load_rasp_eng(path: Path) -> list[tuple[float, float]]:
    """Read the time/thrust section of a RASP `.eng` motor file."""
    data: list[tuple[float, float]] = []
    with path.open(encoding="utf-8-sig") as handle:
        header_seen = False
        for number, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line or line.startswith(";") or line.startswith("#"):
                continue
            fields = line.split()
            if not header_seen:
                if len(fields) < 6:
                    raise ValueError(f"RASP motor header is invalid on row {number}")
                header_seen = True
                continue
            if len(fields) < 2:
                continue
            try:
                time_s, thrust_n = float(fields[0]), float(fields[1])
            except ValueError as exc:
                raise ValueError(f"invalid RASP thrust values on row {number}") from exc
            if not isfinite(time_s) or not isfinite(thrust_n) or time_s < 0 or thrust_n < 0:
                raise ValueError(f"invalid RASP thrust values on row {number}")
            data.append((time_s, thrust_n))
    if not header_seen or len(data) < 2:
        raise ValueError("RASP motor file contains no usable thrust curve")
    if data[0][0] != 0 or any(b[0] <= a[0] for a, b in zip(data, data[1:])):
        raise ValueError("RASP thrust curve must start at zero with increasing time")
    return data


def _interpolate(curve: list[tuple[float, float]], t: float) -> float:
    if t < 0 or t > curve[-1][0]:
        return 0.0
    for (ta, fa), (tb, fb) in zip(curve, curve[1:]):
        if ta <= t <= tb:
            fraction = (t - ta) / (tb - ta)
            return fa + fraction * (fb - fa)
    return 0.0


def simulate(config: FlightConfig) -> tuple[list[FlightSample], FlightSummary]:
    """Vertical point-mass reference simulation with coast and recovery.

    Use this for smoke tests and parameter sweeps; use RocketPy/OpenRocket for
    design decisions involving 6-DOF stability, wind, or aerodynamic geometry.
    """
    if config.dry_mass_kg <= 0 or config.propellant_mass_kg < 0:
        raise ValueError("dry mass must be positive and propellant mass cannot be negative")
    if config.diameter_m <= 0 or config.drag_coefficient < 0:
        raise ValueError("diameter must be positive and drag coefficient cannot be negative")
    if config.time_step_s <= 0 or config.max_time_s <= 0:
        raise ValueError("time step and max time must be positive")
    if config.rail_length_m <= 0 or config.parachute_cd_area_m2 < 0 or config.deploy_delay_s < 0:
        raise ValueError("rail length must be positive and recovery parameters non-negative")
    curve = load_thrust_curve(config.thrust_curve)
    burn_time = curve[-1][0]
    area = pi * config.diameter_m**2 / 4
    initial_mass = config.dry_mass_kg + config.propellant_mass_kg
    dt, t, h, v = config.time_step_s, 0.0, 0.0, 0.0
    samples: list[FlightSample] = []
    rail_exit: float | None = None
    apogee_time: float | None = None

    while t <= config.max_time_s:
        thrust = _interpolate(curve, t)
        burned = min(1.0, t / burn_time) * config.propellant_mass_kg
        mass = initial_mass - burned
        rho = 1.225 * exp(-(config.launch_altitude_m + max(h, 0)) / 8_500)
        if apogee_time is not None and t >= apogee_time + config.deploy_delay_s:
            cd_area, phase = config.parachute_cd_area_m2, "recovery"
        else:
            cd_area = config.drag_coefficient * area
            phase = "boost" if t <= burn_time else "coast"
        drag = 0.5 * rho * cd_area * v * abs(v)
        acceleration = (thrust - drag - mass * G0) / mass
        if h <= 0 and v <= 0 and thrust <= mass * G0:
            acceleration = 0.0
        next_v = v + acceleration * dt
        next_h = max(0.0, h + (v + next_v) * 0.5 * dt)
        if rail_exit is None and next_h >= config.rail_length_m:
            rail_exit = next_v
        if apogee_time is None and t > burn_time and v > 0 >= next_v:
            apogee_time = t + dt
        samples.append(FlightSample(t, h, v, acceleration, mass, thrust, phase))
        t, h, v = t + dt, next_h, next_v
        if apogee_time is not None and h <= 0 and t > apogee_time + 0.5:
            break

    summary = FlightSummary(
        max(s.altitude_m for s in samples),
        max(abs(s.velocity_m_s) for s in samples),
        max(abs(s.acceleration_m_s2) for s in samples),
        rail_exit,
        burn_time,
        samples[-1].time_s,
    )
    return samples, summary


def write_csv(samples: list[FlightSample], path: Path) -> None:
    if not samples:
        raise ValueError("cannot write an empty flight result")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(samples[0])))
        writer.writeheader()
        writer.writerows(asdict(sample) for sample in samples)
