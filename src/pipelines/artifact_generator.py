from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.pipelines.run_layout import RunTables, load_run_tables
from src.utils.atomic_io import dataframe_to_csv_atomic
from src.plots.templates import (
    PlotAnnotationOptions,
    PlotRenderResult,
    render_gsignaling,
    render_histamine,
    render_receptors,
)


@dataclass(frozen=True)
class UnifiedArtifacts:
    """File map of generated tabular artifacts and required plots."""

    tables: dict[str, Path]
    plots: dict[str, Path]
    plot_snapshots: dict[str, Path]


def _annotation_options(report: dict[str, Any] | None, config: dict[str, Any] | None) -> PlotAnnotationOptions:
    """Enable phase/EC50 annotations only when explicitly present in report/config."""

    merged: dict[str, Any] = {}
    if config:
        merged.update(config)
    if report:
        merged.update(report)

    markers = merged.get("phase_markers_h") or merged.get("phase_markers") or ()
    ec50 = merged.get("ec50_nm")

    phase_markers_h: tuple[float, ...]
    if isinstance(markers, (list, tuple)):
        phase_markers_h = tuple(float(value) for value in markers)
    else:
        phase_markers_h = ()

    ec50_nm = float(ec50) if ec50 is not None else None
    return PlotAnnotationOptions(phase_markers_h=phase_markers_h, ec50_nm=ec50_nm)


def _write_tables(tables: RunTables, output_root: Path) -> dict[str, Path]:
    tables_dir = output_root / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    mapping = {
        "timeseries": tables.timeseries,
        "marker_points": tables.marker_points,
        "summary": tables.summary,
    }

    written: dict[str, Path] = {}
    for name, table in mapping.items():
        path = tables_dir / f"{name}.csv"
        dataframe_to_csv_atomic(table, path, index=False)
        written[name] = path

    return written


def _write_snapshot_csv(name: str, rendered: PlotRenderResult, output_root: Path) -> Path:
    snapshots_dir = output_root / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    path = snapshots_dir / f"{name}.csv"
    dataframe_to_csv_atomic(rendered.data_rows, path, index=False)
    return path


def generate_unified_artifacts(
    run_dir: str | Path,
    out_dir: str | Path | None = None,
    report_meta: dict[str, Any] | None = None,
    config_meta: dict[str, Any] | None = None,
) -> UnifiedArtifacts:
    """Generate tables + mandatory H/R/G plots + CSV snapshots in one pass."""

    run_path = Path(run_dir)
    output_root = Path(out_dir) if out_dir is not None else run_path
    output_root.mkdir(parents=True, exist_ok=True)

    tables = load_run_tables(run_path)
    table_paths = _write_tables(tables, output_root)

    annotations = _annotation_options(report=report_meta, config=config_meta)
    plots_dir = output_root / "plots"

    histamine = render_histamine(tables.timeseries, plots_dir / "histamine.png", annotations)
    receptors = render_receptors(tables.timeseries, plots_dir / "receptors.png", annotations)
    gsignaling = render_gsignaling(tables.timeseries, plots_dir / "gsignaling.png", annotations)

    plots = {
        "histamine": histamine.image_path,
        "receptors": receptors.image_path,
        "gsignaling": gsignaling.image_path,
    }

    snapshots = {
        "histamine": _write_snapshot_csv("histamine", histamine, output_root),
        "receptors": _write_snapshot_csv("receptors", receptors, output_root),
        "gsignaling": _write_snapshot_csv("gsignaling", gsignaling, output_root),
    }

    return UnifiedArtifacts(tables=table_paths, plots=plots, plot_snapshots=snapshots)
