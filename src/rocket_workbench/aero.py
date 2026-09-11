from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from math import isfinite
from pathlib import Path


@dataclass(frozen=True)
class AeroPoint:
    mach: float
    alpha_deg: float
    cd: float
    cl: float
    cm: float


@dataclass(frozen=True)
class AeroPolar:
    source: str
    points: tuple[AeroPoint, ...]
    mach_min: float
    mach_max: float
    alpha_min_deg: float
    alpha_max_deg: float
    cd_min: float
    cd_max: float

    def as_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["points"] = len(self.points)
        return result

    def nearest(self, mach: float, alpha_deg: float) -> AeroPoint:
        """Return the nearest tabulated point for SIL and quick parameter sweeps.

        This is intentionally not a flight-quality interpolation scheme. It makes extrapolation
        visible by clamping to the nearest available point; production use should use a reviewed
        table/interpolator with explicit Mach/Reynolds bounds.
        """
        if not isfinite(mach) or not isfinite(alpha_deg) or mach < 0:
            raise ValueError("Mach and angle of attack must be finite, with Mach non-negative")
        mach_span = max(self.mach_max - self.mach_min, 1e-12)
        alpha_span = max(self.alpha_max_deg - self.alpha_min_deg, 1e-12)
        return min(self.points, key=lambda point: ((point.mach - mach) / mach_span) ** 2
                   + ((point.alpha_deg - alpha_deg) / alpha_span) ** 2)


REQUIRED = ("mach", "alpha_deg", "cd", "cl", "cm")
ALIASES = {
    "mach": {"mach", "mach_number", "mach number", "m"},
    "alpha_deg": {"alpha_deg", "alpha", "aoa", "aoa_deg", "angle_of_attack_deg", "angle of attack"},
    "cd": {"cd", "drag_coefficient"},
    "cl": {"cl", "lift_coefficient"},
    "cm": {"cm", "pitching_moment_coefficient", "moment_coefficient"},
}


def load_aero_polar(path: Path) -> AeroPolar:
    """Read a dimensionless aerodynamic polar exported by CFD or a rocket aero tool."""
    if not path.is_file():
        raise ValueError(f"aerodynamic polar does not exist: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(line for line in handle if not line.lstrip().startswith("#"))
        headers = {header.strip().lower(): header for header in (reader.fieldnames or []) if header}
        columns = {
            key: next((headers[name] for name in aliases if name in headers), None)
            for key, aliases in ALIASES.items()
        }
        missing = {key for key, column in columns.items() if column is None}
        if missing:
            raise ValueError(f"aerodynamic polar missing columns: {', '.join(sorted(missing))}")
        points: list[AeroPoint] = []
        for number, row in enumerate(reader, 2):
            try:
                values = {key: float(row[columns[key]]) for key in REQUIRED}  # type: ignore[index]
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid aerodynamic values on row {number}") from exc
            if not all(isfinite(value) for value in values.values()):
                raise ValueError(f"aerodynamic polar contains a non-finite value on row {number}")
            if values["mach"] < 0 or values["cd"] < 0:
                raise ValueError(f"Mach and cd must be non-negative on row {number}")
            points.append(AeroPoint(**values))
    if not points:
        raise ValueError("aerodynamic polar contains no rows")
    return AeroPolar(str(path), tuple(points), min(p.mach for p in points), max(p.mach for p in points),
                     min(p.alpha_deg for p in points), max(p.alpha_deg for p in points),
                     min(p.cd for p in points), max(p.cd for p in points))
