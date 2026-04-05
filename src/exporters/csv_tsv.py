from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.pipelines.run_layout import RunTables

RoundingSpec = int | dict[str, int] | None


def apply_rounding(frame: pd.DataFrame, rounding_spec: RoundingSpec) -> pd.DataFrame:
    out = frame.copy()
    if rounding_spec is None:
        return out

    if isinstance(rounding_spec, int):
        numeric_columns = out.select_dtypes(include="number").columns
        if len(numeric_columns) > 0:
            out.loc[:, numeric_columns] = out.loc[:, numeric_columns].round(rounding_spec)
        return out

    for column, decimals in rounding_spec.items():
        if column in out.columns and pd.api.types.is_numeric_dtype(out[column]):
            out[column] = out[column].round(decimals)

    return out


def export_delimited(
    frame: pd.DataFrame,
    out_path: str | Path,
    *,
    sep: str = ",",
    rounding_spec: RoundingSpec = None,
    encoding: str = "utf-8",
) -> Path:
    normalized = apply_rounding(frame, rounding_spec)
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(path, index=False, sep=sep, encoding=encoding)
    return path


def export_run_tables_csv_tsv(
    tables: RunTables,
    out_dir: str | Path,
    *,
    sep: str = ",",
    suffix: str = "csv",
    rounding_spec: RoundingSpec = None,
    encoding: str = "utf-8",
) -> dict[str, Path]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)

    return {
        "timeseries": export_delimited(
            tables.timeseries,
            root / f"timeseries.{suffix}",
            sep=sep,
            rounding_spec=rounding_spec,
            encoding=encoding,
        ),
        "marker_points": export_delimited(
            tables.marker_points,
            root / f"marker_points.{suffix}",
            sep=sep,
            rounding_spec=rounding_spec,
            encoding=encoding,
        ),
        "summary": export_delimited(
            tables.summary,
            root / f"summary.{suffix}",
            sep=sep,
            rounding_spec=rounding_spec,
            encoding=encoding,
        ),
    }
