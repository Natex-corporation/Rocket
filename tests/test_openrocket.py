from pathlib import Path

from rocket_workbench.openrocket import inspect_project


def test_openrocket_metadata_import(tmp_path: Path):
    project = tmp_path / "sample.ork"
    project.write_text(
        "<openrocket><name>Demo Rocket</name><designer>Student Team</designer>"
        "<rocket><length>2.4</length><mass>12.5</mass><stage><bodytube/>"
        "<motor>example.eng</motor></stage></rocket></openrocket>",
        encoding="utf-8",
    )
    info = inspect_project(project)
    assert info.name == "Demo Rocket"
    assert info.rocket_length_m == 2.4
    assert info.rocket_mass_kg == 12.5
    assert info.motor_names == ("example.eng",)
    assert info.component_count == 2
