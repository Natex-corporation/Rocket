# CAD and adjacent simulation tools

## Recommended interchange path

```text
CAD (STEP/IGES native)
  ├─> STL/OBJ export ─> cad-info / trimesh (geometry sanity check)
  ├─> OpenRocket model ─> stability and basic trajectory checks
  ├─> RocketPy geometry + measured mass/CG ─> 6-DOF + weather + Monte Carlo
  ├─> CFD mesh ─> OpenFOAM, SU2, ANSYS Fluent, or Star-CCM+
  └─> structural mesh ─> CalculiX, Ansys Mechanical, Abaqus, or Nastran
```

The workbench's `cad-info` command is deliberately read-only. It reports vertices, faces,
bounding-box dimensions, and—when `trimesh` is installed—watertightness and mesh volume. It does
not infer drag, stability derivatives, stress, thermal performance, or manufacturability.

## Import rules

- Keep the native CAD file as the design authority; treat STL/OBJ as analysis exports.
- Record units explicitly. `cad-info` defaults to metres and supports `mm`, `cm`, and `in`.
- Validate mesh normals, watertightness, scale, and coordinate origin before meshing for CFD/FEA.
- Keep aerodynamic surfaces, internal cavities, and structural solids as separate named exports when
  downstream tools need different representations.
- Record CAD revision, export tolerance, repair operations, and mesh settings beside every result.
- Replace placeholder mass/CG/inertia values in the RocketPy integration with measured or CAD-derived
  properties reviewed by the structures team.

STEP/IGES parsing is intentionally not bundled: PythonOCC/CadQuery/OpenCascade environments are
large and platform-specific. Exporting a reviewed mesh from the team's CAD system is more
reproducible for this starter workbench; a future adapter can add native B-rep properties without
changing the CSV/JSON contract.

`openrocket-info` reads common XML metadata from `.ork` files (including gzip-compressed files)
and reports the project name, designer, length, mass, motor references, and component count. It is
an import/traceability aid, not a replacement for OpenRocket's simulation engine. Recreate the
reviewed dimensions, measured mass/CG/inertia, motor curve, weather, and recovery configuration in
RocketPy before using results for a flight decision.

`mass-info` validates a one-row SI CSV exported from CAD or FEA. Required columns are
`mass_kg`, `cg_x_m`, `cg_y_m`, `cg_z_m`, `ixx_kg_m2`, `iyy_kg_m2`, and `izz_kg_m2`; optional
products of inertia are `ixy_kg_m2`, `ixz_kg_m2`, and `iyz_kg_m2`. It deliberately does not guess
coordinate transforms or apply a parallel-axis correction. Confirm the inertia reference point and
axes before passing values into a RocketPy model.

`aero-info` validates dimensionless aerodynamic polars exported from CFD, RASAero-style tools, or
wind-tunnel reduction. Required columns are `mach`, `alpha_deg`, `cd`, `cl`, and `cm`. This is a
traceability and schema check; it does not interpolate coefficients or claim that a polar is valid
for every Reynolds number, configuration, or flight regime.

Common aliases are accepted for interoperability: `Mach`, `Mach Number`, `AoA`, `Alpha`, `CD`,
`CL`, and `Cm`, plus descriptive coefficient names. The normalized internal contract remains SI
angles in degrees and dimensionless coefficients.

For software-in-the-loop experiments, the parsed polar exposes a nearest-tabulated-point lookup.
That lookup is deliberately clamped and non-extrapolating; it is useful for wiring tests only,
not a substitute for a reviewed Mach/Reynolds-aware interpolation table.
