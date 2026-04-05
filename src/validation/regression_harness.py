"""Helpers to compare pipeline marker tables against external reference CSVs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import api
from src.config.schemas import (
    ConcentrationUnit,
    KineticsConfig,
    LossMode,
    ModelConfig,
    ParameterResolutionMode,
    RateUnit,
    TissueConfig,
    Traceability,
    TimeUnit,
    effective_g_signal_ec50_nm,
)
from src.models.receptor_trafficking import TraffickingParams, build_model_params


def g_signal_proxy(r_surf: np.ndarray, histamine_nm: np.ndarray, ec50_nm: float) -> np.ndarray:
    """G column consistent with plot proxy: R_surf * H / (EC50 + H)."""
    h = np.asarray(histamine_nm, dtype=float)
    rs = np.asarray(r_surf, dtype=float)
    den = float(ec50_nm) + h
    return (rs * h) / den


def loss_metric(r_surf: np.ndarray, r_int: np.ndarray) -> np.ndarray:
    """Implicit third-pool fraction (non-negative) for report-style loss column."""
    return np.clip(1.0 - np.asarray(r_surf, dtype=float) - np.asarray(r_int, dtype=float), 0.0, 1.0)


def regression_model_config(
    model_key: str,
    time_grid: list[float],
    *,
    trafficking: TraffickingParams | None = None,
) -> ModelConfig:
    """Minimal canonical config for regression runs (fixed PK across models unless extended)."""

    from src.config.schemas import TraffickingConfig

    t_cfg: TraffickingConfig | None = None
    if trafficking is not None:
        t_cfg = TraffickingConfig(
            k_int_max=trafficking.k_int_max,
            k_rec=trafficking.k_rec,
            k_synth=trafficking.k_synth,
            ec50_barr_nm=trafficking.ec50_barr_nm,
            hill_n=trafficking.hill_n,
            ec50_g_nm=trafficking.ec50_g_nm,
        )

    return ModelConfig(
        model_id=model_key,
        compound="histamine",
        loss_mode=LossMode.MSE,
        parameter_resolution=ParameterResolutionMode.FIXED_PARAMS_ONLY,
        assumptions=[f"Regression harness: synthetic PK/PD for model_id={model_key!r}"],
        traceability=Traceability(
            source_in_report="regression_harness",
            source_reference="tests/test_regression_marker_tables.py",
            source_version="1",
        ),
        time_grid=time_grid,
        time_unit=TimeUnit.H,
        initial_concentration=100.0,
        concentration_unit=ConcentrationUnit.NM,
        kinetics=KineticsConfig(k_abs=1.2, k_elim=0.3, rate_unit=RateUnit.PER_H),
        tissues=[
            TissueConfig(name="plasma", volume=1.0, volume_unit="L", partition_coeff=1.0),
        ],
        plots=[],
        trafficking=t_cfg,
    )


def marker_table_from_simulation_result(
    expected: pd.DataFrame,
    *,
    ec50_g_nm: float | None = None,
    model_key: str = "regression",
) -> pd.DataFrame:
    """Build a marker table whose columns match ``expected`` using last simulation row order."""

    time_grid = expected["time_h"].astype(float).tolist()
    cfg = regression_model_config(model_key, time_grid)
    result = api.run_simulation(cfg)
    tp = build_model_params(cfg).trafficking
    ec50_eff = float(ec50_g_nm) if ec50_g_nm is not None else effective_g_signal_ec50_nm(cfg, tp.ec50_g_nm)
    mp = result.marker_points.copy()
    h = mp["histamine_nm"].to_numpy(dtype=float)
    rs = mp["R_surf"].to_numpy(dtype=float)
    ri = mp["R_int"].to_numpy(dtype=float)

    out = pd.DataFrame({"time_h": mp["time_h"].to_numpy(dtype=float)})
    for col in expected.columns:
        if col == "time_h":
            continue
        if col == "H":
            out["H"] = h
        elif col == "R_surf":
            out["R_surf"] = rs
        elif col == "R_int":
            out["R_int"] = ri
        elif col == "G":
            out["G"] = g_signal_proxy(rs, h, ec50_g_nm)
        elif col == "loss":
            out["loss"] = loss_metric(rs, ri)
        else:
            raise ValueError(f"Unsupported reference column for pipeline mapping: {col!r}")

    return out[list(expected.columns)]


def pipeline_marker_table_vs_reference(expected: pd.DataFrame, *, model_key: str) -> pd.DataFrame:
    """Run pipeline on ``expected`` time grid; return table with same columns as reference."""

    return marker_table_from_simulation_result(expected, ec50_g_nm=None, model_key=model_key)
