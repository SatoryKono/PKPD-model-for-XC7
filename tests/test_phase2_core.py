from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.io.layout import (
    ANTAGONIST_CONCENTRATION_COL,
    SIMULATION_SCHEMA_VERSION,
    TIMESERIES_COLUMN_ORDER,
    enforce_timeseries_layout,
)
from pkpd_xc7.models.h3_signaling import beta_arr_fraction, g_signal_percent, g_signaling_fraction
from pkpd_xc7.models.receptor_trafficking import (
    MODEL_RUNTIME_ASSUMPTION,
    analytic_steady_state_fractions,
    internalization_drive,
    k_int_eff,
    receptor_pool_balance_rhs_sum,
    receptor_trafficking_rhs,
    steady_state_ic,
)
from pkpd_xc7.simulation.model_mapping import (
    model_config_to_trafficking_core,
    resolve_trafficking_config,
    runtime_assumptions,
)
from pkpd_xc7.simulation.postprocessing import add_g_signal_columns
from pkpd_xc7.simulation.runner import (
    RECEPTOR_INVARIANT_EPS,
    _validate_tissue_receptor_invariants,
    run_experiment,
)


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "model_id": "phase2",
        "compound": "xc7",
        "traceability": {"source_in_report": "table-1"},
        "assumptions": ["baseline assumption"],
        "driver": {"driver_type": "scenario", "scenario_id": "formalin"},
        "tissues": ["skin"],
        "time_grid_h": [0.0, 0.5, 1.0],
    }
    payload.update(overrides)
    return payload


def test_model_config_to_trafficking_core_uses_schema_values() -> None:
    cfg = ModelConfig.model_validate(
        _payload(
            trafficking={
                "k_int_max_per_h": 4.0,
                "k_rec_per_h": 0.8,
                "k_synth_per_h": 0.1,
                "ec50_barr_nm": 1200.0,
                "kb_arr_nm": 300.0,
                "hill_n": 1.2,
                "ec50_g_nm": 40.0,
                "kb_g_nm": 25.0,
                "constitutive_activity": 0.15,
            }
        )
    )

    params = model_config_to_trafficking_core(cfg)
    assert params.k_int_max_per_h == pytest.approx(4.0)
    assert params.k_rec_per_h == pytest.approx(0.8)
    assert params.ec50_internalization_nm == pytest.approx(1200.0)
    assert params.kb_arr_nm == pytest.approx(300.0)
    assert params.kb_g_nm == pytest.approx(25.0)
    assert params.constitutive_activity == pytest.approx(0.15)


def test_tissue_specific_trafficking_override_is_resolved_per_tissue() -> None:
    cfg = ModelConfig.model_validate(
        _payload(
            tissues=["skin", "spinal_coord"],
            tissue_overrides={
                "spinal_coord": {
                    "trafficking": {
                        "k_rec_per_h": 0.9,
                        "ec50_g_nm": 25.0,
                        "constitutive_activity": 0.2,
                    }
                }
            },
        )
    )

    skin = resolve_trafficking_config(cfg, "skin")
    spinal = resolve_trafficking_config(cfg, "spinal_coord")
    spinal_params = model_config_to_trafficking_core(cfg, tissue="spinal_coord")

    assert skin.ec50_g_nm == pytest.approx(cfg.trafficking.ec50_g_nm)
    assert spinal.k_rec_per_h == pytest.approx(0.9)
    assert spinal.ec50_g_nm == pytest.approx(25.0)
    assert spinal_params.constitutive_activity == pytest.approx(0.2)


def test_runtime_assumptions_append_mass_balance_once() -> None:
    cfg = ModelConfig.model_validate(_payload(assumptions=["baseline assumption", MODEL_RUNTIME_ASSUMPTION]))
    merged = runtime_assumptions(cfg)
    assert merged.count(MODEL_RUNTIME_ASSUMPTION) == 1
    assert merged[0] == "baseline assumption"


def test_k_int_eff_zero_and_large_histamine_behaviour() -> None:
    params = model_config_to_trafficking_core(ModelConfig.model_validate(_payload()))
    assert k_int_eff(0.0, params) == pytest.approx(0.0)
    assert np.isclose(k_int_eff(1e12, params), params.k_int_max_per_h, rtol=0.0, atol=1e-6)


def test_analytic_steady_state_matches_rhs_equilibrium() -> None:
    params = model_config_to_trafficking_core(ModelConfig.model_validate(_payload()))
    h_base_nm = 50.0
    xc7_nm = 25.0
    y0 = steady_state_ic(h_base_nm, params, xc7_nm=xc7_nm)
    dydt = receptor_trafficking_rhs(0.0, y0, h_base_nm, params, xc7_nm=xc7_nm)

    assert 0.0 <= y0[0] <= 1.0
    assert 0.0 <= y0[1] <= 1.0
    assert math.isclose(sum(y0), 1.0, rel_tol=0.0, abs_tol=1e-12)
    assert np.allclose(dydt, np.zeros(2), atol=1e-10)


