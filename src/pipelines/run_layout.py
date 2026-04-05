from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

TIMESERIES_REQUIRED_COLUMNS: tuple[str, ...] = (
    "time_h",
    "R_surf",
    "R_int",
    "histamine_nm",
)
MARKER_POINTS_REQUIRED_COLUMNS: tuple[str, ...] = (
    "time_h",
    "R_surf",
    "R_int",
    "histamine_nm",
)
SUMMARY_REQUIRED_COLUMNS: tuple[str, ...] = (
    "metric",
    "value",
)


@dataclass(frozen=True)
class RunTables:
    timeseries: pd.DataFrame
    marker_points: pd.DataFrame
    summary: pd.DataFrame


def _ensure_required_prefix(df: pd.DataFrame, required: tuple[str, ...], name: str) -> pd.DataFrame:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")

    ordered = list(required) + [column for column in df.columns if column not in required]
    return df.loc[:, ordered].copy()


def _default_marker_points(timeseries: pd.DataFrame) -> pd.DataFrame:
    return timeseries.loc[:, list(MARKER_POINTS_REQUIRED_COLUMNS)].copy()


def _default_summary(timeseries: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = [
        {"metric": "rows", "value": int(len(timeseries))},
    ]

    for column in TIMESERIES_REQUIRED_COLUMNS[1:]:
        series = pd.to_numeric(timeseries[column], errors="coerce")
        if series.notna().any():
            rows.extend(
                [
                    {"metric": f"{column}_min", "value": float(series.min())},
                    {"metric": f"{column}_max", "value": float(series.max())},
                ]
            )

    return pd.DataFrame(rows, columns=list(SUMMARY_REQUIRED_COLUMNS))


def build_run_tables(
    timeseries: pd.DataFrame,
    marker_points: pd.DataFrame | None = None,
    summary: pd.DataFrame | None = None,
) -> RunTables:
    ts = _ensure_required_prefix(timeseries, TIMESERIES_REQUIRED_COLUMNS, "timeseries")
    markers = _default_marker_points(ts) if marker_points is None else marker_points
    marker_layout = _ensure_required_prefix(markers, MARKER_POINTS_REQUIRED_COLUMNS, "marker_points")

    summary_data = _default_summary(ts) if summary is None else summary
    summary_layout = _ensure_required_prefix(summary_data, SUMMARY_REQUIRED_COLUMNS, "summary")

    return RunTables(timeseries=ts, marker_points=marker_layout, summary=summary_layout)


def load_run_tables(run_dir: str | Path) -> RunTables:
    root = Path(run_dir)
    simulation_csv = root / "simulation.csv"
    if not simulation_csv.exists():
        raise ValueError(f"simulation.csv not found in run-dir: {root}")

    timeseries = pd.read_csv(simulation_csv)

    marker_csv = root / "marker_points.csv"
    summary_csv = root / "summary.csv"

    marker_points = pd.read_csv(marker_csv) if marker_csv.exists() else None
    summary = pd.read_csv(summary_csv) if summary_csv.exists() else None

    return build_run_tables(timeseries=timeseries, marker_points=marker_points, summary=summary)
