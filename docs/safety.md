# Safety and review boundary

This repository is an engineering workbench, not flight authorization. Rocket motors, pressure
systems, energetic recovery devices, high-current batteries, radio transmitters, and active
control surfaces can injure people and may be regulated.

- Follow your university's written safety system, launch-site rules, and national law.
- Have propulsion, structures, recovery, avionics, and software reviewed by competent people who
  did not author the item being reviewed.
- Treat every sample number as fictional until replaced by measured, traceable project data.
- Do not use theoretical CEA temperature/performance alone to size chambers, injectors, feed
  systems, pressure vessels, cooling, or structural margins.
- Use independent recovery electronics and physical safing/inhibits. Experimental software must
  fail safe and must not be the sole life-safety layer.
- Test with inert substitutes first. Separate personnel from pressurized/energetic hardware with
  suitable distance, shielding, procedures, and remote operation.
- Run Monte Carlo dispersion and verify the entire impact footprint is acceptable for every
  credible failure mode—not merely the nominal trajectory.

Before each flight, freeze inputs and software, archive checksums and test evidence, confirm the
BOM/assembly revision, run sensor calibration and preflight checks, and obtain the responsible
range/safety authority's approval.
