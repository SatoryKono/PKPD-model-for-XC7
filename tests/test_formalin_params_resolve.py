from __future__ import annotations

import numpy as np
import pytest

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.simulation.histamine_driver import resolve_histamine_nm
from pkpd_xc7.simulation.scenario_registry import (
    build_scenario_histamine_nm,
    get_scenario_spec,
    resolve_formalin_spec,
    sum_gaussian_profile_nm,
    sum_pulse_profile_nm,
)


def _formalin_config(**overrides: object) -> ModelConfig:
    payload: dict[str, object] = {
        "model_id": "formalin_cfg",
        "compound": "xc7",
        "loss_mode": "mse",
        "assumptions": ["formalin spec test"],
        "traceability": {"source_in_report": "unit test"},
        "driver": {"driver_type": "scenario", "scenario_id": "formalin"},
        "tissues": ["skin", "spinal_coord", "ganglia"],
        "time_grid_h": [0.0, 0.5, 1.0],
    }
    payload.update(overrides)
    return ModelConfig.model_validate(payload)


def test_resolve_formalin_spec_uses_registered_defaults() -> None:
    config = _formalin_config()
    base = get_scenario_spec("formalin")
    resolved = resolve_formalin_spec(config)

    assert resolved.scenario_id == "formalin"
    assert resolved.profile_shape == base.default_shape
    assert resolved.tissue_profiles["skin"].h_base_nm == pytest.approx(50.0)
    assert resolved.tissue_profiles["spinal_coord"].h_base_nm == pytest.approx(2.0)
    assert resolved.tissue_profiles["ganglia"].h_base_nm == pytest.approx(5.0)


def test_top_level_trafficking_h_base_overrides_registered_values() -> None:
    config = _formalin_config(
        trafficking={"h_base_nm": 55.0},
        formalin_profile={
            "phase1": {"amplitude_nm": 960.0, "center_min": 6.0, "sigma_min": 8.0},
            "phase2": {"amplitude_nm": 275.0},
        }
    )

    resolved = resolve_formalin_spec(config)
    skin = resolved.tissue_profiles["skin"]

    assert skin.h_base_nm == pytest.approx(55.0)
    assert skin.gaussian_components[0].amplitude_nm == pytest.approx(960.0)
    assert skin.gaussian_components[0].center_h == pytest.approx(0.1)
    assert skin.gaussian_components[0].sigma_h == pytest.approx(8.0 / 60.0)
    assert skin.gaussian_components[1].amplitude_nm == pytest.approx(275.0)


def test_tissue_specific_trafficking_h_base_wins_over_top_level_override() -> None:
    config = _formalin_config(
        trafficking={"h_base_nm": 55.0},
        tissue_overrides={
            "skin": {
                "trafficking": {"h_base_nm": 10.0},
                "formalin_profile": {
                    "phase1": {"center_min": 7.0},
                }
            }
        },
    )

    resolved = resolve_formalin_spec(config)

    assert resolved.tissue_profiles["skin"].h_base_nm == pytest.approx(10.0)
    assert resolved.tissue_profiles["skin"].gaussian_components[0].center_h == pytest.approx(7.0 / 60.0)
    assert resolved.tissue_profiles["spinal_coord"].h_base_nm == pytest.approx(55.0)


def test_legacy_formalin_profile_h_base_remains_backward_compatible() -> None:
    config = _formalin_config(formalin_profile={"h_base_nm": 60.0})

    resolved = resolve_formalin_spec(config)

    assert resolved.tissue_profiles["skin"].h_base_nm == pytest.approx(60.0)


def test_formalin_histamine_is_deterministic_for_same_config() -> None:
    config = _formalin_config(
        formalin_profile={"phase1": {"amplitude_nm": 925.0}, "phase2": {"amplitude_nm": 240.0}}
    )
    grid = np.array([0.0, 5.0 / 60.0, 15.0 / 60.0, 1.0], dtype=float)

    first = np.array([resolve_histamine_nm(float(t_h), config, "skin") for t_h in grid], dtype=float)
    second = np.array([resolve_histamine_nm(float(t_h), config, "skin") for t_h in grid], dtype=float)

    np.testing.assert_array_equal(first, second)


def test_formalin_profile_shape_can_switch_to_pulse() -> None:
    config = _formalin_config(
        driver={"driver_type": "scenario", "scenario_id": "formalin", "profile_shape": "pulse"}
    )

    resolved = resolve_formalin_spec(config)
    assert resolved.profile_shape == "pulse"


def test_formalin_profile_shape_can_be_tissue_specific() -> None:
    config = _formalin_config(
        driver={"driver_type": "scenario", "scenario_id": "formalin", "profile_shape": "pulse"},
        tissue_overrides={
            "skin": {
                "formalin_profile": {
                    "profile_shape": "gaussian_sum",
                    "phase1": {"amplitude_nm": 900.0, "center_min": 6.0, "sigma_min": 8.0},
                }
            }
        },
    )

    resolved = resolve_formalin_spec(config)
    assert resolved.profile_shape == "pulse"
    assert resolved.tissue_profile_shapes["skin"] == "gaussian_sum"
    assert resolved.tissue_profile_shapes["spinal_coord"] == "pulse"

    t_h = 6.0 / 60.0
    skin_profile = resolved.tissue_profiles["skin"]
    spinal_profile = resolved.tissue_profiles["spinal_coord"]

    assert build_scenario_histamine_nm(t_h, resolved, "skin") == pytest.approx(
        sum_gaussian_profile_nm(t_h, skin_profile)
    )
    assert build_scenario_histamine_nm(t_h, resolved, "skin") != pytest.approx(
        sum_pulse_profile_nm(t_h, skin_profile)
    )
    assert build_scenario_histamine_nm(t_h, resolved, "spinal_coord") == pytest.approx(
        sum_pulse_profile_nm(t_h, spinal_profile)
    )
