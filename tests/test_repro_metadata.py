from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.io import export_simulation_run
from pkpd_xc7.simulation.runner import run_experiment


def _config() -> ModelConfig:
    return ModelConfig.model_validate(
        {
            "model_id": "repro_model",
            "compound": "xc7",
            "loss_mode": "mse",
            "assumptions": ["repro_test_assumption"],
            "traceability": {
                "source_in_report": "Repro test source",
                "source_reference": "internal",
                "source_version": "1",
            },
            "driver": {"driver_type": "scenario", "scenario_id": "formalin"},
            "tissues": ["skin", "spinal_coord"],
            "time_grid_h": [0.0, 0.5, 1.0, 1.5, 2.0],
        }
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_repeated_deterministic_runs_keep_simulation_hash_and_meta_contract(tmp_path: Path) -> None:
    config = _config()
    out_a = tmp_path / "run_a"
    out_b = tmp_path / "run_b"

    export_simulation_run(run_experiment(config), config, out_a)
    export_simulation_run(run_experiment(config), config, out_b)

    simulation_hash_a = _sha256(out_a / "simulation.csv")
    simulation_hash_b = _sha256(out_b / "simulation.csv")

    assert simulation_hash_a == simulation_hash_b

    meta_a = yaml.safe_load((out_a / "meta.yaml").read_text(encoding="utf-8"))
    meta_b = yaml.safe_load((out_b / "meta.yaml").read_text(encoding="utf-8"))

    for meta in (meta_a, meta_b):
        required = {
            "config_sha256",
            "config_schema_version",
            "simulation_schema_version",
            "column_order",
            "row_count",
            "driver_type",
            "driver_id",
            "generated_at_utc",
            "default_trafficking_params",
            "trafficking_params_by_tissue",
            "solver_metadata",
            "runtime_assumptions",
        }
        assert required.issubset(meta.keys())

    assert meta_a["config_sha256"] == meta_b["config_sha256"]
    assert meta_a["driver_type"] == meta_b["driver_type"] == "scenario"
    assert meta_a["driver_id"] == meta_b["driver_id"] == "formalin"
