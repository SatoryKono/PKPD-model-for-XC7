from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.simulation import histamine_driver
from pkpd_xc7.simulation.histamine_driver import resolve_histamine_nm
from pkpd_xc7.simulation.scenario_registry import (
    get_scenario_spec,
    hours_from_minutes,
    resolve_formalin_spec,
)


def _scenario_config(**overrides: object) -> ModelConfig:
    payload: dict[str, object] = {
        "model_id": "phase5_scenario",
        "compound": "xc7",
        "traceability": {"source_in_report": "table-1"},
        "assumptions": ["phase5 registry test"],
        "driver": {"driver_type": "scenario", "scenario_id": "formalin"},
        "tissues": ["skin", "spinal_coord", "ganglia"],
        "time_grid_h": [0.0, 0.5, 1.0],
    }
    payload.update(overrides)
    return ModelConfig.model_validate(payload)


def _gaussian_sum(t_min: float, h_base: float, phases: list[tuple[float, float, float]]) -> float:
    value = h_base
    for amplitude, center, sigma in phases:
        value += amplitude * math.exp(-((t_min - center) ** 2) / (2.0 * sigma**2))
    return value


def test_formalin_registry_matches_legacy_plot_formulas() -> None:
    config = _scenario_config()

    skin = resolve_histamine_nm(5.0 / 60.0, config, "skin")
    spinal_coord = resolve_histamine_nm(30.0 / 60.0, config, "spinal_coord")
    ganglia = resolve_histamine_nm(15.0 / 60.0, config, "ganglia")

    expected_skin = _gaussian_sum(5.0, 50.0, [(950.0, 5.0, 4.0), (250.0, 40.0, 25.0)])
    expected_spinal = _gaussian_sum(30.0, 2.0, [(10.0, 30.0, 20.0)])
    expected_ganglia = _gaussian_sum(15.0, 5.0, [(10.0, 15.0, 10.0)])

    assert math.isclose(skin, expected_skin, rel_tol=1e-12)
    assert math.isclose(spinal_coord, expected_spinal, rel_tol=1e-12)
    assert math.isclose(ganglia, expected_ganglia, rel_tol=1e-12)


