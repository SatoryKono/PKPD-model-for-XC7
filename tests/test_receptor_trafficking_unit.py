from __future__ import annotations

import numpy as np
import pytest

from src.config.schemas import ModelConfig
from src.models.receptor_trafficking import (
    DEFAULT_PARAMS,
    build_model_params,
    histamine_input_profile,
    k_int_eff,
    receptor_trafficking_rhs,
    steady_state_ic,
)


def test_k_int_eff_zero_histamine_is_zero() -> None:
    assert k_int_eff(0.0) == 0.0


def test_k_int_eff_approaches_k_int_max_for_large_histamine() -> None:
    value = k_int_eff(1e12)
    assert np.isclose(value, DEFAULT_PARAMS.k_int_max, rtol=0.0, atol=1e-6)


def test_steady_state_ic_is_bounded_and_mass_conserved() -> None:
    r_surf0, r_int0 = steady_state_ic(50.0)
    assert 0.0 <= r_surf0 <= 1.0
    assert 0.0 <= r_int0 <= 1.0
    assert abs((r_surf0 + r_int0) - 1.0) < 1e-6


def test_rhs_at_steady_state_returns_zero_vector() -> None:
    h_base_nm = 50.0
    y0 = steady_state_ic(h_base_nm)
    dydt = receptor_trafficking_rhs(t_h=0.0, y=y0, histamine_nm=h_base_nm)
    assert np.allclose(dydt, np.zeros(2), atol=1e-10)


def test_rhs_clipping_mode_is_explicit_and_logged() -> None:
    assumptions: list[str] = []
    dydt = receptor_trafficking_rhs(
        t_h=0.0,
        y=(1.2, -0.2),
        histamine_nm=10.0,
        clip_state_explicit=True,
        assumptions=assumptions,
    )
    assert dydt.shape == (2,)
    assert any("Scenario assumption" in text for text in assumptions)


def test_build_model_params_rejects_unsupported_tissue_units() -> None:
    cfg = ModelConfig.model_validate(
        {
            "model_id": "unit_model",
            "compound": "histamine",
            "loss_mode": "mse",
            "assumptions": ["unit_test_assumption"],
            "traceability": {"source_in_report": "Unit test source"},
            "time_grid": [0.0, 1.0],
            "time_unit": "h",
            "initial_concentration": 10.0,
            "concentration_unit": "nM",
            "kinetics": {"k_abs": 0.4, "k_elim": 0.1, "rate_unit": "1/h"},
            "tissues": [
                {
                    "name": "plasma",
                    "volume": 1.0,
                    "volume_unit": "mL",
                    "partition_coeff": 1.0,
                }
            ],
            "plots": [],
        }
    )

    with pytest.raises(ValueError, match="volume_unit='L'"):
        build_model_params(cfg)


def test_build_model_params_uses_config_trafficking_when_set() -> None:
    cfg = ModelConfig.model_validate(
        {
            "model_id": "unit_model",
            "compound": "histamine",
            "loss_mode": "mse",
            "assumptions": ["unit_test_assumption"],
            "traceability": {"source_in_report": "Unit test source"},
            "time_grid": [0.0, 1.0],
            "time_unit": "h",
            "initial_concentration": 100.0,
            "concentration_unit": "nM",
            "kinetics": {"k_abs": 1.0, "k_elim": 0.2, "rate_unit": "1/h"},
            "tissues": [
                {"name": "plasma", "volume": 1.0, "volume_unit": "L", "partition_coeff": 1.0}
            ],
            "plots": [],
            "trafficking": {
                "k_int_max": 3.0,
                "k_rec": 0.5,
                "k_synth": 0.05,
                "ec50_barr_nm": 1500.0,
                "hill_n": 1.0,
                "ec50_g_nm": 50.0,
            },
        }
    )
    mp = build_model_params(cfg)
    assert mp.trafficking.k_int_max == 3.0
    assert mp.trafficking.k_rec == 0.5
    assert mp.trafficking.ec50_g_nm == 50.0


