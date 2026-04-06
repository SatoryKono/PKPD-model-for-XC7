from __future__ import annotations

import numpy as np
from pandas.testing import assert_frame_equal

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.simulation.histamine_driver import resolve_histamine_nm
from pkpd_xc7.simulation.runner import run_experiment
from pkpd_xc7.simulation.scenario_registry import get_scenario_spec


def _capsaicin_config() -> ModelConfig:
    return ModelConfig.model_validate(
        {
            "model_id": "capsaicin_deterministic",
            "compound": "xc7",
            "loss_mode": "mse",
            "traceability": {"source_in_report": "deterministic test"},
            "assumptions": ["capsaicin registry deterministic test"],
            "driver": {"driver_type": "scenario", "scenario_id": "capsaicin"},
            "tissues": ["skin", "spinal_coord", "ganglia"],
            "time_grid_h": [0.0, 0.25, 0.5, 1.0, 2.0],
        }
    )


def test_capsaicin_registry_profile_is_deterministic() -> None:
    config = _capsaicin_config()
    spec = get_scenario_spec("capsaicin")
    grid = np.array(config.time_grid_h, dtype=float)

    first = np.array([resolve_histamine_nm(float(t_h), config, "skin") for t_h in grid], dtype=float)
    second = np.array([resolve_histamine_nm(float(t_h), config, "skin") for t_h in grid], dtype=float)

    assert spec.scenario_id == "capsaicin"
    np.testing.assert_array_equal(first, second)


def test_run_experiment_is_deterministic_for_capsaicin_scenario() -> None:
    config = _capsaicin_config()

    first = run_experiment(config)
    second = run_experiment(config)

    assert_frame_equal(first, second)
    assert first.attrs["solver_metadata"] == second.attrs["solver_metadata"]
    assert first.attrs["runtime_assumptions"] == second.attrs["runtime_assumptions"]
