# Established toolchain

| Need | Primary tool | Why it is here |
|---|---|---|
| Airframe geometry and stability | OpenRocket | Mature visual model-rocket design and simulation |
| Higher-fidelity amateur trajectory/aerodynamics | RASAero II, RockSim | Useful independent cross-checks; proprietary/project-specific inputs must be archived |
| 6-DOF trajectory, weather, recovery, Monte Carlo | RocketPy | Python-native and supports variable mass and sensor studies |
| Controls and estimator prototyping | MATLAB/Simulink, Python/SciPy | Block-diagram and numerical controls development; export only reviewed models |
| Generic vehicle dynamics | JSBSim | Mature open-source 6-DOF dynamics engine; adapt coordinate and propulsion conventions carefully |
| Orbital/spaceflight mission analysis | NASA GMAT | Mission/orbit analysis, not atmospheric launch-rail or motor-internal simulation |
| Chemical equilibrium and theoretical performance | NASA CEA / RocketCEA | Established thermochemistry; RocketCEA provides Python access |
| Motor thrust-curve libraries | RASP `.eng` / OpenRocket motor data | Imported directly by the reference flight model |
| Combustion chemistry extensions | Cantera | Open-source kinetics, equilibrium, and reacting-flow library |
| Flight estimator, logs, HIL | PX4 EKF2 + PX4 SITL | Maintained embedded estimator and simulation interfaces |
| Ground station | QGroundControl | MAVLink telemetry, parameter, and log workflow |
| PCB and schematic source of truth | KiCad | Open electronics design and BOM properties |
| CFD / external aerodynamics | OpenFOAM, SU2, ANSYS Fluent, STAR-CCM+ | Generate and validate coefficient polars; connect through `aero-info` CSV contract |
| Structural and thermal FEA | CalculiX, Ansys Mechanical, Abaqus, Nastran | Produce reviewed mass properties and margins; connect mass data through `mass-info` |
| Versioning/CI | Git + pytest | Reproducible model and software reviews |

Official starting points:

- RocketPy: <https://docs.rocketpy.org/en/latest/>
- OpenRocket: <https://openrocket.readthedocs.io/en/latest/>
- NASA CEA: <https://nasa.github.io/cea/>
- RocketCEA: <https://rocketcea.readthedocs.io/en/latest/>
- Cantera: <https://cantera.org/stable/>
- PX4 simulation: <https://docs.px4.io/main/en/simulation/>
- PX4 EKF2: <https://docs.px4.io/main/en/advanced_config/tuning_the_ecl_ekf>
- QGroundControl: <https://docs.qgroundcontrol.com/master/en/>
- KiCad: <https://docs.kicad.org/>
- RASAero II: <https://www.rasaero.com/>
- NASA GMAT: <https://gmat.atlassian.net/wiki/spaces/GW/overview>
- JSBSim: <https://jsbsim.sourceforge.net/>
- OpenFOAM: <https://openfoam.org/>
- SU2: <https://su2code.github.io/>

Pin stable versions for a campaign, record them in the test report, and update only between test
campaigns. Never compare nominal apogees without also aligning mass, CG, atmosphere, thrust-curve
normalization, launch rail, drag assumptions, and recovery events.

PX4's stock vehicle models are not rocket models. Use its estimator/logging/HIL infrastructure,
but supply a reviewed rocket dynamics model through the documented simulator interface before
claiming closed-loop validation.
