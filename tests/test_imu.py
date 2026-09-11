from pathlib import Path

from rocket_workbench.config import load_flight
from rocket_workbench.flight import simulate
from rocket_workbench.imu import make_synthetic_log, replay
from rocket_workbench.guidance import ballistic_apogee, replay_estimates


ROOT = Path(__file__).parents[1]


def test_synthetic_log_replays(tmp_path):
    samples, _ = simulate(load_flight(ROOT / "examples/flight_reference.toml"))
    log, output = tmp_path / "imu.csv", tmp_path / "estimate.csv"
    make_synthetic_log(samples, log)
    estimates = replay(log, output)
    assert output.exists()
    assert max(item.altitude_m for item in estimates) > 100
    assert {item.phase for item in estimates} >= {"PAD", "BOOST", "COAST", "DESCENT"}


def test_imu_replay_rejects_empty_log(tmp_path):
    log = tmp_path / "empty.csv"
    log.write_text("time_s,ax_m_s2,ay_m_s2,az_m_s2,gx_rad_s,gy_rad_s,gz_rad_s,baro_altitude_m\n", encoding="utf-8")
    try:
        replay(log, tmp_path / "estimate.csv")
    except ValueError as exc:
        assert "no samples" in str(exc)
    else:
        raise AssertionError("empty log was accepted")


def test_imu_replay_rejects_nonfinite_sensor_value(tmp_path):
    log = tmp_path / "nan.csv"
    log.write_text(
        "time_s,ax_m_s2,ay_m_s2,az_m_s2,gx_rad_s,gy_rad_s,gz_rad_s,baro_altitude_m\n"
        "0,nan,0,-9.8,0,0,0,0\n",
        encoding="utf-8",
    )
    try:
        replay(log, tmp_path / "estimate.csv")
    except ValueError as exc:
        assert "non-finite" in str(exc)
    else:
        raise AssertionError("non-finite sensor value was accepted")


def test_guidance_is_advisory_only_and_replays_estimates(tmp_path):
    samples, _ = simulate(load_flight(ROOT / "examples/flight_reference.toml"))
    log, estimate, advisory = (
        tmp_path / "imu.csv",
        tmp_path / "estimate.csv",
        tmp_path / "advisory.csv",
    )
    make_synthetic_log(samples, log)
    replay(log, estimate)
    advisories = replay_estimates(estimate, advisory, target_apogee_m=2_000)
    assert advisory.exists()
    assert ballistic_apogee(100, 20) > 120
    assert advisories[-1].recommendation in {"RECOVERY_SYSTEM_REQUIRED", "UNKNOWN_PHASE_HOLD"}
