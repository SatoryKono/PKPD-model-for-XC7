from __future__ import annotations

import pandas as pd

# Schema Versioning Rules:
# - MINOR bump: new columns appended at the end, or backwards-compatible metadata additions.
# - MAJOR bump: column renaming/removal, or semantics/unit changes for existing fields.
SIMULATION_SCHEMA_VERSION = "2.1.0"

TIME_H_COL = "time_h"
TISSUE_COL = "tissue"
HISTAMINE_COL = "histamine_nm"
R_SURF_COL = "R_surf"
R_INT_COL = "R_int"
G_SIGNAL_COL = "G_signal"
G_SIGNAL_PCT_COL = "G_signal_pct"
G_SIGNAL_LIGAND_COL = "G_signal_ligand"
G_SIGNAL_LIGAND_PCT_COL = "G_signal_ligand_pct"
G_SIGNAL_CONSTITUTIVE_COL = "G_signal_constitutive"
G_SIGNAL_CONSTITUTIVE_PCT_COL = "G_signal_constitutive_pct"
BETA_ARR_SIGNAL_COL = "beta_arr_signal"
BETA_ARR_SIGNAL_PCT_COL = "beta_arr_signal_pct"
INTERNALIZATION_DRIVE_COL = "internalization_drive"
K_INT_EFF_PER_H_COL = "k_int_eff_per_h"
DRIVER_TYPE_COL = "driver_type"
DRIVER_ID_COL = "driver_id"
ANTAGONIST_CONCENTRATION_COL = "antagonist_concentration_nm"

TIMESERIES_COLUMN_ORDER: list[str] = [
    TIME_H_COL,
    TISSUE_COL,
    HISTAMINE_COL,
    R_SURF_COL,
    R_INT_COL,
    G_SIGNAL_COL,
    G_SIGNAL_PCT_COL,
    G_SIGNAL_LIGAND_COL,
    G_SIGNAL_LIGAND_PCT_COL,
    G_SIGNAL_CONSTITUTIVE_COL,
    G_SIGNAL_CONSTITUTIVE_PCT_COL,
    BETA_ARR_SIGNAL_COL,
    BETA_ARR_SIGNAL_PCT_COL,
    INTERNALIZATION_DRIVE_COL,
    K_INT_EFF_PER_H_COL,
    DRIVER_TYPE_COL,
    DRIVER_ID_COL,
    ANTAGONIST_CONCENTRATION_COL,
]

TIMESERIES_REQUIRED_COLUMNS: tuple[str, ...] = tuple(column for column in TIMESERIES_COLUMN_ORDER if column != ANTAGONIST_CONCENTRATION_COL)


def enforce_timeseries_layout(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and reorder exported timeseries columns deterministically."""
    missing = [column for column in TIMESERIES_REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Timeseries dataframe is missing required columns: {missing}")
    layout_df = df.copy()
    if ANTAGONIST_CONCENTRATION_COL not in layout_df.columns:
        layout_df[ANTAGONIST_CONCENTRATION_COL] = pd.Series([float("nan")] * len(layout_df.index), index=layout_df.index)
    return layout_df.loc[:, TIMESERIES_COLUMN_ORDER].copy()
