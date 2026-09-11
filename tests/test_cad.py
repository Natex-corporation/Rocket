from pathlib import Path

from rocket_workbench.cad import inspect_mesh


def test_builtin_stl_inspection_normalizes_units(tmp_path: Path):
    stl = tmp_path / "triangle.stl"
    stl.write_text(
        "solid test\n"
        " facet normal 0 0 1\n outer loop\n"
        "  vertex 0 0 0\n  vertex 10 0 0\n  vertex 0 10 0\n"
        " endloop\n endfacet\nendsolid test\n",
        encoding="utf-8",
    )
    info = inspect_mesh(stl, "mm")
    assert info.format == "STL"
    assert info.vertices == 3
    assert info.faces == 1
    assert info.bounds_max_m == (0.01, 0.01, 0.0)
