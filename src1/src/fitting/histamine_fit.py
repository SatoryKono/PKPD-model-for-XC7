from __future__ import annotations

import json
import warnings
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np
import pandas as pd
import scipy
from scipy.optimize import least_squares

from src.fitting.fit_spec import FitSpec, fit_spec_to_dict, scipy_least_squares_loss
from src.utils.atomic_io import write_text_atomic


def _set_nested_value(root: dict[str, Any], dotted_name: str, value: float) -> None:
    keys = dotted_name.split(".")
    cursor: dict[str, Any] = root
    for key in keys[:-1]:
        child = cursor.get(key)
        if child is None:
            child = {}
            cursor[key] = child
        if not isinstance(child, dict):
            raise ValueError(f"Cannot assign parameter '{dotted_name}': '{key}' is not a mapping")
        cursor = child
    cursor[keys[-1]] = float(value)


def _independent_constraints_count(marker_df: pd.DataFrame) -> int:
    t = marker_df["t_h"].to_numpy(dtype=float)
    y = marker_df["histamine_nm"].to_numpy(dtype=float)
    valid = np.isfinite(t) & np.isfinite(y)
    return int(np.unique(t[valid]).size)


def _params_template(default_params: Any) -> dict[str, Any]:
    if is_dataclass(default_params):
        return asdict(default_params)
    if isinstance(default_params, Mapping):
        return dict(default_params)
    raise TypeError("default_params must be a dataclass or mapping")


def fit_histamine_to_markers(
    marker_df: pd.DataFrame,
    model_fn: Callable[[np.ndarray, Mapping[str, Any] | None], np.ndarray | float],
    default_params: Any,
    fit_spec: FitSpec,
    output_json_path: str | Path,
    *,
    source_in_report: str,
    assumptions: list[str] | None = None,
) -> dict[str, Any]:
    """Fit histamine profile parameters to marker points and persist full report JSON."""

    warnings.warn(
        "fit_histamine_to_markers is legacy; prefer fixed parameters (parameter_resolution=fixed_params_only "
        "and histamine_profile / formalin_profile / trafficking overrides in ModelConfig).",
        DeprecationWarning,
        stacklevel=2,
    )

    required_cols = {"t_h", "histamine_nm"}
    if not required_cols.issubset(set(marker_df.columns)):
        raise ValueError("marker_df must contain columns: 't_h', 'histamine_nm'")

    fit_spec.validate()
    fit_spec.validate_identifiability(_independent_constraints_count(marker_df))

    np.random.seed(fit_spec.seed)

    t = marker_df["t_h"].to_numpy(dtype=float)
    y_obs = marker_df["histamine_nm"].to_numpy(dtype=float)
    mask = np.isfinite(t) & np.isfinite(y_obs)
    t = t[mask]
    y_obs = y_obs[mask]

    if t.size == 0:
        raise ValueError("No finite marker rows available for fitting")

    param_template = _params_template(default_params)

    def build_params(x: np.ndarray) -> dict[str, Any]:
        params = json.loads(json.dumps(param_template))
        for name, value in fit_spec.fixed_params.items():
            _set_nested_value(params, name, float(value))
        for name, value in zip(fit_spec.parameter_names, x, strict=True):
            _set_nested_value(params, name, float(value))
        return params

    def residuals(x: np.ndarray) -> np.ndarray:
        params = build_params(x)
        y_pred = np.asarray(model_fn(t, params), dtype=float)
        return y_pred - y_obs

    result = least_squares(
        residuals,
        x0=fit_spec.init_guess,
        bounds=fit_spec.bounds,
        method=fit_spec.method,
        loss=scipy_least_squares_loss(fit_spec.loss_mode),
        ftol=fit_spec.ftol,
        xtol=fit_spec.xtol,
        gtol=fit_spec.gtol,
        max_nfev=fit_spec.max_nfev,
    )

    fitted_params = build_params(result.x)
    final_residuals = residuals(result.x)

    assumptions_out = list(assumptions or [])
    if fit_spec.fixed_params:
        assumptions_out.append(
            "Scenario assumption: fixed_params were frozen during optimization due to missing explicit report parameters."
        )

    report: dict[str, Any] = {
        "fitted_params": fitted_params,
        "fixed_params": dict(fit_spec.fixed_params),
        "bounds": {
            "lower": fit_spec.bounds[0].tolist(),
            "upper": fit_spec.bounds[1].tolist(),
        },
        "init_guess": fit_spec.init_guess.tolist(),
        "objective_definition": fit_spec.objective_definition,
        "loss_mode": fit_spec.loss_mode.value,
        "residuals_summary": {
            "n": int(final_residuals.size),
            "rmse": float(np.sqrt(np.mean(final_residuals**2))),
            "mae": float(np.mean(np.abs(final_residuals))),
            "max_abs": float(np.max(np.abs(final_residuals))),
            "sum_sq": float(np.sum(final_residuals**2)),
        },
        "seed": fit_spec.seed,
        "scipy_version": scipy.__version__,
        "source_in_report": source_in_report,
        "assumptions": assumptions_out,
        "fit_meta": {
            "success": bool(result.success),
            "status": int(result.status),
            "message": str(result.message),
            "nfev": int(result.nfev),
            "active_mask": result.active_mask.tolist(),
            **fit_spec_to_dict(fit_spec),
        },
    }

    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(output_path, json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


__all__ = ["fit_histamine_to_markers"]