def test_formalin_profile_override_updates_defaults() -> None:
    config = _scenario_config(
        formalin_profile={
            "profile_shape": "gaussian_sum",
            "h_base_nm": 60.0,
            "phase1": {"amplitude_nm": 900.0, "center_min": 6.0, "sigma_min": 8.0},
        }
    )

    spec = resolve_formalin_spec(config)
    assert config.schema_version == "1.3.0"
    assert spec.profile_shape == "gaussian_sum"
    assert math.isclose(spec.tissue_profiles["skin"].h_base_nm, 60.0, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(
        spec.tissue_profiles["skin"].gaussian_components[0].amplitude_nm,
        900.0,
        rel_tol=0.0,
        abs_tol=1e-12,
    )
    assert math.isclose(spec.tissue_profiles["skin"].gaussian_components[0].center_h, 0.1, abs_tol=1e-12)
    assert math.isclose(
        spec.tissue_profiles["skin"].gaussian_components[0].sigma_h,
        8.0 / 60.0,
        rel_tol=0.0,
        abs_tol=1e-12,
    )

    late_value = resolve_histamine_nm(100.0, config, "skin")
    assert math.isclose(late_value, 60.0, rel_tol=0.0, abs_tol=1e-9)


def test_formalin_tissue_override_has_priority_over_global_override() -> None:
    config = _scenario_config(
        formalin_profile={
            "profile_shape": "gaussian_sum",
            "h_base_nm": 60.0,
            "phase1": {"amplitude_nm": 900.0, "center_min": 6.0, "sigma_min": 8.0},
        },
        tissue_overrides={
            "spinal_coord": {
                "formalin_profile": {
                    "h_base_nm": 3.0,
                    "phase1": {"amplitude_nm": 12.0, "center_min": 25.0, "sigma_min": 18.0},
                }
            }
        },
    )

    spec = resolve_formalin_spec(config)
    skin_profile = spec.tissue_profiles["skin"]
    spinal_profile = spec.tissue_profiles["spinal_coord"]

    assert math.isclose(skin_profile.h_base_nm, 60.0, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(spinal_profile.h_base_nm, 3.0, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(skin_profile.gaussian_components[0].amplitude_nm, 900.0, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(spinal_profile.gaussian_components[0].amplitude_nm, 12.0, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(spinal_profile.gaussian_components[0].center_h, 25.0 / 60.0, rel_tol=0.0, abs_tol=1e-12)


def test_formalin_profile_override_has_priority_over_driver_shape() -> None:
    config = _scenario_config(
        driver={"driver_type": "scenario", "scenario_id": "formalin", "profile_shape": "gaussian_sum"},
        formalin_profile={
            "profile_shape": "pulse",
            "phase1": {"tau_rise_min": 4.0, "tau_fall_min": 12.0},
            "phase2": {"tau_rise_min": 15.0, "tau_fall_min": 30.0},
        }
    )

    spec = resolve_formalin_spec(config)
    assert spec.profile_shape == "pulse"

    pulse_value = resolve_histamine_nm(10.0 / 60.0, config, "skin")
    gaussian_value = resolve_histamine_nm(10.0 / 60.0, _scenario_config(), "skin")
    assert pulse_value > 50.0
    assert not math.isclose(pulse_value, gaussian_value, rel_tol=1e-9)


def test_hours_from_minutes_converts_yaml_override_units() -> None:
    assert hours_from_minutes(None) is None
    assert math.isclose(hours_from_minutes(15.0) or 0.0, 0.25, rel_tol=0.0, abs_tol=1e-12)


def test_formalin_tissue_level_h_base_matches_reference_plot() -> None:
    spec = get_scenario_spec("formalin")
    assert math.isclose(spec.tissue_profiles["skin"].h_base_nm, 50.0, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(spec.tissue_profiles["spinal_coord"].h_base_nm, 2.0, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(spec.tissue_profiles["ganglia"].h_base_nm, 5.0, rel_tol=0.0, abs_tol=1e-12)


def test_zymosan_uses_gaussian_sum_mvp_profile() -> None:
    config = _scenario_config(
        driver={"driver_type": "scenario", "scenario_id": "zymosan"},
        tissues=["peritoneum", "spinal_coord", "ganglia"],
    )

    spec = histamine_driver.resolve_scenario_spec(config)
    assert spec.profile_shape == "gaussian_sum"
    assert any("MVP approximation" in note for note in spec.notes)

    peak_value = resolve_histamine_nm(210.0 / 60.0, config, "peritoneum")
    assert peak_value > spec.tissue_profiles["peritoneum"].h_base_nm


def test_non_formalin_h_base_can_be_overridden_via_trafficking() -> None:
    config = _scenario_config(
        driver={"driver_type": "scenario", "scenario_id": "zymosan"},
        tissues=["peritoneum", "spinal_coord", "ganglia"],
        trafficking={"h_base_nm": 77.0},
        tissue_overrides={"peritoneum": {"trafficking": {"h_base_nm": 88.0}}},
    )

    spec = histamine_driver.resolve_scenario_spec(config)

    assert math.isclose(spec.tissue_profiles["peritoneum"].h_base_nm, 88.0, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(spec.tissue_profiles["spinal_coord"].h_base_nm, 77.0, rel_tol=0.0, abs_tol=1e-12)


def test_resolve_histamine_nm_clips_negative_registry_output(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _scenario_config()

    def _negative(*_args: object, **_kwargs: object) -> float:
        return -12.0

    monkeypatch.setattr(histamine_driver, "build_scenario_histamine_nm", _negative)
    assert math.isclose(resolve_histamine_nm(0.25, config, "skin"), 0.0, rel_tol=0.0, abs_tol=1e-12)


def test_unknown_scenario_id_rejected_by_schema() -> None:
    with pytest.raises(ValidationError, match="Unsupported scenario_id='unknown'"):
        _scenario_config(driver={"driver_type": "scenario", "scenario_id": "unknown"})


def test_compound_alias_is_canonicalized_by_schema() -> None:
    config = _scenario_config(driver={"driver_type": "scenario", "scenario_id": "compound48_80"})
    assert config.driver.driver_type == "scenario"
    assert config.driver.scenario_id == "compound_48_80"


def test_unsupported_profile_shape_for_scenario_raises_clear_error() -> None:
    config = _scenario_config(driver={"driver_type": "scenario", "scenario_id": "zymosan", "profile_shape": "pulse"})

    with pytest.raises(ValueError, match="Unsupported profile_shape='pulse'"):
        resolve_histamine_nm(0.0, config, "peritoneum")


def test_brain_is_available_as_runtime_proxy_profile() -> None:
    config = _scenario_config()

    brain = resolve_histamine_nm(30.0 / 60.0, config, "brain")
    spinal_coord = resolve_histamine_nm(30.0 / 60.0, config, "spinal_coord")

    assert math.isclose(brain, spinal_coord, rel_tol=0.0, abs_tol=1e-12)
