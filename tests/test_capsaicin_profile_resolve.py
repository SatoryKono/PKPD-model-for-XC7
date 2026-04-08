from __future__ import annotations

import numpy as np
import pytest

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.simulation.histamine_driver import resolve_histamine_nm
from pkpd_xc7.simulation.scenario_registry import get_scenario_spec, resolve_capsaicin_spec


def _capsaicin_config(**overrides: object) -> ModelConfig:
    payload: dict[str, object] = {
        "model_id": "capsaicin_cfg",
        "compound": "xc7",
        "loss_mode": "mse",
        "assumptions": ["capsaicin spec test"],
        "traceability": {"source_in_report": "unit test"},
        "driver": {"driver_type": "scenario", "scenario_id": "capsaicin"},
        "tissues": ["skin", "spinal_coord", "ganglia"],
        "time_grid_h": [0.0, 0.5, 1.0],
    }
    payload.update(overrides)
    return ModelConfig.model_validate(payload)


def test_resolve_capsaicin_spec_uses_registered_defaults() -> None:
    config = _capsaicin_config()
    base = get_scenario_spec("capsaicin")
    resolved = resolve_capsaicin_spec(config)

    assert resolved.scenario_id == "capsaicin"
    assert resolved.profile_shape == base.default_shape
    assert resolved.tissue_profiles["skin"].h_base_nm == pytest.approx(50.0)
    assert resolved.tissue_profiles["skin"].gaussian_components[0].amplitude_nm == pytest.approx(177.0)
    assert resolved.tissue_profiles["spinal_coord"].h_base_nm == pytest.approx(2.0)
    assert resolved.tissue_profiles["ganglia"].h_base_nm == pytest.approx(5.0)


def test_capsaicin_profile_override_updates_defaults() -> None:
    config = _capsaicin_config(
        trafficking={"h_base_nm": 55.0},
        capsaicin_profile={
            "profile_shape": "gaussian_sum",
            "h_base_nm": 60.0,
            "phase1": {"amplitude_nm": 190.0, "center_min": 20.0, "sigma_min": 10.0},
        },
    )

    resolved = resolve_capsaicin_spec(config)
    skin = resolved.tissue_profiles["skin"]

    assert skin.h_base_nm == pytest.approx(60.0)
    assert skin.gaussian_components[0].amplitude_nm == pytest.approx(190.0)
    assert skin.gaussian_components[0].center_h == pytest.approx(20.0 / 60.0)
    assert skin.gaussian_components[0].sigma_h == pytest.approx(10.0 / 60.0)


def test_capsaicin_tissue_override_has_priority_over_global_override() -> None:
    config = _capsaicin_config(
        capsaicin_profile={
            "profile_shape": "gaussian_sum",
            "h_base_nm": 60.0,
            "phase1": {"amplitude_nm": 190.0, "center_min": 20.0, "sigma_min": 10.0},
        },
        tissue_overrides={
            "spinal_coord": {
                "capsaicin_profile": {
                    "h_base_nm": 3.0,
                    "phase1": {"amplitude_nm": 12.0, "center_min": 25.0, "sigma_min": 18.0},
                }
            }
        },
    )

    resolved = resolve_capsaicin_spec(config)
    skin_profile = resolved.tissue_profiles["skin"]
    spinal_profile = resolved.tissue_profiles["spinal_coord"]

    assert skin_profile.h_base_nm == pytest.approx(60.0)
    assert spinal_profile.h_base_nm == pytest.approx(3.0)
    assert skin_profile.gaussian_components[0].amplitude_nm == pytest.approx(190.0)
    assert spinal_profile.gaussian_components[0].amplitude_nm == pytest.approx(12.0)
    assert spinal_profile.gaussian_components[0].center_h == pytest.approx(25.0 / 60.0)


def test_capsaicin_histamine_is_deterministic_for_same_config() -> None:
    config = _capsaicin_config(
        capsaicin_profile={"phase1": {"amplitude_nm": 180.0, "center_min": 12.0, "sigma_min": 10.0}}
    )
    grid = np.array([0.0, 5.0 / 60.0, 15.0 / 60.0, 1.0], dtype=float)

    first = np.array([resolve_histamine_nm(float(t_h), config, "skin") for t_h in grid], dtype=float)
    second = np.array([resolve_histamine_nm(float(t_h), config, "skin") for t_h in grid], dtype=float)

    np.testing.assert_array_equal(first, second)


def test_capsaicin_supports_pulse_shape_overrides() -> None:
    config = _capsaicin_config(
        driver={"driver_type": "scenario", "scenario_id": "capsaicin", "profile_shape": "pulse"},
        capsaicin_profile={
            "profile_shape": "pulse",
            "phase1": {"amplitude_nm": 900.0, "center_min": 0.0, "tau_rise_min": 15.0, "tau_fall_min": 120.0},
        },
    )

    resolved = resolve_capsaicin_spec(config)
    skin = resolved.tissue_profiles["skin"]

    assert resolved.profile_shape == "pulse"
    assert skin.pulse_phases[0].amplitude_nm == pytest.approx(900.0)
    assert skin.pulse_phases[0].tau_rise_h == pytest.approx(15.0 / 60.0)
    assert skin.pulse_phases[0].tau_fall_h == pytest.approx(120.0 / 60.0)

    early = resolve_histamine_nm(5.0 / 60.0, config, "skin")
    assert early > skin.h_base_nm
