from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from pkpd_xc7.config.loader import load_model_config
from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.simulation.histamine_driver import resolve_histamine_nm
from pkpd_xc7.simulation.scenario_registry import get_scenario_spec, resolve_scenario_spec


def test_cyp_cystitis_registered() -> None:
    spec = get_scenario_spec("cyp_cystitis")
    assert spec.scenario_id == "cyp_cystitis"
    assert "bladder" in spec.tissue_profiles


@pytest.mark.parametrize(
    ("time_h", "expected_min", "expected_max"),
    [
        (0.0, 12.75, 12.77),
        (3.0, 30.06, 30.07),
        (24.0, 10.27, 10.28),
    ],
)
def test_cyp_cystitis_bladder_histamine_nm_deterministic(
    time_h: float,
    expected_min: float,
    expected_max: float,
) -> None:
    cfg_path = Path(__file__).resolve().parents[1] / "examples" / "configs" / "scenarios" / "cyp_cystitis.yaml"
    cfg = load_model_config(cfg_path)
    h = resolve_histamine_nm(time_h, cfg, "bladder")
    assert expected_min <= h <= expected_max


def _minimal_cyp_payload(
    *,
    bladder_phase1_amplitude: float,
    include_cyp_top_profile: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model_id": "cyp_yaml_override_probe",
        "compound": "xc7",
        "species": "rat",
        "traceability": {"source_in_report": "unit_test"},
        "assumptions": ["yaml histamine override probe"],
        "driver": {"driver_type": "scenario", "scenario_id": "cyp_cystitis"},
        "tissues": ["bladder"],
        "time_grid_h": [0.0, 3.0],
        "trafficking": {
            "h_base_nm": 10.0,
            "k_int_max_per_h": 1.25,
            "k_rec_per_h": 0.5,
            "k_synth_per_h": 0.05,
            "ec50_barr_nm": 500.0,
            "ec50_g_nm": 20.0,
            "hill_n": 1.0,
            "constitutive_activity": 0.05,
        },
        "tissue_overrides": {
            "bladder": {
                "formalin_profile": {
                    "profile_shape": "gaussian_sum",
                    "phase1": {
                        "amplitude_nm": bladder_phase1_amplitude,
                        "center_min": 180.0,
                        "sigma_min": 90.0,
                    },
                    "phase2": {
                        "amplitude_nm": 25.0,
                        "center_min": 10080.0,
                        "sigma_min": 2880.0,
                    },
                }
            }
        },
    }
    if include_cyp_top_profile:
        payload["cyp_cystitis_profile"] = {"profile_shape": "gaussian_sum"}
    return payload


def test_cyp_cystitis_tissue_formalin_profile_amplitude_changes_histamine() -> None:
    cfg_low = ModelConfig.model_validate(_minimal_cyp_payload(bladder_phase1_amplitude=10.0, include_cyp_top_profile=True))
    cfg_high = ModelConfig.model_validate(_minimal_cyp_payload(bladder_phase1_amplitude=40.0, include_cyp_top_profile=True))
    h_low = resolve_histamine_nm(3.0, cfg_low, "bladder")
    h_high = resolve_histamine_nm(3.0, cfg_high, "bladder")
    assert h_high > h_low + 1.0


def test_cyp_cystitis_pulse_profile_shape_rejected() -> None:
    payload = _minimal_cyp_payload(bladder_phase1_amplitude=20.0, include_cyp_top_profile=False)
    payload["cyp_cystitis_profile"] = {
        "profile_shape": "pulse",
        "phase1": {
            "amplitude_nm": 10.0,
            "center_min": 0.0,
            "tau_rise_min": 2.0,
            "tau_fall_min": 8.0,
        },
    }
    cfg = ModelConfig.model_validate(payload)
    with pytest.raises(ValueError, match="Unsupported profile_shape"):
        resolve_scenario_spec(cfg)


def test_cyp_example_yaml_histamine_matches_registry_only_merge() -> None:
    """Explicit phase1/2 in YAML match registry → same bladder H(t) as config without tissue formalin_profile."""
    cfg_path = Path(__file__).resolve().parents[1] / "examples" / "configs" / "scenarios" / "cyp_cystitis.yaml"
    h_from_example = resolve_histamine_nm(3.0, load_model_config(cfg_path), "bladder")
    cfg_min = ModelConfig.model_validate(
        {
            "model_id": "registry_merge",
            "compound": "xc7",
            "species": "rat",
            "traceability": {"source_in_report": "t"},
            "assumptions": ["registry-only histamine phases"],
            "driver": {"driver_type": "scenario", "scenario_id": "cyp_cystitis"},
            "tissues": ["bladder"],
            "time_grid_h": [0.0, 3.0],
            "trafficking": {"h_base_nm": 10.0},
            "cyp_cystitis_profile": {"profile_shape": "gaussian_sum"},
        }
    )
    h_registry_only = resolve_histamine_nm(3.0, cfg_min, "bladder")
    assert h_from_example == pytest.approx(h_registry_only)