def test_histamine_input_profile_responds_to_kinetics() -> None:
    cfg = ModelConfig.model_validate(
        {
            "model_id": "unit_model",
            "compound": "histamine",
            "loss_mode": "mse",
            "assumptions": ["unit_test_assumption"],
            "traceability": {"source_in_report": "Unit test source"},
            "time_grid": [0.0, 1.0],
            "time_unit": "h",
            "initial_concentration": 100.0,
            "concentration_unit": "nM",
            "kinetics": {"k_abs": 1.0, "k_elim": 0.2, "rate_unit": "1/h"},
            "tissues": [
                {"name": "plasma", "volume": 1.0, "volume_unit": "L", "partition_coeff": 1.0}
            ],
            "plots": [],
        }
    )
    params = build_model_params(cfg)
    at_1h = histamine_input_profile(1.0, params)
    assert at_1h > 0.0


def test_build_model_params_uses_explicit_capsaicin_histamine_profile() -> None:
    cfg = ModelConfig.model_validate(
        {
            "model_id": "capsaicin_profile_model",
            "compound": "capsaicin",
            "loss_mode": "mse",
            "assumptions": ["unit_test_assumption"],
            "traceability": {"source_in_report": "Unit test source"},
            "time_grid": [0.0, 0.25, 0.5, 1.0],
            "time_unit": "h",
            "tissues": [
                {"name": "plasma", "volume": 1.0, "volume_unit": "L", "partition_coeff": 1.0}
            ],
            "plots": [],
            "histamine_profile": {
                "profile_id": "capsaicin",
                "tissue": "skin",
            },
        }
    )

    mp = build_model_params(cfg)
    assert mp.histamine_source == "capsaicin"
    assert mp.k_abs_per_h is None
    assert mp.k_elim_per_h is None
    assert np.isclose(histamine_input_profile(0.0, mp), 50.0)
    assert histamine_input_profile(0.25, mp) > 50.0


def test_build_model_params_applies_histamine_profile_phase_override() -> None:
    cfg = ModelConfig.model_validate(
        {
            "model_id": "capsaicin_override_model",
            "compound": "capsaicin",
            "loss_mode": "mse",
            "assumptions": ["unit_test_assumption"],
            "traceability": {"source_in_report": "Unit test source"},
            "time_grid": [0.0, 1.0],
            "time_unit": "h",
            "tissues": [
                {"name": "plasma", "volume": 1.0, "volume_unit": "L", "partition_coeff": 1.0}
            ],
            "plots": [],
            "histamine_profile": {
                "profile_id": "capsaicin",
                "tissue": "skin",
                "phase1": {"amplitude_nm": 200.0},
            },
        }
    )

    mp = build_model_params(cfg)
    assert mp.histamine_profile is not None
    assert np.isclose(mp.histamine_profile.phase1.amplitude_nm, 200.0)


def test_build_model_params_uses_formalin_histamine_profile_without_legacy_pk_fields() -> None:
    cfg = ModelConfig.model_validate(
        {
            "model_id": "formalin_profile_model",
            "compound": "histamine",
            "loss_mode": "mse",
            "assumptions": ["unit_test_assumption"],
            "traceability": {"source_in_report": "Unit test source"},
            "time_grid": [0.0, 0.25, 0.5, 1.0, 2.0, 4.0],
            "time_unit": "h",
            "tissues": [
                {"name": "skin", "volume": 1.0, "volume_unit": "L", "partition_coeff": 1.0}
            ],
            "plots": [],
            "histamine_profile": {
                "profile_id": "formalin",
                "tissue": "skin",
            },
        }
    )

    mp = build_model_params(cfg)
    assert mp.histamine_source == "formalin"
    assert mp.histamine_profile is not None
    assert np.isclose(mp.histamine_profile.h_base_nm, 50.0)
    assert mp.k_abs_per_h is None
    assert mp.k_elim_per_h is None
    assert np.isclose(histamine_input_profile(0.0, mp), 50.0)
    assert histamine_input_profile(0.25, mp) > 50.0
