from __future__ import annotations

import pandas as pd

from pkpd_xc7.validation.rounding_spec import RoundingSpec


def apply_rounding_spec(df: pd.DataFrame, spec: RoundingSpec) -> pd.DataFrame:
    """Apply deterministic rounding to a dataframe based on the specification."""
    rounded = df.copy()
    for col in rounded.columns:
        if pd.api.types.is_numeric_dtype(rounded[col]):
            decimals = spec.decimals.get(col, spec.default_decimals)
            rounded[col] = rounded[col].round(decimals)
    return rounded
