from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src import api
from src.config.schemas import ModelConfig


def _valid_config() -> ModelConfig:
    return ModelConfig.model_validate(
        {
            "model_id": "unit_model",
            "compound": "histamine",
            "loss_mode": "mse",
            "assumptions": ["unit_test_assumption"],
            "traceability": {
                "source_in_report": "Unit test source",
                "source_reference": "internal",
                "source_version": "1",
            },
            "time_grid": [0.0, 0.5, 1.0, 1.5, 2.0],
            "time_unit": "h",
            "initial_concentration": 100.0,
            "concentration_unit": "nM",
            "kinetics": {
                "k_abs": 0.4,
                "k_elim": 0.1,
                "rate_unit": "1/h",
            },
            "tissues": [
                {
                    "name": "plasma",
                    "volume": 1.0,
                    "volume_unit": "L",
                    "partition_coeff": 1.0,
                }
            ],
            "plots": [],
        }
    )


def test_run_simulation_returns_in_memory_tables_without_filesystem_side_effects() -> None:
    cfg = _valid_config()

    result = api.run_simulation(cfg)

    assert result.cfg == cfg
    assert list(result.run_tables.timeseries.columns) == ["time_h", "R_surf", "R_int", "histamine_nm"]
    assert list(result.run_tables.marker_points.columns) == ["time_h", "R_surf", "R_int", "histamine_nm"]
    assert list(result.run_tables.summary.columns) == ["metric", "value"]
    assert len(result.run_tables.timeseries) == len(cfg.time_grid)
    assert (result.run_tables.timeseries["histamine_nm"] == cfg.initial_concentration).all()


def test_persist_run_writes_csv_yaml_and_metadata(tmp_path: Path) -> None:
    cfg = _valid_config()
    result = api.run_simulation(cfg)

    artifacts = api.persist_run(result, tmp_path / "run")

    assert artifacts.simulation_csv.exists()
    assert artifacts.marker_points_csv.exists()
    assert artifacts.summary_csv.exists()
    assert artifacts.used_config_yaml.exists()
    assert artifacts.metadata_json.exists()

    persisted_timeseries = pd.read_csv(artifacts.simulation_csv)
    assert list(persisted_timeseries.columns) == ["time_h", "R_surf", "R_int", "histamine_nm"]

    metadata = json.loads(artifacts.metadata_json.read_text(encoding="utf-8"))
    assert metadata["deterministic_mode"] is True
    artifact_paths = {item["path"] for item in metadata["artifacts"]}
    assert artifact_paths == {
        "simulation.csv",
        "marker_points.csv",
        "summary.csv",
        "config.used.yaml",
    }
