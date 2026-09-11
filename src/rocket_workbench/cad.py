"""Lightweight CAD mesh inspection with an optional trimesh backend.

The importer is intentionally read-only. It extracts mesh metadata and does not infer aerodynamic
coefficients, structural margins, or flight stability from geometry alone.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite, sqrt
from pathlib import Path
import re


@dataclass(frozen=True)
class CadMeshInfo:
    path: str
    format: str
    vertices: int
    faces: int
    bounds_min_m: tuple[float, float, float]
    bounds_max_m: tuple[float, float, float]
    volume_m3: float | None
    watertight: bool | None
    backend: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _bounds(vertices: list[tuple[float, float, float]]) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if not vertices:
        raise ValueError("CAD mesh contains no vertices")
    return tuple(min(v[i] for v in vertices) for i in range(3)), tuple(max(v[i] for v in vertices) for i in range(3))


def _scale_bounds(bounds: tuple[tuple[float, float, float], tuple[float, float, float]], scale: float):
    return tuple(tuple(value * scale for value in item) for item in bounds)


def inspect_mesh(path: Path, units: str = "m") -> CadMeshInfo:
    """Inspect STL/OBJ mesh exports and normalize coordinates to metres.

    Supported units: ``m``, ``mm``, ``cm``, and ``in``. If trimesh is installed it supplies
    watertightness and signed volume; otherwise metadata remains available without dependencies.
    """
    if units not in {"m", "mm", "cm", "in"}:
        raise ValueError("units must be one of m, mm, cm, or in")
    if not path.is_file():
        raise ValueError(f"CAD file does not exist: {path}")
    suffix = path.suffix.lower()
    if suffix not in {".stl", ".obj"}:
        raise ValueError("CAD mesh format must be STL or OBJ; export STEP/IGES to a mesh first")
    scale = {"m": 1.0, "mm": 1e-3, "cm": 1e-2, "in": 0.0254}[units]
    try:
        import trimesh  # type: ignore
    except ImportError:
        trimesh = None
    if trimesh is not None:
        mesh = trimesh.load_mesh(path, process=False)
        if hasattr(mesh, "geometry"):
            mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
        bounds = _scale_bounds((tuple(mesh.bounds[0]), tuple(mesh.bounds[1])), scale)
        volume = float(abs(mesh.volume)) * scale**3 if isfinite(float(mesh.volume)) else None
        return CadMeshInfo(str(path), suffix[1:].upper(), len(mesh.vertices), len(mesh.faces),
                           bounds[0], bounds[1], volume, bool(mesh.is_watertight), "trimesh")
    text = path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".obj":
        vertices = [tuple(float(item) for item in match.split()) for match in
                    re.findall(r"(?m)^v\s+([-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+)", text)]
        faces = sum(1 for line in text.splitlines() if line.lstrip().startswith("f "))
    else:
        vertices = [tuple(float(item) for item in match) for match in
                    re.findall(r"(?m)^\s*vertex\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)", text)]
        faces = sum(1 for line in text.splitlines() if line.strip().lower() == "endloop")
    bounds = _scale_bounds(_bounds(vertices), scale)
    return CadMeshInfo(str(path), suffix[1:].upper(), len(set(vertices)), faces,
                       bounds[0], bounds[1], None, None, "builtin-metadata")
