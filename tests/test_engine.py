from rocket_workbench.config import EngineConfig
from rocket_workbench.engine import ideal_nozzle
import pytest


def test_ideal_engine_is_physically_plausible():
    result = ideal_nozzle(EngineConfig(40, 3.4, 20, 3500, 1.22, 22))
    assert 1300 < result.characteristic_velocity_m_s < 2500
    assert 150 < result.specific_impulse_s < 400
    assert result.exit_mach > 2


def test_engine_config_rejects_nonphysical_values():
    with pytest.raises(ValueError, match="expansion ratio"):
        EngineConfig(40, 3.4, 1, 3500, 1.22, 22)
