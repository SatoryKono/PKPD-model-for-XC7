from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.histamine_profiles import Tissue


@dataclass(frozen=True)
class GSignalParams:
    """Model 3 parameters for H3R G-signaling."""

    ec50_g_nm: float = 50.0
    hill_n: float = 1.0
    constitutive_activity_fraction: float = 0.05


CONSTITUTIVE_ACTIVITY_BY_TISSUE: dict[Tissue, float] = {
    Tissue.SKIN: 0.05,
    Tissue.GANGLIA: 0.10,
    Tissue.CNS: 0.25,
}


def constitutive_activity_fraction_for_tissue(tissue: Tissue) -> float:
    try:
        return float(CONSTITUTIVE_ACTIVITY_BY_TISSUE[tissue])
    except KeyError as exc:
        raise ValueError(f"Constitutive activity is not defined for tissue: {tissue}") from exc


def default_g_signal_params_for_tissue(
    tissue: Tissue,
    *,
    ec50_g_nm: float = 50.0,
    hill_n: float = 1.0,
) -> GSignalParams:
    if ec50_g_nm <= 0:
        raise ValueError("ec50_g_nm must be > 0")
    if hill_n <= 0:
        raise ValueError("hill_n must be > 0")
    return GSignalParams(
        ec50_g_nm=float(ec50_g_nm),
        hill_n=float(hill_n),
        constitutive_activity_fraction=constitutive_activity_fraction_for_tissue(tissue),
    )


def g_signal_percent(
    histamine_nm: float | np.ndarray,
    r_surf: float | np.ndarray,
    params: GSignalParams,
) -> float | np.ndarray:
    h = np.asarray(histamine_nm, dtype=float)
    rs = np.asarray(r_surf, dtype=float)

    if np.any(h < 0):
        raise ValueError("histamine_nm must be >= 0")
    if np.any(rs < 0):
        raise ValueError("r_surf must be >= 0")
    if params.ec50_g_nm <= 0:
        raise ValueError("params.ec50_g_nm must be > 0")
    if params.hill_n <= 0:
        raise ValueError("params.hill_n must be > 0")
    if not (0.0 <= params.constitutive_activity_fraction <= 1.0):
        raise ValueError("params.constitutive_activity_fraction must be in [0, 1]")

    occupancy = h**params.hill_n / (params.ec50_g_nm**params.hill_n + h**params.hill_n)
    response_fraction = params.constitutive_activity_fraction + (
        (1.0 - params.constitutive_activity_fraction) * occupancy
    )
    signal = response_fraction * rs * 100.0
    if np.isscalar(histamine_nm) and np.isscalar(r_surf):
        return float(signal.item())
    return signal


__all__ = [
    "GSignalParams",
    "CONSTITUTIVE_ACTIVITY_BY_TISSUE",
    "constitutive_activity_fraction_for_tissue",
    "default_g_signal_params_for_tissue",
    "g_signal_percent",
]
