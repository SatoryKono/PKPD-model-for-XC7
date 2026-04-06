from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from src.exporters.csv_tsv import RoundingSpec, apply_rounding
from src.pipelines.run_layout import RunTables
from src.utils.atomic_io import write_text_atomic


def _as_records_dict(tables: RunTables, rounding_spec: RoundingSpec) -> dict[str, list[dict[str, Any]]]:
    return {
        "timeseries": apply_rounding(tables.timeseries, rounding_spec).to_dict(orient="records"),
        "marker_points": apply_rounding(tables.marker_points, rounding_spec).to_dict(orient="records"),
        "summary": apply_rounding(tables.summary, rounding_spec).to_dict(orient="records"),
    }


def export_json(
    tables: RunTables,
    out_path: str | Path,
    *,
    rounding_spec: RoundingSpec = None,
) -> Path:
    payload = _as_records_dict(tables, rounding_spec)
    write_text_atomic(out_path, json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return Path(out_path)


def export_yaml(
    tables: RunTables,
    out_path: str | Path,
    *,
    rounding_spec: RoundingSpec = None,
) -> Path:
    payload = _as_records_dict(tables, rounding_spec)
    write_text_atomic(
        out_path,
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return Path(out_path)
