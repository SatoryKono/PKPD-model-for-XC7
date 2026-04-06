from __future__ import annotations

import numpy as np

from pkpd_xc7.models.receptor_trafficking import TraffickingCoreParams, competitive_effective_histamine_nm


def hill_activation(histamine_nm: float | np.ndarray, ec50_nm: float, hill_n: float) -> float | np.ndarray:
    """Return Hill activation in [0, 1] with a zero branch for H <= 0."""
    histamine = np.asarray(histamine_nm, dtype=float)
    positive = np.clip(histamine, 0.0, None)
    numerator = positive**hill_n
    denominator = (ec50_nm**hill_n) + numerator
    with np.errstate(divide="ignore", invalid="ignore"):
        activation = np.divide(numerator, denominator, out=np.zeros_like(positive), where=denominator > 0.0)
    if np.isscalar(histamine_nm):
        return float(activation.item())
    return activation


def constitutive_signal_fraction(
    r_surf: float | np.ndarray,
    params_or_constitutive: TraffickingCoreParams | float,
) -> float | np.ndarray:
    """Return constitutive receptor activity in [0, 1] on the report Emax scale."""
    constitutive = (
        params_or_constitutive.constitutive_activity
        if isinstance(params_or_constitutive, TraffickingCoreParams)
        else float(params_or_constitutive)
    )
    r_surf_arr = np.clip(np.asarray(r_surf, dtype=float), 0.0, 1.0)
    fraction = np.clip(constitutive * r_surf_arr, 0.0, 1.0)
    if np.isscalar(r_surf):
        return float(fraction.item())
    return fraction


def agonist_g_signal_fraction(
    histamine_nm: float | np.ndarray,
    r_surf: float | np.ndarray,
    params_or_ec50: TraffickingCoreParams | float,
    hill_n: float | None = None,
) -> float | np.ndarray:
    """Return agonist-driven G-signal fraction in [0, 1], excluding constitutive activity."""
    if isinstance(params_or_ec50, TraffickingCoreParams):
        ec50_g_nm = params_or_ec50.ec50_g_nm
        hill = params_or_ec50.hill_n
    else:
        if hill_n is None:
            raise TypeError("hill_n is required when params are not provided.")
        ec50_g_nm = float(params_or_ec50)
        hill = float(hill_n)

    activation = hill_activation(histamine_nm, ec50_g_nm, hill)
    r_surf_arr = np.clip(np.asarray(r_surf, dtype=float), 0.0, 1.0)
    fraction = np.clip(np.asarray(activation, dtype=float) * r_surf_arr, 0.0, 1.0)
    if np.isscalar(histamine_nm) and np.isscalar(r_surf):
        return float(fraction.item())
    return fraction


def beta_arr_fraction(
    histamine_nm: float | np.ndarray,
    params_or_ec50: TraffickingCoreParams | float,
    hill_n: float | None = None,
    *,
    xc7_nm: float | np.ndarray = 0.0,
    kb_arr_nm: float | None = None,
) -> float | np.ndarray:
    """Return beta-arrestin pathway activation fraction in [0, 1]."""
    if isinstance(params_or_ec50, TraffickingCoreParams):
        ec50_barr_nm = params_or_ec50.ec50_barr_nm
        hill = params_or_ec50.hill_n
        kb_arr = params_or_ec50.kb_arr_nm if kb_arr_nm is None else float(kb_arr_nm)
    else:
        if hill_n is None:
            raise TypeError("hill_n is required when params are not provided.")
        ec50_barr_nm = float(params_or_ec50)
        hill = float(hill_n)
        if kb_arr_nm is None and np.any(np.asarray(xc7_nm, dtype=float) > 0.0):
            raise TypeError("kb_arr_nm is required when xc7_nm is provided without params.")
        kb_arr = 1.0 if kb_arr_nm is None else float(kb_arr_nm)

    if np.isscalar(histamine_nm) and np.isscalar(xc7_nm):
        histamine_scalar = float(np.asarray(histamine_nm, dtype=float).item())
        xc7_scalar = float(np.asarray(xc7_nm, dtype=float).item())
        effective_histamine_scalar = competitive_effective_histamine_nm(
            histamine_scalar,
            xc7_nm=xc7_scalar,
            kb_nm=kb_arr,
        )
        return hill_activation(effective_histamine_scalar, ec50_barr_nm, hill)

    histamine = np.asarray(histamine_nm, dtype=float)
    xc7 = np.asarray(xc7_nm, dtype=float)
    if np.any(xc7 < 0.0):
        raise ValueError("xc7_nm must be non-negative.")
    if kb_arr <= 0.0:
        raise ValueError("kb_arr_nm must be positive.")

    positive_histamine = np.clip(histamine, 0.0, None)
    effective_histamine_arr = positive_histamine / (1.0 + (xc7 / kb_arr))
    return hill_activation(effective_histamine_arr, ec50_barr_nm, hill)


def g_signaling_fraction(
    histamine_nm: float | np.ndarray,
    r_surf: float | np.ndarray,
    params_or_ec50: TraffickingCoreParams | float,
    hill_n: float | None = None,
    constitutive_activity: float | None = None,
) -> float | np.ndarray:
    """
    Return G-signal fraction in [0, 1].

    Supports both the current `TraffickingCoreParams` contract and the legacy
    explicit-parameter calling convention.
    """
    if isinstance(params_or_ec50, TraffickingCoreParams):
        ec50_g_nm = params_or_ec50.ec50_g_nm
        hill = params_or_ec50.hill_n
        constitutive = params_or_ec50.constitutive_activity
    else:
        if hill_n is None or constitutive_activity is None:
            raise TypeError("hill_n and constitutive_activity are required when params are not provided.")
        ec50_g_nm = float(params_or_ec50)
        hill = float(hill_n)
        constitutive = float(constitutive_activity)

    agonist_fraction = agonist_g_signal_fraction(histamine_nm, r_surf, ec50_g_nm, hill_n=hill)
    constitutive_fraction = constitutive_signal_fraction(r_surf, constitutive)
    fraction = np.asarray(constitutive_fraction, dtype=float) + (
        (1.0 - constitutive) * np.asarray(agonist_fraction, dtype=float)
    )
    fraction = np.clip(fraction, 0.0, 1.0)
    if np.isscalar(histamine_nm) and np.isscalar(r_surf):
        return float(fraction.item())
    return fraction


def g_signal_percent(g_signal_fraction_value: float | np.ndarray) -> float | np.ndarray:
    """Convert model-space fraction to report-space percentage."""
    value = np.asarray(g_signal_fraction_value, dtype=float) * 100.0
    if np.isscalar(g_signal_fraction_value):
        return float(value.item())
    return value