def test_analytic_steady_state_fractions_sum_to_one() -> None:
    r_surf, r_int = analytic_steady_state_fractions(k_eff_per_h=0.35, k_rec_per_h=0.5)
    assert r_surf == pytest.approx(0.5 / 0.85)
    assert r_int == pytest.approx(0.35 / 0.85)
    assert r_surf + r_int == pytest.approx(1.0)


def test_rhs_uses_clipped_state_for_mass_balance_invariant() -> None:
    params = model_config_to_trafficking_core(ModelConfig.model_validate(_payload()))
    y = (1.2, -0.2)
    dydt = receptor_trafficking_rhs(0.0, y, histamine_nm=10.0, params=params)

    assert dydt.shape == (2,)
    assert float(dydt.sum()) == pytest.approx(receptor_pool_balance_rhs_sum(y, params))


def test_validate_tissue_receptor_invariants_accepts_sum_at_eps_boundary() -> None:
    time_grid = np.array([0.0, 0.5], dtype=float)
    y_sol = np.array(
        [
            [1.0, 0.4],
            [0.0, 0.6 + RECEPTOR_INVARIANT_EPS],
        ],
        dtype=float,
    )

    _validate_tissue_receptor_invariants(time_grid, y_sol, tissue="skin")


def test_validate_tissue_receptor_invariants_rejects_negative_r_surf() -> None:
    time_grid = np.array([0.0, 0.5], dtype=float)
    y_sol = np.array(
        [
            [1.0, -0.01],
            [0.0, 0.8],
        ],
        dtype=float,
    )

    with pytest.raises(
        ValueError,
        match=r"tissue 'skin'.*time_h=0\.5.*R_surf=-0\.01.*must be >= 0",
    ):
        _validate_tissue_receptor_invariants(time_grid, y_sol, tissue="skin")


def test_validate_tissue_receptor_invariants_rejects_sum_above_eps() -> None:
    time_grid = np.array([0.0, 0.5], dtype=float)
    y_sol = np.array(
        [
            [1.0, 0.4],
            [0.0, 0.6 + RECEPTOR_INVARIANT_EPS + 1e-7],
        ],
        dtype=float,
    )

    with pytest.raises(
        ValueError,
        match=r"tissue 'skin'.*time_h=0\.5.*R_surf \+ R_int=.*must be <= 1 \+ eps",
    ):
        _validate_tissue_receptor_invariants(time_grid, y_sol, tissue="skin")


def test_g_signaling_fraction_and_percent_are_bounded() -> None:
    cfg = ModelConfig.model_validate(_payload(trafficking={"constitutive_activity": 0.1}))
    params = model_config_to_trafficking_core(cfg)

    assert g_signaling_fraction(-1.0, 1.0, params) == pytest.approx(0.1)
    assert g_signaling_fraction(50.0, 0.8, params) <= 1.0
    assert beta_arr_fraction(50.0, params, xc7_nm=25.0) <= 1.0
    assert internalization_drive(50.0, params) <= 1.0
    assert g_signal_percent(0.42) == pytest.approx(42.0)


def test_add_g_signal_columns_adds_report_space_columns_once() -> None:
    cfg = ModelConfig.model_validate(_payload())
    params = model_config_to_trafficking_core(cfg)
    df = pd.DataFrame(
        {
            "histamine_nm": [0.0, 50.0],
            "R_surf": [1.0, 0.5],
            ANTAGONIST_CONCENTRATION_COL: [0.0, 100.0],
        }
    )

    result = add_g_signal_columns(df, params)

    g_signal = np.asarray(result["G_signal"].to_numpy(dtype=float), dtype=float)
    g_signal_pct = np.asarray(result["G_signal_pct"].to_numpy(dtype=float), dtype=float)
    g_ligand_pct = np.asarray(result["G_signal_ligand_pct"].to_numpy(dtype=float), dtype=float)
    g_constitutive_pct = np.asarray(result["G_signal_constitutive_pct"].to_numpy(dtype=float), dtype=float)
    beta_arr_pct = np.asarray(result["beta_arr_signal_pct"].to_numpy(dtype=float), dtype=float)
    np.testing.assert_allclose(g_signal_pct, g_signal * 100.0)
    assert result["internalization_drive"].between(0.0, 1.0).all()
    assert result["k_int_eff_per_h"].between(0.0, params.k_int_max_per_h).all()
    assert np.all((g_ligand_pct >= 0.0) & (g_ligand_pct <= 100.0))
    assert np.all((g_constitutive_pct >= 0.0) & (g_constitutive_pct <= 100.0))
    assert np.all((beta_arr_pct >= 0.0) & (beta_arr_pct <= 100.0))
    assert result.loc[1, "internalization_drive"] < internalization_drive(50.0, params)


