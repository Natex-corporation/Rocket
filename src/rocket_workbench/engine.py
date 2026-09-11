from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt

from .config import EngineConfig

G0 = 9.80665
R_UNIVERSAL = 8.314462618


@dataclass(frozen=True)
class EngineResult:
    method: str
    characteristic_velocity_m_s: float
    thrust_coefficient: float
    specific_impulse_s: float
    exit_mach: float
    exit_pressure_pa: float

    def as_dict(self) -> dict[str, float | str]:
        return asdict(self)


def _area_ratio(mach: float, gamma: float) -> float:
    term = (2 / (gamma + 1)) * (1 + (gamma - 1) * mach * mach / 2)
    return (term ** ((gamma + 1) / (2 * (gamma - 1)))) / mach


def _supersonic_mach(expansion_ratio: float, gamma: float) -> float:
    lo, hi = 1.000001, 20.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if _area_ratio(mid, gamma) < expansion_ratio:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def ideal_nozzle(config: EngineConfig) -> EngineResult:
    """Ideal, equilibrium, calorically-perfect-gas nozzle estimate.

    This is a transparent sanity check, not a substitute for NASA CEA/RocketCEA.
    """
    g = config.gamma
    pc = config.chamber_pressure_bar * 100_000
    gas_r = R_UNIVERSAL / (config.molar_mass_g_mol / 1000)
    c_star = sqrt(gas_r * config.chamber_temperature_k / g) / (
        (2 / (g + 1)) ** ((g + 1) / (2 * (g - 1)))
    )
    me = _supersonic_mach(config.expansion_ratio, g)
    pressure_ratio = (1 + (g - 1) * me * me / 2) ** (-g / (g - 1))
    pe = pc * pressure_ratio
    momentum_cf = sqrt(
        (2 * g * g / (g - 1))
        * (2 / (g + 1)) ** ((g + 1) / (g - 1))
        * (1 - pressure_ratio ** ((g - 1) / g))
    )
    cf = momentum_cf + (pe - config.ambient_pressure_pa) * config.expansion_ratio / pc
    return EngineResult("ideal-gas", c_star, cf, cf * c_star / G0, me, pe)


def rocketcea(config: EngineConfig, oxidizer: str, fuel: str) -> EngineResult:
    """Use RocketCEA when installed; values are converted explicitly to SI."""
    try:
        from rocketcea.cea_obj import CEA_Obj
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("RocketCEA is not installed; install the 'engine' extra") from exc
    cea = CEA_Obj(oxName=oxidizer, fuelName=fuel)
    pc_psi = config.chamber_pressure_bar * 14.5037738
    isp = cea.estimate_Ambient_Isp(
        Pc=pc_psi,
        MR=config.mixture_ratio,
        eps=config.expansion_ratio,
        Pamb=config.ambient_pressure_pa / 6_894.757293,
    )[0]
    c_star_ft_s = cea.get_Cstar(Pc=pc_psi, MR=config.mixture_ratio)
    c_star = c_star_ft_s * 0.3048
    fallback = ideal_nozzle(config)
    return EngineResult(
        "RocketCEA",
        c_star,
        float(isp) * G0 / c_star,
        float(isp),
        fallback.exit_mach,
        fallback.exit_pressure_pa,
    )
