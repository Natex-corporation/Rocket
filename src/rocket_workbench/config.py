from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class EngineConfig:
    chamber_pressure_bar: float
    mixture_ratio: float
    expansion_ratio: float
    chamber_temperature_k: float
    gamma: float
    molar_mass_g_mol: float
    ambient_pressure_pa: float = 101_325.0

    def __post_init__(self) -> None:
        values = (self.chamber_pressure_bar, self.mixture_ratio, self.expansion_ratio,
                  self.chamber_temperature_k, self.gamma, self.molar_mass_g_mol,
                  self.ambient_pressure_pa)
        if not all(isfinite(value) for value in values):
            raise ValueError("engine configuration values must be finite")
        if self.chamber_pressure_bar <= 0 or self.mixture_ratio <= 0 or self.expansion_ratio <= 1:
            raise ValueError("engine pressure, mixture ratio, and expansion ratio are invalid")
        if self.chamber_temperature_k <= 0 or self.molar_mass_g_mol <= 0 or self.ambient_pressure_pa < 0:
            raise ValueError("engine temperature, molar mass, and ambient pressure are invalid")
        if not 1.0 < self.gamma < 2.0:
            raise ValueError("gamma must be between 1 and 2")


@dataclass(frozen=True)
class FlightConfig:
    dry_mass_kg: float
    propellant_mass_kg: float
    diameter_m: float
    drag_coefficient: float
    launch_altitude_m: float
    rail_length_m: float
    time_step_s: float
    max_time_s: float
    parachute_cd_area_m2: float
    deploy_delay_s: float
    thrust_curve: Path

    def __post_init__(self) -> None:
        values = (self.dry_mass_kg, self.propellant_mass_kg, self.diameter_m,
                  self.drag_coefficient, self.launch_altitude_m, self.rail_length_m,
                  self.time_step_s, self.max_time_s, self.parachute_cd_area_m2,
                  self.deploy_delay_s)
        if not all(isfinite(value) for value in values):
            raise ValueError("flight configuration values must be finite")
        if self.dry_mass_kg <= 0 or self.propellant_mass_kg < 0 or self.diameter_m <= 0:
            raise ValueError("flight mass and diameter values are invalid")
        if self.drag_coefficient < 0 or self.launch_altitude_m < 0 or self.rail_length_m <= 0:
            raise ValueError("flight drag, altitude, and rail values are invalid")
        if self.time_step_s <= 0 or self.max_time_s <= 0:
            raise ValueError("flight timestep and duration must be positive")
        if self.parachute_cd_area_m2 < 0 or self.deploy_delay_s < 0:
            raise ValueError("recovery values must be non-negative")
        if not self.thrust_curve.is_file():
            raise ValueError(f"thrust curve does not exist: {self.thrust_curve}")


def load_engine(path: str | Path) -> EngineConfig:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))["engine"]
    return EngineConfig(**data)


def load_flight(path: str | Path) -> FlightConfig:
    source = Path(path)
    data = tomllib.loads(source.read_text(encoding="utf-8"))["flight"]
    curve = Path(data.pop("thrust_curve"))
    if not curve.is_absolute():
        curve = (source.parent / curve).resolve()
    return FlightConfig(thrust_curve=curve, **data)