def test_run_experiment_dataframe_keeps_g_signal_percent_in_sync() -> None:
    cfg = ModelConfig.model_validate(_payload(time_grid_h=[0.0, 0.25, 0.5, 1.0]))
    result = run_experiment(cfg)

    g_signal = np.asarray(result["G_signal"].to_numpy(dtype=float), dtype=float)
    g_signal_pct = np.asarray(result["G_signal_pct"].to_numpy(dtype=float), dtype=float)

    assert result.columns.tolist() == TIMESERIES_COLUMN_ORDER
    np.testing.assert_allclose(g_signal_pct, g_signal * 100.0)
    assert np.all((g_signal >= 0.0) & (g_signal <= 1.0))
    assert np.all((g_signal_pct >= 0.0) & (g_signal_pct <= 100.0))


def test_run_experiment_uses_tissue_specific_params_per_branch() -> None:
    cfg = ModelConfig.model_validate(
        {
            "model_id": "phase2_tissue_specific",
            "compound": "xc7",
            "traceability": {"source_in_report": "table-1"},
            "assumptions": ["tissue-specific run"],
            "driver": {"driver_type": "pk", "k_abs_per_h": 1.0, "k_elim_per_h": 0.5},
            "tissues": ["skin", "spinal_coord"],
            "time_grid_h": [0.0, 0.5, 1.0],
            "trafficking": {
                "k_rec_per_h": 0.5,
                "ec50_g_nm": 50.0,
                "constitutive_activity": 0.05,
                "h_base_nm": 50.0,
            },
            "tissue_overrides": {
                "spinal_coord": {
                    "trafficking": {
                        "k_rec_per_h": 0.9,
                        "ec50_g_nm": 10.0,
                        "constitutive_activity": 0.2,
                        "h_base_nm": 2.0,
                    }
                }
            },
        }
    )

    result = run_experiment(cfg)
    at_t0 = result.loc[np.isclose(result["time_h"].to_numpy(dtype=float), 0.0)].set_index("tissue")

    assert at_t0.loc["skin", "R_surf"] != pytest.approx(at_t0.loc["spinal_coord", "R_surf"])
    assert at_t0.loc["skin", "G_signal"] != pytest.approx(at_t0.loc["spinal_coord", "G_signal"])


def test_enforce_timeseries_layout_reorders_columns_deterministically() -> None:
    df = pd.DataFrame(
        {
            "driver_id": ["formalin"],
            "k_int_eff_per_h": [0.3],
            "internalization_drive": [0.1],
            "beta_arr_signal_pct": [0.4],
            "beta_arr_signal": [0.004],
            "G_signal_constitutive_pct": [5.0],
            "G_signal_constitutive": [0.05],
            "G_signal_ligand_pct": [15.0],
            "G_signal_ligand": [0.15],
            "R_int": [0.1],
            "G_signal": [0.2],
            "time_h": [0.0],
            "tissue": ["skin"],
            "driver_type": ["scenario"],
            "R_surf": [0.9],
            "histamine_nm": [50.0],
            "G_signal_pct": [20.0],
        }
    )

    result = enforce_timeseries_layout(df)

    assert result.columns.tolist() == TIMESERIES_COLUMN_ORDER
    assert SIMULATION_SCHEMA_VERSION == "2.1.0"


def test_antagonist_pk_reduces_internalization_and_uses_t0_concentration(tmp_path: Path) -> None:
    source = tmp_path / "pk_source.xlsx"
    pd.DataFrame(
        [
            {"species": "mice", "regimen": "single", "organ": "skin", "dose": 90.0, "time_h": 0.0, "C_nM": 120.0},
            {"species": "mice", "regimen": "single", "organ": "skin", "dose": 90.0, "time_h": 1.0, "C_nM": 120.0},
        ]
    ).to_excel(source, index=False)
    payload = _payload(
        species="mouse",
        time_grid_h=[0.0, 1.0],
        trafficking={"h_base_nm": 50.0, "kb_arr_nm": 60.0},
        antagonist_pk={
            "enabled": True,
            "source_xlsx": str(source),
            "dose_mg_per_kg": 90.0,
            "regimen": "single",
            "concentration_column": "C_nM",
            "tissue_map": {"skin": "skin"},
        },
    )
    cfg_with_xc7 = ModelConfig.model_validate(payload)
    cfg_without_xc7 = ModelConfig.model_validate(_payload(species="mouse", time_grid_h=[0.0, 1.0], trafficking={"h_base_nm": 50.0}))

    with_xc7 = run_experiment(cfg_with_xc7)
    without_xc7 = run_experiment(cfg_without_xc7)

    params = model_config_to_trafficking_core(cfg_with_xc7)
    at_t0 = with_xc7.loc[np.isclose(with_xc7["time_h"].to_numpy(dtype=float), 0.0)].iloc[0]
    control_t0 = without_xc7.loc[np.isclose(without_xc7["time_h"].to_numpy(dtype=float), 0.0)].iloc[0]
    expected_y0 = steady_state_ic(float(at_t0["histamine_nm"]), params, xc7_nm=float(at_t0[ANTAGONIST_CONCENTRATION_COL]))

    assert at_t0["R_surf"] == pytest.approx(expected_y0[0])
    assert at_t0["R_int"] == pytest.approx(expected_y0[1])
    assert at_t0["R_int"] < control_t0["R_int"]
