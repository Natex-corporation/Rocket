from pathlib import Path

from rocket_workbench.mass_properties import load_mass_properties


def test_mass_properties_import(tmp_path: Path):
    path = tmp_path / "mass.csv"
    path.write_text(
        "mass_kg,cg_x_m,cg_y_m,cg_z_m,ixx_kg_m2,iyy_kg_m2,izz_kg_m2\n"
        "12.5,1.2,0,0,0.8,0.8,0.02\n",
        encoding="utf-8",
    )
    props = load_mass_properties(path)
    assert props.mass_kg == 12.5
    assert props.cg_x_m == 1.2
    assert props.izz_kg_m2 == 0.02
