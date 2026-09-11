"""Runnable RocketPy 6-DOF reference case.

All geometry and mass properties are fictional placeholders. Replace them with measured team
data before using results. Run from the repository root after installing the simulation extra:
    .venv/Scripts/python integrations/rocketpy_reference.py
"""

from __future__ import annotations

import json
from pathlib import Path

from rocketpy import Environment, Flight, Rocket, SolidMotor

from rocket_workbench.flight import load_thrust_curve


ROOT = Path(__file__).parents[1]


def build_flight() -> Flight:
    environment = Environment(latitude=50.0, longitude=14.0, elevation=300.0)
    environment.set_atmospheric_model(type="standard_atmosphere")

    motor = SolidMotor(
        thrust_source=load_thrust_curve(ROOT / "examples/reference_thrust.csv"),
        dry_mass=3.0,
        dry_inertia=(0.18, 0.18, 0.02),
        nozzle_radius=0.035,
        grain_number=4,
        grain_density=1_700,
        grain_outer_radius=0.055,
        grain_initial_inner_radius=0.025,
        grain_initial_height=0.16,
        grain_separation=0.004,
        grains_center_of_mass_position=0.42,
        center_of_dry_mass_position=0.25,
        nozzle_position=0.0,
        burn_time=3.0,
        throat_radius=0.018,
    )

    rocket = Rocket(
        radius=0.0762,
        mass=15.0,
        inertia=(7.0, 7.0, 0.09),
        power_off_drag=0.55,
        power_on_drag=0.50,
        center_of_mass_without_motor=1.45,
    )
    rocket.add_motor(motor, position=0.05)
    rocket.add_nose(length=0.55, kind="von karman", position=2.75)
    rocket.add_trapezoidal_fins(
        n=4,
        root_chord=0.32,
        tip_chord=0.14,
        span=0.16,
        position=0.22,
        sweep_length=0.13,
    )
    rocket.add_tail(top_radius=0.0762, bottom_radius=0.055, length=0.12, position=0.0)
    rocket.add_parachute("drogue", cd_s=0.25, trigger="apogee", sampling_rate=100, lag=1.0)
    rocket.add_parachute("main", cd_s=1.8, trigger=500, sampling_rate=100, lag=1.0)

    return Flight(
        rocket=rocket,
        environment=environment,
        rail_length=6.0,
        inclination=85.0,
        heading=90.0,
        max_time=300,
        max_time_step=0.05,
        verbose=False,
    )


def main() -> None:
    flight = build_flight()
    print(
        json.dumps(
            {
                "apogee_m_asl": flight.apogee,
                "apogee_m_agl": flight.apogee - flight.env.elevation,
                "apogee_time_s": flight.apogee_time,
                "max_speed_m_s": flight.max_speed,
                "out_of_rail_velocity_m_s": flight.out_of_rail_velocity,
                "flight_time_s": flight.t_final,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
