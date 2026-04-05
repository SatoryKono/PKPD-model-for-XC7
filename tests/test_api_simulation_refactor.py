from __future__ import annotations

import json
from pathlib import Path

from src import api
from src.config.schemas import ModelConfig


def _canonical_config() -> ModelConfig:
    return ModelConfig.model_validate(
        {
            "model_id": "refactor_test_model",
            "compound": "histamine",
            "loss_mode": "mse",
            "assumptions": ["refactor_test_assumption"],
            "traceability": {
                "source_in_report": "Refactor test source",
                "source_reference": "tests",
                "source_version": "1",
            },
            "time_grid": [0.0, 0.5, 1.0, 1.5, 2.0],
            "time_unit": "h",
            "initial_concentration": 100.0,
            "concentration_unit": "nM",
            "kinetics": {
                "k_abs": 1.2,
                "k_elim": 0.3,
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


def test_run_simulation_is_pure_and_deterministic_without_filesystem() -> None:
    cfg = _canonical_config()

    first = api.run_simulation(cfg)
    second = api.run_simulation(cfg)

    assert first.config == cfg
    assert list(first.timeseries.columns) == [
        "time_h",
        "R_surf",
        "R_int",
        "histamine_nm",
        "k_abs_per_h",
        "k_elim_per_h",
        "tissue_partition_weighted_volume_l",
    ]
    assert len(first.timeseries) == len(cfg.time_grid)
    assert first.timeseries.equals(second.timeseries)
    assert first.marker_points.equals(second.marker_points)
    assert first.summary.equals(second.summary)


def test_persist_run_writes_csv_yaml_and_metadata(tmp_path: Path) -> None:
    result = api.run_simulation(_canonical_config())

    artifacts = api.persist_run(result, tmp_path / "run")

    assert artifacts.run_dir.exists()
    assert artifacts.simulation_csv.exists()
    assert artifacts.marker_points_csv.exists()
    assert artifacts.summary_csv.exists()
    assert artifacts.used_config_yaml.exists()
    assert artifacts.metadata_json.exists()

    metadata = json.loads(artifacts.metadata_json.read_text(encoding="utf-8"))
    recorded_paths = {item["path"] for item in metadata["artifacts"]}
    assert {"simulation.csv", "marker_points.csv", "summary.csv", "config.used.yaml"}.issubset(
        recorded_paths
    )
