from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .bom import validate
from .config import load_engine, load_flight
from .cad import inspect_mesh
from .openrocket import inspect_project
from .mass_properties import load_mass_properties
from .aero import load_aero_polar
from .engine import ideal_nozzle, rocketcea
from .flight import simulate, write_csv
from .guidance import replay_estimates
from .dispersion import run as run_dispersion, write_csv as write_dispersion_csv, write_summary
from .imu import make_synthetic_log, replay


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="rocket-workbench")
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    engine = commands.add_parser("engine", help="estimate ideal or CEA engine performance")
    engine.add_argument("config", type=Path)
    engine.add_argument("--backend", choices=("ideal", "rocketcea"), default="ideal")
    engine.add_argument("--oxidizer", default="LOX")
    engine.add_argument("--fuel", default="CH4")
    flight = commands.add_parser("flight", help="run reference vertical flight simulation")
    flight.add_argument("config", type=Path)
    flight.add_argument("--output", type=Path, default=Path("results/flight.csv"))
    imu = commands.add_parser("imu-replay", help="replay an IMU/barometer CSV log")
    imu.add_argument("input", type=Path)
    imu.add_argument("--output", type=Path, default=Path("results/estimate.csv"))
    demo = commands.add_parser("imu-demo", help="generate and replay synthetic flight sensors")
    demo.add_argument("config", type=Path)
    demo.add_argument("--log", type=Path, default=Path("results/imu.csv"))
    demo.add_argument("--output", type=Path, default=Path("results/estimate.csv"))
    guidance = commands.add_parser("guidance", help="generate non-actuating guidance advisories")
    guidance.add_argument("input", type=Path, help="estimator CSV from imu-replay or imu-demo")
    guidance.add_argument("--target-apogee-m", type=float, required=True)
    guidance.add_argument("--recovery-margin-m", type=float, default=50.0)
    guidance.add_argument("--output", type=Path, default=Path("results/advisory.csv"))
    dispersion = commands.add_parser("dispersion", help="run seeded flight uncertainty analysis")
    dispersion.add_argument("config", type=Path)
    dispersion.add_argument("--cases", type=int, default=100)
    dispersion.add_argument("--seed", type=int, default=7)
    dispersion.add_argument("--mass-sigma", type=float, default=0.03)
    dispersion.add_argument("--drag-sigma", type=float, default=0.08)
    dispersion.add_argument("--thrust-sigma", type=float, default=0.05)
    dispersion.add_argument("--output", type=Path, default=Path("results/dispersion.csv"))
    dispersion.add_argument("--summary-output", type=Path, default=None)
    bom = commands.add_parser("bom-check", help="validate the reference BOM")
    bom.add_argument("input", type=Path)
    cad = commands.add_parser("cad-info", help="inspect an STL/OBJ CAD export")
    cad.add_argument("input", type=Path)
    cad.add_argument("--units", choices=("m", "mm", "cm", "in"), default="m")
    ork = commands.add_parser("openrocket-info", help="inspect OpenRocket project metadata")
    ork.add_argument("input", type=Path)
    mass = commands.add_parser("mass-info", help="validate CAD/FEA mass-properties CSV")
    mass.add_argument("input", type=Path)
    aero = commands.add_parser("aero-info", help="validate CFD/RASAero aerodynamic polar CSV")
    aero.add_argument("input", type=Path)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "engine":
        config = load_engine(args.config)
        result = (
            ideal_nozzle(config)
            if args.backend == "ideal"
            else rocketcea(config, args.oxidizer, args.fuel)
        )
        print(json.dumps(result.as_dict(), indent=2))
    elif args.command == "flight":
        samples, summary = simulate(load_flight(args.config))
        write_csv(samples, args.output)
        print(json.dumps(summary.as_dict(), indent=2))
        print(f"wrote {args.output}")
    elif args.command == "imu-replay":
        result = replay(args.input, args.output)
        print(json.dumps(asdict_estimate(result[-1]), indent=2))
        print(f"wrote {args.output}")
    elif args.command == "imu-demo":
        samples, _ = simulate(load_flight(args.config))
        make_synthetic_log(samples, args.log)
        result = replay(args.log, args.output)
        print(json.dumps(asdict_estimate(result[-1]), indent=2))
        print(f"wrote {args.log} and {args.output}")
    elif args.command == "guidance":
        advisories = replay_estimates(
            args.input, args.output, args.target_apogee_m, args.recovery_margin_m
        )
        print(json.dumps(asdict_estimate(advisories[-1]), indent=2))
        print(f"wrote {args.output}; advisory-only, no actuator commands issued")
    elif args.command == "dispersion":
        cases, summary = run_dispersion(
            load_flight(args.config), args.cases, args.seed,
            args.mass_sigma, args.drag_sigma, args.thrust_sigma,
        )
        write_dispersion_csv(cases, args.output)
        if args.summary_output is not None:
            write_summary(summary, args.summary_output, mass_sigma=args.mass_sigma,
                          drag_sigma=args.drag_sigma, thrust_sigma=args.thrust_sigma)
        print(json.dumps(asdict_estimate(summary), indent=2))
        print(f"wrote {args.output}")
    elif args.command == "bom-check":
        report = validate(args.input)
        print(json.dumps({**report.__dict__, "errors": list(report.errors)}, indent=2))
        return 1 if report.errors else 0
    elif args.command == "cad-info":
        print(json.dumps(inspect_mesh(args.input, args.units).as_dict(), indent=2))
    elif args.command == "openrocket-info":
        print(json.dumps(inspect_project(args.input).as_dict(), indent=2))
    elif args.command == "mass-info":
        print(json.dumps(load_mass_properties(args.input).as_dict(), indent=2))
    elif args.command == "aero-info":
        print(json.dumps(load_aero_polar(args.input).as_dict(), indent=2))
    return 0


def asdict_estimate(value: object) -> dict[str, object]:
    from dataclasses import asdict

    return asdict(value)
