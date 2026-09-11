"""Non-actuating guidance and recovery advisories.

This module intentionally emits recommendations only. It never drives a servo, pyro channel,
motor, or recovery output. A qualified flight computer must independently implement inhibits,
arming, redundancy, command limits, and the team's approved recovery logic.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from math import sqrt
from pathlib import Path

G0 = 9.80665


@dataclass(frozen=True)
class GuidanceAdvisory:
    time_s: float
    altitude_m: float
    vertical_velocity_m_s: float
    predicted_apogee_m: float
    apogee_margin_m: float
    phase: str
    recommendation: str


def ballistic_apogee(altitude_m: float, vertical_velocity_m_s: float) -> float:
    """Return a no-drag apogee estimate from an upward-positive state."""
    # Barometric filters commonly undershoot ground by a small amount. Clamp that
    # numerical/recovery artifact, while still rejecting clearly invalid values.
    if altitude_m < -100:
        raise ValueError("altitude is implausibly negative")
    return max(altitude_m, 0.0) + max(vertical_velocity_m_s, 0.0) ** 2 / (2 * G0)


def advise(
    time_s: float,
    altitude_m: float,
    vertical_velocity_m_s: float,
    phase: str,
    target_apogee_m: float,
    recovery_margin_m: float = 50.0,
) -> GuidanceAdvisory:
    if target_apogee_m <= 0 or recovery_margin_m < 0:
        raise ValueError("target apogee must be positive and recovery margin non-negative")
    predicted = ballistic_apogee(altitude_m, vertical_velocity_m_s)
    margin = predicted - target_apogee_m
    normalized = phase.upper()
    if normalized in {"PAD", "BOOST", "COAST"}:
        recommendation = "MONITOR_ONLY"
    elif normalized == "DESCENT":
        recommendation = "RECOVERY_SYSTEM_REQUIRED"
    elif normalized == "LANDED":
        recommendation = "SAFE_AND_LOG"
    else:
        recommendation = "UNKNOWN_PHASE_HOLD"
    if normalized == "COAST" and margin < -recovery_margin_m:
        recommendation = "UNDER_TARGET_MONITOR_ONLY"
    return GuidanceAdvisory(
        time_s, altitude_m, vertical_velocity_m_s, predicted, margin, normalized, recommendation
    )


def replay_estimates(
    input_csv: Path, output_csv: Path, target_apogee_m: float, recovery_margin_m: float = 50.0
) -> list[GuidanceAdvisory]:
    """Convert estimator CSV output into advisory CSV without issuing hardware commands."""
    advisories: list[GuidanceAdvisory] = []
    with input_csv.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"time_s", "altitude_m", "vertical_velocity_m_s", "phase"}
        missing = required.difference(reader.fieldnames or ())
        if missing:
            raise ValueError(f"estimator CSV missing columns: {', '.join(sorted(missing))}")
        for row in reader:
            advisories.append(
                advise(
                    float(row["time_s"]),
                    float(row["altitude_m"]),
                    float(row["vertical_velocity_m_s"]),
                    row["phase"],
                    target_apogee_m,
                    recovery_margin_m,
                )
            )
    if not advisories:
        raise ValueError("estimator CSV contains no samples")
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(advisories[0])))
        writer.writeheader()
        writer.writerows(asdict(item) for item in advisories)
    return advisories
