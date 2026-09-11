from __future__ import annotations

import csv
import json
import random
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .config import FlightConfig
from .flight import FlightSummary, load_thrust_curve, simulate


@dataclass(frozen=True)
class DispersionCase:
    case: int
    dry_mass_kg: float
    drag_coefficient: float
    thrust_scale: float
    apogee_m_agl: float
    max_velocity_m_s: float
    rail_exit_velocity_m_s: float | None


@dataclass(frozen=True)
class DispersionSummary:
    cases: int
    seed: int
    apogee_p05_m: float
    apogee_p50_m: float
    apogee_p95_m: float
    velocity_p05_m_s: float
    velocity_p50_m_s: float
    velocity_p95_m_s: float

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower, upper = int(position), min(int(position) + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def run(
    config: FlightConfig,
    cases: int = 100,
    seed: int = 7,
    mass_sigma: float = 0.03,
    drag_sigma: float = 0.08,
    thrust_sigma: float = 0.05,
) -> tuple[list[DispersionCase], DispersionSummary]:
    if cases < 1:
        raise ValueError("cases must be positive")
    if mass_sigma < 0 or drag_sigma < 0 or thrust_sigma < 0:
        raise ValueError("dispersion sigmas must be non-negative")
    rng = random.Random(seed)
    base_curve = load_thrust_curve(config.thrust_curve)
    outputs: list[DispersionCase] = []
    for number in range(1, cases + 1):
        dry_mass = config.dry_mass_kg * rng.gauss(1.0, mass_sigma)
        drag = max(0.05, config.drag_coefficient * rng.gauss(1.0, drag_sigma))
        thrust_scale = max(0.5, rng.gauss(1.0, thrust_sigma))
        scaled_curve = [(time_s, thrust_n * thrust_scale) for time_s, thrust_n in base_curve]
        # A private curve makes each case reproducible without mutating the user's input file.
        case_curve = config.thrust_curve.with_name(f".dispersion-{seed}-{number}.csv")
        with case_curve.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("time_s", "thrust_n"))
            writer.writerows(scaled_curve)
        try:
            _, summary = simulate(replace(config, dry_mass_kg=dry_mass, drag_coefficient=drag, thrust_curve=case_curve))
        finally:
            case_curve.unlink(missing_ok=True)
        outputs.append(DispersionCase(number, dry_mass, drag, thrust_scale, summary.apogee_m_agl,
                                      summary.max_velocity_m_s, summary.rail_exit_velocity_m_s))
    apogees = [item.apogee_m_agl for item in outputs]
    velocities = [item.max_velocity_m_s for item in outputs]
    report = DispersionSummary(cases, seed, _percentile(apogees, .05), _percentile(apogees, .5),
                               _percentile(apogees, .95), _percentile(velocities, .05),
                               _percentile(velocities, .5), _percentile(velocities, .95))
    return outputs, report


def write_csv(cases: list[DispersionCase], path: Path) -> None:
    if not cases:
        raise ValueError("cannot write empty dispersion results")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(cases[0])))
        writer.writeheader()
        writer.writerows(asdict(item) for item in cases)


def write_summary(summary: DispersionSummary, path: Path, *, mass_sigma: float,
                  drag_sigma: float, thrust_sigma: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **summary.as_dict(),
        "mass_sigma": mass_sigma,
        "drag_sigma": drag_sigma,
        "thrust_sigma": thrust_sigma,
        "model": "vertical point-mass reference simulation",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
