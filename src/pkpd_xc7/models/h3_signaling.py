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


def _resolve_competitive_kb_nm(
    default_kb_nm: float | None,
    kb_nm: float | None,
    xc7_nm: float | np.ndarray,
    *,
    param_name: str,
) -> float:
    if kb_nm is not None:
        return float(kb_nm)
    if default_kb_nm is not None:
        return float(default_kb_nm)
    if np.any(np.asarray(xc7_nm, dtype=float) > 0.0):
        raise TypeError(f"{param_name} is required when xc7_nm is provided without params.")
    return 1.0


def _competitive_effective_histamine(
    histamine_nm: float | np.ndarray,
    xc7_nm: float | np.ndarray,
    kb_nm: float,
    *,
    param_name: str,
) -> float | np.ndarray:
    if np.isscalar(histamine_nm) and np.isscalar(xc7_nm):
        histamine_scalar = float(np.asarray(histamine_nm, dtype=float).item())
        xc7_scalar = float(np.asarray(xc7_nm, dtype=float).item())
        return competitive_effective_histamine_nm(
            histamine_scalar,
            xc7_nm=xc7_scalar,
            kb_nm=kb_nm,
        )

    histamine = np.asarray(histamine_nm, dtype=float)
    xc7 = np.asarray(xc7_nm, dtype=float)
    if np.any(xc7 < 0.0):
        raise ValueError("xc7_nm must be non-negative.")
    if kb_nm <= 0.0:
        raise ValueError(f"{param_name} must be positive.")

    positive_histamine = np.clip(histamine, 0.0, None)
    return positive_histamine / (1.0 + (xc7 / kb_nm))


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
    *,
    xc7_nm: float | np.ndarray = 0.0,
    kb_g_nm: float | None = None,
) -> float | np.ndarray:
    """Return agonist-driven G-signal fraction in [0, 1], excluding constitutive activity."""
    if isinstance(params_or_ec50, TraffickingCoreParams):
        ec50_g_nm = params_or_ec50.ec50_g_nm
        hill = params_or_ec50.hill_n
        kb_g = _resolve_competitive_kb_nm(params_or_ec50.kb_g_nm, kb_g_nm, xc7_nm, param_name="kb_g_nm")
    else:
        if hill_n is None:
            raise TypeError("hill_n is required when params are not provided.")
        ec50_g_nm = float(params_or_ec50)
        hill = float(hill_n)
        kb_g = _resolve_competitive_kb_nm(None, kb_g_nm, xc7_nm, param_name="kb_g_nm")

    effective_histamine = _competitive_effective_histamine(histamine_nm, xc7_nm, kb_g, param_name="kb_g_nm")
    activation = hill_activation(effective_histamine, ec50_g_nm, hill)
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
        kb_arr = _resolve_competitive_kb_nm(params_or_ec50.kb_arr_nm, kb_arr_nm, xc7_nm, param_name="kb_arr_nm")
    else:
        if hill_n is None:
            raise TypeError("hill_n is required when params are not provided.")
        ec50_barr_nm = float(params_or_ec50)
        hill = float(hill_n)
        kb_arr = _resolve_competitive_kb_nm(None, kb_arr_nm, xc7_nm, param_name="kb_arr_nm")

    effective_histamine = _competitive_effective_histamine(histamine_nm, xc7_nm, kb_arr, param_name="kb_arr_nm")
    return hill_activation(effective_histamine, ec50_barr_nm, hill)


def g_signaling_fraction(
    histamine_nm: float | np.ndarray,
    r_surf: float | np.ndarray,
    params_or_ec50: TraffickingCoreParams | float,
    hill_n: float | None = None,
    constitutive_activity: float | None = None,
    *,
    xc7_nm: float | np.ndarray = 0.0,
    kb_g_nm: float | None = None,
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

    if isinstance(params_or_ec50, TraffickingCoreParams):
        agonist_fraction = agonist_g_signal_fraction(
            histamine_nm,
            r_surf,
            params_or_ec50,
            xc7_nm=xc7_nm,
            kb_g_nm=kb_g_nm,
        )
    else:
        agonist_fraction = agonist_g_signal_fraction(
            histamine_nm,
            r_surf,
            ec50_g_nm,
            hill_n=hill,
            xc7_nm=xc7_nm,
            kb_g_nm=kb_g_nm,
        )
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