from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from pkpd_xc7.cli.app import app
from pkpd_xc7.config.loader import load_model_config
from pkpd_xc7.io.layout import SIMULATION_SCHEMA_VERSION, TIMESERIES_COLUMN_ORDER

RUNNER = CliRunner()
SCENARIO_CONFIG_CASES = [
    "formalin",
    "capsaicin",
    "compound_48_80",
    "carrageenan",
    "hot_plate",
    "acetic_writhing",
    "zymosan",
]


def test_cli_version() -> None:
    result = RUNNER.invoke(app, ["version"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "pkpd-model-xc7 v" in result.stdout


def test_cli_simulate_writes_csv_and_meta_yaml(tmp_path: Path) -> None:
    cfg = Path(__file__).resolve().parent / "fixtures" / "phase1_minimal_scenario.yaml"
    out = tmp_path / "run_out"
    result = RUNNER.invoke(app, ["simulate", "--config", str(cfg), "--out", str(out)])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert (out / "simulation.csv").exists()

    meta_path = out / "meta.yaml"
    assert meta_path.exists()
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
    assert meta["simulation_schema_version"] == SIMULATION_SCHEMA_VERSION
    assert meta["column_order"] == TIMESERIES_COLUMN_ORDER
    assert meta["row_count"] > 0
    assert meta["generated_at_utc"].endswith("Z")
    assert "config_sha256" in meta
    assert "solver_metadata" in meta
    assert "runtime_assumptions" in meta
    assert isinstance(meta["runtime_assumptions"], list)
    assert len(meta["runtime_assumptions"]) >= 1


@pytest.mark.parametrize("scenario_id", SCENARIO_CONFIG_CASES)
def test_cli_simulate_runs_all_scenario_example_configs(tmp_path: Path, scenario_id: str) -> None:
    cfg = Path(__file__).resolve().parents[1] / "examples" / "configs" / "scenarios" / f"{scenario_id}.yaml"
    out = tmp_path / scenario_id

    result = RUNNER.invoke(app, ["simulate", "--config", str(cfg), "--out", str(out)])
    assert result.exit_code == 0, result.stdout + result.stderr

    meta = yaml.safe_load((out / "meta.yaml").read_text(encoding="utf-8"))
    model = load_model_config(cfg)

    assert meta["driver_type"] == "scenario"
    assert meta["driver_id"] == scenario_id
    assert meta["simulation_schema_version"] == SIMULATION_SCHEMA_VERSION
    assert meta["column_order"] == TIMESERIES_COLUMN_ORDER
    assert meta["row_count"] == len(model.tissues) * len(model.time_grid_h)
    assert meta["generated_at_utc"].endswith("Z")
    assert "trafficking_params_by_tissue" in meta
    assert "brain" in meta["trafficking_params_by_tissue"]