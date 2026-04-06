from __future__ import annotations

from typing import NamedTuple, Sequence

import numpy as np

MODEL_RUNTIME_ASSUMPTION = "k_deg implicitly equals k_synth per ODE mass-balance invariant"


class TraffickingCoreParams(NamedTuple):
    """Lightweight immutable parameter container for the ODE hot path."""

    k_int_max_per_h: float
    k_rec_per_h: float
    k_synth_per_h: float
    ec50_barr_nm: float
    ec50_internalization_nm: float
    hill_n: float
    ec50_g_nm: float
    constitutive_activity: float = 0.0


def internalization_drive(histamine_nm: float, params: TraffickingCoreParams) -> float:
    """Return internalization driver in [0, 1]."""
    if histamine_nm <= 0.0:
        return 0.0
    ec50_nm = params.ec50_internalization_nm
    numerator = histamine_nm**params.hill_n
    denominator = (ec50_nm**params.hill_n) + numerator
    return numerator / denominator


def k_int_eff(histamine_nm: float, params: TraffickingCoreParams) -> float:
    """Return ligand-driven internalization rate in 1/h."""
    if histamine_nm <= 0.0:
        return 0.0
    return params.k_int_max_per_h * internalization_drive(histamine_nm, params)


def analytic_steady_state_fractions(k_eff_per_h: float, k_rec_per_h: float) -> tuple[float, float]:
    """Return analytic steady state on the invariant manifold R_surf + R_int = 1."""
    if k_eff_per_h < 0.0:
        raise ValueError("k_eff_per_h must be non-negative.")
    if k_rec_per_h < 0.0:
        raise ValueError("k_rec_per_h must be non-negative.")
    if k_eff_per_h == 0.0 and k_rec_per_h == 0.0:
        return (1.0, 0.0)

    denom = k_eff_per_h + k_rec_per_h
    return (k_rec_per_h / denom, k_eff_per_h / denom)


def steady_state_ic(histamine_nm: float, params: TraffickingCoreParams) -> tuple[float, float]:
    """Return analytic initial conditions at constant baseline histamine."""
    return analytic_steady_state_fractions(
        k_eff_per_h=k_int_eff(histamine_nm, params),
        k_rec_per_h=params.k_rec_per_h,
    )


def receptor_pool_balance_rhs_sum(y: Sequence[float], params: TraffickingCoreParams) -> float:
    """Return d(R_surf + R_int)/dt under the model's mass-balance assumption."""
    r_surf = max(float(y[0]), 0.0)
    r_int = max(float(y[1]), 0.0)
    return params.k_synth_per_h * (1.0 - r_surf - r_int)


def receptor_trafficking_rhs(
    t_h: float,
    y: Sequence[float],
    histamine_nm: float,
    params: TraffickingCoreParams,
    *,
    clip_state_explicit: bool = False,
    assumptions: list[str] | None = None,
) -> np.ndarray:
    """
    RHS for receptor trafficking with k_deg == k_synth mass-balance assumption.

    Negative state values are clipped before evaluating linear terms so adaptive
    solvers cannot propagate unphysical receptor fractions.
    """
    r_surf_raw = float(y[0])
    r_int_raw = float(y[1])

    r_surf = max(r_surf_raw, 0.0)
    r_int = max(r_int_raw, 0.0)

    if clip_state_explicit and assumptions is not None and (r_surf_raw < 0.0 or r_int_raw < 0.0):
        msg = f"Scenario assumption: Negative receptor state clipped at t={t_h:.3f}"
        if msg not in assumptions:
            assumptions.append(msg)

    k_eff = k_int_eff(histamine_nm, params)
    pool_repair = params.k_synth_per_h * (1.0 - r_surf - r_int)

    d_r_surf = pool_repair - (k_eff * r_surf) + (params.k_rec_per_h * r_int)
    d_r_int = (k_eff * r_surf) - (params.k_rec_per_h * r_int)
    return np.array([d_r_surf, d_r_int], dtype=float)