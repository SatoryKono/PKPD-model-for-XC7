from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.validation.rounding_spec import RoundingSpec


@dataclass(frozen=True)
class Difference:
    row_idx: int
    column: str
    expected: object
    actual: object
    rounding_decimals: int | None


def _rounded_series(series: pd.Series, decimals: int) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    mask = numeric.notna()
    out = series.copy()
    out.loc[mask] = numeric.loc[mask].round(decimals)
    return out


def apply_rounding_spec(df: pd.DataFrame, spec: RoundingSpec) -> pd.DataFrame:
    rounded = df.copy()
    for column in rounded.columns:
        decimals = spec.decimals_for(column)
        rounded[column] = _rounded_series(rounded[column], decimals)
    return rounded


def compare_marker_tables(
    expected: pd.DataFrame,
    actual: pd.DataFrame,
    spec: RoundingSpec,
    *,
    abs_tol_1dp: float = 0.1,
) -> list[Difference]:
    """Return row/column differences after canonical rounding by RoundingSpec."""
    expected_r = apply_rounding_spec(expected, spec).reset_index(drop=True)
    actual_r = apply_rounding_spec(actual, spec).reset_index(drop=True)

    if list(expected_r.columns) != list(actual_r.columns):
        raise ValueError("expected and actual marker tables must have identical columns")

    if len(expected_r) != len(actual_r):
        raise ValueError("expected and actual marker tables must have identical row count")

    diffs: list[Difference] = []
    for row_idx in range(len(expected_r)):
        for column in expected_r.columns:
            exp = expected_r.at[row_idx, column]
            act = actual_r.at[row_idx, column]
            decimals = spec.decimals_for(column)

            exp_num = pd.to_numeric(pd.Series([exp]), errors="coerce").iloc[0]
            act_num = pd.to_numeric(pd.Series([act]), errors="coerce").iloc[0]

            if pd.notna(exp_num) and pd.notna(act_num):
                if np.isclose(exp_num, act_num, rtol=0.0, atol=0.0):
                    continue
                if decimals == 1 and abs(float(exp_num) - float(act_num)) <= abs_tol_1dp:
                    continue
                diffs.append(Difference(row_idx, column, float(exp_num), float(act_num), decimals))
                continue

            if pd.isna(exp) and pd.isna(act):
                continue
            if exp != act:
                diffs.append(Difference(row_idx, column, exp, act, decimals))

    return diffs
