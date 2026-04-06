from __future__ import annotations

import yaml
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.io import export_simulation_run, load_simulation_run
from pkpd_xc7.io.layout import TIMESERIES_COLUMN_ORDER
from pkpd_xc7.simulation.runner import run_experiment


def _canonical_config() -> ModelConfig:
    return ModelConfig.model_validate(
        {
            "model_id": "refactor_test_model",
            "compound": "xc7",
            "loss_mode": "mse",
            "assumptions": ["refactor_test_assumption"],
            "traceability": {
                "source_in_report": "Refactor test source",
                "source_reference": "tests",
                "source_version": "1",
            },
            "driver": {"driver_type": "pk", "dose": 100.0, "k_abs_per_h": 1.2, "k_elim_per_h": 0.3},
            "trafficking": {"h_base_nm": 50.0},
            "tissue_overrides": {"brain": {"trafficking": {"h_base_nm": 2.0}}},
            "tissues": ["brain"],
            "time_grid_h": [0.0, 0.5, 1.0, 1.5, 2.0],
        }
    )


def test_run_experiment_is_pure_and_deterministic_without_filesystem() -> None:
    cfg = _canonical_config()

    first = run_experiment(cfg)
    second = run_experiment(cfg)

    assert list(first.columns) == TIMESERIES_COLUMN_ORDER
    assert len(first) == len(cfg.time_grid_h)
    assert first.equals(second)
    assert first.attrs["solver_metadata"] == second.attrs["solver_metadata"]
    assert first.attrs["runtime_assumptions"] == second.attrs["runtime_assumptions"]


def test_export_simulation_run_writes_csv_and_meta_yaml(tmp_path: Path) -> None:
    result = run_experiment(_canonical_config())

    artifacts = export_simulation_run(result, _canonical_config(), tmp_path / "run")

    assert artifacts.out_dir.exists()
    assert artifacts.simulation_csv.exists()
    assert artifacts.meta_yaml.exists()

    simulation = pd.read_csv(artifacts.simulation_csv)
    run = load_simulation_run(tmp_path / "run")
    meta = yaml.safe_load(artifacts.meta_yaml.read_text(encoding="utf-8"))

    assert simulation.columns.tolist()[0] == "time_h"
    assert_frame_equal(run.timeseries, simulation, check_dtype=False)
    assert meta["driver_type"] == "pk"
    assert meta["driver_id"] == "pk_model"
    assert meta["row_count"] == len(simulation)
    assert meta["trafficking_params_by_tissue"]["brain"]["h_base_nm"] == pytest.approx(2.0)
    assert "refactor_test_assumption" in meta["runtime_assumptions"]
    assert all("legacy h_base_nm=50.0" not in item for item in meta["runtime_assumptions"])
