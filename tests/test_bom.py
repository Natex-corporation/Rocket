from pathlib import Path

from rocket_workbench.bom import validate


def test_reference_bom_is_machine_valid():
    report = validate(Path(__file__).parents[1] / "bom/reference_bom.csv")
    assert report.rows >= 8
    assert not report.errors
    assert report.placeholders > 0
