"""Helpers to compare pipeline marker tables against external reference CSVs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import api
from src.config.schemas import (
    ConcentrationUnit,
    HistamineProfileConfig,
    HistamineProfileId,
    HistamineTissue,
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
from src.histamine_profiles import Tissue
from src.models.g_signaling import default_g_signal_params_for_tissue, g_signal_percent
from src.models.receptor_trafficking import TraffickingParams, build_model_params


def g_signal_proxy(
    r_surf: np.ndarray,
    histamine_nm: np.ndarray,
    *,
    ec50_nm: float,
    hill_n: float = 1.0,
) -> np.ndarray:
    """G column consistent with Model 3 G-signaling equation."""
    params = default_g_signal_params_for_tissue(
        Tissue.SKIN,
        ec50_g_nm=ec50_nm,
        hill_n=hill_n,
    )
    return np.asarray(g_signal_percent(histamine_nm, r_surf, params), dtype=float)


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

    histamine_profile: HistamineProfileConfig | None = None
    initial_concentration: float | None = 100.0
    concentration_unit: ConcentrationUnit | None = ConcentrationUnit.NM
    kinetics: KineticsConfig | None = KineticsConfig(k_abs=1.2, k_elim=0.3, rate_unit=RateUnit.PER_H)
    if model_key == "formalin":
        histamine_profile = HistamineProfileConfig(
            profile_id=HistamineProfileId.FORMALIN,
            tissue=HistamineTissue.SKIN,
        )
        initial_concentration = None
        concentration_unit = None
        kinetics = None

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
        initial_concentration=initial_concentration,
        concentration_unit=concentration_unit,
        kinetics=kinetics,
        tissues=[
            TissueConfig(name="plasma", volume=1.0, volume_unit="L", partition_coeff=1.0),
        ],
        plots=[],
        histamine_profile=histamine_profile,
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
            out["G"] = g_signal_proxy(
                rs,
                h,
                ec50_nm=ec50_eff,
                hill_n=tp.hill_n,
            )
        elif col == "loss":
            out["loss"] = loss_metric(rs, ri)
        else:
            raise ValueError(f"Unsupported reference column for pipeline mapping: {col!r}")

    return out[list(expected.columns)]


def pipeline_marker_table_vs_reference(expected: pd.DataFrame, *, model_key: str) -> pd.DataFrame:
    """Run pipeline on ``expected`` time grid; return table with same columns as reference."""

    return marker_table_from_simulation_result(expected, ec50_g_nm=None, model_key=model_key)
