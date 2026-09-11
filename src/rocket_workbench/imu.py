from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from math import atan2, cos, isfinite, sin, sqrt
from pathlib import Path
import random

from .flight import FlightSample


@dataclass(frozen=True)
class Estimate:
    time_s: float
    roll_deg: float
    pitch_deg: float
    altitude_m: float
    vertical_velocity_m_s: float
    phase: str


class VerticalKalman:
    """Small altitude/vertical-speed filter for simulation and log replay."""

    def __init__(self, acceleration_variance: float = 9.0, baro_variance: float = 4.0):
        self.h = self.v = 0.0
        self.p00, self.p01, self.p10, self.p11 = 100.0, 0.0, 0.0, 100.0
        self.q, self.r = acceleration_variance, baro_variance

    def update(
        self, acceleration_m_s2: float, baro_altitude_m: float, dt: float
    ) -> tuple[float, float]:
        self.h += self.v * dt + 0.5 * acceleration_m_s2 * dt * dt
        self.v += acceleration_m_s2 * dt
        p00 = self.p00 + dt * (self.p10 + self.p01) + dt * dt * self.p11 + self.q * dt**4 / 4
        p01 = self.p01 + dt * self.p11 + self.q * dt**3 / 2
        p10 = self.p10 + dt * self.p11 + self.q * dt**3 / 2
        p11 = self.p11 + self.q * dt**2
        innovation = baro_altitude_m - self.h
        denom = p00 + self.r
        k0, k1 = p00 / denom, p10 / denom
        self.h += k0 * innovation
        self.v += k1 * innovation
        self.p00, self.p01 = (1 - k0) * p00, (1 - k0) * p01
        self.p10, self.p11 = p10 - k1 * p00, p11 - k1 * p01
        return self.h, self.v


class FlightPhase:
    def __init__(self) -> None:
        self.phase = "PAD"
        self._apogee_votes = 0

    def update(self, acceleration_m_s2: float, velocity_m_s: float, altitude_m: float) -> str:
        if self.phase == "PAD" and acceleration_m_s2 > 15:
            self.phase = "BOOST"
        elif self.phase == "BOOST" and acceleration_m_s2 < 2:
            self.phase = "COAST"
        elif self.phase == "COAST":
            self._apogee_votes = self._apogee_votes + 1 if velocity_m_s < -1 else 0
            if self._apogee_votes >= 5:
                self.phase = "DESCENT"
        elif self.phase == "DESCENT" and altitude_m < 10 and abs(velocity_m_s) < 8:
            self.phase = "LANDED"
        return self.phase


def replay(path: Path, output: Path, attitude_gain: float = 0.02) -> list[Estimate]:
    """Replay a standard CSV log through complementary attitude + vertical filters.

    Required columns: time_s, ax_m_s2, ay_m_s2, az_m_s2, gx_rad_s,
    gy_rad_s, gz_rad_s, baro_altitude_m. Axes are body-forward/right/down.
    This demonstrator estimates roll/pitch only; production navigation should use
    PX4 EKF2 or an equivalently validated estimator.
    """
    if not 0 < attitude_gain <= 1:
        raise ValueError("attitude_gain must be greater than 0 and no more than 1")
    result: list[Estimate] = []
    roll = pitch = 0.0
    vertical = VerticalKalman()
    detector = FlightPhase()
    previous_time: float | None = None
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            t = float(row["time_s"])
            dt = 0.01 if previous_time is None else t - previous_time
            if dt <= 0 or dt > 1:
                raise ValueError("IMU timestamps must increase with gaps <= 1 second")
            ax, ay, az = (float(row[key]) for key in ("ax_m_s2", "ay_m_s2", "az_m_s2"))
            gx, gy = float(row["gx_rad_s"]), float(row["gy_rad_s"])
            gz = float(row["gz_rad_s"])
            baro_altitude = float(row["baro_altitude_m"])
            values = (t, ax, ay, az, gx, gy, gz, baro_altitude)
            if not all(isfinite(value) for value in values):
                raise ValueError(f"IMU log contains a non-finite value at time {t!r}")
            accel_roll = atan2(ay, az)
            accel_pitch = atan2(-ax, sqrt(ay * ay + az * az))
            roll = (1 - attitude_gain) * (roll + gx * dt) + attitude_gain * accel_roll
            pitch = (1 - attitude_gain) * (pitch + gy * dt) + attitude_gain * accel_pitch
            # Rotate body acceleration onto navigation-up for modest attitudes.
            vertical_accel = (
                -(ax * sin(pitch) - ay * sin(roll) * cos(pitch) + az * cos(roll) * cos(pitch))
                - 9.80665
            )
            altitude, velocity = vertical.update(vertical_accel, baro_altitude, dt)
            phase = detector.update(vertical_accel, velocity, altitude)
            result.append(
                Estimate(t, roll * 57.2957795, pitch * 57.2957795, altitude, velocity, phase)
            )
            previous_time = t
    if not result:
        raise ValueError("IMU log contains no samples")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(result[0])))
        writer.writeheader()
        writer.writerows(asdict(item) for item in result)
    return result


def make_synthetic_log(samples: list[FlightSample], output: Path, seed: int = 7) -> None:
    """Create a deterministic FRD-axis IMU/barometer log from a reference flight."""
    rng = random.Random(seed)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "time_s",
        "ax_m_s2",
        "ay_m_s2",
        "az_m_s2",
        "gx_rad_s",
        "gy_rad_s",
        "gz_rad_s",
        "baro_altitude_m",
    )
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for sample in samples:
            writer.writerow(
                {
                    "time_s": sample.time_s,
                    "ax_m_s2": rng.gauss(0, 0.03),
                    "ay_m_s2": rng.gauss(0, 0.03),
                    "az_m_s2": -(sample.acceleration_m_s2 + 9.80665) + rng.gauss(0, 0.12),
                    "gx_rad_s": rng.gauss(0, 0.001),
                    "gy_rad_s": rng.gauss(0, 0.001),
                    "gz_rad_s": rng.gauss(0, 0.001),
                    "baro_altitude_m": sample.altitude_m + rng.gauss(0, 1.5),
                }
            )
