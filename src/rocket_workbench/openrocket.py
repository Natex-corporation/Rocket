from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import gzip
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class OpenRocketInfo:
    path: str
    name: str | None
    designer: str | None
    rocket_length_m: float | None
    rocket_mass_kg: float | None
    motor_names: tuple[str, ...]
    component_count: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _value(root: ET.Element, tag: str) -> float | None:
    item = root.find(f".//{tag}")
    if item is None or item.text is None:
        return None
    try:
        return float(item.text)
    except ValueError:
        return None


def inspect_project(path: Path) -> OpenRocketInfo:
    """Read common OpenRocket XML metadata without altering the project."""
    if not path.is_file():
        raise ValueError(f"OpenRocket project does not exist: {path}")
    try:
        raw = path.read_bytes()
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        root = ET.fromstring(raw)
    except (OSError, ET.ParseError, gzip.BadGzipFile) as exc:
        raise ValueError(f"could not parse OpenRocket project: {path}") from exc
    motor_names = tuple(sorted({item.text.strip() for item in root.findall(".//motor") if item.text and item.text.strip()}))
    name = root.findtext(".//name")
    designer = root.findtext(".//designer")
    return OpenRocketInfo(
        str(path), name.strip() if name else None, designer.strip() if designer else None,
        _value(root, "length"), _value(root, "mass"), motor_names,
        sum(1 for item in root.iter() if item.tag in {"stage", "bodytube", "nosecone", "trapezoidfinset", "transition"}),
    )
