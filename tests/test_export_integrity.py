from __future__ import annotations

import json
from pathlib import Path

import openpyxl
import pandas as pd
import yaml

from src.exporters.csv_tsv import export_delimited
from src.exporters.json_yaml import export_json, export_yaml
from src.exporters.xlsx import export_xlsx
from src.pipelines.run_layout import build_run_tables


def _sample_timeseries() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time_h": [0.0, 0.5, 1.0],
            "R_surf": [10.123456, 9.987654, 9.543219],
            "R_int": [1.234567, 1.876543, 2.111119],
            "histamine_nm": [100.0, 100.0, 100.0],
            "extra_tail": ["a", "b", "c"],
        }
    )


def test_csv_tsv_utf8_separator_and_rounding(tmp_path: Path) -> None:
    table = _sample_timeseries()

    csv_path = export_delimited(
        table,
        tmp_path / "timeseries.csv",
        sep=",",
        rounding_spec={"R_surf": 2, "R_int": 3},
        encoding="utf-8",
    )
    tsv_path = export_delimited(
        table,
        tmp_path / "timeseries.tsv",
        sep="\t",
        rounding_spec=2,
        encoding="utf-8",
    )

    csv_df = pd.read_csv(csv_path)
    tsv_df = pd.read_csv(tsv_path, sep="\t")

    assert csv_df.loc[0, "R_surf"] == 10.12
    assert csv_df.loc[0, "R_int"] == 1.235
    assert tsv_df.loc[1, "R_surf"] == 9.99
    assert tsv_df.loc[1, "R_int"] == 1.88


def test_json_yaml_and_xlsx_layout(tmp_path: Path) -> None:
    tables = build_run_tables(_sample_timeseries())

    json_path = export_json(tables, tmp_path / "run.json", rounding_spec={"R_surf": 2})
    yaml_path = export_yaml(tables, tmp_path / "run.yaml", rounding_spec={"R_surf": 2})
    xlsx_path = export_xlsx(tables, tmp_path / "run.xlsx", rounding_spec={"R_surf": 2})

    json_payload = json.loads(json_path.read_text(encoding="utf-8"))
    yaml_payload = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    assert list(json_payload.keys()) == ["timeseries", "marker_points", "summary"]
    assert list(yaml_payload.keys()) == ["timeseries", "marker_points", "summary"]

    workbook = openpyxl.load_workbook(xlsx_path)
    assert workbook.sheetnames == ["timeseries", "marker_points", "summary"]
    assert workbook["timeseries"].freeze_panes == "A2"
    assert workbook["marker_points"].freeze_panes == "A2"
    assert workbook["summary"].freeze_panes == "A2"


def test_run_layout_keeps_required_columns_prefix() -> None:
    raw = _sample_timeseries()
    tables = build_run_tables(raw)

    assert list(tables.timeseries.columns[:4]) == ["time_h", "R_surf", "R_int", "histamine_nm"]
    assert list(tables.marker_points.columns[:4]) == ["time_h", "R_surf", "R_int", "histamine_nm"]
    assert list(tables.summary.columns)[:2] == ["metric", "value"]
