from pathlib import Path

from rocket_workbench.config import FlightConfig, load_flight
from rocket_workbench.flight import simulate
from rocket_workbench.flight import load_thrust_curve
from rocket_workbench.dispersion import run as run_dispersion, write_summary
import pytest


ROOT = Path(__file__).parents[1]


def test_reference_flight_launches_and_lands():
    samples, summary = simulate(load_flight(ROOT / "examples/flight_reference.toml"))
    assert summary.apogee_m_agl > 100
    assert summary.rail_exit_velocity_m_s is not None
    assert summary.rail_exit_velocity_m_s > 10
    assert samples[-1].altitude_m < 1
    assert samples[-1].phase == "recovery"


def test_thrust_curve_rejects_negative_values(tmp_path):
    curve = tmp_path / "bad.csv"
    curve.write_text("time_s,thrust_n\n0,0\n1,-1\n", encoding="utf-8")
    try:
        load_thrust_curve(curve)
    except ValueError as exc:
        assert "non-negative" in str(exc)
    else:
        raise AssertionError("negative thrust was accepted")


def test_thrust_curve_rejects_missing_schema(tmp_path):
    curve = tmp_path / "bad-schema.csv"
    curve.write_text("time_s,force_n\n0,0\n1,10\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing columns"):
        load_thrust_curve(curve)


def test_rasp_eng_motor_import(tmp_path):
    motor = tmp_path / "demo.eng"
    motor.write_text(
        "; RASP motor file\nDemo 24 70 0-0 0.10 0.25 0.15 0.05\n"
        "0.0 0.0\n0.1 100.0\n0.2 0.0\n",
        encoding="utf-8",
    )
    assert load_thrust_curve(motor) == [(0.0, 0.0), (0.1, 100.0), (0.2, 0.0)]


def test_dispersion_is_seeded_and_reports_percentiles():
    config = load_flight(ROOT / "examples/flight_reference.toml")
    _, first = run_dispersion(config, cases=8, seed=11)
    _, second = run_dispersion(config, cases=8, seed=11)
    assert first == second
    assert first.apogee_p05_m < first.apogee_p50_m < first.apogee_p95_m


def test_dispersion_accepts_custom_uncertainty_widths():
    config = load_flight(ROOT / "examples/flight_reference.toml")
    _, report = run_dispersion(config, cases=8, seed=11, mass_sigma=0.0, drag_sigma=0.0, thrust_sigma=0.0)
    assert report.apogee_p05_m == report.apogee_p50_m == report.apogee_p95_m


def test_dispersion_summary_is_reproducible_metadata(tmp_path):
    config = load_flight(ROOT / "examples/flight_reference.toml")
    _, report = run_dispersion(config, cases=2, seed=3)
    summary = tmp_path / "summary.json"
    write_summary(report, summary, mass_sigma=0.03, drag_sigma=0.08, thrust_sigma=0.05)
    text = summary.read_text(encoding="utf-8")
    assert '"seed": 3' in text
    assert '"model": "vertical point-mass reference simulation"' in text


def test_flight_config_rejects_missing_curve():
    with pytest.raises(ValueError, match="does not exist"):
        FlightConfig(18, 4, 0.1524, 0.55, 300, 6, 0.01, 300, 1.8, 1, ROOT / "missing.csv")
