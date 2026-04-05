from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class TraffickingParams:
    """H3R trafficking parameters in canonical units (nM, 1/h)."""

    k_int_max: float = 2.5
    k_rec: float = 0.50
    k_synth: float = 0.05
    k_deg: float = 0.05
    ec50_barr_nm: float = 1500.0
    hill_n: float = 1.0
    ec50_g_nm: float = 50.0


DEFAULT_PARAMS = TraffickingParams()


def _register_assumption(assumptions: list[str] | None, message: str) -> None:
    if assumptions is None:
        return
    if message not in assumptions:
        assumptions.append(message)


def k_int_eff(histamine_nm: float, params: TraffickingParams = DEFAULT_PARAMS) -> float:
    """Effective internalization rate as β-arrestin-like Hill response."""

    if histamine_nm < 0:
        raise ValueError("histamine_nm must be >= 0")

    numerator = histamine_nm**params.hill_n
    denominator = params.ec50_barr_nm**params.hill_n + numerator
    if denominator <= 0:
        raise ValueError("Invalid parameters: Hill denominator must be positive")
    return params.k_int_max * (numerator / denominator)


def receptor_trafficking_rhs(
    t_h: float,
    y: Sequence[float],
    histamine_nm: float,
    params: TraffickingParams = DEFAULT_PARAMS,
    *,
    clip_state_explicit: bool = False,
    assumptions: list[str] | None = None,
) -> np.ndarray:
    """RHS for (R_surf, R_int) dynamics.

    The optional clipping mode is an explicit scenario assumption and must be
    logged in ``assumptions`` by the caller.
    """

    del t_h  # autonomous system, kept for ODE solver signature compatibility

    if len(y) != 2:
        raise ValueError("State y must contain exactly two values: (R_surf, R_int)")

    r_surf, r_int = float(y[0]), float(y[1])

    if clip_state_explicit:
        _register_assumption(
            assumptions,
            "Scenario assumption: receptor states are clipped to [0, 1] in RHS before derivative evaluation.",
        )
        r_surf = float(np.clip(r_surf, 0.0, 1.0))
        r_int = float(np.clip(r_int, 0.0, 1.0))
    else:
        if not (0.0 <= r_surf <= 1.0 and 0.0 <= r_int <= 1.0):
            raise ValueError("R_surf and R_int must be in [0, 1] unless clip_state_explicit=True")

    k_int = k_int_eff(histamine_nm=histamine_nm, params=params)

    d_r_surf = -k_int * r_surf + params.k_rec * r_int + params.k_synth * (1.0 - r_surf - r_int)
    d_r_int = k_int * r_surf - params.k_rec * r_int - params.k_deg * r_int

    return np.array([d_r_surf, d_r_int], dtype=float)


def steady_state_ic(
    h_base_nm: float,
    params: TraffickingParams = DEFAULT_PARAMS,
) -> tuple[float, float]:
    """Return stationary initial conditions (R_surf0, R_int0) at baseline histamine."""

    if params.k_rec <= 0:
        raise ValueError("k_rec must be > 0 to compute steady-state IC")

    k_int = k_int_eff(histamine_nm=h_base_nm, params=params)
    denom = params.k_deg * k_int + params.k_deg * params.k_synth + k_int * params.k_synth + params.k_rec * params.k_synth
    if denom <= 0:
        raise ValueError("Invalid parameters: denom must be positive")

    r_surf0 = params.k_synth * (params.k_deg + params.k_rec) / denom
    r_int0 = k_int * params.k_synth / denom

    if not (0.0 <= r_surf0 <= 1.0 and 0.0 <= r_int0 <= 1.0):
        raise ValueError("steady_state_ic produced values outside [0, 1]")

    return (r_surf0, r_int0)
