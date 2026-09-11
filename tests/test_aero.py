from pathlib import Path

from rocket_workbench.aero import load_aero_polar


def test_aero_polar_import(tmp_path: Path):
    path = tmp_path / "polar.csv"
    path.write_text("mach,alpha_deg,cd,cl,cm\n0.3,0,0.42,0,-0.01\n0.8,4,0.48,0.32,-0.04\n", encoding="utf-8")
    polar = load_aero_polar(path)
    assert len(polar.points) == 2
    assert polar.mach_max == 0.8
    assert polar.cd_min == 0.42
    assert polar.nearest(0.75, 3).cd == 0.48


def test_aero_polar_accepts_common_export_aliases(tmp_path: Path):
    path = tmp_path / "rasaero.csv"
    path.write_text("Mach,AoA,CD,CL,Cm\n0.4,2,0.4,0.1,-0.02\n", encoding="utf-8")
    polar = load_aero_polar(path)
    assert polar.points[0].alpha_deg == 2
