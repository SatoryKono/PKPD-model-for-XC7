from __future__ import annotations

import yaml
from pathlib import Path

import pandas as pd

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.io import build_simulation_meta, export_simulation_run, load_simulation_run
from pkpd_xc7.io.layout import TIMESERIES_COLUMN_ORDER
from pkpd_xc7.simulation.runner import run_experiment


def _sample_config() -> ModelConfig:
    return ModelConfig.model_validate(
        {
            "model_id": "export_integrity",
            "compound": "xc7",
            "loss_mode": "mse",
            "traceability": {"source_in_report": "export integrity"},
            "assumptions": ["export integrity test"],
            "driver": {"driver_type": "scenario", "scenario_id": "formalin"},
            "tissues": ["skin", "spinal_coord"],
            "time_grid_h": [0.0, 0.25, 1.0],
        }
    )


def test_export_simulation_run_writes_canonical_csv_and_yaml(tmp_path: Path) -> None:
    config = _sample_config()
    df = run_experiment(config)

    artifacts = export_simulation_run(df, config, tmp_path / "run")
    simulation = pd.read_csv(artifacts.simulation_csv)
    meta = yaml.safe_load(artifacts.meta_yaml.read_text(encoding="utf-8"))

    assert simulation.columns.tolist() == TIMESERIES_COLUMN_ORDER
    assert meta["column_order"] == TIMESERIES_COLUMN_ORDER
    assert meta["row_count"] == len(simulation.index)
    assert meta["driver_type"] == "scenario"
    assert meta["driver_id"] == "formalin"


def test_build_simulation_meta_includes_resolved_trafficking_and_runtime_assumptions() -> None:
    config = _sample_config()
    df = run_experiment(config)

    meta = build_simulation_meta(df, config)

    assert meta["default_trafficking_params"]["ec50_g_nm"] == config.trafficking.ec50_g_nm
    assert set(meta["trafficking_params_by_tissue"]) == {"skin", "spinal_coord"}
    assert "runtime_assumptions" in meta
    assert meta["simulation_schema_version"]


def test_load_simulation_run_roundtrips_exported_timeseries(tmp_path: Path) -> None:
    config = _sample_config()
    df = run_experiment(config)
    export_simulation_run(df, config, tmp_path / "run")

    run = load_simulation_run(tmp_path / "run")
    raw_csv = pd.read_csv(tmp_path / "run" / "simulation.csv")

    assert run.timeseries.equals(raw_csv)
    assert run.meta["driver_id"] == "formalin"
