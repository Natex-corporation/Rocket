from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from math import isfinite
from pathlib import Path


@dataclass(frozen=True)
class MassProperties:
    mass_kg: float
    cg_x_m: float
    cg_y_m: float
    cg_z_m: float
    ixx_kg_m2: float
    iyy_kg_m2: float
    izz_kg_m2: float
    ixy_kg_m2: float = 0.0
    ixz_kg_m2: float = 0.0
    iyz_kg_m2: float = 0.0
    source: str = ""

    def as_dict(self) -> dict[str, float | str]:
        return asdict(self)


REQUIRED = ("mass_kg", "cg_x_m", "cg_y_m", "cg_z_m", "ixx_kg_m2", "iyy_kg_m2", "izz_kg_m2")


def load_mass_properties(path: Path) -> MassProperties:
    """Read one-row SI CSV exported from CAD/FEA mass-property reports."""
    if not path.is_file():
        raise ValueError(f"mass-properties file does not exist: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = set(REQUIRED).difference(reader.fieldnames or ())
        if missing:
            raise ValueError(f"mass-properties CSV missing columns: {', '.join(sorted(missing))}")
        rows = list(reader)
    if len(rows) != 1:
        raise ValueError("mass-properties CSV must contain exactly one data row")
    row = rows[0]
    values: dict[str, float] = {}
    for key in (*REQUIRED, "ixy_kg_m2", "ixz_kg_m2", "iyz_kg_m2"):
        try:
            values[key] = float(row.get(key, "0") or 0)
        except ValueError as exc:
            raise ValueError(f"mass-properties value is invalid: {key}") from exc
        if not isfinite(values[key]):
            raise ValueError(f"mass-properties value is non-finite: {key}")
    if values["mass_kg"] <= 0 or any(values[key] < 0 for key in ("ixx_kg_m2", "iyy_kg_m2", "izz_kg_m2")):
        raise ValueError("mass must be positive and diagonal inertias cannot be negative")
    return MassProperties(**values, source=str(path))
