from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.exporters.csv_tsv import RoundingSpec, apply_rounding
from src.pipelines.run_layout import RunTables


def export_xlsx(
    tables: RunTables,
    out_path: str | Path,
    *,
    rounding_spec: RoundingSpec = None,
    freeze_panes: str = "A2",
) -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rounded_timeseries = apply_rounding(tables.timeseries, rounding_spec)
    rounded_markers = apply_rounding(tables.marker_points, rounding_spec)
    rounded_summary = apply_rounding(tables.summary, rounding_spec)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        rounded_timeseries.to_excel(writer, sheet_name="timeseries", index=False)
        rounded_markers.to_excel(writer, sheet_name="marker_points", index=False)
        rounded_summary.to_excel(writer, sheet_name="summary", index=False)

        for sheet_name in ("timeseries", "marker_points", "summary"):
            writer.sheets[sheet_name].freeze_panes = freeze_panes

    return path
