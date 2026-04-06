import math
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.simulation.histamine_driver import _bateman_pulse, resolve_histamine_nm
from pkpd_xc7.simulation.model_mapping import resolve_effective_h_base_nm
from pkpd_xc7.simulation.runner import run_experiment
from pkpd_xc7.solvers.solve_ivp_wrapper import SolverConfig


def _pk_config() -> ModelConfig:
    return ModelConfig.model_validate(
        {
            "model_id": "phase3_pk",
            "compound": "xc7",
            "traceability": {"source_in_report": "table-1"},
            "assumptions": ["pk driver test"],
            "driver": {"driver_type": "pk", "k_abs_per_h": 1.0, "k_elim_per_h": 0.5},
            "trafficking": {"h_base_nm": 50.0},
            "tissues": ["brain"],
            "time_grid_h": [0.0, 1.0],
        }
    )


def test_bateman_edge_case():
    """Проверка краевого случая ka == ke через предел Лопиталя."""
    dose, ka, ke = 100.0, 1.0, 1.0
    t = 2.0
    # Ожидаемое значение: D * ka * t * exp(-ka * t)
    expected = dose * ka * t * math.exp(-ka * t)
    result = _bateman_pulse(t, dose, ka, ke)
    assert math.isclose(result, expected, rel_tol=1e-7)
    
    # Проверка обычного случая ka != ke
    result_normal = _bateman_pulse(t, 100.0, 2.0, 0.5)
    expected_normal = 100.0 * 2.0 / (2.0 - 0.5) * (math.exp(-0.5 * t) - math.exp(-2.0 * t))
    assert math.isclose(result_normal, expected_normal, rel_tol=1e-7)


def test_resolve_histamine_nm_pk_driver():
    """Убеждаемся, что PK ветка работает и гистамин не константный."""
    config = _pk_config()

    h_t0 = resolve_histamine_nm(0.0, config, "tissue_1")
    h_t1 = resolve_histamine_nm(1.0, config, "tissue_1")
    h_t5 = resolve_histamine_nm(5.0, config, "tissue_1")

    # Должен быть базовый уровень + выброс, который растет, затем падает
    assert math.isclose(h_t0, 50.0, rel_tol=0.0, abs_tol=1e-12)  # (t=0 -> pulse=0)
    assert h_t1 > 50.0
    assert h_t5 != h_t1


def test_resolve_histamine_nm_pk_driver_uses_tissue_specific_h_base() -> None:
    config = ModelConfig.model_validate(
        {
            "model_id": "phase3_pk_hbase",
            "compound": "xc7",
            "traceability": {"source_in_report": "table-1"},
            "assumptions": ["pk driver h_base override test"],
            "driver": {"driver_type": "pk", "k_abs_per_h": 1.0, "k_elim_per_h": 0.5},
            "trafficking": {"h_base_nm": 50.0},
            "tissue_overrides": {
                "spinal_coord": {"trafficking": {"h_base_nm": 2.0}},
                "brain": {"trafficking": {"h_base_nm": 3.0}},
            },
            "tissues": ["spinal_coord", "brain"],
            "time_grid_h": [0.0, 1.0],
        }
    )

    spinal_h_base = resolve_effective_h_base_nm(config, "spinal_coord")
    brain_h_base = resolve_effective_h_base_nm(config, "brain")

    assert spinal_h_base is not None
    assert brain_h_base is not None
    assert math.isclose(spinal_h_base, 2.0, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(brain_h_base, 3.0, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(resolve_histamine_nm(0.0, config, "spinal_coord"), 2.0, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(resolve_histamine_nm(0.0, config, "brain"), 3.0, rel_tol=0.0, abs_tol=1e-12)


@patch("pkpd_xc7.solvers.ivp.solve_ivp_wrapper")
def test_runner_uses_wrapper(mock_solve_ivp_wrapper):
    """Убеждаемся, что run_experiment использует обертку SolverConfig и solve_ivp_wrapper."""
    config = _pk_config()

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.y = np.array([[1.0, 0.9], [0.0, 0.1]])
    mock_solve_ivp_wrapper.return_value = mock_result

    df = run_experiment(config)

    # Проверяем, что solve_ivp_wrapper был вызван с нужными аргументами
    mock_solve_ivp_wrapper.assert_called_once()
    assert "config" in mock_solve_ivp_wrapper.call_args.kwargs
    assert isinstance(mock_solve_ivp_wrapper.call_args.kwargs["config"], SolverConfig)

    # Метаданные должны быть сохранены в DataFrame.attrs
    assert "solver_metadata" in df.attrs
    assert df.attrs["solver_metadata"]["solver_method"] == "LSODA"


@patch("pkpd_xc7.solvers.ivp.solve_ivp_wrapper")
def test_run_experiment_fails_fast_on_post_validation_invariant_violation(mock_solve_ivp_wrapper):
    config = _pk_config()

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.y = np.array([[1.0, 0.4], [0.0, 0.600002]])
    mock_solve_ivp_wrapper.return_value = mock_result

    with pytest.raises(
        ValueError,
        match=r"tissue 'brain'.*R_surf \+ R_int=.*must be <= 1 \+ eps",
    ):
        run_experiment(config)