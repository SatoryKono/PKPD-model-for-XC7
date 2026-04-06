from __future__ import annotations

import pandas as pd

from pkpd_xc7.io.layout import (
    BETA_ARR_SIGNAL_COL,
    BETA_ARR_SIGNAL_PCT_COL,
    G_SIGNAL_COL,
    G_SIGNAL_CONSTITUTIVE_COL,
    G_SIGNAL_CONSTITUTIVE_PCT_COL,
    G_SIGNAL_LIGAND_COL,
    G_SIGNAL_LIGAND_PCT_COL,
    G_SIGNAL_PCT_COL,
    HISTAMINE_COL,
    INTERNALIZATION_DRIVE_COL,
    K_INT_EFF_PER_H_COL,
    R_SURF_COL,
)
from pkpd_xc7.models.h3_signaling import (
    agonist_g_signal_fraction,
    beta_arr_fraction,
    constitutive_signal_fraction,
    g_signal_percent,
    g_signaling_fraction,
)
from pkpd_xc7.models.receptor_trafficking import TraffickingCoreParams, internalization_drive, k_int_eff


def add_g_signal_columns(
    df: pd.DataFrame,
    params: TraffickingCoreParams,
    *,
    histamine_col: str = HISTAMINE_COL,
    r_surf_col: str = R_SURF_COL,
) -> pd.DataFrame:
    """Add model-space and report-space G columns from receptor trajectories."""
    result = df.copy()
    histamine = result[histamine_col].to_numpy()
    r_surf = result[r_surf_col].to_numpy()
    g_signal_total = g_signaling_fraction(histamine, r_surf, params)
    g_signal_ligand = agonist_g_signal_fraction(histamine, r_surf, params)
    g_signal_constitutive = constitutive_signal_fraction(r_surf, params)
    beta_arr_signal = beta_arr_fraction(histamine, params)
    int_drive = [internalization_drive(float(h), params) for h in histamine]
    k_int_values = [k_int_eff(float(h), params) for h in histamine]

    result[G_SIGNAL_COL] = g_signal_total
    result[G_SIGNAL_PCT_COL] = g_signal_percent(g_signal_total)
    result[G_SIGNAL_LIGAND_COL] = g_signal_ligand
    result[G_SIGNAL_LIGAND_PCT_COL] = g_signal_percent(g_signal_ligand)
    result[G_SIGNAL_CONSTITUTIVE_COL] = g_signal_constitutive
    result[G_SIGNAL_CONSTITUTIVE_PCT_COL] = g_signal_percent(g_signal_constitutive)
    result[BETA_ARR_SIGNAL_COL] = beta_arr_signal
    result[BETA_ARR_SIGNAL_PCT_COL] = g_signal_percent(beta_arr_signal)
    result[INTERNALIZATION_DRIVE_COL] = int_drive
    result[K_INT_EFF_PER_H_COL] = k_int_values
    return result
